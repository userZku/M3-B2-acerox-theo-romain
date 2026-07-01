# Decisions — Binôme `<prénom1>` × `<prénom2>` (M3-B2 Acerox)

> Document à compléter à 2 pendant la phase sync (15 min avant de coder).
> Servira de référence pendant la phase async + RDV vendredi.

## 1. Source choisie pour l'ingestion

> Quelle source intégrez-vous en M3-B2 ? Argumentez en 3 lignes max.

**Choix** : ☐ `capteurs_iot.csv` (CSV ~51k lignes) ☐ `erp_export.json` (JSON ~2k ordres)

**Argument** :
- ...
- ...
- ...

## 2. Stratégie de gestion des doublons

> Comment gérez-vous les doublons à l'ingestion ? `INSERT OR IGNORE` SQL,
> upsert applicatif, dédup pandas avant insertion ?

**Choix** : ...

**Argument** : ...

## 3. Stratégie RGPD (si vous prenez ERP)

> Si vous prenez ERP : que faites-vous de `ouvrier_id` ?

- ☐ Suppression pure
- ☐ Hash salé (avec quel sel ?)
- ☐ Conservation pseudonymisée (justifier)

**Argument** : ...

## 4. Stratégie de tests

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → la table existe : ...
2. Ingestion d'un fichier valide → N lignes insérées sans doublon : ...
3. Ingestion fichier malformé → exception claire, BDD inchangée : ...

## 5. Convention binôme

- Driver / Navigator switch toutes les **30 min** : ☐ oui ☐ adapté à...
- Tous les commits significatifs ont `Co-authored-by:` : ☐ oui ☐ ...
- Branche perso ou main partagée : ...

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

*Décisions tracées par le binôme `<prénom1>` × `<prénom2>` — `<date>`.*
