# T-016: Rescan + snapshot diff + change flags

- **Status:** Done (merged in #16)
- **Phase:** P2
- **Target:** W+5
- **Modules:** maintainer, api, store, runner, web-ui
- **Requirements:** REQ-P2-4, REQ-G8
- **Depends on:** T-007, T-014
- **Plan:** [PLAN-016](../implementationPlans/PLAN-016-rescan-diff.md)
- **ADRs:** [ADR-024](../decisions/ADR-024-rescan-matching-rules.md) (refines ADR-007)
- **TCs:** TC-208 Pass
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
On user request, re-inspect the page and flag what changed relative to the snapshot the tests were built on (ADR-007).

## Acceptance criteria
- [x] Fixture v1→v2: the clear change (FXC-1) is classified as a clear match; the ambiguous change (FXC-2) is classified ambiguous
- [x] Unit tests for scoring on synthetic fingerprints

## Verification (real system)
- **Tuning experiment** on real v1 and v2 inspections (same port, setup steps): sign-in 0.85 → clear; Save → Save draft 0.81 / Publish 0.69 → ambiguous; all other elements unchanged.
- **Tests:** `test_maintain.py` (3), against the real fixture switched v1 → v2 on the same origin.
- **UI walkthrough screen 19**, after the T-015 rerun:
  1. The site is restarted as v2 and the tester clicks Rescan.
  2. The setup alert explains the read-only retry.
  3. index.html shows 1 clear match (Sign in → Log in) with the per-field table.
  4. add.html shows 1 ambiguous (Save; candidates Save draft 0.81 and Publish 0.69).
  5. Both pages show "page HTML changed" (FXC-3).
  6. The step shows "needs approval".
- **Found and fixed:**
  - Without the retry, the add page could not be compared at all.
  - Locators were displayed in normalised single-quote form.

## Explain it (code-defense prep)
**What.** "Rescan pages" inspects every approved page again and compares each element the tests use with the snapshot the tests were generated from. Each used element is marked unchanged, changed with a clear match, ambiguous, or missing, together with the evidence: candidate elements, their scores and a field-by-field before/after table.

**Why.** REQ-P2-4: after the site changes, the assistant must flag what changed and prepare evidence-backed repairs, and ask when unsure. Doing the matching deterministically means the same pages always give the same answer, and every decision can be explained field by field (ADR-007).

**How it works:**
1. **Baseline:** the snapshots referenced by the approved scope. **Used elements:** plan steps and expectations, plus setup-step locators.
2. **New snapshots:** each page is inspected again; snapshots are immutable, so old evidence is never overwritten.
3. **Unchanged:** if the old default locator is still a unique, verified locator in the new snapshot.
4. **Scoring:** the remaining old elements are scored against elements that appeared, with a weighted fingerprint similarity (role, name, test id, form, position, …).
5. **Classification:**
   - **clear** needs score ≥ 0.70, a margin ≥ 0.15 and no "split" (several new elements of the same role in the same form);
   - otherwise **ambiguous** if any candidate is ≥ 0.45, else **missing**.
6. **Setup retry:** if a setup step broke on an element with a clear match, the page is inspected once more, read-only, with the proposed locator, and the UI says so.
7. **Storage:** a rescan row plus per-page change sets. The `maintain` step shows needs approval.

**Likely examiner questions:**
- *Why not let the model match elements?* It isn't reproducible and can't show evidence. The model will only explain (T-017).
- *Why is Save ambiguous although Save draft scores higher?* One button became two in the same form. Picking one would decide the test's intent (draft vs publish), and that is the tester's call. The margin is also below 0.15.
- *Did the rescan change my setup steps?* No. The retry is read-only and labelled; changing steps or code needs G4.
- *What about the footer text change?* It is reported as "page HTML changed" (low impact). Footer text is not an element the tests use.
- *Will the thresholds work on another site?* They were tuned on the fixture and are constants; SG-006 lists retuning as a known limitation.
