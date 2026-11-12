"""Fusion des résultats dense et lexical, puis reranking local.

- Fusion : Reciprocal Rank Fusion (RRF), sans paramètre à ajuster.
- Reranker : heuristique reproductible (recouvrement de termes), servant de
  référence avant tout reranker neuronal.
"""

from __future__ import annotations

from typing import Dict, List

from lexical import couverture

K_RRF = 60


def point_vers_candidat(point) -> Dict[str, object]:
    """Convertit un point Qdrant en candidat commun aux deux canaux."""
    charge = point.payload or {}
    return {
        "doc_id": charge.get("doc_id"),
        "titre": charge.get("titre"),
        "version": charge.get("version"),
        "statut": charge.get("statut"),
        "domaine": charge.get("domaine"),
        "fichier": charge.get("fichier"),
        "section": charge.get("section"),
        "position": charge.get("position"),
        "texte": charge.get("texte", ""),
        "score": float(point.score),
        "source": "dense",
    }


def cle(candidat: Dict[str, object]) -> str:
    """Identifie un chunk de façon stable entre les deux canaux."""
    return f"{candidat.get('fichier')}#{candidat.get('section')}"


def fusion_rrf(
    canaux: List[List[Dict[str, object]]], k: int = K_RRF
) -> List[Dict[str, object]]:
    """Fusionne plusieurs classements par Reciprocal Rank Fusion.

    Chaque candidat reçoit la somme de 1 / (k + rang) sur chaque canal où il
    apparaît. Le rang démarre à 1.
    """
    cumul: Dict[str, Dict[str, object]] = {}
    scores: Dict[str, float] = {}

    for canal in canaux:
        for rang, candidat in enumerate(canal, start=1):
            identifiant = cle(candidat)
            if identifiant not in cumul:
                cumul[identifiant] = dict(candidat)
                scores[identifiant] = 0.0
            scores[identifiant] += 1.0 / (k + rang)

    fusionnes = []
    for identifiant, candidat in cumul.items():
        fusion = dict(candidat)
        fusion["score_rrf"] = scores[identifiant]
        fusionnes.append(fusion)

    fusionnes.sort(key=lambda item: item["score_rrf"], reverse=True)
    for rang, candidat in enumerate(fusionnes, start=1):
        candidat["rang_rrf"] = rang
    return fusionnes


def reranker_heuristique(
    question: str, candidats: List[Dict[str, object]]
) -> List[Dict[str, object]]:
    """Réordonne les candidats par recouvrement lexical, puis par score RRF.

    Le score heuristique est volontairement simple et explicable :
    70 % de couverture des termes de la question, 20 % de présence dans le
    titre ou la section, 10 % de rang RRF normalisé.
    """
    if not candidats:
        return []

    total = len(candidats)
    reordonnes = []

    for candidat in candidats:
        texte = str(candidat.get("texte", ""))
        titre = f"{candidat.get('titre') or ''} {candidat.get('section') or ''}"

        couverture_texte = couverture(question, texte)
        couverture_titre = couverture(question, titre)
        rang = int(candidat.get("rang_rrf") or total)
        score_rang = 1.0 - (rang - 1) / max(total, 1)

        score = 0.7 * couverture_texte + 0.2 * couverture_titre + 0.1 * score_rang

        enrichi = dict(candidat)
        enrichi["score_heuristique"] = round(score, 4)
        enrichi["couverture"] = round(couverture_texte, 3)
        reordonnes.append(enrichi)

    reordonnes.sort(
        key=lambda item: (item["score_heuristique"], item.get("score_rrf", 0.0)),
        reverse=True,
    )
    for rang, candidat in enumerate(reordonnes, start=1):
        candidat["rang_final"] = rang
    return reordonnes
