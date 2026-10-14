"""Renal and hepatic function — per-product SmPC limits plus BHIVA tenofovir advice."""
from __future__ import annotations

from ...knowledge.guidelines import BHIVA_ART
from ...knowledge.organ_limits import LIMITS, applicable
from ...models import Severity, guideline, smpc
from .base import CLAIMS, finding, rule

for _l in LIMITS:  # register every limit as a verifiable SmPC claim
    CLAIMS.append((_l.product, _l.section, _l.evidence))

_SEVERITY = {"exclude": Severity.EXCLUDE, "caution": Severity.CAUTION, "info": Severity.INFO}


@rule("organ", "Renal & hepatic function")
def organ(regimen, ctx):
    p = ctx.patient
    out = []
    for limit in applicable(regimen.products, regimen.components, p):
        out.append(finding("organ", _SEVERITY[limit.severity], limit.message, limit.score,
                           refs=(smpc(limit.product, limit.section),), dose_change=limit.dose_change))

    if "TDF" in regimen.components and p.crcl is not None and not p.on_dialysis and 50 <= p.crcl < 60:
        out.append(finding(
            "organ", Severity.CAUTION,
            f"CrCl {p.crcl:.0f} mL/min — BHIVA advises avoiding tenofovir disoproxil in people with, or at risk "
            "of, chronic kidney disease; tenofovir alafenamide or a tenofovir-free regimen is preferred.", -25,
            refs=(guideline(BHIVA_ART),)))
    if "TAF" in regimen.components and p.crcl is not None and 30 <= p.crcl < 60:
        out.append(finding("organ", Severity.BENEFIT,
                           "Tenofovir alafenamide has less renal toxicity than tenofovir disoproxil.", 8,
                           refs=(guideline(BHIVA_ART),),
                           teaching="TAF reaches ~90% lower plasma tenofovir levels than TDF because it is "
                                    "converted inside cells — the source of its renal and bone advantage."))
    if p.crcl is None and "TDF" in regimen.components:
        out.append(finding("organ", Severity.INFO,
                           "Creatinine clearance not entered — check renal function and urinalysis before "
                           "tenofovir disoproxil."))
    if "COBI" in regimen.components and p.crcl is not None:
        out.append(finding("organ", Severity.INFO,
                           "Cobicistat inhibits tubular creatinine secretion: expect a small early rise in creatinine "
                           "without a true fall in GFR.", refs=(smpc("rezolsta", "4.2"),)))
    return out
