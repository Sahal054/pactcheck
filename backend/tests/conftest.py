"""All tests run without credentials, network access or mutations to user reports."""

from pathlib import Path
import pytest
from app.config import settings
from app.services.ai.embeddings import EmbeddingService, get_embedding_service
from app.services.rag.playbook import index_playbook

ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = ROOT / "backend/data/playbook/legal_playbook.md"
SAMPLES = ROOT / "sample_data"
ORIGINAL_LOCAL_MODEL = EmbeddingService._local_model


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch):
    for name, value in settings.model_dump().items():
        monkeypatch.setattr(settings, name, value)
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "embedding_provider", "local")
    monkeypatch.setattr(
        settings, "local_embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
    )
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(EmbeddingService, "_local_model", lambda self: None)
    get_embedding_service.cache_clear()
    yield
    get_embedding_service.cache_clear()


@pytest.fixture
def index_dir(tmp_path):
    path = tmp_path / "indexes"
    index_playbook(str(PLAYBOOK), str(path))
    return path


@pytest.fixture
def reviewer(index_dir):
    from app.services.analysis.reviewer import ContractReviewer

    return ContractReviewer(str(index_dir))


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app import main

    base = tmp_path / "data"
    for folder in ("playbook", "contracts", "indexes", "reports"):
        (base / folder).mkdir(parents=True)
    (base / "playbook/legal_playbook.md").write_bytes(PLAYBOOK.read_bytes())
    monkeypatch.setattr(main, "BASE", base)
    from fastapi.testclient import TestClient

    with TestClient(main.app) as test_client:
        yield test_client
