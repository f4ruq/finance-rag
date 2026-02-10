import os
import json
import time
import requests
import sys
from datetime import datetime, timezone
import config

SEC_USER_AGENT = config.USER_AGENT

HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

OUTPUT_DIR = config.EDGAR_RAW_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)



def safe_filename(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")


def download_file(url: str, out_path: str):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)


def main(input_file=None):
    if not input_file:
        # Find the latest submissions file in EDGAR_DATA_DIR
        files = [f for f in os.listdir(config.EDGAR_DATA_DIR) if f.startswith(f"{config.EDGAR_TICKER.lower()}_submissions_") and f.endswith(".json")]
        if not files:
             print("No submission file found.")
             return
        files.sort(reverse=True)
        input_file = os.path.join(config.EDGAR_DATA_DIR, files[0])
        print(f"Using latest submission file: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    filings = payload.get("filings", [])
    print(f"Total filings in input: {len(filings)}")

    limit = 10  # download only first 10 (most recent)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for i, filing in enumerate(filings[:limit], start=1):
        accession = filing["accession_number"]
        form = filing["form"]
        filing_date = filing["filing_date"]

        base_url = filing["filing_base_url"]
        index_url = filing["index_html_url"]
        txt_url = filing["full_text_url"]

        folder_name = safe_filename(f"{filing_date}_{form}_{accession}")
        filing_dir = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(filing_dir, exist_ok=True)

        index_path = os.path.join(filing_dir, f"{accession}-index.html")
        txt_path = os.path.join(filing_dir, f"{accession}.txt")

        print(f"\n[{i}/{limit}] Downloading {form} {filing_date} {accession}")
        print(f"Index: {index_url}")
        print(f"TXT:   {txt_url}")

        try:
            download_file(index_url, index_path)
            print(f"Saved index -> {index_path}")

            download_file(txt_url, txt_path)
            print(f"Saved txt   -> {txt_path}")

        except Exception as e:
            print(f"FAILED: {e}")

        # SEC rate limiting safety
        time.sleep(1.2)

    print("\nDone.")


if __name__ == "__main__":
    main()