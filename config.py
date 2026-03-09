from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / "instance" / "hazard_source_system.db"
DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    # Use local SQLite as the safe default to avoid MySQL auth errors on first run.
    # Production should override DATABASE_URL via environment variables.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
