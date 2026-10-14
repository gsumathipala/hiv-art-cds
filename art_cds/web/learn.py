"""Teaching pages: classes, drug monographs, products (SmPC), interactions, resistance."""
from __future__ import annotations

from flask import Blueprint, abort, render_template

from ..knowledge import smpc
from ..knowledge import resistance as rkb
from ..knowledge.cases import CASES
from ..knowledge.drugs import CLASSES, DRUGS
from ..knowledge.guidelines import SCENARIOS, TIER_LABELS, TIERS
from ..knowledge.interactions import COMEDICATIONS, INTERACTIONS, SEVERITY_ORDER, for_drug
from ..knowledge.products import PRODUCTS, PRODUCTS_BY_KEY, products_containing
from ..knowledge.regimens import REGIMENS

bp = Blueprint("learn", __name__)

MATRIX_DRUGS = ("BIC", "DTG", "RAL", "CAB", "DOR", "RPV", "EFV", "DRV", "ATV", "RTV", "COBI", "TAF", "TDF")


@bp.get("/")
def hub():
    by_class = {}
    for d in DRUGS.values():
        by_class.setdefault(d.drug_class, []).append(d)
    return render_template("learn/hub.html", by_class=by_class)


@bp.get("/class/<code>")
def drug_class(code):
    klass = CLASSES.get(code) or abort(404)
    drugs = [d for d in DRUGS.values() if d.drug_class == code]
    return render_template("learn/class.html", klass=klass, drugs=drugs)


@bp.get("/drug/<code>")
def drug(code):
    d = DRUGS.get(code) or abort(404)
    key = d.monograph
    return render_template(
        "learn/drug.html", drug=d, key=key, doc=smpc.load(key), grid=smpc.adverse_grid(key),
        counts=smpc.frequency_counts(key), products=products_containing(code), pk=smpc.pk_facts(key),
        interactions=for_drug(code), comeds={c.key: c for c in COMEDICATIONS},
        mutations=_mutations_for(code),
    )


@bp.get("/product/<key>")
def product(key):
    p = PRODUCTS_BY_KEY.get(key) or abort(404)
    doc = smpc.load(key)
    return render_template("learn/product.html", product=p, doc=doc, grid=smpc.adverse_grid(key),
                           counts=smpc.frequency_counts(key), order=smpc.SECTION_ORDER)


@bp.get("/formulary")
def formulary():
    return render_template("learn/formulary.html", products=PRODUCTS)


@bp.get("/regimens")
def regimens():
    return render_template("learn/regimens.html", regimens=REGIMENS, tiers=TIERS, scenarios=SCENARIOS,
                           tier_labels=TIER_LABELS)


@bp.get("/interactions")
def interactions():
    cells = {(i.comed, i.drug): i for i in INTERACTIONS}
    return render_template("learn/interactions.html", comeds=COMEDICATIONS, drugs=MATRIX_DRUGS, cells=cells,
                           interactions=sorted(INTERACTIONS, key=lambda i: (i.comed, SEVERITY_ORDER[i.severity])))


@bp.get("/resistance")
def resistance():
    genes = {
        "RT": ("Reverse transcriptase", rkb.NRTI_DRUGS + rkb.NNRTI_DRUGS),
        "IN": ("Integrase", rkb.INSTI_DRUGS),
        "PR": ("Protease", rkb.PI_DRUGS),
    }
    return render_template("learn/resistance.html", genes=genes, scores=rkb.SCORES, notes=rkb.NOTES,
                           levels=rkb.LEVELS, combos=rkb.COMBINATIONS)


@bp.get("/cases")
def cases():
    return render_template("learn/cases.html", cases=CASES)


@bp.get("/about")
def about():
    docs = [(p, smpc.load(p.key)) for p in PRODUCTS]
    return render_template("learn/about.html", docs=docs)


def _mutations_for(code):
    scored = rkb.SCORED_AS.get(code, code)
    out = []
    for gene, muts in rkb.SCORES.items():
        for m, s in muts.items():
            if s.get(scored, 0) >= 15:
                out.append((gene, m, s[scored], rkb.level_for(s[scored])))
    return sorted(out, key=lambda x: -x[2])
