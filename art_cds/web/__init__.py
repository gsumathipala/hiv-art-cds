"""Web layer: blueprints for the decision tool, the teaching pages and the API."""
from __future__ import annotations

from flask import Flask

from .. import __version__
from ..knowledge import smpc
from ..knowledge.drugs import CLASSES, DRUGS
from ..knowledge.guidelines import TIER_LABEL
from ..knowledge.products import PRODUCTS_BY_KEY
from ..visuals import pills


def register(app: Flask) -> None:
    from .api import bp as api_bp
    from .assess import bp as assess_bp
    from .learn import bp as learn_bp

    app.register_blueprint(assess_bp)
    app.register_blueprint(learn_bp, url_prefix="/learn")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def globals_():
        return {
            "app_version": __version__,
            "DRUGS": DRUGS,
            "CLASSES": CLASSES,
            "PRODUCTS": PRODUCTS_BY_KEY,
            "TIER_LABEL": TIER_LABEL,
            "smpc_doc": smpc.load,
            "pill_units": pills.units_for,
            "pill_svg": pills.svg_for,
            "pill_photo": pills.photo_for,
            "smpc_mechanism": smpc.mechanism_sentence,
            "smpc_appearance": smpc.appearance_text,
        }
