#!/usr/bin/env python3
"""Generate — and RE-VERIFY — the vendored UAX #29 grapheme-break tables.

One generator, two coherency projections (ADR-0009). It emits BOTH:

  * ``c/src/srmech_unicode_gb_tables.h``      — the compiled projection's table
  * ``python/srmech/math/_unicode_gb_tables.py`` — the scripting projection's

from ONE upstream source, so the two are byte-identical by construction rather
than by discipline. ``tests/test_unicode_gb_tables_attested.py`` pins that.

Why the table is vendored at all (the ADR-0005 argument, re-checked rc287):
the ADR's scope is *imports and links* — "srmech source imports NO external
mathematics library"; "The C side likewise links no external math/bignum
library" — enforced by an AST import-walk that cannot see a static array. A
vendored table is **data**, not a dependency. The in-tree precedent is
``c/src/srmech_sha256_constants.h`` (FIPS-180-4 round constants with an MPR v1
attestation block in the comment). The decisive point is narrower than "it is
allowed": ``Extended_Pictographic`` and ``InCB`` are **not derivable from
``unicodedata`` at any fidelity**, so the real choice is vendored-vs-ABSENT,
and absent means no GB11 (emoji ZWJ) and no GB9c (Indic conjuncts).

MODES
-----
``--emit``    regenerate both projections from a local UCD directory.
``--verify``  RE-FETCH the official files, recompute, and diff against what is
              vendored. Exits non-zero on ANY drift. This is the re-derivation
              path the MPM discipline requires: a vendored table nobody can
              re-derive is exactly the failure the discipline exists to
              prevent. Needs network; NOT a unit test (see the module note in
              tests/test_unicode_gb_tables_attested.py for why the host's own
              ``unicodedata`` cannot serve as the drift oracle).

Usage
-----
    python3 gen_unicode_gb_tables.py --emit   [--ucd-dir DIR]
    python3 gen_unicode_gb_tables.py --verify [--ucd-dir DIR]

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
UCD_RETRIEVED_AT = "2026-07-19T00:00:00Z"
UCD_BASE = f"https://www.unicode.org/Public/{UCD_VERSION}/ucd"

#: filename → (url, expected sha256 of the upstream file).
UCD_SOURCES = {
    "GraphemeBreakProperty.txt": (
        f"{UCD_BASE}/auxiliary/GraphemeBreakProperty.txt",
        "c29360bd6f7132811d701d29069541e827eb44bfc4c8fbde8c370d6982689dc1",
    ),
    "emoji-data.txt": (
        f"{UCD_BASE}/emoji/emoji-data.txt",
        "f1365a5173eee18e1f98b240cdc492e84a25f1ce7e0c9d1094eb29c41a22696a",
    ),
    "DerivedCoreProperties.txt": (
        f"{UCD_BASE}/DerivedCoreProperties.txt",
        "39d35161f2954497f69e08bdb9e701493f476a3d30222de20028feda36c1dabd",
    ),
    "GraphemeBreakTest.txt": (
        f"{UCD_BASE}/auxiliary/GraphemeBreakTest.txt",
        "ee2b9354d270ac061b29f09662cafea06341d77e704b8cc6bd72aaeeda363cb5",
    ),
}

MAX_CP = 0x110000

# ── UAX #29 §3 Hangul syllable algebra — ARITHMETIC, never table rows ───────
# Storing the precomposed syllables as data would cost 7,254 B more (798
# ranges of pure LV/LVT alternation). The algebra is exact over U+AC00..U+D7A3
# ONLY, so exactly those rows are omitted and the lookup recovers them
# arithmetically in both projections. Jamo L/V/T stay as table rows — see
# HANGUL_TAGS below for why deriving them from these constants is wrong.
SBASE, LBASE, VBASE, TBASE = 0xAC00, 0x1100, 0x1161, 0x11A7
LCOUNT, VCOUNT, TCOUNT = 19, 21, 28
NCOUNT = VCOUNT * TCOUNT      # 588
SCOUNT = LCOUNT * NCOUNT      # 11172

#: GBP tag values. Order is the wire format — APPEND only, never reorder.
GBP_TAGS = (
    "Other", "CR", "LF", "Control", "Extend", "ZWJ", "Regional_Indicator",
    "Prepend", "SpacingMark", "L", "V", "T", "LV", "LVT",
)
GBP_INDEX = {name: i for i, name in enumerate(GBP_TAGS)}

#: InCB tag values (UAX #29 GB9c, Unicode 15.1+).
INCB_TAGS = ("None", "Linker", "Consonant", "Extend")
INCB_INDEX = {name: i for i, name in enumerate(INCB_TAGS)}

#: Packed property byte layout: gbp in bits 0-3, Extended_Pictographic in bit
#: 4, InCB in bits 5-6. Bit 7 reserved (must be 0).
PROP_GBP_MASK = 0x0F
PROP_EXTPICT_BIT = 0x10
PROP_INCB_SHIFT = 5
PROP_INCB_MASK = 0x60

#: Hangul rows omitted from the table and recovered by arithmetic instead.
#:
#: ONLY the precomposed syllable block U+AC00..U+D7A3 qualifies. There the
#: UAX #29 §3 algebra ``(cp - SBase) % TCount == 0 ? LV : LVT`` is EXACT, and
#: it is where the bulk sits: 798 ranges of pure LV/LVT alternation, 7,254 B.
#:
#: The jamo L/V/T rows are NOT included here, and must not be. The §3
#: composition constants (LBase/VBase/TBase) are *composition* anchors, not
#: the GBP jamo ranges, and they do not coincide: U+1160 HANGUL JUNGSEONG
#: FILLER is GBP=V yet sits below VBase=U+1161. Deriving jamo from those
#: constants silently mis-tags the fillers and drops the Jamo Extended-A/B
#: blocks (U+A960.., U+D7B0..) entirely — caught here by GraphemeBreakTest
#: case <U+1100, U+1160>, which needs GB6 (L × V) and got a break. Jamo is
#: only ~7 ranges of table, so the saving would have been negligible anyway.
HANGUL_TAGS = frozenset({"LV", "LVT"})


# ── UCD parsing ────────────────────────────────────────────────────────────
def _iter_ucd(text):
    """Yield (lo, hi, fields) for each non-comment UCD line."""
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        fields = [f.strip() for f in line.split(";")]
        rng = fields[0]
        if ".." in rng:
            lo, hi = (int(x, 16) for x in rng.split(".."))
        else:
            lo = hi = int(rng, 16)
        yield lo, hi, fields[1:]


def build_props(sources):
    """UCD text → {cp: packed property byte}, Hangul rows EXCLUDED.

    ``sources`` maps filename → decoded text.
    """
    props = {}

    def _set(cp, mask, value):
        props[cp] = (props.get(cp, 0) & ~mask) | value

    for lo, hi, fields in _iter_ucd(sources["GraphemeBreakProperty.txt"]):
        tag = fields[0]
        if tag in HANGUL_TAGS:
            continue                     # derived arithmetically — see above
        idx = GBP_INDEX[tag]
        for cp in range(lo, hi + 1):
            _set(cp, PROP_GBP_MASK, idx)

    for lo, hi, fields in _iter_ucd(sources["emoji-data.txt"]):
        if fields[0] != "Extended_Pictographic":
            continue
        for cp in range(lo, hi + 1):
            _set(cp, PROP_EXTPICT_BIT, PROP_EXTPICT_BIT)

    for lo, hi, fields in _iter_ucd(sources["DerivedCoreProperties.txt"]):
        if len(fields) < 2 or fields[0] != "InCB":
            continue
        idx = INCB_INDEX[fields[1]]
        for cp in range(lo, hi + 1):
            _set(cp, PROP_INCB_MASK, idx << PROP_INCB_SHIFT)

    return {cp: p for cp, p in props.items() if p != 0}


def pack_ranges(props):
    """{cp: prop} → sorted, coalesced, non-overlapping [(lo, hi, prop)]."""
    ranges = []
    for cp in sorted(props):
        prop = props[cp]
        if ranges and ranges[-1][1] == cp - 1 and ranges[-1][2] == prop:
            ranges[-1][1] = cp
        else:
            ranges.append([cp, cp, prop])
    return [tuple(r) for r in ranges]


def blob_bytes(ranges):
    """The canonical packed wire form BOTH projections embed and hash.

    Little-endian ``lo:u32 || hi:u32 || prop:u8`` per range, in ascending
    order. 9 bytes per range. This byte string IS the attested artefact: its
    sha256 is what the drift test pins.
    """
    out = bytearray()
    for lo, hi, prop in ranges:
        out += lo.to_bytes(4, "little")
        out += hi.to_bytes(4, "little")
        out.append(prop)
    return bytes(out)


# ── emitters ───────────────────────────────────────────────────────────────
def _attestation_lines(digest, ranges, source_hashes):
    """The shared MPR v1 attestation block, as plain text lines."""
    lines = [
        "ATTESTATION (MPR v1 — the on-disk MPM discipline applied to a VENDORED",
        "DATA TABLE, following c/src/srmech_sha256_constants.h):",
        "",
        "  data           : UAX #29 extended-grapheme-cluster break properties —",
        "                   GraphemeBreakProperty + Extended_Pictographic (GB11)",
        "                   + InCB (GB9c). Hangul L/V/T/LV/LVT rows are OMITTED",
        "                   and derived by the UAX #29 §3 syllable algebra.",
        "  data_schema_id : unicode://uax29/grapheme-break-table/v1",
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
        f"                   (sha256 of the packed blob: {len(ranges)} ranges,",
        f"                    {len(ranges) * 9} bytes, little-endian",
        "                    lo:u32 || hi:u32 || prop:u8)",
        "  verification   : RE-DERIVABLE — c/tools/gen_unicode_gb_tables.py",
        "                   --verify re-fetches the official files, recomputes",
        "                   this table and diffs it against what is vendored.",
        "                   Conformance is pinned separately at 1093/1093",
        "                   against the official GraphemeBreakTest.txt.",
        "  cite_as        : \"Unicode Standard Annex #29, Unicode Text",
        f"                   Segmentation, Unicode {UCD_VERSION}.\"",
        "",
        "RULE: do NOT edit these values by hand. Regenerate with the generator",
        "above; a hand edit that the attested-digest test does not bless is a",
        "defect by construction.",
    ]
    return lines


def emit_c(ranges, digest, source_hashes):
    lo_vals = [r[0] for r in ranges]
    hi_vals = [r[1] for r in ranges]
    props = [r[2] for r in ranges]
    att = "\n".join(" * " + ln if ln else " *" for ln in
                    _attestation_lines(digest, ranges, source_hashes))

    def _rows(vals, fmt, per):
        out = []
        for i in range(0, len(vals), per):
            out.append("    " + " ".join(fmt(v) for v in vals[i:i + per]))
        return "\n".join(out)

    return f"""/*
 * srmech_unicode_gb_tables.h — the SINGLE attested home for the vendored
 * UAX #29 grapheme-cluster break-property table.
 *
 * GENERATED FILE — do not edit. Regenerate with:
 *     python3 c/tools/gen_unicode_gb_tables.py --emit
 * Re-verify against upstream with:
 *     python3 c/tools/gen_unicode_gb_tables.py --verify
 *
 * This header is what makes a BARE-C HOST WITH NO PYTHON PRESENT able to
 * segment the full Unicode domain (ADR-0003). The table stays a
 * caller-provided INPUT to the segmenter — srmech ships this as the DEFAULT
 * table; a host may hand the segmenter its own. Nothing here is linked or
 * imported (ADR-0005: the scope is imports and links; this is data).
 *
 * ────────────────────────────────────────────────────────────────────
{att}
 * ────────────────────────────────────────────────────────────────────
 *
 * Packed property byte: gbp in bits 0-3, Extended_Pictographic in bit 4,
 * InCB in bits 5-6, bit 7 reserved 0.
 *
 * License: MIT (the srmech code); the DATA is {UCD_LICENSE}.
 */
