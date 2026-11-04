# T-014: Approved execution, results, screenshots (G3)

- **Status:** Done
- **Phase:** P2
- **Target:** W+4
- **Modules:** runner, api, store, web-ui
- **Requirements:** REQ-G5, REQ-P2-3, REQ-Q3, REQ-Q5, REQ-Q6, REQ-Q8
- **Depends on:** T-013
- **Plan:** [PLAN-014](../implementationPlans/PLAN-014-execution.md)
- **ADRs:** [ADR-022](../decisions/ADR-022-approved-execution-sandbox.md)
- **TCs:** TC-205 Pass, TC-206 Pass
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
Run exactly the approved code version in the isolated runner with a visible browser and show reviewable results.

## Acceptance criteria
- [x] Execution refused without G3 approval on the exact version (and on any later edit; one approval = one run)
- [x] A deliberately failing case shows its real failure (not hidden): message with expected vs actual, stack, `test-failed` screenshot; code unchanged

## Verification (real system)
- **Probe run on the real runner under bubblewrap:**
  - **Isolation:** a probe test confirmed the GATP database is invisible, no API key is in the environment, the repo is read-only and the sandbox writable. Under `process` isolation the same probe **could** see the DB, which shows why bwrap is the default.
  - **Network:** an external `fetch` was blocked and recorded.
  - **Failures:** a deliberate failure was reported with Playwright's message.
- **Bugs found and fixed:**
  - pytest used GATP's `pyproject.toml` inside the repo (that would also have broken `collect`);
  - the `/work` mount failed on a read-only root;
  - screenshots weren't matched to tests.
- **Smoke:** a full G3 run over the socket in bwrap (CI installs bubblewrap and enables user namespaces).
- **Walkthrough (screens 14–15):** the G3 screen, then the run. The offline example's confirmed assumption "error region becomes visible" **fails for real**. The screenshot shows the page reported Year/Genre errors instead, which is exactly the kind of evidence T-015's feedback loop acts on.
- **From the review:** the run step now shows "last run failed" instead of "needs approval".

## Explain it (code-defense prep)
**What.** The Run step shows exactly what a G3 approval will authorise: the code file versions, the target origin, which tests, the sandbox type and the browser mode. "Approve (G3) and run" records that approval, and the runner then runs pytest on exactly those files in a sandbox. Results show each test's outcome, time, real error message, stack excerpt and screenshot.

**Why.** Executing generated code is the most consequential step (REQ-G5). It must happen in a restricted process limited to the approved target (REQ-Q5, REQ-Q6). Real failures must stay visible instead of being weakened away (REQ-Q3). Test time is reported separately from model time (REQ-Q8).

**How it works:**
1. **Subject:** `current_subject()` = all current code version ids (which must be G2-approved) + the project origin + the selected tests.
2. **Approval:** the approval endpoint refuses a G3 whose subject differs.
3. **Run checks:** `execute()` re-checks the subject, refuses an already-used approval, and creates the run.
4. **Execution:** the runner writes the files, `gatp_run_plugin.py` and a `pytest.ini` into a fresh sandbox, then starts `bwrap … python -m pytest -p gatp_run_plugin --junitxml … --screenshot=on`.
5. **Isolation:** bwrap makes `/` read-only, hides `.env`, GATP's data/artifacts and secret home folders, makes only the sandbox writable, and clears the environment.
6. **Allowlist:** the plugin routes every test browser context through the origin check.
7. **Results:** junit XML gives per-test outcome, time and message; screenshots are matched per test and copied to `artifacts/`.
8. **Storage and status:** the run and its results are stored, and the workflow shows passed / last run failed.

**Likely examiner questions:**
- *Can a test run without approval, or with code edited after approval?* No. G3 names exact version ids, and every run re-checks them. An edit creates a new version, so the old approval no longer matches. An approval can't be reused.
- *What can a malicious test do?* Static checks reject dangerous imports and calls before G2. At run time bubblewrap gives a read-only system with secrets hidden, and the browser can only reach the target origin. Remaining limits (same OS user, no network namespace) are documented in SG-006.
- *How do I know a failure is real?* The message shows Playwright's expected vs actual, the screenshot shows the page at failure, and the code version is unchanged. GATP never edits assertions to make a run pass.
- *Where is the visible browser?* The runner is headed by default (`GATP_RUNNER_HEADLESS=false`), and the generated conftest passes that to the test browser. CI and the cloud build use headless or Xvfb.
