# SQLAlchemy ORM — Mini-cours

> Brief associé : M3-B2
> Durée de lecture + pratique : ~25 min
> Pré-requis : `pip install sqlalchemy==2.0.36`, notion de table SQL.

## Pourquoi cette techno ?

Un **ORM** (Object-Relational Mapping) traduit entre des **objets Python**
et des **tables SQL**. Au lieu d'écrire :

```sql
INSERT INTO produits (produit_ref, nom, categorie, unite)
VALUES ('ALU-T1-15', 'Tôle aluminium T1 15mm', 'aluminium', 'kg');
```

Tu écris :

```python
session.add(Produit(produit_ref="ALU-T1-15", nom="Tôle aluminium T1 15mm",
                    categorie="aluminium", unite="kg"))
session.commit()
```

**Pourquoi c'est utile** :
- **Type hints** Python sur tes données → IDE t'aide
- **Migrations** : tu changes le modèle Python, Alembic génère le SQL DDL
- **Indépendance BDD** : passe de SQLite à PostgreSQL en changeant l'URL
- **Tests** : remplace ta BDD par une instance temporaire (cf. fixtures M3-B2)

**SQLAlchemy** est **le** standard Python (≈ Spring Data côté Java, ≈
ActiveRecord côté Ruby). Version actuelle : **2.x** (l'API a changé en
2023 — toujours utiliser des exemples 2.x récents).

**Alternatives à connaître :**

| Approche | Quand l'utiliser ? |
|---|---|
| **SQLAlchemy ORM** | Notre M3 — standard, riche, mature |
| **SQLAlchemy Core** | Niveau plus bas (proche du SQL) — pas notre choix M3 |
| **SQL brut + psycopg2 / sqlite3** | Scripts one-shot, perfo extrême |
| **Django ORM** | Si tu utilises Django (pas notre stack) |
| **Tortoise ORM / SQLModel** | Plus jeunes, async-native — bonus si curieux |

## Concepts clés

- **`Base = declarative_base()`** : classe de base pour déclarer tes
  modèles. Tous tes modèles héritent de `Base`.
- **Modèle** : classe Python avec `__tablename__` + colonnes
  (`Column(...)`). Représente une table.
- **`Column(Type, ...)`** : colonne. Type = `Integer`, `String(N)`,
  `DateTime`, `Float`, `Boolean`, etc.
- **Contraintes** : `primary_key=True`, `nullable=False`, `unique=True`,
  `index=True`, `default=...`, `ForeignKey("autre_table.id")`.
- **`engine = create_engine(URL)`** : connexion à la BDD (lazy — pas
  ouverte tant qu'on ne l'utilise pas).
- **`Session`** : transaction. On ouvre, on fait du CRUD, on `commit()`
  (ou `rollback()`), on `close()`.
- **CRUD** :
  - **Create** : `session.add(obj)` + `session.commit()`
  - **Read** : `session.execute(select(Model).where(...))`
  - **Update** : modifie l'attribut Python, `session.commit()`
  - **Delete** : `session.delete(obj)` + `session.commit()`

## Exemple minimal qui tourne

On illustre sur la table **déjà présente** dans le squelette (`Produit`,
dans `src/models.py`) — c'est aussi le modèle que vous imiterez pour la vôtre.

```python
# sqlalchemy==2.0.36
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.models import Base, Produit   # table déjà déclarée dans le squelette

# Setup
engine = create_engine("sqlite:///data/acerox.db", future=True)
Base.metadata.create_all(engine)  # en M3, c'est Alembic qui crée les tables
Session = sessionmaker(bind=engine)

# Création
session = Session()
session.add(Produit(
    produit_ref="ALU-T1-15", nom="Tôle aluminium T1 15mm",
    categorie="aluminium", unite="kg",
))
session.commit()

# Lecture
results = session.execute(
    select(Produit).where(Produit.categorie == "aluminium").limit(5)
).scalars().all()
for r in results:
    print(r.produit_ref, r.nom)

session.close()
```

