import pytest

from app.chunking import ChunkingConfig, build_chunk_id, chunk_file, chunk_repository_files
from app.models import FileMetadata


COMMIT_SHA = "a" * 40


def make_file(content: str, file_path: str = "src/app.py") -> FileMetadata:
    return FileMetadata(
        file_path=file_path,
        extension=".py",
        language="Python",
        content=content,
        line_count=len(content.splitlines()),
    )


def make_config(max_lines: int, overlap_lines: int = 0, max_chars: int = 8_000) -> ChunkingConfig:
    return ChunkingConfig(max_lines=max_lines, overlap_lines=overlap_lines, max_chars=max_chars)


def test_small_file_becomes_one_chunk() -> None:
    file_metadata = make_file("line 1\nline 2\n")

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=10, overlap_lines=2))

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2
    assert chunks[0].content == "line 1\nline 2\n"


def test_long_file_becomes_multiple_chunks_with_accurate_line_numbers() -> None:
    file_metadata = make_file("".join(f"line {line}\n" for line in range(1, 8)))

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=3))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [
        (1, 3),
        (4, 6),
        (7, 7),
    ]
    assert chunks[1].content == "line 4\nline 5\nline 6\n"


def test_overlap_repeats_trailing_lines_in_next_chunk() -> None:
    file_metadata = make_file("".join(f"line {line}\n" for line in range(1, 8)))

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=3, overlap_lines=1))

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

    chunks = chunk_file(
        "repo-1",
        file_metadata,
        make_config(max_lines=10),
        repo_url="https://github.com/example/repo.git",
        repo_owner="example",
        repo_name="repo",
        commit_sha=COMMIT_SHA,
    )

    assert chunks[0].repo_id == "repo-1"
    assert chunks[0].repo_url == "https://github.com/example/repo"
    assert chunks[0].repo_owner == "example"
    assert chunks[0].repo_name == "repo"
    assert chunks[0].commit_sha == COMMIT_SHA
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
        make_config(max_lines=10),
        repo_url="https://github.com/example/repo.git",
        repo_owner="example",
        repo_name="repo",
        commit_sha=COMMIT_SHA,
    )

    assert response.repo_id == "repo-1"
    assert response.chunk_count == 1
    assert response.chunks[0].file_path == "src/app.py"
    assert response.chunks[0].repo_url == "https://github.com/example/repo"
    assert response.chunks[0].commit_sha == COMMIT_SHA


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        ChunkingConfig(max_lines=0, overlap_lines=0, max_chars=8_000)
    with pytest.raises(ValueError):
        ChunkingConfig(max_lines=2, overlap_lines=0, max_chars=0)
    with pytest.raises(ValueError):
        ChunkingConfig(max_lines=2, overlap_lines=-1, max_chars=8_000)
    with pytest.raises(ValueError):
        ChunkingConfig(max_lines=2, overlap_lines=2, max_chars=8_000)


def test_single_line_exceeding_max_chars_is_force_included() -> None:
    file_metadata = make_file("this line is longer than max chars\nshort\n")

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=10, max_chars=5))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 1), (2, 2)]
    assert chunks[0].content == "this line is longer than max chars\n"


def test_trailing_blank_lines_do_not_create_empty_chunks() -> None:
    file_metadata = make_file("line 1\nline 2\n\n\n")

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=2))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 2)]
    assert chunks[0].content == "line 1\nline 2\n"


def test_trailing_blank_lines_with_overlap_do_not_create_empty_chunks() -> None:
    file_metadata = make_file("line 1\nline 2\nline 3\n\n\n")

    chunks = chunk_file("repo-1", file_metadata, make_config(max_lines=3, overlap_lines=1))

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 3), (3, 5)]
    assert all(chunk.content.strip() for chunk in chunks)


def test_chunk_id_is_deterministic_and_uses_stable_json_boundaries() -> None:
    chunk_id = build_chunk_id(
        repo_id="repo:one",
        commit_sha=COMMIT_SHA,
        file_path="src/app's.py",
        start_line=1,
        end_line=5,
    )

    assert chunk_id == build_chunk_id("repo:one", COMMIT_SHA, "src/app's.py", 1, 5)
    assert chunk_id != build_chunk_id("repo", f"one:{COMMIT_SHA}", "src/app's.py", 1, 5)
