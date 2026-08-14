"""rc293 — the attestation + drift gate for the VENDORED combining-mark table.

srmech vendors external data here, so the MPM discipline applies in full: a
datum without attestation is not real, and one that cannot be re-verified is
broken. This module is the "cannot be re-verified" half, and it is the rc287
gate (``test_unicode_gb_tables_attested.py``) applied to the second table.

WHY THE HOST'S ``unicodedata`` IS NOT THE DRIFT ORACLE — AND WHY THAT IS
SHARPER HERE THAN IT WAS FOR rc287
------------------------------------------------------------------------
For the UAX #29 table the argument was easy: ``unicodedata`` does not expose
Extended_Pictographic or InCB at all, so there was nothing to compare against.
Here it *does* expose category and decomposition, so a "re-derive from the host
and diff" test could be written — and it would be wrong for the same reason,
one step less obviously.

This project's own build host runs ``unicodedata.unidata_version == 13.0.0``
while the table is vendored at UCD 16.0.0. Every codepoint assigned in 14/15/16
and unknown to the host would read as a mismatch, and a guard that is red for a
legitimate reason is a guard people learn to ignore.

The deeper point is architectural, not numeric. srmech is MULTI-implementation
(ADR-0009): the scripting and compiled projections are co-equal. The compiled
projection has no ``unicodedata`` at ALL (ADR-0003 — a bare-C host), so if the
scripting projection derived this from the host while the compiled one read a
vendored table, the two would fold text differently on any host whose Unicode
is not exactly 16.0.0. Deriving in Python would not be a shortcut; it would be
the drift.

So both projections read the same vendored bytes, and the favourable
consequence is the same one rc287 named: two hosts at different Python /
Unicode versions now fold text IDENTICALLY.

WHAT ACTUALLY GUARDS DRIFT, THEN
--------------------------------
1. **Artefact integrity** (here) — the packed table's sha256 is committed, so a
   hand edit the generator did not bless fails immediately.
2. **Cross-projection identity** (here) — the C header and the Python module
   are emitted from one generator and must hold the same bytes.
3. **Structural invariants** (here) — sortedness, closure and no-growth are the
   three properties the runtime's correctness actually rests on, so they are
   asserted against the shipped bytes rather than trusted from the generator.
4. **Functional behaviour** (``test_fold_marks_rc293.py``) — a wrongly
   regenerated table breaks the op even if its digest is self-consistent.

Upstream drift — Unicode publishing a revision — is caught by
``c/tools/gen_unicode_fold_tables.py --verify``, which re-fetches the official
file and diffs a fresh derivation against what is vendored. That needs network,
so it is a script rather than a unit test.
"""
from __future__ import annotations

import hashlib
import os
import re

from srmech.math import _unicode_fold_tables as fdt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # docs/srmech
C_HEADER = os.path.join(ROOT, "c", "src", "srmech_unicode_fold_tables.h")

#: The Unicode version the vendored table is pinned to. Bumping this is a
#: deliberate re-vendoring act: regenerate, re-run the fold tests, update the
#: CHANGELOG. It is not a value to nudge to make a test pass.
EXPECTED_UCD_VERSION = "16.0.0"

#: sha256 of the packed table blob (little-endian lo:u32 || hi:u32 || rep:u32
#: per range, ascending). Emitted by c/tools/gen_unicode_fold_tables.py.
EXPECTED_TABLE_SHA256 = (
    "437ad84163d1797b8d565628858c9c4fafde92de37edebc340db7eb145fbca12")

#: Row count at rc293. Pinned so a silently-emptied or doubled table is loud.
EXPECTED_RANGE_COUNT = 1090

ROW_BYTES = 12


def _c_arrays():
    """Parse the three static arrays out of the generated C header."""
    with open(C_HEADER, encoding="utf-8") as fh:
        src = fh.read()
    out = {}
    for name in ("SRMECH_FOLD_LO", "SRMECH_FOLD_HI", "SRMECH_FOLD_REP"):
        m = re.search(name + r"\[SRMECH_FOLD_RANGE_COUNT\]\s*=\s*\{(.*?)\};",
                      src, re.S)
        assert m, f"{name} not found in {C_HEADER}"
        out[name] = [int(v, 16) for v in
                     re.findall(r"0x([0-9A-Fa-f]+)u", m.group(1))]
    return src, out


