import asyncio, subprocess, sys, os, json, shlex
from typing import List, Tuple
from rich.console import Console

console = Console()

def which(cmd: str) -> str | None:
    from shutil import which as w
    return w(cmd)

async def run_cmd(cmd: str, cwd: str | None = None, timeout: int = 900) -> Tuple[int, str, str]:
    console.log(f"[cyan]$ {cmd}")
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return (999, "", f"Timeout after {timeout}s")
    return (proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore"))

def save_text(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def load_lines(path: str) -> List[str]:
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]
