"""Build a submission PDF from repository Markdown (``uv run poe pdf``).

Markdown -> HTML with pandoc, Mermaid diagrams rendered by mermaid.js in Chromium, then printed
to PDF by Playwright. Relative links become GitHub links; local images are embedded.

    uv run poe pdf -- --out docs/submission/phase1/GATP-phase1-design.pdf \
        docs/submission/phase1/README.md docs/architecture/HLD.md

Requires: pandoc (apt install pandoc) and ``npm --prefix scripts/pdf ci`` (Mermaid).
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/3essawyy/GATP/blob/main/"
MERMAID = ROOT / "scripts" / "pdf" / "node_modules" / "mermaid" / "dist" / "mermaid.min.js"

CSS = """
body { font-family: 'Segoe UI', system-ui, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1f2933; }
h1 { font-size: 20pt; border-bottom: 2px solid #2f5d50; padding-bottom: 4px; page-break-before: always; }
section.doc:first-of-type h1 { page-break-before: avoid; }
h2 { font-size: 14pt; color: #2f5d50; margin-top: 18px; }
h3 { font-size: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9pt; page-break-inside: auto; }
th, td { border: 1px solid #d0d7de; padding: 3px 6px; vertical-align: top; text-align: left; }
th { background: #f0f4f2; }
tr { page-break-inside: avoid; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; background: #f4f4f2; padding: 0 2px; }
pre { background: #f4f4f2; padding: 8px; overflow-wrap: anywhere; white-space: pre-wrap; font-size: 8.5pt; }
pre.mermaid { background: white; text-align: center; page-break-inside: avoid; }
pre.mermaid svg { max-width: 100% !important; max-height: 235mm; width: auto; height: auto; }
img { max-width: 100%; border: 1px solid #d0d7de; }
a { color: #1a5fb4; text-decoration: none; }
"""


def md_to_html(path: Path) -> str:
    out = subprocess.run(
        ["pandoc", "--from=gfm", "--to=html5", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    # Mermaid wants the raw diagram text directly inside <pre class="mermaid">.
    out = re.sub(
        r'<pre class="mermaid"><code>(.*?)</code></pre>',
        lambda m: f'<pre class="mermaid">{m.group(1)}</pre>',
        out,
        flags=re.S,
    )

    def fix(match: re.Match[str]) -> str:
        attr, target = match.group(1), html.unescape(match.group(2))
        if re.match(r"^[a-z]+:|^#", target):
            return match.group(0)
        resolved = (path.parent / target.split("#")[0]).resolve()
        if attr == "src":
            return f'src="{resolved.as_uri()}"'
        anchor = "#" + target.split("#", 1)[1] if "#" in target else ""
        try:
            rel = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)
        return f'href="{GITHUB}{rel}{anchor}"'

    return re.sub(r'(href|src)="([^"]+)"', fix, out)


def build(sources: list[Path], out: Path, title: str) -> None:
    body = "\n".join(f'<section class="doc">{md_to_html(p)}</section>' for p in sources)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{CSS}</style><script src="{MERMAID.as_uri()}"></script></head><body>{body}
<script>
mermaid.initialize({{ startOnLoad: false, theme: 'neutral', flowchart: {{ htmlLabels: true }} }});
mermaid.run({{ querySelector: 'pre.mermaid' }}).then(() => {{ window.__done = true; }})
  .catch((e) => {{ window.__done = 'error: ' + e; }});
</script></body></html>"""
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "doc.html"
        html_path.write_text(page, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=os.environ.get("GATP_CHROMIUM_EXECUTABLE") or None
            )
            tab = browser.new_page()
            tab.goto(html_path.as_uri())
            tab.wait_for_function("window.__done !== undefined", timeout=60_000)
            status = tab.evaluate("window.__done")
            if status is not True:
                raise RuntimeError(f"mermaid failed: {status}")
            out.parent.mkdir(parents=True, exist_ok=True)
            tab.pdf(
                path=str(out),
                format="A4",
                print_background=True,
                margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=(
                    f'<div style="font-size:8px;width:100%;text-align:center;color:#888">'
                    f'{html.escape(title)} · page <span class="pageNumber"></span>/<span class="totalPages"></span></div>'
                ),
            )
            browser.close()
    print(f"wrote {out} ({out.stat().st_size // 1024} kB)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="GATP")
    parser.add_argument("sources", type=Path, nargs="+")
    args = parser.parse_args()
    if not MERMAID.exists():
        print("missing Mermaid: run `npm --prefix scripts/pdf ci` first")
        return 2
    build([s.resolve() for s in args.sources], args.out.resolve(), args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
