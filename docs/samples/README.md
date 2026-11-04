# Samples (submission evidence)

Real outputs produced by GATP and committed as evidence for the phase submissions (REQ-P1-S, REQ-P2-S).

| File | What | Produced by |
|---|---|---|
| [inspection-bookshelf-v1-login.json](inspection-bookshelf-v1-login.json) (+ `.png`) | Structured inspection of the BookShelf v1 sign-in page | Runner `inspect` job, T-007, 2026-11-04 |
| [inspection-bookshelf-v1-add-book.json](inspection-bookshelf-v1-add-book.json) (+ `.png`) | Inspection of the add-book form, reached via sign-in setup steps | Runner `inspect` job, T-007, 2026-11-04 |
| [phase1-walkthrough/](phase1-walkthrough/) | Screenshots of the real UI through the Phase 1 flow (create project → inspect → source line → setup steps → inspect add-book → scope → G0) | `uv run poe ui-walkthrough`, T-009, 2026-11-04 |
| [phase2-walkthrough/](phase2-walkthrough/) | Real UI, Phase 2 steps as they are built (T-012: plan proposed → clarifications → G1 → edit needs re-approval) | `uv run poe ui-walkthrough`, 2026-11-04 |
