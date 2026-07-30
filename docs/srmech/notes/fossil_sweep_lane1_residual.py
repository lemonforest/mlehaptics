"""LANE 1 stage 6 — the RESIDUAL off-diagonal invariant, and whether it is
anything other than the metric signature.

Stage 5 measured that eps_definite XOR eps_split is NOT in (gauge + diagonal):
there IS gauge-invariant OFF-DIAGONAL content separating O from split-O.  Two
readings are possible and they have opposite verdicts:

  (a) FOSSIL reading   -- the residual records the ORDER of the doubling path.
  (b) CIRCULAR reading -- the residual is a FUNCTION of the diagonal q, i.e. of
      WHICH Fano line carries the negative squares; then it re-reads the metric
      signature and is not a fossil of order.

Discriminator, exact and exhaustive:
  * enumerate the whole gamma family at each dim;
  * compute (i) the diagonal q as a SET of indices, and (ii) the gauge class
    (packed eps reduced modulo the coboundary subspace B^2);
  * ask whether q -> gauge class is a well-defined FUNCTION on the family
    (same q  =>  same class).  If yes, every gauge invariant separating the
    family members factors through q = the signature.
  * compute the GL(d,F2) stabiliser of the gauge class and the GL stabiliser of
    q, and ask whether they are the SAME SUBGROUP (element-for-element).
  * run the same two questions on RANDOM ANTICOMMUTATIVE controls, where the
    implication is expected to FAIL -- which is what makes its holding on the
    gamma family a measurement rather than a triviality.

Exact F2 throughout.  No float, no abs(), no numpy.
"""

import json
import sys

sys.path.append("../notes")
from fossil_sweep_lane1_gauge_gl_dim import (   # noqa: E402
    coboundary_gens, eps_from_table, gamma_family, gl_perms, pack,
    rand_anticomm_table, relabel,
)
from fossil_sweep_lane1_circularity import echelon, reduce_by  # noqa: E402


def emit(**r):
    sys.stdout.write(json.dumps(r, sort_keys=True) + "\n")
    sys.stdout.flush()


def gauge_class(E, ech):
    return reduce_by(ech, pack(E))


def diag_set(E):
    return tuple(i for i in range(len(E)) if E[i][i])


def main():
    for dim in (4, 8, 16):
        d = dim.bit_length() - 1
        ech = echelon(coboundary_gens(dim))
        perms = gl_perms(d)
        fam = gamma_family(dim)

        rows = []
        for g, T in sorted(fam.items()):
            E = eps_from_table(T)
            rows.append({"gammas": list(g), "q": diag_set(E),
                         "cls": gauge_class(E, ech), "E": E})

        # (1) is q -> gauge class a FUNCTION on the gamma family?
        by_q = {}
        well_defined = True
        for r in rows:
            s = by_q.setdefault(r["q"], set())
            s.add(r["cls"])
            if len(s) > 1:
                well_defined = False
        emit(kind="residual_family", dim=dim, family_size=len(rows),
             distinct_diagonals=len(by_q),
             distinct_gauge_classes=len({r["cls"] for r in rows}),
             q_determines_gauge_class=well_defined,
             diagonals=[{"q": list(k), "n_classes": len(v)}
                        for k, v in sorted(by_q.items())])

        # (2) GL stabiliser of the gauge class vs GL stabiliser of q
        for r in rows:
            lbl = "definite" if all(v < 0 for v in r["gammas"]) else "split"
            E = r["E"]
            stab_cls, stab_q, both = [], [], 0
            for n, perm in enumerate(perms):
                Eg = relabel(E, perm)
                sc = gauge_class(Eg, ech) == r["cls"]
                sq = diag_set(Eg) == r["q"]
                if sc:
                    stab_cls.append(n)
                if sq:
                    stab_q.append(n)
                if sc and sq:
                    both += 1
            emit(kind="stabiliser", dim=dim, gammas=r["gammas"], label=lbl,
                 gl_order=len(perms),
                 stab_gauge_class_order=len(stab_cls),
                 stab_diagonal_order=len(stab_q),
                 same_subgroup=(stab_cls == stab_q),
                 stab_class_subset_of_stab_q=set(stab_cls).issubset(set(stab_q)),
                 stab_q_subset_of_stab_class=set(stab_q).issubset(set(stab_cls)),
                 gl_orbit_of_gauge_class=len(perms) // max(len(stab_cls), 1),
                 gl_orbit_of_diagonal=len(perms) // max(len(stab_q), 1))
            if dim == 16 and lbl == "split":
                break   # the 15 remaining dim-16 splits are GL-conjugate

        # (3) CONTROL: random anticommutative tables with the SAME diagonal.
        #     If two tables share q but land in different gauge classes, then q
        #     does NOT determine the class in general -- so its doing so on the
        #     gamma family is a measurement, not a tautology.
        ctrl = {}
        for seed in (11, 22, 33, 44, 55, 66, 77, 88):
            E = eps_from_table(rand_anticomm_table(dim, seed,
                                                   diagonal=[-1] * (dim - 1)))
            ctrl.setdefault(diag_set(E), set()).add(gauge_class(E, ech))
        emit(kind="residual_control", dim=dim,
             control="random_anticommutative_with_FIXED_diagonal",
             n_tables=8,
             distinct_diagonals=len(ctrl),
             classes_per_diagonal=[len(v) for v in ctrl.values()],
             q_determines_gauge_class=all(len(v) == 1 for v in ctrl.values()))


if __name__ == "__main__":
    main()
