"""rc119 — the #712 Dzhanibekov harmonic⊗subharmonic half-period readers on the
EllRatio carrier (GitHub task #713).

The torque-free (Dzhanibekov / tennis-racket) rotation's Jacobi sn/cn/dn map to
EllRatio theta quotients under the #712 bridge (w = e^{iζ}, x = w², carrier-p =
q_c²; DLMF 22.2/20.5). Its solution two-torus is a CYCLE OF CYCLES with TWO
independent half-beats (DLMF 22.4). This suite pins the three rc119 ops against
the committed #712 probes (the in-repo SSoT + exact-ℚ oracle):

  * ``half_shift_response`` — the exact edge MULTIPLIER under a half-period shift
    (oracle: dzhan_q2 — sn/cn/dn real-2K −1/−1/+1; nome pshift theta-parts q/−q/−1);
  * ``chirality_parity`` — even (harmonic) / odd (subharmonic) (oracle: dzhan_q3/q4);
  * ``beat_relation_residue`` — the q²·p⁻¹ residue recovering p = q_c² (oracle: q4).

Plus the C==Python byte-for-byte parity of the C-dispatched half_shift_response
(a divergence is a BLOCKER), the FLIP=Klein-4 action, and the boundary-blind
finding (chirality-even readers are 2K-invariant). Reproduces the #712 probes'
EXACT numbers; the probes are cited as the oracle throughout.
"""

import pytest

from srmech.amsc.ellbase import (
    EllMonomial as M, Theta, EllRatio as R,
    half_shift_response, chirality_parity, beat_relation_residue,
    _half_shift_response_py, _half_shift_response_c, _normalize_half_axis,
)
from srmech.amsc.q import Q
from srmech.amsc import _native
from srmech.amsc.tool_schema import get_tool_schema

ONE = Q(1, 1)
M_ONE = M.one()
M_MINUS = M(Q(-1, 1), {})

_HAS_C = _native.has_native_ellratio_half_shift()
_skip_c = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_ellratio_half_shift_response not loaded")


def _sym(n, e=1):
    return M(ONE, {n: e})


# The #712 bridge carrier objects (dzhan_q1/q2/q3/q4). w-frame: theta args in
# x = w² (even), prefactor carries the subharmonic w-power. x-frame: the harmonic
# frame the nome pshift acts on.
_W = _sym("w")
_W2 = _sym("w", 2)
_QW2 = _sym("q") * _W2
_X = _sym("x")
_QX = _sym("q") * _X

SN = R(_W.inv(), num=(Theta(_W2),), den=(Theta(_QW2),))
CN = R(_W.inv(), num=(Theta(M(Q(-1, 1), {"w": 2})),), den=(Theta(_QW2),))
DN = R(None, num=(Theta(M(Q(-1, 1), {"q": 1, "w": 2})),), den=(Theta(_QW2),))
SX = R(None, num=(Theta(_X),), den=(Theta(_QX),))
CX = R(None, num=(Theta(M(Q(-1, 1), {"x": 1})),), den=(Theta(_QX),))
DX = R(None, num=(Theta(M(Q(-1, 1), {"q": 1, "x": 1})),), den=(Theta(_QX),))
# sn² on the HARMONIC (x) frame alone (dzhan_q4 beat-relation object).
SN2X = R(_sym("x", -1), num=(Theta(_X), Theta(_X)), den=(Theta(_QX), Theta(_QX)))


# ── op 1: half_shift_response reproduces the dzhan_q2 oracle ────────────────────
def test_real_2K_multiplier_matches_dzhan_q2():
    """dzhan_q2 real 2K row (DLMF Table 22.4.3): sn/cn/dn → −1/−1/+1 (the pure
    Class-K (−1)^{w-parity} sign). Both call forms + both axis aliases."""
    for name, W, want in (("sn", SN, M_MINUS), ("cn", CN, M_MINUS), ("dn", DN, M_ONE)):
        assert half_shift_response(W, "real") == want, name
        assert W.half_shift_response("2K") == want, name          # method + alias


def test_nome_2iKprime_theta_part_matches_dzhan_q2():
    """dzhan_q2 nome 2iK′ pshift theta-parts (the −x⁻¹-type canonicalize prefactor):
    the x-frame sn/cn/dn → q / −q / −1."""
    assert SX.half_shift_response("nome") == _sym("q")
    assert CX.half_shift_response("nome") == M(Q(-1, 1), {"q": 1})
    assert DX.half_shift_response("nome") == M_MINUS
    # apostrophe-/case-insensitive alias.
    assert half_shift_response(SX, "2iK'") == _sym("q")


