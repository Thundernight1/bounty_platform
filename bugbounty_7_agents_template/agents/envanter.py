import asyncio, os
from agents.utils import run_cmd, save_text
from rich.console import Console

console = Console()

async def run(cfg: dict):
    targets = [t["domain"] for t in cfg.get("targets", []) if t.get("in_scope")]
    lines = []
    for d in targets:
        lines.append(d)

    # Run subfinder if available
    if os.system("which subfinder > /dev/null 2>&1") == 0:
        for d in targets:
            rc, out, err = await run_cmd(f"subfinder -silent -d {d}")
            if rc == 0:
                for l in out.splitlines():
                    if l.strip(): lines.append(l.strip())
    # Unique subdomains
    uniq = sorted(set(lines))
    save_text("outputs/subdomains.txt", "\n".join(uniq))
    console.log(f"[green]inventory: {len(uniq)} domains/subdomains written -> outputs/subdomains.txt")
