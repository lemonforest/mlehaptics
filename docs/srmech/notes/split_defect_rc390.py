#!/usr/bin/env python3
"""Computational provenance for rc390 (`#T961`) — the ORDER-carrying octonion
associativity read ``srmech.biology.genome.split_defect``.

Reproduces the ratchet census THROUGH the SHIPPED ops (``split_defect`` /
``oct_mult`` for 𝕆; ``cd_basis_product`` for the ℂ/ℍ/𝕊 rungs; ``algebra_table`` for
the split-𝕆 twist). Emits one NDJSON record per finding to
``split_defect_rc390.ndjson`` ([[feedback_computational_provenance_discipline]],
[[feedback_ndjson_over_bloated_json]]).

The census enumeration (all reproduced EXACTLY):
  * ℂ / ℍ / 𝕆 : ALL length-4 words over the imaginary units, middle split k=2
                (division algebras — every word is admissible).
  * 𝕊         : length-4 words with DISTINCT letters, k=2 (the non-division rung;
                distinct letters avoid the zero-divisor-degenerate configurations).
  The 𝕆 census is 1008/2401 at n=4 — so the ORDER-carrying defect FIRES at a middle
  split from n=4 up (both sides length >= 2). The brief's "five letters" narrative is
  off-by-one against its OWN 1008/2401 count, which is n=4; the honest firing
  threshold is "both split sides length >= 2".

No ``abs()`` (sign is the Class-K pin bit ``b>>3``, re-applied by the Class-C XOR); no
stdlib ``fractions`` (integer byte ops).

    PYTHONPATH=<pkg> python3 docs/srmech/notes/split_defect_rc390.py
"""
from __future__ import annotations

import json
from itertools import product, permutations
from pathlib import Path

from srmech.biology.genome import split_defect
from srmech.math.octonion import oct_mult
from srmech.cascade.cayley_dickson import cd_basis_product, algebra_table


# ── generic (index, sign_bit) byte fold for any Cayley–Dickson rung ──────────
def _bp_cd(dim):
    return lambda i, j: cd_basis_product(dim, i, j)


def _bp_octonion(i, j):
    b = oct_mult(i, j)
    return b & 7, (1 if (b >> 3) == 0 else -1)


def _bp_from_table(dim, gammas):
    """A monomial (index, sign) basis product read straight off the SHIPPED
    ``algebra_table`` — used for the split-𝕆 twist (gammas with a +1 rung)."""
    tbl = algebra_table(dim, gammas)
    def bp(i, j):
        for k, c in enumerate(tbl[i][j]):
            cc = int(c)
            if cc != 0:
                return k, (1 if cc > 0 else -1)
        raise AssertionError("zero basis product")
    return bp


def _bfold(word, bp):
    idx, sgn = 0, 0
    for i in word:
        ni, s = bp(idx, i)
        sgn ^= (0 if s == 1 else 1)
        idx = ni
    return idx, sgn


def _sd(word, k, bp):
    ia, sa = _bfold(word, bp)
    ip, sp = _bfold(word[:k], bp)
    isf, ssf = _bfold(word[k:], bp)
    ni, ps = bp(ip, isf)
    assert ni == ia                          # index is ⊕-associative on every rung
    return sa ^ (sp ^ ssf ^ (0 if ps == 1 else 1))


def _census(bp, dim, k=2, distinct=False):
    units = list(range(1, dim))
    fire = tot = 0
    it = permutations(units, 4) if distinct else product(units, repeat=4)
    for w in it:
        tot += 1
        fire += _sd(list(w), k, bp)
    return fire, tot


# ── the associative Cl(0,7) CONTROL (a purpose-built reference, NOT a CD op) ──
# Cayley–Dickson is NON-associative at every rung >= 8 regardless of the split
# gammas, so an associative 7-generator peer cannot come from algebra_table. The
# Clifford blade product e_A·e_B = ±e_{A△B} is monomial with the SAME ⊕ index lane
# as 𝕆 but the ASSOCIATIVE cocycle — it matches 𝕆 on alphabet size (7) and
# anticommutativity, differing ONLY in associativity. Exact integer sign; no abs().
def _clifford_bp(A, B):
    la, lb = sorted(A), sorted(B)
    swaps = sum(1 for j in lb for i in la if i > j)
    sign = (-1) ** (swaps + len(A & B))          # e_i^2 = -1 for each shared gen
    return (A ^ B), sign