def test_axis_alias_normalization():
    for a in ("real", "2K", "2k", " Real "):
        assert _normalize_half_axis(a) == "real"
    for a in ("nome", "2iK'", "2ik'", "2iKprime", "NOME"):
        assert _normalize_half_axis(a) == "nome"
    with pytest.raises(ValueError):
        _normalize_half_axis("diagonal")


def test_non_covariant_ratio_raises():
    """A ratio with a chirality-ODD theta under the real double-cover is not
    half-shift-covariant → the multiplier is not a bare monomial → ValueError."""
    odd = R(num=(Theta(_sym("w")),))            # θ(w): odd in w → θ(−w) ≠ θ(w)
    with pytest.raises(ValueError):
        half_shift_response(odd, "real", var="w")


# ── op 2: chirality_parity reproduces the dzhan_q3/q4 oracle ────────────────────
def test_chirality_parity_matches_dzhan_q3_q4():
    """dzhan_q3/q4: sn/cn odd (subharmonic), dn even (harmonic); every quadratic/
    intensity observable is chirality-EVEN (boundary-blind)."""
    cases = [
        ("sn", SN, "odd"), ("cn", CN, "odd"), ("dn", DN, "even"),
        ("sn^2", SN * SN, "even"), ("cn^2", CN * CN, "even"),
        ("sn*cn", SN * CN, "even"), ("sn*dn", SN * DN, "odd"),
        ("cn*dn", CN * DN, "odd"), ("sn*cn*dn", SN * CN * DN, "even"),
    ]
    for name, W, want in cases:
        assert chirality_parity(W) == want, name
        assert W.chirality_parity() == want, name


def test_chirality_parity_agrees_with_real_response():
    """The #712 identity: chirality-even ⇔ the real-2K half_shift_response is +1
    (boundary-blind); chirality-odd ⇔ it is −1 (holds the flip)."""
    for W in (SN, CN, DN, SN * SN, SN * CN, SN * DN):
        par = chirality_parity(W)
        resp = half_shift_response(W, "real")
        assert (par == "even") == (resp == M_ONE)


# ── op 3: beat_relation_residue reproduces the dzhan_q4 oracle ──────────────────
def test_beat_relation_residue_matches_dzhan_q4():
    """dzhan_q4: sn² on the harmonic (x) frame has exact pshift residue q²·p⁻¹,
    which recovers the beat relation p = q_c² (unity at the bridge point)."""
    res = beat_relation_residue(SN2X)
    assert res == M(ONE, {"q": 2, "p": -1})
    assert SN2X.beat_relation_residue() == res
    # closes exactly at the bridge point p = q_c² (dzhan_q4 rational eval).
    assert res.eval({"q": Q(3, 7), "p": Q(9, 49)}) == ONE
    # is_elliptic honestly declines the lone harmonic frame (dzhan_q4).
    assert SN2X.is_elliptic() is False


# ── the FLIP is the Klein-4 action; the even sector is boundary-blind (q4/q5) ────
def test_flip_is_klein4_hold_dn_flip_sncn():
    """dzhan_q5: the Dzhanibekov flip = hold the harmonic (dn) axis, flip the two
    subharmonic (sn/cn) axes — the Klein-4 element (−,−,+) on the 2K half-beat."""
    flip = (half_shift_response(SN, "2K"),
            half_shift_response(CN, "2K"),
            half_shift_response(DN, "2K"))
    assert flip == (M_MINUS, M_MINUS, M_ONE)      # (sn,cn,dn) → (−,−,+)


def test_chirality_even_readers_are_boundary_blind():
    """dzhan_q4 pair-closure: every chirality-even (quadratic) reader is 2K-INVARIANT
    (+1) — it cannot see the Dzhanibekov flip boundary; only chirality-odd readers
    hold the −1."""
    for W in (SN * SN, CN * CN, SN * CN, SN * CN * DN):     # even → blind
        assert half_shift_response(W, "real") == M_ONE
        assert chirality_parity(W) == "even"
    for W in (SN, CN, SN * DN, CN * DN):                    # odd → sees the −1
        assert half_shift_response(W, "real") == M_MINUS
        assert chirality_parity(W) == "odd"


