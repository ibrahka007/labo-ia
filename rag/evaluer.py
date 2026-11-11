"""Évalue le retrieval et l'abstention sur les cas C1 à C6 et hors corpus."""

from __future__ import annotations

import argparse
from pathlib import Path

from calibrer_seuil import HORS_CORPUS
from rag_lib import SEUIL_ABSTENTION, decide_reponse
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
]


def main() -> int:
    parseur = argparse.ArgumentParser(description="Évalue le retrieval sur C1–C6.")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    parseur.add_argument("--seuil", type=float, default=SEUIL_ABSTENTION)
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    reussis = 0
    repondus = 0

    for cas in CAS:
        points = rechercher(cas["question"], arguments.index, arguments.model, arguments.top)
        documents = [str((point.payload or {}).get("doc_id")) for point in points]
        retenus, motif = decide_reponse(points, arguments.seuil)
        trouve = bool(cas["attendus"] & set(documents[: arguments.top]))

        reussis += int(trouve)
        repondus += int(motif == "ok")

        print(f"\n{cas['nom']}")
        print(f"  documents : {documents}")
        print(f"  scores    : {[round(point.score, 3) for point in points[:3]]}")
        print(f"  rappel@top{arguments.top} : {'OK' if trouve else 'ÉCHEC'}")
        print(f"  décision  : {motif}")

    abstentions_correctes = 0
    for nom, question in HORS_CORPUS:
        points = rechercher(question, arguments.index, arguments.model, arguments.top)
        retenus, motif = decide_reponse(points, arguments.seuil)
        correcte = motif != "ok"
        abstentions_correctes += int(correcte)
        meilleur = round(points[0].score, 3) if points else 0.0
        print(
            f"\n{nom} — {question}\n"
            f"  meilleur score : {meilleur} | décision : {motif} "
            f"{'OK' if correcte else 'ÉCHEC'}"
        )

    print(f"\nRappel@top{arguments.top} sur C1–C5 : {reussis}/{len(CAS)}")
    print(f"Cas répondus (au-dessus du seuil) : {repondus}/{len(CAS)}")
    print(
        f"Abstentions correctes : {abstentions_correctes}/{len(HORS_CORPUS)} "
        f"(seuil {arguments.seuil:.2f})"
    )
    print(
        "Fausses réponses évitées : "
        f"{abstentions_correctes}/{len(HORS_CORPUS)} questions hors corpus"
    )

    return 0 if reussis == len(CAS) and abstentions_correctes == len(HORS_CORPUS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
