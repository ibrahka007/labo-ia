# AGENTS.md — Règles du projet labo-ia

Fichier destiné à tout agent travaillant sur ce dépôt (OpenCode, Copilot).
Claude lit `CLAUDE.md`, qui pointe vers ce fichier.

## Nature du projet

Laboratoire local de comparaison documentaire, de recherche RAG et d'analyse
d'impact. Dépôt public : https://github.com/ibrahka007/labo-ia
Suivi : https://github.com/users/ibrahka007/projects/1

## Règles non négociables

- **Tout est local.** Aucune API cloud, aucun Docker. Ollama + Qdrant local,
  SQLite FTS5 pour l'index lexical. Ne jamais proposer un service distant.
- **Le corpus est entièrement fictif.** Le dépôt est public : ne jamais y
  versionner de donnée réelle, de nom, d'extrait de document interne.
- **Aucun jeton exposé**, aucun `push --force`, aucune suppression d'issue,
  de branche ou de projet sans confirmation explicite.
- **Le moteur d'impact ne modifie jamais un document.** Il produit un rapport ;
  seul le fichier demandé via `--sortie` est écrit. Validation humaine requise.
- **Pas de complexité sans gain mesuré.** Une fonctionnalité n'est conservée
  que si elle améliore un cas mesuré sans en dégrader un autre.
- **Langue : français** — code, commentaires, documentation, messages de commit.

## Environnement

- Python de test : `python3` (suffisant pour `rag/`, `impact/`, `premier-test/`).
- Dépendances lourdes (Qdrant, Ollama, python-docx) : `premier-test/.venv/bin/python`.
- Modèles Ollama : `bge-m3` (embeddings, 1024 dims, digest `790764642607`),
  `gemma4:12b` (présent, **non utilisé** : aucune génération de réponse).

## Commandes vérifiées

```bash
# Tests (68 au total)
python3 -m unittest discover -s rag/tests                    # 39
python3 -m unittest discover -s impact/tests                 # 22
python3 -m unittest discover -s premier-test -p "test_*.py"  # 7

# Indexation et recherche
premier-test/.venv/bin/python rag/index_corpus.py
premier-test/.venv/bin/python rag/search.py "question" --mode dense
premier-test/.venv/bin/python rag/evaluer.py --comparer
premier-test/.venv/bin/python rag/calibrer_seuil.py

# Analyse d'impact
premier-test/.venv/bin/python impact/analyser.py --changement "..."

# Document qualité (seul écrivain du .docx)
premier-test/.venv/bin/python premier-test/generer_doc_qualite.py
```

## Architecture

| Dossier | Rôle |
| --- | --- |
| `premier-test/` | prototype de comparaison, générateur du document qualité |
| `rag/` | `rag_lib` (découpage, embeddings, seuil), `index_corpus`, `search`, `evaluer`, `calibrer_seuil`, `lexical`, `hybrid` |
| `impact/` | `moteur.py` (diff, qualification), `analyser.py` (CLI) |
| `corpus/` | 22 fichiers, **20 indexés** (`README.md` et `annotations/` exclus), 143 chunks |
| `.opencode/agent/` | six sous-agents spécialisés |

Le document qualité n'est jamais édité à la main : il est régénéré par
`premier-test/generer_doc_qualite.py` vers
`/Users/ibrahimkamate/Downloads/AI_PROJECT/Quality Doc AI Project.docx`
(auteur : Ibrahim Kamate). Le script est versionné, le `.docx` ne l'est pas.

## État mesuré — à ne pas surinterpréter

- Seuil d'abstention `SEUIL_ABSTENTION = 0,65` dans `rag/rag_lib.py`.
- Jeu d'évaluation : 5 questions avec réponse, 13 hors corpus.
  **Dense, lexical et hybride sont au plafond** (5/5, MRR 1,000), donc ce jeu
  ne mesure aucune différence entre les modes. Ne pas en conclure qu'un mode
  est meilleur.
- La marge de 0,001 du seuil (C4 = 0,651 contre C6 = 0,650) est un artefact
  d'annotation, pas une propriété du modèle : les 12 autres négatifs sont
  tous ≤ 0,537.
- Le mode lexical **ne calcule pas d'abstention** (`evaluer.py`), et les jetons
  d'un seul caractère sont supprimés : « 2 jours » et « 5 jours » sont
  indiscernables pour ce canal.
- L'hybride n'apporte aucun gain mesuré : il reste disponible, **non activé
  par défaut**.

## Dette connue

- Annotations à corriger dans `corpus/annotations/cas_de_test.md` :
  C2 renvoie à une section 8 inexistante (la conservation est en §6) ;
  C4 n'est pas une contradiction (RH-005 parle d'entretiens de suivi) ;
  C5 compare un renouvellement de milieu à un passage avant congélation.
- C6 : le corpus contient bien une règle RH, mais marquée « hypothèse à
  confirmer ». C'est une réserve, pas une absence de preuve.

## Conventions de travail

- Une seule source fait autorité par type de fait : « ce qui a été fait » →
  document qualité ; « ce qui reste » → board ; « comment ça marche » → code
  et tests ; « pourquoi » → issues.
- Un brainstorming externe (projet Claude, Copilot) est une **hypothèse**.
  Il ne devient une décision qu'après une issue avec critères mesurables.
- Board : statuts Backlog, Ready, In progress, In review, Done ; champs
  Priorité (P0–P2) et Taille (XS–XL).
- Ne pas créer de sous-agent sans vérifier qu'il se charge réellement
  (une valeur `color` invalide le fait ignorer silencieusement).
