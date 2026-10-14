"""The decision-support pages: patient form and recommendation report."""
from __future__ import annotations

from pathlib import Path

import json
from datetime import date

from flask import Blueprint, abort, current_app, render_template, request
from werkzeug.datastructures import MultiDict

from .. import __version__, governance
from ..engine.recommender import recommend
from ..knowledge.cases import CASES, CASES_BY_KEY
from .. import fhir
from ..knowledge import smpc
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


def _build(form):
    patient, errors = parse_patient(form)
    if errors:
        return None, None, errors
    report = recommend(patient)
    return report, _audit(report), None


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


@bp.post("/assess/letter")
def letter():
    report, audit_ref, errors = _build(request.form)
    if errors:
        return render_template("assess/form.html", **_form_context(request.form, errors)), 422
    return render_template("outputs/letter.html", report=report, audit_ref=audit_ref,
                           today=date.today().strftime("%d %B %Y"))


@bp.post("/assess/leaflet")
def leaflet():
    report, _, errors = _build(request.form)
    if errors:
        return render_template("assess/form.html", **_form_context(request.form, errors)), 422
    side_effects = []
    if report.top:
        merged = {}
        for key in report.top.regimen.products:
            for freqs in smpc.adverse_grid(key).values():
                for freq, items in freqs.items():
                    if freq in ("very common", "common"):
                        merged.setdefault(freq, [])
                        merged[freq] += [i.lower() for i in items if i.lower() not in merged[freq]]
        side_effects = [(f, sorted(merged[f])[:14]) for f in ("very common", "common") if merged.get(f)]
    return render_template("outputs/leaflet.html", report=report, side_effects=side_effects)


@bp.post("/assess/import")
def import_fhir():
    """Read a FHIR Bundle and pre-fill the assessment form."""
    upload = request.files.get("bundle")
    raw = upload.read().decode("utf-8", "replace") if upload else (request.form.get("bundle_text") or "")
    try:
        fields, notes = fhir.parse_bundle(json.loads(raw))
    except (ValueError, json.JSONDecodeError) as exc:
        return render_template("assess/form.html", **_form_context(request.form, {"bundle": f"Could not read the "
                                                                                 f"bundle: {exc}"})), 422
    values = MultiDict()
    for key, value in fields.items():
        for item in (value if isinstance(value, list) else [value]):
            values.add(key, str(item))
    return render_template("assess/form.html", **_form_context(values), import_notes=notes)
