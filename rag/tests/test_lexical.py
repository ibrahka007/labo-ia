"""Tests de l'index lexical FTS5 (sans Qdrant ni Ollama)."""

import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from lexical import (  # noqa: E402
    construire_index,
    couverture,
    jetons,
    normaliser,
    rechercher_lexical,
    requete_match,
)


@dataclass
class FauxChunk:
    doc_id: str
    titre: str
    version: str
    statut: str
    domaine: str
    fichier: str
    section: str
    position: int
    texte: str


def chunk(doc_id, section, texte, fichier=None):
    return FauxChunk(
        doc_id=doc_id,
        titre=f"Titre {doc_id}",
        version="1.0",
        statut="Approuvé",
        domaine="Test",
        fichier=fichier or f"test/{doc_id}.md",
        section=section,
        position=0,
        texte=texte,
    )


class TestNormalisation(unittest.TestCase):
    def test_accents_et_casse(self):
        self.assertEqual(normaliser("Délai de CONSERVATION"), "delai de conservation")

    def test_ponctuation_reduite(self):
        self.assertEqual(normaliser("écart qualité, 30 jours."), "ecart qualite 30 jours")

    def test_jetons_retire_stopwords(self):
        jetons_obtenus = jetons("Quel est le délai pour un écart ?")

        self.assertIn("delai", jetons_obtenus)
        self.assertIn("ecart", jetons_obtenus)
        self.assertNotIn("quel", jetons_obtenus)
        self.assertNotIn("le", jetons_obtenus)

    def test_jetons_sans_doublon(self):
        self.assertEqual(jetons("écart écart ECART"), ["ecart"])

    def test_requete_and(self):
        self.assertEqual(requete_match("délai écart"), '"delai" AND "ecart"')

    def test_requete_or(self):
        self.assertEqual(requete_match("délai écart", "OR"), '"delai" OR "ecart"')

    def test_couverture(self):
        self.assertAlmostEqual(couverture("délai écart", "le délai est fixé"), 0.5)


class TestIndexLexical(unittest.TestCase):
    def setUp(self):
        self._dossier = tempfile.TemporaryDirectory()
        self.chemin = str(Path(self._dossier.name) / "index.sqlite")
        self.chunks = [
            chunk("PHA-001", "2. Délais", "Un écart doit être déclaré sous 24 heures."),
            chunk("RH-003", "4. Délai cible", "Le délai cible est de 45 jours ouvrés."),
        ]

    def tearDown(self):
        self._dossier.cleanup()

    def test_construire_et_compter(self):
        self.assertEqual(construire_index(self.chunks, self.chemin), 2)

    def test_recherche_retourne_le_bon_document(self):
        construire_index(self.chunks, self.chemin)

        resultats = rechercher_lexical("déclarer un écart", self.chemin, 2)

        self.assertTrue(resultats)
        self.assertEqual(resultats[0]["doc_id"], "PHA-001")
        self.assertEqual(resultats[0]["rang"], 1)
        self.assertEqual(resultats[0]["source"], "lexical")

    def test_couverture_prioritaire_sur_bm25(self):
        construire_index(
            [
                chunk("A", "S", "Le délai est mentionné ici sans autre terme."),
                chunk("B", "S", "Un écart déclaré sous 24 heures par le laboratoire."),
            ],
            self.chemin,
        )

        resultats = rechercher_lexical("écart déclaré délai", self.chemin, 2)

        # B couvre deux termes sur trois, A un seul.
        self.assertEqual(resultats[0]["doc_id"], "B")

    def test_question_sans_jeton(self):
        construire_index(self.chunks, self.chemin)

        self.assertEqual(rechercher_lexical("le la les", self.chemin, 5), [])

    def test_index_absent(self):
        with self.assertRaises(FileNotFoundError):
            rechercher_lexical("écart", self.chemin, 5)

    def test_reconstruction_sans_doublon(self):
        construire_index(self.chunks, self.chemin)
        construire_index(self.chunks, self.chemin)

        resultats = rechercher_lexical("écart", self.chemin, 10)

        self.assertEqual(len(resultats), 1)


if __name__ == "__main__":
    unittest.main()
