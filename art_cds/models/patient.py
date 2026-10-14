"""The patient profile the decision engine reasons about."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional, Tuple


class TreatmentStatus(str, Enum):
    NAIVE = "naive"
    SUPPRESSED = "suppressed"
    FAILURE = "failure"

    @property
    def label(self) -> str:
        return {
            "naive": "ART-naive — starting first-line therapy",
            "suppressed": "Virologically suppressed — switching or simplifying",
            "failure": "Virological failure on current or previous ART",
        }[self.value]


class LabResult(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class Pregnancy(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    NOT_PREGNANT = "not_pregnant"
    PLANNING = "planning"
    PREGNANT = "pregnant"

    @property
    def label(self) -> str:
        return {
            "not_applicable": "Not applicable",
            "not_pregnant": "Not pregnant",
            "planning": "Planning conception",
            "pregnant": "Pregnant",
        }[self.value]


class ChildPugh(str, Enum):
    NONE = "none"
    A = "A"
    B = "B"
    C = "C"


ARV_CLASSES = ("NRTI", "NNRTI", "INSTI", "PI")


@dataclass(frozen=True)
class GenotypeTest:
    """One resistance test. Mutations may carry a variant frequency, e.g. ``K103N:12%``."""

    date: str = ""  # ISO date or month
    source: str = "plasma"  # plasma RNA | proviral DNA
    rt: str = ""
    pr: str = ""
    integrase: str = ""
    sequence: str = ""  # optional FASTA (analysed by Stanford HIVdb when enabled)

    @property
    def label(self) -> str:
        kind = "proviral DNA" if self.source == "proviral" else "plasma RNA"
        return f"{self.date or 'undated'} · {kind}"


@dataclass(frozen=True)
class LabValue:
    """A dated result. ``censored`` marks a below-limit result such as '<50' (value = the limit)."""

    date: str
    value: float
    censored: bool = False

    @property
    def display(self) -> str:
        return f"<{self.value:g}" if self.censored else f"{self.value:,.0f}"


STOP_REASONS = ("", "virological failure", "toxicity/intolerance", "simplification", "drug interaction",
                "pregnancy", "patient choice", "other")


@dataclass(frozen=True)
class ArtEpisode:
    start: str
    stop: str = ""  # blank = current
    regimen: str = ""  # regimen id from knowledge/regimens.py, or free text
    components: Tuple[str, ...] = ()  # drug codes
    reason_stopped: str = ""

    @property
    def current(self) -> bool:
        return not self.stop


@dataclass(frozen=True)
class PatientProfile:
    age: int
    sex: str = "male"  # sex registered at birth: male | female
    weight_kg: Optional[float] = None
    pregnancy: Pregnancy = Pregnancy.NOT_APPLICABLE
    breastfeeding: bool = False

    status: TreatmentStatus = TreatmentStatus.NAIVE
    virus_type: str = "HIV-1"  # HIV-1 | HIV-2 | HIV-1/HIV-2
    failed_classes: FrozenSet[str] = frozenset()  # classes in a regimen that failed
    cab_prep_exposure: bool = False  # long-acting cabotegravir PrEP before diagnosis
    rapid_start: bool = False  # start before baseline results return

    viral_load: Optional[int] = None  # HIV-1 RNA copies/mL
    cd4: Optional[int] = None  # cells/mm3
    crcl: Optional[float] = None  # creatinine clearance, mL/min (Cockcroft-Gault)
    on_dialysis: bool = False
    child_pugh: ChildPugh = ChildPugh.NONE
    hbsag: LabResult = LabResult.UNKNOWN
    hla_b5701: LabResult = LabResult.UNKNOWN
    hcv: bool = False
    anti_hbc: LabResult = LabResult.UNKNOWN
    anti_hbs: LabResult = LabResult.UNKNOWN
    hbv_dna: Optional[float] = None  # IU/mL
    crag: LabResult = LabResult.UNKNOWN  # serum cryptococcal antigen
    tb_start: str = ""  # date TB treatment started

    genotype_available: bool = False
    rt_mutations: str = ""  # shorthand for a single current genotype
    pr_mutations: str = ""
    in_mutations: str = ""
    genotypes: Tuple[GenotypeTest, ...] = ()  # full history, including archived/proviral tests
    use_hivdb: bool = False  # send mutations/sequences to Stanford HIVdb
    minority_threshold: float = 20.0  # % below which NGS minority variants are reported but not scored
    subtype: str = ""
    tropism: str = "unknown"  # unknown | R5 | X4 | dual/mixed

    comorbidities: FrozenSet[str] = frozenset()
    comedications: FrozenSet[str] = frozenset()
    medicines_text: str = ""  # free-text medicines list, reconciled into comedications

    # measurements feeding the calculators
    creatinine_umol: Optional[float] = None
    cystatin_c: Optional[float] = None  # mg/L
    height_cm: Optional[float] = None
    bilirubin_umol: Optional[float] = None
    albumin_g_l: Optional[float] = None
    inr: Optional[float] = None
    ascites: str = ""  # none | mild | severe
    encephalopathy: str = ""  # none | mild | severe
    qrisk3: Optional[float] = None  # 10-year CVD risk, %
    frax_mof: Optional[float] = None  # 10-year major osteoporotic fracture probability, %
    frax_hip: Optional[float] = None  # 10-year hip fracture probability, %

    vl_history: Tuple[LabValue, ...] = ()  # sorted by date
    cd4_history: Tuple[LabValue, ...] = ()
    art_history: Tuple[ArtEpisode, ...] = ()

    prefers_single_tablet: bool = False
    prefers_long_acting: bool = False
    adherence_concerns: bool = False
    food_insecurity: bool = False

    @property
    def is_pregnant(self) -> bool:
        return self.pregnancy is Pregnancy.PREGNANT

    def has(self, condition: str) -> bool:
        return condition in self.comorbidities

    @property
    def high_cv_risk(self) -> bool:
        return self.has("cvd") or (self.qrisk3 is not None and self.qrisk3 >= 10)

    @property
    def high_fracture_risk(self) -> bool:
        """BHIVA §8.2 thresholds: osteoporosis/fragility fracture, FRAX MOF > 5% or hip > 1%."""
        return self.has("osteoporosis") or (self.frax_mof or 0) > 5 or (self.frax_hip or 0) > 1

    def takes(self, comedication: str) -> bool:
        return comedication in self.comedications

    @property
    def genotype_history(self) -> Tuple[GenotypeTest, ...]:
        """All resistance tests; the shorthand fields count as one current plasma test."""
        tests = list(self.genotypes)
        if self.rt_mutations or self.pr_mutations or self.in_mutations:
            tests.append(GenotypeTest(rt=self.rt_mutations, pr=self.pr_mutations, integrase=self.in_mutations))
        if not tests and self.genotype_available:
            tests.append(GenotypeTest())  # tested, no mutations
        return tuple(tests)
