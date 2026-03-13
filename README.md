# Finance RAG Pipeline

[English](#english) | [Türkçe](#türkçe)

<a name="english"></a>
## English

This project is a data collection and processing pipeline for a financial RAG system, specifically focused on NVIDIA (NVDA) as an example. It fetches data from various sources (macroeconomic data, news, company filings), cleans it, and makes it ready for use in a RAG system.

### Features

The project collects data from four main sources:

1.  **FRED - Federal Reserve Economic Data (Macroeconomic Indicators)**:
    *   Fetches US macroeconomic data (Fed Funds Rate, CPI, Unemployment, Treasury Yields).
    *   Automatically calculates the "Yield Curve" and analyzes recession signals.
    *   Saves data as raw JSON and summary reports (`summary/macro_report_*.json`).

> [!NOTE]
> **Production Status:** Fully operational RAG system running on Azure. Automated data collection (timer trigger), Azure AI Search vectorization, and GPT-4o query API are all active. Test with `python test_production.py`

2.  **GDELT - Global Database of Events, Language, and Tone (Global News)**:
    *   Scans recent news containing keywords "NVDA" or "NVIDIA".
    *   Filters English content and stores it in JSON format.

3.  **YFinance - Yahoo Finance (Analyst Insights & News Scraping)**:
    *   Fetches Wall Street analyst recommendations (Buy/Hold/Sell) and price targets.
    *   Collects company financial metrics and recent rating upgrades/downgrades.
    *   Scrapes full text from recent Yahoo Finance news articles for deeper RAG context.

4.  **SEC EDGAR - Electronic Data Gathering, Analysis, and Retrieval (Company Filings)**:
    *   Tracks official filings (10-K, 10-Q, 8-K) submitted by NVIDIA to the SEC.
    *   Downloads filings, converts HTML content to text, and cleans it.
    *   Creates clean text files optimized for RAG.

### Installation

1.  Install the requirements:
    ```bash
    pip install -r requirements.txt
    pip install beautifulsoup4 lxml  # Add if not in requirements.txt
    ```

2.  Create a `.env` file and add the following keys:
    ```env
    FRED_API_KEY=your_api_key_here
    SEC_USER_AGENT="Name Surname email@address.com"
    ```

### Usage

To run all data sources and clean old data before fetching new ones:

```bash
python pipeline.py --source all
```

To run a specific source:

```bash
python pipeline.py --source fred
python pipeline.py --source gdelt
python pipeline.py --source edgar
python pipeline.py --source yfinance
```

### Project Structure

*   `pipeline.py`: Main script for local execution. Orchestrates the entire process.
*   `config.py`: Configuration, API keys, and file paths (local mode).
*   `azure/`: Cloud deployment files
    *   `function_app.py`: Azure Functions (timer trigger for data collection)
    *   `config_cloud.py`: Cloud-specific configuration (Blob Storage, Key Vault)
    *   `blob_helper.py`: Azure Blob Storage helper functions
*   `fred_collector.py`: Fetches macro data from FRED.
*   `gdelt.py`: Fetches news from GDELT.
*   `yfinance_collector.py`: Fetches analyst insights and scrapes news from Yahoo Finance.
*   `edgar_*.py`: Scripts for downloading and processing SEC filings.
*   `data/`: Directory where downloaded and processed data is stored (local mode only).

### Production Azure Architecture

** Fully Operational:**
- **Data Collection:** Automated pipeline (timer trigger every weekday 03:00 UTC)
  - FRED (macroeconomic indicators)
  - GDELT (global news)
  - YFinance (analyst insights + news scraping)
  - SEC EDGAR (10-K, 10-Q, 8-K filings)
- **Storage:** Azure Blob Storage (raw-data + clean-data containers)
- **Vectorization:** Azure AI Search with integrated vectorization
  - Automatic chunking and embedding (text-embedding-ada-002)
  - Indexer runs every 5 minutes
- **RAG Query API:** HTTP POST endpoint (`/api/query`)
  - Hybrid search (vector + text)
  - GPT-4o generation
  - Test script: `test_production.py`
- **Dual Mode:** Works both locally and on Azure

**Documentation:**
- Architecture Analysis: [`CURRENT_ARCHITECTURE_ANALYSIS.md`](CURRENT_ARCHITECTURE_ANALYSIS.md)
- Deployment Guide: [`AZURE_DEPLOY_GUIDE.md`](AZURE_DEPLOY_GUIDE.md)
- Test Guide: [`PRODUCTION_TEST_GUIDE.md`](PRODUCTION_TEST_GUIDE.md)
- System Prompt: [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)

** Next Steps (Optional Enhancements):**
- Conversational RAG (multi-turn conversation support)
- Tool calling (calculator, charting, forecasting)
- CI/CD automation (GitHub Actions)
- Advanced RAG techniques (HyDE, re-ranking)

---

<a name="türkçe"></a>
## Türkçe

Bu proje, örnek olarak NVIDIA (NVDA) odaklı bir finansal RAG sistemi için veri toplama ve işleme hattıdır. Farklı kaynaklardan (makroekonomik veriler, haberler, şirket dosyaları) veri çeker, temizler ve RAG sisteminde kullanıma hazır hale getirir.

### Özellikler

Proje dört ana kaynaktan veri toplar:

1.  **FRED - Federal Reserve Economic Data (Makroekonomik Göstergeler)**:
    *   ABD makroekonomik verilerini (Fed Faizi, TÜFE, İşsizlik, Tahvil Faizleri) çeker.
    *   Otomatik olarak "Yield Curve" (Getiri Eğrisi) hesabı yapar ve durgunluk sinyallerini analiz eder.
    *   Verileri ham JSON ve özet rapor (`summary/macro_report_*.json`) olarak kaydeder.

> [!NOTE]
> **Production Durumu:** Azure üzerinde tam operasyonel RAG sistemi çalışıyor. Otomatik veri toplama (timer trigger), Azure AI Search vektörleştirme ve GPT-4o sorgu API'si aktif. Test için: `python test_production.py`

2.  **GDELT - Global Database of Events, Language, and Tone (Küresel Haber Veritabanı)**:
    *   "NVDA" veya "NVIDIA" anahtar kelimelerini içeren son haberleri tarar.
    *   İngilizce içeriği filtreler ve JSON formatında saklar.

3.  **YFinance - Yahoo Finance (Analist Görüşleri ve Haber Kazıma)**:
    *   Wall Street analistlerinin tavsiyelerini (Al/Tut/Sat) ve hedef fiyatlarını çeker.
    *   Şirketin finansal oranlarını ve son not artırımı/indirimi güncellemelerini alır.
    *   RAG sisteminin derin bağlam yeteneği için Yahoo Finance üzerindeki son haberlerin tam metnini kazıyıp kaydeder (Web Scraping).

4.  **SEC EDGAR - Electronic Data Gathering, Analysis, and Retrieval (Resmi Şirket Dosyaları)**:
    *   NVIDIA'nın SEC'e sunduğu resmi dosyaları (10-K, 10-Q, 8-K) takip eder.
    *   Dosyaları indirir, HTML içeriğini metne çevirir ve temizler.
    *   RAG için optimize edilmiş temiz metin dosyaları oluşturur.

### Kurulum

1.  Gereksinimleri yükleyin:
    ```bash
    pip install -r requirements.txt
    pip install beautifulsoup4 lxml  # requirements.txt içinde yoksa ekleyin
    ```

2.  `.env` dosyasını oluşturun ve aşağıdaki anahtarları ekleyin:
    ```env
    FRED_API_KEY=your_api_key_here
    SEC_USER_AGENT="Isim Soyisim email@address.com"
    ```

### Kullanım

Tüm veri kaynaklarını çalıştırmak ve eski verileri temizleyip yenilerini çekmek için:

```bash
python pipeline.py --source all
```

Belirli bir kaynağı çalıştırmak için:

```bash
python pipeline.py --source fred
python pipeline.py --source gdelt
python pipeline.py --source edgar
python pipeline.py --source yfinance
```

### Proje Yapısı

*   `pipeline.py`: Yerel çalıştırma için ana script. Tüm süreci yönetir.
*   `config.py`: Ayarlar, API anahtarları ve dosya yolları (yerel mod).
*   `azure/`: Bulut deployment dosyaları
    *   `function_app.py`: Azure Functions (veri toplama için timer trigger)
    *   `config_cloud.py`: Bulut özel yapılandırma (Blob Storage, Key Vault)
    *   `blob_helper.py`: Azure Blob Storage yardımcı fonksiyonları
*   `fred_collector.py`: FRED'den makro verileri çeker.
*   `gdelt.py`: GDELT'ten haberleri çeker.
*   `yfinance_collector.py`: YFinance'den analist tavsiyelerini çeker ve güncel haberleri kazır.
*   `edgar_*.py`: SEC dosyalarını indirme ve işleme scriptleri.
*   `data/`: İndirilen ve işlenen verilerin saklandığı klasör (sadece yerel mod).

### Production Azure Mimarisi

** Tam Operasyonel:**
- **Veri Toplama:** Otomatik pipeline (hafta içi her gece 03:00 UTC)
  - FRED (makroekonomik göstergeler)
  - GDELT (küresel haberler)
  - YFinance (analist görüşleri + haber kazıma)
  - SEC EDGAR (10-K, 10-Q, 8-K dosyaları)
- **Depolama:** Azure Blob Storage (raw-data + clean-data containers)
- **Vektörleştirme:** Azure AI Search integrated vectorization
  - Otomatik chunking ve embedding (text-embedding-ada-002)
  - Indexer her 5 dakikada çalışıyor
- **RAG Sorgu API:** HTTP POST endpoint (`/api/query`)
  - Hybrid search (vektör + metin)
  - GPT-4o ile cevap üretimi
  - Test script: `test_production.py`
- **Dual Mode:** Hem yerel hem Azure'da çalışıyor

** Dokümantasyon:**
- Mimari Analiz: [`CURRENT_ARCHITECTURE_ANALYSIS.md`](CURRENT_ARCHITECTURE_ANALYSIS.md)
- Deployment Rehberi: [`AZURE_DEPLOY_GUIDE.md`](AZURE_DEPLOY_GUIDE.md)
- Test Rehberi: [`PRODUCTION_TEST_GUIDE.md`](PRODUCTION_TEST_GUIDE.md)
- System Prompt: [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)

** Sonraki Adımlar (Opsiyonel İyileştirmeler):**
- Conversational RAG (multi-turn konuşma desteği)
- Tool calling (hesaplama, grafik, tahmin)
- CI/CD otomasyonu (GitHub Actions)
- Gelişmiş RAG teknikleri (HyDE, re-ranking)
