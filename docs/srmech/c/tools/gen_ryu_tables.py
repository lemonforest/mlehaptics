#!/usr/bin/env python3
"""Generate — and RE-VERIFY — the vendored Ryu power-of-five tables (rc403).

Emits ``c/src/srmech_ryu_tables.h``, the two 128-bit lookup tables the
integer-only shortest-round-trip ``double`` -> decimal converter in
``c/src/srmech_ryu.c`` reads.

WHY THE TABLE IS DERIVED HERE AND NOT AT RUNTIME
------------------------------------------------
The entries are 128-bit rationals — ``2**k / 5**q`` and ``5**i * 2**s`` — that
a C host cannot compute without arbitrary-precision arithmetic it does not
have at start-up. Deriving them once, in Python's exact integers, and
vendoring the result is the same move ``gen_unicode_fold_tables.py`` makes for
the combining-mark table and ``srmech_sha256_constants.h`` makes for the
SHA-256 round constants: a static array is DATA, not a dependency (ADR-0005),
and ADR-0003's bare-C host has no other way to obtain it.

Per the computational-provenance discipline, the numbers ship WITH the code
that produced them. ``tests/test_ryu_tables_attested_rc403.py`` re-derives both
tables from the definitions below and compares them to the committed header, so
a hand-edited entry is caught rather than trusted.

THE DEFINITIONS (this is the whole specification)
-------------------------------------------------
Ryu (Ulf Adams, *Ryu: fast float-to-string conversion*, PLDI 2018) converts a
binary significand to a decimal one by ONE multiply against a pre-scaled power
of five, then a shift. Writing ``B = 125`` for the table bit-count:

    pow5bits(e)               = bit_length(5**e)          == ceil(log2(5**e))
    RYU_POW5_INV_SPLIT[q]     = floor(2**(B - 1 + pow5bits(q)) / 5**q) + 1
    RYU_POW5_SPLIT[i]         = floor(5**i * 2**(B - pow5bits(i)))

The ``+ 1`` on the inverse table makes it an OVER-estimate, which is what lets
the consumer truncate (a floor shift) and still bound the error on the low
side; the forward table is a plain truncation. Both are stored as
``{ low 64 bits, high 64 bits }`` so the C reads them as two ``uint64_t``
with no 128-bit literal (MSVC has no ``unsigned __int128``).

Table extents are exactly what the reachable IEEE-754 binary64 exponent range
demands: ``q`` reaches 290 and ``i`` reaches 325 (see ``verify_extents``), and
the sizes 292 / 326 match upstream Ryu byte-for-byte so the two are diffable.

Usage
-----
    python3 c/tools/gen_ryu_tables.py            # rewrite the header
    python3 c/tools/gen_ryu_tables.py --verify   # exit 1 if it has drifted
"""

from __future__ import annotations

import argparse
import os
import sys

#: Table bit-count. Both tables hold this many significant bits, which is the
#: precision Ryu's error analysis requires for binary64 (see the paper, §4).
POW5_BITCOUNT = 125

#: Entry counts. 291 / 326 are the reachable minima (``verify_extents``);
#: 292 / 326 are upstream Ryu's, kept so the tables diff clean against it.
POW5_INV_TABLE_SIZE = 292
POW5_TABLE_SIZE = 326

_HEADER_NAME = "srmech_ryu_tables.h"


def pow5bits(e: int) -> int:
    """``ceil(log2(5**e))`` == ``bit_length(5**e)``, via Ryu's integer
    approximation. The C reads the SAME expression, so this doubles as the
    oracle for it."""
    return ((e * 1217359) >> 19) + 1


def log10_pow2(e: int) -> int:
    """``floor(log10(2**e))`` via Ryu's integer approximation."""
    return (e * 78913) >> 18


def log10_pow5(e: int) -> int:
    """``floor(log10(5**e))`` via Ryu's integer approximation."""
    return (e * 732923) >> 20


