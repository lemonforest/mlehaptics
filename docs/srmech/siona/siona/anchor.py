"""siona.anchor — the GENERAL cross-lingual glyph→CONCEPT anchor (F1141; the FORM axis, F1140).

The glyph→concept LEXICON for a logographic / non-cognate script (a glyph IS a concept, bit-exact op(x)operand,
F1128): load a lexicon (Egyptian Vygus / Sumerian ETCSL), lemmatize a surface form to its lemma (F1144), and bridge
a glyph to its English CONCEPT — on which the RELATIONAL + CHIRALITY axes then operate.

**Typology note (F1170):** this module is language-GENERAL — the anchor mechanism for ANY non-cognate script. The
SYNTHETIC/agglutinative Sumerian-specific MORPHOLOGY (`case` / `verb_infixes` / `determinative` / `render_cased` /
the case/infix/determinative tables) migrated to `siona.sumerian`, so `anchor` stays the general concept-anchor and
`sumerian` owns the Sumerian language kernel. A module-level `__getattr__` (PEP 562) forwards the migrated names to
`sumerian` for backward compatibility, so existing `anchor.case(...)` etc. call sites keep working.

sparse (a lexicon dict), numpy-free.
"""
import html
import json
import os
import re

__all__ = ["load_anchor", "load_sux", "concept", "bridge_units", "transcribe", "have_anchor"]

_VYGUS = "/home/skirklan/corpora/egyptian_tla/vygus_dict_slice.jsonl"          # Egyptian (Vygus jsonl)
_SUX = "/home/skirklan/corpora/etcsl/sux_gilgamesh_lemmatized.json"           # Sumerian (ETCSL Gilgameš, lemmatized)
_anchor = None       # LEMMA → [English concept glosses]  (the ACTIVE anchor)
_surf2lemma = None   # surface form → lemma (the lemmatization layer, F1144; None = no lemmatization)

# the Sumerian-morphology names migrated to siona.sumerian (F1170); forwarded lazily for backward compatibility
_MIGRATED = frozenset((
    "determinative", "case", "verb_infixes", "verb_direction", "coupling_ec", "render_fluent", "render_repaired",
    "render_cased", "transcription_errors", "express_story", "bridge_disambiguated",
    "_phrase_cycles", "_rna", "_past", "_ROLE", "_CASE", "_INFIX", "_CONJ", "_DET_CLASS", "_CLASS_KEYWORDS",
    "_IRREG", "_FUNCTION"))


def __getattr__(name):     # PEP 562: forward migrated Sumerian morphology to siona.sumerian (F1170); keeps old call sites working
    if name in _MIGRATED:
        from siona import sumerian
        return getattr(sumerian, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def _norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))     # strip markup (KEEP content), unescape entities (F1155)
    return t.strip().lstrip(".=").lower()                    # so concept() resolves a RAW glyph too (idempotent on clean)


def _words(gloss):
    return [w for w in re.split(r"[ ,;/()]+", (gloss or "").lower()) if len(w) > 2]


def load_anchor(path=None, kind=None):
    """Load a glyph→concept anchor ``{transliteration: [concepts]}``. ``kind='vygus'`` reads the Egyptian Vygus
    jsonl (default); ``kind='json'`` reads a ``{"anchor": {glyph: [glosses]}}`` file (the ETCSL Sumerian Gilgameš
    anchor). Auto-detected by extension. The last-loaded anchor is active; pass a ``path`` to switch languages."""
    global _anchor, _surf2lemma
    if _anchor is not None and path is None:
        return _anchor
    _anchor = {}
    _surf2lemma = None
    p = path or _VYGUS
    kind = kind or ("json" if p.endswith(".json") else "vygus")
    if not os.path.exists(p):
        return _anchor
    if kind == "json":                                         # ETCSL {"anchor": {lemma:[gloss]}, "surf2lemma": {...}}
        d = json.load(open(p, encoding="utf-8"))
        for t, gs in d.get("anchor", {}).items():
            _anchor[_norm(t)] = list(gs)
        s2l = d.get("surf2lemma")
        if s2l:
            _surf2lemma = {_norm(s): _norm(l) for s, l in s2l.items()}         # the lemmatization layer (F1144)
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
    language). When a lemmatization layer is loaded (F1144), the inflected SURFACE form is mapped to its LEMMA
    first (so ``bi2-in-dug4`` → lemma ``dug4`` → "to say"). ``[]`` if no entry — an honest gap, not a guess."""
    a = load_anchor()
    n = _norm(glyph)
    if _surf2lemma:
        n = _surf2lemma.get(n, n)          # lemmatize surface → lemma before lookup (F1144)
    return a.get(n, [])


def bridge_units(units):
    """Bridge a sequence of source units → ``[(unit, [concepts])]`` — the glyph→concept FORM axis over a phrase.
    Units with no anchor entry carry ``[]`` (surfaced, not hidden — the coverage gap is the honest signal)."""
    return [(u, concept(u)) for u in units]


def transcribe(glyph_lines, *, with_class=False):
    """Orchestrate the glyph→concept bridge over a WHOLE text (F1145): each LINE (the phrase unit, F1143) →
    its concept-gloss per glyph. The FRACTAL-TOWER orchestration (F1117) — the per-line bridge assembled line →
    passage → story. Returns ``[[gloss-or-None per glyph] per line]``.

    ``with_class=True`` PRESERVES the DETERMINATIVE (the Sumerian semantic-class tag, now in `siona.sumerian`,
    F1156/F1170) through the transcription: returns ``[[(gloss, [class…]) per glyph] per line]`` — imported lazily
    so the general anchor keeps no Sumerian dependency."""
    det = None
    if with_class:
        from siona import sumerian
        det = sumerian.determinative
    out = []
    for line in glyph_lines:
        row = []
        for g in line:
            gl = concept(g)
            c = gl[0].split(",")[0] if gl else None
            row.append((c, det(g)) if with_class else c)
        out.append(row)
    return out
