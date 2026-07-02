# Decisions — Binôme `Théo` × `Romain` (M3-B2 Acerox)

> Document à compléter à 2 pendant la phase sync (15 min avant de coder).
> Servira de référence pendant la phase async + RDV vendredi.

## 1. Source choisie pour l'ingestion

> Quelle source intégrez-vous en M3-B2 ? Argumentez en 3 lignes max.

**Choix** : ☑ `capteurs_iot.csv` (CSV ~51k lignes) ☑ `erp_export.json` (JSON ~2k ordres)

**Argument** :
- Lors de M3-B1 on pensait tous les deux ne pas utiliser ERP comme source d'entrainement mais plus comme source d'enrichissement
- IOT contient les données industrielles sur l'état des capteurs : ça devrait être suffisant pour déterminer dans un premier temps le defaut qualité

Finalement on a aussi intégré `erp_export.json` dans un deuxième temps.

## 2. Réflexe de stockage

> Pourquoi une BDD relationnelle SQLite ici, et dans quel cas du document MongoDB ou du fichier Parquet ?
> S'appuyer sur la grille de décision Stockage & échelle

**Choix** : BDD relationnelle SQLite :)

**Argument** : 
- Données structurée (lignes/colonnes, schéma stable) donc BDD relationnelle suffit. 
- Les logs IOT demandent des écritures fréquentes.
- Volume des logs < 1 Go (3Mo sur un mois), même sur du temps réel les données tiennent ne RAM.

## 3. Exigences du contrat

- Côté IoT, clé d'unicité : qu'est-ce qui identifie une ligne ? => `UniqueConstraint(timestamp, sensor_id)` sur `mesures_iot`.
- Côté IoT, index : quelle(s) colonne(s) sont filtrées souvent ? => `timestamp`, `site`, `line_id`, `sensor_id` : ces colonnes seront souvent utilisées dans les `WHERE` des requêtes.
- Côté IoT, nullable : quels champs peuvent légitimement manquer ? => `vibration_mms` peut manquer (capteur momentanément muet).
- Côté ERP, unicité et recherche : chaque ordre est identifié par `ordre_id`, qui doit donc être `unique` et indexé pour accélérer les recherches directes.
- Côté ERP, lien métier : `produit_ref` doit être une clé étrangère vers `produits.produit_ref` pour garantir qu'un ordre ERP référence toujours un produit du référentiel.
- Côté ERP, RGPD : `ouvrier_id` n'est jamais stocké en clair : il est transformé à l'ingestion en hash salé, puis stocké dans une colonne dédiée de type chaîne (`ouvrier_hash`).

## 4. Stratégie de gestion des doublons

> Comment gérez-vous les doublons à l'ingestion ? `INSERT OR IGNORE` SQL,
> upsert applicatif, dédup pandas avant insertion ?

**Choix** : dédup pandas avant insertion

**Argument** : ça permet de les regrouper en une seule ligne (utile pour le CSV capteurs IoT qui a 2 % de doublons natifs :))

## 5. Gestion du capteur défaillant Roubaix L3

> DÉCIDER du sort du capteur défaillant Roubaix L3 (écarter / marquer / traiter en aval)
> et le documenter (cf. contrat + fiche modèle)

Nous avons choisit de le traiter en aval pour garder les données de température et de débit qui nous parraissent pas aberrantes et qui peuvent aider à l'entrainement du modèle.
Nous avons donc inséré null pour la donnée vibration car le modèle l'autorise.

## 6. Migration Alembic

> Documenter le rollback (alembic downgrade -1) et expliquer quand un rollback est nécessaire (migration boguée, déploiement à annuler), pas seulement la commande.

**Choix** : rollback contrôlé à une migration (downgrade -1) en cas d'incident : `alembic downgrade -1`

**Argument** :
- `alembic downgrade -1` fait revenir la BDD d'une révision Alembic en arrière (annule la dernière migration appliquée, via la fonction `downgrade()` du script de migration).
- `alembic downgrade 0db6ffca86dc` : fait revenir à la base `mesure_iot`.
- `alembic downgrade 0001` : fait revenir à la base initiale.
- `alembic upgrade head` : fait revenir ensuite au dernier état du projet.
- On l'utilise si la migration présente une erreur (erreur SQL, contrainte incohérente, type incorrect) ou si un déploiement doit être annulé.
- Avant rollback: sauvegarde de la BDD + vérification de l'impact (perte potentielle de données si la migration supprimait des colonnes/tables).
- Après rollback: correction du script, nouveau test, puis `alembic upgrade head` pour redéployer proprement.

