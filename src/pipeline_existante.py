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
from src.models import Base, Produit

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


def main() -> None:
    """Init BDD + chargement référentiel produits."""
    init_db()
    n = ingest_produits()
    print(f"Pipeline existante : {n} produit(s) inséré(s) (idempotent — relancer ne duplique pas).")


if __name__ == "__main__":
    main()
