"""Medicines reconciliation: free-text medicine names -> the interaction table's co-medication keys.

Names, UK brands and common combinations are matched exactly, then fuzzily (typos). Anything
not recognised is reported so it can be checked with the Liverpool HIV interaction checker.

dm+d coding: the NHS Dictionary of medicines and devices is licensed through NHS TRUD and is not
bundled. If a TRUD extract of virtual therapeutic moieties is saved as ``art_cds/data/dmd/vtm.csv``
(columns ``VTMID,NM``), matched medicines are shown with their dm+d VTM code.
"""
from __future__ import annotations

import csv
import difflib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DMD_VTM = Path(__file__).resolve().parent.parent / "data" / "dmd" / "vtm.csv"

SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "rifampicin": ("rifampicin", "rifampin", "rifadin", "rimactane", "rifinah", "rifater", "voractiv"),
    "rifabutin": ("rifabutin", "mycobutin"),
    "rifapentine": ("rifapentine", "priftin"),
    "carbamazepine": ("carbamazepine", "tegretol", "carbagen"),
    "oxcarbazepine": ("oxcarbazepine", "trileptal"),
    "phenytoin": ("phenytoin", "fosphenytoin", "epanutin"),
    "phenobarbital": ("phenobarbital", "phenobarbitone", "primidone", "mysoline"),
    "st_johns_wort": ("st john's wort", "st johns wort", "hypericum"),
    "ppi": ("omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole", "losec", "nexium", "zoton"),
    "h2ra": ("famotidine", "ranitidine", "cimetidine", "nizatidine", "pepcid"),
    "antacids": ("gaviscon", "rennie", "calcium carbonate", "adcal", "adcal-d3", "calcichew", "ferrous sulfate",
                 "ferrous sulphate", "ferrous fumarate", "ferrous gluconate", "iron", "zinc", "magnesium",
                 "magnesium hydroxide", "aluminium hydroxide", "maalox", "multivitamin", "sucralfate"),
    "simvastatin": ("simvastatin", "lovastatin", "zocor"),
    "atorvastatin": ("atorvastatin", "rosuvastatin", "lipitor", "crestor"),
    "amiodarone": ("amiodarone", "cordarone"),
    "fampridine": ("fampridine", "fampyra", "dalfampridine"),
    "doac": ("apixaban", "rivaroxaban", "dabigatran", "edoxaban", "eliquis", "xarelto", "pradaxa", "lixiana"),
    "ticagrelor": ("ticagrelor", "clopidogrel", "brilique", "plavix"),
    "metformin": ("metformin", "glucophage"),
    "dexamethasone": ("dexamethasone",),
    "inhaled_steroid": ("fluticasone", "budesonide", "mometasone", "flixotide", "seretide", "relvar", "avamys",
                        "flixonase", "symbicort", "pulmicort", "rhinocort", "nasonex"),
    "salmeterol": ("salmeterol", "serevent"),
    "hormonal_contraception": ("combined pill", "ethinylestradiol", "levonorgestrel", "desogestrel", "etonogestrel",
                               "drospirenone", "norethisterone", "microgynon", "rigevidon", "yasmin", "cerazette",
                               "nexplanon", "levonelle", "evra", "nuvaring", "implant"),
    "methadone": ("methadone", "physeptone"),
    "midazolam_oral": ("midazolam", "triazolam", "buccolam"),
    "quetiapine": ("quetiapine", "seroquel"),
    "pimozide": ("pimozide", "lurasidone", "latuda"),
    "sildenafil_pah": ("revatio", "sildenafil for pah", "sildenafil pah"),
    "pde5_ed": ("sildenafil", "tadalafil", "vardenafil", "viagra", "cialis", "levitra"),
    "avanafil": ("avanafil", "spedra"),
    "colchicine": ("colchicine",),
    "ergot": ("ergotamine", "dihydroergotamine", "migril"),
    "sof_vel": ("sofosbuvir/velpatasvir", "epclusa", "velpatasvir"),
    "glec_pib": ("glecaprevir/pibrentasvir", "maviret", "glecaprevir"),
    "elbasvir": ("elbasvir/grazoprevir", "zepatier", "elbasvir"),
    "ledipasvir": ("ledipasvir/sofosbuvir", "harvoni", "ledipasvir"),
    "clarithromycin": ("clarithromycin", "klaricid"),
    "itraconazole": ("itraconazole", "posaconazole", "sporanox", "noxafil"),
    "voriconazole": ("voriconazole", "vfend"),
    "artemether": ("artemether", "lumefantrine", "riamet"),
    "atovaquone": ("atovaquone/proguanil", "malarone"),
    "tacrolimus": ("tacrolimus", "ciclosporin", "cyclosporine", "prograf", "adoport", "advagraf", "neoral"),
    "dronedarone": ("dronedarone", "ranolazine", "multaq", "ranexa"),
    "ivabradine": ("ivabradine", "procoralan"),
    "digoxin": ("digoxin", "lanoxin"),
    "lomitapide": ("lomitapide", "lojuxta"),
    "domperidone": ("domperidone", "motilium"),
    "naloxegol": ("naloxegol", "moventig"),
    "alfuzosin": ("alfuzosin", "xatral"),
    "lamotrigine": ("lamotrigine", "lamictal"),
    "antidepressant": ("sertraline", "citalopram", "escitalopram", "fluoxetine", "paroxetine", "fluvoxamine",
                       "trazodone", "lustral", "cipralex", "prozac", "seroxat"),
    "opioid": ("fentanyl", "oxycodone", "oxycontin", "durogesic"),
    "steroid_injection": ("triamcinolone", "methylprednisolone", "kenalog", "depo-medrone", "adcortyl"),
    "bosentan": ("bosentan", "tracleer"),
}

