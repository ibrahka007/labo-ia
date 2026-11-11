"""Évalue le rappel du retrieval sur les cas C1 à C6 du corpus."""

from __future__ import annotations

import argparse
from pathlib import Path

from search import rechercher

CAS = [
    {
        "nom": "C1 — délai de déclaration d'écart",
        "question": "Quel est le délai pour déclarer un écart qualité ?",
        "attendus": {"PHA-001", "PHA-002"},
    },
    {
        "nom": "C2 — conservation des enregistrements",
        "question": "Quelle est la durée de conservation des enregistrements qualité ?",
        "attendus": {"PHA-003", "PHA-004"},
    },
    {
        "nom": "C3 — télétravail équipes support",
        "question": "Combien de jours de télétravail par semaine pour les équipes support ?",
        "attendus": {"RH-002"},
    },
    {
        "nom": "C4 — entretiens de recrutement",
        "question": "Combien d'entretiens comprend le processus de recrutement ?",
        "attendus": {"RH-003"},
    },
    {
        "nom": "C5 — renouvellement du milieu de culture",
        "question": "À quelle fréquence faut-il renouveler le milieu de culture cellulaire ?",
        "attendus": {"BIO-001"},
    },
    {
        "nom": "C6 — conservation des dossiers RH (abstention attendue)",
        "question": "Quel est le délai de conservation des dossiers RH ?",
        "attendus": set(),
    },
]


def main() -> int:
    parseur = argparse.ArgumentParser(description="Évalue le retrieval sur C1–C6.")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    reussis = 0
    evaluables = 0

    for cas in CAS:
        points = rechercher(cas["question"], arguments.index, arguments.model, arguments.top)
        documents = [str((point.payload or {}).get("doc_id")) for point in points]
        meilleurs_scores = [round(point.score, 3) for point in points[:3]]

        if cas["attendus"]:
            evaluables += 1
            trouve = bool(cas["attendus"] & set(documents))
            reussis += int(trouve)
            verdict = "OK" if trouve else "ÉCHEC"
        else:
            # Cas d'abstention : on observe simplement les scores.
            verdict = "À JUGER (aucune preuve attendue)"

        print(f"\n{cas['nom']}")
        print(f"  question : {cas['question']}")
        print(f"  documents: {documents}")
        print(f"  scores   : {meilleurs_scores}")
        print(f"  verdict  : {verdict}")

    print(f"\nRappel@top{arguments.top} sur C1–C5 : {reussis}/{evaluables}")
    return 0 if reussis == evaluables else 1


if __name__ == "__main__":
    raise SystemExit(main())
