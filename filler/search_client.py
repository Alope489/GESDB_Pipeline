"""Web search client: SerpAPI implementation. Reads SEARCH_API_KEY from env (load dotenv before use)."""
import logging
import os
import subprocess
import sys
from typing import Protocol, runtime_checkable

_log = logging.getLogger(__name__)


@runtime_checkable
class SearchResult(Protocol):
    title: str
    snippet: str


def search(query: str, api_key: str | None = None, num: int = 10, debug: bool = False) -> list[dict]:
    """
    Run a web search and return a list of result dicts with "title" and "snippet".
    Uses SerpAPI (google-search-results). If api_key is missing or search fails, returns [].
    When debug is True, log SerpAPI errors and exceptions.
    """
    key = api_key or os.environ.get("SEARCH_API_KEY")
    if not key or not key.strip():
        if debug:
            _log.warning("search: SEARCH_API_KEY missing or empty")
        return []
    try:
        from serpapi import GoogleSearch
    except ModuleNotFoundError:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "google-search-results"],
                capture_output=True,
                timeout=120,
                check=False,
            )
            from serpapi import GoogleSearch
        except Exception:
            raise ModuleNotFoundError(
                "SerpAPI client not installed. Install it with: pip install google-search-results"
            ) from None
    try:
        search = GoogleSearch({"q": query, "api_key": key, "num": num})
        result = search.get_dict()
        if result.get("error"):
            if debug:
                _log.warning("search: SerpAPI error: %s", result.get("error"))
            return []
        organic = result.get("organic_results") or []
        return [{"title": r.get("title") or "", "snippet": r.get("snippet") or ""} for r in organic]
    except Exception as e:
        if debug:
            _log.warning("search: exception %s: %s", type(e).__name__, e)
        return []
