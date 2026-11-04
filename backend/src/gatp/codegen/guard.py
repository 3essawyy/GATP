"""Assertion-weakening guard for tester edits of test code (T-015, ADR-023).

Compares an edited test file with its last **approved** (G2) version, per test function:
- a test function that disappeared,
- an assertion (``expect(...)…`` or ``assert``) that is no longer there (removed or changed),
- a test that is now skipped or expected to fail (``pytest.mark.skip/xfail``, ``pytest.skip()``).
Each finding becomes a clarification that blocks G2 until the tester accepts it explicitly.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

SKIP_MARKERS = ("skip", "skipif", "xfail")


@dataclass(frozen=True)
class CodeWeakening:
    key: str  # e.g. "tests/test_plan.py::test_x:assert:expect(...).to_be_visible()"
    path: str
    test: str
    change: str  # test_removed | assertion_removed | skipped
    message: str


def _assertions(fn: ast.FunctionDef) -> list[str]:
    out = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            out.append(ast.unparse(node))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            root = node.value.func
            while isinstance(root, ast.Attribute | ast.Call):
                root = root.value if isinstance(root, ast.Attribute) else root.func
            if isinstance(root, ast.Name) and root.id == "expect":
                out.append(ast.unparse(node))
    return out


def _skipped(fn: ast.FunctionDef) -> bool:
    for deco in fn.decorator_list:
        text = ast.unparse(deco)
        if any(f"mark.{m}" in text for m in SKIP_MARKERS):
            return True
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            text = ast.unparse(node.func)
            if text in ("pytest.skip", "pytest.xfail"):
                return True
    return False


def _tests(content: str) -> dict[str, ast.FunctionDef] | None:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None
    return {
        n.name: n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")
    }


def code_weakenings(path: str, approved: str, edited: str) -> list[CodeWeakening]:
    """Findings for ``edited`` compared with the ``approved`` content of the same file."""
    before, after = _tests(approved), _tests(edited)
    if before is None or after is None:
        return []  # syntax errors are reported by static validation
    out: list[CodeWeakening] = []
    for name, fn in before.items():
        new = after.get(name)
        where = f"{path}::{name}"
        if new is None:
            out.append(
                CodeWeakening(f"{where}:removed", path, name, "test_removed", f"{name} was removed")
            )
            continue
        remaining = _assertions(new)
        for assertion in _assertions(fn):
            if assertion in remaining:
                remaining.remove(assertion)
                continue
            out.append(
                CodeWeakening(
                    f"{where}:assert:{assertion}",
                    path,
                    name,
                    "assertion_removed",
                    f"{name}: assertion removed or changed: {assertion}",
                )
            )
        if _skipped(new) and not _skipped(fn):
            out.append(
                CodeWeakening(
                    f"{where}:skipped", path, name, "skipped", f"{name} is now skipped / xfail"
                )
            )
    return out
