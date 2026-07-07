"""siona.anchor — the cross-lingual glyph→CONCEPT anchor (F1141): the missing bottom-up layer (F1140).

Our meaning stack is English-surface-anchored — FORM (byte-cognate), RELATIONAL (`relate`, English co-occurrence),
CHIRALITY (`chirality`, English antonyms) — so a NON-COGNATE / logographic language blinds every axis (F1140). The
fix is a language-independent glyph→CONCEPT anchor: for a logographic script the FORM axis is NOT bytes, it is the
glyph→concept LEXICON (F1128 — a glyph IS a concept, bit-exact op(x)operand). This module loads such an anchor
(Egyptian Vygus dictionary — the tractable model; the Sumerian analog is the ePSD, not yet on disk) and bridges a
source unit to English CONCEPTS, on which the RELATIONAL + CHIRALITY axes then operate.

So the pipeline for a non-cognate language: glyph → CONCEPT (this anchor = the FORM axis) → the English-anchored
RELATIONAL/CHIRALITY reasoning. The anchor is the bottom layer the k=3 spread regime (F1131) needs where no
perspective otherwise has signal.

sparse (a lexicon dict), numpy-free. Attested to the Vygus 2018 Middle Egyptian dictionary (`vygus_dict_slice`).
"""
import json
import os
import re

__all__ = ["load_anchor", "concept", "bridge_units", "bridge_disambiguated", "have_anchor"]

_VYGUS = "/home/skirklan/corpora/egyptian_tla/vygus_dict_slice.jsonl"          # Egyptian (Vygus jsonl)
_SUX = "/home/skirklan/corpora/etcsl/sux_gilgamesh_anchor.json"               # Sumerian (ETCSL Gilgameš json)
_anchor = None       # transliteration → [English concept glosses]  (the ACTIVE anchor)


def _norm(t):
    return (t or "").strip().lstrip(".=").lower()


def load_anchor(path=None, kind=None):
    """Load a glyph→concept anchor ``{transliteration: [concepts]}``. ``kind='vygus'`` reads the Egyptian Vygus
    jsonl (default); ``kind='json'`` reads a ``{"anchor": {glyph: [glosses]}}`` file (the ETCSL Sumerian Gilgameš
    anchor). Auto-detected by extension. The last-loaded anchor is active; pass a ``path`` to switch languages."""
    global _anchor
    if _anchor is not None and path is None:
        return _anchor
    _anchor = {}
    p = path or _VYGUS
    kind = kind or ("json" if p.endswith(".json") else "vygus")
    if not os.path.exists(p):
        return _anchor
    if kind == "json":                                                        # ETCSL-style {"anchor": {...}}
        d = json.load(open(p, encoding="utf-8"))
        for t, gs in d.get("anchor", {}).items():
            _anchor[_norm(t)] = list(gs)
        return _anchor
    for line in open(p, encoding="utf-8"):                                     # Vygus jsonl
        try:
            r = json.loads(line)
        except Exception:
            continue
        t = _norm(r.get("transliteration_unicode"))
        m = (r.get("translation") or "").strip()
        if t and m and m.lower() != "none":
            _anchor.setdefault(t, [])
            if m not in _anchor[t]:
                _anchor[t].append(m)
    return _anchor


def load_sux(path=None):
    """Load the ETCSL Sumerian Gilgameš glyph→concept anchor (3186 lemmas; #246). Switches the active anchor."""
    return load_anchor(path or _SUX, kind="json")


def have_anchor():
    return bool(load_anchor())


def concept(glyph):
    """A source glyph / transliteration → its English CONCEPT gloss(es) (the FORM axis for a logographic
    language). ``[]`` if the anchor has no entry — an honest coverage gap, not a guess."""
    a = load_anchor()
    return a.get(_norm(glyph), [])


def bridge_units(units):
    """Bridge a sequence of source units → ``[(unit, [concepts])]`` — the glyph→concept FORM axis over a phrase.
    Units with no anchor entry carry ``[]`` (surfaced, not hidden — the coverage gap is the honest signal)."""
    return [(u, concept(u)) for u in units]


def _words(gloss):
    return [w for w in re.split(r"[ ,;/()]+", (gloss or "").lower()) if len(w) > 2]


def bridge_disambiguated(units):
    """Glyph→concept WITH SENSE-SELECTION by context (F608/F1127 — the sense-determinative applied to the
    cross-lingual bridge, reusing the RELATIONAL axis): for a polysemous glyph, pick the anchor gloss whose words
    are most RELATED (`relate`) to the OTHER glyphs' concept words. Returns ``[(unit, best_gloss_or_None)]`` — the
    same polysemy-resolution machinery ASL uses, now on the English concept side of the bridge."""
    from siona import relate as _rel
    _rel.load()
    cand = {u: concept(u) for u in units}
    ctx = set()
    for cs in cand.values():
        for c in cs:
            ctx |= set(_words(c))
    out = []
    for u in units:
        cs = cand[u]
        if not cs:
            out.append((u, None))
        elif len(cs) == 1:
            out.append((u, cs[0]))
        else:
            out.append((u, max(cs, key=lambda g: _rel.relatedness(_words(g), ctx - set(_words(g))))))
    return out
