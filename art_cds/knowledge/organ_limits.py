"""Renal and hepatic limits per UK product, from SmPC §4.2 (and §4.3).

Each limit names the product, the condition it applies to, what the SmPC says
and the evidence patterns that ``tools/verify_smpc.py`` checks in that section.
Rules apply the limits of every product in a regimen.

Conditions (CrCl by Cockcroft–Gault, as SmPCs use):
  crcl_lt_15_no_hd  CrCl < 15 and not on chronic haemodialysis
  crcl_lt_30        CrCl < 30, not on haemodialysis
  crcl_lt_50        CrCl < 50, not on haemodialysis
  crcl_lt_70        CrCl < 70, not on haemodialysis
  crcl_lt_80        CrCl < 80, not on haemodialysis
  haemodialysis     on chronic haemodialysis
  child_pugh_b      Child-Pugh B
  child_pugh_bc     Child-Pugh B or C
  child_pugh_c      Child-Pugh C
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from ..models import ChildPugh, PatientProfile


@dataclass(frozen=True)
class Limit:
    product: str
    when: str
    severity: str  # exclude | caution | info
    message: str
    section: str
    evidence: Tuple[str, ...]
    score: float = 0.0
    dose_change: Optional[str] = None
    requires: Tuple[str, ...] = ()  # applies only if the regimen also contains one of these drugs


def _crcl_below(limit: float) -> Callable[[PatientProfile], bool]:
    return lambda p: p.crcl is not None and p.crcl < limit and not p.on_dialysis


CONDITIONS: Dict[str, Callable[[PatientProfile], bool]] = {
    "crcl_lt_15_no_hd": _crcl_below(15),
    "crcl_lt_30": _crcl_below(30),
    "crcl_lt_50": _crcl_below(50),
    "crcl_lt_70": _crcl_below(70),
    "crcl_lt_80": _crcl_below(80),
    "haemodialysis": lambda p: p.on_dialysis,
    "child_pugh_b": lambda p: p.child_pugh is ChildPugh.B,
    "child_pugh_bc": lambda p: p.child_pugh in (ChildPugh.B, ChildPugh.C),
    "child_pugh_c": lambda p: p.child_pugh is ChildPugh.C,
}

_TAF_RENAL_30 = ("should be avoided", r"< 30 mL/min")
_TAF_HD = ("haemodialysis", r"generally,? be avoided")

LIMITS: Tuple[Limit, ...] = (
    # ---- tenofovir alafenamide combinations
    Limit("biktarvy", "crcl_lt_30", "exclude",
          "Initiation should be avoided at CrCl 15–29 mL/min, or < 15 mL/min without chronic haemodialysis.",
          "4.2", _TAF_RENAL_30),
    Limit("biktarvy", "haemodialysis", "caution",
          "On chronic haemodialysis Biktarvy should generally be avoided; use only if benefit outweighs risk, "
          "dosed after dialysis.", "4.2", _TAF_HD, score=-30),
    Limit("biktarvy", "child_pugh_c", "exclude", "Not recommended in severe hepatic impairment (not studied).",
          "4.2", (r"Child.Pugh Class C", "not recommended")),
    Limit("descovy", "crcl_lt_30", "exclude",
          "Emtricitabine/tenofovir alafenamide should be avoided at CrCl 15–29 mL/min, or < 15 mL/min "
          "without chronic haemodialysis.", "4.2", _TAF_RENAL_30),
    Limit("descovy", "haemodialysis", "caution",
          "On chronic haemodialysis emtricitabine/tenofovir alafenamide should generally be avoided; use only "
          "if benefit outweighs risk.", "4.2", _TAF_HD, score=-30),
    Limit("odefsey", "crcl_lt_30", "exclude",
          "Should be avoided at CrCl 15–29 mL/min, or < 15 mL/min without chronic haemodialysis.",
          "4.2", _TAF_RENAL_30),
    Limit("odefsey", "haemodialysis", "caution",
          "On chronic haemodialysis it should generally be avoided; use only if benefit outweighs risk.",
          "4.2", _TAF_HD, score=-30),
    Limit("odefsey", "child_pugh_c", "caution", "Not studied in severe hepatic impairment.",
          "4.2", (r"not been studied",), score=-25),
    Limit("symtuza", "crcl_lt_30", "exclude", "Should not be initiated with eGFR (Cockcroft–Gault) < 30 mL/min.",
          "4.2", ("should not be initiated", r"< 30 mL/min")),
    Limit("symtuza", "haemodialysis", "exclude", "Should not be initiated with eGFR < 30 mL/min (no data).",
          "4.2", ("should not be initiated",)),
    Limit("symtuza", "child_pugh_c", "exclude", "Contraindicated in severe (Child-Pugh C) hepatic impairment.",
          "4.3", (r"Child-Pugh Class C",)),
    # ---- tenofovir disoproxil combinations
    Limit("delstrigo", "crcl_lt_50", "exclude",
          "Should not be initiated at CrCl < 50 mL/min — lamivudine and tenofovir disoproxil need interval "
          "adjustment the combination tablet cannot provide.", "4.2", ("should not be initiated", r"50 mL/min")),
    Limit("delstrigo", "haemodialysis", "exclude", "Not suitable — requires CrCl ≥ 50 mL/min.",
          "4.2", ("should not be initiated",)),
    Limit("delstrigo", "child_pugh_c", "caution", "Doravirine not studied in severe hepatic impairment.",
          "4.2", (r"Child-Pugh Class C", "caution"), score=-20),
    Limit("ftc_tdf", "crcl_lt_30", "exclude",
          "Not recommended at CrCl < 30 mL/min — dose reductions cannot be achieved with the combination tablet.",
          "4.2", ("appropriate dose reductions cannot be achieved",)),
    Limit("ftc_tdf", "haemodialysis", "exclude", "Not recommended in haemodialysis.",
          "4.2", ("haemodialysis", "Not recommended")),
    Limit("ftc_tdf", "crcl_lt_50", "caution",
          "CrCl 30–49 mL/min: the SmPC recommends dosing every 48 hours; BHIVA prefers avoiding tenofovir "
          "disoproxil in kidney disease.", "4.2", ("every 48 hours",), score=-35,
          dose_change="Emtricitabine/tenofovir disoproxil one tablet every 48 hours (CrCl 30–49 mL/min)"),
    Limit("ftc_tdf", "crcl_lt_80", "caution",
          "Use at CrCl < 80 mL/min only if the potential benefits outweigh the potential risks.",
          "4.2", (r"<80 mL/min", "benefits are considered to outweigh"), score=-5),
    Limit("atazanavir", "haemodialysis", "exclude", "Atazanavir with ritonavir is not recommended in haemodialysis.",
          "4.2", ("not recommended in patients undergoing haemodialysis",)),
    Limit("atazanavir", "child_pugh_bc", "exclude",
          "Atazanavir with ritonavir must not be used in moderate to severe hepatic impairment.",
          "4.2", ("must not be used in patients with moderate to severe hepatic impairment",)),
    Limit("eviplera", "crcl_lt_50", "exclude",
          "Not recommended at CrCl < 50 mL/min (interval adjustment not possible with the combination tablet).",
          "4.2", ("not recommended", r"< 50 mL/min")),
    Limit("eviplera", "haemodialysis", "exclude", "Not recommended at CrCl < 50 mL/min.",
          "4.2", ("not recommended",)),
    Limit("efv_ftc_tdf", "crcl_lt_50", "exclude",
          "Not recommended at CrCl < 50 mL/min (interval adjustment not possible with the combination tablet).",
          "4.2", ("not recommended", r"< 50 ml/min")),
    Limit("efv_ftc_tdf", "haemodialysis", "exclude", "Not recommended at CrCl < 50 mL/min.",
          "4.2", ("not recommended",)),
    Limit("efavirenz", "child_pugh_c", "exclude", "Efavirenz is contraindicated in severe hepatic impairment.",
          "4.3", (r"Child Pugh Class C",)),
    # ---- dolutegravir products
    Limit("tivicay", "child_pugh_c", "caution",
          "No data in severe hepatic impairment — use dolutegravir with caution.", "4.2",
          (r"Child-Pugh grade C", "caution"), score=-20),
    Limit("dovato", "crcl_lt_30", "exclude", "Not recommended at CrCl < 30 mL/min (fixed lamivudine dose).",
          "4.2", ("not recommended", r"< 30 mL/min")),
    Limit("dovato", "haemodialysis", "exclude", "Not recommended at CrCl < 30 mL/min.", "4.2", ("not recommended",)),
    Limit("dovato", "crcl_lt_50", "caution",
          "Lamivudine exposure is significantly increased at CrCl < 50 mL/min — monitor for toxicity.",
          "4.2", (r"< 50 mL/min", "lamivudine exposure"), score=-5),
    Limit("dovato", "child_pugh_c", "caution", "No data in severe hepatic impairment — use with caution.",
          "4.2", (r"Child-Pugh grade C", "caution"), score=-20),
    Limit("triumeq", "crcl_lt_30", "exclude", "Not recommended at CrCl < 30 mL/min (fixed lamivudine dose).",
          "4.2", ("not recommended", r"< 30 mL/min")),
    Limit("triumeq", "haemodialysis", "exclude", "Not recommended at CrCl < 30 mL/min.", "4.2", ("not recommended",)),
    Limit("triumeq", "crcl_lt_50", "caution",
          "Lamivudine exposure is significantly increased at CrCl < 50 mL/min — monitor for toxicity.",
          "4.2", (r"< 50 mL/min", "lamivudine exposure"), score=-5),
    Limit("triumeq", "child_pugh_bc", "caution",
          "Abacavir: not recommended in moderate or severe hepatic impairment unless judged necessary.",
          "4.2", ("moderate or severe hepatic impairment", "not recommended"), score=-40),
    Limit("juluca", "child_pugh_c", "exclude", "Not recommended in severe hepatic impairment (no data).",
          "4.2", (r"Child-Pugh score C", "not recommended")),
    # ---- other third agents
    Limit("isentress", "child_pugh_c", "caution",
          "Safety not established in severe liver disease — use with caution.", "4.2",
          ("severe hepatic impairment", "caution"), score=-10),
    Limit("isentress_600", "child_pugh_c", "caution",
          "Safety not established in severe liver disease — use with caution.", "4.2",
          ("severe hepatic impairment", "caution"), score=-10),
    Limit("pifeltro", "child_pugh_c", "caution", "Doravirine not studied in severe hepatic impairment.",
          "4.2", (r"Child-Pugh Class C", "caution"), score=-20),
    Limit("pifeltro", "haemodialysis", "caution", "Doravirine not studied in end-stage renal disease or dialysis.",
          "4.2", ("dialysis",), score=-15),
    Limit("edurant", "crcl_lt_30", "caution", "Use rilpivirine with caution in severe renal impairment.",
          "4.2", ("severe renal impairment", "caution"), score=-10),
    Limit("rezolsta", "crcl_lt_70", "exclude",
          "Rezolsta should not be initiated at CrCl < 70 mL/min when a co-administered drug (emtricitabine, "
          "lamivudine, tenofovir disoproxil) needs CrCl-based dose adjustment.", "4.2",
          (r"70 mL/min", "should not be initiated"), requires=("FTC", "3TC", "TDF")),
    Limit("rezolsta", "child_pugh_c", "exclude", "Must not be used in severe hepatic impairment.",
          "4.2", ("must not be used",)),
    Limit("prezista", "child_pugh_c", "exclude", "Darunavir must not be used in severe hepatic impairment.",
          "4.2", ("must not be used", r"Child-Pugh Class C")),
    Limit("norvir", "child_pugh_c", "caution",
          "Ritonavir must not be given with decompensated liver disease; caution in stable Child-Pugh C.",
          "4.3", ("decompensated",), score=-25),
    Limit("vocabria_inj", "child_pugh_c", "caution", "Cabotegravir not studied in severe hepatic impairment.",
          "4.2", (r"Child-Pugh score C", "caution"), score=-20),
    Limit("vocabria_inj", "haemodialysis", "caution",
          "Cabotegravir not studied in end-stage renal disease on renal replacement therapy.",
          "4.2", ("renal replacement therapy",), score=-10),
    Limit("combivir", "crcl_lt_30", "caution",
          "Use separate lamivudine and zidovudine preparations in severe renal impairment.", "4.2",
          ("separate preparations",), score=-15,
          dose_change="Give lamivudine and zidovudine as separate, renally dosed preparations"),
)


def applicable(products: Tuple[str, ...], components: Tuple[str, ...], patient: PatientProfile):
    for limit in LIMITS:
        if limit.product not in products or not CONDITIONS[limit.when](patient):
            continue
        if limit.requires and not any(c in components for c in limit.requires):
            continue
        yield limit