# Combination products that carry more than one interacting ingredient
ALSO: Dict[str, Tuple[str, ...]] = {"seretide": ("salmeterol",), "combodart": (), "voractiv": ()}

_INDEX: Dict[str, str] = {name: key for key, names in SYNONYMS.items() for name in names}


@dataclass(frozen=True)
class Reconciled:
    text: str
    key: Optional[str]  # co-medication key, or None if not recognised
    also: Tuple[str, ...] = ()
    matched_as: str = ""
    fuzzy: bool = False
    dmd_vtm: str = ""


@lru_cache(maxsize=1)
def _dmd() -> Dict[str, str]:
    if not DMD_VTM.exists():
        return {}
    with DMD_VTM.open(newline="", encoding="utf-8") as f:
        return {row["NM"].strip().lower(): row["VTMID"].strip() for row in csv.DictReader(f) if row.get("NM")}


def _clean(line: str) -> str:
    line = line.lower().strip()
    line = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|micrograms?|g|ml|units?|%)\b.*$", "", line)  # drop dose and after
    line = re.sub(r"\b(tablets?|capsules?|inhaler|injection|cream|oral|solution|once|twice|daily|od|bd|tds|"
                  r"prn|nocte|mane)\b.*$", "", line)
    return re.sub(r"[^a-z0-9'/ -]", "", line).strip(" -/")


def reconcile_line(raw: str) -> Reconciled:
    text = raw.strip()
    name = _clean(text)
    if not name:
        return Reconciled(text, None)
    dmd = _dmd().get(name, "")
    if name in _INDEX:
        return Reconciled(text, _INDEX[name], ALSO.get(name, ()), name, dmd_vtm=dmd)
    for token in sorted(re.split(r"[ /]+", name), key=len, reverse=True):  # "sertraline hydrochloride"
        if token in _INDEX:
            return Reconciled(text, _INDEX[token], ALSO.get(token, ()), token, dmd_vtm=_dmd().get(token, ""))
    close = difflib.get_close_matches(name, _INDEX, n=1, cutoff=0.85)
    if close:
        return Reconciled(text, _INDEX[close[0]], ALSO.get(close[0], ()), close[0], fuzzy=True,
                          dmd_vtm=_dmd().get(close[0], ""))
    return Reconciled(text, None, dmd_vtm=dmd)


def reconcile(text: str) -> List[Reconciled]:
    lines = [l for l in re.split(r"[\n;]+|,(?![^(]*\))", text or "") if l.strip()]
    return [reconcile_line(l) for l in lines][:60]
