"""Run the filler on processed_data.json: load data, fill missing fields per group, save data and attributions."""
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .config import PROCESSED_DATA_PATH, ATTRIBUTIONS_PATH, PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()
from . import project_details
from . import location_information
from . import date_information
from . import contact_information
from . import grid_utility
from . import ownership_financials
from . import subsystems
from .attributions import save_attributions, apply_attributions_to_data, load_attributions
from .validation_loader import load_validation_status

GROUP_FILLERS = [
    project_details,
    location_information,
    date_information,
    contact_information,
    grid_utility,
    ownership_financials,
    subsystems,
]


def run(
    data_path: Path | None = None,
    attributions_path: Path | None = None,
    limit_records: int | None = None,
    start_record_index: int = 0,
    debug: bool = False,
) -> tuple[int, int, int]:
    """
    Load processed_data.json, run all group fillers on each record, save updated data and attributions.
    Returns (records_processed, records_modified, attributes_filled).
    When debug is True, enable INFO logging and log env path, keys, validation; fillers log search/LLM errors.
    Debug can also be enabled by setting env FILLER_DEBUG=1 (or true/yes).
    """
    debug = debug or (os.environ.get("FILLER_DEBUG") or "").strip().lower() in ("1", "true", "yes")
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()
    if debug:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    data_path = data_path or PROCESSED_DATA_PATH
    attributions_path = attributions_path or ATTRIBUTIONS_PATH
    if not data_path.exists():
        return 0, 0, 0
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return 0, 0, 0
    validation_df = load_validation_status()
    attributions = load_attributions(attributions_path)
    api_key_search = (os.environ.get("SEARCH_API_KEY") or "").strip()
    api_key_openai = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key_search and not api_key_openai:
        if debug:
            logging.getLogger(__name__).warning("run_filler: both SEARCH_API_KEY and OPENAI_API_KEY missing; no fill possible")
        return 0, 0, 0
    if debug:
        log = logging.getLogger(__name__)
        log.info("run_filler: .env path %s", PROJECT_ROOT / ".env")
        log.info("run_filler: SEARCH_API_KEY=%s OPENAI_API_KEY=%s", "set" if api_key_search else "MISSING", "set" if api_key_openai else "MISSING")
        log.info("run_filler: validation loaded rows=%s", len(validation_df) if validation_df is not None else 0)
    records_modified = 0
    start = max(0, start_record_index)
    end = min(start + (limit_records if limit_records else len(data)), len(data))
    for i in range(start, end):
        record = data[i]
        before = json.dumps(record, sort_keys=True)
        for filler in GROUP_FILLERS:
            filler.fill_group(
                record, i, attributions,
                api_key_search=api_key_search or None,
                api_key_openai=api_key_openai or None,
                validation_df=validation_df,
                debug=debug,
            )
        if json.dumps(record, sort_keys=True) != before:
            records_modified += 1
    apply_attributions_to_data(data, attributions)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    save_attributions(attributions, attributions_path)
    attributes_filled = sum(len(e["fields_filled"]) for e in attributions)
    return end - start, records_modified, attributes_filled
