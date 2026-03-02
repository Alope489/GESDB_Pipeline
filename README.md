# GESDB Pipeline

A pipeline for collecting articles, extracting structured GESDB data via LLM, validating records, filling missing fields with web search, and viewing or exporting validated records. The app provides a Streamlit UI (Run Pipeline, View Records, Validated Records) and an optional CLI via `main.py`.

## Table of contents

- [1. Installation](#1-installation)
- [2. Pipeline steps overview (brief)](#2-pipeline-steps-overview-brief)
- [3. View tab and Validated Records tab (brief)](#3-view-tab-and-validated-records-tab-brief)
- [4. Pipeline steps: detailed user guide](#4-pipeline-steps-detailed-user-guide)
- [5. View and Validate Records — full functionality](#5-view-and-validate-records--full-functionality)
- [6. Validated Records tab — full functionality](#6-validated-records-tab--full-functionality)
- [7. Technical analysis of backend code](#7-technical-analysis-of-backend-code)
- [8. Services overview](#8-services-overview)
- [9. Developer guide](#9-developer-guide)

---

## 1. Installation

### Dependencies

Install the required Python packages from the project root:

```bash
pip install -r requirements.txt
```

Main dependencies include: `python-dotenv`, `requests`, `beautifulsoup4`, `newspaper4k`, `lxml`, `openai`, `langchain_openai`, `langchain_community`, `langchain_core`, `langchain`, `pytest`, `validators`, `fuzzywuzzy[speedup]`, `pandas`, `numpy`, `python-dateutil`, `streamlit`, `tqdm`, and `pydantic`.

**Step 4 (Data Filler)** uses SerpAPI for web search. If you use the Data Filler step, install the SerpAPI client:

```bash
pip install google-search-results
```

If you see an error like "no module called serpapi" when running the Data Filler, run the command above in the same Python environment that runs the Streamlit app, then restart the app.

### Environment variables

Copy `.env.example` to `.env` in the project root and fill in your values. **Do not commit `.env`.**

| Variable | Required | Purpose |
|----------|----------|---------|
| **OPENAI_API_KEY** | Yes | Article processing (Step 2), LLM extraction in the filler (Step 4), and data_insert autofill. [OpenAI API keys](https://platform.openai.com/api-keys) |
| **GOOGLE_CSE_API_KEY** | No | Google Custom Search API key (used only by `data_insert` for autofill suggestions) |
| **GOOGLE_CSE_ENGINE_ID** | No | Google Custom Search Engine ID (used with the above) |
| **SEARCH_API_KEY** | For Step 4 | SerpAPI key for the Data Filler web search. If unset, the filler cannot run search (LLM-only fills may still run) |
| **SERPER_API_KEY** | No | Reserved for future use (e.g. alternative search provider) |
| **HTTP_PROXY** / **HTTPS_PROXY** | No | Optional corporate proxy |

The app loads `.env` automatically when you run `main.py` or the Streamlit pipeline.

### Running the app

- **Streamlit UI (recommended):** From the project root:

  ```bash
  streamlit run pipeline.py
  ```

  This opens the Processed Data Viewer with three tabs: **Run Pipeline**, **View Records**, and **Validated Records**.

- **CLI pipeline:** From the project root:

  ```bash
  python main.py
  ```

  This runs: article collection → article processing → validation → `data_insert.process_data()`. **Note:** As of this writing, `data_insert.process_data()` is not implemented; `data_insert` provides `process_record()` and a CLI that writes autofill suggestions to JSON. Running `main.py` will therefore fail at the final step unless that call is removed or `process_data()` is implemented. See the Technical analysis and Developer guide for details.

### Data paths

- **Input:** `data/input/` — e.g. `articles_power_technology.json`, `urls_power_technology.txt`, `processed_urls.txt`.
- **Output:** `data/output/` — `processed_data.json` (main pipeline output), `validated_records.json` (saved from the Validated Records tab), `filler_attributions.json` (filled-by-search attributions from Step 4).
- **Validation:** `validation/output/` — `validation_status.csv`, `validation_status.json`, `warning_messages.csv` (written by Step 3). Rules: `validation/data/gesdb_data_rules.csv`.

Create `data/input/` and `data/output/` as needed; the pipeline and Streamlit app use paths relative to the project root.

---

## 2. Pipeline steps overview (brief)

The **Run Pipeline** tab has four steps in order:

1. **Step 1: Collect Articles** — Scrapes article URLs and content from a configured site and saves raw articles to a JSON file.
2. **Step 2: Process Articles** — Turns raw articles into structured GESDB records using the LLM extractor and postprocessor; writes to `data/output/processed_data.json`.
3. **Step 3: Validation** — Runs validation rules on `processed_data.json` and writes `validation/output/validation_status.csv` (and `.json`), one row per record with Validated/Unvalidated per field.
4. **Step 4: Data Filler (web search)** — Fills missing, empty, or validation-flagged fields using web search (SerpAPI) and LLM extraction; updates `processed_data.json` and writes attributions to `filler_attributions.json`.

The main data file is **`data/output/processed_data.json`**. Validation output is **`validation/output/validation_status.csv`** (and `validation_status.json`).

---

## 3. View tab and Validated Records tab (brief)

- **View Records** (tab label). The page header inside this tab is **"View and Validate Records"**. Here you select a record by its ID, edit fields by category (each category in an expander), and mark each category as validated. When all categories are marked, the record can be set as fully validated; if the validation report has errors for that record, you are asked to confirm ("Mark as validated anyway" or "Cancel"). **Save Changes to This Record** and **Revert Unsaved Changes** appear only when there are unsaved edits (the app compares edited vs last-saved record and ignores minor widget differences like empty string vs `None`).

- **Validated Records** (tab label). This tab shows the list of records considered validated. The list is **merged** from: (1) records that pass the validation report (Step 3 CSV) when it exists and has the same row count as the data, and (2) records you marked as fully validated in View and Validate Records (session state). You can **Save validated records to JSON** (writes `data/output/validated_records.json`) and **Push to GitHub** (selected or all validated records as JSON files in a repo).

---

## 4. Pipeline steps: detailed user guide

This section describes each pipeline step from the user’s perspective: what it does, what the fields mean, and how to use it.

### Step 1: Collect Articles

**Purpose:** Scrape article URLs from a website and extract each article’s title, body text, and source URL. Results are saved to a JSON file and URLs are recorded so the same articles are not re-scraped.

**Use Default Configuration:** When checked (default), the step uses the built-in site configuration (e.g. power-technology.com). When unchecked, the form shows the following fields so you can customize the run:

| Field | Meaning | Typical value |
|-------|--------|----------------|
| **Base URL** | The webpage to scrape for article links (e.g. a project listing page). | `https://www.power-technology.com/projects/` |
| **Link Selector** | CSS selector that matches the `<a>` tags for article links. | `a[href^='https://www.power-technology.com/projects/']` |
| **URLs File Path** | File where discovered URLs are stored (and read to avoid duplicates). | `data/input/urls_power_technology.txt` |
| **Articles Output File Path** | JSON file where extracted article content (title, text, source) will be saved. | `data/input/articles_power_technology.json` |
| **Processed URLs File Path** | Used by the pipeline config; the scraper uses the URLs file above for duplicate tracking. | `data/input/processed_urls.txt` |
| **URL Prefix** | Only links starting with this prefix are collected. | `https://www.power-technology.com/projects/` |

**Button:** **Run Article Collection.** A warning is shown: the first run on a new URL can take a long time. On success, articles are written to the Articles Output File.

### Step 2: Process Articles

**Purpose:** Turn raw articles (from Step 1) into structured GESDB records. Each article is sent to the LLM extractor; the results are postprocessed into a single record per article and appended to the output file. Already-processed article URLs are skipped using the processed URLs file.

| Field | Meaning | Typical value |
|-------|--------|----------------|
| **Input Path** | JSON file of raw articles (usually the Articles Output File from Step 1). | `data/input/articles_power_technology.json` |
| **Output Path** | JSON file where structured records are written (main pipeline output). | `data/output/processed_data.json` |
| **Processing Limit (0 for no limit)** | Stop after this many articles. Use 0 to process all articles in the input file. | `1` or `0` |
| **API Key** | Your OpenAI API key (prefilled from `.env` if set). Required for the extractor. | (password field) |

**Button:** **Run Article Processing.** A warning notes that the process can take a long time. On success, the app sets “data stale” so the View Records and Validated Records tabs will show a message suggesting you click **Refresh Data** to load the latest output.

### Step 3: Validation

**Purpose:** Run validation rules on `data/output/processed_data.json`. Each record and field is checked against the GESDB rules (required, type, range, valid values, etc.). Results are written to `validation/output/validation_status.csv` and `validation_status.json` (one row per record; each cell is Validated or Unvalidated). Warnings (e.g. capacity-to-power ratio, date order) are written to `warning_messages.csv`.

There are no configuration fields. **Button:** **Run Validation.** After it completes, open the **View Records** or **Validated Records** tab to see validation status and any validation errors per record.

### Step 4: Data Filler (web search)

**Purpose:** Fill missing, empty, or validation-flagged fields in `processed_data.json` using web search (SerpAPI) and LLM extraction. For each record (in the range you set), the filler identifies fields to fill per category, builds a search query, fetches snippets, and uses the LLM to extract values; acceptable values are written back into the record and recorded in `filler_attributions.json`. Requires **SEARCH_API_KEY** (SerpAPI) and **OPENAI_API_KEY** in `.env`. If you see a “no module called serpapi” error, install: `pip install google-search-results`, then restart the Streamlit app.

| Field | Meaning | Typical value |
|-------|--------|----------------|
| **Start from record number (1 = first)** | 1-based index of the first record to process. | `1` |
| **Number of records to process (0 = all from start)** | How many records to process from the start index. 0 means “all from start.” | `0` or a positive number |
| **Debug (log steps to console)** | When checked, extra logging is printed to the console for troubleshooting. | Unchecked |

**Button:** **Run Data Filler.** The app shows a spinner and may warn that no attributes were filled if keys are missing or invalid. On success, cache is cleared and “data stale” is set so you can refresh View/Validated Records to see updates.

---

## 5. View and Validate Records — full functionality

The **View Records** tab shows the header **“View and Validate Records”**. Below is a complete description of every UI element and when buttons appear or disappear.

### Stale data

When the pipeline has just updated the data (after Step 2, 3, or 4), the app sets a “data stale” flag. In this tab you will see:

- A warning: **“Data may be stale. Click **Refresh Data** to load the latest from the pipeline.”**
- A button: **Refresh Data.** Clicking it clears the app’s data cache and clears the stale flag so the next load reads the latest `processed_data.json` and (if present) `validation_status.csv`.

### Select Record

A dropdown (**Select Record**) lists all records. Each option is shown by the record’s **ID** (or “Record {index}” if ID is missing). The value used internally is the record’s index in the data list. After you select a record, the rest of the page shows that record’s data and validation state.

### Record display and categories

Below the selector you see **“### Record ID: {id}”** (the display ID for the selected record). The record is grouped into **categories** (each in an expander, collapsed by default):

- **Project Details** — ID, Project/Plant Name, Status, Rated Power (kW), Storage Capacity (kWh), Applications, Paired Grid Resources, Description/Notes, URL, Latest Update Date  
- **Location Information** — Country, City, State/Province/Territory, County, Street Address, Postal Code, Latitude, Longitude  
- **Date Information** — Announced Date, Constructed Date, Commissioned Date, Decommissioned Date  
- **Contact Information** — Contact Information: Name, Email Address, Phone Number  
- **Grid & Utility** — Grid Interconnection Level, Interconnection Type, ISO/RTO, System Operator, Utility Type  
- **Ownership and Financials** — Ownership Model, Owner(s), CAPEX, OPEX, Debt Provider, Funding Source 1/2/3 and amounts  
- **Subsystems** — Subsystems (table-style editor)

**Widgets per field:** Most fields use a text or number input; booleans use a checkbox. **Grid Interconnection Level** and **Interconnection Type** use dropdowns (with allowed values and support for a custom value). **Subsystems** uses a data editor (add/remove rows, edit cells). Other list or dict fields use a JSON text area. Changes you make in these widgets are reflected in memory; they are only written to disk when you click **Save Changes to This Record** (see below).

### Per-category validation buttons

Inside each category expander:

- **When the category is not marked validated:** Only **“Mark {category} as Validated”** is shown. Click it to mark that category as validated.
- **When the category is marked validated:** **“Unmark {category} as Validated”** is shown. Click it to clear the validated state for that category. If the validation report (from Step 3) has errors for any field in this category, a yellow warning **“Validation errors are present.”** is shown next to the Unmark button.

Validation state is kept in session (per record, per category) and is not saved to a file until you use **Save validated records to JSON** in the Validated Records tab.

### Overall validation state (below all category expanders)

- **All categories marked validated and (no validation report or the report row is fully validated):** A green message **“This record is fully validated!”** is shown, and the record is treated as fully validated for the Validated Records list.
- **All categories marked validated but the report has errors for this record:**  
  - If you have already confirmed: **“This record was fully validated (with errors present).”**  
  - If not: A warning **“This record has validation errors. Do you want to mark it as validated anyway?”** and two buttons: **“Mark as validated anyway”** (primary) and **“Cancel.”** These two buttons stay until you choose one or the validation report is re-run and the row becomes fully validated. **“Mark as validated anyway”** sets the record as fully validated despite errors; **“Cancel”** clears that state.
- **Not all categories marked validated:** A warning **“Some categories are not validated yet.”** is shown, and the record is not considered fully validated.

### Save / Revert buttons (only when there are unsaved edits)

**“Save Changes to This Record”** and **“Revert Unsaved Changes”** are shown **only when** the edited record (what you see in the form) is different from the last-saved version of that record. The app compares values after normalizing (e.g. empty string and `None` are treated the same, whole-number floats and integers are treated the same, NaN is ignored), so small widget artifacts do not trigger these buttons.

- **Save Changes to This Record:** Writes the current edited record back into the data list, saves the full list to `data/output/processed_data.json`, clears the cache, and resets the form version so the widgets reflect the saved state. A success message and toast confirm the save.
- **Revert Unsaved Changes:** Discards in-memory edits by incrementing a form version and rerunning the app, which resets the widgets to the last-saved record.

If you have not changed anything (or only changed things that normalize to the same value), these two buttons do **not** appear.

### Validation Errors section

A **Validation Errors** subheader is followed by an expander **“View Validation Errors”**:

- If there is no validation data for this record: **“No validation data for this record yet.”**
- If there is validation data and no issues: **“No validation issues for this record.”**
- If there are issues: For each field with an Unvalidated flag, the expander shows the **field name**, a **description**, and a list of **error code — message** lines. The meanings of the codes are fixed in the app; the main ones are:

| Code range | Meaning (summary) |
|------------|-------------------|
| 101–108 | Missing required/optional data, wrong type, date format (MM-DD-YYYY), type mismatch |
| 201–206 | Range validation (missing, optional, &gt;0, lower/upper range, date range) |
| 301–302 | Status required or not in valid value list |
| 701–702 | Applications: at least one required; values must be in valid list |
| 1001 | URL possibly malformed |
| 2501–2502 | Grid Interconnection Level required or not in valid list |
| 6401–6504 | Technology Broad Category / Technology Mid Type required or not in valid list |
| 20001–20002 | Discharge duration vs storage/power ratio |
| 30001–30006 | Date order (constructed/commissioned/decommissioned vs announced/constructed/commissioned) |

### Download Record as JSON

A **Download Record as JSON** button is always shown when data is available. It downloads the **current** (possibly edited) record as a JSON file named `record_{id}.json`. This does not save to `processed_data.json`; use **Save Changes to This Record** for that.

---

## 6. Validated Records tab — full functionality

The **Validated Records** tab shows the list of records considered validated and lets you save them to JSON or push them to GitHub.

### How the list is built

The validated list is **merged** from two sources:

1. **From the validation report (CSV):** If `validation/output/validation_status.csv` exists, is non-empty, and has the **same number of rows** as the current data, every record whose CSV row is **fully validated** (no Unvalidated in any field) is added to the list.
2. **From session state:** Every record for which you clicked **“Mark as validated anyway”** or which became **“This record is fully validated!”** in the View and Validate Records tab is tracked in session state. If that record was **not** already added from the CSV (e.g. report missing or row count mismatch), it is added to the list.

So a record can appear because it passed the automated validation report, because you manually marked it fully validated in View Records, or both (it is only counted once).

### Stale data and Refresh Data

If **data stale** is set (e.g. after Step 2, 3, or 4), a warning is shown and a **Refresh Data** button appears. Click it to clear the cache and reload the latest data and validation status.

### Messages when there are no validated records

- **No validation report (or empty report):** An info message: *“No validation report found. Mark all categories as validated in **View and Validate Records** for each record you want here, or run **Step 3: Validation** in the Run Pipeline tab to use the validation report.”*
- **Validation row count does not match data:** A warning: *“Validation row count does not match data. Re-run **Step 3: Validation** in the Run Pipeline tab, or mark records as validated in **View and Validate Records**.”*
- **Report exists and row count matches but no record is fully validated:** An info message: *“No records are fully validated yet. Mark all categories as validated in **View and Validate Records** for each record you want here, or fix validation errors and re-run Step 3.”*

### Total validated records

The line **“Total validated records: N”** shows the size of the merged list (N).

### View validated records JSON

When there is at least one validated record, an expander **“View validated records JSON”** is shown. Inside it, for each validated record, a heading **“### Record ID: …”** and the full record as JSON (read-only).

### Save validated records to JSON

When there is at least one validated record, a subheader **“Save validated records to JSON”** and a button **“Save validated records to JSON”** are shown. Clicking the button writes the current validated list to **`data/output/validated_records.json`** (creating the directory if needed) and shows a success message with the path and count. This button is **not** shown when the validated list is empty.

When there are no validated records, a caption is shown: *“You can save your GitHub token below so it is prefilled when you have validated records.”*

### Push validated records to GitHub

A divider and subheader **“Push validated records to GitHub”** are always shown. Below them is a **form** that is always visible (whether or not you have validated records).

**Form fields:**

| Field | Purpose |
|-------|--------|
| **GitHub Owner / Org** | GitHub user or organization that owns the repo (default from git remote if available). |
| **Repository Name** | Repository name (default from git remote). |
| **Branch** | Branch to push to (default from git, e.g. `main`). |
| **Target directory in repo** | Directory path inside the repo where each record’s JSON file will be written (e.g. `data/exports`). |
| **GitHub Token (PAT)** | Personal access token with repo write access. Can be prefilled from `.streamlit/secrets.toml` if `github_token` is set. |
| **Commit message prefix** | Each commit message is “{prefix}: ID {id}” (e.g. “Add/Update record: ID 123”). |
| **Save/overwrite this PAT to .streamlit/secrets.toml** | If checked, on submit the token is written to `.streamlit/secrets.toml` so it is prefilled next time. |

**Multiselect:** **“Select record IDs to push (leave empty to push ALL validated)”** — options are the IDs of the current validated records. If you leave it empty, **all** validated records are pushed; if you select one or more IDs, only those records are pushed.

**Submit button:** **“Push to GitHub”** (primary). Submitting the form:

1. If no token was entered, an error is shown and the rest is skipped.
2. If **Save/overwrite this PAT** was checked, the token is written to `.streamlit/secrets.toml` and a success or error message is shown.
3. The list to push is either the selected IDs or all validated records.
4. If the list to push is empty, an info message says to validate records first.
5. Otherwise, each record is written as a separate JSON file under the target directory (e.g. `data/exports/record_123.json`). The GitHub Contents API creates or updates each file; commit message is “{prefix}: ID {id}”. A spinner is shown during the push.
6. After the push: a success line with the count of pushed files, then for each record a line with an icon (✅ or ❌), ID, file path, and detail (e.g. “Committed” or error text). A caption reminds you that checking “Save/overwrite PAT” stores the token for next time.

---

## 7. Technical analysis of backend code

This section describes the implementation of each part of the repo for engineers working on the codebase.

### 7.1 pipeline.py

**Paths:** `_DATA_DIR = Path(__file__).resolve().parent`. `DATA_FILE_PATH = _DATA_DIR / "data" / "output" / "processed_data.json"`. `VALIDATION_STATUS_FILE = _DATA_DIR / "validation" / "output" / "validation_status.csv"`. These absolute paths ensure the pipeline and filler use the same files regardless of current working directory.

**Loading:** `load_data(file_path)` is decorated with `@st.cache_data`; it reads JSON from `file_path` and returns the list (or None on error). `load_validation_status(file_path)` reads the validation CSV with pandas (no cache); returns DataFrame or None.

**Categories:** `categorize_data(record)` returns a dict mapping category names to dicts of field names → values. Categories: Project Details, Location Information, Date Information, Contact Information, Grid & Utility, Ownership and Financials, Subsystems. Only keys present in the record are included.

**Validation helpers:** `_parse_validation_cell(cell)` normalizes a CSV cell (string, list, or NaN) into a list of dicts for the validation entry. `_format_validation_issues(val_row, code_messages)` returns a list of `{field, description, codes}` for every column in `val_row` that has an Unvalidated flag; `code_messages` comes from `_error_code_messages()`. `_row_fully_validated(val_row)` returns True iff no column (except Index/ID) has an Unvalidated flag. `_category_has_validation_errors(val_row, field_names)` returns True iff any of the given field names has Unvalidated in `val_row`. `_normalize_for_compare(val)` recursively normalizes values so that empty string/None/NaN, whole-number float→int, and numpy scalars are comparable for equality; used to decide when to show Save/Revert buttons.

**Widgets:** `edit_value_widget(label, value, widget_key)` renders the appropriate Streamlit widget by type: Grid Interconnection Level and Interconnection Type use selectboxes with fixed options plus current value; booleans → checkbox; int → number_input step 1; float → number_input step 0.1; Subsystems (list of dicts) → `st.data_editor`; other list/dict → text_area with JSON; default → text_input. Returns the (possibly edited) value.

**Record UI:** `display_record_grouped(record, record_id, edit_mode, val_row, form_version)` builds `grouped_data = categorize_data(record)`, initializes `st.session_state["validation_status_{record_id}"]` as a dict of category → bool (all False), and for each category expander renders fields via `edit_value_widget` (writing into `edited_record`) and per-category “Mark/Unmark {category} as Validated” buttons. If the category is marked validated and `val_row` has errors for that category’s fields, it shows `st.warning("Validation errors are present.")`. Below expanders, if all categories are marked: if `val_row` is None or `_row_fully_validated(val_row)`, sets `record_validated_{record_id}` True and shows success; else shows “Mark as validated anyway” / “Cancel” and manages `record_validated_{record_id}`. Returns `edited_record` (the in-memory edited copy). Session keys: `validation_status_{record_id}`, `record_validated_{record_id}`; widget keys use `edit_{record_id}_{form_version}_{slug(category)}_{slug(key)}`.

**Validated list and GitHub:** `display_validated_records(data)` loads validation CSV; builds `validated_records` by (1) appending every `data[idx]` whose CSV row is fully validated when CSV exists and `len(validation_status) == len(data)`, and (2) appending every record with `record_validated_{idx}` True and not already in the CSV set. Renders messages when empty (no report, row count mismatch, or no records validated). “Save validated records to JSON” writes `validated_records` to `data/output/validated_records.json`. GitHub form uses `get_git_origin_defaults()` (cached) for owner/repo/branch defaults; on submit calls `save_github_token_to_secrets(token)` if requested, then `push_validated_to_github(to_push, owner, repo, branch, dir_path_in_repo, token, commit_prefix)`. `push_validated_to_github` writes one file per record under `dir_path_in_repo` (filename `record_{id}.json`) via `github_upsert_content` (GET to check sha, PUT with base64 content). `_get_git_origin_defaults(repo_root)` runs `git remote get-url origin` and `git rev-parse --abbrev-ref origin/HEAD`; `_parse_github_remote_url` parses HTTPS or SSH URLs to (owner, repo). Session state keys used: `data_stale`, `validation_status_{record_id}`, `record_validated_{record_id}`, `edit_form_version_{selected_index}`.

**Tabs:** `main()` creates `st.tabs(["Run Pipeline", "View Records", "Validated Records"])`; tab 0 runs `pipeline_tab()`, tab 1 runs `view_records_tab()`, tab 2 runs refresh logic then `display_validated_records(data)`.

### 7.2 main.py

**Flow:** `pipeline()` (invoked when `__name__ == "__main__"`): (1) for each config in `site_configs`, calls `collect_articles(config)`; (2) builds `ArticleProcessor(input_path, output_path, api_key, limit)` and calls `processor.process_articles()`; (3) calls `run_validation(output_path)`; (4) calls `data_insert.process_data()`. **Note:** `data_insert.process_data()` does not exist in the current codebase; only `process_record` and `main()` (CLI) are implemented in `data_insert.py`. Running `python main.py` will raise `AttributeError` at the last step unless `process_data` is implemented or the call is removed.

### 7.3 article_scraper.py

**Entry:** `collect_articles(config)` expects `config` with keys: `base_url`, `link_selector`, and optionally `urls_file`, `articles_output_file`, `url_prefix`. It calls `read_existing_urls(urls_file)` to get a set of already-seen URLs, `gather_urls(base_url, link_selector, existing_urls, url_prefix)` to fetch the page and collect new links matching the selector (and prefix), then for each new URL uses the `newspaper` library to download and parse the article (title, text, source). New URLs are appended to `urls_file`; extracted articles are written to `articles_output_file` as a JSON array. Errors during download/parsing are caught and logged without stopping. Articles missing title or text are skipped.

### 7.4 article_processor.py

**ArticleProcessor:** Constructor takes `input_path`, `output_path`, `api_key`, `limit` (None = no limit), `processed_urls_file` (default under `data/input/`), `fail_fast`, `max_errors`. It initializes the extractor via `initialize_extractor()` (registers nine tools: project_info, location_info, date_info, project_applications, grid_utility, project_participants, project_ownership_funding, contact_info, subsystem_specifications), loads processed URLs from the file into a set, and sets `processed_count`, `error_count` to 0.

**Methods:** `load_articles()` reads the input JSON and returns the list. `load_processed_urls()` reads the processed URLs file (one URL per line) into a set. `save_processed_data(data)` appends one record to the output JSON (loads existing list if file exists, appends, writes back). `add_to_processed_urls(url)` appends the URL to the file and adds it to the in-memory set.

**process_articles():** Loads articles; for each article, if limit reached or URL already in processed_urls, skips. Builds prompt string `Title: ...\nSource: ...\nText: ...` and calls `self.extractor.extract_all(prompt_text)` to get a dict of tool name → result. Wraps that in a single-element list and passes to `PostProcessor(extracted_data_list=[extracted_data]).process_all()[0]`, sets `Data Source = "GESDB_Pipeline"`, then `save_processed_data(processed_element)` and `add_to_processed_urls(article['source'])`. On exception, increments `error_count`; if `fail_fast` or `error_count >= max_errors`, breaks; else continues.

### 7.5 extractor/

**Extractor (extractor.py):** Uses `ChatOpenAI` with `model="gpt-5"`, `temperature=0`, `use_responses_api=True`. `register_tool(tool_name, tool_func)` stores the tool and infers its declared name for `tool_choice`. `extract(text, tool_name)` binds the single tool, invokes the LLM with forced tool call, and returns `ExtractorUtils.process_response(tool_name, response)`. `extract_all(article)` runs all registered tools in parallel via `ThreadPoolExecutor(max_workers=current_workers)`. On OpenAI 429 (detected via `_is_rate_limit_error`), it collects failed tool names, waits (`_get_retry_after_seconds` from response header or default), then retries only the failed tools with `current_workers` halved (floor `min_workers`). After `max_rate_limit_retries` retries it re-raises. Constructor params: `max_workers`, `min_workers`, `rate_limit_retry_delay_seconds`, `max_rate_limit_retries`.

**ExtractorUtils (utils/extractor_utils.py):** `process_response(tool_name, response)` selects the processor for `tool_name`, gets tool-call args (e.g. from the first tool call or by matching declared name), and calls the processor to map raw args to a single dict (GESDB-style keys). Each tool has a corresponding `*_util.py` that implements that processor (e.g. project_info_utils, location_info_utils, date_info_util, contact_info_util, project_applications_util, grid_utility_util, project_ownership_funding_util, subsystem_specifications_util).

**Tools (extractor/tools/):** Each file defines a LangChain `@tool` and a Pydantic schema. Registered tools: project_info (ProjectInfoSchema), location_info (LocationInfoSchema), date_info (DateInfoSchema), project_applications (ProjectApplications), grid_utility (GridUtilitySchema), project_participants (ProjectParticipantsSchema), project_ownership_funding (ProjectOwnershipFundingSchema), contact_info (ContactInfoSchema), subsystem_specifications (SubsystemSpecificationsSchema). The extractor runs these on the same prompt in parallel; results are merged per article and passed to the postprocessor.

### 7.6 postprocessor/

**PostProcessor (postprocessor.py):** Constructor takes `extracted_data_list` (list of dicts keyed by tool name) and optional `output_file_path`. If that file exists and is valid JSON list, `offset = len(existing_data)` for ID assignment. `assign_id(index)` returns `offset + index + 1`. `process_element(extracted_data, index)` builds one flat record: maps project_info, location_info, date_info, grid_utility, project_participants, project_ownership_funding, contact_info, and applications/subsystems into GESDB field names; `format_applications` maps tool keys to display keys; `format_subsystems` normalizes subsystem details from the tool output and ensures at least one subsystem entry (default shell if empty). `process_all()` runs `process_element` for each item in `extracted_data_list` and returns the list of records. **postprocessor_utils.py:** `PostProcessingUtils.fill_missing_values(element)` currently leaves values unchanged (placeholder for future normalization).

### 7.7 validation/

**validation_script.run_validation(input_path=None):** Default input is `validation/data/test_data.json`; when called from pipeline/main, `input_path` is the path to `processed_data.json`. Reads the JSON into a DataFrame and loads rules from `validation/data/gesdb_data_rules.csv`. Rule lookup `get_rule(col_name)`:
exact match on Unique Field Name, else normalized (case and spaces around `/_-`), else DEFAULT_RULE (Optional, Text, not applicable); missing rules are reported. For each row and each field (including nested Applications and Subsystems), runs type/range and field-specific validators, builds a single status via `validation_detail_builder` (any Unvalidated → Unvalidated), and stores `{flag, flag_description, error_codes, timestamp}` per cell. Also runs row-level checks (e.g. capacity-to-power ratio, date order) and stores warnings. Writes `validation/output/validation_status.csv`, `validation_status.json`, and `warning_messages.csv`.

**validation_functions.py:** Exposes `validate_data_type`, `validate_data_range`, and field-specific validators (e.g. Status, URL, Applications, Grid Interconnection Level, Technology Broad/Mid). `validate_capacity_to_power_ratio`, `validate_dates` produce warnings. **errorcodes.py:** Defines error code constants (1xx, 2xx, 3xx, 7xx, 1001, 25xx, 64xx, 65xx, 20001–20002, 30001–30006). **display_information.py** and **data_consumption.py** read the validation JSON and produce downstream outputs (e.g. unvalidated Excel, error_count CSV).

### 7.8 filler/

**run_filler.run(data_path, attributions_path, limit_records, start_record_index, debug):** Loads JSON from `data_path` (default `config.PROCESSED_DATA_PATH`), loads validation CSV via `validation_loader.load_validation_status()`, loads attributions from `attributions_path`. Gets `SEARCH_API_KEY` and `OPENAI_API_KEY` from env; if both missing, returns (0,0,0). For each record in the slice `[start_record_index, start_record_index + limit_records)` (or to end if limit_records is None), calls each module in `GROUP_FILLERS` (project_details, location_information, date_information, contact_information, grid_utility, ownership_financials, subsystems). Each `fill_group(record, record_index, attributions, api_key_search, api_key_openai, validation_df, debug)` determines fields to fill (empty or Unvalidated with a fillable error code from config.FILLABLE_ERROR_CODES), builds a search query (e.g. project name + location + field descriptions from field_descriptions.py), calls `search_client.search(query, api_key=api_key_search)` (SerpAPI), then `llm_extract.extract_from_snippets(snippets, field_descriptions, api_key=api_key_openai)` (OpenAI), and writes acceptable values back into the record and appends to attributions. After all records, `apply_attributions_to_data(data, attributions)` applies attributions, then the updated data and attributions are saved to disk. Returns (records_processed, records_modified, attributes_filled).

**config.py:** Defines paths (PROCESSED_DATA_PATH, ATTRIBUTIONS_PATH, VALIDATION_STATUS_PATH), FILLABLE_ERROR_CODES, VALIDATION_COLUMN_TO_RECORD_KEY, CATEGORY_KEYS (aligned with pipeline categorize_data), FIELDS_REQUIRE_POSITIVE. **search_client.py:** Uses SerpAPI (`google-search-results`); `search(query, api_key, num, debug)` returns list of `{title, snippet}`. **llm_extract.py:** Uses OpenAI (e.g. gpt-4o-mini) to extract field values from snippets; returns a dict. **validation_loader:** Loads validation CSV; `get_fields_to_fill_from_validation` returns record keys in a category that are Unvalidated with a fillable error code. **helpers:** `is_empty`, `get_empty_or_unvalidated_fields`, etc. **attributions:** load/save/append attributions; `apply_attributions_to_data` writes filled values back into data by path.

### 7.9 data_insert.py

**Current behavior:** The module does **not** define `process_data()`. It implements:

- **process_record(record, treat_zero_as_missing, max_results, sleep_s):** Walks the record with `walk()`; for each leaf or empty container path where the value is “missing” (via `is_missing` or `is_missing_with_zero`), builds context with `extract_context(record)`, builds a query with `make_query(ctx, field_name, rule_for_path(path))`, calls `google_cse_search(query, max_results, sleep_s)` (Google Custom Search API), then `summarize_value(...)` (OpenAI) to get a suggested value. Returns a dict of path → `{value, confidence, rationale, references}`. No merging of two files; no fuzzy matching.

- **main():** CLI: reads JSON array from `input_json`, runs `process_record` on each record, writes per-record suggestions to an output JSON (default `*_autofill.json`).

The README’s “Data Matching and Merging with process_data” section describes behavior (fuzzy matching, originals_matched.json, unvalidated_matched.json) that is **not** implemented. `main.py`’s call to `data_insert.process_data()` will raise `AttributeError` unless that function is added or the call is removed.

---

## 8. Services overview

| Service | Where it is used | Role | Configuration |
|--------|-------------------|------|----------------|
| **OpenAI** | `article_processor` (extractor tools), `filler/llm_extract.py`, `data_insert.summarize_value` | LLM extraction from article text (Step 2), extraction from search snippets (Step 4 filler), and summarization of missing-field values (data_insert CLI). | `OPENAI_API_KEY` in `.env`. Required for Steps 2 and 4; optional for data_insert. |
| **SerpAPI (google-search-results)** | `filler/search_client.py` only | Web search for the Data Filler: returns organic search results (title + snippet) used as input to the LLM for filling missing fields. | `SEARCH_API_KEY` in `.env`. Install: `pip install google-search-results`. If unset, the filler cannot run search (only in-memory/LLM logic can run). |
| **Google Custom Search** | `data_insert.py` (`google_cse_search`) only | Web search for the data_insert autofill suggestions: fetches snippets for missing fields, then OpenAI summarizes. Not used by the Streamlit pipeline or the filler. | `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ENGINE_ID` in `.env`. Optional. |
| **GitHub API (Contents)** | `pipeline.py` (`github_upsert_content`, `push_validated_to_github`) | Creates or updates files in a GitHub repo. Used by the Validated Records tab “Push to GitHub”: one JSON file per validated record under a configurable directory; GET to resolve existing file sha, PUT to create/update. | GitHub Personal Access Token (PAT) with repo scope. Can be stored in `.streamlit/secrets.toml` as `github_token` so the form prefills. |
| **requests** | `article_scraper` (page fetch), `pipeline.py` (GitHub API), `data_insert` (Google CSE) | HTTP client for scraping, GitHub API calls, and Google CSE. | Optional: `HTTP_PROXY`, `HTTPS_PROXY` in `.env` for corporate proxies (used in data_insert). |
| **newspaper4k** | `article_scraper.py` | Parses article HTML to extract title, text, and metadata from each collected URL. | None. |

**Note:** `.env.example` mentions `SERPER_API_KEY` for “future filler”; the current filler uses **SerpAPI** only. There is no Serper implementation in the codebase.

---

## 9. Developer guide

### Repo layout

- **Root:** `pipeline.py` (Streamlit app entry: `streamlit run pipeline.py`), `main.py` (CLI pipeline), `article_scraper.py`, `article_processor.py`, `data_insert.py`, `requirements.txt`, `.env.example`.
- **data/:** `data/input/` (articles JSON, URL lists, processed_urls.txt), `data/output/` (processed_data.json, validated_records.json, filler_attributions.json).
- **validation/:** `validation_script.py`, `validation_functions.py`, `errorcodes.py`, `display_information.py`, `data_consumption.py`; `validation/data/` (test_data.json, gesdb_data_rules.csv); `validation/output/` (validation_status.csv, validation_status.json, warning_messages.csv).
- **extractor/:** `extractor.py` (Extractor class); `tools/` (one file per tool + Pydantic schema); `utils/` (extractor_utils + per-tool processors).
- **postprocessor/:** `postprocessor.py`, `postprocessor_utils.py`.
- **filler/:** `run_filler.py`, `config.py`, `search_client.py`, `llm_extract.py`, `validation_loader.py`, `helpers.py`, `field_descriptions.py`, `attributions.py`; group fillers: `project_details.py`, `location_information.py`, `date_information.py`, `contact_information.py`, `grid_utility.py`, `ownership_financials.py`, `subsystems.py`.
- **tests/:** `test_pipeline_helpers.py` (tests for `_parse_github_remote_url`, `_get_git_origin_defaults`, `_parse_validation_cell`, `_row_fully_validated`, `_category_has_validation_errors`; no Streamlit).

### Running tests

From the project root:

```bash
pytest
```

Or run a specific file:

```bash
pytest tests/test_pipeline_helpers.py
```

The pipeline helper tests do not start Streamlit; they import `pipeline` and call the tested functions directly. Validation and filler have their own test or runner modules (e.g. `validation/test_validation_functions.py`, `filler/test_filler_run.py`); run them as needed. **Convention (per project rules):** Run integration tests at the end and fix any failures; do not remove or skip failing tests.

### Architecture file

The project rule is to maintain an architecture file and update it after changes. There is no `ARCHITECTURE.md` in the repo today. Section 7 (Technical analysis) of this README serves as the main technical reference. Consider adding `ARCHITECTURE.md` (e.g. a shorter summary with links to this README) and updating it when you change backend behavior.

### Conventions

- **No intermediate variables** (project rule): Prefer direct expressions where it does not harm readability.
- **Build and test iteratively** (project rule): Test small parts as you go; run the full test suite before considering a task done.

### Extension points

- **New extractor tool:** Add a tool in `extractor/tools/` (LangChain tool + Pydantic schema), add a processor in `extractor/utils/`, register the tool in `article_processor.initialize_extractor()`, and map the tool output in `PostProcessor.process_element()` if the record shape changes.
- **New validation rule or field:** Add or edit rules in `validation/data/gesdb_data_rules.csv`; add field-specific logic in `validation_functions.py` and wire it in `validation_script.run_validation()`.
- **New filler category:** Add a new module in `filler/` with `fill_group(...)` (same signature as existing group fillers), add it to `GROUP_FILLERS` in `run_filler.py`, and ensure `config.CATEGORY_KEYS` and pipeline `categorize_data()` stay in sync if you add UI categories.

### Validation test data

- When **run with no arguments** (e.g. `python -m validation.validation_script` or from tests), validation reads **`validation/data/test_data.json`**.
- When run **from the pipeline or main** with a path, it reads **`data/output/processed_data.json`** (or the path passed by the caller). Ensure the JSON is an array of objects with the expected GESDB field names.

### data_insert and main.py

`main.py` calls `data_insert.process_data()`, which does not exist. Either implement `process_data()` (e.g. fuzzy matching and dual output files as described in the old README) or remove/comment out that call so the CLI pipeline completes after validation.

---

**Note on legacy sections:** Earlier versions of this README described an article scraper, article processor, and a "Data Matching and Merging with `process_data`" module. The scraper and processor are covered in **Section 4** (user guide) and **Section 7** (technical analysis). The function **`data_insert.process_data()`** (fuzzy matching, `originals_matched.json`, `unvalidated_matched.json`) is **not implemented** in the current codebase. `data_insert` provides only `process_record()` and a CLI that writes autofill suggestions to JSON. See **Section 1** (Installation), **Section 7.2** and **7.9**, and **Section 9** (Developer guide) for details and how to fix or work around the `main.py` call to `process_data()`.
