"""Build the static GitHub Pages showcase.

    python -m tools.build_pages [--out docs/site]

Freezes the teaching pages — which need no server — into plain HTML: the formulary, drug
monographs, product SmPC pages, interactions, resistance primer, regimens, quiz and the
life-cycle diagram. Pages that need the engine (the assessment form, calculators, planners and
the resistance explorer) are replaced by a page explaining that they need the running app, with
a link to Codespaces.

Drug monographs and product pages are deliberately withheld: they reproduce SmPC text, which is the
copyright of the marketing authorisation holders and is not republished by this project.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from art_cds import create_app  # noqa: E402
from art_cds.config import Config  # noqa: E402
from art_cds.knowledge.cases import CASES  # noqa: E402
from art_cds.knowledge.drugs import CLASSES, DRUGS  # noqa: E402
from art_cds.knowledge.quiz import QUESTIONS  # noqa: E402

# Routes that cannot work without the Flask app behind them
DYNAMIC = ("/assess", "/calculators", "/long-acting", "/perinatal", "/explore", "/api")

# Pages that reproduce SmPC or guideline text verbatim. They are deliberately NOT published:
# that text is the copyright of the marketing authorisation holders and BHIVA, and this site is
# public. They are available in the running application, which reads your own downloaded copies.
WITHHELD = ("/learn/product/", "/learn/drug/")

NEEDS_APP = """<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Needs the running app · ART Navigator UK</title><link rel="stylesheet" href="{root}static/css/app.css"></head>
<body><main><div class="wrap" style="padding-top:40px">
<div class="card" style="max-width:640px;margin:0 auto">
<h1>This part needs the application running</h1>
<p>Two kinds of page are missing from this static showcase:</p>
<ul>
<li><b>The decision engine, calculators, planners and the resistance explorer</b> work out their answers on a
server, so they cannot be part of a static site.</li>
<li><b>Drug monographs and product pages</b> reproduce the UK Summary of Product Characteristics, which is the
copyright of the marketing authorisation holders. They are not republished here; the application builds them from
the copy you download yourself.</li>
</ul>
<p>Run it in your browser with <b>GitHub Codespaces</b> (Code → Codespaces → Create codespace), or locally:</p>
<pre class="mono" style="background:var(--surface-2);padding:12px;border-radius:8px">git clone https://github.com/{repo}.git
cd hiv-art-cds
python3 -m venv .venv &amp;&amp; .venv/bin/pip install -r requirements.txt
.venv/bin/python -m tools.fetch_guidelines
.venv/bin/python -m tools.fetch_smpc
.venv/bin/python run.py</pre>
<p><a class="btn" href="{root}index.html">← Back to the showcase</a>
<a class="btn ghost" href="https://github.com/{repo}">View on GitHub</a></p>
</div></div></main></body></html>
"""


def static_pages() -> List[str]:
    pages = ["/", "/learn/", "/learn/formulary", "/learn/regimens", "/learn/interactions", "/learn/resistance",
             "/learn/cases", "/learn/about", "/learn/governance", "/quiz/"]
    pages += [f"/learn/class/{code}" for code in CLASSES]
    pages += [f"/quiz/{q.id}" for q in QUESTIONS]
    pages += [f"/quiz/{q.id}?a={q.answer}" for q in QUESTIONS]
    return pages


def local_name(url: str) -> str:
    path, _, query = url.partition("?")
    name = path.strip("/") or "index"
    if query:
        name += "__" + re.sub(r"[^a-zA-Z0-9]+", "-", query)
    return f"{name}.html" if not name.endswith(".html") else name


def rewrite(html: str, depth: int, repo: str) -> str:
    root = "../" * depth or "./"

    def fix(match: re.Match) -> str:
        href = match.group(2)
        if href.startswith("/static/"):
            return f'{match.group(1)}="{root}{href[1:]}"'
        if any(href.startswith(d) for d in DYNAMIC + WITHHELD):
            return f'{match.group(1)}="{root}needs-the-app.html"'
        return f'{match.group(1)}="{root}{local_name(href)}"'

    html = re.sub(r'(href|src)="(/[^"]*)"', fix, html)
    banner = ('<div class="banner"><b>Static showcase.</b> This is a read-only copy of the teaching pages. '
              f'The decision engine and tools need the running application — see '
              f'<a href="https://github.com/{repo}">the repository</a>.</div>')
    return html.replace('<div class="wrap">\n      ', '<div class="wrap">\n      ' + banner, 1)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/site")
    ap.add_argument("--repo", default="gsumathipala/hiv-art-cds")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    app = create_app(Config)
    app.config["AUDIT"] = False
    client = app.test_client()
    written: Dict[str, int] = {}
    for url in static_pages():
        response = client.get(url)
        if response.status_code != 200:
            print(f"skip {url} ({response.status_code})")
            continue
        name = local_name(url)
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        depth = name.count("/")
        target.write_text(rewrite(response.get_data(as_text=True), depth, args.repo), encoding="utf-8")
        written[name] = len(response.data)

    (out / "needs-the-app.html").write_text(NEEDS_APP.format(root="./", repo=args.repo), encoding="utf-8")
    shutil.copytree(ROOT / "art_cds" / "static", out / "static")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    print(f"{len(written) + 1} pages written to {out}")
    print("note: drug and product pages are withheld from the static site (third-party SmPC text)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
