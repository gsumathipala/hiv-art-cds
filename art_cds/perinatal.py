"""Infant post-natal prophylaxis (PNP) and perinatal management.

All rules from the BHIVA guidelines on the management of HIV in pregnancy and the postpartum
period (2025), section 11 (infant PNP) and section 8.7 (intrapartum care). Dosing is intentionally
not reproduced here: use Appendix 4 of the guideline, which is weight- and gestation-banded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .knowledge.citations import bhiva
from .models import Ref

LOW_RISK = bhiva("bhiva_pregnancy", "11.1", r"we recommend 2 weeks of zidovudine monotherapy if all the following "
                                            r"criteria are met")
HIGH_RISK = bhiva("bhiva_pregnancy", "11.1", r"we recommend use of combination PNP if the above criteria for low-risk "
                                             r"infants are not met")
COMBINATION = bhiva("bhiva_pregnancy", "11.1", r"standard combination PNP should consist of nevirapine for 2 weeks "
                                               r"with zidovudine and lamivudine for 4 weeks")
WITHIN_4_HOURS = bhiva("bhiva_pregnancy", "11.1", r"PNP should be commenced as soon as possible after birth, and at "
                                                  r"the latest within 4 hours")
BREASTFEEDING_PNP = bhiva("bhiva_pregnancy", "11.1", r"infant PNP should not usually be given beyond 2 weeks for "
                                                     r"low-risk infants even if the infant is breast/chestfed")
MATERNAL_ART = bhiva("bhiva_pregnancy", "11.1", r"lifelong ART for the woman/feeding parent \(rather than extended "
                                                r"infant PNP\)")
IV_ZDV = bhiva("bhiva_pregnancy", "8.7", r"intravenous zidovudine infusion through labour and/or delivery")
IV_ZDV_LOW = bhiva("bhiva_pregnancy", "8.7", r"intrapartum intravenous zidovudine infusion can be considered for "
                                             r"women/people on ART with a plasma viral load of 50.1000 copies/mL")
NVP_RESISTANCE = bhiva("bhiva_pregnancy", "11.1", r"high risk \(combination PNP indicated\), nevirapine will not be "
                                                  r"effective")
CHIVA = bhiva("bhiva_pregnancy", "11.1", r"Chiva\) paediatric PEP guidelines")

APPENDIX_4 = ("Dose by weight and gestation using Appendix 4 of the BHIVA pregnancy guidelines "
              "(https://bhiva.org/clinical-guideline/pregnancy-guidelines/).")


@dataclass(frozen=True)
class InfantPlan:
    risk: str  # low | high
    regimen: str
    duration: str
    criteria_met: Tuple[str, ...]
    criteria_failed: Tuple[str, ...]
    notes: Tuple[str, ...]
    refs: Tuple[Ref, ...]


def infant_pnp(art_started_weeks_before_delivery: Optional[float], good_engagement: bool,
               vl_in_last_6_weeks: bool, all_vl_under_50_in_last_10_weeks: bool,
               delivery_vl: Optional[float], breastfeeding: bool = False,
               maternal_nnrti_resistance: bool = False) -> InfantPlan:
    """BHIVA §11.1 low-risk criteria — all four must be met, and the delivery viral load < 50."""
    met: List[str] = []
    failed: List[str] = []

    def check(ok: Optional[bool], yes: str, no: str) -> None:
        (met if ok else failed).append(yes if ok else no)

    check(art_started_weeks_before_delivery is not None and art_started_weeks_before_delivery >= 10,
          "ART started at least 10 weeks before delivery",
          "ART not started at least 10 weeks before delivery (or unknown)")
    check(good_engagement, "Good engagement with maternity, antenatal and HIV services",
          "Engagement with services not documented as good")
    check(vl_in_last_6_weeks, "At least one viral load in the 6 weeks before delivery",
          "No viral load in the 6 weeks before delivery")
    check(all_vl_under_50_in_last_10_weeks, "All viral loads < 50 copies/mL in the 10 weeks before delivery",
          "Not all viral loads < 50 copies/mL in the 10 weeks before delivery")
    if delivery_vl is None:
        failed.append("Viral load on the day of delivery unknown")
    elif delivery_vl >= 50:
        failed.append(f"Viral load {delivery_vl:,.0f} copies/mL at delivery")
    else:
        met.append("Viral load < 50 copies/mL at delivery")

    notes: List[str] = [APPENDIX_4, "Start PNP as soon as possible after birth and within 4 hours at the latest."]
    refs: List[Ref] = [WITHIN_4_HOURS]
    if failed:
        notes.append("Discuss with the paediatric/ID MDT; Chiva paediatric PEP guidance covers unusual situations.")
        if maternal_nnrti_resistance:
            notes.append("Maternal NNRTI resistance — nevirapine will not be effective; the MDT should choose an "
                         "alternative third drug.")
            refs.append(NVP_RESISTANCE)
        refs += [HIGH_RISK, COMBINATION, CHIVA]
        return InfantPlan("high", "Combination PNP: zidovudine + lamivudine with nevirapine",
                          "Zidovudine and lamivudine for 4 weeks; nevirapine for 2 weeks",
                          tuple(met), tuple(failed), tuple(notes), tuple(refs))

    if breastfeeding:
        notes.append("Breastfeeding: PNP is not usually extended beyond 2 weeks for low-risk infants; protection comes "
                     "from the parent's sustained viral suppression on ART, not from longer infant PNP.")
        refs += [BREASTFEEDING_PNP, MATERNAL_ART]
    return InfantPlan("low", "Zidovudine monotherapy", "2 weeks", tuple(met), tuple(failed), tuple(notes), tuple(refs))


def intrapartum_zidovudine(delivery_vl: Optional[float], untreated_unknown_vl: bool = False) -> Tuple[str, Ref]:
    if untreated_unknown_vl:
        return ("Intravenous zidovudine through labour/delivery is recommended: untreated with an unknown viral load, "
                "whatever the mode of delivery.", IV_ZDV)
    if delivery_vl is None:
        return ("Viral load at delivery unknown — treat as > 1000 copies/mL until known and plan intravenous "
                "zidovudine.", IV_ZDV)
    if delivery_vl > 1000:
        return ("Intravenous zidovudine through labour/delivery is recommended (viral load > 1000 copies/mL); start "
                "4 hours before a planned caesarean section.", IV_ZDV)
    if delivery_vl >= 50:
        return ("Intravenous zidovudine can be considered (viral load 50–1000 copies/mL) alongside the other measures "
                "in BHIVA §8.7.", IV_ZDV_LOW)
    return ("Intravenous zidovudine is not indicated at a viral load < 50 copies/mL; delayed cord clamping and water "
            "birth can be supported.", IV_ZDV_LOW)


INFANT_TESTING = ("HIV PCR at birth (high risk: also at 2 weeks), 6 weeks and 12 weeks, with a final antibody test at "
                  "18–24 months. Breastfed infants need PCR every 4 weeks while feeding and for 8 weeks after it stops.")
MONITORING_BREASTFEEDING = ("Maternal HIV RNA monthly while breastfeeding, and the infant tested as above; stop "
                            "breastfeeding and seek MDT advice if the maternal viral load becomes detectable.")
