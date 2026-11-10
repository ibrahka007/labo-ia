# Corpus fictif — Laboratoire IA

> **Avertissement** : tous les documents de ce dossier sont **entièrement fictifs**.
> Entreprises, produits, autorités, délais et règles sont inventés pour l'exercice.
> Aucune valeur réglementaire, clinique ou juridique ne doit en être déduite.

## Objectif

Ce corpus sert de terrain d'entraînement pour :

- la comparaison de versions documentaires ;
- la détection de contradictions entre documents liés ;
- l'analyse d'impact (un changement dans un document affecte quels autres documents ?) ;
- l'évaluation du futur moteur RAG (recherche, citations, abstention).

## Structure

```
corpus/
├── README.md
├── index.csv
├── annotations/
│   └── cas_de_test.md
├── biologie/          BIO-001 à BIO-004
├── sante_pharma/      PHA-001 à PHA-005
├── rh/                RH-001 à RH-005
├── gouvernance_documentaire/  DOC-001 à DOC-004
└── versions/          PHA-001 v1.0 et v2.0 (paire de comparaison)
```

## Conventions

Chaque document commence par un bloc de métadonnées :

```
---
id: PHA-001
titre: ...
version: 1.0
statut: Approuvé
date_application: 2026-01-15
proprietaire: ...
domaine: Santé / Pharma
classification: Fictif — exercice
---
```

Les références croisées utilisent le format `[PHA-001]`, `[FRM-PHA-001]`.

## Anomalies volontaires

Le corpus contient des incohérences **intentionnelles**, documentées dans
`annotations/cas_de_test.md` :

| Anomalie | Documents concernés |
| --- | --- |
| Délai de déclaration d'écart : 2 jours vs 5 jours | PHA-001 / PHA-002 |
| Conservation : 5 ans vs 10 ans | PHA-003 / PHA-004 |
| Télétravail : 3 jours vs 2 jours | RH-001 / RH-002 |
| Recrutement : 3 entretiens vs 2 entretiens | RH-003 / RH-005 |
| Fréquence de passage cellulaire : 2 jours vs 3 jours | BIO-001 / BIO-002 |

Ces écarts ne doivent pas être « corrigés » sans mettre à jour les annotations :
ils constituent la vérité de référence des tests.

## Utilisation

1. Comparer `versions/PHA-001_v1.0.md` et `versions/PHA-001_v2.0.md`.
2. Chercher les passages devenus obsolètes dans les documents liés.
3. Vérifier que le système cite le document, la version et la section exacte.
4. Ne jamais conclure sans validation humaine.

## Limites

- Documents courts, en Markdown, sans tableaux complexes ni scans.
- Aucune donnée réelle, personnelle ou sensible.
- Les seuils et délais sont arbitraires et ne reflètent aucune réglementation.
