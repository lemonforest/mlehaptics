"""rc386 (`#T1062`) — cd_three_form, the exact-ℚ G₂ associative 3-form.

``srmech.cascade.cd_three_form(x, y, z, *, table=None)`` → a SCALAR ℚ,
``φ(x, y, z) = Re(x̄·(y·z))``: the regrouping-INVARIANT real shadow both
``(x̄·y)·z`` and ``x̄·(y·z)`` share (Re(associator) ≡ 0), the Re-companion to
:func:`associator`'s Im defect. On Im 𝕆 = ℝ⁷ it is the Harvey–Lawson calibration
3-form, ±1 on the 7 Fano associative planes; ``composition_of_c`` (NO new C
symbol), Class M ∘ C then a real-part read.

Genuine checks (NOT smoke tests):

  1. THE FANO CENSUS — 7 of the 35 unordered imaginary basis triples carry ±1:
     {123,145,246,257,347}=+1, {167,356}=−1; the other 28 are 0 (exact ℚ).
  2. THE CONSISTENCY ORACLE (co-equal dual construction) — cd_three_form equals
     the shipped FLOAT peer ``g2_three_form`` bit-for-bit, 35/35 unordered AND
     343/343 ordered.
  3. THE ACCEPTANCE ORACLE (native only) — pure vs c_dispatched byte-identity on
     the Fano triples + generic exact-ℚ octonions.
  4. the Re/Im split — Re(associator) ≡ 0, and cd_three_form is the single
     regrouping-invariant scalar both bracketings share on generic octonions.
  5. G₂-invariance — every g2_subalgebra derivation annihilates φ (490/490, 56
     of them non-trivial), so stab(φ) = G₂ = Der(𝕆).
  6. full antisymmetry + the table= branch parity + the CD_MAX_DIM guards.
  7. registration ratchet (__all__ / Rosetta composition_of_c / registered
     op-name list / describe() total 546) + a no-abs() source guard.

numpy-free (srmech + stdlib only); mirrors notes/cd_three_form_rc386.py.
"""
from __future__ import annotations

import json
from itertools import combinations, permutations, product
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech.cascade import cd_three_form, cd_basis
from srmech.cascade import cayley_dickson as CD
from srmech.cascade.cayley_dickson import (
    cd_mult, cd_conjugate, associator, algebra_table, table_product,
)
from srmech.math.hdc import g2_three_form, cross7
from srmech.math.q import Q

IMAG = list(range(1, 8))
FANO_EXPECT = {
    (1, 2, 3): 1, (1, 4, 5): 1, (2, 4, 6): 1, (2, 5, 7): 1, (3, 4, 7): 1,
    (1, 6, 7): -1, (3, 5, 6): -1,
}


def E(i):
    return cd_basis(8, i)


