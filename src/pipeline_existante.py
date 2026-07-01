"""Pipeline Acerox existante — référentiel produits.

Le binôme **ne doit pas modifier** ce fichier. Il sert de référence :
la pipeline doit continuer de fonctionner après vos ajouts.

Usage::

    python -m src.pipeline_existante
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.db import engine, get_session
from src.models import Base, Produit, MesuresIoT

PRODUITS_CSV: Path = Path(__file__).parent.parent / "data" / "produits.csv"


def init_db() -> None:
    """Crée toutes les tables déclarées dans `models.Base.metadata`.

    En prod, c'est Alembic qui gère ça. Ici, init brutal pour bootstrap.
    """
    Base.metadata.create_all(engine)


def ingest_produits() -> int:
    """Charge le référentiel produits depuis le CSV vers la table `produits`.

    Idempotent : si un `produit_ref` existe déjà, il n'est pas réinséré.
    Retourne le nombre de produits effectivement insérés.
    """
    df = pd.read_csv(PRODUITS_CSV)
    session = get_session()
    inserted = 0
    try:
        existing_refs = {p.produit_ref for p in session.query(Produit.produit_ref).all()}
        for _, row in df.iterrows():
            if row["produit_ref"] in existing_refs:
                continue
            session.add(
                Produit(
                    produit_ref=row["produit_ref"],
                    nom=row["nom"],
                    categorie=row["categorie"],
                    unite=row["unite"],
                )
            )
            inserted += 1
        session.commit()
    finally:
        session.close()
    return inserted

def ingest_mesures_iot() -> int:
    """Charge les mesures IoT depuis le CSV vers la table `mesures_iot`.

    Idempotent : si une mesure avec le même `timestamp` et `sensor_id` existe déjà, elle n'est pas réinsérée.
    Retourne le nombre de mesures effectivement insérées.
    """
    # Lecture brute du CSV source (même logique que la pipeline produits).
    df = pd.read_csv(Path(__file__).parent.parent / "data" / "capteurs_iot.csv")
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

def main() -> None:
    """Init BDD + chargement référentiel produits."""
    init_db()
    n = ingest_produits()
    print(f"Pipeline existante : {n} produit(s) inséré(s) (idempotent — relancer ne duplique pas).")
    m = ingest_mesures_iot()
    print(f"Pipeline existante : {m} mesure(s) IoT insérée(s) (idempotent — relancer ne duplique pas).")


if __name__ == "__main__":
    main()
