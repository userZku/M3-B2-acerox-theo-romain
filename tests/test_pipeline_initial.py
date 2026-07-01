"""Tests de la pipeline existante — DOIVENT rester verts après vos ajouts.

C'est un test de **non-régression** : si vous cassez la pipeline initiale
en ajoutant votre nouvelle source, ces tests sautent et vous le saurez tout
de suite.
"""
from __future__ import annotations

from sqlalchemy import select

from src.models import Produit


def test_produits_table_exists(tmp_engine):
    """La table produits existe après création du schéma."""
    inspector_tables = list(tmp_engine.dialect.get_table_names(tmp_engine.connect()))
    assert "produits" in inspector_tables


def test_produits_schema_attendu(tmp_session):
    """Les colonnes attendues de produits sont présentes."""
    # Insertion test
    p = Produit(produit_ref="TEST-01", nom="Test", categorie="aluminium", unite="kg")
    tmp_session.add(p)
    tmp_session.commit()

    # Lecture
    result = tmp_session.execute(select(Produit).where(Produit.produit_ref == "TEST-01")).scalar_one()
    assert result.nom == "Test"
    assert result.categorie == "aluminium"
    assert result.unite == "kg"
