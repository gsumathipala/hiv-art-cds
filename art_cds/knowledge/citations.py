"""Verifiable citations.

``smpc_claim`` cites a UK SmPC section; ``bhiva`` cites a BHIVA guideline section.
Each records patterns that must occur in the cited text, and
``tools/verify_smpc.py`` (and the test suite) checks every one: against the parsed
SmPC, or against the guideline text in ``art_cds/data/guidelines``.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ..models.assessment import Ref

GUIDELINE_DIR = Path(__file__).resolve().parent.parent / "data" / "guidelines"

GUIDELINE_DOCS = {
    "bhiva_art": ("BHIVA ART 2025",
                  "BHIVA guidelines on antiretroviral treatment for adults living with HIV-1 2022 "
                  "(2025 interim update)"),
    "bhiva_pregnancy": ("BHIVA pregnancy 2025",
                        "BHIVA guidelines on the management of HIV in pregnancy and the postpartum period (2025)"),
    "bhiva_tb": ("BHIVA TB 2023",
                 "BHIVA guidelines for the management of tuberculosis in adults living with HIV 2018 (2023 interim "
                 "update)"),
}

SMPC_CLAIMS: List[Tuple[str, str, Tuple[str, ...]]] = []
GUIDELINE_CLAIMS: List[Tuple[str, str, Tuple[str, ...]]] = []


def smpc_claim(product: str, section: str, *patterns: str) -> Ref:
    SMPC_CLAIMS.append((product, section, patterns))
    return Ref(product=product, section=section)


def bhiva(doc: str, section: str, *patterns: str) -> Ref:
    """Cite a BHIVA guideline section; patterns are matched case-insensitively with whitespace collapsed."""
    GUIDELINE_CLAIMS.append((doc, section, patterns))
    short, full = GUIDELINE_DOCS[doc]
    return Ref(guideline=f"{short} §{section}", title=f"{full}, section {section}")


@lru_cache(maxsize=None)
def guideline_text(doc: str) -> str:
    path = GUIDELINE_DIR / f"{doc}.txt"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").replace("ﬁ", "fi").replace("ﬂ", "fl")
    return re.sub(r"\s+", " ", text)
