"""Shared helpers: is_empty check, encoding validation, and building search context from record."""
import re

from .config import CATEGORY_KEYS, FIELDS_REQUIRE_POSITIVE

# Mojibake indicators (UTF-8 misinterpreted as Latin-1/Windows-1252)
_MOJIBAKE_PATTERN = re.compile(
    r"\uFFFD|Ãƒ|Ã¢|Ã©|Ã¨|Ã |Â°.*Ã|Ã†|Ã‚Â|Ã¢â‚¬|Ã¢â€šÂ¬|Ã…Â¡|Ã¢â‚¬Å¡|Ãƒâ€š"
)


def is_acceptable_text(s: str) -> bool:
    """Return False if the string is None, contains replacement char, mojibake patterns, or invalid UTF-8."""
    if s is None or not isinstance(s, str):
        return False
    if "\uFFFD" in s:
        return False
    if _MOJIBAKE_PATTERN.search(s):
        return False
    try:
        s.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return True


def is_acceptable_value(value) -> bool:
    """Return True for None, numbers, bool; for str use is_acceptable_text."""
    if value is None:
        return True
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, str):
        return is_acceptable_text(value)
    return False


# Placeholder strings treated as empty (case-insensitive). None/null are always empty.
_EMPTY_STRINGS = frozenset({"", "n/a", "na", "none", "-", "--", "null", "tbd", "tba", "n.a.", "n.a"})


def is_empty(value, field_name: str) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        if value.strip().lower() in _EMPTY_STRINGS:
            return True
        if value.strip() == "":
            return True
    if isinstance(value, (int, float)) and value == 0 and field_name in FIELDS_REQUIRE_POSITIVE:
        return True
    return False


def get_empty_fields_in_group(record: dict, category: str) -> list[str]:
    keys = CATEGORY_KEYS.get(category, [])
    return [k for k in keys if k in record and is_empty(record.get(k), k)]


def get_empty_or_unvalidated_fields(
    record: dict,
    record_index: int,
    category: str,
    validation_df=None,
) -> list[str]:
    """Fields to try to fill: empty (by value) or Unvalidated with a fillable error code."""
    empty = get_empty_fields_in_group(record, category)
    if validation_df is None:
        return empty
    from .validation_loader import get_fields_to_fill_from_validation
    from_validation = get_fields_to_fill_from_validation(
        record_index, category, validation_df, set(record.keys())
    )
    seen = set(empty)
    for k in from_validation:
        if k not in seen and k in record:
            seen.add(k)
            empty = empty + [k]
    return empty


def location_string(record: dict) -> str:
    """Build project + location string for search query."""
    name = record.get("Project/Plant Name") or record.get("URL") or "energy storage project"
    if isinstance(name, str):
        name = name.strip()
    if not name:
        name = "energy storage project"
    parts = [name]
    for key in ("Country", "City", "State/Province", "State/Province/Territory"):
        if key in record and record.get(key) and str(record[key]).strip():
            parts.append(str(record[key]).strip())
    return " ".join(parts)
