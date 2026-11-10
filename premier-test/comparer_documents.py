from difflib import unified_diff
from pathlib import Path
import sys

ancienne_version = """Procédure de revue documentaire
Le responsable qualité valide le dossier.
Le délai de revue est de 30 jours.
Les documents sont conservés pendant 5 ans.
"""

nouvelle_version = """Procédure de revue documentaire
Le responsable qualité valide le dossier.
Le délai de revue est de 15 jours.
Les documents sont conservés pendant 10 ans.
"""


class DocumentIntrouvable(Exception):
    """Le fichier demandé n'existe pas."""


class DocumentIllisible(Exception):
    """Le fichier existe mais ne peut pas être lu comme document."""


class DocumentSansTexte(Exception):
    """Le document ne contient aucun texte exploitable."""


def comparer_documents(ancien: str, nouveau: str) -> str:
    """Retourne les différences entre deux textes."""
    differences = unified_diff(
        ancien.splitlines(),
        nouveau.splitlines(),
        fromfile="Procedure_v1",
        tofile="Procedure_v2",
        lineterm="",
    )
    return "\n".join(differences)


def _verifier_marqueur_eof(fichier: Path) -> None:
    """Un PDF valide doit se terminer par %%EOF (éventuellement suivi d'espaces)."""
    with fichier.open("rb") as flux:
        flux.seek(0, 2)
        taille = flux.tell()
        flux.seek(max(0, taille - 2048))
        fin = flux.read()

    if b"%%EOF" not in fin:
        raise DocumentIllisible(
            f"{fichier} : marqueur de fin PDF (%%EOF) absent, fichier probablement endommagé"
        )


def lire_document(chemin: str) -> str:
    """Lit un fichier texte ou PDF et retourne son contenu."""
    fichier = Path(chemin)

    if not fichier.exists():
        raise DocumentIntrouvable(f"{chemin} : fichier introuvable")

    if fichier.suffix.lower() == ".pdf":
        _verifier_marqueur_eof(fichier)

        from pypdf import PdfReader  # import tardif : seul le mode PDF en dépend

        try:
            lecteur = PdfReader(str(fichier))
            texte = "\n".join(page.extract_text() or "" for page in lecteur.pages)
        except Exception as erreur:
            raise DocumentIllisible(
                f"{fichier} : lecture PDF impossible ({type(erreur).__name__})"
            ) from erreur
    else:
        try:
            texte = fichier.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as erreur:
            raise DocumentIllisible(
                f"{fichier} : lecture impossible ({type(erreur).__name__})"
            ) from erreur

    if not texte.strip():
        raise DocumentSansTexte(
            f"{fichier} : aucun texte extractible. "
            "Le document est peut-être un scan : un OCR est nécessaire."
        )

    return texte


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage : python3 comparer_documents.py <ancien> <nouveau>")
        return 2

    try:
        ancien = lire_document(sys.argv[1])
        nouveau = lire_document(sys.argv[2])
    except DocumentIntrouvable as erreur:
        print(f"Erreur : {erreur}")
        return 3
    except DocumentIllisible as erreur:
        print(f"Erreur : document illisible — {erreur}")
        return 4
    except DocumentSansTexte as erreur:
        print(f"Erreur : document sans texte — {erreur}")
        return 5

    resultat = comparer_documents(ancien, nouveau)

    if resultat:
        print("Modifications détectées :\n")
        print(resultat)
    else:
        print("Aucune modification détectée.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
