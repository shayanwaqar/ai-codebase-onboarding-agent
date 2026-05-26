import pytest
from pydantic import ValidationError

from app.models import CodeChunk, RepositoryIngestResponse


VALID_SHA = "a" * 40


def test_repository_ingest_response_requires_full_commit_sha() -> None:
    response = RepositoryIngestResponse(
        repository_url="https://github.com/example/repo",
        owner="example",
        name="repo",
        commit_sha=VALID_SHA,
        file_count=0,
        files=[],
    )

    assert response.commit_sha == VALID_SHA


def test_repository_ingest_response_rejects_empty_or_short_commit_sha() -> None:
    with pytest.raises(ValidationError):
        RepositoryIngestResponse(
            repository_url="https://github.com/example/repo",
            owner="example",
            name="repo",
            commit_sha="",
            file_count=0,
            files=[],
        )


def test_repository_ingest_response_rejects_uppercase_commit_sha() -> None:
    with pytest.raises(ValidationError):
        RepositoryIngestResponse(
            repository_url="https://github.com/example/repo",
            owner="example",
            name="repo",
            commit_sha="A" * 40,
            file_count=0,
            files=[],
        )

    with pytest.raises(ValidationError):
        RepositoryIngestResponse(
            repository_url="https://github.com/example/repo",
            owner="example",
            name="repo",
            commit_sha="abc123",
            file_count=0,
            files=[],
        )


def test_code_chunk_allows_missing_commit_sha_but_validates_when_present() -> None:
    chunk = CodeChunk(
        chunk_id="chunk-1",
        repo_id="repo-1",
        file_path="src/app.py",
        language="Python",
        extension=".py",
        start_line=1,
        end_line=1,
        content="print('hello')\n",
        char_count=15,
    )

    assert chunk.commit_sha is None
    assert chunk.token_count is None

    with pytest.raises(ValidationError):
        CodeChunk(
            chunk_id="chunk-1",
            repo_id="repo-1",
            commit_sha="main",
            file_path="src/app.py",
            language="Python",
            extension=".py",
            start_line=1,
            end_line=1,
            content="print('hello')\n",
            char_count=15,
        )


def test_code_chunk_normalizes_repo_url() -> None:
    chunk = CodeChunk(
        chunk_id="chunk-1",
        repo_id="repo-1",
        repo_url="https://github.com/example/repo.git",
        file_path="src/app.py",
        language="Python",
        extension=".py",
        start_line=1,
        end_line=1,
        content="print('hello')\n",
        char_count=15,
        token_count=4,
    )

    assert chunk.repo_url == "https://github.com/example/repo"
    assert chunk.token_count == 4
