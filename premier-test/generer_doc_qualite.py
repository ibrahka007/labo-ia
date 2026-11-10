"""Génère le document qualité du projet d'assistant de comparaison documentaire."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

SORTIE = Path("/Users/ibrahimkamate/Downloads/AI_PROJECT/Quality Doc AI Project.docx")
DOSSIER = Path(__file__).resolve().parent


def ajouter_tableau(document, entetes, lignes):
    tableau = document.add_table(rows=1, cols=len(entetes))
    tableau.style = "Table Grid"
    for index, entete in enumerate(entetes):
        cellule = tableau.rows[0].cells[index]
        cellule.text = entete
        for run in cellule.paragraphs[0].runs:
            run.bold = True
    for ligne in lignes:
        cellules = tableau.add_row().cells
        for index, valeur in enumerate(ligne):
            cellules[index].text = str(valeur)
    document.add_paragraph()
    return tableau


def ajouter_bloc_code(document, chemin):
    """Insère un fichier Python en bloc monospace avec fond gris clair."""
    code = Path(chemin).read_text(encoding="utf-8")
    for ligne in code.splitlines():
        paragraphe = document.add_paragraph()
        paragraphe.paragraph_format.space_before = Pt(0)
        paragraphe.paragraph_format.space_after = Pt(0)
        paragraphe.paragraph_format.line_spacing = 1.0

        run = paragraphe.add_run(ligne if ligne else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(8)

        ombre = OxmlElement("w:shd")
        ombre.set(qn("w:fill"), "F2F2F2")
        paragraphe._p.get_or_add_pPr().append(ombre)


def construire_document():
    document = Document()

    document.core_properties.author = "Ibrahim Kamate"
    document.core_properties.title = "Quality Doc AI Project"

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    titre = document.add_heading("Quality Doc AI Project", level=0)
    titre.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sous_titre = document.add_paragraph(
        "Journal qualité — assistant de comparaison documentaire"
    )
    sous_titre.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_heading("1. Informations du document", level=1)
    ajouter_tableau(
        document,
        ["Champ", "Valeur"],
        [
            ("Version", "1.2"),
            ("Date", "08/11/2026"),
            ("Statut", "Étape de comparaison documentaire validée"),
            ("Périmètre", "Projet premier-test (comparaison de fichiers texte et PDF)"),
            (
                "Emplacement du document",
                "/Users/ibrahimkamate/Downloads/AI_PROJECT/Quality Doc AI Project.docx",
            ),
            (
                "Sources",
                "/Users/ibrahimkamate/Downloads/AI_PROJECT/AI project_files_samples/",
            ),
            ("Auteur", "Ibrahim Kamate"),
            (
                "Règle de mise à jour",
                "Ce document est mis à jour à chaque étape de travail : nouvelle "
                "fonctionnalité, anomalie, correction, test ou décision.",
            ),
            (
                "Avertissement",
                "Les informations marquées « hypothèse » ou « non vérifié » ne sont pas "
                "des faits établis.",
            ),
        ],
    )

    document.add_heading("2. Objet et périmètre", level=1)
    document.add_paragraph(
        "Ce document trace les étapes réalisées pour construire un premier prototype "
        "capable de comparer deux versions d'un document et d'en afficher les "
        "différences. Il consigne également les anomalies rencontrées, les corrections "
        "apportées et les résultats des tests."
    )
    document.add_paragraph(
        "Le périmètre couvre la lecture de fichiers texte et PDF textuels, la "
        "comparaison ligne à ligne et la gestion des erreurs de lecture. L'analyse "
        "d'impact métier, l'interface graphique, la recherche RAG et l'orchestration "
        "multi-agents sont hors périmètre à ce stade."
    )

    document.add_heading("3. Environnement de travail", level=1)
    ajouter_tableau(
        document,
        ["Élément", "Valeur constatée", "Remarque"],
        [
            ("Système", "macOS (Apple Silicon)", "Mac utilisé comme station locale"),
            ("Python", "3.9.6 (système)", "Interpréteur fourni avec les outils Apple"),
            (
                "Environnement virtuel",
                "premier-test/.venv",
                "Dépendances locales au projet, aucune installation globale",
            ),
            ("pypdf", "6.21.4", "Extraction du texte des PDF"),
            ("python-docx", "1.2.0", "Génération du présent document"),
            ("opencode", "v2.2.5", "Outil de développement"),
            ("Ollama", "0.40.15", "Moteur d'inférence local"),
            ("Modèle local", "gemma4:12b (7,7 Go)", "Disponible, non utilisé dans ce prototype"),
            (
                "Dépendances externes",
                "unittest, difflib, pathlib",
                "Bibliothèques standard de Python",
            ),
        ],
    )

    document.add_heading("4. Déroulé des étapes", level=1)
    ajouter_tableau(
        document,
        ["N°", "Étape", "Action réalisée", "Résultat"],
        [
            ("1", "Préparation", "Création du dossier premier-test", "Dossier opérationnel"),
            (
                "2",
                "Premier prototype",
                "Script comparant deux chaînes de texte codées en dur",
                "Diff des modifications affiché",
            ),
            (
                "3",
                "Tests initiaux",
                "Trois cas unittest : textes identiques, ligne modifiée, ligne ajoutée",
                "3 tests réussis",
            ),
            (
                "4",
                "Lecture de fichiers",
                "Ajout de la lecture par chemin (texte et PDF) et de pypdf",
                "Comparaison de fichiers réels possible",
            ),
            (
                "5",
                "Comparaison réelle",
                "Comparaison de AR-001_v1.pdf et AR-001_v2.pdf",
                "Diff complet produit, changements identifiés",
            ),
            (
                "6",
                "Gestion des erreurs",
                "Exceptions dédiées, messages personnalisés, codes de sortie",
                "Plus de faux négatif ni de traceback",
            ),
            (
                "7",
                "Tests de robustesse",
                "Fichier absent, PDF endommagé, document sans texte, texte valide",
                "7 tests réussis au total",
            ),
        ],
    )

    document.add_heading("5. Anomalies et corrections", level=1)
    ajouter_tableau(
        document,
        ["ID", "Anomalie observée", "Impact", "Correction apportée", "Statut"],
        [
            (
                "A1",
                "Le script ignorait les arguments et comparait deux textes codés en dur",
                "Les PDF fournis n'étaient pas réellement lus",
                "Lecture des chemins en arguments, extraction PDF via pypdf",
                "Corrigée",
            ),
            (
                "A2",
                "Deux documents sans texte produisaient « Aucune modification détectée »",
                "Faux négatif pouvant masquer un scan non exploitable",
                "Détection d'un texte vide ou blanc, message dédié et code 5",
                "Corrigée",
            ),
            (
                "A3",
                "Fichier absent : traceback Python exposé à l'utilisateur",
                "Message technique peu exploitable",
                "Exception DocumentIntrouvable, message clair, code 3",
                "Corrigée",
            ),
            (
                "A4",
                "PDF endommagé non géré explicitement",
                "Erreur technique ou comportement indéterminé",
                "Contrôle du marqueur %%EOF et capture des erreurs pypdf, code 4",
                "Corrigée",
            ),
            (
                "A5",
                "Impossible de distinguer un scan illisible d'un scan lisible sans OCR",
                "Les deux sont signalés comme sans texte extractible",
                "Limite documentée ; OCR à décider séparément",
                "Ouverte",
            ),
            (
                "A6",
                "Nom de fichier comparateur.py demandé alors que le script est comparer_documents.py",
                "Risque de confusion dans les commandes",
                "Nom réel documenté ; renommage possible sur demande",
                "Documentée",
            ),
        ],
    )

    document.add_heading("6. Résultats des tests", level=1)
    document.add_paragraph(
        "Commande : python3 -m unittest -v (exécutée depuis le dossier premier-test)."
    )
    ajouter_tableau(
        document,
        ["Test", "Cas vérifié", "Résultat"],
        [
            ("test_textes_identiques", "Deux textes identiques", "Réussi"),
            ("test_ligne_modifiee", "Une ligne remplacée", "Réussi"),
            ("test_ligne_ajoutee", "Une ligne ajoutée", "Réussi"),
            ("test_fichier_absent", "Chemin inexistant", "Réussi"),
            ("test_pdf_endommage", "PDF invalide sans marqueur de fin", "Réussi"),
            ("test_document_sans_texte", "Fichier texte vide", "Réussi"),
            ("test_texte_valide", "Lecture nominale d'un fichier texte", "Réussi"),
        ],
    )
    document.add_paragraph("Synthèse : 7 tests exécutés, 7 réussis, 0 échec.")

    document.add_heading("7. Comparaison AR-001 v1.0 / v2.0", level=1)
    document.add_paragraph(
        "La comparaison des deux PDF fictifs a mis en évidence les changements "
        "suivants :"
    )
    for changement in [
        "Version 1.0 → 2.0 ; dates d'approbation et d'application repoussées.",
        "Périmètre étendu au site de fabrication, avec évaluation d'impact sécurité.",
        "Assurance qualité désormais cosignataire de l'autorisation de transmission.",
        "Formulaire FRM-AR-001 v1.0 → v2.0.",
        "Enregistrement de la demande : 5 → 2 jours ouvrés.",
        "Qualification : 10 → 5 jours ouvrés, avec nouvelle catégorie « critique ».",
        "Dossier enrichi : matrice des documents impactés et checklist signée.",
        "Revue documentaire AQ : 15 → 10 jours ouvrés.",
        "Mise à jour du registre : 3 → 1 jour ouvré.",
        "Conservation : 5 → 10 ans.",
        "Formation avec contrôle de compréhension et règle de transition des dossiers en cours.",
    ]:
        document.add_paragraph(changement, style="List Bullet")

    document.add_paragraph(
        "Les documents AR-001 sont des documents fictifs destinés à l'exercice. "
        "Aucune exigence réglementaire réelle ne doit en être déduite."
    )

    document.add_heading("8. Règles de gestion des erreurs", level=1)
    ajouter_tableau(
        document,
        ["Situation", "Message", "Code de sortie"],
        [
            ("Succès (diff ou aucune différence)", "Résultat affiché", "0"),
            ("Nombre d'arguments incorrect", "Usage du script", "2"),
            ("Fichier introuvable", "Erreur : fichier introuvable", "3"),
            ("PDF ou fichier illisible", "Erreur : document illisible", "4"),
            ("Aucun texte extractible", "Erreur : document sans texte, OCR possible", "5"),
        ],
    )

    document.add_heading("9. Limites connues", level=1)
    for limite in [
        "La comparaison est un diff ligne à ligne : elle ne qualifie pas l'impact métier.",
        "Les PDF image sans couche texte ne sont pas océrisés.",
        "Un PDF peut être visuellement illisible tout en restant techniquement valide ; "
        "le programme ne peut pas en juger sans OCR ou analyse d'image.",
        "Les libellés du diff restent génériques (Procedure_v1 / Procedure_v2).",
        "Aucune mesure de performance ou de consommation mémoire n'a été réalisée.",
    ]:
        document.add_paragraph(limite, style="List Bullet")

    document.add_heading("10. Prochaines actions", level=1)
    for action in [
        "Personnaliser les messages d'erreur selon le contexte d'usage.",
        "Décider de l'ajout d'un OCR (Tesseract ou Vision macOS) pour les PDF image.",
        "Afficher le nom réel des fichiers comparés dans l'en-tête du diff.",
        "Ajouter un formulaire fictif lié (FRM-AR-001) et rechercher les passages impactés.",
        "Préparer le corpus annoté et les critères d'évaluation avant d'introduire le RAG.",
    ]:
        document.add_paragraph(action, style="List Number")

    document.add_heading("11. Historique des révisions", level=1)
    ajouter_tableau(
        document,
        ["Version", "Date", "Nature de la modification"],
        [
            (
                "1.0",
                "08/11/2026",
                "Création du document : étapes, anomalies, tests, limites et actions.",
            ),
            (
                "1.1",
                "08/11/2026",
                "Ajout de l'auteur Ibrahim Kamate et de la règle de mise à jour à "
                "chaque étape de travail.",
            ),
            (
                "1.2",
                "08/11/2026",
                "Ajout en annexe du code Python du projet.",
            ),
        ],
    )

    document.add_page_break()
    document.add_heading("Annexe A — comparer_documents.py", level=1)
    document.add_paragraph(
        "Script principal : lecture des fichiers texte/PDF, comparaison et gestion "
        "des erreurs."
    )
    ajouter_bloc_code(document, DOSSIER / "comparer_documents.py")

    document.add_page_break()
    document.add_heading("Annexe B — test_comparateur.py", level=1)
    document.add_paragraph(
        "Tests unitaires (unittest) : comparaison, lecture et cas d'erreur."
    )
    ajouter_bloc_code(document, DOSSIER / "test_comparateur.py")

    document.add_page_break()
    document.add_heading("Annexe C — generer_doc_qualite.py", level=1)
    document.add_paragraph(
        "Outil de génération du présent document qualité."
    )
    ajouter_bloc_code(document, DOSSIER / "generer_doc_qualite.py")

    document.add_paragraph()
    document.add_paragraph(
        "Fin du document. Les éléments non vérifiés doivent être confirmés avant "
        "toute utilisation en contexte professionnel."
    )

    return document


if __name__ == "__main__":
    document = construire_document()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    document.save(SORTIE)
    print(f"Document créé : {SORTIE}")
