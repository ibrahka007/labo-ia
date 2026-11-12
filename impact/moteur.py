"""Moteur d'analyse d'impact documentaire.

Principe : un changement est décrit (ou déduit d'un diff), puis chaque passage
du corpus susceptible d'être concerné est qualifié en « constat » ou « impact
supposé ». Le moteur ne modifie jamais un document : il produit des propositions
soumises à validation humaine.
"""

from __future__ import annotations

import difflib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE / "rag") not in sys.path:
    sys.path.insert(0, str(RACINE / "rag"))

from lexical import couverture, jetons  # noqa: E402
from rag_lib import detecter_reserve  # noqa: E402

MOTIF_NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")
SEUIL_ALIGNE = 0.0

# Termes trop génériques : à eux seuls, ils ne prouvent pas qu'un passage
# reprend la règle modifiée.
TERMES_GENERIQUES = {
    "delai", "delais", "jour", "jours", "heure", "heures", "fois", "date",
    "valeur", "nombre", "echeance", "duree", "annee", "annees", "mois",
    "document", "documents", "procedure", "qualite",
}

# Nombre de termes communs exigé pour affirmer qu'un passage reprend la règle.
TERMES_MINIMUM = 2

# Part des termes du changement présente dans le passage.
COUVERTURE_IMPACT = 0.5
COUVERTURE_DOUTE = 0.3


@dataclass
class Changement:
    """Une évolution factuelle extraite d'un document ou décrite par l'utilisateur."""

    avant: str = ""
    apres: str = ""
    contexte: str = ""

    @property
    def valeurs(self):
        return valeurs_numeriques(self.apres)

    @property
    def termes(self):
        return jetons(f"{self.avant} {self.apres}")

    def resume(self) -> str:
        if self.avant and self.apres:
            return f"« {self.avant.strip()} » → « {self.apres.strip()} »"
        return (self.apres or self.avant).strip()


@dataclass
class Impact:
    """Qualification d'un passage au regard d'un changement."""

    changement: Changement
    doc_id: Optional[str] = None
    version: Optional[str] = None
    section: Optional[str] = None
    extrait: str = ""
    score: float = 0.0
    type: str = "preuve insuffisante"
    confiance: str = "basse"
    actions: List[str] = field(default_factory=list)
    reserves: List[str] = field(default_factory=list)

    def ligne_tableau(self) -> str:
        extrait = " ".join(self.extrait.split())[:180]
        return "| {} | {} | {} | {} | {} | {} | {} |".format(
            self.changement.resume().replace("|", "/"),
            self.doc_id or "—",
            f"v{self.version}" if self.version else "—",
            (self.section or "—").replace("|", "/"),
            extrait.replace("|", "/") if extrait else "—",
            self.type,
            self.confiance,
        )


def valeurs_numeriques(texte: str) -> set:
    """Nombres présents dans un texte, indépendamment des espaces."""
    return set(MOTIF_NOMBRE.findall((texte or "").replace(" ", "")))


def est_metadonnee(ligne: str) -> bool:
    """Vrai pour une ligne de front matter ou un titre Markdown.

    Ces lignes changent à chaque version sans modifier une règle : les traiter
    comme des changements d'impact produirait du bruit.
    """
    contenu = ligne.strip()
    if not contenu or contenu == "---":
        return True
    if contenu.startswith("#"):
        return True
    return bool(re.match(r"^[a-zA-Z_]+\s*:\s", contenu))


def extraire_changements(
    texte_avant: str, texte_apres: str, contexte_max: int = 120
) -> List[Changement]:
    """Déduit les changements factuels d'un diff ligne à ligne.

    Seules les lignes remplacées ou ajoutées sont retenues : une suppression
    pure n'a pas de valeur de référence à rechercher.
    """
    lignes_avant = (texte_avant or "").splitlines()
    lignes_apres = (texte_apres or "").splitlines()

    changements: List[Changement] = []
    comparateur = difflib.SequenceMatcher(None, lignes_avant, lignes_apres)

    for operation, debut_a, fin_a, debut_b, fin_b in comparateur.get_opcodes():
        if operation == "equal":
            continue

        bloc_avant = [ligne.strip() for ligne in lignes_avant[debut_a:fin_a] if ligne.strip()]
        bloc_apres = [ligne.strip() for ligne in lignes_apres[debut_b:fin_b] if ligne.strip()]

        if not bloc_apres:
            continue
        if all(est_metadonnee(ligne) for ligne in bloc_apres):
            continue

        avant = " ".join(bloc_avant)[:contexte_max]
        apres = " ".join(bloc_apres)[:contexte_max]
        contexte = " ".join(lignes_apres[max(debut_b - 1, 0):debut_b])[:contexte_max]

        changements.append(Changement(avant=avant, apres=apres, contexte=contexte))

    return changements


