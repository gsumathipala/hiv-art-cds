from __future__ import annotations

import os


class Config:
    SECRET_KEY = os.environ.get("ART_CDS_SECRET_KEY", "dev-only-not-secret")
    MAX_CONTENT_LENGTH = 64 * 1024  # form posts only; no uploads
    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
