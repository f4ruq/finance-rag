import requests
import json
from datetime import datetime, timezone
BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERY = "(title:NVDA OR title:NVIDIA) sourcelang:english"
MODE = "ArtList"
FORMAT = "json"
MAX_RECORDS = 50

# last 7 days
START_DATETIME = (datetime.now(timezone.utc).replace(microsecond=0)).strftime("%Y%m%d%H%M%S")

# Manually construct URL to control encoding
# GDELT requires %20 for spaces and usually prefers no encoding for parentheses in some contexts, 
# or specific encoding. Let's try fully encoded.
import urllib.parse
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
    print(f"Response URL: {r.url}")
    print(f"Response Text: {r.text[:500]}")
    exit(1)

articles = data.get("articles", [])
print(f"Total articles fetched (raw): {len(articles)}")

# Client-side filtering for Title
filtered_articles = [
    a for a in articles 
    if a.get("title") and ("NVDA" in a["title"].upper() or "NVIDIA" in a["title"].upper())
]

print(f"Total articles after title filtering: {len(filtered_articles)}\n")

print("First 10 filtered articles:\n")
for i, a in enumerate(filtered_articles[:10], start=1):
    print(f"{i}. {a.get('seendate')} | {a.get('sourceCountry')} | {a.get('domain')}")
    print(f"   {a.get('title')}")
    print(f"   {a.get('url')}\n")

# Save filtered output
out_file = f"gdelt_nvda_{START_DATETIME}.json"
output_data = {
    "fetched_at_utc": START_DATETIME,
    "query": QUERY_STRING,
    "total_raw": len(articles),
    "total_filtered": len(filtered_articles),
    "articles": filtered_articles
}

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Saved full response to: {out_file}")