"""HIV antiretroviral therapy decision support and teaching tool (UK).

Regimen tiers follow BHIVA guidance; every product fact comes from the UK
Summary of Product Characteristics on emc.
"""
from __future__ import annotations

from typing import Optional

from flask import Flask

from .config import Config

__version__ = "1.0.0"


def create_app(config: Optional[type] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or Config)

    from .web import register

    register(app)
    return app
