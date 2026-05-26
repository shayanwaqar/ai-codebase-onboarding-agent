import os

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


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
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_batch_size: int = 64
    openai_chat_model: str = "gpt-4o-mini"
    chroma_persist_dir: str = "data/chroma"
    chroma_collection_name: str = "code_chunks"


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
    openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_embedding_batch_size=int(os.getenv("OPENAI_EMBEDDING_BATCH_SIZE", "64")),
    openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
    chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", "data/chroma"),
    chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "code_chunks"),
)