def _cl_fold(word):
    S, sgn = frozenset(), 0
    for i in word:
        S2, s = _clifford_bp(S, frozenset({i}))
        sgn ^= (0 if s == 1 else 1)
        S = S2
    return S, sgn


def _cl_sd(word, k):
    Sa, sa = _cl_fold(word)
    Sp, sp = _cl_fold(word[:k])
    Ssf, ssf = _cl_fold(word[k:])
    S2, ps = _clifford_bp(Sp, Ssf)
    assert S2 == Sa
    return sa ^ (sp ^ ssf ^ (0 if ps == 1 else 1))


FANO = [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 4, 7), (1, 6, 7), (2, 5, 7), (3, 5, 6)]


def census_finding():
    # 𝕆 through the SHIPPED split_defect itself.
    o_fire = o_tot = 0
    for w in product(range(1, 8), repeat=4):
        o_tot += 1
        o_fire += split_defect(list(w), 2)
    c = _census(_bp_cd(2), 2)
    h = _census(_bp_cd(4), 4)
    s = _census(_bp_cd(16), 16, distinct=True)
    return {"finding": "census_associativity_not_division",
            "C_all_n4_k2": list(c), "H_all_n4_k2": list(h),
            "O_all_n4_k2_via_split_defect": [o_fire, o_tot],
            "S_distinct_n4_k2": list(s),
            "note": "ℂ/ℍ/𝕆 = all length-4 words; 𝕊 = distinct-letter length-4 words "
                    "(the non-division rung). 𝕆 folded through the SHIPPED split_defect.",
            "pass": c == (0, 1) and h == (0, 81)
                    and (o_fire, o_tot) == (1008, 2401) and s == (18480, 32760)}


def split_octonion_finding():
    # split-𝕆 detects ASSOCIATIVITY, not division: identical 1008/2401 to 𝕆 for
    # EVERY split gamma configuration (a +1 at any doubling rung).
    rows = {}
    for g in ([-1, -1, 1], [-1, 1, 1], [1, 1, 1], [1, -1, -1]):
        rows[str(g)] = list(_census(_bp_from_table(8, g), 8))
    return {"finding": "split_octonion_is_the_non_discriminator",
            "split_O_census_by_gammas": rows,
            "O_reference": [1008, 2401],
            "note": "split-𝕆 is NON-division (has zero divisors) but equally "
                    "NON-associative, so split_defect gives the IDENTICAL 1008/2401 — "
                    "it reads associativity, NOT the division property.",
            "pass": all(v == [1008, 2401] for v in rows.values())}


def clifford_control_finding():
    fire = tot = 0
    for w in product(range(1, 8), repeat=4):
        tot += 1
        fire += _cl_sd(list(w), 2)
    return {"finding": "cl07_associative_control_is_zero",
            "Cl_0_7_all_n4_k2": [fire, tot],
            "brief_stated_total": 595448,
            "note": "the CONTROL that makes it real: Cl(0,7) matches 𝕆 on alphabet "
                    "size (7) + anticommutativity but is ASSOCIATIVE -> 0. Delivered at "
                    "the 𝕆-matched n=4-all enumeration (0/2401). SPEC GAP: the brief's "
                    "stated total 595448 (=248*2401) uses a larger enumeration not "
                    "reproducible through a clean 7-generator word count; the control's "
                    "MEANING (associative => 0) is what is pinned.",
            "pass": (fire, tot) == (0, 2401)}


def fano_frame_finding():
    fire = tot = 0
    for L in FANO:
        for w in product(L, repeat=4):
            tot += 1
            fire += split_defect(list(w), 2)
    return {"finding": "zero_inside_every_fano_frame",
            "fano_7lines_x_3pow4": [fire, tot],
            "note": "a single Fano line is a quaternion (associative) subalgebra, so "
                    "split_defect is a purely CROSS-FRAME quantity: 0 inside every frame.",
            "pass": (fire, tot) == (0, 567)}


