"""Calibre un seuil d'abstention sur les scores de retrieval.

Compare deux populations :
- questions dont la réponse existe dans le corpus (C1 à C5) ;
- questions hors corpus, pour lesquelles le système doit répondre
  « preuve insuffisante ».

Le script ne modifie rien : il mesure et propose un seuil.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from search import rechercher

CONNUES = [
    ("C1", "Quel est le délai pour déclarer un écart qualité ?"),
    ("C2", "Quelle est la durée de conservation des enregistrements qualité ?"),
    ("C3", "Combien de jours de télétravail par semaine pour les équipes support ?"),
    ("C4", "Combien d'entretiens comprend le processus de recrutement ?"),
    ("C5", "À quelle fréquence faut-il renouveler le milieu de culture cellulaire ?"),
]

HORS_CORPUS = [
    ("H1", "Quel est le montant du budget annuel de formation ?"),
    ("H2", "Combien de jours de congés payés par an ?"),
    ("H3", "Quelle est la procédure de licenciement économique ?"),
    ("H4", "Quel est le prix de vente du produit fini ?"),
    ("H5", "Quelle est la température de conservation du vaccin ?"),
    ("H6", "Combien de salariés compte l'entreprise ?"),
    ("H7", "Qui est le directeur général de l'entreprise ?"),
    ("H8", "Quelle est la procédure d'achat de matériel informatique ?"),
    ("H9", "Quel est le délai de préavis de démission ?"),
    ("H10", "Quelle est la composition du comité de direction ?"),
    ("H11", "Quel est le numéro d'agrément de l'établissement pharmaceutique ?"),
    ("H12", "Quelle est la durée de garantie des équipements de laboratoire ?"),
    ("H13", "Quel est le délai de conservation des dossiers RH ?"),
]


def mesurer(cas, index: str, modele: str, top: int):
    mesures = []
    for nom, question in cas:
        points = rechercher(question, index, modele, top)
        scores = [round(point.score, 3) for point in points]
        documents = [str((point.payload or {}).get("doc_id")) for point in points]
        mesures.append(
            {
                "nom": nom,
                "question": question,
                "top1": scores[0] if scores else 0.0,
                "scores": scores,
                "documents": documents,
            }
        )
    return mesures


def evaluer_seuil(seuil: float, connues, hors_corpus):
    """Retourne (bonnes réponses gardées, abstentions correctes)."""
    gardees = sum(1 for mesure in connues if mesure["top1"] >= seuil)
    abstentions = sum(1 for mesure in hors_corpus if mesure["top1"] < seuil)
    return gardees, abstentions


def main() -> int:
    parseur = argparse.ArgumentParser(description="Calibre le seuil d'abstention.")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    connues = mesurer(CONNUES, arguments.index, arguments.model, arguments.top)
    hors_corpus = mesurer(HORS_CORPUS, arguments.index, arguments.model, arguments.top)

    print("Questions dont la réponse existe dans le corpus (top1 attendu haut)")
    for mesure in connues:
        print(
            f"  {mesure['nom']:<3} top1={mesure['top1']:.3f} "
            f"top3={mesure['scores'][:3]} {mesure['documents'][:2]}"
        )

    print("\nQuestions hors corpus (top1 attendu bas)")
    for mesure in hors_corpus:
        print(
            f"  {mesure['nom']:<3} top1={mesure['top1']:.3f} "
            f"top3={mesure['scores'][:3]} {mesure['documents'][:2]}"
        )

    scores_connus = sorted(mesure["top1"] for mesure in connues)
    scores_hors = sorted(mesure["top1"] for mesure in hors_corpus)
    print(f"\nConnues   : min={scores_connus[0]:.3f} max={scores_connus[-1]:.3f}")
    print(f"Hors corpus: min={scores_hors[0]:.3f} max={scores_hors[-1]:.3f}")

    candidats = sorted({mesure["top1"] for mesure in connues + hors_corpus})
    bornes = [(a + b) / 2 for a, b in zip(candidats, candidats[1:])]
    resultats = []
    for seuil in bornes:
        gardees, abstentions = evaluer_seuil(seuil, connues, hors_corpus)
        resultats.append(
            {
                "seuil": seuil,
                "gardees": gardees,
                "abstentions": abstentions,
                "total": gardees + abstentions,
            }
        )

    print("\nSeuils candidats (bonnes réponses gardées / abstentions correctes)")
    meilleur = max(resultats, key=lambda item: (item["total"], item["gardees"]))
    for resultat in resultats:
        marque = "  <-- meilleur" if resultat is meilleur else ""
        print(
            f"  seuil={resultat['seuil']:.3f} : "
            f"{resultat['gardees']}/{len(connues)} gardées, "
            f"{resultat['abstentions']}/{len(hors_corpus)} abstentions"
            f"{marque}"
        )

    print(
        f"\nProposition : seuil={meilleur['seuil']:.2f} "
        f"({meilleur['total']}/{len(connues) + len(hors_corpus)} cas corrects)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
