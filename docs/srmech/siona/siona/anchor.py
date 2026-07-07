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
import html
import json
import os
import re

__all__ = ["load_anchor", "load_sux", "concept", "determinative", "bridge_units", "bridge_disambiguated", "transcribe", "express_story", "render_fluent", "render_repaired", "transcription_errors", "have_anchor"]

_VYGUS = "/home/skirklan/corpora/egyptian_tla/vygus_dict_slice.jsonl"          # Egyptian (Vygus jsonl)
_SUX = "/home/skirklan/corpora/etcsl/sux_gilgamesh_lemmatized.json"           # Sumerian (ETCSL Gilgameš, lemmatized)
_anchor = None       # LEMMA → [English concept glosses]  (the ACTIVE anchor)
_surf2lemma = None   # surface form → lemma (the lemmatization layer, F1144; None = no lemmatization)


def _norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))     # strip markup (KEEP content), unescape entities (F1155)
    return t.strip().lstrip(".=").lower()                    # so concept() resolves a RAW glyph too (idempotent on clean)


# Sumerian DETERMINATIVES (F1155): the script's OWN glyph-intrinsic semantic-class classifiers — a coherency-
# AGNOSTIC type tag (divine / place / wood / stone …, NOT noun/verb), written INTO the glyph as a super/sub-script.
# This is the genome-surface identifier that abstracts away POS. clean()/transcribe were STRIPPING these (a
# no-doctoring-SSoT violation, F817) — they are FIBER, not noise.
_DET_CLASS = {"d": "divine", "diĝir": "divine", "ki": "place", "ĝiš": "wood", "gish": "wood", "ĝeš": "wood",
              "na4": "stone", "gi": "reed", "lu2": "person", "lú": "person", "munus": "woman", "kur": "land",
              "uruda": "copper", "urudu": "copper", "tug2": "textile", "gada": "linen", "zabar": "bronze",
              "dug": "vessel", "u2": "plant", "šem": "aromatic", "mušen": "bird", "ku6": "fish", "id2":
              "watercourse", "kuš": "leather", "ansze": "equid", "e2": "building", " nisi": "vegetable"}

# class → English gloss keywords: lets the DETERMINATIVE disambiguate a polysemous glyph (F1156) by preferring the
# anchor sense consistent with the script's own class tag (a place-classified glyph → the toponym sense, not a homophone).
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


def determinative(raw_glyph):
    """Extract the Sumerian DETERMINATIVE(s) from a RAW glyph (F1155): the writing system's OWN semantic-class
    classifier — written as a ``<sup>…</sup>`` super/sub-script ({d}=divine, {ki}=place, {ĝiš}=wood, {na4}=stone)
    — a GLYPH-DERIVED, coherency-AGNOSTIC type tag (semantic CLASS, not noun/verb). This is the identifier the
    genome surface carries instead of POS. Returns the class name(s) (mapped; the raw tag if unmapped), or ``[]``
    for a bare glyph. NOTE: `clean()` / `transcribe` were STRIPPING these markers — a no-doctoring-SSoT violation
    (F817); the determinative is FIBER, the script's own coherency tag, not noise to remove."""
    out = []
    for d in re.findall(r"<sup>(.*?)</sup>", raw_glyph or ""):
        d = html.unescape(re.sub(r"<[^>]+>", "", d)).strip().lower()   # unescape HTML entities (ĝ = &#x011d;)
        if not d or d in "?!*":                                        # skip ETCSL editorial markers (uncertainty), not classifiers
            continue
        out.append(_DET_CLASS.get(d, d))
    return out


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


# ---- the surface VENEER (F1149): the separate lossy English-projection layer (F1128), kept distinct from substrate
_IRREG = {"go": "went", "say": "said", "seek": "sought", "come": "came", "give": "gave", "take": "took",
          "see": "saw", "make": "made", "stand": "stood", "strike": "struck", "fall": "fell", "hold": "held",
          "bring": "brought", "speak": "spoke", "build": "built", "beat": "beat", "cut": "cut", "set": "set",
          "put": "put", "run": "ran", "sit": "sat", "rise": "rose", "grow": "grew", "throw": "threw"}
