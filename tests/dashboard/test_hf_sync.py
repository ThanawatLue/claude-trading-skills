import sqlite3
from unittest.mock import MagicMock, patch

from dashboard import hf_sync


def test_hf_sync_skips_when_no_credentials(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HF_DB_REPO_ID", raising=False)

    assert hf_sync.download_db() is False


def test_hf_sync_download_success(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_TOKEN", "mock_token")
    monkeypatch.setenv("HF_DB_REPO_ID", "test/repo")

    mock_db = tmp_path / "market_cache.db"
    monkeypatch.setattr(hf_sync, "DB_PATH", mock_db)

    with patch("dashboard.hf_sync.hf_hub_download") as mock_download:
        assert hf_sync.download_db() is True
        mock_download.assert_called_once()


def test_hf_sync_upload_creates_backup_and_cleans_up(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_TOKEN", "mock_token")
    monkeypatch.setenv("HF_DB_REPO_ID", "test/repo")

    mock_db = tmp_path / "market_cache.db"
    monkeypatch.setattr(hf_sync, "DB_PATH", mock_db)

    # Initialize a valid sqlite db
    with sqlite3.connect(mock_db) as conn:
        conn.execute("CREATE TABLE test_data (id INT, val TEXT)")
        conn.execute("INSERT INTO test_data VALUES (1, 'hello')")

    mock_api = MagicMock()
    with patch("dashboard.hf_sync.HfApi", return_value=mock_api):
        hf_sync.upload_db_now()

        mock_api.upload_file.assert_called_once()
        uploaded_path = mock_api.upload_file.call_args[1]["path_or_fileobj"]
        assert uploaded_path.endswith(".upload_tmp")

        # Verify uploaded file was cleaned up
        temp_backup = mock_db.with_suffix(".upload_tmp")
        assert not temp_backup.exists()


def test_hf_sync_skips_concurrent_upload(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_TOKEN", "mock_token")
    monkeypatch.setenv("HF_DB_REPO_ID", "test/repo")

    mock_db = tmp_path / "market_cache.db"
    mock_db.touch()
    monkeypatch.setattr(hf_sync, "DB_PATH", mock_db)

    # Lock already acquired
    hf_sync._upload_lock.acquire()
    try:
        with patch("dashboard.hf_sync.HfApi") as mock_api:
            hf_sync.upload_db_now()
            mock_api.assert_not_called()
    finally:
        hf_sync._upload_lock.release()
