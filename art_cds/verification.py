"""Check every SmPC and BHIVA citation the engine makes against the source text."""
from __future__ import annotations

import re
from typing import List, Tuple

from .engine import recommender  # noqa: F401  (importing registers every claim)
from .knowledge import quiz  # noqa: F401
from . import longacting, perinatal  # noqa: F401
from .visuals import pharmacokinetics  # noqa: F401
from .knowledge import smpc
from .knowledge.citations import GUIDELINE_CLAIMS, SMPC_CLAIMS as CLAIMS, guideline_text

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


