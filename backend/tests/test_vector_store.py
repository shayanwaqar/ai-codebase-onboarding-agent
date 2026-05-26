import pytest

from app.models import CodeChunk
from app.vector_store import (
    ChromaVectorStore,
    VectorStoreError,
    chunk_to_metadata,
    metadata_to_chunk,
    parse_query_result,
)


COMMIT_SHA = "a" * 40


def make_chunk() -> CodeChunk:
    return CodeChunk(
        chunk_id="chunk-1",
        repo_id="repo-1",
        repo_url="https://github.com/example/repo.git",
        repo_owner="example",
        repo_name="repo",
        commit_sha=COMMIT_SHA,
        file_path="src/app.py",
        language="Python",
        extension=".py",
        start_line=1,
        end_line=2,
        content="line 1\nline 2\n",
        char_count=14,
        token_count=5,
    )


def test_chunk_metadata_round_trips() -> None:
    chunk = make_chunk()
    metadata = chunk_to_metadata(chunk)

    assert metadata["repo_url"] == "https://github.com/example/repo"
    assert metadata["token_count"] == 5

    restored = metadata_to_chunk("chunk-1", metadata, chunk.content)

    assert restored == chunk


def test_parse_query_result_returns_retrieved_chunks() -> None:
    chunk = make_chunk()
    result = {
        "ids": [["chunk-1"]],
        "metadatas": [[chunk_to_metadata(chunk)]],
        "documents": [[chunk.content]],
        "distances": [[0.25]],
    }

    retrieved = parse_query_result(result)

    assert len(retrieved) == 1
    assert retrieved[0].chunk.file_path == "src/app.py"
    assert retrieved[0].score == 0.8


def test_vector_store_error_for_mismatched_embedding_count() -> None:
    store = object.__new__(ChromaVectorStore)

    with pytest.raises(VectorStoreError):
        store.replace_repo_chunks("repo-1", [make_chunk()], [])
