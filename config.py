import os
from dotenv import load_dotenv

load_dotenv()

# FRED API Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY not found in .env file")

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Data Series to Fetch
SERIES_LIST = [
    "FEDFUNDS",  # Federal Funds Rate
    "CPIAUCSL",  # Consumer Price Index
    "UNRATE",    # Unemployment Rate
    "DGS10",     # 10-Year Treasury Constant Maturity Rate
    "DGS2"       # 2-Year Treasury Constant Maturity Rate
]

# Fetch Configuration
START_DATE = "2020-01-01"

# Paths
DATA_DIR = "data/fred"
RAW_DIR = os.path.join(DATA_DIR, "raw")
SUMMARY_DIR = os.path.join(DATA_DIR, "summary")
