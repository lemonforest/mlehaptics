#!/usr/bin/env python3
"""Generate — and RE-VERIFY — the vendored combining-mark fold table.

One generator, two coherency projections (ADR-0009). It emits BOTH:

  * ``c/src/srmech_unicode_fold_tables.h``        — the compiled projection's
  * ``python/srmech/amsc/_unicode_fold_tables.py`` — the scripting projection's

from ONE upstream source, so the two are byte-identical by construction rather
than by discipline. ``tests/test_unicode_fold_tables_attested.py`` pins that.

This is the rc287 vendoring pattern applied to a second table; the argument for
vendoring is the same one, re-checked (ADR-0005's scope is *imports and links*
— a static array is DATA, not a dependency; the in-tree precedents are
``srmech_sha256_constants.h`` and ``srmech_unicode_gb_tables.h``). What makes
it necessary here rather than merely permitted is ADR-0003: a **bare-C host has
no Python ``unicodedata``**, so deriving the mapping at runtime is not
available to the compiled projection at any fidelity. The choice is
vendored-vs-ABSENT.

WHAT IS VENDORED, AND WHY IT IS ONE TABLE
-----------------------------------------
``fold_marks`` needs two facts per codepoint, and they merge into one row:

  * is this codepoint a combining MARK (General_Category Mn / Mc / Me)? — drop
  * does its canonical decomposition CONTAIN a mark? — replace with the base

Both are answered by a single coalesced range table with a 32-bit payload:
``rep == 0`` means *drop* (the codepoint is a mark), ``rep != 0`` means
*replace every codepoint in this range with ``rep``*. U+0000 is never a fold
target, so 0 is a safe sentinel. One binary search serves both — the same
merge-into-one-table discipline rc287 used for three UAX #29 property sets.

THE RECURSION IS RESOLVED AT GENERATION TIME
--------------------------------------------
The vendored ``rep`` is the FULL, transitively-resolved fold: U+1EBF ``ế``
decomposes to U+00EA U+0301, and U+00EA decomposes again to U+0065 U+0302, so
the row for U+1EBF stores U+0065 directly. Two consequences, both load-bearing:

  * the runtime does no recursion and needs no decomposition buffer, which is
    what lets the C peer satisfy the JPL Power-of-Ten rules (no recursion, no
    malloc) with a flat single-pass loop;
  * a single pass is provably sufficient — CLOSURE is asserted below: no
    replacement codepoint is itself a table entry.

Canonical decompositions are either singletons, or a starter followed by
combining marks, or Hangul (starters only). So a mark-containing decomposition
always leaves EXACTLY ONE non-mark codepoint. That is asserted, not assumed.

SCOPE — CATEGORY ONLY (this is the whole contract)
--------------------------------------------------
Combining marks are dropped by Unicode **category**. No case change, no locale
tailoring, no NFKD/compatibility folding, no ligature expansion. Consequences
that follow from the scope and are correct, not oversights:

  * ``ø`` U+00F8 is unchanged — a stroke is part of the letter, not a mark, and
    it has no canonical decomposition;
  * ``Ω`` U+2126 OHM SIGN is unchanged — a singleton compatibility-ish mapping
    with no mark in it is not this op's business;
  * ``한`` is unchanged in either normalization form — Hangul decomposes to
    jamo, which are starters, so no row exists and nothing is touched.

NORMALIZATION INDEPENDENCE
--------------------------
Because precomposed characters are handled by the fold rows and decomposed
sequences by the drop rows, the op drops the SAME marks whichever form it is
given, and therefore calls ``unicodedata`` NOWHERE. Verified exhaustively over
the whole codepoint domain: ``NFC(fold(NFC(s))) == NFC(fold(NFD(s)))`` with
zero violations. The one form-sensitivity is that the op PRESERVES the input's
Hangul form rather than composing or decomposing it — it is a fold, not a
normalizer, and Hangul carries no marks either way.

MODES
-----
``--emit``    regenerate both projections from a local UCD directory.
``--verify``  RE-FETCH the official file, recompute, and diff against what is
              vendored. Exits non-zero on ANY drift. This is the re-derivation
              path the MPM discipline requires: a vendored table nobody can
              re-derive is exactly the failure the discipline exists to
              prevent. Needs network; NOT a unit test — the host's own
              ``unicodedata`` cannot serve as the drift oracle, because it is
              pinned to the host interpreter's Unicode version (a CI host at
              UCD 13.0.0 disagrees with this table by construction and by
              design).

Usage
-----
    python3 gen_unicode_fold_tables.py --emit   [--ucd-dir DIR]
    python3 gen_unicode_fold_tables.py --verify [--ucd-dir DIR]

No abs(); no external libraries; deterministic byte-for-byte output.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request

# ── Attestation (MPR v1) — the SINGLE source of the vendored table ──────────
UCD_VERSION = "16.0.0"
UCD_LICENSE = "Unicode-DFS-2016"
UCD_RETRIEVED_AT = "2026-07-20T00:00:00Z"
UCD_BASE = f"https://www.unicode.org/Public/{UCD_VERSION}/ucd"

#: filename → (url, expected sha256 of the upstream file).
UCD_SOURCES = {
    "UnicodeData.txt": (
        f"{UCD_BASE}/UnicodeData.txt",
        "ff58e5823bd095166564a006e47d111130813dcf8bf234ef79fa51a870edb48f",
    ),
}

#: General_Category values that ARE combining marks. This set IS the op's
#: scope: Mn nonspacing, Mc spacing-combining, Me enclosing. A virama is Mn —
#: which is why the op is `fold_marks` and not `fold_accents`.
MARK_CATEGORIES = frozenset({"Mn", "Mc", "Me"})

#: `rep` sentinel meaning "this codepoint IS a mark — drop it". U+0000 is
#: never a canonical-decomposition base, so the sentinel cannot collide.
FOLD_DROP = 0


# ── UCD parsing ────────────────────────────────────────────────────────────
def parse_unicode_data(text):
    """UnicodeData.txt → (categories, decompositions).

    ``categories`` maps cp → General_Category; ``decompositions`` maps cp → the
    CANONICAL decomposition only (fields tagged ``<compat>``/``<font>``/… are
    compatibility mappings and are deliberately skipped — see the scope note).

    UnicodeData.txt expresses large uniform blocks as a ``First>``/``Last>``
    line pair rather than one line per codepoint. Those blocks are expanded
    for the category check only if they could contain marks; ASSERTED below
    that none do, so they contribute no rows and are skipped entirely.
    """
    categories, decompositions = {}, {}
    range_blocks, pending = [], None
    for line in text.splitlines():
        if not line:
            continue
        fields = line.split(";")
        cp = int(fields[0], 16)
        name, category, decomp = fields[1], fields[2], fields[5]
        if name.endswith(", First>"):
            pending = (cp, category)
            continue
        if name.endswith(", Last>"):
            if pending is None:
                raise SystemExit(f"UnicodeData.txt: Last> without First> at {cp:04X}")
            range_blocks.append((pending[0], cp, pending[1]))
            pending = None
            continue
        categories[cp] = category
        if decomp and not decomp.startswith("<"):
            decompositions[cp] = [int(x, 16) for x in decomp.split()]
    if pending is not None:
        raise SystemExit("UnicodeData.txt: unterminated First> block")

    # The First>/Last> blocks are CJK ideographs, Hangul syllables, Tangut,
    # private use and surrogates — none of which is a mark, and none of which
    # carries a canonical decomposition in the file. Assert rather than assume:
    # a future UCD that put a mark in a range block would silently lose it.
    mark_blocks = [b for b in range_blocks if b[2] in MARK_CATEGORIES]
    if mark_blocks:
        raise SystemExit(
            "UnicodeData.txt range block carries a MARK category: "
            f"{mark_blocks!r}\nThe generator skips range blocks on the "
            "assumption that they never do. Re-vendor deliberately.")
    return categories, decompositions


def build_entries(categories, decompositions):
    """(categories, decompositions) → {cp: rep}, rep 0 meaning DROP.

    Two kinds of row, merged into one map:

      * every combining mark          → FOLD_DROP
      * every non-mark whose full canonical decomposition contains a mark
                                      → the single surviving base codepoint
    """
    def is_mark(cp):
        return categories.get(cp) in MARK_CATEGORIES

    def full_decomposition(cp):
        """Transitive canonical decomposition. Terminates: the canonical
        decomposition relation is a DAG rooted at codepoints with no mapping
        (Unicode guarantees no cycles), so this is a finite unfolding."""
        mapping = decompositions.get(cp)
        if mapping is None:
            return [cp]
        out = []
        for component in mapping:
            out.extend(full_decomposition(component))
        return out

    entries = {}
    for cp, category in categories.items():
        if category in MARK_CATEGORIES:
            entries[cp] = FOLD_DROP

    for cp in decompositions:
        if is_mark(cp):
            continue                      # already a DROP row; marks that
            # decompose into marks (U+0344 and 61 others) need no fold row.
        decomposed = full_decomposition(cp)
        if not any(is_mark(c) for c in decomposed):
            continue                      # Hangul, and singletons with no mark
        survivors = [c for c in decomposed if not is_mark(c)]
        # Canonical decompositions are singleton | starter+marks | Hangul, so
        # a mark-containing decomposition leaves exactly one starter. Assert.
        if len(survivors) != 1:
            raise SystemExit(
                f"U+{cp:04X}: mark-containing canonical decomposition left "
                f"{len(survivors)} non-mark codepoints {survivors!r}, expected "
                "exactly 1. The one-starter invariant the flat table depends "
                "on no longer holds; re-vendor deliberately.")
        entries[cp] = survivors[0]

    # CLOSURE — the property that makes ONE runtime pass sufficient. No
    # replacement may itself be a table entry (foldable or a mark), else a
    # folded string could still contain foldable content.
    unclosed = [(cp, rep) for cp, rep in entries.items()
                if rep != FOLD_DROP and rep in entries]
    if unclosed:
        raise SystemExit(
            "fold table is not closed — these replacements are themselves "
            f"table entries: {[(hex(a), hex(b)) for a, b in unclosed[:8]]!r}\n"
            "A single-pass fold would be incomplete. Re-vendor deliberately.")

    # NO-GROWTH — the property the C peer's output-capacity contract rests on
    # ("out_cap >= text_len always suffices"). A replacement is always a base
    # letter at or below its precomposed form's UTF-8 width, so folding can
    # only shrink. If that ever stopped holding, a caller sizing its arena to
    # text_len would overflow on valid input, so this is asserted, not assumed.
    def utf8_len(cp):
        return 1 if cp < 0x80 else 2 if cp < 0x800 else 3 if cp < 0x10000 else 4

    grew = [(cp, rep) for cp, rep in entries.items()
            if rep != FOLD_DROP and utf8_len(rep) > utf8_len(cp)]
    if grew:
        raise SystemExit(
            "fold table breaks the NO-GROWTH invariant — these rows encode "
            f"WIDER than their source: {[(hex(a), hex(b)) for a, b in grew[:8]]!r}\n"
            "The C peer documents out_cap >= text_len as always sufficient. "
            "Re-vendor deliberately and revisit that contract.")
    return entries


def pack_ranges(entries):
    """{cp: rep} → sorted, coalesced, non-overlapping [(lo, hi, rep)]."""
    ranges = []
    for cp in sorted(entries):
        rep = entries[cp]
        if ranges and ranges[-1][1] == cp - 1 and ranges[-1][2] == rep:
            ranges[-1][1] = cp
        else:
            ranges.append([cp, cp, rep])
    return [tuple(r) for r in ranges]


def blob_bytes(ranges):
    """The canonical packed wire form BOTH projections embed and hash.

    Little-endian ``lo:u32 || hi:u32 || rep:u32`` per range, in ascending
    order. 12 bytes per range. This byte string IS the attested artefact: its
    sha256 is what the drift test pins.
    """
    out = bytearray()
    for lo, hi, rep in ranges:
        out += lo.to_bytes(4, "little")
        out += hi.to_bytes(4, "little")
        out += rep.to_bytes(4, "little")
    return bytes(out)


# ── emitters ───────────────────────────────────────────────────────────────
def _attestation_lines(digest, ranges, source_hashes):
    """The shared MPR v1 attestation block, as plain text lines."""
    drop_rows = sum(1 for r in ranges if r[2] == FOLD_DROP)
    map_rows = len(ranges) - drop_rows
    lines = [
        "ATTESTATION (MPR v1 — the on-disk MPM discipline applied to a VENDORED",
        "DATA TABLE, following c/src/srmech_unicode_gb_tables.h):",
        "",
        "  data           : combining-mark fold table — General_Category",
        "                   Mn/Mc/Me (DROP rows) plus the transitively",
        "                   resolved canonical-decomposition base for every",
        "                   non-mark whose decomposition contains a mark",
        "                   (MAP rows). Category only: no case folding, no",
        "                   compatibility (NFKD) folding, no locale tailoring.",
        "  data_schema_id : unicode://ucd/combining-mark-fold-table/v1",
        f"  unicode_version: {UCD_VERSION}",
        f"  license        : {UCD_LICENSE}",
        f"  retrieved_at   : {UCD_RETRIEVED_AT}",
        "  source_url     :",
    ]
    for name, (url, _) in sorted(UCD_SOURCES.items()):
        lines.append(f"                   {url}")
    lines.append("  response_sha256 (of each upstream file, as fetched):")
    for name in sorted(source_hashes):
        lines.append(f"                   {name}")
        lines.append(f"                     {source_hashes[name]}")
    lines += [
        f"  table_sha256   : {digest}",
        f"                   (sha256 of the packed blob: {len(ranges)} ranges",
        f"                    = {drop_rows} drop + {map_rows} map,",
        f"                    {len(ranges) * 12} bytes, little-endian",
        "                    lo:u32 || hi:u32 || rep:u32)",
        "  verification   : RE-DERIVABLE — c/tools/gen_unicode_fold_tables.py",
        "                   --verify re-fetches the official file, recomputes",
        "                   this table and diffs it against what is vendored.",
        "                   Closure and the one-starter invariant are asserted",
        "                   by the generator, not assumed.",
        "  cite_as        : \"The Unicode Standard, UnicodeData.txt, Unicode "
        f"{UCD_VERSION}.\"",
        "",
        "RULE: do NOT edit these values by hand. Regenerate with the generator",
        "above; a hand edit that the attested-digest test does not bless is a",
        "defect by construction.",
    ]
    return lines


def emit_c(ranges, digest, source_hashes):
    lo_vals = [r[0] for r in ranges]
    hi_vals = [r[1] for r in ranges]
    reps = [r[2] for r in ranges]
    att = "\n".join(" * " + ln if ln else " *" for ln in
                    _attestation_lines(digest, ranges, source_hashes))

    def _rows(vals, fmt, per):
        out = []
        for i in range(0, len(vals), per):
            out.append("    " + " ".join(fmt(v) for v in vals[i:i + per]))
        return "\n".join(out)

    return f"""/*
 * srmech_unicode_fold_tables.h — the SINGLE attested home for the vendored
 * combining-mark fold table.
 *
 * GENERATED FILE — do not edit. Regenerate with:
 *     python3 c/tools/gen_unicode_fold_tables.py --emit
 * Re-verify against upstream with:
 *     python3 c/tools/gen_unicode_fold_tables.py --verify
 *
 * This header is what makes a BARE-C HOST WITH NO PYTHON PRESENT able to fold
 * combining marks over the full Unicode domain (ADR-0003) — there is no
 * `unicodedata` to ask, so the data must be here. The table stays a
 * caller-provided INPUT to the folder — srmech ships this as the DEFAULT
 * table; a host may hand the folder its own. Nothing here is linked or
 * imported (ADR-0005: the scope is imports and links; this is data).
 *
 * ────────────────────────────────────────────────────────────────────
{att}
 * ────────────────────────────────────────────────────────────────────
 *
 * Row payload: SRMECH_FOLD_REP[i] == 0 means every codepoint in
 * [LO[i], HI[i]] is a combining mark and is DROPPED; a non-zero value is the
 * codepoint each one is REPLACED by. Replacements are fully resolved, so one
 * pass suffices (closure is asserted by the generator).
 *
 * License: MIT (the srmech code); the DATA is {UCD_LICENSE}.
 */
