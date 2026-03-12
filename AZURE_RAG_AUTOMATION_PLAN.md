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

### Aşama 1: Kodun Buluta Hazırlanması (Refactoring) (TAMAMLANDI)
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

### Aşama 3: Veri Hattı Otomasyonu (Data Pipeline Automation) ✅ TAMAMLANDI
*   **Adım 3.1:** ✅ Azure Functions (Python V2) projesi oluşturuldu.
*   **Adım 3.2:** ✅ Timer Trigger tanımlandı ve aktif.
*   **Adım 3.3:** ✅ Tüm veri toplama scriptleri Azure Functions'a taşındı. Veriler Blob Storage'a başarıyla yazılıyor.
*   **Durum:** Veri toplama pipeline'ı tam operasyonel. FRED, GDELT, YFinance ve SEC EDGAR verileri otomatik olarak toplanıp Azure Blob Storage'da saklanıyor.

### Aşama 4: RAG - Vektörleştirme Süreci (Ingestion Pipeline) ⏳ BEKLEMEDE
Veriler temizlendikten sonra Azure AI Search'e gönderilmelidir.
*   **Adım 4.1:** ⏳ Azure AI Search Integrated Vectorization kurulumu yapılacak.
*   **Adım 4.2:** ⏳ Azure AI Search Indexer'ı Blob Storage'a (`clean-data` container) bağlanacak.
*   **Adım 4.3:** ⏳ Azure OpenAI Embedding modeli (text-embedding-ada-002) ile otomatik vektörleştirme aktif edilecek.
*   **Mevcut Durum:** AI Search servisi kurulu ancak Blob Storage'a henüz bağlı değil. Indexer yapılandırması bekleniyor.

### Aşama 5: Soru-Cevap Arayüzü veya API (Serving) ⏳ BEKLEMEDE
Vektörleştirilmiş verilerle konuşabilmek için bir uç nokta (Endpoint) oluşturulacak.
*   **Adım 5.1:** ⚠️ HTTP Trigger Azure Function kodu yazıldı ancak test edilmedi.
*   **Adım 5.2:** ⏳ RAG pipeline (Retrieval + Generation) Azure AI Search entegrasyonu tamamlandıktan sonra aktif edilecek.
*   **Adım 5.3 (Opsiyonel):** ⏳ Web arayüzü (Streamlit) eklenebilir.
*   **Mevcut Durum:** `query_function` kodu mevcut ancak AI Search index olmadığı için çalışamıyor.

### Aşama 6: Sürekli Entegrasyon ve İzleme (CI/CD & Monitoring) (BEKLEMEDE / TEST EDİLMEDİ)
*   **Adım 6.1:** GitHub Actions kurularak, koda her push yapıldığında Azure Functions projesinin otomatik olarak dağıtılması (deploy) sağlanacak.
*   **Adım 6.2:** Azure **Application Insights** entegre edilerek; veri çekerken API limitine takılmalar (Özellikle SEC rate limitleri), hatalar ve sorgu süreleri izlenecek.

---

---

## 📊 Proje Durumu Özeti (12 Mart 2026)

### ✅ Çalışan Bileşenler
- Veri toplama pipeline (FRED, GDELT, YFinance, SEC EDGAR)
- Azure Functions timer trigger (otomatik çalışma)
- Azure Blob Storage entegrasyonu
- Dual-mode destek (yerel + bulut)
- Manuel deployment süreci

### ⏳ Bekleyen Bileşenler
- Azure AI Search Indexer kurulumu
- Blob Storage → AI Search data pipeline
- Azure OpenAI embedding entegrasyonu
- RAG query endpoint aktivasyonu
- Application Insights monitoring
- CI/CD automation (GitHub Actions)

### 🚀 Sonraki Öncelikli Adımlar
1. **Azure AI Search Index Oluşturma:** Doküman şeması ve vector field'ları tanımla
2. **Indexer Yapılandırma:** Blob Storage data source'u bağla ve schedule ayarla
3. **Skillset Tanımlama:** Text splitting ve embedding için Azure OpenAI skillset oluştur
4. **Test:** Sample query ile RAG pipeline'ı test et
5. **Query API Aktivasyonu:** HTTP endpoint'i production'a al
