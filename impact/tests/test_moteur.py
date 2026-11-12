"""Tests du moteur d'analyse d'impact (sans Qdrant, Ollama ni écriture)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "impact"))
sys.path.insert(0, str(RACINE / "rag"))

from moteur import (  # noqa: E402
    Changement,
    analyser_changement,
    analyser_textes,
    est_metadonnee,
    extraire_changements,
    qualifier,
    rendre_rapport,
    valeurs_numeriques,
)


def candidat(doc_id, section, texte, score=0.7, version="1.0"):
    return {
        "doc_id": doc_id,
        "titre": "Titre",
        "version": version,
        "statut": "Approuvé",
        "domaine": "Test",
        "fichier": f"test/{doc_id}.md",
        "section": section,
        "texte": texte,
        "score": score,
    }


class TestValeurs(unittest.TestCase):
    def test_extrait_les_nombres(self):
        self.assertEqual(valeurs_numeriques("sous 24 heures ou 2 jours"), {"24", "2"})

    def test_valeurs_decimale_avec_virgule(self):
        self.assertEqual(valeurs_numeriques("seuil de 0,5 mg"), {"0,5"})

    def test_texte_vide(self):
        self.assertEqual(valeurs_numeriques(""), set())


class TestExtractionChangements(unittest.TestCase):
    def test_detecte_une_ligne_modifiee(self):
        avant = "Ouvrir la fiche sous 2 jours ouvrés."
        apres = "Ouvrir la fiche sous 24 heures."

        changements = extraire_changements(avant, apres)

        self.assertEqual(len(changements), 1)
        self.assertIn("24 heures", changements[0].apres)
        self.assertIn("2 jours", changements[0].avant)

    def test_ignore_les_metadonnees(self):
        avant = "---\nversion: 1.0\n---\n\n## 1. Objet\n\nTexte."
        apres = "---\nversion: 2.0\n---\n\n## 1. Objet\n\nTexte."

        self.assertEqual(extraire_changements(avant, apres), [])

    def test_ignore_un_titre_modifie(self):
        self.assertEqual(
            extraire_changements("# Ancien titre", "# Nouveau titre"), []
        )

    def test_detecte_est_metadonnee(self):
        self.assertTrue(est_metadonnee("statut: Approuvé"))
        self.assertTrue(est_metadonnee("## 3. Déclaration"))
        self.assertTrue(est_metadonnee("---"))
        self.assertFalse(est_metadonnee("- Ouvrir la fiche sous 2 jours."))

    def test_suppression_pure_ignoree(self):
        self.assertEqual(extraire_changements("Une ligne.", ""), [])


class TestQualification(unittest.TestCase):
    def setUp(self):
        self.changement = Changement(
            avant="Ouvrir la fiche sous 2 jours ouvrés",
            apres="Ouvrir la fiche sous 24 heures",
        )

    def test_aligne_quand_la_valeur_cible_est_presente(self):
        impact = qualifier(
            self.changement,
            candidat("PHA-001", "3. Déclaration", "Ouvrir la fiche sous 24 heures."),
        )

        self.assertEqual(impact.type, "aligné")
        self.assertEqual(impact.confiance, "haute")

    def test_a_mettre_a_jour_quand_la_valeur_differe(self):
        impact = qualifier(
            self.changement,
            candidat(
                "PHA-001",
                "3. Déclaration",
                "Ouvrir la fiche d'écart sous 2 jours ouvrés après identification.",
            ),
        )

        self.assertEqual(impact.type, "à mettre à jour")
        self.assertIn(impact.confiance, ("haute", "moyenne"))

    def test_reserve_prioritaire_sur_la_valeur(self):
        impact = qualifier(
            self.changement,
            candidat(
                "PHA-004",
                "3. Durées",
                "Ouvrir la fiche sous 2 jours, hypothèse à confirmer.",
            ),
        )

        self.assertEqual(impact.type, "réserve")
        self.assertTrue(impact.reserves)

    def test_hors_sujet_sans_terme_commun(self):
        impact = qualifier(
            self.changement,
            candidat("BIO-001", "Culture", "Renouveler le milieu tous les 3 jours."),
        )

        self.assertEqual(impact.type, "hors sujet")

    def test_meme_valeur_mais_regle_differente(self):
        changement = Changement(apres="Les dossiers RH sont conservés 5 ans")
        impact = qualifier(
            changement,
            candidat(
                "PHA-001",
                "6. Conservation",
                "Conserver le dossier d'écart 5 ans après clôture.",
            ),
        )

        self.assertNotEqual(impact.type, "aligné")
        self.assertIn(impact.type, ("à vérifier", "hors sujet"))

    def test_doute_quand_couverture_partielle(self):
        impact = qualifier(
            self.changement,
            candidat(
                "PHA-001",
                "5. Investigation",
                "Réaliser l'investigation d'un écart sous 10 jours ouvrés.",
            ),
        )

        self.assertEqual(impact.type, "à vérifier")


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        self.changement = Changement(
            avant="Ouvrir la fiche sous 2 jours",
            apres="Ouvrir la fiche sous 24 heures",
        )

    def test_preuve_insuffisante_sans_candidat(self):
        impacts = analyser_changement(self.changement, lambda question, limite: [])

        self.assertEqual(len(impacts), 1)
        self.assertEqual(impacts[0].type, "preuve insuffisante")
        self.assertIsNone(impacts[0].doc_id)

    def test_trie_les_impacts_a_traiter_avant_les_alignes(self):
        def faux_rechercher(question, limite):
            return [
                candidat("PHA-001", "3. Déclaration", "Ouvrir la fiche sous 24 heures."),
                candidat(
                    "PHA-002",
                    "3. Déclaration",
                    "Ouvrir la fiche d'écart sous 2 jours ouvrés.",
                ),
            ]

        impacts = analyser_changement(self.changement, faux_rechercher)

        self.assertEqual(impacts[0].type, "à mettre à jour")
        self.assertEqual(impacts[-1].type, "aligné")

    def test_analyse_textes_enchaine_les_changements(self):
        def faux_rechercher(question, limite):
            return [candidat("PHA-001", "S", "Ouvrir la fiche sous 24 heures.")]

        impacts = analyser_textes(
            "Ouvrir la fiche sous 2 jours.",
            "Ouvrir la fiche sous 24 heures.",
            faux_rechercher,
        )

        self.assertTrue(impacts)
        self.assertTrue(all(impact.changement for impact in impacts))

    def test_le_moteur_ne_modifie_aucun_fichier(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "doc.md"
            fichier.write_text("Ouvrir la fiche sous 2 jours.", encoding="utf-8")
            avant = fichier.read_text(encoding="utf-8")

            analyser_textes(
                avant,
                "Ouvrir la fiche sous 24 heures.",
                lambda question, limite: [
                    candidat("PHA-001", "S", "Ouvrir la fiche sous 2 jours.")
                ],
            )

            self.assertEqual(fichier.read_text(encoding="utf-8"), avant)


class TestRapport(unittest.TestCase):
    def test_contient_la_validation_humaine(self):
        impact = qualifier(
            Changement(apres="Ouvrir la fiche sous 24 heures"),
            candidat("PHA-001", "3. Déclaration", "Ouvrir la fiche sous 24 heures."),
        )

        rapport = rendre_rapport([impact])

        self.assertIn("Validation humaine requise", rapport)
        self.assertIn("Aucun document n'a été modifié", rapport)
        self.assertIn("| Changement |", rapport)

    def test_rapport_vide_reste_valide(self):
        rapport = rendre_rapport([])

        self.assertIn("Validation humaine requise", rapport)


class TestCLI(unittest.TestCase):
    def test_fichier_absent_code_3(self):
        resultat = subprocess.run(
            [
                sys.executable,
                str(RACINE / "impact" / "analyser.py"),
                "--apres",
                "/chemin/inexistant.md",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(resultat.returncode, 3)

    def test_sans_argument_code_2(self):
        resultat = subprocess.run(
            [sys.executable, str(RACINE / "impact" / "analyser.py")],
            capture_output=True,
            text=True,
        )

        self.assertEqual(resultat.returncode, 2)


if __name__ == "__main__":
    unittest.main()
