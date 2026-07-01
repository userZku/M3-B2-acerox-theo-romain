"""Fixtures pytest partagées — BDD éphémère SQLite par test.

Le binôme étend ce module si besoin pour les tests d'ingestion.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base


@pytest.fixture
def tmp_db_url() -> str:
    """Crée une BDD SQLite temporaire et retourne son URL."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield f"sqlite:///{path}"
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def tmp_engine(tmp_db_url):
    """Engine SQLAlchemy sur la BDD temporaire, schéma créé."""
    engine = create_engine(tmp_db_url, future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def tmp_session(tmp_engine):
    """Session SQLAlchemy à utiliser dans les tests d'ingestion."""
    Session = sessionmaker(bind=tmp_engine, autoflush=False)
    session = Session()
    yield session
    session.close()
