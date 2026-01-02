# BOLT'S JOURNAL - CRITICAL LEARNINGS ONLY
This journal is for capturing critical, non-routine performance learnings specific to this codebase.

Format:
## YYYY-MM-DD - [Title]
**Learning:** [Insight]
**Action:** [How to apply next time]

## 2024-08-14 - Use Shared httpx.AsyncClient for FastAPI Performance
**Learning:** Creating a new `httpx.AsyncClient` for every request is a significant performance anti-pattern. The correct and most performant approach is to use a single, shared client for the application's entire lifespan. This allows `httpx` to leverage connection pooling, which reuses TCP connections and reduces the overhead of establishing new ones for every request.
**Action:** For all future FastAPI applications, I will implement a shared `httpx.AsyncClient` instance managed by the `lifespan` context manager. The client should be stored on the `app.state` object for easy access throughout the application.