def pow5_inv_split(q: int) -> int:
    """``floor(2**(124 + pow5bits(q)) / 5**q) + 1`` — the 128-bit over-estimate
    of ``2**k / 5**q`` used when the binary exponent is non-negative."""
    k = POW5_BITCOUNT - 1 + pow5bits(q)
    value = ((1 << k) // (5 ** q)) + 1
    assert value < (1 << 128), q
    return value


def pow5_split(i: int) -> int:
    """``floor(5**i * 2**(125 - pow5bits(i)))`` — the 128-bit truncation of
    ``5**i`` normalised to 125 significant bits."""
    shift = POW5_BITCOUNT - pow5bits(i)
    value = (5 ** i) << shift if shift >= 0 else (5 ** i) >> (-shift)
    assert value < (1 << 128), i
    return value


def verify_approximations(limit: int = 1600) -> None:
    """The three integer log approximations are EXACT over the range Ryu uses.

    They are approximations only in the sense that they are magic-multiply
    forms; over ``[0, limit)`` they agree with the exact value on every input,
    and the C relies on that. Checked here rather than asserted in prose.
    """
    for e in range(limit):
        assert pow5bits(e) == (5 ** e).bit_length(), ("pow5bits", e)
        assert log10_pow2(e) == len(str(2 ** e)) - 1, ("log10_pow2", e)
        assert log10_pow5(e) == len(str(5 ** e)) - 1, ("log10_pow5", e)


def verify_extents() -> tuple[int, int, int, int]:
    """Walk every reachable IEEE-754 binary64 exponent field and return
    ``(max_q, max_i, min_shift, max_shift)``.

    This is what proves the table sizes are sufficient AND that the consumer's
    128-bit shift distance always lands in ``(0, 64)`` — outside that range the
    C shift would be undefined behaviour.
    """
    max_q = -1
    max_i = -1
    shifts: set[int] = set()
    for exponent_field in range(2047):
        if exponent_field == 0:
            e2 = 1 - 1023 - 52 - 2
        else:
            e2 = exponent_field - 1023 - 52 - 2
        if e2 >= 0:
            q = log10_pow2(e2) - (1 if e2 > 3 else 0)
            k = POW5_BITCOUNT + pow5bits(q) - 1
            index = -e2 + q + k
            max_q = max(max_q, q)
            shifts.add(index - 64)
        else:
            q = log10_pow5(-e2) - (1 if -e2 > 1 else 0)
            index = -e2 - q
            k = pow5bits(index) - POW5_BITCOUNT
            max_i = max(max_i, index)
            shifts.add(q - k - 64)
    assert max_q < POW5_INV_TABLE_SIZE, (max_q, POW5_INV_TABLE_SIZE)
    assert max_i < POW5_TABLE_SIZE, (max_i, POW5_TABLE_SIZE)
    assert 0 < min(shifts) and max(shifts) < 64, (min(shifts), max(shifts))
    return max_q, max_i, min(shifts), max(shifts)


def _emit_table(name: str, size: int, fn) -> str:
    rows = ["static const uint64_t %s[%d][2] = {" % (name, size)]
    for k in range(size):
        value = fn(k)
        rows.append("    { %20du, %20du },"
                    % (value & 0xFFFFFFFFFFFFFFFF, value >> 64))
    rows.append("};")
    return "\n".join(rows)


def render() -> str:
    """The full header text (deterministic — no timestamps, no host state)."""
    verify_approximations()
    max_q, max_i, min_shift, max_shift = verify_extents()
    parts = [
        "/* srmech_ryu_tables.h — GENERATED, do not hand-edit.",
        " *",
        " * Produced by c/tools/gen_ryu_tables.py; re-derived and compared by",
        " * python/tests/test_ryu_tables_attested_rc403.py. The definitions:",
        " *",
        " *   pow5bits(e)           = bit_length(5**e)",
        " *   RYU_POW5_INV_SPLIT[q] = floor(2**(%d + pow5bits(q)) / 5**q) + 1"
        % (POW5_BITCOUNT - 1),
        " *   RYU_POW5_SPLIT[i]     = floor(5**i * 2**(%d - pow5bits(i)))"
        % POW5_BITCOUNT,
        " *",
        " * Each row is { low 64 bits, high 64 bits } of a %d-bit value, so no"
        % POW5_BITCOUNT,
        " * 128-bit literal is needed (MSVC has no unsigned __int128).",
        " *",
        " * Reachable extents over every IEEE-754 binary64 exponent field:",
        " *   max q = %d (< %d rows), max i = %d (< %d rows)"
        % (max_q, POW5_INV_TABLE_SIZE, max_i, POW5_TABLE_SIZE),
        " *   128-bit shift distance in [%d, %d] — always inside (0, 64), so the"
        % (min_shift, max_shift),
        " *   consumer's shift is never undefined behaviour.",
        " *",
        " * Tables are byte-identical to upstream Ryu (Ulf Adams, PLDI 2018).",
        " */",
        "",
        "#ifndef SRMECH_RYU_TABLES_H",
        "#define SRMECH_RYU_TABLES_H",
        "",
        "#include <stdint.h>",
        "",
        "#define SRMECH_RYU_POW5_BITCOUNT       %d" % POW5_BITCOUNT,
        "#define SRMECH_RYU_POW5_INV_BITCOUNT   %d" % POW5_BITCOUNT,
        "",
        _emit_table("RYU_POW5_INV_SPLIT", POW5_INV_TABLE_SIZE, pow5_inv_split),
        "",
        _emit_table("RYU_POW5_SPLIT", POW5_TABLE_SIZE, pow5_split),
        "",
        "#endif /* SRMECH_RYU_TABLES_H */",
        "",
    ]
    return "\n".join(parts)


def header_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))          # c/tools
    return os.path.join(os.path.dirname(here), "src", _HEADER_NAME)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true",
                    help="compare the committed header to a fresh derivation")
    args = ap.parse_args(argv)
    path = header_path()
    fresh = render()
    if not args.verify:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(fresh)
        print("wrote %s" % path)
        return 0
    with open(path, "r", encoding="utf-8", newline="") as fh:
        have = fh.read()
    # Newlines are NORMALISED before comparing. This repo's git config rewrites
    # LF to CRLF in the working copy on checkout, so an exact byte compare would
    # report DRIFT on every Windows checkout of an unmodified file — a false
    # alarm that teaches people to ignore this mode. Table drift is a change in
    # the NUMBERS, and tests/test_ryu_tables_attested_rc403.py checks those limb
    # by limb, newline-blind by construction (it parses integers).
    if have.replace("\r\n", "\n") != fresh.replace("\r\n", "\n"):
        print("DRIFT: %s differs from a fresh re-derivation" % path,
              file=sys.stderr)
        return 1
    print("ok: %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
