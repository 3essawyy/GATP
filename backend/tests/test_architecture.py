"""Module dependency direction (docs/modules/README.md) is enforced by import-linter.

Runs in a subprocess: import-linter reconfigures logging (disabling existing loggers),
which would leak into other tests if called in-process.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = "from importlinter.cli import lint_imports; raise SystemExit(lint_imports(no_cache=True))"


def test_import_contracts_hold() -> None:
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-c", LINT],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
