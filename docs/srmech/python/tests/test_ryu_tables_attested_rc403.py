"""rc403 (`#T1071`) — the vendored Ryu power-of-five tables are RE-DERIVED here.

``c/src/srmech_ryu_tables.h`` carries 618 rows of 128-bit constants that the
shortest-round-trip converter multiplies against. They are numbers, they are
load-bearing, and a single wrong limb would corrupt a narrow band of doubles
that the sweep might or might not sample — so per the computational-provenance
discipline they ship with the code that produced them
(``c/tools/gen_ryu_tables.py``) and this test re-runs that derivation from the
mathematical definitions and compares BYTE-FOR-BYTE against the committed file.

The definitions, with ``B = 125`` significant bits:

    pow5bits(e)               = bit_length(5**e)
    RYU_POW5_INV_SPLIT[q]     = floor(2**(B - 1 + pow5bits(q)) / 5**q) + 1
    RYU_POW5_SPLIT[i]         = floor(5**i * 2**(B - pow5bits(i)))

Pure Python integers, no numpy, no native library — so this runs on a pure /
Pyodide checkout too, and it is the one gate here that needs no C at all.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SRMECH_ROOT = _HERE.parent.parent                      # docs/srmech
_GENERATOR = _SRMECH_ROOT / "c" / "tools" / "gen_ryu_tables.py"
_HEADER = _SRMECH_ROOT / "c" / "src" / "srmech_ryu_tables.h"

pytestmark = pytest.mark.skipif(
    not _GENERATOR.exists() or not _HEADER.exists(),
    reason=(
        "C tree not present (pure-Python checkout); this test attests the "
        "vendored Ryu tables and is only meaningful with c/ checked out"
    ),
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("gen_ryu_tables", _GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_table(text: str, name: str) -> list[int]:
    """Pull ``{ lo, hi }`` rows out of the committed header as 128-bit ints.

    Anchored on the DECLARATION, not on the bare name: the header's prose
    preamble states both table definitions by name, and a bare ``name + "["``
    search matches the comment first and then reads to the wrong ``};``.
    """
    start = text.index("static const uint64_t %s[" % name)
    body = text[start:]
    body = body[:body.index("};")]
    rows = re.findall(r"\{\s*(\d+)u,\s*(\d+)u\s*\}", body)
    return [int(lo) + (int(hi) << 64) for lo, hi in rows]


def _header_text() -> str:
    """The committed header verbatim, newlines untranslated.

    ``Path.read_text`` grew a ``newline`` parameter only in 3.13, and srmech
    supports 3.10, so this goes through ``open`` explicitly.
    """
    with open(_HEADER, encoding="utf-8", newline="") as handle:
        return handle.read()


def test_integer_log_approximations_are_exact_over_the_used_range() -> None:
    """The three magic-multiply logs the C uses are EXACT, not approximate.

    ``ryu_pow5bits`` / ``ryu_log10_pow2`` / ``ryu_log10_pow5`` in
    ``srmech_ryu.c`` are the same expressions; if any of them were off by one
    anywhere in the reachable range the table index would be wrong and a whole
    decade of doubles would mis-convert.
    """
    gen = _load_generator()
    for e in range(1600):
        assert gen.pow5bits(e) == (5 ** e).bit_length(), e
        assert gen.log10_pow2(e) == len(str(2 ** e)) - 1, e
        assert gen.log10_pow5(e) == len(str(5 ** e)) - 1, e


def test_table_extents_cover_every_reachable_exponent() -> None:
    """Table sizes are sufficient AND the consumer's 128-bit shift distance
    always lands strictly inside (0, 64) — outside it the C shift would be
    undefined behaviour rather than a wrong answer."""
    gen = _load_generator()
    max_q, max_i, min_shift, max_shift = gen.verify_extents()
    assert max_q == 290, max_q
    assert max_i == 325, max_i
    assert 0 < min_shift <= max_shift < 64, (min_shift, max_shift)
    assert (min_shift, max_shift) == (54, 61), (min_shift, max_shift)


def test_committed_tables_match_a_fresh_derivation() -> None:
    """Every one of the 618 rows, re-derived from the definition."""
    gen = _load_generator()
    text = _header_text()

    inv = _parse_table(text, "RYU_POW5_INV_SPLIT")
    fwd = _parse_table(text, "RYU_POW5_SPLIT")
    assert len(inv) == gen.POW5_INV_TABLE_SIZE == 292, len(inv)
    assert len(fwd) == gen.POW5_TABLE_SIZE == 326, len(fwd)

    for q, have in enumerate(inv):
        assert have == gen.pow5_inv_split(q), f"RYU_POW5_INV_SPLIT[{q}]"
    for i, have in enumerate(fwd):
        assert have == gen.pow5_split(i), f"RYU_POW5_SPLIT[{i}]"


def test_generator_verify_mode_reports_no_drift() -> None:
    """The whole header, including its prose preamble — not just the rows.

    Compared with newlines NORMALISED. The generator writes LF, but editors and
    Windows checkouts in this tree do rewrite whole files to CRLF (it has
    already happened to ``srmech_unicode_fold_tables.h``), and a line-ending
    flip is not table drift. The DATA is checked exactly, limb by limb, in
    ``test_committed_tables_match_a_fresh_derivation`` — which is newline-blind
    by construction because it parses integers rather than comparing text. This
    test adds the prose; letting it red on CRLF would be a false alarm that
    teaches people to ignore it.
    """
    gen = _load_generator()
    fresh = gen.render().replace("\r\n", "\n")
    have = _header_text().replace("\r\n", "\n")
    assert fresh == have, (
        "srmech_ryu_tables.h has drifted from c/tools/gen_ryu_tables.py; "
        "re-run `python3 c/tools/gen_ryu_tables.py`"
    )


def test_first_rows_match_upstream_ryu() -> None:
    """Anchor the derivation to the published Ryu table (Ulf Adams, PLDI 2018)
    so an internally-consistent but WRONG definition cannot pass the two tests
    above. These four literals are from upstream's ``d2s_full_table.h``."""
    text = _header_text()
    inv = _parse_table(text, "RYU_POW5_INV_SPLIT")
    fwd = _parse_table(text, "RYU_POW5_SPLIT")
    assert inv[0] == (2305843009213693952 << 64) | 1
    assert inv[1] == (1844674407370955161 << 64) | 11068046444225730970
    assert fwd[0] == (1152921504606846976 << 64) | 0
    assert fwd[1] == (1441151880758558720 << 64) | 0
