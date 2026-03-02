"""Fill Project Details group from web search."""
import logging

from .helpers import get_empty_or_unvalidated_fields, is_empty, location_string, is_acceptable_text, is_acceptable_value
from .field_descriptions import get_descriptions_for_fields
from . import search_client
from . import llm_extract
from .attributions import append_attribution

SKIP_KEYS = frozenset({"ID", "Applications"})
GROUP_NAME = "Project Details"
_log = logging.getLogger(__name__)


def fill_group(
    record: dict,
    record_index: int,
    attributions: list[dict],
    api_key_search: str | None = None,
    api_key_openai: str | None = None,
    validation_df=None,
    debug: bool = False,
) -> None:
    """Find empty or validation-flagged Project Details fields, search, extract with LLM, update record and attributions."""
    empty = [
        k for k in get_empty_or_unvalidated_fields(record, record_index, GROUP_NAME, validation_df)
        if k not in SKIP_KEYS
    ]
    if not empty:
        return
    if debug:
        _log.info("%s: record %s, %s fields to fill", GROUP_NAME, record_index, len(empty))
    loc = location_string(record)
    descriptions = get_descriptions_for_fields(empty)
    query = f"{loc} " + " ".join(descriptions.values())
    snippets = search_client.search(query, api_key=api_key_search, debug=debug)
    if not snippets:
        if debug:
            _log.info("%s: search skipped or no snippets", GROUP_NAME)
        append_attribution(attributions, record.get("ID", record_index), [], note="no snippets")
        return
    if debug:
        _log.info("%s: %s snippets", GROUP_NAME, len(snippets))
    extracted = llm_extract.extract_from_snippets(snippets, descriptions, api_key=api_key_openai, debug=debug)
    if debug:
        _log.info("%s: %s non-null extractions", GROUP_NAME, sum(1 for v in extracted.values() if v is not None))
    fields_filled = []
    for k, v in extracted.items():
        if v is None:
            continue
        if not is_acceptable_text(k) or not is_acceptable_value(v):
            continue
        if k not in record or is_empty(record.get(k), k):
            record[k] = v
            fields_filled.append({"field": k, "value": v, "source": "web_search"})
    if fields_filled:
        append_attribution(attributions, record.get("ID", record_index), fields_filled)
    elif empty:
        append_attribution(attributions, record.get("ID", record_index), [], note="no values extracted")
