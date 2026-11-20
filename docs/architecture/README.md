# Architecture

| File | What | Status |
|---|---|---|
| [HLD.md](HLD.md) | High-level design: components, data flow, approval gates, validation, data model, security, resources | v0.2 |
| [GATP-system-design.drawio](GATP-system-design.drawio) | Editable draw.io diagram: components, data flow, gates, validation, resources, inspection → maintenance path (from HLD §2–§9) | v0.2 |

Rules:
- The HLD describes the system as it **is** on `main`. Planned-but-unbuilt parts are marked *(planned)*.
- Any change to components, flows or gates needs a matching ADR in [../architectureDecisionRecords/](../architectureDecisionRecords/README.md).
- The Phase 1 design-document deliverable is produced from this HLD (task T-011).
