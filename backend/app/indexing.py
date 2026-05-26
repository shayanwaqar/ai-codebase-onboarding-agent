from typing import Protocol

from app.chunking import chunk_repository_files
from app.embeddings import OpenAIEmbeddingService
from app.ingestion import ingest_repository
from app.models import (
    CodeChunk,
    RepositoryIndexResponse,
    RepositoryIngestResponse,
    RetrievedChunk,
)
from app.vector_store import ChromaVectorStore


class EmbeddingService(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class VectorStore(Protocol):
    def replace_repo_chunks(
        self,
        repo_id: str,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ) -> None:
        pass

    def query(self, repo_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        pass


def index_ingested_repository(
    repo_id: str,
    ingested_repo: RepositoryIngestResponse,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
) -> RepositoryIndexResponse:
    chunk_response = chunk_repository_files(
        repo_id=repo_id,
        files=ingested_repo.files,
        repo_url=ingested_repo.repository_url,
        repo_owner=ingested_repo.owner,
        repo_name=ingested_repo.name,
        commit_sha=ingested_repo.commit_sha,
    )
    embeddings = embedding_service.embed_texts([chunk.content for chunk in chunk_response.chunks])
    vector_store.replace_repo_chunks(repo_id, chunk_response.chunks, embeddings)

    return RepositoryIndexResponse(
        repo_id=repo_id,
        status="indexed",
        chunk_count=chunk_response.chunk_count,
    )


def index_repository_url(
    repo_id: str,
    url: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
) -> RepositoryIndexResponse:
    ingested_repo = ingest_repository(url)
    return index_ingested_repository(
        repo_id=repo_id,
        ingested_repo=ingested_repo,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def retrieve_relevant_chunks(
    repo_id: str,
    query: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    query_embedding = embedding_service.embed_texts([query])[0]
    return vector_store.query(repo_id=repo_id, query_embedding=query_embedding, top_k=top_k)


def index_repository_url_with_defaults(repo_id: str, url: str) -> RepositoryIndexResponse:
    return index_repository_url(
        repo_id=repo_id,
        url=url,
        embedding_service=OpenAIEmbeddingService(),
        vector_store=ChromaVectorStore(),
    )
