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
> **Azure Data Pipeline:** Data collection pipeline is active on Azure. Data is automatically collected and stored in Blob Storage. RAG integration (Azure AI Search + OpenAI) is in progress.

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

### Current Azure Status

✅ **Active Components:**
- Data collection pipeline (FRED, GDELT, YFinance, SEC EDGAR)
- Azure Functions with timer trigger
- Azure Blob Storage integration
- Dual-mode support (local + cloud)

⏳ **In Progress:**
- Azure AI Search indexer setup
- Azure OpenAI embedding integration
- RAG query API

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
> **Azure Veri Toplama:** Veri pipeline Azure'da aktif. Veriler otomatik olarak toplanıp Blob Storage'a kaydediliyor. RAG entegrasyonu (Azure AI Search + OpenAI) devam ediyor.

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

### Azure Durumu

✅ **Aktif Bileşenler:**
- Veri toplama pipeline (FRED, GDELT, YFinance, SEC EDGAR)
- Azure Functions timer trigger
- Azure Blob Storage entegrasyonu
- Dual-mode destek (yerel + bulut)

⏳ **Devam Eden:**
- Azure AI Search indexer kurulumu
- Azure OpenAI embedding entegrasyonu
- RAG query API
