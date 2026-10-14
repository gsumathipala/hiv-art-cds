"""JSON API: the same engine for integration with other systems."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..engine.recommender import recommend
from ..knowledge import smpc
from ..knowledge.products import PRODUCTS
from .forms import parse_patient

bp = Blueprint("api", __name__)


@bp.post("/assess")
def assess():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send a JSON object describing the patient."), 400
    patient, errors = parse_patient(payload)
    if errors:
        return jsonify(errors=errors), 422
    return jsonify(recommend(patient).to_dict())


@bp.get("/products")
def products():
    out = []
    for p in PRODUCTS:
        doc = smpc.load(p.key)
        out.append({
            "key": p.key, "brand": p.brand, "ingredients": list(p.ingredients),
            "smpc_name": doc["name"] if doc else None, "smpc_url": doc["url"] if doc else None,
            "smpc_revision": doc["revision"] if doc else None,
        })
    return jsonify(out)
