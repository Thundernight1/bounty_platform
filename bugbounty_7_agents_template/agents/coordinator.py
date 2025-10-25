import asyncio, yaml, os, json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from agents.utils import save_text

console = Console()

async def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--program", required=True)
    ap.add_argument("--auto-approve", action="store_true", help="Final raporu otomatik onayla (demo)")
    args = ap.parse_args()

    with open(args.program, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Import agents as modules
    from agents import envanter, tech_fp, scan_web, content, auth_checks, prompt_ai, reporter

    os.makedirs("outputs", exist_ok=True)

    tasks = [
        envanter.run(cfg),
        tech_fp.run(cfg),
        scan_web.run(cfg),
        content.run(cfg),
        auth_checks.run(cfg),
        prompt_ai.run(cfg),
    ]

    console.rule("[bold green]7 Agents Running")
    await asyncio.gather(*tasks)

    # Pre-report and approval checkpoint
    await reporter.pre_report(cfg)
    if not args.auto_approve:
        console.print("[yellow]outputs/REVIEW.md generated. Review and create 'outputs/APPROVED.txt' to approve.")
        # Wait for user approval
        for _ in range(60):  # ~60 seconds wait (demo)
            if os.path.exists("outputs/APPROVED.txt"):
                break
            await asyncio.sleep(1)

    await reporter.finalize(cfg, auto=args.auto_approve)
    console.rule("[bold green]Done")

if __name__ == "__main__":
    asyncio.run(main())