#ifndef SRMECH_UNICODE_GB_TABLES_H
#define SRMECH_UNICODE_GB_TABLES_H

#include <stdint.h>
#include <stddef.h>

#define SRMECH_UCD_VERSION "{UCD_VERSION}"
#define SRMECH_GB_TABLE_SHA256 "{digest}"
#define SRMECH_GB_RANGE_COUNT {len(ranges)}u

/* GBP tag values — the wire format; APPEND only, never reorder. */
{chr(10).join(f'#define SRMECH_GBP_{t.upper()} {i}u' for i, t in enumerate(GBP_TAGS))}

/* InCB tag values (UAX #29 GB9c). */
{chr(10).join(f'#define SRMECH_INCB_{t.upper()} {i}u' for i, t in enumerate(INCB_TAGS))}

#define SRMECH_GB_PROP_GBP_MASK    0x0Fu
#define SRMECH_GB_PROP_EXTPICT_BIT 0x10u
#define SRMECH_GB_PROP_INCB_SHIFT  5u
#define SRMECH_GB_PROP_INCB_MASK   0x60u

/* UAX #29 §3 Hangul syllable algebra — arithmetic, not table rows. */
#define SRMECH_HANGUL_SBASE  0xAC00u
#define SRMECH_HANGUL_LBASE  0x1100u
#define SRMECH_HANGUL_VBASE  0x1161u
#define SRMECH_HANGUL_TBASE  0x11A7u
#define SRMECH_HANGUL_LCOUNT 19u
#define SRMECH_HANGUL_VCOUNT 21u
#define SRMECH_HANGUL_TCOUNT 28u
#define SRMECH_HANGUL_NCOUNT 588u
#define SRMECH_HANGUL_SCOUNT 11172u

