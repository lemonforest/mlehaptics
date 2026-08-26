"""siona.synthetic — the SYNTHETIC / AGGLUTINATIVE-language render (F1168), the peer to `analytic` (F1166).

Synthetic/agglutinative languages (Sumerian, Turkish, Japanese, Swahili) mark grammatical role IN THE WORD (case
enclitics, verbal-chain infixes, determinatives). This module is the general RENDER for that type, parameterized
by a per-language MORPHOLOGY adapter — so the render is NOT hardcoded to one language. Sumerian is the first
adapter (it wraps `anchor`'s `case` + `render_cased`; those Sumerian-specific tables should eventually migrate
wholly into `sumerian.py`, leaving `anchor` as the general glyph→concept anchor — the F1167 refactor).

The SELECTION is the same as everywhere — `couple()`'s residue (a coupling graph → signed Class-L → spine +
communities). ONLY the RENDER is synthetic-morphology-driven here (vs analytic word-order + function words).
Sparse, numpy-free.
"""
from collections import namedtuple
from siona import anchor

__all__ = ["Morphology", "SUMERIAN", "adapters", "render_line", "translate"]

# a MORPHOLOGY adapter = a language's role-reader + line-renderer (the pluggable per-language part, F1167)
Morphology = namedtuple("Morphology", "name case render_line")

# the SUMERIAN adapter — the first synthetic instance; wraps anchor's Sumerian morphology (F1157/F1158)
SUMERIAN = Morphology(
    name="sumerian",
    case=anchor.case,                                        # operand relational role from the case enclitic
    render_line=anchor.render_cased,                         # subject + verb + case-marked obliques
)

adapters = {"sumerian": SUMERIAN}                            # registry; other synthetic languages register their own


def render_line(raw_line, morph=SUMERIAN):
    """Render ONE synthetic-language line via its MORPHOLOGY adapter (F1168): the morphology (`case`) supplies the
    op(x)operand coupling and the adapter's `render_line` turns it into a cased clause. Sumerian is the default
    adapter; another synthetic language supplies its own `Morphology(name, case, render_line)`."""
    return morph.render_line(raw_line)


def translate(raw_glyph_lines, morph=SUMERIAN):
    """Translate a whole synthetic-language text → per-line rendered clauses — the synthetic-pole peer to
    `analytic.describe`. The SELECTION (what to foreground) rides `couple()`'s residue as elsewhere; this is the
    morphology-driven RENDER side. Returns one rendered clause per line."""
    return [render_line(ln, morph) for ln in raw_glyph_lines]
