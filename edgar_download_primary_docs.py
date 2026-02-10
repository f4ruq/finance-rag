import os
import time
import requests
from bs4 import BeautifulSoup
import config

SEC_USER_AGENT = config.USER_AGENT

HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}

RAW_DIR = config.EDGAR_RAW_DIR


def download_file(url: str, out_path: str):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)


def find_primary_doc(index_html_path: str, target_form: str):
    """
    Parses the EDGAR index.html file and finds the document
    whose Type matches target_form (10-Q / 10-K / 8-K).
    Returns the filename if found.
    """
    with open(index_html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    table = soup.find("table", class_="tableFile", summary="Document Format Files")
    if not table:
        return None

    rows = table.find_all("tr")
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        # The document name is usually in an <a> tag inside the cell
        a_tag = cols[2].find("a")
        if a_tag:
            doc_name = a_tag.get_text(strip=True)
        else:
            doc_name = cols[2].get_text(strip=True)
        doc_type = cols[3].get_text(strip=True)

        if doc_type.upper() == target_form.upper():
            return doc_name

    return None


def main():
    if not os.path.exists(RAW_DIR):
        raise ValueError(f"{RAW_DIR} not found. Run the downloader first.")

    filing_folders = sorted(os.listdir(RAW_DIR))
    print(f"Found {len(filing_folders)} filing folders.\n")

    for folder in filing_folders:
        folder_path = os.path.join(RAW_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        files = os.listdir(folder_path)
        index_files = [f for f in files if f.endswith("-index.html")]

        if not index_files:
            print(f"Skipping {folder} (no index.html found)")
            continue

        index_file = index_files[0]
        index_path = os.path.join(folder_path, index_file)

        # folder naming format: YYYY-MM-DD_FORM_ACCESSION
        parts = folder.split("_")
        if len(parts) < 2:
            print(f"Skipping {folder} (unexpected folder name)")
            continue

        target_form = parts[1]

        # base url is in the txt filename pattern
        accession = index_file.replace("-index.html", "")
        accession_no_dash = accession.replace("-", "")

        # extract cik from folder structure? we hardcode NVDA cik no-zero
        cik_no_zero = "1045810"

        base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession_no_dash}/"

        primary_doc_name = find_primary_doc(index_path, target_form)

        if not primary_doc_name:
            print(f"[{folder}] No primary doc found for form {target_form}")
            continue

        primary_url = base_url + primary_doc_name
        out_path = os.path.join(folder_path, primary_doc_name)

        if os.path.exists(out_path):
            print(f"[{folder}] Already downloaded: {primary_doc_name}")
            continue

        print(f"[{folder}] Downloading primary doc: {primary_doc_name}")
        print(f"URL: {primary_url}")

        try:
            download_file(primary_url, out_path)
            print(f"Saved -> {out_path}\n")
        except Exception as e:
            print(f"FAILED: {e}\n")

        time.sleep(1.2)

    print("Done.")


if __name__ == "__main__":
    main()