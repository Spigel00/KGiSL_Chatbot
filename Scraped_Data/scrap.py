!pip install BeautifulSoup
import requests
from bs4 import BeautifulSoup

url = "https://www.kgkite.ac.in/sitemap.xml"
r = requests.get(url)
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "xml")
    urls = [loc.text for loc in soup.find_all("loc")]
    print(f"Found {len(urls)} pages in sitemap.")
    for u in urls[:10]:
        print(u)
else:
    print("No sitemap found.")



import requests
from bs4 import BeautifulSoup

sitemaps = [
    "https://www.kgkite.ac.in/page-sitemap.xml",
    "https://www.kgkite.ac.in/news-and-event-sitemap.xml",
    "https://www.kgkite.ac.in/blog-sitemap.xml"
]

for sitemap in sitemaps:
    response = requests.get(sitemap)
    soup = BeautifulSoup(response.content, "xml")
    urls = soup.find_all("loc")
    print(f"{sitemap} → {len(urls)} URLs found")


# 🚀 Extract URLs from KGiSL sitemaps (page, news, blog)
# =====================================================

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# List of sitemap URLs
sitemaps = [
    "https://www.kgkite.ac.in/page-sitemap.xml",
    "https://www.kgkite.ac.in/news-and-event-sitemap.xml",
    "https://www.kgkite.ac.in/blog-sitemap.xml"
]

all_urls = []

for sitemap_url in sitemaps:
    print(f"📄 Fetching: {sitemap_url}")
    try:
        r = requests.get(sitemap_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")

        urls = [loc.text.strip() for loc in soup.find_all("loc")]
        print(f"  ➤ Found {len(urls)} URLs")

        for url in urls:
            all_urls.append({
                "sitemap": sitemap_url,
                "url": url,
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        print(f"  ❌ Failed to fetch {sitemap_url}: {e}")

# Convert to DataFrame
df = pd.DataFrame(all_urls)
print(f"\n✅ Total URLs found across all sitemaps: {len(df)}")

# Save to CSV for cross-checking later
output_file = "kgisl_all_sitemap_urls.csv"
df.to_csv(output_file, index=False)
print(f"📁 Saved list to: {output_file}")

# Display sample URLs
df.head(10)


# ========================================
# 📦 Install dependencies
# ========================================
!pip install requests beautifulsoup4 tqdm pandas

# ========================================
# 📚 Import libraries
# ========================================
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from tqdm import tqdm
from datetime import datetime
import time

# ========================================
# 📁 Load sitemap URLs
# ========================================
csv_path = "kgisl_all_sitemap_urls.csv"  # your file path
urls_df = pd.read_csv(csv_path)

# Existing URLs from CSV
urls = urls_df['url'].dropna().unique().tolist()

# ✅ Add your custom URLs here
extra_urls = [
    "https://www.kgkite.ac.in/blog/role-ai-learning-engineering-education/",
    "https://www.kgkite.ac.in/blog/smt-divyalakshmi-awards-and-kindathon-2025/",
    "https://www.kgkite.ac.in/common-setting/common-setting/"
]

# Merge & remove duplicates
urls = list(set(urls + extra_urls))

print(f"Total URLs found (including extra): {len(urls)}")


# ========================================
# ⚙️ Helper: extract visible text from page
# ========================================
def extract_text_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {"url": url, "status": resp.status_code, "text": ""}

        soup = BeautifulSoup(resp.text, "html.parser")

        # remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())  # clean extra spaces

        return {
            "url": url,
            "status": resp.status_code,
            "timestamp": datetime.now().isoformat(),
            "length": len(text),
            "text": text
        }
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e), "text": ""}

# ========================================
# 🧾 Crawl each page & collect data
# ========================================
results = []
for url in tqdm(urls, desc="Scraping pages"):
    data = extract_text_from_url(url)
    results.append(data)
    time.sleep(1)  # be polite (avoid ban)

# ========================================
# 💾 Save results
# ========================================
json_path = "kgisl_pages_content.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(results)} pages to {json_path}")

# ========================================
# 📉 Optional: summary
# ========================================
ok = sum(1 for r in results if r['status'] == 200 and len(r['text']) > 0)
fail = sum(1 for r in results if r['status'] != 200 or len(r['text']) == 0)
print(f"\nSuccessful: {ok} | Failed: {fail}")


  import json

  # Load scraped pages
  with open("kgisl_pages_content.json", "r", encoding="utf-8") as f:
      pages = json.load(f)

  print(f"Loaded {len(pages)} pages")

  # ----------------------------------------
  # Function to search pages by keyword
  # ----------------------------------------
  def search_pages(query, pages, top_n=3):
      """
      Simple demo search: returns top_n pages containing the query
      """
      query = query.lower()
      results = []

      for page in pages:
          text = page.get("text", "").lower()
          if query in text:
              # count occurrences as a simple relevance score
              score = text.count(query)
              results.append({"url": page["url"], "score": score, "text_snippet": text[:300]})

      # sort by score descending
      results = sorted(results, key=lambda x: x["score"], reverse=True)

      return results[:top_n]

  # ----------------------------------------
  # Demo: ask a question
  # ----------------------------------------
  query = "school of innovation"
  results = search_pages(query, pages)

  print(f"\nTop results for: '{query}'\n")
  for r in results:
      print(f"URL: {r['url']}\nScore: {r['score']}\nSnippet: {r['text_snippet']}\n{'-'*80}")
