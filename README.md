# AI Codebase Onboarding Agent

An AI onboarding assistant that indexes a public GitHub repository and answers codebase questions with source-linked file and line citations.

## Problem

Understanding an unfamiliar codebase is slow. Engineers usually jump between README files, package manifests, source folders, and search results before they can answer basic questions like how the app starts, where core logic lives, or how a feature is implemented.

This project turns a public GitHub repository into a local semantic search index, then uses retrieved code chunks to answer onboarding questions with citations back to the exact source lines.

## Features

- Public GitHub repository indexing
- File filtering for generated, binary, oversized, dependency, build, and cache files
- Deterministic line-based chunking with overlap
- OpenAI embeddings with Chroma local vector storage
- Source-grounded ask endpoint
- GitHub permalink citations with commit SHA, file path, and line range
- React frontend for indexing, Q&A, answer history, and citation cards
- Backend tests using fakes/mocks so unit tests do not require an API key

## Architecture

```text
React + TypeScript frontend
        |
        | POST /repos/{repo_id}/index
        | POST /repos/{repo_id}/ask
        v
FastAPI backend
        |
        | clone public GitHub repo
        v
File extraction and filtering
        |
        | line-based chunks with citation metadata
        v
OpenAI embeddings -> Chroma persistent vector store
        |
        | retrieve top-k chunks
        v
OpenAI chat model -> cited answer JSON
```

## Tech Stack

- Frontend: React, TypeScript, Vite
- Backend: FastAPI, Python, Pydantic
- AI: OpenAI embeddings and chat completions
- Vector store: Chroma persistent local storage
- Repo access: local `git clone`
- Local orchestration: Docker Compose
- Tests: Pytest, TypeScript compiler checks

## Project Structure

```text
backend/
  app/
    chat.py          # OpenAI chat wrapper
    chunking.py      # deterministic file chunking
    embeddings.py    # OpenAI embedding wrapper
    github.py        # GitHub URL parsing and clone helpers
    indexing.py      # ingestion + chunking + embedding orchestration
    ingestion.py     # file extraction and filtering
    main.py          # FastAPI routes
    models.py        # API schemas
    qa.py            # retrieval-grounded answer generation
    vector_store.py  # Chroma storage/retrieval
  tests/
frontend/
  src/
    api.ts
    App.tsx
    types.ts
docker-compose.yml
```

## Environment Variables

Copy the example files and fill in local values:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Required for real indexing and asking:

```bash
OPENAI_API_KEY=your_openai_api_key
```

Useful defaults:

```bash
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_BATCH_SIZE=64
OPENAI_CHAT_MODEL=gpt-4o-mini
CHROMA_PERSIST_DIR=data/chroma
CHROMA_COLLECTION_NAME=code_chunks
VITE_API_BASE_URL=http://localhost:8000
```

Do not commit `.env` files. Only `.env.example` files belong in Git.

## Local Setup

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Docker Compose

Docker Compose v2 is required:

```bash
docker compose version
```

Run the stack:

```bash
docker compose up --build
```

The compose file expects `backend/.env` and `frontend/.env` to exist. Chroma data is stored under `backend/data`, which is ignored by Git.

## API Endpoints

Health:

```bash
GET /health
```

Ingest only:

```bash
POST /repositories/ingest
{ "url": "https://github.com/octocat/Hello-World" }
```

Index a repo:

```bash
POST /repos/{repo_id}/index
{ "url": "https://github.com/octocat/Hello-World" }
```

Ask a question:

```bash
POST /repos/{repo_id}/ask
{ "question": "What does this repository do?", "top_k": 5 }
```

## Demo Flow

1. Start backend and frontend.
2. Open http://localhost:5173.
3. Enter a public GitHub repository URL.
4. Click `Index repo`.
5. Wait for the indexed status and chunk count.
6. Ask a question.
7. Review the answer and citation cards.
8. Open a citation link to inspect the exact GitHub source lines.

## Sample Repositories

Small sanity check:

```text
https://github.com/octocat/Hello-World
```

Questions:

- What does this repository contain?
- What files are available?

Python library:

```text
https://github.com/psf/requests
```

Questions:

- How is the package organized?
- Where is the public API defined?
- How does session handling work?

Web framework:

```text
https://github.com/pallets/flask
```

Questions:

- How does routing work?
- Where is the application object implemented?
- How is request handling structured?

## Screenshots

Add screenshots before sharing the repo publicly:

```text
docs/screenshots/indexing.png
docs/screenshots/answer-with-citations.png
docs/screenshots/source-link.png
```

Suggested screenshots:

- Repository indexing success state
- Q&A history with answer and confidence badge
- Citation cards with GitHub source links

## Checks

Backend:

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Backend tests use fakes for OpenAI and vector-store behavior where appropriate. Unit tests do not require `OPENAI_API_KEY`.

## Known Limitations

- Public GitHub repositories only
- No authentication or private repo support
- Indexing and asking are synchronous
- No background job queue or progress polling
- No streaming responses
- No multi-repo dashboard
- No syntax highlighting in citation snippets
- Chroma is local-only storage for MVP speed
- Answers depend on retrieved context quality and the selected OpenAI model

## Future Improvements

- Background indexing jobs with progress status
- Persistent repository metadata database
- Incremental re-indexing by commit SHA
- Retrieval quality tuning and hybrid keyword/vector search
- Source file viewer with syntax highlighting
- Streaming answers
- User accounts and private repository support
- Deployment guide and hosted demo
