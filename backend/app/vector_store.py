from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.models import CodeChunk, RetrievedChunk


class VectorStoreError(RuntimeError):
    pass


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: str = settings.chroma_persist_dir,
        collection_name: str = settings.chroma_collection_name,
    ) -> None:
        from chromadb import PersistentClient

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def replace_repo_chunks(
        self,
        repo_id: str,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunk count and embedding count must match.")

        self._delete_repo(repo_id)
        if not chunks:
            return

        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.content for chunk in chunks],
            metadatas=[chunk_to_metadata(chunk) for chunk in chunks],
        )

    def query(self, repo_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        if top_k < 1:
            raise VectorStoreError("top_k must be at least 1.")

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"repo_id": repo_id},
        )
        return parse_query_result(result)

    def _delete_repo(self, repo_id: str) -> None:
        try:
            self._collection.delete(where={"repo_id": repo_id})
        except Exception:
            # Chroma raises for some empty-collection delete paths. Replacement is still safe.
            return


def chunk_to_metadata(chunk: CodeChunk) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "repo_id": chunk.repo_id,
        "repo_url": chunk.repo_url or "",
        "repo_owner": chunk.repo_owner or "",
        "repo_name": chunk.repo_name or "",
        "commit_sha": chunk.commit_sha or "",
        "file_path": chunk.file_path,
        "language": chunk.language,
        "extension": chunk.extension,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "char_count": chunk.char_count,
    }
    if chunk.token_count is not None:
        metadata["token_count"] = chunk.token_count
    return metadata


def metadata_to_chunk(
    chunk_id: str,
    metadata: dict[str, Any],
    content: str,
) -> CodeChunk:
    token_count = metadata.get("token_count")
    return CodeChunk(
        chunk_id=chunk_id,
        repo_id=str(metadata["repo_id"]),
        repo_url=optional_string(metadata.get("repo_url")),
        repo_owner=optional_string(metadata.get("repo_owner")),
        repo_name=optional_string(metadata.get("repo_name")),
        commit_sha=optional_string(metadata.get("commit_sha")),
        file_path=str(metadata["file_path"]),
        language=str(metadata["language"]),
        extension=str(metadata["extension"]),
        start_line=int(metadata["start_line"]),
        end_line=int(metadata["end_line"]),
        content=content,
        char_count=int(metadata["char_count"]),
        token_count=int(token_count) if token_count is not None else None,
    )


def parse_query_result(result: dict[str, Any]) -> list[RetrievedChunk]:
    ids = first_result_list(result.get("ids"))
    metadatas = first_result_list(result.get("metadatas"))
    documents = first_result_list(result.get("documents"))
    distances = first_result_list(result.get("distances"))

    retrieved: list[RetrievedChunk] = []
    for index, chunk_id in enumerate(ids):
        distance = float(distances[index]) if index < len(distances) else 0.0
        score = 1.0 / (1.0 + distance)
        retrieved.append(
            RetrievedChunk(
                chunk=metadata_to_chunk(
                    chunk_id=str(chunk_id),
                    metadata=metadatas[index],
                    content=documents[index],
                ),
                score=score,
            )
        )
    return retrieved


def first_result_list(value: Optional[list[Any]]) -> list[Any]:
    if not value:
        return []
    first = value[0]
    return first if first else []


def optional_string(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    return str(value)
