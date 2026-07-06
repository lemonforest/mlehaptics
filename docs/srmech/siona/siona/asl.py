"""siona.asl — the ASL PHRASE-COHERENCY kernel layer + the first framework-native ASL escaped-sign RENDER.

ASL is a complete language of the Deaf community, NOT "English on the hands". Its unit is a SIGN, and a sign is
a CHORD of phonological parameters — handshape / selected-fingers / flexion / sign-type / movement / location
(F608: "a sign is a chord, the sense is the determinative"). ASL-gloss is the MIDDLE RUNG of the
knowledge→communication hierarchy (F966: ~2× cleaner recall, 41% fewer tokens than the English surface). This
module makes that a genuine Siona kernel layer and Siona's FIRST ASL output surface: English → ASL escaped signs.

The sign-chord layer is UNIVERSAL, not English-specific: people who never learned to sign still GESTURE
(co-speech hand movements) when explaining things verbally — the SAME handshape/location/movement parameters,
surfacing spontaneously — because the phrase-coherency layer is intrinsic to how humans group meaning into
concept-phrases (user, 2026-07-06, F1125). So the sign-chord is a candidate UNIVERSAL shared layer (the Rosetta
layer, #54), the embodied concept substrate byte/word encodings skip.

ATTESTED to ASL-LEX (Caselli, Sehyr, Cohen-Goldberg, Emmorey, *Behavior Research Methods* 2017;
`asllex/signdata.csv`, 2723 signs). Escaped-sign notation (F608 "LaTeX-for-signs"): a lexical sign is its GLOSS
in CAPS; a word with no ASL-LEX sign is FINGERSPELLED as ``fs:C-A-R``; the chord is available as ``⟨…⟩``.
"""
import csv
import os
import re

__all__ = ["load_lex", "sign_chord", "render", "gloss_signs", "CHORD_PARAMS"]

# the ASL-LEX phonological parameters that compose the sign CHORD (the ".2.0" = the coded/rated release columns)
CHORD_PARAMS = ("Handshape.2.0", "SelectedFingers.2.0", "Flexion.2.0", "SignType.2.0",
                "Movement.2.0", "MajorLocation.2.0", "MinorLocation.2.0")

_DEFAULT_LEX = "/home/skirklan/corpora/asllex/signdata.csv"
# ASL content-density: pronouns/articles/copulas/prepositions are carried by space+grammar, not separate signs.
_DROP = frozenset("a an the is are was were be been being am of to in on at for and or but with as by "
                  "that this these those it its his her their our your my do does did has have had will "
                  "would can could should may might must".split())
_lex = None


def load_lex(path=None):
    """Load the ASL-LEX sign lexicon → ``{gloss: chord-tuple}`` (gloss = ``LemmaID``; chord = CHORD_PARAMS).
    Cached after first load. Returns ``{}`` if the corpus is absent (render then fingerspells everything)."""
    global _lex
    if _lex is not None:
        return _lex
    p = path or _DEFAULT_LEX
    _lex = {}
    if not os.path.exists(p):
        return _lex
    with open(p, newline="", encoding="latin-1") as f:
        r = csv.reader(f)
        cols = next(r)
        gi = cols.index("LemmaID") if "LemmaID" in cols else 1
        ci = [cols.index(c) for c in CHORD_PARAMS if c in cols]
        for row in r:
            if gi >= len(row):
                continue
            g = (row[gi] or "").strip().lower()
            g = re.sub(r"[_\d]+$", "", g)                      # strip disambiguating suffix: 'run_1' -> 'run'
            if g and g not in _lex:
                _lex[g] = tuple((row[i] if i < len(row) else "") for i in ci)
    return _lex


def sign_chord(word):
    """The ASL sign CHORD for an English ``word`` (the embodied concept parameters), or ``None`` if the word has
    no ASL-LEX sign (→ it would be fingerspelled). The chord is the phrase-coherency substrate — the same
    handshape/location/movement a co-speech gesture uses."""
    return load_lex().get((word or "").strip().lower())


def _lemma_variants(w):
    """Cheap English de-inflection so ``helps``/``helping`` reach the ``help`` sign before fingerspelling."""
    yield w
    if w.endswith("ies") and len(w) > 4:
        yield w[:-3] + "y"
    for suf in ("s", "es", "ed", "ing", "d"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            yield w[:-len(suf)]


def _lookup(lw):
    lex = load_lex()
    for v in _lemma_variants(lw):
        if v in lex:
            return v
    return None


def _fingerspell(word):
    return "fs:" + "-".join(word.upper())


def gloss_signs(text, *, chord=False):
    """Render English ``text`` → a LIST of ASL escaped signs: a lexical sign is its GLOSS in CAPS (optionally with
    its ``⟨chord⟩``); a non-sign content word is fingerspelled ``fs:W-O-R-D``; ASL-carried function words drop
    (content-density, F966). Order is source order — a topic-comment reorder is the next rung (not invented here)."""
    lex = load_lex()
    out = []
    for w in re.findall(r"[A-Za-z']+", text or ""):
        lw = w.lower()
        if lw in _DROP:
            continue
        sign = _lookup(lw)                                    # de-inflect before fingerspelling
        if sign:
            tok = sign.upper()
            if chord:
                tok += "⟨%s⟩" % ",".join(x for x in lex[sign] if x and x != "NA")
            out.append(tok)
        else:
            out.append(_fingerspell(w))
    return out


def render(text, *, chord=False):
    """English ``text`` → an ASL escaped-sign gloss STRING (signs space-separated). Siona's ASL output surface."""
    return " ".join(gloss_signs(text, chord=chord))
