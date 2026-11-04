# Session S003 — 2026-11-04 — Linux migration + TC-102 clean-machine run

- **Tasks touched:** T-002 (follow-up)
- **Branches / PRs:** `claude/serene-johnson-xtbl4s` → PR to `main` (squash)

## Done
- Abdo decided the team **migrates to Linux** (Windows users → WSL2), recorded as [ADR-014](../decisions/ADR-014-linux-only-platform.md). ADR-012 is marked as partially superseded (platform assumption only).
- Rewrote [SG-001](../SystemGuides/SG-001-setup-and-run.md) for Linux:
  - apt base packages.
  - uv via the official script *or* pipx.
  - Node 22 via nvm.
  - `poe browsers` now installs Chromium's system libraries too (`--with-deps`).
- Ran **TC-102** in a clean `ubuntu:24.04` container as a non-root sudo user, following SG-001 literally. api, runner and frontend pass, and the UI shows "API ok". See the [run log](../TCs/TC-102-runs.md). No undocumented steps were found.
- Pushing the follow-up hit a rejected push (the old session-branch tip from PR #1 was still on the remote) and a denied force-push. I resolved it by merging the old tip, which has identical content to `main`, so no history was rewritten.

## Decisions (with ADR links)
| Topic | Decision | ADR |
|---|---|---|
| Platform | Linux only (Ubuntu 24.04 reference, WSL2 for Windows users); bash/Linux tools allowed | ADR-014 |

## Open items / blockers
- **TC-102:** the full Pass needs the fixture-site section (T-003). The Chromium download step and the astral.sh uv installer can't be exercised in this sandbox (blocked hosts); CI covers the Chromium step.
- Still open from S001/S002: component owners, W9/W13 dates, demo GPU, branch protection, npm dev advisories, httpx2.

## Next steps (in order)
1. Finish the "complete the project" interview (autonomy, LLM access in dev, bonus, plus per-task decisions).
2. **T-003** Fixture site v1/v2.

## Notes for next session
- To rerun TC-102: start `dockerd` in the cloud container, then run `ubuntu:24.04` with `--network host` plus the proxy/CA environment listed in the run log.
