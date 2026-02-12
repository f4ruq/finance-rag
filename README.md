# Finance RAG Pipeline

[English](#english) | [Türkçe](#türkçe)

<a name="english"></a>
## English

This project is a data collection and processing pipeline for a financial RAG system, specifically focused on NVIDIA (NVDA) as an example. It fetches data from various sources (macroeconomic data, news, company filings), cleans it, and makes it ready for use in a RAG system.

### Features

The project collects data from three main sources:

1.  **FRED - Federal Reserve Economic Data (Macroeconomic Indicators)**:
    *   Fetches US macroeconomic data (Fed Funds Rate, CPI, Unemployment, Treasury Yields).
    *   Automatically calculates the "Yield Curve" and analyzes recession signals.
    *   Saves data as raw JSON and summary reports (`summary/macro_report_*.json`).

> [!NOTE]
> Once this data pipeline is fully stabilized, the RAG integration will also be hosted in this repository.

2.  **GDELT - Global Database of Events, Language, and Tone (Global News)**:
    *   Scans recent news containing keywords "NVDA" or "NVIDIA".
    *   Filters English content and stores it in JSON format.

3.  **SEC EDGAR - Electronic Data Gathering, Analysis, and Retrieval (Company Filings)**:
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
```

### Project Structure

*   `pipeline.py`: Main script. Orchestrates the entire process.
*   `config.py`: Configuration, API keys, and file paths.
*   `fred_collector.py`: Fetches macro data from FRED.
*   `gdelt.py`: Fetches news from GDELT.
*   `edgar_*.py`: Scripts for downloading and processing SEC filings.
*   `data/`: Directory where downloaded and processed data is stored.

---

<a name="türkçe"></a>
## Türkçe

Bu proje, örnek olarak NVIDIA (NVDA) odaklı bir finansal RAG sistemi için veri toplama ve işleme hattıdır. Farklı kaynaklardan (makroekonomik veriler, haberler, şirket dosyaları) veri çeker, temizler ve RAG sisteminde kullanıma hazır hale getirir.

### Özellikler

Proje üç ana kaynaktan veri toplar:

1.  **FRED - Federal Reserve Economic Data (Makroekonomik Göstergeler)**:
    *   ABD makroekonomik verilerini (Fed Faizi, TÜFE, İşsizlik, Tahvil Faizleri) çeker.
    *   Otomatik olarak "Yield Curve" (Getiri Eğrisi) hesabı yapar ve durgunluk sinyallerini analiz eder.
    *   Verileri ham JSON ve özet rapor (`summary/macro_report_*.json`) olarak kaydeder.

> [!NOTE]
> Bu veri hattı tam olarak stabil hale getirildikten sonra, RAG entegrasyonu da bu repoya eklenecektir.

2.  **GDELT - Global Database of Events, Language, and Tone (Küresel Haber Veritabanı)**:
    *   "NVDA" veya "NVIDIA" anahtar kelimelerini içeren son haberleri tarar.
    *   İngilizce içeriği filtreler ve JSON formatında saklar.

3.  **SEC EDGAR - Electronic Data Gathering, Analysis, and Retrieval (Resmi Şirket Dosyaları)**:
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
```

### Proje Yapısı

*   `pipeline.py`: Ana çalışan script. Tüm süreci yönetir.
*   `config.py`: Ayarlar, API anahtarları ve dosya yolları.
*   `fred_collector.py`: FRED'den makro verileri çeker.
*   `gdelt.py`: GDELT'ten haberleri çeker.
*   `edgar_*.py`: SEC dosyalarını indirme ve işleme scriptleri.
*   `data/`: İndirilen ve işlenen verilerin saklandığı klasör.
