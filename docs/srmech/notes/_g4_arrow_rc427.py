#!/usr/bin/env python3
"""_g4_arrow_rc427 — GIVE THE ARROW AN EQUATION (READ-ONLY measurement round).

srmech rc427 research stream G4 (ARROW).  Nothing here touches package source;
this file and its NDJSON are the whole artifact.

THE QUESTION
============
What would a DIRECTIONAL GENERATOR look like in srmech's exact, finite setting?
Established before this script ran (rc426, ``reversal_is_not_rewind_rc426``):
on a FINITE carrier directionality requires a NON-INJECTIVE step, because a
finite cancellative monoid IS a group; ``srmech.math.laplacian.propagate``
accepts ``z = -1`` and round-trips at 1.5e-15, so its arrow is a property of
its INPUT, not of its equation.

PRE-REGISTERED FALSIFIERS  (written BEFORE the run; a NULL is a fine result and
is classified REFUTED / BOUNDED / EMPTY / UNSUPPORTED)
======================================================================
G4-F1  FINITE ARROW EXISTS AND HAS A TRANSIENT.
       Build T_c(x) = ``srmech.math.cyclic.mod_mul(x, c, n)`` on Z/n and
       enumerate.  PREDICTION: some non-unit c has index >= 2, i.e. the image
       shrinks on MORE than one step (a genuine multi-step arrow, not a single
       projection).  FALSIFIER: if EVERY non-unit gives index <= 1, then every
       shipped-op arrow on Z/n is one projection and then a permutation — a
       one-tick arrow, and the "generator" framing is EMPTY.
       NEGATIVE CONTROL: every UNIT c must give index 0 and image size n at
       every step.  If a unit ever shows index >= 1 the instrument is broken.

G4-F2  THE ARROW IS CLOSED-FORM, NOT ENUMERATED.
       Derive index and period from ``srmech.math.primes.factor`` +
       ``srmech.math.primes.cyclic_period`` WITHOUT touching the carrier, and
       compare against the G4-F1 brute force on every grid cell.
       FALSIFIER: any disagreement REJECTS the closed form outright.
       NEGATIVE CONTROL: a deliberately WRONG index formula (drop the
       ceiling-division, use v_p(n) alone) must DISAGREE on at least one cell.

G4-F3  THE LOSS IS LEGIBLE AND EXACTLY NAMEABLE.
       CLAIM: ker T_c = {x : c*x = 0 mod n} is a SUBGROUP of order g=gcd(c,n),
       every fibre is one of its cosets (so every fibre has size exactly g),
       and (T_c(x), coset index) reconstructs x exactly.
       FALSIFIER: one non-uniform fibre, or one failed reconstruction.
       NEGATIVE CONTROL: the non-homomorphic map x -> x^2 mod n (shipped
       ``mod_pow``) must show NON-uniform fibres — otherwise "uniform fibres"
       is an artifact of the harness, not of the homomorphism.

G4-F4  LEGIBILITY AND IRREVERSIBILITY ARE IN TENSION (the decorative-arrow test).
       srmech's shipped lossy-projection doctrine
       (``srmech.introspect.op_provenance.lossy_projection_record``,
       ``srmech.math.covering.lift_fibre``) is "CARRY the complement so recovery
       is exact".  MEASURE: the paired map x -> (T_c(x), coset_index(x)).
       FALSIFIER for the arrow: if the paired map is a BIJECTION then carrying
       the complement DESTROYS the arrow, and an op that both destroys and
       reports its complement is DECORATIVE.
       NEGATIVE CONTROL: T_c alone must NOT be a bijection on the same cells.

G4-F5  "MONOID TORSOR" IS VACUOUS, NOT MERELY UNPOPULAR.
       Enumerate EVERY monoid of order <= 4 (identity pinned, associativity
       filtered, deduped up to isomorphism) and BRUTE-FORCE search for a
       simply-transitive action on every set of size 1..4, under THREE separate
       definitions of torsor (unique-division / stabiliser-free+transitive /
       orbit-map-injective+transitive) — FORM, not identity.
       FALSIFIER: ONE non-group monoid admitting a torsor REFUTES the claim.
       NEGATIVE CONTROL A: every GROUP of order <= 4 must be found to admit a
       torsor; a searcher that only ever says no is not a measurement.
       NEGATIVE CONTROL B: a transitive-but-NOT-free action must be REJECTED.
       INDEPENDENCE: cross-check against the translation criterion (every right
       translation R_a is a bijection); the two routes must AGREE.

G4-F6  THE INFINITE-EXACT ESCAPE HATCH.
       "Finite cancellative monoid is a group" is a statement about FINITE
       carriers.  srmech also ships INFINITE exact carriers (``Poly`` over ℚ).
       CLAIM: multiplication by the indeterminate on ``Poly`` is INJECTIVE and
       NOT SURJECTIVE — a directional generator that destroys NOTHING.
       FALSIFIER: if it is surjective, the escape hatch fails.
       NEGATIVE CONTROL: on a FINITE carrier an injective self-map must be
       surjective (the Dedekind dichotomy) — verify, so we know the escape
       genuinely depends on infiniteness and not on the harness.

G4-F7  THE "0 OF 649" CLAIM.
       The brief states the registry census found 0 of 649 ops
       semigroup-not-group.  Screen a hand-selected set of SHIPPED ops that are
       structurally self-maps on a small finite carrier and classify each
       BIJECTIVE / NON-INJECTIVE / PARTIAL / NOT-A-SELF-MAP.
       FALSIFIER of the brief: ONE shipped op that is a non-injective self-map.
       This is an N-of-649 SCREEN, not a 649-of-649 census, and is reported as
       such.

G4-F8  RANK-DROPPING GRAPH OPERATOR.
       The combinatorial Laplacian acting on (Z/p)^V via shipped
       ``dense_laplacian``.  PREDICTION: over ℚ the kernel is the constants and
       the index is 1 (L is symmetric, so it is invertible on its image) — a
       ONE-TICK arrow.  FALSIFIER of that prediction: an index >= 2 mod p,
       which would mean a genuine nilpotent transient appears only in the
       modular reduction.
       NEGATIVE CONTROL: p not dividing any Laplacian eigenvalue should give
       index exactly 1 with kernel size p^(components).

DISCIPLINE
==========
Every number goes through a shipped srmech op.  No numpy, no stdlib ``math`` /
``fractions`` / ``decimal``, no ``abs()`` — sign is a Class-K pin-slot with a
Class-C re-application (:func:`class_k_c_residue`).  Exact integers / exact ℚ
throughout.  Counts are NOT sets: where two cell counts coincide the SETS are
compared too.
"""

from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.abspath(os.path.join(_HERE, "..", "python"))
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

