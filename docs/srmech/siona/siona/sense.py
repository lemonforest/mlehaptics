"""siona.sense — the 3-AXIS meaning signature (F1137): FORM ⊕ RELATIONAL ⊕ CHIRALITY.

The session's axes sub-arc lands here. Three TYPE-INDEPENDENT semantic axes (measured independent, F1135/F1136),
each catching a distinction the others miss — like the three cones giving full colour discrimination:

  * FORM       (`translate.comprehend` byte-glyph)  — spelling / cognate bridge (edukesen~education, cross-lingual)
  * RELATIONAL (`relate` co-occurrence ⊕ `conceptnet` typed) — synonymy / relatedness (car~automobile)
  * CHIRALITY  (`chirality` opponent, Class C)       — antonymy / opposite-pole (hot|cold), the metamer the
                                                       relational axes collapse

`relationship(a, b)` fuses them into a 4-way call — opposite / synonym / related / unrelated — that NO single axis
can make (proximity confuses synonym with antonym; chirality only sees antonyms; form is semantically flat). The
chirality axis is checked FIRST because it RESOLVES the antonym metamer (a high-proximity pair that is an opponent
pair is OPPOSITE, not synonym). Sparse, numpy-free.
"""
from . import chirality, conceptnet, relate

__all__ = ["axes", "relationship"]

# thresholds from the measured per-category proximity means (F1135): synonym~0.17, related~0.08, unrelated~0.00
_SYN, _REL = 0.12, 0.03


def axes(a, b):
    """The 3-axis meaning signature of a word pair: ``{"relational": float, "chirality": 0/1}`` (FORM is a
    per-word byte encoding, folded in by callers that need the cognate axis)."""
    rel = max(relate.related(a, b), conceptnet.related(a, b))
    return {"relational": rel, "chirality": chirality.opposite(a, b)}


def relationship(a, b):
    """4-way meaning call using all three axes — ``"opposite"`` / ``"synonym"`` / ``"related"`` / ``"unrelated"``.
    Chirality FIRST (it resolves the antonym metamer the relational axis collapses), then the relational axis."""
    if chirality.opposite(a, b) >= 1.0:            # CHIRALITY axis — opposite poles, even when proximity is high
        return "opposite"
    rel = max(relate.related(a, b), conceptnet.related(a, b))   # RELATIONAL axis
    if rel >= _SYN:
        return "synonym"
    if rel >= _REL:
        return "related"
    return "unrelated"
