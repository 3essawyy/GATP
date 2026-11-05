# Session S004 — 2026-11-04 — Full-build run (T-003 onward)

- **Tasks touched:** T-003 … T-016 (T-016 in review)
- **Branches / PRs:** `claude/serene-johnson-xtbl4s`, one squash-merged PR per task

## Interview outcome (before the run)
Abdo approved a "grill now, then run" mode: Claude builds T-003…T-021 in order without stopping and asks only for blockers. Decisions agreed, each recorded as an ADR in the task that implements it:

| Area | Decision | ADR (when written) |
|---|---|---|
| LLM in dev | Real Gemini via `GATP_GEMINI_API_KEY` env secret (added by Abdo, never in the repo); CI uses a deterministic fake provider; Ollama checked by the team locally | T-005 |
| Visible browser | Always headed; Xvfb + screenshots in the cloud; `GATP_RUNNER_HEADLESS=1` only for CI | T-006 |
| Fixture site | "BookShelf" static HTML/JS; FXC-1 clear, FXC-2 ambiguous | T-003 (in PLAN-003, ADR-009) |
| Store | SQLAlchemy 2 + Alembic behind repositories | T-004 |
| Runner IPC | Typed HTTP over a Unix domain socket (0600); progress relayed API → UI via SSE | T-006 |
| Codegen | Page objects rendered from inspected elements; LLM emits step JSON referencing known element IDs only; Jinja templates render pytest + POM; AST check as second guard | T-013 |
| Sandbox | bubblewrap + resource limits + scrubbed env + origin allowlist; clear error if bwrap is missing | T-014/T-020 |
| Product shape | Project = one origin, many pages inspected one by one; workspace + step nav with gate states (React Router); single local user, no auth, approver name recorded | T-008/T-009 |
| Owners | Member 1–4 suggested grouping; names filled in later | — |
| Submission | Claude writes SG-004 and records a backup walkthrough video; team records the live demo; Markdown + PDF export; tags `phase1-rc`/`phase2-rc`, final tags at real submission | T-011/T-021 |
| Bonus | Stays deferred (ADR-011) | — |

