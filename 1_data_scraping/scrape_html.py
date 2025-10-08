"""
HTML Web Scraper for KGiSL Website
Scrapes HTML pages and extracts text content for chatbot training
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin, urlparse
import time
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTMLScraper:
    def __init__(self, base_url="https://www.kgisl.com", output_dir="raw_data"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.scraped_urls = set()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def get_page_content(self, url):
        """Fetch and parse HTML content from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': text,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_page(self, url):
        """Scrape a single page and save to JSON"""
        if url in self.scraped_urls:
            return
        
        logger.info(f"Scraping: {url}")
        content = self.get_page_content(url)
        
        if content:
            # Generate filename from URL
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}.json"
            filename = filename.replace('__', '_').strip('_')
            
            # Save to file
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            self.scraped_urls.add(url)
            logger.info(f"Saved: {filepath}")
    
    def scrape_multiple_pages(self, urls):
        """Scrape multiple pages with progress bar"""
        for url in tqdm(urls, desc="Scraping pages"):
            self.scrape_page(url)
            time.sleep(1)  # Be respectful to the server

def main():
    scraper = HTMLScraper()
    
    # Example URLs to scrape
    urls_to_scrape = [
        "https://www.kgisl.com/",
        "https://www.kgisl.com/about",
        "https://www.kgisl.com/services",
        "https://www.kgisl.com/careers",
        "https://www.kgisl.com/contact"
    ]
    
    scraper.scrape_multiple_pages(urls_to_scrape)

if __name__ == "__main__":
    main()