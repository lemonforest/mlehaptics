"""rc293 (#928 / F1258 / UPSTREAM_NOTES §106) — ``srmech.amsc.text.fold_marks``.

THE NAME IS PART OF THE CONTRACT, SO IT IS TESTED
-------------------------------------------------
The op drops combining marks by Unicode category, and it is called
``fold_marks`` rather than the downstream name ``fold_accents`` because **a
virama is a mark, not an accent**. That is not a spelling preference: the
Latin-shaped name describes a Latin-shaped op, and the cases where the two
names would diverge are exactly the Indic ones this line of work exists to
stop mishandling. So the Devanagari case below is a FIRST-CLASS assertion, not
a bonus — and ``test_the_op_is_not_named_for_accents`` fails if the retired
vocabulary comes back.

WHAT "CATEGORY ONLY" BUYS, AND WHAT IT DELIBERATELY DOES NOT
------------------------------------------------------------
Scope is General_Category Mn / Mc / Me and nothing else. Several results that
look like omissions are the scope working correctly, so each is pinned with
the reason attached: ``ø`` keeps its stroke (part of the letter), the OHM SIGN
is untouched (a singleton with no mark in it), Hangul survives in either
normalization form (it decomposes to jamo, which are starters), and case is
never changed.
"""
from __future__ import annotations

import unicodedata

import pytest

from srmech.amsc import _native
from srmech.amsc import text as T
from srmech.amsc import _unicode_fold_tables as fdt


# ── the naming argument, as an executable claim ───────────────────────────
def test_virama_is_a_mark_which_is_why_the_op_is_not_called_fold_accents():
    """क्षि → कष. The virama (U+094D) and the vowel sign (U+093F) are BOTH
    marks; neither is an accent by any reading. An op named ``fold_accents``
    would either wrongly exclude them or be misnamed — this assertion is the
    reason the name settled where it did."""
    assert unicodedata.category("्") == "Mn"      # virama, nonspacing
    assert unicodedata.category("ि") == "Mc"      # vowel sign, spacing
    assert T.fold_marks("क्षि") == "कष"


def test_the_op_is_not_named_for_accents():
    """The retired downstream name must not come back through the front door."""
    assert hasattr(T, "fold_marks")
    assert not hasattr(T, "fold_accents"), \
        "fold_accents is the retired downstream name — a virama is not an accent"
    assert "fold_marks" in T.__all__
    assert "fold_accents" not in T.__all__
    doc = T.fold_marks.__doc__ or ""
    # The docstring may NAME the retired spelling to explain the decision, but
    # must not present the op as folding "accents".
    assert "combining mark" in doc.lower()


# ── the Latin case (the easy one) ─────────────────────────────────────────
@pytest.mark.parametrize("src,want", [
    ("naïve", "naive"),
    ("café", "cafe"),
    ("Å", "A"),
    ("ñ", "n"),
    ("ế", "e"),          # doubly-composed: circumflex THEN acute
    ("Ǻ", "A"),          # ring + acute
])
def test_latin_precomposed_folds_to_its_base(src, want):
    assert T.fold_marks(src) == want


def test_decomposed_input_gives_the_same_answer_as_precomposed():
    """The table's map rows handle precomposed characters and its drop rows
    handle decomposed sequences, so the op needs NO normalizer — which is what
    lets a bare-C host with no ``unicodedata`` be correct."""
    nfc = unicodedata.normalize("NFC", "naïve")
    nfd = unicodedata.normalize("NFD", "naïve")
    assert nfc != nfd                       # genuinely different inputs
    assert T.fold_marks(nfc) == T.fold_marks(nfd) == "naive"


def test_a_bare_combining_mark_is_dropped():
    assert T.fold_marks("́") == ""
    assert T.fold_marks("á̧b") == "ab"


