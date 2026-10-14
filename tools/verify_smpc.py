"""Check every SmPC and BHIVA claim the engine makes against the source text.

    python -m tools.verify_smpc

A claim is (product, section, patterns): every pattern must occur in that
section of that product's SmPC. Claims for products whose SmPC has not been
downloaded are reported as missing. Exits non-zero if any claim fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from art_cds.engine import recommender  # noqa: E402,F401  (importing registers every claim)
from art_cds.knowledge import smpc  # noqa: E402
from art_cds.knowledge.citations import GUIDELINE_CLAIMS, SMPC_CLAIMS as CLAIMS, guideline_text  # noqa: E402

SECTION_KEYS = {
    "1": "name", "2": "composition", "3": "form", "4.1": "indications", "4.2": "posology",
    "4.3": "contraindications", "4.4": "warnings", "4.5": "interactions", "4.6": "pregnancy",
    "4.8": "adverse_effects", "5.1": "pharmacodynamics", "5.2": "pharmacokinetics",
}


def check() -> Tuple[List[str], List[str], int]:
    failures, missing = [], []
    seen = set()
    for doc, section, patterns in GUIDELINE_CLAIMS:
        key = ("guideline", doc, section, patterns)
        if key in seen:
            continue
        seen.add(key)
        text = guideline_text(doc)
        if not text:
            missing.append(f"{doc} §{section}: guideline text not downloaded (python -m tools.fetch_guidelines)")
            continue
        absent = [p for p in patterns if not re.search(p, text, re.I)]
        if absent:
            failures.append(f"{doc} §{section}: pattern(s) not found: {absent}")
    for product, section, patterns in CLAIMS:
        key = (product, section, patterns)
        if key in seen:
            continue
        seen.add(key)
        if smpc.load(product) is None:
            missing.append(f"{product} §{section}: SmPC not downloaded")
            continue
        text = smpc.section_text(product, SECTION_KEYS[section])
        absent = [p for p in patterns if not re.search(p, text, re.I)]
        if absent:
            failures.append(f"{product} §{section}: pattern(s) not found: {absent}")
    return failures, missing, len(seen)


def main() -> int:
    failures, missing, total = check()
    for line in missing:
        print("MISSING ", line)
    for line in failures:
        print("FAIL    ", line)
    print(f"{total - len(failures) - len(missing)}/{total} claims verified against the SmPC/BHIVA text; "
          f"{len(failures)} failed, {len(missing)} missing.")
    return 1 if failures or missing else 0


if __name__ == "__main__":
    sys.exit(main())