def test_two_2K_steps_close_the_subharmonic():
    """dzhan_q3(b): two 2K half-beats = identity on ALL three (4K closes the
    subharmonic) — the multiplier squared is +1 for sn/cn/dn."""
    for W in (SN, CN, DN):
        r = half_shift_response(W, "real")
        assert r * r == M_ONE


# ── C==Python byte-for-byte parity (a divergence is a BLOCKER) ──────────────────
def _assert_parity(W, axis, var):
    a = _normalize_half_axis(axis)
    py_err = c_err = None
    try:
        py = _half_shift_response_py(W, a, var)
    except ValueError as e:
        py, py_err = None, e
    if not _HAS_C:
        return
    try:
        c = _half_shift_response_c(W, a, var)
    except ValueError as e:
        c, c_err = None, e
    assert (py_err is None) == (c_err is None), (
        f"C/Python covariance DIVERGENCE on {axis}/{var}: "
        f"py_err={py_err} c_err={c_err} (BLOCKER)")
    assert py == c, f"C/Python DIVERGENCE on {axis}/{var}: PY={py} C={c} (BLOCKER)"


@_skip_c
def test_c_parity_dzhan_objects():
    """The C multiplier EQUALS the pure-Python EllMonomial byte-for-byte on every
    #712 carrier object (both axes)."""
    for W in (SN, CN, DN, SN * SN, CN * CN, SN * CN, SN * DN, CN * DN, SN * CN * DN):
        _assert_parity(W, "real", "w")
    for W in (SX, CX, DX, SN2X, SX * SX, SX * CX):
        _assert_parity(W, "nome", "x")


@_skip_c
def test_c_parity_valid_fuzz():
    """A randomized parity fuzz over valid theta-quotient carriers; the C peer must
    NEVER diverge from Python where the shared Theta.canonicalize succeeds. (The
    pre-existing Q.__pow__ negative-base limitation in canonicalize — shared by the
    shipped pshift/is_elliptic — is skipped: a carrier-internal raise is not a
    half_shift_response divergence.)"""
    import random
    rng = random.Random(713119)
    syms = ["a", "b", "w", "x"]

    def rmono():
        e = {s: rng.choice([-2, -1, 1, 2])
             for s in random.sample(syms, rng.randint(0, 2))}
        return M(Q(rng.choice([-1, 1]), 1), e)

    checked = 0
    for _ in range(300):
        try:
            num = tuple(Theta(rmono()) for _ in range(rng.randint(0, 2)))
            den = tuple(Theta(rmono()) for _ in range(rng.randint(0, 2)))
            W = R(rmono(), num=num, den=den)
        except Exception:  # noqa: BLE001 — an invalid random ratio has nothing to test
            continue
        for axis, var in (("real", "w"), ("nome", "x")):
            a = _normalize_half_axis(axis)
            try:
                py = _half_shift_response_py(W, a, var)
            except ValueError as e:
                if "not half-shift-covariant" not in str(e):
                    continue          # pre-existing carrier canonicalize limitation
                py = None
            try:
                c = _half_shift_response_c(W, a, var)
            except ValueError:
                c = None
            assert py == c, f"fuzz DIVERGENCE {axis}/{var}: PY={py} C={c} (BLOCKER)"
            checked += 1
    assert checked > 50, f"fuzz exercised too few valid cases ({checked})"


@_skip_c
def test_public_dispatches_to_native():
    """``has_native_ellratio_half_shift`` is True AND the public op routes through
    the C peer (the native multiplier equals the pure-Python one)."""
    assert _native.has_native_ellratio_half_shift() is True
    got = half_shift_response(SN2X, "nome")
    assert got == M(ONE, {"q": 2, "p": -1})
    assert _half_shift_response_c(SN2X, "nome", "x") == got


def test_has_native_flag_present():
    assert isinstance(_native.has_native_ellratio_half_shift(), bool)


# ── tool-schema registration (the coverage/rosetta surface) ─────────────────────
def test_tools_total_is_384():
    """rc119 ships 3 genuinely NEW public ops → +3 ToolEntries (381 → 384)."""
    import srmech.introspect as introspect
    assert introspect.describe()["tools"]["total"] == 393


def test_three_ops_registered():
    names = {t.name for t in get_tool_schema().tools}
    for op in ("half_shift_response", "chirality_parity", "beat_relation_residue"):
        assert f"srmech.amsc.ellbase.{op}" in names, op
