# ADR-006: Locator candidates and ranking

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P1-2, REQ-P2-2, REQ-Q1; modules inspector, codegen

## Context
Locators must be grounded in observed elements and validated, including uniqueness for single-element actions.

## Decision
- For each interactive element, the inspector generates candidate locators in **Playwright's recommended priority**:
  1. `get_by_role(role, name=...)`
  2. `get_by_label(...)`
  3. `get_by_test_id(...)`
  4. `get_by_placeholder(...)` / `get_by_text(...)`
  5. CSS (stable attributes preferred; positional CSS last)
- Each candidate is **counted on the live page**. A candidate is `usable` for a single-element action only if `count == 1`.
- The highest-ranked usable candidate is the default; all candidates and counts are stored as evidence.
- Elements with no unique candidate are flagged; the tester is asked for clarification before they are used in tests.
- The LLM never invents locators; codegen may only use locators present in the snapshot.

## Alternatives considered
| Option | Why not |
|---|---|
| LLM picks locators | Less grounded; brief stresses evidence |

## Consequences
- Codegen's locator verification is a lookup against the snapshot + a recount before execution.
- Locator candidates also feed the maintenance fingerprint.
