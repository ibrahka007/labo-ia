import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from rag_lib import (  # noqa: E402
    collecter_chunks,
    decouper_sections,
    decouper_texte,
    extraire_chunks,
    lire_front_matter,
)


class TestParsing(unittest.TestCase):
    def test_front_matter(self):
        contenu = "---\nid: TEST-001\nversion: 1.0\n---\n\n# Titre\n\nCorps."
        metadonnees, corps = lire_front_matter(contenu)

        self.assertEqual(metadonnees["id"], "TEST-001")
        self.assertEqual(metadonnees["version"], "1.0")
        self.assertIn("Corps.", corps)

    def test_sans_front_matter(self):
        metadonnees, corps = lire_front_matter("# Titre\n\nTexte")
        self.assertEqual(metadonnees, {})
        self.assertIn("Texte", corps)

    def test_decoupage_sections(self):
        corps = "Introduction.\n\n## 1. Objet\n\nTexte A.\n\n## 2. Suite\n\nTexte B."
        sections = decouper_sections(corps)

        self.assertEqual([titre for titre, _ in sections], ["Introduction", "1. Objet", "2. Suite"])
        self.assertIn("Texte B.", sections[2][1])

    def test_texte_long_decoupe(self):
        texte = "\n\n".join(["paragraphe " * 40] * 10)
        morceaux = decouper_texte(texte)

        self.assertGreater(len(morceaux), 1)
        self.assertTrue(all(len(morceau) <= 1600 for morceau in morceaux))


class TestChunks(unittest.TestCase):
    def setUp(self):
        self._dossier = tempfile.TemporaryDirectory()
        self.racine = Path(self._dossier.name)

    def tearDown(self):
        self._dossier.cleanup()

    def test_extraction_metadonnees(self):
        fichier = self.racine / "domaine" / "TEST-001.md"
        fichier.parent.mkdir()
        fichier.write_text(
            "---\nid: TEST-001\ntitre: Essai\nversion: 2.0\nstatut: Approuvé\n"
            "domaine: Test\n---\n\n## 1. Objet\n\nContenu.\n",
            encoding="utf-8",
        )

        chunks = extraire_chunks(fichier, self.racine)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].doc_id, "TEST-001")
        self.assertEqual(chunks[0].version, "2.0")
        self.assertIn("1. Objet", chunks[0].section)
        self.assertIn("Contenu.", chunks[0].texte)

    def test_collecte_exclut_readme_et_annotations(self):
        (self.racine / "annotations").mkdir()
        (self.racine / "annotations" / "notes.md").write_text(
            "---\nid: NOTE-1\n---\n\n## X\n\nY\n", encoding="utf-8"
        )
        (self.racine / "README.md").write_text("# Doc\n", encoding="utf-8")
        (self.racine / "doc.md").write_text(
            "---\nid: DOC-1\ntitre: D\nversion: 1.0\n---\n\n## 1. Objet\n\nZ\n",
            encoding="utf-8",
        )

        chunks = collecter_chunks(self.racine)

        self.assertEqual({chunk.doc_id for chunk in chunks}, {"DOC-1"})


if __name__ == "__main__":
    unittest.main()
