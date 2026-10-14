"""Worked teaching cases. Each pre-fills the assessment form."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union

from werkzeug.datastructures import MultiDict

Value = Union[str, Tuple[str, ...]]


@dataclass(frozen=True)
class Case:
    key: str
    title: str
    summary: str
    values: Dict[str, Value]
    learning_points: Tuple[str, ...]
    topics: Tuple[str, ...] = field(default_factory=tuple)

    def as_multidict(self) -> MultiDict:
        items: List[Tuple[str, str]] = [("case_key", self.key)]
        for k, v in self.values.items():
            if isinstance(v, tuple):
                items.extend((k, x) for x in v)
            else:
                items.append((k, v))
        return MultiDict(items)


CASES: Tuple[Case, ...] = (
    Case(
        "first-line", "Starting ART: an uncomplicated first presentation",
        "A 31-year-old man diagnosed at a sexual health clinic. HIV RNA 48,000 copies/mL, CD4 520. "
        "HBsAg negative, HLA-B*57:01 negative, baseline resistance test shows no mutations.",
        {"age": "31", "sex": "male", "weight_kg": "74", "status": "naive", "viral_load": "48000", "cd4": "520",
         "crcl": "118", "hbsag": "negative", "hla_b5701": "negative", "genotype": "available",
         "prefers_single_tablet": "on"},
        ("BHIVA preferred first-line options are an INSTI (bictegravir or dolutegravir) with two NRTIs, or "
         "dolutegravir/lamivudine when HBV, resistance and high viral load have been excluded.",
         "Single-tablet regimens are favoured for convenience but are not more effective than multi-tablet ones.",
         "Check the SmPC §4.5 of the chosen regimen against every co-medication, including over-the-counter "
         "antacids and supplements (cation chelation with INSTIs)."),
        ("first-line", "INSTI"),
    ),
    Case(
        "hbv-ckd", "Hepatitis B co-infection with chronic kidney disease",
        "A 58-year-old man, HBsAg positive, creatinine clearance 42 mL/min, type 2 diabetes on metformin, "
        "on atorvastatin. HIV RNA 120,000 copies/mL, CD4 310.",
        {"age": "58", "sex": "male", "weight_kg": "88", "status": "naive", "viral_load": "120000", "cd4": "310",
         "crcl": "42", "hbsag": "positive", "hla_b5701": "unknown", "genotype": "available",
         "comorbidities": ("diabetes", "cvd", "dyslipidaemia"), "comedications": ("metformin", "atorvastatin")},
        ("HBV co-infection needs tenofovir plus emtricitabine or lamivudine — dual-therapy and abacavir "
         "backbones do not treat HBV adequately.",
         "Below CrCl 50 mL/min tenofovir disoproxil combinations should not be started (Delstrigo, Eviplera "
         "SmPC §4.2); tenofovir alafenamide combinations remain usable down to 30 mL/min.",
         "Dolutegravir raises metformin exposure (SmPC §4.5) — adjust and monitor."),
        ("HBV", "renal"),
    ),
    Case(
        "pregnancy", "Newly diagnosed in pregnancy",
        "A 27-year-old woman at 14 weeks' gestation found to have HIV at antenatal screening. HIV RNA "
        "30,000 copies/mL, CD4 450, HBsAg negative.",
        {"age": "27", "sex": "female", "pregnancy": "pregnant", "weight_kg": "63", "status": "naive",
         "viral_load": "30000", "cd4": "450", "crcl": "125", "hbsag": "negative", "hla_b5701": "unknown",
         "genotype": "available"},
        ("Dolutegravir-based ART is preferred in pregnancy; the early neural-tube-defect signal was not "
         "confirmed in larger datasets.",
         "Cobicistat-boosted regimens are not recommended in pregnancy — exposures fall in the second and "
         "third trimesters (Symtuza, Rezolsta SmPC §4.6).",
         "BHIVA recommends monitoring HIV RNA through pregnancy and planning delivery around the 36-week "
         "viral load."),
        ("pregnancy",),
    ),
    Case(
        "tb", "Advanced HIV with tuberculosis on rifampicin",
        "A 35-year-old man with pulmonary TB, started on rifampicin-based treatment 10 days ago. CD4 85, "
        "HIV RNA 250,000 copies/mL. Resistance test pending.",
        {"age": "35", "sex": "male", "weight_kg": "58", "status": "naive", "viral_load": "250000", "cd4": "85",
         "crcl": "105", "hbsag": "negative", "hla_b5701": "negative", "genotype": "pending",
         "comorbidities": ("active_tb",), "comedications": ("rifampicin",), "crag": "negative",
         "tb_start": "2026-10-05"},
        ("Rifampicin is contraindicated with bictegravir, rilpivirine, doravirine, cabotegravir and boosted PIs "
         "(SmPC §4.3), and BHIVA advises against cobicistat with any rifamycin.",
         "BHIVA's TB guideline puts efavirenz with tenofovir disoproxil/emtricitabine first line on rifampicin, with "
         "dolutegravir (50 mg twice daily) or raltegravir as alternatives, and advises against TAF- or "
         "bictegravir-containing combinations and two-drug regimens until outcome data exist.",
         "ART within 2 weeks of TB treatment if CD4 < 50, otherwise within 4 weeks of the TB diagnosis; CNS TB is the "
         "exception and can be delayed for 8 weeks. Watch for paradoxical TB-IRIS."),
        ("TB", "interactions"),
    ),
    Case(
        "failure", "Virological failure on an NNRTI regimen",
        "A 41-year-old woman on efavirenz/emtricitabine/tenofovir disoproxil since 2019, suppressed until 2025; "
        "HIV RNA now 15,000 copies/mL. Resistance test: RT K65R, M184V, K103N.",
        {"age": "41", "sex": "female", "pregnancy": "not_pregnant", "weight_kg": "66", "status": "failure",
         "failed_classes": ("NNRTI", "NRTI"), "viral_load": "15000", "cd4": "210", "crcl": "96",
         "hbsag": "negative", "hla_b5701": "negative", "genotype": "available",
         "g0_date": "2026-09-01", "g0_rt": "K65R, M184V, K103N",
         "vl_history": "2019-02-01 86000\n2019-04-01 <50\n2020-03-01 <50\n2022-05-01 <50\n2024-06-01 140\n"
                       "2024-07-15 <50\n2025-11-01 2400\n2026-08-10 15000",
         "cd4_history": "2019-02-01 180\n2020-03-01 360\n2022-05-01 420\n2026-08-10 210",
         "a0_start": "2019-02-15", "a0_other": "Efavirenz/emtricitabine/tenofovir disoproxil"},
        ("K65R reduces tenofovir and abacavir activity but increases zidovudine susceptibility; M184V makes "
         "lamivudine/emtricitabine only partly active.",
         "A fully active, high-barrier anchor (dolutegravir or boosted darunavir) is the priority after failure; "
         "trials such as NADIA showed recycled tenofovir/lamivudine works with dolutegravir.",
         "Address adherence, interactions and tolerability before switching — and always act on a genotype "
         "taken on the failing regimen."),
        ("resistance", "failure"),
    ),
    Case(
        "long-acting", "Switching to long-acting injectable therapy",
        "A 29-year-old man suppressed for 3 years on Biktarvy, no previous failure, HBsAg negative and "
        "HBV-immune, who would prefer not to take daily tablets.",
        {"age": "29", "sex": "male", "weight_kg": "79", "status": "suppressed", "viral_load": "20", "cd4": "710",
         "crcl": "120", "hbsag": "negative", "hla_b5701": "negative", "genotype": "pending",
         "prefers_long_acting": "on"},
        ("Cabotegravir + rilpivirine long-acting is for adults who are virologically suppressed with no known "
         "or suspected resistance to NNRTIs or INSTIs (Vocabria and Rekambys SmPC §4.1; BHIVA 2025 §5.11; NICE TA757).",
         "Injections every 2 months, gluteal IM, with an optional oral lead-in; missed injections need an "
         "oral bridging plan. BHIVA advises 2-monthly viral loads for the first 6–12 months.",
         "BHIVA 2025: high BMI alone does not reduce efficacy, but avoid the combination of BMI > 30 kg/m² with "
         "HIV-1 subtype A6; rilpivirine resistance mutations are a contraindication."),
        ("switch", "long-acting"),
    ),
)

CASES_BY_KEY = {c.key: c for c in CASES}
