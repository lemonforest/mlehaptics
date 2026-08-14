"""rc318 — Class-N precision-contract migration WAVE 1 prove-gates.

``precision_bits`` → ``precision``: a PURE keyword RENAME on three Class-N ops
(:func:`~srmech.math.rational.sqrt` / :func:`~srmech.math.rational.hypot` /
:func:`~srmech.math.rational.pi_cascade_digits`), plus the generalization of the
rc317 dual-precision pilot helper ``_classn_precision`` into the KIND-
parametrized :func:`~srmech.math.rational._classn_working`. BREAKING, NO legacy
``precision_bits`` alias.

Gates
-----
P1  bit-identity (load-bearing): ``op(…, precision=None)`` reproduces the OLD
    ``op(…, precision_bits=None)`` default BYTE-FOR-BYTE, AND ``op(…,
    precision=P)`` reproduces the OLD ``op(…, precision_bits=P)`` for a range of
    P — asserted against pre-migration reference literals captured from a rc317
    (pre-rename) run. This is what proves ZERO semantic drift.
P2  the uniform contract: ``precision=None`` → platform/default; ``precision=P``
    (int ≥ 1) tightens; bool / non-int / ``P<1`` raise (shared with the pilot).
P3  relative_writhe UNCHANGED under the generalized helper (byte-for-byte). Its
    full F1–F7 gates live in ``test_relative_writhe_rc317.py`` and run in the
    suite; here we pin its exact output + the helper's byte-for-byte mapping.
P4  native == pure: force ``_native.HAS_NATIVE=False`` and re-run P1 — identical.
P5  the OLD ``precision_bits=`` keyword is GONE (raises ``TypeError``; no shim).

numpy-free (no numpy import anywhere in the call graph).
"""
import pytest

from srmech import _native
from srmech.math import rational as R
from srmech.math.rational import (
    sqrt, hypot, pi_cascade_digits, relative_writhe,
    _classn_working, _CLASSN_PLATFORM_DEN_BITS,
)


def _pair(q):
    """The exact ``(num, den)`` int pair of a Class-N ``Q``."""
    n, d = q.as_pair()
    return (int(n), int(d))


# ── pre-migration reference literals ────────────────────────────────────────
# Captured from a rc317 (PRE-rename) run of the SAME ops with ``precision_bits=``
# (native AND numpy-absent pure produced identical values). The rename must
# reproduce each of these byte-for-byte at the matched precision.  None = the
# default (old ``precision_bits=None``); an int key = old ``precision_bits=<key>``.
SQRT_2 = {
    None: (12738103345051545, 9007199254740992),
    10: (181, 128),
    64: (3260954456333195553, 2305843009213693952),
    128: (240615969168004511545033772477625056927,
          170141183460469231731687303715884105728),
}
SQRT_1EM16_DEFAULT = (12089258196146291, 1208925819614629174706176)
SQRT_Q5 = {None: (20140709820486303, 9007199254740992),
           30: (600239927, 268435456)}
SQRT_QHALF = {None: (1, 2), 100: (1, 2)}

HYPOT_1_1 = {
    None: (12738103345051545, 9007199254740992),
    10: (181, 128),
    54: (12738103345051545, 9007199254740992),
}
HYPOT_3_4_DEFAULT = (5, 1)
HYPOT_1EM16_0_DEFAULT = (2028240960365167, 20282409603651670423947251286016)

PI = {
    (15, None, None): "3.141592653589793",
    (0, None, None): "3.",
    (5, 1, 64): "3.16060",
    (5, 10, 128): "3.14159",
    (15, 90, 512): "3.141592653589793",
    (30, None, 200): "3.141592653589793238462643383279",
}

# relative_writhe reference (fixed exact-rational hexagon pair; deterministic).
_RW_REF = [(4, 0, 0), (2, 3, 0), (-2, 3, 0), (-4, 0, 0), (-2, -3, 0), (2, -3, 0)]
_RW_EMB = [(4, 0, 0), (2, 3, 1), (-2, 3, 0), (-4, 0, -1), (-2, -3, 0), (2, -3, 1)]
RW_PLATFORM = {
    "value": (995587514456749, 227029767637520250),
    "remainder_bound": (3338409863235763, 274877906944000000000000000000000),
    "mode": "platform", "precision": 60, "antipodal_events": 0,
    "min_one_plus_dot": (498782532751511651, 254699867791067548),
}
RW_BIG64 = {
    "value": (49299419421302419, 11242041079623413391),
    "remainder_bound": (26234839794194083, 43980465111040000000000000000000000),
    "mode": "bigint", "precision": 64, "antipodal_events": 0,
    "min_one_plus_dot": (2676320630658204768, 1366644711944527063),
}


