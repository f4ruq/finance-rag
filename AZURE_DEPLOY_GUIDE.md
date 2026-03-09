# Finance RAG — Azure Deployment Technical Guide

Bu belge, `finance-rag` projesini yerel bir Python ortamından tam bulut tabanlı,
otomatize edilmiş ve üretim kalitesinde bir Azure mimarisine dönüştürmek için
adım adım teknik bir rehberdir.

> **Hedef Branch:** `feature/azure-cloud-deploy`
> **Hedef Mimari:** Azure Functions + Blob Storage + Azure AI Search + Azure OpenAI + Azure Key Vault

---

## 📐 Genel Mimari Şeması

```
[Zamanlayıcı / Timer]
        │
        ▼
┌─────────────────────────────┐
│   Azure Functions           │  ← Compute (Hesaplama)
│   (Timer Trigger)           │
│   pipeline_function.py      │
└────────────┬────────────────┘
             │ Veri çeker
             ▼
┌─────────────────────────────┐
│   Azure Blob Storage        │  ← Depolama (Yerel /data klasörünün yerini alır)
│   raw-data/   clean-data/   │
└────────────┬────────────────┘
             │ Yeni dosya gelince
             ▼
┌─────────────────────────────┐
│   Azure Functions           │
│   (Blob Trigger)            │  ← RAG Ingestion
│   ingestion_function.py     │
└────────────┬────────────────┘
             │ Chunk + Embed
             ▼
┌─────────────────────────────┐
│   Azure OpenAI Service      │  ← text-embedding-ada-002
│   (Embeddings)              │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Azure AI Search           │  ← Vektör Veritabanı (Semantic/Vector Search)
│   (Index: finance-rag-idx)  │
└────────────┬────────────────┘
             │ Soru/Cevap
             ▼
┌─────────────────────────────┐
│   Azure Functions           │
│   (HTTP Trigger) / FastAPI  │  ← Serving Layer (RAG API)
│   query_function.py         │
└────────────┬────────────────┘
             │ GPT ile cevap üret
             ▼
┌─────────────────────────────┐
│   Azure OpenAI Service      │  ← gpt-4o (Generation)
└─────────────────────────────┘

🔐 Azure Key Vault — Tüm API anahtarları ve secret'lar burada saklanır.
📊 Application Insights — Tüm fonksiyonlar buraya log gönderir.
```

---

## 🔐 Kullanılacak Azure Kaynakları (Özet)

| Kaynak | Tier / SKU | Kullanım Amacı |
|---|---|---|
| **Azure Resource Group** | — | Tüm kaynakları gruplayıp yönetmek |
| **Azure Storage Account** | Standard LRS | Blob olarak ham/temiz veri dosyaları |
| **Azure Functions** | Consumption (Serverless) | Pipeline, Ingestion ve Query fonksiyonları |
| **Azure OpenAI Service** | Regional | Embedding (ada-002) + Chat (gpt-4o) |
| **Azure AI Search** | Basic veya Standard | Vektör + semantik arama (Vector Index) |
| **Azure Key Vault** | Standard | API key, connection string, secret yönetimi |
| **Application Insights** | — | Log, hata ve performans izleme |

---

## Aşama 1 — Kodun Buluta Hazırlanması (Refactoring) (TAMAMLANDI)

**İlgili Azure Kaynağı:** Henüz yok — sadece kod değişikliği.

### 1.1 Yeni Bağımlılıkları Ekle

`azure/requirements.txt` dosyası oluştur:

```txt
# Mevcut bağımlılıklar
requests
pandas
beautifulsoup4
lxml
python-dotenv
yfinance

# Azure SDK
azure-storage-blob>=12.0.0
azure-identity>=1.0.0
azure-keyvault-secrets>=4.0.0
azure-search-documents>=11.4.0
openai>=1.0.0
# Azure Functions runtime
azure-functions
```

### 1.2 `config_cloud.py` Dosyasını Oluştur

