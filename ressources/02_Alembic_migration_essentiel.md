# Alembic — migration de schéma — Mini-cours

> Brief associé : M3-B2
> Durée de lecture + pratique : ~25 min
> Pré-requis : avoir ajouté votre modèle dans `src/models.py` (mini-cours 01).

## Pourquoi cette techno ?

Quand un projet tourne déjà en production avec des **données réelles**,
tu ne peux pas juste éditer `models.py` et faire `Base.metadata.create_all()` :
ça ne change rien à la BDD existante (les tables existantes restent
telles quelles, les colonnes manquantes ne sont pas ajoutées).

Tu as besoin d'une **migration** : un fichier Python qui dit
*« avant la BDD ressemblait à ça, maintenant elle ressemble à ça »*,
avec un `upgrade()` (appliquer) et un `downgrade()` (revenir en arrière).

**Alembic** est l'outil standard côté Python/SQLAlchemy. Il :
- **Génère** automatiquement la migration en comparant `models.py` à la
  BDD réelle (`--autogenerate`)
- **Applique** les migrations dans l'ordre (`upgrade head`)
- **Revient en arrière** si besoin (`downgrade -1`)
- **Garde l'historique** des migrations dans `alembic/versions/`

C'est le geste pro **central** d'un data engineer junior. Sans migration,
chaque déploiement en prod = risque de casser la BDD.

**Alternatives à connaître :**

| Approche | Quand l'utiliser ? |
|---|---|
| **Alembic** | Notre M3 — standard SQLAlchemy |
| **Django Migrations** | Si tu es sur Django (pas notre stack) |
| **Liquibase / Flyway** | Java-centric, mais aussi multi-langue. Utilisé en grosse boîte. |
| **Scripts SQL manuels** | Anti-pattern en équipe — pas de versioning, pas de rollback |
| **`DROP TABLE; CREATE TABLE`** | **JAMAIS en prod** — perte de données |

## Concepts clés

- **Revision** : un fichier de migration. Identifié par un hash (ex. `0001`,
  `a1b2c3d4`). Lié à la précédente (`down_revision`).
- **`alembic init alembic`** : initialise le dossier. **Déjà fait dans le
  squelette** — ne pas le refaire.
- **`alembic revision --autogenerate -m "message"`** : compare
  `Base.metadata` (tes modèles Python) à la BDD réelle et génère un fichier
  de migration. **Toujours relire** ce qu'il génère avant d'appliquer.
- **`alembic upgrade head`** : applique toutes les migrations jusqu'à la
  dernière (la "tête").
- **`alembic upgrade +1`** ou `alembic upgrade <hash>` : applique 1
  migration de plus / jusqu'à une version précise.
- **`alembic downgrade -1`** : annule la dernière migration appliquée.
- **`alembic downgrade base`** : annule tout (revient à la BDD vide).
- **`alembic current`** : montre la version actuelle de la BDD.
- **`alembic history`** : montre l'historique des migrations.

## Exemple minimal qui tourne

Squelette M3-B2 (déjà configuré) :

```
alembic/
├── env.py                   # connecte alembic à src.models.Base
├── script.py.mako           # template des migrations générées
└── versions/
    └── 0001_initial_schema.py   # crée la table produits
```

`alembic.ini` à la racine définit `sqlalchemy.url = sqlite:///data/acerox.db`.

### Workflow type pour M3-B2

```bash
# 1. Tu modifies src/models.py (ta nouvelle table — cf. mini-cours 01)

# 2. Tu génères la migration
alembic revision --autogenerate -m "add <table> table"

# Alembic crée alembic/versions/<hash>_add_<table>_table.py
# avec un upgrade() et un downgrade() pré-remplis. RELIS-LE.

# 3. Tu appliques
alembic upgrade head

# 4. Tu vérifies
alembic current  # → abc123 (head)

# 5. Tu testes le rollback
alembic downgrade -1
# → table supprimée

# 6. Tu réappliques pour bosser
alembic upgrade head
```

### À quoi ressemble une migration

