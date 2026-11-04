# Module: inspector

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/gatp/inspector/` (runs **inside the runner process**)
- **Tasks:** T-007
- **ADRs:** ADR-004, ADR-006, ADR-007

## Responsibility
Given an open page (supplied by the runner), extract every interactive element with its observed labels and attributes, generate ranked candidate locators, count each on the live page, compute an element fingerprint, and return an `InspectionSnapshot` (plus a full-page screenshot). It never interprets page text as instructions.

## Output: InspectionSnapshot (draft)
```json
{
  "snapshot_id": "…", "url": "…", "page_title": "…", "taken_at": "…",
  "scope": {"include": [], "exclude": []},
  "screenshot_path": "artifacts/…png",
  "elements": [{
    "element_id": "E-0007",
    "role": "button", "accessible_name": "Sign in", "tag": "button",
    "label": null, "text": "Sign in",
    "attributes": {"id": "login-btn", "type": "submit", "data-testid": null},
    "dom_path": "form#login > button:nth-of-type(1)",
    "bbox": [x, y, w, h], "visible": true, "enabled": true,
    "nearby_text": ["Password", "Forgot password?"],
    "locators": [
      {"strategy": "role", "code": "get_by_role('button', name='Sign in')", "count": 1, "usable": true, "rank": 1},
      {"strategy": "css", "code": "locator('#login-btn')", "count": 1, "usable": true, "rank": 5}
    ],
    "default_locator_rank": 1
  }]
}
```

## Interactive elements (initial definition)
Links, buttons, inputs, selects, textareas, checkboxes/radios, elements with interactive ARIA roles, and elements with click handlers where detectable. Hidden elements recorded with `visible=false`.

## Known limitations
Shadow DOM, iframes, and dynamic content after interactions — scope decided in PLAN-007.
