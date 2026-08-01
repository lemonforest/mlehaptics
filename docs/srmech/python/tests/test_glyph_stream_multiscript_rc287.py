"""rc287 — the multi-script evaluation, as tests rather than as prose.

The design spike measured the retired word tokenizer against thirteen writing
systems and found six distinct failure modes. Prose recording that is not a
guard; these are the guards. Each test names the language, the concrete input,
and what the *word* front door did wrong — so a regression reads as "Turkish
broke again", not as "assertion failed".

The emoji cases are last and are the sharpest: they are where codepoint-level
and glyph-level answers diverge maximally, and where the old path returned an
empty list or a base-less mark.

Both coherency projections run every case (ADR-0009 — neither is primary).
"""
from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.math import text as T


@pytest.fixture(params=["scripting", "compiled"])
def projection(request, monkeypatch):
    """Run every case in BOTH projections."""
    if request.param == "scripting":
        monkeypatch.setattr(_native, "has_native_text_glyph_stream",
                            lambda: False)
    elif not _native.has_native_text_glyph_stream():
        pytest.skip("native srmech_text_glyph_stream not loaded")
    return request.param


# ── scripts where the word decision merely under-performed ─────────────────

def test_english_is_glyphs_not_words(projection):
    """The baseline. Note what is NOT dropped any more: single letters ('a',
    'I') survived no length floor, and 'the'/'on' survive no stoplist.

    F1257 found the operator layer IS the conserved core (94/94 tokens entering
    it were stoplist members), so the old default discarded precisely the layer
    the science found load-bearing.
    """
    assert T.glyph_stream("a cat") == ["a", " ", "c", "a", "t"]
    assert T.glyph_stream("I am") == ["I", " ", "a", "m"]


def test_turkish_dotted_and_dotless_i_stay_distinct(projection):
    """`casefold` collapsed Turkish's i/ı distinction and split the vocabulary.

    'İ'.casefold() returns TWO codepoints (i + U+0307), and 'I'.casefold()
    returns 'i', colliding with dotless 'ı'. The same word in two cases became
    two types. No casefold at the front door, no collision.
    """
    assert T.glyph_stream("ışık") == ["ı", "ş", "ı", "k"]
    assert T.glyph_stream("IŞIK") == ["I", "Ş", "I", "K"]
    # İ carries its dot as one perceived character.
    assert T.glyph_stream("İstanbul")[0] == "İ"
    assert T.glyph_stream("ışık") != T.glyph_stream("IŞIK")


def test_greek_accented_and_final_sigma(projection):
    """The design corrected the brief here, and TWO Greek non-issues are
    pinned as non-issues so nobody "fixes" them later:

    * **Final sigma was never the failure.** `casefold` correctly unified
      ς→σ, which is the desirable behaviour. Do not add a ς→σ mapping.
    * **U+02BB ʻokina was never mishandled either** (see the Hawaiian test) —
      that one is a homoglyph bug, not a category bug.

    The real Greek break is **uppercase accent loss** (ΓΛΩΣΣΑ vs γλώσσα),
    which no casefold policy can repair. **rc287 does NOT fix it and does not
    claim to** — it is a downstream case/accent-matching concern, filed
    separately and out of scope here. What this test pins is only that
    segmentation is correct in both cases: accented and unaccented, upper and
    lower, are each their own clusters, and the two forms remain DISTINCT.
    """
    assert T.glyph_stream("γλώσσα") == ["γ", "λ", "ώ", "σ", "σ", "α"]
    assert T.glyph_stream("ΓΛΩΣΣΑ") == ["Γ", "Λ", "Ω", "Σ", "Σ", "Α"]
    # Final sigma is its own cluster, distinct from medial sigma.
    assert T.glyph_stream("λόγος")[-1] == "ς"
    # The accent-loss pair stays DISTINCT at the front door — recording the
    # open issue, not papering over it.
    assert T.glyph_stream("ΓΛΩΣΣΑ") != T.glyph_stream("γλώσσα")


