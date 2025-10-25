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
    lines = ["# PRE‑REVIEW (Ön Rapor)",
             f"Program: {cfg.get('program_name')}",
             f"Tarih: {datetime.datetime.utcnow().isoformat()}Z",
             "",
             "## Özet",
             f"- nuclei bulguları: {len(nuclei)}",
             f"- auth/pasif bulgular: {len(auth)}",
             f"- prompt_ai denemeleri: {len(prompt_ai)}",
             "",
             "## İnceleme Notu",
             "Bu aşamada doğruluğu kontrol et ve `outputs/APPROVED.txt` oluştur."]
    save_text("outputs/REVIEW.md", "\n".join(lines))

async def finalize(cfg: dict, auto: bool=False):
    nuclei = load_json("outputs/nuclei.json")
    auth = load_json("outputs/auth_checks.json")
    prompt_ai = load_json("outputs/prompt_ai.json")

    lines = ["# Nihai Rapor",
             f"Program: {cfg.get('program_name')}",
             f"Tarih: {datetime.datetime.utcnow().isoformat()}Z",
             "",
             "## Bulgular Özeti",
             f"- nuclei: {len(nuclei)}",
             f"- pasif auth: {len(auth)}",
             f"- prompt_ai: {len(prompt_ai)}",
             "",
             "## Ayrıntılar",
             "### nuclei",
             "```json",
             json.dumps(nuclei, ensure_ascii=False, indent=2),
             "```",
             "### auth/pasif",
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
    console.log("[green]Rapor üretildi -> outputs/report.md / outputs/report.json")
