import json
import requests
from bs4 import BeautifulSoup
from crawler_utils import get_sitemap_links

SITEMAP_URL = 'https://www.kgkite.ac.in/sitemap.xml'

def parse_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return {
            'title': soup.title.string if soup.title else '',
            'headings': [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])],
            'paragraphs': [p.get_text() for p in soup.find_all('p')],
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    links = get_sitemap_links(SITEMAP_URL)
    html_links = [url for url in links if 'kgkite.ac.in' in url and not url.lower().endswith(('.pdf', '.xls', '.xlsx'))]
    data = {}
    print(f"Found {len(html_links)} HTML pages")

    for link in html_links:
        print(f"Processing: {link}")
        data[link] = parse_html_content(link)

    with open('html_data.json', 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    main()
