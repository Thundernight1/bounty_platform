## 2024-05-23 - [Shared httpx.AsyncClient Optimization]
**Learning:** Reusing a single `httpx.AsyncClient` throughout the application lifespan significantly reduces overhead compared to creating a new client for every request.
**Action:** Use `app.state.http_client` initialized in the `lifespan` event handler for all internal HTTP requests. Always include a fallback for contexts where the app state might not be fully initialized (like unit tests).
