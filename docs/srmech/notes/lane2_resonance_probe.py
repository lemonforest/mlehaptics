"""LANE 2 — ASK THE RESONANCE SURFACE DIRECTLY.

QUESTION: does the EXACT SPECTRAL / HARMONIC signature of a cascade depend on
the ORDER in which the cascade's steps were applied?

SUBJECT (all shipped srmech ops — nothing hand-rolled in the measurement path):
  srmech.amsc.cascade.cayley_dickson.algebra_table   -- the CD/gamma algebra family
  srmech.amsc.cascade.cayley_dickson.table_product   -- the cascade STEP
  srmech.amsc.cascade.cayley_dickson.left_mult_matrix-- accumulator -> matrix (exact Q)
  srmech.amsc.cascade.cayley_dickson.cd_basis        -- the seed accumulator
  srmech.amsc.cascade.cayley_dickson.inertia_signature
  srmech.amsc.cascade.matrix_cascades.char_poly      -- EXACT integer spectral signature
  srmech.amsc.cascade.matrix_cascades.eigvals_exact  -- exact eigen isolation (demo)
  srmech.amsc.harmonics._spectral_scores             -- EXACT Q (dc, mirror, three)
  srmech.amsc.harmonics.classify_chirality_harmonic
  srmech.amsc.format.sha256_bytes                    -- Class A, deterministic control seed

NO floats in any decision.  NO abs().  NO numpy.  NO stdlib fractions.
The only non-shipped arithmetic is F2 bit-XOR for enumerating GL(d,F2) --
srmech ships no GL(d,F2) / F2-linear-algebra op (reported as a missing surface).
"""
import itertools
import json
import sys
import time

from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, table_product, left_mult_matrix, cd_basis, inertia_signature,
)
from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals_exact
from srmech.amsc.harmonics import _spectral_scores, classify_chirality_harmonic
from srmech.amsc.format import sha256_bytes
from srmech.amsc.q import Q

DIM = 8
D = 3                      # grading group (Z/2)^D, 2^D == DIM


# ---------------------------------------------------------------- signatures
def _int_matrix(L):
    """left_mult_matrix -> nested ints.  Class-K style explicit exactness guard:
    every entry must already BE an integer rational (denominator 1)."""
    out = []
    for row in L:
        r = []
        for v in row:
            if v.denominator != 1:
                raise ValueError("non-integer entry in left-mult matrix: %r" % (v,))
            r.append(v.numerator)
        out.append(r)
    return out


_CP_CACHE = {}


def sig_charpoly(acc, table_key, table):
    """EXACT spectral signature: the integer characteristic polynomial of the
    accumulator's left-regular representation.  char_poly is the exact
    ALGEBRAIC substrate of the eigenproblem (trace, det, every elementary
    symmetric function of the spectrum) -- eigenvalues are its roots."""
    key = (table_key, acc)
    hit = _CP_CACHE.get(key)
    if hit is None:
        hit = tuple(char_poly(_int_matrix(left_mult_matrix(acc, table))))
        _CP_CACHE[key] = hit
    return hit


def sig_harmonic(acc):
    """The shipped resonance surface, asked directly, on the accumulator."""
    return tuple(q.as_pair() for q in _spectral_scores(acc))


def sig_harmonic_cp(cp):
    """The shipped resonance surface asked on the exact char-poly coefficients."""
    return tuple(q.as_pair() for q in _spectral_scores(list(cp)))


def sig_elem(acc):
    """The purely ALGEBRAIC baseline: the accumulator itself."""
    return tuple(q.as_pair() for q in acc)


# ---------------------------------------------------------------- the cascade
def step_element(a):
    """A cascade STEP indexed by a grading element a in (Z/2)^D \\ {0}:
    the binomial  1 + e_a.  Non-monomial on purpose -- a monomial step would
    make every ordering land on the same +/- basis element and the question
    would be answered by the sign alone (measured separately below)."""
    return tuple(Q(1) if i in (0, a) else Q(0) for i in range(DIM))


def run_cascade(table, word, monomial=False):
    """acc <- step * acc, LEFT-multiplied, one step per word entry."""
    acc = cd_basis(DIM, 0)
    for a in word:
        s = cd_basis(DIM, a) if monomial else step_element(a)
        acc = table_product(table, s, acc)
    return acc


def distinct_counts(table, table_key, multiset, monomial=False):
    """N_distinct for each signature family over ALL orderings of `multiset`."""
    elems, cps, harms, harmcps = set(), set(), set(), set()
    for word in itertools.permutations(multiset):
        acc = run_cascade(table, word, monomial=monomial)
        cp = sig_charpoly(acc, table_key, table)
        elems.add(sig_elem(acc))
        cps.add(cp)
        harms.add(sig_harmonic(acc))
        harmcps.add(sig_harmonic_cp(cp))
    return {"elem": len(elems), "charpoly": len(cps),
            "harm": len(harms), "harm_cp": len(harmcps)}


# ---------------------------------------------------------------- algebras
def trivial_cocycle_table(dim):
    """DISCRIMINATION CONTROL -- provably ORDER-FREE.
    The group algebra of (Z/2)^D with the trivial cocycle: e_i.e_j = +e_{i^j}.
    Commutative AND associative, so every ordering of any multiset must land on
    the identical accumulator.  If the probe reports order-dependence here the
    probe is broken and every verdict it produces is worthless."""
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            t[i][j][i ^ j] = 1
    return t


