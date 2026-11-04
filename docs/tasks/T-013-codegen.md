# T-013: POM code generation + validation + review (G2)

- **Status:** Done
- **Phase:** P2
- **Target:** W+3
- **Modules:** codegen, runner, api, store, web-ui
- **Requirements:** REQ-P2-2, REQ-Q1, REQ-Q3
- **Depends on:** T-012
- **Plan:** [PLAN-013](../implementationPlans/PLAN-013-codegen.md)
- **ADRs:** [ADR-021](../decisions/ADR-021-deterministic-codegen.md)
- **TCs:** TC-203 Pass, TC-204 Pass
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
Executable pytest-playwright POM code from an approved plan, validated and reviewable (ADR-008, [codegen LLD](../modules/codegen/README.md)).

## Acceptance criteria
- [x] Generated code for fixture v1 passes all validation steps, **and the generated test really passes in a browser** on v1
- [x] An injected invented locator is caught and reported (static finding with file and line; G2 blocked)
- [x] Code versions linked to the plan version they came from (header + version reason)

## Verification (real system)
- **Real run of the generated test (new test):** it first **failed**, because the test reached `add.html` while signed out and was redirected. This led to replaying the page's setup steps in `open()`. Now it passes.
- **Collection bug:** the collect step caught a generator bug (imports derived from element ids). Fixed.
- **`poe smoke`:** new step "plan G1 → code → validate (runner) → G2" over the real runner socket.
- **`poe ui-walkthrough`:** generate → validation passed → G2 → editor injects `#made-up` → validation failed with the finding → G2 disabled. Evidence: [phase2-walkthrough 12–13](../samples/phase2-walkthrough/).
- **Fixes from reviewing the screenshots:**
  - the report states how many locators come from approved setup steps (sign-in);
  - the step status shows a file count instead of a long list;
  - the test file opens first;
  - generated comments name regions (`alert #title-error`).

## Explain it (code-defense prep)
**What.** From the G1-approved plan, GATP writes runnable pytest-playwright code in the Page Object pattern:
- **Page objects:** one class per page, holding verified locators and an `open()` that replays the page's approved setup steps.
- **Tests:** one test function per approved case, with every assertion traced to its expectation id and basis.

Before the tester can approve it (G2), the code is validated three ways, and the result is stored against the exact file versions.

**Why.** Generated tests must be executable, syntax-checked, locator-verified and reviewable (REQ-P2-2), and must reference only observed elements with unique locators (REQ-Q1). Rendering from structured data rather than letting the model write code makes invented locators impossible by construction. Validation then proves it, including against edits by humans.

**How it works:**
1. `generate()` refuses unless the latest plan version carries G1, and every cited element has a verified default locator.
2. `render()` maps each step (`fill` → `.fill(value)`, `click` → `.click()`, …) and each expectation kind (`text_equals` → `expect(x).to_have_text(v)`, `url_contains` → `expect(page).to_have_url(re.compile(...))`, …) to one line, using the page object attribute for the cited element.
3. `validate()` parses each file. It compares every locator call in the page objects (normalised by `ast.unparse`) with the allowed set: verified candidates plus approved setup-step locators. It flags locators created in tests and unsafe imports or calls.
4. The runner recounts each snapshot locator on the live page, after the page's setup steps, and runs `pytest --collect-only` in a fresh sandbox.
5. The report is stored with the version ids. G2 checks that a passing report covers the version.

**Likely examiner questions:**
- *Does the model write the code?* No. It proposed the plan, which the tester approved. The code is a deterministic rendering of that plan with verified locators.
- *What if a reviewer types in a made-up selector?* Static validation flags it with file and line, collection is skipped, and G2 stays blocked until it's fixed (shown in the walkthrough).
- *How do you know the code actually works?* Three ways. Validation recounts every locator live and collects the tests. A GATP test runs a generated test in a real browser and it passes. Execution itself comes with G3 in T-014.
- *Why does the page object sign in?* The page is protected. The tester approved those exact steps when inspecting it, so the test reuses them rather than inventing a login.
