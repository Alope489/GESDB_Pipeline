from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from .utils.extractor_utils import ExtractorUtils


class Extractor:
    def __init__(self, api_key):
        # GPT-5 via Responses API; message shape is AIMessage with .tool_calls
        self.llm = ChatOpenAI(
            model="gpt-5",
            api_key=api_key,
            temperature=0.0,
            use_responses_api=True,
            output_version="responses/v1",
        )
        # maps your registry key (e.g., "contact_info") -> tool object
        self.tools = {}
        # maps your registry key -> tool's declared name (e.g., "extract_contact_info")
        self._tool_declared_names = {}

    def register_tool(self, tool_name, tool_func):
        """
        Register a LangChain tool. 'tool_name' is your key (used by ArticleProcessor
        and ExtractorUtils). The tool's *declared* name (from @tool) may differ;
        we detect and remember it so tool_choice works reliably.
        """
        self.tools[tool_name] = tool_func
        declared = getattr(tool_func, "name", None)  # set by @tool
        if not declared:
            # fallback to function __name__ or your key
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

        # Bind only this tool and REQUIRE its use (schema-enforced).
        llm_with_tool = self.llm.bind_tools(
            [tool_func],
            tool_choice=declared_name,  # <-- force the declared tool name
            # strict=True                 # <-- enforce tool schema
        )

        # IMPORTANT: we pass 'text' through as-is; ArticleProcessor already built it.
        response: AIMessage = llm_with_tool.invoke(text)

        # Hand off to your existing router/processor (no change here yet).
        return ExtractorUtils.process_response(tool_name, response)

    def extract_all(self, article):
        """
        Iteratively run all registered tools on the same prompt string or article blob.
        ArticleProcessor currently passes a single prompt string, which is fine.
        """
        results = {}
        for tname in self.tools.keys():
            results[tname] = self.extract(article, tname)
        return results
