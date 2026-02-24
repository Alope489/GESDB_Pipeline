import streamlit as st
import pandas as pd
import json
import re
import os
import requests
import base64
import time
from copy import deepcopy
from pathlib import Path
from article_scraper import collect_articles
from article_processor import ArticleProcessor  # For step 2
from validation.validation_script import run_validation  # For step 3
import data_insert  # For step 4

# Placeholder for the pipeline tab layout
SITE_CONFIGS = [
    {
        'base_url': 'https://www.power-technology.com/projects/',
        'link_selector': 'a[href^="https://www.power-technology.com/projects/"]',
        'urls_file': 'data/input/urls_power_technology.txt',
        'articles_output_file': 'data/input/articles_power_technology.json',
        'processed_urls_file': 'data/input/processed_urls.txt',
        'url_prefix': 'https://www.power-technology.com/projects/'
    },
    # Add additional configurations if needed
]

# File path for the processed data
DATA_FILE_PATH = "data/output/processed_data.json"
VALIDATION_STATUS_FILE = "validation/output/validation_status.csv"

# Load JSON data
@st.cache_data
def load_data(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        st.error("Error decoding JSON file.")
        return None

# Load validation status data
def load_validation_status(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Validation status file not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error reading validation status file: {e}")
        return None

# Group keys into logical categories
def categorize_data(record):
    categories = {
        "Project Details": [
            "ID", "Project/Plant Name", "Status", "Rated Power (kW)",
            "Storage Capacity (kWh)", "Applications", "Paired Grid Resources",
            "Description/Notes", "URL", "Latest Update Date"
        ],
        "Location Information": [
            "Country", "City", "State/Province/Territory", "County",
            "Street Address", "Postal Code", "Latitude", "Longitude"
        ],
        "Date Information": [
            "Announced Date", "Constructed Date", "Commissioned Date",
            "Decommissioned Date"
        ],
        "Contact Information": [
            "Contact Information: Name", "Contact Information: Email Address",
            "Contact Information: Phone Number"
        ],
        "Grid & Utility": [
            "Grid Interconnection Level",
            "Interconnection Type",
            "ISO/RTO",
            "System Operator",
            "Utility Type",
        ],
        "Ownership and Financials": [
            "Ownership Model", "Owner(s)", "Capital Expenditure - CAPEX (USD)",
            "Annual Operational Cost - OPEX (USD)", "Debt Provider",
            "Funding Source 1", "Funding Source Amount 1 (USD)",
            "Funding Source 2", "Funding Source Amount 2 (USD)",
            "Funding Source 3", "Funding Source Amount 3 (USD)"
        ],
        "Subsystems": ["Subsystems"]
    }
    grouped_data = {category: {} for category in categories.keys()}

    for category, keys in categories.items():
        for key in keys:
            if key in record:
                grouped_data[category][key] = record[key]

    return grouped_data
def _slug(s: str) -> str:
    # safe, stable widget keys
    return re.sub(r'[^0-9a-zA-Z_]+', '_', str(s))

def _slug_filename(x) -> str:
    # simple, safe filename: record_123.json, etc.
    s = str(x)
    return re.sub(r'[^0-9a-zA-Z._-]+', '_', s)
def save_github_token_to_secrets(token: str) -> tuple[bool, str]:
    """
    Save/overwrite github_token in a local .streamlit/secrets.toml.
    Tries project path first, then user home. Returns (ok, message).
    """
    token_escaped = token.replace('"', '\\"')
    candidates = [
        Path(".streamlit") / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ]

    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            text = ""
            if path.exists():
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    text = ""

            if re.search(r"(?m)^\s*github_token\s*=", text):
                # overwrite existing line
                new_text = re.sub(
                    r'(?m)^\s*github_token\s*=.*$',
                    f'github_token = "{token_escaped}"',
                    text
                )
            else:
                # append new key
                new_text = (text.rstrip() + ("\n" if text and not text.endswith("\n") else "")) + f'github_token = "{token_escaped}"\n'

            path.write_text(new_text, encoding="utf-8")
            return True, f"PAT saved to {path}"
        except Exception as e:
            # try next candidate
            last_err = f"{type(e).__name__}: {e}"

    return False, f"Unable to write secrets.toml. Last error: {last_err}"

def github_upsert_content(*, token: str, owner: str, repo: str, branch: str,
                          path_in_repo: str, content_bytes: bytes,
                          commit_message: str,
                          committer_name: str = "GESDB Pipeline",
                          committer_email: str = "no-reply@gesdb.local"):
    """
    Creates or updates a single file via GitHub Contents API.
    Returns (ok: bool, detail: str)
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    # Check if file exists to get sha
    sha = None
    r_get = requests.get(url, headers=headers, params={"ref": branch})
    if r_get.status_code == 200:
        try:
            sha = r_get.json().get("sha")
        except Exception:
            sha = None
    elif r_get.status_code not in (404,):
        return False, f"Lookup failed ({r_get.status_code}): {r_get.text}"

    b64 = base64.b64encode(content_bytes).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": b64,
        "branch": branch,
        "committer": {"name": committer_name, "email": committer_email},
    }
    if sha:
        payload["sha"] = sha  # required to update existing file

    r_put = requests.put(url, headers=headers, json=payload)
    if r_put.status_code in (200, 201):
        return True, "Committed"
    return False, f"Commit failed ({r_put.status_code}): {r_put.text}"

def push_validated_to_github(validated_records, *, owner, repo, branch,
                             dir_path_in_repo, token, commit_prefix="Add/Update record"):
    """
    Push all validated_records as JSON files to GitHub.
    Returns list of results per record: {"id": id, "file": path, "ok": bool, "detail": str}
    """
    results = []
    for rec in validated_records:
        rid = rec.get("ID", "unknown")
        fname = _slug_filename(f"record_{rid}.json")
        path_in_repo = f"{dir_path_in_repo.rstrip('/')}/{fname}"
        content = json.dumps(rec, indent=2, ensure_ascii=False).encode("utf-8")
        msg = f"{commit_prefix}: ID {rid}"

        ok, detail = github_upsert_content(
            token=token, owner=owner, repo=repo, branch=branch,
            path_in_repo=path_in_repo, content_bytes=content, commit_message=msg
        )
        results.append({"id": rid, "file": path_in_repo, "ok": ok, "detail": detail})
        time.sleep(0.2)  # tiny pause to be nice to the API
    return results

def _is_list_of_dicts(v):
    return isinstance(v, list) and all(isinstance(x, dict) for x in v)

def edit_value_widget(label: str, value, widget_key: str):
    """
    Renders the right editor for a value and returns the possibly-edited value.
    Guarded to avoid StreamlitMixedNumericTypesError by matching step/value types.
    """

    # small helper for selectboxes that preserve current custom values
    def _select_with_current(_label, options, current, key):
        base = [""] + options  # allow blank/None
        if current and current not in base:
            base = [current] + [o for o in base if o != current]
        idx = base.index(current) if current in base else 0
        out = st.selectbox(_label, base, index=idx, key=key)
        return out if out != "" else None

    # Special dropdowns for a couple of grid/utility fields
    if "Grid Interconnection Level" in label:
        return _select_with_current(
            "Grid Interconnection Level",
            ["Transmission", "Distribution", "Customer (behind-the-meter)"],
            value,
            widget_key,
        )

    if "Interconnection Type" in label:
        return _select_with_current(
            "Interconnection Type",
            ["AC", "DC", "Hybrid"],
            value,
            widget_key,
        )
        
    # Booleans
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=widget_key)

    # Integers
    if isinstance(value, int):
        new_val = st.number_input(label, value=int(value), step=1, key=widget_key)
        return int(new_val)

    # Floats
    if isinstance(value, float):
        new_val = st.number_input(label, value=float(value), step=0.1, format="%.6f", key=widget_key)
        return float(new_val)

    # List[Dict] → table editor (your Subsystems)
    if label == "Subsystems" and isinstance(value, list) and all(isinstance(x, dict) for x in value):
        df = pd.DataFrame(value) if value else pd.DataFrame([{}])
        edited_df = st.data_editor(
            df, use_container_width=True, num_rows="dynamic", key=widget_key
        )
        return edited_df.fillna("").to_dict(orient="records")

    # Any other list/dict → JSON text area
    if isinstance(value, (list, dict)):
        current = json.dumps(value, indent=2, ensure_ascii=False)
        text = st.text_area(label, value=current, height=200, key=widget_key)
        try:
            return json.loads(text) if text.strip() else value
        except json.JSONDecodeError:
            st.warning("Invalid JSON; keeping previous value.")
            return value

    # Fallback: strings / None
    return st.text_input(label, value="" if value is None else str(value), key=widget_key)



# Render record details by categories with validation
def display_record_grouped(record, record_id, edit_mode: bool = True):
    grouped_data = categorize_data(record)
    edited_record = deepcopy(record)

    # Initialize validation state for the record if not already done
    vs_key = f"validation_status_{record_id}"
    if vs_key not in st.session_state:
        st.session_state[vs_key] = {category: False for category in grouped_data}

    for category, fields in grouped_data.items():
        with st.expander(category, expanded=False):
            if fields:
                for key, value in fields.items():
                    label = f"**{key}:**"
                    wid_key = f"edit_{record_id}_{_slug(category)}_{_slug(key)}"
                    if edit_mode:
                        new_val = edit_value_widget(label, value, wid_key)
                        # write back into edited_record
                        edited_record[key] = new_val
                    else:
                        # read-only display (not used now, but handy)
                        if isinstance(value, (dict, list)):
                            st.markdown(label)
                            st.json(value, expanded=False)
                        else:
                            st.markdown(f"{label} {value if value is not None else 'N/A'}")
            else:
                st.write("No data available.")

            # Validation toggle (unchanged behavior)
            if st.session_state[vs_key][category]:
                if st.button(f"Unmark {category} as Validated", key=f"{record_id}_{category}_unmark"):
                    st.session_state[vs_key][category] = False
            else:
                if st.button(f"Mark {category} as Validated", key=f"{record_id}_{category}_mark"):
                    st.session_state[vs_key][category] = True

    # Overall validation state
    if all(st.session_state[vs_key].values()):
        st.success("This record is fully validated!")
        st.session_state[f"record_validated_{record_id}"] = True
    else:
        st.warning("Some categories are not validated yet.")
        st.session_state[f"record_validated_{record_id}"] = False

    return edited_record

def display_validated_records(data):
    st.title("Validated Records")

    validated_records = []
    for idx, record in enumerate(data):
        if st.session_state.get(f"record_validated_{idx}", False):
            validated_records.append(record)

    st.write(f"Total validated records: {len(validated_records)}")

    if validated_records:
        with st.expander("View validated records JSON"):
            for record in validated_records:
                st.markdown(f"### Record ID: {record.get('ID', 'Unknown')}")
                st.json(record)
    else:
        st.info("No records have been fully validated yet. You can still save your GitHub token below so you don’t have to paste it later.")

    st.markdown("---")
    st.subheader("Push validated records to GitHub")

    with st.form("github_push_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            owner = st.text_input("GitHub Owner / Org", value="your-org-or-user")
            repo = st.text_input("Repository Name", value="your-repo")
            branch = st.text_input("Branch", value="main")
            dir_path = st.text_input("Target directory in repo", value="data/exports")
        with col2:
            # Gracefully read a default from secrets if present; don’t crash if missing
            try:
                default_token = st.secrets.get("github_token", "")
            except Exception:
                default_token = ""
            token = st.text_input("GitHub Token (PAT)", value=default_token, type="password")
            commit_prefix = st.text_input("Commit message prefix", value="Add/Update record")
            save_pat = st.checkbox("Save/overwrite this PAT to .streamlit/secrets.toml")

        # Allow selecting a subset to push (still shown even if empty)
        ids_available = [rec.get("ID", None) for rec in validated_records]
        ids_available = [i for i in ids_available if i is not None]
        selected_ids = st.multiselect(
            "Select record IDs to push (leave empty to push ALL validated)",
            ids_available
        )

        submitted = st.form_submit_button("Push to GitHub", type="primary")

    if submitted:
        if not token:
            st.error("Please provide a GitHub token (PAT).")
            return

        # Save/overwrite PAT to secrets if requested
        if save_pat:
            ok, msg = save_github_token_to_secrets(token)
            (st.success if ok else st.error)(msg)

        # Compute which records to push
        if selected_ids:
            to_push = [r for r in validated_records if r.get("ID") in selected_ids]
        else:
            to_push = validated_records

        if not to_push:
            st.info("No validated records to push yet. Validate some records first, then try again.")
            return

        with st.spinner(f"Pushing {len(to_push)} record(s) to GitHub…"):
            results = push_validated_to_github(
                to_push,
                owner=owner,
                repo=repo,
                branch=branch,
                dir_path_in_repo=dir_path,
                token=token,                   # uses the entered token immediately
                commit_prefix=commit_prefix,
            )

        ok_count = sum(r["ok"] for r in results)
        st.success(f"Pushed {ok_count}/{len(results)} file(s).")
        for r in results:
            icon = "✅" if r["ok"] else "❌"
            st.write(f"{icon} ID {r['id']} → {r['file']} — {r['detail']}")

        st.caption("Tip: checking “Save/overwrite PAT” writes it to .streamlit/secrets.toml so it’s prefilled next time.")



# View Records Tab Functionality (Merged with Validation)
def view_records_tab():
    st.header("View and Validate Records")

    # Refresh Data Button
    if st.button("Refresh Data", key="refresh_view_records"):
        st.cache_data.clear()

    # Load processed data and (optionally) validation status
    data = load_data(DATA_FILE_PATH)
    validation_status = load_validation_status(VALIDATION_STATUS_FILE)

    if data is not None and isinstance(data, list) and len(data) > 0:
        ids = [item.get("ID", f"Record {idx}") for idx, item in enumerate(data)]
        selected_index = st.selectbox(
            "Select Record", range(len(ids)), format_func=lambda x: ids[x]
        )

        selected_record = deepcopy(data[selected_index])
        st.markdown(f"### Record ID: {ids[selected_index]}")

        # Editable grouped UI → returns the edited copy
        edited_record = display_record_grouped(selected_record, selected_index, edit_mode=True)

        # Save / Revert buttons
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Save Changes to This Record", type="primary"):
                try:
                    # Write back to in-memory dataset
                    data[selected_index] = edited_record

                    # Persist to file (overwrite in place)
                    Path(DATA_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
                    with open(DATA_FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    st.cache_data.clear()  # refresh cached loaders
                    st.success("Saved changes to processed_data.json.")
                    st.toast("Record saved.")
                except Exception as e:
                    st.error(f"Error saving changes: {e}")

        with c2:
            if st.button("Revert Unsaved Changes"):
                st.info("Reverted to last saved version on disk.")
                st.rerun()

        # Validation Errors
        st.subheader("Validation Errors")

        val_row = None
        if validation_status is not None:
            try:
                if hasattr(validation_status, "empty") and not validation_status.empty:
                    # Prefer matching by ID if present
                    rec_id = selected_record.get("ID", None)
                    if rec_id is not None and "ID" in validation_status.columns:
                        match = validation_status[validation_status["ID"] == rec_id]
                        if not match.empty:
                            val_row = match.iloc[0]

                    # Fallback to positional index if within bounds
                    if val_row is None and selected_index < len(validation_status):
                        val_row = validation_status.iloc[selected_index]
            except Exception as e:
                st.info(f"Unable to read validation row: {e}")

        with st.expander("View Validation Errors"):
            if val_row is not None:
                for col, val in val_row.items():
                    st.markdown(f"**{col}:** {val}")
            else:
                st.write("No validation data for this record yet.")

        # Download current (possibly edited) record as JSON
        st.download_button(
            label="Download Record as JSON",
            data=json.dumps(edited_record, indent=4, ensure_ascii=False),
            file_name=f"record_{ids[selected_index]}.json",
            mime="application/json"
        )
    else:
        st.error("No data available to display.")


# Pipeline Tab Functionality
def pipeline_tab():
    st.header("Pipeline Execution")

    with st.expander("Step 1: Collect Articles"):
        use_default_config = st.checkbox("Use Default Configuration", value=True)

        if not use_default_config:
            base_url = st.text_input("Base URL", value="https://www.power-technology.com/projects/")
            link_selector = st.text_input("Link Selector", value="a[href^='https://www.power-technology.com/projects/']")
            urls_file = st.text_input("URLs File Path", value="data/input/urls_power_technology.txt")
            articles_output_file = st.text_input("Articles Output File Path", value="data/input/articles_power_technology.json")
            processed_urls_file = st.text_input("Processed URLs File Path", value="data/input/processed_urls.txt")
            url_prefix = st.text_input("URL Prefix", value="https://www.power-technology.com/projects/")

            custom_config = {
                'base_url': base_url,
                'link_selector': link_selector,
                'urls_file': urls_file,
                'articles_output_file': articles_output_file,
                'processed_urls_file': processed_urls_file,
                'url_prefix': url_prefix
            }
        else:
            custom_config = SITE_CONFIGS[0]

        if st.button("Run Article Collection"):
            st.write("Running article collection with the following configuration:")
            st.json(custom_config)
            st.write("WARNING: This process can take a very long time the first time it runs on a new URL.")

            try:
                collect_articles(custom_config)
                st.success("Article collection complete.")
            except Exception as e:
                st.error(f"Error during article collection: {e}")

    with st.expander("Step 2: Process Articles"):
        input_path = st.text_input("Input Path", value="data/input/articles_power_technology.json", key="input_path")
        output_path = st.text_input("Output Path", value="data/output/processed_data.json", key="output_path")
        limit = st.number_input("Processing Limit (0 for no limit)", min_value=0, value=1, step=1, key="limit")
        api_key = st.text_input("API Key", type="password", key="api_key")

        if st.button("Run Article Processing"):
            st.write("Running article processing with the following configuration:")
            st.json({"input_path": input_path, "output_path": output_path, "limit": limit, "api_key": "[HIDDEN]"})
            st.write("WARNING: This process can take a very long time.")

            try:
                processor = ArticleProcessor(input_path=input_path, output_path=output_path, api_key=api_key, limit=(None if limit == 0 else limit))
                processor.process_articles()
                st.success("Article processing complete.")
            except Exception as e:
                st.error(f"Error during article processing: {e}")

    with st.expander("Step 3: Validation"):
        if st.button("Run Validation"):
            st.write("Running validation step...")

            try:
                run_validation()
                st.success("Validation complete.")
            except Exception as e:
                st.error(f"Error during validation: {e}")

    with st.expander("Step 4: Data Insertion (experimental feature)"):
        if st.button("Run Data Insertion"):
            st.write("Running data insertion step...")

            try:
                data_insert.process_data()
                st.success("Data insertion complete.")
            except Exception as e:
                st.error(f"Error during data insertion: {e}")

# Main application
def main():
    st.title("Processed Data Viewer")
    st.markdown("### View and validate elements from processed data grouped by categories.")

    # Tabs for the application
    tabs = st.tabs(["Run Pipeline", "View Records", "Validated Records"])

    # Tab 1: Run pipeline
    with tabs[0]:
        pipeline_tab()

    # Tab 2: View records
    with tabs[1]:
        view_records_tab()

    # Tab 3: Validated records
    with tabs[2]:
        data = load_data(DATA_FILE_PATH)
        if data:
            display_validated_records(data)
        else:
            st.error("No data available to display.")

if __name__ == "__main__":
    main()