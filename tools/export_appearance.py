"""Export the dose-unit facts needed to draw each product.

    python -m tools.export_appearance

Writes ``art_cds/data/appearance.json`` holding only factual attributes parsed from SmPC
section 3 — kind, shape, colour, dimensions in mm and the debossing — and no SmPC prose. The
file is committed so the tablet drawings work before the SmPCs have been downloaded (and in the
static site, which does not carry SmPC text).
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from art_cds.knowledge import smpc  # noqa: E402
from art_cds.knowledge.products import PRODUCTS  # noqa: E402
from art_cds.visuals import pills  # noqa: E402

OUT = ROOT / "art_cds" / "data" / "appearance.json"


def main() -> int:
    if not smpc.available():
        print("No SmPCs downloaded — run python -m tools.fetch_smpc first.")
        return 1
    data = {}
    for product in PRODUCTS:
        units = pills.parse_units(smpc.appearance_text(product.key))
        if not units:
            continue
        data[product.key] = [{k: v for k, v in asdict(u).items() if k != "text"} for u in units]
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{len(data)} products written to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
