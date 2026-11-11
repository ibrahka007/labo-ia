"""Recherche sémantique dans l'index Qdrant local."""

from __future__ import annotations

import argparse
from pathlib import Path

from qdrant_client import QdrantClient

from rag_lib import COLLECTION, embed_texte


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
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    points = rechercher(arguments.question, arguments.index, arguments.model, arguments.top)

    if not points:
        print("Aucun résultat.")
        return 0

    print(f"Question : {arguments.question}\n")
    for rang, point in enumerate(points, start=1):
        charge = point.payload or {}
        extrait = " ".join(str(charge.get("texte", "")).split())
        print(
            f"{rang}. [{point.score:.3f}] {charge.get('doc_id')} "
            f"v{charge.get('version')} — {charge.get('section')} "
            f"({charge.get('statut')})"
        )
        print(f"   {charge.get('titre')} — {charge.get('fichier')}")
        print(f"   {extrait[:220]}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