Yerel `config.py`'yi doğrudan değiştirmek yerine `azure/config_cloud.py` adında
ayrı bir cloud-only config dosyası oluşturulacak:

```python
# azure/config_cloud.py
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# --- Azure Kimlik Doğrulama ---
credential = DefaultAzureCredential()

# --- Key Vault ---
KEY_VAULT_URL = os.environ["KEY_VAULT_URL"]  # Örn: https://kv-finance-rag.vault.azure.net/
kv_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

def get_secret(name: str) -> str:
    return kv_client.get_secret(name).value

# --- Blob Storage ---
STORAGE_ACCOUNT_URL = os.environ["STORAGE_ACCOUNT_URL"]
CONTAINER_RAW   = "raw-data"
CONTAINER_CLEAN = "clean-data"

# Blob path şablonları (yerel /data klasörünün karşılıkları)
BLOB_PATHS = {
    "fred_raw":      "fred/raw/{filename}",
    "fred_summary":  "fred/summary/{filename}",
    "gdelt":         "gdelt/{filename}",
    "yfinance":      "yfinance/{filename}",
    "edgar_raw":     "edgar/raw/{accession}/{filename}",
    "edgar_clean":   "edgar/clean/{accession}/{filename}",
}

# --- Azure OpenAI ---
AZURE_OPENAI_ENDPOINT   = os.environ["AZURE_OPENAI_ENDPOINT"]
EMBEDDING_DEPLOYMENT    = "text-embedding-ada-002"
CHAT_DEPLOYMENT         = "gpt-4o"

# --- Azure AI Search ---
SEARCH_SERVICE_ENDPOINT = os.environ["SEARCH_SERVICE_ENDPOINT"]
SEARCH_INDEX_NAME       = "finance-rag-idx"
```

### 1.3 Blob Storage Yardımcı Modülü

```python
# azure/blob_helper.py
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from config_cloud import STORAGE_ACCOUNT_URL

def get_blob_client(container: str, blob_name: str):
    service = BlobServiceClient(
        account_url=STORAGE_ACCOUNT_URL,
        credential=DefaultAzureCredential()
    )
    return service.get_blob_client(container=container, blob=blob_name)

def upload_json(container: str, blob_name: str, data: dict) -> None:
    """JSON veriyi Blob Storage'a yükle (yerel open() fonksiyonunun yerini alır)."""
    import json
    client = get_blob_client(container, blob_name)
    client.upload_blob(json.dumps(data, ensure_ascii=False, indent=2), overwrite=True)

def download_json(container: str, blob_name: str) -> dict:
    """Blob Storage'dan JSON veriyi indir."""
    import json
    client = get_blob_client(container, blob_name)
    return json.loads(client.download_blob().readall())

def upload_text(container: str, blob_name: str, text: str) -> None:
    """Düz metni Blob Storage'a yükle."""
    client = get_blob_client(container, blob_name)
    client.upload_blob(text.encode("utf-8"), overwrite=True)
```

---

## Aşama 2 — Azure Kaynaklarının Kurulumu (Provisioning)

**İlgili Azure Kaynakları:** Resource Group, Storage Account, Azure OpenAI, AI Search, Key Vault

### 2.1 Resource Group

```bash
az group create \
  --name rg-finance-rag \
  --location eastus
```

### 2.2 Storage Account + Container'lar

```bash
az storage account create \
  --name stfinancerag001 \
  --resource-group rg-finance-rag \
  --sku Standard_LRS \
  --kind StorageV2

# Container'ları oluştur
az storage container create --name raw-data   --account-name stfinancerag001
az storage container create --name clean-data --account-name stfinancerag001
```

### 2.3 Azure OpenAI Service

```bash
az cognitiveservices account create \
  --name oai-finance-rag \
  --resource-group rg-finance-rag \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Embedding modeli deployment
az cognitiveservices account deployment create \
  --name oai-finance-rag \
  --resource-group rg-finance-rag \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI

# Chat modeli deployment
az cognitiveservices account deployment create \
  --name oai-finance-rag \
  --resource-group rg-finance-rag \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI
```

