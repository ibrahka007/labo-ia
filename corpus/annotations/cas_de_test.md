# Cas de test et impacts attendus

> Hypothèses de travail à valider. Ce ne sont pas des vérités métier.

## Principe

Chaque cas part d'un changement dans un document source et décrit les documents
susceptibles d'être impactés. Le système devra retrouver ces documents et citer
les passages concernés ; l'humain valide ou rejette.

## C1 — Délai de déclaration d'un écart

- **Source** : PHA-001 v2.0, section 3.
- **Changement** : déclaration sous 1 jour ouvré au lieu de 2.
- **Impacts attendus** :
  - PHA-002 (formulaire) mentionne encore « 5 jours ouvrés » ;
  - PHA-005 (CAPA) rappelle le délai d'ouverture ;
  - PHA-001 v1.0 devient obsolète.
- **Piège** : PHA-002 ne contient pas « 2 jours » mais « 5 jours ». Une recherche
  littérale sur l'ancienne valeur échouerait : il faut comprendre la notion.

## C2 — Durée de conservation

- **Source** : PHA-001 v2.0, section 8.
- **Changement** : conservation portée de 5 à 10 ans.
- **Impacts attendus** :
  - PHA-003 indique 5 ans ;
  - DOC-003 (archivage) indique 5 ans avec une exception « données de santé » ;
  - PHA-004 indique déjà 10 ans : cohérent avec la v2, incohérent avec la v1.
- **Piège** : PHA-003 et DOC-003 sont tous deux à 5 ans mais pour des raisons
  différentes ; le système doit citer les deux passages.

## C3 — Télétravail

- **Source** : RH-001 (3 jours/semaine).
- **Contradiction** : RH-002 limite les équipes support à 2 jours/semaine.
- **Attendu** : signaler la contradiction et préciser le périmètre (équipes support).
- **Piège** : RH-002 est une exception légitime, pas nécessairement une erreur.

## C4 — Nombre d'entretiens de recrutement

- **Source** : RH-003 (3 entretiens).
- **Contradiction** : RH-005 (guide d'intégration) mentionne 2 entretiens.
- **Attendu** : impact documentaire sur RH-005, à corriger.

## C5 — Fréquence de passage cellulaire

- **Source** : BIO-001 (renouvellement du milieu tous les 2 jours).
- **Contradiction** : BIO-002 (congélation) mentionne un passage tous les 3 jours.
- **Attendu** : signaler l'écart et citer les sections concernées.

## C6 — Cas sans preuve suffisante

- **Question** : « Quel est le délai de conservation des dossiers RH ? »
- **Attendu** : le corpus ne contient pas de règle RH explicite de conservation.
  Le système doit s'abstenir plutôt qu'inventer une valeur.

## Critères d'évaluation proposés

| Dimension | Objectif |
| --- | --- |
| Rappel des documents impactés | ≥ 90 % sur C1–C5 |
| Précision | ≥ 85 % |
| Citations résolubles | 100 % |
| Abstention sur C6 | Oui |
| Distinction fait / hypothèse | Toujours explicite |
| Validation humaine | Obligatoire avant toute action |
