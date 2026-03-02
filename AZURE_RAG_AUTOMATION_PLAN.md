# Finance RAG: Azure Otomasyonu ve RAG Geçiş İş Planı

Mevcut proje, NVIDIA (NVDA) hissesi için FRED, GDELT, YFinance ve SEC EDGAR üzerinden lokal bir bilgisayarda (`pipeline.py` çalıştırılarak) veri çeken ve bunları `/data` klasöründe saklayan bir yapıdadır. 

Bu projeyi %100 bulut tabanlı, kendi kendine çalışan ve kurumsal seviyede bir RAG (Retrieval-Augmented Generation) sistemine dönüştürmek için aşağıdaki adım adım iş planı uygulanmalıdır.

---

## 🏗️ 1. Hedef Azure Mimarisi

*   **Compute (Hesaplama & Otomasyon):** Azure Functions (Timer Trigger) - Veri çekme kodlarını (pipeline) her gece otomatik çalıştıracak.
*   **Storage (Depolama):** Azure Blob Storage - Yerel `/data` klasörünün yerini alacak. Ham JSON ve işlenmiş metin dosyaları burada tutulacak.
*   **Vector Database (Vektör DB):** Azure AI Search - Metinlerin vektörleştirilmiş hallerini tutacak ve semantik arama (semantic search) yapacak. (Alternatif: Azure Cosmos DB for MongoDB vCore)
*   **LLM & Embeddings:** Azure OpenAI Service - Bağlamı anlayıp cevap üretmek (GPT-4o vb.) ve metinleri vektörlere dönüştürmek (text-embedding-3-small) için.
*   **Security (Güvenlik):** Azure Key Vault - FRED API Key, Azure OpenAI Key gibi hassas verileri güvenli saklamak için.

---

## 📋 2. Adım Adım İş Planı

### Aşama 1: Kodun Buluta Hazırlanması (Refactoring)
Şu an kodlar yerel dosya sistemine (`os.makedirs`, `with open(...)`) bağımlı çalışıyor. 
*   **Adım 1.1:** Projeye `azure-storage-blob` kütüphanesi eklenecek.
*   **Adım 1.2:** `config.py` içerisindeki dosya yolları ve kaydetme/okuma fonksiyonları, Azure Blob Storage'a yazacak/okuyacak şekilde güncellenecek.
*   **Adım 1.3:** `pipeline.py` dahil tüm veri çekme scriptleri bir Python pakedi/fonksiyonu olarak çağrılabilir hale getirilecek.

### Aşama 2: Azure Kaynaklarının Kurulumu (Provisioning)
*   **Adım 2.1:** Azure Portal üzerinden bir **Resource Group** (Örn: `rg-finance-rag`) oluşturulacak.
*   **Adım 2.2:** Dosyalar için **Azure Storage Account** oluşturulup `raw-data`, `clean-data` gibi Container'lar eklenecek.
*   **Adım 2.3:** **Azure OpenAI Service** ayağa kaldırılacak. Embedding ve Chat modelleri için iki ayrı deployment yapılacak (Örn: `text-embedding-ada-002` ve `gpt-4o`).
*   **Adım 2.4:** Vektör araması için **Azure AI Search** servisi oluşturulacak ve dizin (index) yapısı tanımlanacak.
*   **Adım 2.5:** Tüm API anahtarları **Azure Key Vault** içerisine "Secret" olarak eklenecek.

### Aşama 3: Veri Hattı Otomasyonu (Data Pipeline Automation)
*   **Adım 3.1:** Yeni bir **Azure Functions (Python V2)** projesi oluşturulacak.
*   **Adım 3.2:** Bir **Timer Trigger** (Örn: Hafta içi her gece 03:00'te çalışacak bir CRON expression) tanımlanacak.
*   **Adım 3.3:** `pipeline.py`'nin yaptığı tüm işler (FRED, GDELT, YFinance ve SEC verilerinin çekilmesi) bu fonksiyon içerisine taşınacak. Çekilen/temizlenen veriler direkt Blob Storage'a yazılacak.

### Aşama 4: RAG - Vektörleştirme Süreci (Ingestion Pipeline)
Veriler temizlendikten sonra ChromaDB yerine Azure AI Search'e gönderilmelidir.
*   **Adım 4.1:** **Blob Trigger** türünde ikinci bir Azure Function yazılacak. (Veya ana Timer fonksiyonunun son adımı olarak kurgulanacak).
*   **Adım 4.2:** Bu fonksiyon; Blob Storage'a yeni eklenen "temiz" metinleri (`edgar_clean_text.py` çıktıları vd.) okuyacak.
*   **Adım 4.3:** `langchain-openai` kullanılarak metinler Chunk'lara (parçalara) ayrılacak, Azure OpenAI Embeddings ile vektörleştirilecek ve Azure AI Search Index'ine yüklenecek.

### Aşama 5: Soru-Cevap Arayüzü veya API (Serving)
Vektörleştirilmiş verilerle konuşabilmek için bir uç nokta (Endpoint) oluşturulacak.
*   **Adım 5.1:** Yeni bir **HTTP Trigger Azure Function** veya **Azure Container Apps** kullanılarak API oluşturulacak (FastAPI veya Flask ile).
*   **Adım 5.2:** Kullanıcıdan gelen soru bu API'ye iletilecek. API; 
    1. Soruyu vektörleştirecek, 
    2. Azure AI Search'te benzer dokümanları arayacak (Retrieval), 
    3. Bulunan dokümanları Azure OpenAI'a (GPT) bağlam olarak verip cevabı üretecek (Generation).
*   **Adım 5.3 (Opsiyonel):** Streamlit kullanılarak basit bir web arayüzü yazılıp bu API'ye bağlanacak.

### Aşama 6: Sürekli Entegrasyon ve İzleme (CI/CD & Monitoring)
*   **Adım 6.1:** GitHub Actions kurularak, koda her push yapıldığında Azure Functions projesinin otomatik olarak dağıtılması (deploy) sağlanacak.
*   **Adım 6.2:** Azure **Application Insights** entegre edilerek; veri çekerken API limitine takılmalar (Özellikle SEC rate limitleri), hatalar ve sorgu süreleri izlenecek.

---

## 🚀 Sonraki Adım
Eğer kabul ederseniz, ilk uygulama adımı olan **Aşama 1: Kodun Buluta Hazırlanması** süreciyle, `config.py` ve yerel dosya yazma fonksiyonlarını Azure Blob Storage'a uyumlu hale getirmeye başlayabiliriz.
