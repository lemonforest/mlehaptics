"""rc287 — the attestation + drift gate for the VENDORED UAX #29 table.

srmech vendors external data here, so the MPM discipline applies in full: a
datum without attestation is not real, and one that cannot be re-verified is
broken. This module is the "cannot be re-verified" half.

WHY THE HOST'S ``unicodedata`` IS NOT THE DRIFT ORACLE
------------------------------------------------------
The design note proposed guarding drift with "a committed test that re-derives
the vendored table's *derivable* subset from the running ``unicodedata`` and
fails on divergence". **That test would be wrong, and it was measured to be
wrong on this project's own build host.**

Against a host at ``unicodedata.unidata_version == 13.0.0`` with the table
vendored at UCD 16.0.0, the derivable subset (GBP Extend / SpacingMark /
Control, recoverable from ``category()``) reports **4,140 mismatches out of
6,469 rows** — of which **3,982 (96%) are simply codepoints unassigned in the
host's older Unicode**, and only 158 are genuine reclassifications. So such a
test goes red whenever the host's Unicode predates the vendored UCD, which is
the ordinary case, not the exception. A guard that is red for a legitimate
reason is a guard people learn to ignore.

The host tracking a different Unicode version is not drift at all — it is the
*point*. Because the table no longer derives from the host, two hosts at
different Python versions now segment text **identically**, which the previous
derive-from-host tokenizer could not promise.

WHAT ACTUALLY GUARDS DRIFT, THEN
--------------------------------
Three layers, none of which depends on the host's Unicode version:

1. **Artefact integrity** (here) — the packed table's sha256 is committed, so a
   hand edit that the generator did not bless fails immediately. This mirrors
   the ``srmech_sha256_constants.h`` rule.
2. **Cross-projection identity** (here) — the C header and the Python module
   are emitted from one generator and must hold the same bytes.
3. **Functional conformance** (``test_glyph_stream_conformance_rc287.py``) —
   1093/1093 against the official suite. A wrongly regenerated table breaks
   this even if its digest is self-consistent.

Upstream drift — Unicode publishing a revision — is caught by
``c/tools/gen_unicode_gb_tables.py --verify``, which re-fetches the official
files and diffs a fresh derivation against what is vendored. That needs
network, so it is a script rather than a unit test; the annual re-vendoring
cost is real and is meant to be *visible*.
"""
from __future__ import annotations

import hashlib
import os
import re

import pytest

from srmech.amsc import _unicode_gb_tables as gbt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # docs/srmech
C_HEADER = os.path.join(ROOT, "c", "src", "srmech_unicode_gb_tables.h")

#: The Unicode version the vendored table is pinned to. Bumping this is a
#: deliberate re-vendoring act: regenerate, re-run conformance, update the
#: CHANGELOG. It is not a value to nudge to make a test pass.
EXPECTED_UCD_VERSION = "16.0.0"

#: sha256 of the packed table blob (little-endian lo:u32 || hi:u32 || prop:u8
#: per range, ascending). Emitted by c/tools/gen_unicode_gb_tables.py.
EXPECTED_TABLE_SHA256 = (
    "a41b5376a7b7c50fe2cf3140538a5a9d0bebbd14cc1f06b771c63dc27fc639d7")


def _c_arrays():
    """Parse the three static arrays out of the generated C header."""
    with open(C_HEADER, encoding="utf-8") as fh:
        src = fh.read()
    out = {}
    for name in ("SRMECH_GB_LO", "SRMECH_GB_HI", "SRMECH_GB_PROP"):
        m = re.search(name + r"\[SRMECH_GB_RANGE_COUNT\]\s*=\s*\{(.*?)\};",
                      src, re.S)
        assert m, f"{name} not found in {C_HEADER}"
        out[name] = [int(v, 16) for v in
                     re.findall(r"0x([0-9A-Fa-f]+)u", m.group(1))]
    return src, out


def test_declared_unicode_version_is_pinned():
    assert gbt.UCD_VERSION == EXPECTED_UCD_VERSION


def test_unicode_version_agrees_across_projections():
    src, _ = _c_arrays()
    m = re.search(r'#define SRMECH_UCD_VERSION "([^"]+)"', src)
    assert m, "SRMECH_UCD_VERSION not declared in the C header"
    assert m.group(1) == gbt.UCD_VERSION, (
        f"the compiled projection declares UCD {m.group(1)} but the scripting "
        f"projection declares UCD {gbt.UCD_VERSION} — one was regenerated "
        "without the other"
    )


def test_table_matches_its_attested_digest():
    """A hand edit the generator did not bless is a defect by construction."""
    digest = hashlib.sha256(gbt.GB_TABLE_BLOB).hexdigest()
    assert digest == EXPECTED_TABLE_SHA256, (
        "the vendored grapheme-break table no longer matches its attested "
        "sha256. If this was a deliberate re-vendoring, regenerate with "
        "c/tools/gen_unicode_gb_tables.py --emit, re-run the conformance "
        "suite, and update EXPECTED_TABLE_SHA256 here and in the CHANGELOG."
    )


def test_module_self_declared_digest_agrees():
    assert gbt.GB_TABLE_SHA256 == EXPECTED_TABLE_SHA256


def test_blob_shape_is_consistent():
    assert len(gbt.GB_TABLE_BLOB) == gbt.GB_RANGE_COUNT * 9


