"""rc287 — the official UAX #29 conformance gate for :func:`glyph_stream`.

The acceptance bar is **1093/1093** on Unicode's own ``GraphemeBreakTest.txt``,
in BOTH coherency projections (ADR-0009), with zero disagreement between them.

Why the whole suite and not a sample: the design spike measured a best-effort
``unicodedata``-only derivation at 954/1093 (87.28%), and on real prose that
approximation is **exactly correct** for Latin, Greek, Cyrillic, Arabic,
Hebrew, CJK, Korean and Hawaiian while being **19.2% wrong for Burmese, 9.2%
Bengali and 8.0% Devanagari**. An aggregate error figure hides that completely.
A partial conformance score would hide it the same way — perfect on the scripts
that barely need clustering, broken on the ones that do. So the bar is the
whole suite, and it is exact.

The suite is also what FOUND the third data dependency: omitting InCB scores
1086/1093, and those 7 cases are the only signal that GB9c (Indic conjuncts,
added in Unicode 15.1) exists at all.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from srmech.amsc import _native
from srmech.amsc import _unicode_gb_tables as gbt
from srmech.math import text as T

DATA = os.path.join(os.path.dirname(__file__), "data")
FIXTURE = os.path.join(DATA, "GraphemeBreakTest.txt")

#: sha256 of the official UCD 16.0.0 GraphemeBreakTest.txt, as fetched from
#: https://www.unicode.org/Public/16.0.0/ucd/auxiliary/GraphemeBreakTest.txt
FIXTURE_SHA256 = "ee2b9354d270ac061b29f09662cafea06341d77e704b8cc6bd72aaeeda363cb5"

#: The bar. Not a floor to be negotiated down — see the module docstring.
EXPECTED_CASES = 1093


def _load_cases():
    """Parse ``GraphemeBreakTest.txt`` into ``[(text, [clusters])]``.

    Format: ``÷`` marks a cluster boundary, ``×`` marks a non-boundary, and
    each token between them is a hex codepoint.
    """
    cases = []
    with open(FIXTURE, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if not line:
                continue
            toks = line.split()
            if toks and toks[0] == "÷":
                toks = toks[1:]
            if toks and toks[-1] == "÷":
                toks = toks[:-1]
            expected, cur = [], ""
            for tok in toks:
                if tok == "×":
                    continue
                if tok == "÷":
                    expected.append(cur)
                    cur = ""
                else:
                    cur += chr(int(tok, 16))
            expected.append(cur)
            cases.append(("".join(expected), expected))
    return cases


@pytest.fixture(scope="module")
def cases():
    return _load_cases()


@pytest.fixture
def pure(monkeypatch):
    """Force the scripting projection (decline the native peer)."""
    monkeypatch.setattr(_native, "has_native_text_glyph_stream", lambda: False)


def test_fixture_is_the_attested_upstream_file():
    """The conformance fixture is the official file, byte for byte.

    A conformance suite that has been edited proves nothing, so the fixture
    carries the same attestation discipline as the table it validates.
    """
    with open(FIXTURE, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == FIXTURE_SHA256, (
        "GraphemeBreakTest.txt is not the attested UCD "
        f"{gbt.UCD_VERSION} file. Re-fetch it from unicode.org; do not edit "
        "the conformance fixture to make a test pass."
    )


def test_case_count_is_the_full_suite(cases):
    assert len(cases) == EXPECTED_CASES


def test_conformance_scripting_projection(cases, pure):
    """1093/1093 with the pure-Python body — the parity oracle."""
    failures = [
        (txt, exp, T.glyph_stream(txt, unicode_normalize=False))
        for txt, exp in cases
        if T.glyph_stream(txt, unicode_normalize=False) != exp
    ]
    assert not failures, _report(failures)


@pytest.mark.skipif(not _native.has_native_text_glyph_stream(),
                    reason="native srmech_text_glyph_stream not loaded")
def test_conformance_compiled_projection(cases):
    """1093/1093 with the C peer — same bar, no allowance for being 'the fast
    path'. ADR-0009: neither projection is primary."""
    failures = [
        (txt, exp, T.glyph_stream(txt, unicode_normalize=False))
        for txt, exp in cases
        if T.glyph_stream(txt, unicode_normalize=False) != exp
    ]
    assert not failures, _report(failures)


@pytest.mark.skipif(not _native.has_native_text_glyph_stream(),
                    reason="native srmech_text_glyph_stream not loaded")
def test_projections_agree_byte_identically(cases, monkeypatch):
    """The ADR-0009 §1.3 differential gate (design falsifier F6).

    F6 was the one falsifier the design spike could not test, because no
    implementation existed yet. This is it.
    """
    native = [T.glyph_stream(txt, unicode_normalize=False)
              for txt, _ in cases]
    monkeypatch.setattr(_native, "has_native_text_glyph_stream", lambda: False)
    scripted = [T.glyph_stream(txt, unicode_normalize=False)
                for txt, _ in cases]
    disagreements = [
        (txt, a, b) for (txt, _), a, b in zip(cases, native, scripted) if a != b
    ]
    assert not disagreements, (
        f"{len(disagreements)} input(s) segment differently between the "
        f"compiled and scripting projections; first: {disagreements[0]!r}"
    )


def test_gb9c_indic_conjuncts_are_one_cluster(pure):
    """GB9c (Unicode 15.1) — the rule whose absence costs exactly 7 cases.

    Pinned separately because it is recent, easy to miss, and invisible in an
    aggregate score.
    """
    # DEVANAGARI KA + VIRAMA + SSA + VOWEL SIGN I -> one conjunct cluster
    assert T.glyph_stream("क्षि") == [
        "क्षि"]


def test_gb11_emoji_zwj_sequence_is_one_cluster(pure):
    """GB11 — a 7-codepoint family sequence is ONE thing a human sees."""
    family = "\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466"
    assert T.glyph_stream(family) == [family]
    assert len(family) == 7          # 7 codepoints, 1 cluster


def test_gb12_gb13_regional_indicator_parity(pure):
    """Flags pair up two-by-two; an odd trailing RI stands alone."""
    vu = "\U0001F1FB\U0001F1FA"                     # VU
    assert T.glyph_stream(vu) == [vu]
    # Three RIs = one flag + one lone indicator (parity, not greedy pairing).
    assert T.glyph_stream(vu + "\U0001F1FB") == [vu, "\U0001F1FB"]


def test_stream_is_lossless(cases, pure):
    """Every codepoint lands in exactly one cluster, in order.

    This is design falsifier F7 (R-RBS-LM-25 §3.5): a boundary must never fall
    inside a codepoint or between a base and its combining marks, so U+FFFD can
    never be manufactured by segmentation.
    """
    for txt, _ in cases:
        assert "".join(T.glyph_stream(txt, unicode_normalize=False)) == txt


def _report(failures):
    head = failures[:5]
    lines = [f"{len(failures)}/{EXPECTED_CASES} conformance failures; first 5:"]
    for txt, exp, got in head:
        cps = " ".join(f"U+{ord(c):04X}" for c in txt)
        lines.append(f"  input {cps}\n    expected {exp!r}\n    got      {got!r}")
    return "\n".join(lines)
