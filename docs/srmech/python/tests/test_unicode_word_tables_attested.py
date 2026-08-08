"""The vendored WORD-CHARACTER table is attested, byte-identical and honest.

v0.9.0rc416 (`#T1102`). The rc287 / rc293 vendoring pattern applied to a third
table, and this file is its rc293 peer — same shape, same pins, same
projection-equality proof.

WHAT MAKES THIS TABLE NECESSARY RATHER THAN MERELY PERMITTED
============================================================
Its two predecessors are vendored because ``unicodedata`` cannot answer at all
(no Grapheme_Cluster_Break, no InCB) or because a bare-C host has no Python.
This one is vendored against a call that DOES exist and DOES answer:
``str.isalnum()``. So the argument has to be sharper, and it is measured:

* ``str.isalnum()`` reads the RUNNING interpreter's UCD. The reference
  interpreter for this tree reports ``unicodedata.unidata_version ==
  '13.0.0'`` while every vendored table here is **16.0.0**. That skew is live,
  not theoretical — :func:`test_the_host_disagrees_with_the_vendored_table`
  finds the disagreeing codepoints and asserts there is at least one, so the
  motivating fact fails loudly if it ever stops being true rather than
  quietly becoming decoration.
* a bare-C host has no ``str`` at all (ADR-0003), so the compiled projection
  could not reproduce the scripting projection's classification. Two
  projections on different data is the ADR-0009 forbidden shape.

⚠️ THE HOST IS NOT AN ORACLE HERE, and that is the same trap
``test_unicode_fold_tables_attested`` names: an auditor's instinct is to check
the vendored table against ``unicodedata``, and doing so would be checking
16.0.0 against 13.0.0 and calling the newer one wrong. The re-derivation path
is ``c/tools/gen_unicode_word_tables.py --verify``, which re-fetches the
pinned upstream file. It needs network and is deliberately NOT a unit test.
"""
from __future__ import annotations

import hashlib
import os
import re
import unicodedata

from srmech.math import _unicode_word_tables as wdt

HERE = os.path.dirname(os.path.abspath(__file__))        # docs/srmech/python/tests
ROOT = os.path.dirname(os.path.dirname(HERE))            # docs/srmech
C_HEADER = os.path.join(ROOT, "c", "src", "srmech_unicode_word_tables.h")

#: The Unicode version the vendored table is pinned to. Bumping this is a
#: deliberate re-vendoring act: regenerate, re-run the word tests, update the
#: CHANGELOG. It is not a value to nudge to make a test pass.
EXPECTED_UCD_VERSION = "16.0.0"

#: sha256 of the packed table blob (little-endian lo:u32 || hi:u32 || kind:u8
#: per range, ascending). Emitted by c/tools/gen_unicode_word_tables.py.
EXPECTED_TABLE_SHA256 = (
    "78c11e16309b5ed4a183dfba3354a1bc825b18b13f73410e318e5eafd226cbb3")

#: Row count at rc416. Pinned so a silently-emptied or doubled table is loud.
EXPECTED_RANGE_COUNT = 890

#: Codepoints the ranges cover. Pinned for the same reason, and because it is
#: the number that would collapse if the UnicodeData First>/Last> range blocks
#: (CJK, Hangul, Tangut) stopped being expanded — ~100k of the 145,440.
EXPECTED_CODEPOINT_COUNT = 145440

ROW_BYTES = 9


def _c_arrays():
    """Parse the three static arrays out of the generated C header."""
    with open(C_HEADER, encoding="utf-8") as fh:
        src = fh.read()
    out = {}
    for name in ("SRMECH_WORD_LO", "SRMECH_WORD_HI"):
        m = re.search(name + r"\[SRMECH_WORD_RANGE_COUNT\]\s*=\s*\{(.*?)\};",
                      src, re.S)
        assert m, f"{name} not found in {C_HEADER}"
        out[name] = [int(v, 16) for v in
                     re.findall(r"0x([0-9A-Fa-f]+)u", m.group(1))]
    m = re.search(r"SRMECH_WORD_KIND\[SRMECH_WORD_RANGE_COUNT\]\s*=\s*\{(.*?)\};",
                  src, re.S)
    assert m, f"SRMECH_WORD_KIND not found in {C_HEADER}"
    out["SRMECH_WORD_KIND"] = [int(v) for v in
                               re.findall(r"(\d+)u", m.group(1))]
    return src, out


