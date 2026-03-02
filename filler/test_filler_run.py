"""
Run the filler chain for one record and one category; print results or errors at each step.
Run from project root: python -m filler.test_filler_run
"""
import json
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from filler.config import PROCESSED_DATA_PATH
from filler.helpers import get_empty_or_unvalidated_fields, location_string
from filler.field_descriptions import get_descriptions_for_fields
from filler import search_client
from filler import llm_extract
from filler.validation_loader import load_validation_status

SKIP = {"ID", "Applications"}


def main():
    print("=== 1. Env and paths ===")
    env_path = PROJECT_ROOT / ".env"
    print(f"  .env exists: {env_path.exists()}")
    search_key = os.environ.get("SEARCH_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    print(f"  SEARCH_API_KEY: {'set' if (search_key and search_key.strip()) else 'MISSING'}")
    print(f"  OPENAI_API_KEY: {'set' if (openai_key and openai_key.strip()) else 'MISSING'}")
    print(f"  processed_data exists: {PROCESSED_DATA_PATH.exists()}")

    if not PROCESSED_DATA_PATH.exists():
        print("  Abort: no processed_data.json")
        return
    with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) < 2:
        print("  Abort: need at least 2 records")
        return
    record = data[1]
    record_index = 1
    print(f"  Using record index {record_index} (ID={record.get('ID')})")

    print("\n=== 2. Empty / validation fields (Project Details) ===")
    validation_df = load_validation_status()
    print(f"  validation loaded: {validation_df is not None} (rows: {len(validation_df) if validation_df is not None else 0})")
    to_fill = [
        k for k in get_empty_or_unvalidated_fields(record, record_index, "Project Details", validation_df)
        if k not in SKIP
    ]
    print(f"  fields to fill: {len(to_fill)} -> {to_fill}")
    if not to_fill:
        print("  Abort: no fields to fill")
        return

    print("\n=== 3. Search ===")
    loc = location_string(record)
    descriptions = get_descriptions_for_fields(to_fill)
    query = f"{loc} " + " ".join(descriptions.values())
    print(f"  query (first 120 chars): {query[:120]}...")
    try:
        snippets = search_client.search(query, api_key=search_key, debug=True)
        print(f"  snippets returned: {len(snippets)}")
        if not snippets:
            print("  Abort: no snippets (check SEARCH_API_KEY or SerpAPI; run with debug for details)")
            return
        print(f"  first snippet title: {(snippets[0].get('title') or '')[:60]}...")
    except Exception as e:
        print(f"  Search exception: {e}")
        return

    print("\n=== 4. LLM extract ===")
    try:
        extracted = llm_extract.extract_from_snippets(snippets, descriptions, api_key=openai_key, debug=True)
        non_null = {k: v for k, v in extracted.items() if v is not None}
        print(f"  extracted non-null: {len(non_null)} -> {list(non_null.keys())}")
        for k, v in list(non_null.items())[:3]:
            print(f"    {k}: {v}")
    except Exception as e:
        print(f"  LLM exception: {e}")
        return

    print("\n=== Done: chain completed ===")


if __name__ == "__main__":
    main()