def test_projections_hold_byte_identical_tables():
    """The C header and the Python module are one artefact in two forms.

    They are emitted together by one generator, so any divergence means one was
    regenerated without the other — exactly the failure that would make the two
    coherency projections segment text differently.
    """
    _, arr = _c_arrays()
    n = gbt.GB_RANGE_COUNT
    assert len(arr["SRMECH_GB_LO"]) == n
    assert len(arr["SRMECH_GB_HI"]) == n
    assert len(arr["SRMECH_GB_PROP"]) == n
    blob = gbt.GB_TABLE_BLOB
    for i in range(n):
        base = i * 9
        assert int.from_bytes(blob[base:base + 4], "little") == \
            arr["SRMECH_GB_LO"][i], f"lo[{i}] differs between projections"
        assert int.from_bytes(blob[base + 4:base + 8], "little") == \
            arr["SRMECH_GB_HI"][i], f"hi[{i}] differs between projections"
        assert blob[base + 8] == arr["SRMECH_GB_PROP"][i], \
            f"prop[{i}] differs between projections"


def test_ranges_are_sorted_and_non_overlapping():
    """The binary search in both projections depends on this invariant."""
    blob = gbt.GB_TABLE_BLOB
    prev_hi = -1
    for i in range(gbt.GB_RANGE_COUNT):
        base = i * 9
        lo = int.from_bytes(blob[base:base + 4], "little")
        hi = int.from_bytes(blob[base + 4:base + 8], "little")
        assert lo <= hi, f"range {i} is inverted"
        assert lo > prev_hi, f"range {i} overlaps or is out of order"
        assert hi < 0x110000, f"range {i} exceeds the Unicode codepoint space"
        prev_hi = hi


def test_hangul_precomposed_block_is_absent_from_the_table():
    """Hangul LV/LVT are recovered arithmetically, so they must NOT be rows.

    This is the 7,254-byte saving (798 ranges of pure alternation), and it is
    exact. If a re-vendoring ever reintroduces those rows the table silently
    grows by more than it needs to.
    """
    blob = gbt.GB_TABLE_BLOB
    for i in range(gbt.GB_RANGE_COUNT):
        base = i * 9
        lo = int.from_bytes(blob[base:base + 4], "little")
        hi = int.from_bytes(blob[base + 4:base + 8], "little")
        assert not (lo < gbt.HANGUL_SBASE + gbt.HANGUL_SCOUNT
                    and hi >= gbt.HANGUL_SBASE), (
            f"range {i} (U+{lo:04X}..U+{hi:04X}) overlaps the precomposed "
            "Hangul block, which is derived by the UAX #29 §3 algebra"
        )


def test_hangul_jamo_ARE_present_as_rows():
    """The counterpart trap, and the one that actually bit.

    LBase/VBase/TBase are *composition* anchors, not the GBP jamo ranges, and
    they do not coincide: U+1160 HANGUL JUNGSEONG FILLER is GBP=V yet sits
    below VBase=U+1161. Deriving jamo from those constants mis-tags the fillers
    and drops Jamo Extended-A/B entirely — it cost 4 conformance cases when
    tried. Jamo is ~8 ranges, so the saving would have been negligible anyway.
    """
    from srmech.amsc import text as T
    V = gbt.GBP_TAGS.index("V")
    assert (T._gb_prop(0x1160) & gbt.PROP_GBP_MASK) == V
    L = gbt.GBP_TAGS.index("L")
    assert (T._gb_prop(0xA960) & gbt.PROP_GBP_MASK) == L      # Jamo Ext-A
    # And the pair that failed: GB6 must join L x V with no break.
    assert T.glyph_stream("ᄀᅠ") == ["ᄀᅠ"]


def test_hangul_syllable_algebra_is_exact():
    """Spot-check the derived LV/LVT alternation at the block edges."""
    from srmech.amsc import text as T
    LV = gbt.GBP_TAGS.index("LV")
    LVT = gbt.GBP_TAGS.index("LVT")
    assert (T._gb_prop(0xAC00) & gbt.PROP_GBP_MASK) == LV     # 가, T-index 0
    assert (T._gb_prop(0xAC01) & gbt.PROP_GBP_MASK) == LVT    # 각, T-index 1
    assert (T._gb_prop(0xD7A3) & gbt.PROP_GBP_MASK) == LVT    # last syllable


def test_non_derivable_properties_are_actually_present():
    """The whole justification for vendoring: these cannot come from the host.

    ``unicodedata`` exposes no Extended_Pictographic and no InCB at any
    fidelity, so if they were ever dropped from the table the segmenter would
    silently lose GB11 and GB9c — degrading emoji and Indic while still
    passing anything that only checks Latin.
    """
    blob = gbt.GB_TABLE_BLOB
    ext = incb = 0
    for i in range(gbt.GB_RANGE_COUNT):
        prop = blob[i * 9 + 8]
        if prop & gbt.PROP_EXTPICT_BIT:
            ext += 1
        if (prop & gbt.PROP_INCB_MASK) >> gbt.PROP_INCB_SHIFT:
            incb += 1
    assert ext > 0, "Extended_Pictographic (GB11) is missing from the table"
    assert incb > 0, "InCB (GB9c) is missing from the table"


def test_generator_is_shipped_and_offers_reverification():
    """The re-derivation path must exist in-tree, not just in a commit message."""
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_gb_tables.py")
    assert os.path.isfile(gen), "the table generator is not shipped"
    with open(gen, encoding="utf-8") as fh:
        src = fh.read()
    assert "--verify" in src and "--emit" in src
    for _, expected in re.findall(r'"(https://www\.unicode\.org[^"]+)",\s*\n\s*"([0-9a-f]{64})"', src):
        assert len(expected) == 64
    assert EXPECTED_UCD_VERSION in src
