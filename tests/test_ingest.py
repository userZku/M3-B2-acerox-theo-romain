"""
Tests pour l'ingestion des mesures IoT.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from src.ingest_iot import ingest_mesures_iot

normale_path = "tests/fixtures/test_ingestion_normale.csv"
malformee_path = "tests/fixtures/test_ingestion_malformee.csv"

def test_ingestion_normale(tmp_session, monkeypatch):
    # prépare une mini-fixture (quelques lignes, dont 1 doublon sur la clé)
    # puis redirige chemin source + get_session vers la BDD éphémère :
    monkeypatch.setattr("src.ingest_iot.CAPTEURS_IOT_CSV", normale_path)
    monkeypatch.setattr("src.ingest_iot.get_session", lambda: tmp_session)
    assert ingest_mesures_iot() == 7        # 7 lignes insérées (1 doublon ignoré), cf test_mini.csv
    assert ingest_mesures_iot() == 0        # idempotence


def test_ingestion_invalide(tmp_session, monkeypatch, tmp_path):
    monkeypatch.setattr("src.ingest_iot.CAPTEURS_IOT_CSV", tmp_path / "absent.csv")
    monkeypatch.setattr("src.ingest_iot.get_session", lambda: tmp_session)
    with pytest.raises(FileNotFoundError):
        ingest_mesures_iot()


def test_ingestion_malformee(tmp_session, monkeypatch):
    # prépare une mini-fixture (quelques lignes, dont 1 doublon sur la clé)
    # puis redirige chemin source + get_session vers la BDD éphémère :
    monkeypatch.setattr("src.ingest_iot.CAPTEURS_IOT_CSV", malformee_path)
    monkeypatch.setattr("src.ingest_iot.get_session", lambda: tmp_session)
    with pytest.raises(IntegrityError):
        ingest_mesures_iot()