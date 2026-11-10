---
id: DOC-002
titre: Instruction de nommage des fichiers
version: 1.0
statut: Approuvé
date_application: 2026-01-10
proprietaire: Responsable documentation
domaine: Gouvernance documentaire
classification: Fictif — exercice
---

# DOC-002 — Instruction de nommage des fichiers

## 1. Objet

Uniformiser le nommage des documents décrits dans [DOC-001].

## 2. Format

```
<ID>_<titre_court>_v<version>.<extension>
```

Exemples :

- `PHA-001_gestion_ecarts_v1.0.md`
- `RH-003_recrutement_v1.2.md`

## 3. Règles

- Identifiant en majuscules, sans espace.
- Version au format `v<entier>.<entier>`.
- Pas de caractères accentués dans le nom de fichier.
- Le titre court utilise des underscores.

## 4. Versions

- Une nouvelle version majeure change le numéro avant la virgule.
- Une correction mineure change le numéro après la virgule.
- Le fichier obsolète n'est jamais supprimé avant archivage ([DOC-003]).

## 5. Contrôle

- Le propriétaire vérifie le nommage avant publication.
- Une non-conformité de nommage est signalée au responsable documentation.

## 6. Références

- [DOC-001] Procédure de gestion documentaire.
- [DOC-003] Procédure d'archivage.
