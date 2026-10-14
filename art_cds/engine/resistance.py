"""Interpret a genotype: parse mutations and score every drug."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from ..knowledge import resistance as kb
from ..knowledge.drugs import BOOSTERS

_TOKEN = re.compile(r"^([A-Z])?(\d{1,3})([A-Z]+|INS|_?INS[A-Z]*)$")

GENE_DRUGS = {
    "RT": kb.NRTI_DRUGS + kb.NNRTI_DRUGS,
    "PR": kb.PI_DRUGS,
    "IN": kb.INSTI_DRUGS,
}


@dataclass
class DrugSusceptibility:
    drug: str
    score: float
    level: int
    contributors: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return kb.LEVELS[self.level]

    @property
    def activity(self) -> float:
        return kb.ACTIVITY[self.level]


@dataclass
class ResistanceReport:
    mutations: Dict[str, List[str]]  # gene -> recognised mutations
    unrecognised: List[str]
    drugs: Dict[str, DrugSusceptibility]

    def level(self, drug: str) -> int:
        s = self.drugs.get(kb.SCORED_AS.get(drug, drug))
        return s.level if s else 1

    def get(self, drug: str) -> Optional[DrugSusceptibility]:
        return self.drugs.get(kb.SCORED_AS.get(drug, drug))

    @property
    def any_mutations(self) -> bool:
        return any(self.mutations.values())

    def resistant_classes(self, minimum: int = 4) -> List[str]:
        classes = {"NRTI": kb.NRTI_DRUGS, "NNRTI": kb.NNRTI_DRUGS, "INSTI": kb.INSTI_DRUGS, "PI": kb.PI_DRUGS}
        return [c for c, drugs in classes.items() if any(self.level(d) >= minimum for d in drugs)]

    def to_dict(self) -> Dict:
        return {
            "mutations": self.mutations,
            "unrecognised": self.unrecognised,
            "drugs": {d: {"score": s.score, "level": s.level, "label": s.label, "mutations": s.contributors}
                      for d, s in self.drugs.items()},
        }


def parse(text: str, gene: str) -> Tuple[List[str], List[str]]:
    """Return (recognised, unrecognised) mutations from free text such as 'M184V, K65R, K103KN'."""
    known = kb.SCORES[gene]
    by_position: Dict[Tuple[int, str], str] = {}
    for name in known:
        m = _TOKEN.match(name.upper())
        if m:
            by_position[(int(m.group(2)), m.group(3))] = name
    recognised: List[str] = []
    unrecognised: List[str] = []
    for raw in re.split(r"[\s,;/]+", text.upper()):
        raw = raw.strip()
        if not raw:
            continue
        raw = re.sub(r"^(RT|PR|IN|INT)[:_-]", "", raw)
        m = _TOKEN.match(raw)
        if not m:
            unrecognised.append(raw)
            continue
        wt, pos, aas = m.group(1), int(m.group(2)), m.group(3)
        if "INS" in aas:
            candidates = ["INS"]
        else:
            candidates = [aa for aa in aas if aa != wt]  # mixtures such as K103KN
        found = False
        for aa in candidates:
            name = by_position.get((pos, aa))
            if name:
                found = True
                if name not in recognised:
                    recognised.append(name)
        if not found:
            unrecognised.append(raw)
    return recognised, unrecognised


def score(mutations: Dict[str, Iterable[str]]) -> Dict[str, DrugSusceptibility]:
    drugs: Dict[str, DrugSusceptibility] = {}
    for gene, gene_drugs in GENE_DRUGS.items():
        for d in gene_drugs:
            drugs[d] = DrugSusceptibility(d, 0.0, 1)
    for gene, muts in mutations.items():
        present = set(muts)
        for mut in present:
            for d, s in kb.SCORES[gene][mut].items():
                drugs[d].score += s
                drugs[d].contributors.append(mut)
        for g, groups, scores in kb.COMBINATIONS:
            if g == gene and all(any(alt in present for alt in grp) for grp in groups):
                label = " + ".join(next(a for a in grp if a in present) for grp in groups)
                for d, s in scores.items():
                    drugs[d].score += s
                    drugs[d].contributors.append(f"({label})")
    for s in drugs.values():
        s.level = kb.level_for(s.score)
    return drugs


def interpret(rt: str = "", pr: str = "", integrase: str = "") -> ResistanceReport:
    mutations: Dict[str, List[str]] = {}
    unrecognised: List[str] = []
    for gene, text in (("RT", rt), ("PR", pr), ("IN", integrase)):
        found, bad = parse(text or "", gene)
        mutations[gene] = found
        unrecognised += [f"{gene}:{b}" for b in bad]
    return ResistanceReport(mutations, unrecognised, score(mutations))


def regimen_gss(components: Iterable[str], report: Optional[ResistanceReport]) -> Optional[float]:
    if report is None:
        return None
    return round(sum(kb.ACTIVITY[report.level(c)] for c in components if c not in BOOSTERS), 2)
