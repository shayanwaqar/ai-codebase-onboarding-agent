from pydantic import BaseModel


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
    file_count: int
    files: list[FileMetadata]


class CodeChunk(BaseModel):
    chunk_id: str
    repo_id: str
    file_path: str
    language: str
    extension: str
    start_line: int
    end_line: int
    content: str
    char_count: int


class RepositoryChunkResponse(BaseModel):
    repo_id: str
    chunk_count: int
    chunks: list[CodeChunk]