#ifndef SRMECH_UNICODE_FOLD_TABLES_H
#define SRMECH_UNICODE_FOLD_TABLES_H

#include <stdint.h>
#include <stddef.h>

#define SRMECH_FOLD_UCD_VERSION "{UCD_VERSION}"
#define SRMECH_FOLD_TABLE_SHA256 "{digest}"
#define SRMECH_FOLD_RANGE_COUNT {len(ranges)}u

/* Payload sentinel: the range is a combining mark and is dropped. */
#define SRMECH_FOLD_DROP 0u

/* Range low bounds (ascending, non-overlapping). */
static const uint32_t SRMECH_FOLD_LO[SRMECH_FOLD_RANGE_COUNT] = {{
{_rows(lo_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Range high bounds (inclusive). */
static const uint32_t SRMECH_FOLD_HI[SRMECH_FOLD_RANGE_COUNT] = {{
{_rows(hi_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Replacement codepoint per range; SRMECH_FOLD_DROP means delete. */
static const uint32_t SRMECH_FOLD_REP[SRMECH_FOLD_RANGE_COUNT] = {{
{_rows(reps, lambda v: f"0x{v:05X}u,", 8)}
}};

#endif /* SRMECH_UNICODE_FOLD_TABLES_H */
"""


def emit_py(ranges, digest, source_hashes):
    att = "\n".join(_attestation_lines(digest, ranges, source_hashes))
    blob = blob_bytes(ranges)
    # 16 bytes per source line keeps the generated file diff-legible.
    lit = "\n".join(
        "    " + repr(blob[i:i + 16]) for i in range(0, len(blob), 16)
    )
    drop_rows = sum(1 for r in ranges if r[2] == FOLD_DROP)
    return f'''"""Vendored combining-mark fold table.

GENERATED FILE — do not edit. Regenerate with::

    python3 c/tools/gen_unicode_fold_tables.py --emit

Re-verify against upstream with ``--verify``.

This module and ``c/src/srmech_unicode_fold_tables.h`` are emitted from ONE
upstream source by ONE generator, so the two coherency projections (ADR-0009)
hold byte-identical tables by construction rather than by discipline;
``tests/test_unicode_fold_tables_attested.py`` pins that equality.

{att}
"""
from __future__ import annotations

#: Unicode version this table was generated from.
UCD_VERSION = "{UCD_VERSION}"

#: sha256 of :data:`FOLD_TABLE_BLOB` — the attested digest the drift test pins.
FOLD_TABLE_SHA256 = "{digest}"

#: Number of packed ranges ({drop_rows} drop + {len(ranges) - drop_rows} map).
FOLD_RANGE_COUNT = {len(ranges)}

#: Payload sentinel: the range is a combining mark and is dropped.
FOLD_DROP = 0

#: General_Category values that ARE combining marks — the op's whole scope.
MARK_CATEGORIES = {tuple(sorted(MARK_CATEGORIES))!r}

#: The canonical packed wire form: little-endian ``lo:u32 || hi:u32 ||
#: rep:u32`` per range, ascending. Byte-identical to the C projection's
#: SRMECH_FOLD_LO / _HI / _REP arrays.
FOLD_TABLE_BLOB = (
{lit}
)
'''


# ── fetch / load ───────────────────────────────────────────────────────────
def load_sources(ucd_dir, fetch):
    """Return (texts, hashes). Fetches from unicode.org when ``fetch``."""
    texts, hashes = {}, {}
    for name, (url, expected) in UCD_SOURCES.items():
        if fetch:
            with urllib.request.urlopen(url, timeout=120) as fh:
                raw = fh.read()
        else:
            with open(os.path.join(ucd_dir, name), "rb") as fh:
                raw = fh.read()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise SystemExit(
                f"UPSTREAM DRIFT: {name}\n"
                f"  attested sha256 : {expected}\n"
                f"  actual sha256   : {digest}\n"
                f"  source          : {url}\n"
                "The vendored table is pinned to a specific upstream byte "
                "stream. If Unicode has published a revision, re-vendor "
                "deliberately (update UCD_SOURCES + UCD_VERSION, re-emit, and "
                "re-run the fold tests) — do not silently accept."
            )
        texts[name] = raw.decode("utf-8")
        hashes[name] = digest
    return texts, hashes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true",
                   help="regenerate both projections from --ucd-dir")
    g.add_argument("--verify", action="store_true",
                   help="re-fetch upstream, recompute, diff against vendored")
    ap.add_argument("--ucd-dir", default=None,
                    help="local UCD directory (default: fetch from unicode.org)")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))          # docs/srmech
    c_path = os.path.join(root, "c", "src", "srmech_unicode_fold_tables.h")
    py_path = os.path.join(root, "python", "srmech", "amsc",
                           "_unicode_fold_tables.py")

    fetch = args.ucd_dir is None
    texts, hashes = load_sources(args.ucd_dir, fetch)
    categories, decompositions = parse_unicode_data(texts["UnicodeData.txt"])
    ranges = pack_ranges(build_entries(categories, decompositions))
    blob = blob_bytes(ranges)
    digest = hashlib.sha256(blob).hexdigest()
    c_text = emit_c(ranges, digest, hashes)
    py_text = emit_py(ranges, digest, hashes)

    if args.emit:
        with open(c_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(c_text)
        with open(py_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(py_text)
        print(f"emitted {len(ranges)} ranges / {len(blob)} bytes "
              f"(sha256 {digest[:16]}…)")
        print(f"  {c_path}")
        print(f"  {py_path}")
        return 0

    # --verify: the re-derivation the MPM discipline requires.
    bad = 0
    for path, fresh in ((c_path, c_text), (py_path, py_text)):
        with open(path, "r", encoding="utf-8", newline="") as fh:
            vendored = fh.read().replace("\r\n", "\n")
        if vendored != fresh:
            print(f"DRIFT: {path} differs from a fresh re-derivation", file=sys.stderr)
            bad += 1
        else:
            print(f"ok: {path}")
    print(f"ranges={len(ranges)} bytes={len(blob)} table_sha256={digest}")
    if bad:
        print("\nRE-VERIFICATION FAILED — the vendored table does not match a "
              "fresh derivation from the attested upstream file.", file=sys.stderr)
        return 1
    print("re-verification OK — vendored table re-derives exactly from upstream.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
