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

# 2. Interroger l'index
premier-test/.venv/bin/python rag/search.py "Quel est le délai de déclaration d'un écart ?"

# 3. Évaluer le rappel sur les cas C1–C6
premier-test/.venv/bin/python rag/evaluer.py
```

## Fonctionnement

- Découpage par section `##`, avec métadonnées (id, version, statut, domaine,
  fichier, section).
- Les sections longues sont découpées en fenêtres de 1600 caractères.
- Exclusions : `corpus/README.md` et `corpus/annotations/`.
- L'index est persistant dans `rag/index_qdrant/` et reconstruit à chaque
  exécution d'`index_corpus.py`.
- `rag/index_meta.json` enregistre le modèle, la dimension et le nombre de chunks.

## Limites

- Recherche dense uniquement : pas encore de recherche lexicale ni de reranker.
- Aucun seuil d'abstention calibré : les scores servent d'observation.
- Les documents image (scans) ne sont pas couverts sans OCR.
- Ne pas utiliser en production : corpus fictif et validation humaine requise.
