import os
import threading
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = BASE_DIR / "state" / "market_cache.db"
DB_FILE = "market_cache.db"

# Thread-lock to prevent concurrent uploads causing race conditions
_upload_lock = threading.Lock()


def get_config():
    """Retrieve HF configuration from environment variables."""
    return {
        "token": os.environ.get("HF_TOKEN"),
        "repo_id": os.environ.get("HF_DB_REPO_ID"),
    }


def download_db():
    """Download the SQLite database from the HF Dataset on startup."""
    cfg = get_config()
    if not cfg["token"] or not cfg["repo_id"]:
        print("[HF Sync] HF_TOKEN or HF_DB_REPO_ID not set. Skipping DB download.")
        return False

    print(f"[HF Sync] Attempting to download database from {cfg['repo_id']}...")
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        hf_hub_download(
            repo_id=cfg["repo_id"],
            filename=DB_FILE,
            repo_type="dataset",
            local_dir=str(DB_PATH.parent),
            token=cfg["token"],
        )
        print("[HF Sync] Database downloaded successfully.")
        return True
    except Exception as e:
        print(f"[HF Sync] Warning: Could not download database (might be a new setup): {e}")
        return False


def _async_upload():
    """Internal upload runner to execute in a separate thread."""
    cfg = get_config()
    if not cfg["token"] or not cfg["repo_id"]:
        return

    if not DB_PATH.exists():
        print("[HF Sync] Local DB file does not exist. Skipping upload.")
        return

    # Acquire lock to ensure only one thread uploads at a time
    if not _upload_lock.acquire(blocking=False):
        print("[HF Sync] Upload already in progress. Skipping duplicate request.")
        return

    try:
        print(f"[HF Sync] Starting database upload to {cfg['repo_id']}...")
        api = HfApi()
        api.upload_file(
            path_or_fileobj=str(DB_PATH),
            path_in_repo=DB_FILE,
            repo_id=cfg["repo_id"],
            repo_type="dataset",
            token=cfg["token"],
        )
        print("[HF Sync] Database uploaded successfully.")
    except Exception as e:
        print(f"[HF Sync] Error uploading database: {e}")
    finally:
        _upload_lock.release()


def upload_db():
    """Upload the SQLite database in the background to avoid blocking the web request."""
    cfg = get_config()
    if not cfg["token"] or not cfg["repo_id"]:
        return

    thread = threading.Thread(target=_async_upload)
    thread.daemon = True
    thread.start()


def upload_db_now():
    """Upload the SQLite database synchronously for maintenance operations."""
    _async_upload()