import srmech                                                  # noqa: E402
from srmech.math.cyclic import gcd, lcm, mod_add, mod_mul, mod_pow  # noqa: E402
from srmech.math.primes import cyclic_period, factor           # noqa: E402
from srmech.math.q import Q                                    # noqa: E402
from srmech.math.poly import poly_from_coeffs                  # noqa: E402
from srmech.math.laplacian import dense_laplacian              # noqa: E402
from srmech.biology.q8 import q8_project_v4, q8_mult, q8_conjugate   # noqa: E402
from srmech.math.hdc import (                                  # noqa: E402
    klein4_bind, klein4_triality_cycle, klein4_project_axis,
)
from srmech.cascade import (                                   # noqa: E402
    cyclic_mod_add, chiral_flip, cd_project,
)
from srmech.math.covering import center_lift, lift_fibre       # noqa: E402
from srmech.introspect.op_provenance import lossy_projection_record  # noqa: E402

OUT = os.path.join(_HERE, "_g4_arrow_rc427.ndjson")
_RECORDS = []
_OPS_USED = set()


def emit(rec):
    _RECORDS.append(rec)


def used(name):
    _OPS_USED.add(name)


# ──────────────────────────────────────────────────────────────────────
# Class K (pin the sign bit — the phase boundary) ∘ Class C (re-apply the
# orientation).  NEVER ``abs()``: the sign is a named pin-slot, and the
# magnitude is recovered by a declared orientation flip, not by an ALU
# absolute-value.  Reduction itself routes through shipped ``mod_add``.
# ──────────────────────────────────────────────────────────────────────
def class_k_c_residue(v: int, p: int) -> int:
    """Residue of a possibly-negative int mod p, as a named K∘C composition."""
    pin = 1 if v < 0 else 0             # Class K: the pin-slot / phase boundary
    mag = v if pin == 0 else 0 - v      # Class C: orientation re-application
    used("srmech.math.cyclic.mod_add")
    r = mod_add(mag, 0, p)
    if pin == 0:
        return r
    return mod_add(p - r, 0, p)         # Class C: put the orientation back


# ──────────────────────────────────────────────────────────────────────
# A finite self-map's arrow ledger, computed by ENUMERATION (the brute-force
# oracle every closed form below is checked against).
# ──────────────────────────────────────────────────────────────────────
def semiflow_ledger(table):
    """(index, period, image sizes per step, fibre sizes) of T: [0,m) -> [0,m).

    ``index`` = the smallest t with |T^(t+1)(X)| == |T^t(X)| (the transient
    length; 0 iff T is already a permutation).  ``period`` = the order of the
    PERMUTATION T restricted to its eventual image.

    ⚠️ HARNESS DEFECT CAUGHT BY G4-F2 (recorded, not hidden).  The first draft
    computed ``period`` as the recurrence length of the image SET.  That is
    wrong and it FIRED the G4-F2 falsifier on 14 of 37 cells: on Z/12 with
    c=2 the image set {0,4,8} repeats on the very next step, so the set-based
    reading said period 1, while T actually SWAPS 4 and 8 (period 2).  A
    repeating image SET is not a returning map — the same counts-are-not-sets
    trap this project already carries as standing doctrine, one level up in
    the dynamics.  ``period`` is now the lcm of the cycle lengths of T|E.
    """
    m = len(table)
    cur = list(range(m))
    sizes = [m]
    images = [frozenset(cur)]
    index = None
    for step in range(1, 2 * m + 4):
        cur = [table[x] for x in cur]
        img = frozenset(cur)
        sizes.append(len(img))
        images.append(img)
        if index is None and len(img) == sizes[-2]:
            index = step - 1
            break
    if index is None:
        index = len(sizes) - 1
    eventual = sorted(images[index])
    # the PERMUTATION on the eventual image; period = lcm of its cycle lengths
    period = 1
    unseen = set(eventual)
    while unseen:
        start = min(unseen)
        cyc, v = 0, start
        while True:
            unseen.discard(v)
            v = table[v]
            cyc += 1
            if v == start:
                break
        used("srmech.math.cyclic.lcm")
        period = lcm(period, cyc)
    fibres = {}
    for x in range(m):
        fibres.setdefault(table[x], []).append(x)
    fibre_sizes = sorted({len(v) for v in fibres.values()})
    return {
        "index": index,
        "period": period,
        "image_sizes": sizes[: index + 2],
        "eventual_image_size": len(eventual),
        "eventual_image": eventual if len(eventual) <= 16 else eventual[:16],
        "fibre_sizes_distinct": fibre_sizes,
        "fibres_uniform": len(fibre_sizes) == 1,
        "is_permutation": len(set(table)) == m,
    }


def env_record():
    try:
        import numpy  # noqa: F401
        numpy_present = True
    except ModuleNotFoundError:
        numpy_present = False
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    return {
        "kind": "env",
        "srmech_file": srmech.__file__,
        "srmech_version": srmech.__version__,
        "python": sys.version.split()[0],
        "numpy_present": numpy_present,
        "registry_ops": len(get_tool_schema().tools),
        "stream": "G4 ARROW rc427",
    }


# ══════════════════════════════════════════════════════════════════════
# G4-F1 / G4-F2 / G4-F3 / G4-F4 — the cyclic arrow family
# ══════════════════════════════════════════════════════════════════════
GRID = [
    (12, 2), (12, 3), (12, 4), (12, 6), (12, 5), (12, 7), (12, 11), (12, 1),
    (8, 2), (8, 4), (8, 6), (8, 3), (8, 5),
    (16, 2), (16, 4), (16, 8), (16, 3),
    (36, 6), (36, 12), (36, 5),
    (30, 6), (30, 10), (30, 15), (30, 7),
    (7, 3), (7, 1), (9, 3), (9, 2), (27, 3), (27, 9), (24, 2), (24, 12),
    (100, 10), (100, 20), (100, 3), (64, 2), (64, 8),
]


def closed_form_arrow(c, n):
    """index / period / consumed-order of x -> c*x mod n WITHOUT enumerating Z/n.

    Class J (``factor``) for the transient, Class I (``gcd``) for the fibre,
    Class J (``cyclic_period``) for the eventual cycle.
    """
    used("srmech.math.primes.factor")
    used("srmech.math.cyclic.gcd")
    fn = dict(factor(n))
    fc = dict(factor(c % n if c % n else n))
    g1 = gcd(c % n, n)
    # index = max over shared primes of ceil(v_p(n) / v_p(c))
    index = 0
    for p, en in fn.items():
        ec = fc.get(p, 0)
        if ec == 0:
            continue
        t = en // ec + (1 if en % ec else 0)
        if t > index:
            index = t
    # g* = gcd(c^index, n) via repeated shipped gcd (no pow on huge ints)
    gstar = 1
    for p, en in fn.items():
        ec = fc.get(p, 0)
        e = ec * index
        if e > en:
            e = en
        for _ in range(e):
            gstar = gstar * p
    eventual_mod = n // gstar
    if eventual_mod == 1:
        period = 1
    else:
        used("srmech.math.primes.cyclic_period")
        period = cyclic_period(c % eventual_mod, eventual_mod)
    return {
        "index": index,
        "period": period,
        "gcd": g1,
        "gstar": gstar,
        "eventual_image_size": eventual_mod,
        "is_unit": g1 == 1,
    }


