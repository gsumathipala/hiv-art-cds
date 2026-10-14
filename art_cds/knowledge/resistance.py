"""Drug-resistance mutation penalty scores (simplified, educational).

Modelled on the penalty-score approach of the Stanford HIV Drug Resistance
Database (HIVdb): each mutation adds a score per drug, some combinations add
more, and the total maps to a susceptibility level. The scores below are an
abridged approximation for the major mutations only. For clinical
interpretation submit the sequence to Stanford HIVdb (https://hivdb.stanford.edu)
or use the UK laboratory's report — this table exists to make the reasoning
visible, not to replace them.
"""
from __future__ import annotations

from typing import Dict, Tuple

NRTI_DRUGS = ("ABC", "AZT", "FTC", "3TC", "TDF")
NNRTI_DRUGS = ("DOR", "EFV", "ETR", "RPV")
INSTI_DRUGS = ("BIC", "CAB", "DTG", "RAL")
PI_DRUGS = ("ATV", "DRV")

# TAF shares tenofovir's resistance profile.
SCORED_AS = {"TAF": "TDF"}

LEVELS = {
    1: "Susceptible",
    2: "Potential low-level resistance",
    3: "Low-level resistance",
    4: "Intermediate resistance",
    5: "High-level resistance",
}

# Contribution of a drug to the genotypic susceptibility score (GSS)
ACTIVITY = {1: 1.0, 2: 1.0, 3: 0.75, 4: 0.5, 5: 0.0}


def level_for(score: float) -> int:
    if score >= 60:
        return 5
    if score >= 30:
        return 4
    if score >= 15:
        return 3
    if score >= 10:
        return 2
    return 1


S = Dict[str, int]

# gene -> mutation -> {drug: score}; mutation written as wild type + position + mutant
SCORES: Dict[str, Dict[str, S]] = {
    "RT": {
        # NRTI
        "M41L": {"ABC": 5, "AZT": 15, "TDF": 5},
        "K65R": {"ABC": 45, "AZT": -10, "FTC": 30, "3TC": 30, "TDF": 50},
        "K65N": {"ABC": 30, "FTC": 15, "3TC": 15, "TDF": 30},
        "D67N": {"ABC": 5, "AZT": 15, "TDF": 5},
        "T69ins": {"ABC": 60, "AZT": 60, "FTC": 30, "3TC": 30, "TDF": 60},
        "K70R": {"ABC": 5, "AZT": 30, "TDF": 5},
        "K70E": {"ABC": 15, "FTC": 10, "3TC": 10, "TDF": 30},
        "L74V": {"ABC": 30},
        "L74I": {"ABC": 30},
        "Y115F": {"ABC": 30, "TDF": 10},
        "Q151M": {"ABC": 60, "AZT": 60, "FTC": 10, "3TC": 10, "TDF": 15},
        "M184V": {"ABC": 15, "AZT": -10, "FTC": 60, "3TC": 60, "TDF": -10},
        "M184I": {"ABC": 15, "AZT": -10, "FTC": 60, "3TC": 60, "TDF": -10},
        "L210W": {"ABC": 5, "AZT": 30, "TDF": 5},
        "T215Y": {"ABC": 10, "AZT": 60, "TDF": 10},
        "T215F": {"ABC": 10, "AZT": 60, "TDF": 10},
        "K219Q": {"ABC": 5, "AZT": 15},
        "K219E": {"ABC": 5, "AZT": 15},
        # NNRTI
        "A98G": {"DOR": 10, "EFV": 15, "ETR": 10, "RPV": 15},
        "L100I": {"DOR": 15, "EFV": 60, "ETR": 30, "RPV": 60},
        "K101E": {"DOR": 15, "EFV": 30, "ETR": 30, "RPV": 45},
        "K101P": {"DOR": 15, "EFV": 60, "ETR": 60, "RPV": 60},
        "K103N": {"EFV": 60},
        "K103S": {"EFV": 45},
        "V106A": {"DOR": 45, "EFV": 30},
        "V106M": {"DOR": 30, "EFV": 60},
        "V108I": {"DOR": 10, "EFV": 10},
        "E138A": {"ETR": 10, "RPV": 15},
        "E138G": {"ETR": 10, "RPV": 15},
        "E138K": {"EFV": 10, "ETR": 15, "RPV": 45, "DOR": 10},
        "E138Q": {"ETR": 10, "RPV": 15},
        "V179D": {"DOR": 10, "EFV": 10, "ETR": 10, "RPV": 10},
        "Y181C": {"DOR": 10, "EFV": 30, "ETR": 30, "RPV": 45},
        "Y181I": {"DOR": 15, "EFV": 30, "ETR": 60, "RPV": 60},
        "Y181V": {"DOR": 15, "EFV": 30, "ETR": 60, "RPV": 60},
        "Y188L": {"DOR": 60, "EFV": 60, "ETR": 10, "RPV": 60},
        "Y188H": {"DOR": 15, "EFV": 30, "RPV": 15},
        "G190A": {"DOR": 10, "EFV": 45, "ETR": 10, "RPV": 15},
        "G190S": {"DOR": 15, "EFV": 60, "ETR": 10, "RPV": 15},
        "G190E": {"DOR": 60, "EFV": 60, "ETR": 45, "RPV": 60},
        "H221Y": {"EFV": 10, "RPV": 15},
        "P225H": {"DOR": 10, "EFV": 45},
        "F227C": {"DOR": 60, "EFV": 15, "ETR": 30, "RPV": 30},
        "F227L": {"DOR": 15},
        "M230L": {"DOR": 30, "EFV": 45, "ETR": 30, "RPV": 60},
        "Y318F": {"DOR": 30},
    },
    "IN": {
        "T66I": {"RAL": 15, "CAB": 10},
        "T66K": {"BIC": 15, "CAB": 15, "DTG": 15, "RAL": 30},
        "E92Q": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 30},
        "T97A": {"CAB": 10, "DTG": 5, "RAL": 10},
        "G118R": {"BIC": 30, "CAB": 45, "DTG": 30, "RAL": 60},
        "E138A": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "E138K": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "E138T": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "G140A": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "G140C": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "G140S": {"BIC": 10, "CAB": 10, "DTG": 10, "RAL": 15},
        "Y143C": {"CAB": 10, "RAL": 45},
        "Y143H": {"CAB": 10, "RAL": 45},
        "Y143R": {"CAB": 10, "RAL": 60},
        "Q148H": {"BIC": 15, "CAB": 30, "DTG": 15, "RAL": 60},
        "Q148K": {"BIC": 30, "CAB": 45, "DTG": 30, "RAL": 60},
        "Q148R": {"BIC": 25, "CAB": 45, "DTG": 25, "RAL": 60},
        "N155H": {"BIC": 10, "CAB": 15, "DTG": 10, "RAL": 60},
        "R263K": {"BIC": 30, "CAB": 30, "DTG": 30, "RAL": 15},
    },
    "PR": {
        "V32I": {"ATV": 15, "DRV": 15},
        "L33F": {"ATV": 5, "DRV": 5},
        "M46I": {"ATV": 10},
        "M46L": {"ATV": 10},
        "I47V": {"ATV": 10, "DRV": 15},
        "G48V": {"ATV": 30},
        "I50L": {"ATV": 60},
        "I50V": {"DRV": 20},
        "I54L": {"ATV": 15, "DRV": 20},
        "I54M": {"ATV": 15, "DRV": 20},
        "L76V": {"DRV": 20},
        "V82A": {"ATV": 15},
        "V82F": {"ATV": 10, "DRV": 10},
        "I84V": {"ATV": 60, "DRV": 15},
        "N88S": {"ATV": 60},
        "L90M": {"ATV": 20},
    },
}

