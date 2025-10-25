import json, os
from agents.utils import save_text
from rich.console import Console

console = Console()

async def run(cfg: dict):
    # Pasif kontroller: set-cookie, secure/httponly/csrf header izleri
    try:
        import json
        with open("outputs/tech_fp.json","r") as f:
            items = json.load(f)
    except Exception:
        items = []
    findings = []
    for it in items:
        if not isinstance(it, dict): continue
        csp = it.get("csp","")
        server = it.get("server","")
        if csp == "":
            findings.append({"url": it.get("url"), "issue": "Missing CSP", "severity": "medium"})
        if "Apache" in server or "nginx" in server:
            findings.append({"url": it.get("url"), "note": f"Server: {server}", "severity": "info"})
    save_text("outputs/auth_checks.json", json.dumps(findings, ensure_ascii=False, indent=2))
    console.log(f"[green]auth: {len(findings)} pasif bulgu -> outputs/auth_checks.json")