### 2.4 Azure AI Search

```bash
az search service create \
  --name srch-finance-rag \
  --resource-group rg-finance-rag \
  --sku basic \
  --partition-count 1 \
  --replica-count 1
```

**Index Şeması** (`azure/search_index_schema.json`):

```json
{
  "name": "finance-rag-idx",
  "fields": [
    { "name": "id",        "type": "Edm.String", "key": true, "filterable": true },
    { "name": "source",    "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "date",      "type": "Edm.String", "filterable": true, "sortable": true },
    { "name": "content",   "type": "Edm.String", "searchable": true },
    {
      "name": "embedding",
      "type": "Collection(Edm.Single)",
      "dimensions": 1536,
      "vectorSearchProfile": "hnsw-profile"
    }
  ],
  "vectorSearch": {
    "algorithms": [{ "name": "hnsw-algo", "kind": "hnsw" }],
    "profiles": [{ "name": "hnsw-profile", "algorithm": "hnsw-algo" }]
  }
}
```

### 2.5 Key Vault + Secret'lar

```bash
az keyvault create \
  --name kv-finance-rag \
  --resource-group rg-finance-rag \
  --location eastus

# Secret'ları ekle
az keyvault secret set --vault-name kv-finance-rag --name "FRED-API-KEY"    --value "<your_fred_key>"
az keyvault secret set --vault-name kv-finance-rag --name "SEC-USER-AGENT"  --value "<Ad Soyad email>"
az keyvault secret set --vault-name kv-finance-rag --name "OPENAI-API-KEY"  --value "<your_openai_key>"
az keyvault secret set --vault-name kv-finance-rag --name "SEARCH-API-KEY"  --value "<your_search_key>"
```

---

## Aşama 3 — Data Pipeline Otomasyonu (Azure Functions / Timer Trigger) (TAMAMLANDI)

**İlgili Azure Kaynağı:** Azure Functions (Consumption Plan)

### 3.1 Functions Projesi Oluştur

```bash
func init azure --python
cd azure
func new --name pipeline_function --template "Timer trigger"
```

### 3.2 `host.json`

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": { "samplingSettings": { "isEnabled": true } }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

### 3.3 `function_app.py` — Timer Trigger (Pipeline)

```python
# azure/function_app.py
import azure.functions as func
import logging
import sys, os

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 3 * * 1-5",  # Hafta içi her gece 03:00 (UTC)
    arg_name="timer",
    run_on_startup=False
)
def pipeline_function(timer: func.TimerRequest) -> None:
    """Her gece veri çekme pipeline'ını çalıştırır."""
    logging.info("Pipeline Timer Trigger başladı.")

    from fred_collector   import run as run_fred
    from gdelt            import run as run_gdelt
    from yfinance_collector import run as run_yfinance
    from edgar_submissions_nvda      import run as run_edgar_sub
    from edgar_downloader_nvda       import run as run_edgar_dl
    from edgar_download_primary_docs import run as run_edgar_primary
    from edgar_clean_text            import run as run_edgar_clean

    steps = [
        ("FRED",           run_fred),
        ("GDELT",          run_gdelt),
        ("YFinance",       run_yfinance),
        ("EDGAR-Sub",      run_edgar_sub),
        ("EDGAR-DL",       run_edgar_dl),
        ("EDGAR-Primary",  run_edgar_primary),
        ("EDGAR-Clean",    run_edgar_clean),
    ]

    for name, fn in steps:
        try:
            logging.info(f"[{name}] başlıyor...")
            fn(use_blob=True)  # Cloud modda çalıştır
            logging.info(f"[{name}] tamamlandı.")
        except Exception as e:
            logging.error(f"[{name}] hata: {e}", exc_info=True)

    logging.info("Pipeline Timer Trigger tamamlandı.")
```

