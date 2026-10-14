"""Licensed indication (SmPC §4.1): who each product is authorised for in the UK."""
from __future__ import annotations

from ...knowledge.guidelines import NICE_TA757
from ...models import Severity, TreatmentStatus, guideline
from .base import bhiva, claim, finding, rule

DTG_3TC_VL = bhiva("bhiva_art", "5", r"Baseline viral load <500,000 copies/mL")
LA_CRITERIA = bhiva("bhiva_art", "5.11", r"Have been on ART for at least 3.6 months and are virally suppressed")
LA_A6 = bhiva("bhiva_art", "5.11", r"body mass index \(BMI\) >30 kg/m2 and subtype A6")

RPV_VL = {
    "edurant": claim("edurant", "4.1", r"viral load ≤ 100,000"),
    "odefsey": claim("odefsey", "4.1", r"viral load ≤ 100,000"),
    "eviplera": claim("eviplera", "4.1", r"viral load ≤ 100,000"),
}
NNRTI_HISTORY = {
    "pifeltro": claim("pifeltro", "4.1", r"without past or present evidence of resistance to the non-nucleoside"),
    "delstrigo": claim("delstrigo", "4.1", r"without past or present evidence of resistance to the non-nucleoside"),
}
DOVATO = claim("dovato", "4.1", r"no known or suspected resistance to the integrase inhibitor class, or lamivudine")
JULUCA = claim("juluca", "4.1", r"virologically-suppressed", r"no history of virological failure")
CAB_RPV = claim("vocabria_inj", "4.1", r"virologically suppressed", r"no prior virological failure")
EFV_FDC = claim("efv_ftc_tdf", "4.1", r"virologic suppression", r"must not have experienced virological failure")
BIKTARVY = claim("biktarvy", "4.1", r"without present or past evidence of viral resistance to bictegravir or tenofovir")


@rule("indication", "Licensed indication")
def indication(regimen, ctx):
    p = ctx.patient
    out = []
    naive = p.status is TreatmentStatus.NAIVE
    failed = p.failed_classes

    if regimen.id in ("rpv_ftc_taf", "rpv_ftc_tdf"):
        product = regimen.products[0]
        if p.viral_load is not None and p.viral_load > 100_000:
            out.append(finding("indication", Severity.EXCLUDE,
                               f"HIV RNA {p.viral_load:,} copies/mL — rilpivirine is licensed only with viral load "
                               "≤ 100,000 copies/mL (higher virological failure above this).", refs=(RPV_VL[product],)))
        elif p.viral_load is None and naive:
            out.append(finding("indication", Severity.CAUTION,
                               "Viral load unknown — rilpivirine requires HIV RNA ≤ 100,000 copies/mL.", -25,
                               refs=(RPV_VL[product],)))
        if "NNRTI" in failed:
            out.append(finding("indication", Severity.EXCLUDE,
                               "Previous NNRTI failure — not licensed where NNRTI resistance mutations may be present.",
                               refs=(RPV_VL[product],)))

    for key in ("pifeltro", "delstrigo"):
        if key in regimen.products and "NNRTI" in failed:
            out.append(finding("indication", Severity.EXCLUDE,
                               "Previous NNRTI failure — doravirine is licensed only without past or present NNRTI "
                               "resistance.", refs=(NNRTI_HISTORY[key],)))

    if regimen.id == "dtg_3tc":
        if failed & {"NRTI", "INSTI"}:
            out.append(finding("indication", Severity.EXCLUDE,
                               "Previous NRTI/INSTI failure — Dovato needs no known or suspected integrase or "
                               "lamivudine resistance.", refs=(DOVATO,)))
        elif naive and not p.genotype_available:
            out.append(finding("indication", Severity.EXCLUDE,
                               "No baseline resistance test — Dovato requires lamivudine and integrase resistance to be "
                               "excluded first.", refs=(DOVATO,)))
        if naive and p.viral_load is not None and p.viral_load > 500_000:
            out.append(finding("indication", Severity.EXCLUDE,
                               "HIV RNA > 500,000 copies/mL — BHIVA recommends DTG/3TC first line only below "
                               "500,000 copies/mL.", refs=(DTG_3TC_VL,)))

    if regimen.id == "dtg_rpv" and (failed or (p.viral_load is not None and p.viral_load >= 50)):
        out.append(finding("indication", Severity.EXCLUDE,
                           "Juluca is licensed only for adults suppressed < 50 copies/mL for ≥ 6 months with no history "
                           "of virological failure.", refs=(JULUCA,)))

    if regimen.long_acting:
        if failed:
            out.append(finding("indication", Severity.EXCLUDE,
                               "Cabotegravir + rilpivirine LA requires no prior virological failure with NNRTIs or "
                               "INSTIs.", refs=(CAB_RPV, guideline(NICE_TA757))))
        if p.viral_load is not None and p.viral_load >= 50:
            out.append(finding("indication", Severity.EXCLUDE,
                               "Licensed only for people suppressed below 50 copies/mL.", refs=(CAB_RPV,)))
        out.append(finding("indication", Severity.INFO,
                           "BHIVA criteria: on ART for at least 3–6 months, motivated for injections, able to attend "
                           "2-monthly, and not the combination of BMI > 30 kg/m² with HIV-1 subtype A6.",
                           refs=(LA_CRITERIA, LA_A6, guideline(NICE_TA757))))

    if regimen.id == "efv_ftc_tdf" and (p.status is not TreatmentStatus.SUPPRESSED or failed):
        out.append(finding("indication", Severity.EXCLUDE,
                           "The efavirenz/emtricitabine/tenofovir disoproxil tablet is licensed only for switching "
                           "people suppressed < 50 copies/mL for > 3 months with no previous virological failure.",
                           refs=(EFV_FDC,)))

    if regimen.id == "bic_ftc_taf" and "INSTI" in failed and not p.genotype_available:
        out.append(finding("indication", Severity.EXCLUDE,
                           "Previous INSTI failure without a genotype — Biktarvy is licensed only without present or "
                           "past bictegravir or tenofovir resistance.", refs=(BIKTARVY,)))
    return out
