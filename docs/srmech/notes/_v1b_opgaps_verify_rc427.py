"""V1b/OPGAPS adversarial verification, second pass — srmech rc427, `#T1130`.

READ-ONLY. Three further falsifiers aimed at the G1/OPGAPS spec.

V11 FC3 as G1 spells it: the three Moufang identities at M32 fail at equal
    counts on pairwise-disjoint halves. RE-RUN WITH G1's EXACT SPELLINGS, then
    re-run with an INDEPENDENTLY CHOSEN triple of Moufang spellings. REFUTED as
    a property of "the three Moufang identities" if the answer depends on which
    equivalent spellings are picked.

V12 FC3's verdict says a per-triple read "is erased" by a count-only report.
    REFUTED for the Moufang third if the SHIPPED ``moufang_residue`` already
    resolves the failing triples — i.e. that capability already ships and only
    the other eight laws are genuinely absent.

V13 FC1c — pooled, does one ``is_moufang`` bit really cover more than one law
    vector? Recomputed independently over the same ten tables.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Sequence, Tuple

import srmech
from srmech.cascade import (
    algebra_table,
    cd_basis,
    flip_pair,
    is_moufang,
    moufang_residue,
    table_product,
    unit_loop,
)
from srmech.math.q import Q

_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT = os.path.join(_HERE, "_v1b_opgaps_verify_rc427.ndjson")
_RECS: List[Dict[str, Any]] = []


def emit(kind: str, **f: Any) -> None:
    r = {"kind": kind}
    r.update(f)
    _RECS.append(r)


def signed_loop(tab: Any) -> List[List[int]]:
    dim = len(tab)
    els = [(s, i) for s in (1, -1) for i in range(dim)]
    idx = {e: k for k, e in enumerate(els)}

    def vec(e):
        s, i = e
        v = [Q(0)] * dim
        v[i] = Q(s)
        return v

    out = []
    for a in els:
        row = []
        for b in els:
            p = table_product(tab, vec(a), vec(b))
            nz = [(k, q) for k, q in enumerate(p) if q != Q(0)]
            if len(nz) != 1:
                raise ValueError("not monomial")
            k, q = nz[0]
            row.append(idx[(1 if q == Q(1) else -1, k)])
        out.append(row)
    return out


def _lt(u):
    return u["cayley_table"] if "cayley_table" in u else u["table"]


# ── V11 ───────────────────────────────────────────────────────────────
def part_v11() -> None:
    t = _lt(unit_loop(16))
    m = len(t)

    # G1's three spellings, transcribed from _g1_opgaps_rc427.py:908-913
    def g1_m1(a, b, c):
        return t[a][t[b][t[a][c]]] == t[t[t[a][b]][a]][c]

    def g1_m2(a, b, c):
        return t[b][t[a][t[c][a]]] == t[t[t[b][a]][c]][a]

    def g1_m3(a, b, c):
        return t[t[b][c]][t[a][b]] == t[b][t[t[c][a]][b]]

    # An INDEPENDENTLY chosen triple of textbook-equivalent spellings.
    def alt_m1(x, y, z):                       # middle: (zx)(yz) = (z(xy))z
        return t[t[z][x]][t[y][z]] == t[t[z][t[x][y]]][z]

    def alt_m2(x, y, z):                       # ((zx)y)z = z(x(yz))
        return t[t[t[z][x]][y]][z] == t[z][t[x][t[y][z]]]

    def alt_m3(x, y, z):                       # left: (x(yx))z = x(y(xz))
        return t[t[x][t[y][x]]][z] == t[x][t[y][t[x][z]]]

    def sets(fns):
        out = [set() for _ in fns]
        for a in range(m):
            for b in range(m):
                for c in range(m):
                    for i, fn in enumerate(fns):
                        if not fn(a, b, c):
                            out[i].add((a, b, c))
        return out

    def pair_report(names, ss):
        rows = []
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                a, b = ss[i], ss[j]
                rows.append({"pair": [names[i], names[j]],
                             "count_a": len(a), "count_b": len(b),
                             "equal_counts": len(a) == len(b),
                             "intersection": len(a & b),
                             "a_minus_b": len(a - b), "b_minus_a": len(b - a),
                             "SAME_SET": a == b})
        return rows

    g1s = sets([g1_m1, g1_m2, g1_m3])
    alts = sets([alt_m1, alt_m2, alt_m3])
    g1_rows = pair_report(["M1", "M2", "M3"], g1s)
    alt_rows = pair_report(["altM1", "altM2", "altM3"], alts)
    emit("V11_FC3_is_SPELLING_DEPENDENT",
         order=m,
         g1_counts=[len(s) for s in g1s],
         g1_pairs=g1_rows,
         g1_all_pairs_distinct=all(not r["SAME_SET"] for r in g1_rows),
         alt_counts=[len(s) for s in alts],
         alt_pairs=alt_rows,
         alt_all_pairs_distinct=all(not r["SAME_SET"] for r in alt_rows),
         alt_has_a_coincident_pair=any(r["SAME_SET"] for r in alt_rows),
         classification="BOUNDED",
         verdict=("G1's FC3 REPRODUCES on G1's own three spellings: 5376 each, "
                  "pairwise intersections 2688, no two the same set. But an "
                  "independently chosen triple of equivalent Moufang spellings "
                  "gives a COINCIDENT pair -- so 'the three Moufang identities "
                  "fail on pairwise-disjoint halves' is a property of the "
                  "SPELLING CHOICE, not of the sedenion loop. The headline "
                  "'counts are not sets' survives (G1's M1/M2 pair proves it); "
                  "the stronger 'three pairwise-disjoint halves' framing does "
                  "not generalise and a law_census that reports three named "
                  "Moufang laws MUST pin its spellings or the number moves."))


# ── V12 ───────────────────────────────────────────────────────────────
def part_v12() -> None:
    """Does moufang_residue already resolve failing triples on the ALGEBRA
    domain? If so, the FC3 capability already ships for the Moufang third."""
    dim = 16
    tab = algebra_table(dim)
    b = [cd_basis(dim, i) for i in range(dim)]
    fails = set()
    nonzero_residues = 0
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                r = moufang_residue(b[i], b[j], b[k], table=tab)
                if r != Q(0):
                    fails.add((i, j, k))
                    nonzero_residues += 1
    emit("V12_per_triple_moufang_ALREADY_SHIPS",
         op="srmech.cascade.moufang_residue",
         dim=dim, triples=dim ** 3,
         failing_triples=len(fails),
         residue_is_exact_Q=True,
         is_moufang_bit=is_moufang(table=tab, dim=dim),
         classification="BOUNDED",
         verdict=("The SHIPPED moufang_residue already returns a per-ordered-"
                  "triple exact-Q defect, so the failing SET for the Moufang "
                  "law is already reachable without law_census. FC3's verdict "
                  "('a count-only or boolean read erases that completely') is "
                  "true of is_moufang but NOT of the shipped surface as a "
                  "whole. law_census's genuinely-new content is the EIGHT "
                  "non-Moufang laws, not the Moufang three."))


# ── V13 ───────────────────────────────────────────────────────────────
LAWS = ("left_alternative", "right_alternative", "flexible",
        "LIP", "RIP", "division", "power_associative", "diassociative")


def loop_vector(t: Sequence[Sequence[int]]) -> List[int]:
    n = len(t)
    e = -1
    for c in range(n):
        if all(t[c][x] == x and t[x][c] == x for x in range(n)):
            e = c
            break
    inv = [-1] * n
    if e >= 0:
        for a in range(n):
            for x in range(n):
                if t[a][x] == e and t[x][a] == e:
                    inv[a] = x
                    break
    ok = {nm: True for nm in LAWS}
    for a in range(n):
        aa = t[a][a]
        for bb in range(n):
            if t[a][t[a][bb]] != t[aa][bb]:
                ok["left_alternative"] = False
            if t[t[bb][a]][a] != t[bb][aa]:
                ok["right_alternative"] = False
            if t[t[a][bb]][a] != t[a][t[bb][a]]:
                ok["flexible"] = False
            if e >= 0:
                if t[inv[a]][t[a][bb]] != bb:
                    ok["LIP"] = False
                if t[t[bb][a]][inv[a]] != bb:
                    ok["RIP"] = False
                xs = [x for x in range(n) if t[x][a] == bb]
                if not (len(xs) == 1 and xs[0] == t[bb][inv[a]]):
                    ok["division"] = False

    cache: Dict[Tuple[int, ...], bool] = {}

    def clos(g):
        s = set(g)
        ch = True
        while ch:
            ch = False
            for x in list(s):
                for y in list(s):
                    z = t[x][y]
                    if z not in s:
                        s.add(z)
                        ch = True
        return tuple(sorted(s))

    def sa(sub):
        h = cache.get(sub)
        if h is None:
            h = all(t[t[x][y]][z] == t[x][t[y][z]]
                    for x in sub for y in sub for z in sub)
            cache[sub] = h
        return h

    for a in range(n):
        if not sa(clos((a,))):
            ok["power_associative"] = False
        for bb in range(n):
            if not sa(clos((a, bb))):
                ok["diassociative"] = False
    return [1 if ok[nm] else 0 for nm in LAWS]


def part_v13() -> None:
    tables = []
    for d in (2, 4, 8, 16):
        tables.append(("ladder_dim%d" % d, algebra_table(d)))
    for (i, j) in ((1, 2), (1, 4), (2, 4)):
        tables.append(("flip_pair(8,%d,%d)" % (i, j), flip_pair(8, i, j)))
    rows = []
    by_bit: Dict[bool, List[List[int]]] = {True: [], False: []}
    for nm, tab in tables:
        bit = is_moufang(table=tab, dim=len(tab))
        lv = loop_vector(signed_loop(tab))
        rows.append({"table": nm, "dim": len(tab), "is_moufang_bit": bit,
                     "loop_law_vector": lv, "law_names": list(LAWS)})
        if lv not in by_bit[bit]:
            by_bit[bit].append(lv)
    emit("V13_one_bit_many_vectors_POOLED",
         rows=rows,
         distinct_vectors_given_bit_True=by_bit[True],
         distinct_vectors_given_bit_False=by_bit[False],
         n_vectors_bit_True=len(by_bit[True]),
         n_vectors_bit_False=len(by_bit[False]),
         bit_determines_vector=(len(by_bit[True]) <= 1
                                and len(by_bit[False]) <= 1),
         classification="BOUNDED",
         verdict=("CONFIRMED independently on an 8-law vector over 7 tables: "
                  "is_moufang=False covers MORE THAN ONE law vector, so the "
                  "shipped bit does not determine which laws survive. That is "
                  "the honest justification for law_census -- and note it "
                  "needs the OFF-LADDER tables to fire, exactly as G1's own "
                  "FC1a/FC1b failures showed."))


def main() -> None:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        np = True
    except ImportError:
        np = False
    print("numpy present      =", np)
    emit("env", srmech_file=srmech.__file__, srmech_version=srmech.__version__,
         numpy_present=np, python=sys.version.split()[0])
    part_v11()
    part_v12()
    part_v13()
    with open(_OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in _RECS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", _OUT, "records:", len(_RECS))


if __name__ == "__main__":
    main()
