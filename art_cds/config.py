from __future__ import annotations

import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("ART_CDS_SECRET_KEY", "dev-only-not-secret")
    # "education" (default) or "clinical" — see docs/clinical-safety before changing
    MODE = os.environ.get("ART_CDS_MODE", "education")
    AUDIT = os.environ.get("ART_CDS_AUDIT", "1") == "1"
    AUDIT_DIR = os.environ.get("ART_CDS_AUDIT_DIR",
                               str(Path(__file__).resolve().parent.parent / "instance" / "audit"))
    AUDIT_STORE_INPUTS = os.environ.get("ART_CDS_AUDIT_INPUTS", "0") == "1"
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # forms with sequences, FHIR bundles
    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
    AUDIT = False
