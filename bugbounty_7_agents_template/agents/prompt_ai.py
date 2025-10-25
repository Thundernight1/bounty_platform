import os, yaml, json, aiohttp, asyncio, async_timeout
from agents.utils import save_text
from rich.console import Console

console = Console()

async def attack_endpoint(session, ep: dict, payload: str):
    url = ep.get("url")
    method = ep.get("method","POST").upper()
    headers = {}
    if ep.get("auth_header"):
        headers["Authorization"] = ep["auth_header"]
    data = ep.get("body_template","{payload}").replace("{payload}", payload)
    try:
        async with async_timeout.timeout(12):
            if method == "GET":
                async with session.get(url, headers=headers) as r:
                    txt = await r.text()
                    return {"url": url, "status": r.status, "len": len(txt)}
            else:
                async with session.post(url, data=data, headers=headers) as r:
                    txt = await r.text()
                    return {"url": url, "status": r.status, "len": len(txt)}
    except Exception as e:
        return {"url": url, "error": str(e)}

async def run(cfg: dict):
    if not cfg.get("allowed_tests",{}).get("prompt_injection_checks", True):
        return
    # payloadlar
    payloads = []
    if os.path.exists("data/prompt_payloads.txt"):
        with open("data/prompt_payloads.txt","r", encoding="utf-8") as f:
            payloads = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    endpoints = cfg.get("llm_endpoints", [])
    results = []
    connector = aiohttp.TCPConnector(ssl=False, limit=cfg.get("rate_limit",{}).get("max_concurrency",5))
    async with aiohttp.ClientSession(connector=connector) as session:
        for ep in endpoints:
            for p in payloads[:5]:
                res = await attack_endpoint(session, ep, p)
                res["payload"] = p[:50]
                results.append(res)
    save_text("outputs/prompt_ai.json", json.dumps(results, ensure_ascii=False, indent=2))
    console.log(f"[green]prompt_ai: {len(results)} deneme -> outputs/prompt_ai.json")
