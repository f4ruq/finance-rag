import os
from bs4 import BeautifulSoup
import config

RAW_DIR = config.EDGAR_RAW_DIR
CLEAN_DIR = config.EDGAR_CLEAN_DIR

os.makedirs(CLEAN_DIR, exist_ok=True)


def html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "lxml")

    # remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # basic cleanup: remove excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def run(use_blob: bool = False):
    total_converted = 0

    if use_blob:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "azure"))
        from blob_helper import list_blobs, download_text, upload_text, blob_exists
        from config_cloud import CONTAINER_RAW, CONTAINER_CLEAN, BLOB_PATHS
        
        all_blobs = list_blobs(CONTAINER_RAW, prefix="edgar/raw/")
        
        # Sadece .htm veya .html ile biten ve -index.html OLMAYAN blobları bul
        htm_blobs = [
            b for b in all_blobs 
            if (b.endswith(".htm") or b.endswith(".html")) and not b.endswith("-index.html")
        ]
        
        print(f"Scanning {len(htm_blobs)} primary doc blobs in Blob Storage...\n")
        
        for blob_path in htm_blobs:
            # blob_path: edgar/raw/20240221_10-K_000104581024000029/nvda-20240128.htm
            parts = blob_path.split("/")
            if len(parts) < 4:
                continue
                
            folder = parts[2]
            filename = parts[3]
            
            out_blob_name = BLOB_PATHS["edgar_clean"].format(folder=folder, filename=filename + ".txt")
            
            if blob_exists(CONTAINER_CLEAN, out_blob_name):
                continue
                
            html_content = download_text(CONTAINER_RAW, blob_path)
            clean_text = html_to_text(html_content)
            
            upload_text(CONTAINER_CLEAN, out_blob_name, clean_text)
            
            total_converted += 1
            print(f"Converted Blob: {CONTAINER_RAW}/{blob_path} -> {CONTAINER_CLEAN}/{out_blob_name}")
            
        print(f"\nDone. Total converted: {total_converted}")
        return

    # LOCAL DISK EXECUTION
    if not os.path.exists(RAW_DIR):
        raise ValueError(f"{RAW_DIR} not found. Ensure raw downloaded data exists.")

    filing_folders = sorted(os.listdir(RAW_DIR))
    print(f"Scanning {len(filing_folders)} filing folders...\n")

    for folder in filing_folders:
        folder_path = os.path.join(RAW_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        # find .htm files (primary docs)
        htm_files = [
            f for f in os.listdir(folder_path)
            if (f.endswith(".htm") or f.endswith(".html"))
            and not f.endswith("-index.html")
        ]

        if not htm_files:
            continue

        out_folder = os.path.join(CLEAN_DIR, folder)
        os.makedirs(out_folder, exist_ok=True)

        for htm_file in htm_files:
            in_path = os.path.join(folder_path, htm_file)
            out_path = os.path.join(out_folder, htm_file + ".txt")

            if os.path.exists(out_path):
                continue

            with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

            clean_text = html_to_text(html_content)

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(clean_text)

            total_converted += 1
            print(f"Converted: {in_path} -> {out_path}")

    print(f"\nDone. Total converted: {total_converted}")


if __name__ == "__main__":
    run(use_blob=False)