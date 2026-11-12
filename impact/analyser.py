"""CLI d'analyse d'impact : décrit un changement, liste les documents impactés."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
for dossier in (RACINE / "rag", RACINE / "impact"):
    if str(dossier) not in sys.path:
        sys.path.insert(0, str(dossier))

from hybrid import point_vers_candidat  # noqa: E402
from moteur import (  # noqa: E402
    Changement,
    analyser_changement,
    analyser_textes,
    rendre_rapport,
)
from rag_lib import SEUIL_ABSTENTION, decide_reponse  # noqa: E402


def construire_recherche(mode, index, index_lexical, modele, seuil):
    """Adapte la recherche du pipeline RAG à l'interface du moteur."""

    # Import tardif : la CLI doit pouvoir valider ses arguments et signaler un
    # fichier absent sans exiger Qdrant.
    from search import rechercher, rechercher_hybride

    def rechercher_candidats(question, limite):
        if mode == "hybride":
            candidats, points = rechercher_hybride(
                question, index, index_lexical, modele, limite
            )
        else:
            points = rechercher(question, index, modele, limite)
            candidats = [point_vers_candidat(point) for point in points]

        if not points:
            return []
        retenus, motif = decide_reponse(points, seuil)
        if motif != "ok":
            return []
        return candidats[:limite]

    return rechercher_candidats


def lire_texte(chemin: Path):
    """Lit un document texte ; retourne (texte, erreur)."""
    if not chemin.exists():
        return None, f"fichier introuvable : {chemin}"
    try:
        return chemin.read_text(encoding="utf-8"), None
    except (OSError, UnicodeDecodeError) as erreur:
        return None, f"document illisible : {chemin} ({erreur})"


def main() -> int:
    parseur = argparse.ArgumentParser(
        description="Analyse l'impact d'un changement sur le corpus."
    )
    parseur.add_argument("--avant", help="Document avant modification (optionnel).")
    parseur.add_argument("--apres", help="Document après modification.")
    parseur.add_argument(
        "--changement",
        help="Changement décrit directement, dans sa forme cible "
        "(ex. « Le délai de déclaration est de 24 heures »).",
    )
    parseur.add_argument("--index", default="rag/index_qdrant")
    parseur.add_argument("--index-lexical", default="rag/index_fts/corpus.sqlite")
    parseur.add_argument("--model", default="bge-m3")
    parseur.add_argument("--mode", choices=("dense", "hybride"), default="dense")
    parseur.add_argument("--seuil", type=float, default=SEUIL_ABSTENTION)
    parseur.add_argument("--top", type=int, default=5)
    parseur.add_argument("--sortie", help="Fichier Markdown de sortie (défaut : stdout).")
    arguments = parseur.parse_args()

    if not Path(arguments.index).exists():
        print(f"Erreur : index introuvable — {arguments.index}")
        return 2

    if not arguments.changement and not arguments.apres:
        print("Erreur : fournir --changement ou --apres (avec ou sans --avant).")
        return 2

    # Lecture des documents avant toute dépendance lourde.
    avant = apres = ""
    if not arguments.changement:
        apres, erreur = lire_texte(Path(arguments.apres))
        if erreur:
            print(f"Erreur : {erreur}")
            return 3
        if arguments.avant:
            avant, erreur = lire_texte(Path(arguments.avant))
            if erreur:
                print(f"Erreur : {erreur}")
                return 3

    rechercher_candidats = construire_recherche(
        arguments.mode,
        arguments.index,
        arguments.index_lexical,
        arguments.model,
        arguments.seuil,
    )

    if arguments.changement:
        changement = Changement(avant="", apres=arguments.changement)
        impacts = analyser_changement(changement, rechercher_candidats, limite=arguments.top)
        titre = "Analyse d'impact — changement décrit"
    else:
        impacts = analyser_textes(avant, apres, rechercher_candidats, limite=arguments.top)
        titre = "Analyse d'impact — comparaison de versions"

    rapport = rendre_rapport(impacts, titre)

    if arguments.sortie:
        destination = Path(arguments.sortie)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rapport, encoding="utf-8")
        print(f"Rapport écrit : {destination.resolve()}")
        print(f"Impacts qualifiés : {len(impacts)}")
    else:
        print(rapport)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
