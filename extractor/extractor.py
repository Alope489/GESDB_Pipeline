import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from openai import RateLimitError as OpenAIRateLimitError

from .utils.extractor_utils import ExtractorUtils


logger = logging.getLogger(__name__)


def _is_rate_limit_error(exc: BaseException) -> bool:
    if isinstance(exc, OpenAIRateLimitError):
        return True
    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, OpenAIRateLimitError):
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg


def _get_retry_after_seconds(exc: BaseException, default_seconds: int) -> int:
    err = exc
    if isinstance(exc, OpenAIRateLimitError):
        pass
    else:
        cause = getattr(exc, "__cause__", None)
        if isinstance(cause, OpenAIRateLimitError):
            err = cause
        else:
            return default_seconds
    response = getattr(err, "response", None)
    if response is None:
        return default_seconds
    raw = response.headers.get("Retry-After")
    if not raw:
        return default_seconds
    raw = raw.strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return default_seconds


class Extractor:
    """
    Runs registered LLM tools on article text. extract_all runs tools in parallel;
    on OpenAI rate limit (429) it logs, waits (Retry-After or default), and retries
    with reduced concurrency. Rate-limit events are logged.
    """

    def __init__(
        self,
        api_key,
        *,
        max_workers=8,
        min_workers=1,
        rate_limit_retry_delay_seconds=60,
        max_rate_limit_retries=3,
    ):
        """
        max_workers: initial parallel tool concurrency per article.
        min_workers: floor when reducing concurrency after 429.
        rate_limit_retry_delay_seconds: default wait when Retry-After header is missing.
        max_rate_limit_retries: max 429 retries per article before raising.
        """
        self.llm = ChatOpenAI(
            model="gpt-5",
            api_key=api_key,
            temperature=0.0,
            use_responses_api=True,
            output_version="responses/v1",
        )
        self.tools = {}
        self._tool_declared_names = {}
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.rate_limit_retry_delay_seconds = rate_limit_retry_delay_seconds
        self.max_rate_limit_retries = max_rate_limit_retries

    def register_tool(self, tool_name, tool_func):
        """
        Register a LangChain tool. 'tool_name' is your key (used by ArticleProcessor
        and ExtractorUtils). The tool's *declared* name (from @tool) may differ;
        we detect and remember it so tool_choice works reliably.
        """
        self.tools[tool_name] = tool_func
        declared = getattr(tool_func, "name", None)
        if not declared:
            declared = getattr(tool_func, "__name__", tool_name)
        self._tool_declared_names[tool_name] = declared

    def extract(self, text, tool_name):
        """
        Run GPT-5 with exactly one bound tool and force it to call that tool.
        'text' is the fully formatted prompt string from ArticleProcessor.
        """
        tool_func = self.tools.get(tool_name)
        if not tool_func:
            raise ValueError(f"Tool {tool_name} is not registered.")

        declared_name = self._tool_declared_names.get(tool_name, tool_name)

        llm_with_tool = self.llm.bind_tools(
            [tool_func],
            tool_choice=declared_name,
        )

        response: AIMessage = llm_with_tool.invoke(text)
        return ExtractorUtils.process_response(tool_name, response)

    def extract_all(self, article):
        """
        Run all registered tools on the same prompt in parallel. On OpenAI rate limit
        (429), logs the event, waits (Retry-After or configured default), then retries
        with reduced concurrency. Rate-limit events are logged.
        """
        tool_names = list(self.tools.keys())
        if not tool_names:
            return {}

        current_workers = self.max_workers
        retries = 0
        results = {}

        while tool_names:
            batch_results = {}
            failed = []
            rate_limit_hit = False
            rate_limit_exc = None

            with ThreadPoolExecutor(max_workers=current_workers) as executor:
                future_to_tname = {
                    executor.submit(self.extract, article, tname): tname
                    for tname in tool_names
                }
                for future in as_completed(future_to_tname):
                    tname = future_to_tname[future]
                    try:
                        batch_results[tname] = future.result()
                    except Exception as e:
                        if _is_rate_limit_error(e):
                            rate_limit_hit = True
                            rate_limit_exc = e
                            failed.append(tname)
                        else:
                            raise

            for tname, value in batch_results.items():
                results[tname] = value

            if not rate_limit_hit:
                return results

            retries += 1
            wait_seconds = _get_retry_after_seconds(
                rate_limit_exc, self.rate_limit_retry_delay_seconds
            )
            logger.warning(
                "OpenAI rate limit (429) hit (tools %s). Waiting %ds then retrying with reduced concurrency (retry %d/%d).",
                failed,
                wait_seconds,
                retries,
                self.max_rate_limit_retries,
            )
            time.sleep(wait_seconds)

            if retries >= self.max_rate_limit_retries:
                raise rate_limit_exc

            next_workers = max(current_workers // 2, self.min_workers)
            logger.info(
                "Reducing tool concurrency from %d to %d.",
                current_workers,
                next_workers,
            )
            current_workers = next_workers
            tool_names = failed
