"""Tests pour l'ingestion des ordres ERP."""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import select

from src.ingest_erp import ingest_erp
from src.models import OrdresErp, Produit

NORMALE_PATH = "tests/fixtures/test_ingestion_erp_normale.json"
MALFORMEE_PATH = "tests/fixtures/test_ingestion_erp_malformee.json"


def _seed_produits(tmp_session) -> None:
    tmp_session.add_all(
        [
            Produit(produit_ref="ALU-001", nom="Alu test", categorie="aluminium", unite="kg"),
            Produit(produit_ref="INOX-001", nom="Inox test", categorie="inox", unite="kg"),
        ]
    )
    tmp_session.commit()


def test_ingestion_erp_normale_et_idempotente(tmp_session, monkeypatch):
    _seed_produits(tmp_session)
    monkeypatch.setenv("ACEROX_ERP_SALT", "test-salt")
    monkeypatch.setattr("src.ingest_erp.ERP_JSON", NORMALE_PATH)
    monkeypatch.setattr("src.ingest_erp.get_session", lambda: tmp_session)

    assert ingest_erp() == 3
    assert ingest_erp() == 0

    rows = tmp_session.execute(select(OrdresErp).order_by(OrdresErp.ordre_id)).scalars().all()
    assert len(rows) == 3
    assert rows[0].ouvrier_hash != "OP-001"
    assert rows[0].ouvrier_hash == hashlib.sha256("test-salt:OP-001".encode("utf-8")).hexdigest()


def test_ingestion_erp_fichier_absent(tmp_session, monkeypatch, tmp_path):
    _seed_produits(tmp_session)
    monkeypatch.setattr("src.ingest_erp.ERP_JSON", tmp_path / "absent.json")
    monkeypatch.setattr("src.ingest_erp.get_session", lambda: tmp_session)

    with pytest.raises(FileNotFoundError):
        ingest_erp()


def test_ingestion_erp_malformee(tmp_session, monkeypatch):
    _seed_produits(tmp_session)
    monkeypatch.setattr("src.ingest_erp.ERP_JSON", MALFORMEE_PATH)
    monkeypatch.setattr("src.ingest_erp.get_session", lambda: tmp_session)

    with pytest.raises(ValueError, match="Colonnes ERP manquantes"):
        ingest_erp()