def test_hawaiian_okina_survives_in_both_encodings(projection):
    """The design corrected the brief here too, and found a REAL bug behind it.

    The brief said ʻokina (U+02BB) was mishandled; it was not — U+02BB is Lm,
    so the L/M rule kept it. The genuine failure was the homoglyph: U+2019 was
    in `_APOS`, mapped to ASCII "'", then stripped word-initially, so
    '’okina' → ['okina'] — the okina DELETED. U+2019 is extremely common as an
    okina substitute in real text.

    Both encodings now survive, as their own clusters.
    """
    assert T.glyph_stream("ʻokina")[0] == "ʻ"          # U+02BB
    assert T.glyph_stream("’okina")[0] == "’"          # U+2019 — was deleted
    assert T.glyph_stream("Hawaiʻi") == list("Hawaiʻi")
    assert T.glyph_stream("Hawai’i") == list("Hawai’i")


def test_bislama_latin_script_vanuatu(projection):
    """Bislama — the design's anchor language (Vanuatu sand drawing, one path
    read across ~80 language groups). Latin script, so this is a plain
    regression guard rather than a hard case."""
    assert T.glyph_stream("Yumi") == ["Y", "u", "m", "i"]
    assert "".join(T.glyph_stream("Bislama i lanwis")) == "Bislama i lanwis"


# ── right-to-left ──────────────────────────────────────────────────────────

def test_arabic_keeps_combining_marks_with_their_base(projection):
    """A base and its harakat are ONE perceived character (GB9)."""
    assert T.glyph_stream("عربية") == ["ع", "ر", "ب", "ي", "ة"]
    # ARABIC LETTER BEH + FATHA -> one cluster, not two.
    assert T.glyph_stream("بَ") == ["بَ"]


def test_hebrew_points_attach_to_their_consonant(projection):
    """Niqqud are Extend, so they never split from the letter (GB9)."""
    assert T.glyph_stream("עברית") == ["ע", "ב", "ר", "י", "ת"]
    assert T.glyph_stream("בָּ") == ["בָּ"]     # BET + DAGESH + QAMATS = 1 cluster


# ── the scripts the derivation got WRONG (why vendoring won) ───────────────

def test_devanagari_conjuncts_are_single_clusters(projection):
    """GB9c. A `unicodedata`-only derivation was 8.0% wrong on Devanagari — it
    cannot see InCB at all, so conjuncts fall apart at the virama."""
    assert T.glyph_stream("क्षि") == ["क्षि"]
    # KA + VIRAMA + TA -> one conjunct cluster.
    assert T.glyph_stream("क्त") == ["क्त"]
    # A vowel sign stays with its consonant (SpacingMark, GB9a).
    assert T.glyph_stream("का") == ["का"]


def test_thai_combining_vowels_and_tone_marks(projection):
    """Thai is scriptio continua: the old path returned the entire 96-character
    run as ONE 'word'. Above-line vowels and tone marks are Extend and stay
    attached to their consonant.
    """
    out = T.glyph_stream("ภาษาไทย")
    assert "".join(out) == "ภาษาไทย"
    assert len(out) > 1, "scriptio continua must not collapse to one token"
    # SARA I and MAI EK are combining -> attached, not free-standing.
    assert T.glyph_stream("กิ") == ["กิ"]
    assert T.glyph_stream("ก่") == ["ก่"]


# ── scriptio continua: where the vocabulary was being manufactured ─────────

def test_chinese_splits_into_characters(projection):
    """The headline failure: `tokenize` returned ONE 45-character token here,
    and ~89% of Chinese types were singletons as a result."""
    text = "语言是人类交流的工具"
    out = T.glyph_stream(text)
    assert out == list(text)
    assert len(out) == 10


def test_japanese_mixed_scripts_and_combining_marks(projection):
    """Kanji + kana in one run; dakuten combines onto its kana.

    Two routes to the same perceived character, and both must give ONE cluster.
    NFC composes KA + COMBINING DAKUTEN into precomposed GA; with normalisation
    OFF the pair is still one cluster because the dakuten is Extend (GB9). The
    second assertion is the one that exercises a break rule -- the first only
    exercises normalisation, which is a different claim.
    """
    assert T.glyph_stream("\u65e5\u672c\u8a9e") == ["\u65e5", "\u672c", "\u8a9e"]
    decomposed = "\u304b\u3099"          # HIRAGANA KA + COMBINING DAKUTEN
    assert T.glyph_stream(decomposed) == ["\u304c"]                    # NFC -> GA
    assert T.glyph_stream(decomposed, unicode_normalize=False) == [decomposed]


