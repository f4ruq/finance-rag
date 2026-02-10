import os
from bs4 import BeautifulSoup
import config

RAW_DIR = config.EDGAR_RAW_DIR
CLEAN_DIR = config.EDGAR_CLEAN_DIR

os.makedirs(CLEAN_DIR, exist_ok=True)


def html_to_text(html_path: str) -> str:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # basic cleanup: remove excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def main():
    filing_folders = sorted(os.listdir(RAW_DIR))
    print(f"Scanning {len(filing_folders)} filing folders...\n")

    total_converted = 0

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

            clean_text = html_to_text(in_path)

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(clean_text)

            total_converted += 1
            print(f"Converted: {in_path} -> {out_path}")

    print(f"\nDone. Total converted: {total_converted}")


if __name__ == "__main__":
    main()