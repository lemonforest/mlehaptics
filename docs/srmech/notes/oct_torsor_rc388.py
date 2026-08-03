#!/usr/bin/env python3
"""Computational provenance for rc388 (`#T963`) — the octonion ℍ-torsor ops
``srmech.math.octonion.oct_torsor_act`` / ``oct_torsor_div``.

Reproduces the four ratchet points AND the 3+4/3+1+3 notebook correction THROUGH
the SHIPPED ops (oct_torsor_act / oct_torsor_div / oct_mult / oct_conjugate /
cd_mult / cd_basis). Emits one NDJSON record per finding to
``oct_torsor_rc388.ndjson`` ([[feedback_computational_provenance_discipline]],
[[feedback_ndjson_over_bloated_json]]).

No abs() (sign is the Class-K pin bit b>>3, re-applied by the Class-C XOR); no
stdlib ``fractions`` (these are integer byte ops).

    python3 tools/run  (from docs/srmech/python)  OR
    PYTHONPATH=<pkg> python3 docs/srmech/notes/oct_torsor_rc388.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from srmech.math.octonion import (
    oct_torsor_act, oct_torsor_div, oct_mult, oct_conjugate,
)
from srmech.cascade.cayley_dickson import cd_mult, cd_basis, cd_basis_product

# The 7 Fano lines = the 7 XOR-closed imaginary triples = the 7 quaternion
# subalgebras H_L = {e0, e_a, e_b, e_c}.
FANO = [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 4, 7), (1, 6, 7), (2, 5, 7),
        (3, 5, 6)]


def signed(idxs):
    return [i for i in idxs] + [i | 8 for i in idxs]


def seams():
    out = []
    for L in FANO:
        assert L[0] ^ L[1] == L[2]
        Hidx = [0] + list(L)
        Tidx = [i for i in range(8) if i not in Hidx]
        for e in Tidx:
            out.append((L, e, signed(Hidx), signed(Tidx)))
    return out


SEAMS = seams()


def ratchet1():
    act_ok = act_tot = land = solve = div_tot = 0
    hist: dict[int, int] = {}
    for _L, _e, H, T in SEAMS:
        Hs, Ts = set(H), set(T)
        for t in sorted(Ts):
            for g in sorted(Hs):
                act_tot += 1
                act_ok += oct_torsor_act(t, g) in Ts
        for t1 in sorted(Ts):
            for t2 in sorted(Ts):
                div_tot += 1
                g = oct_torsor_div(t1, t2)
                land += g in Hs
                solve += oct_torsor_act(t1, g) == t2
                n = sum(1 for gg in Hs if oct_torsor_act(t1, gg) == t2)
                hist[n] = hist.get(n, 0) + 1
    return {"finding": "ratchet1_closure_and_simple_transitivity",
            "act_closes": [act_ok, act_tot], "div_lands_in_H": [land, div_tot],
            "div_solves": [solve, div_tot],
            "orbit_histogram": {str(k): v for k, v in hist.items()},
            "denominated": "448 x 4 (28 seams, 7 distinct (H,T); T = H complement)",
            "pass": act_ok == act_tot == 1792 and land == solve == div_tot == 1792
                    and hist == {1: 1792}}


def ratchet2():
    law = naive = tot = 0
    for _L, _e, H, T in SEAMS:
        for t in sorted(set(T)):
            for g in sorted(set(H)):
                for h in sorted(set(H)):
                    tot += 1
                    lhs = oct_torsor_act(oct_torsor_act(t, g), h)
                    law += lhs == oct_torsor_act(t, oct_mult(h, g))
                    naive += lhs == oct_torsor_act(t, oct_mult(g, h))
    return {"finding": "ratchet2_law_AND_defect",
            "law_(t<|g)<|h==t<|(h.g)": [law, tot],
            "naive_t<|(g.h)": [naive, tot],
            "pass": law == tot == 14336 and naive == 8960}


def ratchet3():
    ok = tot = 0
    for _L, _e, H, T in SEAMS:
        for t in T:
            tot += 1
            ok += oct_conjugate(t) == t ^ 8 and (t & 7) != 0
    return {"finding": "ratchet3_conj_is_xor8_on_T",
            "conj==^8_and_idx!=0": [ok, tot], "pass": ok == tot == 224}


def ratchet4():
    be = sum(1 for a in range(16) for b in range(16)
             if oct_torsor_act(a, b) == oct_mult(a, b))
    rl = tot = 0
    for _L, _e, H, T in SEAMS:
        for t in T:
            for g in H:
                tot += 1
                rl += oct_torsor_act(t, g) == oct_mult(oct_conjugate(g), t)
    F = [[0 if cd_basis_product(8, xa, xb)[1] == 1 else 1 for xb in range(8)]
         for xa in range(8)]
    drift = 0
    for a in range(16):
        for b in range(16):
            xa, xb = a & 7, b & 7
            sign = (a >> 3) ^ (b >> 3) ^ F[xa][xb]
            drift += oct_mult(a, b) != ((sign << 3) | (xa ^ xb))
    return {"finding": "ratchet4_byte_exact_and_sign_from_cd_basis_product",
            "act==oct_mult": [be, 256], "R_g==L_conj(g)_on_T": [rl, tot],
            "sign_table_drift_from_cd_basis_product": drift,
            "pass": be == 256 and rl == tot == 1792 and drift == 0}


def correction_3plus4():
    ok = tot = 0
    first_escape = None
    for L in FANO:
        Hidx = [0] + list(L)
        Tidx = [i for i in range(8) if i not in Hidx]
        for e in Tidx:
            T3 = set(signed([i for i in Tidx if i != e]))
            for t in sorted(T3):
                for g in signed(Hidx):
                    tot += 1
                    r = oct_mult(t, g)
                    if r in T3:
                        ok += 1
                    elif first_escape is None:
                        first_escape = {"L": list(L), "e": e, "g": g, "t": t,
                                        "result_byte": r}
    return {"finding": "correction_strict_3index_vs_4index_coset",
            "strict_3index_H_stable": [ok, tot],
            "coset_4index_H_stable": [1792, 1792],
            "first_escape": first_escape,
            "note": "3+4 is the structure; 3+1+3 manufactures a seam artifact. "
                    "shipped RIGHT action e5.e1 -> byte 4 (+e4, the seam unit); "
                    "the reversed order e1.e5 is byte 12 (-e4).",
            "pass": (ok, tot) == (1008, 1344)
                    and first_escape == {"L": [1, 2, 3], "e": 4, "g": 1, "t": 5,
                                         "result_byte": 4}}


def hurwitz_wall():
    """The action law is native to the 𝕆 rung (#1514: turns->ℍ, composition->𝕆).
    Sampled as torsor signed-basis-unit triples with the group an ASSOCIATIVE
    rung it is 200/200 at dim 8; the quaternion-group torsor stays 200/200 even
    embedded at dim 16 (group associativity carries it), and only degrades when
    the GROUP itself is pushed up to the non-associative 𝕆 (dim 16 group=𝕆)."""
    def su(dim, idxs):
        out = []
        for i in idxs:
            out.append(cd_basis(dim, i))
            out.append([-c for c in cd_basis(dim, i)])
        return out

    def sample_law(dim, Hidx, Tidx, seed=1514, n=200):
        H, T = su(dim, Hidx), su(dim, Tidx)
        triples = [(t, g, h) for t in T for g in H for h in H]
        random.seed(seed)
        s = random.sample(triples, min(n, len(triples)))
        ok = sum(1 for t, g, h in s
                 if list(cd_mult(cd_mult(t, g), h)) == list(cd_mult(t, cd_mult(h, g))))
        return ok, len(s)

    d8 = sample_law(8, [0, 1, 2, 3], [4, 5, 6, 7])
    d16_quat = sample_law(16, [0, 1, 2, 3], [8, 9, 10, 11])
    d16_oct = sample_law(16, list(range(8)), list(range(8, 16)))
    return {"finding": "hurwitz_wall_composition_native_to_O",
            "dim8_group=H(assoc)": list(d8),
            "dim16_group=H(assoc)": list(d16_quat),
            "dim16_group=O(nonassoc)": list(d16_oct),
            "note": "composition->𝕆, turns->ℍ (#1514): the action law needs an "
                    "ASSOCIATIVE group; it holds 200/200 at dim8 and for a "
                    "quaternion-group torsor even at dim16, and degrades only "
                    "when the group is the non-associative 𝕆. The ephemeral "
                    "brief's clean '0/200 at dim16' is NOT reproducible through "
                    "the shipped cd_mult and is replaced by this structure.",
            "seam_independent_W_is_tautological": True,
            "pass": d8 == (200, 200) and d16_quat == (200, 200)}


def main():
    records = [ratchet1(), ratchet2(), ratchet3(), ratchet4(),
               correction_3plus4(), hurwitz_wall()]
    out = Path(__file__).with_suffix(".ndjson")
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "meta", "task": "#T963", "rc": "0.9.0rc388",
                             "ops": ["srmech.math.octonion.oct_torsor_act",
                                     "srmech.math.octonion.oct_torsor_div"]},
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
