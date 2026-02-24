import requests
from bs4 import BeautifulSoup
from newspaper import Article
from newspaper.article import ArticleException
import json
# import logging
import os

# # Configure logging
# logging.basicConfig(
#     level=print,  # Set to DEBUG for more detailed output
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]  # Log to console
# )

def read_existing_urls(urls_file):
    """
    Reads URLs from a given file and returns them as a set.

    Parameters
    ----------
    urls_file : str
        The file path where URLs are stored.

    Returns
    -------
    set
        A set of URLs read from the file.

    Notes
    -----
    If the file does not exist, an empty set is returned.
    """
    try:
        with open(urls_file, 'r') as file:
            urls = set(url.strip() for url in file.readlines())
            print(f"Read {len(urls)} existing URLs from {urls_file}.")
            return urls
    except FileNotFoundError:
        print(f"No existing URLs file found at {urls_file}. Starting fresh.")
        return set()

def gather_urls(base_url, link_selector, existing_urls, url_prefix=None):
    """
    Gathers all article URLs from the base URL using the specified CSS selector,
    avoiding duplicates.

    Parameters
    ----------
    base_url : str
        The base URL of the website to scrape.
    link_selector : str
        The CSS selector used to identify article links on the webpage.
    existing_urls : set
        A set of URLs that have already been processed.
    url_prefix : str, optional
        A prefix that URLs must start with to be considered (default is None).

    Returns
    -------
    list
        A list of new URLs found on the page that are not already in the existing URLs set.

    Raises
    ------
    requests.exceptions.RequestException
        If the HTTP request to the base URL fails.
    """
    print(f"Gathering URLs from {base_url}...")
    try:
        response = requests.get(base_url)
        response.raise_for_status()  # Ensure we catch bad HTTP responses
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {base_url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    new_urls = set()

    for a in soup.select(link_selector):
        href = a.get('href')
        if href:
            # Apply prefix filtering if specified and check for duplicates
            if (url_prefix is None or href.startswith(url_prefix)) and href not in existing_urls:
                new_urls.add(href)

    print(f"Found {len(new_urls)} new URLs.")
    return list(new_urls)

def extract_article_content(url):
    """
    Extracts the content of an article given its URL.

    Parameters
    ----------
    url : str
        The URL of the article to extract.

    Returns
    -------
    dict or None
        A dictionary containing the article's title, text, and source URL,
        or None if the extraction failed.

    Notes
    -----
    - The function uses the `newspaper3k` library to parse articles.
    """
    print(f"Extracting content from {url}...")
    try:
        article = Article(url)
        article.download()
        article.parse()
        if not article.title or not article.text:
            print(f"Article from {url} is missing title or text, skipping.")
            return None
        return {
            'title': article.title,
            'text': article.text,
            'source': url
        }
    except ArticleException as e:
        print(f"ArticleException for {url}: {e}")
        return None
    except Exception as e:
        print(f"Failed to extract {url}: {type(e).__name__} - {e}")
        return None

def collect_articles(config):
    """
    Collects new article URLs, extracts their content, and saves the data to files.

    Parameters
    ----------
    config : dict
        A dictionary containing configuration parameters:
            - base_url (str): The base URL of the website to scrape.
            - link_selector (str): The CSS selector for article links.
            - urls_file (str): The file path where URLs are stored.
            - articles_output_file (str): The file path where articles will be saved.
            - url_prefix (str, optional): A prefix that URLs must start with to be considered.

    Returns
    -------
    None
    """

    base_url = config['base_url']
    link_selector = config['link_selector']
    urls_file = config.get('urls_file', 'urls.txt')
    articles_output_file = config.get('articles_output_file', 'articles.json')
    url_prefix = config.get('url_prefix', None)

    # Step 1: Read existing URLs
    existing_urls = read_existing_urls(urls_file)

    # Step 2: Gather all article URLs from the main page
    article_urls = gather_urls(base_url, link_selector, existing_urls, url_prefix=url_prefix)

    if not article_urls:
        print("No new URLs found.")
        return

    # Ensure the directory for urls_file exists
    os.makedirs(os.path.dirname(urls_file), exist_ok=True)

    # Step 3: Write new URLs to the file, avoiding duplicates
    print(f"Writing {len(article_urls)} new URLs to {urls_file}...")
    with open(urls_file, 'a') as url_file:
        for url in article_urls:
            if url not in existing_urls:  # Avoid writing duplicates
                url_file.write(url + '\n')
    print(f"New URLs have been written to {urls_file}.")


    # Step 4: Extract content from each new article URL
    print("Extracting content from new URLs...")
    articles = []
    for idx, url in enumerate(article_urls, start=1):
        article = extract_article_content(url)
        if article:
            articles.append(article)
            print(f"Extracted article {idx}/{len(article_urls)}: {url}")

    print("Content extraction completed.")

    # Step 5: Save the extracted articles to a JSON file
    print(f"Saving extracted articles to {articles_output_file}...")
    with open(articles_output_file, 'w') as f:
        json.dump(articles, f, indent=2)
    print(f"Articles have been saved to {articles_output_file}.")