def _pure(fn, *args, **kw):
    """Run ``fn`` forced through the PURE cascade (native dispatch disabled)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _generic_triples():
    def lcg(seed, n):
        x = seed
        out = []
        for _ in range(n):
            x = (1103515245 * x + 12345) % (2 ** 31)
            out.append((x % 15) - 7)
        return out
    vals = lcg(20260803, 8 * 3 * 200)
    octs = []
    idx = 0
    while len(octs) < 60:
        v = [Q(x) for x in vals[idx:idx + 8]]
        idx += 8
        if any(v[m] != 0 for m in range(4)) and any(v[m] != 0 for m in range(4, 8)):
            octs.append(tuple(v))
    return [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]


# ── 1. the Fano census ──────────────────────────────────────────────────────
def test_fano_census():
    """cd_three_form is ±1 on exactly the 7 Fano associative 3-planes, 0 else.

    THE acceptance oracle sign convention: {123,145,246,257,347}=+1,
    {167,356}=−1 — the convention the Cayley–Dickson product fixes, and the
    one that matches the shipped g2_three_form (see test 2). The prose gloss
    ``Re((x·y)·z)`` in the brief carries the OPPOSITE sign and is NOT this op.
    """
    census = {}
    for i, j, k in combinations(IMAG, 3):
        v = cd_three_form(E(i), E(j), E(k))
        assert v in (Q(-1), Q(0), Q(1)), (i, j, k, v)
        if v != 0:
            census[(i, j, k)] = int(v)
    assert census == FANO_EXPECT
    assert len(census) == 7


# ── 2. the consistency oracle (co-equal dual construction) ──────────────────
def test_consistency_oracle_vs_g2_three_form():
    """exact-ℚ cd_three_form == shipped FLOAT g2_three_form, 35/35 + 343/343."""
    for i, j, k in combinations(IMAG, 3):
        q = cd_three_form(E(i), E(j), E(k))
        f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                          [float(x) for x in E(k)])
        assert float(q) == float(f), (i, j, k, q, f)
    n = 0
    for i, j, k in product(IMAG, repeat=3):
        q = cd_three_form(E(i), E(j), E(k))
        f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                          [float(x) for x in E(k)])
        assert float(q) == float(f), (i, j, k, q, f)
        n += 1
    assert n == 343


def test_phi_calibrates_cross7():
    """φ(a,b,c) = ⟨a, cross7(b,c)⟩ — the scalar reads the 7-D cross product."""
    for i, j, k in product(IMAG, repeat=3):
        q = cd_three_form(E(i), E(j), E(k))
        a = [float(v) for v in E(i)]
        bc = cross7([float(v) for v in E(j)], [float(v) for v in E(k)])
        assert float(q) == sum(a[m] * bc[m] for m in range(8)), (i, j, k)


# ── 3. the acceptance oracle: pure vs c_dispatched byte-identity ────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_pure_vs_c_dispatched_byte_identity():
    """cd_three_form is composition_of_c; the c_dispatched value must be
    byte-identical (exact ℚ) to the pure-cascade value on the Fano triples and
    on generic exact-ℚ octonions — the co-equal dual-construction gate."""
    for i, j, k in product(IMAG, repeat=3):
        c_disp = cd_three_form(E(i), E(j), E(k))
        pure = _pure(cd_three_form, E(i), E(j), E(k))
        assert c_disp == pure, (i, j, k, c_disp, pure)
    for a, b, c in _generic_triples():
        assert cd_three_form(a, b, c) == _pure(cd_three_form, a, b, c)


# ── 4. the Re/Im split ──────────────────────────────────────────────────────
def test_re_associator_is_zero():
    """Re(associator) ≡ 0 on all 343 ordered imaginary triples — the defect is
    pure imaginary, so the scalar φ is exactly the part associator misses."""
    for i, j, k in product(IMAG, repeat=3):
        assert associator(E(i), E(j), E(k))[0] == 0, (i, j, k)


def test_regrouping_invariant_scalar_generic():
    """On generic octonions cd_three_form(x,y,z) is the single scalar both
    bracketings share: Re((x̄·y)·z) == Re(x̄·(y·z)) == cd_three_form, while the
    associator (the Im defect) is nonzero there."""
    seen_nonassoc = False
    for a, b, c in _generic_triples():
        cb = cd_conjugate(a)
        left = cd_mult(cd_mult(cb, b), c)[0]
        right = cd_mult(cb, cd_mult(b, c))[0]
        assert left == right == cd_three_form(a, b, c)
        if any(v != 0 for v in associator(a, b, c)):
            seen_nonassoc = True
    assert seen_nonassoc, "the generic sample must include non-associating triples"


# ── 5. G₂-invariance ────────────────────────────────────────────────────────
def test_g2_invariance():
    """Every g2_subalgebra derivation annihilates φ:
    φ(Dx,y,z)+φ(x,Dy,z)+φ(x,y,Dz) = 0 on all 14×35=490 (D,triple); 56 of them
    NON-TRIVIALLY (individual terms not all 0), so stab(φ)=G₂=Der(𝕆) is a
    measurement, not a vacuous 0=0."""
    from srmech.physics.qm.so8 import g2_subalgebra
    G = g2_subalgebra()
    assert len(G) == 14

    def Dact(D, e):
        out = []
        for r in range(8):
            s = Q(0)
            for c in range(8):
                val = float(D[r][c])
                assert val == int(round(val)), "derivation entries must be integers"
                s += Q(int(round(val))) * e[c]
            out.append(s)
        return tuple(out)

    hold = tot = nontrivial = nontrivial_hold = 0
    for D in G:
        for i, j, k in combinations(IMAG, 3):
            x, y, z = E(i), E(j), E(k)
            t1 = cd_three_form(Dact(D, x), y, z)
            t2 = cd_three_form(x, Dact(D, y), z)
            t3 = cd_three_form(x, y, Dact(D, z))
            s = t1 + t2 + t3
            tot += 1
            if s == 0:
                hold += 1
            if not (t1 == 0 and t2 == 0 and t3 == 0):
                nontrivial += 1
                if s == 0:
                    nontrivial_hold += 1
    assert hold == tot == 490
    assert nontrivial_hold == nontrivial == 56


# ── 6. antisymmetry + table branch + guards ─────────────────────────────────
def test_full_antisymmetry():
    """φ is alternating: any transposition flips the sign; a repeated argument
    annihilates it (Class-K sign pin, never abs())."""
    for i, j, k in combinations(IMAG, 3):
        base = cd_three_form(E(i), E(j), E(k))
        ref = [i, j, k]
        for p in permutations((i, j, k)):
            arr = [ref.index(x) for x in p]
            parity = sum(1 for a in range(3) for b in range(a + 1, 3)
                         if arr[a] > arr[b])
            sign = -1 if parity % 2 else 1
            assert cd_three_form(E(p[0]), E(p[1]), E(p[2])) == sign * base
    # a repeated argument → 0
    assert cd_three_form(E(1), E(1), E(2)) == 0
    assert cd_three_form(E(3), E(5), E(3)) == 0


def test_table_branch_matches_ladder():
    """The table= branch (algebra_table(8) definite ladder) reproduces the
    table=None result on all 343 ordered imaginary triples; conjugation is
    table-independent."""
    tbl = algebra_table(8)
    for i, j, k in product(IMAG, repeat=3):
        assert cd_three_form(E(i), E(j), E(k), table=tbl) == \
            cd_three_form(E(i), E(j), E(k))


def test_table_is_keyword_only_and_guards():
    """``table`` is keyword-only; unequal-length and non-power-of-two operands
    raise."""
    with pytest.raises(TypeError):
        cd_three_form(E(1), E(2), E(3), algebra_table(8))   # positional table
    with pytest.raises(ValueError):
        cd_three_form([1, 0], [1, 0, 0, 0], [1, 0])          # unequal length
    with pytest.raises(ValueError):
        cd_three_form([1, 0, 0], [0, 1, 0], [0, 0, 1])       # dim 3 (not 2^k)


def test_lower_rungs():
    """φ is defined at every rung. On ℝ / ℂ it is just Re(x̄·(y·z)); on ℍ it is
    still associative so Re((x̄·y)·z)==Re(x̄·(y·z))."""
    # ℝ: φ(2,3,5) = 2*15 = 30
    assert cd_three_form([2], [3], [5]) == Q(30)
    # ℂ: e1·e1 = -1, so φ(e1,e1,1)=Re(conj(e1)·(e1·1))=Re((-e1)·e1)=Re(-e1²)=1
    e1c = [0, 1]
    one = [1, 0]
    assert cd_three_form(e1c, e1c, one) == Q(1)


# ── 7. registration ratchet + no-abs source guard ───────────────────────────
def test_registration_ratchet():
    import srmech.cascade as C
    assert "cd_three_form" in C.__all__
    from srmech.introspect.tool_schema import tool_schema_view
    view = tool_schema_view()
    assert len(view["tools"]) == 655
    names = {t["name"] for t in view["tools"]}
    assert "srmech.cascade.cd_three_form" in names


def test_rosetta_and_op_name_ledgers():
    here = Path(__file__).resolve().parent
    rosetta = (here / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    rows = [json.loads(ln) for ln in rosetta.splitlines() if ln.strip()]
    row = next(r for r in rows if r["exposed_as"] == "srmech.cascade.cd_three_form")
    assert row["bucket"] == "composition_of_c"
    assert row["defined_at"] == "srmech.cascade.cayley_dickson.cd_three_form"
    names = (here / "registered_op_names.txt").read_text(
        encoding="utf-8").split()
    assert "srmech.cascade.cd_three_form" in names


def test_no_abs_in_source():
    """The op CODE must not call abs() — sign is Class-K pin, magnitude is
    Class-N squared norm (cascade-honesty discipline). The docstring MAY say
    "no abs()", so scan only the executable body after the docstring."""
    src = Path(CD.__file__).read_text(encoding="utf-8")
    start = src.index("def cd_three_form(")
    end = src.index("\ndef ", start + 1)
    func = src[start:end]
    # drop the docstring: everything between the first pair of triple-quotes
    q = '"""'
    d0 = func.index(q)
    d1 = func.index(q, d0 + 3)
    code = func[:d0] + func[d1 + 3:]
    assert "abs(" not in code, "cd_three_form code must not use abs()"
