"""LLM extraction from search snippets: given snippets + field descriptions, return dict of field -> value or None."""
import json
import logging
import os
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

_log = logging.getLogger(__name__)


def extract_from_snippets(
    snippets: list[dict],
    field_descriptions: dict[str, str],
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    debug: bool = False,
) -> dict[str, Any]:
    """
    Ask the LLM to extract the given fields from search result snippets.
    field_descriptions: { "Field Name": "description and expected format" }.
    Returns { "Field Name": extracted_value or None }. If parsing fails, returns all None.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key or not snippets or not field_descriptions:
        if debug and (not key or not key.strip()):
            _log.warning("extract_from_snippets: OPENAI_API_KEY missing or empty")
        return {f: None for f in field_descriptions}
    text = "\n\n".join(
        f"[{i+1}] {s.get('title', '')}\n{s.get('snippet', '')}" for i, s in enumerate(snippets[:15])
    )
    fields_block = "\n".join(f"- {k}: {v}" for k, v in field_descriptions.items())
    prompt = f"""You are extracting structured data about an energy storage project from web search snippets.
Extract only the requested fields. Use the exact field names as keys. If a value is not found or uncertain, use null.
Return a single JSON object with no markdown or explanation. Dates must be MM-DD-YYYY. Numbers as numbers, not strings.

Fields to extract:
{fields_block}

Search results:
{text}

JSON object:"""
    try:
        llm = ChatOpenAI(model=model, api_key=key, temperature=0.0)
        response = llm.invoke([HumanMessage(content=prompt)])
        body = response.content if hasattr(response, "content") else str(response)
        body = re.sub(r"^```\w*\n?", "", re.sub(r"\n?```\s*$", "", body.strip()))
        out = json.loads(body)
        return {k: out.get(k) for k in field_descriptions}
    except Exception as e:
        if debug:
            _log.warning("extract_from_snippets: exception %s: %s", type(e).__name__, e)
        return {f: None for f in field_descriptions}
