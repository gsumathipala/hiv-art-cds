"""Comorbidities and long-term tolerability."""
from __future__ import annotations

from ...knowledge.guidelines import BHIVA_ART
from ...models import Severity, guideline
from .base import bhiva, claim, finding, rule

_A = "bhiva_art"
TDF_BONE_BHIVA = bhiva(_A, "8.2", r"We recommend against the use of tenofovir DF in individuals with osteoporosis")
EFV_PSYCH_BHIVA = bhiva(_A, "8.8", r"efavirenz-containing regimens should be avoided in individuals with a current or "
                                  r"past history of depression")
INSTI_PSYCH = bhiva(_A, "8.8", r"INSTI-containing regimens should be used with caution in patients with a pre-? ?existing "
                              r"history of any psychiatric illness")
TDF_YOUNG = bhiva(_A, "8.1", r"avoiding tenofovir DF in adolescents and young adults under the age of 25")
CKD_PI = bhiva(_A, "8.4", r"darunavir/ritonavir or darunavir/cobicistat in individuals with an eGFR of <60")
CKD_STOP = bhiva(_A, "8.4", r"against continued use of tenofovir DF, lopinavir/ritonavir or atazanavir")
ABC_CVD_BHIVA = bhiva(_A, "5.3.6", r"Use of abacavir in people with CVD risk factors")
TDF_FRAX = bhiva(_A, "8.2", r"10-year probability of a major osteoporotic fracture >5% and/or a 10-year probability "
                            r"of a hip fracture >1%")

ABC_MI = claim("ziagen", "4.4", r"myocardial infarction")
TDF_BONE = claim("viread", "4.4", r"bone mineral density")
EFV_PSYCH = claim("efavirenz", "4.4", r"psychiatric")
RPV_DEPRESSION = claim("edurant", "4.8", r"depression")
WEIGHT = claim("tivicay", "4.4", r"increase in weight")
AZT_HAEM = claim("combivir", "4.4", r"anaemia")
ATV_BILI = claim("atazanavir", "4.4", r"hyperbilirubinaemia")

BHIVA = guideline(BHIVA_ART)


@rule("tolerability", "Comorbidities & tolerability")
def tolerability(regimen, ctx):
    p = ctx.patient
    comps = set(regimen.components)
    boosted = regimen.boosted
    out = []

    if p.high_cv_risk:
        if "ABC" in comps:
            out.append(finding("tolerability", Severity.CAUTION,
                               "Abacavir is associated with a higher risk of myocardial infarction — avoid with high "
                               "cardiovascular risk.", -25, refs=(ABC_MI, ABC_CVD_BHIVA)))
        if boosted:
            out.append(finding("tolerability", Severity.CAUTION,
                               "Boosted PIs raise lipids, and cumulative darunavir exposure has been linked to "
                               "cardiovascular disease.", -8, refs=(BHIVA,)))
    if p.high_fracture_risk:
        if "TDF" in comps:
            why = "Osteoporosis or fragility fracture" if p.has("osteoporosis") else \
                f"FRAX {p.frax_mof or 0:g}% major osteoporotic / {p.frax_hip or 0:g}% hip"
            out.append(finding("tolerability", Severity.EXCLUDE,
                               f"{why} — BHIVA recommends against tenofovir disoproxil (osteoporosis, fragility "
                               "fracture, FRAX major osteoporotic > 5% or hip > 1%).",
                               refs=(TDF_BONE_BHIVA, TDF_FRAX, TDF_BONE)))
        elif "TAF" in comps or "ABC" in comps:
            out.append(finding("tolerability", Severity.BENEFIT, "Backbone with less bone toxicity than TDF.", 5,
                               refs=(BHIVA,)))
    if p.has("psychiatric"):
        if "EFV" in comps:
            out.append(finding("tolerability", Severity.EXCLUDE,
                               "History of depression, psychosis or suicidality — BHIVA recommends avoiding efavirenz.",
                               refs=(EFV_PSYCH_BHIVA, EFV_PSYCH)))
        if "RPV" in comps:
            out.append(finding("tolerability", Severity.CAUTION, "Depressive disorders are reported with rilpivirine.",
                               -10, refs=(RPV_DEPRESSION,)))
        if "DTG" in comps or "BIC" in comps:
            out.append(finding("tolerability", Severity.CAUTION,
                               "INSTIs can cause insomnia and, rarely, depression or suicidal ideation — mainly in "
                               "people with pre-existing psychiatric illness; BHIVA advises caution.", -5,
                               refs=(INSTI_PSYCH, claim("tivicay", "4.8", r"[Ss]uicidal ideation"))))
        if "DOR" in comps:
            out.append(finding("tolerability", Severity.BENEFIT,
                               "Doravirine has fewer neuropsychiatric effects than efavirenz.", 5, refs=(BHIVA,)))
    if p.has("weight"):
        if "DTG" in comps or "BIC" in comps:
            out.append(finding("tolerability", Severity.CAUTION,
                               "INSTI-based ART is associated with more weight gain, particularly with TAF.", -8,
                               refs=(WEIGHT, BHIVA)))
        if "TAF" in comps:
            out.append(finding("tolerability", Severity.CAUTION, "TAF is associated with more weight gain than TDF.", -5,
                               refs=(BHIVA,)))
        if "DOR" in comps:
            out.append(finding("tolerability", Severity.BENEFIT, "Doravirine is largely weight-neutral.", 5,
                               refs=(BHIVA,)))
    if p.has("dyslipidaemia"):
        if boosted or "EFV" in comps:
            out.append(finding("tolerability", Severity.CAUTION, "Raises cholesterol and triglycerides.", -10,
                               refs=(BHIVA,)))
        elif regimen.anchor in ("DTG", "BIC", "RAL", "DOR", "RPV"):
            out.append(finding("tolerability", Severity.BENEFIT, "Lipid-neutral third agent.", 5, refs=(BHIVA,)))
        if "TDF" in comps:
            out.append(finding("tolerability", Severity.BENEFIT, "TDF has a modest lipid-lowering effect.", 3,
                               refs=(BHIVA,)))

    if "TDF" in comps and p.age < 25:
        out.append(finding("tolerability", Severity.CAUTION,
                           "Under 25 — BHIVA recommends avoiding tenofovir disoproxil before peak bone mass.", -15,
                           refs=(TDF_YOUNG,)))
    if "ATV" in comps and p.crcl is not None and p.crcl < 60:
        out.append(finding("tolerability", Severity.CAUTION,
                           "Reduced kidney function — if a PI is needed BHIVA recommends boosted darunavir rather than "
                           "atazanavir.", -20, refs=(CKD_PI, CKD_STOP)))
    if "AZT" in comps:
        out.append(finding("tolerability", Severity.CAUTION,
                           "Zidovudine: anaemia, neutropenia, lipoatrophy and twice-daily dosing.", -10,
                           refs=(AZT_HAEM,)))
    if "EFV" in comps and not p.has("psychiatric"):
        out.append(finding("tolerability", Severity.CAUTION,
                           "Efavirenz commonly causes dizziness, abnormal dreams and rash early in treatment.", -5,
                           refs=(claim("efavirenz", "4.8", r"[Aa]bnormal dreams"),)))
    if "ATV" in comps:
        out.append(finding("tolerability", Severity.INFO,
                           "Atazanavir causes unconjugated hyperbilirubinaemia (sometimes jaundice).",
                           refs=(ATV_BILI,)))
    return out
