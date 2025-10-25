import os, json
from agents.utils import run_cmd, save_text
from rich.console import Console

console = Console()

async def run(cfg: dict):
    # Use httpx + nuclei if available, otherwise skip
    out_urls = []
    # httpx
    if os.system("which httpx > /dev/null 2>&1") == 0 and os.path.exists("outputs/subdomains.txt"):
        rc, out, err = await run_cmd("httpx -silent -l outputs/subdomains.txt -ports 80,443,8080,8443")
        if rc == 0:
            out_urls = [l.strip() for l in out.splitlines() if l.strip()]
            save_text("outputs/urls.txt", "\n".join(out_urls))
            console.log(f"[green]scan_web: httpx {len(out_urls)} URLs generated -> outputs/urls.txt")

    nuclei_findings = []
    if cfg.get("allowed_tests",{}).get("nuclei_signatures", True) and os.system("which nuclei > /dev/null 2>&1") == 0 and os.path.exists("outputs/urls.txt"):
        rc, out, err = await run_cmd("nuclei -silent -l outputs/urls.txt -json")
        if rc == 0:
            # nuclei JSON Satır bazlı
            for line in out.splitlines():
                try:
                    nuclei_findings.append(json.loads(line))
                except: pass
            save_text("outputs/nuclei.json", json.dumps(nuclei_findings, ensure_ascii=False, indent=2))
            console.log(f"[green]scan_web: nuclei bulguları -> outputs/nuclei.json ({len(nuclei_findings)})")
    else:
        save_text("outputs/nuclei.json", "[]")
