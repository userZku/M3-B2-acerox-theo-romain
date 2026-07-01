# Ressources M3-B2 — Pipeline + migration Acerox

> Brief associé : **M3-B2** (suite directe de M3-B1).
> Mode : sync binôme mercredi (2 h) + 3 h async binôme jeudi/vendredi matin.

---

## 📚 Ordre de mobilisation

| Tâche | Durée | Mini-cours |
|---|---|---|
| 1. Setup binôme + appropriation squelette | 30 min | [`05_Pair_coding_git_essentiel.md`](./05_Pair_coding_git_essentiel.md) |
| 2. Choix source + normalisation | 60 min | [`03_Ingestion_idempotente_essentiel.md`](./03_Ingestion_idempotente_essentiel.md) |
| 3. Modèle SQLAlchemy nouvelle table | 30 min | [`01_SQLAlchemy_ORM_essentiel.md`](./01_SQLAlchemy_ORM_essentiel.md) |
| 4. Migration Alembic (async) | 60 min | [`02_Alembic_migration_essentiel.md`](./02_Alembic_migration_essentiel.md) |
| 5. Tests pytest (async) | 45 min | [`04_Tests_pipeline_essentiel.md`](./04_Tests_pipeline_essentiel.md) |
| 6. README + tag (async) | 60 min | (capitalise mini-cours M1-B2 Mermaid) |

> 💡 Tu peux lire `05_Pair_coding_git_essentiel.md` **avant** 9h mercredi
> si tu veux gagner du temps sur le setup binôme.

## 📄 Documents fournis par Acerox (lecture seule, à lire en tâche 2)

Avant de coder l'ingestion, lisez ces deux documents : ils disent **pour qui**
vous préparez les données et **à quoi** votre livraison doit ressembler.

| Document | Rôle | Quand |
|---|---|---|
| [`fiche_modele_acerox.md`](./fiche_modele_acerox.md) | Le modèle existant (votre client interne) : objectif, entrées/sortie, limites | avant tâche 2 |
| [`contrat_donnees_modele.md`](./contrat_donnees_modele.md) | La **table cible** + clauses de qualité que votre pipeline doit livrer | pendant tâches 2-3, à honorer |

---

## 🎯 Ce qu'on cherche à atteindre

À la fin de M3-B2, votre binôme doit avoir :

- **Une nouvelle table** SQLAlchemy déclarée + **1 migration Alembic**
  réversible
- **Un script d'ingestion** idempotent (`src/ingest_<source>.py`)
- **≥ 3 tests pytest** verts (initial + migration + ingestion)
- Un **README** avec schéma Mermaid + 3 commandes de reproduction +
  section Rollback
- Un **tag git** `v0.1.0-pipeline-m3` sur le commit final
- Tous les commits significatifs en `Co-authored-by:`

→ Compétences visées : **C1 — imiter** (renforcement) + **C3 — transposer** (palier final).

---

## 🔗 Liens externes

Cf. [`liens_officiels.md`](./liens_officiels.md).

---

## 🆘 Bloqué·e·s ?

1. Relisez le mini-cours de la tâche en cours.
2. **Alembic** : si une migration plante, supprimez `data/acerox.db` et
   refaites `alembic upgrade head` — repart d'un état propre.
3. **Tests qui cassent** : `test_pipeline_initial.py` doit rester vert.
   Si non, votre régression est localisée dans `src/models.py` ou
   `pipeline_existante.py`.
4. **En binôme** : si 30 min sur le même problème, **switchez**
   driver/navigator. Souvent ça débloque.
5. Demande sur Discord (`fil-M3-B2`).
