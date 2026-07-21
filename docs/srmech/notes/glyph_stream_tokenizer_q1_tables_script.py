#!/usr/bin/env python3
"""Q1 — can UAX #29 GraphemeBreakProperty be DERIVED from `unicodedata`?

Generating code for every Q1 number in `glyph_stream_tokenizer_design.md`.

Method
------
1. TRUE   : parse the UCD 16.0.0 GraphemeBreakProperty.txt + emoji-data.txt
            (Extended_Pictographic) — ground truth.
2. DERIVED: best-effort reconstruction using ONLY what the running
            interpreter's `unicodedata` exposes (category / combining / name)
            plus pure ARITHMETIC (Hangul syllable algebra from UAX #29 §3,
            Regional_Indicator block). No vendored data.
3. Score  : per-codepoint disagreement, by property; then run BOTH through a
            full UAX #29 GB1..GB999 segmenter against the official
            GraphemeBreakTest.txt conformance suite.

The point is to MEASURE the approximation error, not assume it is small.

Usage:  python3 glyph_stream_tokenizer_q1_tables_script.py <ucd_dir>
UCD files (fetched, sha256 recorded in the NDJSON ledger):
  https://www.unicode.org/Public/16.0.0/ucd/auxiliary/GraphemeBreakProperty.txt
  https://www.unicode.org/Public/16.0.0/ucd/auxiliary/GraphemeBreakTest.txt
  https://www.unicode.org/Public/16.0.0/ucd/emoji/emoji-data.txt

No abs(); no external libraries; deterministic.
"""
from __future__ import annotations

import sys
import unicodedata
from collections import Counter

MAX_CP = 0x110000

# ── UAX #29 §3 Hangul syllable algebra — ARITHMETIC, not data ───────────────
SBASE, LBASE, VBASE, TBASE = 0xAC00, 0x1100, 0x1161, 0x11A7
LCOUNT, VCOUNT, TCOUNT = 19, 21, 28
NCOUNT = VCOUNT * TCOUNT          # 588
SCOUNT = LCOUNT * NCOUNT          # 11172


