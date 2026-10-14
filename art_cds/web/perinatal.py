"""Infant post-natal prophylaxis and intrapartum planner."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from .. import perinatal

bp = Blueprint("perinatal", __name__)


@bp.get("/")
def index():
    a = request.args
    plan = iv = None
    if a.get("go"):
        def num(name):
            try:
                return float(a.get(name, ""))
            except ValueError:
                return None

        plan = perinatal.infant_pnp(
            art_started_weeks_before_delivery=num("art_weeks"),
            good_engagement=a.get("engagement") == "on",
            vl_in_last_6_weeks=a.get("vl_6_weeks") == "on",
            all_vl_under_50_in_last_10_weeks=a.get("vl_10_weeks") == "on",
            delivery_vl=num("delivery_vl"),
            breastfeeding=a.get("breastfeeding") == "on",
            maternal_nnrti_resistance=a.get("nnrti_resistance") == "on")
        iv = perinatal.intrapartum_zidovudine(num("delivery_vl"), a.get("untreated") == "on")
    return render_template("perinatal/index.html", a=a, plan=plan, iv=iv, p=perinatal)
