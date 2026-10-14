"""Co-infections beyond HBsAg: HBV serology detail, hepatitis C treatment pairing, tuberculosis."""
from __future__ import annotations

from ...knowledge.interactions import AVOID, COMEDICATIONS_BY_KEY, CONTRAINDICATED, lookup
from ...knowledge.drugs import CYTIDINE, TENOFOVIR
from ...models import LabResult, Severity
from .base import bhiva, finding, rule

_A, _TB = "bhiva_art", "bhiva_tb"
REACTIVATION_LA = bhiva(_A, "5.11", r"Are not considered at significant risk of hepatitis B reactivation or re-infection")
REACTIVATION_DTG_RPV = bhiva(_A, "5.10", r"Who are considered at risk of hepatitis B reactivation")
DTG_3TC_HBV = bhiva(_A, "5.10", r"Who need a tenofovir-containing regimen for the treatment or prevention of "
                                r"hepatitis B")
TB_FIRST = bhiva(_TB, "8", r"We recommend efavirenz \(standard dose\) in combination with tenofovir disoproxil and "
                           r"emtricitabine as first-line ART for people taking rifampicin-based TB treatment")
TB_ALT = bhiva(_TB, "8", r"We suggest that raltegravir or dolutegravir may be used as alternatives to efavirenz")
TB_COBI = bhiva(_TB, "8", r"We recommend against the use of cobicistat with rifampicin or rifabutin")
TB_AGAINST = bhiva(_TB, "8", r"We recommend against the use of fixed-dose combinations containing tenofovir "
                             r"alafenamide or bictegravir, and dual therapy with cabotegravir/rilpivirine or "
                             r"dolutegravir/lamivudine")

DAAS = ("sof_vel", "glec_pib", "elbasvir", "ledipasvir")


def isolated_anti_hbc(p) -> bool:
    return p.hbsag is LabResult.NEGATIVE and p.anti_hbc is LabResult.POSITIVE and p.anti_hbs is not LabResult.POSITIVE


def hbv_non_immune(p) -> bool:
    return p.hbsag is LabResult.NEGATIVE and p.anti_hbc is LabResult.NEGATIVE and p.anti_hbs is LabResult.NEGATIVE


def on_rifamycin(p) -> bool:
    return p.takes("rifampicin") or p.takes("rifabutin") or p.takes("rifapentine")


@rule("coinfection", "Co-infections")
def coinfection(regimen, ctx):
    p = ctx.patient
    comps = set(regimen.components)
    hbv_active = bool(comps & TENOFOVIR) and bool(comps & CYTIDINE)
    out = []

    # ---- hepatitis B serology beyond HBsAg
    occult = p.hbsag is not LabResult.POSITIVE and (p.hbv_dna or 0) > 0
    if occult and not hbv_active:
        out.append(finding("coinfection", Severity.EXCLUDE,
                           "HBV DNA detectable without HBsAg (occult hepatitis B) — the regimen must contain tenofovir "
                           "plus emtricitabine/lamivudine.", refs=(DTG_3TC_HBV,)))
    elif isolated_anti_hbc(p) and not hbv_active:
        if regimen.long_acting:
            out.append(finding("coinfection", Severity.CAUTION,
                               "Isolated anti-HBc — risk of hepatitis B reactivation without tenofovir; BHIVA advises "
                               "long-acting CAB/RPV only for people not at significant risk.", -30,
                               refs=(REACTIVATION_LA,)))
        elif regimen.id == "dtg_rpv":
            out.append(finding("coinfection", Severity.CAUTION,
                               "Isolated anti-HBc — DTG/RPV is not suitable for people at risk of HBV reactivation.",
                               -30, refs=(REACTIVATION_DTG_RPV,)))
        else:
            out.append(finding("coinfection", Severity.CAUTION,
                               "Isolated anti-HBc — check HBV DNA; without tenofovir there is a risk of reactivation.",
                               -15, refs=(DTG_3TC_HBV,)))
    if hbv_non_immune(p) and regimen.long_acting:
        out.append(finding("coinfection", Severity.CAUTION,
                           "Not immune to hepatitis B — vaccinate before relying on a tenofovir-free injectable "
                           "regimen (risk of HBV infection).", -10, refs=(REACTIVATION_LA,)))

    # ---- hepatitis C: which direct-acting antivirals fit this regimen
    if p.hcv:
        fits = []
        for daa in DAAS:
            problems = [lookup(daa, c) for c in comps]
            if not any(i and i.severity in (CONTRAINDICATED, AVOID) for i in problems):
                fits.append(COMEDICATIONS_BY_KEY[daa].label)
        if fits:
            out.append(finding("coinfection", Severity.INFO, "Compatible hepatitis C regimens: " + "; ".join(fits)
                               + " (per the interaction table)."))
        else:
            out.append(finding("coinfection", Severity.CAUTION,
                               "No pan-genotypic hepatitis C regimen in the interaction table is compatible.", -10))

    # ---- tuberculosis (BHIVA TB 2018, 2023 interim update)
    if on_rifamycin(p) or p.has("active_tb"):
        if "COBI" in comps and (p.takes("rifampicin") or p.takes("rifabutin")):
            out.append(finding("coinfection", Severity.EXCLUDE,
                               "BHIVA recommends against cobicistat with rifampicin or rifabutin.", refs=(TB_COBI,)))
        if "TAF" in comps or "BIC" in comps or regimen.id in ("cab_rpv_la", "dtg_3tc"):
            out.append(finding("coinfection", Severity.EXCLUDE,
                               "With TB treatment, BHIVA recommends against TAF- or bictegravir-containing "
                               "combinations and dual CAB/RPV or DTG/3TC until clinical outcome data exist.",
                               refs=(TB_AGAINST,)))
        if p.takes("rifampicin"):
            if regimen.id == "efv_plus_ftc_tdf":
                out.append(finding("coinfection", Severity.BENEFIT,
                                   "BHIVA's first-line choice with rifampicin-based TB treatment.", 20, refs=(TB_FIRST,)))
            elif regimen.anchor in ("DTG", "RAL"):
                out.append(finding("coinfection", Severity.INFO,
                                   "BHIVA suggests dolutegravir or raltegravir as alternatives to efavirenz with "
                                   "rifampicin.", refs=(TB_ALT,)))
    return out