def _rows():
    """The vendored table as ``[(lo, hi, kind), ...]``."""
    blob = wdt.WORD_TABLE_BLOB
    return [
        (int.from_bytes(blob[i * ROW_BYTES:i * ROW_BYTES + 4], "little"),
         int.from_bytes(blob[i * ROW_BYTES + 4:i * ROW_BYTES + 8], "little"),
         blob[i * ROW_BYTES + 8])
        for i in range(wdt.WORD_RANGE_COUNT)
    ]


def test_declared_unicode_version_is_pinned():
    assert wdt.UCD_VERSION == EXPECTED_UCD_VERSION


def test_unicode_version_agrees_across_projections():
    src, _ = _c_arrays()
    m = re.search(r'#define SRMECH_WORD_UCD_VERSION "([^"]+)"', src)
    assert m, "SRMECH_WORD_UCD_VERSION not declared in the C header"
    assert m.group(1) == wdt.UCD_VERSION, (
        f"the compiled projection declares UCD {m.group(1)} but the scripting "
        f"projection declares UCD {wdt.UCD_VERSION} — one was regenerated "
        "without the other")


def test_table_matches_its_attested_digest():
    """A hand edit the generator did not bless is a defect by construction."""
    digest = hashlib.sha256(wdt.WORD_TABLE_BLOB).hexdigest()
    assert digest == EXPECTED_TABLE_SHA256, (
        "the vendored word table no longer matches its attested sha256. If "
        "this was a deliberate re-vendoring, regenerate with "
        "c/tools/gen_unicode_word_tables.py --emit, re-run the word tests, "
        "and update EXPECTED_TABLE_SHA256 here and in the CHANGELOG.")


def test_module_self_declared_digest_agrees():
    assert wdt.WORD_TABLE_SHA256 == EXPECTED_TABLE_SHA256


def test_blob_shape_is_consistent():
    assert wdt.WORD_RANGE_COUNT == EXPECTED_RANGE_COUNT
    assert len(wdt.WORD_TABLE_BLOB) == wdt.WORD_RANGE_COUNT * ROW_BYTES
    covered = sum(hi - lo + 1 for lo, hi, _ in _rows())
    assert covered == wdt.WORD_CODEPOINT_COUNT == EXPECTED_CODEPOINT_COUNT


def test_projections_hold_byte_identical_tables():
    """The C header and the Python module are one artefact in two forms."""
    _, arr = _c_arrays()
    n = wdt.WORD_RANGE_COUNT
    for key in ("SRMECH_WORD_LO", "SRMECH_WORD_HI", "SRMECH_WORD_KIND"):
        assert len(arr[key]) == n, f"{key} holds {len(arr[key])} rows, not {n}"
    for i, (lo, hi, kind) in enumerate(_rows()):
        assert lo == arr["SRMECH_WORD_LO"][i], f"lo[{i}] differs"
        assert hi == arr["SRMECH_WORD_HI"][i], f"hi[{i}] differs"
        assert kind == arr["SRMECH_WORD_KIND"][i], f"kind[{i}] differs"


def test_ranges_are_sorted_and_non_overlapping():
    """The binary search in both projections depends on this invariant."""
    prev_hi = -1
    for lo, hi, _ in _rows():
        assert lo <= hi, f"inverted range U+{lo:04X}..U+{hi:04X}"
        assert lo > prev_hi, (
            f"range starting U+{lo:04X} overlaps or precedes the previous "
            f"range ending U+{prev_hi:04X} — the binary search would be unsound")
        prev_hi = hi


def test_every_codepoint_is_in_the_unicode_domain():
    for _lo, hi, _kind in _rows():
        assert hi < 0x110000, f"range end U+{hi:04X} is outside Unicode"


def test_every_row_carries_a_declared_kind():
    legal = {wdt.WORD_KIND_LETTER, wdt.WORD_KIND_NUMBER}
    for lo, hi, kind in _rows():
        assert kind in legal, (
            f"U+{lo:04X}..U+{hi:04X} carries kind {kind}, outside "
            f"{sorted(legal)} — a row with no kind is a row the consumer "
            "cannot act on")


