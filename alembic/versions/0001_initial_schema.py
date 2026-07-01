"""initial schema — table produits

Revision ID: 0001
Revises:
Create Date: 2026-05-26 09:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée la table `produits` initiale."""
    op.create_table(
        "produits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("produit_ref", sa.String(20), nullable=False),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("categorie", sa.String(20), nullable=False),
        sa.Column("unite", sa.String(10), nullable=False, server_default="kg"),
    )
    op.create_index("ix_produits_produit_ref", "produits", ["produit_ref"], unique=True)


def downgrade() -> None:
    """Supprime la table `produits`."""
    op.drop_index("ix_produits_produit_ref", table_name="produits")
    op.drop_table("produits")