> **Not:** Her mevcut script'e `run(use_blob: bool = False)` fonksiyonu eklenecek.
> `use_blob=False` → yerel dosyaya yaz (geliştirme/test), `use_blob=True` → Blob'a yaz.

---

## Aşama 4 — RAG Vektörleştirme (Blob Trigger / Ingestion) (TAMAMLANDI)

**İlgili Azure Kaynakları:** Azure Functions (Blob Trigger), Azure OpenAI, Azure AI Search

```python
# azure/function_app.py içine eklenecek (devam)

@app.blob_trigger(
    arg_name="blob",
    path="clean-data/{name}",
    connection="AzureWebJobsStorage"
)
def ingestion_function(blob: func.InputStream) -> None:
    """Blob'a yeni temiz metin gelince otomatik vektörleştirir."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import AzureOpenAIEmbeddings
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    from config_cloud import (
        AZURE_OPENAI_ENDPOINT, EMBEDDING_DEPLOYMENT,
        SEARCH_SERVICE_ENDPOINT, SEARCH_INDEX_NAME
    )
    import uuid

    logging.info(f"Ingestion başladı: {blob.name}")

    raw_text = blob.read().decode("utf-8")

    # 1. Chunk'la
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    # 2. Vektörleştir
    embedder = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_deployment=EMBEDDING_DEPLOYMENT
    )
    vectors = embedder.embed_documents(chunks)

    # 3. Azure AI Search'e yükle
    search_client = SearchClient(
        endpoint=SEARCH_SERVICE_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(os.environ["SEARCH_API_KEY"])
    )
    docs = [
        {
            "id":        str(uuid.uuid4()),
            "source":    blob.name,
            "date":      blob.name.split("/")[0],
            "content":   chunk,
            "embedding": vector
        }
        for chunk, vector in zip(chunks, vectors)
    ]
    search_client.upload_documents(documents=docs)
    logging.info(f"Ingestion tamamlandı: {len(docs)} chunk yüklendi.")
```

---

## Aşama 5 — RAG Soru-Cevap API (HTTP Trigger) (TAMAMLANDI)

**İlgili Azure Kaynakları:** Azure Functions (HTTP Trigger), Azure AI Search, Azure OpenAI

```python
# azure/function_app.py içine eklenecek (devam)

@app.route(route="query", methods=["POST"])
def query_function(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/query
    Body: { "question": "NVDA'nın son çeyrek geliri ne oldu?" }
    """
    from openai import AzureOpenAI
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
    from azure.core.credentials import AzureKeyCredential
    from config_cloud import (
        AZURE_OPENAI_ENDPOINT, EMBEDDING_DEPLOYMENT, CHAT_DEPLOYMENT,
        SEARCH_SERVICE_ENDPOINT, SEARCH_INDEX_NAME
    )
    import json

    question = req.get_json().get("question", "")
    if not question:
        return func.HttpResponse("Soru boş olamaz.", status_code=400)

    client = AzureOpenAI(azure_endpoint=AZURE_OPENAI_ENDPOINT, api_version="2024-02-01")

    # 1. Soruyu vektörleştir
    q_vector = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT, input=question
    ).data[0].embedding

    # 2. Azure AI Search'te semantik arama (Retrieval)
    search_client = SearchClient(
        endpoint=SEARCH_SERVICE_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(os.environ["SEARCH_API_KEY"])
    )
    results = search_client.search(
        search_text=question,
        vector_queries=[VectorizedQuery(vector=q_vector, k_nearest_neighbors=5, fields="embedding")],
        select=["content", "source", "date"],
        top=5
    )
    context = "\n\n---\n\n".join([r["content"] for r in results])

    # 3. GPT ile cevap üret (Generation)
    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen NVIDIA hissesi (NVDA) üzerine uzmanlaşmış bir finansal analiz asistanısın. "
                    "Sadece aşağıdaki belgelerden yararlanarak soruları yanıtla. "
                    "Eğer belgede cevap yoksa bunu belirt.\n\n"
                    f"BELGELER:\n{context}"
                )
            },
            { "role": "user", "content": question }
        ]
    )
    answer = response.choices[0].message.content

    return func.HttpResponse(
        json.dumps({"answer": answer, "sources": context[:500]}, ensure_ascii=False),
        mimetype="application/json"
    )
```

