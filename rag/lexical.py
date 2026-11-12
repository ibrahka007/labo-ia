"""Index lexical BM25 du corpus, via SQLite FTS5 (bibliothèque standard).

Aucune dépendance externe : l'index est un simple fichier SQLite
reconstructible, à l'image de l'index vectoriel Qdrant.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Dict, List

from rag_lib import Chunk

CHEMIN_DEFAUT = "rag/index_fts/corpus.sqlite"
TABLE = "chunks"

STOPWORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle",
    "en", "et", "eux", "il", "ils", "je", "la", "le", "les", "leur", "lui",
    "mais", "me", "meme", "mes", "moi", "mon", "ne", "nos", "notre", "nous",
    "on", "ou", "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses",
    "son", "sont", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un", "une",
    "vos", "votre", "vous", "y", "est", "sont", "ete", "etre", "avoir",
    "quel", "quelle", "quels", "quelles", "combien", "faut", "doit",
    "comment", "pourquoi", "quand",
}


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, ponctuation réduite à des espaces."""
    decompose = unicodedata.normalize("NFD", texte or "")
    sans_accent = "".join(
        caractere for caractere in decompose if unicodedata.category(caractere) != "Mn"
    )
    minuscules = sans_accent.lower()
    return re.sub(r"[^a-z0-9]+", " ", minuscules).strip()


def jetons(question: str) -> List[str]:
    """Jetons significatifs d'une question, sans doublon ni ordre garanti."""
    vus = []
    for jeton in normaliser(question).split():
        if len(jeton) < 2 or jeton in STOPWORDS:
            continue
        if jeton not in vus:
            vus.append(jeton)
    return vus


def requete_match(question: str, operateur: str = "AND") -> str:
    """Construit une requête FTS5 sûre : jetons cités, reliés par un opérateur."""
    return f" {operateur} ".join(f'"{jeton}"' for jeton in jetons(question))


def couverture(question: str, texte: str) -> float:
    """Part des jetons de la question présents dans le texte (0 à 1)."""
    jetons_question = jetons(question)
    if not jetons_question:
        return 0.0
    texte_plat = normaliser(texte)
    presents = sum(1 for jeton in jetons_question if jeton in texte_plat)
    return presents / len(jetons_question)


def construire_index(chunks: List[Chunk], chemin: str = CHEMIN_DEFAUT) -> int:
    """(Re)construit l'index lexical et retourne le nombre de chunks indexés."""
    fichier = Path(chemin)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    if fichier.exists():
        fichier.unlink()

    connexion = sqlite3.connect(fichier)
    try:
        connexion.execute(
            f"""
            CREATE VIRTUAL TABLE {TABLE} USING fts5(
                doc_id UNINDEXED,
                titre UNINDEXED,
                version UNINDEXED,
                statut UNINDEXED,
                domaine UNINDEXED,
                fichier UNINDEXED,
                section UNINDEXED,
                position UNINDEXED,
                texte UNINDEXED,
                texte_plat,
                tokenize='unicode61'
            )
            """
        )
        connexion.executemany(
            f"""
            INSERT INTO {TABLE} (
                doc_id, titre, version, statut, domaine,
                fichier, section, position, texte, texte_plat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.doc_id,
                    chunk.titre,
                    chunk.version,
                    chunk.statut,
                    chunk.domaine,
                    chunk.fichier,
                    chunk.section,
                    chunk.position,
                    chunk.texte,
                    normaliser(chunk.texte),
                )
                for chunk in chunks
            ],
        )
        connexion.commit()
    finally:
        connexion.close()

    return len(chunks)


def rechercher_lexical(
    question: str, chemin: str = CHEMIN_DEFAUT, limite: int = 5
) -> List[Dict[str, object]]:
    """Recherche BM25 ; retourne des passages triés du plus pertinent au moins."""
    fichier = Path(chemin)
    if not fichier.exists():
        raise FileNotFoundError(f"Index lexical introuvable : {fichier}")

    if not jetons(question):
        return []

    connexion = sqlite3.connect(fichier)
    connexion.row_factory = sqlite3.Row
    try:
        lignes = []
        # Priorité à la conjonction (précision), repli sur la disjonction (rappel).
        for operateur in ("AND", "OR"):
            expression = requete_match(question, operateur)
            lignes = connexion.execute(
                f"""
                SELECT doc_id, titre, version, statut, domaine, fichier,
                       section, position, texte, bm25({TABLE}) AS score_brut
                FROM {TABLE}
                WHERE {TABLE} MATCH ?
                ORDER BY score_brut
                LIMIT ?
                """,
                (expression, max(limite * 4, 20)),
            ).fetchall()
            if lignes:
                break
    finally:
        connexion.close()

    classement = []
    for ligne in lignes:
        # bm25() renvoie une valeur négative : plus proche de zéro = plus pertinent.
        score = -float(ligne["score_brut"])
        # La couverture des termes départage les correspondances partielles :
        # sans elle, un seul mot rare peut devancer un passage qui répond mieux.
        couverture_texte = couverture(question, ligne["texte"])
        classement.append((couverture_texte, score, ligne))

    classement.sort(key=lambda item: (item[0], item[1]), reverse=True)

    resultats = []
    for rang, (couverture_texte, score, ligne) in enumerate(classement[:limite], start=1):
        resultats.append(
            {
                "doc_id": ligne["doc_id"],
                "titre": ligne["titre"],
                "version": ligne["version"],
                "statut": ligne["statut"],
                "domaine": ligne["domaine"],
                "fichier": ligne["fichier"],
                "section": ligne["section"],
                "position": ligne["position"],
                "texte": ligne["texte"],
                "score": score,
                "couverture": round(couverture_texte, 3),
                "rang": rang,
                "source": "lexical",
            }
        )
    return resultats