def test_the_contract_holds_for_the_characters_the_index_is_about():
    """The four notation glyphs ``srmech.introspect.search`` names in its own
    source, plus the three exclusions, asserted as the CONTRACT they are.

    ``ℚ`` / ``𝕆`` / ``Σ`` are LETTERS (``Lu``), which is why the double-struck
    and Greek notation filling the registry's prose is searchable. ``→`` is a
    SYMBOL and is deliberately not, and that cost is asserted here rather than
    discovered later.
    """
    from srmech.math.text import _word_kind_cp

    for ch in "ℚ𝕆Σκπ中国क":
        assert _word_kind_cp(ord(ch)) == wdt.WORD_KIND_LETTER, f"{ch!r}"
    for ch in "0९٤":                       # ASCII, Devanagari, Arabic-Indic
        assert _word_kind_cp(ord(ch)) == wdt.WORD_KIND_NUMBER, f"{ch!r}"
    for ch in "→⊗≤+=<>|~$^":               # Symbol — deliberately OUT
        assert _word_kind_cp(ord(ch)) == 0, f"{ch!r} must be a separator"
    for ch in "_.,:;()[]{} \t\n-/":        # Pc / P* / Z* — deliberately OUT
        assert _word_kind_cp(ord(ch)) == 0, f"{ch!r} must be a separator"


def test_ascii_alphanumerics_are_all_covered():
    """The registry corpus is ~99% ASCII; a table that lost ASCII would break
    every existing query while looking like an improvement elsewhere."""
    from srmech.math.text import _word_kind_cp

    for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert _word_kind_cp(ord(ch)) == wdt.WORD_KIND_LETTER, ch
    for ch in "0123456789":
        assert _word_kind_cp(ord(ch)) == wdt.WORD_KIND_NUMBER, ch


def test_the_host_disagrees_with_the_vendored_table():
    """THE MOTIVATING FACT, asserted rather than asserted-about.

    If this ever passes vacuously — host and table agreeing everywhere — the
    whole "do not call ``str.isalnum()``" argument has become decoration and
    should be re-argued, not inherited. So the test requires a NON-EMPTY
    disagreement and reports the host's version with it.

    Scanning the whole codepoint domain is affordable and is the honest scope:
    a sampled scan could miss the skew entirely on a host one version behind.
    """
    from srmech.math.text import _word_kind_cp

    disagree = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:                 # surrogates: no str form
            continue
        table = _word_kind_cp(cp) != 0
        host = chr(cp).isalnum()
        if table != host:
            disagree.append(cp)
    assert disagree, (
        f"the host (UCD {unicodedata.unidata_version}) agrees with the "
        f"vendored table (UCD {wdt.UCD_VERSION}) on every codepoint. That is "
        "not a failure of the table — it means the versions have converged "
        "and the argument for vendoring must be re-made on the ADR-0003 "
        "bare-C-host ground alone, in the module docstring, deliberately.")
    # Marks are the systematic half: str.isalnum() excludes M*, this table
    # includes it, so the disagreement can never be zero while any mark exists.
    marks = [cp for cp in disagree
             if unicodedata.category(chr(cp)) in ("Mn", "Mc", "Me")]
    assert marks, "no mark-category disagreement found — the M* inclusion has "\
                  "silently been dropped from the table"


def test_generator_is_shipped_and_offers_reverification():
    """A vendored table nobody can re-derive is the failure the MPM discipline
    exists to prevent."""
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_word_tables.py")
    assert os.path.exists(gen), f"missing generator {gen}"
    src = open(gen, encoding="utf-8").read()
    assert "--verify" in src and "--emit" in src
    assert EXPECTED_TABLE_SHA256 not in src, (
        "the generator must DERIVE the digest, never carry it as a constant — "
        "a generator that hard-codes the answer cannot detect drift")


def test_generator_pins_the_upstream_file_it_was_built_from():
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_word_tables.py")
    src = open(gen, encoding="utf-8").read()
    assert "UnicodeData.txt" in src
    assert "ff58e5823bd095166564a006e47d111130813dcf8bf234ef79fa51a870edb48f" \
        in src, ("the generator no longer pins the upstream UnicodeData.txt "
                 "digest; an unpinned fetch cannot detect an upstream revision")


def test_generator_asserts_its_invariants_rather_than_assuming_them():
    """The generator's own guards are load-bearing and must not be softened."""
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_word_tables.py")
    src = open(gen, encoding="utf-8").read()
    for needle in ("omits ASCII alphanumerics",
                   "includes ASCII separator",
                   "codepoints came from First>/",
                   "is not classified LETTER",
                   "is not classified NUMBER"):
        assert needle in src, (
            f"the generator no longer asserts {needle!r}. Each of these is a "
            "way the table could be silently wrong while still parsing.")
