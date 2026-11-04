"""TC-103: v1 and v2 differ in exactly the documented ways (fixtures/README.md, FXC-1…FXC-3)."""

import difflib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
V1 = REPO_ROOT / "fixtures" / "site-v1"
V2 = REPO_ROOT / "fixtures" / "site-v2"

FOOTER = (
    "    <footer>BookShelf fixture site · v1</footer>",
    "    <footer>BookShelf fixture site · v2</footer>",
)
# file -> (removed lines, added lines). Keep in sync with fixtures/README.md.
EXPECTED: dict[str, tuple[list[str], list[str]]] = {
    "index.html": (  # FXC-1 + FXC-3
        ['        <button type="submit" data-testid="login-submit">Sign in</button>', FOOTER[0]],
        ['        <button type="submit" data-testid="login-button">Log in</button>', FOOTER[1]],
    ),
    "add.html": (  # FXC-2 + FXC-3
        ['        <button type="submit" data-testid="save-book">Save</button>', FOOTER[0]],
        [
            '        <button type="submit" data-testid="save-draft" data-draft="true" '
            'class="secondary">Save draft</button>',
            '        <button type="submit" data-testid="publish-book">Publish</button>',
            FOOTER[1],
        ],
    ),
    "books.html": ([FOOTER[0]], [FOOTER[1]]),  # FXC-3
}


def _changes(a: Path, b: Path) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []
    diff = difflib.unified_diff(a.read_text().splitlines(), b.read_text().splitlines(), n=0)
    for line in diff:
        if line.startswith(("---", "+++", "@@")):
            continue
        (removed if line.startswith("-") else added).append(line[1:])
    return removed, added


def test_same_file_set() -> None:
    names_v1 = sorted(p.name for p in V1.iterdir())
    names_v2 = sorted(p.name for p in V2.iterdir())
    assert names_v1 == names_v2


def test_only_documented_changes() -> None:
    actual = {}
    for f in sorted(V1.iterdir()):
        removed, added = _changes(f, V2 / f.name)
        if removed or added:
            actual[f.name] = (removed, added)
    assert actual == EXPECTED
