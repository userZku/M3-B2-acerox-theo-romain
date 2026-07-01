# Decisions — Binôme `<prénom1>` × `<prénom2>` (M3-B2 Acerox)

> Document à compléter à 2 pendant la phase sync (15 min avant de coder).
> Servira de référence pendant la phase async + RDV vendredi.

## 1. Source choisie pour l'ingestion

> Quelle source intégrez-vous en M3-B2 ? Argumentez en 3 lignes max.

**Choix** : ☑ `capteurs_iot.csv` (CSV ~51k lignes) ☐ `erp_export.json` (JSON ~2k ordres)

**Argument** :
- Lors de M3-B1 on pensait tous les deux ne pas utiliser ERP comme source d'entrainement mais plus comme source d'enrichissement
- IOT contient les données industrielles sur l'état des capteurs : ça devrait être suffisant pour déterminer dans un premier temps le defaut qualité

## 2. Stratégie de gestion des doublons

> Comment gérez-vous les doublons à l'ingestion ? `INSERT OR IGNORE` SQL,
> upsert applicatif, dédup pandas avant insertion ?

**Choix** : dédup pandas avant insertion

**Argument** : ça permet de les regrouper en une seule ligne (utile pour le CSV capteurs IoT qui a 2 % de doublons natifs :))

## 3. Stratégie RGPD (si vous prenez ERP)

> Si vous prenez ERP : que faites-vous de `ouvrier_id` ?

- ☐ Suppression pure
- ☐ Hash salé (avec quel sel ?)
- ☐ Conservation pseudonymisée (justifier)

**Argument** : inutile dans notre cas

## 4. Stratégie de tests

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → la table existe : vérification que la table attendue existe après création du schéma
2. Ingestion d'un fichier valide → N lignes insérées sans doublon : vérification qu'aucune insertion en BDD ne se produit à la 2ème insertion
3. Ingestion fichier malformé → exception claire, BDD inchangée : vérification de la bonne réception d'un exception claire et que la BDD est inchangée

## 5. Convention binôme

- Driver / Navigator switch toutes les **30 min** : ☑ oui ☐ adapté à...
- Tous les commits significatifs ont `Co-authored-by:` : ☑ oui ☐ ...
- Branche perso ou main partagée : main partagé

## 6. Conformité au contrat de données

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
