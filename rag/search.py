"""Recherche sémantique dans l'index Qdrant local, avec abstention."""

from __future__ import annotations

import argparse
from pathlib import Path

from qdrant_client import QdrantClient

from rag_lib import (
    COLLECTION,
    SEUIL_ABSTENTION,
    decide_reponse,
    detecter_reserve,
    embed_texte,
)


def rechercher(question: str, index: str, modele: str, limite: int = 5):
    client = QdrantClient(path=index)
    vecteur = embed_texte(question, modele)
    reponse = client.query_points(
        collection_name=COLLECTION,
        query=vecteur,
        limit=limite,
        with_payload=True,
    )
    client.close()
    return reponse.points


def main() -> int:
    parseur = argparse.ArgumentParser(description="Recherche dans le corpus indexé.")
    parseur.add_argument("question")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    parseur.add_argument(
        "--seuil",
        type=float,
        default=SEUIL_ABSTENTION,
        help="Score minimal pour répondre (0 pour désactiver l'abstention).",
    )
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    if arguments.seuil < 0 or arguments.seuil > 1:
        print("Erreur : le seuil doit être compris entre 0 et 1.")
        return 2

    points = rechercher(arguments.question, arguments.index, arguments.model, arguments.top)

    if not points:
        print("Aucun résultat.")
        return 0

    retenus, motif = decide_reponse(points, arguments.seuil)

    print(f"Question : {arguments.question}")
    print(f"Seuil d'abstention : {arguments.seuil:.2f}\n")

    if motif != "ok":
        meilleur = points[0].score
        print("Preuve insuffisante : le corpus ne contient pas de passage")
        print("dépassant le seuil de confiance.")
        print(
            f"Meilleur score observé : {meilleur:.3f} "
            f"({(points[0].payload or {}).get('doc_id')})"
        )
        meilleur_texte = (points[0].payload or {}).get("texte", "")
        marqueurs = detecter_reserve(meilleur_texte)
        if marqueurs:
            print(
                "Détail : ce meilleur passage présente la valeur comme une "
                f"règle non établie ({', '.join(marqueurs)})."
            )
        print("Aucune réponse ne doit être déduite de ces résultats.")
        print("Validation humaine ou recherche complémentaire requise.")
        return 0

    reserves = []
    for rang, point in enumerate(retenus, start=1):
        charge = point.payload or {}
        extrait = " ".join(str(charge.get("texte", "")).split())
        marqueurs = detecter_reserve(charge.get("texte", ""))
        if marqueurs:
            reserves.append((charge.get("doc_id"), marqueurs))
        print(
            f"{rang}. [{point.score:.3f}] {charge.get('doc_id')} "
            f"v{charge.get('version')} — {charge.get('section')} "
            f"({charge.get('statut')})"
        )
        print(f"   {charge.get('titre')} — {charge.get('fichier')}")
        print(f"   {extrait[:220]}")
        if marqueurs:
            print(f"   /!\\ Réserve dans le document : {', '.join(marqueurs)}")
        print()

    if reserves:
        documents = ", ".join(str(doc) for doc, _ in reserves)
        print(
            "Réserve : ces passages ne formulent pas une règle établie "
            f"({documents}). La valeur doit être présentée comme une hypothèse "
            "à confirmer, jamais comme une obligation."
        )
        print("Validation humaine requise.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
