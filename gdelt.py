import os
import logging
import requests
import json
from datetime import datetime, timezone, timedelta
import urllib.parse
from collections import Counter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = config.GDELT_BASE_URL
QUERY = config.GDELT_QUERY
MODE = "ArtList"
FORMAT = "json"
MAX_RECORDS = 50
DATA_DIR = config.GDELT_DATA_DIR

# Ensure output directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# last 7 days
START_DATETIME = (datetime.now(timezone.utc).replace(microsecond=0)).strftime("%Y%m%d%H%M%S")

# Manually construct URL to control encoding
# We used to hardcode "(NVDA OR NVIDIA) sourcelang:english", now we use config
# But config.GDELT_QUERY is the full string. We expect the user to have put the right query in config.
QUERY_STRING = config.GDELT_QUERY
encoded_query = urllib.parse.quote(QUERY_STRING)

url = f"{BASE_URL}?query={encoded_query}&mode={MODE}&format={FORMAT}&maxrecords={MAX_RECORDS}&sort=datedesc"

logger.info(f"Requesting URL: {url}")

# Setup Retry logic
session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

try:
    r = session.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
except Exception as e:
    logger.error(f"Failed to fetch GDELT data: {e}")
    try:
        logger.error(f"Response Text: {r.text[:500]}")
    except:
        pass
    exit(1)

articles = data.get("articles", [])
logger.info(f"Total articles fetched (raw): {len(articles)}")

# Client-side filtering for Title
filtered_articles = [
    a for a in articles 
    if a.get("title") and ("NVDA" in a["title"].upper() or "NVIDIA" in a["title"].upper())
]

logger.info(f"Total articles after title filtering: {len(filtered_articles)}")

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

logger.info(f"Total articles after deduplication: {len(clean_articles)}")

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

logger.info(f"Saved clean response to: {out_file}")
logger.info("Stats:")
logger.info(f" - Unique Domains: {unique_domain_count}")
logger.info(f" - Top Domains: {top_5_domains}")