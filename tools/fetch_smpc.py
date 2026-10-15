"""Download and parse UK SmPCs from emc (medicines.org.uk).

    python -m tools.fetch_smpc            # fetch every product not yet cached
    python -m tools.fetch_smpc dovato     # (re)fetch named products
    python -m tools.fetch_smpc --refresh  # re-fetch everything

Requests are spaced out (``--delay``, default 20 s). emc protects itself with a
human check; when it is served, the fetcher waits and retries a few times and
then stops — it never tries to get past it. Raw HTML is cached under
``.cache/emc`` so nothing is downloaded twice.

Each SmPC is written to ``art_cds/data/smpc/<key>.json`` as a list of sections,
each section a list of blocks (paragraph, heading, list or table), with the
emc URL and the SmPC's "date of revision of the text".
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from art_cds.knowledge.products import PRODUCTS, PRODUCTS_BY_KEY, Product  # noqa: E402

BASE = "https://www.medicines.org.uk"
CACHE = ROOT / ".cache" / "emc"
OUT = ROOT / "art_cds" / "data" / "smpc"
UA = "Mozilla/5.0 (ART-CDS SmPC reader; educational use)"

# emc's section anchors -> our keys and SmPC section numbers
SECTIONS = {
    "PRODUCTINFO": ("name", "1"),
    "COMPOSITION": ("composition", "2"),
    "FORM": ("form", "3"),
    "INDICATIONS": ("indications", "4.1"),
    "POSOLOGY": ("posology", "4.2"),
    "CONTRAINDICATIONS": ("contraindications", "4.3"),
    "CLINICAL_PRECAUTIONS": ("warnings", "4.4"),
    "INTERACTIONS": ("interactions", "4.5"),
    "PREGNANCY": ("pregnancy", "4.6"),
    "MACHINEOPS": ("driving", "4.7"),
    "UNDESIRABLE_EFFECTS": ("adverse_effects", "4.8"),
    "OVERDOSE": ("overdose", "4.9"),
    "PHARMACODYNAMIC_PROPS": ("pharmacodynamics", "5.1"),
    "PHARMACOKINETIC_PROPS": ("pharmacokinetics", "5.2"),
    "PRECLINICAL_SAFETY": ("preclinical", "5.3"),
    "EXCIPIENTS": ("excipients", "6.1"),
    "SHELF_LIFE": ("shelf_life", "6.3"),
    "STORAGE": ("storage", "6.4"),
    "PACKAGE": ("container", "6.5"),
    "ORIGINAL": ("ma_holder", "7"),
    "NUMBER": ("ma_number", "8"),
    "DOCREVISION": ("revision", "10"),
}


class BotCheck(RuntimeError):
    pass


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-GB"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    if "are you human" in text[:3000].lower():
        raise BotCheck(url)
    return text


def polite_get(url: str, cache_name: str, delay: float, retries: int = 4) -> str:
    path = CACHE / cache_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    wait = 120.0
    for attempt in range(retries + 1):
        time.sleep(delay)
        try:
            text = _get(url)
        except BotCheck:
            if attempt == retries:
                raise
            print(f"  emc human check — waiting {wait:.0f} s", flush=True)
            time.sleep(wait)
            wait *= 2
            continue
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text
    raise RuntimeError("unreachable")


# ---------------------------------------------------------------- HTML -> blocks
class _BlockParser(HTMLParser):
    """Flatten a section's HTML into paragraphs, headings, lists and tables."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: List[Dict] = []
        self._text: List[str] = []
        self._strong_only = True
        self._in_strong = 0
        self._table: Optional[List[List[str]]] = None
        self._row: Optional[List[str]] = None
        self._cell: Optional[List[str]] = None
        self._list: Optional[List[str]] = None
        self._depth_table = 0

    # text buffer for paragraphs / list items
    def _flush(self, kind: str = "p") -> None:
        text = " ".join("".join(self._text).split())
        if text:
            if kind == "li" and self._list is not None:
                self._list.append(text)
            elif self._strong_only and kind == "p":
                self.blocks.append({"type": "h", "text": text})
            else:
                self.blocks.append({"type": "p", "text": text})
        self._text = []
        self._strong_only = True

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth_table += 1
            if self._depth_table == 1:
                self._flush()
                self._table = []
        elif self._depth_table:
            if tag == "tr":
                self._row = []
            elif tag in ("td", "th"):
                self._cell = []
            elif tag in ("br", "p") and self._cell is not None and self._cell:
                self._cell.append("; " if tag == "p" else " ")
        elif tag in ("p", "div", "h1", "h2", "h3", "h4"):
            self._flush()
        elif tag in ("ul", "ol"):
            self._flush()
            self._list = []
        elif tag == "li":
            self._flush("li")
        elif tag == "br":
            self._text.append(" ")
        elif tag in ("strong", "b"):
            self._in_strong += 1
        elif tag == "sup":
            self._emit("^")

    def handle_endtag(self, tag):
        if self._depth_table:
            if tag in ("td", "th") and self._cell is not None and self._row is not None:
                self._row.append(" ".join("".join(self._cell).split()).strip("; "))
                self._cell = None
            elif tag == "tr" and self._row is not None and self._table is not None:
                if any(c for c in self._row):
                    self._table.append(self._row)
                self._row = None
            elif tag == "table":
                self._depth_table -= 1
                if self._depth_table == 0 and self._table is not None:
                    if self._table:
                        self.blocks.append({"type": "table", "rows": self._table})
                    self._table = None
        elif tag in ("p", "div", "h1", "h2", "h3", "h4"):
            self._flush()
        elif tag == "li":
            self._flush("li")
        elif tag in ("ul", "ol"):
            self._flush("li")
            if self._list:
                self.blocks.append({"type": "list", "items": self._list})
            self._list = None
        elif tag in ("strong", "b"):
            self._in_strong = max(0, self._in_strong - 1)

    def _emit(self, data: str) -> None:
        if self._depth_table:
            if self._cell is not None:
                self._cell.append(data)
            return
        if data.strip() and not self._in_strong:
            self._strong_only = False
        self._text.append(data)

    def handle_data(self, data):
        self._emit(data)

    def close(self):
        super().close()
        self._flush()
        return self.blocks


