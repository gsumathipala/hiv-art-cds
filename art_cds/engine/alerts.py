"""Patient-level alerts that are not about one regimen."""
from __future__ import annotations

from typing import List, Optional

from ..knowledge.guidelines import BHIVA_ART, BHIVA_HEPATITIS, BHIVA_MONITORING, BHIVA_PREGNANCY, BHIVA_TB
from ..models import Alert, LabResult, PatientProfile, Pregnancy, RegimenAssessment, TreatmentStatus, guideline
from ..knowledge.citations import bhiva
from .resistance import ResistanceReport
from .virology import classify


# Citations (module level so they register once and are verified by tools/verify_smpc.py)
CRYPTO_ART = bhiva("bhiva_art", "5.6", r"favour deferred \(after 2 weeks\) intitiation of ART during treatment of "
                                       r"cryptococcal meningitis")
TB_CNS = bhiva("bhiva_tb", "8", r"against the early initiation of ART in individuals with central nervous system "
                                r"\(CNS\) TB \(can be delayed for 8 weeks\)")
TB_4_WEEKS = bhiva("bhiva_tb", "8", r"offered ART as soon as is practicable and within 4 weeks of the TB diagnosis")
TB_2_WEEKS = bhiva("bhiva_tb", "8", r"CD4 counts <50 cells/mm3, treatment should be offered within 2 weeks")
TB_RECONCILE = bhiva("bhiva_tb", "8", r"complete medicines reconciliation prior to starting treatment for either TB or")
TB_NO_INTERRUPT = bhiva("bhiva_tb", "8", r"develop TB on ART with undetectable HIV viral loads do not interrupt their ART")
PREG_RESISTANCE = bhiva("bhiva_pregnancy", "8.5", r"resistance testing \(including integrase resistance\) should be "
                                                 r"undertaken prior to initiation of treatment")


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
        add("critical", "Cryptococcal meningitis: do not start ART rapidly. Most studies favour starting after the first "
            "2 weeks of antifungal treatment, timed case by case with clinical and CSF assessment.",
            CRYPTO_ART)
    if p.crag is LabResult.POSITIVE and not p.has("crypto_meningitis"):
        add("critical", "Serum CrAg positive: exclude meningitis with a lumbar puncture before starting ART, and treat "
            "accordingly.")
    elif p.cd4 is not None and p.cd4 < 100 and p.crag is LabResult.UNKNOWN:
        add("warning", "CD4 < 100 and no serum CrAg result — screen for cryptococcal antigen before starting ART.")
    if p.has("active_tb") or p.has("cns_tb"):
        if p.has("cns_tb"):
            add("critical", "CNS tuberculosis: BHIVA recommends against early ART — it can be delayed for 8 weeks.",
                TB_CNS)
        else:
            timing = ("within 2 weeks of starting TB treatment (CD4 < 50)" if (p.cd4 or 999) < 50
                      else "as soon as practicable and within 4 weeks of the TB diagnosis")
            add("warning", f"Active TB: start ART {timing}. Watch for paradoxical TB-IRIS.",
                TB_4_WEEKS, TB_2_WEEKS)
        add("info", "Do a complete medicines reconciliation before starting treatment for either TB or HIV.",
            TB_RECONCILE)
        if not (p.takes("rifampicin") or p.takes("rifabutin") or p.takes("rifapentine")):
            add("info", "TB recorded but no rifamycin selected — add rifampicin, rifabutin or rifapentine to the "
                "co-medications so the interactions are assessed.")
        if p.status is TreatmentStatus.SUPPRESSED:
            add("info", "TB diagnosed on suppressive ART: do not interrupt ART; adjust the rifamycin or the regimen "
                "instead.", TB_NO_INTERRUPT)

    vir = classify(p.vl_history, p.art_history)
    if vir is not None:
        level = {"confirmed virological failure": "critical", "suspected virological failure": "warning",
                 "low-level viraemia": "warning"}.get(vir.status, "info")
        add(level, f"Viral-load course: {vir.status}. {vir.message}", *vir.refs)
        if vir.status == "confirmed virological failure" and p.status is not TreatmentStatus.FAILURE:
            add("critical", "The viral-load history shows confirmed failure — reassess using the 'virological "
                "failure' scenario.")
    current = [e for e in p.art_history if e.current]
    if current and current[0].components:
        add("info", "Current regimen: " + " + ".join(current[0].components)
            + (f" since {current[0].start}" if current[0].start else "") + ".")

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

    if p.virus_type != "HIV-1":
        from .rules.hiv2 import EXPERT, MVC_HIV2
        add("critical", f"{p.virus_type}: manage with an HIV-2 expert. NNRTIs are inactive against HIV-2; maraviroc and "
            "enfuvirtide are not reliable options. HIV-2 needs an HIV-2-specific viral load assay (HIV-1 assays do not "
            "detect it), and HIV-1 resistance algorithms do not apply to HIV-2 genotypes"
            + (" — the HIV-1 genotype was still scored for the HIV-1 component." if p.virus_type == "HIV-1/HIV-2"
               else " — resistance scoring has been switched off."), EXPERT, MVC_HIV2)

    if p.medicines_text:
        from ..knowledge.medicines import reconcile
        unknown = [r.text for r in reconcile(p.medicines_text) if not r.key]
        if unknown:
            add("warning", "Not in this tool's interaction table — check with the Liverpool HIV interaction checker "
                "(hiv-druginteractions.org): " + "; ".join(unknown) + ".")

    if p.hbsag is LabResult.UNKNOWN:
        add("warning", "Hepatitis B status unknown — check HBsAg, anti-HBc and anti-HBs; vaccinate if non-immune.",
            guideline(BHIVA_HEPATITIS))
    elif p.hbsag is LabResult.NEGATIVE:
        if p.anti_hbc is LabResult.POSITIVE and p.anti_hbs is not LabResult.POSITIVE:
            add("warning", "Isolated anti-HBc (HBsAg negative, anti-HBs negative) — check HBV DNA for occult hepatitis B "
                "and consider keeping tenofovir in the regimen.", guideline(BHIVA_HEPATITIS))
        elif p.anti_hbc is LabResult.UNKNOWN or p.anti_hbs is LabResult.UNKNOWN:
            add("info", "HBsAg negative — complete the panel with anti-HBc and anti-HBs before a tenofovir-free regimen.",
                guideline(BHIVA_HEPATITIS))
        elif p.anti_hbs is LabResult.NEGATIVE and p.anti_hbc is LabResult.NEGATIVE:
            add("info", "Not immune to hepatitis B — vaccinate (double-dose schedule with HIV).",
                guideline(BHIVA_HEPATITIS))
    if p.hbsag is LabResult.POSITIVE and p.hbv_dna is None:
        add("info", "Hepatitis B: check HBV DNA, HBeAg, delta serology and assess liver fibrosis.",
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
            "at delivery.", PREG_RESISTANCE)
    if p.breastfeeding:
        add("info", "Breastfeeding with sustained suppression can be supported with shared decision-making and monthly "
            "maternal and infant monitoring.", guideline(BHIVA_PREGNANCY))
    if 40 <= p.age <= 75 and not p.has("cvd"):
        if p.qrisk3 is not None:
            add("info", f"QRISK3 {p.qrisk3:g}% (10-year). QRISK3 has no term for HIV and underestimates risk in people "
                "with HIV.")
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
