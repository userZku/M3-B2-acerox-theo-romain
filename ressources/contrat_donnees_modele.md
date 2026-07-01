# Contrat de données — ce que le modèle attend en entrée

> Brief associé : **M3-B2**
> Nature : **spécification fournie par l'équipe modèle Acerox** — c'est votre
> **cible de livraison**, pas une suggestion.
> Pré-requis : [`fiche_modele_acerox.md`](./fiche_modele_acerox.md) (savoir à qui vous livrez).

## Pourquoi un contrat de données ?

Vous ne préparez pas des données « en général » : vous les préparez **pour un
consommateur précis** (le Prédicteur NC Acerox). Un **contrat de données**
(*data contract*) fige ce que ce consommateur exige : **structure, types,
contraintes de qualité**. Tant que votre table respecte le contrat, le modèle
peut la consommer. C'est la pratique réelle en industrialisation (l'ancêtre du
*feature store*).

> 🎯 Le contrat décrit **les entrées (features)** du modèle. Il **ne contient
> pas** la cible (le label NC) : celle-ci reste chez Acerox (cf. fiche modèle).
> Votre job = livrer une table **conforme**, pas trouver une variable à prédire.

## Le contrat, selon la source que votre binôme intègre

Vous intégrez **une** des deux sources (cf. `decisions.md`). Voici la table
cible attendue dans la BDD pivot pour chacune.

> 🛠️ **Ceci est une spécification, pas du code.** À vous de la **traduire** en
> modèle SQLAlchemy dans `src/models.py` — **imitez la table `Produit`** déjà
> présente (types `Column`, `UniqueConstraint`, `ForeignKey`, `index`). On ne
> vous donne pas la classe toute faite : l'écrire à partir du contrat, **c'est
> le cœur du brief**.

### Option A — source `capteurs_iot.csv` → table `mesures_iot`

Champs disponibles et **type attendu** en base :

| Champ | Type | Sens |
|---|---|---|
| `timestamp` | DateTime | horodatage de la mesure |
| `site` | str | site de production |
| `line_id` | int | ligne |
| `sensor_id` | str | capteur émetteur |
| `temperature_c` | float | température (°C) |
| `vibration_mms` | float | vibration (mm/s) |
| `debit_uh` | float | débit (u/h) |

### Option B — source `erp_export.json` → table `ordres_erp`

| Champ | Type | Sens |
|---|---|---|
| `ordre_id` | int | identifiant de l'ordre |
| `produit_ref` | str | produit fabriqué |
| `site` | str | site |
| `line_id` | int | ligne |
| `date_lancement` | DateTime | début de l'ordre |
| `date_fin_prevue` | DateTime | fin prévue |
| `statut` | str | état de l'ordre |
| `ouvrier_id` | str | ⚠️ **donnée personnelle** (opérateur) |
| `quantite_kg` | int | quantité produite |

> ⚠️ Le `statut` ERP (`termine`/`suspendu`/…) est l'**état de l'ordre**,
> **pas** la conformité qualité. Ce n'est pas un label NC.

## Ce que le modèle exige — à vous de le traduire en contraintes

> Le contrat exprime un **besoin métier**. La traduction technique (clé
> d'unicité, index, clé étrangère, nullable, traitement RGPD) est **votre
> travail de conception** : choisissez-la, déclarez-la dans `models.py`, et
> **justifiez-la dans `decisions.md`**. C'est le cœur du niveau *transposer*.

**Option A — mesures IoT :**
- Une mesure est **identifiée de façon unique** par son **horodatage + son capteur**. → quelle contrainte en base ?
- Le modèle interroge surtout les mesures **par période** (`timestamp`). → quoi pour que ces requêtes restent rapides ?
- La **vibration peut manquer** (capteur momentanément muet), c'est toléré ; température et débit sont **toujours présents**. → que rendez-vous *nullable* ou non ?

**Option B — ordres ERP :**
- Chaque **ordre a un identifiant unique** (`ordre_id`), souvent recherché tel quel. → unicité ? index ?
- Chaque ordre **porte sur un produit du référentiel `produits`**. → quel lien déclarer entre les deux tables ?
- `ouvrier_id` est une **donnée personnelle** qui ne doit **jamais** être stockée en clair. → qu'en faites-vous à l'ingestion (et quel type de colonne en résulte) ?

## Clauses de qualité (communes, non négociables)

Ces règles sont la raison d'être de votre étape de nettoyage — chaque clause
doit être **honorée dans le code** et **justifiée dans `decisions.md`** :

1. **Unicité respectée** : aucun doublon sur la clé (ingestion **idempotente** — relancer n'ajoute rien).
2. **Manquants traités** : explicitement (drop, valeur par défaut, ou conservation `null` assumée) — jamais ignorés en silence.
3. **Capteur défaillant — décision documentée** (option A) : les mesures aberrantes du capteur **Roubaix L3** (T° 140-160 °C, vibration figée à 12.0) doivent être **repérées** et faire l'objet d'une **décision tracée** (les écarter à l'ingestion, les marquer, ou conserver le brut et traiter en aval). Les insérer sans s'en apercevoir = risque d'empoisonner le modèle (cf. fiche modèle).
4. **RGPD** (option B) : `ouvrier_id` **hashé ou retiré**, jamais inséré en clair. Principe de **minimisation**.
5. **Types conformes** : timestamps en `DateTime` (pas en `str`), numériques typés — pas de colonne `object` fourre-tout.

## Définition de « conforme » (ce que vérifie le modèle / vos tests)

Votre livraison est **conforme** si :

- [ ] La table cible existe (via migration Alembic) avec les **types** ci-dessus.
- [ ] La contrainte d'**unicité** est en base et tient (réingestion = 0 doublon).
- [ ] Les **manquants** ont une stratégie appliquée et tracée.
- [ ] (Option A) le sort du capteur défaillant Roubaix L3 est **décidé et documenté** (écarter / marquer / traiter en aval).
- [ ] (Option B) aucune valeur `ouvrier_id` en clair n'est présente.
- [ ] Vos **tests pytest** vérifient au moins l'unicité et le rejet d'un fichier malformé.

> Si une case n'est pas cochée, la donnée **n'est pas livrable au modèle** —
> même si « le script tourne ». *Ça charge* ≠ *c'est conforme*.

---

*Contrat fourni dans le cadre du brief M3-B2 ATOS — entrées du modèle Acerox.*