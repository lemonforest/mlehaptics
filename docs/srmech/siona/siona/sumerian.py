"""siona.sumerian — the Sumerian LANGUAGE KERNEL: the sub-language markup-router (F1156) + the full Sumerian
SYNTHETIC/agglutinative MORPHOLOGY (migrated from `anchor`, F1170).

Sumerian is a SYNTHETIC / agglutinative language — grammatical role is marked IN THE WORD: the DETERMINATIVE (a
semantic-class classifier: {d}=divine, {ki}=place, {ĝiš}=wood…), the CASE enclitic (the operand's relational role:
-ta=from, -še₃=to, -ke₄=of…), and the verbal-chain INFIXES (the operator's re-encoding of those roles). This module
owns all of that. `anchor` stays the general glyph→concept anchor (the FORM axis); `sumerian` is the Sumerian
render + morphology + markup kernel — the SYNTHETIC pole peer to `analytic` (F1166) via `synthetic` (F1168).

The SELECTION is `couple()`'s residue as everywhere; this module is the synthetic RENDER + the glyph-morphology
read (case / infix / determinative → the op(x)operand coupling + its native EC, F1157–F1160). Sparse, numpy-free.
Attested to ETCSL (the transliteration + determinative conventions).
"""
import re

from siona import anchor

__all__ = ["surface", "class_profile", "route", "dispatch_line", "have_kernel",
           "determinative", "case", "verb_infixes", "verb_direction", "coupling_ec",
           "render_fluent", "render_repaired", "render_cased", "transcription_errors",
           "express_story", "bridge_disambiguated"]

# ── DETERMINATIVES (F1155): the script's OWN semantic-class classifiers (coherency-agnostic type tag, not POS) ──
_DET_CLASS = {"d": "divine", "diĝir": "divine", "ki": "place", "ĝiš": "wood", "gish": "wood", "ĝeš": "wood",
              "na4": "stone", "gi": "reed", "lu2": "person", "lú": "person", "munus": "woman", "kur": "land",
              "uruda": "copper", "urudu": "copper", "tug2": "textile", "gada": "linen", "zabar": "bronze",
              "dug": "vessel", "u2": "plant", "šem": "aromatic", "mušen": "bird", "ku6": "fish", "id2":
              "watercourse", "kuš": "leather", "ansze": "equid", "e2": "building", " nisi": "vegetable"}

_CLASS_KEYWORDS = {
    "divine": {"god", "goddess", "deity", "divine", "inana", "enlil", "an"},
    "place": {"city", "town", "place", "land", "country", "region", "mountain", "temple"},
    "person": {"man", "person", "king", "lord", "priest", "official", "servant", "smith"},
    "woman": {"woman", "lady", "queen", "priestess", "female"},
    "wood": {"wood", "tree", "wooden", "plough", "boat", "chair", "throne", "weapon"},
    "stone": {"stone", "rock", "flint", "bead"},
    "bird": {"bird", "eagle", "raven", "goose"},
    "fish": {"fish", "carp"},
    "plant": {"plant", "grass", "herb", "reed", "grain", "onion"},
    "watercourse": {"river", "canal", "watercourse", "water", "stream"},
    "copper": {"copper", "bronze", "metal", "tool", "axe"},
    "land": {"land", "mountain", "country", "foreign"},
}

# ── CASE enclitics (F1157) + the verbal INFIX / CONJUGATION morphology (F1158/F1159) ──
_CASE = {"ta": "from", "sze3": "to", "še3": "to", "ce3": "to", "ra": "to/for", "da": "with",
         "ke4": "of", "ka": "of", "ak": "of", "gin7": "like", "gen7": "like", "bi": "its", "a": "in"}
_ROLE = {"from": "from", "to": "to", "to/for": "to", "in": "in", "with": "with"}          # canonical shared roles (F1158)
_INFIX = {"ta": "from", "ši": "to", "ci": "to", "sze": "to", "ni": "in", "da": "with"}    # verbal dimensional infixes
_CONJ = {"mu": "toward", "im": "toward", "ba": "away", "bi2": "away", "al": "stative"}    # conjugation prefix = direction

