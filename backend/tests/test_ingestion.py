from pathlib import Path

from app.ingestion import extract_repository_files, should_ignore_path


def write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_should_ignore_configured_directories_and_lockfiles() -> None:
    assert should_ignore_path(Path(".git/config"))
    assert should_ignore_path(Path("node_modules/react/index.js"))
    assert should_ignore_path(Path("dist/app.js"))
    assert should_ignore_path(Path("build/app.js"))
    assert should_ignore_path(Path("__pycache__/module.pyc"))
    assert should_ignore_path(Path("package-lock.json"))
    assert should_ignore_path(Path("requirements.lock"))


def test_extract_repository_files_skips_ignored_binary_and_large_files(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "app.py", b"print('hello')\nprint('world')\n")
    write_file(tmp_path / "README.md", b"# Example\n\nSetup notes\n")
    write_file(tmp_path / ".git" / "config", b"[remote]\n")
    write_file(tmp_path / "node_modules" / "lib.js", b"console.log('skip')\n")
    write_file(tmp_path / "package-lock.json", b"{}\n")
    write_file(tmp_path / "image.png", b"\x89PNG\x00binary")
    write_file(tmp_path / "large.txt", b"x" * 20)

    files = extract_repository_files(tmp_path, max_file_size_bytes=10)

    assert [file.file_path for file in files] == []


def test_extract_repository_files_returns_metadata(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "app.py", b"print('hello')\nprint('world')\n")
    write_file(tmp_path / "docs" / "setup.md", b"# Setup\nRun tests")

    files = extract_repository_files(tmp_path, max_file_size_bytes=200_000)

    assert [(file.file_path, file.language, file.line_count) for file in files] == [
        ("docs/setup.md", "Markdown", 2),
        ("src/app.py", "Python", 2),
    ]
    assert files[1].extension == ".py"
    assert files[1].content == "print('hello')\nprint('world')\n"
