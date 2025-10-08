"""
Crawler Utilities for Web Scraping
Helper functions for link extraction, sitemap parsing, and crawling utilities
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import xml.etree.ElementTree as ET
import logging
import time
from typing import List, Set

logger = logging.getLogger(__name__)

class CrawlerUtils:
    def __init__(self, base_url: str, max_depth: int = 3):
        self.base_url = base_url
        self.max_depth = max_depth
        self.session = requests.Session()
        self.visited_urls: Set[str] = set()
        
        # Set headers to appear as a legitimate browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(self.base_url)
            
            # Check if URL belongs to the same domain
            if parsed.netloc != base_parsed.netloc:
                return False
            
            # Skip common non-content URLs
            skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.ico', '.pdf']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
            
        except Exception:
            return False
    
    def extract_links_from_page(self, url: str) -> List[str]:
        """Extract all valid links from a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Find all anchor tags with href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                
                # Clean the URL (remove fragments)
                parsed = urlparse(absolute_url)
                clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                                      parsed.params, parsed.query, ''))
                
                if self.is_valid_url(clean_url) and clean_url not in self.visited_urls:
                    links.append(clean_url)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {str(e)}")
            return []
    
    def crawl_website(self, start_url: str = None, max_pages: int = 50) -> List[str]:
        """Crawl website and return list of URLs to scrape"""
        if not start_url:
            start_url = self.base_url
        
        urls_to_visit = [start_url]
        all_urls = []
        
        while urls_to_visit and len(all_urls) < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            logger.info(f"Crawling: {current_url}")
            self.visited_urls.add(current_url)
            all_urls.append(current_url)
            
            # Extract links from current page
            new_links = self.extract_links_from_page(current_url)
            urls_to_visit.extend(new_links)
            
            # Be respectful to the server
            time.sleep(1)
        
        return all_urls
    
    def parse_sitemap(self, sitemap_url: str = None) -> List[str]:
        """Parse XML sitemap and extract URLs"""
        if not sitemap_url:
            sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        
        try:
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Handle different sitemap namespaces
            namespaces = {
                'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }
            
            urls = []
            
            # Check if it's a sitemap index
            sitemap_elements = root.findall('.//sitemap:sitemap', namespaces)
            if sitemap_elements:
                for sitemap in sitemap_elements:
                    loc_element = sitemap.find('sitemap:loc', namespaces)
                    if loc_element is not None:
                        # Recursively parse individual sitemaps
                        sub_urls = self.parse_sitemap(loc_element.text)
                        urls.extend(sub_urls)
            else:
                # Parse individual URLs
                url_elements = root.findall('.//sitemap:url', namespaces)
                for url_element in url_elements:
                    loc_element = url_element.find('sitemap:loc', namespaces)
                    if loc_element is not None:
                        url = loc_element.text
                        if self.is_valid_url(url):
                            urls.append(url)
            
            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {str(e)}")
            return []
    
    def get_robots_txt(self) -> str:
        """Fetch and return robots.txt content"""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            response = self.session.get(robots_url, timeout=10)
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.error(f"Error fetching robots.txt: {str(e)}")
            return ""
    
    def discover_urls(self, use_sitemap: bool = True, crawl_depth: int = 2) -> List[str]:
        """Discover URLs using multiple methods"""
        all_urls = set()
        
        # Try sitemap first
        if use_sitemap:
            sitemap_urls = self.parse_sitemap()
            all_urls.update(sitemap_urls)
            logger.info(f"Found {len(sitemap_urls)} URLs from sitemap")
        
        # Crawl website if we don't have enough URLs
        if len(all_urls) < 10:  # Adjust threshold as needed
            crawled_urls = self.crawl_website(max_pages=50)
            all_urls.update(crawled_urls)
            logger.info(f"Found {len(crawled_urls)} URLs from crawling")
        
        return list(all_urls)

def main():
    """Example usage of crawler utilities"""
    base_url = "https://www.kgisl.com"
    crawler = CrawlerUtils(base_url)
    
    # Discover URLs
    urls = crawler.discover_urls()
    
    print(f"Discovered {len(urls)} URLs:")
    for url in urls[:10]:  # Print first 10 URLs
        print(f"  - {url}")

if __name__ == "__main__":
    main()