# ── the scope boundary: things that must NOT change ───────────────────────
@pytest.mark.parametrize("src,why", [
    ("ø", "a stroke is part of the letter, not a combining mark"),
    ("Ø", "same, uppercase"),
    ("đ", "a bar is part of the letter"),
    ("ı", "dotless i is its own letter"),
    ("Ω", "OHM SIGN: a singleton mapping with no mark in it"),
    ("한", "Hangul decomposes to jamo, which are starters"),
    ("日本語", "CJK carries no marks"),
    ("\U0001f44d", "emoji carry no marks"),
    ("hello, world!", "ASCII is untouched"),
])
def test_category_only_scope_leaves_these_alone(src, why):
    assert T.fold_marks(src) == src, why


def test_hangul_is_unchanged_in_either_normalization_form():
    """Hangul is the one place the op is form-sensitive, and correctly so: it
    PRESERVES the caller's form rather than composing or decomposing. It is a
    fold, not a normalizer, and jamo carry no marks either way."""
    for form in ("NFC", "NFD"):
        s = unicodedata.normalize(form, "한글")
        assert T.fold_marks(s) == s


def test_case_is_never_changed():
    """Casefolding is a per-locale decision and is explicitly out of scope —
    it is destructive in Turkish and a no-op in caseless scripts."""
    assert T.fold_marks("ÀÉÎÕÜ") == "AEIOU"
    assert T.fold_marks("àéîõü") == "aeiou"


def test_compatibility_folding_is_out_of_scope():
    """NFKD would expand these; category-only folding must not."""
    assert T.fold_marks("ﬁ") == "ﬁ"          # ligature, not a mark
    assert T.fold_marks("²") == "²"          # superscript, not a mark
    assert T.fold_marks("Ⅷ") == "Ⅷ"          # roman numeral, not a mark


# ── contract invariants ───────────────────────────────────────────────────
def test_idempotent():
    """Guaranteed by the vendored table being CLOSED (no replacement is itself
    foldable), which the attestation module asserts against the shipped bytes."""
    for s in ["naïve", "क्षि", "한글", "á̧", "ÀÉÎÕÜ", ""]:
        once = T.fold_marks(s)
        assert T.fold_marks(once) == once


def test_empty_and_whitespace():
    assert T.fold_marks("") == ""
    assert T.fold_marks("   ") == "   "
    assert T.fold_marks("\n\t") == "\n\t"


def test_never_grows_the_utf8_byte_length():
    """The C peer's ``out_cap >= text_len`` contract depends on this."""
    for s in ["naïve", "क्षि", "한글", "ế", "́" * 8, "日本語"]:
        assert len(T.fold_marks(s).encode()) <= len(s.encode())


def test_rejects_non_str():
    for bad in (b"bytes", 42, None, ["a"]):
        with pytest.raises(TypeError, match="fold_marks: text must be str"):
            T.fold_marks(bad)


# ── the two coherency projections agree (ADR-0009) ────────────────────────
CORPUS = [
    "naïve café résumé", "क्षि हिन्दी", "한글 테스트", "日本語のテスト",
    "Ελληνικά", "Русский", "العربية", "עִבְרִית", "Tiếng Việt",
    "á̧b̈", "́", "", "ASCII only", "👨‍👩‍👧‍👦 🇻🇺",
    "ÀÉÎÕÜ àéîõü", "ø đ ı Ω", "ế Ǻ Å",
]


@pytest.mark.skipif(not _native.has_native_text_fold_marks(),
                    reason="native fold peer not loaded")
@pytest.mark.parametrize("src", CORPUS)
def test_native_and_pure_projections_are_byte_identical(src):
    """Not a smoke test: with the table vendored, the two projections read the
    SAME bytes, so any divergence is a bug in one of the two loops."""
    native = T.fold_marks(src)
    real = _native.has_native_text_fold_marks
    _native.has_native_text_fold_marks = lambda: False
    try:
        pure = T.fold_marks(src)
    finally:
        _native.has_native_text_fold_marks = real
    assert native == pure, f"projection divergence on {src!r}"


