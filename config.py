import os
from dotenv import load_dotenv

load_dotenv()

# --- Common Config ---
USER_AGENT = os.getenv("SEC_USER_AGENT")
if not USER_AGENT:
    raise ValueError("SEC_USER_AGENT not found in .env file")

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
SUMMARY_DIR = os.path.join(DATA_DIR, "summary")

# --- FRED Configuration ---
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY not found in .env file")

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES_LIST = [
    "FEDFUNDS",  # Federal Funds Rate
    "CPIAUCSL",  # Consumer Price Index
    "UNRATE",    # Unemployment Rate
    "DGS10",     # 10-Year Treasury Constant Maturity Rate
    "DGS2"       # 2-Year Treasury Constant Maturity Rate
]
FRED_START_DATE = "2020-01-01"

# --- EDGAR Configuration ---
EDGAR_TICKER = "NVDA"
EDGAR_CIK = "0001045810"
EDGAR_CIK_NO_ZERO = "1045810"
EDGAR_FORMS = {"10-K", "10-Q", "8-K"}
EDGAR_DATA_DIR = os.path.join(DATA_DIR, "edgar")
EDGAR_RAW_DIR = os.path.join(EDGAR_DATA_DIR, "raw")
EDGAR_CLEAN_DIR = os.path.join(EDGAR_DATA_DIR, "clean")


# --- GDELT Configuration ---
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = "(NVDA OR NVIDIA) sourcelang:english"
GDELT_DATA_DIR = os.path.join(DATA_DIR, "gdelt")