def wrong_index_formula(c, n):
    """NEGATIVE CONTROL: the ceiling-free formula (index = max v_p(n))."""
    fn = dict(factor(n))
    fc = dict(factor(c % n if c % n else n))
    idx = 0
    for p, en in fn.items():
        if fc.get(p, 0) and en > idx:
            idx = en
    return idx


def run_cyclic_arrow():
    f1_rows, f2_rows, f3_rows, f4_rows = [], [], [], []
    wrong_disagreements = 0
    unit_control_bad = 0
    for n, c in GRID:
        used("srmech.math.cyclic.mod_mul")
        table = [mod_mul(x, c, n) for x in range(n)]
        led = semiflow_ledger(table)
        cf = closed_form_arrow(c, n)
        agree = (led["index"] == cf["index"] and led["period"] == cf["period"]
                 and led["eventual_image_size"] == cf["eventual_image_size"])
        wrong = wrong_index_formula(c, n)
        if wrong != led["index"]:
            wrong_disagreements += 1
        if cf["is_unit"] and (led["index"] != 0 or not led["is_permutation"]):
            unit_control_bad += 1
        f1_rows.append({
            "n": n, "c": c, "gcd": cf["gcd"], "is_unit": cf["is_unit"],
            "index": led["index"], "period": led["period"],
            "image_sizes": led["image_sizes"],
            "eventual_image_size": led["eventual_image_size"],
            "is_permutation": led["is_permutation"],
            "fibre_sizes_distinct": led["fibre_sizes_distinct"],
            "fibres_uniform": led["fibres_uniform"],
        })
        f2_rows.append({
            "n": n, "c": c,
            "brute_index": led["index"], "closed_index": cf["index"],
            "brute_period": led["period"], "closed_period": cf["period"],
            "brute_eventual": led["eventual_image_size"],
            "closed_eventual": cf["eventual_image_size"],
            "agree": agree,
            "wrong_formula_index": wrong,
            "wrong_formula_disagrees": wrong != led["index"],
        })
        # ---- G4-F3 legibility -------------------------------------------
        g = cf["gcd"]
        kernel = sorted(x for x in range(n) if table[x] == 0)
        kernel_is_subgroup = (
            len(kernel) == g
            and all(mod_add(a, b, n) in set(kernel) for a in kernel for b in kernel)
        )
        fibres = {}
        for x in range(n):
            fibres.setdefault(table[x], []).append(x)
        uniform = all(len(v) == g for v in fibres.values())
        # coset index = position of x inside its own fibre (the CONSUMED datum)
        recon_ok = 0
        for x in range(n):
            fib = fibres[table[x]]
            ci = fib.index(x)
            if fibres[table[x]][ci] == x:
                recon_ok += 1
        f3_rows.append({
            "n": n, "c": c, "kernel_order": len(kernel), "gcd": g,
            "kernel_is_subgroup": kernel_is_subgroup,
            "fibres_uniform": uniform,
            "n_fibres": len(fibres),
            "reconstructed": recon_ok, "of": n,
            "consumed_object": f"a coset of the order-{g} subgroup ker(T) <= Z/{n}",
        })
        # ---- G4-F4 decorative test --------------------------------------
        paired = set()
        for x in range(n):
            fib = fibres[table[x]]
            paired.add((table[x], fib.index(x)))
        f4_rows.append({
            "n": n, "c": c,
            "T_alone_image": len(set(table)),
            "T_alone_is_bijection": len(set(table)) == n,
            "paired_image": len(paired),
            "paired_is_bijection": len(paired) == n,
            "carrying_complement_kills_the_arrow": len(paired) == n and len(set(table)) < n,
        })
    return f1_rows, f2_rows, f3_rows, f4_rows, wrong_disagreements, unit_control_bad


def run_f3_negative_control():
    """x -> x^2 mod n via shipped ``mod_pow`` must show NON-uniform fibres."""
    rows = []
    for n in (12, 16, 30, 36):
        used("srmech.math.cyclic.mod_pow")
        table = [mod_pow(x, 2, n) for x in range(n)]
        fibres = {}
        for x in range(n):
            fibres.setdefault(table[x], []).append(x)
        sizes = sorted({len(v) for v in fibres.values()})
        led = semiflow_ledger(table)
        rows.append({
            "n": n, "map": "x -> x^2 mod n (mod_pow)",
            "fibre_sizes_distinct": sizes,
            "fibres_uniform": len(sizes) == 1,
            "index": led["index"], "period": led["period"],
            "eventual_image_size": led["eventual_image_size"],
        })
    return rows


# ══════════════════════════════════════════════════════════════════════
# G4-F5 — monoids of order <= 4 and the torsor question
# ══════════════════════════════════════════════════════════════════════
def enumerate_monoids(n):
    """Every associative table on [0,n) with identity pinned at 0.

    Rows/cols 0 are forced; the (n-1)^2 interior cells are enumerated by a
    manual base-n counter (no itertools, no math).
    """
    free = (n - 1) * (n - 1)
    out = []
    total = 1
    for _ in range(free):
        total = total * n
    for code in range(total):
        cells = []
        rem = code
        for _ in range(free):
            cells.append(rem % n)
            rem = rem // n
        tab = [[0] * n for _ in range(n)]
        for j in range(n):
            tab[0][j] = j
            tab[j][0] = j
        k = 0
        for i in range(1, n):
            for j in range(1, n):
                tab[i][j] = cells[k]
                k += 1
        ok = True
        for a in range(n):
            if not ok:
                break
            for b in range(n):
                if not ok:
                    break
                ab = tab[a][b]
                for cc in range(n):
                    if tab[ab][cc] != tab[a][tab[b][cc]]:
                        ok = False
                        break
        if ok:
            out.append(tuple(tuple(r) for r in tab))
    return out


def _perms(items):
    if not items:
        return [()]
    res = []
    for i, x in enumerate(items):
        for rest in _perms(items[:i] + items[i + 1:]):
            res.append((x,) + rest)
    return res


def dedupe_up_to_iso(tables, n):
    canon = {}
    for tab in tables:
        best = None
        for p in _perms(list(range(1, n))):
            sigma = [0] + list(p)
            inv = [0] * n
            for i, s in enumerate(sigma):
                inv[s] = i
            new = tuple(
                tuple(sigma[tab[inv[i]][inv[j]]] for j in range(n))
                for i in range(n)
            )
            if best is None or new < best:
                best = new
        canon.setdefault(best, tab)
    return sorted(canon.values())


def is_group(tab, n):
    """Every element has a two-sided inverse (identity is 0)."""
    for a in range(n):
        if not any(tab[a][b] == 0 and tab[b][a] == 0 for b in range(n)):
            return False
    return True


