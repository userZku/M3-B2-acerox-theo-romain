"""Pipeline ingest ERP : ingestion des ordres depuis le JSON vers `ordres_erp`.

Idempotent : si un `ordre_id` existe déjà, il n'est pas réinséré.
RGPD : `ouvrier_id` n'est jamais stocké en clair (hash SHA-256 salé).
Retourne le nombre d'ordres effectivement insérés.

Usage::

    python -m src.ingest_erp
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import MetaData, Table, select
from sqlalchemy.exc import NoSuchTableError

from src.db import get_session

ERP_JSON: Path = Path(__file__).parent.parent / "data" / "erp_export.json"
REQUIRED_COLUMNS = {
    "ordre_id",
    "produit_ref",
    "site",
    "line_id",
    "date_lancement",
    "date_fin_prevue",
    "statut",
    "ouvrier_id",
    "quantite_kg",
}


def _hash_ouvrier_id(raw_value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{raw_value}".encode("utf-8")).hexdigest()


def _load_ordres_table(session) -> Table:
    bind = session.get_bind()
    if bind is None:
        raise RuntimeError("Session SQLAlchemy non liée à un engine.")
    metadata = MetaData()
    try:
        return Table("ordres_erp", metadata, autoload_with=bind)
    except NoSuchTableError as exc:
        raise RuntimeError(
            "Table 'ordres_erp' introuvable. Lancez d'abord les migrations Alembic (ex: alembic upgrade head)."
        ) from exc


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Colonnes ERP manquantes: {missing_str}")

    df = df.copy()
    df["date_lancement"] = pd.to_datetime(df["date_lancement"], errors="coerce")
    df["date_fin_prevue"] = pd.to_datetime(df["date_fin_prevue"], errors="coerce")
    df["ordre_id"] = pd.to_numeric(df["ordre_id"], errors="coerce")
    df["line_id"] = pd.to_numeric(df["line_id"], errors="coerce")
    df["quantite_kg"] = pd.to_numeric(df["quantite_kg"], errors="coerce")

    # Drop explicite des lignes invalides sur les champs obligatoires du contrat.
    df = df.dropna(
        subset=[
            "ordre_id",
            "produit_ref",
            "site",
            "line_id",
            "date_lancement",
            "date_fin_prevue",
            "statut",
            "ouvrier_id",
            "quantite_kg",
        ]
    )

    df["ordre_id"] = df["ordre_id"].astype(int)
    df["line_id"] = df["line_id"].astype(int)
    df["quantite_kg"] = df["quantite_kg"].astype(int)

    # Idempotence intra-fichier: 1 seul ordre retenu par ordre_id.
    df = df.drop_duplicates(subset=["ordre_id"], keep="first")
    return df


def ingest_erp() -> int:
    """Charge les ordres ERP depuis le JSON vers la table `ordres_erp`.

    Idempotent : si un ordre avec le même `ordre_id` existe déjà, il n'est pas réinséré.
    Retourne le nombre d'ordres effectivement insérés.
    """
    df = pd.read_json(ERP_JSON)
    df = _prepare_dataframe(df)

    salt = os.environ.get("ACEROX_ERP_SALT", "dev-only-change-me")
    session = get_session()
    inserted = 0

    try:
        ordres_table = _load_ordres_table(session)
        existing_order_ids = {
            int(row[0]) for row in session.execute(select(ordres_table.c.ordre_id)).all()
        }

        table_columns = set(ordres_table.c.keys())

        for _, row in df.iterrows():
            ordre_id = int(row["ordre_id"])
            if ordre_id in existing_order_ids:
                continue

            payload = {
                "ordre_id": ordre_id,
                "produit_ref": str(row["produit_ref"]),
                "site": str(row["site"]),
                "line_id": int(row["line_id"]),
                "date_lancement": row["date_lancement"].to_pydatetime(),
                "date_fin_prevue": row["date_fin_prevue"].to_pydatetime(),
                "statut": str(row["statut"]),
                "quantite_kg": int(row["quantite_kg"]),
            }

            ouvrier_hash = _hash_ouvrier_id(str(row["ouvrier_id"]), salt)
            if "ouvrier_hash" in table_columns:
                payload["ouvrier_hash"] = ouvrier_hash
            elif "ouvrier_id" in table_columns:
                # Compatibilité : si la colonne s'appelle encore ouvrier_id,
                # on y stocke la valeur hashée (jamais la valeur brute).
                payload["ouvrier_id"] = ouvrier_hash

            filtered_payload = {k: v for k, v in payload.items() if k in table_columns}
            session.execute(ordres_table.insert().values(**filtered_payload))

            existing_order_ids.add(ordre_id)
            inserted += 1

        session.commit()
    finally:
        session.close()

    return inserted


def main() -> None:
    inserted = ingest_erp()
    print(f"Pipeline ERP : {inserted} ordre(s) inséré(s) (idempotent).")


if __name__ == "__main__":
    main()
