"""Antiretroviral substances: class, mechanism and where their SmPC lives.

Product-level facts (dosing, interactions, adverse reactions, pharmacokinetics)
are read from the UK SmPCs — see ``smpc.py``. What is kept here is the
class-level pharmacology a teaching tool needs to explain them, and
``monograph`` — the product whose SmPC is used as the drug's monograph
(the single-agent product where one is licensed in the UK).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

NRTI = "NRTI"
NNRTI = "NNRTI"
INSTI = "INSTI"
PI = "PI"
BOOSTER = "Booster"
ENTRY = "Entry"
CAPSID = "Capsid"


@dataclass(frozen=True)
class DrugClass:
    code: str
    name: str
    target: str  # the viral step it blocks (matches the life-cycle diagram)
    mechanism: str
    class_effects: Tuple[str, ...]
    barrier: str  # genetic barrier to resistance, in general terms


CLASSES: Dict[str, DrugClass] = {
    NRTI: DrugClass(
        NRTI, "Nucleoside/nucleotide reverse transcriptase inhibitors", "reverse-transcription",
        "Prodrugs phosphorylated by host-cell kinases to the active triphosphate (diphosphate for tenofovir). "
        "The active anabolite competes with the natural deoxynucleotide for HIV reverse transcriptase and, "
        "lacking a 3'-hydroxyl group, terminates the growing proviral DNA chain once incorporated.",
        ("Mitochondrial toxicity (older thymidine analogues: lipoatrophy, lactic acidosis, myopathy)",
         "Lamivudine, emtricitabine and tenofovir also suppress hepatitis B — stopping them can cause "
         "an HBV flare"),
        "Low for lamivudine/emtricitabine alone (M184V/I); higher for tenofovir (K65R).",
    ),
    NNRTI: DrugClass(
        NNRTI, "Non-nucleoside reverse transcriptase inhibitors", "reverse-transcription",
        "Bind a hydrophobic pocket close to (not in) the reverse transcriptase active site, causing an "
        "allosteric change that blocks DNA polymerisation. No intracellular activation is needed. "
        "Active against HIV-1 only (not HIV-2 or group O).",
        ("Rash (including severe cutaneous reactions)", "Hepatotoxicity",
         "CYP3A substrates or inducers — interaction-prone"),
        "Low: a single mutation (e.g. K103N, Y181C, E138K) can confer high-level resistance.",
    ),
    INSTI: DrugClass(
        INSTI, "Integrase strand-transfer inhibitors", "integration",
        "Chelate the two Mg²⁺ ions in the integrase active site, blocking the strand-transfer step that "
        "inserts proviral DNA into the host genome.",
        ("Weight gain", "Insomnia, headache, neuropsychiatric effects",
         "Chelation by polyvalent cations (antacids, iron, calcium) lowers absorption",
         "Dolutegravir and bictegravir inhibit OCT2 → small, non-progressive creatinine rise"),
        "High for dolutegravir and bictegravir; low for raltegravir and elvitegravir.",
    ),
    PI: DrugClass(
        PI, "Protease inhibitors", "maturation",
        "Peptidomimetic inhibitors of the viral aspartyl protease, preventing cleavage of the Gag and "
        "Gag-Pol polyproteins so that new virions are immature and non-infectious. Given with a "
        "pharmacokinetic booster (ritonavir or cobicistat).",
        ("Gastrointestinal effects", "Dyslipidaemia", "Many CYP3A-mediated interactions (via the booster)"),
        "High when boosted: several mutations are needed for darunavir resistance.",
    ),
    BOOSTER: DrugClass(
        BOOSTER, "Pharmacokinetic enhancers", "maturation",
        "Strong mechanism-based CYP3A inhibitors with no useful antiviral activity at booster doses; they "
        "raise and prolong exposure to the co-administered protease inhibitor.",
        ("Extensive drug–drug interactions",
         "Cobicistat inhibits tubular creatinine secretion (MATE1) — creatinine rises without a true fall in GFR"),
        "—",
    ),
    ENTRY: DrugClass(
        ENTRY, "Entry and attachment inhibitors", "entry",
        "Maraviroc blocks the CCR5 co-receptor (R5-tropic virus only); fostemsavir's active moiety "
        "temsavir binds gp120 and prevents attachment to CD4.",
        ("Maraviroc: hepatotoxicity, postural hypotension", "Fostemsavir: QT prolongation at high exposure"),
        "Reserved for multiclass resistance.",
    ),
    CAPSID: DrugClass(
        CAPSID, "Capsid inhibitors", "uncoating",
        "Lenacapavir binds the interface between capsid protein subunits, disrupting capsid-mediated nuclear "
        "import, assembly and capsid formation — it acts at several stages of the life cycle.",
        ("Injection-site nodules and reactions",),
        "Reserved for multiclass resistance.",
    ),
}


@dataclass(frozen=True)
class Drug:
    code: str
    name: str
    drug_class: str
    monograph: str  # product key whose SmPC serves as the monograph
    abbreviation_note: str = ""

    @property
    def klass(self) -> DrugClass:
        return CLASSES[self.drug_class]


DRUGS: Dict[str, Drug] = {d.code: d for d in (
    Drug("TAF", "Tenofovir alafenamide", NRTI, "descovy"),
    Drug("TDF", "Tenofovir disoproxil", NRTI, "viread",
         "245 mg tenofovir disoproxil (as fumarate) — the UK/EU expression of the US '300 mg TDF'"),
    Drug("FTC", "Emtricitabine", NRTI, "emtriva"),
    Drug("3TC", "Lamivudine", NRTI, "epivir"),
    Drug("ABC", "Abacavir", NRTI, "ziagen"),
    Drug("AZT", "Zidovudine", NRTI, "retrovir"),
    Drug("EFV", "Efavirenz", NNRTI, "efavirenz"),
    Drug("RPV", "Rilpivirine", NNRTI, "edurant"),
    Drug("DOR", "Doravirine", NNRTI, "pifeltro"),
    Drug("ETR", "Etravirine", NNRTI, "intelence"),
    Drug("DTG", "Dolutegravir", INSTI, "tivicay"),
    Drug("BIC", "Bictegravir", INSTI, "biktarvy"),
    Drug("RAL", "Raltegravir", INSTI, "isentress"),
    Drug("CAB", "Cabotegravir", INSTI, "vocabria_tab"),
    Drug("DRV", "Darunavir", PI, "prezista"),
    Drug("ATV", "Atazanavir", PI, "atazanavir"),
    Drug("RTV", "Ritonavir", BOOSTER, "norvir"),
    Drug("COBI", "Cobicistat", BOOSTER, "tybost"),
    Drug("MVC", "Maraviroc", ENTRY, "celsentri"),
    Drug("FTR", "Fostemsavir", ENTRY, "rukobia"),
    Drug("LEN", "Lenacapavir", CAPSID, "sunlenca_tab"),
)}

TENOFOVIR = frozenset({"TDF", "TAF"})
CYTIDINE = frozenset({"FTC", "3TC"})
BOOSTERS = frozenset({"RTV", "COBI"})
HIGH_BARRIER = frozenset({"DTG", "BIC", "DRV"})
LOW_BARRIER = frozenset({"EFV", "RPV", "RAL", "DOR", "ETR"})


def drug_class(code: str) -> str:
    return DRUGS[code].drug_class


def name(code: str) -> str:
    return DRUGS[code].name


# Old and current brand names an ART history might contain -> drug codes
_HISTORIC_BRANDS = {
    "atripla": ("EFV", "FTC", "TDF"), "truvada": ("FTC", "TDF"), "kivexa": ("ABC", "3TC"),
    "combivir": ("AZT", "3TC"), "trizivir": ("ABC", "3TC", "AZT"), "eviplera": ("FTC", "RPV", "TDF"),
    "stribild": ("EVG", "COBI", "FTC", "TDF"), "genvoya": ("EVG", "COBI", "FTC", "TAF"),
    "kaletra": ("LPV", "RTV"), "sustiva": ("EFV",), "viramune": ("NVP",), "tle": ("TDF", "3TC", "EFV"),
    "tld": ("TDF", "3TC", "DTG"),
}
_EXTRA_CODES = {"EVG": "Elvitegravir", "NVP": "Nevirapine", "LPV": "Lopinavir"}
_EXTRA_CLASSES = {"EVG": INSTI, "NVP": NNRTI, "LPV": PI}


def class_of(code: str) -> str:
    return DRUGS[code].drug_class if code in DRUGS else _EXTRA_CLASSES.get(code, "")


def drugs_from_text(text: str):
    """Resolve 'Atripla', 'DTG + TDF/FTC', 'dolutegravir, emtricitabine' etc. to drug codes."""
    import re

    from .products import PRODUCTS

    found = []
    low = text.lower()
    for code, d in DRUGS.items():  # full names first ("tenofovir disoproxil" vs "tenofovir alafenamide")
        if d.name.lower() in low:
            low = low.replace(d.name.lower(), code.lower())
    brands = dict(_HISTORIC_BRANDS)
    for p in PRODUCTS:
        brands.setdefault(p.brand.split(" (")[0].split()[0].lower(), p.ingredients)
    for token in re.split(r"[\s,+/;]+", low):
        if not token:
            continue
        if token in brands:
            found += brands[token]
            continue
        up = token.upper()
        if up in DRUGS or up in _EXTRA_CODES:
            found.append(up)
            continue
        for code, d in DRUGS.items():
            if d.name.lower().split()[0] == token and token != "tenofovir":
                found.append(code)
        for code, name in _EXTRA_CODES.items():
            if name.lower() == token:
                found.append(code)
    return tuple(dict.fromkeys(found))
