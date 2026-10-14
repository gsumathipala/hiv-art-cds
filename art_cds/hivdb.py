"""Client for the Stanford HIV Drug Resistance Database (HIVdb) GraphQL service.

https://hivdb.stanford.edu/page/webservice/ — the same algorithm the Stanford web tools
use. Calls are opt-in per assessment: mutation lists or sequences are sent to Stanford,
so only send what your information-governance rules allow (no identifiers are ever sent).
Results are cached in memory for the life of the process.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Dict, List, Tuple

ENDPOINT = "https://hivdb.stanford.edu/graphql"
TIMEOUT = 25

# HIVdb drug abbreviations -> this app's drug codes
DRUG_MAP = {"ATV/r": "ATV", "DRV/r": "DRV", "LPV/r": "LPV", "FPV/r": "FPV", "IDV/r": "IDV", "NFV": "NFV",
            "SQV/r": "SQV", "TPV/r": "TPV"}

_DRUG_FIELDS = "version{text publishDate} gene{name} drugScores{drug{displayAbbr} score level " \
               "partialScores{mutations{text} score}}"


class HivdbError(RuntimeError):
    pass


def _post(query: str, variables: Dict) -> Dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json",
                                                              "User-Agent": "ART-Navigator-UK"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise HivdbError(f"Stanford HIVdb could not be reached ({exc})") from exc
    if data.get("errors"):
        raise HivdbError("Stanford HIVdb rejected the request: " + data["errors"][0].get("message", "")[:200])
    return data["data"]


def _drugs(drug_resistance: List[Dict]) -> Tuple[str, Dict[str, Dict]]:
    version, drugs = "", {}
    for gene in drug_resistance:
        version = gene["version"]["text"]
        for s in gene["drugScores"]:
            code = DRUG_MAP.get(s["drug"]["displayAbbr"], s["drug"]["displayAbbr"])
            contributors = []
            for part in s["partialScores"]:
                label = " + ".join(m["text"] for m in part["mutations"])
                if part["score"]:
                    contributors.append(label if len(part["mutations"]) == 1 else f"({label})")
            drugs[code] = {"score": s["score"], "level": s["level"], "contributors": contributors}
    return version, drugs


@lru_cache(maxsize=256)
def analyse_mutations(mutations: Tuple[str, ...]) -> Dict:
    """Score a mutation list such as ('RT:K65R', 'IN:Q148H')."""
    query = ("query($m:[String]!){ mutationsAnalysis(mutations:$m){ validationResults{level message} "
             "drugResistance{" + _DRUG_FIELDS + "} } }")
    data = _post(query, {"m": list(mutations)})["mutationsAnalysis"]
    version, drugs = _drugs(data["drugResistance"])
    return {"version": version, "drugs": drugs,
            "validation": [f"{v['level']}: {v['message']}" for v in data["validationResults"]]}


@lru_cache(maxsize=64)
def analyse_sequence(fasta: str) -> Dict:
    """Align and analyse a pol sequence (FASTA or bare nucleotides)."""
    lines = [l.strip() for l in fasta.strip().splitlines() if l.strip()]
    header = lines[0][1:] if lines and lines[0].startswith(">") else "sequence"
    seq = "".join(l for l in lines if not l.startswith(">"))
    seq = re.sub(r"[^A-Za-z]", "", seq)
    if len(seq) < 100:
        raise HivdbError("Sequence too short to analyse (need at least 100 nucleotides).")
    query = ("query($s:[UnalignedSequenceInput]!){ sequenceAnalysis(sequences:$s){ validationResults{level message} "
             "bestMatchingSubtype{display} apobecMutationCount availableGenes{name} "
             "mutations{gene{name} text isApobecMutation isUnusual} drugResistance{" + _DRUG_FIELDS + "} } }")
    data = _post(query, {"s": [{"header": header, "sequence": seq}]})["sequenceAnalysis"][0]
    version, drugs = _drugs(data["drugResistance"])
    muts: Dict[str, List[str]] = {}
    apobec, unusual = [], []
    for m in data["mutations"]:
        gene = m["gene"]["name"]
        muts.setdefault(gene, []).append(m["text"])
        if m["isApobecMutation"]:
            apobec.append(f"{gene}:{m['text']}")
        if m["isUnusual"]:
            unusual.append(f"{gene}:{m['text']}")
    subtype = (data.get("bestMatchingSubtype") or {}).get("display", "")
    return {"version": version, "drugs": drugs, "mutations": muts, "subtype": subtype, "apobec": apobec,
            "apobec_count": data.get("apobecMutationCount") or 0, "unusual": unusual,
            "genes": [g["name"] for g in data.get("availableGenes") or []],
            "validation": [f"{v['level']}: {v['message']}" for v in data["validationResults"]]}
