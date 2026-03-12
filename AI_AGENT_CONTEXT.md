# Finance RAG Projesi - AI Asistan Bilgi Notu

Bu belge, "finance-rag" projesi üzerinde çalışacak yapay zeka asistanları için projenin tüm teknik detaylarını, mimarisini ve çalışma mantığını içermektedir. Lütfen projede herhangi bir değişiklik yapmadan önce bu belgeyi dikkatlice okuyun.

## 1. Proje Özeti
Bu proje, NVIDIA (NVDA) hissesi özelinde finansal bir RAG (Retrieval-Augmented Generation) sistemi oluşturmak için veri toplayan, işleyen ve temizleyen bir "Data Pipeline" (Veri Hattı) projesidir. Temel amacı; makroekonomik veriler, küresel haberler ve resmi şirket finansal raporlarını toplayarak LLM'lerin (Büyük Dil Modelleri) anlayabileceği temiz metin ve JSON formatlarına dönüştürmektir.

Pipeline dört ana kaynaktan beslenir:
1. **FRED (Federal Reserve Economic Data):** ABD Makroekonomik verileri.
2. **GDELT (Global Database of Events, Language, and Tone):** Küresel NVIDIA haberleri.
3. **YFinance:** Analist beklentileri, hedef fiyatlar ve uzun haber metinleri kazıma.
4. **SEC EDGAR:** NVIDIA'nın resmi şirket bildirimleri (10-K, 10-Q, 8-K).

---

## 2. Proje Mimarisi ve Ana Dosyalar

Proje modüler bir yapıda tasarlanmıştır. Tüm süreç `pipeline.py` üzerinden orkestre edilir.

### `config.py`
Projenin merkezi yapılandırma dosyasıdır. `.env` dosyasından `FRED_API_KEY` ve `SEC_USER_AGENT` değişkenlerini okur.
*   **Dizin Yapılandırmaları:** `data/raw`, `data/summary`, `data/edgar/raw`, `data/edgar/clean`, `data/gdelt` gibi çıktı klasörlerinin yollarını tutar.
*   **FRED Ayarları:** Hangi serilerin çekileceği listesi (`FEDFUNDS`, `CPIAUCSL`, `UNRATE`, `DGS10`, `DGS2`) ve başlangıç tarihi ("2020-01-01").
*   **EDGAR Ayarları:** Hedef şirket (`NVDA`), CIK numarası (`0001045810`), ve çekilecek form tipleri (`10-K`, `10-Q`, `8-K`).
*   **GDELT Ayarları:** Arama sorgusu (`(NVDA OR NVIDIA) sourcelang:english`).
*   **YFinance Ayarları:** Hedef analist şirketi (`NVDA`) ve çıktı klasörü (`data/yfinance`).

### `pipeline.py`
Projeyi baştan sona çalıştıran orkestrasyon script'idir. `subprocess` kullanarak diğer scriptleri sırasıyla tetikler.
*   **Argümanlar:** `--source` (all, fred, gdelt, edgar, yfinance) ve `--clean` (eski verileri silme) parametreleri alır.
*   **Temizlik Mantığı:** RAG sisteminin her zaman en taze veriyi kullanması hedeflendiğinden, scriptler çalışmadan önce ilgili `data/` alt klasörlerindeki eski verileri tamamen temizler (`clean_directory` fonksiyonu).

---

## 3. Veri Kaynakları ve Çalışma Mantıkları

