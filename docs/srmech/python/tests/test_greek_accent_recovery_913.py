"""#913 — the Greek uppercase→lowercase accent 'loss' is a memoryless-projection
artifact, NOT inherent unrecoverability. This test MACHINE-CHECKS the corrected
understanding so the honesty is gated by CI.

The original #913 claim was "ΓΛΩΣΣΑ does not fold to γλώσσα — no casefold policy
repairs it," read as *inherently unrecoverable*. That conflated "a memoryless
per-character casefold cannot do it" with "it cannot be done." It cannot:

  * casefold is a context-free, per-character string homomorphism. It maps
    Ω→ω (U+03C9) with no word-model, so it CANNOT emit the stressed ώ (U+03CE)
    of γλώσσα — the tonos is absent from the uppercase codepoint stream.
  * BUT the tonos is not absent from the WORD. Modern-Greek stress is lexically
    fixed (free within the three-syllable window; not computable from the letter
    skeleton by rule). So the accented form is a deterministic function of the
    lexeme — a recoverable fiber that lives in lexical structure, which the
    local map provably cannot see. Recovery is a *structure-aware inverse*
    (lexicon + morphology + optional context), not a memoryless map.

The sharp proof that structure-aware recovery is real and already shipping:
``str.lower`` ALREADY performs one — final sigma, ΟΔΟΣ→οδο**ς** (U+03C2),
recovered from word-boundary POSITION — while dropping the tonos in the same
call. The dividing line is exactly locally-computable-from-position (final
sigma: yes) vs requires-the-lexicon (accent: no). srmech's fold surface
inherits the same memoryless property; the recovery, if ever built, is an
E-catalog (lexicon lookup) ∘ D (morphology) ∘ C (which-accent) ∘ K (present/
absent) cascade — a future arc gated on an attested Greek stress lexicon, NOT
shipped here.

Honest bound (this is the whole point — the recovery is NOT total): a genuinely
irreducible tail remains — heterophonic homographs (η/ή, που/πού, πως/πώς,
άλλα/αλλά, ματια→{μάτια, ματιά}) that a word IN ISOLATION cannot disambiguate,
plus OOV proper nouns and syntactic/enclitic accents. These need sentence
context, not a per-word map. This test pins BOTH halves: deterministic recovery
is possible for lexicon words, AND the tail is genuinely multi-valued.

Prior art (attested, not fabricated): diacritic restoration is an established
NLP task — Náplava & Straka "Diacritics Restoration using BERT"; "Dilated CNNs
for Lightweight Diacritics Restoration," LREC 2022 (arXiv:2201.06757); Greek is
an actively-surveyed NLP language (arXiv:2408.10962). No Greek accuracy figure
is asserted here (that would be unattested).

Pure Python (str + unicodedata); no srmech import, no native lib.
"""

from __future__ import annotations

import unicodedata as ud


def _strip_accents(s: str) -> str:
    """The bare skeleton: NFD-decompose and drop combining marks (the tonos)."""
    return "".join(c for c in ud.normalize("NFD", s) if ud.category(c) != "Mn")


def _n_tonos(s: str) -> int:
    """How many combining acute (tonos) marks the string carries."""
    return sum(1 for c in ud.normalize("NFD", s) if c == "́")


# ── The word this whole ticket is about ──────────────────────────────────────
_UPPER = "ΓΛΩΣΣΑ"          # ΓΛΩΣΣΑ (no accents)
_LOWER_TRUE = "γλώσσα"     # γλώσσα (ώ = U+03CE)
_LOWER_SKELETON = "γλωσσα"  # γλωσσα (ω = U+03C9)


def test_casefold_is_a_memoryless_projection_that_drops_the_tonos():
    """casefold(ΓΛΩΣΣΑ) yields the ACCENTLESS skeleton — the omega is plain
    U+03C9, not the stressed U+03CE. The loss belongs to the memoryless map,
    not to the string's recoverable information content."""
    folded = _UPPER.casefold()
    assert folded == _LOWER_SKELETON            # γλωσσα
    assert folded != _LOWER_TRUE                # ≠ γλώσσα
    assert ord(folded[2]) == 0x03C9             # plain omega
    assert ord(_LOWER_TRUE[2]) == 0x03CE        # omega-with-tonos
    assert _n_tonos(folded) == 0 and _n_tonos(_LOWER_TRUE) == 1


