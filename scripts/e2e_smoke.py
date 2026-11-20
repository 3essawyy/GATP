"""End-to-end smoke test of the REAL system (``uv run poe smoke``).

Starts the fixture site, the runner (separate process on its Unix socket) and the API
(separate process on a free port) in a temporary data directory, then walks the workflow over
HTTP exactly as the UI would. Prints PASS/FAIL per step with timings; exit code 1 on failure.

Usage:
    uv run poe smoke              # headless browser
    uv run poe smoke --headed     # visible browser (needs a display, or run under xvfb-run)
    uv run poe smoke --keep       # keep the temp dir (DB, screenshots) for inspection
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class Smoke:
    def __init__(self, headed: bool, keep: bool) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="gatp-smoke-"))
        self.keep = keep
        self.site_port, self.api_port = free_port(), free_port()
        self.site = f"http://127.0.0.1:{self.site_port}"
        self.api = httpx.Client(base_url=f"http://127.0.0.1:{self.api_port}", timeout=120)
        self.env = {
            **os.environ,
            "GATP_DATA_DIR": str(self.tmp / "data"),
            "GATP_ARTIFACTS_DIR": str(self.tmp / "artifacts"),
            "GATP_RUNNER_SANDBOX_DIR": str(self.tmp / "sandbox"),
            "GATP_RUNNER_SOCKET": str(self.tmp / "run" / "runner.sock"),
            "GATP_RUNNER_HEADLESS": "false" if headed else "true",
            # Default to the offline provider so CI/smoke never need a key; export
            # GATP_LLM_PRIMARY=gemini (and optionally GATP_LLM_FALLBACK) for a real-model run.
            "GATP_LLM_PRIMARY": os.environ.get("GATP_LLM_PRIMARY", "fake"),
            "GATP_LLM_FALLBACK": os.environ.get("GATP_LLM_FALLBACK", ""),
        }
        self.procs: list[subprocess.Popen[bytes]] = []
        self.failures = 0
        self.state: dict[str, Any] = {}

    # -- process management -------------------------------------------------------------
    def start(self, name: str, argv: list[str]) -> None:
        log = (self.tmp / f"{name}.log").open("wb")
        self.procs.append(
            subprocess.Popen(argv, cwd=ROOT, env=self.env, stdout=log, stderr=subprocess.STDOUT)
        )

    def wait_for(self, what: str, probe: Callable[[], bool], timeout: float = 30) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if probe():
                    return
            except (httpx.HTTPError, OSError):
                pass
            time.sleep(0.2)
        raise RuntimeError(f"{what} did not start; see logs in {self.tmp}")

    def up(self) -> None:
        py = sys.executable
        self.start("fixtures", [py, "fixtures/serve.py", "v1", "--port", str(self.site_port)])
        self.start("runner", [py, "-m", "gatp.runner.main"])
        self.start("api", [py, "-m", "gatp.api.main", "--port", str(self.api_port)])
        self.wait_for("fixture site", lambda: httpx.get(self.site).status_code == 200)
        self.wait_for("api", lambda: self.api.get("/api/health").status_code == 200)
        self.wait_for("runner", lambda: self.api.get("/api/runner/health").json()["available"])

    def switch_site(self, version: str) -> None:
        """Restart the fixture site as ``version`` on the same port: the site "changes"."""
        old = self.procs.pop(0)  # started first in up()
        old.send_signal(signal.SIGTERM)
        old.wait(timeout=10)
        py = sys.executable
        log = (self.tmp / f"fixtures-{version}.log").open("wb")
        argv = [py, "fixtures/serve.py", version, "--port", str(self.site_port)]
        self.procs.insert(
            0, subprocess.Popen(argv, cwd=ROOT, env=self.env, stdout=log, stderr=subprocess.STDOUT)
        )
        self.wait_for(f"fixture site {version}", lambda: httpx.get(self.site).status_code == 200)

    def down(self) -> None:
        for p in self.procs:
            p.send_signal(signal.SIGTERM)
        for p in self.procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        if self.keep or self.failures:
            print(f"\nkept for inspection: {self.tmp}")
        else:
            shutil.rmtree(self.tmp, ignore_errors=True)

    # -- steps ----------------------------------------------------------------------------
    def step(self, title: str, fn: Callable[[], str]) -> None:
        started = time.perf_counter()
        try:
            detail = fn()
            status = "PASS"
        except Exception as exc:
            detail, status = f"{type(exc).__name__}: {exc}", "FAIL"
            self.failures += 1
        ms = round((time.perf_counter() - started) * 1000)
        print(f"{status}  {title:<52} {ms:>6} ms  {detail}")

    def call(self, method: str, url: str, expect: int, **kw: Any) -> Any:
        resp = self.api.request(method, url, **kw)
        if resp.status_code != expect:
            raise AssertionError(f"{method} {url} -> {resp.status_code} {resp.text[:300]}")
        return resp.json() if resp.content else None

    def run(self) -> int:
        s = self.state

        def create() -> str:
            p = self.call(
                "POST",
                "/api/projects",
                201,
                json={"name": "Smoke", "url": f"{self.site}/index.html"},
            )
            s["pid"] = p["id"]
            s["start_page"] = self.call("GET", f"/api/projects/{p['id']}/pages", 200)[0]["id"]
            return f"project {p['id']} origin={p['origin']}"

        def inspect_login() -> str:
            r = self.call("POST", f"/api/pages/{s['start_page']}/inspections", 201, json={})
            snap = r["snapshot"]
            s["login_snap"] = snap
            names = [e["name"] for e in snap["elements"] if e["details"]["interactive"]]
            assert names == ["Username", "Password", "Sign in"], names
            shot = self.api.get(f"/api/files/{snap['screenshot_path']}")
            assert shot.content[:4] == b"\x89PNG", "screenshot not served"
            return f"{len(names)} elements, browser {r['duration_ms']} ms, blocked={len(r['blocked_requests'])}"

        def add_page_with_setup() -> str:
            page = self.call(
                "POST",
                f"/api/projects/{s['pid']}/pages",
                201,
                json={"url": f"{self.site}/add.html"},
            )
            s["add_page"] = page["id"]
            steps = [
                {"action": "goto", "url": f"{self.site}/index.html"},
                {
                    "action": "fill",
                    "locator": {"strategy": "label", "value": "Username"},
                    "value": "tester",
                },
                {
                    "action": "fill",
                    "locator": {"strategy": "label", "value": "Password"},
                    "value": "secret123",
                },
                {"action": "click", "locator": {"strategy": "test_id", "value": "login-submit"}},
            ]
            self.call("PUT", f"/api/pages/{page['id']}/setup", 200, json={"steps": steps})
            return "add.html with 4 sign-in setup steps"

        def inspect_add() -> str:
            r = self.call("POST", f"/api/pages/{s['add_page']}/inspections", 201, json={})
            snap = r["snapshot"]
            s["add_snap"] = snap
            assert snap["title"] == "BookShelf · Add book", snap["title"]
            flagged = {
                e["name"]: e["details"]["flags"] for e in snap["elements"] if e["details"]["flags"]
            }
            assert "no_visible_label" in flagged.get("Year published", []), flagged
            return f"{len(snap['elements'])} elements; flagged: {flagged}"

        def scope_and_gate() -> str:
            body = {
                "pages": [{"snapshot_id": s["add_snap"]["id"], "exclude": ["e1", "e7"]}],
                "goal": "Adding a book validates input",
                "actor": "smoke",
            }
            scope = self.call("PUT", f"/api/projects/{s['pid']}/scope", 200, json=body)
            wf = {
                x["step"]: x["status"]
                for x in self.call("GET", f"/api/projects/{s['pid']}/workflow", 200)
            }
            assert wf["scope"] == "needs_approval", wf
            self.call(
                "POST",
                f"/api/projects/{s['pid']}/approvals",
                201,
                json={
                    "gate": "G0",
                    "actor": "smoke",
                    "artifact_version_id": scope["version"]["id"],
                },
            )
            wf = {
                x["step"]: x["status"]
                for x in self.call("GET", f"/api/projects/{s['pid']}/workflow", 200)
            }
            assert wf["scope"] == "approved", wf
            s["scope_v1"] = scope["version"]["id"]
            return "scope v1 saved -> needs_approval -> G0 -> approved"

        def edit_invalidates() -> str:
            body = {
                "pages": [{"snapshot_id": s["add_snap"]["id"], "exclude": ["e1"]}],
                "actor": "smoke",
            }
            scope = self.call("PUT", f"/api/projects/{s['pid']}/scope", 200, json=body)
            assert scope["version"]["number"] == 2 and not scope["approved"], scope
            stale = self.api.post(
                f"/api/projects/{s['pid']}/approvals",
                json={"gate": "G0", "actor": "smoke", "artifact_version_id": s["scope_v1"]},
            )
            assert stale.status_code == 409, stale.text
            return "edit -> v2 unapproved; re-approving v1 refused (409)"

        def model_insight() -> str:
            scope = self.call("GET", f"/api/projects/{s['pid']}/scope", 200)
            self.call(
                "POST",
                f"/api/projects/{s['pid']}/approvals",
                201,
                json={
                    "gate": "G0",
                    "actor": "smoke",
                    "artifact_version_id": scope["version"]["id"],
                },
            )
            r = self.call("POST", f"/api/projects/{s['pid']}/insight", 201)
            sent = set(r["element_ids_sent"])
            assert f"s{s['add_snap']['id']}.e1" not in sent, sent  # excluded in the scope
            c = r["call"]
            return f"{c['provider']}/{c['model']} {c['latency_ms']} ms model vs {r['browser_ms']} ms browser, {len(sent)} elements sent"

        def plan_and_code() -> str:
            pid = s["pid"]
            plan = self.call("POST", f"/api/projects/{pid}/plan/propose", 201, json={})
            for c in plan["open_clarifications"]:
                answer = "Confirm" if c["kind"] == "assumption" else "any letters"
                self.call(
                    "POST",
                    f"/api/clarifications/{c['id']}/answer",
                    200,
                    json={"answer": answer, "actor": "smoke"},
                )
            plan = self.call("GET", f"/api/projects/{pid}/plan", 200)
            assert plan["blockers"] == [], plan["blockers"]
            self.call(
                "POST",
                f"/api/projects/{pid}/approvals",
                201,
                json={"gate": "G1", "actor": "smoke", "artifact_version_id": plan["version"]["id"]},
            )
            code = self.call("POST", f"/api/projects/{pid}/code/generate", 201)
            report = self.call("POST", f"/api/projects/{pid}/code/validate", 200)["report"]
            assert report["ok"], report["report"]
            self.call("POST", f"/api/projects/{pid}/code/approve", 201, json={"actor": "smoke"})
            tests = report["report"]["collect"]["tests"]
            subject = self.call("GET", f"/api/projects/{pid}/runs/subject", 200)["subject"]
            g3 = self.call(
                "POST",
                f"/api/projects/{pid}/approvals",
                201,
                json={"gate": "G3", "actor": "smoke", "subject": subject},
            )
            run = self.call(
                "POST", f"/api/projects/{pid}/runs", 201, json={"approval_id": g3["id"]}
            )
            assert run["status"] in ("passed", "failed"), run["scope"]
            outcomes = [r["outcome"] for r in run["results"]]
            return (
                f"plan v{plan['version']['number']} G1; {len(code['files'])} files; collect: {len(tests)} test(s); G2; "
                f"G3 run #{run['id']} {run['status']} {outcomes} in {run['duration_ms']} ms ({run['scope']['isolation']})"
            )

        def off_origin_refused() -> str:
            r = self.api.post(
                f"/api/projects/{s['pid']}/pages", json={"url": "http://example.com/"}
            )
            assert r.status_code == 422, r.text
            return "page outside the project origin -> 422"

        for title, fn in (
            ("create project (origin = allowlist)", create),
            ("inspect sign-in page via runner socket", inspect_login),
            ("add page + sign-in setup steps", add_page_with_setup),
            ("inspect add-book page (signed in)", inspect_add),
            ("save scope, approve G0", scope_and_gate),
            ("edit scope invalidates approval", edit_invalidates),
            ("re-approve + grounded model call (T-010)", model_insight),
            ("plan G1 -> code -> validate -> G2 -> G3 run (runner)", plan_and_code),
            ("off-origin page refused", off_origin_refused),
        ):
            self.step(title, fn)
        (self.tmp / "state.json").write_text(
            json.dumps({k: v for k, v in s.items() if "snap" not in k})
        )
        print(f"\n{'OK' if not self.failures else 'FAILED'}: {self.failures} failing step(s)")
        return 1 if self.failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--headed", action="store_true", help="visible browser")
    parser.add_argument("--keep", action="store_true", help="keep temp dir")
    args = parser.parse_args()
    smoke = Smoke(args.headed, args.keep)
    try:
        smoke.up()
        return smoke.run()
    except RuntimeError as exc:
        print(f"FAIL  startup: {exc}")
        smoke.failures += 1
        return 1
    finally:
        smoke.down()


if __name__ == "__main__":
    raise SystemExit(main())
