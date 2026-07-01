"""Pipeline ingest IOT : ingestion des mesures depuis le CSV vers la table `mesures_iot`.
Idempotent : si une mesure avec le même `timestamp` et `sensor_id` existe déjà, elle n'est pas réinsérée.
Retourne le nombre de mesures effectivement insérées.

Usage::

    python -m src.pipeline_existante
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.db import get_session
from src.models import MesuresIoT

CAPTEURS_IOT_CSV: Path = Path(__file__).parent.parent / "data" / "capteurs_iot.csv"


def ingest_mesures_iot() -> int:
    """Charge les mesures IoT depuis le CSV vers la table `mesures_iot`.

    Idempotent : si une mesure avec le même `timestamp` et `sensor_id` existe déjà, elle n'est pas réinsérée.
    Retourne le nombre de mesures effectivement insérées.
    """
    # Lecture brute du CSV source (même logique que la pipeline produits).
    df = pd.read_csv(CAPTEURS_IOT_CSV)
    # Conversion explicite vers datetime Python-compatible pour SQLite/SQLAlchemy.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    # Déduplication pandas en amont sur la clé métier du contrat IoT.
    df = df.drop_duplicates(subset=["timestamp", "sensor_id"], keep="first")
    session = get_session()
    inserted = 0
    try:
        # Snapshot des clés déjà en base pour garantir l'idempotence.
        existing_measurements = {
            (m.timestamp, m.sensor_id) for m in session.query(MesuresIoT.timestamp, MesuresIoT.sensor_id).all()
        }
        for _, row in df.iterrows():
            timestamp = row["timestamp"].to_pydatetime()
            key = (timestamp, row["sensor_id"])
            # On ignore toute ligne déjà présente (même timestamp + sensor_id).
            if key in existing_measurements:
                continue
            # Traiter en aval la ligne 3 du site Roubaix pour prendre en compte les données température et débit mais pas la vibration qu'on passe à null (car autorisé)
            if row["site"] == "Roubaix" and row["line_id"] == 3:
                row["vibration_mms"] = None
            # Mapping explicite CSV -> modèle SQLAlchemy avant insertion.
            session.add(
                MesuresIoT(
                    timestamp=timestamp,
                    sensor_id=row["sensor_id"],
                    site=row["site"],
                    line_id=row["line_id"],
                    temperature_c=row["temperature_c"],
                    vibration_mms=row["vibration_mms"],
                    debit_uh=row["debit_uh"],
                )
            )
            # Important: couvre aussi les doublons présents dans le même fichier CSV.
            existing_measurements.add(key)
            inserted += 1
        # Commit unique en fin de boucle pour valider le lot inséré.
        session.commit()
    finally:
        session.close()
    return inserted