/* Range low bounds (ascending, non-overlapping). */
static const uint32_t SRMECH_GB_LO[SRMECH_GB_RANGE_COUNT] = {{
{_rows(lo_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Range high bounds (inclusive). */
static const uint32_t SRMECH_GB_HI[SRMECH_GB_RANGE_COUNT] = {{
{_rows(hi_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Packed property byte per range. */
static const uint8_t SRMECH_GB_PROP[SRMECH_GB_RANGE_COUNT] = {{
{_rows(props, lambda v: f"0x{v:02X}u,", 16)}
}};

#endif /* SRMECH_UNICODE_GB_TABLES_H */
"""


def emit_py(ranges, digest, source_hashes):
    att = "\n".join(_attestation_lines(digest, ranges, source_hashes))
    blob = blob_bytes(ranges)
    # 16 bytes per source line keeps the generated file diff-legible.
    lit = "\n".join(
        "    " + repr(blob[i:i + 16]) for i in range(0, len(blob), 16)
    )
    return f'''"""Vendored UAX #29 grapheme-cluster break-property table.

GENERATED FILE — do not edit. Regenerate with::

    python3 c/tools/gen_unicode_gb_tables.py --emit

Re-verify against upstream with ``--verify``.

This module and ``c/src/srmech_unicode_gb_tables.h`` are emitted from ONE
upstream source by ONE generator, so the two coherency projections (ADR-0009)
hold byte-identical tables by construction rather than by discipline;
``tests/test_unicode_gb_tables_attested.py`` pins that equality.

{att}
"""
from __future__ import annotations

#: Unicode version this table was generated from.
UCD_VERSION = "{UCD_VERSION}"

#: sha256 of :data:`GB_TABLE_BLOB` — the attested digest the drift test pins.
GB_TABLE_SHA256 = "{digest}"

#: Number of packed ranges (Hangul omitted; derived arithmetically).
GB_RANGE_COUNT = {len(ranges)}

#: GBP tag values. Order is the wire format — APPEND only, never reorder.
GBP_TAGS = {GBP_TAGS!r}

#: InCB tag values (UAX #29 GB9c, Unicode 15.1+).
INCB_TAGS = {INCB_TAGS!r}

#: Packed property byte layout.
PROP_GBP_MASK = 0x0F
PROP_EXTPICT_BIT = 0x10
PROP_INCB_SHIFT = 5
PROP_INCB_MASK = 0x60

#: UAX #29 §3 Hangul syllable algebra — arithmetic, not table rows.
HANGUL_SBASE, HANGUL_LBASE, HANGUL_VBASE, HANGUL_TBASE = 0xAC00, 0x1100, 0x1161, 0x11A7
HANGUL_LCOUNT, HANGUL_VCOUNT, HANGUL_TCOUNT = 19, 21, 28
HANGUL_NCOUNT = 588
HANGUL_SCOUNT = 11172

#: The canonical packed wire form: little-endian ``lo:u32 || hi:u32 ||
#: prop:u8`` per range, ascending. Byte-identical to the C projection's
#: SRMECH_GB_LO / _HI / _PROP arrays.
GB_TABLE_BLOB = (
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
                "re-run the conformance suite) — do not silently accept."
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
    c_path = os.path.join(root, "c", "src", "srmech_unicode_gb_tables.h")
    py_path = os.path.join(root, "python", "srmech", "math",
                           "_unicode_gb_tables.py")

    fetch = args.ucd_dir is None
    texts, hashes = load_sources(args.ucd_dir, fetch)
    ranges = pack_ranges(build_props(texts))
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
              "fresh derivation from the attested upstream files.", file=sys.stderr)
        return 1
    print("re-verification OK — vendored table re-derives exactly from upstream.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
