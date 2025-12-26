## 2024-05-23 - [Blocking Calls in Async Functions]
**Learning:** Mixing synchronous I/O (like `requests`) in async FastAPI routes or background tasks blocks the entire event loop, killing concurrency. Using `httpx` or `asyncio.to_thread` is essential.
**Action:** Always check for blocking I/O in async paths and convert to async alternatives or offload to a thread.
