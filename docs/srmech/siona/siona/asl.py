"""siona.asl — the ASL PHRASE-COHERENCY kernel layer + a SENSE-DETERMINATIVE English→ASL escaped-sign render.

ASL is a complete language of the Deaf community, NOT "English on the hands". Its unit is a SIGN, and a sign is
a CHORD of phonological parameters — handshape / selected-fingers / flexion / sign-type / movement / location
(F608: "a sign is a chord, the SENSE is the determinative"). ASL-gloss is the MIDDLE RUNG of the
knowledge→communication hierarchy (F966: ~2× cleaner recall, 41% fewer tokens than the English surface).

SENSE IS THE DETERMINATIVE (F608 / user 2026-07-06): one English word carries many meanings and ASL has a
DIFFERENT sign per sense — "beat" has ~a dozen signs (BEAT-defeat vs IMPACT-hit …), "light" has 13
(LAMP/FLASHLIGHT/GLOW vs LIGHT-WEIGHT), "run" has 4 (RUN vs OPERATE-MACHINE …). So the render must DISAMBIGUATE
the sense by CONTEXT and pick the matching sign. Choosing the wrong sign IS a coherency-loss mutation (F1121);
the sense-determinative is its correction — the ASL glyph choice is the context-coupling (F1123). Each candidate
sign carries its MEANING-SET (the sense's semantic field, from the ASL-LEX translation columns); the sense is
picked by the meaning-set that best matches the sentence context.

The embodied sign-chord layer is UNIVERSAL, not English/Deaf-specific: non-signers still GESTURE (co-speech) and
FOOT-FLAGGING FROGS communicate by visual limb-waving when the acoustic channel is jammed — three substrates
converging on the same embodied phrase-coherency primitive (F1125). So the sign-chord is a candidate universal
Rosetta shared layer (#54).

ATTESTED to ASL-LEX (Caselli, Sehyr, Cohen-Goldberg, Emmorey, *Behavior Research Methods* 2017;
`asllex/signdata.csv`, 2723 signs). Escaped-sign notation (F608 "LaTeX-for-signs"): a lexical sign is its GLOSS
in CAPS; a word with no ASL-LEX sign is FINGERSPELLED ``fs:C-A-R``; the chord is available as ``⟨…⟩``.
"""
import csv
import os
import re

__all__ = ["load_lex", "sign_chord", "candidate_signs", "disambiguate",
           "render", "gloss_signs", "CHORD_PARAMS"]

CHORD_PARAMS = ("Handshape.2.0", "SelectedFingers.2.0", "Flexion.2.0", "SignType.2.0",
                "Movement.2.0", "MajorLocation.2.0", "MinorLocation.2.0")
_TRANS_COLS = ("DominantTranslation", "NondominantTranslations", "SignBankEnglishTranslations")
_DEFAULT_LEX = "/home/skirklan/corpora/asllex/signdata.csv"
_DROP = frozenset("a an the is are was were be been being am of to in on at for and or but with as by "
                  "that this these those it its his her their our your my do does did has have had will "
                  "would can could should may might must".split())
_chord = None       # sign-gloss -> chord tuple
_senses = None      # english word -> [(sign-gloss, frozenset(meaning-words))]  (the sense candidates)


def _load(path=None):
    global _chord, _senses
    if _chord is not None:
        return
    # 1) prefer the BUNDLED attested JSON subset (ships with the package → ASL works out-of-the-box)
    jp = os.path.join(os.path.dirname(__file__), "asl_lex.json")
    if path is None and os.path.exists(jp):
        import json
        b = json.load(open(jp, encoding="utf-8"))
        _chord = {g: tuple(c) for g, c in b.get("signs", {}).items()}
        _senses = {w: [(s, frozenset(m)) for s, m in cands] for w, cands in b.get("senses", {}).items()}
        return
    # 2) fallback: parse the external ASL-LEX CSV (the build-time source for the bundle)
    _chord, _senses = {}, {}
    p = path or _DEFAULT_LEX
    if not os.path.exists(p):
        return
    from collections import defaultdict
    senses = defaultdict(list)
    with open(p, newline="", encoding="latin-1") as f:
        r = csv.reader(f)
        cols = next(r)
        gi = cols.index("LemmaID") if "LemmaID" in cols else 1
        ei = cols.index("EntryID") if "EntryID" in cols else 0
        chi = [cols.index(c) for c in CHORD_PARAMS if c in cols]
        tci = [cols.index(c) for c in _TRANS_COLS if c in cols]
        for row in r:
            if gi >= len(row):
                continue
            base = re.sub(r"[_\d]+$", "", (row[gi] or "").strip()).lower()   # 'run_1' -> 'run' (the sign gloss)
            eid = (row[ei] if ei < len(row) else base).strip()
            chord = tuple((row[i] if i < len(row) else "") for i in chi)
            if base and base not in _chord:
                _chord[base] = chord
            mset = set()
            for i in tci:
                for t in re.split(r"[;,/|]| and ", (row[i] if i < len(row) else "").lower()):
                    t = t.strip()
                    if t and len(t) <= 20:
                        mset.add(t)
            mset = frozenset(mset) or frozenset([base])
            for t in mset:                                                    # english word -> this sense-sign
                senses[t].append((base, mset))
    _senses = dict(senses)


