"""``collect`` job: write approved code into the sandbox and run ``pytest --collect-only``.

Collection imports the test modules, so it runs in the job's private sandbox directory with a
scrubbed environment (no API keys, HOME = sandbox) and a timeout. Static checks (codegen
validate) have already rejected dangerous imports and calls before this runs.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from gatp.runner.jobs import CollectJob


def scrubbed_env(home: Path) -> dict[str, str]:
    """Minimal environment: nothing from the API process (keys, DB paths) leaks in."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "LANG": "C.UTF-8",
    }
    for key in ("PLAYWRIGHT_BROWSERS_PATH", "DISPLAY", "GATP_CHROMIUM_EXECUTABLE"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def write_files(files: dict[str, str], root: Path) -> None:
    for rel, content in files.items():
        target = (root / rel).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError(f"{rel} escapes the sandbox")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def collect(job: CollectJob, sandbox: Path) -> tuple[dict[str, Any], bool, str]:
    """Return (data, failed, error). data = {tests, exit_code, output}."""
    write_files(job.files, sandbox)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
        "tests",
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, sandbox cwd, scrubbed env
            cmd,
            cwd=sandbox,
            env=scrubbed_env(sandbox),
            capture_output=True,
            text=True,
            timeout=job.timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"tests": [], "exit_code": None, "output": ""}, True, "collection timed out"
    output = (proc.stdout + proc.stderr)[-4000:]
    tests = [line.strip() for line in proc.stdout.splitlines() if "::" in line]
    failed = proc.returncode != 0 or not tests
    error = "" if not failed else (output.strip().splitlines() or ["collection failed"])[-1]
    return {"tests": tests, "exit_code": proc.returncode, "output": output}, failed, error
