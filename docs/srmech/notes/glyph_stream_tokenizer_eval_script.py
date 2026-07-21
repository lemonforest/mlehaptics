#!/usr/bin/env python3
"""Glyph-stream tokenizer design spike — the evaluation harness.

Generating code for the multi-script table, the Q1 real-text error rate, and
the Q2 scale estimate in `glyph_stream_tokenizer_design.md`.

Sections
--------
A  multi-script behaviour   : current `tokenize` vs the proposed glyph stream
B  Q1 real-text error       : DERIVED (unicodedata-only) vs TRUE (UCD) grapheme
                              segmentation over real Wikipedia prose
C  Q2 scale                 : types / tokens / co-occurrence edges / encode time
                              at WORD vs GLYPH granularity, + extrapolation to
                              the measured field store

Corpus: per-language Wikipedia extracts (plain text, CC-BY-SA), fetched by
`glyph_stream_tokenizer_fetch_corpus_script.py`. Real prose, not toy strings.

Usage:
  python3 glyph_stream_tokenizer_eval_script.py <corpus_dir> <ucd_dir>

No abs(); sign handling is Class-K pin-slot + Class-C reorientation.
No external libraries.
"""
from __future__ import annotations

import os
import sys
import time
import unicodedata
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "python"))

from glyph_stream_tokenizer_q1_tables_script import (       # noqa: E402
    derived_tables, graphemes, true_tables,
)
from srmech.amsc.text import cooccurrence_edges, tokenize    # noqa: E402


# ── the proposed primitive: the glyph stream ───────────────────────────────
def glyph_stream(text, gbp, extpict, incb, normalize=True):
    """The DESIGN's front door: NFC → extended grapheme clusters. No word
    decision, no casefold, no stoplist, no length floor."""
    if normalize:
        text = unicodedata.normalize("NFC", text)
    return graphemes(text, gbp, extpict, incb)


