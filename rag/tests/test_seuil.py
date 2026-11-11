"""Tests de la décision d'abstention (sans Qdrant ni Ollama)."""

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from rag_lib import SEUIL_ABSTENTION, decide_reponse, detecter_reserve  # noqa: E402


@dataclass
class FauxPoint:
    score: float
    payload: dict = None


class TestDecision(unittest.TestCase):
    def test_repond_au_dessus_du_seuil(self):
        points = [FauxPoint(0.71), FauxPoint(0.62)]

        retenus, motif = decide_reponse(points, 0.65)

        self.assertEqual(motif, "ok")
        self.assertEqual(len(retenus), 1)
        self.assertAlmostEqual(retenus[0].score, 0.71)

    def test_abstention_sous_le_seuil(self):
        points = [FauxPoint(0.64), FauxPoint(0.60)]

        retenus, motif = decide_reponse(points, 0.65)

        self.assertEqual(motif, "preuve insuffisante")
        self.assertEqual(retenus, [])

    def test_seuil_inclusif(self):
        points = [FauxPoint(0.65)]

        retenus, motif = decide_reponse(points, 0.65)

        self.assertEqual(motif, "ok")
        self.assertEqual(len(retenus), 1)

    def test_aucun_resultat(self):
        retenus, motif = decide_reponse([], 0.65)

        self.assertEqual(motif, "aucun résultat")
        self.assertEqual(retenus, [])

    def test_seuil_zero_desactive_l_abstention(self):
        points = [FauxPoint(0.10)]

        retenus, motif = decide_reponse(points, 0.0)

        self.assertEqual(motif, "ok")
        self.assertEqual(len(retenus), 1)

    def test_score_manquant_ne_casse_pas(self):
        points = [FauxPoint(None)]

        retenus, motif = decide_reponse(points, 0.65)

        self.assertEqual(motif, "preuve insuffisante")
        self.assertEqual(retenus, [])

    def test_seuil_par_defaut_documente(self):
        self.assertGreater(SEUIL_ABSTENTION, 0.0)
        self.assertLess(SEUIL_ABSTENTION, 1.0)


class TestReserve(unittest.TestCase):
    def test_detecte_hypothese(self):
        texte = "Une durée de 5 ans est retenue, à titre d'hypothèse à confirmer."

        marqueurs = detecter_reserve(texte)

        self.assertIn("hypothèse", marqueurs)
        self.assertIn("à confirmer", marqueurs)

    def test_regle_etablie_sans_reserve(self):
        texte = "Les enregistrements sont conservés cinq ans."

        self.assertEqual(detecter_reserve(texte), [])

    def test_insensible_a_la_casse(self):
        self.assertIn("sous réserve", detecter_reserve("Sous réserve de validation."))

    def test_texte_vide(self):
        self.assertEqual(detecter_reserve(""), [])
        self.assertEqual(detecter_reserve(None), [])


if __name__ == "__main__":
    unittest.main()
