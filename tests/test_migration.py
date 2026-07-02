"""
Tests pour la migration des mesures IoT.
"""

from __future__ import annotations

from sqlalchemy import inspect


def test_mesures_iot_existe(tmp_engine):
    tables = inspect(tmp_engine).get_table_names()
    assert "mesures_iot" in tables
    assert "produits" in tables 


def test_ordres_erp_schema(tmp_engine):
    tables = inspect(tmp_engine).get_table_names()
    assert "ordres_erp" in tables