# ── the surface VENEER conjugation tables (F1149) ──
_IRREG = {"go": "went", "say": "said", "seek": "sought", "come": "came", "give": "gave", "take": "took",
          "see": "saw", "make": "made", "stand": "stood", "strike": "struck", "fall": "fell", "hold": "held",
          "bring": "brought", "speak": "spoke", "build": "built", "beat": "beat", "cut": "cut", "set": "set",
          "put": "put", "run": "ran", "sit": "sat", "rise": "rose", "grow": "grew", "throw": "threw"}
_FUNCTION = frozenset(("the of a an and to in on at for with by from as is are was were be has have "
                       "his her its their my your our this that").split())


def determinative(raw_glyph):
    """The Sumerian DETERMINATIVE(s) of a RAW glyph (F1155): the writing system's OWN semantic-class classifier
    (a ``<sup>…</sup>`` super/sub-script — {d}=divine, {ki}=place…), a glyph-derived, coherency-AGNOSTIC type tag
    (semantic CLASS, not noun/verb). Returns the class name(s), or ``[]`` for a bare glyph. FIBER, not noise (F817)."""
    out = []
    for d in re.findall(r"<sup>(.*?)</sup>", raw_glyph or ""):
        import html as _h
        d = _h.unescape(re.sub(r"<[^>]+>", "", d)).strip().lower()
        if not d or d in "?!*":                                        # skip ETCSL editorial markers, not classifiers
            continue
        out.append(_DET_CLASS.get(d, d))
    return out


def case(surface):
    """The Sumerian CASE enclitic → the operand's RELATIONAL ROLE (F1157): from/-ta, to/-še₃-ra, of/-ke₄, with/-da,
    in/-a, like/-gin₇. A glyph-derived coherency-agnostic coupling tag that lemmatization drops. Scans the hyphen
    morphemes from the end for the last enclitic."""
    for suf in reversed(re.split(r"[-.]", anchor._norm(surface))):
        if suf in _CASE:
            return _CASE[suf]
    return None


def verb_infixes(glyph):
    """The dimensional INFIXES in a Sumerian verbal chain (F1159) → the coupling roles the VERB re-encodes
    (from/to/in/with) — the OPERATOR-side mirror of the operand cases (cross-referencing, F1158)."""
    return {_INFIX[m] for m in re.split(r"[-.]", anchor._norm(glyph)) if m in _INFIX}


def verb_direction(glyph):
    """The Sumerian conjugation PREFIX (first morpheme) → the verb's deictic DIRECTION (F1159): mu-=toward,
    ba-=away, al-=stative — a Class-C CHIRALITY on the OPERATOR. ``None`` if not a recognised prefix."""
    first = re.split(r"[-.]", anchor._norm(glyph))[0] if anchor._norm(glyph) else ""
    return _CONJ.get(first)


def coupling_ec(raw_glyph_line):
    """COUPLING-level error-correction (F1159) via the NATIVE case↔infix redundancy (F1158): each operand's role is
    stated TWICE — the operand's CASE + the VERB's infix. RECOVER a verb-only role (a dropped case); DETECT an
    operand role the verb does not license (a mismatch = the F1149 watermark at the COUPLING). Returns a dict."""
    vroles, oroles = set(), set()
    for g in raw_glyph_line:
        c = (anchor.concept(g) or [""])[0]
        if c.startswith("to "):
            vroles |= verb_infixes(g)
        else:
            cs = case(g)
            if cs in _ROLE:
                oroles.add(_ROLE[cs])
    return {"verb_roles": sorted(vroles), "operand_roles": sorted(oroles),
            "recovered": sorted(vroles - oroles),
            "mismatched": sorted(oroles - vroles) if vroles else []}


def _rna(concepts):
    """DNA→RNA half-beat (F1146): couple the concepts into a verb-anchored ordered form (Sumerian is verb-final:
    the last "to X" is the verb). Returns ``(pre, verb_or_None, post)``."""
    cs = [c for c in concepts if c]
    vi = next((i for i in range(len(cs) - 1, -1, -1) if cs[i].startswith("to ")), None)
    if vi is None:
        return (cs, None, [])
    return (cs[:vi], cs[vi][3:], cs[vi + 1:])


