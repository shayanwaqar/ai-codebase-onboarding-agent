from app.config import settings


class EmbeddingError(RuntimeError):
    pass


class OpenAIEmbeddingService:
    def __init__(
        self,
        api_key: str = settings.openai_api_key,
        model: str = settings.openai_embedding_model,
        batch_size: int = settings.openai_embedding_batch_size,
    ) -> None:
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY is required for embedding generation.")
        if batch_size < 1:
            raise EmbeddingError("OpenAI embedding batch size must be at least 1.")

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._batch_size = batch_size

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start_index in range(0, len(texts), self._batch_size):
            batch = texts[start_index : start_index + self._batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            embeddings.extend(item.embedding for item in response.data)
        return embeddings
