"""Clinical calculators: kidney function, Child-Pugh, QRISK3, FRAX thresholds.

Equations (verified against the National Kidney Foundation's published forms):
  * CKD-EPI 2021 creatinine (race-free):
      142 × min(Scr/κ,1)^α × max(Scr/κ,1)^-1.200 × 0.9938^age × 1.012 [female];
      κ 0.7 F / 0.9 M, α -0.241 F / -0.302 M, Scr in mg/dL.
  * CKD-EPI 2012 cystatin C: 133 × min(Scys/0.8,1)^-0.499 × max(Scys/0.8,1)^-1.328 × 0.996^age × 0.932 [female].
  * CKD-EPI 2021 creatinine–cystatin C: 135 × min(Scr/κ,1)^α × max(Scr/κ,1)^-0.544 × min(Scys/0.8,1)^-0.323
      × max(Scys/0.8,1)^-0.778 × 0.9961^age × 0.963 [female]; α -0.219 F / -0.144 M.
  * Cockcroft–Gault (UK, µmol/L): CrCl = (140 − age) × weight(kg) × 1.23 [male] or 1.04 [female] / creatinine.
    SmPC renal dose limits are expressed as CrCl, so this is the value the engine uses.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from . import qrisk3_raw

UMOL_PER_MG_DL = 88.42


def cockcroft_gault(age: int, weight_kg: float, female: bool, creatinine_umol: float) -> float:
    return (140 - age) * weight_kg * (1.04 if female else 1.23) / creatinine_umol


def egfr_creatinine_2021(creatinine_umol: float, age: int, female: bool) -> float:
    scr = creatinine_umol / UMOL_PER_MG_DL
    k, a = (0.7, -0.241) if female else (0.9, -0.302)
    return 142 * min(scr / k, 1) ** a * max(scr / k, 1) ** -1.200 * 0.9938 ** age * (1.012 if female else 1)


def egfr_cystatin_2012(cystatin_mg_l: float, age: int, female: bool) -> float:
    s = cystatin_mg_l / 0.8
    return 133 * min(s, 1) ** -0.499 * max(s, 1) ** -1.328 * 0.996 ** age * (0.932 if female else 1)


def egfr_combined_2021(creatinine_umol: float, cystatin_mg_l: float, age: int, female: bool) -> float:
    scr = creatinine_umol / UMOL_PER_MG_DL
    k, a = (0.7, -0.219) if female else (0.9, -0.144)
    s = cystatin_mg_l / 0.8
    return (135 * min(scr / k, 1) ** a * max(scr / k, 1) ** -0.544 * min(s, 1) ** -0.323 * max(s, 1) ** -0.778
            * 0.9961 ** age * (0.963 if female else 1))


@dataclass(frozen=True)
class KidneyFunction:
    crcl: Optional[float]
    egfr_cr: Optional[float]
    egfr_cys: Optional[float]
    egfr_combined: Optional[float]

    @property
    def note(self) -> str:
        if self.egfr_cr and self.egfr_combined and abs(self.egfr_cr - self.egfr_combined) > 15:
            return ("Creatinine- and cystatin-based estimates differ by >15 mL/min/1.73 m² — dolutegravir, bictegravir, "
                    "rilpivirine and cobicistat raise creatinine without changing GFR; prefer the combined estimate.")
        return ""


def kidney(age: int, female: bool, weight_kg: Optional[float], creatinine_umol: Optional[float],
           cystatin_mg_l: Optional[float]) -> KidneyFunction:
    crcl = cockcroft_gault(age, weight_kg, female, creatinine_umol) if weight_kg and creatinine_umol else None
    cr = egfr_creatinine_2021(creatinine_umol, age, female) if creatinine_umol else None
    cys = egfr_cystatin_2012(cystatin_mg_l, age, female) if cystatin_mg_l else None
    both = egfr_combined_2021(creatinine_umol, cystatin_mg_l, age, female) if creatinine_umol and cystatin_mg_l \
        else None
    r = lambda v: round(v, 1) if v is not None else None  # noqa: E731
    return KidneyFunction(r(crcl), r(cr), r(cys), r(both))


# ------------------------------------------------------------------ Child-Pugh
def child_pugh(bilirubin_umol: float, albumin_g_l: float, inr: float, ascites: str,
               encephalopathy: str) -> Tuple[int, str]:
    """Score and class (A 5–6, B 7–9, C 10–15). ascites/encephalopathy: none | mild | severe."""
    pts = 1 if bilirubin_umol < 34 else 2 if bilirubin_umol <= 50 else 3
    pts += 1 if albumin_g_l > 35 else 2 if albumin_g_l >= 28 else 3
    pts += 1 if inr < 1.7 else 2 if inr <= 2.3 else 3
    grade = {"none": 1, "mild": 2, "severe": 3}
    pts += grade[ascites] + grade[encephalopathy]
    return pts, "A" if pts <= 6 else "B" if pts <= 9 else "C"


# ------------------------------------------------------------------ QRISK3
ETHNICITY = ("White or not stated", "Indian", "Pakistani", "Bangladeshi", "Other Asian", "Black Caribbean",
             "Black African", "Chinese", "Other ethnic group")  # QRISK3 codes 1..9
SMOKING = ("Non-smoker", "Ex-smoker", "Light smoker (<10/day)", "Moderate smoker (10–19/day)",
           "Heavy smoker (≥20/day)")  # QRISK3 codes 0..4


@dataclass(frozen=True)
class QriskInputs:
    age: int
    female: bool
    ethnicity: int  # 1..9
    smoking: int  # 0..4
    height_cm: float
    weight_kg: float
    chol_hdl_ratio: float
    sbp: float
    sbp_sd: float = 0.0
    townsend: float = 0.0
    af: bool = False
    atypical_antipsychotic: bool = False
    corticosteroids: bool = False
    erectile_dysfunction: bool = False
    migraine: bool = False
    rheumatoid_arthritis: bool = False
    ckd_3_5: bool = False
    severe_mental_illness: bool = False
    sle: bool = False
    treated_hypertension: bool = False
    type1_diabetes: bool = False
    type2_diabetes: bool = False
    family_history_chd: bool = False


def qrisk3(i: QriskInputs) -> float:
    """10-year risk (%) by QRISK3-2017. Valid for ages 25–84."""
    if not 25 <= i.age <= 84:
        raise ValueError("QRISK3 is valid for ages 25–84.")
    bmi = i.weight_kg / (i.height_cm / 100) ** 2
    args = dict(age=i.age, b_AF=int(i.af), b_atypicalantipsy=int(i.atypical_antipsychotic),
                b_corticosteroids=int(i.corticosteroids), b_migraine=int(i.migraine), b_ra=int(i.rheumatoid_arthritis),
                b_renal=int(i.ckd_3_5), b_semi=int(i.severe_mental_illness), b_sle=int(i.sle),
                b_treatedhyp=int(i.treated_hypertension), b_type1=int(i.type1_diabetes), b_type2=int(i.type2_diabetes),
                bmi=bmi, ethrisk=i.ethnicity, fh_cvd=int(i.family_history_chd), rati=i.chol_hdl_ratio, sbp=i.sbp,
                sbps5=i.sbp_sd, smoke_cat=i.smoking, surv=10, town=i.townsend)
    if i.female:
        return qrisk3_raw.cvd_female_raw(**args)
    return qrisk3_raw.cvd_male_raw(b_impotence2=int(i.erectile_dysfunction), **args)


QRISK3_DISCLAIMER = qrisk3_raw.DISCLAIMER
HIV_CV_NOTE = ("QRISK3 has no term for HIV; people with HIV have higher cardiovascular risk than the score predicts, "
               "and REPRIEVE showed benefit from statins even at low-to-moderate estimated risk.")

FRAX_UK_URL = "https://frax.shef.ac.uk/FRAX/tool.aspx?country=1"