def load_lex(path=None):
    """Load ASL-LEX → the sign-CHORD map ``{gloss: chord}``; also builds the SENSE candidates. Cached."""
    _load(path)
    return _chord


def candidate_signs(word):
    """The candidate ASL signs for an English ``word`` — ``[(sign_gloss, meaning_set)]``, one per SENSE (F608).
    ``beat`` → the IMPACT sense and the BEAT/defeat sense; ``light`` → ~13 senses."""
    _load()
    return _senses.get((word or "").strip().lower(), [])


def sign_chord(word):
    """The ASL sign CHORD for ``word`` (the embodied concept parameters), or ``None`` if it has no sign."""
    _load()
    return _chord.get((word or "").strip().lower())


def disambiguate(word, context=()):
    """SENSE-DETERMINATIVE (F608): pick the ASL sign for ``word`` whose MEANING-SET best matches the ``context``
    words — the correct glyph FOR CONTEXT, not a blind first-sense. Returns ``(sign_gloss, meaning_set)`` or
    ``None``. Ties break to the sign whose own gloss IS the word (the dominant sense). HONEST: this is a
    meaning-set∩context overlap — a weak first WSD; the strong sense-read is the deeper gloss layer (F1124)."""
    cands = candidate_signs(word)
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    ctx = {w.strip().lower() for w in context}
    ctx2 = set(ctx)
    for w in ctx:                                            # 1-hop context expansion: the context words' own senses
        for _, ms in candidate_signs(w):
            ctx2 |= ms
    lw = word.strip().lower()
    # score = meaning-set∩context overlap; ties break to the sign whose gloss IS the word (the dominant sense)
    return max(cands, key=lambda c: (len(c[1] & ctx2), c[0] == lw))


def _lemma_variants(w):
    yield w
    if w.endswith("ies") and len(w) > 4:
        yield w[:-3] + "y"
    for suf in ("s", "es", "ed", "ing", "d"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            yield w[:-len(suf)]


def _resolve(lw, context):
    for v in _lemma_variants(lw):
        best = disambiguate(v, context)
        if best:
            return best
    return None


def gloss_signs(text, *, chord=False):
    """Render English ``text`` → a LIST of ASL escaped signs, SENSE-DISAMBIGUATED by sentence context (F608):
    a lexical sign is its GLOSS in CAPS (optionally with its ``⟨chord⟩``); a non-sign content word is
    fingerspelled ``fs:W-O-R-D``; ASL-carried function words drop (content-density, F966)."""
    _load()
    toks = re.findall(r"[A-Za-z']+", text or "")
    content = [t for t in toks if t.lower() not in _DROP]
    out = []
    for i, w in enumerate(content):
        context = [c for j, c in enumerate(content) if j != i]      # the rest of the clause = the determinative
        best = _resolve(w.lower(), context)
        if best:
            tok = best[0].upper()
            if chord:
                tok += "⟨%s⟩" % ",".join(x for x in _chord.get(best[0], ()) if x and x != "NA")
            out.append(tok)
        else:
            out.append("fs:" + "-".join(w.upper()))
    return out


def render(text, *, chord=False):
    """English ``text`` → a SENSE-DISAMBIGUATED ASL escaped-sign gloss STRING. Siona's ASL output surface."""
    return " ".join(gloss_signs(text, chord=chord))
