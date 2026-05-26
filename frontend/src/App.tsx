import { FormEvent, useMemo, useState } from "react";

import { askRepository, buildRepoId, indexRepository } from "./api";
import "./App.css";
import type { AskResponse, RepositoryIndexResponse } from "./types";

const SAMPLE_REPOS = [
  {
    name: "octocat/Hello-World",
    url: "https://github.com/octocat/Hello-World",
    questions: ["What does this repository contain?", "What files are available?"],
  },
  {
    name: "psf/requests",
    url: "https://github.com/psf/requests",
    questions: ["How is the package organized?", "Where is the public API defined?"],
  },
  {
    name: "pallets/flask",
    url: "https://github.com/pallets/flask",
    questions: ["How does routing work?", "Where is the application object implemented?"],
  },
];

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repoState, setRepoState] = useState<RepositoryIndexResponse | null>(null);
  const [repoError, setRepoError] = useState("");
  const [isIndexing, setIsIndexing] = useState(false);
  const [question, setQuestion] = useState("");
  const [answers, setAnswers] = useState<AskResponse[]>([]);
  const [askError, setAskError] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  const repoId = useMemo(() => buildRepoId(repoUrl), [repoUrl]);
  const canAsk = Boolean(repoState && !isIndexing);

  async function handleIndexSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRepoError("");
    setAnswers([]);
    setAskError("");

    if (!repoUrl.trim()) {
      setRepoError("Enter a public GitHub repository URL.");
      return;
    }

    setIsIndexing(true);
    setRepoState(null);
    try {
      const response = await indexRepository(repoId, repoUrl.trim());
      setRepoState(response);
    } catch (error) {
      setRepoError(error instanceof Error ? error.message : "Failed to index repository.");
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleAskSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAskError("");

    if (!repoState) {
      setAskError("Index a repository before asking questions.");
      return;
    }
    if (!question.trim()) {
      setAskError("Enter a question.");
      return;
    }

    setIsAsking(true);
    try {
      const response = await askRepository(repoState.repo_id, question.trim(), 5);
      setAnswers((currentAnswers) => [...currentAnswers, response]);
      setQuestion("");
    } catch (error) {
      setAskError(error instanceof Error ? error.message : "Failed to answer question.");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-labelledby="page-title">
        <header className="page-header">
          <p className="eyebrow">Public GitHub repo onboarding</p>
          <h1 id="page-title">Ask codebase questions with source citations.</h1>
          <p className="summary">
            Index a public repository, ask setup or architecture questions, and inspect the exact
            files and lines used to answer.
          </p>
        </header>

        <section className="panel" aria-labelledby="repo-heading">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Step 1</p>
              <h2 id="repo-heading">Index repository</h2>
            </div>
            {repoState ? <span className="status-pill success">Indexed</span> : null}
          </div>

          <form className="repo-form" onSubmit={handleIndexSubmit}>
            <label className="sr-only" htmlFor="repo-url">
              GitHub repository URL
            </label>
            <input
              id="repo-url"
              name="repo-url"
              type="url"
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              placeholder="https://github.com/owner/repository"
              aria-label="GitHub repository URL"
              disabled={isIndexing}
            />
            <button type="submit" disabled={isIndexing}>
              {isIndexing ? "Indexing..." : "Index repo"}
            </button>
          </form>

          {repoUrl ? <p className="status-note">Repo ID: {repoId || "waiting for URL"}</p> : null}
          {repoState ? (
            <div className="result-banner">
              <strong>{repoState.repo_id}</strong>
              <span>{repoState.chunk_count} chunks indexed</span>
            </div>
          ) : null}
          {repoError ? <p className="error-message">{repoError}</p> : null}

          <div className="samples">
            <h3>Sample repos</h3>
            <div className="sample-grid">
              {SAMPLE_REPOS.map((sample) => (
                <article className="sample-card" key={sample.url}>
                  <button type="button" onClick={() => setRepoUrl(sample.url)} disabled={isIndexing}>
                    {sample.name}
                  </button>
                  <ul>
                    {sample.questions.map((sampleQuestion) => (
                      <li key={sampleQuestion}>{sampleQuestion}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="panel" aria-labelledby="chat-heading">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Step 2</p>
              <h2 id="chat-heading">Ask a question</h2>
            </div>
            {answers.length > 0 ? <span className="status-pill">{answers.length} answered</span> : null}
          </div>

          <form className="chat-form" onSubmit={handleAskSubmit}>
            <label className="sr-only" htmlFor="question">
              Question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="How is this project structured?"
              disabled={!canAsk || isAsking}
              rows={4}
            />
            <button type="submit" disabled={!canAsk || isAsking}>
              {isAsking ? "Asking..." : "Ask"}
            </button>
          </form>

          {!canAsk ? <p className="status-note">Index a repository to enable questions.</p> : null}
          {askError ? <p className="error-message">{askError}</p> : null}

          {answers.length > 0 ? (
            <div className="answer-history" aria-label="Answer history">
              {answers.map((answerItem, answerIndex) => (
                <section className="answer-block" key={`${answerItem.question}-${answerIndex}`}>
                  <div className="question-row">
                    <div className="question-bubble">
                      <span>You</span>
                      <p>{answerItem.question}</p>
                    </div>
                  </div>
                  <div className="answer-heading">
                    <h3>Answer</h3>
                    <span className={`status-pill ${answerItem.confidence}`}>{answerItem.confidence}</span>
                  </div>
                  <p>{answerItem.answer}</p>

                  <div className="citations">
                    <h3>Citations</h3>
                    {answerItem.citations.map((citation) => (
                      <article className="citation-card" key={`${answerIndex}-${citation.chunk_id}`}>
                        <div className="citation-header">
                          <span>
                            {citation.file_path}:{citation.start_line}-{citation.end_line}
                          </span>
                          <a href={citation.github_url} target="_blank" rel="noreferrer">
                            Open source
                          </a>
                        </div>
                        <pre>{citation.snippet}</pre>
                      </article>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : null}
        </section>
      </section>
    </main>
  );
}

export default App;
