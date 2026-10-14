"""Interpret resistance: every genotype the patient has ever had, combined.

Resistance is cumulative — a mutation seen once (in plasma or archived proviral DNA)
must be assumed present for life. All tests are therefore merged into one
cumulative genotype, which is scored either by the Stanford HIVdb service (when
enabled) or by the local teaching approximation in ``knowledge/resistance.py``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .. import hivdb
from ..knowledge import resistance as kb
from ..knowledge.drugs import BOOSTERS
from ..models.patient import GenotypeTest

_TOKEN = re.compile(r"^([A-Z])?(\d{1,3})([A-Z*]+|INS|DEL|_?INS[A-Z]*)$")
_WITH_FREQ = re.compile(r"^(?P<mut>[^:()]+?)\s*(?:[:(]\s*(?P<pct>\d+(?:\.\d+)?)\s*%?\s*\)?)?$")
GENE_LENGTH = {"RT": 560, "PR": 99, "IN": 288}

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
class TestSummary:
    label: str
    source: str
    mutations: Dict[str, List[str]]
    subtype: str = ""


@dataclass
class ResistanceReport:
    mutations: Dict[str, List[str]]  # cumulative: gene -> mutations
    unrecognised: List[str]
    drugs: Dict[str, DrugSusceptibility]
    source: str = "local"  # local | hivdb
    version: str = "ART Navigator teaching table"
    tests: List[TestSummary] = field(default_factory=list)
    minority: List[str] = field(default_factory=list)  # below threshold — reported, not scored
    not_in_local_table: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    subtype: str = ""
    apobec: List[str] = field(default_factory=list)

    def level(self, drug: str) -> int:
        s = self.get(drug)
        return s.level if s else 1

    def get(self, drug: str) -> Optional[DrugSusceptibility]:
        return self.drugs.get(kb.SCORED_AS.get(drug, drug))

    @property
    def any_mutations(self) -> bool:
        return any(self.mutations.values())

    @property
    def archived_only(self) -> List[str]:
        """Mutations seen only in proviral DNA."""
        plasma = {f"{g}:{m}" for t in self.tests if t.source != "proviral" for g, ms in t.mutations.items() for m in ms}
        return sorted({f"{g}:{m}" for t in self.tests if t.source == "proviral"
                       for g, ms in t.mutations.items() for m in ms} - plasma)

    def resistant_classes(self, minimum: int = 4) -> List[str]:
        classes = {"NRTI": kb.NRTI_DRUGS, "NNRTI": kb.NNRTI_DRUGS, "INSTI": kb.INSTI_DRUGS, "PI": kb.PI_DRUGS}
        return [c for c, drugs in classes.items() if any(self.level(d) >= minimum for d in drugs)]

    def to_dict(self) -> Dict:
        return {
            "source": self.source, "version": self.version, "mutations": self.mutations,
            "unrecognised": self.unrecognised, "minority": self.minority, "warnings": self.warnings,
            "subtype": self.subtype, "apobec": self.apobec,
            "tests": [{"label": t.label, "source": t.source, "mutations": t.mutations} for t in self.tests],
            "drugs": {d: {"score": s.score, "level": s.level, "label": s.label, "mutations": s.contributors}
                      for d, s in self.drugs.items()},
        }


# ------------------------------------------------------------------ parsing
def _canonical(gene: str, token: str) -> Optional[str]:
    """Validate one mutation token and return it in canonical form (e.g. 'K103KN', 'T69ins'), else None."""
    m = _TOKEN.match(token)
    if not m:
        return None
    wt, pos, aas = m.group(1) or "", int(m.group(2)), m.group(3)
    if not 1 <= pos <= GENE_LENGTH[gene]:
        return None
    if "INS" in aas:
        return f"{wt}{pos}ins"
    if aas == "DEL":
        return f"{wt}{pos}del"
    return f"{wt}{pos}{aas}"


def parse_with_frequency(text: str, gene: str) -> Tuple[List[Tuple[str, Optional[float]]], List[str]]:
    """'K103N, M184V:12%, Q148H(4)' -> ([('K103N', None), ('M184V', 12.0), ...], invalid tokens)."""
    found: List[Tuple[str, Optional[float]]] = []
    bad: List[str] = []
    for raw in re.split(r"[,;\s]+", (text or "").upper()):
        raw = re.sub(r"^(RT|PR|IN|INT)[:_-]", "", raw.strip())
        if not raw:
            continue
        m = _WITH_FREQ.match(raw)
        canonical = _canonical(gene, m.group("mut")) if m else None
        if canonical is None:
            bad.append(raw)
            continue
        pct = float(m.group("pct")) if m.group("pct") else None
        found.append((canonical, pct))
    return found, bad


def _local_names(gene: str, mutation: str) -> List[str]:
    """Map a canonical mutation (possibly a mixture) onto entries in the local table."""
    m = _TOKEN.match(mutation.upper())
    if not m:
        return []
    wt, pos, aas = m.group(1), int(m.group(2)), m.group(3)
    by_position = {}
    for name in kb.SCORES[gene]:
        n = _TOKEN.match(name.upper())
        if n:
            by_position[(int(n.group(2)), n.group(3))] = name
    if "INS" in aas:
        return [by_position[(pos, "INS")]] if (pos, "INS") in by_position else []
    return [by_position[(pos, aa)] for aa in aas if aa != wt and (pos, aa) in by_position]


def parse(text: str, gene: str) -> Tuple[List[str], List[str]]:
    """Mutations from free text, restricted to the local teaching table (kept for teaching tools)."""
    found, bad = parse_with_frequency(text, gene)
    names: List[str] = []
    for mut, _pct in found:
        local = _local_names(gene, mut)
        if not local:
            bad.append(mut)
        for n in local:
            if n not in names:
                names.append(n)
    return names, bad


# ------------------------------------------------------------------ scoring
def score(mutations: Dict[str, Iterable[str]]) -> Dict[str, DrugSusceptibility]:
    """Local approximate scoring of mutations already mapped to local-table names."""
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
    """Local interpretation of a single genotype (used by teaching tools and tests)."""
    return interpret_history([GenotypeTest(rt=rt, pr=pr, integrase=integrase)])


def interpret_history(tests: Sequence[GenotypeTest], threshold: float = 20.0,
                      use_hivdb: bool = False) -> ResistanceReport:
    cumulative: Dict[str, List[str]] = {"RT": [], "PR": [], "IN": []}
    minority: List[str] = []
    unrecognised: List[str] = []
    warnings: List[str] = []
    summaries: List[TestSummary] = []
    subtype, apobec = "", []

    for test in tests:
        per_test: Dict[str, List[str]] = {"RT": [], "PR": [], "IN": []}
        for gene, text in (("RT", test.rt), ("PR", test.pr), ("IN", test.integrase)):
            found, bad = parse_with_frequency(text, gene)
            unrecognised += [f"{gene}:{b}" for b in bad]
            for mut, pct in found:
                if pct is not None and pct < threshold:
                    minority.append(f"{gene}:{mut} ({pct:g}%)")
                    continue
                per_test[gene].append(mut)
        test_subtype = ""
        if test.sequence.strip():
            if not use_hivdb:
                warnings.append(f"Sequence in test '{test.label}' was not analysed — enable Stanford HIVdb to align "
                                "sequences (the local engine reads mutation lists only).")
            else:
                try:
                    seq = hivdb.analyse_sequence(test.sequence.strip())
                except hivdb.HivdbError as exc:
                    warnings.append(str(exc))
                else:
                    test_subtype = seq["subtype"]
                    for gene, muts in seq["mutations"].items():
                        if gene in per_test:
                            per_test[gene] += [m for m in muts if m not in per_test[gene]]
                    apobec += seq["apobec"]
                    if seq["apobec_count"] >= 3:
                        warnings.append(f"Sequence '{test.label}': {seq['apobec_count']} APOBEC-context mutations — "
                                        "possible G-to-A hypermutation; interpret drug-resistance mutations at "
                                        "APOBEC sites with caution.")
                    warnings += [f"Sequence '{test.label}': {v}" for v in seq["validation"]]
        for gene, muts in per_test.items():
            for m in muts:
                if m not in cumulative[gene]:
                    cumulative[gene].append(m)
        summaries.append(TestSummary(test.label, test.source, per_test, test_subtype))
        subtype = test_subtype or subtype

    report = ResistanceReport(mutations=cumulative, unrecognised=unrecognised, drugs={}, tests=summaries,
                              minority=minority, warnings=warnings, subtype=subtype, apobec=apobec)
    if len(tests) > 1 and report.any_mutations:
        report.warnings.append("Scored on the cumulative genotype: every mutation from every test (including archived "
                               "proviral DNA) is assumed to persist.")

    if use_hivdb:
        payload = tuple(f"{g}:{m}" for g, ms in cumulative.items() for m in ms)
        try:
            result = hivdb.analyse_mutations(payload) if payload else hivdb.analyse_mutations(("RT:M41M",))
        except hivdb.HivdbError as exc:
            report.warnings.append(f"{exc} — fell back to the local approximate scores.")
        else:
            report.source, report.version = "hivdb", f"Stanford HIVdb {result['version']}"
            report.drugs = {code: DrugSusceptibility(code, v["score"], int(v["level"]), v["contributors"])
                            for code, v in result["drugs"].items()}
            report.warnings += [w for w in result["validation"] if w not in report.warnings]
            return report

    local: Dict[str, List[str]] = {}
    for gene, muts in cumulative.items():
        names: List[str] = []
        for mut in muts:
            mapped = _local_names(gene, mut)
            if not mapped:
                report.not_in_local_table.append(f"{gene}:{mut}")
            names += [n for n in mapped if n not in names]
        local[gene] = names
    report.drugs = score(local)
    return report


def regimen_gss(components: Iterable[str], report: Optional[ResistanceReport]) -> Optional[float]:
    if report is None:
        return None
    return round(sum(kb.ACTIVITY[report.level(c)] for c in components if c not in BOOSTERS), 2)
