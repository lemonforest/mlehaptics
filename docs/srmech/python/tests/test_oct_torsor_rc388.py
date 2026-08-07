"""rc388 (`#T963`) — the octonion ℍ-torsor of a seam coset.

``srmech.math.octonion.oct_torsor_act(t, g)`` = the RIGHT action ``t <| g =
oct_mult(t, g)``; ``oct_torsor_div(t1, t2)`` = the unique ``g`` with ``t1 <| g ==
t2``, ``= oct_mult(t1 ^ 8, t2)``. A quaternion subalgebra ``H = {±e₀..±e₃}`` and
its set-complement — the seam coset ``T = H·e = {±e₄..±e₇}`` — form a PRINCIPAL
right torsor: ``H`` acts on ``T`` simply-transitively. Both ops are
``composition_of_c`` (NO new C symbol; they ride the c_dispatched
``srmech_oct_mult``), Class M∘I and Class C∘M.

THE 4-POINT RATCHET (the whole point: it catches a FALSE GREEN a closure-only
pin misses — the naive composition order still LANDS IN T 14336/14336 while
being the WRONG element):

  1. act closes into T; div lands in H, solves, and is UNIQUE — 1792/1792 each,
     orbit histogram exactly {1: 1792}. Denominated honestly as 448 × 4 (the 28
     seams carry only 7 distinct (H,T) decompositions; T is always H's
     set-complement).
  2. BOTH the law AND the defect: ``(t<|g)<|h == t<|(h·g)`` is 14336/14336, AND
     the naive ``t<|(g·h)`` is 8960/14336.
  3. ``oct_conjugate(t) == t ^ 8`` on T, 224/224.
  4. act byte-exact vs ``oct_mult`` 256/256; R_g == L_{conj g} on T 1792/1792;
     and oct_mult's sign table recomputed from ``cd_basis_product`` (no drift).

Plus the notebook correction (3+4 is the structure, 3+1+3 a seam artifact: the
strict 3-index set is H-stable only 1008/1344), the guards, the pure-vs-
c_dispatched byte-identity oracle, the registration ratchet and a no-abs()
source guard. numpy-free (srmech + stdlib only); mirrors
notes/oct_torsor_rc388.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech.math import octonion as OCT
from srmech.math.octonion import (
    oct_torsor_act, oct_torsor_div, oct_mult, oct_conjugate,
)

# The 7 Fano lines = the 7 XOR-closed imaginary triples = the 7 quaternion
# subalgebras H_L = {e0, e_a, e_b, e_c}. a ^ b == c on each.
FANO = [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 4, 7), (1, 6, 7), (2, 5, 7),
        (3, 5, 6)]


def _signed(idxs):
    """The signed basis bytes {+e_i, -e_i : i in idxs} (byte = (sign<<3)|idx)."""
    return [i for i in idxs] + [i | 8 for i in idxs]


def _seams():
    """The 28 seams: (H_bytes, T_bytes) for each (Fano line, complement gen).

    A seam is (L, e) with L a Fano line and e one of the 4 complement indices;
    the coset H·e is the SAME set T for all 4 e of a line, so the 28 seams carry
    only 7 DISTINCT (H, T) decompositions and T is always H's set-complement.
    """
    out = []
    for L in FANO:
        assert L[0] ^ L[1] == L[2]
        Hidx = [0] + list(L)
        Tidx = [i for i in range(8) if i not in Hidx]
        assert len(Tidx) == 4
        for _e in Tidx:                      # 4 seam generators per line
            out.append((_signed(Hidx), _signed(Tidx)))
    return out


SEAMS = _seams()


def test_seam_bookkeeping():
    """28 seams, 7 distinct (H, T) decompositions, T = H's set-complement."""
    assert len(SEAMS) == 28
    distinct = {(tuple(sorted(H)), tuple(sorted(T))) for H, T in SEAMS}
    assert len(distinct) == 7
    for H, T in SEAMS:
        assert set(H) | set(T) == set(range(16))     # complement
        assert set(H) & set(T) == set()


