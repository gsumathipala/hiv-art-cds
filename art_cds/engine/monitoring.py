"""A monitoring plan for a chosen regimen."""
from __future__ import annotations

from typing import List

from ..knowledge.drugs import CYTIDINE, TENOFOVIR
from ..knowledge.regimens import Regimen
from ..models import LabResult, PatientProfile, Pregnancy, TreatmentStatus


def monitoring_plan(regimen: Regimen, p: PatientProfile) -> List[str]:
    comps = set(regimen.components)
    plan: List[str] = []
    if regimen.long_acting:
        plan.append("HIV RNA every 2 months for the first 6–12 months, then every 4–6 months if no risk factors "
                    "(BHIVA 2025 §5.11).")
        plan.append("Injections within ±7 days of the target date; agree a plan for missed injections (oral bridging).")
    elif p.status is TreatmentStatus.SUPPRESSED:
        plan.append("HIV RNA 4–8 weeks after the switch, then every 3–6 months.")
    else:
        plan.append("HIV RNA at 2–4 weeks and monthly until < 50 copies/mL, then every 3–6 months.")
    if p.cd4 is None or p.cd4 < 350:
        plan.append("CD4 every 3–6 months until above 350 cells/mm³ with suppressed viral load.")
    if "TDF" in comps:
        plan.append("Tenofovir disoproxil: creatinine/eGFR, urine protein:creatinine ratio and phosphate at baseline, "
                    "4 weeks, then every 6–12 months; bone health assessment if at risk.")
    if "TAF" in comps:
        plan.append("Renal function and urinalysis every 6–12 months; weight and lipids annually.")
    if "ABC" in comps:
        plan.append("Abacavir: counsel on hypersensitivity (fever, rash, GI or respiratory symptoms) — stop and never "
                    "rechallenge.")
    if "AZT" in comps:
        plan.append("Zidovudine: full blood count at 4, 8 and 12 weeks (anaemia, neutropenia).")
    if "EFV" in comps:
        plan.append("Efavirenz: liver function, mood and sleep at each visit; lipids.")
    if "RPV" in comps and not regimen.long_acting:
        plan.append("Rilpivirine: take with a meal; avoid proton pump inhibitors; screen mood.")
    if regimen.boosted:
        plan.append("Boosted regimen: lipids and liver function; review every new prescription and OTC/herbal product "
                    "for CYP3A interactions.")
    if "ATV" in comps:
        plan.append("Atazanavir: bilirubin; ask about renal colic or biliary symptoms.")
    if comps & {"DTG", "BIC", "RAL"}:
        plan.append("INSTI: weight/BMI at each visit; separate from antacids and mineral supplements as the SmPC directs.")
    if p.hbsag is LabResult.POSITIVE and comps & TENOFOVIR and comps & CYTIDINE:
        plan.append("Hepatitis B: ALT and HBV DNA every 3–6 months; never stop the HBV-active drugs without alternative "
                    "cover.")
    if p.pregnancy is Pregnancy.PREGNANT:
        if p.status is TreatmentStatus.SUPPRESSED:
            plan.append("Pregnancy (suppressed at conception): HIV RNA every 2 months, at 36 weeks and at delivery; CD4 "
                        "at baseline in the first trimester (BHIVA pregnancy 2025).")
        else:
            plan.append("Pregnancy (starting or switching ART): HIV RNA and toxicity tests at 2 weeks, monthly until "
                        "undetectable, then at least every 2 months, at 36 weeks and at delivery (BHIVA pregnancy 2025).")
    plan.append("Annual: lipids, HbA1c, cardiovascular risk (QRISK3), and renal and liver function.")
    return plan
