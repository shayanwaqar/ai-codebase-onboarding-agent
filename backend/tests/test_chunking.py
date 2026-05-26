import pytest

from app.chunking import ChunkingConfig, chunk_file, chunk_repository_files
from app.models import FileMetadata


def make_file(content: str, file_path: str = "src/app.py") -> FileMetadata:
    return FileMetadata(
        file_path=file_path,
        extension=".py",
        language="Python",
        content=content,
        line_count=len(content.splitlines()),
    )


def test_small_file_becomes_one_chunk() -> None:
    file_metadata = make_file("line 1\nline 2\n")

    chunks = chunk_file("repo-1", file_metadata, ChunkingConfig(max_lines=10, overlap_lines=2))

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2
    assert chunks[0].content == "line 1\nline 2\n"


def test_long_file_becomes_multiple_chunks_with_accurate_line_numbers() -> None:
    file_metadata = make_file("".join(f"line {line}\n" for line in range(1, 8)))

    chunks = chunk_file("repo-1", file_metadata, ChunkingConfig(max_lines=3, overlap_lines=0))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [
        (1, 3),
        (4, 6),
        (7, 7),
    ]
    assert chunks[1].content == "line 4\nline 5\nline 6\n"


def test_overlap_repeats_trailing_lines_in_next_chunk() -> None:
    file_metadata = make_file("".join(f"line {line}\n" for line in range(1, 8)))

    chunks = chunk_file("repo-1", file_metadata, ChunkingConfig(max_lines=3, overlap_lines=1))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [
        (1, 3),
        (3, 5),
        (5, 7),
    ]
    assert chunks[1].content == "line 3\nline 4\nline 5\n"


def test_empty_or_whitespace_only_files_are_skipped() -> None:
    assert chunk_file("repo-1", make_file("")) == []
    assert chunk_file("repo-1", make_file("  \n\t\n")) == []


def test_metadata_is_preserved() -> None:
    file_metadata = FileMetadata(
        file_path="docs/setup.md",
        extension=".md",
        language="Markdown",
        content="# Setup\nRun tests\n",
        line_count=2,
    )

    chunks = chunk_file("repo-1", file_metadata, ChunkingConfig(max_lines=10, overlap_lines=0))

    assert chunks[0].repo_id == "repo-1"
    assert chunks[0].file_path == "docs/setup.md"
    assert chunks[0].language == "Markdown"
    assert chunks[0].extension == ".md"
    assert chunks[0].char_count == len("# Setup\nRun tests\n")


def test_chunk_repository_files_returns_chunk_count() -> None:
    response = chunk_repository_files(
        "repo-1",
        [
            make_file("line 1\nline 2\n", "src/app.py"),
            make_file("   \n", "empty.py"),
        ],
        ChunkingConfig(max_lines=10, overlap_lines=0),
    )

    assert response.repo_id == "repo-1"
    assert response.chunk_count == 1
    assert response.chunks[0].file_path == "src/app.py"


def test_invalid_overlap_is_rejected() -> None:
    with pytest.raises(ValueError):
        chunk_file("repo-1", make_file("line 1\n"), ChunkingConfig(max_lines=2, overlap_lines=2))
