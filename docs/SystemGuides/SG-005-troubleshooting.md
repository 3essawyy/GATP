# SG-005: Troubleshooting

- **Audience:** tester, developer
- **Last verified:** 2026-11-04

Troubleshooting tables live next to the step they belong to:

| Problem area | Where |
|---|---|
| Installing, starting api/runner/web/fixtures, ports, Chromium, WSL, `xvfb-run` | [SG-001 § Troubleshooting](SG-001-setup-and-run.md#troubleshooting) |
| Gemini key, Ollama, rate limits, invalid model output | [SG-003 § Troubleshooting](SG-003-models.md#troubleshooting) |
| During a demo | [SG-004 § If something goes wrong](SG-004-demo-script.md#if-something-goes-wrong) |
| Starting or resetting the whole stack from Windows (launcher, stale processes, empty database) | [SG-004 § One-command start](SG-004-demo-script.md#one-command-start-windows--wsl) |
| Tests, CI, generated client out of date, migrations | [SG-002](SG-002-developer-workflow.md) |

When a check fails, run the real-system checks to localise the problem: `uv run poe smoke` (API + runner + fixture site) and `uv run poe ui-walkthrough` (UI). Both keep their logs and screenshots on failure.
