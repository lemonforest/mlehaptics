"""siona.sumerian — the Sumerian SUB-LANGUAGE KERNEL (F1156): the #225/#226 markup-router for cuneiform.

A sub-language kernel COMPREHENDS a script's own markup as a FORM layer (F817/F764 `understand_markup` — markup is
to comprehend, NEVER to strip). For Sumerian that markup is the DETERMINATIVE — a semantic-class classifier written
INTO the glyph ({d}=divine, {ki}=place, {ĝiš}=wood, {na4}=stone…). This kernel produces the genome SURFACE for a
Sumerian line — per glyph, its ``(concept, semantic-CLASS)`` — where the class is the determinative (coherency-
AGNOSTIC, NOT noun/verb, F1155), and routes glyphs to class-handlers (the markup → kernel dispatch).

This is what the srmech genome surface carries for Sumerian: glyph-derived concept + glyph-derived class, no POS.
Sparse, numpy-free. Attested to ETCSL (the determinative markup is the edition's own transliteration convention).
"""
from siona import anchor

__all__ = ["surface", "class_profile", "route", "dispatch_line", "have_kernel"]


def surface(raw_glyph_lines):
    """The genome SURFACE for Sumerian (F1156): ``[[(concept, [class…]) per glyph] per line]`` — the determinative
    PRESERVED alongside each concept (via `anchor.transcribe(with_class=True)`). The coherency-agnostic type the
    genome carries instead of POS. Pass RAW glyphs (markup intact) so the determinative survives."""
    return anchor.transcribe(raw_glyph_lines, with_class=True)


def class_profile(raw_line):
    """The determinative CLASS profile of a raw Sumerian line — ``{class: count}`` over its glyphs. The line's
    semantic-class signature (how many divine / place / wood … glyphs), a coherency-agnostic line descriptor."""
    prof = {}
    for g in raw_line:
        for c in anchor.determinative(g):
            prof[c] = prof.get(c, 0) + 1
    return prof


def route(raw_glyph, handlers, default=None):
    """Dispatch a glyph to a class-HANDLER by its determinative (the markup → kernel dispatch, #225/#226):
    ``handlers = {class: fn(concept, glyph)}``. Runs the handler for the glyph's FIRST class tag; falls back to
    ``handlers['*']`` then ``default``. The genome routes a divine name, a toponym, a wooden object each to its
    own class-kernel WITHOUT any noun/verb tagging — the classifier decides."""
    concept = (anchor.concept(raw_glyph) or [None])[0]
    for cls in anchor.determinative(raw_glyph):
        if cls in handlers:
            return handlers[cls](concept, raw_glyph)
    if "*" in handlers:
        return handlers["*"](concept, raw_glyph)
    return default


def dispatch_line(raw_line, handlers, default=None):
    """`route` over a whole line → the per-glyph dispatch results (the class-routed genome surface of the line)."""
    return [route(g, handlers, default) for g in raw_line]


def have_kernel():
    return anchor.have_anchor()
