# Pair-coding Git en binôme — Mini-cours

> Brief associé : M3-B2 (premier vrai brief en pair-coding sur code partagé)
> Durée de lecture + pratique : ~15 min
> Pré-requis : Git de base (clone, commit, push, branches).

## Pourquoi cette techno ?

En M2-B2, vous avez bossé en **binôme** mais l'async était individuel.
Vous avez vu `Co-authored-by:` comme convention. **C'était l'échauffement.**

En M3-B2, c'est un **vrai pair-coding** : vous codez **sur le même code
partagé**, vous **switchez driver/navigator** régulièrement, vous mergez
vos contributions sur **un seul repo binôme**.

Trois pratiques à acquérir :

1. **Driver / Navigator** : un seul code, l'autre relit, conteste, documente
2. **`Co-authored-by:`** : convention Git pour signaler que 2 personnes ont
   produit ensemble
3. **Branches courtes + merges propres** : éviter le bordel des conflits

**Pourquoi c'est central** : en M5 (CI/CD), M6 (brief groupe entier), M7
et M8 vous serez encore en collaboration. Installer ces réflexes
maintenant = ça paye 4 fois.

## Concepts clés

### Driver / Navigator

- **Driver** : la personne au clavier. **Une seule à la fois.**
- **Navigator** : la personne qui regarde l'écran partagé, **conteste**
  les choix, ouvre la doc, vérifie les types. **Pas** la personne qui
  scroll Slack — elle est **active**.
- **Switch** : tous les **30 min**, on échange. Sans switch, le navigator
  décroche en 10 min.
- **Règle d'or** : *« si je ne comprends pas ce que tu fais, on s'arrête
  et on en parle »*.

### `Co-authored-by:`

GitHub reconnaît un commit comme **co-écrit** quand le message contient :

```
feat(ingest): script ingest_iot avec idempotence

Co-authored-by: Alice Dupont <alice@example.com>
```

Format strict :
- **Ligne vide** avant `Co-authored-by:`
- `Co-authored-by:` (avec deux-points)
- Nom + email **valide** (de préférence celui du profil GitHub)
- 1 ligne par co-auteur

GitHub affiche les 2 (ou +) avatars sur le commit, le contributeur compte
dans les stats des 2 profils.

### Configuration des emails

Pour que `Co-authored-by:` lie au profil GitHub :
- Utilise l'email **enregistré sur ton profil GitHub** (Settings → Emails)
- Tu peux aussi utiliser ton email "no-reply" GitHub (style
  `12345+username@users.noreply.github.com`)

### Branches en binôme

- En sync (mercredi) : commits sur `main` directement, OK (vous êtes 2
  sur le même clavier de facto)
- En async (jeudi/vendredi) : **chacun sur sa branche** si vous bossez en
  parallèle, puis merge sur main. Si toujours en pair-coding voix → main
  directement OK.

## Exemple minimal qui tourne

### Setup binôme à 9h15 mercredi

```bash
# Tirage formatrice : Alice + Bob
# Alice crée le repo depuis le template
# Sur github.com :
#   "Use this template" → "Create a new repository"
#   Nom : M3-B2-acerox-alice-bob
#   Owner : alice
#   Privé OK

# Alice ajoute Bob comme collaborateur :
# Settings → Collaborators → Add Bob

# Les deux clonent
git clone git@github.com:alice/M3-B2-acerox-alice-bob.git
cd M3-B2-acerox-alice-bob

# Chacun configure son identité locale
git config user.name "Alice Dupont"     # ou Bob
git config user.email "alice@..."        # ou Bob
```

### Premier commit binôme

```bash
# Alice est driver (share son écran sur Discord vocal)
# Bob est navigator (relit, ouvre la doc, vote)
# Ils éditent ensemble src/models.py

git add src/models.py
git commit -m "feat(models): add <table> table

Co-authored-by: Bob Martin <bob@email.com>"

git push
```

### Switch driver après 30 min

```bash
# Bob prend le clavier (share son écran)
# Alice devient navigator
# Rien à changer dans Git — juste qui code.
# Prochain commit :

git commit -m "feat(ingest): script ingest_iot idempotent

Co-authored-by: Alice Dupont <alice@example.com>"
```

### Async — branche dédiée par sujet

```bash
# Alice travaille sur les tests, Bob travaille sur le README
# Ils créent chacun leur branche
git checkout -b tests/alice
# ... commits ...
git push -u origin tests/alice

# Bob de son côté
git checkout -b docs/readme-bob
# ... commits ...
git push -u origin docs/readme-bob

# Pull request, review croisée, merge sur main
# (ou merge direct si vous êtes pressés et confiants)
```

## Exercice guidé (à 9h15 mercredi avec ton binôme)

1. Choisissez **qui est owner** du repo
2. L'owner crée le repo depuis le template + invite l'autre
3. Les deux clonent + configurent leur identité git locale
4. Faites votre **premier commit duo** :
   - Le driver édite `decisions.md` (votre choix de source)
   - Commit avec `Co-authored-by:`
5. Vérifiez sur GitHub que le commit affiche **2 avatars**

Si ce premier commit duo passe, le reste suit. Si bloqué > 10 min, demande
à Marianne — c'est plus simple que de bloquer.

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Deux drivers en parallèle (2 écrans, 2 codes) | Merges en pagaille au bout de 30 min |
| Pas de switch — l'un code tout | CT9 ratée, l'autre décroche |
| `Co-authored-by:` mal formaté | GitHub ne l'affiche pas |
| Email perso vs email no-reply GitHub | Lien profil ne marche pas |
| Push direct sur le main du commun en async **sans s'être prévenu** | L'autre écrase ton travail |
| Branche `tests/alice` qui dure 2 jours | Conflits énormes au merge — vise des PR courtes |

**Symptôme → cause probable** :

| Symptôme | Cause probable |
|---|---|
| GitHub n'affiche pas le 2ᵉ avatar | Ligne vide manquante avant `Co-authored-by:` |
| Bob ne peut pas push | Pas invité comme collaborateur — Alice doit l'inviter en Settings |
| Conflit énorme au merge | Branche trop longue OU push sans pull — toujours `git pull --rebase` avant push |
| Le commit montre `unknown user` au lieu du nom Bob | Email pas matching avec profil GitHub Bob — vérifie Settings → Emails |
| `git push` refusé | Pas de droit, ou besoin de `--force-with-lease` après rebase |

## Pour aller plus loin

- **GitHub Docs — Co-authored commits** : <https://docs.github.com/fr/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors>
- **Atlassian — Pair programming** : <https://www.atlassian.com/agile/software-development/pair-programming>
- **`git mob`** (bonus pour qui aime les CLI) : <https://github.com/findmypast-oss/git-mob>
  (ajoute automatiquement `Co-authored-by:` — pas imposé en M3, mais
  élégant)

## Vérification (checklist binôme)

- [ ] Repo binôme créé, l'autre est collaborateur
- [ ] Au moins **3 commits significatifs** avec `Co-authored-by:` correct
- [ ] GitHub affiche **2 avatars** sur ces commits
- [ ] Le binôme a **switché** driver/navigator au moins **2 fois** dans la sync
- [ ] En async, si branche perso : push + merge propre sur main
