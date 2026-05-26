from app.indexing import index_ingested_repository, retrieve_relevant_chunks
from app.models import FileMetadata, RepositoryIngestResponse, RetrievedChunk


COMMIT_SHA = "a" * 40


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.inputs: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.inputs.append(texts)
        return [[float(len(text)), float(index)] for index, text in enumerate(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.replace_calls: list[tuple[str, int, int]] = []
        self.chunks = []
        self.embeddings = []
        self.query_calls: list[tuple[str, list[float], int]] = []

    def replace_repo_chunks(self, repo_id, chunks, embeddings) -> None:
        self.replace_calls.append((repo_id, len(chunks), len(embeddings)))
        self.chunks = chunks
        self.embeddings = embeddings

    def query(self, repo_id, query_embedding, top_k):
        self.query_calls.append((repo_id, query_embedding, top_k))
        return [RetrievedChunk(chunk=self.chunks[0], score=0.9)] if self.chunks else []


def make_ingested_repo() -> RepositoryIngestResponse:
    return RepositoryIngestResponse(
        repository_url="https://github.com/example/repo",
        owner="example",
        name="repo",
        commit_sha=COMMIT_SHA,
        file_count=1,
        files=[
            FileMetadata(
                file_path="src/app.py",
                extension=".py",
                language="Python",
                content="line 1\nline 2\n",
                line_count=2,
            )
        ],
    )


def test_index_ingested_repository_embeds_and_replaces_chunks() -> None:
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    response = index_ingested_repository(
        repo_id="repo-1",
        ingested_repo=make_ingested_repo(),
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    assert response.repo_id == "repo-1"
    assert response.status == "indexed"
    assert response.chunk_count == 1
    assert embedding_service.inputs == [["line 1\nline 2\n"]]
    assert vector_store.replace_calls == [("repo-1", 1, 1)]
    assert vector_store.chunks[0].repo_owner == "example"
    assert vector_store.chunks[0].repo_name == "repo"
    assert vector_store.chunks[0].commit_sha == COMMIT_SHA
    assert vector_store.chunks[0].file_path == "src/app.py"
    assert vector_store.embeddings == [[14.0, 0.0]]


def test_retrieve_relevant_chunks_embeds_query_and_queries_store() -> None:
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()
    index_ingested_repository("repo-1", make_ingested_repo(), embedding_service, vector_store)

    results = retrieve_relevant_chunks(
        repo_id="repo-1",
        query="How does setup work?",
        embedding_service=embedding_service,
        vector_store=vector_store,
        top_k=3,
    )

    assert embedding_service.inputs[-1] == ["How does setup work?"]
    assert vector_store.query_calls == [("repo-1", [20.0, 0.0], 3)]
    assert results[0].chunk.file_path == "src/app.py"
    assert results[0].score == 0.9
