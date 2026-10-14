"""Stand-alone calculators page: kidney function, Child-Pugh, QRISK3, FRAX link."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from .. import calculators as calc

bp = Blueprint("calculators", __name__)


def _f(name):
    try:
        v = request.args.get(name, "").strip()
        return float(v) if v else None
    except ValueError:
        return None


@bp.get("/")
def index():
    a = request.args
    kidney = qrisk = cp = None
    errors = []
    female = a.get("sex") == "female"
    age = _f("age")
    if a.get("calc") == "kidney" and age:
        kidney = calc.kidney(int(age), female, _f("weight"), _f("creatinine"), _f("cystatin"))
    if a.get("calc") == "childpugh":
        vals = (_f("bilirubin"), _f("albumin"), _f("inr"))
        if None in vals or not a.get("ascites") or not a.get("encephalopathy"):
            errors.append("Child-Pugh needs bilirubin, albumin, INR, ascites and encephalopathy.")
        else:
            cp = calc.child_pugh(*vals, a["ascites"], a["encephalopathy"])
    if a.get("calc") == "qrisk3":
        try:
            qrisk = calc.qrisk3(calc.QriskInputs(
                age=int(age or 0), female=female, ethnicity=int(a.get("ethnicity", 1)), smoking=int(a.get("smoking", 0)),
                height_cm=_f("height") or 0, weight_kg=_f("weight") or 0, chol_hdl_ratio=_f("ratio") or 0,
                sbp=_f("sbp") or 0, sbp_sd=_f("sbp_sd") or 0, townsend=_f("townsend") or 0,
                **{k: a.get(k) == "on" for k in (
                    "af", "atypical_antipsychotic", "corticosteroids", "erectile_dysfunction", "migraine",
                    "rheumatoid_arthritis", "ckd_3_5", "severe_mental_illness", "sle", "treated_hypertension",
                    "type1_diabetes", "type2_diabetes", "family_history_chd")}))
        except (ValueError, ZeroDivisionError) as exc:
            errors.append(f"QRISK3: {exc if str(exc) else 'height, weight, cholesterol ratio and SBP are required.'}")
    return render_template("calculators/index.html", a=a, kidney=kidney, qrisk=qrisk, cp=cp, errors=errors,
                           calc=calc)
