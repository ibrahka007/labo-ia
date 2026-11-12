# RAG local — indexation du corpus

Pipeline minimal : chunks Markdown → embeddings Ollama (`bge-m3`) → Qdrant local
(sans serveur, sans Docker) → recherche sémantique.

## Prérequis

- Ollama démarré sur `http://127.0.0.1:11434`.
- Modèle d'embeddings : `ollama pull bge-m3` (1,2 Go, 1024 dimensions).
- Dépendances installées dans `premier-test/.venv` : `qdrant-client`, `numpy` (et
  `pypdf`, `python-docx` pour les autres scripts).

## Commandes

Depuis la racine `labo-ia/` :

```bash
# 1. Construire l'index
premier-test/.venv/bin/python rag/index_corpus.py

# 2. Interroger l'index (dense par défaut)
premier-test/.venv/bin/python rag/search.py "Quel est le délai de déclaration d'un écart ?"

# 2b. Mode hybride (dense + lexical) ou lexical seul
premier-test/.venv/bin/python rag/search.py "question" --mode hybride
premier-test/.venv/bin/python rag/search.py "question" --mode lexical

# 3. Évaluer le rappel et l'abstention sur C1–C6
premier-test/.venv/bin/python rag/evaluer.py

# 4. Recalibrer le seuil d'abstention
premier-test/.venv/bin/python rag/calibrer_seuil.py

# 5. Comparer dense / lexical / hybride
premier-test/.venv/bin/python rag/evaluer.py --comparer
```

## Fonctionnement

- Découpage par section `##`, avec métadonnées (id, version, statut, domaine,
  fichier, section).
- Les sections longues sont découpées en fenêtres de 1600 caractères.
- Exclusions : `corpus/README.md` et `corpus/annotations/`.
- L'index est persistant dans `rag/index_qdrant/` et reconstruit à chaque
  exécution d'`index_corpus.py`.
- `rag/index_meta.json` enregistre le modèle, la dimension et le nombre de chunks.

## Recherche hybride

Trois modes, sélectionnables par `--mode` :

| Mode | Principe | Abstention |
| --- | --- | --- |
| `dense` (défaut) | similarité cosinus bge-m3 | seuil 0,65 |
| `lexical` | BM25 SQLite FTS5, couverture de termes | non calibrée (diagnostic) |
| `hybride` | fusion RRF des deux canaux + reranker heuristique | seuil appliqué au score dense |

L'index lexical est un fichier SQLite (`rag/index_fts/corpus.sqlite`), construit
par `rag/index_corpus.py` et exclu de Git.

**Résultat mesuré sur les 18 cas** : aucun gain mesurable de l'hybride par
rapport au dense (rappel 5/5, MRR 1,000, 13/13 abstentions dans les deux cas).
Le corpus est trop petit et le dense sature déjà. L'hybride reste donc
**désactivé par défaut** : il ne doit pas ajouter de complexité sans preuve.
La comparaison devra être refaite sur le jeu de 100 cas.

## Abstention

`search.py` refuse de répondre quand aucun passage n'atteint le seuil
`SEUIL_ABSTENTION` (0,65 par défaut, `rag_lib.py`). L'option `--seuil` permet de
le changer (`--seuil 0` désactive l'abstention).

Un second garde-fou signale les passages qui ne formulent pas une règle établie
(« hypothèse », « à confirmer », « sous réserve »…) : la valeur est alors
présentée comme à confirmer, jamais comme une obligation.

Mesure actuelle sur 18 cas (5 avec réponse, 13 hors corpus) : 5/5 réponses
conservées, 13/13 abstentions correctes. **La marge est faible** (0,651 pour le
cas légitime le plus bas, 0,650 pour le cas d'abstention le plus haut) : le seuil
est provisoire et doit être re-mesuré sur un jeu plus large.

## Limites

- Recherche dense uniquement : pas encore de recherche lexicale ni de reranker.
- Seuil d'abstention calibré sur 18 cas seulement : marge quasi nulle, à
  consolider sur le jeu de 100 cas avant tout usage décisionnel.
- Les documents image (scans) ne sont pas couverts sans OCR.
- Ne pas utiliser en production : corpus fictif et validation humaine requise.
