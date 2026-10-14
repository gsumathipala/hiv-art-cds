"""BHIVA recommendation tiers for each clinical scenario.

Sources (texts in ``art_cds/data/guidelines``, every tier citation verified):
  * BHIVA adult ART guidelines 2022, 2025 interim update — Table 5.1 (first line),
    Table 5.2 (suppressed switch/maintenance), section 7 (virological failure);
  * BHIVA pregnancy and postpartum guidelines 2025 — Table 8.3 (starting ART in pregnancy).

Section 7 sets principles for failure rather than a table, so failure tiers are this
tool's application of them (high-barrier anchors first).
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from ..models.assessment import Ref
from ..models.patient import TreatmentStatus
from .citations import bhiva

PREFERRED = "preferred"
ALTERNATIVE = "alternative"
OTHER = "other"

TIER_SCORE = {PREFERRED: 100.0, ALTERNATIVE: 80.0, OTHER: 60.0}

# Scenario keys: the three treatment statuses plus starting ART in pregnancy.
NAIVE = "naive"
NAIVE_PREGNANT = "naive_pregnant"
SUPPRESSED = "suppressed"
FAILURE = "failure"
SCENARIOS = {
    NAIVE: "First-line",
    NAIVE_PREGNANT: "Starting in pregnancy",
    SUPPRESSED: "Suppressed switch",
    FAILURE: "Virological failure",
}

TIER_LABELS: Dict[str, Dict[str, str]] = {
    NAIVE: {PREFERRED: "Recommended for most people", ALTERNATIVE: "Certain clinical situations", OTHER: "Other"},
    NAIVE_PREGNANT: {PREFERRED: "Recommended in pregnancy", ALTERNATIVE: "Alternative in pregnancy",
                     OTHER: "Limited pregnancy data"},
    SUPPRESSED: {PREFERRED: "Recommended (first-line option)", ALTERNATIVE: "Acceptable for switch",
                 OTHER: "Maintenance only"},
    FAILURE: {PREFERRED: "Preferred (high barrier)", ALTERNATIVE: "Alternative", OTHER: "Other"},
}
# Short labels for badges where the scenario is obvious
TIER_LABEL = {PREFERRED: "Preferred", ALTERNATIVE: "Alternative", OTHER: "Other"}

BHIVA_ART = "BHIVA adult ART guidelines 2022 (2025 interim update)"
BHIVA_PREGNANCY = "BHIVA pregnancy and postpartum guidelines (2025)"
BHIVA_MONITORING = "BHIVA guidelines for the routine investigation and monitoring of adults with HIV-1"
BHIVA_TB = "BHIVA guidelines for the management of tuberculosis in adults living with HIV"
BHIVA_HEPATITIS = "BHIVA guidelines for the management of hepatitis viruses in adults with HIV"
NICE_TA757 = "NICE TA757: cabotegravir with rilpivirine for treating HIV-1 (2022)"

_A = "bhiva_art"
_P = "bhiva_pregnancy"

# Distinctive wording of each regimen's entry in the relevant table.
_T51_DRV = bhiva(_A, "5", r"Darunavir plus cobicistat or ritonavir plus emtricitabine plus tenofovir AF or tenofovir DX")
_T51_DOR = bhiva(_A, "5", r"Doravirine plus emtricitabine or lamivudine plus tenofovir AF or tenofovir DX")
_T51_RAL = bhiva(_A, "5", r"Raltegravir plus emtricitabine plus tenofovir AF or tenofovir DX")
_T51_DTG = bhiva(_A, "5", r"Dolutegravir plus emtricitabine/tenofovir AF or emtricitabine/tenofovir DX")
_T52 = bhiva(_A, "5.10", r"Acceptable for switch or to continue where clinically appropriate")
_T83_DTG = bhiva(_P, "8.3.1", r"Dolutegravir plus emtricitabine/tenofovir DX First choice")
_T83_RPV = bhiva(_P, "8.3.1", r"Rilpivirine plus emtricitabine/tenofovir DX or emtricitabine/tenofovir AF")
_T83_RAL = bhiva(_P, "8.3.1", r"Raltegravir 400 mg twice daily plus emtricitabine/tenofovir DX")
_T83_DRV = bhiva(_P, "8.3.1", r"Darunavir 600 mg plus ritonavir 100 mg twice daily plus emtricitabine/tenofovir")
_T83_EFV = bhiva(_P, "8.3.1", r"Efavirenz plus emtricitabine/tenofovir DX or emtricitabine/tenofovir AF")
_T82_TWO = bhiva(_P, "8.1", r"not in combinations with fewer than three agents in pregnancy")
_FAIL = bhiva(_A, "7.5", r"Individuals with no or limited drug resistance")

_NAIVE: Dict[str, Tuple[str, Ref]] = {
    "bic_ftc_taf": (PREFERRED, bhiva(_A, "5", r"Recommended as initial treatment for most people",
                                     r"Bictegravir/emtricitabine/tenofovir AF")),
    "dtg_ftc_taf": (PREFERRED, _T51_DTG),
    "dtg_ftc_tdf": (PREFERRED, _T51_DTG),
    "dtg_3tc": (PREFERRED, bhiva(_A, "5", r"Dolutegravir/lamivudine No baseline lamivudine resistance")),
    "drvc_ftc_taf": (ALTERNATIVE, _T51_DRV), "drvc_ftc_tdf": (ALTERNATIVE, _T51_DRV),
    "drvr_ftc_taf": (ALTERNATIVE, _T51_DRV), "drvr_ftc_tdf": (ALTERNATIVE, _T51_DRV),
    "dor_3tc_tdf": (ALTERNATIVE, _T51_DOR), "dor_ftc_taf": (ALTERNATIVE, _T51_DOR),
    "ral_ftc_taf": (ALTERNATIVE, _T51_RAL), "ral_ftc_tdf": (ALTERNATIVE, _T51_RAL),
    "dtg_abc_3tc": (ALTERNATIVE, bhiva(_A, "5", r"Dolutegravir plus abacavir plus lamivudine Where a three-drug "
                                                r"regimen is necessary")),
    "efv_plus_ftc_tdf": (ALTERNATIVE, bhiva(_A, "5", r"May be a first-line choice in pregnancy and for people on TB "
                                                     r"treatment")),
}

_NAIVE_PREGNANT: Dict[str, Tuple[str, Ref]] = {
    "dtg_ftc_tdf": (PREFERRED, _T83_DTG),
    "dtg_ftc_taf": (PREFERRED, bhiva(_P, "8.3.1", r"Dolutegravir plus emtricitabine/tenofovir AF Association with "
                                                  r"weight gain")),
    "dtg_abc_3tc": (PREFERRED, bhiva(_P, "8.3.1", r"Dolutegravir/lamivudine/abacavir Ensure HLA B\*5701 negative")),
    "rpv_ftc_tdf": (ALTERNATIVE, _T83_RPV), "rpv_ftc_taf": (ALTERNATIVE, _T83_RPV),
    "ral_ftc_taf": (ALTERNATIVE, _T83_RAL), "ral_ftc_tdf": (ALTERNATIVE, _T83_RAL),
    "drvr_ftc_taf": (ALTERNATIVE, _T83_DRV), "drvr_ftc_tdf": (ALTERNATIVE, _T83_DRV),
    "efv_plus_ftc_tdf": (ALTERNATIVE, _T83_EFV),
    "bic_ftc_taf": (OTHER, bhiva(_P, "8.1", r"Bictegravir Limited pharmacokinetic and pregnancy outcome data")),
    "dtg_3tc": (OTHER, _T82_TWO),
    "dor_3tc_tdf": (OTHER, bhiva(_P, "8.1", r"Doravirine Limited pharmacokinetic data")),
    "dor_ftc_taf": (OTHER, bhiva(_P, "8.1", r"Doravirine Limited pharmacokinetic data")),
    "drvc_ftc_taf": (OTHER, bhiva(_P, "8.1", r"cobicistat should NOT be used as a booster in pregnancy")),
    "drvc_ftc_tdf": (OTHER, bhiva(_P, "8.1", r"cobicistat should NOT be used as a booster in pregnancy")),
}

_SUPPRESSED: Dict[str, Tuple[str, Ref]] = {
    **{k: v for k, v in _NAIVE.items() if v[0] == PREFERRED},
    **{k: (ALTERNATIVE, _T52) for k, v in _NAIVE.items() if v[0] != PREFERRED and k != "efv_plus_ftc_tdf"},
    "rpv_ftc_taf": (ALTERNATIVE, bhiva(_A, "5.10", r"abacavir/lamivudine plus rilpivirine")),
    "rpv_ftc_tdf": (ALTERNATIVE, bhiva(_A, "5.10", r"abacavir/lamivudine plus rilpivirine")),
    "atvr_ftc_tdf": (ALTERNATIVE, bhiva(_A, "5.10", r"with atazanavir/ritonavir or atazanavir/cobicistat Where "
                                                    r"resistance necessitates a PI")),
    "dtg_rpv": (ALTERNATIVE, bhiva(_A, "5.10", r"Dolutegravir/rilpivirine Studied only in suppressed switch")),
    "cab_rpv_la": (ALTERNATIVE, bhiva(_A, "5.10", r"Cabotegravir plus rilpivirine injectable Studied only in "
                                                  r"suppressed switch")),
    "drvr_dtg": (ALTERNATIVE, bhiva(_A, "5.10", r"Dolutegravir with darunavir/ritonavir or darunavir/cobicistat")),
    "efv_ftc_tdf": (OTHER, bhiva(_A, "5.10", r"plus efavirenz Maintenance only")),
    "efv_plus_ftc_tdf": (OTHER, bhiva(_A, "5.10", r"plus efavirenz Maintenance only")),
}

_FAILURE: Dict[str, Tuple[str, Ref]] = {
    **{k: (PREFERRED, _FAIL) for k in ("drvr_ftc_taf", "drvr_ftc_tdf", "drvc_ftc_taf", "drvc_ftc_tdf",
                                      "dtg_ftc_taf", "dtg_ftc_tdf")},
    **{k: (ALTERNATIVE, _FAIL) for k in ("bic_ftc_taf", "drvr_dtg", "dtg_abc_3tc", "dtg_azt_3tc", "atvr_ftc_tdf")},
    **{k: (OTHER, _FAIL) for k in ("dor_3tc_tdf", "dor_ftc_taf", "ral_ftc_taf", "ral_ftc_tdf", "rpv_ftc_taf",
                                  "rpv_ftc_tdf", "efv_plus_ftc_tdf")},
}

TIERS: Dict[str, Dict[str, Tuple[str, Ref]]] = {
    NAIVE: _NAIVE, NAIVE_PREGNANT: _NAIVE_PREGNANT, SUPPRESSED: _SUPPRESSED, FAILURE: _FAILURE,
}


def scenario(status: TreatmentStatus, pregnant: bool = False) -> str:
    if status is TreatmentStatus.NAIVE:
        return NAIVE_PREGNANT if pregnant else NAIVE
    return SUPPRESSED if status is TreatmentStatus.SUPPRESSED else FAILURE


def tier_for(status: TreatmentStatus, regimen_id: str, pregnant: bool = False) -> Optional[Tuple[str, str, Ref]]:
    """(tier, label, citation) for the regimen in this scenario, or None if it is not offered."""
    key = scenario(status, pregnant)
    entry = TIERS[key].get(regimen_id)
    if entry is None:
        return None
    tier, ref = entry
    return tier, TIER_LABELS[key][tier], ref
