"""
Utility functions for running security scans.

Tries real tools if present (OWASP ZAP, Mythril, nuclei, osv-scanner),
otherwise returns mock/heuristic results to keep the flow usable.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any


def run_zap_scan(url: str) -> Dict[str, Any]:
    zap_cli_path = shutil.which("zap-cli")
    if zap_cli_path:
        try:
            completed = subprocess.run(
                [zap_cli_path, "quick-scan", url],
                check=False,
                capture_output=True,
                text=True,
            )
            return {
                "tool": "owasp_zap",
                "summary": "ZAP quick scan completed",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
            }
        except Exception as exc:
            return {"tool": "owasp_zap", "summary": f"ZAP failed: {exc}", "vulnerabilities": []}
    else:
        return {
            "tool": "owasp_zap",
            "summary": "OWASP ZAP not installed – mock findings",
            "vulnerabilities": [
                {
                    "id": "XSS001",
                    "description": "Reflected XSS suspected in query param",
                    "severity": "medium",
                },
                {
                    "id": "SQLI001",
                    "description": "Potential SQL injection in login endpoint",
                    "severity": "high",
                },
            ],
        }


def run_nuclei_scan(url: str) -> Dict[str, Any]:
    nuclei = shutil.which("nuclei")
    if nuclei:
        try:
            completed = subprocess.run(
                [nuclei, "-u", url, "-json", "-silent"],
                check=False,
                capture_output=True,
                text=True,
            )
            findings = []
            for line in completed.stdout.splitlines():
                try:
                    findings.append(json.loads(line))
                except Exception:
                    pass
            return {
                "tool": "nuclei",
                "summary": f"nuclei completed, {len(findings)} findings",
                "findings": findings,
                "returncode": completed.returncode,
            }
        except Exception as exc:
            return {"tool": "nuclei", "summary": f"nuclei failed: {exc}", "findings": []}
    else:
        return {
            "tool": "nuclei",
            "summary": "nuclei not installed – mock findings",
            "findings": [
                {
                    "template": "cves/2021/CVE-2021-XXXXX",
                    "info": {"name": "Example RCE", "severity": "critical"},
                    "matched-at": url,
                }
            ],
        }


def run_mythril_scan(source_code: str) -> Dict[str, Any]:
    mythril_path = shutil.which("mythril")
    if mythril_path:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as tmp:
            tmp.write(source_code)
            tmp.flush()
            tmp_path = tmp.name
        try:
            completed = subprocess.run(
                [mythril_path, "-x", tmp_path, "--no-color"],
                check=False,
                capture_output=True,
                text=True,
            )
            return {
                "tool": "mythril",
                "summary": "Mythril analysis completed",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
            }
        except Exception as exc:
            return {"tool": "mythril", "summary": f"Mythril failed: {exc}", "issues": []}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    else:
        issues = []
        if "call.value" in source_code:
            issues.append(
                {
                    "id": "REENTRANCY",
                    "description": "Usage of call.value detected, potential reentrancy",
                    "severity": "critical",
                }
            )
        if "unchecked" in source_code or "add(" in source_code:
            issues.append(
                {
                    "id": "INTEGER_OVERFLOW",
                    "description": "Unchecked arithmetic operations may overflow",
                    "severity": "high",
                }
            )
        return {"tool": "mythril", "summary": "Mythril not installed – heuristic issues", "issues": issues}


def run_sca_scan(path_or_repo: str) -> Dict[str, Any]:
    """
    Software Composition Analysis. If 'osv-scanner' is installed, run it against the path.
    Otherwise, attempt a very naive parse of common manifest files or return mock issues.
    """
    osv = shutil.which("osv-scanner")
    if osv:
        try:
            completed = subprocess.run(
                [osv, "--recursive", path_or_repo, "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
            data = {}
            try:
                data = json.loads(completed.stdout or "{}")
            except Exception:
                pass
            return {
                "tool": "osv-scanner",
                "summary": "OSV scan completed",
                "results": data,
                "returncode": completed.returncode,
            }
        except Exception as exc:
            return {"tool": "osv-scanner", "summary": f"OSV failed: {exc}", "results": {}}
    # Fallback mock
    manifests = ["requirements.txt", "package.json", "pyproject.toml"]
    found = [m for m in manifests if (Path(path_or_repo) / m).exists()]
    return {
        "tool": "osv-scanner",
        "summary": "osv-scanner not installed – mock SCA",
        "manifests_found": found,
        "vulnerabilities": [
            {"package": "examplepkg", "version": "1.2.3", "cve": "CVE-2022-XXXXX", "severity": "high"}
        ],
    }
