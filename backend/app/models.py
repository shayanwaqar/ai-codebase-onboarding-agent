import re
from typing import Optional

from pydantic import BaseModel, field_validator


COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def normalize_repo_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return value[:-4] if value.endswith(".git") else value


def validate_commit_sha(value: str) -> str:
    if not COMMIT_SHA_PATTERN.fullmatch(value):
        raise ValueError("commit_sha must be a 40-character lowercase hexadecimal SHA.")
    return value


def validate_optional_commit_sha(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    return validate_commit_sha(value)


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


class RepositoryIngestRequest(BaseModel):
    url: str


class FileMetadata(BaseModel):
    file_path: str
    extension: str
    language: str
    content: str
    line_count: int


class RepositoryIngestResponse(BaseModel):
    repository_url: str
    owner: str
    name: str
    commit_sha: str
    file_count: int
    files: list[FileMetadata]

    @field_validator("commit_sha")
    @classmethod
    def validate_response_commit_sha(cls, value: str) -> str:
        return validate_commit_sha(value)


class CodeChunk(BaseModel):
    chunk_id: str
    repo_id: str
    repo_url: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    commit_sha: Optional[str] = None
    file_path: str
    language: str
    extension: str
    start_line: int
    end_line: int
    content: str
    char_count: int
    token_count: Optional[int] = None

    @field_validator("repo_url")
    @classmethod
    def normalize_chunk_repo_url(cls, value: Optional[str]) -> Optional[str]:
        return normalize_repo_url(value)

    @field_validator("commit_sha")
    @classmethod
    def validate_chunk_commit_sha(cls, value: Optional[str]) -> Optional[str]:
        return validate_optional_commit_sha(value)


class RepositoryChunkResponse(BaseModel):
    repo_id: str
    chunk_count: int
    chunks: list[CodeChunk]