> Le squelette en contient **déjà** une : `alembic/versions/0001_initial_schema.py`
> (création de `produits`). **Ouvrez-la** — c'est exactement la structure
> qu'`--autogenerate` produira pour votre table.

```python
# extrait de alembic/versions/0001_initial_schema.py (existant)
def upgrade() -> None:
    op.create_table(
        "produits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("produit_ref", sa.String(20), nullable=False),
        # ... autres colonnes
    )
    op.create_index("ix_produits_produit_ref", "produits", ["produit_ref"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_produits_produit_ref", table_name="produits")
    op.drop_table("produits")
```

> 💡 Vous n'écrivez **pas** ce fichier à la main : `--autogenerate` le génère
> depuis votre modèle. Les `create_index` / contraintes qui apparaissent sont
> le **reflet de ce que vous avez déclaré dans `models.py`** — d'où l'importance
> d'y avoir mis les bons `index` / `unique` / `ForeignKey` (cf. contrat).

## Exercice guidé (tâche 5 du brief)

1. Vérifiez que `alembic current` retourne `0001` (initial)
2. Modifiez `src/models.py` selon le choix de votre binôme
3. `alembic revision --autogenerate -m "add <table> table"`
4. **Relisez** le fichier généré dans `alembic/versions/` — Alembic peut
   se tromper sur les défauts ou les contraintes complexes
5. `alembic upgrade head` → la table est créée
6. Vérifiez avec `sqlite3 data/acerox.db ".tables"` (ou DBeaver)
7. **Testez le rollback** : `alembic downgrade -1` puis `alembic upgrade head`
8. Documentez dans le README la commande de rollback

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Modifier directement la BDD avant la migration | Désynchro modèle / BDD — Alembic perdu |
| Ne pas relire la migration générée | Faux positifs (changements parasites) — Alembic n'est pas magique |
| Oublier de commit `alembic/versions/<hash>.py` | Autre dev qui clone n'a pas ta migration |
| `--autogenerate` sur une BDD avec données | OK si la migration ajoute une table — risque si elle modifie une existante (perte de données) |
| Plusieurs `--autogenerate` empilés sans nettoyage | Historique pourri — préfère 1 migration propre par feature |
| `downgrade()` vide ou identique à upgrade | Rollback impossible — toujours relire et corriger |
| Faire pétiller `Base.metadata.create_all()` après une migration | Conflit — `create_all` ignore les migrations, ne pas mélanger |

**Symptôme → cause probable** :

| Symptôme | Cause probable |
|---|---|
| `Can't locate revision identified by '...'` | Migration manquante (pas committée par un collègue) |
| `Target database is not up to date` | Pas dans le bon état — fais `alembic upgrade head` |
| `--autogenerate` génère une migration vide | Aucun changement dans `models.py` vs BDD actuelle |
| `alembic upgrade head` ne fait rien | La BDD est déjà à jour |
| `IntegrityError` pendant l'upgrade | Données existantes qui ne respectent pas le nouveau schéma — à gérer dans la migration (`op.bulk_insert`, ou nettoyage avant) |

## Pour aller plus loin

- **Alembic — Tutorial** : <https://alembic.sqlalchemy.org/en/latest/tutorial.html>
- **Alembic — Auto Generating Migrations** : <https://alembic.sqlalchemy.org/en/latest/autogenerate.html>
- **Article "Database migrations done right"** : <https://martinfowler.com/articles/evodb.html>
  (Fowler, 2003 — toujours d'actualité conceptuellement)

## Vérification (checklist binôme)

- [ ] Nous avons généré **1 migration** (et **une seule**) via `--autogenerate`
- [ ] Nous avons **relu** le fichier généré avant `upgrade head`
- [ ] `alembic upgrade head` fonctionne sur une BDD vierge
- [ ] `alembic downgrade -1` ramène à l'état précédent **sans erreur**
- [ ] Le fichier `alembic/versions/<hash>.py` est **committé**
- [ ] La commande de **rollback** est **documentée** dans le README
