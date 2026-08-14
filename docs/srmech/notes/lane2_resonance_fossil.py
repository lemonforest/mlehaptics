"""LANE 2 phase 2 -- the FULL three-part fossil test on the order-difference the
exact spectral surface reports.

Phase 1 measured (35 multisets x 6 orderings, exact):
  octonion, binomial steps:  N_distinct(char_poly) == 1 on the 28 linearly
  INDEPENDENT index-triples and == 2 on the 7 DEPENDENT ones (the Fano lines).

Phase 2 asks of that 2-fold split:
  (i)   is it GAUGE-INVARIANT   -- all 2^(dim-1) = 128 diagonal +/-1 rescalings
  (ii)  is it GL(d,F2)-INVARIANT-- all |GL(3,F2)| = 168 ordered-basis relabellings
  (iii) is it DIM-DETERMINED    -- octonion vs SPLIT-octonion, both dim 8
  and WHAT the split is: which orderings share a signature?  (If it is the
  even/odd permutation split, order-REVERSAL flips it -- and the reversal gauge
  is an already-buried corpse.)
"""
import itertools
import json
import sys
import time

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, left_mult_matrix, cd_basis, inertia_signature,
)
from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals_exact
from srmech.music.harmonics import _spectral_scores
from srmech.amsc.format import sha256_bytes
from srmech.amsc.q import Q

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lane2_resonance_probe import (                                    # noqa: E402
    DIM, D, _int_matrix, sig_elem, sig_harmonic, step_element, run_cascade,
    trivial_cocycle_table, random_anticommutative_table,
    gauge_transport, gl_maps, gl_transport,
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def cp_of(acc, table):
    return tuple(char_poly(_int_matrix(left_mult_matrix(acc, table))))


def sig_profile(table, multiset, monomial=False):
    """The ordered list of exact char-polys, one per ordering (lexicographic
    permutation order), plus the partition of orderings into equal-signature
    classes."""
    words = list(itertools.permutations(multiset))
    cps = [cp_of(run_cascade(table, w, monomial=monomial), table) for w in words]
    uniq = []
    for c in cps:
        if c not in uniq:
            uniq.append(c)
    classes = [uniq.index(c) for c in cps]
    return words, cps, classes, len(uniq)


def perm_parity(word, base):
    """Parity of the permutation taking `base` (sorted) to `word`. Pure counting
    of inversions -- no float, no abs."""
    pos = {v: i for i, v in enumerate(base)}
    idx = [pos[v] for v in word]
    inv = 0
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            if idx[i] > idx[j]:
                inv += 1
    return inv % 2


def main():
    t0 = time.time()
    O = algebra_table(DIM)
    SO = algebra_table(DIM, (1, -1, -1))
    SO2 = algebra_table(DIM, (-1, 1, -1))
    SO3 = algebra_table(DIM, (-1, -1, 1))
    TRIV = trivial_cocycle_table(DIM)
    RAND = [random_anticommutative_table(DIM, "lane2-random-anticommutative-%d" % k)
            for k in range(5)]

    fano = [ms for ms in itertools.combinations(range(1, DIM), 3)
            if (ms[0] ^ ms[1] ^ ms[2]) == 0]
    indep = [ms for ms in itertools.combinations(range(1, DIM), 3)
             if (ms[0] ^ ms[1] ^ ms[2]) != 0]
    emit({"kind": "orbits", "fano_lines": len(fano), "independent": len(indep),
          "fano": [list(m) for m in fano]})

    # ---------------------------------------------------------------- WHAT the split is
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        for ms in fano:
            words, cps, classes, n = sig_profile(tbl, ms)
            par = [perm_parity(w, tuple(sorted(ms))) for w in words]
            # does the signature class coincide with permutation parity?
            by_par = {0: set(), 1: set()}
            for w, c, p in zip(words, classes, par):
                by_par[p].add(c)
            # does order-REVERSAL move between classes?
            widx = {w: i for i, w in enumerate(words)}
            rev_flips = all(classes[widx[w]] != classes[widx[tuple(reversed(w))]]
                            for w in words)
            emit({"kind": "fano_split", "algebra": name, "multiset": list(ms),
                  "n_distinct_charpoly": n,
                  "class_by_permutation": classes,
                  "parity_by_permutation": par,
                  "class_equals_parity": (len(by_par[0]) == 1 and len(by_par[1]) == 1
                                          and by_par[0] != by_par[1]),
                  "reversal_flips_class": rev_flips,
                  "charpolys": [list(c) for c in cps[:2]]})
            break   # one Fano line is representative; the orbit sweep below covers all

    # every Fano line, both algebras, compact
    for name, tbl in (("octonion", O), ("split_octonion", SO),
                      ("split_octonion_g2", SO2), ("split_octonion_g3", SO3)):
        rows = []
        for ms in fano:
            words, cps, classes, n = sig_profile(tbl, ms)
            par = [perm_parity(w, tuple(sorted(ms))) for w in words]
            ok_par = all((classes[i] == classes[j]) == (par[i] == par[j])
                         for i in range(6) for j in range(6))
            rows.append({"ms": list(ms), "n": n, "class_is_parity": ok_par,
                         "cpset": sorted(cps)})
        emit({"kind": "fano_all", "algebra": name,
              "n_values": sorted({r["n"] for r in rows}),
              "class_is_parity_all": all(r["class_is_parity"] for r in rows),
              "distinct_cpsets_across_lines": len({json.dumps(r["cpset"]) for r in rows}),
              "example_cpset": [list(c) for c in rows[0]["cpset"]]})

    # ---------------------------------------------------------------- (iii) DIM-DETERMINED?
    def profile(tbl):
        """The candidate quantity, as a whole: for each GL-orbit of index-triples,
        the sorted set of N_distinct(char_poly) values."""
        f = sorted({sig_profile(tbl, ms)[3] for ms in fano})
        i = sorted({sig_profile(tbl, ms)[3] for ms in indep})
        return {"fano": f, "independent": i}

    prof = {}
    for name, tbl in (("octonion", O), ("split_octonion", SO),
                      ("split_octonion_g2", SO2), ("split_octonion_g3", SO3),
                      ("TRIVIAL_COCYCLE_control", TRIV)):
        prof[name] = profile(tbl)
        emit({"kind": "iii_dim_determined", "algebra": name, "dim": DIM,
              "profile": prof[name]})
    for k, tbl in enumerate(RAND):
        p = profile(tbl)
        emit({"kind": "iii_dim_determined", "algebra": "random_anticomm_%d" % k,
              "dim": DIM, "profile": p})
    emit({"kind": "iii_verdict",
          "octonion_vs_split_identical": prof["octonion"] == prof["split_octonion"],
          "octonion_profile": prof["octonion"],
          "split_profile": prof["split_octonion"]})

    # also: is the char-poly SET (not just its size) the same on O vs split-O?
    for ms in fano[:3]:
        so_set = sorted(sig_profile(SO, ms)[1])
        o_set = sorted(sig_profile(O, ms)[1])
        emit({"kind": "iii_cpset", "multiset": list(ms),
              "octonion_cpset": [list(c) for c in sorted(set(o_set))],
              "split_cpset": [list(c) for c in sorted(set(so_set))],
              "identical": sorted(set(o_set)) == sorted(set(so_set))})

    emit({"kind": "timing", "phase": "what+iii", "seconds": round(time.time() - t0, 1)})

    # ---------------------------------------------------------------- (i) GAUGE
    t1 = time.time()
    base = profile(O)
    gauges = [(1,) + s for s in itertools.product((1, -1), repeat=DIM - 1)]
    assert len(gauges) == 1 << (DIM - 1)
    bad = 0
    seen = set()
    for s in gauges:
        p = profile(gauge_transport(O, s))
        seen.add(json.dumps(p, sort_keys=True))
        if p != base:
            bad += 1
    emit({"kind": "i_gauge", "algebra": "octonion", "n_gauges": len(gauges),
          "distinct_profiles": len(seen), "violations": bad,
          "gauge_invariant": bad == 0, "seconds": round(time.time() - t1, 1)})

    t1 = time.time()
    base_so = profile(SO)
    bad = 0
    for s in gauges:
        if profile(gauge_transport(SO, s)) != base_so:
            bad += 1
    emit({"kind": "i_gauge", "algebra": "split_octonion", "n_gauges": len(gauges),
          "violations": bad, "gauge_invariant": bad == 0,
          "seconds": round(time.time() - t1, 1)})

    # ---------------------------------------------------------------- (ii) GL(3,F2)
    t1 = time.time()
    G = gl_maps(D)
    emit({"kind": "ii_group", "d": D, "order": len(G)})

    # (a) are all 168 relabelled tables the SAME algebra?  read with a shipped op.
    ins = []
    in_gauge_orbit = 0
    gauge_orbit = {json.dumps(gauge_transport(O, s)) for s in gauges}
    for perm in G:
        t = gl_transport(O, perm)
        ins.append(tuple(inertia_signature(t)["signature"]))
        if json.dumps(t) in gauge_orbit:
            in_gauge_orbit += 1
    emit({"kind": "ii_isomorphic", "algebra": "octonion",
          "distinct_trace_signatures": [list(x) for x in sorted(set(ins))],
          "all_same_as_base": len(set(ins)) == 1,
          "relabellings_inside_the_gauge_orbit": in_gauge_orbit,
          "of_total": len(G)})

    # (b) EQUIVARIANCE: N(T.A, T.table) == N(A, table) for every T and every triple
    all_ms = fano + indep
    base_n = {ms: sig_profile(O, ms)[3] for ms in all_ms}
    base_n_so = {ms: sig_profile(SO, ms)[3] for ms in all_ms}
    for aname, atbl, abase in (("octonion", O, base_n),
                               ("split_octonion", SO, base_n_so)):
        viol = 0
        checked = 0
        for perm in G:
            t = gl_transport(atbl, perm)
            for ms in all_ms:
                tms = tuple(sorted(perm[a] for a in ms))
                checked += 1
                if abase[ms] != sig_profile(t, tms)[3]:
                    viol += 1
        emit({"kind": "ii_equivariance", "algebra": aname, "checked": checked,
              "violations": viol, "gl_invariant": viol == 0,
              "seconds": round(time.time() - t1, 1)})

    emit({"kind": "timing", "phase": "total", "seconds": round(time.time() - t0, 1)})


if __name__ == "__main__":
    main()
