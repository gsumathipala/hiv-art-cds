"""Orchestrate the decision: candidate regimens -> rules -> ranked report."""
from __future__ import annotations

from dataclasses import replace
from typing import List, Optional

from ..knowledge.guidelines import TIER_SCORE, tier_for
from ..knowledge.regimens import REGIMENS, Regimen
from ..calculators import child_pugh, cockcroft_gault, kidney
from ..knowledge.drugs import class_of
from ..knowledge.medicines import reconcile
from ..models import ChildPugh, PatientProfile, RegimenAssessment, Report, TreatmentStatus
from . import rules
from .alerts import patient_alerts
from .monitoring import monitoring_plan
from .resistance import ResistanceReport, interpret_history, regimen_gss
from .virology import classify, latest


def assess_regimen(regimen: Regimen, tier: str, ctx: rules.RuleContext, label: str = "",
                   ref=None) -> RegimenAssessment:
    a = RegimenAssessment(regimen=regimen, tier=tier, base_score=TIER_SCORE[tier], tier_label=label, tier_ref=ref)
    for _name, _label, fn in rules.REGISTRY:
        a.findings.extend(fn(regimen, ctx))
    a.gss = regimen_gss(regimen.components, ctx.resistance)
    if not a.excluded:
        a.monitoring = monitoring_plan(regimen, ctx.patient)
    return a


def derive(patient: PatientProfile) -> PatientProfile:
    """Fill current values from the longitudinal record when they were not entered directly."""
    changes = {}
    if patient.crcl is None and patient.creatinine_umol and patient.weight_kg:
        changes["crcl"] = round(cockcroft_gault(patient.age, patient.weight_kg, patient.sex == "female",
                                                patient.creatinine_umol), 1)
    if (patient.child_pugh is ChildPugh.NONE and None not in (patient.bilirubin_umol, patient.albumin_g_l, patient.inr)
            and patient.ascites and patient.encephalopathy):
        score, cls = child_pugh(patient.bilirubin_umol, patient.albumin_g_l, patient.inr, patient.ascites,
                                patient.encephalopathy)
        changes["child_pugh"] = ChildPugh(cls)
    if patient.medicines_text:
        matched = {k for r in reconcile(patient.medicines_text) if r.key for k in (r.key,) + r.also}
        if matched - set(patient.comedications):
            changes["comedications"] = frozenset(patient.comedications | matched)
    vl, cd4 = latest(patient.vl_history), latest(patient.cd4_history)
    if patient.viral_load is None and vl is not None:
        changes["viral_load"] = 0 if vl.censored else int(vl.value)
    if patient.cd4 is None and cd4 is not None:
        changes["cd4"] = int(cd4.value)
    failed = {class_of(c) for e in patient.art_history if e.reason_stopped == "virological failure"
              for c in e.components} - {"", "Booster"}
    if failed - set(patient.failed_classes) and patient.status is not TreatmentStatus.NAIVE:
        changes["failed_classes"] = frozenset(patient.failed_classes | failed)
    return replace(patient, **changes) if changes else patient


def recommend(patient: PatientProfile) -> Report:
    patient = derive(patient)
    resistance: Optional[ResistanceReport] = None
    tests = patient.genotype_history
    if tests:
        resistance = interpret_history(tests, patient.minority_threshold, patient.use_hivdb)
    ctx = rules.RuleContext(patient, resistance, classify(patient.vl_history, patient.art_history))

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
    report = Report(patient, viable, excluded, patient_alerts(patient, resistance, viable), resistance)
    report.virology = ctx.virology
    report.medicines = reconcile(patient.medicines_text) if patient.medicines_text else []
    report.kidney = kidney(patient.age, patient.sex == "female", patient.weight_kg, patient.creatinine_umol,
                           patient.cystatin_c) if patient.creatinine_umol or patient.cystatin_c else None
    return report
