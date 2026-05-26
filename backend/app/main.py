from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.chat import ChatError
from app.embeddings import EmbeddingError
from app.github import GitHubUrlError, RepositoryError
from app.ingestion import ingest_repository
from app.indexing import index_repository_url_with_defaults
from app.models import (
    AskRequest,
    AskResponse,
    HealthResponse,
    RepositoryIndexRequest,
    RepositoryIndexResponse,
    RepositoryIngestRequest,
    RepositoryIngestResponse,
)
from app.qa import (
    CitationMetadataError,
    RepositoryNotIndexedError,
    answer_repo_question_with_defaults,
)
from app.vector_store import VectorStoreError

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Indexes public GitHub repositories and answers onboarding questions with source citations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, environment=settings.app_env)


@app.post(
    "/repositories/ingest",
    response_model=RepositoryIngestResponse,
    status_code=status.HTTP_200_OK,
    tags=["repositories"],
)
def ingest_repository_endpoint(request: RepositoryIngestRequest) -> RepositoryIngestResponse:
    try:
        return ingest_repository(request.url)
    except GitHubUrlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RepositoryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post(
    "/repos/{repo_id}/index",
    response_model=RepositoryIndexResponse,
    status_code=status.HTTP_200_OK,
    tags=["repositories"],
)
def index_repository_endpoint(repo_id: str, request: RepositoryIndexRequest) -> RepositoryIndexResponse:
    try:
        return index_repository_url_with_defaults(repo_id=repo_id, url=request.url)
    except GitHubUrlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except RepositoryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except VectorStoreError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.post(
    "/repos/{repo_id}/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    tags=["repositories"],
)
def ask_repository_endpoint(repo_id: str, request: AskRequest) -> AskResponse:
    try:
        return answer_repo_question_with_defaults(
            repo_id=repo_id,
            question=request.question,
            top_k=request.top_k or 5,
        )
    except RepositoryNotIndexedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except VectorStoreError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except CitationMetadataError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
