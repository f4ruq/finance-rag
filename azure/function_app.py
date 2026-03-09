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


@app.blob_trigger(
    arg_name="blob",
    path="clean-data/{name}",
    connection="AzureWebJobsStorage"
)
def ingestion_function(blob: func.InputStream) -> None:
    """
    Blob'a yeni temiz metin gelince tetiklenir.
    NOT: Chunking ve Embedding işlemleri (eski Langchain altyapısı) kaldırılmıştır.
    Azure AI Foundry + Azure AI Search'ün 'Integrated Vectorization' özelliği kullanıldığı için,
    bu dosya Azure AI Search tarafından otomatik olarak okunup vektörleştirilecektir.
    Bu fonksiyon sadece ek loglama veya harici sistemleri tetikleme amacı taşıyabilir.
    """
    logging.info(f"Yeni veri sisteme dahil edildi (Native Ingestion tetiklenecek): {blob.name}")



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
