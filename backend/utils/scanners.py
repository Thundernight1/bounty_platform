"""
Utility functions for running security scans.

Tries real tools if present (OWASP ZAP, Mythril, nuclei, osv-scanner),
otherwise returns mock/heuristic results to keep the flow usable.
"""

from __future__ import annotations

import json
import os
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


async def _run_command(args: List[str]) -> Dict[str, Any]:
    """
    Helper to run a subprocess asynchronously.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "returncode": process.returncode
        }
    except Exception as exc:
        raise exc


async def run_zap_scan(url: str) -> Dict[str, Any]:
    zap_cli_path = shutil.which("zap-cli")
    if zap_cli_path:
        try:
            completed = await _run_command([zap_cli_path, "quick-scan", url])
            return {
                "tool": "owasp_zap",
                "summary": "ZAP quick scan completed",
                "stdout": completed["stdout"],
                "stderr": completed["stderr"],
                "returncode": completed["returncode"],
            }
        except Exception as exc:
            return {"tool": "owasp_zap", "summary": f"ZAP failed: {exc}", "vulnerabilities": []}
    else:
        # Return empty results if ZAP not installed
        return {
            "tool": "owasp_zap",
            "summary": "OWASP ZAP not installed - skipping web scan",
            "vulnerabilities": [],
            "warning": "Install ZAP for real vulnerability scanning: apt-get install zaproxy"
        }


async def run_nuclei_scan(url: str) -> Dict[str, Any]:
    nuclei = shutil.which("nuclei")
    if nuclei:
        try:
            completed = await _run_command([nuclei, "-u", url, "-json", "-silent"])
            findings = []
            for line in completed["stdout"].splitlines():
                try:
                    findings.append(json.loads(line))
                except Exception:
                    pass
            return {
                "tool": "nuclei",
                "summary": f"nuclei completed, {len(findings)} findings",
                "findings": findings,
                "returncode": completed["returncode"],
            }
        except Exception as exc:
            return {"tool": "nuclei", "summary": f"nuclei failed: {exc}", "findings": []}
    else:
        # Return empty results if nuclei not installed
        return {
            "tool": "nuclei",
            "summary": "nuclei not installed - skipping CVE scan",
            "findings": [],
            "warning": "Install nuclei for CVE scanning: go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
        }


async def run_mythril_scan(source_code: str) -> Dict[str, Any]:
    mythril_path = shutil.which("mythril")
    if mythril_path:
        # Mythril requires a file, so we still need sync file IO for temp file creation,
        # but it's negligible compared to the scan time.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as tmp:
            tmp.write(source_code)
            tmp.flush()
            tmp_path = tmp.name
        try:
            completed = await _run_command([mythril_path, "-x", tmp_path, "--no-color"])
            return {
                "tool": "mythril",
                "summary": "Mythril analysis completed",
                "stdout": completed["stdout"],
                "stderr": completed["stderr"],
                "returncode": completed["returncode"],
            }
        except Exception as exc:
            return {"tool": "mythril", "summary": f"Mythril failed: {exc}", "issues": []}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    else:
        # Basic heuristic analysis
        issues = []
        if "call.value" in source_code:
            issues.append(
                {
                    "id": "PATTERN_DETECTED",
                    "description": "call.value pattern detected - review for reentrancy (install Mythril for proper analysis)",
                    "severity": "info",
                }
            )
        return {
            "tool": "mythril",
            "summary": "Mythril not installed - basic heuristic only",
            "issues": issues,
            "warning": "Install Mythril for real smart contract analysis: pip install mythril"
        }


async def run_sca_scan(path_or_repo: str) -> Dict[str, Any]:
    """
    Software Composition Analysis.
    """
    osv = shutil.which("osv-scanner")
    if osv:
        try:
            completed = await _run_command([osv, "--recursive", path_or_repo, "--json"])
            data = {}
            try:
                data = json.loads(completed["stdout"] or "{}")
            except Exception:
                pass
            return {
                "tool": "osv-scanner",
                "summary": "OSV scan completed",
                "results": data,
                "returncode": completed["returncode"],
            }
        except Exception as exc:
            return {"tool": "osv-scanner", "summary": f"OSV failed: {exc}", "results": {}}

    # Fallback: just list manifests found
    manifests = ["requirements.txt", "package.json", "pyproject.toml", "Gemfile", "pom.xml"]
    found = [m for m in manifests if (Path(path_or_repo) / m).exists()]
    return {
        "tool": "osv-scanner",
        "summary": "osv-scanner not installed - skipping SCA",
        "manifests_found": found,
        "vulnerabilities": [],
        "warning": "Install osv-scanner for dependency vulnerability scanning: go install github.com/google/osv-scanner/cmd/osv-scanner@latest"
    }
