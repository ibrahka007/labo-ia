"""Bibliothèque commune du pipeline RAG local (parsing, chunks, embeddings)."""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

OLLAMA_URL = "http://127.0.0.1:11434"
COLLECTION = "corpus_labo_ia"
TAILLE_CHUNK_MAX = 1600
CHEVAUCHEMENT = 150

# Seuil provisoire calibré sur 18 cas (voir rag/calibrer_seuil.py).
# Marge faible : à re-mesurer sur un jeu plus large avant usage réel.
SEUIL_ABSTENTION = 0.65

# Marqueurs indiquant qu'un passage ne formule pas une règle établie.
INDICES_RESERVE = (
    "hypothèse",
    "à confirmer",
    "sous réserve",
    "non confirmé",
    "à valider",
)


@dataclass
class Chunk:
    doc_id: str
    titre: str
    version: str
    statut: str
    domaine: str
    fichier: str
    section: str
    position: int
    texte: str


def lire_front_matter(contenu: str) -> Tuple[Dict[str, str], str]:
    """Sépare le bloc YAML simple (clé: valeur) du corps Markdown."""
    if not contenu.startswith("---"):
        return {}, contenu

    fin = contenu.find("\n---", 3)
    if fin == -1:
        return {}, contenu

    bloc = contenu[3:fin]
    corps = contenu[fin + 4 :].lstrip("\n")

    metadonnees: Dict[str, str] = {}
    for ligne in bloc.splitlines():
        if ":" in ligne:
            cle, valeur = ligne.split(":", 1)
            metadonnees[cle.strip()] = valeur.strip()

    return metadonnees, corps


def decouper_sections(corps: str) -> List[Tuple[str, str]]:
    """Retourne des couples (titre de section, contenu)."""
    parties = re.split(r"(?m)^##\s+", corps)
    sections: List[Tuple[str, str]] = []

    introduction = parties[0].strip()
    if introduction:
        sections.append(("Introduction", introduction))

    for partie in parties[1:]:
        lignes = partie.splitlines()
        if not lignes:
            continue
        titre = lignes[0].strip()
        contenu = "\n".join(lignes[1:]).strip()
        sections.append((titre, contenu))

    return sections


def decouper_texte(texte: str) -> List[str]:
    """Découpe un texte trop long en fenêtres avec chevauchement."""
    if len(texte) <= TAILLE_CHUNK_MAX:
        return [texte]

    paragraphes = [p.strip() for p in texte.split("\n\n") if p.strip()]
    morceaux: List[str] = []
    courant = ""

    for paragraphe in paragraphes:
        if len(courant) + len(paragraphe) + 2 <= TAILLE_CHUNK_MAX:
            courant = f"{courant}\n\n{paragraphe}".strip()
        else:
            if courant:
                morceaux.append(courant)
            courant = paragraphe

    if courant:
        morceaux.append(courant)

    return morceaux


def extraire_chunks(chemin: Path, racine: Path) -> List[Chunk]:
    """Transforme un fichier Markdown en chunks porteurs de métadonnées."""
    contenu = chemin.read_text(encoding="utf-8")
    metadonnees, corps = lire_front_matter(contenu)

    if not metadonnees.get("id"):
        return []

    relative = str(chemin.relative_to(racine))
    chunks: List[Chunk] = []

    for section, contenu_section in decouper_sections(corps):
        for numero, morceau in enumerate(decouper_texte(contenu_section), start=1):
            libelle = section if numero == 1 else f"{section} (partie {numero})"
            texte = f"{libelle}\n{metadonnees.get('titre', '')}\n{morceau}".strip()

            chunks.append(
                Chunk(
                    doc_id=metadonnees.get("id", ""),
                    titre=metadonnees.get("titre", ""),
                    version=metadonnees.get("version", ""),
                    statut=metadonnees.get("statut", ""),
                    domaine=metadonnees.get("domaine", ""),
                    fichier=relative,
                    section=libelle,
                    position=len(chunks),
                    texte=texte,
                )
            )

    return chunks


def collecter_chunks(racine: Path) -> List[Chunk]:
    """Parcourt le corpus et exclut la documentation et les annotations."""
    chunks: List[Chunk] = []

    for chemin in sorted(racine.rglob("*.md")):
        relative = chemin.relative_to(racine)
        if relative.parts[0] in {"annotations"}:
            continue
        if chemin.name == "README.md":
            continue
        chunks.extend(extraire_chunks(chemin, racine))

    return chunks


def embed_textes(textes: List[str], modele: str, lot: int = 16) -> List[List[float]]:
    """Calcule les embeddings via l'API locale Ollama."""
    vecteurs: List[List[float]] = []

    for debut in range(0, len(textes), lot):
        paquet = textes[debut : debut + lot]
        charge = json.dumps({"model": modele, "input": paquet}).encode("utf-8")
        requete = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed",
            data=charge,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(requete, timeout=300) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))

        embeddings = donnees.get("embeddings", [])
        if len(embeddings) != len(paquet):
            raise RuntimeError(
                f"Réponse d'embeddings incohérente : {len(embeddings)} vecteurs "
                f"pour {len(paquet)} textes"
            )
        vecteurs.extend(embeddings)

    return vecteurs


def embed_texte(texte: str, modele: str) -> List[float]:
    return embed_textes([texte], modele)[0]


def decide_reponse(points, seuil: float = SEUIL_ABSTENTION):
    """Décide s'il existe une preuve suffisante pour répondre.

    Retourne un couple (points retenus, motif) :
    - motif « ok » : au moins un passage dépasse le seuil ;
    - motif « preuve insuffisante » : aucun passage ne le dépasse ;
    - motif « aucun résultat » : l'index n'a rien renvoyé.
    """
    if not points:
        return [], "aucun résultat"

    retenus = [
        point
        for point in points
        if float(getattr(point, "score", 0.0) or 0.0) >= seuil
    ]

    if not retenus:
        return [], "preuve insuffisante"

    return retenus, "ok"


def detecter_reserve(texte: str) -> list:
    """Retourne les marqueurs de réserve présents dans un passage."""
    contenu = (texte or "").lower()
    return [indice for indice in INDICES_RESERVE if indice in contenu]