_FUNCTION = frozenset(("the of a an and to in on at for with by from as is are was were be has have "
                       "his her its their my your our this that").split())


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
    """RENDER a line's sparse concepts → a continuous English form (the surface VENEER, F1149 — the SEPARATE lossy
    English projection, F1128, NOT the substrate render). Via the DNA→RNA→language path: :func:`_rna` couples the
    concepts (verb-anchored), then reorder verb-final→medial + conjugate (the ``_IRREG`` table) + a "the/of" glue.
    Rough by design — the substrate coherence is the concurrent cycle-read (`express_story`); this is only the
    human-readable veneer on top. Invents NO content — only re-orders, conjugates, and glues what was stored."""
    pre, verb, post = _rna(concept_line)
    if verb is None:                                        # noun phrase — Sumerian genitive chain
        cs = [c for c in pre if c]
        return ("the " + " of the ".join(cs)) if 1 < len(cs) <= 3 else " ".join(cs)
    subj = ("the " + " of the ".join(pre)) if pre else ""
    obj = ("the " + " ".join(post)) if post else ""
    return " ".join(x for x in (subj, _past(verb), obj) if x)


def _phrase_cycles(concepts):
    """Split a line's concepts into PHRASE-CYCLES at each verb (Sumerian is verb-final): each verb closes a cycle
    ``[operands… verb]``, so a MULTI-verb line is MULTIPLE phrase-cycles. This is the NER / Class-L phrase-scale
    unit (F1151) — repairing each verb-cluster at ITS scale, not the op-scale single-anchor that dropped the
    coupling (the F1150 62% floor). Returns a list of cycles."""
    cycles, cur = [], []
    for c in (x for x in concepts if x):
        cur.append(c)
        if c.startswith("to "):                            # a verb closes the phrase-cycle
            cycles.append(cur)
            cur = []
    if cur:
        cycles.append(cur)                                 # a trailing verbless operand tail
    return cycles


def render_repaired(concept_line, *, with_ec=False):
    """SCALE-STRATIFIED render (F1151) + intrinsic G4 chirality-EC (F1154 — **op(x)operand(x)EC**: the error-
    correction is the THIRD factor of the SAME transcription unit, not a downstream pass). Splits the line into
    phrase-cycles (:func:`_phrase_cycles`, one per verb) and renders EACH at its scale (:func:`render_fluent`),
    fixing the veneer's 62% floor (F1150). Each phrase-cycle carries a CHIRALITY (the verb's which-way, Class-C)
    the bit-exact silicon substrate FLATTENS (F552).

    ``with_ec=True`` runs the G4 chirality-EC (the metamer motif → selective Klein-4 fold, F1153) AS PART OF the
    render and returns ``(text, ec)`` where ``ec = {word: Klein-4 sector}`` preserves the which-way at the metamer
    loci — so a directional opposite is never collapsed. The EC RIDES WITH the render (one process emits operand +
    EC), proving EC is intrinsic to the transcription, not bolted on."""
    cycles = _phrase_cycles(concept_line)
    text = ", ".join(render_fluent(cy) for cy in cycles) if cycles else ""
    if with_ec:
        from siona import g4                                  # lazy: g4 imports anchor (avoid the import cycle)
        return text, g4.g4_fold(concept_line)                # op(x)operand(x)EC — the EC emitted by the same pass
    return text


def transcription_errors(rendered, source_concepts):
    """DETECT transcription errors via the T-vs-U / attestation WATERMARK (F1149). Biology detects C→U deamination
    because DNA uses T: any U is un-belonging = an unambiguous error (uracil-DNA-glycosylase excises it). ANALOG:
    every CONTENT token in a render must trace back to an ATTESTED stored concept (the "T" — the lemma/anchor); a
    content token that does NOT (no lemma / not a source concept or its conjugation) is the "U" — a transcription
    error. Function-word scaffold is exempt (the T-methyl backbone). Returns the un-attested (error) tokens."""
    src = set()
    for g in source_concepts:                              # the attested store: source concepts + their forms/glosses
        for w in re.split(r"[ ,;/()]+", (g or "").lower()):
            if len(w) >= 2:                                 # incl. short verbs (go/be) so their conjugations attest
                src.add(w)
                src.add(_past(w))
    errs = []
    for t in re.split(r"\s+", (rendered or "").strip()):
        tl = t.lower().strip(".,;:")
        if not tl or tl in _FUNCTION:                      # scaffold — the T-methyl backbone, exempt
            continue
        if tl not in src and (concept(tl) == []):          # content not traceable to an attested concept = U (error)
            errs.append(t)
    return errs


