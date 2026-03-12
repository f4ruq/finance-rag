"""
blob_helper.py — Azure Blob Storage için yardımcı fonksiyonlar.
Tüm collector script'lerin use_blob=True modunda kullandığı
ortak upload/download arayüzüdür. Yerel open() / os.makedirs()
çağrılarının bulut karşılığıdır.
"""
import json
import logging
from typing import Union

from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

# Lazy-init: servis istemcisi ilk kullanımda oluşturulur
_service_client: BlobServiceClient | None = None


def _get_service() -> BlobServiceClient:
    """BlobServiceClient'ı döndürür (singleton)."""
    global _service_client
    if _service_client is None:
        from config_cloud import STORAGE_ACCOUNT_URL
        _service_client = BlobServiceClient(
            account_url=STORAGE_ACCOUNT_URL,
            credential=DefaultAzureCredential()
        )
    return _service_client


def _blob_client(container: str, blob_name: str):
    return _get_service().get_blob_client(container=container, blob=blob_name)


# ── Yükleme Fonksiyonları ─────────────────────────────────────────────────────

def upload_json(container: str, blob_name: str, data: dict) -> None:
    """
    Python dict'i JSON olarak Blob Storage'a yükler.
    Yerel: json.dump(data, open(path, 'w'))
    """
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    _blob_client(container, blob_name).upload_blob(payload, overwrite=True)
    logger.info(f"Blob yüklendi: {container}/{blob_name}")


def upload_text(container: str, blob_name: str, text: str) -> None:
    """
    Düz metni (str) Blob Storage'a yükler.
    Yerel: open(path, 'w').write(text)
    """
    _blob_client(container, blob_name).upload_blob(
        text.encode("utf-8"), overwrite=True
    )
    logger.info(f"Blob yüklendi: {container}/{blob_name}")


def upload_bytes(container: str, blob_name: str, data: bytes) -> None:
    """
    Ham bayt verisini (binary) Blob Storage'a yükler.
    Yerel: open(path, 'wb').write(data)
    """
    _blob_client(container, blob_name).upload_blob(data, overwrite=True)
    logger.info(f"Blob yüklendi: {container}/{blob_name}")


# ── İndirme Fonksiyonları ─────────────────────────────────────────────────────

def download_json(container: str, blob_name: str) -> dict:
    """Blob Storage'dan JSON'u Python dict olarak döndürür."""
    raw = _blob_client(container, blob_name).download_blob().readall()
    return json.loads(raw)


def download_text(container: str, blob_name: str) -> str:
    """Blob Storage'dan düz metni str olarak döndürür."""
    raw = _blob_client(container, blob_name).download_blob().readall()
    return raw.decode("utf-8")


def download_bytes(container: str, blob_name: str) -> bytes:
    """Blob Storage'dan ham bayt verisini döndürür."""
    return _blob_client(container, blob_name).download_blob().readall()


# ── Liste Fonksiyonları ───────────────────────────────────────────────────────

def list_blobs(container: str, prefix: str = "") -> list[str]:
    """
    Belirtilen container içindeki blob isimlerini listeler.
    Yerel: os.listdir(path) karşılığı.
    """
    svc = _get_service()
    container_client = svc.get_container_client(container)
    return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]


def blob_exists(container: str, blob_name: str) -> bool:
    """Blob'un var olup olmadığını kontrol eder. Yerel: os.path.exists() karşılığı."""
    try:
        _blob_client(container, blob_name).get_blob_properties()
        return True
    except Exception:
        return False


# ── Silme Fonksiyonları ───────────────────────────────────────────────────────

def delete_blob(container: str, blob_name: str) -> None:
    """Tek bir blob'u siler. Yerel: os.remove() karşılığı."""
    try:
        _blob_client(container, blob_name).delete_blob()
        logger.info(f"Blob silindi: {container}/{blob_name}")
    except Exception as e:
        logger.warning(f"Blob silinemedi: {container}/{blob_name} - {e}")


def delete_blobs_by_prefix(container: str, prefix: str) -> int:
    """
    Belirtilen prefix ile başlayan tüm blob'ları siler.
    Yerel: shutil.rmtree() veya klasör temizleme karşılığı.
    Returns: Silinen blob sayısı
    """
    blobs = list_blobs(container, prefix=prefix)
    deleted_count = 0
    for blob_name in blobs:
        try:
            _blob_client(container, blob_name).delete_blob()
            deleted_count += 1
        except Exception as e:
            logger.warning(f"Blob silinemedi: {blob_name} - {e}")
    
    logger.info(f"{deleted_count} blob silindi ({container}/{prefix})")
    return deleted_count
