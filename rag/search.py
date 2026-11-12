"""Recherche dans le corpus : dense, lexicale ou hybride, avec abstention."""

from __future__ import annotations

import argparse
from pathlib import Path

from qdrant_client import QdrantClient

from hybrid import fusion_rrf, point_vers_candidat, reranker_heuristique
from lexical import CHEMIN_DEFAUT as INDEX_LEXICAL, rechercher_lexical
from rag_lib import (
    COLLECTION,
    SEUIL_ABSTENTION,
    decide_reponse,
    detecter_reserve,
    embed_texte,
)

MODES = ("dense", "lexical", "hybride")


def rechercher(question: str, index: str, modele: str, limite: int = 5):
    """Recherche vectorielle dense (comportement historique)."""
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


def rechercher_hybride(
    question: str,
    index_dense: str,
    index_lexical: str,
    modele: str,
    limite: int = 5,
    taille_canal: int = 10,
    reranker: bool = True,
):
    """Fusionne les canaux dense et lexical, puis reranke.

    Retourne (candidats, points_denses). Les points denses sont conservés pour
    que l'abstention reste évaluée sur le signal calibré (similarité cosinus).
    """
    points = rechercher(question, index_dense, modele, taille_canal)
    denses = [point_vers_candidat(point) for point in points]
    lexicaux = rechercher_lexical(question, index_lexical, taille_canal)

    fusionnes = fusion_rrf([denses, lexicaux])
    if reranker:
        fusionnes = reranker_heuristique(question, fusionnes)

    return fusionnes[:limite], points


def afficher_candidat(rang: int, candidat, mode: str) -> None:
    charge = candidat
    extrait = " ".join(str(charge.get("texte", "")).split())
    details = f"[{charge.get('score', 0.0):.3f}]"
    if mode == "hybride":
        details = (
            f"[rrf {charge.get('score_rrf', 0.0):.4f} | "
            f"heur {charge.get('score_heuristique', 0.0):.3f} | "
            f"couv {charge.get('couverture', 0.0):.2f}]"
        )
    print(
        f"{rang}. {details} {charge.get('doc_id')} "
        f"v{charge.get('version')} — {charge.get('section')} "
        f"({charge.get('statut')})"
    )
    print(f"   {charge.get('titre')} — {charge.get('fichier')}")
    print(f"   {extrait[:220]}")
    marqueurs = detecter_reserve(charge.get("texte", ""))
    if marqueurs:
        print(f"   /!\\ Réserve dans le document : {', '.join(marqueurs)}")
    print()


def decider(question, points_denses, mode, seuil):
    """Décide de l'abstention selon le mode.

    - dense : seuil appliqué aux scores cosinus (signal calibré) ;
    - hybride : seuil appliqué au meilleur score dense, même si le classement
      final vient de la fusion (le score RRF n'est pas calibré) ;
    - lexical : pas d'abstention calibrée, le mode sert au diagnostic.
    """
    if mode == "lexical":
        return [], "non calibré"
    return decide_reponse(points_denses, seuil)


def main() -> int:
    parseur = argparse.ArgumentParser(description="Recherche dans le corpus indexé.")
    parseur.add_argument("question")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--index-lexical", default=INDEX_LEXICAL)
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    parseur.add_argument("--mode", choices=MODES, default="dense")
    parseur.add_argument(
        "--reranker",
        choices=("heuristic", "none"),
        default="heuristic",
        help="Reranker appliqué en mode hybride.",
    )
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
    if arguments.mode != "dense" and not Path(arguments.index_lexical).exists():
        print(f"Erreur : index lexical introuvable — {arguments.index_lexical}")
        print("Construire les index avec : rag/index_corpus.py")
        return 2
    if arguments.seuil < 0 or arguments.seuil > 1:
        print("Erreur : le seuil doit être compris entre 0 et 1.")
        return 2

    print(f"Question : {arguments.question}")
    print(f"Mode : {arguments.mode} | Seuil d'abstention : {arguments.seuil:.2f}\n")

    if arguments.mode == "dense":
        points = rechercher(arguments.question, arguments.index, arguments.model, arguments.top)
        if not points:
            print("Aucun résultat.")
            return 0
        retenus, motif = decide_reponse(points, arguments.seuil)
        if motif != "ok":
            return afficher_abstention(points[0].score, points[0].payload or {})
        candidats = [point_vers_candidat(point) for point in retenus]
    elif arguments.mode == "lexical":
        candidats = rechercher_lexical(
            arguments.question, arguments.index_lexical, arguments.top
        )
        if not candidats:
            print("Aucun résultat lexical.")
            print("Mode lexical : abstention non calibrée, usage diagnostic.")
            return 0
        print("Mode lexical : abstention non calibrée, usage diagnostic.\n")
    else:
        candidats, points = rechercher_hybride(
            arguments.question,
            arguments.index,
            arguments.index_lexical,
            arguments.model,
            arguments.top,
            reranker=arguments.reranker == "heuristic",
        )
        _, motif = decider(arguments.question, points, "hybride", arguments.seuil)
        if motif != "ok":
            return afficher_abstention(points[0].score, points[0].payload or {})
        if not candidats:
            print("Aucun résultat hybride.")
            return 0

    for rang, candidat in enumerate(candidats, start=1):
        afficher_candidat(rang, candidat, arguments.mode)

    reserves = [
        (c.get("doc_id"), detecter_reserve(c.get("texte", "")))
        for c in candidats
        if detecter_reserve(c.get("texte", ""))
    ]
    if reserves:
        documents = ", ".join(str(doc) for doc, _ in reserves)
        print(
            "Réserve : ces passages ne formulent pas une règle établie "
            f"({documents}). La valeur doit être présentée comme une hypothèse "
            "à confirmer, jamais comme une obligation."
        )
        print("Validation humaine requise.")

    return 0


def afficher_abstention(meilleur_score: float, charge) -> int:
    print("Preuve insuffisante : le corpus ne contient pas de passage")
    print("dépassant le seuil de confiance.")
    print(f"Meilleur score observé : {meilleur_score:.3f} ({charge.get('doc_id')})")
    marqueurs = detecter_reserve(charge.get("texte", ""))
    if marqueurs:
        print(
            "Détail : ce meilleur passage présente la valeur comme une "
            f"règle non établie ({', '.join(marqueurs)})."
        )
    print("Aucune réponse ne doit être déduite de ces résultats.")
    print("Validation humaine ou recherche complémentaire requise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