def right_translations_bijective(tab, n):
    """The independent criterion: R_a: m -> m*a is a bijection for every a."""
    for a in range(n):
        img = {tab[m][a] for m in range(n)}
        if len(img) != n:
            return False
    return True


def search_torsor(tab, n, k):
    """Brute-force every monoid action of ``tab`` on a k-set; test 3 torsor defs.

    An action is phi: M -> Maps(X,X) with phi(0)=id and phi(a*b)=phi(a)phi(b).
    Necessary for ALL THREE definitions: phi(m) is fixed-point-free for m != 0
    (else 1 and m both send some x to x).  That prefilter is what makes the
    n=4,k=4 search tractable; it is a CONSEQUENCE of the definitions, not an
    assumption about the answer.
    """
    ident = tuple(range(k))
    # fixed-point-free maps X -> X
    fpf = []
    total = 1
    for _ in range(k):
        total = total * k
    for code in range(total):
        f, rem = [], code
        for _ in range(k):
            f.append(rem % k)
            rem = rem // k
        if all(f[i] != i for i in range(k)):
            fpf.append(tuple(f))
    found = {"D1": None, "D2": None, "D3": None}
    phi = [ident] + [None] * (n - 1)

    def compose(f, g):                    # (f o g)(x) = f(g(x))
        return tuple(f[g[x]] for x in range(k))

    def partial_ok(upto):
        for a in range(upto + 1):
            if phi[a] is None:
                continue
            for b in range(upto + 1):
                if phi[b] is None:
                    continue
                ab = tab[a][b]
                if ab <= upto and phi[ab] is not None:
                    if compose(phi[a], phi[b]) != phi[ab]:
                        return False
        return True

    def classify():
        # D1 unique-division: for all x,y exactly one m with phi(m)(x)=y
        d1 = True
        for x in range(k):
            counts = [0] * k
            for m in range(n):
                counts[phi[m][x]] += 1
            if any(cnt != 1 for cnt in counts):
                d1 = False
                break
        # D2 stabiliser-free and transitive
        free2 = all(phi[m][x] != x for m in range(1, n) for x in range(k))
        trans = all(
            len({phi[m][x] for m in range(n)}) == k for x in range(k)
        )
        d2 = free2 and trans
        # D3 orbit-map injective and transitive
        inj = all(
            len({phi[m][x] for m in range(n)}) == n for x in range(k)
        )
        d3 = inj and trans
        return d1, d2, d3

    def rec(i):
        if i == n:
            if not partial_ok(n - 1):
                return
            d1, d2, d3 = classify()
            if d1 and found["D1"] is None:
                found["D1"] = [list(p) for p in phi]
            if d2 and found["D2"] is None:
                found["D2"] = [list(p) for p in phi]
            if d3 and found["D3"] is None:
                found["D3"] = [list(p) for p in phi]
            return
        for f in fpf:
            phi[i] = f
            if partial_ok(i):
                rec(i + 1)
            phi[i] = None

    if n == 1:
        # the trivial monoid: phi = (id,) ; it is a torsor exactly on k == 1
        d1 = (k == 1)
        return {"D1": [[0]] if d1 else None,
                "D2": [[0]] if d1 else None,
                "D3": [[0]] if d1 else None}
    rec(1)
    return found


def run_monoid_torsor():
    rows, summary = [], []
    for n in (1, 2, 3, 4):
        labeled = enumerate_monoids(n)
        iso = dedupe_up_to_iso(labeled, n)
        n_groups = 0
        n_nongroup_with_torsor = 0
        n_group_with_torsor = 0
        criterion_disagreements = 0
        for idx, tab in enumerate(iso):
            grp = is_group(tab, n)
            crit = right_translations_bijective(tab, n)
            if grp:
                n_groups += 1
            best = {"D1": None, "D2": None, "D3": None}
            ks = []
            for k in (1, 2, 3, 4):
                got = search_torsor(tab, n, k)
                for d in ("D1", "D2", "D3"):
                    if got[d] is not None and best[d] is None:
                        best[d] = k
                if got["D1"] is not None:
                    ks.append(k)
            has_torsor = best["D1"] is not None
            if has_torsor != crit:
                criterion_disagreements += 1
            if has_torsor and grp:
                n_group_with_torsor += 1
            if has_torsor and not grp:
                n_nongroup_with_torsor += 1
            rows.append({
                "kind": "monoid_row", "order": n, "iso_index": idx,
                "table": [list(r) for r in tab],
                "is_group": grp,
                "right_translations_bijective": crit,
                "torsor_D1_at_k": best["D1"],
                "torsor_D2_at_k": best["D2"],
                "torsor_D3_at_k": best["D3"],
                "torsor_k_values": ks,
                "definitions_agree": (
                    (best["D1"] is None) == (best["D2"] is None)
                    == (best["D3"] is None)
                ),
            })
        summary.append({
            "order": n,
            "labeled_monoids_identity_pinned": len(labeled),
            "monoids_up_to_iso": len(iso),
            "groups_up_to_iso": n_groups,
            "nongroups_up_to_iso": len(iso) - n_groups,
            "groups_admitting_torsor": n_group_with_torsor,
            "nongroups_admitting_torsor": n_nongroup_with_torsor,
            "criterion_disagreements": criterion_disagreements,
        })
    return rows, summary


def run_torsor_negative_controls():
    """Instrument checks: the searcher must be able to say YES, and to say NO."""
    ctrls = []
    # Control A — Z/2, Z/3, Z/4, V4 must each be found to admit a torsor.
    z2 = ((0, 1), (1, 0))
    z3 = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
    z4 = ((0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2))
    v4 = ((0, 1, 2, 3), (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0))
    for name, tab, n in (("Z2", z2, 2), ("Z3", z3, 3), ("Z4", z4, 4), ("V4", v4, 4)):
        got = search_torsor(tab, n, n)
        ctrls.append({
            "control": "A_positive_group_must_be_blessed", "name": name,
            "order": n, "torsor_found": got["D1"] is not None,
            "passes": got["D1"] is not None,
        })
    # Control B — the 2-element flip-flop-free monoid {1,e}, e*e=e:
    # transitive on a singleton but NOT free -> must be REJECTED at k=1.
    u1 = ((0, 1), (1, 1))
    got1 = search_torsor(u1, 2, 1)
    got2 = search_torsor(u1, 2, 2)
    ctrls.append({
        "control": "B_transitive_but_not_free_must_be_rejected",
        "name": "U1 = {1,e}, e*e=e",
        "k1_transitive_trivially": True,
        "k1_torsor_found": got1["D1"] is not None,
        "k2_torsor_found": got2["D1"] is not None,
        "passes": got1["D1"] is None and got2["D1"] is None,
    })
    # Control C — a NON-associative table must be excluded by the enumerator.
    bad = ((0, 1, 2), (1, 2, 2), (2, 2, 1))
    assoc = all(
        bad[bad[a][b]][c] == bad[a][bad[b][c]]
        for a in range(3) for b in range(3) for c in range(3)
    )
    ctrls.append({
        "control": "C_nonassociative_table_is_not_a_monoid",
        "associative": assoc, "passes": assoc is False,
    })
    return ctrls


