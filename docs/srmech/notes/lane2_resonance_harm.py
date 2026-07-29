"""LANE 2 phase 4 -- can the shipped HARMONICS surface express the question?

harmonics._spectral_scores reads three POSITIONAL-INDEX symmetries of a
coefficient list: dc = |sum x| / sum|x|, mirror = |<x, reverse(x)>| / <x,x>,
three = |<x, roll(x, n/3)>| / <x,x>.  `reverse` and `roll` are operations on the
POSITION of a coefficient in the list -- i.e. on the ORDERED BASIS of the
grading group.  Condition (ii) of the fossil test says exactly that ordered
basis is gauge.  So the prediction is that the harmonic signature is NOT
GL(d,F2)-invariant.  MEASURE it rather than assert it.
"""
import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import algebra_table, left_mult_matrix
from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals_exact
from srmech.amsc.harmonics import _spectral_scores, classify_chirality_harmonic

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lane2_resonance_probe import (                                    # noqa: E402
    DIM, D, _int_matrix, run_cascade, gl_maps, gl_transport, gauge_transport,
    trivial_cocycle_table,
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def cp_of(acc, table):
    return tuple(char_poly(_int_matrix(left_mult_matrix(acc, table))))


def n_harm(table, ms):
    s = set()
    for w in itertools.permutations(ms):
        acc = run_cascade(table, w)
        s.add(tuple(q.as_pair() for q in _spectral_scores(acc)))
    return len(s)


def n_cp(table, ms):
    s = set()
    for w in itertools.permutations(ms):
        s.add(cp_of(run_cascade(table, w), table))
    return len(s)


def n_trace(table, ms):
    """Is the whole exact char-poly worth more than its FIRST coefficient?"""
    s = set()
    for w in itertools.permutations(ms):
        s.add(cp_of(run_cascade(table, w), table)[1])
    return len(s)


def main():
    O = algebra_table(DIM)
    SO = algebra_table(DIM, (1, -1, -1))
    G = gl_maps(D)
    triples = list(itertools.combinations(range(1, DIM), 3))
    fano = [m for m in triples if (m[0] ^ m[1] ^ m[2]) == 0]

    # --- is the exact spectral signature worth more than one bit (the trace)? ---
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        same = all(n_cp(tbl, m) == n_trace(tbl, m) for m in triples)
        emit({"kind": "one_bit", "algebra": name,
              "charpoly_N_equals_trace_N_on_all_35_triples": same,
              "charpoly_N_by_orbit": {
                  "fano": sorted({n_cp(tbl, m) for m in fano}),
                  "independent": sorted({n_cp(tbl, m) for m in triples if m not in fano})},
              "trace_N_by_orbit": {
                  "fano": sorted({n_trace(tbl, m) for m in fano}),
                  "independent": sorted({n_trace(tbl, m) for m in triples if m not in fano})}})

    # --- harmonics: within-orbit variation (the (ii) failure), measured ---
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        per = {m: n_harm(tbl, m) for m in triples}
        emit({"kind": "harm_within_orbit", "algebra": name,
              "fano_values": sorted({per[m] for m in fano}),
              "fano_detail": {str(list(m)): per[m] for m in fano},
              "independent_values": sorted({per[m] for m in triples if m not in fano}),
              "constant_on_GL_orbits": (len({per[m] for m in fano}) == 1 and
                                        len({per[m] for m in triples if m not in fano}) == 1)})

    # --- harmonics: full GL equivariance sweep (all 168) on the Fano orbit ---
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        base = {m: n_harm(tbl, m) for m in fano}
        viol = 0
        checked = 0
        for p in G:
            t = gl_transport(tbl, p)
            for m in fano:
                tm = tuple(sorted(p[a] for a in m))
                checked += 1
                if n_harm(t, tm) != base[m]:
                    viol += 1
        emit({"kind": "harm_ii_gl", "algebra": name, "checked": checked,
              "violations": viol, "gl_invariant": viol == 0})

    # --- and the same sweep for char_poly on the Fano orbit, for contrast ---
    for name, tbl in (("octonion", O), ("split_octonion", SO)):
        base = {m: n_cp(tbl, m) for m in fano}
        viol = 0
        checked = 0
        for p in G:
            t = gl_transport(tbl, p)
            for m in fano:
                tm = tuple(sorted(p[a] for a in m))
                checked += 1
                if n_cp(t, tm) != base[m]:
                    viol += 1
        emit({"kind": "cp_ii_gl", "algebra": name, "checked": checked,
              "violations": viol, "gl_invariant": viol == 0})

    # --- eigvals_exact: confirm it is the PROJECTION of the same exact substrate ---
    acc = run_cascade(O, (1, 2, 3))
    m = _int_matrix(left_mult_matrix(acc, O))
    emit({"kind": "eigvals_exact_demo", "word": [1, 2, 3],
          "char_poly": list(char_poly(m)),
          "eigvals_exact_real_only": eigvals_exact(m),
          "eigvals_exact_with_complex": [[c.real, c.imag] if isinstance(c, complex)
                                         else [c, 0.0]
                                         for c in eigvals_exact(m, include_complex=True)],
          "note": "eigvals_exact float-projects at the end; char_poly is the exact substrate"})


if __name__ == "__main__":
    main()
