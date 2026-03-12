import os
import sys
import logging
import requests
import json
from datetime import datetime, timezone
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


def normalize_url(url_str):
    if not url_str:
        return ""
    if url_str.startswith("http://"):
        url_str = "https://" + url_str[7:]
    parsed = urllib.parse.urlparse(url_str)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return clean_url


def run(use_blob: bool = False):
    """Pipeline ve Azure Functions tarafından çağrılacak ana fonksiyon."""

    BASE_URL    = config.GDELT_BASE_URL
    QUERY_STRING = config.GDELT_QUERY
    MODE        = "ArtList"
    FORMAT      = "json"
    MAX_RECORDS = 50
    DATA_DIR    = config.GDELT_DATA_DIR

    START_DATETIME = (datetime.now(timezone.utc).replace(microsecond=0)).strftime("%Y%m%d%H%M%S")

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
        except Exception:
            pass
        logger.warning("GDELT API is currently down or unreachable. Exiting gracefully.")
        return

    articles = data.get("articles", [])
    logger.info(f"Total articles fetched (raw): {len(articles)}")

    # Client-side filtering for Title
    filtered_articles = [
        a for a in articles
        if a.get("title") and ("NVDA" in a["title"].upper() or "NVIDIA" in a["title"].upper())
    ]
    logger.info(f"Total articles after title filtering: {len(filtered_articles)}")

    # --- Cleaning & Deduplication ---
    unique_urls = set()
    unique_title_domain = set()
    clean_articles = []

    for a in filtered_articles:
        raw_url  = a.get("url", "")
        title    = a.get("title", "").strip()
        domain   = a.get("domain", "").strip()
        clean_url = normalize_url(raw_url)

        if clean_url in unique_urls:
            continue
        td_key = (title, domain)
        if td_key in unique_title_domain:
            continue

        unique_urls.add(clean_url)
        unique_title_domain.add(td_key)
        a["url"] = clean_url
        clean_articles.append(a)

    logger.info(f"Total articles after deduplication: {len(clean_articles)}")

    # --- Statistics ---
    domains = [a.get("domain") for a in clean_articles if a.get("domain")]
    domain_counts = Counter(domains)
    top_5_domains = dict(domain_counts.most_common(5))
    unique_domain_count = len(domain_counts)

    daily_counts: Counter = Counter()
    for a in clean_articles:
        sd = a.get("seendate")
        if sd:
            try:
                dt = datetime.strptime(sd, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                daily_counts[str(dt.date())] += 1
            except ValueError:
                pass

    output_data = {
        "fetched_at_utc":   START_DATETIME,
        "query":            QUERY_STRING,
        "total_raw":        len(articles),
        "total_filtered":   len(filtered_articles),
        "total_unique":     len(clean_articles),
        "unique_domains":   unique_domain_count,
        "top_domains":      top_5_domains,
        "daily_counts":     dict(daily_counts),
        "articles":         clean_articles,
    }

    filename = f"gdelt_nvda_clean_{START_DATETIME}.json"

    if use_blob:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "azure"))
        from blob_helper import upload_json
        from config_cloud import CONTAINER_RAW, CONTAINER_CLEAN, BLOB_PATHS
        
        # Raw data'yı raw container'a kaydet
        blob_name = BLOB_PATHS["gdelt"].format(filename=filename)
        upload_json(CONTAINER_RAW, blob_name, output_data)
        logger.info(f"Raw blob'a yüklendi: {CONTAINER_RAW}/{blob_name}")
        
        # Clean/filtered data'yı clean container'a da kaydet (RAG için)
        upload_json(CONTAINER_CLEAN, blob_name, output_data)
        logger.info(f"Clean blob'a yüklendi: {CONTAINER_CLEAN}/{blob_name}")
    else:
        os.makedirs(DATA_DIR, exist_ok=True)
        out_file = os.path.join(DATA_DIR, filename)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved clean response to: {out_file}")

    logger.info(f" - Unique Domains: {unique_domain_count}")
    logger.info(f" - Top Domains: {top_5_domains}")


if __name__ == "__main__":
    run(use_blob=False)