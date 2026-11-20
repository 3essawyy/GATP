# PLAN-014: Approved execution (for T-014)

- **Task:** [T-014](../tasks/T-014-execution.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Implement [ADR-022](../architectureDecisionRecords/ADR-022-approved-execution-sandbox.md): G3 approves an exact subject, the runner's `run_tests` job runs pytest in a bubblewrap sandbox with an allowlist plugin, results come from junit and screenshots, and a Run page shows them. Verify on the real runner first with probe tests (secrets hidden, repo read-only, external blocked, a deliberate failure).

## Steps
1. Runner: `RunTestsJob`, `gatp_run_plugin.py`, `execute.py` (bwrap prefix, pytest argv, junit + screenshot parsing), executor wiring, `GATP_RUNNER_ISOLATION`.
2. Store `runs.py`; API `run_service.py` (subject, single-use approval, execute), `/runs` routes, G3 subject check on approval, `run` workflow step.
3. UI `RunPage` (G3 subject screen, approve and run, results with messages, stack, screenshots).
4. Tests, smoke, walkthrough, CI bubblewrap + sysctl, SG-001 prerequisite.

## Tests to add
| Test | Proves |
|---|---|
| `test_runs.py` | G3 required, exact subject, single use; passing run with screenshot + timing; code edit after G3 refuses the run; **deliberately wrong expectation fails visibly** and the code is untouched |
| smoke step | Real G3 run over the runner socket in bwrap |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| GitHub Ubuntu 24.04 blocks unprivileged user namespaces | CI sets `kernel.apparmor_restrict_unprivileged_userns=0` |

## Deviations (filled after execution)
- **Found by probing the real runner:** pytest picked up GATP's own `pyproject.toml` when the sandbox lived inside the repo, which also affected `collect`. Every sandbox now gets its own `pytest.ini` + `--rootdir`.
- **Fixed during the probe runs:** the `/work` mount (read-only root) and screenshot matching (hyphenated folder names).
