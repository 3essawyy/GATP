# ADR-014: Linux-only platform for development, demo and examiners

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S003
- **Related:** REQ-P1-S, REQ-P2-6, TC-102, SG-001; supersedes the native-Windows assumption in [ADR-012](ADR-012-backend-and-dev-tooling.md)

## Context
ADR-012 assumed some team members would use native Windows, so every command had to work without bash or Make, and TC-102 needed a Windows run that the cloud development environment can't perform. Abdo decided that the team migrates to Linux.

## Decision
- GATP officially supports **Linux only**: Ubuntu 24.04 is the reference, and Windows users run it inside **WSL2 Ubuntu** (WSLg shows the headed browser).
- The demo machine runs Linux (or WSL2).
- [SG-001](../SystemGuides/SG-001-setup-and-run.md) is written for Linux. TC-102 is verified in a **clean `ubuntu:24.04` container**, following SG-001 literally as a non-root user with sudo.
- The tooling from ADR-012 stays as it is (uv, poethepoet, ruff, mypy, pytest). poe tasks still work and keep a single entry point. Bash scripts and Linux-only tools (e.g. Xvfb, `playwright install --with-deps`, Docker) are now allowed where they help.
- CI stays on ubuntu-latest, which now matches the target platform exactly.

## Alternatives considered
| Option | Why not |
|---|---|
| Keep native Windows support | Can't be verified by Claude (no Windows host); costs portability work in the runner (signals, process groups, paths) |
| Whole app in Docker | Not chosen now; still possible later for the runner (ADR-004 keeps the interface Docker-ready) |

## Consequences
- TC-102 can be run end to end by Claude in a container, with no teammate dependency.
- The runner (T-006) can use POSIX features (process groups, `resource` limits, signals) for sandboxing.
- Teammates on Windows must install WSL2 once; SG-001 links to it.
