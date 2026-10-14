"""Turn submitted form data (or JSON) into a validated PatientProfile."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from ..knowledge.conditions import COMORBIDITIES
from ..knowledge.interactions import COMEDICATIONS_BY_KEY
from ..models.patient import (
    ARV_CLASSES, STOP_REASONS, ArtEpisode, ChildPugh, GenotypeTest, LabResult, LabValue, PatientProfile, Pregnancy,
    TreatmentStatus,
)
from ..knowledge.drugs import drugs_from_text
from ..knowledge.regimens import REGIMENS_BY_ID

MAX_ART = 8
_LINE = re.compile(r"^\s*(\d{4}-\d{2}(?:-\d{2})?)[\s,;:]+(<|≤|&lt;)?\s*([\d,.]+|tnd|not detected|undetectable)",
                   re.I)

MAX_GENOTYPES = 5
SUBTYPES = ("", "A1", "A6", "B", "C", "D", "F", "G", "CRF01_AE", "CRF02_AG", "other")
TROPISMS = ("unknown", "R5", "X4", "dual/mixed")
VIRUS_TYPES = ("HIV-1", "HIV-2", "HIV-1/HIV-2")

Errors = Dict[str, str]


def _getlist(form: Mapping[str, Any], name: str) -> List[str]:
    if hasattr(form, "getlist"):
        return [v for v in form.getlist(name) if v]
    value = form.get(name)
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


def _bool(form: Mapping[str, Any], name: str) -> bool:
    value = form.get(name)
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("on", "true", "1", "yes")


def _number(form, name, errors, lo, hi, required=False, integer=True, label=None):
    raw = form.get(name)
    if raw is None or str(raw).strip() == "":
        if required:
            errors[name] = f"{label or name} is required."
        return None
    try:
        value = float(str(raw).replace(",", "").strip())
    except ValueError:
        errors[name] = f"{label or name} must be a number."
        return None
    if not lo <= value <= hi:
        errors[name] = f"{label or name} must be between {lo:g} and {hi:g}."
        return None
    return int(round(value)) if integer else value


def _enum(form, name, enum, default, errors):
    raw = form.get(name)
    if raw in (None, ""):
        return default
    try:
        return enum(raw)
    except ValueError:
        errors[name] = f"Invalid value for {name}."
        return default


def _choice(form, name, allowed, errors):
    value = form.get(name) or ""
    if value not in allowed:
        errors[name] = f"Invalid value for {name}."
        return ""
    return value


def _subset(values: Iterable[str], allowed: Iterable[str], name: str, errors: Errors) -> frozenset:
    allowed = set(allowed)
    bad = [v for v in values if v not in allowed]
    if bad:
        errors[name] = f"Unknown option(s): {', '.join(bad)}"
    return frozenset(v for v in values if v in allowed)


def _genotypes(form: Mapping[str, Any], errors: Errors) -> List[GenotypeTest]:
    """Genotype rows g0_..g4_ from the form, or a ``genotypes`` list in JSON."""
    rows: List[Mapping[str, Any]] = []
    raw = form.get("genotypes")
    if isinstance(raw, list):
        rows = [r for r in raw if isinstance(r, dict)]
    else:
        for i in range(MAX_GENOTYPES):
            rows.append({k: form.get(f"g{i}_{k}") or "" for k in
                         ("date", "source", "rt", "pr", "integrase", "sequence")})
    tests = []
    for i, r in enumerate(rows):
        fields = {k: str(r.get(k) or "").strip() for k in ("date", "source", "rt", "pr", "integrase", "sequence")}
        if not any(fields[k] for k in ("rt", "pr", "integrase", "sequence")) and not fields["date"]:
            continue
        if fields["source"] not in ("", "plasma", "proviral"):
            errors[f"g{i}_source"] = "Source must be plasma or proviral."
        if len(fields["sequence"]) > 20000:
            errors[f"g{i}_sequence"] = "Sequence too long (max 20,000 characters)."
        tests.append(GenotypeTest(date=fields["date"][:10], source=fields["source"] or "plasma",
                                  rt=fields["rt"][:500], pr=fields["pr"][:500], integrase=fields["integrase"][:500],
                                  sequence=fields["sequence"]))
    return tests


def _lab_series(form: Mapping[str, Any], name: str, errors: Errors, label: str) -> Tuple[LabValue, ...]:
    """One result per line: 'YYYY-MM-DD value' (value may be '<50', 'TND'), or a JSON list of {date, value}."""
    raw = form.get(name)
    lines: List[str] = []
    if isinstance(raw, list):
        lines = [f"{r.get('date', '')} {r.get('value', '')}" for r in raw if isinstance(r, dict)]
    elif raw:
        lines = str(raw).splitlines()
    out: List[LabValue] = []
    for n, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        m = _LINE.match(line)
        if not m:
            errors[name] = f"{label}: line {n} not understood — use 'YYYY-MM-DD value'."
            continue
        date_, lt, value = m.group(1), m.group(2), m.group(3).lower()
        if value in ("tnd", "not detected", "undetectable"):
            out.append(LabValue(date_, 20.0, True))
            continue
        try:
            num = float(value.replace(",", ""))
        except ValueError:
            errors[name] = f"{label}: line {n} has no number."
            continue
        out.append(LabValue(date_, num, bool(lt)))
    return tuple(sorted(out, key=lambda v: v.date))


def _art_history(form: Mapping[str, Any], errors: Errors) -> Tuple[ArtEpisode, ...]:
    raw = form.get("art_history")
    rows: List[Mapping[str, Any]] = [r for r in raw if isinstance(r, dict)] if isinstance(raw, list) else [
        {k: form.get(f"a{i}_{k}") or "" for k in ("start", "stop", "regimen", "other", "reason")}
        for i in range(MAX_ART)]
    episodes = []
    for i, r in enumerate(rows):
        start, stop = str(r.get("start") or "").strip(), str(r.get("stop") or "").strip()
        regimen, other = str(r.get("regimen") or "").strip(), str(r.get("other") or "").strip()
        reason = str(r.get("reason") or r.get("reason_stopped") or "").strip()
        if not (start or regimen or other):
            continue
        if reason not in STOP_REASONS:
            errors[f"a{i}_reason"] = "Unknown reason."
        if regimen in REGIMENS_BY_ID:
            comps, label = REGIMENS_BY_ID[regimen].components, REGIMENS_BY_ID[regimen].short
        else:
            comps, label = drugs_from_text(other or regimen), (other or regimen)
            if not comps:
                errors[f"a{i}_other"] = f"Regimen '{label}' not recognised — enter drug names or abbreviations."
        if stop and start and stop < start:
            errors[f"a{i}_stop"] = "Stop date is before the start date."
        episodes.append(ArtEpisode(start=start[:10], stop=stop[:10], regimen=label[:80], components=comps,
                                   reason_stopped=reason))
    return tuple(sorted(episodes, key=lambda e: e.start))


def parse_patient(form: Mapping[str, Any]) -> Tuple[Optional[PatientProfile], Errors]:
    errors: Errors = {}
    age = _number(form, "age", errors, 0, 120, required=True, label="Age")
    weight = _number(form, "weight_kg", errors, 2, 350, integer=False, label="Weight")
    sex = form.get("sex") or "male"
    if sex not in ("male", "female"):
        errors["sex"] = "Sex must be male or female."
    status = _enum(form, "status", TreatmentStatus, TreatmentStatus.NAIVE, errors)
    pregnancy = _enum(form, "pregnancy", Pregnancy, Pregnancy.NOT_APPLICABLE, errors)
    if sex != "female":
        pregnancy = Pregnancy.NOT_APPLICABLE
    elif pregnancy is Pregnancy.NOT_APPLICABLE:
        pregnancy = Pregnancy.NOT_PREGNANT

    failed = _subset(_getlist(form, "failed_classes"), ARV_CLASSES, "failed_classes", errors)
    if status is TreatmentStatus.NAIVE:
        failed = frozenset()

    genotypes = _genotypes(form, errors)
    genotype = form.get("genotype") == "available" or _bool(form, "genotype_available") or bool(genotypes)
    if genotypes and form.get("genotype") == "pending":
        genotype = True
    threshold = _number(form, "minority_threshold", errors, 1, 50, integer=False, label="Minority-variant threshold")
    subtype = form.get("subtype") or ""
    if subtype not in SUBTYPES:
        errors["subtype"] = "Unknown subtype."
    tropism = form.get("tropism") or "unknown"
    if tropism not in TROPISMS:
        errors["tropism"] = "Unknown tropism result."
    profile_kwargs = dict(
        age=age or 0,
        sex=sex,
        weight_kg=weight,
        pregnancy=pregnancy,
        breastfeeding=_bool(form, "breastfeeding") and sex == "female",
        status=status,
        virus_type=_choice(form, "virus_type", VIRUS_TYPES + ("",), errors) or "HIV-1",
        failed_classes=failed,
        cab_prep_exposure=_bool(form, "cab_prep_exposure"),
        rapid_start=_bool(form, "rapid_start") and status is TreatmentStatus.NAIVE,
        viral_load=_number(form, "viral_load", errors, 0, 50_000_000, label="HIV RNA"),
        cd4=_number(form, "cd4", errors, 0, 5000, label="CD4 count"),
        crcl=_number(form, "crcl", errors, 0, 250, integer=False, label="Creatinine clearance"),
        on_dialysis=_bool(form, "on_dialysis"),
        child_pugh=_enum(form, "child_pugh", ChildPugh, ChildPugh.NONE, errors),
        hbsag=_enum(form, "hbsag", LabResult, LabResult.UNKNOWN, errors),
        hla_b5701=_enum(form, "hla_b5701", LabResult, LabResult.UNKNOWN, errors),
        hcv=_bool(form, "hcv"),
        anti_hbc=_enum(form, "anti_hbc", LabResult, LabResult.UNKNOWN, errors),
        anti_hbs=_enum(form, "anti_hbs", LabResult, LabResult.UNKNOWN, errors),
        hbv_dna=_number(form, "hbv_dna", errors, 0, 1e10, integer=False, label="HBV DNA"),
        crag=_enum(form, "crag", LabResult, LabResult.UNKNOWN, errors),
        tb_start=str(form.get("tb_start") or "").strip()[:10],
        genotype_available=genotype,
        rt_mutations=(form.get("rt_mutations") or "").strip()[:500] if genotype else "",
        pr_mutations=(form.get("pr_mutations") or "").strip()[:500] if genotype else "",
        in_mutations=(form.get("in_mutations") or "").strip()[:500] if genotype else "",
        genotypes=tuple(genotypes) if genotype else (),
        use_hivdb=_bool(form, "use_hivdb"),
        minority_threshold=threshold or 20.0,
        subtype=subtype,
        tropism=tropism,
        comorbidities=_subset(_getlist(form, "comorbidities"), COMORBIDITIES, "comorbidities", errors),
        comedications=_subset(_getlist(form, "comedications"), COMEDICATIONS_BY_KEY, "comedications", errors),
        medicines_text=str(form.get("medicines_text") or "")[:4000],
        creatinine_umol=_number(form, "creatinine_umol", errors, 10, 2000, integer=False, label="Creatinine"),
        cystatin_c=_number(form, "cystatin_c", errors, 0.2, 10, integer=False, label="Cystatin C"),
        height_cm=_number(form, "height_cm", errors, 100, 250, integer=False, label="Height"),
        bilirubin_umol=_number(form, "bilirubin_umol", errors, 1, 1000, integer=False, label="Bilirubin"),
        albumin_g_l=_number(form, "albumin_g_l", errors, 5, 70, integer=False, label="Albumin"),
        inr=_number(form, "inr", errors, 0.5, 10, integer=False, label="INR"),
        ascites=_choice(form, "ascites", ("", "none", "mild", "severe"), errors),
        encephalopathy=_choice(form, "encephalopathy", ("", "none", "mild", "severe"), errors),
        qrisk3=_number(form, "qrisk3", errors, 0, 100, integer=False, label="QRISK3"),
        frax_mof=_number(form, "frax_mof", errors, 0, 100, integer=False, label="FRAX major osteoporotic"),
        frax_hip=_number(form, "frax_hip", errors, 0, 100, integer=False, label="FRAX hip"),
        vl_history=_lab_series(form, "vl_history", errors, "Viral load history"),
        cd4_history=_lab_series(form, "cd4_history", errors, "CD4 history"),
        art_history=_art_history(form, errors),
        prefers_single_tablet=_bool(form, "prefers_single_tablet"),
        prefers_long_acting=_bool(form, "prefers_long_acting"),
        adherence_concerns=_bool(form, "adherence_concerns"),
        food_insecurity=_bool(form, "food_insecurity"),
    )
    if errors:
        return None, errors
    return PatientProfile(**profile_kwargs), errors
