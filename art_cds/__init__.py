"""ART Navigator UK — HIV antiretroviral decision support and teaching tool.

Created by Saranga Sumathipala.

Regimen tiers follow BHIVA guidance; every product fact comes from the UK
Summary of Product Characteristics on emc. Every such statement is verified
against its source text — see tools/verify_smpc.py.
"""
from __future__ import annotations

from typing import Optional

from flask import Flask

from .config import Config

__author__ = "Saranga Sumathipala"
__version__ = "2.0.0"


def create_app(config: Optional[type] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or Config)

    from .web import register

    register(app)
    return app
