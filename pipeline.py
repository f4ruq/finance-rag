import argparse
import logging
import os
import shutil
import config
from datetime import datetime

# Import collectors
# Note: We import importing the modules to call them via subprocess or directly if they had main() that accepts args
# Since most have `if __name__ == "__main__": main()`, we can import `main` from them if we slightly modified them to be callable, 
# or just run them with subprocess. Given the previous changes, I've exposed `main()` in `edgar_downloader_nvda`.
# For others, I will use subprocess to ensure clean execution environments, or I can import them if I am careful.
# Using subprocess is safer for avoiding global state conflicts between scripts if any.

import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Pipeline")

def clean_directory(path: str):
    """Deletes all files in the directory but keeps the directory itself."""
    if not os.path.exists(path):
        return
    logger.info(f"Cleaning directory: {path}")
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            logger.error(f"Failed to delete {item_path}. Reason: {e}")

def run_script(script_name: str, args: list = None):
    """Runs a python script as a subprocess."""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running script: {script_name} {' '.join(args) if args else ''}")
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=False) # capture_output=False to show output in real-time
        logger.info(f"Script {script_name} finished successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with exit code {e.returncode}.")
        raise e

def run_fred():
    logger.info("Starting FRED collection...")
    # clean summary and raw fred data if needed? user said "clean old data"
    # we should probably clean config.RAW_DIR (shared?) or specific ones.
    # config.RAW_DIR is "data/raw". config.SUMMARY_DIR is "data/summary".
    # FRED uses these.
    # We will clean them in the main execution block if requested.
    run_script("fred_collector.py")

def run_gdelt():
    logger.info("Starting GDELT collection...")
    # GDELT uses config.GDELT_DATA_DIR
    run_script("gdelt.py")

def run_edgar():
    logger.info("Starting EDGAR collection pipeline...")
    # 1. Submissions
    run_script("edgar_submissions_nvda.py")
    
    # 2. Downloader
    # It will automatically pick up the latest JSON from step 1 because we updated it to do so.
    run_script("edgar_downloader_nvda.py")
    
    # 3. Primary Docs
    run_script("edgar_download_primary_docs.py")
    
    # 4. Clean Text
    run_script("edgar_clean_text.py")

def main():
    parser = argparse.ArgumentParser(description="Finance RAG Data Pipeline")
    parser.add_argument("--source", type=str, choices=["all", "fred", "gdelt", "edgar"], default="all", help="Data source to run")
    parser.add_argument("--clean", action="store_true", help="Clean data directories before running (default: True based on requirements)")
    
    # User requested: "her zaman data klasörlerinde en güncel veri olsun. eskilerin kalmasına gerek yok."
    # So we force clean by default unless logic changes. 
    # But let's keep the flag for flexibility, and default to cleaning in logic if 'all' is run or implied.
    
    args = parser.parse_args()

    # Determine directories to clean based on source
    dirs_to_clean = []
    
    if args.source in ["all", "fred"]:
        dirs_to_clean.append(config.RAW_DIR) # FRED puts raw jsons here
        dirs_to_clean.append(config.SUMMARY_DIR)
        
    if args.source in ["all", "gdelt"]:
        dirs_to_clean.append(config.GDELT_DATA_DIR)
        
    if args.source in ["all", "edgar"]:
        dirs_to_clean.append(config.EDGAR_DATA_DIR) # Submissions json
        dirs_to_clean.append(config.EDGAR_RAW_DIR)  # Raw filings
        dirs_to_clean.append(config.EDGAR_CLEAN_DIR) # Clean txt

    # Execute cleaning
    # The user request is strong: "delete old data". So we do it.
    logger.info("Performing data cleanup...")
    for d in dirs_to_clean:
         clean_directory(d)

    # Execute Pipelines
    try:
        if args.source in ["all", "fred"]:
            run_fred()
            
        if args.source in ["all", "gdelt"]:
            run_gdelt()
            
        if args.source in ["all", "edgar"]:
            run_edgar()
            
        logger.info("Pipeline execution completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
