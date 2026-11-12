"""Génère le document qualité du projet d'assistant de comparaison documentaire."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

SORTIE = Path("/Users/ibrahimkamate/Downloads/AI_PROJECT/Quality Doc AI Project.docx")
DOSSIER = Path(__file__).resolve().parent
RAG = DOSSIER.parent / "rag"


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
            ("Version", "1.10"),
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
            (
                "A7",
                "Sous-agents ignorés : OpenCode V2 rejetait la couleur déclarée "
                "(« purple », « blue »…) et le dièse non quoté en YAML",
                "Les six agents du projet n'étaient jamais chargés",
                "Couleurs converties en hexadécimal et entourées de guillemets",
                "Corrigée",
            ),
            (
                "A8",
                "Agent Plan inutilisable : modèle par défaut claude-fable-5-2 avec "
                "clé API Anthropic refusée (invalid x-api-key)",
                "Erreur immédiate, aucun plan produit",
                "Modèle par défaut fixé à opencode/deepseek-v4.1-flash-free",
                "Corrigée",
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
    document.add_paragraph(
        "Tests du pipeline RAG : 39 tests exécutés avec python3 -m unittest "
        "discover -s rag/tests, 39 réussis, 0 échec."
    )
    ajouter_tableau(
        document,
        ["Fichier de tests", "Nombre", "Objet"],
        [
            ("test_rag_lib.py", "6", "Parsing Markdown, découpage, métadonnées"),
            ("test_seuil.py", "11", "Décision d'abstention et détection de réserve"),
            ("test_lexical.py", "13", "Index FTS5, normalisation, couverture"),
            ("test_hybrid.py", "9", "Fusion RRF et reranker heuristique"),
        ],
    )
    document.add_paragraph(
        "Tests du moteur d'impact : 22 tests exécutés avec python3 -m unittest "
        "discover -s impact/tests, 22 réussis, 0 échec."
    )
    ajouter_tableau(
        document,
        ["Famille de tests", "Nombre", "Objet"],
        [
            ("Valeurs et changements", "6", "Extraction des nombres, diff, filtrage"),
            ("Qualification", "6", "Aligné, à mettre à jour, réserve, doute"),
            ("Analyse", "4", "Abstention, tri, enchaînement, absence d'écriture"),
            ("Rapport et CLI", "6", "Format Markdown, codes de sortie"),
        ],
    )
    document.add_paragraph(
        "Ces tests ne nécessitent ni Qdrant ni Ollama : ils s'exécutent avec la "
        "bibliothèque standard et restent donc utilisables en intégration continue."
    )

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
        "Étendre le corpus fictif aux formats Word et Excel.",
        "Ajouter une recherche hybride (dense + lexicale) et un reranker mesuré.",
        "Calibrer un seuil d'abstention sur les scores de retrieval.",
        "Construire le moteur d'analyse d'impact au-dessus du retriever.",
    ]:
        document.add_paragraph(action, style="List Number")

    document.add_heading("11. Corpus fictif (Mock Corpus)", level=1)
    document.add_paragraph(
        "Un corpus entièrement fictif a été créé dans "
        "/Users/ibrahimkamate/Documents/labo-ia/corpus. Il sert de terrain "
        "d'entraînement pour la comparaison, la détection de contradictions et "
        "l'analyse d'impact, sans aucune donnée réelle ou sensible."
    )
    ajouter_tableau(
        document,
        ["Domaine", "Documents", "Identifiants"],
        [
            ("Biologie", "4", "BIO-001 à BIO-004"),
            ("Santé / Pharma", "5", "PHA-001 à PHA-005"),
            ("Ressources humaines", "5", "RH-001 à RH-005"),
            ("Gouvernance documentaire", "4", "DOC-001 à DOC-004"),
            ("Versions de comparaison", "2", "PHA-001 v1.0 et v2.0"),
        ],
    )
    document.add_paragraph(
        "Chaque document comporte des métadonnées (identifiant, version, statut, "
        "propriétaire, domaine) et des références croisées. Un index CSV recense "
        "les fichiers."
    )
    document.add_paragraph(
        "Des anomalies sont introduites volontairement et documentées dans "
        "annotations/cas_de_test.md :"
    )
    for anomalie in [
        "Délai de déclaration d'écart : 2 jours (PHA-001) contre 5 jours (PHA-002).",
        "Conservation : 5 ans (PHA-003) contre 10 ans (PHA-004).",
        "Télétravail : 3 jours (RH-001) contre 2 jours pour le support (RH-002).",
        "Recrutement : 3 entretiens (RH-003) contre 2 dans le guide d'intégration (RH-005).",
        "Culture cellulaire : milieu renouvelé tous les 2 jours (BIO-001) contre un "
        "passage tous les 3 jours (BIO-002).",
    ]:
        document.add_paragraph(anomalie, style="List Bullet")
    document.add_paragraph(
        "Six cas de test (C1 à C6) décrivent les impacts attendus, y compris un cas "
        "sans preuve suffisante destiné à vérifier l'abstention du système. Ces "
        "cas sont des hypothèses à valider, pas une vérité métier."
    )
    document.add_paragraph(
        "Validation réalisée : la paire versions/PHA-001_v1.0.md et "
        "versions/PHA-001_v2.0.md a été comparée avec succès par le prototype "
        "(changements de délais, de classification, de conservation et de "
        "responsabilités identifiés)."
    )

    document.add_heading("12. Indexation RAG du corpus", level=1)
    document.add_paragraph(
        "Le corpus fictif a été indexé dans une base vectorielle locale afin de "
        "permettre la recherche sémantique et de préparer l'analyse d'impact. "
        "Aucun service cloud ni conteneur Docker n'est utilisé."
    )
    ajouter_tableau(
        document,
        ["Composant", "Choix retenu", "Justification"],
        [
            (
                "Découpage",
                "Par section Markdown (##), fenêtres de 1600 caractères",
                "Conserver le contexte et la section citable",
            ),
            (
                "Embeddings",
                "bge-m3 via Ollama (1024 dimensions)",
                "Multilingue, local, adapté au français",
            ),
            (
                "Base vectorielle",
                "Qdrant en mode local (fichiers)",
                "Aucun serveur ni Docker ; persistant et reconstructible",
            ),
            ("Collection", "corpus_labo_ia", "Une collection dédiée au corpus"),
        ],
    )
    document.add_paragraph(
        "Résultat de l'indexation : 143 chunks issus de 20 fichiers, embeddings "
        "calculés en 2,0 secondes sur la machine locale."
    )
    document.add_paragraph("Commandes du pipeline :")
    for commande in [
        "premier-test/.venv/bin/python rag/index_corpus.py",
        "premier-test/.venv/bin/python rag/search.py \"question\"",
        "premier-test/.venv/bin/python rag/evaluer.py",
    ]:
        document.add_paragraph(commande, style="List Bullet")

    document.add_paragraph(
        "Évaluation du rappel sur les cas C1 à C5 (documents attendus dans le "
        "top 5) :"
    )
    ajouter_tableau(
        document,
        ["Cas", "Question", "Résultat"],
        [
            ("C1", "Délai de déclaration d'écart", "OK — PHA-001, PHA-002"),
            ("C2", "Conservation des enregistrements", "OK — PHA-003, DOC-003"),
            ("C3", "Télétravail équipes support", "OK — RH-002"),
            ("C4", "Entretiens de recrutement", "OK — RH-003, RH-005"),
            ("C5", "Renouvellement du milieu de culture", "OK — BIO-001"),
        ],
    )
    document.add_paragraph(
        "Rappel@top5 : 5/5. Le cas C6 (conservation des dossiers RH) remonte "
        "PHA-004 avec un score de 0,65 ; ce document mentionne une durée de 5 ans "
        "pour les données RH administratives en la présentant comme une hypothèse "
        "à confirmer. Le système ne doit donc pas répondre comme à une règle "
        "établie : la nuance « hypothèse » doit être restituée."
    )
    document.add_paragraph("Limites de cette indexation :")
    for limite_rag in [
        "Recherche dense uniquement : pas encore de recherche lexicale ni de reranker.",
        "Aucun seuil d'abstention calibré ; les scores sont observés, pas décisionnels.",
        "Les scores ne sont pas comparables entre modèles d'embeddings.",
        "Les PDF image restent hors périmètre sans OCR.",
        "Validation humaine toujours requise avant toute conclusion d'impact.",
    ]:
        document.add_paragraph(limite_rag, style="List Bullet")

    document.add_heading("13. Gestion de projet GitHub", level=1)
    document.add_paragraph(
        "Le suivi du projet est centralisé sur le board GitHub Projects "
        "« AI Project_IK_GEDs » : "
        "https://github.com/users/ibrahka007/projects/1. "
        "Chaque étape du laboratoire y figure sous forme d'issue reliée au "
        "dépôt https://github.com/ibrahka007/labo-ia, avec un statut, une "
        "priorité et une taille."
    )
    document.add_paragraph(
        "Le board utilise trois champs personnalisés : Statut (Backlog, Ready, "
        "In progress, In review, Done), Priorité (P0, P1, P2) et Taille "
        "(XS, S, M, L, XL)."
    )
    ajouter_tableau(
        document,
        ["Statut", "Nombre", "Contenu"],
        [
            ("Done", "10", "Environnement, prototype de comparaison, gestion "
                           "des erreurs, document qualité, corpus fictif, "
                           "indexation RAG, sous-agents, recherche hybride, "
                           "seuil d'abstention, moteur d'analyse d'impact"),
            ("Ready", "0", "Aucune étape prête à démarrer"),
            ("Backlog", "5", "Word/Excel et OCR, interface web, jeu de 100 cas, "
                             "automatisation du document qualité, intégration "
                             "continue"),
            ("Total", "15", "10 étapes terminées, 5 actions ouvertes"),
        ],
    )
    document.add_paragraph("Répartition par priorité :")
    for ligne_priorite in [
        "P0 (critique) : indexation RAG, seuil d'abstention et moteur "
        "d'analyse d'impact — tous terminés.",
        "P1 (important) : prototype de comparaison, gestion des erreurs, "
        "document qualité, corpus fictif, recherche hybride, interface web, "
        "jeu de 100 cas.",
        "P2 (secondaire) : environnement, sous-agents, Word/Excel et OCR, "
        "automatisation du document qualité, intégration continue.",
    ]:
        document.add_paragraph(ligne_priorite, style="List Bullet")
    document.add_paragraph(
        "Chaque issue décrit le contexte, le résultat attendu, les critères "
        "d'acceptation, les fichiers concernés et les dépendances. Une étape "
        "n'est déclarée terminée que si le code, les tests et le document "
        "qualité sont à jour."
    )
    document.add_paragraph(
        "Anomalie rencontrée lors de la synchronisation : l'identifiant de "
        "l'option « L » du champ Taille était erroné (un caractère manquant), "
        "ce qui provoquait le rejet de la mise à jour. Correction appliquée et "
        "script rendu idempotent (relance sans doublon) avec reprise sur "
        "erreur réseau."
    )

    document.add_heading("14. Consolidation du dépôt et nettoyage", level=1)
    document.add_paragraph(
        "Trois copies obsolètes du dépôt historique AI_Project_repo occupaient "
        "encore le disque et pouvaient laisser croire à plusieurs versions du "
        "projet. Elles ont été supprimées après vérification et sauvegarde."
    )
    ajouter_tableau(
        document,
        ["Emplacement supprimé", "Nature", "Contenu vérifié avant suppression"],
        [
            (
                "~/AI_Project_repo",
                "Clone Git du dépôt historique",
                "Aucun commit non poussé ; copie partielle de labo-ia",
            ),
            (
                "~/Documents/GitHub/AI_Project_repo",
                "Clone GitHub Desktop",
                "Synchronisé avec origin/main ; échantillons déjà présents "
                "dans ~/Downloads/AI_PROJECT",
            ),
            (
                "~/copilot-worktrees/AI_Project_repo",
                "Worktrees Copilot du clone ci-dessus",
                "Retirés avec git worktree remove --force puis prune",
            ),
        ],
    )
    document.add_paragraph(
        "Contrôles effectués avant suppression : les cinq PDF d'échantillons "
        "(AR-001_v1, AR-001_v2, 01_pdf_endommage, 02_pdf_illisible, "
        "03_pdf_sans_texte_extractible) sont identiques octet pour octet à ceux "
        "de ~/Downloads/AI_PROJECT ; aucun commit local n'était en attente ; "
        "l'archive de sécurité a été testée (321 entrées)."
    )
    document.add_paragraph(
        "Une archive complète, incluant l'historique Git et la branche locale "
        "non poussée ibrahka007-ai-project-readme, a été créée avant "
        "suppression : ~/Documents/_archive_AI_Project_2026-11-11.tar.gz "
        "(9,9 Mo). Restauration possible avec :"
    )
    document.add_paragraph(
        "tar -xzf ~/Documents/_archive_AI_Project_2026-11-11.tar.gz -C ~/",
        style="List Bullet",
    )
    document.add_paragraph(
        "Après nettoyage, un seul dépôt de travail subsiste : "
        "~/Documents/labo-ia, relié à github.com/ibrahka007/labo-ia. Le document "
        "qualité reste dans ~/Downloads/AI_PROJECT. Les copies supprimées ne "
        "contenaient aucune donnée unique."
    )
    document.add_paragraph("Résultat : environ 10,8 Mo libérés.", style="List Bullet")

    document.add_heading("15. Seuil d'abstention et réserves", level=1)
    document.add_paragraph(
        "La recherche sémantique seule ne sait pas dire « je ne sais pas » : une "
        "question hors corpus remonte malgré tout cinq passages, avec des scores "
        "de 0,41 à 0,65. Deux garde-fous ont donc été ajoutés."
    )
    document.add_paragraph("Méthode de calibration", style="Heading 2")
    document.add_paragraph(
        "Deux populations ont été mesurées avec le même index : cinq questions "
        "dont la réponse existe dans le corpus (C1 à C5) et treize questions hors "
        "corpus, dont le cas C6 sur la conservation des dossiers RH."
    )
    ajouter_tableau(
        document,
        ["Population", "Nombre", "Score top1 observé"],
        [
            ("Réponse dans le corpus", "5", "0,651 à 0,768"),
            ("Hors corpus (abstention attendue)", "13", "0,409 à 0,650"),
        ],
    )
    document.add_paragraph(
        "Un seuil de 0,65 sépare les deux populations sur cet échantillon : "
        "5/5 réponses conservées, 13/13 abstentions correctes, soit 18/18 cas "
        "traités correctement et 13 fausses réponses évitées."
    )
    document.add_paragraph("Limite majeure de cette calibration", style="Heading 2")
    document.add_paragraph(
        "La marge est quasi nulle. Le cas légitime le plus bas (C4, processus de "
        "recrutement) obtient 0,651 et le cas d'abstention le plus haut (C6) "
        "obtient 0,650 : un écart d'un millième. Le succès du seuil sur C6 dépend "
        "donc du quatrième chiffre du score et n'est pas robuste. Baisser le seuil "
        "fait répondre sur C6 ; le monter fait refuser C4."
    )
    document.add_paragraph(
        "Conclusion honnête : en recherche dense seule, C4 et C6 ne sont pas "
        "séparables de façon fiable. Le seuil de 0,65 est retenu comme valeur "
        "provisoire, à re-mesurer sur le jeu de 100 cas (issue 13) et à consolider "
        "par la recherche hybride et un reranker (issue 8)."
    )
    document.add_paragraph("Second garde-fou : détection de réserve", style="Heading 2")
    document.add_paragraph(
        "Certains passages ne formulent pas une règle établie. Le système détecte "
        "les marqueurs « hypothèse », « à confirmer », « sous réserve », "
        "« non confirmé » et « à valider », puis affiche explicitement que la "
        "valeur ne doit pas être présentée comme une obligation."
    )
    document.add_paragraph(
        "Exemple vérifié : interrogé sur la conservation des dossiers RH, le "
        "système s'abstient (score 0,650) et précise que le meilleur passage "
        "(PHA-004) présente la durée de cinq ans comme une hypothèse à confirmer "
        "juridiquement. Avec un seuil abaissé à 0,60, le passage est affiché mais "
        "accompagné de la réserve : la nuance n'est jamais perdue."
    )
    document.add_paragraph("Mise en œuvre", style="Heading 2")
    for ligne_seuil in [
        "Seuil par défaut : SEUIL_ABSTENTION = 0,65 dans rag/rag_lib.py.",
        "Décision centralisée dans decide_reponse(), testable sans Qdrant.",
        "Option --seuil dans rag/search.py ; --seuil 0 désactive l'abstention.",
        "Calibration reproductible : rag/calibrer_seuil.py.",
        "Évaluation : rag/evaluer.py rapporte rappel et abstentions.",
        "Tests : 17/17 réussis, dont 10 sur la décision et les réserves.",
    ]:
        document.add_paragraph(ligne_seuil, style="List Bullet")

    document.add_heading("16. Recherche hybride et reranker", level=1)
    document.add_paragraph(
        "Objectif : compenser la faiblesse de la recherche dense sur les valeurs "
        "littérales (durées, seuils, identifiants) en ajoutant un canal lexical, "
        "puis un reranker. Tout reste local, sans nouvelle dépendance."
    )
    ajouter_tableau(
        document,
        ["Composant", "Choix retenu", "Justification"],
        [
            (
                "Canal lexical",
                "BM25 via SQLite FTS5 (bibliothèque standard)",
                "Zéro dépendance ; index reconstructible en une commande",
            ),
            (
                "Normalisation",
                "Minuscules, sans accents, ponctuation réduite",
                "Évite les échecs sur « écart » / « ecart »",
            ),
            (
                "Précision",
                "Requête ET, repli sur OU si aucun résultat",
                "Un terme conjugué différemment ne doit pas vider la réponse",
            ),
            (
                "Fusion",
                "Reciprocal Rank Fusion (k = 60)",
                "Aucun paramètre à ajuster, donc pas de sur-ajustement",
            ),
            (
                "Reranker",
                "Heuristique : couverture 70 %, titre 20 %, rang 10 %",
                "Référence mesurable avant tout modèle neuronal",
            ),
        ],
    )
    document.add_paragraph("Résultats comparés sur les 18 cas", style="Heading 2")
    ajouter_tableau(
        document,
        ["Mode", "Rappel@5", "MRR", "Abstentions", "Non sécurisées"],
        [
            ("Dense", "5/5", "1,000", "13/13", "0"),
            ("Lexical", "5/5", "1,000", "non calibrée", "non applicable"),
            ("Hybride", "5/5", "1,000", "13/13", "0"),
        ],
    )
    document.add_paragraph(
        "Résultat honnête : l'hybride n'apporte aucun gain mesurable sur ce "
        "corpus. Le rappel et le MRR sont déjà saturés en dense, et la fusion ne "
        "modifie pas la marge C4 / C6, qui reste de 0,001."
    )
    document.add_paragraph("Décisions qui en découlent", style="Heading 2")
    for decision_hybride in [
        "Le mode dense reste le mode par défaut : aucune complexité ajoutée au "
        "chemin de production sans preuve de gain.",
        "L'hybride reste disponible pour expérimentation, mesuré et testé.",
        "L'abstention conserve le signal dense calibré : le score RRF n'est pas "
        "comparable et ne peut pas servir de seuil.",
        "La confusion C4 / C6 n'est pas résolue par l'hybride ; elle ne le sera "
        "pas non plus par un reranker, qui réordonne sans créer d'information.",
    ]:
        document.add_paragraph(decision_hybride, style="List Bullet")
    document.add_paragraph(
        "Conséquence pour l'analyse d'impact : le moteur ne doit pas s'appuyer "
        "sur l'espoir d'un meilleur score, mais sur les deux garde-fous vérifiés "
        "— le seuil d'abstention et la détection de réserve. Une réponse hors "
        "corpus reste refusée (13/13) et aucune réponse n'est produite sans "
        "réserve lorsqu'une hypothèse est en jeu (0 non sécurisée)."
    )
    document.add_paragraph("Limites", style="Heading 2")
    for limite_hybride in [
        "18 cas seulement : insuffisant pour trancher entre dense et hybride.",
        "Le reranker neuronal local n'a pas été installé : il ajouterait 1,2 Go.",
        "Le mode lexical n'a pas de seuil calibré ; il ne sert qu'au diagnostic.",
        "La comparaison devra être refaite sur le jeu de 100 cas (issue 13).",
    ]:
        document.add_paragraph(limite_hybride, style="List Bullet")

    document.add_heading("17. Moteur d'analyse d'impact", level=1)
    document.add_paragraph(
        "Objectif du laboratoire : à partir d'un changement documentaire, "
        "identifier les passages du corpus qui risquent d'être concernés, avec "
        "preuve et niveau de confiance. Le moteur ne modifie jamais un "
        "document : il produit un rapport soumis à validation humaine."
    )
    document.add_paragraph("Chaîne de traitement", style="Heading 2")
    for etape_impact in [
        "Changement décrit par l'utilisateur, ou déduit d'un diff entre deux "
        "versions (difflib).",
        "Filtrage des métadonnées et des titres Markdown : ils changent à "
        "chaque version sans modifier une règle.",
        "Recherche des passages concernés, avec le seuil d'abstention du "
        "pipeline RAG.",
        "Qualification de chaque passage : aligné, à mettre à jour, réserve, "
        "à vérifier ou preuve insuffisante.",
        "Rapport Markdown avec citation (document, version, section) et "
        "validation humaine obligatoire.",
    ]:
        document.add_paragraph(etape_impact, style="List Number")
    ajouter_tableau(
        document,
        ["Type", "Signification", "Confiance"],
        [
            (
                "aligné",
                "Le passage énonce déjà la nouvelle valeur dans un contexte "
                "comparable",
                "haute",
            ),
            (
                "à mettre à jour",
                "Le passage reprend la règle avec une valeur différente",
                "haute ou moyenne",
            ),
            (
                "réserve",
                "Le passage présente la valeur comme une hypothèse à confirmer",
                "basse",
            ),
            (
                "à vérifier",
                "Recouvrement partiel : la portée du changement reste à établir",
                "basse",
            ),
            (
                "preuve insuffisante",
                "Aucun passage au-dessus du seuil : aucune conclusion",
                "basse",
            ),
        ],
    )
    document.add_paragraph("Deux règles de prudence", style="Heading 2")
    document.add_paragraph(
        "Première règle : un nombre identique ne suffit pas. « 5 ans » pour les "
        "écarts qualité et « 5 ans » pour les dossiers RH sont deux règles "
        "distinctes. La qualification « aligné » exige donc aussi une "
        "couverture suffisante des termes du changement."
    )
    document.add_paragraph(
        "Seconde règle : une réserve prime sur toute autre qualification. Un "
        "passage qui dit « hypothèse à confirmer » n'est jamais présenté comme "
        "une règle établie, même si sa valeur correspond."
    )
    document.add_paragraph("Vérifications réalisées", style="Heading 2")
    ajouter_tableau(
        document,
        ["Scénario", "Résultat observé"],
        [
            (
                "Changement « ouvrir la fiche sous 24 heures »",
                "PHA-001 section 3 qualifié « à mettre à jour » (haute) ; "
                "section 5 « à vérifier » (basse)",
            ),
            (
                "Changement sur les dossiers RH (5 ans)",
                "Abstention à 0,65 ; avec seuil abaissé à 0,60, PHA-004 est "
                "qualifié « réserve », jamais « aligné »",
            ),
            (
                "Changement hors corpus (budget de formation)",
                "« preuve insuffisante », aucune conclusion produite",
            ),
            (
                "Diff PHA-001 v1.0 / v2.0",
                "Changements de métadonnées écartés ; seules les règles "
                "modifiées sont analysées",
            ),
        ],
    )
    document.add_paragraph(
        "Garantie d'absence d'écriture : un test vérifie que l'analyse ne "
        "modifie aucun fichier. Le seul écrit possible est le rapport demandé "
        "explicitement avec l'option --sortie."
    )
    document.add_paragraph("Limites", style="Heading 2")
    for limite_impact in [
        "Le diff travaille ligne à ligne : une reformulation complète produit "
        "beaucoup de changements.",
        "Aucune équivalence d'unités : « 1 jour » n'est pas reconnu comme "
        "« 24 heures ».",
        "Pas de détection de contradiction entre deux documents du corpus.",
        "La qualification reste heuristique : elle guide la relecture, elle ne "
        "la remplace pas.",
    ]:
        document.add_paragraph(limite_impact, style="List Bullet")

    document.add_heading("18. Historique des révisions", level=1)
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
            (
                "1.3",
                "11/11/2026",
                "Ajout du corpus fictif (22 documents, 5 domaines) et des cas de "
                "test d'impact.",
            ),
            (
                "1.4",
                "11/11/2026",
                "Ajout de l'indexation RAG locale (bge-m3, Qdrant, 143 chunks) et "
                "des résultats d'évaluation C1–C6.",
            ),
            (
                "1.5",
                "11/11/2026",
                "Ajout de la section Gestion de projet GitHub : board, 15 issues, "
                "statuts, priorités et tailles ; sous-agents expert métier et chef "
                "de projet.",
            ),
            (
                "1.6",
                "11/11/2026",
                "Consolidation du dépôt : suppression des trois copies obsolètes "
                "d'AI_Project_repo après archivage et vérification ; board GitHub "
                "complété (15 issues).",
            ),
            (
                "1.7",
                "11/11/2026",
                "Ajout du seuil d'abstention (0,65) et de la détection de réserve ; "
                "calibration sur 18 cas, 13 fausses réponses évitées ; limite de "
                "marge documentée.",
            ),
            (
                "1.8",
                "11/11/2026",
                "Correction du chargement des sous-agents (couleurs) et du modèle "
                "par défaut de l'agent Plan ; anomalies A7 et A8 documentées.",
            ),
            (
                "1.9",
                "12/11/2026",
                "Ajout de la recherche hybride (BM25 FTS5, fusion RRF, reranker "
                "heuristique) et comparaison dense / lexical / hybride sur 18 cas ; "
                "aucun gain mesuré, mode dense conservé par défaut.",
            ),
            (
                "1.10",
                "12/11/2026",
                "Ajout du moteur d'analyse d'impact : qualification des passages, "
                "rapport Markdown, garantie d'absence d'écriture ; 22 tests.",
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

    document.add_page_break()
    document.add_heading("Annexe D — rag/rag_lib.py", level=1)
    document.add_paragraph(
        "Bibliothèque du pipeline RAG : parsing, découpage et embeddings."
    )
    ajouter_bloc_code(document, RAG / "rag_lib.py")

    document.add_page_break()
    document.add_heading("Annexe E — rag/index_corpus.py", level=1)
    document.add_paragraph(
        "Construction de l'index Qdrant local."
    )
    ajouter_bloc_code(document, RAG / "index_corpus.py")

    document.add_page_break()
    document.add_heading("Annexe F — rag/search.py", level=1)
    document.add_paragraph(
        "Recherche sémantique dans l'index."
    )
    ajouter_bloc_code(document, RAG / "search.py")

    document.add_page_break()
    document.add_heading("Annexe G — rag/evaluer.py", level=1)
    document.add_paragraph(
        "Évaluation du rappel sur les cas C1 à C6."
    )
    ajouter_bloc_code(document, RAG / "evaluer.py")

    document.add_page_break()
    document.add_heading("Annexe H — rag/calibrer_seuil.py", level=1)
    document.add_paragraph(
        "Calibration du seuil d'abstention sur les cas connus et hors corpus."
    )
    ajouter_bloc_code(document, RAG / "calibrer_seuil.py")

    document.add_page_break()
    document.add_heading("Annexe I — rag/lexical.py", level=1)
    document.add_paragraph(
        "Index lexical BM25 (SQLite FTS5) : normalisation, jetons et recherche."
    )
    ajouter_bloc_code(document, RAG / "lexical.py")

    document.add_page_break()
    document.add_heading("Annexe J — rag/hybrid.py", level=1)
    document.add_paragraph(
        "Fusion RRF des canaux dense et lexical, puis reranker heuristique."
    )
    ajouter_bloc_code(document, RAG / "hybrid.py")

    document.add_page_break()
    document.add_heading("Annexe K — impact/moteur.py", level=1)
    document.add_paragraph(
        "Extraction des changements et qualification des passages impactés."
    )
    ajouter_bloc_code(document, DOSSIER.parent / "impact" / "moteur.py")

    document.add_page_break()
    document.add_heading("Annexe L — impact/analyser.py", level=1)
    document.add_paragraph(
        "Interface en ligne de commande du moteur d'analyse d'impact."
    )
    ajouter_bloc_code(document, DOSSIER.parent / "impact" / "analyser.py")

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