### 3.1. FRED (Makroekonomik Veriler)
**İlgili Scriptler:** `fred_collector.py`, `fred_client.py`
*   `FRED_SERIES_LIST` içindeki makroekonomik verileri (Enflasyon, İşsizlik, Faiz oranları) FRED API üzerinden çeker.
*   Gelen verileri `data/raw/` dizinine ham JSON olarak kaydeder.
*   **Özet ve Analiz:** Son 12 dönemin (ay/gün) verisini kullanarak yüzdelik değişimleri ve "trend" (artan, azalan, yatay) durumunu hesaplar.
*   **Yield Curve (Getiri Eğrisi):** 10 yıllık (DGS10) ve 2 yıllık (DGS2) tahvil faizlerini karşılaştırarak spread (fark) hesabı yapar. Spread 0'ın altındaysa "INVERTED" (tersine dönmüş getiri eğrisi - durgunluk sinyali), aksi halde "NORMAL" olarak etiketler.
*   Tüm bu analizleri `data/summary/macro_report_*.json` dosyasına raporlar.

### 3.2. GDELT (Küresel Haberler)
**İlgili Script:** `gdelt.py`
*   GDELT V2 API Endpoint'ini kullanarak İngilizce dilindeki ve içinde "NVDA" veya "NVIDIA" geçen son 50 haberi (`MAX_RECORDS=50`) çeker.
*   **Filtreleme:** Sadece haber *başlığında* (title) "NVDA" veya "NVIDIA" geçenleri tutarak alakasız haberleri eler.
*   **Deduplication (Tekilleştirme):** Aynı URL'e sahip veya aynı başlık + aynı domain kombinasyonuna sahip haberleri filtreleyerek mükerrer verileri engeller.
*   Domain istatistiklerini (en çok haber çıkan 5 site), günlük haber sayımlarını ve temizlenmiş haber listesini `data/gdelt/gdelt_nvda_clean_*.json` dosyasına kaydeder.

### 3.3. YFinance (Analist Görüşleri ve Haber Kazıma)
**İlgili Script:** `yfinance_collector.py`
*   Yahoo Finance üzerinden hissenin güncel analist hedef fiyatlarını (High, Low, Mean), Al/Tut/Sat tavsiye trendlerini ve son Upgrades/Downgrades raporlarını çıkarır.
*   Bu kantitatif (sayısal) büyüklükleri `data/yfinance/{ticker}_yfinance_insight.json` içerisine aktarır.
*   **Haber Kazıma (Scraping):** Sadece "Yahoo Finance" platformunda listelenen güncel haber başlıklarını almakla kalmaz. Aynı zamanda `requests` ve `BeautifulSoup` yardımıyla o haberin sayfasına **bağlanıp**, ana metni `caas-body` veya benzer niteliklerle kazır.
*   Uzun formdaki haber makalelerini `data/yfinance/{ticker}_yfinance_news.json` dosyasına ayrı olarak kaydeder.

### 3.4. SEC EDGAR (Resmi Şirket Finansal Raporları)
Bu modül SEC limitlerine takılmamak (rate limiting) için adım adım (4 aşamalı) çalışır ve "User-Agent" başlığını zorunlu olarak kullanır.

1.  **`edgar_submissions_nvda.py`**: NVIDIA'nın son bildirimlerini listeler. Sadece 10-K (Yıllık), 10-Q (Çeyreklik) ve 8-K (Anlık önemli gelişmeler) formlarını filtreler. Sonuçları json olarak `data/edgar/nvda_submissions_*.json` dosyasına kaydeder.
2.  **`edgar_downloader_nvda.py`**: Bir önceki adımda oluşturulan JSON'u okur. En güncel 10 kaydın (`limit=10`) ana dizin dosyasını (`-index.html`) ve tüm metni içeren karmaşık txt dosyasını indirerek `data/edgar/raw/{tarih}_{form}_{accession}/` dizinlerine kaydeder.
3.  **`edgar_download_primary_docs.py`**: İndirilen `-index.html` dosyalarını BeautifulSoup ile parse eder. Form tipine (10-K vb.) tam uyan *Asıl (Primary) Dökümanı* bularak (genellikle `.htm` uzantılıdır) ilgili klasöre indirir.
4.  **`edgar_clean_text.py`**: İndirilen asıl (primary) HTML dökümanları BeautifulSoup (lxml) ile okur. `<script>`, `<style>` gibi RAG için gürültü yaratacak etiketleri temizler. Sadece saf metni çıkararak gereksiz boşlukları siler ve `data/edgar/clean/{tarih}_{form}_{accession}/{dosya_adi}.htm.txt` olarak RAG'in vektor veritabanına girmeye hazır hale getirir.