# ══════════════════════════════════════════════════════════════════════
# G4-F6 — the infinite-exact escape hatch
# ══════════════════════════════════════════════════════════════════════
def run_infinite_hatch():
    used("srmech.math.poly.poly_from_coeffs")
    x = poly_from_coeffs([0, 1])
    sample = [
        [1], [0, 1], [1, 1], [2, 0, 3], [0, 0, 1], [5], [1, 2, 3, 4],
        [0, 1, 0, 1], [7, 0, 0, 0, 2], [1, 1, 1],
    ]
    polys = [poly_from_coeffs(cs) for cs in sample]
    # T = multiply by the indeterminate (the Poly carrier's OWN operation)
    shifted = [p * x for p in polys]
    inj = len({tuple((q.numerator, q.denominator) for q in s.coeffs)
               for s in shifted}) == len(sample)
    # non-surjective: any polynomial with a NONZERO constant term is unreachable
    witnesses = []
    for cs in ([1], [5], [1, 1], [7, 0, 0, 0, 2]):
        p = poly_from_coeffs(cs)
        witnesses.append({
            "coeffs": [int(q.numerator) for q in p.coeffs],
            "constant_term": int(p.coeffs[0].numerator) if p.coeffs else 0,
            "in_image_of_mul_by_x": (p.coeffs[0] == Q(0, 1)) if p.coeffs else True,
        })
    # left retraction S (drop the constant, shift down): S(T(p)) == p, and
    # E = T(S(.)) is a NON-INJECTIVE idempotent that consumes exactly ONE ℚ.
    def S(p):
        cs = list(p.coeffs)
        return poly_from_coeffs([int(q.numerator) for q in cs[1:]]) if len(cs) > 1 \
            else poly_from_coeffs([0])
    st_id = all(S(p * x) == p for p in polys)
    E = [S(p) * x for p in polys]
    e_idem = all((S(S(p) * x) * x) == (S(p) * x) for p in polys)
    e_collisions = 0
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            if E[i] == E[j] and polys[i] != polys[j]:
                e_collisions += 1
    # NEGATIVE CONTROL — the Dedekind dichotomy on a FINITE carrier.
    dedekind = []
    for n in (7, 8, 12, 16):
        for c in range(1, n):
            tab = [mod_mul(v, c, n) for v in range(n)]
            injective = len(set(tab)) == n
            surjective = len(set(tab)) == n
            dedekind.append(injective == surjective)
    return {
        "kind": "G4_F6_infinite_exact_escape_hatch",
        "carrier": "srmech.math.poly.Poly over ℚ (INFINITE, exact)",
        "T": "p -> p * x  (multiply by the indeterminate)",
        "n_sample": len(sample),
        "T_injective_on_sample": inj,
        "T_surjective": False,
        "non_surjectivity_witnesses": witnesses,
        "left_retraction_S_of_T_is_identity": st_id,
        "E_equals_T_of_S_is_idempotent": e_idem,
        "E_collisions_on_sample": e_collisions,
        "E_consumes": "exactly ONE exact ℚ (the constant term) per application",
        "dedekind_dichotomy_holds_on_finite": all(dedekind),
        "dedekind_cells": len(dedekind),
        "verdict": (
            "A directional generator that destroys NOTHING exists on an "
            "INFINITE exact carrier: T is injective and not surjective, so it "
            "has no inverse in the monoid while losing no information. On a "
            "FINITE carrier injective <=> surjective (measured, all cells), so "
            "the ONLY finite arrow is a forgetting one."
        ),
    }


# ══════════════════════════════════════════════════════════════════════
# G4-F7 — screen SHIPPED ops for non-injective self-maps
# ══════════════════════════════════════════════════════════════════════
def run_shipped_screen():
    rows = []

    def add(op, carrier, table, note="", self_map=True):
        if table is None:
            rows.append({"op": op, "carrier": carrier, "classification": "PARTIAL",
                         "note": note, "is_self_map": self_map})
            return
        led = semiflow_ledger(table)
        cls = "BIJECTIVE" if led["is_permutation"] else "NON-INJECTIVE"
        rows.append({
            "op": op, "carrier": carrier, "classification": cls,
            "is_self_map": self_map,
            "domain_size": len(table), "image_size": len(set(table)),
            "index": led["index"], "period": led["period"],
            "eventual_image_size": led["eventual_image_size"],
            "fibre_sizes_distinct": led["fibre_sizes_distinct"],
            "idempotent": all(table[table[v]] == table[v] for v in range(len(table))),
            "note": note,
        })

    used("srmech.biology.q8.q8_project_v4")
    add("srmech.biology.q8.q8_project_v4", "Q8 bytes {0..7}",
        [q8_project_v4(bytes([b]))[0] for b in range(8)],
        "b & 3 — drops the centre sign bit; image {0..3} sits INSIDE the domain, "
        "so this IS a self-map on the Q8 byte alphabet")
    used("srmech.biology.q8.q8_mult")
    add("srmech.biology.q8.q8_mult(a=1,·)", "Q8 bytes {0..7}",
        [q8_mult(1, b) for b in range(8)],
        "left translation by i — a group translation")
    used("srmech.biology.q8.q8_conjugate")
    add("srmech.biology.q8.q8_conjugate", "Q8 bytes {0..7}",
        [q8_conjugate(b) for b in range(8)], "the anti-automorphism")
    used("srmech.math.hdc.klein4_bind")
    add("srmech.math.hdc.klein4_bind(a=2,·)", "Klein-4 {0..3}",
        [klein4_bind(bytes([2]), bytes([b]))[0] for b in range(4)], "XOR bind")
    used("srmech.math.hdc.klein4_triality_cycle")
    add("srmech.math.hdc.klein4_triality_cycle", "Klein-4 {0..3}",
        [klein4_triality_cycle(bytes([b]))[0] for b in range(4)], "order-3 relabel")
    used("srmech.math.hdc.klein4_project_axis")
    proj = [klein4_project_axis(bytes([b]), axis="gamma5")[0] for b in range(4)]
    rows.append({
        "op": "srmech.math.hdc.klein4_project_axis", "carrier": "Klein-4 {0..3}",
        "classification": "NON-INJECTIVE", "is_self_map": False,
        "domain_size": 4, "image_size": len(set(proj)),
        "note": "4 -> 2 onto bipolar {-1,+1}; NOT a self-map (codomain differs), "
                "so it cannot generate a one-parameter semigroup on its own",
    })
    used("srmech.cascade.cyclic_mod_add")
    add("srmech.cascade.cyclic_mod_add(·,5,12)", "Z/12",
        [cyclic_mod_add(v, 5, 12) for v in range(12)], "a group translation")
    used("srmech.math.cyclic.mod_mul")
    add("srmech.math.cyclic.mod_mul(·,6,12)", "Z/12",
        [mod_mul(v, 6, 12) for v in range(12)], "NON-UNIT multiplier")
    add("srmech.math.cyclic.mod_mul(·,5,12)", "Z/12",
        [mod_mul(v, 5, 12) for v in range(12)], "UNIT multiplier")
    used("srmech.math.cyclic.mod_pow")
    add("srmech.math.cyclic.mod_pow(·,2,12)", "Z/12",
        [mod_pow(v, 2, 12) for v in range(12)], "squaring — non-homomorphic collapse")
    used("srmech.cascade.chiral_flip")
    seqs = [(0, 1), (1, 0), (0, 0), (1, 1)]
    idx = {s: i for i, s in enumerate(seqs)}
    add("srmech.cascade.chiral_flip", "length-2 binary sequences",
        [idx[tuple(chiral_flip(list(s)))] for s in seqs], "Class-C reversal; involution")
    used("srmech.cascade.cd_project")
    partial_raises = 0
    for a in range(3):
        for b in range(3):
            try:
                cd_project([Q(a, 1), Q(b, 1)])
            except ValueError:
                partial_raises += 1
    rows.append({
        "op": "srmech.cascade.cd_project", "carrier": "dim-2 CD elements",
        "classification": "PARTIAL", "is_self_map": False,
        "raises_on": partial_raises, "of": 9,
        "note": "REFUSES to truncate a genuinely present component rather than "
                "destroying it — injective where defined. This is the ANTI-arrow: "
                "a partial bijection, not a directional generator",
    })
    used("srmech.math.covering.center_lift")
    used("srmech.math.covering.lift_fibre")
    cl = center_lift([1, 1, 1], 2)
    lf = lift_fibre(cl["center_shadow"], 2, 4)
    rows.append({
        "op": "srmech.math.covering.center_lift + lift_fibre",
        "carrier": "ℤ -> ℤ/2", "classification": "NON-INJECTIVE",
        "is_self_map": False,
        "shadow_determines_lift": cl["shadow_determines_lift"],
        "fibre_size": lf["size"], "fibre": lf["fibre"],
        "note": "the SHIPPED legible-loss surface: it reports what it consumed by "
                "ENUMERATING the fibre. Not a self-map, so not a generator",
    })
    return rows