def parse_ranges(path, want=None):
    """UCD semicolon file → {cp: prop}. `want` filters to one property."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if not line:
                continue
            rng, prop = [x.strip() for x in line.split(";")[:2]]
            if want is not None and prop != want:
                continue
            if ".." in rng:
                a, b = [int(x, 16) for x in rng.split("..")]
            else:
                a = b = int(rng, 16)
            for cp in range(a, b + 1):
                out[cp] = prop
    return out


def parse_incb(path):
    """DerivedCoreProperties.txt → {cp: InCB value} (UAX #29 GB9c, Unicode 15.1+)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if not line:
                continue
            parts = [x.strip() for x in line.split(";")]
            if len(parts) < 3 or parts[1] != "InCB":
                continue
            rng, val = parts[0], parts[2]
            if ".." in rng:
                a, b = [int(x, 16) for x in rng.split("..")]
            else:
                a = b = int(rng, 16)
            for cp in range(a, b + 1):
                out[cp] = val
    return out


def true_tables(ucd_dir):
    gbp = parse_ranges(f"{ucd_dir}/GraphemeBreakProperty.txt")
    extpict = set(parse_ranges(f"{ucd_dir}/emoji-data.txt",
                               want="Extended_Pictographic"))
    incb = parse_incb(f"{ucd_dir}/DerivedCoreProperties.txt")
    return gbp, extpict, incb


# ── DERIVED: unicodedata + arithmetic only ─────────────────────────────────
def derived_tables():
    """Best-effort GraphemeBreakProperty from the RUNNING interpreter.

    Every rule here uses only unicodedata.category / .combining / .name, or
    fixed arithmetic. Nothing is vendored.
    """
    gbp = {}
    extpict = set()                     # NOT derivable — see report
    for cp in range(MAX_CP):
        ch = chr(cp)
        cat = unicodedata.category(ch)
        # --- constants (single codepoints, universally known) ---
        if cp == 0x0D:
            gbp[cp] = "CR"; continue
        if cp == 0x0A:
            gbp[cp] = "LF"; continue
        if cp == 0x200D:
            gbp[cp] = "ZWJ"; continue
        # --- Regional_Indicator: one contiguous block, arithmetic ---
        if 0x1F1E6 <= cp <= 0x1F1FF:
            gbp[cp] = "Regional_Indicator"; continue
        # --- Hangul: syllable algebra + jamo names ---
        if SBASE <= cp < SBASE + SCOUNT:
            gbp[cp] = "LV" if (cp - SBASE) % TCOUNT == 0 else "LVT"; continue
        if cat == "Lo":
            try:
                nm = unicodedata.name(ch)
            except ValueError:
                nm = ""
            if nm.startswith("HANGUL CHOSEONG"):
                gbp[cp] = "L"; continue
            if nm.startswith("HANGUL JUNGSEONG"):
                gbp[cp] = "V"; continue
            if nm.startswith("HANGUL JONGSEONG"):
                gbp[cp] = "T"; continue
        # --- Control: Cc/Cf/Zl/Zp (CR/LF/ZWJ already handled) ---
        if cat in ("Cc", "Cf", "Zl", "Zp"):
            gbp[cp] = "Control"; continue
        # --- Extend: nonspacing + enclosing marks ---
        if cat in ("Mn", "Me"):
            gbp[cp] = "Extend"; continue
        # --- SpacingMark: spacing combining marks ---
        if cat == "Mc":
            gbp[cp] = "SpacingMark"; continue
        # Prepend: no unicodedata signal exists — silently absent.
    return gbp, extpict


# ── UAX #29 GB1..GB999 segmenter, parameterised by the tables ──────────────
def graphemes(text, gbp, extpict, incb=None):
    """Extended grapheme cluster boundaries per UAX #29 (rev 43) rules."""
    if not text:
        return []
    incb = incb or {}
    P = lambda ch: gbp.get(ord(ch), "Other")           # noqa: E731
    I = lambda ch: incb.get(ord(ch), "None")           # noqa: E731

    def gb9c(i):
        """GB9c: Consonant [Extend|Linker]* Linker [Extend|Linker]* x Consonant."""
        if I(text[i]) != "Consonant":
            return False
        j, seen_linker = i - 1, False
        while j >= 0 and I(text[j]) in ("Extend", "Linker"):
            if I(text[j]) == "Linker":
                seen_linker = True
            j -= 1
        return seen_linker and j >= 0 and I(text[j]) == "Consonant"

    out, cur = [], [text[0]]
    ri_run = 1 if P(text[0]) == "Regional_Indicator" else 0
    for i in range(1, len(text)):
        a, b = text[i - 1], text[i]
        pa, pb = P(a), P(b)
        brk = True
        if pa == "CR" and pb == "LF":
            brk = False                                        # GB3
        elif pa in ("Control", "CR", "LF") or pb in ("Control", "CR", "LF"):
            brk = True                                         # GB4/GB5
        elif pa == "L" and pb in ("L", "V", "LV", "LVT"):
            brk = False                                        # GB6
        elif pa in ("LV", "V") and pb in ("V", "T"):
            brk = False                                        # GB7
        elif pa in ("LVT", "T") and pb == "T":
            brk = False                                        # GB8
        elif pb in ("Extend", "ZWJ"):
            brk = False                                        # GB9
        elif pb == "SpacingMark":
            brk = False                                        # GB9a
        elif pa == "Prepend":
            brk = False                                        # GB9b
        elif pa == "ZWJ" and ord(b) in extpict:
            # GB11: ExtPict Extend* ZWJ x ExtPict — walk back over Extend*
            j = i - 2
            while j >= 0 and P(text[j]) == "Extend":
                j -= 1
            brk = not (j >= 0 and ord(text[j]) in extpict)
        elif pa == "Regional_Indicator" and pb == "Regional_Indicator":
            brk = (ri_run % 2) == 0                            # GB12/GB13
        elif gb9c(i):
            brk = False                                        # GB9c
        if pb == "Regional_Indicator":
            ri_run = ri_run + 1 if (pa == "Regional_Indicator" and not brk) else 1
        else:
            ri_run = 0
        if brk:
            out.append("".join(cur)); cur = [b]
        else:
            cur.append(b)
    out.append("".join(cur))
    return out


def load_conformance(path):
    """GraphemeBreakTest.txt → [(text, [clusters])]."""
    cases = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if not line:
                continue
            # '÷ 0061 × 0301 ÷'  → clusters split on ÷
            toks = line.split()
            clusters, cur = [], []
            for t in toks:
                if t == "÷":                      # break
                    if cur:
                        clusters.append("".join(cur)); cur = []
                elif t == "×":                    # no break
                    pass
                else:
                    cur.append(chr(int(t, 16)))
            if cur:
                clusters.append("".join(cur))
            if clusters:
                cases.append(("".join(clusters), clusters))
    return cases


def main():
    ucd = sys.argv[1]
    t_gbp, t_ext, t_incb = true_tables(ucd)
    d_gbp, d_ext = derived_tables()
    d_incb = {}          # InCB is NOT exposed by unicodedata either

    print(f"interpreter unidata_version = {unicodedata.unidata_version}")
    print(f"TRUE    : {len(t_gbp)} cps carry a GBP; "
          f"{len(t_ext)} Extended_Pictographic")
    print(f"DERIVED : {len(d_gbp)} cps carry a GBP; "
          f"{len(d_ext)} Extended_Pictographic")

    # ---- per-codepoint disagreement ----
    mism = Counter()
    n_bad = 0
    for cp in range(MAX_CP):
        tv, dv = t_gbp.get(cp, "Other"), d_gbp.get(cp, "Other")
        if tv != dv:
            n_bad += 1
            mism[(tv, dv)] += 1
    print(f"\n== per-codepoint GBP disagreement: {n_bad} codepoints ==")
    print(f"{'TRUE':<20} {'DERIVED':<20} {'count':>8}")
    for (tv, dv), n in mism.most_common(20):
        print(f"{tv:<20} {dv:<20} {n:>8}")

    ext_missing = len(t_ext - d_ext)
    print(f"\nExtended_Pictographic derivable? "
          f"{'NO' if not d_ext else 'partial'} — {ext_missing} cps unobtainable")

    # ---- official conformance suite ----
    cases = load_conformance(f"{ucd}/GraphemeBreakTest.txt")
    print(f"\n== UAX #29 conformance ({len(cases)} official cases) ==")
    for name, g, e, ic in (("TRUE tables   ", t_gbp, t_ext, t_incb),
                           ("DERIVED tables", d_gbp, d_ext, d_incb)):
        ok = sum(1 for text, exp in cases if graphemes(text, g, e, ic) == exp)
        pct = 100.0 * ok / len(cases)
        print(f"  {name}: {ok}/{len(cases)} pass  ({pct:.2f}%)")

    # ---- where DERIVED fails, bucketed by cause ----
    causes = Counter()
    for text, exp in cases:
        if graphemes(text, d_gbp, d_ext, d_incb) == exp:
            continue
        cps = [ord(c) for c in text]
        if any(t_incb.get(c) == "Linker" for c in cps):
            causes["InCB / GB9c (Indic conjunct)"] += 1
        elif any(c in t_ext for c in cps):
            causes["Extended_Pictographic (GB11 emoji ZWJ)"] += 1
        elif any(t_gbp.get(c) == "Prepend" for c in cps):
            causes["Prepend"] += 1
        else:
            causes["other (Extend/SpacingMark/Control edge)"] += 1
    print("\n== DERIVED conformance failures by cause ==")
    for c, n in causes.most_common():
        print(f"  {n:>4}  {c}")

    # ---- vendoring cost, if we vendor instead ----
    def n_ranges(pred):
        r, prev = 0, False
        for cp in range(MAX_CP):
            cur = pred(cp)
            if cur and not prev:
                r += 1
            prev = cur
        return r
    hangul_free = {cp: p for cp, p in t_gbp.items() if p not in ("LV", "LVT")}
    print("\n== vendoring cost ==")
    print(f"  full GBP ranges                     : "
          f"{n_ranges(lambda c: c in t_gbp)}")
    print(f"  GBP minus arithmetic-derivable LV/LVT: "
          f"{n_ranges(lambda c: c in hangul_free)}")
    print(f"  Extended_Pictographic ranges         : "
          f"{n_ranges(lambda c: c in t_ext)}")
    # 2x uint32 + 1 byte tag per range
    rr = n_ranges(lambda c: c in hangul_free) + n_ranges(lambda c: c in t_ext)
    print(f"  packed (lo:u32, hi:u32, tag:u8) x {rr} = {rr * 9} bytes")


if __name__ == "__main__":
    main()
