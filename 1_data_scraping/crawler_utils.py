# crawler_utils.py
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse

# Download any file (PDF, XLS, etc.)
def download_file(url, save_dir='downloads'):
    os.makedirs(save_dir, exist_ok=True)
    local_filename = os.path.join(save_dir, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

# Extract all content URLs from sitemap and subsitemaps
def get_sitemap_links(sitemap_url):
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'xml')
    sub_sitemaps = [loc.text for loc in soup.find_all('loc')]

    all_links = []
    for sub_url in sub_sitemaps:
        sub_response = requests.get(sub_url)
        sub_soup = BeautifulSoup(sub_response.content, 'xml')
        all_links.extend([loc.text for loc in sub_soup.find_all('loc')])

    return all_links

# Recursively crawl pages to find all PDF links
def find_all_pdf_links(start_url, max_depth=3):
    visited = set()
    pdf_links = set()

    def crawl(url, depth):
        if url in visited or depth == 0:
            return
        visited.add(url)
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                full_url = urljoin(url, href)
                if full_url.lower().endswith('.pdf'):
                    pdf_links.add(full_url)
                elif is_internal_link(full_url, start_url):
                    crawl(full_url, depth - 1)
        except Exception:
            pass

    def is_internal_link(link, base):
        return urlparse(link).netloc == urlparse(base).netloc

    crawl(start_url, max_depth)
    return list(pdf_links)
