"""``run_tests`` job: run approved test code in a confined sandbox (T-014, ADR-004, ADR-022).

Isolation (``GATP_RUNNER_ISOLATION``):
- ``bwrap`` (default): bubblewrap. The whole filesystem is read-only, the job sandbox is
  the only writable place (bound at its own path), secrets are hidden (``.env``, GATP data and
  artifacts, ~/.ssh, ~/.config, …), separate PID/IPC/UTS namespaces, cleared environment.
- ``process``: same sandbox directory + scrubbed environment, without bubblewrap. Use only
  where bubblewrap cannot run; GATP reports which isolation each run used.
The target allowlist is enforced inside the tests' browsers by ``gatp_run_plugin``.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from importlib.resources import files as package_files
from pathlib import Path
from typing import Any

from gatp.runner.collect import scrubbed_env, write_files
from gatp.runner.jobs import RunTestsJob

SECRET_HOME_DIRS = (".ssh", ".config", ".aws", ".gnupg", ".docker", ".kube", ".netrc")


class IsolationUnavailableError(RuntimeError):
    """bubblewrap was requested but is not installed / not usable."""


@dataclass(frozen=True)
class RunOptions:
    isolation: str  # bwrap | process
    headless: bool
    chromium_executable: str
    slow_mo_ms: int
    hide: tuple[Path, ...]  # GATP data dir, artifacts dir, .env …


def bwrap_prefix(sandbox: Path, hide: tuple[Path, ...]) -> list[str]:
    """bubblewrap arguments: read-only system, secrets hidden, only the sandbox writable.

    Order matters: hide mounts come first; the sandbox (which lives under the hidden GATP data
    folder) is bound last at its own path, so exactly that directory becomes visible+writable.
    """
    exe = shutil.which("bwrap")
    if exe is None:
        raise IsolationUnavailableError(
            "bubblewrap is not installed (sudo apt-get install -y bubblewrap), "
            "or set GATP_RUNNER_ISOLATION=process"
        )
    tmp = "/tmp"  # noqa: S108 - mount point inside the sandbox (fresh tmpfs), not a temp file
    args = [exe, "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", tmp]
    x11 = Path(tmp) / ".X11-unix"
    if x11.exists():  # headed browser needs the display socket
        args += ["--ro-bind", str(x11), str(x11)]
    home = Path.home()
    for name in SECRET_HOME_DIRS:
        target = home / name
        if target.is_dir():
            args += ["--tmpfs", str(target)]
        elif target.exists():
            args += ["--ro-bind", "/dev/null", str(target)]
    for path in hide:
        resolved = path.resolve()
        if resolved.is_dir():
            args += ["--tmpfs", str(resolved)]
        elif resolved.exists():
            args += ["--ro-bind", "/dev/null", str(resolved)]
    real = str(sandbox.resolve())
    args += [
        "--bind", real, real,
        "--chdir", real,
        "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--unshare-cgroup-try",
        "--die-with-parent", "--new-session",
    ]  # fmt: skip
    return args


def run_tests(job: RunTestsJob, sandbox: Path, options: RunOptions) -> dict[str, Any]:
    """Write files + plugin, run pytest (confined), return parsed results."""
    write_files(job.files, sandbox)
    plugin = package_files("gatp.runner").joinpath("gatp_run_plugin.py").read_text(encoding="utf-8")
    (sandbox / "gatp_run_plugin.py").write_text(plugin, encoding="utf-8")
    (sandbox / "results").mkdir(exist_ok=True)
    workdir = str(sandbox.resolve())
    env = scrubbed_env(Path(workdir))
    env.update(
        {
            "GATP_BASE_URL": job.base_url,
            "GATP_ALLOWLIST": json.dumps(job.allowlist),
            "GATP_HEADLESS": "1" if options.headless else "0",
            "GATP_SLOW_MO": str(options.slow_mo_ms),
            "PYTHONPATH": workdir,
        }
    )
    if options.chromium_executable:
        env["GATP_CHROMIUM_EXECUTABLE"] = options.chromium_executable
    argv = [
        sys.executable,
        "-m",
        "pytest",
        f"--rootdir={workdir}",
        "-p",
        "gatp_run_plugin",
        "-p",
        "no:cacheprovider",
        "--junitxml=results/junit.xml",
        "--screenshot=on",
        "--output=results/artifacts",
        "-q",
        "-rA",
        *(job.tests or ["tests"]),
    ]
    prefix: list[str] = []
    if options.isolation == "bwrap":
        prefix = [*bwrap_prefix(sandbox, options.hide), "--clearenv"]
        for key, value in env.items():
            prefix += ["--setenv", key, value]
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv; code passed static checks and G2/G3
            prefix + argv,
            cwd=sandbox,
            env=env if not prefix else None,
            capture_output=True,
            text=True,
            timeout=job.timeout_s,
            check=False,
        )
        output = (proc.stdout + proc.stderr)[-6000:]
        exit_code: int | None = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = str(exc.stdout or "")[-6000:]
        exit_code, timed_out = None, True
    results = parse_junit(sandbox / "results" / "junit.xml")
    attach_screenshots(results, sandbox / "results" / "artifacts")
    blocked_file = sandbox / "results" / "blocked.json"
    blocked = json.loads(blocked_file.read_text()) if blocked_file.exists() else []
    return {
        "isolation": options.isolation,
        "headless": options.headless,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "results": results,
        "blocked_requests": blocked,
        "output": output,
    }


def parse_junit(path: Path) -> list[dict[str, Any]]:
    """Per-test outcome, duration, message and a stack excerpt from pytest's junit XML."""
    if not path.exists():
        return []
    root = ET.parse(path).getroot()  # noqa: S314 - file written by pytest in our sandbox
    out = []
    for case in root.iter("testcase"):
        test_id = f"{case.get('classname', '').replace('.', '/')}.py::{case.get('name')}"
        outcome, message, details = "passed", "", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                message = (node.get("message") or "")[:1000]
                details = (node.text or "")[-3000:]
                break
        out.append(
            {
                "test_id": test_id,
                "name": case.get("name", ""),
                "outcome": outcome,
                "duration_ms": round(float(case.get("time", "0")) * 1000),
                "message": message,
                "details": details,
                "screenshots": [],
            }
        )
    return out


def attach_screenshots(results: list[dict[str, Any]], artifacts: Path) -> None:
    """pytest-playwright writes ``<output>/<slug of node id>/test-*.png``; match them to tests."""
    if not artifacts.exists():
        return
    folders = {f.name: f for f in artifacts.iterdir() if f.is_dir()}
    for r in results:
        expected = re.sub(r"[^a-z0-9]+", "-", r["test_id"].lower()).strip("-")
        folder = folders.get(expected) or next(
            (f for name, f in folders.items() if expected.startswith(name)), None
        )
        if folder is not None:
            r["screenshots"] = sorted(
                str(p.relative_to(artifacts.parent.parent)) for p in folder.glob("*.png")
            )