def load_corpus(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"):
            continue
        with open(os.path.join(d, fn), encoding="utf-8") as fh:
            t = fh.read()
        if len(t) > 300:
            out[fn[:-4]] = t
    return out


LANG_NAME = {
    "ar": "Arabic", "bi": "Bislama", "bn": "Bengali", "el": "Greek",
    "en": "English", "haw": "Hawaiian", "he": "Hebrew", "hi": "Devanagari",
    "ja": "Japanese", "km": "Khmer", "ko": "Korean", "lo": "Lao",
    "my": "Burmese", "ru": "Russian", "ta": "Tamil", "th": "Thai",
    "tr": "Turkish", "zh": "Chinese",
}
CONTINUA = {"zh", "ja", "th", "km", "lo", "my", "bo"}


def section_a(corpus, gbp, extpict, incb):
    print("=" * 78)
    print("A. MULTI-SCRIPT BEHAVIOUR — current tokenize vs proposed glyph stream")
    print("=" * 78)
    print(f"{'lang':<11}{'chars':>8}{'cur.tok':>9}{'cur.typ':>9}"
          f"{'glyphs':>8}{'gly.typ':>8}{'longest cur. token':>22}")
    rows = []
    for code, text in sorted(corpus.items()):
        toks = tokenize(text, stoplist=None)
        gl = glyph_stream(text, gbp, extpict, incb)
        longest = max((len(t) for t in toks), default=0)
        rows.append((code, len(text), len(toks), len(set(toks)),
                     len(gl), len(set(gl)), longest))
        print(f"{LANG_NAME.get(code, code):<11}{len(text):>8}{len(toks):>9}"
              f"{len(set(toks)):>9}{len(gl):>8}{len(set(gl)):>8}{longest:>22}")
    print("\n  'longest cur. token' is the scriptio-continua tell: a whole "
          "run of\n  letters with no delimiter returns as ONE token.")
    return rows


def section_a2(gbp, extpict, incb):
    """The named traps, worked one by one."""
    print("\n" + "=" * 78)
    print("A2. THE NAMED TRAPS — worked examples")
    print("=" * 78)
    cases = [
        ("1 scriptio continua", "语言是人类交流的工具"),
        ("1 scriptio continua", "ภาษาไทยเป็นภาษาราชการ"),
        ("2 Turkish upper",     "IŞIK"),
        ("2 Turkish lower",     "ışık"),
        ("2 Turkish dotted-I",  "İSTANBUL"),
        ("2 Greek upper",       "ΓΛΩΣΣΑ"),
        ("2 Greek lower",       "γλώσσα"),
        ("3 okina U+02BB",      "ʻokina"),
        ("3 okina U+2019",      "’okina"),
        ("3 okina medial 02BB", "Hawaiʻi"),
        ("3 okina medial 2019", "Hawai’i"),
        ("4 min-len ASCII",     "a cat"),
        ("4 min-len CJK",       "中 国"),
        ("6 function words",    "the cat sat on a mat"),
        ("emoji family ZWJ",    "👨‍👩‍👧‍👦"),
        ("emoji flag VU",       "🇻🇺"),
        ("emoji keycap",        "1️⃣"),
        ("Korean jamo NFC",     "한국어"),
        ("Devanagari conjunct", "क्षि"),
    ]
    print(f"{'trap':<22}{'input':<24}{'current tokenize':<30}{'glyph stream'}")
    for label, s in cases:
        cur = tokenize(s, stoplist=None)
        gl = glyph_stream(s, gbp, extpict, incb)
        print(f"{label:<22}{s!r:<24}{str(cur):<30}{gl}")
    print("\n  NOTE trap 3: U+02BB (Lm) is ALREADY handled correctly by the")
    print("  current L/M rule. The real okina failure is the U+2019 homoglyph,")
    print("  which _APOS maps to \"'\" and _emit's strip(\"'\") then DELETES")
    print("  word-initially. Correcting the brief's premise.")
    print("  NOTE trap 2: casefold DOES unify Greek final sigma (ς→σ).")
    print("  The real Greek break is uppercase accent loss (ΓΛΩΣΣΑ≠γλώσσα).")


def section_b(corpus, gbp, extpict, incb, d_gbp, d_ext, d_incb):
    print("\n" + "=" * 78)
    print("B. Q1 — DERIVED (unicodedata-only) vs TRUE (UCD) on REAL prose")
    print("=" * 78)
    print(f"{'lang':<11}{'glyphs(TRUE)':>13}{'glyphs(DERIV)':>14}"
          f"{'mismatched':>12}{'err %':>9}")
    tot_t = tot_bad = 0
    for code, text in sorted(corpus.items()):
        t = glyph_stream(text, gbp, extpict, incb)
        d = glyph_stream(text, d_gbp, d_ext, d_incb)
        # count clusters that differ (walk both, compare boundary offsets)
        bt, off = set(), 0
        for g in t:
            off += len(g); bt.add(off)
        bd, off = set(), 0
        for g in d:
            off += len(g); bd.add(off)
        bad = len(bt ^ bd)
        tot_t += len(t); tot_bad += bad
        pct = 100.0 * bad / max(len(t), 1)
        print(f"{LANG_NAME.get(code, code):<11}{len(t):>13}{len(d):>14}"
              f"{bad:>12}{pct:>8.4f}%")
    print(f"{'TOTAL':<11}{tot_t:>13}{'':>14}{tot_bad:>12}"
          f"{100.0 * tot_bad / max(tot_t, 1):>8.4f}%")
    print("\n  Boundary-set symmetric difference — a disagreement counts once")
    print("  per differing boundary offset, in EITHER direction.")


def section_c(corpus, gbp, extpict, incb, window=5):
    print("\n" + "=" * 78)
    print("C. Q2 — SCALE at WORD vs GLYPH granularity")
    print("=" * 78)
    all_text = "\n".join(corpus.values())

    t0 = time.perf_counter()
    words = tokenize(all_text, stoplist=None)
    t_word = time.perf_counter() - t0

    t0 = time.perf_counter()
    glyphs = glyph_stream(all_text, gbp, extpict, incb)
    t_glyph = time.perf_counter() - t0

    print(f"corpus: {len(all_text)} chars across {len(corpus)} languages\n")
    print(f"{'':<16}{'tokens':>12}{'types':>10}{'tok/type':>10}{'segment s':>12}")
    for name, seq, dt in (("WORD", words, t_word), ("GLYPH", glyphs, t_glyph)):
        print(f"{name:<16}{len(seq):>12}{len(set(seq)):>10}"
              f"{len(seq) / max(len(set(seq)), 1):>10.1f}{dt:>12.3f}")

    print(f"\nco-occurrence (window={window}):")
    print(f"{'':<16}{'vocab':>10}{'edges':>12}{'density':>12}{'build s':>10}")
    stats = {}
    for name, seq in (("WORD", words), ("GLYPH", glyphs)):
        t0 = time.perf_counter()
        n, edges, weights = cooccurrence_edges([seq], window=window)[:3]
        dt = time.perf_counter() - t0
        dens = 2.0 * len(edges) / max(n * (n - 1), 1)
        stats[name] = (n, len(edges), dens, dt)
        print(f"{name:<16}{n:>10}{len(edges):>12}{dens:>12.5f}{dt:>10.3f}")

    # ---- extrapolation to the measured field store ----
    print("\n" + "-" * 78)
    print("EXTRAPOLATION to the measured simplewiki field store")
    print("  measured (word granularity): 1,100,189 types | 240,881 sections")
    print("                               | 336 MB | 11.1 min plasmid_extract")
    wt, gt = len(set(words)), len(set(glyphs))
    wtok, gtok = len(words), len(glyphs)
    type_ratio = gt / max(wt, 1)
    tok_ratio = gtok / max(wtok, 1)
    edge_ratio = stats["GLYPH"][1] / max(stats["WORD"][1], 1)
    print(f"\n  measured ratios on THIS corpus (glyph / word):")
    print(f"    types    {type_ratio:>8.4f}x")
    print(f"    tokens   {tok_ratio:>8.4f}x")
    print(f"    edges    {edge_ratio:>8.4f}x")
    print(f"    seg time {t_glyph / max(t_word, 1e-9):>8.4f}x")
    print(f"\n  projected field store at GLYPH granularity:")
    print(f"    types   1,100,189 -> {int(1100189 * type_ratio):,}")
    print(f"    turns  18,376,459 -> {int(18376459 * tok_ratio):,}")
    print(f"    size      323.7 MB -> {323.7 * edge_ratio:,.1f} MB "
          f"(edge-count-scaled)")
    print(f"    rebuild    11.1 min -> {11.1 * tok_ratio:,.1f} min "
          f"(token-count-scaled, segmentation only)")
    print("\n  CAVEAT: type_ratio is measured on an 18-language balanced")
    print("  corpus; simplewiki is ~monolingual English, where the glyph")
    print("  alphabet is far smaller. See the design note's bounding argument.")
    return stats, (type_ratio, tok_ratio, edge_ratio)


def main():
    corpus_dir, ucd_dir = sys.argv[1], sys.argv[2]
    corpus = load_corpus(corpus_dir)
    gbp, extpict, incb = true_tables(ucd_dir)
    d_gbp, d_ext = derived_tables()
    d_incb = {}
    section_a(corpus, gbp, extpict, incb)
    section_a2(gbp, extpict, incb)
    section_b(corpus, gbp, extpict, incb, d_gbp, d_ext, d_incb)
    section_c(corpus, gbp, extpict, incb)


if __name__ == "__main__":
    main()
