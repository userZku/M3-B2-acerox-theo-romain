"""Configuration BDD partagée (engine + session).

Utilisé par `pipeline_existante.py`, `ingest_*.py`, et les tests.
SQLite local (`data/acerox.db`), DSN configurable par variable d'env.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DB_PATH: Path = Path(__file__).parent.parent / "data" / "acerox.db"
DB_URL: str = os.environ.get("ACEROX_DB_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_session() -> Session:
    """Retourne une session SQLAlchemy (à fermer après usage)."""
    return SessionLocal()
