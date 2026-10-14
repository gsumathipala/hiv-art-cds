"""What the engine produces: findings per regimen and the overall report."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover
    from ..engine.resistance import ResistanceReport
    from ..knowledge.regimens import Regimen
    from .patient import PatientProfile


class Severity(str, Enum):
    EXCLUDE = "exclude"  # contraindicated or inappropriate — regimen removed
    CAUTION = "caution"  # usable with care — scored down
    INFO = "info"  # worth knowing — not scored
    BENEFIT = "benefit"  # a reason to favour the regimen — scored up


@dataclass(frozen=True)
class Ref:
    """A citation: a UK SmPC section, or a guideline."""

    product: Optional[str] = None  # product key, see knowledge/products.py
    section: Optional[str] = None  # SmPC section number, e.g. "4.5"
    guideline: Optional[str] = None  # short guideline citation, e.g. "BHIVA ART 2025 §5.4"
    title: Optional[str] = None  # full citation for tooltips

    def label(self) -> str:
        if self.product:
            from ..knowledge.products import PRODUCTS_BY_KEY

            brand = PRODUCTS_BY_KEY[self.product].brand
            return f"{brand} SmPC §{self.section}" if self.section else f"{brand} SmPC"
        return self.guideline or ""


def smpc(product: str, section: str) -> Ref:
    return Ref(product=product, section=section)


def guideline(text: str) -> Ref:
    return Ref(guideline=text)


@dataclass(frozen=True)
class Finding:
    source: str  # the rule module that raised it
    severity: Severity
    message: str
    score: float = 0.0
    dose_change: Optional[str] = None
    refs: Tuple[Ref, ...] = ()
    teaching: Optional[str] = None  # an educational aside


@dataclass
class RegimenAssessment:
    regimen: "Regimen"
    tier: str
    base_score: float
    findings: List[Finding] = field(default_factory=list)
    tier_label: str = ""
    tier_ref: Optional[Ref] = None
    gss: Optional[float] = None
    monitoring: List[str] = field(default_factory=list)

    @property
    def excluded(self) -> bool:
        return any(f.severity is Severity.EXCLUDE for f in self.findings)

    @property
    def score(self) -> float:
        return self.base_score + sum(f.score for f in self.findings)

    def of(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings if f.severity is severity]

    @property
    def dose_changes(self) -> List[str]:
        seen: List[str] = []
        for f in self.findings:
            if f.dose_change and f.dose_change not in seen:
                seen.append(f.dose_change)
        return seen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regimen": self.regimen.id,
            "name": self.regimen.short,
            "tier": self.tier,
            "tier_label": self.tier_label,
            "tier_source": self.tier_ref.label() if self.tier_ref else None,
            "score": round(self.score, 1),
            "excluded": self.excluded,
            "gss": self.gss,
            "dose_changes": self.dose_changes,
            "monitoring": self.monitoring,
            "findings": [
                {
                    "source": f.source,
                    "severity": f.severity.value,
                    "message": f.message,
                    "score": f.score,
                    "dose_change": f.dose_change,
                    "refs": [r.label() for r in f.refs],
                }
                for f in self.findings
            ],
        }


@dataclass(frozen=True)
class Alert:
    level: str  # critical | warning | info
    message: str
    refs: Tuple[Ref, ...] = ()


@dataclass
class Report:
    patient: "PatientProfile"
    recommended: List[RegimenAssessment]
    excluded: List[RegimenAssessment]
    alerts: List[Alert]
    resistance: Optional["ResistanceReport"]

    @property
    def top(self) -> Optional[RegimenAssessment]:
        return self.recommended[0] if self.recommended else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alerts": [{"level": a.level, "message": a.message} for a in self.alerts],
            "recommended": [a.to_dict() for a in self.recommended],
            "excluded": [a.to_dict() for a in self.excluded],
            "resistance": self.resistance.to_dict() if self.resistance else None,
        }
