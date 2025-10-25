import os
from agents.utils import run_cmd, save_text
from rich.console import Console

console = Console()

async def run(cfg: dict):
    # Simple content discovery with ffuf if available
    if cfg.get("allowed_tests",{}).get("content_discovery", True) and os.system("which ffuf > /dev/null 2>&1") == 0 and os.path.exists("outputs/urls.txt"):
        rc, out, err = await run_cmd('ffuf -u FUZZ -w outputs/urls.txt -mc 200,204,301,302 -of json -o outputs/ffuf.json')
        if rc == 0:
            console.log("[green]content: ffuf executed -> outputs/ffuf.json")
    else:
        # fallback: robots.txt dene
        urls = []
        if os.path.exists("outputs/urls.txt"):
            with open("outputs/urls.txt","r") as f:
                urls = [l.strip().rstrip("/") + "/robots.txt" for l in f if l.strip()]
        save_text("outputs/content_notes.txt", "\n".join(urls[:50]))
        console.log("[yellow]content: ffuf not found, robots.txt list created -> outputs/content_notes.txt")