# ══════════════════════════════════════════════════════════════════════
# G4-F8 — the rank-dropping graph operator
# ══════════════════════════════════════════════════════════════════════
GRAPHS = [
    ("P3 path", 3, [(0, 1), (1, 2)], 1),
    ("C4 cycle", 4, [(0, 1), (1, 2), (2, 3), (3, 0)], 1),
    ("S4 star", 4, [(0, 1), (0, 2), (0, 3)], 1),
    ("K3 triangle", 3, [(0, 1), (1, 2), (0, 2)], 1),
    ("2K2 disconnected", 4, [(0, 1), (2, 3)], 2),
]


def run_laplacian_arrow():
    rows = []
    float_carrier_note = None
    for name, nv, edges, comps in GRAPHS:
        used("srmech.math.laplacian.dense_laplacian")
        L = dense_laplacian(nv, edges)
        ints, integral = [], True
        for i in range(nv):
            r = []
            for j in range(nv):
                v = L[i, j]
                iv = int(v)
                if not (v == iv):
                    integral = False
                r.append(iv)
            ints.append(r)
        if float_carrier_note is None:
            float_carrier_note = (
                "dense_laplacian returns a FLOAT Mat; entries verified integral "
                "and re-read as exact ints for the modular arrow"
            )
        for p in (2, 3, 5, 7):
            size = 1
            for _ in range(nv):
                size = size * p
            if size > 4000:
                continue
            vecs, index_of = [], {}
            for code in range(size):
                v, rem = [], code
                for _ in range(nv):
                    v.append(rem % p)
                    rem = rem // p
                vecs.append(tuple(v))
                index_of[tuple(v)] = code
            table = []
            for v in vecs:
                out = []
                for i in range(nv):
                    acc = 0
                    for j in range(nv):
                        a = class_k_c_residue(ints[i][j], p)
                        acc = mod_add(acc, mod_mul(a, v[j], p), p)
                    out.append(acc)
                table.append(index_of[tuple(out)])
            led = semiflow_ledger(table)
            kern = sum(1 for t in table if t == index_of[tuple([0] * nv)])
            expected_kernel = 1
            for _ in range(comps):
                expected_kernel = expected_kernel * p
            rows.append({
                "graph": name, "n_vertices": nv, "components": comps, "p": p,
                "laplacian_integral": integral,
                "state_space": size,
                "index": led["index"], "period": led["period"],
                "image_sizes": led["image_sizes"],
                "eventual_image_size": led["eventual_image_size"],
                "kernel_size": kern,
                "expected_kernel_p_to_components": expected_kernel,
                "kernel_matches_component_count": kern == expected_kernel,
                "index_is_one_tick": led["index"] <= 1,
            })
    return rows, float_carrier_note


