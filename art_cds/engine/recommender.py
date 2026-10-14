"""Orchestrate the decision: candidate regimens -> rules -> ranked report."""
from __future__ import annotations

from typing import List, Optional

from ..knowledge.guidelines import TIER_SCORE, tier_for
from ..knowledge.regimens import REGIMENS, Regimen
from ..models import PatientProfile, RegimenAssessment, Report
from . import rules
from .alerts import patient_alerts
from .monitoring import monitoring_plan
from .resistance import ResistanceReport, interpret, regimen_gss


def assess_regimen(regimen: Regimen, tier: str, ctx: rules.RuleContext, label: str = "",
                   ref=None) -> RegimenAssessment:
    a = RegimenAssessment(regimen=regimen, tier=tier, base_score=TIER_SCORE[tier], tier_label=label, tier_ref=ref)
    for _name, _label, fn in rules.REGISTRY:
        a.findings.extend(fn(regimen, ctx))
    a.gss = regimen_gss(regimen.components, ctx.resistance)
    if not a.excluded:
        a.monitoring = monitoring_plan(regimen, ctx.patient)
    return a


def recommend(patient: PatientProfile) -> Report:
    resistance: Optional[ResistanceReport] = None
    if patient.genotype_available:
        resistance = interpret(patient.rt_mutations, patient.pr_mutations, patient.in_mutations)
    ctx = rules.RuleContext(patient, resistance)

    assessments: List[RegimenAssessment] = []
    for regimen in REGIMENS:
        entry = tier_for(patient.status, regimen.id, patient.is_pregnant)
        if entry is not None:
            tier, label, ref = entry
            assessments.append(assess_regimen(regimen, tier, ctx, label, ref))

    order = {r.id: i for i, r in enumerate(REGIMENS)}
    viable = sorted((a for a in assessments if not a.excluded),
                    key=lambda a: (-a.score, order[a.regimen.id]))
    excluded = sorted((a for a in assessments if a.excluded), key=lambda a: order[a.regimen.id])
    return Report(patient, viable, excluded, patient_alerts(patient, resistance, viable), resistance)
