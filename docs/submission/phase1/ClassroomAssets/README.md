# Classroom assets (Phase 1)

Files staged for the Classroom hand-in. The demo video is a Drive link and is not stored here.

| File | What | How it was made |
|---|---|---|
| `GATP-system-design.png` | System design: components, data flow, approval gates, validation, resources, inspection → maintenance path | Exported from [`docs/architecture/GATP-system-design.drawio`](../../../architecture/GATP-system-design.drawio): `draw.io -x -f png -s 2 -b 20 -o GATP-system-design.png GATP-system-design.drawio` |
| `GATP-phase1-source.zip` | Runnable source, dependencies and setup docs at tag `phase1` (no `.env`, `.venv` or `node_modules`) | `git archive --format=zip --prefix=GATP/ -o GATP-phase1-source.zip phase1` |
| `usage-evidence.json` | Model usage and timing evidence: real Gemini run (`gemini-3.5-flash`, 2,433 in / 1,437 out tokens, 69.3 s, then `reused`) | Copy of [`../usage-evidence.json`](../usage-evidence.json) |

Not included by choice: the design PDF (`../GATP-phase1-design.pdf`) and the sample inspection JSON (`docs/samples/`). Add them if the hand-in needs them.