def _rows():
    """The vendored table as ``[(lo, hi, rep), ...]``."""
    blob = fdt.FOLD_TABLE_BLOB
    return [
        (int.from_bytes(blob[i * ROW_BYTES:i * ROW_BYTES + 4], "little"),
         int.from_bytes(blob[i * ROW_BYTES + 4:i * ROW_BYTES + 8], "little"),
         int.from_bytes(blob[i * ROW_BYTES + 8:i * ROW_BYTES + 12], "little"))
        for i in range(fdt.FOLD_RANGE_COUNT)
    ]


def test_declared_unicode_version_is_pinned():
    assert fdt.UCD_VERSION == EXPECTED_UCD_VERSION


def test_unicode_version_agrees_across_projections():
    src, _ = _c_arrays()
    m = re.search(r'#define SRMECH_FOLD_UCD_VERSION "([^"]+)"', src)
    assert m, "SRMECH_FOLD_UCD_VERSION not declared in the C header"
    assert m.group(1) == fdt.UCD_VERSION, (
        f"the compiled projection declares UCD {m.group(1)} but the scripting "
        f"projection declares UCD {fdt.UCD_VERSION} — one was regenerated "
        "without the other"
    )


def test_table_matches_its_attested_digest():
    """A hand edit the generator did not bless is a defect by construction."""
    digest = hashlib.sha256(fdt.FOLD_TABLE_BLOB).hexdigest()
    assert digest == EXPECTED_TABLE_SHA256, (
        "the vendored fold table no longer matches its attested sha256. If "
        "this was a deliberate re-vendoring, regenerate with "
        "c/tools/gen_unicode_fold_tables.py --emit, re-run the fold tests, "
        "and update EXPECTED_TABLE_SHA256 here and in the CHANGELOG."
    )


def test_module_self_declared_digest_agrees():
    assert fdt.FOLD_TABLE_SHA256 == EXPECTED_TABLE_SHA256


def test_blob_shape_is_consistent():
    assert fdt.FOLD_RANGE_COUNT == EXPECTED_RANGE_COUNT
    assert len(fdt.FOLD_TABLE_BLOB) == fdt.FOLD_RANGE_COUNT * ROW_BYTES


def test_projections_hold_byte_identical_tables():
    """The C header and the Python module are one artefact in two forms.

    Emitted together by one generator, so any divergence means one was
    regenerated without the other — exactly the failure that would make the
    two coherency projections fold text differently.
    """
    _, arr = _c_arrays()
    n = fdt.FOLD_RANGE_COUNT
    assert len(arr["SRMECH_FOLD_LO"]) == n
    assert len(arr["SRMECH_FOLD_HI"]) == n
    assert len(arr["SRMECH_FOLD_REP"]) == n
    for i, (lo, hi, rep) in enumerate(_rows()):
        assert lo == arr["SRMECH_FOLD_LO"][i], f"lo[{i}] differs"
        assert hi == arr["SRMECH_FOLD_HI"][i], f"hi[{i}] differs"
        assert rep == arr["SRMECH_FOLD_REP"][i], f"rep[{i}] differs"


def test_ranges_are_sorted_and_non_overlapping():
    """The binary search in both projections depends on this invariant."""
    rows = _rows()
    prev_hi = -1
    for lo, hi, _ in rows:
        assert lo <= hi, f"inverted range U+{lo:04X}..U+{hi:04X}"
        assert lo > prev_hi, (
            f"range starting U+{lo:04X} overlaps or precedes the previous "
            f"range ending U+{prev_hi:04X} — the binary search would be unsound")
        prev_hi = hi


def test_every_codepoint_is_in_the_unicode_domain():
    for lo, hi, rep in _rows():
        assert hi < 0x110000, f"range end U+{hi:04X} is outside Unicode"
        assert rep < 0x110000, f"replacement U+{rep:04X} is outside Unicode"


