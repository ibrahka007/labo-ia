"""Tests de la fusion RRF et du reranker heuristique (sans index ni réseau)."""

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from hybrid import fusion_rrf, reranker_heuristique  # noqa: E402


def candidat(fichier, section, texte="", doc_id=None):
    return {
        "doc_id": doc_id or fichier,
        "titre": "Titre",
        "version": "1.0",
        "statut": "Approuvé",
        "domaine": "Test",
        "fichier": fichier,
        "section": section,
        "position": 0,
        "texte": texte,
        "score": 0.7,
        "source": "test",
    }


class TestFusionRRF(unittest.TestCase):
    def test_candidat_commun_cumule_les_deux_rangs(self):
        dense = [candidat("a.md", "S1"), candidat("b.md", "S2")]
        lexical = [candidat("b.md", "S2"), candidat("c.md", "S3")]

        fusion = fusion_rrf([dense, lexical], k=60)

        scores = {item["fichier"]: item["score_rrf"] for item in fusion}
        self.assertAlmostEqual(scores["b.md"], 1 / 62 + 1 / 61)
        self.assertEqual(fusion[0]["fichier"], "b.md")

    def test_union_des_canaux(self):
        fusion = fusion_rrf(
            [[candidat("a.md", "S1")], [candidat("b.md", "S2")]], k=60
        )

        self.assertEqual(len(fusion), 2)

    def test_rangs_attribues(self):
        fusion = fusion_rrf(
            [[candidat("a.md", "S1"), candidat("b.md", "S2")]], k=60
        )

        self.assertEqual([item["rang_rrf"] for item in fusion], [1, 2])

    def test_canaux_vides(self):
        self.assertEqual(fusion_rrf([[], []]), [])

    def test_dedoublonne_par_fichier_et_section(self):
        fusion = fusion_rrf(
            [[candidat("a.md", "S1")], [candidat("a.md", "S1")]], k=60
        )

        self.assertEqual(len(fusion), 1)


class TestReranker(unittest.TestCase):
    def test_priorite_au_recouvrement(self):
        candidats = [
            candidat("a.md", "S", "aucun rapport avec la question"),
            candidat("b.md", "S", "le délai de déclaration d'un écart qualité"),
        ]
        for rang, item in enumerate(candidats, start=1):
            item["rang_rrf"] = rang

        reordonnes = reranker_heuristique("délai déclaration écart", candidats)

        self.assertEqual(reordonnes[0]["fichier"], "b.md")
        self.assertEqual(reordonnes[0]["rang_final"], 1)

    def test_bonus_titre_et_section(self):
        candidats = [
            candidat("a.md", "Annexe", "délai écart"),
            candidat("b.md", "Délai et écart", "délai écart"),
        ]
        for rang, item in enumerate(candidats, start=1):
            item["rang_rrf"] = rang

        reordonnes = reranker_heuristique("délai écart", candidats)

        self.assertEqual(reordonnes[0]["fichier"], "b.md")

    def test_scores_exposes(self):
        item = candidat("a.md", "S", "délai écart")
        item["rang_rrf"] = 1

        reordonnes = reranker_heuristique("délai écart", [item])

        self.assertIn("score_heuristique", reordonnes[0])
        self.assertAlmostEqual(reordonnes[0]["couverture"], 1.0)

    def test_liste_vide(self):
        self.assertEqual(reranker_heuristique("délai", []), [])


if __name__ == "__main__":
    unittest.main()
