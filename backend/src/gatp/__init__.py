"""GATP: human-in-the-loop web testing assistant.

One sub-package per module (see docs/modules/README.md). Dependency direction is
enforced by import-linter contracts in pyproject.toml.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gatp")
except PackageNotFoundError:  # pragma: no cover - only when running from a raw checkout
    __version__ = "0.0.0"