def test_table_is_CLOSED_so_one_pass_suffices():
    """No replacement may itself be a table entry.

    This is the property that makes the single-pass loop in BOTH projections
    complete rather than merely usually-right: if a replacement were itself
    foldable, ``fold_marks`` would return text that still contained foldable
    content and the op would not be idempotent.
    """
    rows = _rows()

    def lookup(cp):
        for lo, hi, rep in rows:
            if lo <= cp <= hi:
                return rep
        return None

    offenders = [(hex(lo), hex(rep)) for lo, hi, rep in rows
                 if rep != fdt.FOLD_DROP and lookup(rep) is not None]
    assert not offenders, (
        "the vendored table is NOT closed — these replacements are themselves "
        f"table entries, so one pass would be incomplete: {offenders[:8]}")


def test_folding_never_grows_the_utf8_length():
    """The C peer documents ``out_cap >= text_len`` as always sufficient.

    A caller sizing its arena to ``len(text.encode())`` — which the Python
    wrapper does — would overflow on valid input if this ever stopped holding.
    """
    def utf8_len(cp):
        return 1 if cp < 0x80 else 2 if cp < 0x800 else 3 if cp < 0x10000 else 4

    grew = [(hex(lo), hex(rep)) for lo, hi, rep in _rows()
            if rep != fdt.FOLD_DROP and utf8_len(rep) > utf8_len(lo)]
    assert not grew, (
        f"these rows encode WIDER than their source, breaking the "
        f"out_cap >= text_len contract: {grew[:8]}")


def test_drop_rows_and_map_rows_are_both_present():
    """A table that lost either kind would still pass a shape check."""
    rows = _rows()
    drop = [r for r in rows if r[2] == fdt.FOLD_DROP]
    mapped = [r for r in rows if r[2] != fdt.FOLD_DROP]
    assert len(drop) == 321, f"expected 321 drop ranges, got {len(drop)}"
    assert len(mapped) == 769, f"expected 769 map ranges, got {len(mapped)}"


def test_mark_categories_are_the_declared_scope():
    """The op's whole contract is 'Mn/Mc/Me and nothing else'."""
    assert tuple(fdt.MARK_CATEGORIES) == ("Mc", "Me", "Mn")


def test_generator_is_shipped_and_offers_reverification():
    """The re-derivation path must exist in-tree, not just in a commit message."""
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_fold_tables.py")
    assert os.path.isfile(gen), "the table generator is not shipped"
    with open(gen, encoding="utf-8") as fh:
        src = fh.read()
    assert "--verify" in src and "--emit" in src
    # The source URL is BUILT from UCD_BASE rather than written out literally,
    # so match the base + the attested per-file digest rather than a whole URL.
    assert re.search(r'UCD_BASE\s*=\s*f?"https://www\.unicode\.org/Public/', src), \
        "the generator declares no unicode.org upstream base"
    hashes = re.findall(r'"([0-9a-f]{64})"', src)
    assert hashes, "the generator declares no attested upstream sha256"
    assert "UnicodeData.txt" in src, "the vendored source file is not named"
    assert EXPECTED_UCD_VERSION in src


def test_generator_pins_the_upstream_file_it_was_built_from():
    """The attested digest in the generator must be the one the shipped table's
    own attestation block records — otherwise `--verify` would be checking a
    different byte stream than the one documented."""
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_fold_tables.py")
    with open(gen, encoding="utf-8") as fh:
        gen_src = fh.read()
    upstream = re.findall(r'"([0-9a-f]{64})"', gen_src)
    assert len(upstream) == 1, \
        f"expected exactly one attested upstream digest, found {len(upstream)}"
    assert upstream[0] in (fdt.__doc__ or ""), (
        "the generator's attested UnicodeData.txt sha256 does not appear in "
        "the vendored module's attestation block — they have drifted apart")


def test_generator_asserts_the_invariants_rather_than_assuming_them():
    """The three properties above are cheap to check and expensive to lose.

    They are asserted at GENERATION time as well, so a re-vendoring that broke
    one fails at the point of re-vendoring instead of shipping a subtly wrong
    table that only this suite would catch.
    """
    gen = os.path.join(ROOT, "c", "tools", "gen_unicode_fold_tables.py")
    with open(gen, encoding="utf-8") as fh:
        src = fh.read()
    assert "is not closed" in src, "generator does not assert CLOSURE"
    assert "NO-GROWTH" in src, "generator does not assert the no-growth bound"
    assert "expected " in src and "exactly 1" in src, \
        "generator does not assert the one-starter invariant"
