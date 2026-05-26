import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


class GitHubUrlError(ValueError):
    pass


class RepositoryError(RuntimeError):
    pass


class RepositoryCloneError(RepositoryError):
    pass


class RepositoryMetadataError(RepositoryError):
    pass


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str
    web_url: str
    clone_url: str


_REPO_PART_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_github_url(url: str) -> GitHubRepository:
    parsed = urlparse(url.strip())

    if parsed.scheme != "https":
        raise GitHubUrlError("Only https GitHub URLs are supported.")

    if parsed.netloc.lower() != "github.com":
        raise GitHubUrlError("Repository URL must use github.com.")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) != 2:
        raise GitHubUrlError("Repository URL must include an owner and repository name.")

    owner, repo_name = parts[0], parts[1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not _REPO_PART_PATTERN.match(owner) or not _REPO_PART_PATTERN.match(repo_name):
        raise GitHubUrlError("Repository owner and name contain unsupported characters.")

    if not owner or not repo_name:
        raise GitHubUrlError("Repository owner and name are required.")

    return GitHubRepository(
        owner=owner,
        name=repo_name,
        web_url=f"https://github.com/{owner}/{repo_name}",
        clone_url=f"https://github.com/{owner}/{repo_name}.git",
    )


def clone_repository(clone_url: str, destination: Path) -> None:
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(destination)],
            check=True,
            capture_output=True,
            text=True,
            timeout=settings.git_clone_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RepositoryCloneError("Timed out while cloning repository.") from exc
    except FileNotFoundError as exc:
        raise RepositoryCloneError("git is not installed or not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "Unable to clone repository."
        raise RepositoryCloneError(detail) from exc


def get_current_commit_sha(repo_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=settings.git_clone_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RepositoryMetadataError("Timed out while reading repository commit SHA.") from exc
    except FileNotFoundError as exc:
        raise RepositoryMetadataError("git is not installed or not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "Unable to read repository commit SHA."
        raise RepositoryMetadataError(detail) from exc

    return result.stdout.strip()
