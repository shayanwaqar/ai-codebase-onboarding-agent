# AI Codebase Onboarding Agent

An MVP app for indexing public GitHub repositories and answering codebase onboarding questions with source-linked citations.

Milestone 1 includes the local development scaffold only:

- FastAPI backend
- React + TypeScript frontend
- Docker Compose development workflow
- Backend health check at `/health`
- Frontend landing page with a GitHub repository URL input placeholder

Current backend ingestion support:

- `POST /repositories/ingest`
- Accepts a public GitHub repository URL
- Clones into a temporary directory
- Returns extracted text file metadata
- Backend chunking service preserves file path and line ranges for future citations

AI answers, embeddings, and vector search are intentionally not implemented yet.

## Project Structure

```text
backend/
  app/
    main.py
    config.py
    models.py
  tests/
frontend/
  src/
    App.tsx
    main.tsx
docker-compose.yml
```

## Local Development

Copy the example environment files before running locally:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Run the full local stack:

```bash
docker compose up --build
```

This requires Docker Compose v2. Check availability with:

```bash
docker compose version
```

Then open:

- Frontend: http://localhost:5173
- Backend health check: http://localhost:8000/health
- Backend API docs: http://localhost:8000/docs

Example ingestion request:

```bash
curl -X POST http://localhost:8000/repositories/ingest \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/octocat/Hello-World"}'
```

## Backend Only

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## Checks

```bash
cd backend && pytest
cd frontend && npm run lint
```

Backend tests cover URL validation, ingestion filtering, chunking, citation metadata, and vector indexing service behavior.

## Embeddings

Backend unit tests use fake embedding providers and do not require `OPENAI_API_KEY`.

Real repository indexing and semantic retrieval require an OpenAI API key:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Keep real values in local `.env` files only. Do not commit `.env`.
