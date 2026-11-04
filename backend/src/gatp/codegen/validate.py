"""Static validation of generated (or tester-edited) test code before G2 (T-013, ADR-008).

1. ``ast.parse`` every file.
2. Every Playwright locator call in a page object must equal a verified snapshot locator.
3. Tests must not build locators themselves (only page objects may).
4. Only harmless imports and calls: generated tests never need the OS, network or eval.
Runtime checks (live recount, ``pytest --collect-only``) run in the runner afterwards.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

LOCATOR_METHODS = {
    "get_by_role",
    "get_by_label",
    "get_by_test_id",
    "get_by_placeholder",
    "get_by_text",
    "get_by_alt_text",
    "get_by_title",
    "locator",
}
ALLOWED_IMPORTS = {"re", "os", "pytest", "playwright.sync_api", "pages"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__", "input", "breakpoint"}
FORBIDDEN_ATTRS = {"system", "popen", "spawn", "remove", "unlink", "rmtree", "evaluate", "route"}
ALLOWED_OS = {"environ"}


@dataclass
class Finding:
    file: str
    line: int
    check: str  # syntax | locator | structure | safety
    message: str


@dataclass
class StaticReport:
    findings: list[Finding] = field(default_factory=list)
    locators: list[str] = field(default_factory=list)  # normalised expressions found

    @property
    def ok(self) -> bool:
        return not self.findings


def normalise(expression: str) -> str:
    """Canonical source form of an expression (quotes, spacing) for comparison."""
    return ast.unparse(ast.parse(expression, mode="eval").body)


def validate(files: dict[str, str], allowed_locators: set[str]) -> StaticReport:
    """``files``: path -> content. ``allowed_locators``: verified expressions on ``page``."""
    report = StaticReport()
    allowed = {normalise(a) for a in allowed_locators}
    for path, content in sorted(files.items()):
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as exc:
            report.findings.append(Finding(path, exc.lineno or 0, "syntax", exc.msg))
            continue
        is_page_object = path.startswith("pages/")
        for node in ast.walk(tree):
            _check_imports(path, node, report)
            _check_safety(path, node, report)
            if isinstance(node, ast.Call) and _is_locator_call(node):
                expr = ast.unparse(node)
                if not is_page_object:
                    report.findings.append(
                        Finding(
                            path,
                            node.lineno,
                            "structure",
                            f"tests must use page objects, not {expr}",
                        )
                    )
                    continue
                report.locators.append(expr)
                if expr not in allowed:
                    report.findings.append(
                        Finding(
                            path,
                            node.lineno,
                            "locator",
                            f"{expr} is not a verified locator from the inspection snapshot",
                        )
                    )
    return report


def _is_locator_call(node: ast.Call) -> bool:
    """``page.get_by_*(...)`` / ``page.locator(...)`` directly on the ``page`` object."""
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in LOCATOR_METHODS
        and isinstance(func.value, ast.Name)
        and func.value.id == "page"
    )


def _check_imports(path: str, node: ast.AST, report: StaticReport) -> None:
    modules: list[str] = []
    if isinstance(node, ast.Import):
        modules = [a.name for a in node.names]
    elif isinstance(node, ast.ImportFrom):
        modules = [node.module or ""]
    for module in modules:
        root = module.split(".")[0]
        if (
            module not in ALLOWED_IMPORTS
            and root not in ALLOWED_IMPORTS - {"playwright"}
            and not (module.startswith("playwright.sync_api") or module.startswith("pages"))
        ):
            report.findings.append(
                Finding(
                    path,
                    getattr(node, "lineno", 0),
                    "safety",
                    f"import of {module!r} is not allowed",
                )
            )


def _check_safety(path: str, node: ast.AST, report: StaticReport) -> None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in FORBIDDEN_CALLS
    ):
        report.findings.append(
            Finding(path, node.lineno, "safety", f"call to {node.func.id}() is not allowed")
        )
    if isinstance(node, ast.Attribute):
        if node.attr in FORBIDDEN_ATTRS:
            report.findings.append(
                Finding(path, node.lineno, "safety", f".{node.attr} is not allowed")
            )
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "os"
            and node.attr not in ALLOWED_OS
        ):
            report.findings.append(
                Finding(path, node.lineno, "safety", f"os.{node.attr} is not allowed")
            )
