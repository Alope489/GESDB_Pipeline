"""Smoke tests for pipeline helpers (no Streamlit)."""
import pandas as pd

def test_parse_validation_cell():
    from pipeline import _parse_validation_cell
    assert _parse_validation_cell("[{'flag': 'Validated'}]") == [{"flag": "Validated"}]
    assert _parse_validation_cell(None) == []
    assert _parse_validation_cell("") == []

def test_row_fully_validated():
    from pipeline import _row_fully_validated
    row = pd.Series({"Index": 0, "ID": 1, "A": "[{'flag': 'Validated'}]"})
    assert _row_fully_validated(row)
    row2 = pd.Series({"Index": 0, "ID": 1, "A": "[{'flag': 'Unvalidated'}]"})
    assert not _row_fully_validated(row2)

def test_category_has_validation_errors():
    from pipeline import _category_has_validation_errors
    row = pd.Series({"Index": 0, "A": "[{'flag': 'Unvalidated'}]", "B": "[{'flag': 'Validated'}]"})
    assert _category_has_validation_errors(row, ["A"])
    assert not _category_has_validation_errors(row, ["B"])
    assert not _category_has_validation_errors(None, ["A"])
