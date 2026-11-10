import tempfile
import unittest
from pathlib import Path

from comparer_documents import (
    DocumentIllisible,
    DocumentIntrouvable,
    DocumentSansTexte,
    comparer_documents,
    lire_document,
)


class TestComparerDocuments(unittest.TestCase):
    def test_textes_identiques(self):
        texte = "Ligne 1\nLigne 2\n"
        self.assertEqual(comparer_documents(texte, texte), "")

    def test_ligne_modifiee(self):
        ancien = "Le délai de revue est de 30 jours.\n"
        nouveau = "Le délai de revue est de 15 jours.\n"

        resultat = comparer_documents(ancien, nouveau)

        self.assertIn("-Le délai de revue est de 30 jours.", resultat)
        self.assertIn("+Le délai de revue est de 15 jours.", resultat)

    def test_ligne_ajoutee(self):
        ancien = "Ligne 1\nLigne 2\n"
        nouveau = "Ligne 1\nLigne 2\nLigne 3\n"

        resultat = comparer_documents(ancien, nouveau)

        self.assertIn("+Ligne 3", resultat)
        self.assertNotIn("-Ligne 1", resultat)


class TestLectureDocument(unittest.TestCase):
    def setUp(self):
        self._dossier_temporaire = tempfile.TemporaryDirectory()
        self.dossier = Path(self._dossier_temporaire.name)

    def tearDown(self):
        self._dossier_temporaire.cleanup()

    def test_fichier_absent(self):
        with self.assertRaises(DocumentIntrouvable):
            lire_document(str(self.dossier / "absent.txt"))

    def test_pdf_endommage(self):
        fichier = self.dossier / "endommage.pdf"
        fichier.write_bytes(b"ceci n'est pas un PDF valide")

        with self.assertRaises(DocumentIllisible):
            lire_document(str(fichier))

    def test_document_sans_texte(self):
        fichier = self.dossier / "vide.txt"
        fichier.write_text("   \n\n  ", encoding="utf-8")

        with self.assertRaises(DocumentSansTexte):
            lire_document(str(fichier))

    def test_texte_valide(self):
        fichier = self.dossier / "valide.txt"
        fichier.write_text("Contenu exploitable\n", encoding="utf-8")

        self.assertEqual(lire_document(str(fichier)), "Contenu exploitable\n")


if __name__ == "__main__":
    unittest.main()