# Combinations: each group is a set of alternatives, all groups must be present.
COMBINATIONS: Tuple[Tuple[str, Tuple[Tuple[str, ...], ...], S], ...] = (
    ("RT", (("M41L",), ("T215Y", "T215F")), {"ABC": 5, "AZT": 15, "TDF": 5}),
    ("RT", (("M41L",), ("L210W",), ("T215Y", "T215F")), {"ABC": 10, "AZT": 10, "TDF": 10}),
    ("RT", (("D67N",), ("K70R",), ("K219Q", "K219E")), {"ABC": 5, "AZT": 10, "TDF": 5}),
    ("IN", (("G140S", "G140A", "G140C"), ("Q148H", "Q148K", "Q148R")), {"BIC": 30, "CAB": 40, "DTG": 30}),
    ("IN", (("E138K", "E138A", "E138T"), ("Q148H", "Q148K", "Q148R")), {"BIC": 25, "CAB": 35, "DTG": 25}),
    ("IN", (("N155H",), ("Q148H", "Q148K", "Q148R")), {"BIC": 20, "CAB": 20, "DTG": 20}),
)

# One-line teaching notes on the signature mutations.
NOTES = {
    "M184V": "Selected by lamivudine/emtricitabine; reduces viral fitness and increases tenofovir and "
             "zidovudine susceptibility.",
    "M184I": "Usually precedes M184V; same phenotype.",
    "K65R": "Selected by tenofovir (and abacavir); reduces tenofovir/abacavir/3TC activity but increases "
            "zidovudine susceptibility.",
    "K103N": "The classic efavirenz/nevirapine mutation; rilpivirine, doravirine and etravirine stay active.",
    "E138K": "Rilpivirine signature mutation, often with M184I.",
    "Y181C": "Broad first-generation NNRTI resistance; reduces rilpivirine and etravirine.",
    "Y188L": "High-level resistance to doravirine, efavirenz and rilpivirine.",
    "Q148H": "Integrase pathway; with G140S it reduces dolutegravir/bictegravir and abolishes raltegravir.",
    "N155H": "Raltegravir/elvitegravir pathway; second-generation INSTIs largely retained alone.",
    "R263K": "Selected by dolutegravir in INSTI-naive patients; low-to-intermediate dolutegravir resistance.",
    "G118R": "Rare dolutegravir-selected mutation with broad INSTI resistance.",
    "I50L": "Atazanavir signature mutation; increases susceptibility to other PIs.",
    "I84V": "Broad PI mutation; contributes to darunavir resistance with others.",
    "L76V": "Darunavir resistance-associated mutation.",
}
