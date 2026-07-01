# Tests pytest pour pipeline + migration — Mini-cours

> Brief associé : M3-B2
> Durée de lecture + pratique : ~20 min
> Pré-requis : pipeline d'ingestion en place (mini-cours 03).

## Pourquoi cette techno ?

Une pipeline de données **doit** être testée — sinon une régression
silencieuse passe en prod et pollue la BDD.

3 tests minimum demandés en M3-B2 :

1. **Test de migration** : après `alembic upgrade head`, la table existe
   avec le bon schéma.
2. **Test d'ingestion valide** : un fichier d'entrée OK insère N lignes
   sans doublon.
3. **Test d'ingestion malformée** : un fichier d'entrée KO lève une
   exception claire, la BDD reste **inchangée** (pas de demi-insertion).

Le **vrai** apport des tests : tu peux **modifier en confiance** ta
pipeline pour ajouter une 2ᵉ source en M5 ou M6, sans casser la 1ʳᵉ.

**Alternatives à connaître :**

| Approche | Quand l'utiliser ? |
|---|---|
| **pytest + fixtures BDD éphémère** | Notre M3 — standard Python, rapide, isolé |
| **pytest + Docker BDD** | Quand on teste contre PostgreSQL/MySQL en CI (M5+) |
| **Unittest stdlib** | OK, mais pytest est plus ergonomique |
| **Test d'intégration end-to-end** | M5 (CI complet) |

## Concepts clés

- **BDD éphémère par test** : à chaque test, on crée une SQLite temporaire,
  on bosse dedans, on la supprime à la fin. Pas d'effet de bord entre tests.
- **Fixture pytest** : fonction qui prépare un état avant le test
  (`@pytest.fixture`). Avec `yield`, le code après yield = cleanup.
- **Isolation** : aucun test ne doit dépendre de l'ordre d'exécution.
- **Test de migration** : on appelle `alembic upgrade head` ou
  `Base.metadata.create_all()` dans la fixture, on vérifie que la table
  attendue existe.
- **Test transactionnel** : on encadre un test dans une transaction qu'on
  rollback à la fin — alternative au "fichier éphémère".

## Exemple minimal qui tourne

### Fixtures (déjà dans `tests/conftest.py`)

```python
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base

@pytest.fixture
def tmp_db_url():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield f"sqlite:///{path}"
    Path(path).unlink(missing_ok=True)

@pytest.fixture
def tmp_engine(tmp_db_url):
    engine = create_engine(tmp_db_url, future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def tmp_session(tmp_engine):
    Session = sessionmaker(bind=tmp_engine, autoflush=False)
    session = Session()
    yield session
    session.close()
```

### Le patron de test, sur la pipeline existante (`produits`)

> `tests/test_pipeline_initial.py` (fourni) teste **déjà** la table `produits`.
> Lisez-le : c'est la forme exacte que vos 3 tests doivent prendre pour
> **votre** table. Les fixtures (`tmp_engine`, `tmp_session`) sont dans
> `tests/conftest.py` — rien à réécrire.

Les **3 formes** à reproduire (remplacez `<…>` par votre source) :

```python
# 1. MIGRATION — la table attendue existe après création du schéma
def test_<table>_existe(tmp_engine):
    from sqlalchemy import inspect
    tables = inspect(tmp_engine).get_table_names()
    assert "<votre_table>" in tables
    assert "produits" in tables          # la pipeline existante doit rester

# 2. INGESTION VALIDE + IDEMPOTENCE — N lignes, puis 0 au 2ᵉ run
def test_ingestion_normale(tmp_session, monkeypatch, tmp_path):
    # prépare une mini-fixture (quelques lignes, dont 1 doublon sur la clé)
    # puis redirige chemin source + get_session vers la BDD éphémère :
    monkeypatch.setattr("src.ingest_<source>.<CHEMIN>", fixture_path)
    monkeypatch.setattr("src.ingest_<source>.get_session", lambda: tmp_session)
    assert ingest_<source>() == N
    assert ingest_<source>() == 0        # idempotence

# 3. ENTRÉE MALFORMÉE — exception claire, BDD inchangée
def test_ingestion_invalide(tmp_session, monkeypatch, tmp_path):
    monkeypatch.setattr("src.ingest_<source>.<CHEMIN>", tmp_path / "absent.csv")
    monkeypatch.setattr("src.ingest_<source>.get_session", lambda: tmp_session)
    with pytest.raises(<ExceptionAttendue>):
        ingest_<source>()
```

> ⚠️ Votre **mini-fixture** doit avoir des colonnes **conformes au contrat**
> (`contrat_donnees_modele.md`) et **au moins un doublon** sur votre clé
> d'unicité — sinon le test 2 ne prouve pas l'idempotence.

## Exercice guidé (tâche 6 du brief)

Écris **au moins 3 tests** dans `tests/test_ingest.py` et `tests/test_migration.py` :

1. La table que vous avez ajoutée **existe** dans la BDD éphémère
2. L'ingestion d'un fichier valide insère N lignes **sans doublon**
3. L'ingestion d'un fichier malformé (ou inexistant) lève une exception
   claire et la BDD reste inchangée

`pytest -v` doit retourner tous verts (y compris le `test_pipeline_initial.py`
fourni).

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Tests qui partagent la même BDD | Effets de bord entre tests, ordre dépendant |
| Pas de cleanup des fichiers temp | Tests qui passent localement mais cassent en CI |
| `monkeypatch` mal posé | Le test attaque la vraie BDD (`data/acerox.db`) — désastre |
| `assert n > 0` au lieu de `assert n == 2` | Tu ne sais pas si tu testes vraiment |
| Test d'ingestion sans test de doublon (2ᵉ run) | Tu rates l'idempotence |
| `pytest` qui montre des warnings | Souvent SQLAlchemy 1.x deprecation — ignore en M3, fix en M5 |

**Symptôme → cause probable** :

| Symptôme | Cause probable |
|---|---|
| `OperationalError: no such table` dans un test | `Base.metadata.create_all(engine)` pas appelé dans la fixture |
| Tests qui passent isolés mais cassent ensemble | Fixture mal scope (utilise `scope="function"` par défaut, pas `module`) |
| `FileNotFoundError` sur le CSV de test | `tmp_path` mal utilisé — utilise `tmp_path / "name.csv"` (Path) |
| `monkeypatch` n'a pas d'effet | Tu monkeypatches après l'import — toujours **avant** d'appeler la fonction |
| Test très lent (> 5 s) | Probablement chargement de tout le CSV de prod — utilise une mini-fixture |

## Pour aller plus loin

- **Pytest — fixtures** : <https://docs.pytest.org/en/stable/explanation/fixtures.html>
- **Pytest — monkeypatch** : <https://docs.pytest.org/en/stable/how-to/monkeypatch.html>
- **Doc SQLAlchemy — testing** : <https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites>

## Vérification (checklist binôme)

- [ ] Notre `tests/test_migration.py` vérifie l'existence de la table ajoutée
- [ ] Notre `tests/test_ingest.py` teste l'ingestion **et** l'idempotence
- [ ] Au moins **1 test** d'erreur (fichier malformé / inexistant)
- [ ] `pytest -v` est **tout vert** (y compris `test_pipeline_initial.py`)
- [ ] Aucun test n'attaque la BDD `data/acerox.db` (toujours via fixture
      éphémère)
