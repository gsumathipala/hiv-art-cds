"""Check whether any UK SmPC has been revised since it was downloaded, and re-verify every claim.

    python -m tools.check_updates              # check all products (slow: emc rate limits)
    python -m tools.check_updates --quick      # only compare revision dates already on disk
    python -m tools.check_updates --apply      # fetch changed SmPCs and rewrite the stored copies
    python -m tools.check_updates biktarvy ... # only these products

Without ``--apply`` nothing on disk changes: it reports which SmPCs have a newer revision date and
which sections differ, so the knowledge base can be reviewed before it is updated. Exits non-zero if
any SmPC changed or any claim no longer matches its source text — suitable for a scheduled CI job.
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from art_cds.knowledge import smpc  # noqa: E402
from art_cds.knowledge.products import PRODUCTS, PRODUCTS_BY_KEY  # noqa: E402
from art_cds.verification import check  # noqa: E402
from tools import fetch_smpc  # noqa: E402

WATCHED = ("indications", "posology", "contraindications", "warnings", "interactions", "pregnancy",
           "adverse_effects")


def section_text(doc: Dict, name: str) -> str:
    section = doc["sections"].get(name)
    if not section:
        return ""
    parts: List[str] = []
    for block in section["blocks"]:
        if block["type"] in ("p", "h"):
            parts.append(block["text"])
        elif block["type"] == "list":
            parts.extend(block["items"])
        elif block["type"] == "table":
            parts.extend(" | ".join(row) for row in block["rows"])
    return "\n".join(parts)


def compare(old: Dict, new: Dict) -> List[Tuple[str, int, int]]:
    """Sections that differ, with added and removed line counts."""
    changed = []
    for name in WATCHED:
        a, b = section_text(old, name).splitlines(), section_text(new, name).splitlines()
        if a == b:
            continue
        diff = list(difflib.ndiff(a, b))
        added = sum(1 for d in diff if d.startswith("+ "))
        removed = sum(1 for d in diff if d.startswith("- "))
        changed.append((name, added, removed))
    return changed


def fetch_fresh(key: str, delay: float) -> Optional[Dict]:
    """Download the current SmPC into a scratch copy without touching the stored one."""
    product = PRODUCTS_BY_KEY[key]
    stored = fetch_smpc.OUT / f"{key}.json"
    backup = stored.with_suffix(".json.bak")
    cached_html = fetch_smpc.CACHE / f"smpc_{json.loads(stored.read_text())['emc_id']}.html" if stored.exists() \
        else None
    try:
        if stored.exists():
            shutil.copy2(stored, backup)
        if cached_html and cached_html.exists():
            cached_html.unlink()
        fetch_smpc.fetch(product, delay, refresh=True)
        fresh = json.loads(stored.read_text(encoding="utf-8"))
    finally:
        if backup.exists():
            shutil.move(str(backup), str(stored))
            smpc.load.cache_clear()
    return fresh


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="product keys (default: all)")
    ap.add_argument("--delay", type=float, default=20.0, help="seconds between emc requests")
    ap.add_argument("--quick", action="store_true", help="do not contact emc; just re-verify the stored copies")
    ap.add_argument("--apply", action="store_true", help="keep the newly downloaded SmPCs")
    args = ap.parse_args(argv)

    products = [PRODUCTS_BY_KEY[k] for k in args.keys] if args.keys else list(PRODUCTS)
    changes = 0

    if not args.quick:
        for product in products:
            stored_path = fetch_smpc.OUT / f"{product.key}.json"
            if not stored_path.exists():
                print(f"NEW   {product.key}: not downloaded yet")
                changes += 1
                continue
            stored = json.loads(stored_path.read_text(encoding="utf-8"))
            try:
                fresh = fetch_fresh(product.key, args.delay)
            except fetch_smpc.BotCheck:
                print(f"STOP  {product.key}: emc human check — try again later")
                return 2
            except Exception as exc:  # network, parse, lookup
                print(f"ERROR {product.key}: {exc}")
                changes += 1
                continue
            if fresh["revision"] != stored["revision"]:
                print(f"REVISED {product.key}: {stored['revision']} -> {fresh['revision']}")
                changes += 1
            diffs = compare(stored, fresh)
            for name, added, removed in diffs:
                print(f"    §{name}: +{added}/-{removed} lines")
            if diffs and not fresh["revision"] != stored["revision"]:
                print(f"CHANGED {product.key}: text differs although the revision date is unchanged")
                changes += 1
            if (diffs or fresh["revision"] != stored["revision"]) and args.apply:
                stored_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"    applied — review the claims that cite {product.key}")
            if not diffs and fresh["revision"] == stored["revision"]:
                print(f"ok    {product.key}: unchanged ({stored['revision']})")

    smpc.load.cache_clear()
    failures, missing, total = check()
    for line in missing:
        print("MISSING ", line)
    for line in failures:
        print("FAIL    ", line)
    print(f"{total - len(failures) - len(missing)}/{total} claims verified; {changes} SmPC change(s) detected.")
    return 1 if (failures or missing or changes) else 0


if __name__ == "__main__":
    sys.exit(main())
