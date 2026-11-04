"""Drive the REAL UI through the Phase 1 flow, taking a screenshot at every step.

Starts the fixture site, runner, API and the Vite dev server (via the smoke harness), then uses
a browser like a tester would. Screenshots (and optionally a video) go to the output folder.

Usage:
    uv run poe ui-walkthrough                    # screenshots to ./walkthrough/
    uv run poe ui-walkthrough --headed           # runner browser visible too
    xvfb-run -a -s "-screen 0 1440x900x24" uv run poe ui-walkthrough --record demo.webm
        # screen recording of the whole display: GATP UI + the runner's visible browser
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from e2e_smoke import ROOT, Smoke, free_port
from playwright.sync_api import Locator, Page, expect, sync_playwright


class Walkthrough(Smoke):
    def __init__(self, headed: bool, out: Path, record: Path | None) -> None:
        super().__init__(headed=headed or record is not None, keep=False)
        self.out = out
        self.record = record
        self.web_port = free_port()
        self.web = f"http://127.0.0.1:{self.web_port}"
        self.shots: list[str] = []

    def up(self) -> None:
        super().up()
        env = {**self.env, "GATP_API_URL": str(self.api.base_url).rstrip("/")}
        log = (self.tmp / "web.log").open("wb")
        self.procs.append(
            subprocess.Popen(
                [
                    "npm",
                    "--prefix",
                    "frontend",
                    "run",
                    "dev",
                    "--",
                    "--port",
                    str(self.web_port),
                    "--host",
                    "127.0.0.1",
                ],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        )
        self.wait_for("vite", lambda: httpx.get(self.web).status_code == 200, timeout=60)

    def shot(self, page: Page, name: str, element: Locator | None = None) -> None:
        path = self.out / f"{len(self.shots) + 1:02d}-{name}.png"
        if element is not None:
            element.screenshot(path=path)
        else:
            page.screenshot(path=path, full_page=True)
        self.shots.append(path.name)

    def walk(self, page: Page) -> None:
        site = self.site
        page.goto(self.web)
        expect(page.get_by_role("heading", name="Projects")).to_be_visible()
        expect(page.get_by_test_id("api-health")).to_contain_text("API ok")  # SG-001 'Verify'
        page.get_by_label("Project name").fill("BookShelf demo")
        page.get_by_label("Start URL").fill(f"{site}/index.html")
        self.shot(page, "projects-new")
        page.get_by_role("button", name="Create").click()
        expect(page.get_by_role("heading", name="Inspect pages")).to_be_visible()
        expect(page.get_by_test_id("runner-health")).to_have_text(
            "Runner ready" + ("" if self.env["GATP_RUNNER_HEADLESS"] == "false" else " (headless)")
        )
        page.get_by_test_id("tester-name").fill("Abdo")

        page.get_by_test_id("inspect-button").click()
        expect(page.get_by_test_id("findings")).to_be_visible(timeout=60_000)
        expect(page.get_by_test_id("row-e3")).to_contain_text("Sign in")
        page.get_by_test_id("row-e3").click()
        expect(page.get_by_test_id("candidates-e3")).to_contain_text("usable")
        self.shot(page, "inspect-signin-selected")
        page.get_by_test_id("row-e3").get_by_text("line 23").click()
        expect(page.get_by_test_id("source-line")).to_contain_text("login-submit")
        self.shot(page, "source-line")
        page.keyboard.press("Escape")

        page.get_by_label("Add a page of this site").fill(f"{site}/add.html")
        page.get_by_role("button", name="Add page").click()
        expect(page.get_by_role("tab", name="/add.html")).to_have_attribute("aria-selected", "true")
        panel = page.get_by_role("tabpanel")
        panel.get_by_text("setup step(s)").click()
        editor = panel.get_by_test_id("setup-editor")
        steps = [
            ("goto", None, f"{site}/index.html", None),
            ("fill", "label", "Username", "tester"),
            ("fill", "label", "Password", "secret123"),
            ("click", "test_id", "login-submit", None),
        ]
        for i, (action, strategy, target, value) in enumerate(steps, start=1):
            editor.get_by_role("button", name="Add step").click()
            editor.get_by_label(f"Step {i} action", exact=True).click()
            page.get_by_role("option", name=action, exact=True).click()
            if action == "goto":
                editor.get_by_label(f"Step {i} URL").fill(target)
                continue
            if strategy != "label":  # label is the default strategy
                editor.get_by_label(f"Step {i} locator strategy", exact=True).click()
                page.get_by_role("option", name=strategy, exact=True).click()
            editor.get_by_label(f"Step {i} locator value").fill(target)
            if value is not None:
                editor.get_by_label(f"Step {i} value", exact=True).fill(value)
        self.shot(page, "setup-steps")
        editor.get_by_role("button", name="Save steps").click()
        expect(panel.get_by_text("4 setup step(s)")).to_be_visible()
        panel.get_by_test_id("inspect-button").click()
        expect(panel.get_by_test_id("findings")).to_contain_text("Year published", timeout=60_000)
        expect(panel.get_by_test_id("row-e4")).to_contain_text("no visible label")
        panel.get_by_test_id("box-e6").click()
        expect(panel.get_by_test_id("row-e6")).to_contain_text("Save")
        self.shot(page, "inspect-add-book")

        page.get_by_test_id("step-scope").click()
        expect(page.get_by_role("heading", name="Scope and goal")).to_be_visible()
        page.get_by_test_id("goal").fill("Adding a book validates title, author, year and genre")
        add_card = page.locator(".mantine-Card-root").filter(has_text="BookShelf · Add book")
        add_card.get_by_label("e1 link “Back to books”").uncheck()
        add_card.get_by_label("e7 link “Cancel”").uncheck()
        signin_card = page.locator(".mantine-Card-root").filter(has_text="BookShelf · Sign in")
        for key in ("e1", "e2", "e3"):
            signin_card.locator(f"[data-testid$='-{key}']").uncheck()
        page.get_by_test_id("save-scope").click()
        expect(page.get_by_test_id("scope-version")).to_have_text("version 1")
        expect(page.get_by_test_id("step-scope")).to_contain_text("needs approval")
        self.shot(page, "scope-saved")
        page.get_by_test_id("approve-g0").click()
        expect(page.get_by_test_id("scope-approved")).to_be_visible()
        expect(page.get_by_test_id("step-scope")).to_contain_text("done")
        self.shot(page, "scope-approved")

        page.get_by_test_id("ask-model").click()
        expect(page.get_by_test_id("insight-summary")).to_be_visible(timeout=120_000)
        expect(page.get_by_test_id("usage")).to_contain_text("Model time")
        expect(page.get_by_test_id("browser-time")).not_to_have_text("0 ms")
        page.get_by_text("Exactly what was sent").click()
        expect(page.get_by_test_id("insight-panel")).to_contain_text("untrusted_page_data")
        self.shot(page, "model-insight", page.get_by_test_id("insight-panel"))

        page.get_by_test_id("ask-model").click()  # identical request -> served from the cache
        expect(page.get_by_test_id("usage")).to_contain_text("reused")
        pid = page.url.split("/projects/")[1].split("/")[0]
        calls = self.api.get(f"/api/projects/{pid}/llm-calls").json()
        snaps = [
            {"title": s["title"], "url": s["url"], "browser_ms": s["meta"].get("browser_ms")}
            for p in self.api.get(f"/api/projects/{pid}/pages").json()
            for s in [
                self.api.get(
                    f"/api/snapshots/{self.api.get(f'/api/pages/{p["id"]}/snapshots').json()[0]['id']}"
                ).json()
            ]
        ]
        evidence = {"inspections": snaps, "llm_calls": calls}
        (self.out / "usage-evidence.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
        )

    def start_recording(self) -> subprocess.Popen[bytes] | None:
        """Record the whole X display (GATP UI + the runner's visible browser) with ffmpeg."""
        if not self.record:
            return None
        display = os.environ.get("DISPLAY")
        if not display:
            raise RuntimeError(
                "--record needs a display; run under: xvfb-run -a -s '-screen 0 1440x900x24'"
            )
        self.record.parent.mkdir(parents=True, exist_ok=True)
        return subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-video_size",
                "1440x900",
                "-framerate",
                "15",
                "-f",
                "x11grab",
                "-i",
                display,
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "600k",
                "-deadline",
                "realtime",
                "-cpu-used",
                "8",
                str(self.record),
            ],
            stdin=subprocess.PIPE,
        )

    def stop_recording(self, recorder: subprocess.Popen[bytes] | None) -> None:
        if recorder is None or recorder.stdin is None:
            return
        recorder.stdin.write(b"q")
        recorder.stdin.flush()
        recorder.wait(timeout=60)
        size = self.record.stat().st_size // 1024 if self.record else 0
        print(f"recorded {self.record} ({size} kB)")

    def run_ui(self) -> int:
        self.out.mkdir(parents=True, exist_ok=True)
        for old in self.out.glob("*.png"):
            old.unlink()
        executable = os.environ.get("GATP_CHROMIUM_EXECUTABLE") or None
        recorder = self.start_recording()
        with sync_playwright() as pw:
            if self.record:
                # Visible, slowed-down browser so the screen recording is watchable.
                browser = pw.chromium.launch(
                    executable_path=executable,
                    headless=False,
                    slow_mo=250,
                    args=["--window-position=0,0", "--window-size=1440,900"],
                )
                context = browser.new_context(no_viewport=True)
            else:
                browser = pw.chromium.launch(executable_path=executable)
                context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(f"page error: {exc}"))
            page.on(
                "console",
                lambda m: (
                    errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None
                ),
            )
            started = time.perf_counter()
            try:
                self.walk(page)
                status = 0
            except Exception as exc:
                self.shot(page, "FAILED")
                print(f"FAIL  {type(exc).__name__}: {exc}")
                status = 1
            if self.record:
                page.wait_for_timeout(2000)  # hold the last screen for a moment
            context.close()
            browser.close()
        self.stop_recording(recorder)
        for e in errors:
            print(f"  {e[:400]}")
            status = 1 if e.startswith("page error") else status
        print(
            f"{'OK' if status == 0 else 'FAILED'} in {time.perf_counter() - started:.1f}s; screenshots in {self.out}:"
        )
        for s in self.shots:
            print(f"  {s}")
        return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--record", type=Path, help="screen-record to this .webm (needs a display)")
    parser.add_argument("--out", type=Path, default=Path("walkthrough"))
    args = parser.parse_args()
    w = Walkthrough(args.headed, args.out.resolve(), args.record.resolve() if args.record else None)
    try:
        w.up()
        return w.run_ui()
    except RuntimeError as exc:
        print(f"FAIL  startup: {exc}")
        w.failures += 1
        return 1
    finally:
        w.down()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