## 7. Stratégie RGPD (si vous prenez ERP)

> Si vous prenez ERP : que faites-vous de `ouvrier_id` ?

- ☐ Suppression pure
- ☑ Hash salé (avec quel sel ?)
- ☐ Conservation pseudonymisée (justifier)

**Argument** :
- Nous choisissons le hash salé de `ouvrier_id` pour conserver une information exploitable par le modèle (effets opérateur potentiels) sans stocker de donnée personnelle en clair.
- Méthode : `ouvrier_id_hash = SHA-256(ouvrier_id + SALT_PROJET)`, avec `SALT_PROJET` secret stocké en variable d'environnement (jamais versionné, jamais loggé).
- Cette stratégie respecte le contrat (`hashé ou retiré, jamais en clair`) et le principe RGPD de minimisation : pas d'identifiant direct, seulement un pseudonyme technique nécessaire à l'usage analytique.

## 8. Stratégie de tests

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → les tables `mesures_iot` et `ordres_erp` existent : vérification du schéma attendu après création de la BDD dans `test_migration.py`.
2. Ingestion IoT valide et idempotente → vérification dans `test_ingest_iot.py` qu'un fichier avec doublon n'insère qu'une seule fois les mesures attendues et qu'une 2ème ingestion ne rajoute rien.
3. Ingestion ERP valide et conforme RGPD → vérification dans `test_ingest_erp.py` que les ordres sont insérés, que `ordre_id` reste unique, et que `ouvrier_id` n'est jamais stocké en clair mais sous forme de hash.
4. Ingestion fichier malformé → exception claire, BDD inchangée : test d'un fichier inexistant (`FileNotFoundError`) ou d'une ligne invalide (`IntegrityError`) sans insertion partielle.

## 9. Convention binôme

- Driver / Navigator switch toutes les **30 min** : ☑ oui ☐ adapté à...
- Tous les commits significatifs ont `Co-authored-by:` : ☑ oui ☐ ...
- Branche perso ou main partagée : main partagé

## 10. Conformité au contrat de données

> Confrontez votre livraison à `ressources/contrat_donnees_modele.md`. Pour
> chaque clause de qualité **honorée** : laquelle, comment, et **où** dans le
> code. (Documenté ici — c'est ce que vous montrez au RDV vendredi.)

| Clause du contrat | Honorée | Comment / où dans le code |
|---|---|---|
| Unicité respectée (ingestion idempotente) | ☑ | Contrainte composite `timestamp + sensor_id` sur `mesures_iot`, avec ingestion idempotente via déduplication avant insertion. À déclarer dans `src/models.py` puis dans la migration Alembic. |
| Manquants traités explicitement | ☑ | `vibration_mms` reste nullable, `temperature_c` et `debit_uh` sont conservés non nuls. La stratégie de nettoyage est appliquée à l'ingestion et couverte par les tests. |
| Capteur défaillant Roubaix L3 : repéré + décision tracée (écarter / marquer / aval) *(option A)* | ☑ | Les valeurs aberrantes du capteur Roubaix L3 sont repérées à l'ingestion mise à `null` selon la règle documentée dans le pipeline, la décision est tracée dans `decisions.md`. |
| `ouvrier_id` hashé ou retiré, jamais en clair *(option B)* | ☑ | `ouvrier_id` est pseudonymisé par hash salé avant insertion en base, puis stocké dans une colonne dédiée de type chaîne (`ouvrier_hash`) sans conserver la valeur brute. Cette règle doit être appliquée dans le pipeline d'ingestion ERP et vérifiée par les tests. |
| Types conformes (DateTime, numériques typés) | ☑ | `timestamp` en `DateTime`, `line_id` en `Integer`, `temperature_c` / `vibration_mms` / `debit_uh` en `Float`, à aligner dans `src/models.py` et la migration. |

---

*Décisions tracées par le binôme `Théo` × `Romain` — `01/07/2026`.*
