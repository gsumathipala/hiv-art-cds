"""Patient-level alerts that are not about one regimen."""
from __future__ import annotations

from typing import List, Optional

from ..knowledge.guidelines import BHIVA_ART, BHIVA_HEPATITIS, BHIVA_MONITORING, BHIVA_PREGNANCY, BHIVA_TB
from ..models import Alert, LabResult, PatientProfile, Pregnancy, RegimenAssessment, TreatmentStatus, guideline
from ..knowledge.citations import bhiva
from .resistance import ResistanceReport


def patient_alerts(p: PatientProfile, res: Optional[ResistanceReport],
                   viable: List[RegimenAssessment]) -> List[Alert]:
    a: List[Alert] = []
    add = lambda level, msg, *refs: a.append(Alert(level, msg, tuple(refs)))  # noqa: E731

    if not viable:
        mvc = {"R5": "maraviroc is an option (R5 tropism)", "X4": "maraviroc is NOT an option (X4 tropism)",
               "dual/mixed": "maraviroc is NOT an option (dual/mixed tropism)"}.get(
            p.tropism, "maraviroc needs a tropism test first")
        add("critical", "No regimen in this tool meets all constraints. Discuss at the HIV MDT / resistance virtual "
            f"clinic. Agents for multiclass resistance include etravirine, fostemsavir and lenacapavir; {mvc}.",
            guideline(BHIVA_ART))
    if p.age < 18:
        add("critical", "This tool covers adults. Follow CHIVA/PENTA guidance for children and adolescents.")
    if p.weight_kg is not None and p.weight_kg < 40:
        add("warning", "Weight below 40 kg — several fixed-dose combinations have minimum weights; check SmPC §4.2.")
    if p.has("crypto_meningitis"):
        add("critical", "Cryptococcal meningitis: defer ART for 4–6 weeks after starting antifungal treatment — early ART "
            "increased mortality (COAT trial).", guideline(BHIVA_ART))
    if p.has("active_tb"):
        add("warning", "Active TB: start ART within 2 weeks of TB treatment if CD4 < 50, otherwise by 8 weeks. Watch for "
            "IRIS. Check every rifamycin interaction.", guideline(BHIVA_TB))
        if not (p.takes("rifampicin") or p.takes("rifabutin")):
            add("info", "Active TB without a rifamycin selected — add rifampicin or rifabutin to the co-medications so "
                "interactions are assessed.")

    if p.status is TreatmentStatus.FAILURE:
        if not p.genotype_available:
            add("critical", "Request a resistance test (RT/protease, plus integrase if INSTI-exposed) while the patient is "
                "still on the failing regimen or within 4 weeks of stopping.", guideline(BHIVA_ART))
        add("info", "Before switching: review adherence, drug and food interactions, tolerability and the full ART and "
            "resistance history.", guideline(BHIVA_ART))
        if p.viral_load is not None and p.viral_load < 200:
            add("warning", "HIV RNA < 200 copies/mL — confirm virological failure (repeat test) before changing therapy.",
                guideline(BHIVA_ART))
    if p.status is TreatmentStatus.SUPPRESSED:
        add("info", "If the current regimen is effective and tolerated, a switch is optional. A new regimen must be fully "
            "active against every previously documented mutation.", guideline(BHIVA_ART))
        if p.viral_load is not None and p.viral_load >= 200:
            add("warning", f"HIV RNA {p.viral_load:,} copies/mL is not suppression — consider the 'virological failure' "
                "scenario.")
    if p.status is TreatmentStatus.NAIVE and not p.genotype_available and not p.rapid_start:
        add("info", "Baseline resistance test recommended before starting ART (add integrase if there was CAB-LA PrEP).",
            guideline(BHIVA_ART))
    if p.cab_prep_exposure:
        add("warning", "Previous long-acting cabotegravir PrEP: request an integrase genotype; HIV RNA testing may be "
            "needed to diagnose infection, and serology can be delayed.", guideline(BHIVA_ART))

    if p.hbsag is LabResult.UNKNOWN:
        add("warning", "Hepatitis B status unknown — check HBsAg, anti-HBc and anti-HBs; vaccinate if non-immune.",
            guideline(BHIVA_HEPATITIS))
    if p.hla_b5701 is LabResult.UNKNOWN:
        add("info", "HLA-B*57:01 not tested — required before any abacavir-containing regimen.")
    if p.hcv:
        add("info", "Hepatitis C: treat HCV; add the planned direct-acting antiviral to the co-medications to check "
            "interactions.", guideline(BHIVA_HEPATITIS))
    if p.cd4 is not None:
        if p.cd4 < 200:
            add("warning", "CD4 < 200: start co-trimoxazole prophylaxis against Pneumocystis; screen for TB.",
                guideline(BHIVA_MONITORING))
        if p.cd4 < 100:
            add("warning", "CD4 < 100: screen serum cryptococcal antigen; consider CMV retinopathy screening.",
                guideline(BHIVA_MONITORING))

    if p.pregnancy is Pregnancy.PREGNANT:
        add("info", "Pregnancy: resistance testing (including integrase) before starting; dolutegravir- or "
            "darunavir/ritonavir-based ART can start before results. Monitor HIV RNA through pregnancy, at 36 weeks and "
            "at delivery.", bhiva("bhiva_pregnancy", "8.5", r"resistance testing \(including integrase resistance\) "
                                  r"should be undertaken prior to initiation of treatment"))
    if p.breastfeeding:
        add("info", "Breastfeeding with sustained suppression can be supported with shared decision-making and monthly "
            "maternal and infant monitoring.", guideline(BHIVA_PREGNANCY))
    if 40 <= p.age <= 75 and not p.has("cvd"):
        add("info", "Cardiovascular prevention: consider statin therapy for people with HIV aged 40–75 (REPRIEVE); check "
            "the statin against the chosen regimen.", guideline(BHIVA_ART))
    if p.prefers_long_acting and p.status is not TreatmentStatus.SUPPRESSED:
        add("info", "Long-acting cabotegravir + rilpivirine is licensed only for people already suppressed on oral ART.")
    if res is not None:
        if res.unrecognised:
            add("warning", "Not valid mutation notation (ignored): " + ", ".join(res.unrecognised) + ".")
        if res.source == "local":
            add("info", "Resistance scored with the local teaching approximation. Tick 'Use Stanford HIVdb' for the "
                "full HIVdb algorithm" + (" — these mutations are not in the local table: "
                                         + ", ".join(res.not_in_local_table) if res.not_in_local_table else "") + ".")
        else:
            add("info", f"Resistance scored by {res.version} (cumulative genotype).")
        for w in res.warnings:
            add("warning", w)
        if res.minority:
            add("info", f"Minority variants below the {p.minority_threshold:g}% threshold, reported but not scored: "
                + ", ".join(res.minority) + ". Low-frequency NNRTI or INSTI variants can still matter clinically.")
        if res.archived_only:
            add("info", "Archived (proviral DNA) mutations not seen in plasma: " + ", ".join(res.archived_only)
                + ". They are included in the scoring; proviral testing can miss archived mutations, so a negative "
                "result does not exclude them.")
        if len(res.resistant_classes()) >= 2:
            add("warning", "Resistance in two or more drug classes — discuss at the HIV MDT / resistance virtual clinic.",
                guideline(BHIVA_ART))
    return a
