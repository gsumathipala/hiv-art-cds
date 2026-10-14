"""Clinical scenario and treatment history (BHIVA adult ART guidelines 2025, sections 5 and 7)."""
from __future__ import annotations

from ...knowledge.drugs import HIGH_BARRIER, INSTI, LOW_BARRIER, NNRTI, drug_class
from ...knowledge.guidelines import BHIVA_ART
from ...models import Severity, TreatmentStatus, guideline
from .base import bhiva, finding, rule

_A = "bhiva_art"
# Tenofovir + FTC/3TC with dolutegravir, bictegravir or boosted darunavir: BHIVA's choice for rapid start,
# transmitted resistance and very high viral load.
HIGH_BARRIER_TXF = {"bic_ftc_taf", "dtg_ftc_taf", "dtg_ftc_tdf", "drvc_ftc_taf", "drvc_ftc_tdf", "drvr_ftc_taf",
                    "drvr_ftc_tdf"}

RAPID = bhiva(_A, "5.6", r"where ART is commenced prior to baseline resistance testing")
TDR = bhiva(_A, "5.5", r"evidence of TDR should start ART containing tenofovir DX or tenofovir AF")
HIGH_VL = bhiva(_A, "5.7", r"very high viral loads \(>500,000 copies/mL\)")
PREP = bhiva(_A, "5.8", r"The ART combinations listed for rapid ART are recommended options while awaiting resistance "
                        r"testing results")
RAL_VL = bhiva(_A, "5", r"Baseline viral load less than 100,000 copies/mL")
EFV_FIRST = bhiva(_A, "5", r"May be a first-line choice in pregnancy and for people on TB treatment but not recommended "
                           r"outside these scenarios")
ABC = bhiva(_A, "5", r"tenofovir DX and tenofovir AF are not suitable and abacavir is the most clinically appropriate "
                     r"option")
NRTI_SWITCH = bhiva(_A, "5.9", r"previous NRTI resistance mutations, we recommend against switching from a boosted PI "
                               r"to an NNRTI or first-generation INSTI")
NNRTI_SWITCH = bhiva(_A, "5.9", r"any NNRTI resistance, we recommend not switching to NNRTI-based ART")
LOW_BARRIER_SWITCH = bhiva(_A, "5.9", r"particular caution when switching from a high-genetic barrier to a low-genetic "
                                      r"barrier regimen")
MDT = bhiva(_A, "7.6", r"discussion within a multidisciplinary team or referral for expert advice")


def _tenofovir_unsuitable(p) -> bool:
    return p.on_dialysis or (p.crcl is not None and p.crcl < 30) or p.has("osteoporosis")


