
# Article Scraper Pipeline

## How to Run the Pipeline

The pipeline is initiated by running `main.py`, which contains the script for scraping articles from various websites. The article scraper is executed as a function inside this pipeline.

### Steps to Run the Pipeline:

1. **Install the required packages**:
   Ensure you have the necessary dependencies installed. The dependencies are listed in the `requirements.txt` file. To install them, run:

   ```bash
   pip install -r requirements.txt
   ```

2. **Execute the pipeline**:
   After installing the dependencies, run the `main.py` script to start the article scraping process:

   ```bash
   python main.py
   ```

   This will trigger the scraping process, gather new article URLs, extract their content, and save the results to a JSON file.

### API keys

Store API keys in a `.env` file in the project root (never commit it). Copy `.env.example` to `.env`, then add your values:

- **OPENAI_API_KEY** — required for article processing and LLM steps ([OpenAI API keys](https://platform.openai.com/api-keys))
- **GOOGLE_CSE_API_KEY** / **GOOGLE_CSE_ENGINE_ID** — optional, for Google Custom Search in data insert
- Uncomment and set **SERPER_API_KEY** or **SEARCH_API_KEY** when you add the web-search filler

The app loads `.env` automatically when you run `main.py` or the Streamlit pipeline.

### Validation data source

The validation step (`run_validation` in `validation/validation_script.py`) runs on different inputs depending on how it is invoked:

- **From the pipeline or main process** (`pipeline.py` or `main.py`): validation reads **`data/output/processed_data.json`**, so validation status reflects the current pipeline output.
- **With no arguments** (e.g. `python -m validation.validation_script` or tests): validation reads **`validation/data/test_data.json`** for development and testing.

---

## Article Scraper: Overview

The article scraper is a critical part of the pipeline, designed to gather and process article URLs from various websites. It performs the following key functions:

1. **URL Gathering**: The scraper fetches article URLs from the configured website, based on the provided CSS selector.
2. **Content Extraction**: For each article URL, the scraper extracts the title, body text, and source URL using the `newspaper` library.
3. **Duplicate Avoidance**: The scraper maintains a record of previously processed URLs to avoid re-scraping the same content.
4. **Saving Data**: Extracted article content is saved as a JSON file, which can be used for further processing.

### Configuration

The article scraper can be customized by modifying the configuration in `main.py` using the `site_configs` list. Each configuration entry contains:

- **base_url**: The website URL from which to scrape articles.
- **link_selector**: A CSS selector used to identify article links on the page.
- **urls_file**: A file where processed URLs are stored to avoid duplication.
- **articles_output_file**: The JSON file where the extracted article data will be saved.
- **url_prefix**: An optional prefix to filter URLs that should be scraped.

### Example Configuration:

```python
site_configs = [
    {
        'base_url': 'https://www.power-technology.com/projects/',
        'link_selector': 'a[href^="https://www.power-technology.com/projects/"]',
        'urls_file': 'articles/urls_power_technology.txt',
        'articles_output_file': 'articles/articles_power_technology.json',
        'url_prefix': 'https://www.power-technology.com/projects/'
    }
]
```

### Customization

You can extend and customize the scraper for various websites:
- **Adding New Sites**: Add more configurations to `site_configs` to scrape additional websites.
- **Changing File Paths**: Modify the `urls_file` and `articles_output_file` paths to organize the output files as needed.
- **Adjusting CSS Selectors**: Update the `link_selector` to match the structure of the articles you want to target.

### Error Handling

The scraper includes error handling for:
- **Download and Parsing Errors**: Any issues during content extraction are logged without stopping the process.
- **Content Validation**: Articles missing critical data (like title or text) are skipped and logged.

# Article Processor for GESDB Pipeline

## Overview

The **Article Processor** is designed to process structured information from scraped articles, ensuring accurate, validated data output. Using LangChain and the OpenAI API, it employs a modular, tool-based approach to flexibly extract specific data points, making it adaptable across various domains. Here’s a breakdown of its structure and layout:

## Code Structure and File Layout

- **`article_processor.py`**: This file orchestrates the scraping and extraction process. It initializes the `Extractor`, registers extraction tools, and runs the extraction on scraped article data.

### Directory Layout

- **`extractor/`**:
  - **`extractor.py`**: Defines the core `Extractor` class, which interacts with the OpenAI API through LangChain’s `ChatOpenAI`. Key methods include:
    - **`register_tool`**: Registers individual tools, making it easy to expand the Extractor's capabilities by adding or modifying tools.
    - **`extract`**: Extracts information based on a registered tool, validating data against specified schemas.
    - **`extract_all`**: Applies all registered tools to a given text, ensuring a comprehensive extraction.

  - **`tools/`**:
    - **`project_info_tool.py`**: Example of a modular extraction tool. This tool uses a Pydantic schema (`ProjectInfoSchema`) to extract project-related data, validating fields like `project_name`, `rated_power`, and `status` against the schema.
    - **Additional Tool Files**: Future tools can be added to this folder to handle various extraction tasks, each with a unique Pydantic schema for validation.

- **`extractor/utils/`**:
  - Contains utility functions for processing responses from LangChain's API calls by mapping each tool to a corresponding processing function, such as:
    - **`process_project_info_tool`**: Processes project information.
    - **`process_location_info_tool`**: Processes location data.
    - **`process_date_info_tool`**: Processes date information.
    - Additional processing utilities for each registered tool to extract and structure data efficiently.

## Key Features

1. **Modular Tool System**: The Extractor’s tools are modular, enabling easy addition of new tools for extracting specific data. This makes the Extractor adaptable to different data requirements without needing significant code restructuring.

2. **Schema-Based Validation**: Each tool is paired with a Pydantic model to validate data. For example, `ProjectInfoSchema` in `project_info_tool.py` checks fields for project information, ensuring consistency and accuracy in the extracted data.

3. **Customizable and Extendable**: New tools can be added by creating additional files in `tools/` and registering them within `article_processor.py`. This modularity makes the Extractor scalable and adaptable for various data extraction needs across domains.

4. **Workflow Flexibility**: Tools can be registered, configured, and customized independently, allowing for a highly tailored and efficient data extraction process.

## ArticleProcessor Class Details

- **`input_path`**: Path to the JSON file containing input articles.
- **`output_path`**: Path to the file where processed data will be saved.
- **`api_key`**: API key for accessing the LangChain/OpenAI model.
- **`limit`**: Optional parameter to set a processing limit for articles (default is unlimited).
- **`processed_urls_file`**: Path to the file storing URLs of already processed articles to avoid redundancy.

## Extractor Class Details

- **`tools`**: Dictionary to store and reference the registered extraction tools.
- **`extract_all()`**: Runs all registered tools on a given text, aggregating results from each tool's output.

## Methods in ArticleProcessor

- **`initialize_extractor()`**: Initializes and registers each tool to the extractor.
- **`load_processed_urls()`**: Loads previously processed URLs to avoid duplicate processing.
- **`load_articles()`**: Loads articles from the input JSON file.
- **`save_processed_data()`**: Appends processed data to the output JSON file.
- **`add_to_processed_urls()`**: Saves a processed URL to the list to prevent re-processing.
- **`process_articles()`**: Primary method that iterates through each article, applies extraction tools, and saves the processed output.

## Example Usage

1. Set up paths and API key in the `if __name__ == "__main__":` section.
2. Initialize an `ArticleProcessor` instance with required paths and configuration.
3. Call `process_articles()` to process the input articles and save structured JSON output.

## Sample Execution

```python
if __name__ == "__main__":
    # Define file paths and API key
    input_path = r"data/input/articles_power_technology.json"
    output_path = r"data/output/processed_data.json"
    limit = 10  # Optional processing limit
    api_key = "your_openai_api_key_here"  # Replace with your actual API key

    # Instantiate and run the processor
    processor = ArticleProcessor(input_path=input_path, output_path=output_path, api_key=api_key, limit=limit)
    processor.process_articles()
```
## Logging

The `logging` module is configured to provide detailed information during the article processing flow. Each stage, including initialization, loading, and processing, is logged for easy debugging and tracking of progress.

## Notes

- Ensure `input_path` and `output_path` directories are correctly structured and accessible.
- Replace the `api_key` in the sample execution code with a valid OpenAI API key.
- The `processed_urls_file` prevents redundant processing by tracking URLs that have already been processed.

---

This documentation provides a structured and detailed overview of the `ArticleProcessor` setup and usage.

---

## Data Matching and Merging with `process_data`

The **Data Matching and Merging** module (`process_data`) is a robust function for comparing and consolidating information between two JSON files: an original data file and a processed data file. Utilizing fuzzy matching techniques, it identifies similar entries based on project names and merges complementary information across these entries to create comprehensive, consistent datasets.

### Key Functions

1. **Fuzzy Matching**: The `process_data` function compares entries using fuzzy matching, allowing it to detect similar project names even when they contain slight variations. This ensures that related entries are matched accurately.
2. **Iterative Merging**: The merging process fills in missing data by iterating over each entry until all possible information has been included. The result is a more complete representation of each matched entry.
3. **Consistent Output Format**: Each field in the output follows a specified order, improving readability and ensuring that the data remains structured and accessible.

### Output Files

The `process_data` function produces two output files:
- **`originals_matched.json`**: Contains entries from the original data file, enriched with any available information from the processed data file.
- **`unvalidated_matched.json`**: Contains entries from the processed data file, enhanced with additional information from the original file.

### Benefits of Dual Output Files

Having both `originals_matched.json` and `unvalidated_matched.json` allows for:
- **Data Completeness**: Each file retains the unique context of its source data while being enriched with supplemental information. This dual-file structure is beneficial for scenarios where data completeness and reliability are crucial.
- **Cross-Referencing**: Users can cross-reference data in the original and processed files, aiding in data validation and quality control.

### Example Usage

The `process_data` function is designed to be run from `main.py`. To call this function, include the following in your `main.py` script:

```python
import data_insert

data_insert.process_data()
```
### Sample Execution

1. Ensure that your data files are correctly formatted and accessible.
2. Execute the `main.py` script to initiate the data matching and merging process:

```bash
python main.py
```
### Note

This will create two output files (`originals_matched.json` and `unvalidated_matched.json`) in the `data/output` directory, containing consolidated and complete data entries.

