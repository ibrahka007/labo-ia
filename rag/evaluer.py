"""Évalue le retrieval et l'abstention : dense, lexical et hybride.

Compare les trois modes sur les mêmes 18 cas (5 avec réponse, 13 hors corpus)
et mesure explicitement la confusion C4 / C6.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from calibrer_seuil import HORS_CORPUS
from hybrid import point_vers_candidat
from lexical import CHEMIN_DEFAUT as INDEX_LEXICAL, rechercher_lexical
from rag_lib import SEUIL_ABSTENTION, decide_reponse, detecter_reserve
from search import rechercher, rechercher_hybride

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

QUESTION_C6 = "Quel est le délai de conservation des dossiers RH ?"


def passages(question, mode, arguments):
    """Retourne (candidats, points_denses) selon le mode demandé."""
    if mode == "dense":
        points = rechercher(question, arguments.index, arguments.model, arguments.top)
        return [point_vers_candidat(point) for point in points], points
    if mode == "lexical":
        return (
            rechercher_lexical(question, arguments.index_lexical, arguments.top),
            [],
        )
    candidats, points = rechercher_hybride(
        question,
        arguments.index,
        arguments.index_lexical,
        arguments.model,
        arguments.top,
        reranker=arguments.reranker == "heuristic",
    )
    return candidats, points


def evaluer_mode(mode, arguments):
    """Évalue un mode et retourne les métriques sous forme de dictionnaire."""
    reussis = 0
    repondus = 0
    rangs_inverses = 0.0

    for cas in CAS:
        candidats, points = passages(cas["question"], mode, arguments)
        documents = [str(c.get("doc_id")) for c in candidats]
        rang_premier = next(
            (rang for rang, doc in enumerate(documents, start=1) if doc in cas["attendus"]),
            None,
        )
        if rang_premier:
            reussis += 1
            rangs_inverses += 1.0 / rang_premier
        if mode == "lexical":
            continue
        _, motif = decide_reponse(points, arguments.seuil)
        repondus += int(motif == "ok")

    abstentions = 0
    non_securisees = 0
    if mode != "lexical":
        for _, question in HORS_CORPUS:
            candidats_hors, points = passages(question, mode, arguments)
            _, motif = decide_reponse(points, arguments.seuil)
            abstentions += int(motif != "ok")
            # Une réponse reste « sécurisée » si elle s'abstient, ou si le
            # meilleur passage porte une réserve explicite (« hypothèse »…).
            if motif == "ok" and candidats_hors:
                texte = str(candidats_hors[0].get("texte", ""))
                if not detecter_reserve(texte):
                    non_securisees += 1

    # Cas C6 : où se classe le document « tentant » et la réserve est-elle vue ?
    candidats_c6, _ = passages(QUESTION_C6, mode, arguments)
    documents_c6 = [str(c.get("doc_id")) for c in candidats_c6]
    rang_pha004 = (
        documents_c6.index("PHA-004") + 1 if "PHA-004" in documents_c6 else None
    )
    reserve_c6 = any(
        detecter_reserve(c.get("texte", "")) for c in candidats_c6
    )

    # Cas C4 : rang du document attendu dans le classement final.
    candidats_c4, _ = passages(CAS[3]["question"], mode, arguments)
    documents_c4 = [str(c.get("doc_id")) for c in candidats_c4]
    rang_rh003 = documents_c4.index("RH-003") + 1 if "RH-003" in documents_c4 else None

    return {
        "rappel": f"{reussis}/{len(CAS)}",
        "mrr": f"{rangs_inverses / len(CAS):.3f}",
        "repondus": "-" if mode == "lexical" else f"{repondus}/{len(CAS)}",
        "abstentions": "-" if mode == "lexical" else f"{abstentions}/{len(HORS_CORPUS)}",
        "non_securisees": "-" if mode == "lexical" else str(non_securisees),
        "rang_c4": rang_rh003,
        "rang_c6": rang_pha004,
        "reserve_c6": "oui" if reserve_c6 else "non",
    }


def afficher_comparaison(resultats) -> None:
    entetes = [
        "Mode", "Rappel@5", "MRR", "Répondus", "Abstentions",
        "Non sécurisées", "Rang C4", "Rang C6", "Réserve C6",
    ]
    lignes = [
        [
            mode,
            valeurs["rappel"],
            valeurs["mrr"],
            valeurs["repondus"],
            valeurs["abstentions"],
            valeurs["non_securisees"],
            str(valeurs["rang_c4"] or "-"),
            str(valeurs["rang_c6"] or "-"),
            valeurs["reserve_c6"],
        ]
        for mode, valeurs in resultats.items()
    ]
    largeurs = [
        max(len(entete), max(len(ligne[i]) for ligne in lignes))
        for i, entete in enumerate(entetes)
    ]

    def formater(cellules):
        return " | ".join(
            cellule.ljust(largeur) for cellule, largeur in zip(cellules, largeurs)
        )

    print(formater(entetes))
    print("-+-".join("-" * largeur for largeur in largeurs))
    for ligne in lignes:
        print(formater(ligne))


def main() -> int:
    parseur = argparse.ArgumentParser(description="Évalue le retrieval sur C1–C6.")
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--index-lexical", default=INDEX_LEXICAL)
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--top", type=int, default=5)
    parseur.add_argument("--seuil", type=float, default=SEUIL_ABSTENTION)
    parseur.add_argument(
        "--mode", choices=("dense", "lexical", "hybride"), default="dense"
    )
    parseur.add_argument(
        "--reranker", choices=("heuristic", "none"), default="heuristic"
    )
    parseur.add_argument(
        "--comparer",
        action="store_true",
        help="Compare les trois modes sur les mêmes cas.",
    )
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    if arguments.comparer:
        if not Path(arguments.index_lexical).exists():
            print(f"Erreur : index lexical introuvable — {arguments.index_lexical}")
            return 2
        resultats = {
            mode: evaluer_mode(mode, arguments)
            for mode in ("dense", "lexical", "hybride")
        }
        afficher_comparaison(resultats)
        print(
            "\nNon sécurisées : questions hors corpus obtenant une réponse sans "
            "réserve explicite (objectif : 0).\n"
            "Rang C4 : position de RH-003 (cas légitime). "
            "Rang C6 : position de PHA-004 (document tentant, sans règle établie)."
        )
        return 0

    mode = arguments.mode
    for cas in CAS:
        candidats, points = passages(cas["question"], mode, arguments)
        documents = [str(c.get("doc_id")) for c in candidats]
        trouve = bool(cas["attendus"] & set(documents))
        motif = "-"
        if mode != "lexical":
            _, motif = decide_reponse(points, arguments.seuil)
        print(
            f"\n{cas['nom']}\n"
            f"  documents : {documents}\n"
            f"  rappel@top{arguments.top} : {'OK' if trouve else 'ÉCHEC'}\n"
            f"  décision  : {motif}"
        )

    abstentions = 0
    if mode != "lexical":
        for nom, question in HORS_CORPUS:
            _, points = passages(question, mode, arguments)
            _, motif = decide_reponse(points, arguments.seuil)
            abstentions += int(motif != "ok")
            print(
                f"\n{nom} — {question}\n"
                f"  meilleur score : {points[0].score:.3f} | décision : {motif} "
                f"{'OK' if motif != 'ok' else 'ÉCHEC'}"
            )

    valeurs = evaluer_mode(mode, arguments)
    print(f"\nRappel@top{arguments.top} sur C1–C5 : {valeurs['rappel']}")
    print(f"Abstentions correctes : {valeurs['abstentions']} (seuil {arguments.seuil:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
