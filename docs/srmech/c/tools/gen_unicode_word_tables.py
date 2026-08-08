#!/usr/bin/env python3
"""Generate — and RE-VERIFY — the vendored WORD-CHARACTER property table.

One generator, two coherency projections (ADR-0009). It emits BOTH:

  * ``c/src/srmech_unicode_word_tables.h``        — the compiled projection's
  * ``python/srmech/math/_unicode_word_tables.py`` — the scripting projection's

from ONE upstream source, so the two are byte-identical by construction rather
than by discipline; ``tests/test_unicode_word_tables_attested.py`` pins that.

This is the rc287 / rc293 vendoring pattern applied to a THIRD table. The
argument for vendoring is the same one, and here it is sharper than for either
predecessor, because the alternative is not merely "derive it" — it is a
SPECIFIC host call with a SPECIFIC measured defect.

WHY NOT ``str.isalnum()``
-------------------------
``str.isalnum()`` answers this question already, and answering it that way is
what this table exists to prevent:

  * it pins the classification to the RUNNING interpreter's UCD. This tree's
    reference interpreter reports ``unicodedata.unidata_version == '13.0.0'``
    while the vendored GB table (``_unicode_gb_tables``) and the vendored fold
    table (``_unicode_fold_tables``) are both **UCD 16.0.0**. That is a live
    three-major-version skew, not a hypothetical one: U+0870 ARABIC LETTER
    ALEF WITH ATTACHED FATHA is ``Lo`` in 16.0.0 and unassigned (``Cn``) in
    13.0.0, so ``str.isalnum()`` says False for a codepoint the SAME PROCESS's
    ``glyph_stream`` segments as a letter cluster. One front door, two
    Unicode versions.
  * a bare-C host has no ``str`` at all (ADR-0003), so the compiled projection
    could never reproduce the scripting projection's answer. Two projections
    on different data is exactly what ADR-0009 forbids.

So the choice is vendored-vs-HOST-DEPENDENT, and the same favourable
consequence follows as for the two predecessor tables: two hosts at different
Python / Unicode versions classify text IDENTICALLY. Under a host-derived
scheme they would not have.

WHAT "WORD CHARACTER" MEANS HERE — the whole contract
-----------------------------------------------------
A codepoint is a WORD character iff its General_Category is one of::

    L*  Lu Ll Lt Lm Lo    letters, in every script
    M*  Mn Mc Me          combining marks
    N*  Nd Nl No          numbers, incl. sub/superscript and letter-numerals

Everything else — punctuation (P*), symbols (S*), separators (Z*), controls
and unassigned (C*) — is a token SEPARATOR.

Three exclusions are deliberate, and each one costs something that is named
rather than glossed:

  * **Pc, Connector_Punctuation (``_``), is EXCLUDED.** UTS #18 Annex C's
    ``\\w`` includes it; this table does not. The reason is measured, not
    stylistic: ``srmech.introspect.search`` documents and depends on the query
    ``"top k score"`` reaching the op ``top_k_by_score``, which works only
    because the underscore SPLITS the query while the corpus keeps the
    underscored form intact and the match is a substring scan. Including Pc
    would fuse ``top_k_by_score`` into one query token and break that.
  * **S*, Symbol, is EXCLUDED** — so ``→`` (U+2192, ``Sm``), ``⊗``, ``≤`` and
    the ASCII operators ``+ = < > | ~ $ ^`` are separators. The cost is
    concrete: a query of a bare arrow tokenises to nothing. The reason it is
    still right is also concrete: including Sm fuses ``a+b`` and ``x=1`` into
    single tokens, which changes retrieval for the ASCII corpus that is
    ~99% of the registry. Note what this does NOT cost — ``ℚ`` (U+211A),
    ``𝕆`` (U+1D546) and ``Σ`` (U+03A3) are all ``Lu``, i.e. LETTERS, so the
    double-struck and Greek notation that fills srmech's prose is IN.
  * **M* is INCLUDED**, which ``str.isalnum()`` does not do. A grapheme
    cluster's continuation codepoints are marks; a cluster whose BASE is a
    mark (a defective combining sequence, or text that begins mid-cluster) is
    still word content, not a separator.

MODES
-----
``--emit``    regenerate both projections from a local UCD directory.
``--verify``  RE-FETCH the official file, recompute, and diff against what is
              vendored. Exits non-zero on ANY drift. This is the
              re-derivation path the MPM discipline requires: a vendored table
              nobody can re-derive is exactly the failure the discipline
              exists to prevent. Needs network; NOT a unit test — the host's
              own ``unicodedata`` cannot serve as the drift oracle, because it
              is pinned to the host interpreter's Unicode version (see above:
              this tree's host disagrees with this table by construction and
              by design).

Usage
-----
    python3 gen_unicode_word_tables.py --emit   [--ucd-dir DIR]
    python3 gen_unicode_word_tables.py --verify [--ucd-dir DIR]

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
UCD_RETRIEVED_AT = "2026-08-08T00:00:00Z"
UCD_BASE = f"https://www.unicode.org/Public/{UCD_VERSION}/ucd"

#: filename → (url, expected sha256 of the upstream file). The same file and
#: the same pinned digest the fold table is built from — one upstream byte
#: stream, two derived tables, so a drift in either is a drift in both.
UCD_SOURCES = {
    "UnicodeData.txt": (
        f"{UCD_BASE}/UnicodeData.txt",
        "ff58e5823bd095166564a006e47d111130813dcf8bf234ef79fa51a870edb48f",
    ),
}

#: The General_Category values that ARE word characters, grouped by the KIND
#: each one contributes. This mapping IS the contract; see the module docstring
#: for what each exclusion costs.
WORD_KIND_LETTER = 1
WORD_KIND_NUMBER = 2
CATEGORY_KIND = {
    "Lu": WORD_KIND_LETTER, "Ll": WORD_KIND_LETTER, "Lt": WORD_KIND_LETTER,
    "Lm": WORD_KIND_LETTER, "Lo": WORD_KIND_LETTER,
    # Marks ride with LETTER: a mark is a cluster CONTINUATION, and the one
    # place a mark can be a cluster BASE is a defective sequence, where the
    # letter reading is the only sane one.
    "Mn": WORD_KIND_LETTER, "Mc": WORD_KIND_LETTER, "Me": WORD_KIND_LETTER,
    "Nd": WORD_KIND_NUMBER, "Nl": WORD_KIND_NUMBER, "No": WORD_KIND_NUMBER,
}
WORD_CATEGORIES = tuple(CATEGORY_KIND)

#: The highest codepoint Unicode defines. Used only to bound assertions.
CP_MAX = 0x10FFFF


# ── UCD parsing ────────────────────────────────────────────────────────────
def parse_unicode_data(text):
    """UnicodeData.txt → {cp: General_Category} over the WHOLE domain.

    UnicodeData.txt expresses large uniform blocks as a ``First>``/``Last>``
    line pair rather than one line per codepoint. Unlike the fold generator —
    which asserts those blocks carry no marks and then SKIPS them — this
    generator must EXPAND them, because they are exactly where the bulk of the
    world's letters live: CJK Unified Ideographs (``Lo``), the Hangul Syllable
    block (``Lo``), Tangut (``Lo``), Nushu (``Lo``). Dropping them would make
    ~100k letters classify as separators, which is the same shape of silent
    content deletion the rc287 tokenizer removal was about.
    """
    categories = {}
    pending = None
    n_expanded = 0
    for line in text.splitlines():
        if not line:
            continue
        fields = line.split(";")
        cp = int(fields[0], 16)
        name, category = fields[1], fields[2]
        if name.endswith(", First>"):
            pending = (cp, category)
            continue
        if name.endswith(", Last>"):
            if pending is None:
                raise SystemExit(
                    f"UnicodeData.txt: Last> without First> at {cp:04X}")
            lo, block_category = pending
            if block_category in CATEGORY_KIND:
                for c in range(lo, cp + 1):
                    categories[c] = block_category
                    n_expanded += 1
            pending = None
            continue
        categories[cp] = category
    if pending is not None:
        raise SystemExit("UnicodeData.txt: unterminated First> block")

    # A range block IS the CJK/Hangul/Tangut bulk. If expansion ever yields
    # nothing the parse has silently stopped observing — fail rather than emit
    # a table missing 100k letters.
    if n_expanded < 90000:
        raise SystemExit(
            f"UnicodeData.txt: only {n_expanded} codepoints came from First>/"
            "Last> range blocks. The CJK / Hangul / Tangut blocks alone are "
            "~100k word characters; this parse is not observing them.")
    return categories


def build_entries(categories):
    """{cp: category} → ``{cp: kind}`` over the WORD codepoints.

    Two invariants are asserted rather than assumed, because both are
    load-bearing for the consumer and both are cheap to check here:

      * every ASCII letter and digit is IN (so the ~99%-ASCII registry corpus
        tokenises exactly as it did before the table existed);
      * ASCII space, ``_``, ``.``, ``+``, ``=`` and ``-`` are OUT (so
        underscore-splitting and the operator separators survive).
    """
    word = {cp: CATEGORY_KIND[category]
            for cp, category in categories.items()
            if category in CATEGORY_KIND}

    must_be_in = ([c for c in range(ord("a"), ord("z") + 1)]
                  + [c for c in range(ord("A"), ord("Z") + 1)]
                  + [c for c in range(ord("0"), ord("9") + 1)])
    absent = [cp for cp in must_be_in if cp not in word]
    if absent:
        raise SystemExit(
            "word table omits ASCII alphanumerics "
            f"{[chr(c) for c in absent]!r} — the corpus is ~99% ASCII and "
            "would stop tokenising. Re-vendor deliberately.")

    must_be_out = [ord(c) for c in " _.+=-/():,\t\n"]
    present = [cp for cp in must_be_out if cp in word]
    if present:
        raise SystemExit(
            "word table includes ASCII separator(s) "
            f"{[chr(c) for c in present]!r} — underscore-splitting and the "
            "operator separators are contract. Re-vendor deliberately.")

    # The KIND split is what makes the letter-digit boundary (`klein4` ->
    # `klein 4`) language-agnostic instead of `[a-z][0-9]`. Assert it on the
    # ASCII case the existing surfaces already depend on.
    for c in "az":
        if word[ord(c)] != WORD_KIND_LETTER:
            raise SystemExit(f"ASCII {c!r} is not classified LETTER")
    for c in "09":
        if word[ord(c)] != WORD_KIND_NUMBER:
            raise SystemExit(f"ASCII {c!r} is not classified NUMBER")
    return word


def pack_ranges(entries):
    """``{cp: kind}`` → coalesced, non-overlapping ``[(lo, hi, kind)]``."""
    ranges = []
    for cp in sorted(entries):
        kind = entries[cp]
        if ranges and ranges[-1][1] == cp - 1 and ranges[-1][2] == kind:
            ranges[-1][1] = cp
        else:
            ranges.append([cp, cp, kind])
    return [tuple(r) for r in ranges]


def blob_bytes(ranges):
    """The canonical packed wire form BOTH projections embed and hash.

    Little-endian ``lo:u32 || hi:u32 || kind:u8`` per range, in ascending
    order. 9 bytes per range — the same row shape as the GB table, and for the
    same reason: the payload carries a real distinction. ``kind`` is 1 for
    LETTER (L* and M*) and 2 for NUMBER (N*); an uncovered codepoint is a
    separator. The split is not decoration — it is what makes the
    letter-digit token boundary (``klein4`` -> ``klein 4``) language-agnostic
    instead of the ``[a-z][0-9]`` regex it replaces. This byte string IS the
    attested artefact: its sha256 is what the drift test pins.
    """
    out = bytearray()
    for lo, hi, kind in ranges:
        out += lo.to_bytes(4, "little")
        out += hi.to_bytes(4, "little")
        out += kind.to_bytes(1, "little")
    return bytes(out)


# ── emitters ───────────────────────────────────────────────────────────────
def _attestation_lines(digest, ranges, n_codepoints, source_hashes):
    """The shared MPR v1 attestation block, as plain text lines."""
    lines = [
        "ATTESTATION (MPR v1 — the on-disk MPM discipline applied to a VENDORED",
        "DATA TABLE, following c/src/srmech_unicode_fold_tables.h):",
        "",
        "  data           : word-character property — General_Category in",
        f"                   {' '.join(WORD_CATEGORIES)}, each row carrying",
        "                   the KIND it contributes: 1 LETTER (L* and M*),",
        "                   2 NUMBER (N*). Punctuation, symbols, separators,",
        "                   controls and unassigned are SEPARATOR (no row).",
        "                   Connector_Punctuation",
        "                   (Pc, `_`) is deliberately EXCLUDED, unlike",
        "                   the UTS #18 word-character class; Symbol (S*)",
        "                   is deliberately EXCLUDED.",
        "  data_schema_id : unicode://ucd/word-character-table/v1",
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
        f"                    covering {n_codepoints} codepoints,",
        f"                    {len(ranges) * 9} bytes, little-endian",
        "                    lo:u32 || hi:u32 || kind:u8)",
        "  verification   : RE-DERIVABLE — c/tools/gen_unicode_word_tables.py",
        "                   --verify re-fetches the official file, recomputes",
        "                   this table and diffs it against what is vendored.",
        "                   The ASCII in/out/KIND invariants and the",
        "                   range-block expansion floor are asserted by",
        "                   the generator, not assumed.",
        "  cite_as        : \"The Unicode Standard, UnicodeData.txt, Unicode "
        f"{UCD_VERSION}.\"",
        "",
        "RULE: do NOT edit these values by hand. Regenerate with the generator",
        "above; a hand edit that the attested-digest test does not bless is a",
        "defect by construction.",
    ]
    return lines


def emit_c(ranges, digest, n_codepoints, source_hashes):
    lo_vals = [r[0] for r in ranges]
    hi_vals = [r[1] for r in ranges]
    kinds = [r[2] for r in ranges]
    att = "\n".join(" * " + ln if ln else " *" for ln in
                    _attestation_lines(digest, ranges, n_codepoints,
                                       source_hashes))

    def _rows(vals, fmt, per):
        out = []
        for i in range(0, len(vals), per):
            out.append("    " + " ".join(fmt(v) for v in vals[i:i + per]))
        return "\n".join(out)

    return f"""/*
 * srmech_unicode_word_tables.h — the SINGLE attested home for the vendored
 * word-character property table.
 *
 * GENERATED FILE — do not edit. Regenerate with:
 *     python3 c/tools/gen_unicode_word_tables.py --emit
 * Re-verify against upstream with:
 *     python3 c/tools/gen_unicode_word_tables.py --verify
 *
 * This header is what makes a BARE-C HOST WITH NO PYTHON PRESENT able to tell
 * a word character from a separator over the full Unicode domain (ADR-0003) —
 * there is no `str.isalnum()` to ask, which is why the table is vendored at
 * all. Nothing here is linked or imported (ADR-0005: the scope is imports and
 * links; this is data).
 *
 * NO C CONSUMER YET, AND THAT IS STATED RATHER THAN IMPLIED. The op that
 * reads this table today is `srmech.introspect.search._tokenize`, a
 * scripting-side `non_compute` registry accessor with no C entry point, so
 * there is nothing in c/src to include this header. It is emitted anyway, by
 * the SAME generator pass, for one reason: when a compiled peer for that
 * index does land it must read the SAME data, not a second derivation of it.
 * A table vendored after the fact is a table that has already diverged.
 *
 * ────────────────────────────────────────────────────────────────────
{att}
 * ────────────────────────────────────────────────────────────────────
 *
 * Membership test: binary-search LO for the last range with LO[i] <= cp; the
 * codepoint is a WORD character iff such an i exists and cp <= HI[i], and
 * SRMECH_WORD_KIND[i] then says which kind it is. A codepoint no range covers
 * is a token SEPARATOR.
 *
 * License: MIT (the srmech code); the DATA is {UCD_LICENSE}.
 */
