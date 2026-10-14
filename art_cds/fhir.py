"""Read a FHIR R4 Bundle into a patient profile.

Supports the resources a trust's record would realistically send: Patient, Observation (viral load,
CD4, creatinine, cystatin C, weight, height, bilirubin, albumin, INR, HBV/HCV serology),
Condition and MedicationStatement/MedicationRequest. Codes are matched by LOINC where possible and
by display text otherwise, so it also works with partially coded extracts.

This reads data only — nothing is written back, and no identifiers are kept.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple

from .knowledge.conditions import COMORBIDITIES
from .models import LabValue, PatientProfile

# LOINC codes -> what the value means here
LOINC = {
    "20447-9": "viral_load", "25836-8": "viral_load", "29539-9": "viral_load", "49890-7": "viral_load",
    "24467-3": "cd4", "8124-1": "cd4", "14135-8": "cd4",
    "2160-0": "creatinine", "38483-4": "creatinine",
    "33863-2": "cystatin",
    "29463-7": "weight", "8302-2": "height",
    "1975-2": "bilirubin", "1751-7": "albumin", "6301-6": "inr", "34714-6": "inr",
    "5195-3": "hbsag", "22322-2": "anti_hbs", "16933-4": "anti_hbc", "13952-7": "anti_hbc",
    "13955-0": "hcv", "16128-1": "hcv",
}
TEXT_HINTS = (
    ("hiv", "viral_load"), ("cd4", "cd4"), ("creatinin", "creatinine"), ("cystatin", "cystatin"),
    ("body weight", "weight"), ("weight", "weight"), ("height", "height"), ("bilirubin", "bilirubin"),
    ("albumin", "albumin"), ("inr", "inr"), ("prothrombin", "inr"), ("hbsag", "hbsag"),
    ("hepatitis b surface antigen", "hbsag"), ("anti-hbs", "anti_hbs"), ("hepatitis b surface antibody", "anti_hbs"),
    ("anti-hbc", "anti_hbc"), ("hepatitis b core", "anti_hbc"), ("hepatitis c", "hcv"),
)
CONDITION_HINTS = (
    ("tubercul", "active_tb"), ("cardiovascular", "cvd"), ("myocardial", "cvd"), ("ischaemic heart", "cvd"),
    ("osteoporos", "osteoporosis"), ("fragility fracture", "osteoporosis"), ("depress", "psychiatric"),
    ("psychos", "psychiatric"), ("obes", "weight"), ("dyslipid", "dyslipidaemia"), ("hyperlipid", "dyslipidaemia"),
    ("diabet", "diabetes"), ("cryptococc", "crypto_meningitis"),
)

Note = Tuple[str, str]  # (level, message)


def _codes(resource: Dict, field: str = "code") -> List[str]:
    return [c.get("code", "") for c in (resource.get(field) or {}).get("coding", []) if c.get("code")]


def _display(resource: Dict, field: str = "code") -> str:
    node = resource.get(field) or {}
    texts = [node.get("text", "")] + [c.get("display", "") for c in node.get("coding", [])]
    return " ".join(t for t in texts if t).lower()


def _kind(observation: Dict) -> Optional[str]:
    for code in _codes(observation):
        if code in LOINC:
            return LOINC[code]
    text = _display(observation)
    for hint, kind in TEXT_HINTS:
        if hint in text:
            return kind
    return None


def _value(observation: Dict) -> Tuple[Optional[float], bool, str]:
    """(numeric value, censored/below-limit, text result)."""
    q = observation.get("valueQuantity")
    if q and q.get("value") is not None:
        return float(q["value"]), q.get("comparator") in ("<", "<="), ""
    for field in ("valueCodeableConcept", "valueString"):
        node = observation.get(field)
        if isinstance(node, str):
            return None, False, node.lower()
        if isinstance(node, dict):
            text = " ".join([node.get("text", "")] + [c.get("display", "") for c in node.get("coding", [])])
            return None, False, text.lower()
    return None, False, ""


def _date(resource: Dict) -> str:
    for field in ("effectiveDateTime", "effectiveInstant", "issued", "onsetDateTime", "authoredOn"):
        value = resource.get(field)
        if isinstance(value, str):
            return value[:10]
    period = resource.get("effectivePeriod") or {}
    return str(period.get("start", ""))[:10]


def _positive(text: str) -> Optional[bool]:
    if any(w in text for w in ("positive", "reactive", "detected")):
        return not any(w in text for w in ("non-reactive", "not detected", "negative"))
    if any(w in text for w in ("negative", "non-reactive", "not detected")):
        return False
    return None


def parse_bundle(bundle: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Note]]:
    """Return form-style fields for ``web.forms.parse_patient`` plus notes about what was read."""
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise ValueError("Not a FHIR Bundle (expected resourceType 'Bundle').")
    entries = [e.get("resource") or {} for e in bundle.get("entry") or []]
    fields: Dict[str, Any] = {}
    notes: List[Note] = []
    series: Dict[str, List[LabValue]] = {"viral_load": [], "cd4": []}
    latest: Dict[str, Tuple[str, float]] = {}
    conditions: List[str] = []
    medicines: List[str] = []
    counts: Dict[str, int] = {}

    for r in entries:
        kind = r.get("resourceType")
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "Patient":
            if r.get("birthDate"):
                from datetime import date
                born = date.fromisoformat(r["birthDate"][:10])
                today = date.today()
                fields["age"] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            if r.get("gender") in ("male", "female"):
                fields["sex"] = r["gender"]
        elif kind == "Observation":
            what = _kind(r)
            if not what:
                continue
            value, censored, text = _value(r)
            when = _date(r)
            if what in series and value is not None:
                series[what].append(LabValue(when or "1900-01-01", value, censored))
            elif what in ("hbsag", "anti_hbs", "anti_hbc", "hcv"):
                result = _positive(text)
                if result is None and value is not None:
                    result = value > 0
                if result is not None:
                    if what == "hcv":
                        fields["hcv"] = "on" if result else ""
                    else:
                        fields[what] = "positive" if result else "negative"
            elif value is not None and (what not in latest or when >= latest[what][0]):
                latest[what] = (when, value)
        elif kind == "Condition":
            text = _display(r)
            if (r.get("clinicalStatus") or {}).get("coding", [{}])[0].get("code") in ("resolved", "inactive"):
                continue
            for hint, key in CONDITION_HINTS:
                if hint in text and key in COMORBIDITIES and key not in conditions:
                    conditions.append(key)
        elif kind in ("MedicationStatement", "MedicationRequest"):
            name = _display(r, "medicationCodeableConcept") or _display(r, "medication")
            status = r.get("status", "active")
            if name and status in ("active", "completed", "intended", "unknown", ""):
                medicines.append(name)

    for what, (when, value) in latest.items():
        key = {"creatinine": "creatinine_umol", "cystatin": "cystatin_c", "weight": "weight_kg",
               "height": "height_cm", "bilirubin": "bilirubin_umol", "albumin": "albumin_g_l",
               "inr": "inr"}.get(what)
        if key:
            fields[key] = value
    for what, values in series.items():
        if values:
            values.sort(key=lambda v: v.date)
            fields[f"{'vl' if what == 'viral_load' else 'cd4'}_history"] = "\n".join(
                f"{v.date} {'<' if v.censored else ''}{v.value:g}" for v in values)
            fields[what] = int(values[-1].value) if not values[-1].censored else 0
    if conditions:
        fields["comorbidities"] = conditions
    if medicines:
        fields["medicines_text"] = "\n".join(dict.fromkeys(medicines))

    notes.append(("info", "Resources read: " + ", ".join(f"{n} × {k}" for k, n in sorted(counts.items())) + "."))
    if series["viral_load"]:
        notes.append(("info", f"{len(series['viral_load'])} viral load and {len(series['cd4'])} CD4 results imported."))
    if medicines:
        notes.append(("info", f"{len(set(medicines))} medicines imported — check the reconciliation on the report."))
    for needed, label in (("age", "date of birth"), ("sex", "gender")):
        if needed not in fields:
            notes.append(("warning", f"No {label} in the bundle — enter it by hand."))
    notes.append(("warning", "Nothing is imported for HLA-B*57:01, resistance genotypes or ART history — add them "
                             "by hand; they are rarely coded in FHIR extracts."))
    return fields, notes