def _past(v):
    v = v.strip()
    if v in _IRREG:
        return _IRREG[v]
    if v.endswith("e"):
        return v + "d"
    if len(v) > 1 and v.endswith("y") and v[-2] not in "aeiou":
        return v[:-1] + "ied"
    return v + "ed"


def render_fluent(concept_line):
    """The surface VENEER render (F1149): sparse concepts → a continuous English form via the DNA→RNA→language path
    (verb-anchored reorder + `_IRREG` conjugation + "the/of" glue). Rough by design — the lossy English projection
    (F1128), not the substrate render. Invents no content."""
    pre, verb, post = _rna(concept_line)
    if verb is None:
        cs = [c for c in pre if c]
        return ("the " + " of the ".join(cs)) if 1 < len(cs) <= 3 else " ".join(cs)
    subj = ("the " + " of the ".join(pre)) if pre else ""
    obj = ("the " + " ".join(post)) if post else ""
    return " ".join(x for x in (subj, _past(verb), obj) if x)


def _phrase_cycles(concepts):
    """Split a line's concepts into PHRASE-CYCLES at each verb (Sumerian verb-final): each verb closes a cycle
    ``[operands… verb]`` (the NER/Class-L phrase-scale unit, F1151). Returns a list of cycles."""
    cycles, cur = [], []
    for c in (x for x in concepts if x):
        cur.append(c)
        if c.startswith("to "):
            cycles.append(cur)
            cur = []
    if cur:
        cycles.append(cur)
    return cycles


def render_repaired(concept_line, *, with_ec=False):
    """SCALE-STRATIFIED render (F1151) + intrinsic G4 chirality-EC (F1154, op(x)operand(x)EC): split into
    phrase-cycles and render each at its scale. ``with_ec=True`` emits ``(text, ec)`` where the G4 fold (F1153)
    rides WITH the render (EC intrinsic, not bolted on)."""
    cycles = _phrase_cycles(concept_line)
    text = ", ".join(render_fluent(cy) for cy in cycles) if cycles else ""
    if with_ec:
        from siona import g4
        return text, g4.g4_fold(concept_line)
    return text


def render_cased(raw_glyph_line):
    """RENDER using the CASE enclitics (F1158) for the REAL coupling — subject + verb + case-marked obliques with
    their real prepositions (from Kiš / to Unug / of Kulaba), the op(x)operand coupling read straight off the
    glyphs. Ergative(-e)=agent; absolutive=object w/agent else subject; ventive/away picks came/went. Pass RAW
    glyphs (the case lives in the suffix)."""
    items = []
    for g in raw_glyph_line:
        c = (anchor.concept(g) or [None])[0]
        if c:
            items.append((c.split(",")[0], case(g), anchor._norm(g), verb_direction(g)))
    verb = next(((c[3:], d) for c, cs, gn, d in items if c.startswith("to ")), None)
    erg = [c for c, cs, gn, d in items if not cs and not c.startswith("to ") and re.search(r"(?:^|-)e\d*$", gn)]
    abso = [c for c, cs, gn, d in items
            if not cs and not c.startswith("to ") and not (re.search(r"(?:^|-)e\d*$", gn) and c in erg)]
    obl = [(c, cs) for c, cs, gn, d in items if cs and not c.startswith("to ")]
    subj = erg or abso[:1]
    obj = abso if erg else abso[1:]
    parts = []
    if subj:
        parts.append(" ".join(subj))
    if verb:
        v, d = verb
        parts.append(("came" if d == "toward" else "went") if v in ("go", "come") else _past(v))
    if obj:
        parts.append(" ".join(obj))
    for c, cs in obl:
        parts.append("%s %s" % (cs, c))
    return " ".join(parts)


