# Ingestion idempotente — Mini-cours

> Brief associé : M3-B2
> Durée de lecture + pratique : ~20 min
> Pré-requis : modèle SQLAlchemy + migration appliquée (mini-cours 01 et 02).

## Pourquoi cette techno ?

Un script qui ingère des données dans une BDD doit être **idempotent** :
le relancer **2 fois** ne doit **pas** dupliquer les lignes.

C'est essentiel en production :
- Le script crash en cours → tu le relances
- Cron / orchestration → exécution répétée
- Tests → on lance N fois la même fixture
- Reprise après incident → relance sans peur

Sans idempotence, chaque relance ajoute des doublons. Au bout d'une semaine
ta BDD est pourrie.

**Le principe** : avant d'insérer une ligne, on **vérifie** si elle existe
déjà. Si oui, on **skip** (ou on **update**, selon le besoin).

**Alternatives à connaître :**

| Approche | Quand l'utiliser ? |
|---|---|
| **Filter avant insert (Python)** | Notre M3 — explicite, lisible, OK petit volume |
| **`INSERT OR IGNORE` (SQLite)** | Idiomatique SQLite — élégant si tu connais |
| **`ON CONFLICT DO NOTHING` (PostgreSQL)** | Équivalent PostgreSQL — pas dispo en SQLite |
| **`bulk_insert_mappings`** | Plus rapide pour gros volumes — pas notre besoin M3 |
| **Pandas `.drop_duplicates()` avant insert** | Dédup en mémoire — OK petit-moyen volume |

## Concepts clés

- **Clé d'unicité** : la colonne (ou combinaison) qui identifie une ligne.
  Ex. `ordre_id` pour ERP, `(timestamp, sensor_id)` pour IoT.
- **Idempotence forte** : N appels = état identique. C'est l'objectif.
- **Stratégie filter** : `SELECT existing_ids → SET → if id in set: skip`.
- **Stratégie upsert** : si existe et différent, update ; sinon insert.
  Plus complexe — pas notre besoin M3.
- **Dédup en source** : pandas `.drop_duplicates(subset=[...])` avant
  insert — utile pour le **CSV capteurs IoT** qui a 2 % de doublons natifs.

## Le pattern, sur la table existante (`produits`)

> Le squelette contient **déjà** une ingestion idempotente complète :
> `src/pipeline_existante.py` → `ingest_produits()`. **C'est votre modèle à
> imiter** — relisez-la avant de coder la vôtre.

```python
# extrait de src/pipeline_existante.py (NE PAS modifier ce fichier)
def ingest_produits() -> int:
    df = pd.read_csv(PRODUITS_CSV)
    session = get_session()
    inserted = 0
    try:
        # clés déjà en base → on ne réinsère pas (idempotence)
        existing = {p.produit_ref for p in session.query(Produit.produit_ref).all()}
        for _, row in df.iterrows():
            if row["produit_ref"] in existing:        # filtre sur la CLÉ d'unicité
                continue
            session.add(Produit(produit_ref=row["produit_ref"], nom=row["nom"],
                                 categorie=row["categorie"], unite=row["unite"]))
            inserted += 1
        session.commit()
    finally:
        session.close()
    return inserted
```

Les **3 gestes** à retenir et transposer :

1. **Charger** la source (CSV → `pd.read_csv` ; JSON → `json.load`).
2. **Filtrer** : lire les clés déjà présentes en base → ne garder que les
   nouvelles lignes. ⚠️ Cette *clé*, c'est **votre contrainte d'unicité** — à
   identifier dans `contrat_donnees_modele.md`, **pas donnée ici**.
3. **Insérer en bloc** (`add_all`) puis **un seul** `commit()`.

## À vous : `src/ingest_<source>.py`

Transposez le pattern à la source de votre binôme. Squelette de départ :

```python
"""src/ingest_<source>.py"""
# TODO imports : pandas / json, select, get_session, et VOTRE modèle

def ingest_<source>() -> int:
    # 1. Charger la source (depuis data/...)
    # 2. Nettoyer AVANT insertion :
    #    - IoT : dédupliquer les doublons natifs ; DÉCIDER du sort du capteur
    #            défaillant Roubaix L3 (écarter / marquer / traiter en aval)
    #            et le documenter (cf. contrat + fiche modèle)
    #    - ERP : traiter `ouvrier_id` (donnée personnelle) selon le contrat
    # 3. Filtrer sur VOTRE clé d'unicité (idempotence) — cf. contrat
    # 4. add_all(...) puis un seul commit()
    ...
```

> 💡 **ERP & RGPD** — `ouvrier_id` ne doit jamais être stocké en clair. Une
> technique courante = un hash avec sel (`hashlib.sha256(sel + valeur)`).
> À vous de trancher *hash* vs *suppression* et de le justifier (`decisions.md`).

## Exercice guidé (tâche 3 du brief)

1. Choisir IoT ou ERP (cf. `decisions.md`)
2. Créer `src/ingest_<source>.py` avec :
   - Type hints
   - **Dédup en source** si pertinent (IoT)
   - **Hash RGPD** si pertinent (ERP)
   - **Filter avant insert** (idempotence)
3. Lancer 2 fois → vérifier que la 2ᵉ fois retourne `0 insertions`

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Pas de dédup CSV en amont | Doublons natifs entrent en BDD → contrainte unique pète |
| Pas de filter avant insert | Crash sur `IntegrityError` au 2ᵉ run |
| `for + session.add + session.commit()` à chaque ligne | Très lent — fais un `add_all` + 1 commit |
| Hash sans sel | RGPD-suspect (rainbow table possible) |
| `ouvrier_id` en clair conservé | RGPD-fail — toujours hasher ou supprimer |
| `INSERT OR IGNORE` sans contrainte unique en BDD | N'a aucun effet — il faut une UNIQUE sur la clé |
| Ingestion qui crash en milieu → pas de rollback | Données partielles en BDD — toujours utiliser session/commit en bloc |

**Symptôme → cause probable** :

| Symptôme | Cause probable |
|---|---|
| `IntegrityError: UNIQUE constraint failed` | Doublon — vérifie ta logique de filter |
| Le 2ᵉ run insère plus de 0 lignes | Logique de filter cassée — vérifie ta clé d'unicité |
| Insertion ultra-lente (> 1 min sur 50k lignes) | Pas de bulk insert — utilise `add_all` + 1 `commit` |
| `KeyError` sur `ouvrier_id` | Le JSON a `null` au lieu de clé absente — `order.get("ouvrier_id")` plutôt que `order["ouvrier_id"]` |
| Hash différents pour même `ouvrier_id` | Sel oublié OU pas constant — toujours le même `HASH_SALT` |

## Pour aller plus loin

- **SQLAlchemy — bulk insert** : <https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-bulk-insert-statements>
- **PostgreSQL `ON CONFLICT`** : <https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT>
  (à connaître pour quand on quittera SQLite)
- **CNIL — pseudonymisation** : <https://www.cnil.fr/fr/technologies/lanonymisation-de-donnees-personnelles>

## Vérification (checklist binôme)

- [ ] Notre `src/ingest_<source>.py` a des **type hints** et **pas de print**
- [ ] Le 1er run insère N lignes
- [ ] Le **2e run insère 0 lignes** (idempotence vérifiée)
- [ ] Si ERP : `ouvrier_id` hashé (avec sel) ou retiré, **jamais** en clair
- [ ] Si IoT : les ~1000 doublons natifs sont déduplés avant insert
- [ ] Le script ne crash pas sur un fichier malformé (gestion d'erreur)
