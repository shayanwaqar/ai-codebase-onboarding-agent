import pytest

from app.models import CodeChunk, RetrievedChunk
from app.qa import (
    CitationMetadataError,
    RepositoryNotIndexedError,
    answer_repo_question,
    build_citation,
    build_github_permalink,
    build_user_prompt,
    estimate_confidence,
)


COMMIT_SHA = "a" * 40


class FakeEmbeddingService:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 2.0] for _ in texts]


class FakeVectorStore:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self.results = results
        self.query_args = None

    def query(self, repo_id: str, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        self.query_args = (repo_id, query_embedding, top_k)
        return self.results


class FakeChatService:
    def __init__(self, answer: str = "This repo prints Hello World [1].") -> None:
        self.answer_text = answer
        self.system_prompt = ""
        self.user_prompt = ""

    def answer(self, system_prompt: str, user_prompt: str) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return self.answer_text


def make_chunk() -> CodeChunk:
    return CodeChunk(
        chunk_id="chunk-1",
        repo_id="repo-1",
        repo_url="https://github.com/octocat/Hello-World",
        repo_owner="octocat",
        repo_name="Hello-World",
        commit_sha=COMMIT_SHA,
        file_path="README.md",
        language="Markdown",
        extension=".md",
        start_line=1,
        end_line=2,
        content="Hello World!\nSecond line\n",
        char_count=25,
    )


def make_result(score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(chunk=make_chunk(), score=score)


def test_answer_repo_question_uses_retrieved_chunks_and_returns_citations() -> None:
    vector_store = FakeVectorStore(results=[make_result()])
    chat_service = FakeChatService()

    response = answer_repo_question(
        repo_id="repo-1",
        question="What does this repo do?",
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
        chat_service=chat_service,
        top_k=3,
    )

    assert response.repo_id == "repo-1"
    assert response.question == "What does this repo do?"
    assert response.answer == "This repo prints Hello World [1]."
    assert response.confidence == "medium"
    assert vector_store.query_args == ("repo-1", [1.0, 2.0], 3)
    assert "[1] README.md:1-2" in chat_service.user_prompt
    assert "Hello World!" in chat_service.user_prompt
    assert response.citations[0].chunk_id == "chunk-1"
    assert response.citations[0].github_url.endswith(f"/blob/{COMMIT_SHA}/README.md#L1-L2")


def test_answer_repo_question_raises_when_repo_has_no_indexed_chunks() -> None:
    with pytest.raises(RepositoryNotIndexedError):
        answer_repo_question(
            repo_id="missing-repo",
            question="What does this repo do?",
            embedding_service=FakeEmbeddingService(),
            vector_store=FakeVectorStore(results=[]),
            chat_service=FakeChatService(),
        )


def test_build_github_permalink_escapes_paths() -> None:
    chunk = make_chunk().model_copy(update={"file_path": "docs/setup guide.md"})

    assert build_github_permalink(chunk).endswith(f"/docs/setup%20guide.md#L1-L2")


def test_build_citation_requires_github_metadata() -> None:
    chunk = make_chunk().model_copy(update={"repo_owner": None})

    with pytest.raises(CitationMetadataError):
        build_citation(chunk)


def test_build_user_prompt_is_inspectable_and_citation_numbered() -> None:
    prompt = build_user_prompt("What does it do?", [make_result()])

    assert "Question:" in prompt
    assert "Retrieved context:" in prompt
    assert "[1] README.md:1-2" in prompt
    assert "Answer with citations" in prompt


def test_estimate_confidence() -> None:
    assert estimate_confidence([make_result(0.8), make_result(0.7)]) == "high"
    assert estimate_confidence([make_result(0.5)]) == "medium"
    assert estimate_confidence([make_result(0.2)]) == "low"
