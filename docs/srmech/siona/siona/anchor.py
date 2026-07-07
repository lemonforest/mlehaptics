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

__all__ = ["load_anchor", "load_sux", "concept", "bridge_units", "bridge_disambiguated", "transcribe", "have_anchor"]

_VYGUS = "/home/skirklan/corpora/egyptian_tla/vygus_dict_slice.jsonl"          # Egyptian (Vygus jsonl)
_SUX = "/home/skirklan/corpora/etcsl/sux_gilgamesh_lemmatized.json"           # Sumerian (ETCSL Gilgameš, lemmatized)
_anchor = None       # LEMMA → [English concept glosses]  (the ACTIVE anchor)
_surf2lemma = None   # surface form → lemma (the lemmatization layer, F1144; None = no lemmatization)


def _norm(t):
    return (t or "").strip().lstrip(".=").lower()


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


def _rna(concepts):
    """DNA→RNA (F1146): the HALF-BEAT intermediate — couple the stored op(x)operand concepts into a transient
    ORDERED form before rendering. Sumerian is verb-final (SOV): the verb ("to X") is the Class-A anchor; the
    coupling groups [pre-verb operands] · VERB · [post-verb operands]. This is the step we were SKIPPING by going
    genome→language directly (DNA→protein); it is where word-ORDER (the coupling) lives, separate from the final
    continuous render. Returns ``(pre, verb_or_None, post)``."""
    cs = [c for c in concepts if c]
    vi = next((i for i in range(len(cs) - 1, -1, -1) if cs[i].startswith("to ")), None)  # verb-final: last "to X"
    if vi is None:
        return (cs, None, [])
    return (cs[:vi], cs[vi][3:], cs[vi + 1:])


def render_fluent(concept_line):
    """RENDER a line's sparse op(x)operand concepts → a continuous English form (the TOWER EDGE / the flat→curved
    Wick rotation, F1146), via the DNA→RNA→language path: (RNA/half-beat) :func:`_rna` couples the concepts into
    a verb-anchored ordered form; (language) reorder verb-final→medial + minimal function-word glue. This is a
    ROUGH v1 — the local-flat concepts are real; the global-curvature (fluent grammar) is the ongoing NLG. The
    render does NOT invent content — only re-orders + glues what the genome stored (no magic-number prose)."""
    pre, verb, post = _rna(concept_line)
    if verb is None:                                        # a noun phrase — Sumerian genitive chain ("of")
        cs = pre
        return " of ".join(cs) if 1 < len(cs) <= 3 else " ".join(cs)
    subj = " ".join(pre)
    v = verb + ("d" if verb.endswith("e") else "ed")        # narrative past (the story register)
    obj = " ".join(post)
    return " ".join(x for x in (subj, v, obj) if x)


def transcribe(glyph_lines):
    """Orchestrate the glyph→concept bridge over a WHOLE text (F1145): each LINE (the phrase unit, F1143) →
    its concept-gloss per glyph. This is the FRACTAL-TOWER orchestration (F1117) — NOT new architecture, just the
    per-line bridge assembled line → passage → story. Returns ``[[gloss-or-None per glyph] per line]``; the
    read-out / natural-language render is the caller's (write the full output to a scratch file while we test
    which render works best). The line-level sparse concepts ARE the story genome expressed to language."""
    return [[(concept(g)[0].split(",")[0] if concept(g) else None) for g in line] for line in glyph_lines]


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