# ── ratchet 1: act closes; div lands / solves / is UNIQUE ({1: 1792}) ─────────
def test_ratchet1_act_closure_and_div_simple_transitivity():
    act_ok = act_tot = 0
    land = solve = div_tot = 0
    hist: dict[int, int] = {}
    for H, T in SEAMS:
        Hset, Tset = set(H), set(T)
        for t in sorted(Tset):
            for g in sorted(Hset):
                act_tot += 1
                act_ok += oct_torsor_act(t, g) in Tset
        for t1 in sorted(Tset):
            for t2 in sorted(Tset):
                div_tot += 1
                g = oct_torsor_div(t1, t2)
                land += g in Hset
                solve += oct_torsor_act(t1, g) == t2
                n = sum(1 for gg in Hset if oct_torsor_act(t1, gg) == t2)
                hist[n] = hist.get(n, 0) + 1
    assert act_ok == act_tot == 1792           # 448 x 4 (28 seams x 8 x 8)
    assert land == solve == div_tot == 1792
    assert hist == {1: 1792}                    # simply transitive


# ── ratchet 2: BOTH the law AND the defect ───────────────────────────────────
def test_ratchet2_action_law_and_naive_defect():
    """(t<|g)<|h == t<|(h·g) MUST hold 14336/14336; the naive t<|(g·h) MUST be
    8960/14336. Pinning only the law lets a silent convention flip pass."""
    law_ok = naive_ok = tot = 0
    for H, T in SEAMS:
        for t in sorted(set(T)):
            for g in sorted(set(H)):
                for h in sorted(set(H)):
                    tot += 1
                    lhs = oct_torsor_act(oct_torsor_act(t, g), h)
                    law_ok += lhs == oct_torsor_act(t, oct_mult(h, g))
                    naive_ok += lhs == oct_torsor_act(t, oct_mult(g, h))
    assert tot == 14336
    assert law_ok == 14336
    assert naive_ok == 8960


# ── ratchet 3: oct_conjugate(t) == t ^ 8 on T, 224/224 ────────────────────────
def test_ratchet3_conj_is_xor8_on_T():
    """The ^8 in oct_torsor_div IS oct_conjugate on T, because idx(t) != 0
    there — the precondition that makes div 10 ops, not 11."""
    ok = tot = 0
    for H, T in SEAMS:
        for t in T:
            assert (t & 7) != 0                  # every seam byte is imaginary
            tot += 1
            ok += oct_conjugate(t) == t ^ 8
    assert ok == tot == 224


# ── ratchet 4: act == oct_mult (256); R_g == L_conj(g) (1792); sign no-drift ──
def test_ratchet4_byte_exact_and_sign_table_from_cd_basis_product():
    # act is byte-exact oct_mult on ALL 256 pairs (the torsor is the reading).
    be = sum(1 for a in range(16) for b in range(16)
             if oct_torsor_act(a, b) == oct_mult(a, b))
    assert be == 256

    # RIGHT action R_g equals LEFT action by conj(g) on T (1792/1792).
    rl = tot = 0
    for H, T in SEAMS:
        for t in T:
            for g in H:
                tot += 1
                rl += oct_torsor_act(t, g) == oct_mult(oct_conjugate(g), t)
    assert rl == tot == 1792

    # oct_mult's sign table is the cd_basis_product cocycle at dim 8 — NOT a
    # hand-entered constant. Recompute F and check every one of the 256 cells.
    from srmech.cascade.cayley_dickson import cd_basis_product
    F = [[0 if cd_basis_product(8, xa, xb)[1] == 1 else 1 for xb in range(8)]
         for xa in range(8)]
    for a in range(16):
        for b in range(16):
            xa, xb = a & 7, b & 7
            sign = (a >> 3) ^ (b >> 3) ^ F[xa][xb]
            assert oct_mult(a, b) == (sign << 3) | (xa ^ xb), (a, b)


