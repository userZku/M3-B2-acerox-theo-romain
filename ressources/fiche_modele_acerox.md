# Fiche modèle — « Prédicteur NC » Acerox (existant)

> Brief associé : **M3-B2**
> Nature : **document fourni par Acerox** — lecture seule, ~5 min.
> Pré-requis : avoir fait M3-B1 (identification des sources).

> ⚠️ **Cadre.** Ce modèle **existe déjà** et tourne **en production chez
> Acerox**. Vous ne le concevez pas, ne l'entraînez pas, ne le modifiez pas
> (ce sera l'objet de M4 → choix de modèle, M5/M6 → entraînement). Cette
> fiche existe pour une seule raison : **savoir pour qui vous préparez les
> données**. C'est votre client interne.

## À quoi sert le modèle

| | |
|---|---|
| **Nom interne** | Prédicteur NC (non-conformité qualité) |
| **Propriétaire** | équipe modèle Acerox (pas FastIA) |
| **Statut** | en production, site Roubaix en priorité |
| **Objectif métier** | estimer le **risque de défaut qualité** sur **Roubaix ligne 3**, ~**24 h à l'avance**, pour déclencher une maintenance *avant* le défaut |

## Entrées / Sortie

- **Entrée** : une **table de conditions machine + contexte de production**, propre et conforme au schéma attendu. **C'est exactement ce que votre pipeline M3-B2 doit livrer** → voir [`contrat_donnees_modele.md`](./contrat_donnees_modele.md).
- **Sortie** : un **score de risque NC** entre 0 et 1, comparé à un seuil → alerte maintenance. (Le seuil et son calibrage, c'est **M6** — pas votre sujet ici.)

## Données d'entraînement (ce que vous n'avez PAS)

Le modèle a été entraîné chez Acerox sur un **historique de tickets qualité étiquetés** (conforme / non-conforme). Cet historique **n'a pas été transmis à FastIA** et **ne figure dans aucune des sources** que vous manipulez.

> 🎯 **C'est le point qui déroute.** Vous ne cherchez **pas** une « colonne à
> prédire » dans les capteurs ou l'ERP : la cible (le label NC) vit chez
> Acerox. Vous, vous préparez les **données d'entrée** (features) que le
> modèle consomme. *« Où est l'historique étiqueté des NC ? »* est d'ailleurs
> une **bonne question à poser à Acerox** — pas un trou dans votre travail.

## Réentraînement

Fréquence : **à clarifier avec Acerox** (impacte la stratégie d'ingestion :
batch quotidien suffisant, ou flux plus fréquent ?). Reste un point ouvert
hérité de M3-B1.

## Limites connues (et pourquoi ça vous concerne)

| Limite | Conséquence pour votre pipeline |
|---|---|
| **Capteur Roubaix L3 défaillant** (T° 140-160 °C, vibration figée à 12.0) | Si vous insérez ces mesures **sans les repérer**, vous **empoisonnez** un modèle qui tourne déjà : *garbage in → garbage out*. Vous devez les **repérer** et **décider** de leur sort (exclure / marquer / traiter en aval), puis le **justifier** dans `decisions.md`. |
| Pas d'accès au code du modèle | Vous travaillez **au contrat** (schéma d'entrée), pas à l'implémentation. |
| Dérive possible dans le temps | Hors-scope M3 ; sujet **M6** (amélioration continue). |

## Ce que ça change pour M3-B2 (en une phrase)

> La fiabilité d'une IA **déjà en production** dépend directement de la
> **qualité des données que vous lui livrez**. Préparer les données n'est pas
> de la plomberie : c'est une **décision qui engage le modèle**.

---

*Fiche fournie dans le cadre du brief M3-B2 ATOS — modèle existant Acerox.*