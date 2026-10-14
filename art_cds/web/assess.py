"""The decision-support pages: patient form and recommendation report."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, request
from werkzeug.datastructures import MultiDict

from .. import __version__, governance
from ..engine.recommender import recommend
from ..knowledge.cases import CASES, CASES_BY_KEY
from ..knowledge.conditions import COMORBIDITIES
from ..knowledge.interactions import COMEDICATIONS
from ..knowledge.regimens import REGIMENS
from ..models.patient import ARV_CLASSES, STOP_REASONS
from ..visuals import timeline
from .forms import SUBTYPES, TROPISMS, VIRUS_TYPES, parse_patient

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
        "virus_types": VIRUS_TYPES,
        "regimens": REGIMENS,
        "stop_reasons": STOP_REASONS,
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
    audit_ref = _audit(report)
    case = CASES_BY_KEY.get(request.form.get("case_key", ""))
    p = report.patient
    chart = timeline.render(p.vl_history, p.cd4_history, p.art_history,
                            report.virology.labels if report.virology else ())
    return render_template("assess/report.html", report=report, values=request.form, case=case, timeline=chart,
                           audit_ref=audit_ref, comed_labels={c.key: c.label for c in COMEDICATIONS})


def _audit(report):
    cfg = current_app.config
    if not cfg.get("AUDIT"):
        return None
    return governance.audit(report, cfg.get("MODE", "education"), __version__, Path(cfg["AUDIT_DIR"]),
                            cfg.get("AUDIT_STORE_INPUTS", False))