# ── the notebook correction: 3+4 is the structure, 3+1+3 a seam artifact ──────
def test_strict_three_index_is_not_stable():
    """The strict 3-index seam set (complement MINUS the generator e) is H-stable
    only 1008/1344 — 3+1+3 manufactures a seam artifact. First escape:
    L=(1,2,3), e=4, g=+e1, t=+e5 -> byte 4 (+e4), the seam unit itself (the
    shipped RIGHT action e5·e1; the reversed order e1·e5 is byte 12)."""
    ok = tot = 0
    first_escape = None
    for L in FANO:
        Hidx = [0] + list(L)
        Tidx = [i for i in range(8) if i not in Hidx]
        for e in Tidx:
            T3 = set(_signed([i for i in Tidx if i != e]))    # the strict 3 units
            for t in sorted(T3):
                for g in _signed(Hidx):
                    tot += 1
                    r = oct_mult(t, g)
                    if r in T3:
                        ok += 1
                    elif first_escape is None:
                        first_escape = (L, e, g, t, r)
    assert (ok, tot) == (1008, 1344)
    assert first_escape == ((1, 2, 3), 4, 1, 5, 4)   # +e5 <| +e1 = +e4 (byte 4)
    # the 4-index coset is fully H-stable by contrast (ratchet 1: 1792/1792).


# ── guards ────────────────────────────────────────────────────────────────────
def test_guards():
    """div refuses the real center (idx==0, where ^8 != conj); both ops reject
    out-of-range bytes."""
    with pytest.raises(ValueError):
        oct_torsor_div(0, 5)          # +e0: idx == 0, not a torsor element
    with pytest.raises(ValueError):
        oct_torsor_div(8, 5)          # -e0: idx == 0
    with pytest.raises(ValueError):
        oct_torsor_act(16, 0)         # out of range
    with pytest.raises(ValueError):
        oct_torsor_div(5, 16)         # out of range
    # a valid imaginary t1 is fine:
    assert oct_torsor_div(5, 6) in range(16)


# ── the acceptance oracle: pure vs c_dispatched byte-identity ─────────────────
def _pure(fn, *a, **k):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn(*a, **k)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_pure_vs_c_dispatched_byte_identity():
    """The ops are composition_of_c over srmech_oct_mult; the c_dispatched value
    must be byte-identical to the pure-cascade value on all 256 pairs."""
    for a in range(16):
        for b in range(16):
            assert oct_torsor_act(a, b) == _pure(oct_torsor_act, a, b)
            if (a & 7) != 0:
                assert oct_torsor_div(a, b) == _pure(oct_torsor_div, a, b)


# ── registration ratchet + no-abs() source guard ─────────────────────────────
def test_registration_ratchet():
    assert "oct_torsor_act" in OCT.__all__
    assert "oct_torsor_div" in OCT.__all__
    from srmech.introspect.tool_schema import tool_schema_view
    view = tool_schema_view()
    assert len(view["tools"]) == 559
    names = {t["name"] for t in view["tools"]}
    assert "srmech.math.octonion.oct_torsor_act" in names
    assert "srmech.math.octonion.oct_torsor_div" in names


def test_rosetta_and_op_name_ledgers():
    here = Path(__file__).resolve().parent
    rosetta = (here / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    rows = [json.loads(ln) for ln in rosetta.splitlines() if ln.strip()]
    for name in ("srmech.math.octonion.oct_torsor_act",
                 "srmech.math.octonion.oct_torsor_div"):
        row = next(r for r in rows if r["exposed_as"] == name)
        assert row["bucket"] == "composition_of_c"
        assert row["defined_at"] == name
    names = (here / "registered_op_names.txt").read_text(encoding="utf-8").split()
    assert "srmech.math.octonion.oct_torsor_act" in names
    assert "srmech.math.octonion.oct_torsor_div" in names


def test_no_abs_in_source():
    """The op CODE must not call abs() — the sign is the Class-K pin bit b>>3,
    re-applied by the Class-C XOR (cascade-honesty discipline). Scan only the
    executable body of each op, after its docstring."""
    src = Path(OCT.__file__).read_text(encoding="utf-8")
    for op in ("oct_torsor_act", "oct_torsor_div"):
        start = src.index(f"def {op}(")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] \
            else len(src)
        func = src[start:end]
        q = '"""'
        d0 = func.index(q)
        d1 = func.index(q, d0 + 3)
        code = func[:d0] + func[d1 + 3:]
        assert "abs(" not in code, f"{op} code must not use abs()"
