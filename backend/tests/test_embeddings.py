import pytest

from app.embeddings import EmbeddingError, OpenAIEmbeddingService


def test_openai_embedding_service_requires_api_key() -> None:
    with pytest.raises(EmbeddingError):
        OpenAIEmbeddingService(api_key="")


def test_openai_embedding_service_rejects_invalid_batch_size() -> None:
    with pytest.raises(EmbeddingError):
        OpenAIEmbeddingService(api_key="test-key", batch_size=0)