## Done
- **T-003:** BookShelf fixture site v1/v2, `poe fixtures`, `GATP_CHROMIUM_EXECUTABLE` setting, 14 new tests (TC-103 Pass), fixtures README, SG-001 section. PR #3.
- **T-004:** Store core: 15-table SQLAlchemy schema, Alembic (auto-migrate on start), repositories returning DTOs, immutable versions with diff/restore, double immutability (ORM guards + SQLite triggers), artifact files confined to `artifacts/`, `poe db-upgrade`/`db-revision`. 22 new tests (TC-104 Pass).
- Fixed: the ADR index was missing the ADR-014 row (a silent replace failure in S003). PR #4.
- **T-005:** LLM gateway: httpx Gemini/Ollama/fake providers, versioned templates with untrusted-data framing, cache (`reused` rows), backoff + fallback, Pydantic validation + one repair retry + semantic `check` hook, every attempt logged (`llm_calls`, migration 0002 adds `template_version`), `poe llm-check`, SG-003. 20 new tests (TC-105 automated Pass). PR #5.
- **T-006:** Runner: typed jobs (`inspect` stub, `recount`) over HTTP on a private Unix socket (0600 in 0700 dir, no TCP port), single worker thread, per-job 0700 sandbox, Playwright allowlist routing with blocked-request log, headed Chromium (verified under `xvfb-run`), `RunnerClient`, `LocatorSpec`. 17 runner tests (TC-106 Pass). PR #6.
- **T-007:** Inspector: read-only in-page extraction, ADR-006 candidates verified live (count + identity), non-positional default, flags for weak elements, source lines from served HTML, fingerprints; runner `inspect` with scope + setup steps (sign-in) + redirect check; store migration 0003; api converter; sample snapshots in `docs/samples/`. 8 inspector tests (TC-108 Pass). PR #7.
- **T-008:** API core: services container + DB migration on startup, projects/pages/setup steps/requirements, inspections via the runner, snapshots/files, scope (G0) as versioned artifact, artifacts (versions, edit, diff, G5 restore), approvals bound to exact versions, clarifications, computed workflow, SSE events, error mapping, regenerated TS client. 17 API tests (TC-109 Pass).
- **Working agreement (Abdo, mid-session):** always verify on the real running system and act on the findings. Added `uv run poe smoke` (real fixture site + runner + API processes; also in CI) and a DoD line in CLAUDE.md. T-008 verified with it, headless and headed. PR #8.
- **T-009:** UI: projects, workspace with API-computed step status, inspect (setup editor, regions, screenshot ⇄ findings, candidates, source modal), scope + goal + G0, clarification banner, SSE refresh. New `uv run poe ui-walkthrough` drives the real UI; its screenshots found 5 issues (React effect returning a Promise, setup-step locator not saved, unlabeled editor fields, wrong placeholder, console 404s), all fixed. Evidence in `docs/samples/phase1-walkthrough/`. PR #9.
- **T-010:** Grounded insight call on the **approved** scope only (G0 required), qualified element ids checked against what was sent (repair retry → 502), observed vs assumption + questions, usage card (provider/model/version, tokens with source, model vs browser time, fresh/reused), exact request logged (migration 0005). Smoke + walkthrough extended; 4 UI polish fixes from the screenshot review. PR #10.
- **T-011:** Phase 1 pack: HLD v0.2, design PDF (`poe pdf-phase1`), SG-004/005/006, DEFENSE.md, screen-recorded walkthrough (`--record`, shows the runner's own window), usage evidence, TC-102 Run 2 Pass (clean container, full SG-001 + real inspection), secret scan clean, `.env.example` completeness test. Testing found 3 issues (missing start-page badge vs SG-001, 4 undocumented settings, PDF diagram split), all fixed. PR #11.
- **T-012:** Test plans: inspector observable regions (`o<n>`), structured `TestPlan` contract validated against the approved scope, stable expectation ids, clarifications for assumptions/questions that block G1 and update the plan as new versions, plan editor UI, revise with feedback, offline example plans for the `fake` provider. Walkthrough extended (screens 09–11); review fixed question wording and a misleading usage row. PR #12.
- **T-013:** Deterministic codegen (POM + tests + conftest) from the G1 plan; static validation (syntax, verified locators, structure, safety), runner recount (with setup steps) + new `collect` job; reports bound to versions (migration 0006); G2 rule; Code page. **Real run** of a generated test found the missing sign-in in tests → page objects replay setup steps; collect caught a generator import bug. Smoke + walkthrough extended (screens 12–13). PR #13.
- **T-014:** Approved execution: G3 subject (exact code versions + target + tests), single-use approvals, `run_tests` job in bubblewrap (secrets hidden, read-only system, cleared env) with an allowlist plugin, junit + screenshots → results; Run page. Real-runner probes found 3 bugs (pytest picking up GATP's pyproject inside the repo, bwrap mount, screenshot matching), all fixed. Smoke runs a real G3 run; walkthrough screens 14–15 show a real, visible failure. PR #14 (CI found that Playwright looked for browsers under the sandbox HOME; fixed).
- **T-015:** Feedback → revise → approved rerun: run failures (mapped back to expectation ids) go to the model as untrusted data; a guard compares every revision/edit with the last approved version and raises `weakening` clarifications (Accept / Restore only) that block G1/G2. Walkthrough screens 16–18: feedback → flagged removals → G1/G2/new G3 → rerun passes. PR #15.
- **T-016 (PR open, not yet merged):** Rescan + diff + change flags.
  - Rescans all approved pages into new snapshots. Deterministic matching (`maintainer/match.py`) gives unchanged / clear (≥ 0.70, margin 0.15, no split) / ambiguous / missing, with per-field evidence.
  - Read-only setup retry when sign-in breaks on a clear match. Rescans + change sets are stored (migration 0007).
  - Maintain page; switchable fixture server.
  - Fixture result: FXC-1 clear (0.85), FXC-2 ambiguous (Save draft 0.81 / Publish 0.69, split), FXC-3 "page HTML changed". Walkthrough screen 19.

## Decisions (with ADR links)
- T-003: none beyond PLAN-003.
- T-004: [ADR-015](../decisions/ADR-015-db-access-sqlalchemy-alembic.md) SQLAlchemy 2 + Alembic; immutability enforced twice.
- T-005: [ADR-016](../decisions/ADR-016-llm-gateway-design.md) gateway design; default `gemini-2.5-flash` (limits unverified: Google docs host blocked in the sandbox).
- T-006: [ADR-017](../decisions/ADR-017-runner-unix-socket-jobs.md) runner transport on a private Unix socket.
- T-007: [ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md) setup steps; usable = unique and targets the element; positional CSS never default.
- T-008: [ADR-019](../decisions/ADR-019-gates-on-versions-computed-workflow.md) approvals bound to immutable versions; workflow computed.
- T-012: [ADR-020](../decisions/ADR-020-test-plan-contract.md) plan contract, observable regions, offline examples.
- T-013: [ADR-021](../decisions/ADR-021-deterministic-codegen.md) deterministic codegen, version-bound reports, setup steps in page objects, Monaco dropped.
- T-014: [ADR-022](../decisions/ADR-022-approved-execution-sandbox.md) G3 subject, one run per approval, bubblewrap, allowlist plugin.
- T-015: [ADR-023](../decisions/ADR-023-feedback-and-weakening-guard.md) run feedback → revision; weakening guard against the approved version.
- T-016: [ADR-024](../decisions/ADR-024-rescan-matching-rules.md) matching rules incl. the "split" rule; read-only setup retry; rescans/change sets write-once.

## Open items / blockers
- Waiting on Abdo to add `GATP_GEMINI_API_KEY` to the cloud environment; it is only visible to a **new** session. Then run `uv run poe llm-check` and fill SG-003 §6 (TC-105 live part, TC-111).
- Ollama live check must be done on a team machine (ollama.com is blocked here).
- **Tag `phase1-rc` not pushed:** the cloud git proxy rejects tag pushes (HTTP 403) and no GitHub tool here creates tags. Create it on GitHub (Releases → new release → tag `phase1-rc` on `74ade15`, the T-011 merge) or locally: `git tag phase1-rc 74ade15 && git push origin phase1-rc`.

## Next steps (in order)
1. **Merge T-016's PR** once CI is green (open it from `claude/serene-johnson-xtbl4s` if this session's PR is gone). Then sync the session branch (`git checkout -B <branch> origin/main` + `merge -s ours` of the old remote tip; force-push is blocked).
2. **T-017 Repairs (G4) + clarification + rerun affected.** Design already implied by ADR-007/024; write PLAN-017 + ADR-025.
   - From the latest rescan, a **clear match** becomes a `repair_proposals` row (table exists since 0001). Evidence: the change-set item and breakdown. The LLM only *explains* the change in plain language (new template; offline example for `fake`).
   - **Ambiguous / missing** elements raise a clarification on step `maintain` with the candidates as options (e.g. "Save draft", "Publish", "Element removed: keep test failing").
     - The tester's choice turns it into a proposal.
     - Never auto-pick (FXC-2).
   - **G4 approval** of a proposal (or a batch) applies it, and **only locators** change:
     - new page-object versions (author `repair`), replacing the old locator expression with the new one;
     - updated page setup steps where the setup used that element (FXC-1 → add.html step 4);
     - plan element ids remapped to the new snapshot (`s<old>.eN` → `s<new>.eM`) so codegen and validation keep working. Assertions and steps stay intact; the T-015 weakening guard must stay silent for locator-only repairs.
   - After applying: re-validate (static + recount + collect), G2, then propose a **rerun of only affected tests** (tests whose page objects or setup changed) via G3, using the existing run subject's `tests` list.
   - The scope must move to the new snapshots. Either save a new scope version pointing at the rescanned snapshots (with G0), or treat the G4 apply as re-baselining. Decide in ADR-025 (recommendation: new scope version created by the repair, needing G0 again, consistent with "every change is a new version").
   - **UI:** proposals with before/after locator + evidence + explanation, approve G4, clarification choices, "rerun affected" button. **Walkthrough:** v2 → rescan → approve FXC-1 repair → answer FXC-2 (Publish) → G4 → validate/G2 → G3 rerun affected → pass. TC-209/TC-210.
3. **T-018** versions UI (history, diffs, G5 restore; backend exists since T-004/T-008).
4. **T-019** usage panel (per-call metrics, averages, fresh vs reused, test vs model time; data already in `llm_calls` and `runs`).
5. **T-020** security hardening tests (prompt injection in page text, allowlist, sandbox escape attempts).
6. **T-021** Phase 2 pack: HLD v0.3, PDF, demo recording (`ui_walkthrough.py --record` under `xvfb-run`), DEFENSE.md update, tag `phase2-rc` (tags must be created on GitHub, see open items).
7. Abdo: add `GATP_GEMINI_API_KEY` (new session) → `poe llm-check` → real-model evidence for TC-111.

## Remaining acceptance tests (TC) and where they come from
| TC | Needs | Task |
|---|---|---|
| TC-209 clear change → repair → approve → rerun passes | repair proposals, G4 apply, rerun affected | T-017 |
| TC-210 ambiguous → clarification, never auto-resolved | maintain clarifications with candidates | T-017 |
| TC-211 version diff + restore | UI only (API done in T-004/T-008) | T-018 |
| TC-212 usage per call + averages, model vs test time | UI over `llm_calls` + `runs` | T-019 |
| TC-213 prompt injection treated as data; sandbox confinement | injection fixture page + tests; bwrap probe already proven in T-014 | T-020 |
| TC-215 full Phase 2 demo end to end | walkthrough extended through T-017, recorded | T-021 |
| TC-111 real model evidence | Gemini key in a new session (Abdo) | — |

## Risks for the Phase 2 submission
- **Only one site has ever been tested.** Everything was verified on our BookShelf fixture. The instructor's site may have no test ids, weaker labels, iframes, or client-side routing.
  - Before T-021, do a dry run of the whole flow on a second, different local app. A small one is fine (e.g. another static site written for it). Log what breaks.
  - The weakest point is likely the matching thresholds (ADR-024).
- **No real model output yet.** The flow was never run with Gemini. Real plans may cite more element kinds, longer evidence, or loosen checks differently from the offline example. The guard should catch that, but the prompts are untested on a real model. Do TC-111 early.
- **The walkthrough is the demo script.** `ui_walkthrough.py` runs the whole demo, so keep it working after every task. Its `--record` mode makes the video (needs `xvfb-run` + ffmpeg).
- **Timing:** each walkthrough is ~60 s headless. The recorded demo with a visible browser and `GATP_RUNNER_SLOW_MO_MS` will be several minutes; check the brief's length limit.

## Technical debt (known, deliberately deferred)
- `rescans` / `change_sets` are protected by the ORM guard only. Snapshots and versions also have SQLite triggers; add triggers for these two in T-017's migration.
- Live progress during a run is start/finish only (SSE). There is no per-test streaming.
- The runner runs one job at a time, so a long test run blocks inspections (documented in SG-006).
- The weakening guard ignores changes to test **steps**; they still need re-approval (ADR-023, SG-006).
- The frontend bundle is over 500 kB (Vite warning). Code-split per page if load time matters.
- CI actions (`actions/checkout@v4`, `setup-node@v4`, `cache@v4`, `setup-uv@v6`) run on deprecated Node 20, and GitHub already forces Node 24. Bump them before they stop working.
- Starlette prints a deprecation warning for `httpx` in TestClient; `httpx2` isn't installable here.
- `process` isolation (fallback without bubblewrap) can read GATP's data. It is only for machines without bwrap; every run records which isolation it used.

## Lessons from this session (keep doing these)
- **Verify on the real system, not just unit tests.** Every task's real run or screenshot review found at least one bug the tests did not, for example:
  - setup steps were missing in the generated page objects;
  - pytest picked up GATP's own config inside the sandbox;
  - CI couldn't find the browser in the sandbox;
  - the model's notes were invisible;
  - the add page couldn't be compared after the sign-in change.
- **Write probes before building on a sandbox or external tool.** E.g. a test that tries to read the DB from inside bwrap. They proved isolation instead of assuming it.
- **Keep the model out of deterministic decisions.** Codegen, matching and gate checks are plain code. The model proposes plans and explains. That keeps runs reproducible and gives each decision an explanation for the defense.
- **One PR per task, docs in the same PR.** ADR + PLAN + task doc (Verification, Explain it) + TC row. The owners prepare for the code defense from those task docs.

## How to resume quickly
- **State:** `main` has T-003…T-015 merged. T-016 is on PR / the session branch.
- **Checks:**
  - `uv run poe check` (≈ 140 tests, ~2 min);
  - `uv run poe smoke`;
  - `cd scripts && uv run python ui_walkthrough.py --out <dir>`, which produces screens 01–19 (~60 s). Review the screenshots, since that has found real bugs every task.
- **Demo order the walkthrough already follows:** inspect (with sign-in setup) → scope G0 → plan G1 (clarifications) → code G2 (an invented locator is caught) → G3 run (real failures) → feedback → weakened checks flagged → rerun passes → site v2 → rescan flags. T-017 continues from screen 19.
- **Fixture switch:** tests use `site_switchable.switch("v2")`. The harness uses `Harness.switch_site("v2")`. Humans restart `uv run poe fixtures v2` on the same port.

## Notes for next session
- In this cloud container, Python Playwright needs `GATP_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (the preinstalled revision differs from the one the pinned Playwright expects).
- Docker: start `dockerd` manually if you need it (TC-102 reruns).
- uv in this container: `export UV_SYSTEM_CERTS=1; unset UV_NATIVE_TLS`.
- **CI differs from the cloud container.** CI runs as a non-root user with Playwright's own browsers and **no** `GATP_CHROMIUM_EXECUTABLE`. Env-related bugs show up only there; T-014's sandbox HOME bug was one. Keep run assertions printing the failure detail.
- **The offline (`fake`) provider drives every demo.** Its plan uses assumption checks that fail for real on v1 (empty error regions), and its revision drops failing checks (labelled). Both are intentional for TC-206/TC-207.
