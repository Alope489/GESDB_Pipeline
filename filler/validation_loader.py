"""Load validation status and derive which fields to fill from error codes."""
import ast
from pathlib import Path
from typing import Any

import pandas as pd

from .config import (
    VALIDATION_STATUS_PATH,
    FILLABLE_ERROR_CODES,
    VALIDATION_COLUMN_TO_RECORD_KEY,
    CATEGORY_KEYS,
)


def _parse_validation_cell(cell: Any) -> list:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    if isinstance(cell, list):
        return cell
    if isinstance(cell, str):
        s = cell.strip()
        if not s:
            return []
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return []
    return []


def load_validation_status(path: Path | None = None) -> Any:
    """Load validation_status.csv; return DataFrame or None if missing."""
    p = path or VALIDATION_STATUS_PATH
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        return None


def _record_key_for_column(col: str, record_keys: set) -> str | None:
    """Return the record key to use for this validation column (column or alias)."""
    if col in record_keys:
        return col
    return VALIDATION_COLUMN_TO_RECORD_KEY.get(col)


def get_fields_to_fill_from_validation(
    record_index: int,
    category: str,
    validation_df: Any,
    record_keys: set,
) -> list[str]:
    """Return list of record keys in this category that have Unvalidated + fillable error code."""
    if validation_df is None or record_index < 0 or record_index >= len(validation_df):
        return []
    category_keys = set(CATEGORY_KEYS.get(category, [])) & record_keys
    out = []
    row = validation_df.iloc[record_index]
    skip = {"Index"}
    for col in validation_df.columns:
        if col in skip:
            continue
        record_key = _record_key_for_column(col, record_keys)
        if not record_key or record_key not in category_keys:
            continue
        parsed = _parse_validation_cell(row[col])
        if not parsed or not isinstance(parsed[0], dict):
            continue
        entry = parsed[0]
        if entry.get("flag", "").lower() != "unvalidated":
            continue
        codes_str = entry.get("error_codes", "") or ""
        for c in codes_str.split(","):
            try:
                if int(c.strip()) in FILLABLE_ERROR_CODES:
                    out.append(record_key)
                    break
            except ValueError:
                continue
    return list(dict.fromkeys(out))

