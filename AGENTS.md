# AGENTS.md

## Project

This is an AI Codebase Onboarding Agent. It indexes GitHub repositories and answers architecture, setup, and implementation questions with source-linked citations.

## Tech Stack

- Frontend: React + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL + pgvector
- AI: OpenAI API for embeddings and chat
- Infra: Docker Compose

## Engineering Rules

- Make small, reviewable changes
- Prefer simple, readable code over clever abstractions
- Add or update tests for backend logic
- Do not add new dependencies without explaining why
- Keep API responses typed and documented
- Never commit secrets or API keys
- Use environment variables for configuration
- Include source file citations in AI answers whenever possible

## Commands

- Backend tests: `pytest`
- Frontend lint: `npm run lint`
- Frontend dev: `npm run dev`
- Full local stack: `docker compose up --build`

## Output Expectations

When implementing a feature:

1. Explain the plan
2. List files changed
3. Run or describe tests
4. Mention known limitations