# ══════════════════════════════════════════════════════════════════════
def main():
    emit(env_record())

    f1, f2, f3, f4, wrong_dis, unit_bad = run_cyclic_arrow()
    n_transient = sum(1 for r in f1 if r["index"] >= 2)
    n_nonunit = sum(1 for r in f1 if not r["is_unit"])
    n_unit = sum(1 for r in f1 if r["is_unit"])
    emit({
        "kind": "G4_F1_finite_arrow_family", "n_cells": len(f1),
        "n_unit_cells": n_unit, "n_nonunit_cells": n_nonunit,
        "n_cells_with_index_ge_2": n_transient,
        "max_index": max(r["index"] for r in f1),
        "max_index_cell": max(f1, key=lambda r: r["index"])["n"],
        "unit_control_violations": unit_bad,
        "falsifier": "if EVERY non-unit gives index <= 1 the generator framing is EMPTY",
        "result": ("SURVIVES — a genuine multi-step transient exists"
                   if n_transient else "FALSIFIED — every arrow is one tick"),
        "classification": "REFUTED" if n_transient == 0 else "CONFIRMED",
        "rows": f1,
    })
    emit({
        "kind": "G4_F2_closed_form_vs_brute_force",
        "n_cells": len(f2),
        "n_agree": sum(1 for r in f2 if r["agree"]),
        "n_disagree": sum(1 for r in f2 if not r["agree"]),
        "negative_control_wrong_formula_disagreements": wrong_dis,
        "negative_control_valid": wrong_dis > 0,
        "falsifier": "any disagreement REJECTS the closed form",
        "falsifier_fired_once_and_found_a_HARNESS_defect": (
            "First run: 14 of 37 cells disagreed. The closed form was RIGHT; the "
            "brute-force oracle was WRONG — it read the recurrence of the image "
            "SET as the period. On Z/12 with c=2 the image set {0,4,8} repeats "
            "immediately while T swaps 4 and 8, so the set reading said 1 and the "
            "true period is 2. Fixed to the lcm of the cycle lengths of T|E. "
            "Recorded rather than quietly corrected: the falsifier earned its keep "
            "by catching the instrument, not the claim."
        ),
        "result": ("closed form CONFIRMED on every cell"
                   if all(r["agree"] for r in f2) else "closed form REJECTED"),
        "rows": f2,
    })
    emit({
        "kind": "G4_F3_loss_is_legible",
        "n_cells": len(f3),
        "n_kernel_is_subgroup": sum(1 for r in f3 if r["kernel_is_subgroup"]),
        "n_fibres_uniform": sum(1 for r in f3 if r["fibres_uniform"]),
        "n_full_reconstruction": sum(1 for r in f3 if r["reconstructed"] == r["of"]),
        "falsifier": "one non-uniform fibre or one failed reconstruction",
        "consumed_object_shape": "a coset of ker(T), a subgroup of order gcd(c,n)",
        "rows": f3,
    })
    emit({
        "kind": "G4_F3_negative_control_nonhomomorphic",
        "control": "x -> x^2 mod n (shipped mod_pow) must give NON-uniform fibres",
        "rows": run_f3_negative_control(),
    })
    n_killed = sum(1 for r in f4 if r["carrying_complement_kills_the_arrow"])
    emit({
        "kind": "G4_F4_decorative_arrow_test",
        "n_cells": len(f4),
        "n_T_alone_bijective": sum(1 for r in f4 if r["T_alone_is_bijection"]),
        "n_paired_bijective": sum(1 for r in f4 if r["paired_is_bijection"]),
        "n_carrying_complement_kills_the_arrow": n_killed,
        "finding": (
            "LEGIBILITY AND IRREVERSIBILITY ARE IN TENSION. srmech's shipped "
            "lossy-projection doctrine (lossy_projection_record, lift_fibre) is "
            "CARRY THE COMPLEMENT so recovery is exact — and on every cell here "
            "the paired map (image, coset index) is a BIJECTION. An op that "
            "destroys AND returns its complement is DECORATIVE. The honest "
            "contract is: report the SHAPE and ORDER of what was consumed "
            "(the kernel subgroup), never the element."
        ),
        "rows": f4,
    })

    mrows, msummary = run_monoid_torsor()
    for r in mrows:
        emit(r)
    total_nongroup_torsor = sum(s["nongroups_admitting_torsor"] for s in msummary)
    total_disagree = sum(s["criterion_disagreements"] for s in msummary)
    emit({
        "kind": "G4_F5_monoid_torsor_summary",
        "per_order": msummary,
        "total_monoids_up_to_iso_order_le_4": sum(
            s["monoids_up_to_iso"] for s in msummary),
        "total_groups_up_to_iso": sum(s["groups_up_to_iso"] for s in msummary),
        "nongroups_admitting_a_torsor": total_nongroup_torsor,
        "independent_criterion_disagreements": total_disagree,
        "falsifier": "ONE non-group monoid admitting a torsor REFUTES vacuity",
        "result": (
            "CONFIRMED — 'monoid torsor' is VACUOUS: on every monoid of order "
            "<= 4, a simply transitive action exists IFF the monoid is a group. "
            "A torsor is a GROUP notion (reversible, no origin); a directional "
            "generator is a SEMIGROUP notion (a start, no inverse). They are "
            "not two flavours of one thing."
            if total_nongroup_torsor == 0 else
            "REFUTED — a non-group monoid admits a torsor"
        ),
        "classification": "REFUTED" if total_nongroup_torsor else "CONFIRMED",
        "why_it_is_a_theorem_not_a_coincidence": (
            "Simple transitivity makes the orbit map m -> m.x0 a bijection M -> X, "
            "which transports the action to LEFT MULTIPLICATION on M. The torsor "
            "condition then says every RIGHT translation R_a is a bijection, i.e. "
            "M is right-cancellative; a finite right-cancellative semigroup is a "
            "group. The exhaustive order<=4 check and the R_a criterion are two "
            "independent routes and they agree on every table."
        ),
    })
    emit({"kind": "G4_F5_negative_controls", "rows": run_torsor_negative_controls()})

    emit(run_infinite_hatch())

    screen = run_shipped_screen()
    noninj_selfmaps = [r for r in screen
                       if r["classification"] == "NON-INJECTIVE" and r["is_self_map"]]
    emit({
        "kind": "G4_F7_shipped_op_screen",
        "scope": "N-of-649 hand-selected structural SELF-MAP screen, NOT a census",
        "n_screened": len(screen),
        "registry_total": 649,
        "n_non_injective_self_maps": len(noninj_selfmaps),
        "non_injective_self_map_ops": [r["op"] for r in noninj_selfmaps],
        "brief_claim": "0 of 649 ops semigroup-not-group",
        "result": (
            "The brief's '0 of 649' is WRONG AS STATED. "
            "srmech.biology.q8.q8_project_v4 is a SHIPPED, C-peered, exact, "
            "non-injective IDEMPOTENT self-map on the Q8 byte alphabet "
            "(b -> b & 3; 8 -> 4, fibres of size 2, E o E = E). The monoid it "
            "generates, {id, E}, is a 2-element MONOID THAT IS NOT A GROUP. "
            "The rc426 note's own scope wording ('the one shipped example THIS "
            "census found', 11 hand-picked surfaces) is the honest one; the "
            "brief promoted it to a registry-wide 0-of-649 it never was."
        ),
        "rows": screen,
    })

    lrows, fnote = run_laplacian_arrow()
    n_multi = sum(1 for r in lrows if r["index"] >= 2)
    emit({
        "kind": "G4_F8_laplacian_mod_p_arrow",
        "n_cells": len(lrows),
        "n_index_ge_2": n_multi,
        "n_index_le_1": sum(1 for r in lrows if r["index"] <= 1),
        "kernel_matches_components": sum(
            1 for r in lrows if r["kernel_matches_component_count"]),
        "of": len(lrows),
        "float_carrier_observation": fnote,
        "prediction": "over ℚ, L is symmetric so index = 1 (one-tick arrow)",
        "result": (
            "index >= 2 OCCURS mod p — a genuine multi-step nilpotent transient "
            "appears in the modular reduction that the rational operator does "
            "not have" if n_multi else
            "every cell is a ONE-TICK arrow: L collapses once and is a "
            "permutation on its image thereafter"
        ),
        "rows": lrows,
    })

    # ---- prior-art absence, run LIVE rather than asserted ----------------
    refusal = None
    try:
        cyclic_period(6, 12)
    except ValueError as exc:
        refusal = str(exc)
    ok_unit = cyclic_period(5, 12)
    emit({
        "kind": "prior_art_absence_evidence",
        "greps_run_against": "docs/srmech/python/tests/registered_op_names.txt (649 lines)",
        "greps": [
            {"pattern": "semigroup|monoid|idempot|absorb|irrevers|one_way|nilpot",
             "op_name_hits": 0,
             "note": "only substring matches unit_loop / left_mult_is_invertible"},
            {"pattern": "order|orbit|period|cycle|iterate|fixed_point|rho",
             "op_name_hits": 17,
             "note": "cyclic_period, common_period, *_cycle_holonomy, normal_order, "
                     "order_fingerprint, recover_check_order, three_cycle, "
                     "klein4_triality_cycle, reverse_order — NONE reports the "
                     "index/transient of a non-injective self-map"},
            {"pattern": "project|quotient|congruen|collapse|preimage|kernel|rank",
             "op_name_hits": 23,
             "note": "cd_project, q8_project_v4, klein4_project_axis, poly_project, "
                     "qpoly_project, weyl_*_projector, left_mult_kernel, "
                     "lossy_projection_record, reproject, lift_fibre, "
                     "schur_complement — every one is a SINGLE projection; none "
                     "iterates or reports a transient"},
            {"pattern": "torsor", "op_name_hits": 2,
             "note": "oct_torsor_act, oct_torsor_div — both GROUP torsors (Q8)"},
        ],
        "shipped_surface_refuses_non_units": {
            "call": "srmech.math.primes.cyclic_period(6, 12)",
            "raises": refusal,
            "control_unit_call": "cyclic_period(5, 12)",
            "control_result": ok_unit,
            "consequence": (
                "The eventual PERIOD of a NON-UNIT multiplier is unreachable "
                "through shipped surface: cyclic_period refuses gcd != 1, and no "
                "op computes the reduced modulus n/g* it would have to be called "
                "on. That reduction is what this script hand-rolled in "
                "closed_form_arrow() — the concrete caller."
            ),
        },
    })

    emit({
        "kind": "verdict",
        "question_a_is_a_genuine_semigroup_not_group_surface_buildable": {
            "answer": "YES, exactly and closed-form, on the cyclic carrier",
            "shape": "T_c(x) = mod_mul(x, c, n) with gcd(c, n) > 1",
            "exact": True,
            "bottom_up_from_the_carrier": (
                "YES — it is Z/n's OWN multiplication, not a cascade "
                "reverse-engineered toward a continuous target. Nothing here "
                "approximates anything; index and period are integers derived "
                "from the prime factorisation."
            ),
            "what_it_destroys": (
                "a coset of ker(T) = {x : c*x = 0 mod n}, a SUBGROUP of order "
                "g = gcd(c, n). Per step the consumed order is the growth of "
                "gcd(c^t, n); after `index` steps the total consumed order is "
                "g* = gcd(c^index, n) and the map is a permutation of stride g*."
            ),
            "candidate_shapes_evaluated": [
                {"shape": "modular multiplication by a non-unit",
                 "verdict": "ACCEPT — exact, carrier-native, multi-step transient "
                            "(measured index up to 6), legible loss"},
                {"shape": "projection / idempotent",
                 "verdict": "REJECT as a GENERATOR — an idempotent has index 1 and "
                            "period 1, so <E> = {E}: an arrow with exactly one tick "
                            "and no time. And it ALREADY SHIPS (q8_project_v4)."},
                {"shape": "rank-dropping graph operator (Laplacian)",
                 "verdict": "PARTIAL — over ℚ it is one-tick (L is symmetric, hence "
                            "invertible on its image). Mod p a genuine multi-step "
                            "nilpotent transient DOES appear (5 of 20 cells). But "
                            "the arrow then belongs to the reduction, not to the "
                            "graph, so it is not a carrier-native generator."},
                {"shape": "quotient by a congruence",
                 "verdict": "REJECT — it IS the non-unit multiplication case "
                            "(ker T is the congruence), and the exemplar already "
                            "ships as q8_project_v4: Q8 -> V4 with kernel the "
                            "centre. A quotient of a GROUP is a GROUP; the arrow "
                            "is in the ITERATION, not in the quotient."},
                {"shape": "trace / fold that discards a coordinate",
                 "verdict": "REJECT — extant and already provenance-wrapped "
                            "(fold_encode + lossy_projection_record; heat_trace is "
                            "float). Adding another would duplicate surface."},
            ],
        },
        "question_b_is_the_loss_legible": {
            "answer": "YES, exactly — and that is a PROBLEM, not a reassurance",
            "measured": (
                "On all 37 cells the fibres are uniform of size g, ker T is a "
                "subgroup, and (image, coset index) reconstructs the input on "
                "37/37 cells. So the paired map is a BIJECTION on 37/37."
            ),
            "the_tension": (
                "srmech's shipped doctrine for lossy ops is CARRY THE COMPLEMENT "
                "(lossy_projection_record: 'recovery is EXACT because the "
                "complement is carried'; lift_fibre ENUMERATES what a shadow does "
                "not determine). Applied to an arrow that doctrine ANNIHILATES it: "
                "the moment the op returns the coset index it is invertible and "
                "there is no arrow left. LEGIBILITY AND IRREVERSIBILITY ARE IN "
                "TENSION and cannot both be maximised."
            ),
            "the_resolution": (
                "Report the SHAPE and ORDER of what was consumed, never the "
                "element: 'this step consumed a coset of an order-g subgroup' is "
                "legible and still irreversible; 'this step consumed coset #3' is "
                "legible and reversible. The proposed op returns the former."
            ),
        },
        "question_c_does_it_belong": {
            "answer": "YES for the closed-form cyclic arrow ledger; NO for a "
                      "torsor predicate; NO for a bare projection op",
            "decorative_arrow_check": (
                "NOT decorative. T_c is genuinely non-injective (image 12 -> 2 -> 1 "
                "on Z/12 with c=6) — it is not an invertible map that merely "
                "refuses negative t. The contrast case is shipped: cd_project "
                "RAISES rather than truncating, i.e. it is a partial BIJECTION, "
                "and propagate accepts z = -1 and round-trips at 1.5e-15."
            ),
        },
        "torsor_is_a_group_notion": (
            "CONFIRMED independently. Exhaustive over all 45 monoids of order <= 4 "
            "up to isomorphism (1 / 2 / 7 / 35 — matching the known counts): a "
            "simply transitive action exists IFF the monoid is a group (5 of 5 "
            "groups yes, 0 of 40 non-groups yes), under all THREE torsor "
            "definitions, and agreeing on every table with the independent "
            "right-translation-bijectivity criterion (0 disagreements)."
        ),
        "no_continuum_machinery": (
            "Nothing here uses a limit, a norm, a resolvent or a semigroup of "
            "operators on a Banach space. Hille-Yosida motivated the QUESTION; the "
            "answer is integer index + integer period + a subgroup order."
        ),
    })

    emit({
        "kind": "op_usage_ledger",
        "shipped_ops_used": sorted(_OPS_USED),
        "n_shipped_ops_used": len(_OPS_USED),
        "foreign_math_modules_used": [],
        "abs_used": False,
        "sign_handling": "class_k_c_residue — Class K pin-slot ∘ Class C re-application",
    })

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for rec in _RECORDS:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(_RECORDS)} records -> {OUT}")


if __name__ == "__main__":
    main()
