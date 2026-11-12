"""Indexe le corpus fictif dans Qdrant (mode local, sans serveur)."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from lexical import CHEMIN_DEFAUT as INDEX_LEXICAL, construire_index
from rag_lib import COLLECTION, collecter_chunks, embed_textes


def main() -> int:
    parseur = argparse.ArgumentParser(description="Indexe le corpus dans Qdrant local.")
    parseur.add_argument("--corpus", default="corpus")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--lot", type=int, default=16)
    parseur.add_argument(
        "--index-lexical", default=INDEX_LEXICAL, help="Fichier SQLite (FTS5)."
    )
    arguments = parseur.parse_args()

    racine = Path(arguments.corpus).resolve()
    if not racine.exists():
        print(f"Erreur : corpus introuvable — {racine}")
        return 2

    chunks = collecter_chunks(racine)
    if not chunks:
        print("Erreur : aucun chunk extrait du corpus.")
        return 3

    documents = {chunk.fichier for chunk in chunks}
    print(f"Corpus : {len(chunks)} chunks issus de {len(documents)} fichiers.")
    print(f"Modèle d'embeddings : {arguments.model}")

    debut = time.time()
    vecteurs = embed_textes([chunk.texte for chunk in chunks], arguments.model, arguments.lot)
    duree = time.time() - debut
    dimension = len(vecteurs[0])

    client = QdrantClient(path=arguments.index)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=index,
            vector=vecteur,
            payload={
                "doc_id": chunk.doc_id,
                "titre": chunk.titre,
                "version": chunk.version,
                "statut": chunk.statut,
                "domaine": chunk.domaine,
                "fichier": chunk.fichier,
                "section": chunk.section,
                "position": chunk.position,
                "texte": chunk.texte,
            },
        )
        for index, (chunk, vecteur) in enumerate(zip(chunks, vecteurs))
    ]

    client.upsert(collection_name=COLLECTION, points=points)
    client.close()

    metadonnees = {
        "modele": arguments.model,
        "dimension": dimension,
        "chunks": len(chunks),
        "fichiers": len(documents),
        "duree_embeddings_s": round(duree, 1),
        "index": str(Path(arguments.index).resolve()),
        "index_lexical": str(Path(arguments.index_lexical).resolve()),
    }
    Path("rag/index_meta.json").write_text(
        json.dumps(metadonnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"Index vectoriel : {len(chunks)} points, dimension {dimension}, "
        f"embeddings en {duree:.1f} s."
    )
    print(f"Index : {Path(arguments.index).resolve()}")

    nombre = construire_index(chunks, arguments.index_lexical)
    print(f"Index lexical : {nombre} chunks dans {Path(arguments.index_lexical).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