# ── P1 — bit-identity against the pre-migration reference (the load-bearing gate)
def _assert_bit_identity():
    """Every migrated op at ``precision=None|P`` reproduces the OLD
    ``precision_bits=None|P`` value BYTE-FOR-BYTE. Reused by P4 under forced-pure."""
    q5 = R._q(5, 1)
    qhalf = R._q(1, 4)

    # sqrt (float input) — omitted default AND explicit precision=None both = old None
    assert _pair(sqrt(2.0)) == SQRT_2[None]
    assert _pair(sqrt(2.0, precision=None)) == SQRT_2[None]
    for p in (10, 64, 128):
        assert _pair(sqrt(2.0, precision=p)) == SQRT_2[p], p
    assert _pair(sqrt(1e-16)) == SQRT_1EM16_DEFAULT           # relative-k default path
    # sqrt (Q input)
    assert _pair(sqrt(q5)) == SQRT_Q5[None]
    assert _pair(sqrt(q5, precision=30)) == SQRT_Q5[30]
    assert _pair(sqrt(qhalf)) == SQRT_QHALF[None]
    assert _pair(sqrt(qhalf, precision=100)) == SQRT_QHALF[100]

    # hypot
    assert _pair(hypot(3.0, 4.0)) == HYPOT_3_4_DEFAULT
    assert _pair(hypot(1.0, 1.0)) == HYPOT_1_1[None]
    assert _pair(hypot(1.0, 1.0, precision=None)) == HYPOT_1_1[None]
    for p in (10, 54):
        assert _pair(hypot(1.0, 1.0, precision=p)) == HYPOT_1_1[p], p
    assert _pair(hypot(1e-16, 0.0)) == HYPOT_1EM16_0_DEFAULT

    # pi_cascade_digits
    for (nd, depth, prec), expected in PI.items():
        kw = {}
        if depth is not None:
            kw["max_cascade_depth"] = depth
        if prec is not None:
            kw["precision"] = prec
        assert pi_cascade_digits(nd, **kw) == expected, (nd, depth, prec)


def test_p1_bit_identity_precision_matches_old_precision_bits():
    _assert_bit_identity()


# ── P2 — the uniform contract (shared with the pilot) ───────────────────────
def test_p2_uniform_contract():
    # precision=None → the PLATFORM projection
    plat = _classn_working(None, kind="bits")
    assert plat.mode == "platform"
    assert plat.effective == _CLASSN_PLATFORM_DEN_BITS == 60
    assert (plat.den_bits, plat.sqrt_bits, plat.pi_digits) == (60, 63, 21)

    # precision=P (int ≥ 1) → the BIGINT projection, TIGHTENING with P
    prev_den = None
    for p in (1, 40, 128, 512):
        r = _classn_working(p, kind="bits")
        assert r.mode == "bigint" and r.effective == p
        # the exact pilot mapping, byte-for-byte
        assert (r.den_bits, r.sqrt_bits, r.pi_digits) == (p, p + 4, (p * 302) // 1000 + 3)
        if prev_den is not None:
            assert r.den_bits > prev_den            # bigger P ⇒ more working bits
        prev_den = r.den_bits

    # bool / non-int / P<1 raise
    with pytest.raises(TypeError):
        _classn_working(True, kind="bits")          # bool is NOT a valid int here
    with pytest.raises(TypeError):
        _classn_working(1.5, kind="bits")           # non-int
    with pytest.raises(ValueError):
        _classn_working(0, kind="bits")             # P < 1
    with pytest.raises(ValueError):
        _classn_working(-4, kind="bits")

    # kind="terms" is now IMPLEMENTED (rc320 WAVE 2) — same None/int dispatch as
    # the bits wave; kind="den" is still reserved for a later wave.
    assert _classn_working(None, kind="terms").mode == "platform"
    assert _classn_working(64, kind="terms").mode == "bigint"
    assert _classn_working(64, kind="terms").effective == 64
    with pytest.raises(NotImplementedError):
        _classn_working(64, kind="den")


# ── P3 — relative_writhe UNCHANGED under the generalized helper ──────────────
def _assert_relative_writhe_reference():
    plat = relative_writhe(_RW_EMB, _RW_REF)
    for k, v in RW_PLATFORM.items():
        assert plat[k] == v, (k, plat[k])
    big = relative_writhe(_RW_EMB, _RW_REF, precision=64)
    for k, v in RW_BIG64.items():
        assert big[k] == v, (k, big[k])


def test_p3_relative_writhe_unchanged():
    # relative_writhe now routes through _classn_working(precision, kind="bits");
    # the bits-branch mapping is the pilot's, so its output is byte-for-byte the
    # rc317 value. (Its full F1–F7 gates run in test_relative_writhe_rc317.py.)
    _assert_relative_writhe_reference()

    # a curve against ITSELF is exactly 0 (the F5 invariant, unchanged)
    assert relative_writhe(_RW_REF, _RW_REF)["value"] == (0, 1)


# ── P4 — native == pure (byte-identical) ────────────────────────────────────
def test_p4_native_equals_pure(monkeypatch):
    # P1 + the relative_writhe reference hold identically with the pure-Python
    # fallback forced on every dispatching Class-N op.
    monkeypatch.setattr(_native, "HAS_NATIVE", False, raising=False)
    monkeypatch.setattr(_native, "LIB", None, raising=False)
    _assert_bit_identity()
    _assert_relative_writhe_reference()


# ── P5 — the OLD precision_bits= keyword is GONE (clean break, not shimmed) ──
def test_p5_precision_bits_keyword_is_removed():
    with pytest.raises(TypeError):
        sqrt(4, precision_bits=8)
    with pytest.raises(TypeError):
        sqrt(R._q(4, 1), precision_bits=8)
    with pytest.raises(TypeError):
        hypot(3.0, 4.0, precision_bits=8)
    with pytest.raises(TypeError):
        pi_cascade_digits(5, precision_bits=64)
    # the new keyword IS accepted (control: not a blanket kwarg rejection)
    assert _pair(sqrt(4.0, precision=8)) == _pair(sqrt(4.0, precision=8))