> 💡 `Produit` n'utilise que des `String`. Votre table aura aussi des
> `DateTime`, `Float`, un `index`, peut-être une `ForeignKey` — voir
> *Concepts clés* ci-dessus pour les briques, et le contrat pour le besoin.

## Exercice guidé (tâche 3 du brief)

Dans `src/models.py`, déclarez la table de votre source — **à partir du
contrat** (`contrat_donnees_modele.md`), en **imitant `Produit`**. On ne vous
donne pas la classe toute faite : l'écrire, **c'est l'exercice**.

Briques SQLAlchemy à votre disposition (cf. *Concepts clés*) :
`Column` · types `Integer / String(N) / Float / DateTime` · contraintes
`primary_key`, `nullable`, `unique`, `index`, `ForeignKey`, `UniqueConstraint`.

Traduisez les **exigences du contrat** en décisions techniques, et tracez-les
dans `decisions.md` :

- **Clé d'unicité** : qu'est-ce qui identifie une ligne ? (une seule colonne
  `unique=True`, ou une combinaison → `UniqueConstraint(...)` ?)
- **Index** : quelle(s) colonne(s) sont filtrées souvent ?
- **Lien entre tables** (option B) : comment rattacher un ordre à un produit ?
- **Nullable** : quels champs peuvent légitimement manquer ?

⚠️ Pensez à **importer** en tête de `models.py` les types/contraintes que vous
utilisez (`DateTime`, `Float`, `ForeignKey`, `UniqueConstraint`…), sinon
`NameError`.

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Oublier `Base.metadata.create_all(engine)` en local | Aucune table créée, INSERT crash |
| Oublier `session.commit()` | Données perdues à la fermeture |
| Oublier `session.close()` (ou contexte manager) | Connexions qui s'accumulent → leak |
| Pas d'`index` sur les colonnes filtrées | Requêtes lentes (acceptable en M3 vu le volume, mais à signaler) |
| `String` sans longueur | OK SQLite, mais portage PostgreSQL → warning |
| Forgot `nullable=False` sur les obligatoires | Tu acceptes des NULL silencieux |
| API SQLAlchemy 1.x (`query()`, `.filter()`) | Deprecated, utiliser `select()` + `where()` (2.x) |

**Symptôme → cause probable** :

| Symptôme | Cause probable |
|---|---|
| `OperationalError: no such table` | `Base.metadata.create_all(engine)` pas appelé OU mauvais engine |
| `IntegrityError: UNIQUE constraint failed` | Tu insères un doublon (cf. mini-cours 03 idempotence) |
| Tes modifs ne persistent pas | `session.commit()` oublié |
| `DetachedInstanceError` | Tu utilises un objet après `session.close()` — `expire_on_commit=False` ou refais une session |
| Tutos d'autres collègues qui n'ont pas la même API | Probablement SQLAlchemy 1.x — préfère la 2.x exclusivement |

## Pour aller plus loin

- **Doc officielle SQLAlchemy 2.0 — ORM Quickstart** : <https://docs.sqlalchemy.org/en/20/orm/quickstart.html>
- **Migration 1.x → 2.x** : <https://docs.sqlalchemy.org/en/20/changelog/migration_20.html>
- **SQLModel** (surcouche Pydantic + SQLAlchemy par le créateur de FastAPI) — bonus à connaître : <https://sqlmodel.tiangolo.com/>

## Vérification (checklist binôme)

- [ ] Nous avons ajouté **1 modèle** dans `src/models.py` avec colonnes typées
- [ ] Les colonnes obligatoires ont `nullable=False`
- [ ] Au moins **1 index** sur une colonne de filtrage fréquent
- [ ] Si ERP : `ouvrier_id` traité (hashé ou retiré), **jamais** stocké en clair
- [ ] `Base.metadata.create_all(engine)` fonctionne en local pour tester
      vite (avant Alembic)
