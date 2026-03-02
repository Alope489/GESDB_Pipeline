"""Load/save filler attributions: which fields were filled from web search per record."""
import json
import re
from pathlib import Path

from .config import ATTRIBUTIONS_PATH
from .helpers import is_acceptable_text, is_acceptable_value


def _set_by_path(record: dict, path: str, value) -> None:
    """Set record[path] = value. Path can be 'Key' or 'Subsystems[0].Storage Device.Storage Capacity (kWh)'."""
    parts = [p.strip() for p in path.split(".")]
    if not parts:
        return
    obj = record
    for part in parts[:-1]:
        m = re.match(r"^(\w+)\[(\d+)\]$", part)
        if m:
            key, idx = m.group(1), int(m.group(2))
            obj = obj[key][idx]
        else:
            obj = obj[part]
    obj[parts[-1]] = value


def apply_attributions_to_data(data: list[dict], attributions: list[dict]) -> None:
    """Apply every fields_filled from attributions into data. Mutates data in place."""
    id_to_index = {}
    for i, rec in enumerate(data):
        id_to_index[rec.get("ID", i + 1)] = i
        id_to_index[i] = i
    for entry in attributions:
        record_id = entry.get("record_id")
        idx = id_to_index.get(record_id)
        if idx is None and record_id is not None:
            try:
                idx = id_to_index.get(int(record_id))
            except (TypeError, ValueError):
                pass
        if idx is None:
            continue
        record = data[idx]
        for item in entry.get("fields_filled") or []:
            field = item.get("field")
            val = item.get("value")
            if field is None:
                continue
            if not is_acceptable_text(field):
                continue
            if not is_acceptable_value(val):
                continue
            try:
                _set_by_path(record, field, val)
            except (KeyError, IndexError, TypeError):
                pass


def load_attributions(path: Path | None = None) -> list[dict]:
    p = path or ATTRIBUTIONS_PATH
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_attributions(attributions: list[dict], path: Path | None = None) -> None:
    p = path or ATTRIBUTIONS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(attributions, f, indent=2, ensure_ascii=False)


def append_attribution(
    attributions: list[dict],
    record_id: int | str,
    fields_filled: list[dict],
    subsystem_index: int | None = None,
    note: str | None = None,
) -> None:
    """Append one record's attribution. fields_filled = [{"field": str, "value": str|number, "source": "web_search"}, ...]. Use note when attempted but nothing filled (e.g. 'no snippets', 'no values extracted')."""
    entry = {"record_id": record_id, "fields_filled": fields_filled, "source": "web_search"}
    if subsystem_index is not None:
        entry["subsystem_index"] = subsystem_index
    if note:
        entry["note"] = note
    attributions.append(entry)
