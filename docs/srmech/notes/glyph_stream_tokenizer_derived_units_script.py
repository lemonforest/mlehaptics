#!/usr/bin/env python3
"""Q2's real question: if we emit a glyph stream with NO word decision, can the
UNITS be DERIVED from the data's own structure (rc272's "partition by the
DATA'S OWN STRUCTURE"), instead of picked?

The classical derivation is Harris's hypothesis: a boundary sits at a local
MAXIMUM of successor (branching) entropy — after a complete unit, many things
can follow; mid-unit, few can. If that works, derived units are viable and
assumptions 1/3/4/5/6 all delete at once. If it does not work, the honest
answer is that units are not derivable at corpus scale and the design must say
so.

This test HAS a ground truth and CAN come back FALSE: in space-separated
scripts the space positions ARE the boundaries. We hide the spaces, run
branching entropy over the resulting glyph stream, and score the recovered
boundaries against the true ones (precision / recall / F1) against a
frequency-matched RANDOM baseline.

A result near the random baseline falsifies derived-unit segmentation.

Usage: python3 glyph_stream_tokenizer_derived_units_script.py <corpus> <ucd>
No abs(); no external libraries.
"""
from __future__ import annotations

import math
import os
import random
import sys
import unicodedata
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from glyph_stream_tokenizer_q1_tables_script import (       # noqa: E402
    graphemes, true_tables,
)


def build_stream(text, gbp, ext, incb):
    """Glyph stream + the TRUE boundary set, then spaces removed.

    Returns (glyphs_without_space, true_boundary_positions).
    A boundary is an index i meaning 'a unit ends before position i'.
    """
    gl = graphemes(unicodedata.normalize("NFC", text), gbp, ext, incb)
    out, bounds = [], set()
    for g in gl:
        if g.isspace():
            if out:
                bounds.add(len(out))
        else:
            out.append(g)
    bounds.discard(0)
    return out, bounds


def branching_entropy(stream, n=3):
    """H(next | previous n glyphs), estimated by counting on the stream."""
    succ = defaultdict(Counter)
    for i in range(len(stream) - n):
        succ[tuple(stream[i:i + n])][stream[i + n]] += 1
    ent = {}
    for ctx, c in succ.items():
        tot = sum(c.values())
        ent[ctx] = -sum((v / tot) * math.log2(v / tot) for v in c.values())
    return ent


def predict_boundaries(stream, ent, n=3):
    """Harris: boundary where entropy RISES then falls (a local maximum).

    Comparison is ordered (Class-K pin-slot style: which side is larger),
    never a magnitude strip.
    """
    h = []
    for i in range(len(stream) - n):
        h.append(ent.get(tuple(stream[i:i + n]), 0.0))
    pred = set()
    for i in range(1, len(h) - 1):
        if h[i] > h[i - 1] and h[i] >= h[i + 1]:
            pred.add(i + n)          # unit ends after the peak context
    return pred


def score(pred, true, n_positions):
    tp = len(pred & true)
    prec = tp / max(len(pred), 1)
    rec = tp / max(len(true), 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return prec, rec, f1


def random_baseline(n_pred, true, n_positions, seed=20260719):
    """Same NUMBER of boundaries, placed at random — the honest null."""
    rng = random.Random(seed)
    pred = set(rng.sample(range(1, n_positions), min(n_pred, n_positions - 1)))
    return score(pred, true, n_positions)


def run(label, text, gbp, ext, incb, n=3):
    stream, true = build_stream(text, gbp, ext, incb)
    if len(stream) < 2000 or not true:
        print(f"{label:<12} SKIP (too little text)")
        return
    ent = branching_entropy(stream, n)
    pred = predict_boundaries(stream, ent, n)
    p, r, f = score(pred, true, len(stream))
    bp, br, bf = random_baseline(len(pred), true, len(stream))
    lift = f / max(bf, 1e-12)
    print(f"{label:<12}{len(stream):>8}{len(true):>8}{len(pred):>8}"
          f"{p:>8.3f}{r:>8.3f}{f:>8.3f}{bf:>10.3f}{lift:>8.2f}x")
    return f, bf, lift


def main():
    corpus_dir, ucd_dir = sys.argv[1], sys.argv[2]
    gbp, ext, incb = true_tables(ucd_dir)
    texts = {}
    for fn in sorted(os.listdir(corpus_dir)):
        if fn.endswith(".txt"):
            with open(os.path.join(corpus_dir, fn), encoding="utf-8") as fh:
                t = fh.read()
            if len(t) > 3000:
                texts[fn[:-4]] = t

    print("=" * 78)
    print("Q2 — can UNITS be DERIVED from the glyph stream? (Harris branching")
    print("entropy vs the TRUE space-boundaries, against a random baseline)")
    print("=" * 78)
    for n in (2, 3, 4):
        print(f"\n--- context order n={n} ---")
        print(f"{'lang':<12}{'glyphs':>8}{'true b':>8}{'pred b':>8}"
              f"{'prec':>8}{'rec':>8}{'F1':>8}{'rand F1':>10}{'lift':>8}")
        for code in ("en", "tr", "ru", "el", "haw"):     # space-separated only
            if code in texts:
                run(code, texts[code], gbp, ext, incb, n)
    print("\nOnly space-separated scripts are scored — they are the ones with a")
    print("ground truth. A lift near 1.00x means branching entropy has found")
    print("nothing a random guess of the same density would not find.")


if __name__ == "__main__":
    main()
