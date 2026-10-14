"""Rule plumbing: registration, context, and SmPC claims.

A rule is a function ``(regimen, ctx) -> list[Finding]``. Rules register
themselves with ``@rule(name, label)`` and run in registration order.

``claim`` (an SmPC section) and ``bhiva`` (a guideline section) return citations and
record patterns that must occur in the cited text; see ``knowledge/citations.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from ...knowledge.citations import SMPC_CLAIMS as CLAIMS, bhiva, smpc_claim as claim  # noqa: F401
from ...models import Finding, PatientProfile, Ref, Severity
from ..resistance import ResistanceReport


@dataclass(frozen=True)
class RuleContext:
    patient: PatientProfile
    resistance: Optional[ResistanceReport]
    virology: Optional["object"] = None  # engine.virology.VirologyAssessment


RuleFn = Callable[["object", RuleContext], List[Finding]]

REGISTRY: List[Tuple[str, str, RuleFn]] = []
LABELS: Dict[str, str] = {}



def rule(name: str, label: str):
    def register(fn: RuleFn) -> RuleFn:
        REGISTRY.append((name, label, fn))
        LABELS[name] = label
        return fn
    return register


def finding(source: str, severity: Severity, message: str, score: float = 0.0, *,
            refs: Tuple[Ref, ...] = (), dose_change: Optional[str] = None,
            teaching: Optional[str] = None) -> Finding:
    return Finding(source, severity, message, score, dose_change, tuple(refs), teaching)
