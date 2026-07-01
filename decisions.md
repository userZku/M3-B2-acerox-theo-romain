# Decisions — Binôme `<prénom1>` × `<prénom2>` (M3-B2 Acerox)

> Document à compléter à 2 pendant la phase sync (15 min avant de coder).
> Servira de référence pendant la phase async + RDV vendredi.

## 1. Source choisie pour l'ingestion

> Quelle source intégrez-vous en M3-B2 ? Argumentez en 3 lignes max.

**Choix** : ☑ `capteurs_iot.csv` (CSV ~51k lignes) ☐ `erp_export.json` (JSON ~2k ordres)

**Argument** :
- Lors de M3-B1 on pensait tous les deux ne pas utiliser ERP comme source d'entrainement mais plus comme source d'enrichissement
- IOT contient les données industrielles sur l'état des capteurs : ça devrait être suffisant pour déterminer dans un premier temps le defaut qualité

## 2. Réflexe de stockage

> Pourquoi une BDD relationnelle SQLite ici, et dans quel cas du document MongoDB ou du fichier Parquet ?
> S'appuyer sur la grille de décision Stockage & échelle

**Choix** : BDD relationnelle SQLite :)

**Argument** : 
- Données structurée (lignes/colonnes, schéma stable) donc BDD relationnelle suffit. 
- Les logs IOT demandent des écritures fréquentes.
- Volume des logs < 1 Go (3Mo sur un mois), même sur du temps réel les données tiennent ne RAM.

## 3. Stratégie de gestion des doublons

> Comment gérez-vous les doublons à l'ingestion ? `INSERT OR IGNORE` SQL,
> upsert applicatif, dédup pandas avant insertion ?

**Choix** : dédup pandas avant insertion

**Argument** : ça permet de les regrouper en une seule ligne (utile pour le CSV capteurs IoT qui a 2 % de doublons natifs :))

## 4. Stratégie RGPD (si vous prenez ERP)

> Si vous prenez ERP : que faites-vous de `ouvrier_id` ?

- ☐ Suppression pure
- ☐ Hash salé (avec quel sel ?)
- ☐ Conservation pseudonymisée (justifier)

**Argument** : inutile dans notre cas

## 5. Stratégie de tests

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → la table existe : vérification que la table attendue existe après création du schéma
2. Ingestion d'un fichier valide → N lignes insérées sans doublon : vérification qu'aucune insertion en BDD ne se produit à la 2ème insertion
3. Ingestion fichier malformé → exception claire, BDD inchangée : vérification de la bonne réception d'un exception claire et que la BDD est inchangée

## 6. Convention binôme

- Driver / Navigator switch toutes les **30 min** : ☑ oui ☐ adapté à...
- Tous les commits significatifs ont `Co-authored-by:` : ☑ oui ☐ ...
- Branche perso ou main partagée : main partagé

## 7. Conformité au contrat de données

> Confrontez votre livraison à `ressources/contrat_donnees_modele.md`. Pour
> chaque clause de qualité **honorée** : laquelle, comment, et **où** dans le
> code. (Documenté ici — c'est ce que vous montrez au RDV vendredi.)

| Clause du contrat | Honorée ? | Comment / où dans le code |
|---|---|---|
| Unicité respectée (ingestion idempotente) | ☑ | Contrainte composite `timestamp + sensor_id` sur `mesures_iot`, avec ingestion idempotente via déduplication avant insertion. À déclarer dans `src/models.py` puis dans la migration Alembic. |
| Manquants traités explicitement | ☑ | `vibration_mms` reste nullable ; `temperature_c` et `debit_uh` sont conservés non nuls. La stratégie de nettoyage doit être appliquée à l'ingestion et couverte par les tests. |
| Capteur défaillant Roubaix L3 : repéré + décision tracée (écarter / marquer / aval) *(option A)* | ☑ | Les valeurs aberrantes du capteur Roubaix L3 sont repérées à l'ingestion et écartées ou marquées selon la règle documentée dans le pipeline ; la décision est tracée dans `decisions.md`. |
| `ouvrier_id` hashé ou retiré, jamais en clair *(option B)* | s.o. | Source IoT choisie, donc clause ERP hors périmètre. |
| Types conformes (DateTime, numériques typés) | ☑ | `timestamp` en `DateTime`, `line_id` en `Integer`, `temperature_c` / `vibration_mms` / `debit_uh` en `Float`, à aligner dans `src/models.py` et la migration. |

---

*Décisions tracées par le binôme `Théo` × `Romain` — `01/07/2026`.*
