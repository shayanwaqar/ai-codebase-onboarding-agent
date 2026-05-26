import "./App.css";

function App() {
  return (
    <main className="app-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Public GitHub repo onboarding</p>
        <h1 id="page-title">Ask architecture questions with source citations.</h1>
        <p className="summary">
          Enter a public repository URL to index code, docs, and configuration, then ask setup,
          architecture, and implementation questions grounded in file and line references.
        </p>

        <form className="repo-form" onSubmit={(event) => event.preventDefault()}>
          <label className="sr-only" htmlFor="repo-url">
            GitHub repository URL
          </label>
          <input
            id="repo-url"
            name="repo-url"
            type="url"
            placeholder="https://github.com/owner/repository"
            aria-label="GitHub repository URL"
          />
          <button type="button" disabled>
            Index repo
          </button>
        </form>

        <p className="status-note">Milestone 1 scaffold: indexing and AI answers come next.</p>
      </section>
    </main>
  );
}

export default App;
