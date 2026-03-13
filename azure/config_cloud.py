"""
config_cloud.py — Azure ortamı için merkezi yapılandırma.
Yerel config.py'ye dokunmaz; sadece cloud modunda import edilir.
Tüm secret'lar environment variable veya Key Vault üzerinden okunur.
"""
import os

# ── Azure Storage ─────────────────────────────────────────────────────────────
# Azure Portal'dan: Storage Account > Endpoints > Blob service URL
STORAGE_ACCOUNT_URL: str = os.environ.get(
    "STORAGE_ACCOUNT_URL",
    "https://<storage-account-name>.blob.core.windows.net"
)

CONTAINER_RAW   = "raw-data"    # Ham JSON ve HTML dosyaları
CONTAINER_CLEAN = "clean-data"  # Temizlenmiş düz metin (RAG'a hazır)

# Blob path şablonları — yerel /data/<...> yollarının karşılıkları
BLOB_PATHS = {
    # FRED
    "fred_raw":      "fred/raw/{filename}",
    "fred_summary":  "fred/summary/{filename}",
    # GDELT
    "gdelt":         "gdelt/{filename}",
    # YFinance
    "yfinance":      "yfinance/{filename}",
    # EDGAR
    "edgar_meta":    "edgar/{filename}",         # nvda_submissions_*.json
    "edgar_raw":     "edgar/raw/{folder}/{filename}",
    "edgar_clean":   "edgar/clean/{folder}/{filename}",
}

# ── Azure OpenAI ──────────────────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT: str  = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION    = "2024-02-01"
EMBEDDING_DEPLOYMENT        = "text-embedding-ada-002"
CHAT_DEPLOYMENT             = "gpt-4o"

# ── Azure AI Search ───────────────────────────────────────────────────────────
SEARCH_SERVICE_ENDPOINT: str = os.environ.get("SEARCH_SERVICE_ENDPOINT", "")
SEARCH_INDEX_NAME            = "rag-1773312433567"

# ── Key Vault (opsiyonel — secret'ları doğrudan env var'dan okuyorsanız gerekmez)
KEY_VAULT_URL: str = os.environ.get("KEY_VAULT_URL", "")

# ── Collector Ayarları (config.py ile aynı değerler, cloud bağımsız) ──────────
FRED_API_KEY: str   = os.environ.get("FRED-API-KEY", os.environ.get("FRED_API_KEY", ""))
SEC_USER_AGENT: str = os.environ.get("SEC_USER_AGENT", "")

FRED_SERIES_LIST = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "DGS10", "DGS2"]
FRED_START_DATE  = "2020-01-01"
FRED_BASE_URL    = "https://api.stlouisfed.org/fred/series/observations"

EDGAR_TICKER     = "NVDA"
EDGAR_CIK        = "0001045810"
EDGAR_CIK_NO_ZERO = "1045810"
EDGAR_FORMS      = {"10-K", "10-Q", "8-K"}

GDELT_BASE_URL   = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY      = "(NVDA OR NVIDIA) sourcelang:english"

YFINANCE_TICKER  = "NVDA"
