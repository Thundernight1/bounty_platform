## 2024-05-23 - [Shared httpx.AsyncClient Optimization]
**Learning:** Reusing a single `httpx.AsyncClient` throughout the application lifespan significantly reduces overhead compared to creating a new client for every request.
**Action:** Use `app.state.http_client` initialized in the `lifespan` event handler for all internal HTTP requests. Always include a fallback for contexts where the app state might not be fully initialized (like unit tests).

## 2024-05-24 - [Code Review Verification]
**Learning:** Code reviews can provide incorrect feedback. A review flagged a missing `httpx` dependency, but it was already present in `requirements.txt`. This highlights the importance of always verifying review feedback against the source of truth—the codebase itself—before acting on it.
**Action:** When receiving feedback, especially about environmental or dependency issues, always cross-reference it with the relevant configuration files (`requirements.txt`, `package.json`, etc.) before making changes.
