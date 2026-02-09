import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")
if not SEC_USER_AGENT:
    raise ValueError("SEC_USER_AGENT not found in .env file")

CIK = "0001045810"          # NVDA (10-digit)
CIK_NO_ZERO = "1045810"     # same CIK but without leading zeros

SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"

HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

DATA_DIR = "data/edgar"
os.makedirs(DATA_DIR, exist_ok=True)

STAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def accession_folder(accession_number: str) -> str:
    # "0001588670-26-000004" -> "000158867026000004"
    return accession_number.replace("-", "")


def build_filing_base_url(accession_number: str) -> str:
    folder = accession_folder(accession_number)
    return f"https://www.sec.gov/Archives/edgar/data/{CIK_NO_ZERO}/{folder}/"


def main():
    TARGET_FORMS = {"10-K", "10-Q", "8-K"}

    print(f"Filtering for forms: {TARGET_FORMS}\n")
    print(f"Requesting: {SUBMISSIONS_URL}\n")

    r = requests.get(SUBMISSIONS_URL, headers=HEADERS)
    r.raise_for_status()

    data = r.json()

    filings_recent = data.get("filings", {}).get("recent", {})
    accession_numbers = filings_recent.get("accessionNumber", [])
    filing_dates = filings_recent.get("filingDate", [])
    forms = filings_recent.get("form", [])
    primary_docs = filings_recent.get("primaryDocument", [])

    total = len(accession_numbers)
    print(f"Total recent filings found: {total}\n")

    limit = 20  # Increased limit to find enough matching forms
    results = []
    
    found_count = 0

    print(f"Scanning filings...\n")

    for i in range(total):
        form = forms[i] if i < len(forms) else None
        
        if form not in TARGET_FORMS:
            continue
            
        accession = accession_numbers[i]
        filing_date = filing_dates[i] if i < len(filing_dates) else None
        primary_doc = primary_docs[i] if i < len(primary_docs) else None

        base_url = build_filing_base_url(accession)

        filing_date = filing_dates[i] if i < len(filing_dates) else None
        primary_doc = primary_docs[i] if i < len(primary_docs) else None

        base_url = build_filing_base_url(accession)

        item = {
            "accession_number": accession,
            "form": form,
            "filing_date": filing_date,
            "primary_document": primary_doc,
            "filing_base_url": base_url,
            "index_html_url": base_url + f"{accession}-index.html",
            "full_text_url": base_url + f"{accession}.txt"
        }

        results.append(item)

        if len(results) >= limit:
            break

        found_count += 1
        print(f"{found_count}. {filing_date} | {form} | {accession}")
        print(f"   base:  {base_url}")
        print(f"   index: {item['index_html_url']}")
        print(f"   txt:   {item['full_text_url']}")
        print()

    out_path = os.path.join(DATA_DIR, f"nvda_submissions_{STAMP}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "ticker": "NVDA",
            "cik": CIK,
            "fetched_at_utc": STAMP,
            "count": len(results),
            "filings": results
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved output to: {out_path}")


if __name__ == "__main__":
    main()