"""The patient profile the decision engine reasons about."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


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
class PatientProfile:
    age: int
    sex: str = "male"  # sex registered at birth: male | female
    weight_kg: Optional[float] = None
    pregnancy: Pregnancy = Pregnancy.NOT_APPLICABLE
    breastfeeding: bool = False

    status: TreatmentStatus = TreatmentStatus.NAIVE
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

    genotype_available: bool = False
    rt_mutations: str = ""
    pr_mutations: str = ""
    in_mutations: str = ""

    comorbidities: FrozenSet[str] = frozenset()
    comedications: FrozenSet[str] = frozenset()

    prefers_single_tablet: bool = False
    prefers_long_acting: bool = False
    adherence_concerns: bool = False
    food_insecurity: bool = False

    @property
    def is_pregnant(self) -> bool:
        return self.pregnancy is Pregnancy.PREGNANT

    def has(self, condition: str) -> bool:
        return condition in self.comorbidities

    def takes(self, comedication: str) -> bool:
        return comedication in self.comedications
