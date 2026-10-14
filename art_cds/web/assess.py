"""The decision-support pages: patient form and recommendation report."""
from __future__ import annotations

from flask import Blueprint, abort, render_template, request
from werkzeug.datastructures import MultiDict

from ..engine.recommender import recommend
from ..knowledge.cases import CASES, CASES_BY_KEY
from ..knowledge.conditions import COMORBIDITIES
from ..knowledge.interactions import COMEDICATIONS
from ..models.patient import ARV_CLASSES
from .forms import SUBTYPES, TROPISMS, parse_patient

bp = Blueprint("assess", __name__)


def _form_context(values: MultiDict, errors=None):
    groups = {}
    for c in COMEDICATIONS:
        groups.setdefault(c.group, []).append(c)
    return {
        "values": values,
        "errors": errors or {},
        "comorbidities": COMORBIDITIES,
        "comedication_groups": groups,
        "arv_classes": ARV_CLASSES,
        "cases": CASES,
        "subtypes": SUBTYPES,
        "tropisms": TROPISMS,
    }


@bp.get("/")
def index():
    return render_template("home.html", cases=CASES)


@bp.get("/assess")
def form():
    values = MultiDict()
    case_key = request.args.get("case")
    if case_key:
        case = CASES_BY_KEY.get(case_key) or abort(404)
        values = case.as_multidict()
    return render_template("assess/form.html", **_form_context(values))


@bp.post("/assess")
def submit():
    patient, errors = parse_patient(request.form)
    if errors:
        return render_template("assess/form.html", **_form_context(request.form, errors)), 422
    report = recommend(patient)
    case = CASES_BY_KEY.get(request.form.get("case_key", ""))
    return render_template("assess/report.html", report=report, values=request.form, case=case)
