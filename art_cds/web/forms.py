"""Turn submitted form data (or JSON) into a validated PatientProfile."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from ..knowledge.conditions import COMORBIDITIES
from ..knowledge.interactions import COMEDICATIONS_BY_KEY
from ..models.patient import (
    ARV_CLASSES, ChildPugh, LabResult, PatientProfile, Pregnancy, TreatmentStatus,
)

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


def _subset(values: Iterable[str], allowed: Iterable[str], name: str, errors: Errors) -> frozenset:
    allowed = set(allowed)
    bad = [v for v in values if v not in allowed]
    if bad:
        errors[name] = f"Unknown option(s): {', '.join(bad)}"
    return frozenset(v for v in values if v in allowed)


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

    genotype = form.get("genotype") == "available" or _bool(form, "genotype_available")
    profile_kwargs = dict(
        age=age or 0,
        sex=sex,
        weight_kg=weight,
        pregnancy=pregnancy,
        breastfeeding=_bool(form, "breastfeeding") and sex == "female",
        status=status,
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
        genotype_available=genotype,
        rt_mutations=(form.get("rt_mutations") or "").strip()[:500] if genotype else "",
        pr_mutations=(form.get("pr_mutations") or "").strip()[:500] if genotype else "",
        in_mutations=(form.get("in_mutations") or "").strip()[:500] if genotype else "",
        comorbidities=_subset(_getlist(form, "comorbidities"), COMORBIDITIES, "comorbidities", errors),
        comedications=_subset(_getlist(form, "comedications"), COMEDICATIONS_BY_KEY, "comedications", errors),
        prefers_single_tablet=_bool(form, "prefers_single_tablet"),
        prefers_long_acting=_bool(form, "prefers_long_acting"),
        adherence_concerns=_bool(form, "adherence_concerns"),
        food_insecurity=_bool(form, "food_insecurity"),
    )
    if errors:
        return None, errors
    return PatientProfile(**profile_kwargs), errors
