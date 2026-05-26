import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Sequence

from app.config import settings
from app.models import CodeChunk, FileMetadata, RepositoryChunkResponse


@dataclass(frozen=True)
class ChunkingConfig:
    max_lines: int
    overlap_lines: int
    max_chars: int

    def __post_init__(self) -> None:
        if self.max_lines < 1:
            raise ValueError("max_lines must be at least 1.")
        if self.max_chars < 1:
            raise ValueError("max_chars must be at least 1.")
        if self.overlap_lines < 0:
            raise ValueError("overlap_lines cannot be negative.")
        if self.overlap_lines >= self.max_lines:
            raise ValueError("overlap_lines must be smaller than max_lines.")


def default_chunking_config() -> ChunkingConfig:
    return ChunkingConfig(
        max_lines=settings.chunk_max_lines,
        overlap_lines=settings.chunk_overlap_lines,
        max_chars=settings.chunk_max_chars,
    )


DEFAULT_CHUNKING_CONFIG = default_chunking_config()


def chunk_repository_files(
    repo_id: str,
    files: Sequence[FileMetadata],
    config: Optional[ChunkingConfig] = None,
    repo_url: Optional[str] = None,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    commit_sha: Optional[str] = None,
) -> RepositoryChunkResponse:
    chunking_config = config or DEFAULT_CHUNKING_CONFIG
    web_url = normalize_repo_url(repo_url)
    chunks: list[CodeChunk] = []

    for file_metadata in files:
        chunks.extend(
            chunk_file(
                repo_id=repo_id,
                file_metadata=file_metadata,
                config=chunking_config,
                repo_url=web_url,
                repo_owner=repo_owner,
                repo_name=repo_name,
                commit_sha=commit_sha,
            )
        )

    return RepositoryChunkResponse(repo_id=repo_id, chunk_count=len(chunks), chunks=chunks)


def chunk_file(
    repo_id: str,
    file_metadata: FileMetadata,
    config: Optional[ChunkingConfig] = None,
    repo_url: Optional[str] = None,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    commit_sha: Optional[str] = None,
) -> list[CodeChunk]:
    chunking_config = config or DEFAULT_CHUNKING_CONFIG
    web_url = normalize_repo_url(repo_url)

    if not file_metadata.content.strip():
        return []

    lines = file_metadata.content.splitlines(keepends=True)
    if not lines:
        return []

    chunks: list[CodeChunk] = []
    start_index = 0

    while start_index < len(lines):
        end_index = find_chunk_end(lines=lines, start_index=start_index, config=chunking_config)
        content = "".join(lines[start_index:end_index])

        if content.strip():
            start_line = start_index + 1
            end_line = end_index
            chunks.append(
                CodeChunk(
                    chunk_id=build_chunk_id(
                        repo_id=repo_id,
                        commit_sha=commit_sha,
                        file_path=file_metadata.file_path,
                        start_line=start_line,
                        end_line=end_line,
                    ),
                    repo_id=repo_id,
                    repo_url=web_url,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    commit_sha=commit_sha,
                    file_path=file_metadata.file_path,
                    language=file_metadata.language,
                    extension=file_metadata.extension,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    char_count=len(content),
                )
            )

        if end_index >= len(lines):
            break

        next_start_index = end_index - chunking_config.overlap_lines
        start_index = next_start_index if next_start_index > start_index else end_index

    return chunks


def find_chunk_end(lines: list[str], start_index: int, config: ChunkingConfig) -> int:
    end_index = start_index
    char_count = 0

    while end_index < len(lines):
        next_line = lines[end_index]
        would_exceed_lines = end_index - start_index >= config.max_lines
        would_exceed_chars = char_count + len(next_line) > config.max_chars

        if end_index > start_index and (would_exceed_lines or would_exceed_chars):
            break

        char_count += len(next_line)
        end_index += 1

    return end_index


def build_chunk_id(
    repo_id: str,
    commit_sha: Optional[str],
    file_path: str,
    start_line: int,
    end_line: int,
) -> str:
    stable_key = json.dumps(
        [repo_id, commit_sha, file_path, start_line, end_line],
        separators=(",", ":"),
    )
    digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    return digest[:24]


def normalize_repo_url(repo_url: Optional[str]) -> Optional[str]:
    if repo_url is None:
        return None
    return repo_url[:-4] if repo_url.endswith(".git") else repo_url