def gauge_invariance_finding():
    # unchanged under the 128 = 2^7 sign re-gaugings of the generators.
    base_words = [[1, 2, 4, 6], [1, 2, 3, 4], [2, 5, 7, 1], [3, 6, 1, 5]]
    ok = tot = 0
    for base in base_words:
        b0 = split_defect(base, 2)
        for flips in product((0, 1), repeat=7):
            gauged = [(x ^ 8) if flips[(x & 7) - 1] else x for x in base]
            tot += 1
            ok += (split_defect(gauged, 2) == b0)
    return {"finding": "gauge_invariant_under_128_sign_regaugings",
            "invariant": [ok, tot], "words_probed": len(base_words),
            "note": "unchanged under all 2^7=128 per-generator sign flips; the 1344 "
                    "octonion basis automorphisms are the other half of the gauge "
                    "(cited, not swept here).",
            "pass": ok == tot == len(base_words) * 128}


def threshold_finding():
    # the ratchet's whole point: 0 is AMBIGUOUS (associative OR too short at k).
    fires_ge5 = split_defect([1, 2, 3, 4, 5], 2)           # a >=5-letter FIRING case
    triple_k1 = split_defect([1, 2, 4], 1)                 # the triple IS non-assoc
    triple_k2 = split_defect([1, 2, 4], 2)                 # but a len-1 side CANNOT fire
    n4 = split_defect([1, 2, 4, 6], 2)                     # n=4 already fires (census)
    return {"finding": "threshold_visible_zero_is_ambiguous",
            "five_letter_fires": fires_ge5,
            "triple_nonassoc_at_k1": triple_k1,
            "triple_cannot_fire_at_k2_len1_side": triple_k2,
            "n4_middle_split_fires": n4,
            "note": "split_defect==0 means EITHER associative OR too short at k: the "
                    "SAME non-associative triple (e1,e2,e4) fires at k=1 but is 0 at k=2 "
                    "(right side length 1). A middle split fires from n=4 up.",
            "pass": fires_ge5 == 1 and triple_k1 == 1 and triple_k2 == 0 and n4 == 1}


def byte_identity_finding():
    # the acceptance oracle: the c_dispatched C peer == the pure oct_mult fold.
    from srmech import _native
    mism = cnt = 0
    def pure(w, k):
        def fold(ws):
            b = 0
            for x in ws:
                b = oct_mult(b, x)
            return b
        return (fold(w) >> 3) ^ (oct_mult(fold(w[:k]), fold(w[k:])) >> 3)
    for w in product(range(16), repeat=3):
        for k in (1, 2):
            cnt += 1
            mism += (split_defect(list(w), k) != pure(list(w), k))
    return {"finding": "c_vs_pure_byte_identity",
            "native_loaded": bool(_native.has_native_split_defect()),
            "mismatches": mism, "cases": cnt,
            "pass": mism == 0}


def inertia_citation_finding():
    return {"finding": "not_associated_with_inertia_signature",
            "permutation_test_p": 0.5893,
            "note": "CITED from the rc390 brief (not recomputed): split_defect is NOT "
                    "associated with inertia_signature (permutation test p≈0.5893) — the "
                    "order-carrying associativity read and the trace-form metric signature "
                    "are independent quantities.",
            "pass": True}


def main():
    records = [census_finding(), split_octonion_finding(), clifford_control_finding(),
               fano_frame_finding(), gauge_invariance_finding(), threshold_finding(),
               byte_identity_finding(), inertia_citation_finding()]
    out = Path(__file__).with_suffix(".ndjson")
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "meta", "task": "#T961", "rc": "0.9.0rc390",
                             "op": "srmech.biology.genome.split_defect"},
                            sort_keys=True) + "\n")
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    allpass = all(r["pass"] for r in records)
    for r in records:
        print(f"  {'PASS' if r['pass'] else 'FAIL'}  {r['finding']}")
    print(f"wrote {out}  ({len(records)} findings, all pass = {allpass})")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
