import os
from dotenv import load_dotenv

load_dotenv()  # OPENAI_API_KEY etc. from .env (see .env.example)

from article_scraper import collect_articles
from article_processor import ArticleProcessor  # Import the ArticleProcessor step
from validation.validation_script import run_validation 
import data_insert
# Define configurations for article scraping
site_configs = [
    {
        'base_url': 'https://www.power-technology.com/projects/',
        'link_selector': 'a[href^="https://www.power-technology.com/projects/"]',
        'urls_file': 'data/input/urls_power_technology.txt',
        'articles_output_file': 'data/input/articles_power_technology.json',
        'processed_urls_file': 'data/input/processed_urls.txt',  # File to store processed URLs
        'url_prefix': 'https://www.power-technology.com/projects/'
    },
    
    # Add more configurations as needed
]

def pipeline():
    # Step 1: Collect articles
    print("Collecting Articles... This may take a long time if there are many articles to process.")
    for config in site_configs:
        collect_articles(config)
    print("Collection Complete.\n")
    
    print("Initializing ArticleProcessor...")

    input_path = r"data\input\articles_power_technology.json"
    output_path = r"data\output\processed_data.json"
    limit = 1  # set the processing limit or None
    api_key = os.getenv("OPENAI_API_KEY", "")
    processor = ArticleProcessor(input_path=input_path, output_path=output_path, api_key=api_key, limit=limit)
    print("Starting ArticleProcessor...")
    processor.process_articles()
    print
    run_validation(output_path)
    
    data_insert.process_data()
    

if __name__ == "__main__":
    pipeline()
#cost before:   8.44, 0.23
#cost after:    9.51, 
# ~$1.10 per 20 texts analyzed
# create a workflow inputing the data into the real GESDB and making use of the pipeline
