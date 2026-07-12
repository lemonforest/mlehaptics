"""#765 FOUNDATION (0.9.0rc167): the Python-side exact-ℚ native dispatch.

The ``Q`` scalar carrier's big-operand arithmetic now runs on srmech's OWN
C bignum (``srmech_bigint``) — CPython ``int`` demoted to the below-threshold /
no-native fallback — via the ``_native.bigq_add_c / bigq_mul_c / bigq_div_c /
bigq_reduce_c`` composites wired into ``rational.rational_add/mul/div`` +
``_reduce_rational``, and ``cyclic.gcd``'s beyond-u64 branch via
``_native.bigint_gcd_c``. Plus #770: the decimal marshal is replaced by the
LINEAR, cap-free binary limb marshal (``int.to_bytes/from_bytes("little")``
straight into/out of the caller-owned limb buffer — ``srmech_bigint`` is
base-2³² little-endian sign-magnitude, i.e. exactly little-endian bytes).

This test pins:
  1. ``Q`` byte-identical to ``fractions.Fraction`` across ``+ − × ÷ // % **``
     + comparisons, at SMALL and HUGE (up to 5000-bit) operands — dispatched
     or not, the values are the same two integers;
  2. the binary limb marshal round-trips exactly (0 / ±1 / ±10⁵⁰⁰⁰ / a
     200000-bit value — far over the old 4300-digit int↔str cap) and agrees
     with the decimal C bridge where both exist;
  3. the native path is GENUINELY EXERCISED for big-ℚ ops (the
     ``BIGQ_DISPATCH_COUNT`` counter moves — no silent fallback) and NOT
     taken below the size-adaptive threshold;
  4. forced-fallback (native gate off) is byte-identical to the dispatched
     results — CPython int is the complete alternative, never a divergence;
  5. ``cyclic.gcd`` big-operand dispatch parity (gcd is unique ⇒ identical);
  6. the representative carrier proof: huge-coord ``Qalg`` field ops dispatch
     through their ℚ components while the carrier's SPARSE structure (the
     coords tuple over the minimal-poly relation ``m``) is untouched, and the
     values match a ``fractions.Fraction`` oracle exactly;
  7. the ``qprime.similarity`` repoint (``Fraction`` intermediate → direct
     ``Q``) is byte-identical and leaves ``qprime`` fractions-free;
  8. the size-adaptive thresholds are the measured, attested constants;
  9. perf sanity: the dispatched huge-ℚ op stays within the measured
     cost-parity band of the pure path (correct + dispatched is the gate; the
     measured verdict is parity, not speedup — see CHANGELOG 0.9.0rc167).

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import random
import time
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc import cyclic as _cyclic
from srmech.amsc import qprime as _qprime_mod
from srmech.amsc import rational as _rational
from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg
from srmech.amsc.qprime import Qprime

_HAS_BIGQ = _native.has_native_bigq()

needs_bigq = pytest.mark.skipif(
    not _HAS_BIGQ, reason="native srmech_bigint arithmetic core not loaded")


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the rc167 dispatch tests must run on the numpy-ABSENT matrix")


# ── 8. the attested size-adaptive thresholds (drift must be deliberate) ─────
def test_thresholds_are_the_measured_constants():
    """Both thresholds are attested-to-measurement (Class B; WSL2 gcc -O2,
    Python 3.12, binary marshal): 1024 bits is the measured parity onset —
    below it the native path clearly loses (0.26–0.83×), at/above it the
    dispatch is cost-parity and buys the #765 self-hosting substrate. A change
    here must come with a new measurement (see CHANGELOG 0.9.0rc167)."""
    assert _rational._BIGQ_MIN_BITS == 1024
    assert _cyclic._GCD_NATIVE_MIN_BITS == 1024


# ── 1. Q byte-identical to Fraction, small + huge ────────────────────────────
def _pairs(bits, count, rng):
    for _ in range(count):
        an = rng.getrandbits(bits) - (1 << (bits - 1))
        ad = rng.getrandbits(bits) + 1
        bn = rng.getrandbits(bits) - (1 << (bits - 1))
        bd = rng.getrandbits(bits) + 1
        if an == 0 or bn == 0:
            continue
        yield an, ad, bn, bd


def _assert_q_eq_fraction(q, f, ctx):
    assert (q.numerator, q.denominator) == (f.numerator, f.denominator), (
        f"{ctx}: Q={q!r} vs Fraction={f!r}")


@pytest.mark.parametrize("bits", [8, 48, 500, 1024, 2200, 5000])
def test_q_byte_identical_to_fraction(bits):
    """Every Q result is the SAME reduced (num, den) integer pair Fraction
    produces — across the arithmetic + comparison surface, at every size tier
    (u64 scalar-C / CPython-int mid / srmech_bigint huge)."""
    rng = random.Random(0xC167 + bits)
    for an, ad, bn, bd in _pairs(bits, 25, rng):
        q1, q2 = Q(an, ad), Q(bn, bd)
        f1, f2 = Fraction(an, ad), Fraction(bn, bd)
        _assert_q_eq_fraction(q1 + q2, f1 + f2, f"add@{bits}")
        _assert_q_eq_fraction(q1 - q2, f1 - f2, f"sub@{bits}")
        _assert_q_eq_fraction(q1 * q2, f1 * f2, f"mul@{bits}")
        _assert_q_eq_fraction(q1 / q2, f1 / f2, f"div@{bits}")
        _assert_q_eq_fraction(q1 % q2, f1 % f2, f"mod@{bits}")
        _assert_q_eq_fraction(q1 ** 3, f1 ** 3, f"pow3@{bits}")
        _assert_q_eq_fraction((q1 * q1) ** -2 if q1 != 0 else Q(1, 1),
                              (f1 * f1) ** -2 if f1 != 0 else Fraction(1),
                              f"powneg@{bits}")
        assert (q1 // q2) == (f1 // f2), f"floordiv@{bits}"
        assert (q1 < q2) == (f1 < f2)
        assert (q1 == q2) == (f1 == f2)
        assert (q1 >= q2) == (f1 >= f2)


# ── 2. the #770 binary limb marshal ──────────────────────────────────────────
@needs_bigq
def test_binary_marshal_roundtrip_exact_and_cap_free():
    """int → srmech_bigint → int round-trips EXACTLY, including values far
    over the old 4300-digit decimal int↔str cap (the binary marshal never
    converts int↔str, so the cap does not apply at all)."""
    rng = random.Random(0x770)
    values = [0, 1, -1, 7, -7, 10 ** 5000, -(10 ** 5000),
              (1 << 200000) - 3, -((1 << 131072) + 12345),
              rng.getrandbits(9999) | 1]
    for v in values:
        mag = v if v >= 0 else -v            # Class-K sign branch, no abs()
        cap = max(mag.bit_length() // 32 + 2, 2)
        bi, keep = _native._bigint_from_int(v, cap)
        # struct invariants: no leading-zero limb; sign == 0 iff n == 0
        assert (bi.n == 0) == (v == 0)
        assert (bi.sign == 0) == (v == 0)
        if v != 0:
            assert bi.limbs[bi.n - 1] != 0, "leading-zero limb"
        assert _native._bigint_to_int(bi) == v


@needs_bigq
def test_binary_marshal_agrees_with_decimal_bridge():
    """The binary marshal and the (still-exported) decimal C bridge carry the
    SAME value — the wire format did not change, only the Python-side path."""
    import ctypes
    v = 10 ** 1200 + 987654321
    bi, keep = _native._bigint_from_int(v, v.bit_length() // 32 + 2)
    a_n = bi.n
    cap = int(_native.LIB.srmech_bigint_to_dec_bound(ctypes.c_size_t(a_n))) + 8
    buf = ctypes.create_string_buffer(cap)
    out_len = ctypes.c_size_t(0)
    sw = a_n * 12 + 64
    scratch = (ctypes.c_uint8 * (sw * 4))()
    rc = _native.LIB.srmech_bigint_to_dec(
        ctypes.byref(bi), buf, ctypes.c_size_t(cap), ctypes.byref(out_len),
        ctypes.cast(scratch, ctypes.c_void_p), ctypes.c_size_t(sw * 4))
    assert rc == _native.SRMECH_OK
    assert bytes(buf)[:out_len.value].decode("ascii") == str(v)


# ── 3. the native path is genuinely exercised / correctly gated ─────────────
@needs_bigq
def test_big_q_ops_dispatch_to_srmech_bigint():
    """A huge-ℚ op MUST move the dispatch counter — the #765 self-hosting is
    real, not a silent fallback."""
    bits = 1500
    rng = random.Random(0x765)
    an, ad, bn, bd = next(_pairs(bits, 1, rng))
    before = _native.BIGQ_DISPATCH_COUNT
    q1, q2 = Q(an, ad), Q(bn, bd)
    _ = q1 + q2
    _ = q1 * q2
    _ = q1 / q2
    assert _native.BIGQ_DISPATCH_COUNT >= before + 3, (
        "big-ℚ add/mul/div did not dispatch to srmech_bigint")
    # the reduce path (Q construction from a huge un-reduced pair) dispatches
    before = _native.BIGQ_DISPATCH_COUNT
    g = rng.getrandbits(1200) | 1
    _ = Q((rng.getrandbits(1200) | 1) * g, (rng.getrandbits(1200) | 1) * g)
    assert _native.BIGQ_DISPATCH_COUNT > before, (
        "huge-ℚ reduce did not dispatch to srmech_bigint")


@needs_bigq
def test_small_q_ops_do_not_dispatch():
    """Below the measured threshold the dispatch must NOT fire (it is a
    measured loss there — the u64 scalar C ops / CPython int own that tier)."""
    before = _native.BIGQ_DISPATCH_COUNT
    q = Q(123456789, 987654321) + Q(555555, 777777)
    q = q * Q(22, 7) / Q(355, 113)
    _ = _cyclic.gcd(123456789123456789, 987654321987654321)
    assert _native.BIGQ_DISPATCH_COUNT == before, (
        "a below-threshold op dispatched to srmech_bigint")


# ── 4. forced fallback is byte-identical (complete alternative) ──────────────
@needs_bigq
def test_forced_fallback_byte_identical(monkeypatch):
    bits = 2048
    rng = random.Random(0xFA11)
    cases = list(_pairs(bits, 6, rng))
    native_results = []
    for an, ad, bn, bd in cases:
        native_results.append((
            _rational.rational_add((an, ad), (bn, bd)),
            _rational.rational_mul((an, ad), (bn, bd)),
            _rational.rational_div((an, ad), (bn, bd)),
        ))
    monkeypatch.setattr(_native, "has_native_bigq", lambda: False)
    for (an, ad, bn, bd), nat in zip(cases, native_results):
        pure = (
            _rational.rational_add((an, ad), (bn, bd)),
            _rational.rational_mul((an, ad), (bn, bd)),
            _rational.rational_div((an, ad), (bn, bd)),
        )
        assert pure == nat, "pure fallback diverged from the dispatched result"


# ── 5. cyclic.gcd big-operand dispatch ───────────────────────────────────────
@needs_bigq
def test_cyclic_gcd_big_dispatch_and_parity():
    rng = random.Random(0x6CD)
    g0 = rng.getrandbits(800) | 1
    a = g0 * (rng.getrandbits(700) | 1)
    b = g0 * (rng.getrandbits(700) | 1)
    before = _native.BIGQ_DISPATCH_COUNT
    g = _cyclic.gcd(a, b)
    assert _native.BIGQ_DISPATCH_COUNT > before, "big gcd did not dispatch"
    x, y = a, b
    while y:
        x, y = y, x % y
    assert g == x, "native gcd != pure Euclid (gcd is unique)"


# ── 6. the representative carrier proof: Qalg field ops over huge Q coords ──
def _fraction_field_mul(ca, cb, m):
    """Fraction oracle of Qalg.__mul__: convolve then reduce mod monic m."""
    n = len(m) - 1
    conv = [Fraction(0)] * (2 * n - 1)
    for i, x in enumerate(ca):
        for j, y in enumerate(cb):
            conv[i + j] += x * y
    work = list(conv)
    for idx in range(len(work) - 1, n - 1, -1):
        top = work[idx]
        if top == 0:
            continue
        work[idx] = Fraction(0)
        base = idx - n
        for j in range(n):
            if m[j] != 0:
                work[base + j] = work[base + j] - top * m[j]
    return work[:n]


def test_qalg_huge_coords_parity_and_sparse_structure():
    """The carrier repoint pattern, proven end-to-end: Qalg already carries Q
    components, so with the dispatch UNDER Q its big-coord field ops run on
    srmech_bigint with ZERO carrier-code change — and the carrier's sparse
    organization (coords tuple over the minimal-poly relation) is untouched
    (the ⚠️ sparse-tower guardrail: only the ℚ COMPONENTS dispatch)."""
    m = (2, 0, 0, 1)                       # x³ + 2, monic irreducible
    big = 1 << 1600
    ca = [Q(big + 7, 3), Q(-big + 11, 5), Q(big // 3 + 1, 7)]
    cb = [Q(big - 13, 9), Q(big + 17, 11), Q(-big + 19, 13)]
    a, b = Qalg(m, ca), Qalg(m, cb)
    before = _native.BIGQ_DISPATCH_COUNT
    prod = a * b
    quot = a / b
    if _HAS_BIGQ:
        assert _native.BIGQ_DISPATCH_COUNT > before, (
            "huge-coord Qalg ops did not dispatch through their Q components")
    # sparse structure preserved: same m, coords stays a length-deg(m) tuple
    assert prod.m == m and quot.m == m
    assert isinstance(prod.coords, tuple) and len(prod.coords) == 3
    # value parity vs the Fraction oracle (byte-identical reduced pairs)
    fa = [Fraction(q.numerator, q.denominator) for q in ca]
    fb = [Fraction(q.numerator, q.denominator) for q in cb]
    for pc, fc in zip(prod.coords, _fraction_field_mul(fa, fb, m)):
        assert (pc.numerator, pc.denominator) == (fc.numerator, fc.denominator)
    # exact field inverse round-trip
    assert (quot * b).coords == a.coords


# ── 7. the qprime.similarity repoint ─────────────────────────────────────────
def test_qprime_similarity_repoint_byte_identical():
    s = Qprime(12).similarity(Qprime(18))
    assert (s.numerator, s.denominator) == (16, 25)
    # huge exponent vectors: the Q components are big enough to dispatch
    e = 10 ** 6
    big1 = Qprime.from_vec({2: e, 3: e, 5: 1})
    big2 = Qprime.from_vec({2: e, 3: 1})
    sim = big1.similarity(big2)
    dot = e * e + e
    oracle = Fraction(dot * dot, (e * e + e * e + 1) * (e * e + 1))
    assert (sim.numerator, sim.denominator) == (
        oracle.numerator, oracle.denominator)


def test_qprime_module_is_fractions_free():
    """The repoint removed qprime's LAST Fraction use — the module no longer
    imports fractions at all (its ℚ result rides the Q carrier directly)."""
    assert not hasattr(_qprime_mod, "Fraction")


# ── 9. perf sanity: dispatched stays in the measured cost-parity band ───────
@needs_bigq
def test_perf_sanity_dispatch_is_cost_parity_not_pathological(monkeypatch):
    """The DoD gate is 'correct + genuinely dispatched'; the measured verdict
    is COST-PARITY (~0.9–1.3× at ≥1024 bits; CHANGELOG 0.9.0rc167). Pin that
    the dispatched path is not pathologically slower than the pure body (a
    generous 3× band — CI machines are noisy; the real measurement lives in
    the CHANGELOG table)."""
    bits = 2048
    rng = random.Random(0x9E2F)
    an, ad, bn, bd = next(_pairs(bits, 1, rng))

    def run_once():
        t0 = time.perf_counter()
        for _ in range(40):
            _rational.rational_add((an, ad), (bn, bd))
            _rational.rational_mul((an, ad), (bn, bd))
        return time.perf_counter() - t0

    before = _native.BIGQ_DISPATCH_COUNT
    t_native = min(run_once() for _ in range(3))
    assert _native.BIGQ_DISPATCH_COUNT > before, "perf run did not dispatch"
    monkeypatch.setattr(_native, "has_native_bigq", lambda: False)
    t_pure = min(run_once() for _ in range(3))
    assert t_native <= 3.0 * t_pure, (
        f"dispatched path pathologically slow: native={t_native:.6f}s "
        f"vs pure={t_pure:.6f}s")