@pytest.mark.skipif(not _native.has_native_text_fold_marks(),
                    reason="native fold peer not loaded")
def test_projections_agree_across_every_table_row():
    """Sampling would be weak evidence for a table-driven op — the interesting
    rows are sparse. This walks every row's endpoints instead."""
    blob = fdt.FOLD_TABLE_BLOB
    probes = []
    for i in range(fdt.FOLD_RANGE_COUNT):
        base = i * 12
        lo = int.from_bytes(blob[base:base + 4], "little")
        hi = int.from_bytes(blob[base + 4:base + 8], "little")
        probes.extend({lo, hi})
    src = "".join(chr(cp) for cp in sorted(set(probes))
                  if not 0xD800 <= cp < 0xE000)
    native = T.fold_marks(src)
    real = _native.has_native_text_fold_marks
    _native.has_native_text_fold_marks = lambda: False
    try:
        pure = T.fold_marks(src)
    finally:
        _native.has_native_text_fold_marks = real
    assert native == pure
    # Most ranges are a single codepoint (lo == hi), so the endpoint set is
    # smaller than 2N — but it must cover every range at least once, or this
    # would not be the exhaustive walk it claims to be.
    assert len(set(probes)) >= fdt.FOLD_RANGE_COUNT


# ── composition, not a mode ───────────────────────────────────────────────
def test_composes_with_glyph_stream_rather_than_being_a_flag_on_it():
    """``glyph_stream`` documents and tests a LOSSLESSNESS invariant, and that
    invariant is why the cluster is trustworthy as a primitive. Folding is
    lossy, so a fold mode would break the contract for one flag value — the two
    stay separate and compose."""
    s = "naïve क्षि"
    assert T.glyph_stream(T.fold_marks(s)) == ["n", "a", "i", "v", "e", " ",
                                               "क", "ष"]
    # glyph_stream remains lossless on its own input
    assert "".join(T.glyph_stream(s)) == unicodedata.normalize("NFC", s)
    # and the shapes genuinely differ, so a flag could not have served both
    assert isinstance(T.fold_marks(s), str)
    assert isinstance(T.glyph_stream(s), list)


def test_glyph_stream_has_no_fold_parameter():
    """If someone later adds one, this is the reminder of why it was declined."""
    import inspect
    params = inspect.signature(T.glyph_stream).parameters
    assert "fold" not in params and "fold_marks" not in params


# ── registration ──────────────────────────────────────────────────────────
def test_rosetta_bucket_is_c_dispatched():
    """The ledger claim must be the truth, not an aspiration."""
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "rosetta_classification.ndjson")
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                rows[r["exposed_as"]] = r["bucket"]
    assert rows.get("srmech.amsc.text.fold_marks") == "c_dispatched"


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib loaded")
def test_the_c_peer_is_actually_REACHABLE_not_merely_exported():
    """An exported symbol nobody can reach is not a C peer.

    Both halves are asserted: the symbol is bound on the loaded library, AND
    the capability predicate the op's dispatch actually consults returns True.
    A symbol present but unbound would pass the first and fail the second.
    """
    assert hasattr(_native.LIB, "srmech_text_fold_marks"), \
        "srmech_text_fold_marks is not bound on the loaded library"
    assert hasattr(_native.LIB, "srmech_text_default_fold_table"), \
        "a bare-C host could not obtain the default table"
    assert _native.has_native_text_fold_marks(), \
        "the symbol is exported but the op's dispatch predicate declines it"


def test_registered_in_the_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    entry = next((t for t in get_tool_schema().tools
                  if t.name == "srmech.amsc.text.fold_marks"), None)
    assert entry is not None, "fold_marks is not registered"
    assert entry.category == "text"
    assert [p.name for p in entry.parameters] == ["text"]
    assert "virama" in entry.summary.lower(), \
        "the summary should carry the naming argument, not just the behaviour"
