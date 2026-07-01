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

## 3. Exigences du contrat

- Clé d'unicité : qu'est-ce qui identifie une ligne ? => UniqueConstraint(`timestamp` + `sensor_id`)
- Index : quelle(s) colonne(s) sont filtrées souvent ? => timestamp, site, line_id, sensor_id : ces colonnes seront souvent utilisées dans les WHERE des requêtes.
- Nullable : quels champs peuvent légitimement manquer ? => vibration peut manquer (capteur momentanément muet)

## 4. Stratégie de gestion des doublons

> Comment gérez-vous les doublons à l'ingestion ? `INSERT OR IGNORE` SQL,
> upsert applicatif, dédup pandas avant insertion ?

**Choix** : dédup pandas avant insertion

**Argument** : ça permet de les regrouper en une seule ligne (utile pour le CSV capteurs IoT qui a 2 % de doublons natifs :))

## 5. Migration Alembic

> Documenter le rollback (alembic downgrade -1) et expliquer quand un rollback est nécessaire (migration boguée, déploiement à annuler), pas seulement la commande.

**Choix** : rollback contrôlé à une migration (downgrade -1) en cas d'incident : `alembic downgrade -1`

**Argument** :
- `alembic downgrade -1` fait revenir la BDD d'une révision Alembic en arrière (annule la dernière migration appliquée, via la fonction `downgrade()` du script de migration).
- On l'utilise si la migration présente une erreur (erreur SQL, contrainte incohérente, type incorrect) ou si un déploiement doit être annulé.
- Avant rollback: sauvegarde de la BDD + vérification de l'impact (perte potentielle de données si la migration supprimait des colonnes/tables).
- Après rollback: correction du script, nouveau test, puis `alembic upgrade head` pour redéployer proprement.

## 6. Stratégie RGPD (si vous prenez ERP)

> Si vous prenez ERP : que faites-vous de `ouvrier_id` ?

- ☐ Suppression pure
- ☐ Hash salé (avec quel sel ?)
- ☐ Conservation pseudonymisée (justifier)

**Argument** : inutile dans notre cas

## 7. Stratégie de tests

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → la table existe : vérification que la table attendue existe après création du schéma
2. Ingestion d'un fichier valide → N lignes insérées sans doublon : vérification qu'aucune insertion en BDD ne se produit à la 2ème insertion
3. Ingestion fichier malformé → exception claire, BDD inchangée : vérification de la bonne réception d'un exception claire et que la BDD est inchangée

## 8. Convention binôme

- Driver / Navigator switch toutes les **30 min** : ☑ oui ☐ adapté à...
- Tous les commits significatifs ont `Co-authored-by:` : ☑ oui ☐ ...
- Branche perso ou main partagée : main partagé

## 9. Conformité au contrat de données

> Confrontez votre livraison à `ressources/contrat_donnees_modele.md`. Pour
> chaque clause de qualité **honorée** : laquelle, comment, et **où** dans le
> code. (Documenté ici — c'est ce que vous montrez au RDV vendredi.)

| Clause du contrat | Honorée ? | Comment / où dans le code |
|---|---|---|
| Unicité respectée (ingestion idempotente) | ☐ | ... |
| Manquants traités explicitement | ☐ | ... |
| Capteur défaillant Roubaix L3 : repéré + décision tracée (écarter / marquer / aval) *(option A)* | ☐ / s.o. | ... |
| `ouvrier_id` hashé ou retiré, jamais en clair *(option B)* | ☐ / s.o. | ... |
| Types conformes (DateTime, numériques typés) | ☐ | ... |

---

*Décisions tracées par le binôme `Théo` × `Romain` — `01/07/2026`.*