def express_story(glyph_lines, query, *, coupling=0.05):
    """Route the render through gene_express (F1148 — the DNA→RNA half-beat, F1147), scoped to a story: the story
    GENOME (each line's concepts a gene = the full-beat store) → EXPRESS the query-relevant subset (the half-beat
    working copy) CONCURRENTLY — every coupled gene selected AT ONCE (a set op, not a linear scan, F1147
    correction) — then a CYCLE-READ ordered by the recurring-concept spine (the_one: the concepts most shared
    across the expressed set are the phase-coupling backbone). Returns the expressed genes ``[(line_idx,
    concepts)]`` in cycle order. Same `gene_express` PRINCIPLE (F256/F1097) as the knowledge genome, story-scoped;
    the render then reads THIS (genome → gene_express → read), not the closed full genome directly."""
    from siona import relate as _rel
    _rel.load()
    genes = [[c for c in transcribe([gl])[0] if c] for gl in glyph_lines]      # store: per-line concept genes
    qc = (concept(query)[0].split(",")[0].lower() if concept(query) else (query or "").strip().lower())

    def couples(g):                                                            # coupled to the query? (concurrent gate)
        gl = [c.lower() for c in g]
        return qc in gl or any(_rel.related(qc, c) > coupling for c in gl)

    expressed = [(i, g) for i, g in enumerate(genes) if couples(g)]            # EXPRESS: the whole coupled subset at once
    freq = {}
    for _, g in expressed:                                                     # the recurring-concept spine (the_one)
        for c in {x.lower() for x in g}:
            freq[c] = freq.get(c, 0) + 1
    return sorted(expressed, key=lambda it: -sum(freq.get(c.lower(), 0) for c in it[1]))   # CYCLE-READ order


def transcribe(glyph_lines, *, with_class=False):
    """Orchestrate the glyph→concept bridge over a WHOLE text (F1145): each LINE (the phrase unit, F1143) →
    its concept-gloss per glyph. The FRACTAL-TOWER orchestration (F1117) — the per-line bridge assembled line →
    passage → story. Returns ``[[gloss-or-None per glyph] per line]``.

    ``with_class=True`` PRESERVES the DETERMINATIVE through the transcription (F1155/F1156 — stop stripping it):
    returns ``[[(gloss, [class…]) per glyph] per line]`` where ``class`` is the glyph's coherency-agnostic
    semantic-class tag (divine/place/wood…) — the genome-surface type the user asked for, carried WITH the concept.
    Accepts RAW glyphs (markup intact): `_norm` strips the surface for the concept lookup while `determinative`
    reads the raw `<sup>` for the class — so the determinative survives the pass instead of being doctored out."""
    out = []
    for line in glyph_lines:
        row = []
        for g in line:
            gl = concept(g)
            c = gl[0].split(",")[0] if gl else None
            row.append((c, determinative(g)) if with_class else c)
        out.append(row)
    return out


def _words(gloss):
    return [w for w in re.split(r"[ ,;/()]+", (gloss or "").lower()) if len(w) > 2]


def bridge_disambiguated(units):
    """Glyph→concept WITH SENSE-SELECTION (F608/F1127/F1156). Two-tier disambiguation: (1) the DETERMINATIVE FIRST
    (F1156) — if a RAW glyph carries a class tag ({d}=divine, {ki}=place…), keep only the anchor senses consistent
    with that class (`_CLASS_KEYWORDS`); this is the script's OWN disambiguator, resolving a homophone by its
    written classifier before any statistics. (2) Then the RELATIONAL context tie-break — among the surviving
    senses, pick the gloss most RELATED (`relate`) to the other glyphs' concept words. Returns
    ``[(unit, best_gloss_or_None)]``."""
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
        dets = determinative(u)                                       # the script's OWN class tag (F1156)
        if dets and len(cs) > 1:                                      # DETERMINATIVE FIRST — filter senses by class
            kw = set().union(*(_CLASS_KEYWORDS.get(d, set()) for d in dets))
            match = [g for g in cs if set(_words(g)) & kw]
            if match:
                cs = match                                           # narrowed by the written classifier
        if not cs:
            out.append((u, None))
        elif len(cs) == 1:
            out.append((u, cs[0]))
        else:
            out.append((u, max(cs, key=lambda g: _rel.relatedness(_words(g), ctx - set(_words(g))))))  # relate tie-break
    return out
