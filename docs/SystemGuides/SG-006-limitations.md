# SG-006: Limitations

- **Audience:** examiner, tester
- **Last verified:** 2026-11-04 (Phase 1, T-011). Updated again for Phase 2 in T-021.

Known limits of GATP, stated plainly. Each links to where it is decided or documented.

| Area | Limitation | Why / mitigation | Reference |
|---|---|---|---|
| Models | Committed evidence uses the offline `fake` provider; the real Gemini run happens on the team machine with a free key | No key in the build environment; `poe llm-check` verifies the setup; the UI labels fake answers | [SG-003 §6](SG-003-models.md), [ADR-016](../decisions/ADR-016-llm-gateway-design.md) |
| Models | Free-tier rate limits; the Ollama fallback (3B model on CPU) gives weaker answers | Backoff, fallback and cache (`reused`); invalid answers are rejected, never used | [ADR-003](../decisions/ADR-003-llm-providers.md) |
| Tokens | Ollama/fake token counts may be estimates (~4 chars/token) | Labelled "estimated" everywhere | [ADR-016](../decisions/ADR-016-llm-gateway-design.md) |
| Isolation | The runner is a separate OS process (private socket, sandbox dir, origin allowlist). Approved tests run inside bubblewrap (read-only system, secrets hidden), but as the same OS user and without a network namespace | bwrap + allowlist routing + static bans; Docker was not chosen, to keep the visible browser simple | [ADR-004](../decisions/ADR-004-runner-isolation.md), [ADR-022](../decisions/ADR-022-approved-execution-sandbox.md) |
| Inspection | Shadow DOM and iframes are not traversed; elements appearing only after interaction need setup steps | Documented; setup steps can open menus or dialogs first | [inspector LLD](../modules/inspector/README.md) |
| Inspection | Accessible names are computed approximately | Every locator is verified live, so a wrong name gives an *unusable* candidate, never a wrong one | [ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md) |
| Setup steps | Values (e.g. test passwords) are stored in the local DB and shown in the editor | Use test accounts only; the DB is local and gitignored | [ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md) |
| Users | Single local user, no login; the server binds to 127.0.0.1; approver names are self-declared | Local tool by design (S004) | [api LLD](../modules/api/README.md) |
| Platform | Linux / WSL2 only | Team decision | [ADR-014](../decisions/ADR-014-linux-only-platform.md) |
| Concurrency | One runner job at a time | One visible browser for the human to follow | [runner LLD](../modules/runner/README.md) |
| Weakening guard | Covers expected results, whole cases and test-file assertions/skips; changes to test **steps** are not classified as weakening (they still need G1) | Every new version needs re-approval anyway | [ADR-023](../decisions/ADR-023-feedback-and-weakening-guard.md) |
