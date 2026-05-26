import pytest

from app.github import GitHubUrlError, parse_github_url


def test_parse_github_url_normalizes_clone_url() -> None:
    repository = parse_github_url("https://github.com/openai/openai-python")

    assert repository.owner == "openai"
    assert repository.name == "openai-python"
    assert repository.web_url == "https://github.com/openai/openai-python"
    assert repository.clone_url == "https://github.com/openai/openai-python.git"


def test_parse_github_url_accepts_git_suffix() -> None:
    repository = parse_github_url("https://github.com/openai/openai-python.git")

    assert repository.owner == "openai"
    assert repository.name == "openai-python"
    assert repository.clone_url == "https://github.com/openai/openai-python.git"


def test_parse_github_url_rejects_http_url() -> None:
    with pytest.raises(GitHubUrlError):
        parse_github_url("http://github.com/openai/openai-python")


def test_parse_github_url_rejects_non_github_url() -> None:
    with pytest.raises(GitHubUrlError):
        parse_github_url("https://example.com/openai/openai-python")


def test_parse_github_url_rejects_extra_path_segments() -> None:
    with pytest.raises(GitHubUrlError):
        parse_github_url("https://github.com/openai/openai-python/tree/main")


def test_parse_github_url_rejects_invalid_owner_or_repo_characters() -> None:
    with pytest.raises(GitHubUrlError):
        parse_github_url("https://github.com/openai%2Fbad/openai-python")
