# M3-B2 — Pipeline Acerox (IoT + migrations)

> Repo binôme Théo & Romain.

Ce dépôt contient une pipeline d’ingestion pour les mesures IoT, un modèle SQLAlchemy, et une migration Alembic pour la table `mesures_iot`.

---

## Schéma des flux

```mermaid
%%{init: {
  "themeVariables": {
    "background": "#0176D3",
    "edgeColor": "#ff0000",
    "lineColor": "#ff0000",
    "arrowheadColor": "#ff0000",
    "edgeStrokeWidth": 5
  }
}}%%
flowchart LR
    %% Sources
    SRC1["📡 capteurs_iot.csv<br>s7"]
    SRC2["📋 erp_export.json<br>s8"]
    SRC3["📝 logs_machines.log<br>s9"]

    %% Ingestion détaillée
    subgraph INGEST["🔄 Ingestion — pandas + SQLAlchemy"]
        STEP1["📆 Conversion vers datetime Python-compatible<br/>(SQLite-friendly)"]
        STEP2["🧹 Déduplication pandas<br/>clé métier (contrat IoT)"]
        STEP3["📸 Snapshot des clés déjà en base<br/>→ idempotence"]
        STEP4["🚫 Ignorer lignes déjà présentes<br/>(même timestamp + sensor_id)"]
        STEP5["🏭 Traitement site Roubaix (ligne 3)<br/>Température + débit conservés, vibration = null"]
        STEP6["🗺️ Mapping explicite CSV → modèle SQLAlchemy"]
        STEP7["🔁 Gestion des doublons dans le même CSV"]
        STEP8["💾 Commit unique en fin de boucle"]
    end

    %% Stockage détaillé
    subgraph BDD["🗄️ BDD pivot — SQLite"]
        PRODUITS["📦 Table PRODUITS<br/>id (PK)<br/>produit_ref (UK)<br/>nom<br/>categorie<br/>unite"]
        MESURES["📈 Table MESURES_IOT<br/>id (PK)<br/>timestamp<br/>site<br/>line_id<br/>sensor_id<br/>temperature_c<br/>vibration_mms<br/>debit_uh"]
    end

    %% Modèle existant
    MODEL[🧠 Modèle prédiction défauts<br/>Acerox — existant]

    %% Liens
    SRC1 -->|temps réel| INGEST
    SRC2 -.->|batch journalier| INGEST
    SRC3 -.->|Transformation CSV : les 4 premiers espaces remplacés par des virgules| INGEST
    STEP8 -->|insertion SQLAlchemy| BDD
    PRODUITS -->|référencé par| MESURES
    BDD -->|consommée par| MODEL

    %% Styles
    classDef source fill:#e1f5ff,stroke:#0277bd,color:#000000
    classDef modele fill:#fff4e1,stroke:#c97a00,color:#000000
    classDef B2 fill:#d4f4dd,stroke:#1a7a3a,color:#000000
    classDef ETAPE fill:#eeeeee,stroke:#bcbcbc,color:#000000
    class SRC1,SRC2,SRC3 source
    class BDD B2
    class INGEST B2
    class STEP1,STEP2,STEP3,STEP4,STEP5,STEP6,STEP7,STEP8,PRODUITS,MESURES ETAPE
    class MODEL modele
```

---

## Démarrage rapide

```bash
git clone git@github.com:<owner>/M3-B2-acerox-<binome>.git
cd M3-B2-acerox-<binome>

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
alembic upgrade head
python -m src.pipeline_existante
```

Puis vérifier les tests :

```bash
pytest -q
```

---

## Reproduire le projet en 3 commandes

Si tu repars d’une base vide, ces 3 commandes suffisent pour remettre le projet en état de fonctionnement :

```bash
pip install -r requirements.txt
alembic upgrade head
python -m src.pipeline_existante
```

Ensuite, pour charger les mesures IoT :

```bash
python -m src.ingest_iot
```

---

## Régénérer la table `mesures_iot`

Quand `src/models.py` change, il faut générer puis appliquer une migration Alembic.

### Cas standard: schéma modifié

```bash
alembic revision --autogenerate -m "add mesures_iot table"
alembic upgrade head
python -m src.ingest_iot
```

### Cas remise à plat complète

Si tu veux repartir de la version initiale puis reconstruire la base :

```bash
alembic downgrade 0001
alembic upgrade head
python -m src.ingest_iot
```

---

## Schéma Mermaid

```mermaid
erDiagram
   PRODUITS {
      int id PK
      string produit_ref UK
      string nom
      string categorie
      string unite
   }

   MESURES_IOT {
      int id PK
      datetime timestamp
      string site
      int line_id
      string sensor_id
      float temperature_c
      float vibration_mms
      float debit_uh
   }

```

Note: la table `mesures_iot` est indépendante de `produits` dans le code actuel. Le diagramme montre surtout les deux entités du projet.

---

## Rollback

### Revenir en arrière d’une migration

```bash
alembic downgrade -1
```

### Revenir à la base initiale

```bash
alembic downgrade 0001
```

### Revenir ensuite au dernier état du projet

```bash
alembic upgrade head
```

Si la base locale est incohérente, tu peux aussi supprimer `data/acerox.db` puis relancer :

```bash
alembic upgrade head
python -m src.pipeline_existante
```

---

## Structure utile

```text
README.md
alembic.ini
alembic/versions/0001_initial_schema.py
alembic/versions/0db6ffca86dc_add_mesures_iot_table.py
data/produits.csv
data/capteurs_iot.csv
src/db.py
src/models.py
src/pipeline_existante.py
src/ingest_iot.py
tests/conftest.py
tests/test_pipeline_initial.py
tests/test_ingest.py
```

---

## Conventions

- Python 3.11+
- Type hints sur les fonctions publiques
- `pathlib.Path` pour les chemins
- Pas de `print` en logique applicative
- Commit binôme avec `Co-authored-by: Prénom Nom <email>`

---

## Aide

- Modèle SQLAlchemy: [ressources/01_SQLAlchemy_ORM_essentiel.md](ressources/01_SQLAlchemy_ORM_essentiel.md)
- Alembic: [ressources/02_Alembic_migration_essentiel.md](ressources/02_Alembic_migration_essentiel.md)
- Ingestion idempotente: [ressources/03_Ingestion_idempotente_essentiel.md](ressources/03_Ingestion_idempotente_essentiel.md)
- Tests: [ressources/04_Tests_pipeline_essentiel.md](ressources/04_Tests_pipeline_essentiel.md)
- Git binome: [ressources/05_Pair_coding_git_essentiel.md](ressources/05_Pair_coding_git_essentiel.md)
