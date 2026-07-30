"""LANE 2 phase 6 -- the MECHANISM behind the null, verified not asserted.

Hypothesis from the measured numbers: on a COMPOSITION algebra the exact
char-poly of the left-regular representation factors as

    char_poly(L(x)) == (lambda^2 - 2*Re(x)*lambda + N(x)) ** (dim/2)

with N the (multiplicative) norm form.  If so, then for a cascade acc =
prod (1 + e_a):

  * N(acc) = prod N(1 + e_a)  -- MULTIPLICATIVE, hence ORDER-BLIND,
  * so the ONLY order-sensitive spectral datum is Re(acc),

which is exactly what "N_charpoly == N_trace on every multiset" measured.
Verify the factorisation identity coefficient-by-coefficient, exactly, on every
cascade accumulator -- and verify it BREAKS on the random anticommutative
control (which is not a composition algebra).
"""
import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, left_mult_matrix, table_product, cd_basis, cd_norm_sq,
)
from srmech.amsc.cascade.matrix_cascades import char_poly
from srmech.amsc.q import Q

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lane2_resonance_probe import _int_matrix, random_anticommutative_table   # noqa: E402


def emit(rec):
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def step_element(dim, a):
    return tuple(Q(1) if i in (0, a) else Q(0) for i in range(dim))


def run(table, dim, word):
    acc = cd_basis(dim, 0)
    for a in word:
        acc = table_product(table, step_element(dim, a), acc)
    return acc


def ipoly_mul(a, b):
    """Integer polynomial product, high->low coefficient lists. Exact ints."""
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def ipoly_pow(p, n):
    r = [1]
    for _ in range(n):
        r = ipoly_mul(r, p)
    return r


def main():
    DIM = 8
    O = algebra_table(DIM)
    SO = algebra_table(DIM, (1, -1, -1))
    RA = random_anticommutative_table(DIM, "lane2-random-anticommutative-0")

    for name, tbl, gammas in (("octonion", O, None),
                              ("split_octonion", SO, (1, -1, -1)),
                              ("random_anticomm_0", RA, "N/A")):
        ok = 0
        bad = 0
        examples = []
        norms = set()
        for ms in itertools.combinations(range(1, DIM), 3):
            for w in itertools.permutations(ms):
                acc = run(tbl, DIM, w)
                cp = char_poly(_int_matrix(left_mult_matrix(acc, tbl)))
                re2 = acc[0]                        # Re(acc), exact Q
                # N via the SHIPPED norm op where it is defined for this table;
                # for the control table there is no gamma vector, so read the
                # constant term of the minimal quadratic off the char-poly's own
                # degree-(dim-2) structure is NOT assumed -- instead derive N
                # from the shipped cd_norm_sq for the CD family only.
                if gammas != "N/A":
                    nrm = cd_norm_sq(acc, gammas)
                    norms.add((tuple(sorted(ms)), nrm.as_pair()))
                    quad = [1, -2 * re2.numerator, nrm.numerator]
                    pred = ipoly_pow(quad, DIM // 2)
                    if list(cp) == pred:
                        ok += 1
                    else:
                        bad += 1
                        if len(examples) < 2:
                            examples.append({"word": list(w), "cp": list(cp),
                                             "pred": pred})
                else:
                    # control: no composition norm -- test whether ANY quadratic
                    # (lam^2 - 2 Re lam + c)^(dim/2) reproduces cp, sweeping c
                    # over the exact integer constant term forced by cp[-1].
                    tail = cp[-1]
                    hit = False
                    for c in range(-64, 65):
                        if c ** (DIM // 2) != tail:
                            continue
                        if list(cp) == ipoly_pow([1, -2 * re2.numerator, c],
                                                 DIM // 2):
                            hit = True
                            break
                    if hit:
                        ok += 1
                    else:
                        bad += 1
        emit({"kind": "mechanism", "algebra": name,
              "cascades": ok + bad,
              "charpoly_equals_quadratic_power": ok,
              "violations": bad,
              "identity_holds": bad == 0,
              "examples": examples,
              "norm_is_order_blind": (len({n for _, n in norms}) <= 1
                                      if gammas != "N/A" else None),
              "distinct_norms_over_all_cascades": sorted({n for _, n in norms})
                                                  if gammas != "N/A" else None})


if __name__ == "__main__":
    main()
