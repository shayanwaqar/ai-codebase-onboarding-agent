import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Codebase Onboarding Agent"
    app_env: str = "development"
    openai_api_key: str = ""
    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    max_file_size_bytes: int = 200_000
    git_clone_timeout_seconds: int = 60
    chunk_max_lines: int = 80
    chunk_overlap_lines: int = 10
    chunk_max_chars: int = 8_000


def _get_csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings(
    app_name=os.getenv("APP_NAME", "AI Codebase Onboarding Agent"),
    app_env=os.getenv("APP_ENV", "development"),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    cors_allowed_origins=_get_csv_env("CORS_ALLOWED_ORIGINS", "http://localhost:5173"),
    max_file_size_bytes=int(os.getenv("MAX_FILE_SIZE_BYTES", "200000")),
    git_clone_timeout_seconds=int(os.getenv("GIT_CLONE_TIMEOUT_SECONDS", "60")),
    chunk_max_lines=int(os.getenv("CHUNK_MAX_LINES", "80")),
    chunk_overlap_lines=int(os.getenv("CHUNK_OVERLAP_LINES", "10")),
    chunk_max_chars=int(os.getenv("CHUNK_MAX_CHARS", "8000")),
)
