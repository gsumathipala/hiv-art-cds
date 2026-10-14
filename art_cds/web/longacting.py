"""Long-acting injectable planner."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, render_template, request

from .. import longacting as la

bp = Blueprint("longacting", __name__)


def _date(name):
    try:
        return date.fromisoformat(request.args.get(name, ""))
    except ValueError:
        return None


def _plan():
    a = request.args
    drug = a.get("drug", "cab_rpv")
    start = _date("start")
    if not start:
        return drug, None
    if drug == "len":
        return drug, la.lenacapavir_schedule(start, int(a.get("visits", 4)))
    return drug, la.cab_rpv_schedule(start, a.get("interval", "q2m") == "q2m", a.get("lead_in") == "on",
                                     int(a.get("visits", 8)))


@bp.get("/")
def index():
    a = request.args
    drug, visits = _plan()
    missed = bridge = risk = None
    last, on = _date("last"), _date("on") or date.today()
    if last and drug == "cab_rpv":
        q2m = a.get("interval", "q2m") == "q2m"
        missed = la.missed_injection(last, on, q2m, int(a.get("missed_visit", 3)))
        bridge = la.oral_bridge(last, q2m)
    if a.get("risk") == "on":
        bmi = None
        try:
            bmi = float(a["weight"]) / (float(a["height"]) / 100) ** 2
        except (KeyError, ValueError, ZeroDivisionError):
            pass
        risk = la.failure_risk([m.strip().upper() for m in a.get("rt", "").replace(",", " ").split()],
                               a.get("subtype", ""), bmi)
    return render_template("longacting/index.html", a=a, drug=drug, visits=visits, missed=missed, bridge=bridge,
                           risk=risk, la=la, today=date.today())


@bp.get("/schedule.ics")
def calendar():
    drug, visits = _plan()
    if not visits:
        return Response("Choose a start date first.", status=400)
    title = "Lenacapavir" if drug == "len" else "Cabotegravir + rilpivirine"
    return Response(la.ics(visits, title), mimetype="text/calendar",
                    headers={"Content-Disposition": 'attachment; filename="long-acting-schedule.ics"'})
