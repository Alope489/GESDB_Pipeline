"""Fill Subsystems (Storage Device, Power Conversion System, Balance of System) from web search."""
import logging

from .helpers import location_string, is_empty
from .field_descriptions import get_descriptions_for_fields
from . import search_client
from . import llm_extract
from .attributions import append_attribution

GROUP_NAME = "Subsystems"
_log = logging.getLogger(__name__)


def _empty_subsystem_fields(subsystem: dict) -> list[tuple[str, str]]:
    """Return list of (section, key) for empty fields in one subsystem."""
    out = []
    for section in ("Storage Device", "Power Conversion System", "Balance of System"):
        block = subsystem.get(section)
        if not isinstance(block, dict):
            continue
        for k, v in block.items():
            if is_empty(v, k):
                out.append((section, k))
    return out


def fill_group(
    record: dict,
    record_index: int,
    attributions: list[dict],
    api_key_search: str | None = None,
    api_key_openai: str | None = None,
    validation_df=None,
    debug: bool = False,
) -> None:
    subsystems = record.get("Subsystems")
    if not isinstance(subsystems, list):
        return
    loc = location_string(record)
    for idx, sub in enumerate(subsystems):
        if not isinstance(sub, dict):
            continue
        empty_pairs = _empty_subsystem_fields(sub)
        if not empty_pairs:
            continue
        if debug:
            _log.info("%s: record %s subsystem %s, %s fields to fill", GROUP_NAME, record_index, idx, len(empty_pairs))
        # Use "Section - Key" as LLM field name so we can map back
        field_names = [f"{sec} - {k}" for sec, k in empty_pairs]
        descriptions = get_descriptions_for_fields(field_names)
        query = f"{loc} subsystem storage device power conversion system specifications " + " ".join(descriptions.values())
        snippets = search_client.search(query, api_key=api_key_search, debug=debug)
        if not snippets:
            if debug:
                _log.info("%s: search skipped or no snippets", GROUP_NAME)
            continue
        if debug:
            _log.info("%s: %s snippets", GROUP_NAME, len(snippets))
        extracted = llm_extract.extract_from_snippets(snippets, descriptions, api_key=api_key_openai, debug=debug)
        if debug:
            _log.info("%s: %s non-null extractions", GROUP_NAME, sum(1 for v in extracted.values() if v is not None))
        fields_filled = []
        for name, v in extracted.items():
            if v is None or " - " not in name:
                continue
            sec, key = name.split(" - ", 1)
            block = sub.get(sec)
            if not isinstance(block, dict) or key not in block:
                continue
            if is_empty(block.get(key), key):
                sub[sec][key] = v
                fields_filled.append({"field": f"Subsystems[{idx}].{sec}.{key}", "value": v, "source": "web_search"})
        if fields_filled:
            append_attribution(attributions, record.get("ID", record_index), fields_filled, subsystem_index=idx)