---

## 4. Ortam Gereksinimleri (Environment)
1.  Python ortamında `requests`, `pandas`, `beautifulsoup4`, `lxml`, `python-dotenv`, `yfinance` kütüphanelerinin yüklü olması gerekir (`requirements.txt` dosyasından kurulabilir).
2.  `.env` dosyasında mutlaka şu iki değişken bulunmalıdır:
    *   `FRED_API_KEY="api_anahtariniz"`
    *   `SEC_USER_AGENT="Ad Soyad email@adresiniz.com"` *(SEC kuralları gereği zorunludur)*

## 5. Azure Bulut Geçişi ve Mevcut Durum

### 5.1. Tamamlanan Bileşenler ✅
*   **Azure Functions - Veri Toplama:** Timer trigger ile otomatik veri toplama pipeline'ı aktif ve çalışır durumda. Tüm collector scriptleri (`fred_collector.py`, `gdelt.py`, `yfinance_collector.py`, `edgar_*.py`) Azure Functions üzerinde düzenli olarak çalışmaktadır.
*   **Azure Blob Storage:** Tüm toplanan veriler Azure Blob Storage'a başarıyla yazılıyor. `use_blob=True` parametresi ile dual-mode (yerel/bulut) desteği eklenmiştir.
*   **Kod Yapısı:** Read-only file system hatası düzeltildi. `os.makedirs()` çağrıları sadece yerel modda (`use_blob=False`) çalışacak şekilde koruma altına alındı.
*   **Azure Kaynakları:** Resource Group, Storage Account, Key Vault ve gerekli Azure servisleri kurulmuş durumda.
*   **Deployment:** Manuel deployment Azure Functions Core Tools (`func azure functionapp publish`) ile başarıyla yapılıyor.

### 5.2. Devam Eden / Bekleyen Bileşenler ⏳
*   **Azure AI Search Entegrasyonu:** AI Search servisi kurulu ancak Blob Storage'a bağlı değil. Indexer ve vectorization pipeline henüz yapılandırılmadı.
*   **RAG Pipeline:** `ingestion_function` ve `query_function` fonksiyonları `azure/function_app.py` içinde kod olarak mevcut ancak aktif değil (Azure AI Search bağlantısı eksik).
*   **LLM Entegrasyonu:** Azure OpenAI embedding ve chat completion entegrasyonu kod seviyesinde yazılmış ancak test edilmemiş ve aktif değil.

### 5.3. Sonraki Adımlar
1. **Azure AI Search Indexer Kurulumu:** Blob Storage → AI Search otomatik data ingestion pipeline'ı kurulmalı
2. **Vectorization:** Azure OpenAI embedding modeli ile otomatik vektörleştirme aktif edilmeli
3. **Query API Test:** RAG query endpoint'i test edilip aktif hale getirilmeli
4. **Monitoring:** Application Insights ile hata izleme ve performans metrikleri eklenmeli
5. **CI/CD (Opsiyonel):** GitHub Actions ile otomatik deployment kurulabilir

### 5.4. Teknik Notlar
*   **Hata Yönetimi:** Tüm collector scriptlerinde try-except blokları ve loglama mevcut. Bu yapı korunmalı.
*   **Yeni Veri Kaynağı Ekleme:** `config_cloud.py` ve `config.py` güncellemesi + `use_blob` mantığı eklenmeli.
*   **Dual-Mode:** Kod hem yerel (`python pipeline.py`) hem Azure üzerinde (`Azure Functions`) çalışabilir.
