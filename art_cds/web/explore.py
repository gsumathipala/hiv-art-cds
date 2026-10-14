"""Interactive teaching visuals: resistance builder and pharmacokinetic curves."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from ..engine.resistance import interpret_history
from ..knowledge import resistance as rkb
from ..models import GenotypeTest
from ..visuals import pharmacokinetics as pk

bp = Blueprint("explore", __name__)

BUILDER_DRUGS = ("TDF", "TAF", "ABC", "3TC", "FTC", "AZT", "EFV", "RPV", "DOR", "ETR", "DTG", "BIC", "CAB", "RAL",
                 "DRV", "ATV")


@bp.get("/resistance")
def resistance():
    chosen = {g: request.args.get(g.lower(), "") for g in ("RT", "PR", "IN")}
    report = interpret_history([GenotypeTest(rt=chosen["RT"], pr=chosen["PR"], integrase=chosen["IN"])])
    common = {gene: [m for m, scores in rkb.SCORES[gene].items() if max(scores.values()) >= 30][:26]
              for gene in ("RT", "PR", "IN")}
    return render_template("explore/resistance.html", chosen=chosen, report=report, common=common,
                           drugs=BUILDER_DRUGS, notes=rkb.NOTES)


@bp.get("/pharmacokinetics")
def pharmacokinetics():
    code = request.args.get("drug", "DTG")
    if code not in pk.PROFILES_BY_CODE:
        code = "DTG"
    stop = request.args.get("stop") == "on"
    profile = pk.PROFILES_BY_CODE[code]
    svg = pk.curve(code, doses_count=8 if not profile.injectable else 4, stop_after=2 if stop else None)
    return render_template("explore/pharmacokinetics.html", profiles=pk.PROFILES, profile=profile, svg=svg,
                           stop=stop, explainer=pk.BOOSTER_EXPLAINER)
