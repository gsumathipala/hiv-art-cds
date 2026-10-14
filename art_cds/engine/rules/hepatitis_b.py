"""Hepatitis B co-infection."""
from __future__ import annotations

from ...knowledge.drugs import CYTIDINE, TENOFOVIR
from ...knowledge.guidelines import BHIVA_HEPATITIS
from ...models import LabResult, Severity, guideline
from .base import claim, finding, rule

LAMIVUDINE_ALONE = claim("dovato", "4.4", r"Lamivudine monotherapy is generally not considered an adequate treatment "
                                          r"for hepatitis B")
CAB_HBV = claim("vocabria_inj", "4.4", r"not recommended to initiate Vocabria in patients with hepatitis B")
JULUCA_HBV = claim("juluca", "4.4", r"No clinical data are available in patients with hepatitis B")
FLARE = claim("descovy", "4.4", r"severe acute exacerbations of hepatitis")


@rule("hbv", "Hepatitis B")
def hepatitis_b(regimen, ctx):
    p = ctx.patient
    comps = set(regimen.components)
    hbv_active = bool(comps & TENOFOVIR) and bool(comps & CYTIDINE)
    if p.hbsag is LabResult.POSITIVE:
        if regimen.long_acting:
            return [finding("hbv", Severity.EXCLUDE, "Chronic hepatitis B: cabotegravir + rilpivirine has no HBV activity "
                            "and should not be initiated.", refs=(CAB_HBV,))]
        if not hbv_active:
            return [finding("hbv", Severity.EXCLUDE,
                            "Chronic hepatitis B: the regimen must contain tenofovir (TDF or TAF) plus emtricitabine or "
                            "lamivudine. Lamivudine alone selects HBV resistance.",
                            refs=(LAMIVUDINE_ALONE, JULUCA_HBV, guideline(BHIVA_HEPATITIS)))]
        return [finding("hbv", Severity.BENEFIT, "Tenofovir + emtricitabine/lamivudine treats HIV and HBV together.", 10,
                        refs=(guideline(BHIVA_HEPATITIS),),
                        teaching="Never stop the HBV-active drugs without alternative HBV cover — "
                                 "severe hepatitis flares occur on withdrawal."),
                finding("hbv", Severity.INFO, "Monitor LFTs and HBV DNA; warn about flares if treatment stops.",
                        refs=(FLARE,))]
    if p.hbsag is LabResult.UNKNOWN:
        if regimen.dual:
            return [finding("hbv", Severity.EXCLUDE,
                            "HBV status unknown — two-drug and long-acting regimens need documented negative HBsAg "
                            "(and HBV immunity).", refs=(LAMIVUDINE_ALONE, guideline(BHIVA_HEPATITIS)))]
        if not hbv_active:
            return [finding("hbv", Severity.CAUTION,
                            "HBV status unknown — check HBsAg, anti-HBc and anti-HBs before a regimen without "
                            "tenofovir + FTC/3TC.", -20, refs=(guideline(BHIVA_HEPATITIS),))]
        return []
    if regimen.dual and not hbv_active:
        return [finding("hbv", Severity.INFO,
                        "HBsAg negative — confirm HBV immunity (anti-HBs) or vaccinate; isolated anti-HBc needs HBV DNA "
                        "before a tenofovir-free regimen.", refs=(guideline(BHIVA_HEPATITIS),))]
    return []
