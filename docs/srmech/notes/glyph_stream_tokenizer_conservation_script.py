#!/usr/bin/env python3
"""Cross-cutting check: does GLYPH granularity change the F1253 conservation
curve — the heavy-tailed distribution on which `conserved_core` DECLINES to
derive a k?

F1253/F1254 (CHANGELOG 0.9.0rc278) measured, at WORD granularity over the full
simplewiki corpus (1,100,189 ids):

    singleton 64.6% | >=2 35.4% | >=5 14.5% | >=10 8.4%
    | >=25 4.3% | >=50 2.7% | >=100 1.7%

"The successive ratios decay SMOOTHLY — a heavy-tailed, near-power-law shape
with NO clean gap. A scale-free distribution has no characteristic scale and
therefore no natural antimode, so k may not be structurally derivable on the
real corpus at all."

The question this script asks: is that a property of the LANGUAGE, or an
artefact of the word-granularity FRONT DOOR? A tokenizer that emits ~89%
singleton types on scriptio-continua text (measured, section A) is
manufacturing the heavy tail it then fails to find a threshold in.

This is a FALSIFIABLE check and it can come back either way:
  - if the glyph curve is ALSO smooth/scale-free -> the decline is a real
    property of language, granularity is irrelevant, F1253 stands untouched;
  - if the glyph curve develops a knee -> the decline was partly a front-door
    artefact, and that is a finding about the tokenizer, not about language.

Usage: python3 glyph_stream_tokenizer_conservation_script.py <corpus> <ucd>
No abs(); no external libraries.
"""
from __future__ import annotations

import os
import sys
import unicodedata
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "python"))

from glyph_stream_tokenizer_q1_tables_script import (       # noqa: E402
    graphemes, true_tables,
)
from srmech.amsc.text import tokenize                        # noqa: E402

CUTS = (1, 2, 5, 10, 25, 50, 100)


def curve(seq):
    """The conserved-core input curve: share of TYPES at each >=n cut."""
    c = Counter(seq)
    n_types = len(c)
    vals = list(c.values())
    out = {}
    for cut in CUTS:
        out[cut] = sum(1 for v in vals if v >= cut) / max(n_types, 1)
    return n_types, out


def ratios(cv):
    """Successive ratios between adjacent cuts — smooth decay => no antimode.

    Cuts where the DENOMINATOR bucket is empty are DEGENERATE (the curve has
    run out of types, not found a knee) and are excluded rather than allowed
    to manufacture an enormous ratio. Returns (ratios, n_degenerate).
    """
    ks, out, degen = list(CUTS), [], 0
    for i in range(len(ks) - 1):
        lo = cv[ks[i + 1]]
        if lo <= 0.0:
            degen += 1
            continue
        out.append(cv[ks[i]] / lo)
    return out, degen


def report(label, seq):
    n_types, cv = curve(seq)
    print(f"\n{label}  ({len(seq):,} tokens, {n_types:,} types)")
    print("   " + "".join(f">={c:<8}" for c in CUTS))
    print("   " + "".join(f"{100 * cv[c]:<10.1f}" for c in CUTS))
    r, degen = ratios(cv)
    sing = 100.0 * (1.0 - cv[2])
    print(f"   singleton share = {sing:.1f}%")
    print("   successive ratios: " + "  ".join(f"{x:.2f}" for x in r)
          + (f"   [{degen} degenerate cut(s) excluded]" if degen else ""))
    if len(r) < 2:
        print("   VERDICT: curve exhausted — too few non-empty cuts to judge")
        return cv, r, None
    # a knee = one ratio markedly larger than its neighbours.
    # Class-K pin-slot: compare via ordered max/min, never abs().
    spread = max(r) / min(r)
    print(f"   max/min ratio spread = {spread:.2f}   "
          f"({'KNEE-LIKE' if spread > 3.0 else 'SMOOTH (scale-free)'})")
    return cv, r, spread


def main():
    corpus_dir, ucd_dir = sys.argv[1], sys.argv[2]
    gbp, ext, incb = true_tables(ucd_dir)
    texts = {}
    for fn in sorted(os.listdir(corpus_dir)):
        if fn.endswith(".txt"):
            with open(os.path.join(corpus_dir, fn), encoding="utf-8") as fh:
                t = fh.read()
            if len(t) > 300:
                texts[fn[:-4]] = t

    print("=" * 74)
    print("F1253 conservation curve — WORD vs GLYPH granularity")
    print("=" * 74)
    print("\nreference, measured at WORD granularity on full simplewiki")
    print("(CHANGELOG 0.9.0rc278, 1,100,189 ids):")
    print("   >=1       >=2       >=5       >=10      >=25      >=50      >=100")
    print("   100.0     35.4      14.5      8.4       4.3       2.7       1.7")
    ref = {1: 1.0, 2: .354, 5: .145, 10: .084, 25: .043, 50: .027, 100: .017}
    rr, _ = ratios(ref)
    print(f"   singleton share = {100.0 * (1.0 - ref[2]):.1f}%")
    print("   successive ratios: " + "  ".join(f"{x:.2f}" for x in rr))
    print(f"   max/min ratio spread = {max(rr) / min(rr):.2f}  (SMOOTH)")

    # English alone — the closest analogue to simplewiki (monolingual)
    en = texts.get("en", "")
    if en:
        print("\n" + "-" * 74)
        print("ENGLISH ONLY (closest analogue to the monolingual simplewiki store)")
        report("  WORD ", tokenize(en, stoplist=None))
        report("  GLYPH", graphemes(unicodedata.normalize("NFC", en),
                                    gbp, ext, incb))

    allt = "\n".join(texts.values())
    print("\n" + "-" * 74)
    print(f"ALL {len(texts)} LANGUAGES")
    report("  WORD ", tokenize(allt, stoplist=None))
    report("  GLYPH", graphemes(unicodedata.normalize("NFC", allt),
                                gbp, ext, incb))

    # scriptio-continua subset — where the word front door is worst
    cont = "\n".join(texts[k] for k in ("zh", "ja", "th", "km", "lo", "my")
                     if k in texts)
    if cont:
        print("\n" + "-" * 74)
        print("SCRIPTIO-CONTINUA SUBSET (zh/ja/th/km/lo/my)")
        report("  WORD ", tokenize(cont, stoplist=None))
        report("  GLYPH", graphemes(unicodedata.normalize("NFC", cont),
                                    gbp, ext, incb))


if __name__ == "__main__":
    main()