def qualifier(changement: Changement, candidat: Dict[str, object]) -> Impact:
    """Classe un passage : aligné, à mettre à jour, réserve ou à vérifier."""
    texte = str(candidat.get("texte", ""))
    impact = Impact(
        changement=changement,
        doc_id=candidat.get("doc_id"),
        version=candidat.get("version"),
        section=candidat.get("section"),
        extrait=texte,
        score=float(candidat.get("score") or 0.0),
    )

    impact.reserves = detecter_reserve(texte)
    if impact.reserves:
        impact.type = "réserve"
        impact.confiance = "basse"
        impact.actions = [
            "Ne pas traiter comme une règle établie",
            "Faire confirmer la valeur par le métier ou le juridique",
        ]
        return impact

    valeurs_passage = valeurs_numeriques(texte)
    valeurs_cible = changement.valeurs
    termes_communs = set(changement.termes) & set(jetons(texte))
    termes_discriminants = termes_communs - TERMES_GENERIQUES
    couverture_changement = couverture(
        f"{changement.avant} {changement.apres}", texte
    )

    # Une valeur identique ne suffit pas : « 5 ans » pour les écarts qualité et
    # « 5 ans » pour les dossiers RH sont deux règles distinctes.
    if (
        valeurs_cible
        and valeurs_cible <= valeurs_passage
        and couverture_changement >= COUVERTURE_IMPACT
    ):
        impact.type = "aligné"
        impact.confiance = "haute"
        impact.actions = ["Vérifier la cohérence rédactionnelle"]
        return impact

    if (
        valeurs_passage
        and len(termes_communs) >= TERMES_MINIMUM
        and termes_discriminants
        and couverture_changement >= COUVERTURE_IMPACT
    ):
        impact.type = "à mettre à jour"
        impact.confiance = "haute" if len(termes_discriminants) >= 2 else "moyenne"
        impact.actions = [
            "Comparer la valeur du passage avec la nouvelle valeur",
            "Mettre à jour si le passage reprend l'ancienne règle",
        ]
        return impact

    if termes_communs and couverture_changement >= COUVERTURE_DOUTE:
        impact.type = "à vérifier"
        impact.confiance = "basse"
        impact.actions = ["Contrôler la portée réelle du changement"]
        return impact

    impact.type = "hors sujet"
    impact.confiance = "basse"
    return impact


def analyser_changement(
    changement: Changement,
    rechercher: Callable[[str, int], Sequence[Dict[str, object]]],
    seuil_preuve: bool = True,
    limite: int = 5,
) -> List[Impact]:
    """Analyse un changement avec une fonction de recherche injectée.

    `rechercher(question, limite)` doit retourner des candidats munis des clés
    doc_id, version, section, texte et score. L'injection permet de tester le
    moteur sans Qdrant ni Ollama.
    """
    # Le contexte améliore le rappel : une ligne de diff isolée est trop courte.
    question = " ".join(
        element for element in (changement.contexte, changement.apres or changement.avant) if element
    )
    candidats = list(rechercher(question, limite))

    if seuil_preuve and not candidats:
        return [
            Impact(
                changement=changement,
                type="preuve insuffisante",
                confiance="basse",
                actions=[
                    "Aucun passage pertinent : ne rien conclure",
                    "Élargir la recherche ou consulter le métier",
                ],
            )
        ]

    impacts = [qualifier(changement, candidat) for candidat in candidats]
    impacts = [impact for impact in impacts if impact.type != "hors sujet"]
    impacts.sort(key=lambda impact: (impact.type == "aligné", -impact.score))
    return impacts


def analyser_textes(
    texte_avant: str,
    texte_apres: str,
    rechercher: Callable[[str, int], Sequence[Dict[str, object]]],
    limite: int = 5,
) -> List[Impact]:
    """Analyse tous les changements détectés entre deux versions."""
    impacts: List[Impact] = []
    for changement in extraire_changements(texte_avant, texte_apres):
        impacts.extend(analyser_changement(changement, rechercher, limite=limite))
    return impacts


def rendre_rapport(impacts: List[Impact], titre: str = "Analyse d'impact") -> str:
    """Produit un rapport Markdown prêt à être relu par un humain."""
    lignes = [
        f"# {titre}",
        "",
        "Rapport généré automatiquement. Aucun document n'a été modifié.",
        "",
        "| Changement | Document | Version | Section | Preuve | Type | Confiance |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lignes.extend(impact.ligne_tableau() for impact in impacts)

    lignes.extend(["", "## Actions proposées", ""])
    for impact in impacts:
        if impact.actions:
            lignes.append(
                f"- **{impact.doc_id or 'corpus'}** ({impact.type}) : "
                + " ; ".join(impact.actions)
            )

    lignes.extend(
        [
            "",
            "## Réserve",
            "",
            "Les lignes de type « réserve » signalent un passage qui n'énonce pas "
            "une règle établie (hypothèse, valeur à confirmer). Elles ne doivent "
            "pas être traitées comme des obligations.",
            "",
            "**Validation humaine requise avant toute modification.**",
            "",
        ]
    )
    return "\n".join(lignes)