#ifndef SRMECH_UNICODE_WORD_TABLES_H
#define SRMECH_UNICODE_WORD_TABLES_H

#include <stdint.h>
#include <stddef.h>

#define SRMECH_WORD_UCD_VERSION "{UCD_VERSION}"
#define SRMECH_WORD_TABLE_SHA256 "{digest}"
#define SRMECH_WORD_RANGE_COUNT {len(ranges)}u

/* Row payload: which KIND of word character the range holds. A codepoint no
 * range covers is a token SEPARATOR and has no kind. */
#define SRMECH_WORD_KIND_LETTER {WORD_KIND_LETTER}u
#define SRMECH_WORD_KIND_NUMBER {WORD_KIND_NUMBER}u

/* Range low bounds (ascending, non-overlapping). */
static const uint32_t SRMECH_WORD_LO[SRMECH_WORD_RANGE_COUNT] = {{
{_rows(lo_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Range high bounds (inclusive). */
static const uint32_t SRMECH_WORD_HI[SRMECH_WORD_RANGE_COUNT] = {{
{_rows(hi_vals, lambda v: f"0x{v:05X}u,", 8)}
}};

/* Per-range kind: SRMECH_WORD_KIND_LETTER or SRMECH_WORD_KIND_NUMBER. */
static const uint8_t SRMECH_WORD_KIND[SRMECH_WORD_RANGE_COUNT] = {{
{_rows(kinds, lambda v: f"{v}u,", 16)}
}};

#endif /* SRMECH_UNICODE_WORD_TABLES_H */
"""


def emit_py(ranges, digest, n_codepoints, source_hashes):
    att = "\n".join(_attestation_lines(digest, ranges, n_codepoints,
                                       source_hashes))
    blob = blob_bytes(ranges)
    # 16 bytes per source line keeps the generated file diff-legible.
    lit = "\n".join(
        "    " + repr(blob[i:i + 16]) for i in range(0, len(blob), 16)
    )
    return f'''"""Vendored word-character property table.

GENERATED FILE — do not edit. Regenerate with::

    python3 c/tools/gen_unicode_word_tables.py --emit

Re-verify against upstream with ``--verify``.

This module and ``c/src/srmech_unicode_word_tables.h`` are emitted from ONE
upstream source by ONE generator, so the two coherency projections (ADR-0009)
hold byte-identical tables by construction rather than by discipline;
``tests/test_unicode_word_tables_attested.py`` pins that equality.

It exists so that no srmech surface has to ask ``str.isalnum()``, which pins
the answer to the RUNNING interpreter's UCD — this tree's host is at 13.0.0
against this table's 16.0.0 — and which a bare-C host cannot ask at all.

{att}
"""
from __future__ import annotations

#: Unicode version this table was generated from.
UCD_VERSION = "{UCD_VERSION}"

#: sha256 of :data:`WORD_TABLE_BLOB` — the attested digest the drift test pins.
WORD_TABLE_SHA256 = "{digest}"

#: Number of packed ranges.
WORD_RANGE_COUNT = {len(ranges)}

#: Codepoints covered (the population the ranges coalesce).
WORD_CODEPOINT_COUNT = {n_codepoints}

#: The General_Category values that ARE word characters — the whole contract.
#: Pc (``_``) and S* (``→``) are deliberately absent; see the generator.
WORD_CATEGORIES = {WORD_CATEGORIES!r}

#: Row payload — which KIND of word character a range holds. A codepoint no
#: range covers is a token SEPARATOR and has no kind. The LETTER/NUMBER split
#: is what makes the letter-digit token boundary (``klein4`` -> ``klein 4``)
#: language-agnostic instead of an ``[a-z][0-9]`` regex.
WORD_KIND_LETTER = {WORD_KIND_LETTER}
WORD_KIND_NUMBER = {WORD_KIND_NUMBER}

#: The canonical packed wire form: little-endian ``lo:u32 || hi:u32 ||
#: kind:u8`` per range, ascending. Byte-identical to the C projection's
#: SRMECH_WORD_LO / _HI / _KIND arrays.
WORD_TABLE_BLOB = (
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
                "re-run the word tests) — do not silently accept."
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
    c_path = os.path.join(root, "c", "src", "srmech_unicode_word_tables.h")
    py_path = os.path.join(root, "python", "srmech", "math",
                           "_unicode_word_tables.py")

    fetch = args.ucd_dir is None
    texts, hashes = load_sources(args.ucd_dir, fetch)
    categories = parse_unicode_data(texts["UnicodeData.txt"])
    entries = build_entries(categories)
    ranges = pack_ranges(entries)
    blob = blob_bytes(ranges)
    digest = hashlib.sha256(blob).hexdigest()
    c_text = emit_c(ranges, digest, len(entries), hashes)
    py_text = emit_py(ranges, digest, len(entries), hashes)

    if args.emit:
        with open(c_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(c_text)
        with open(py_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(py_text)
        print(f"emitted {len(ranges)} ranges / {len(blob)} bytes "
              f"covering {len(entries)} codepoints (sha256 {digest[:16]}…)")
        print(f"  {c_path}")
        print(f"  {py_path}")
        return 0

    # --verify: the re-derivation the MPM discipline requires.
    bad = 0
    for path, fresh in ((c_path, c_text), (py_path, py_text)):
        with open(path, "r", encoding="utf-8", newline="") as fh:
            vendored = fh.read().replace("\r\n", "\n")
        if vendored != fresh:
            print(f"DRIFT: {path} differs from a fresh re-derivation",
                  file=sys.stderr)
            bad += 1
        else:
            print(f"ok: {path}")
    if bad:
        print("\nRe-derivation DIFFERS from the vendored table. Either "
              "upstream moved (re-vendor deliberately) or the vendored file "
              "was hand-edited (revert it).", file=sys.stderr)
        return 1
    print(f"re-derivation matches both projections "
          f"({len(ranges)} ranges, sha256 {digest[:16]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
