#!/usr/bin/env python3
"""LANE 2 — DOES THE NEWLY INTRODUCED GENERATOR BREAK THE RELATION LOST AT ITS
RUNG?  (2026-07-29)

MEASURES, exactly, at every Cayley-Dickson rung n -> 2n, the PARTITION of the
failures of the relation traditionally said to die at that rung, by whether the
failing basis tuple touches:
  - the DESIGNATED new generator  e_n  (the "index n in the doubled algebra"),
  - ANY new index  (n .. 2n-1),
  - only OLD indices (0 .. n-1).

...and the three claims the user's k=3 reading puts on the ladder:
  (1) the fourth rung is misnamed  (alternativity prior, composition consequent,
      zero-divisor-freeness contingent on a DEFINITE norm),
  (2) above H every rung narrows WHICH SHAPE of triple still associates
      (all -> repeat -> palindrome),
  (3) the new generator is exactly the element that breaks the lost relation.

SUBJECT (shipped srmech ops; NO hand-rolled algebra):
  srmech.amsc.cascade.cayley_dickson.algebra_table(dim, gammas)     rc352
  srmech.amsc.cascade.cayley_dickson.table_product(table, x, y)     rc352
  srmech.amsc.cascade.cayley_dickson.cd_norm_sq(x, gammas=)         rc352 gated
  srmech.amsc.cascade.cayley_dickson.cd_add / cd_basis / cd_conjugate
  srmech.amsc.cascade.cayley_dickson.inertia_signature(table)       rc349
  srmech.amsc.cascade.cayley_dickson.left_mult_kernel(x, table=)
  srmech.amsc.cascade.cayley_dickson.left_mult_is_invertible(x, table=)
  srmech.amsc.cascade.cayley_dickson.sedenion_zero_divisor_witness()
  srmech.amsc.format.sha256_bytes                                   Class A

FAST PATH + DIFFERENTIAL: every table here is MONOMIAL, so a basis associator
is read off the table as an exact signed index pair.  That fast read is
DIFFERENTIALLY VERIFIED against the shipped ``table_product`` composition —
FULL sweep at dim 2/4/8, sha256-drawn sample at 16/32.  Any disagreement aborts.

NO float, NO numpy, NO stdlib fractions, NO abs().  Sign handling is the
Class-K pin-slot composed with Class-C re-orientation (comparisons on exact
ints / exact Q only).

CONTROLS (mandatory):
  - every SPLIT gamma-twist reachable at each dim,
  - RAND-ANTICOMM : the CD index lane (i^j) kept, sign cocycle randomised,
  - RAND-FULL     : index lane AND sign randomised.

Run:  python3 lane2_new_generator_partition_2026-07-29.py > <name>.ndjson
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    ALGEBRA_NAMES,
    algebra_table,
    table_product,
    cd_add,
    cd_basis,
    cd_conjugate,
    cd_norm_sq,
    inertia_signature,
    left_mult_kernel,
    left_mult_is_invertible,
    sedenion_zero_divisor_witness,
)
from srmech.amsc.format import sha256_bytes

PERMS = (
    ((0, 1, 2), +1),
    ((1, 2, 0), +1),
    ((2, 0, 1), +1),
    ((0, 2, 1), -1),
    ((2, 1, 0), -1),
    ((1, 0, 2), -1),
)


def emit(rec):
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


# ─────────────────────────── Class-A deterministic stream ────────────────
class ClassAStream:
    def __init__(self, label):
        self._label = label.encode("utf-8")
        self._n = 0
        self._buf = b""

    def _refill(self):
        digest = sha256_bytes(self._label + b":" + str(self._n).encode())
        self._buf += bytes.fromhex(digest)
        self._n += 1

    def byte(self):
        if not self._buf:
            self._refill()
        b = self._buf[0]
        self._buf = self._buf[1:]
        return b

    def below(self, n):
        assert 1 <= n <= 256
        lim = (256 // n) * n
        while True:
            v = self.byte()
            if v < lim:
                return v % n

    def sign(self):
        """A +/-1 — the Class-K pin-slot draw.  No abs()."""
        return 1 if (self.byte() & 1) == 0 else -1

    def small_int(self):
        """Exact small integer in [-4, 4] (Class-K pin-slot x Class-C sign)."""
        return self.sign() * self.below(5)


# ─────────────────────────── control tables ──────────────────────────────
def rand_anticomm_table(dim, label):
    """Monomial, unital, anticommutative, imaginary-square = -e0.

    Index lane is the CD lane i^j; the SIGN cocycle is Class-A random subject
    to  s(0,j)=s(i,0)=+1,  s(i,i)=-1 (i>=1),  s(i,j)=-s(j,i) (i!=j>=1).
    """
    st = ClassAStream(label)
    sgn = [[0] * dim for _ in range(dim)]
    for i in range(dim):
        sgn[0][i] = 1
        sgn[i][0] = 1
    for i in range(1, dim):
        sgn[i][i] = -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            s = st.sign()
            sgn[i][j] = s
            sgn[j][i] = -s
    tbl = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            tbl[i][j][i ^ j] = sgn[i][j]
    return tbl


def rand_full_table(dim, label):
    """Index lane randomised too: a Class-A random involutive lane on the
    imaginaries, still unital with e_i^2 = -e0 and anticommutative."""
    st = ClassAStream(label)
    # random fixed-point-free-ish lane: pick a random permutation p of
    # 1..dim-1 and use lane(i,j) = i ^ perm-scrambled j, forced back to 0 on
    # the diagonal.  Keeps the table monomial + unital, breaks the group lane.
    perm = list(range(dim))
    for i in range(dim - 1, 1, -1):
        j = 1 + st.below(i)
        perm[i], perm[j] = perm[j], perm[i]
    lane = [[0] * dim for _ in range(dim)]
    sgn = [[0] * dim for _ in range(dim)]
    for i in range(dim):
        lane[0][i] = i
        lane[i][0] = i
        sgn[0][i] = 1
        sgn[i][0] = 1
    for i in range(1, dim):
        lane[i][i] = 0
        sgn[i][i] = -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            k = perm[i ^ j]
            if k == 0:
                k = 1 + st.below(dim - 1)
            lane[i][j] = k
            lane[j][i] = k
            s = st.sign()
            sgn[i][j] = s
            sgn[j][i] = -s
    tbl = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            tbl[i][j][lane[i][j]] = sgn[i][j]
    return tbl


# ─────────────────────────── monomial fast path ──────────────────────────
def monomial_map(table):
    dim = len(table)
    mono = [[None] * dim for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            nz = [(k, table[i][j][k]) for k in range(dim) if table[i][j][k]]
            if len(nz) != 1:
                raise ValueError("table is not monomial")
            mono[i][j] = nz[0]
    return mono


def assoc_fast(mono, i, j, k):
    """[e_i,e_j,e_k] as a canonical sparse tuple ((idx, coeff), ...)."""
    p, s1 = mono[i][j]
    q, s2 = mono[p][k]
    r, t1 = mono[j][k]
    u, t2 = mono[i][r]
    lhs, rhs = s1 * s2, t1 * t2
    if q == u:
        d = lhs - rhs
        return () if d == 0 else ((q, d),)
    return tuple(sorted(((q, lhs), (u, -rhs))))


def assoc_shipped(table, i, j, k):
    """The SAME associator through shipped ops only — the differential oracle
    is the fast path; THIS is the subject composition."""
    dim = len(table)
    a, b, c = cd_basis(dim, i), cd_basis(dim, j), cd_basis(dim, k)
    lhs = table_product(table, table_product(table, a, b), c)
    rhs = table_product(table, a, table_product(table, b, c))
    minus = [0] * dim
    minus[0] = -1
    neg = table_product(table, minus, rhs)
    v = cd_add(lhs, neg)
    return tuple(sorted((idx, int(val)) for idx, val in enumerate(v) if val != 0))


def verify_fast_path(table, mono, dim, full_upto=8, samples=400, label=""):
    checks = bad = 0
    if dim <= full_upto:
        trips = itertools.product(range(dim), repeat=3)
    else:
        st = ClassAStream("verify:" + label + ":" + str(dim))
        trips = [(st.below(dim), st.below(dim), st.below(dim))
                 for _ in range(samples)]
    for (i, j, k) in trips:
        checks += 1
        if assoc_fast(mono, i, j, k) != assoc_shipped(table, i, j, k):
            bad += 1
    if bad:
        raise SystemExit(f"FAST-PATH DIFFERENTIAL FAILED: {label} dim={dim}")
    return checks


# ─────────────────────────── partition helper ────────────────────────────
def partition(idxs, n):
    """n = the OLD dimension at this rung; new indices are n..2n-1."""
    new = [i for i in idxs if i >= n]
    return {
        "n_new": len(new),
        "touches_generator_e_n": (n in idxs),
        "all_old": len(new) == 0,
    }


# ─────────────────────────── the norm, read two ways ─────────────────────
def norm_from_table(table, x):
    """N(x) = Re(x * conj(x)) read off the TABLE.  LABELLED ORACLE for random
    control tables (where no gamma vector exists); cross-checked against the
    shipped gated cd_norm_sq on the whole CD/split family below."""
    dim = len(table)
    xb = [x[0]] + [-v for v in x[1:]]
    return table_product(table, x, xb)[0]


# ═════════════════════════════════════════════════════════════════════════
# RUNG 1 — R -> C : ORDERING
# ═════════════════════════════════════════════════════════════════════════
def rung_ordering():
    fam = [("CD-definite", None), ("SPLIT-g+", (1,))]
    for name, g in fam:
        t = algebra_table(2, g)
        mono = monomial_map(t)
        sig = inertia_signature(t)
        # squares of each basis element, read off the table
        squares = {}
        neg_sq = []
        for i in range(2):
            k, s = mono[i][i]
            squares[i] = [k, s]
            if k == 0 and s < 0:
                neg_sq.append(i)
        # zero divisors: (e0 + e1)(e0 - e1) and the shipped kernel probe
        zd = None
        for s in (1, -1):
            x = [1, s]
            if len(left_mult_kernel(x, t)) > 0:
                zd = x
                break
        emit({
            "record": "rung1_ordering",
            "rung": "R->C", "dim": 2, "old_dim": 1,
            "algebra": name,
            "new_indices": [1],
            "basis_squares": squares,
            "negative_square_indices": neg_sq,
            "n_negative_square_candidates_total": 1,
            "n_negative_square_candidates_that_are_new": len(
                [i for i in neg_sq if i >= 1]),
            "trace_signature": list(sig["signature"]),
            "norm_signature": list(sig["norm_signature"]),
            "witness_certifies_nonorderable": sig[
                "witness_certifies_nonorderable"],
            "zero_divisor_witness": zd,
            "has_zero_divisor": zd is not None,
            "cd_norm_sq_shipped_on_[1,-1]": str(cd_norm_sq([1, -1], gammas=g)),
            "note": ("the ONLY imaginary at dim 2 IS the new generator, so the "
                     "partition has exactly one possible answer"),
        })


# ═════════════════════════════════════════════════════════════════════════
# RUNG 2 — C -> H : COMMUTATIVITY
# ═════════════════════════════════════════════════════════════════════════
def commutativity_partition(table, mono, dim, old, label):
    counts = {"commute": 0, "anticommute": 0, "neither": 0}
    fail_part = {"all_old": 0, "touches_gen_e_n": 0,
                 "new_but_not_gen": 0, "n_new_1": 0, "n_new_2": 0}
    ok_part = {"all_old": 0, "touches_gen_e_n": 0, "new_but_not_gen": 0}
    failures = []
    for i in range(dim):
        for j in range(dim):
            ki, si = mono[i][j]
            kj, sj = mono[j][i]
            if ki == kj and si == sj:
                kind = "commute"
            elif ki == kj and si == -sj:
                kind = "anticommute"
            else:
                kind = "neither"
            counts[kind] += 1
            p = partition((i, j), old)
            if kind == "commute":
                if p["all_old"]:
                    ok_part["all_old"] += 1
                elif p["touches_generator_e_n"]:
                    ok_part["touches_gen_e_n"] += 1
                else:
                    ok_part["new_but_not_gen"] += 1
            else:
                failures.append([i, j])
                if p["all_old"]:
                    fail_part["all_old"] += 1
                elif p["touches_generator_e_n"]:
                    fail_part["touches_gen_e_n"] += 1
                else:
                    fail_part["new_but_not_gen"] += 1
                fail_part["n_new_%d" % p["n_new"]] += 1
    return counts, fail_part, ok_part, failures


# ═════════════════════════════════════════════════════════════════════════
# ASSOCIATOR-BASED RUNGS
# ═════════════════════════════════════════════════════════════════════════
def classify_symmetry(mono, i, j, k):
    base = assoc_fast(mono, i, j, k)
    trip = (i, j, k)
    vals = []
    for order, par in PERMS:
        v = assoc_fast(mono, trip[order[0]], trip[order[1]], trip[order[2]])
        vals.append((v, par))
    alternating = True
    symmetric = True
    for v, par in vals:
        negbase = tuple(sorted((idx, -c) for idx, c in base))
        want = base if par > 0 else negbase
        if v != want:
            alternating = False
        if v != base:
            symmetric = False
    if alternating:
        return "alternating", base
    if symmetric:
        return "symmetric", base
    return "neither", base


def assoc_sweep(table, mono, dim, old, label):
    """Full ordered-basis-triple sweep: associativity, symmetry type, shape
    ladder, and the OLD/NEW partition of every failure."""
    dim3 = dim ** 3
    nonassoc = 0
    sym = {"alternating": 0, "symmetric": 0, "neither": 0}
    # partitions
    na_part = {"all_old": 0, "touches_gen": 0, "new_no_gen": 0,
               "n_new_0": 0, "n_new_1": 0, "n_new_2": 0, "n_new_3": 0}
    ne_part = {"all_old": 0, "touches_gen": 0, "new_no_gen": 0,
               "n_new_0": 0, "n_new_1": 0, "n_new_2": 0, "n_new_3": 0}
    assoc_part = {"all_old": 0, "touches_gen": 0, "new_no_gen": 0,
                  "n_new_0": 0, "n_new_1": 0, "n_new_2": 0, "n_new_3": 0}
    alt_ok_part = {"n_new_0": 0, "n_new_1": 0, "n_new_2": 0, "n_new_3": 0}
    # shape ladder (diagonal reads)
    shape = {"aab_nonzero": 0, "abb_nonzero": 0, "aba_nonzero": 0,
             "aab_total": 0, "abb_total": 0, "aba_total": 0}
    # linearised identities over ALL ordered triples
    lin = {"left_alt_holds": 0, "left_alt_fails": 0,
           "right_alt_holds": 0, "right_alt_fails": 0,
           "flex_holds": 0, "flex_fails": 0}
    first_neither = None
    first_lin_alt_fail = None

    def negate(v):
        return tuple(sorted((idx, -c) for idx, c in v))

    def add(u, v):
        acc = {}
        for idx, c in u:
            acc[idx] = acc.get(idx, 0) + c
        for idx, c in v:
            acc[idx] = acc.get(idx, 0) + c
        return tuple(sorted((i2, c) for i2, c in acc.items() if c != 0))

    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                a = assoc_fast(mono, i, j, k)
                p = partition((i, j, k), old)
                bucket_gen = ("all_old" if p["all_old"]
                              else ("touches_gen" if p["touches_generator_e_n"]
                                    else "new_no_gen"))
                nn = "n_new_%d" % p["n_new"]
                if a:
                    nonassoc += 1
                    na_part[bucket_gen] += 1
                    na_part[nn] += 1
                else:
                    assoc_part[bucket_gen] += 1
                    assoc_part[nn] += 1
                st, _ = classify_symmetry(mono, i, j, k)
                sym[st] += 1
                if st == "neither":
                    ne_part[bucket_gen] += 1
                    ne_part[nn] += 1
                    if first_neither is None:
                        first_neither = [i, j, k]
                else:
                    alt_ok_part[nn] += 1
                # linearised identities
                if add(a, assoc_fast(mono, j, i, k)):
                    lin["left_alt_fails"] += 1
                    if first_lin_alt_fail is None:
                        first_lin_alt_fail = [i, j, k]
                else:
                    lin["left_alt_holds"] += 1
                if add(a, assoc_fast(mono, i, k, j)):
                    lin["right_alt_fails"] += 1
                else:
                    lin["right_alt_holds"] += 1
                if add(a, assoc_fast(mono, k, j, i)):
                    lin["flex_fails"] += 1
                else:
                    lin["flex_holds"] += 1
    for i in range(dim):
        for j in range(dim):
            shape["aab_total"] += 1
            shape["abb_total"] += 1
            shape["aba_total"] += 1
            if assoc_fast(mono, i, i, j):
                shape["aab_nonzero"] += 1
            if assoc_fast(mono, i, j, j):
                shape["abb_nonzero"] += 1
            if assoc_fast(mono, i, j, i):
                shape["aba_nonzero"] += 1
    return {
        "ordered_triples": dim3,
        "nonassociating": nonassoc,
        "associating": dim3 - nonassoc,
        "symmetry_type": sym,
        "nonassoc_partition": na_part,
        "assoc_partition": assoc_part,
        "neither_partition": ne_part,
        "not_neither_partition": alt_ok_part,
        "shape_ladder": shape,
        "linearised": lin,
        "first_neither_triple": first_neither,
        "first_left_alt_linearised_failure": first_lin_alt_fail,
    }


# ═════════════════════════════════════════════════════════════════════════
# CLAIM (1) — the implication structure, run across the CONTROL family
# ═════════════════════════════════════════════════════════════════════════
def composition_probe(table, dim, gammas, label, trials=40):
    """N(xy) == N(x)N(y)?   Uses the SHIPPED gated cd_norm_sq where a gamma
    vector names the algebra; the table read is the labelled oracle and is
    cross-checked against it on every CD/split member."""
    st = ClassAStream("comp:" + label + ":" + str(dim))
    holds = fails = 0
    xcheck = xcheck_bad = 0
    first_fail = None
    for _ in range(trials):
        x = [st.small_int() for _ in range(dim)]
        y = [st.small_int() for _ in range(dim)]
        nx = norm_from_table(table, x)
        ny = norm_from_table(table, y)
        if gammas is not None or label == "CD-definite":
            g = gammas
            sx = cd_norm_sq(x, gammas=g)
            sy = cd_norm_sq(y, gammas=g)
            xcheck += 2
            if sx != nx or sy != ny:
                xcheck_bad += 1
        xy = table_product(table, x, y)
        nxy = norm_from_table(table, xy)
        if nxy == nx * ny:
            holds += 1
        else:
            fails += 1
            if first_fail is None:
                first_fail = {"x": [str(v) for v in x], "y": [str(v) for v in y],
                              "N_xy": str(nxy), "NxNy": str(nx * ny)}
    return {"composition_holds": holds, "composition_fails": fails,
            "gated_norm_crosschecks": xcheck,
            "gated_norm_crosscheck_disagreements": xcheck_bad,
            "first_composition_failure": first_fail}


def zero_divisor_probe(table, dim, label):
    """EXHIBIT, do not sample.  Basis-pair search x = e_i +/- e_j."""
    for i in range(1, dim):
        for j in range(i + 1, dim):
            for s in (1, -1):
                x = [0] * dim
                x[i] = 1
                x[j] = s
                ker = left_mult_kernel(x, table)
                if ker:
                    y = ker[0]
                    prod = table_product(table, x, y)
                    return {"has_zero_divisor": True,
                            "x": [str(v) for v in x],
                            "y": [str(v) for v in y],
                            "product_is_zero": all(v == 0 for v in prod),
                            "x_norm_from_table": str(norm_from_table(table, x))}
    return {"has_zero_divisor": False}


# ═════════════════════════════════════════════════════════════════════════
def family(dim, include_all_splits=True):
    out = [("CD-definite", None, algebra_table(dim, None))]
    rungs = dim.bit_length() - 1
    if rungs >= 1:
        combos = list(itertools.product((-1, 1), repeat=rungs))
        for g in combos:
            if all(v == -1 for v in g):
                continue
            if not include_all_splits and g.count(1) > 1:
                continue
            out.append(("SPLIT-" + "".join("+" if v > 0 else "-" for v in g),
                        g, algebra_table(dim, g)))
    out.append(("RAND-ANTICOMM-A", None,
                rand_anticomm_table(dim, "anticomm-A-%d" % dim)))
    out.append(("RAND-ANTICOMM-B", None,
                rand_anticomm_table(dim, "anticomm-B-%d" % dim)))
    out.append(("RAND-FULL-A", None, rand_full_table(dim, "full-A-%d" % dim)))
    return out


def main():
    emit({"record": "environment",
          "subject_ops": ["algebra_table", "table_product", "cd_norm_sq",
                          "inertia_signature", "left_mult_kernel",
                          "left_mult_is_invertible",
                          "sedenion_zero_divisor_witness", "cd_add",
                          "cd_basis"],
          "oracle": "monomial fast associator, differentially verified against "
                    "the shipped table_product composition"})

    rung_ordering()

    # ── rung 2: commutativity at dim 4 (old dim 2, generator index 2) ──
    for name, g, t in family(4):
        mono = monomial_map(t)
        checks = verify_fast_path(t, mono, 4, label=name)
        counts, fp, op, failures = commutativity_partition(t, mono, 4, 2, name)
        emit({"record": "rung2_commutativity", "rung": "C->H", "dim": 4,
              "old_dim": 2, "algebra": name,
              "gammas": None if g is None else list(g),
              "new_indices": [2, 3], "designated_generator": 2,
              "ordered_basis_pairs": 16,
              "counts": counts,
              "failure_partition": fp,
              "commuting_partition": op,
              "failing_pairs": failures,
              "differential_checks": checks, "differential_disagreements": 0})

    # ── rungs 3/4/5: associator sweeps ──
    for dim, old in ((4, 2), (8, 4), (16, 8), (32, 16)):
        fam = family(dim, include_all_splits=(dim <= 16))
        if dim == 32:
            fam = [f for f in fam if f[0] in ("CD-definite", "SPLIT-+----",
                                              "SPLIT-----+", "RAND-ANTICOMM-A")]
        for name, g, t in fam:
            mono = monomial_map(t)
            checks = verify_fast_path(t, mono, dim, label=name)
            res = assoc_sweep(t, mono, dim, old, name)
            res.update({"record": "assoc_sweep", "dim": dim, "old_dim": old,
                        "algebra": name,
                        "algebra_name": ALGEBRA_NAMES.get(dim, str(dim)),
                        "gammas": None if g is None else list(g),
                        "designated_generator": old,
                        "new_indices": [old, dim - 1],
                        "differential_checks": checks,
                        "differential_disagreements": 0})
            emit(res)

    # ── claim (1): the alternative x composition x zero-divisor contingency ──
    for dim in (2, 4, 8, 16):
        for name, g, t in family(dim):
            mono = monomial_map(t)
            verify_fast_path(t, mono, dim, label=name)
            # alternative?  = every ordered basis triple's associator is
            # ALTERNATING under the 6 permutations
            neither = 0
            for i in range(dim):
                for j in range(dim):
                    for k in range(dim):
                        if classify_symmetry(mono, i, j, k)[0] != "alternating":
                            neither += 1
            comp = composition_probe(t, dim, g, name)
            zd = zero_divisor_probe(t, dim, name)
            emit({"record": "claim1_contingency", "dim": dim, "algebra": name,
                  "gammas": None if g is None else list(g),
                  "is_alternative_basis": neither == 0,
                  "non_alternating_triples": neither,
                  "composition": comp,
                  "zero_divisors": zd,
                  "cell": ("ALT" if neither == 0 else "NOT-ALT") + " / " +
                          ("COMP" if comp["composition_fails"] == 0
                           else "NOT-COMP") + " / " +
                          ("ZD" if zd["has_zero_divisor"] else "NO-ZD")})

    # ── the shipped sedenion zero-divisor witness (EXHIBITED, not sampled) ──
    w = sedenion_zero_divisor_witness()
    emit({"record": "shipped_sedenion_witness",
          "x_form": w["x_form"], "y_form": w["y_form"],
          "x_norm_sq": str(w["x_norm_sq"]), "y_norm_sq": str(w["y_norm_sq"]),
          "product_is_zero": w["product_is_zero"],
          "left_mult_is_invertible_on_x": left_mult_is_invertible(w["x"]),
          "note": "sampling does NOT find this wall; it must be exhibited"})


if __name__ == "__main__":
    main()