def test_korean_syllables_and_jamo_compose(projection):
    """Hangul precomposed syllables are one cluster each (LV/LVT recovered by
    the UAX #29 section 3 syllable algebra, not by table rows).

    Conjoining jamo are the interesting half: NFC composes L+V+T into the
    precomposed syllable, but with normalisation OFF they must STILL form one
    cluster, via GB6 (L x V) and GB8 (LVT x T). That is the path the algebra
    and the jamo table rows actually cooperate on.
    """
    assert T.glyph_stream("\ud55c\uad6d\uc5b4") == ["\ud55c", "\uad6d", "\uc5b4"]
    jamo = "\u1100\u1161\u11a8"          # CHOSEONG KIYEOK + JUNGSEONG A + JONGSEONG KIYEOK
    assert T.glyph_stream(jamo) == ["\uac01"]                          # NFC -> GAK
    assert T.glyph_stream(jamo, unicode_normalize=False) == [jamo]
    # The jamo-filler pair a derived table got wrong (GB6, L x V):
    # U+1160 is GBP=V yet sits BELOW VBase, so syllable-algebra jamo mis-tags it.
    filler = "\u1100\u1160"
    assert T.glyph_stream(filler, unicode_normalize=False) == [filler]


def test_single_codepoint_cjk_content_words_survive(projection):
    """`_MIN_LEN = 2` deleted both content words here: tokenize('中 国') -> []."""
    assert T.glyph_stream("中 国") == ["中", " ", "国"]


# ── emoji: maximal divergence between codepoint and glyph ──────────────────

def test_emoji_zwj_family_is_one_cluster(projection):
    """GB11. Seven codepoints, one thing a human sees. The old path returned []."""
    family = "\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466"
    assert len(family) == 7
    assert T.glyph_stream(family) == [family]


def test_emoji_skin_tone_modifier_is_one_cluster(projection):
    """A base emoji + Fitzpatrick modifier is one perceived character."""
    wave = "\U0001F44B\U0001F3FD"
    assert T.glyph_stream(wave) == [wave]


def test_flag_pairs_are_one_cluster_each(projection):
    """GB12/GB13 — Regional_Indicator pairs by PARITY, not greedily."""
    vu = "\U0001F1FB\U0001F1FA"          # Vanuatu
    nz = "\U0001F1F3\U0001F1FF"          # New Zealand
    assert T.glyph_stream(vu) == [vu]
    assert T.glyph_stream(vu + nz) == [vu, nz]
    # An odd trailing indicator stands alone rather than merging backwards.
    assert T.glyph_stream(vu + "\U0001F1FB") == [vu, "\U0001F1FB"]


def test_keycap_sequence_keeps_its_base(projection):
    """The design's 'bonus failure': the old L/M rule dropped the digit (Nd)
    and emitted the two combining marks as a token with NO base character —
    tokenize('1️⃣') -> ['️⃣']. A cluster cannot be base-less."""
    keycap = "1️⃣"
    assert T.glyph_stream(keycap) == [keycap]
    assert T.glyph_stream(keycap)[0][0] == "1"


# ── invariants that must hold across every script above ────────────────────

@pytest.mark.parametrize("text", [
    "a cat", "ışık", "γλώσσα", "Hawai’i", "Bislama i lanwis", "عربية",
    "עברית", "क्षि", "ภาษาไทย", "语言是人类交流的工具", "日本語", "한국어",
    "\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466",
    "\U0001F1FB\U0001F1FA", "1️⃣",
])
def test_lossless_across_every_script(projection, text):
    """No script may lose a codepoint. The old path silently deleted content
    (the okina, single-codepoint CJK, every emoji); losing data at the front
    door is the failure class this whole change exists to end.
    """
    assert "".join(T.glyph_stream(text)) == text


@pytest.mark.parametrize("text", [
    "语言是人类交流的工具", "ภาษาไทย", "日本語",
])
def test_scriptio_continua_no_longer_collapses(projection, text):
    """The vocabulary-manufacturing failure, guarded directly: these scripts
    must never come back as a single mega-token.
    """
    out = T.glyph_stream(text)
    assert len(out) > 1
    assert max(len(g) for g in out) < len(text)