---

## Aşama 6 — CI/CD ve İzleme (TAMAMLANDI - CI/CD Kısmı)

**İlgili Azure Kaynakları:** GitHub Actions, Application Insights

### 6.1 GitHub Actions Workflow

`.github/workflows/azure-functions-deploy.yml`:

```yaml
name: Deploy Azure Functions

on:
  push:
    branches: [ feature/azure-cloud-deploy ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with: { python-version: "3.11" }

      - name: Install dependencies
        run: pip install -r azure/requirements.txt

      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: func-finance-rag
          package: ./azure
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

### 6.2 Application Insights

```bash
az monitor app-insights component create \
  --app appi-finance-rag \
  --resource-group rg-finance-rag \
  --location eastus \
  --kind web
```

İzlenecek başlıca metrikler:
- **SEC rate limit hataları** — 429 / Too Many Requests yanıtları
- **Fonksiyon yürütme süreleri** — Pipeline'ın kaç dakikada tamamlandığı
- **Ingestion chunk sayısı** — Her gecenin kaç dökümanı işlediği
- **Query latency** — Soru-cevap API'nin yanıt süresi

---

## 📁 Önerilen Dosya Yapısı

```
finance-rag/
├── azure/                          ← Cloud-only klasörü
│   ├── function_app.py             ← Timer + Blob + HTTP Trigger fonksiyonları
│   ├── config_cloud.py             ← Blob/Key Vault/Search konfigürasyonu
│   ├── blob_helper.py              ← Blob okuma/yazma yardımcı modülü
│   ├── host.json                   ← Azure Functions runtime ayarları
│   ├── local.settings.json         ← Lokal test ortamı (.gitignore'da!)
│   ├── requirements.txt            ← Cloud bağımlılıkları
│   └── search_index_schema.json    ← AI Search index tanımı
├── .github/
│   └── workflows/
│       └── azure-functions-deploy.yml
├── config.py                       ← Yerel config (değişmez)
├── pipeline.py                     ← Yerel orkestrasyon (değişmez)
├── fred_collector.py               ← run(use_blob) parametresi eklenecek
├── gdelt.py                        ← run(use_blob) parametresi eklenecek
├── yfinance_collector.py           ← run(use_blob) parametresi eklenecek
├── edgar_*.py                      ← run(use_blob) parametresi eklenecek
└── ...
```

> **Önemli:** Mevcut yerel scriptler (`config.py`, `pipeline.py` vb.) bozulmadan kalır.
> Her script'e `use_blob=False` varsayılan parametresi eklenerek **hem lokal hem cloud'da** çalışabilir hale getirilir.

---

## ✅ Uygulama Sırası (Checklist)

| # | Aşama | Süre (tahmini) | Önkoşul |
|---|---|---|---|
| 1 | `azure/` klasörü + `config_cloud.py` + `blob_helper.py` | 2–3 saat | — |
| 2 | Azure CLI ile kaynak kurulumu | 1–2 saat | Azure aboneliği |
| 3 | Script'lere `run(use_blob)` parametresi ekle + test | 3–4 saat | Aşama 1 |
| 4 | Timer Trigger Function + Blob integration testi | 2–3 saat | Aşama 2–3 |
| 5 | Ingestion Function (Blob Trigger) | 2–3 saat | Aşama 4 |
| 6 | HTTP Trigger RAG API | 2–3 saat | Aşama 5 |
| 7 | GitHub Actions CI/CD + Application Insights | 1–2 saat | Aşama 6 |
