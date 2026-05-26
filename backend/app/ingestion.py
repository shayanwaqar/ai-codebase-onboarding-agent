import tempfile
from pathlib import Path
from typing import Optional

from app.config import settings
from app.github import clone_repository, parse_github_url
from app.models import FileMetadata, RepositoryIngestResponse


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}

IGNORED_FILE_NAMES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "uv.lock",
    "cargo.lock",
    "gemfile.lock",
    "composer.lock",
}

LANGUAGE_BY_EXTENSION = {
    ".css": "CSS",
    ".dockerfile": "Dockerfile",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "JavaScript React",
    ".md": "Markdown",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".sql": "SQL",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".txt": "Text",
    ".yaml": "YAML",
    ".yml": "YAML",
}


def ingest_repository(url: str) -> RepositoryIngestResponse:
    repository = parse_github_url(url)

    with tempfile.TemporaryDirectory(prefix="codebase-onboarding-") as temp_dir:
        repo_dir = Path(temp_dir) / repository.name
        clone_repository(repository.clone_url, repo_dir)
        files = extract_repository_files(repo_dir)

    return RepositoryIngestResponse(
        repository_url=repository.clone_url,
        owner=repository.owner,
        name=repository.name,
        file_count=len(files),
        files=files,
    )


def extract_repository_files(
    repo_root: Path,
    max_file_size_bytes: int = settings.max_file_size_bytes,
) -> list[FileMetadata]:
    files: list[FileMetadata] = []

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(repo_root)
        if should_ignore_path(relative_path):
            continue

        if path.stat().st_size > max_file_size_bytes:
            continue

        text = read_text_file(path)
        if text is None:
            continue

        files.append(
            FileMetadata(
                file_path=relative_path.as_posix(),
                extension=path.suffix.lower(),
                language=detect_language(path),
                content=text,
                line_count=count_lines(text),
            )
        )

    return files


def should_ignore_path(relative_path: Path) -> bool:
    parts = {part.lower() for part in relative_path.parts}
    if parts.intersection(IGNORED_DIR_NAMES):
        return True

    name = relative_path.name.lower()
    return name in IGNORED_FILE_NAMES or name.endswith(".lock")


def read_text_file(path: Path) -> Optional[str]:
    sample = path.read_bytes()
    if b"\x00" in sample:
        return None

    try:
        return sample.decode("utf-8")
    except UnicodeDecodeError:
        return None


def detect_language(path: Path) -> str:
    if path.name.lower() == "dockerfile":
        return "Dockerfile"
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "Text")


def count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)
