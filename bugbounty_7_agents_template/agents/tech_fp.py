import asyncio, aiohttp, async_timeout
from agents.utils import save_text
from rich.console import Console

console = Console()

async def fetch_head(session, url):
    try:
        async with async_timeout.timeout(10):
            async with session.get(url, allow_redirects=True) as r:
                return {
                    "url": str(r.url),
                    "status": r.status,
                    "server": r.headers.get("Server",""),
                    "powered_by": r.headers.get("X-Powered-By",""),
                    "via": r.headers.get("Via",""),
                    "csp": r.headers.get("Content-Security-Policy",""),
                }
    except Exception as e:
        return {"url": url, "error": str(e)}

async def run(cfg: dict):
    subs = []
    try:
        with open("outputs/subdomains.txt","r") as f:
            subs = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        subs = []

    urls = [f"https://{h}" for h in subs] + [f"http://{h}" for h in subs]
    results = []
    connector = aiohttp.TCPConnector(ssl=False, limit=cfg.get("rate_limit",{}).get("max_concurrency",5))
    async with aiohttp.ClientSession(connector=connector) as session:
        for u in urls[:100]:  # güvenli limit
            res = await fetch_head(session, u)
            results.append(res)
    import json, os
    os.makedirs("outputs", exist_ok=True)
    save_text("outputs/tech_fp.json", json.dumps(results, ensure_ascii=False, indent=2))
    console.log(f"[green]tech_fp: {len(results)} URL için header bilgisi alındı -> outputs/tech_fp.json")
