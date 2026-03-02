import json
import os
import traceback
# import logging
from extractor.extractor import Extractor
from extractor.tools.project_info_tool import extract_project_info
from extractor.tools.location_info_tool import extract_location_info
from extractor.tools.date_info_tool import extract_date_info
from extractor.tools.project_applications_tool import extract_project_applications
from extractor.tools.grid_utility_tool import extract_grid_utility_info
from extractor.tools.project_participants_tool import extract_project_participants
from extractor.tools.project_ownership_funding_tool import extract_project_ownership_funding
from extractor.tools.contact_info_tool import extract_contact_info
from extractor.tools.subsystem_specification_tool import extract_subsystem_specifications
from postprocessor.postprocessor import PostProcessor

# # Configure logging
# logging.basicConfig(
#     level=print,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]
# )
# logging.getLogger("openai").setLevel(logging.WARNING)
# logging.getLogger("requests").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)


class ArticleProcessor:
    def __init__(self, input_path, output_path, api_key, limit=None, processed_urls_file='processed_urls.txt',
                 fail_fast=False, max_errors=1):
        self.input_path = input_path
        self.output_path = output_path
        self.limit = limit
        self.api_key = api_key
        self.processed_urls_file = os.path.join('data', 'input', processed_urls_file)
        self.extractor = self.initialize_extractor()
        self.processed_count = 0
        self.processed_urls = self.load_processed_urls()
        self.fail_fast = fail_fast
        self.max_errors = max_errors
        self.error_count = 0

    def initialize_extractor(self):
        # Initialize and register tools
        print("Initializing extractor with registered tools...")
        extractor = Extractor(api_key=self.api_key)
        extractor.register_tool("project_info", extract_project_info)
        extractor.register_tool("location_info", extract_location_info)
        extractor.register_tool("date_info", extract_date_info)
        extractor.register_tool("project_applications", extract_project_applications)
        extractor.register_tool("grid_utility", extract_grid_utility_info)
        extractor.register_tool("project_participants", extract_project_participants)
        extractor.register_tool("project_ownership_funding", extract_project_ownership_funding)
        extractor.register_tool("contact_info", extract_contact_info)
        extractor.register_tool("subsystem_specifications", extract_subsystem_specifications)
        print("Extractor initialized.")
        return extractor

    def load_processed_urls(self):
        # Load already processed URLs from the file
        if os.path.exists(self.processed_urls_file):
            with open(self.processed_urls_file, 'r') as file:
                processed_urls = set(line.strip() for line in file)
            print(f"Loaded {len(processed_urls)} processed URLs.")
            return processed_urls
        return set()

    def load_articles(self):
        # Load input JSON data
        print(f"Loading articles from {self.input_path}...")
        with open(self.input_path, 'r') as file:
            articles = json.load(file)
        print(f"Loaded {len(articles)} articles.")
        return articles

    def save_processed_data(self, data):
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        # Check if output file already has data
        if os.path.exists(self.output_path):
            with open(self.output_path, 'r') as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        # Append new data and save
        existing_data.append(data)
        with open(self.output_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
        
        print(f"Processed data saved to {self.output_path}.")

    def add_to_processed_urls(self, url):
        # Append the new URL to the processed URLs file in /data/input/
        with open(self.processed_urls_file, 'a') as file:
            file.write(f"{url}\n")
        self.processed_urls.add(url)
        print(f"URL added to processed list: {url}")

    def process_articles(self):
        articles = self.load_articles()

        try:
            for idx, article in enumerate(articles, start=1):
                # Respect processing limit
                if self.limit and self.processed_count >= self.limit:
                    print("Processing limit reached. Ending process.", flush=True)
                    break

                # Skip if URL already processed
                if article.get('source') in self.processed_urls:
                    continue

                title = article.get('title', 'Unknown Title')
                print(f"Processing article {self.processed_count + 1}: {title}", flush=True)

                try:
                    # Build prompt exactly as before
                    prompt_text = (
                        f"Title: {article.get('title','')}\n"
                        f"Source: {article.get('source','')}\n"
                        f"Text: {article.get('text','')}\n"
                    )
                    print("Formatted Prompt for LLM:", prompt_text[:200], "...", flush=True)

                    # Run extractor
                    extracted_data = self.extractor.extract_all(prompt_text)

                    # Post-process
                    post_processor = PostProcessor(extracted_data_list=[extracted_data])
                    processed_element = post_processor.process_all()[0]
                    processed_element["Data Source"] = "GESDB_Pipeline"

                    # Save + mark URL as processed only on success
                    self.save_processed_data(processed_element)
                    if article.get('source'):
                        self.add_to_processed_urls(article['source'])

                    self.processed_count += 1
                    print(f"Article processed and saved: {title}", flush=True)

                except KeyboardInterrupt:
                    print("\nInterrupted by user. Stopping gracefully...", flush=True)
                    break

                except Exception as e:
                    self.error_count += 1
                    print(f"Error processing article '{title}': {e}", flush=True)
                    print(traceback.format_exc(), flush=True)   # <— add this line

                    if self.fail_fast or self.error_count >= self.max_errors:
                        print(f"Stopping due to errors (fail_fast={self.fail_fast}, "
                              f"error_count={self.error_count}, max_errors={self.max_errors}).", flush=True)
                        break

                    continue  # move on to next article

        except KeyboardInterrupt:
            print("\nInterrupted by user (outer). Exiting.", flush=True)

        print("Processing complete.", flush=True)




if __name__ == "__main__":
    # Direct paths and settings for the run
    input_path = r"data\input\articles_power_technology.json"
    output_path = r"data\output\processed_data.json"
    limit = 10  # set the processing limit or None
    api_key = ""  # replace with actual API key

    # Run the article processor
    processor = ArticleProcessor(input_path=input_path, output_path=output_path, api_key=api_key, limit=limit)
    processor.process_articles()
