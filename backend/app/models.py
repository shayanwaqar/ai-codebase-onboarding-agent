import re
from typing import Literal, Optional

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


def validate_optional_positive_int(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 1:
        raise ValueError("value must be at least 1 when provided.")
    return value


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

    @field_validator("token_count")
    @classmethod
    def validate_chunk_token_count(cls, value: Optional[int]) -> Optional[int]:
        return validate_optional_positive_int(value)


class RepositoryChunkResponse(BaseModel):
    repo_id: str
    chunk_count: int
    chunks: list[CodeChunk]


class RepositoryIndexRequest(BaseModel):
    url: str


class RepositoryIndexResponse(BaseModel):
    repo_id: str
    status: str
    chunk_count: int


class RetrievedChunk(BaseModel):
    chunk: CodeChunk
    score: float


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question is required.")
        return stripped

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 1 or value > 10:
            raise ValueError("top_k must be between 1 and 10.")
        return value


class SourceCitation(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    repo_owner: str
    repo_name: str
    commit_sha: str
    github_url: str
    snippet: str


class AskResponse(BaseModel):
    repo_id: str
    question: str
    answer: str
    citations: list[SourceCitation]
    confidence: Literal["low", "medium", "high"]
