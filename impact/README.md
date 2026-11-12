# Moteur d'analyse d'impact

Prend un changement documentaire et liste les passages du corpus qui risquent
d'être concernés — avec citation, qualification et niveau de confiance.

**Le moteur ne modifie jamais un document.** Il produit un rapport ; l'humain
valide.

## Usage

```bash
# 1. Changement décrit directement, dans sa forme cible
premier-test/.venv/bin/python impact/analyser.py \
  --changement "Ouvrir la fiche d'écart sous 24 heures après identification"

# 2. Comparaison de deux versions (diff -> changements -> impacts)
premier-test/.venv/bin/python impact/analyser.py \
  --avant corpus/versions/PHA-001_v1.0.md \
  --apres corpus/sante_pharma/PHA-001_gestion_ecarts.md

# 3. Rapport Markdown
premier-test/.venv/bin/python impact/analyser.py \
  --changement "..." --sortie impact/rapports/analyse.md
```

Options utiles : `--mode dense|hybride`, `--seuil`, `--top`.

## Qualification des passages

| Type | Signification |
| --- | --- |
| `aligné` | Le passage énonce déjà la nouvelle valeur, avec un contexte comparable |
| `à mettre à jour` | Le passage reprend la règle avec une valeur différente |
| `réserve` | Le passage présente la valeur comme une hypothèse à confirmer |
| `à vérifier` | Recouvrement partiel : la portée du changement reste à établir |
| `preuve insuffisante` | Aucun passage au-dessus du seuil : ne rien conclure |

Règles de décision :

- les métadonnées et les titres Markdown sont ignorés (ils changent à chaque
  version sans modifier une règle) ;
- un nombre identique ne suffit pas : « 5 ans » pour les écarts qualité et
  « 5 ans » pour les dossiers RH sont deux règles distinctes, donc la
  couverture des termes doit aussi être suffisante ;
- un passage portant une réserve prime sur toute autre qualification.

## Codes de sortie

| Code | Sens |
| --- | --- |
| 0 | Analyse produite |
| 2 | Arguments invalides ou index absent |
| 3 | Document introuvable ou illisible |

Une abstention (« preuve insuffisante ») n'est pas une erreur : elle sort en 0
avec la mention explicite dans le rapport.

## Limites

- Le diff travaille ligne à ligne : une reformulation complète peut produire
  beaucoup de changements.
- Aucune équivalence d'unités (« 1 jour » n'est pas reconnu comme « 24 heures »).
- Pas de détection de contradiction entre deux documents du corpus.
- Validation humaine obligatoire avant toute modification.