def html_to_blocks(fragment: str) -> List[Dict]:
    p = _BlockParser()
    p.feed(fragment)
    return p.close()


_SECTION_RE = re.compile(
    r'<summary id="(?P<id>[A-Z_]+)"[^>]*>(?P<title>.*?)</summary>\s*'
    r'<div class="sectionWrapper">(?P<body>.*?)</div>\s*</details>',
    re.S,
)


def parse_smpc(page: str) -> Dict:
    sections: Dict[str, Dict] = {}
    for m in _SECTION_RE.finditer(page):
        sid = m.group("id")
        if sid not in SECTIONS:
            continue
        key, number = SECTIONS[sid]
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group("title"))).strip()
        sections[key] = {"number": number, "title": title, "blocks": html_to_blocks(m.group("body"))}
    if "form" not in sections:
        raise ValueError("page does not look like an SmPC")
    _tidy(sections)
    company = re.search(r'company-details-name[^>]*>([^<]+)<', page)
    return {
        "sections": sections,
        "name": _first_text(sections.get("name")),
        "revision": _first_text(sections.get("revision")),
        "company": html.unescape(company.group(1).strip()) if company else "",
    }


def _tidy(node):
    """Drop the superscript marker in front of symbols (Name^® -> Name®)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str):
                node[k] = re.sub(r"\^\s*([®™*†‡§#])", r"\1", v)
            else:
                _tidy(v)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str):
                node[i] = re.sub(r"\^\s*([®™*†‡§#])", r"\1", v)
            else:
                _tidy(v)


def _first_text(section: Optional[Dict]) -> str:
    if not section:
        return ""
    for block in section["blocks"]:
        if block.get("text"):
            return block["text"]
    return ""


# ------------------------------------------------------------- id resolution
def resolve_id(product: Product, delay: float) -> int:
    if product.emc_id:
        return product.emc_id
    page = polite_get(f"{BASE}/emc/search?q={urllib.request.quote(product.query)}",
                      f"search_{product.query.replace('/', '_')}.html", delay)
    if 'id="FORM"' in page:  # a single hit redirects straight to the SmPC
        ids = re.findall(r"/emc/product/(\d+)/smpc", page)
        if ids:
            return int(max(set(ids), key=ids.count))
    for m in re.finditer(r'<a[^>]+href="/emc/product/(\d+)(?:/smpc)?"[^>]*>(.*?)</a>', page, re.S):
        name = html.unescape(" ".join(re.sub(r"<[^>]+>", "", m.group(2)).split()))
        if name and name.lower().startswith(product.query.lower()) and product.match.lower() in name.lower():
            return int(m.group(1))
    raise LookupError(
        f"{product.key}: no emc result starting with {product.query!r} and containing {product.match!r}. "
        "emc renames products (Descovy is listed as 'Emtricitabine/Tenofovir Alafenamide Gilead'), so pin the "
        "product's emc id with emc_id=... in art_cds/knowledge/products.py — search for it at "
        "https://www.medicines.org.uk/emc and take the number from the /emc/product/<id>/smpc URL.")


def fetch(product: Product, delay: float, refresh: bool) -> Path:
    out = OUT / f"{product.key}.json"
    if out.exists() and not refresh:
        return out
    emc_id = resolve_id(product, delay)
    url = f"{BASE}/emc/product/{emc_id}/smpc"
    cache_name = f"smpc_{emc_id}.html"
    if refresh:
        (CACHE / cache_name).unlink(missing_ok=True)
    data = parse_smpc(polite_get(url, cache_name, delay))
    data.update({"key": product.key, "brand": product.brand, "emc_id": emc_id, "url": url,
                 "retrieved": time.strftime("%Y-%m-%d")})
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="product keys (default: all)")
    ap.add_argument("--delay", type=float, default=20.0, help="seconds between requests")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    products = [PRODUCTS_BY_KEY[k] for k in args.keys] if args.keys else list(PRODUCTS)
    failed = []
    for product in products:
        try:
            path = fetch(product, args.delay, args.refresh)
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"ok   {product.key:14} emc {data['emc_id']:<6} rev {data['revision']:<12} {data['name']}",
                  flush=True)
        except BotCheck:
            print(f"STOP {product.key}: emc human check persists — try again later", flush=True)
            failed.append(product.key)
            break
        except Exception as exc:  # report and continue with the rest
            print(f"FAIL {product.key}: {exc}", flush=True)
            failed.append(product.key)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
