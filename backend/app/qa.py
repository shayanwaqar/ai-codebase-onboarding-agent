from typing import Protocol
from urllib.parse import quote

from app.chat import OpenAIChatService
from app.embeddings import OpenAIEmbeddingService
from app.indexing import EmbeddingService, VectorStore, retrieve_relevant_chunks
from app.models import AskResponse, CodeChunk, RetrievedChunk, SourceCitation
from app.vector_store import ChromaVectorStore


class QuestionAnsweringError(RuntimeError):
    pass


class RepositoryNotIndexedError(QuestionAnsweringError):
    pass


class CitationMetadataError(QuestionAnsweringError):
    pass


class ChatService(Protocol):
    def answer(self, system_prompt: str, user_prompt: str) -> str:
        pass


SYSTEM_PROMPT = """You answer questions about a GitHub repository using only retrieved source context.

Rules:
- Use only the provided context snippets.
- Cite supporting snippets inline using bracketed numbers like [1] or [2].
- If the context is insufficient, say: "The indexed repository context does not contain enough information to answer that."
- Do not invent files, line numbers, APIs, behavior, setup steps, or citations.
- Keep the answer concise and practical.
"""


def answer_repo_question(
    repo_id: str,
    question: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    chat_service: ChatService,
    top_k: int = 5,
) -> AskResponse:
    retrieved_chunks = retrieve_relevant_chunks(
        repo_id=repo_id,
        query=question,
        embedding_service=embedding_service,
        vector_store=vector_store,
        top_k=top_k,
    )
    if not retrieved_chunks:
        raise RepositoryNotIndexedError(f"No indexed chunks found for repo_id '{repo_id}'.")

    citations = [build_citation(result.chunk) for result in retrieved_chunks]
    user_prompt = build_user_prompt(question=question, retrieved_chunks=retrieved_chunks)
    answer = chat_service.answer(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    return AskResponse(
        repo_id=repo_id,
        question=question,
        answer=answer,
        citations=citations,
        confidence=estimate_confidence(retrieved_chunks),
    )


def answer_repo_question_with_defaults(repo_id: str, question: str, top_k: int = 5) -> AskResponse:
    return answer_repo_question(
        repo_id=repo_id,
        question=question,
        embedding_service=OpenAIEmbeddingService(),
        vector_store=ChromaVectorStore(),
        chat_service=OpenAIChatService(),
        top_k=top_k,
    )


def build_user_prompt(question: str, retrieved_chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for index, result in enumerate(retrieved_chunks, start=1):
        chunk = result.chunk
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] {chunk.file_path}:{chunk.start_line}-{chunk.end_line}",
                    f"Repository: {chunk.repo_owner}/{chunk.repo_name}@{chunk.commit_sha}",
                    "Content:",
                    chunk.content,
                ]
            )
        )

    return "\n\n".join(
        [
            "Question:",
            question,
            "",
            "Retrieved context:",
            "\n\n---\n\n".join(context_blocks),
            "",
            "Answer with citations from the retrieved context.",
        ]
    )


def build_citation(chunk: CodeChunk) -> SourceCitation:
    if not chunk.repo_owner or not chunk.repo_name or not chunk.commit_sha:
        raise CitationMetadataError(f"Chunk '{chunk.chunk_id}' is missing GitHub citation metadata.")

    return SourceCitation(
        chunk_id=chunk.chunk_id,
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        repo_owner=chunk.repo_owner,
        repo_name=chunk.repo_name,
        commit_sha=chunk.commit_sha,
        github_url=build_github_permalink(chunk),
        snippet=chunk.content,
    )


def build_github_permalink(chunk: CodeChunk) -> str:
    if not chunk.repo_owner or not chunk.repo_name or not chunk.commit_sha:
        raise CitationMetadataError(f"Chunk '{chunk.chunk_id}' is missing GitHub citation metadata.")

    escaped_path = quote(chunk.file_path, safe="/")
    return (
        f"https://github.com/{chunk.repo_owner}/{chunk.repo_name}/blob/"
        f"{chunk.commit_sha}/{escaped_path}#L{chunk.start_line}-L{chunk.end_line}"
    )


def estimate_confidence(retrieved_chunks: list[RetrievedChunk]) -> str:
    best_score = max((result.score for result in retrieved_chunks), default=0.0)
    if best_score >= 0.75 and len(retrieved_chunks) >= 2:
        return "high"
    if best_score >= 0.45:
        return "medium"
    return "low"