def test_lower_ALREADY_does_a_structure_aware_recovery_final_sigma():
    """The refutation of 'no policy can recover a dropped feature': str.lower
    ALREADY recovers one — final sigma is position-dependent (ς at word end,
    σ elsewhere), a structure-aware choice the memoryless-per-char intuition
    would forbid — while it drops the LEXICAL accent in the same call. Local
    structure: recovered. Lexical structure: not (yet)."""
    assert "ΟΔΟΣ".lower() == "οδος"   # ΟΔΟΣ -> οδος
    assert ord("ΟΔΟΣ".lower()[-1]) == 0x03C2               # FINAL sigma recovered
    # medial sigma stays medial — same letter, position-sensitive output
    assert "ΣΩ".lower()[0] == "σ"                              # ΣΩ -> σω (medial)
    # yet the tonos is dropped for a word that has one:
    assert _n_tonos(_UPPER.lower()) == 0


# ── A tiny ATTESTED deterministic lexicon (the E-catalog core) ───────────────
# skeleton -> its UNIQUE standard accented form. Each entry verified: the
# accented form strips back to exactly this skeleton and carries exactly one
# tonos (asserted below — the data can't silently rot).
_LEXICON = {
    "γλωσσα": "γλώσσα",          # γλωσσα -> γλώσσα (language)
    "ανθρωπος": "άνθρωπος",  # ανθρωπος -> άνθρωπος (human)
    "θαλασσα": "θάλασσα",          # θαλασσα -> θάλασσα (sea)
    "μητερα": "μητέρα",                    # μητερα -> μητέρα (mother)
    "ανθρωπων": "ανθρώπων",  # ανθρωπων -> ανθρώπων (gen.pl., stress SHIFTED off the antepenult)
}


def _recover(skeleton: str) -> str:
    """The deterministic structure-aware inverse for lexicon words: look the
    bare skeleton up (Class E catalog) and return its unique accented form."""
    return _LEXICON[skeleton]


def test_deterministic_recovery_via_lexicon_is_possible():
    """The direct refutation of 'unrecoverable': a lexicon lookup deterministically
    recovers the tonos for every entry — including a paradigm stress-SHIFT form
    (ανθρωπων→ανθρώπων) whose skeleton alone is unambiguous. Recovery IS possible;
    it is simply not a memoryless per-char map."""
    for skel, accented in _LEXICON.items():
        assert _recover(skel) == accented
        assert _strip_accents(accented) == skel   # the recovered form projects back
        assert _n_tonos(accented) == 1             # exactly one stress mark
    # and the headline word:
    assert _recover(_LOWER_SKELETON) == _LOWER_TRUE   # γλωσσα -> γλώσσα


# ── The honest irreducible tail: skeletons that are genuinely multi-valued ────
# ATTESTED heterophonic homographs — one lowercase skeleton, >=2 valid
# accentuations, distinguished ONLY by stress. A word in isolation cannot pick.
_AMBIGUOUS = {
    "ματια": ("μάτια", "ματιά"),   # ματια: μάτια (eyes) | ματιά (a glance)
    "αλλα": ("άλλα", "αλλά"),                     # αλλα: άλλα (other) | αλλά (but)
    "η": ("η", "ή"),                                                                          # η (the, fem.) | ή (or)
    "που": ("που", "πού"),                                       # που (that/rel.) | πού (where?)
    "πως": ("πως", "πώς"),                                       # πως (that/conj.) | πώς (how?)
}


def test_the_irreducible_tail_is_genuinely_multivalued():
    """The honest bound: for these skeletons the map is genuinely MULTI-valued —
    every variant strips to the same skeleton, so a word-in-isolation inverse
    provably cannot choose. This is what needs sentence context, and it is why
    the recovery is 'deterministic core + probabilistic tail,' not total."""
    for skel, forms in _AMBIGUOUS.items():
        assert len(set(forms)) >= 2
        # all variants share the ONE skeleton -> the skeleton cannot disambiguate
        assert {_strip_accents(f) for f in forms} == {skel}
        # and the deterministic lexicon MUST NOT pretend to resolve these
        assert skel not in _LEXICON


def test_the_dividing_line_is_local_position_vs_lexical_identity():
    """One sentence, machine-checked: the feature str.lower recovers (final
    sigma) is computable from LOCAL position; the feature it drops (the tonos)
    requires the LEXEME. That boundary — not 'accents are lost' — is the whole
    #913 finding."""
    # local/positional: recovered by the memoryless-ish map itself
    assert "Σ".lower() == "σ" and "ΑΣ".lower()[-1] == "ς"
    # lexical: NOT recoverable from the skeleton without the catalog
    assert _UPPER.lower() == _LOWER_SKELETON               # map alone: no tonos
    assert _recover(_UPPER.lower()) == _LOWER_TRUE         # catalog: tonos restored