def random_anticommutative_table(dim, tag):
    """NEGATIVE CONTROL -- a random anticommutative monomial algebra on the SAME
    (Z/2)^D grading.  e_0 is the identity, e_i^2 = -1 for i != 0, and
    e_i.e_j = -e_j.e_i for i != j != 0.  Signs come from sha256 (Class A) of
    `tag`, so the table is reproducible with no PRNG state."""
    digest = sha256_bytes(tag.encode())
    if isinstance(digest, str):          # the shipped op returns the hex form
        digest = bytes.fromhex(digest)
    bits = []
    for byte in digest:
        for k in range(8):
            bits.append(1 if (byte >> k) & 1 else -1)
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    idx = 0
    sgn = [[0] * dim for _ in range(dim)]
    for i in range(dim):
        sgn[0][i] = 1
        sgn[i][0] = 1
    for i in range(1, dim):
        sgn[i][i] = -1
    for i in range(1, dim):
        for j in range(i + 1, dim):
            s = bits[idx % len(bits)]
            idx += 1
            sgn[i][j] = s
            sgn[j][i] = -s
    for i in range(dim):
        for j in range(dim):
            t[i][j][i ^ j] = sgn[i][j]
    return t


# ---------------------------------------------------------------- transports
def gauge_transport(table, s):
    """(i) GAUGE: diagonal +/-1 basis rescaling  f_i = s_i e_i, s_0 = +1.
    f_i.f_j = s_i s_j e_i e_j = s_i s_j T[i][j][k] e_k = s_i s_j s_k T[i][j][k] f_k
    (s_k = s_k^-1 since s_k = +/-1)."""
    dim = len(table)
    return [[[s[i] * s[j] * s[k] * table[i][j][k] for k in range(dim)]
             for j in range(dim)] for i in range(dim)]


def gl_maps(d):
    """Every element of GL(d,F2) as an index permutation of {0..2^d-1}.
    F2 bit arithmetic (XOR) -- srmech ships no GL(d,F2) op (MISSING SURFACE)."""
    n = 1 << d
    out = []
    for cols in itertools.product(range(n), repeat=d):
        perm = []
        for i in range(n):
            v = 0
            for b in range(d):
                if (i >> b) & 1:
                    v ^= cols[b]
            perm.append(v)
        if len(set(perm)) == n:          # invertible <=> the map is a bijection
            out.append(tuple(perm))
    return out


def gl_transport(table, perm):
    """(ii) GL(d,F2): relabel the ORDERED BASIS of the grading group.
    new[perm[i]][perm[j]][perm[k]] = old[i][j][k].  perm is F2-linear so
    perm[i^j] == perm[i]^perm[j] -- the monomial grading survives, and
    perm[0] == 0 so e_0 stays the identity."""
    dim = len(table)
    new = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                v = table[i][j][k]
                if v:
                    new[perm[i]][perm[j]][perm[k]] = v
    return new


def table_key_of(table):
    return json.dumps(table, separators=(",", ":"))


# ---------------------------------------------------------------- report
def emit(rec):
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    t_start = time.time()
    import srmech
    from srmech.amsc import _native
    emit({"kind": "env", "srmech": srmech.__version__,
          "has_native": _native.HAS_NATIVE, "python": sys.version.split()[0]})

    O = algebra_table(DIM)                       # definite octonions
    SO = algebra_table(DIM, (1, -1, -1))         # split-octonions (same dim)
    TRIV = trivial_cocycle_table(DIM)            # order-free discrimination control
    RANDS = [random_anticommutative_table(DIM, "lane2-random-anticommutative-%d" % k)
             for k in range(5)]

    algebras = [("octonion", O), ("split_octonion", SO),
                ("TRIVIAL_COCYCLE_control", TRIV)]
    algebras += [("random_anticomm_%d" % k, t) for k, t in enumerate(RANDS)]

    for name, tbl in algebras:
        try:
            ins = inertia_signature(tbl)
            emit({"kind": "algebra", "name": name,
                  "trace_signature": list(ins["signature"]),
                  "norm_signature": list(ins["norm_signature"])})
        except Exception as exc:                       # control tables may be degenerate
            emit({"kind": "algebra", "name": name, "inertia_error": repr(exc)})

    # --------------------------------------------------------------- STEP 2/3
    # All 3-subsets of the 7 nonzero grading elements.  GL(3,F2) has exactly TWO
    # orbits on these: 28 linearly INDEPENDENT triples (bases) and 7 DEPENDENT
    # triples (the Fano lines, a^b^c == 0).  That orbit split is the whole bite
    # of condition (ii) -- a quantity that varies WITHIN an orbit is our own
    # labelling leaking in.
    multisets = list(itertools.combinations(range(1, DIM), 3))
    assert len(multisets) == 35

    def orbit_of(ms):
        return "dependent" if (ms[0] ^ ms[1] ^ ms[2]) == 0 else "independent"

    for name, tbl in algebras:
        key = table_key_of(tbl)
        for mono in (False, True):
            per = {}
            for ms in multisets:
                per[ms] = distinct_counts(tbl, key + ("|M" if mono else "|B"),
                                          ms, monomial=mono)
            for fam in ("elem", "charpoly", "harm", "harm_cp"):
                ind = sorted({per[m][fam] for m in multisets if orbit_of(m) == "independent"})
                dep = sorted({per[m][fam] for m in multisets if orbit_of(m) == "dependent"})
                allv = sorted({per[m][fam] for m in multisets})
                emit({"kind": "Ndistinct", "algebra": name,
                      "steps": "monomial" if mono else "binomial",
                      "family": fam,
                      "values_all": allv,
                      "values_independent_orbit": ind,
                      "values_dependent_orbit": dep,
                      "constant_on_GL_orbits": len(ind) == 1 and len(dep) == 1,
                      "orbit_separating": ind != dep})

    emit({"kind": "timing", "phase": "step23", "seconds": round(time.time() - t_start, 1)})


if __name__ == "__main__":
    main()
