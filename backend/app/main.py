from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.github import GitHubUrlError, RepositoryCloneError
from app.ingestion import ingest_repository
from app.models import HealthResponse, RepositoryIngestRequest, RepositoryIngestResponse

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
    except RepositoryCloneError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