@rule("history", "Scenario & treatment history")
def history(regimen, ctx):
    p = ctx.patient
    res = ctx.resistance
    general = guideline(BHIVA_ART)
    classes = {drug_class(c) for c in regimen.core_agents}
    anchor_classes = {drug_class(regimen.anchor)}
    naive = p.status is TreatmentStatus.NAIVE
    out = []

    if regimen.switch_only and p.status is not TreatmentStatus.SUPPRESSED:
        out.append(finding("history", Severity.EXCLUDE, "Only for switching people who are virologically suppressed.",
                           refs=(general,)))

    # ---- first-line restrictions from BHIVA Table 5.1 (pregnancy follows the pregnancy guideline instead)
    if naive and not p.is_pregnant:
        if regimen.anchor == "RAL" and p.viral_load is not None and p.viral_load >= 100_000:
            out.append(finding("history", Severity.EXCLUDE,
                               "Raltegravir is recommended first line only with baseline viral load < 100,000 copies/mL.",
                               refs=(RAL_VL,)))
        if regimen.anchor == "EFV" and not (p.takes("rifampicin") or p.has("active_tb")):
            out.append(finding("history", Severity.EXCLUDE,
                               "Efavirenz is a first-line choice only in pregnancy or with TB treatment.",
                               refs=(EFV_FIRST,)))
    if "ABC" in regimen.components and not p.is_pregnant and p.status is not TreatmentStatus.FAILURE:
        if _tenofovir_unsuitable(p):
            out.append(finding("history", Severity.INFO,
                               "Tenofovir is unsuitable here, so abacavir may be the most appropriate second NRTI.",
                               refs=(ABC,)))
        else:
            out.append(finding("history", Severity.CAUTION,
                               "BHIVA 2025: use abacavir only where a three-drug regimen is needed and tenofovir DX/AF "
                               "are unsuitable; people on abacavir should be offered a switch.", -30, refs=(ABC,)))

    if naive:
        if p.rapid_start:
            if regimen.id in HIGH_BARRIER_TXF:
                out.append(finding("history", Severity.BENEFIT,
                                   "Suitable for starting before resistance, HBV and HLA results: tenofovir + FTC/3TC "
                                   "with dolutegravir, bictegravir or boosted darunavir.", 5, refs=(RAPID,)))
            else:
                out.append(finding("history", Severity.EXCLUDE,
                                   "Not recommended for starting before baseline resistance testing.", refs=(RAPID,)))
        if p.viral_load is not None and p.viral_load > 500_000 and regimen.id not in HIGH_BARRIER_TXF:
            out.append(finding("history", Severity.CAUTION,
                               "Viral load > 500,000 copies/mL — BHIVA suggests a high-barrier three-drug regimen "
                               "(tenofovir + FTC/3TC with dolutegravir, bictegravir or boosted darunavir).", -15,
                               refs=(HIGH_VL,)))
        if res is not None and res.any_mutations and regimen.id not in HIGH_BARRIER_TXF:
            out.append(finding("history", Severity.CAUTION,
                               "Transmitted drug resistance — BHIVA recommends tenofovir + FTC/3TC with dolutegravir, "
                               "bictegravir or boosted darunavir.", -20, refs=(TDR,)))
        if p.cab_prep_exposure and not p.genotype_available:
            if classes & {INSTI}:
                out.append(finding("history", Severity.CAUTION,
                                   "Previous long-acting cabotegravir PrEP — integrase resistance is possible; get an "
                                   "integrase genotype. (Preferring boosted darunavir until it returns is expert opinion; "
                                   "BHIVA recommends the rapid-start combinations pending results.)", -15,
                                   refs=(PREP,)))
            elif regimen.anchor == "DRV":
                out.append(finding("history", Severity.BENEFIT,
                                   "Boosted darunavir does not depend on integrase susceptibility while the integrase "
                                   "genotype is pending.", 10, refs=(PREP,)))
        if not p.genotype_available and not p.rapid_start and NNRTI in classes:
            out.append(finding("history", Severity.CAUTION,
                               "No baseline genotype — transmitted NNRTI resistance is the commonest; test before "
                               "NNRTI-based ART.", -20, refs=(TDR,)))

    if p.status is TreatmentStatus.SUPPRESSED:
        nnrti_resistance = "NNRTI" in p.failed_classes or (
            res is not None and any(res.level(d) >= 3 for d in ("EFV", "RPV", "DOR", "ETR")))
        if nnrti_resistance and NNRTI in classes:
            out.append(finding("history", Severity.EXCLUDE,
                               "NNRTI resistance or previous NNRTI failure — do not switch to NNRTI-based ART.",
                               refs=(NNRTI_SWITCH,)))
        if "NRTI" in p.failed_classes and (NNRTI in classes or regimen.anchor == "RAL"):
            out.append(finding("history", Severity.EXCLUDE,
                               "Previous NRTI resistance — do not switch to an NNRTI or first-generation INSTI anchor.",
                               refs=(NRTI_SWITCH,)))
        if p.failed_classes and not p.genotype_available:
            overlap = classes & set(p.failed_classes)
            if overlap:
                out.append(finding("history", Severity.CAUTION,
                                   f"Switching to a class with previous failure ({', '.join(sorted(overlap))}) without "
                                   "historical genotypes — archived resistance may be present.", -25,
                                   refs=(LOW_BARRIER_SWITCH,)))

    if p.status is TreatmentStatus.FAILURE:
        if regimen.dual and regimen.id != "drvr_dtg":
            out.append(finding("history", Severity.EXCLUDE,
                               "Two-drug regimens are not appropriate during virological failure.", refs=(general,)))
        if regimen.anchor in HIGH_BARRIER:
            out.append(finding("history", Severity.BENEFIT,
                               "High genetic barrier anchor — favoured after virological failure.", 10, refs=(general,)))
        if regimen.anchor in LOW_BARRIER:
            out.append(finding("history", Severity.CAUTION,
                               "Low genetic barrier anchor — avoid after failure unless fully active with two other "
                               "fully active drugs.", -20, refs=(general,)))
        if not p.genotype_available:
            if "NNRTI" in p.failed_classes and NNRTI in classes:
                out.append(finding("history", Severity.EXCLUDE,
                                   "Previous NNRTI failure without a genotype — assume NNRTI resistance.",
                                   refs=(general,)))
            if "INSTI" in p.failed_classes:
                if regimen.anchor in ("RAL", "BIC") or "CAB" in regimen.components:
                    out.append(finding("history", Severity.EXCLUDE,
                                       "Previous INSTI failure without a genotype — first-generation or cross-resistant "
                                       "INSTIs are not appropriate.", refs=(general,)))
                elif "DTG" in regimen.components:
                    out.append(finding("history", Severity.CAUTION,
                                       "Previous INSTI failure — obtain an integrase genotype; if dolutegravir is used, "
                                       "give it twice daily.", -35, refs=(general,),
                                       dose_change="Dolutegravir 50 mg twice daily after INSTI failure"))
            if regimen.nrtis and p.failed_classes and regimen.anchor in HIGH_BARRIER:
                out.append(finding("history", Severity.INFO,
                                   "M184V/I is likely after failure, so emtricitabine/lamivudine may be only partly "
                                   "active; recycling tenofovir with dolutegravir or boosted darunavir is supported by "
                                   "NADIA and other trials.", refs=(general,)))
        elif not anchor_classes.isdisjoint(p.failed_classes):
            if res is not None and res.level(regimen.anchor) <= 1:
                out.append(finding("history", Severity.CAUTION,
                                   "The anchor's class has failed before but the current genotype shows no resistance — "
                                   "archived mutations may be missed.", -15, refs=(general,)))
        if len(p.failed_classes - {"NRTI"}) >= 2:
            out.append(finding("history", Severity.INFO, "Multi-class failure — discuss at the HIV MDT.", refs=(MDT,)))
    return out