def transcription_errors(rendered, source_concepts):
    """DETECT transcription errors via the T-vs-U / attestation WATERMARK (F1149): every CONTENT token in a render
    must trace to an ATTESTED stored concept (the lemma/anchor); an un-traceable content token is the "U" (error).
    Function-word scaffold exempt. Returns the un-attested (error) tokens."""
    src = set()
    for g in source_concepts:
        for w in re.split(r"[ ,;/()]+", (g or "").lower()):
            if len(w) >= 2:
                src.add(w)
                src.add(_past(w))
    errs = []
    for t in re.split(r"\s+", (rendered or "").strip()):
        tl = t.lower().strip(".,;:")
        if not tl or tl in _FUNCTION:
            continue
        if tl not in src and (anchor.concept(tl) == []):
            errs.append(t)
    return errs


def express_story(glyph_lines, query, *, coupling=0.05):
    """Route the story render through `couple()` (F1148/F1164): couple() ONCE, then the coupled subset is the
    query's COMMUNITY and the cycle-read order is the SPINE — both residue reads of the one signed Class-L op.
    Returns the expressed genes ``[(line_idx, concepts)]`` in spine order."""
    from siona import couple as _cp
    res = _cp.couple(glyph_lines)
    word2code = {w: code for code, ws in res["communities"].items() for w in ws}
    spine = set(res["spine"])
    genes = [[c for c in anchor.transcribe([gl])[0] if c] for gl in glyph_lines]

    def _cw(g):
        return [w for c in g for w in c.replace("to ", "").lower().split()]

    qwords = set(anchor._words((anchor.concept(query) or [""])[0])) or {(query or "").strip().lower()}
    qcodes = {word2code[w] for w in qwords if w in word2code}
    if qcodes:
        expressed = [(i, g) for i, g in enumerate(genes) if any(word2code.get(w) in qcodes for w in _cw(g))]
    else:
        expressed = [(i, g) for i, g in enumerate(genes) if any(w in spine for w in _cw(g))]
    return sorted(expressed, key=lambda it: -sum(1 for w in _cw(it[1]) if w in spine))


def bridge_disambiguated(units):
    """Glyph→concept WITH SENSE-SELECTION (F608/F1127/F1156): the DETERMINATIVE FIRST (filter senses by class
    keywords — the script's own disambiguator), then the RELATIONAL context tie-break. Returns
    ``[(unit, best_gloss_or_None)]``."""
    from siona import relate as _rel
    _rel.load()
    cand = {u: anchor.concept(u) for u in units}
    ctx = set()
    for cs in cand.values():
        for c in cs:
            ctx |= set(anchor._words(c))
    out = []
    for u in units:
        cs = cand[u]
        dets = determinative(u)
        if dets and len(cs) > 1:
            kw = set().union(*(_CLASS_KEYWORDS.get(d, set()) for d in dets))
            match = [g for g in cs if set(anchor._words(g)) & kw]
            if match:
                cs = match
        if not cs:
            out.append((u, None))
        elif len(cs) == 1:
            out.append((u, cs[0]))
        else:
            out.append((u, max(cs, key=lambda g: _rel.relatedness(anchor._words(g), ctx - set(anchor._words(g))))))
    return out


# ── the sub-language markup KERNEL (F1156): determinative → class dispatch (uses the LOCAL determinative now) ──
def surface(raw_glyph_lines):
    """The genome SURFACE for Sumerian (F1156): ``[[(concept, [class…]) per glyph] per line]`` — the determinative
    preserved alongside each concept (via `anchor.transcribe(with_class=True)`)."""
    return anchor.transcribe(raw_glyph_lines, with_class=True)


def class_profile(raw_line):
    """The determinative CLASS profile of a raw Sumerian line — ``{class: count}`` (the line's semantic-class signature)."""
    prof = {}
    for g in raw_line:
        for c in determinative(g):
            prof[c] = prof.get(c, 0) + 1
    return prof


def route(raw_glyph, handlers, default=None):
    """Dispatch a glyph to a class-HANDLER by its determinative (markup → kernel dispatch, #225/#226):
    ``handlers = {class: fn(concept, glyph)}``; falls back to ``handlers['*']`` then ``default``."""
    concept = (anchor.concept(raw_glyph) or [None])[0]
    for cls in determinative(raw_glyph):
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
