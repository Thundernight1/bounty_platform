import os, json, datetime
from agents.utils import save_text
from rich.console import Console

console = Console()

def load_json(path):
    try:
        with open(path,"r") as f:
            return json.load(f)
    except:
        return []

async def pre_report(cfg: dict):
    nuclei = load_json("outputs/nuclei.json")
    auth = load_json("outputs/auth_checks.json")
    prompt_ai = load_json("outputs/prompt_ai.json")
    lines = ["# PRE-REVIEW (Pre-Report)",
             f"Program: {cfg.get('program_name')}",
             f"Date: {datetime.datetime.utcnow().isoformat()}Z",
             "",
             "## Summary",
             f"- nuclei findings: {len(nuclei)}",
             f"- auth/passive findings: {len(auth)}",
             f"- prompt_ai attempts: {len(prompt_ai)}",
             "",
             "## Review Note",
             "Review findings and create `outputs/APPROVED.txt` to approve."]
    save_text("outputs/REVIEW.md", "\n".join(lines))

async def finalize(cfg: dict, auto: bool=False):
    nuclei = load_json("outputs/nuclei.json")
    auth = load_json("outputs/auth_checks.json")
    prompt_ai = load_json("outputs/prompt_ai.json")

    lines = ["# Final Report",
             f"Program: {cfg.get('program_name')}",
             f"Date: {datetime.datetime.utcnow().isoformat()}Z",
             "",
             "## Findings Summary",
             f"- nuclei: {len(nuclei)}",
             f"- passive auth: {len(auth)}",
             f"- prompt_ai: {len(prompt_ai)}",
             "",
             "## Details",
             "### nuclei",
             "```json",
             json.dumps(nuclei, ensure_ascii=False, indent=2),
             "```",
             "### auth/passive",
             "```json",
             json.dumps(auth, ensure_ascii=False, indent=2),
             "```",
             "### prompt_ai",
             "```json",
             json.dumps(prompt_ai, ensure_ascii=False, indent=2),
             "```",
             ]
    save_text("outputs/report.md", "\n".join(lines))
    save_text("outputs/report.json", json.dumps({
        "program": cfg.get("program_name"),
        "summary": {"nuclei": len(nuclei), "auth": len(auth), "prompt_ai": len(prompt_ai)},
        "nuclei": nuclei, "auth": auth, "prompt_ai": prompt_ai
    }, ensure_ascii=False, indent=2))
    console.log("[green]Report generated -> outputs/report.md / outputs/report.json")
