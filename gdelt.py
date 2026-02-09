import os
import requests
import json
from datetime import datetime, timezone, timedelta
import urllib.parse
from collections import Counter

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = "(title:NVDA OR title:NVIDIA) sourcelang:english"
MODE = "ArtList"
FORMAT = "json"
MAX_RECORDS = 50
DATA_DIR = "data/gdelt"

# Ensure output directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# last 7 days
START_DATETIME = (datetime.now(timezone.utc).replace(microsecond=0)).strftime("%Y%m%d%H%M%S")

# Manually construct URL to control encoding
QUERY_STRING = "(NVDA OR NVIDIA) sourcelang:english"
encoded_query = urllib.parse.quote(QUERY_STRING)

url = f"{BASE_URL}?query={encoded_query}&mode={MODE}&format={FORMAT}&maxrecords={MAX_RECORDS}&sort=datedesc"

print(f"Requesting URL: {url}\n")
r = requests.get(url)

try:
    r.raise_for_status()
    data = r.json()
except Exception as e:
    print(f"Error: {e}")
    try:
        print(f"Response Text: {r.text[:500]}")
    except:
        pass
    exit(1)

articles = data.get("articles", [])
print(f"Total articles fetched (raw): {len(articles)}")

# Client-side filtering for Title
filtered_articles = [
    a for a in articles 
    if a.get("title") and ("NVDA" in a["title"].upper() or "NVIDIA" in a["title"].upper())
]

print(f"Total articles after title filtering: {len(filtered_articles)}")

# --- Cleaning & Deduplication ---

def normalize_url(url_str):
    if not url_str:
        return ""
    # Enforce https
    if url_str.startswith("http://"):
        url_str = "https://" + url_str[7:]
    
    parsed = urllib.parse.urlparse(url_str)
    # Remove query parameters (like utm_source)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return clean_url

unique_urls = set()
unique_title_domain = set()
clean_articles = []

for a in filtered_articles:
    raw_url = a.get("url", "")
    title = a.get("title", "").strip()
    domain = a.get("domain", "").strip()
    
    clean_url = normalize_url(raw_url)
    
    # Deduplication checks
    if clean_url in unique_urls:
        continue
    
    # Check title+domain pair
    td_key = (title, domain)
    if td_key in unique_title_domain:
        continue

    unique_urls.add(clean_url)
    unique_title_domain.add(td_key)
    
    # Update article with clean URL
    a["url"] = clean_url
    clean_articles.append(a)

print(f"Total articles after deduplication: {len(clean_articles)}\n")

# --- Statistics ---

domains = [a.get("domain") for a in clean_articles if a.get("domain")]
domain_counts = Counter(domains)
top_5_domains = dict(domain_counts.most_common(5))
unique_domain_count = len(domain_counts)

# Daily counts (last 7 days based on 'seendate')
# seendate format in GDELT: YYYYMMDDTHHMMSSZ
daily_counts = Counter()
today = datetime.now(timezone.utc).date()

for a in clean_articles:
    sd = a.get("seendate")
    if sd:
        try:
            # Parse '20250209T140000Z'
            dt = datetime.strptime(sd, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            date_str = str(dt.date())
            daily_counts[date_str] += 1
        except ValueError:
            pass

# Output Structure
output_data = {
    "fetched_at_utc": START_DATETIME,
    "query": QUERY_STRING,
    "total_raw": len(articles),
    "total_filtered": len(filtered_articles),
    "total_unique": len(clean_articles),
    "unique_domains": unique_domain_count,
    "top_domains": top_5_domains,
    "daily_counts": dict(daily_counts),
    "articles": clean_articles
}

out_file = os.path.join(DATA_DIR, f"gdelt_nvda_clean_{START_DATETIME}.json")

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Saved clean response to: {out_file}")
print("Stats:")
print(f" - Unique Domains: {unique_domain_count}")
print(f" - Top Domains: {top_5_domains}")