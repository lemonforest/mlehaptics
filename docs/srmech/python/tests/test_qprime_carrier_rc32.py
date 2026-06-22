"""rc32 — the **Qprime** graduation: the prime-coordinate exact carrier closes
the LAST harmonic-ladder rung (Class J; F923 / UPSTREAM §74 CAPSTONE).

``Qprime`` carries a positive integer in its prime-coordinate representation —
the exponent vector ``{prime: exponent}`` of the fundamental theorem of
arithmetic ``n = ∏ pᵉ``. The lens: multiplication is ADDITION in
prime-coordinates. It composes the Class-J ``primes.factor`` + Class-I
``cyclic.gcd``/``lcm`` + Class-J ``primes.cyclic_period`` (no new C):

* ``*``           = ADD exponents elementwise  (== ``factor(a·b)``)
* ``gcd``         = elementwise MIN             (== ``cyclic.gcd``)
* ``lcm``         = elementwise MAX             (== ``cyclic.lcm``)
* ``similarity``  = exact cosine² overlap (``Q``); 0 for coprime
* ``period(m)``   = the multiplicative order ``ordₘ(n)`` (the 1/m period lens)

Closing Class J empties ``HARMONIC_LADDER_OPEN_RUNGS`` — no encode blind spots
remain (C/K closed rc31 via ``Qi``, J closed here). Numpy-free + ``math``-free:
srmech + stdlib ``fractions`` + ``random`` (FIXED seed) only.
"""
import random
from fractions import Fraction

import pytest

from srmech.amsc import cyclic, harmonics, primes
from srmech.amsc.q import Q
from srmech.amsc.qprime import Qprime


# ── the 200-pair deterministic exact battery ──────────────────────────────
def _pairs(n=200, seed=20260622):
    """200 deterministic (a, b) pairs over a fixed seed — both within uint64 so
    ``cyclic.lcm`` (uint64-bounded) does not overflow. Range chosen so most
    pairs share factors AND a healthy fraction are coprime."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        a = rng.randint(1, 4096)
        b = rng.randint(1, 4096)
        out.append((a, b))
    return out


def test_round_trip_factor_to_int_200():
    # Qprime(a).to_int() == a — the prime-coordinate round-trip (FTA).
    for a, b in _pairs():
        assert Qprime(a).to_int() == a
        assert Qprime(b).to_int() == b


def test_multiply_is_add_exponents_equals_factor_ab_200():
    # multiply = ADD exponents elementwise, and that EQUALS factor(a·b).
    for a, b in _pairs():
        prod = Qprime(a) * Qprime(b)
        assert prod.coords == Qprime(a * b).coords
        assert prod.to_int() == a * b


def test_gcd_is_min_equals_cyclic_gcd_200():
    # gcd = elementwise MIN over shared primes == cyclic.gcd (Class I).
    for a, b in _pairs():
        assert Qprime(a).gcd(Qprime(b)).to_int() == cyclic.gcd(a, b)


def test_lcm_is_max_equals_cyclic_lcm_200():
    # lcm = elementwise MAX over the prime union == cyclic.lcm (Class I).
    for a, b in _pairs():
        assert Qprime(a).lcm(Qprime(b)).to_int() == cyclic.lcm(a, b)


# ── exact similarity (cosine², a Q) ────────────────────────────────────────
def test_similarity_12_18_is_16_over_25_exact():
    # 12 = 2²·3 → {2:2, 3:1}; 18 = 2·3² → {2:1, 3:2}.
    # dot = 2·1 + 1·2 = 4; ‖a‖² = 4+1 = 5; ‖b‖² = 1+4 = 5; cos² = 16/25.
    sim = Qprime(12).similarity(Qprime(18))
    assert isinstance(sim, Q)
    assert sim == Q(16, 25)
    assert sim == Fraction(16, 25)
    assert float(sim) == 0.64                  # √(16/25) = 0.8 ⇒ cos² = 0.64


def test_similarity_coprime_is_zero():
    # 8 = 2³, 9 = 3² — disjoint support ⇒ dot 0 ⇒ similarity exactly Q(0).
    sim = Qprime(8).similarity(Qprime(9))
    assert isinstance(sim, Q)
    assert sim == Q(0)
    assert float(sim) == 0.0


def test_similarity_self_is_one():
    # cos² of a vector with itself is exactly 1.
    assert Qprime(360).similarity(Qprime(360)) == Q(1)


def test_similarity_with_identity_is_zero():
    # Qprime(1) is the empty (zero-norm) vector — overlap is defined as 0.
    assert Qprime(1).similarity(Qprime(12)) == Q(0)
    assert Qprime(12).similarity(Qprime(1)) == Q(0)


# ── multiplicative-order period (Class J period structure) ─────────────────
def test_period_ord7_10_is_6():
    # ord_7(10) = 6 — the period of the repeating decimal 1/7 = 0.(142857).
    assert Qprime(10).period(7) == 6
    # cross-check directly against the Class-J primitive.
    assert Qprime(10).period(7) == primes.cyclic_period(10, 7)


def test_period_more_cases():
    # ord_5(2) = 4 (2,4,3,1); ord_11(10) = 2 (1/11 = 0.(09)); ord_3(10) = 1.
    assert Qprime(2).period(5) == 4
    assert Qprime(10).period(11) == 2
    assert Qprime(10).period(3) == 1


def test_period_non_coprime_raises_cleanly():
    # ord is undefined when gcd(n, modulus) != 1 — a clean ValueError.
    with pytest.raises(ValueError):
        Qprime(10).period(5)        # gcd(10, 5) = 5
    with pytest.raises(ValueError):
        Qprime(6).period(9)         # gcd(6, 9) = 3
    with pytest.raises(ValueError):
        Qprime(10).period(1)        # modulus < 2


# ── identity / domain guards ───────────────────────────────────────────────
def test_one_is_empty_identity():
    one = Qprime(1)
    assert one.coords == {}
    assert one.to_int() == 1
    # identity under multiply
    q = Qprime(60)
    assert (one * q).coords == q.coords
    assert (q * one).coords == q.coords


def test_zero_and_negative_raise():
    with pytest.raises(ValueError):
        Qprime(0)
    with pytest.raises(ValueError):
        Qprime(-1)
    with pytest.raises(ValueError):
        Qprime(-360)


def test_non_int_raises_type_error():
    for bad in (1.5, "12", None, 3.0):
        with pytest.raises(TypeError):
            Qprime(bad)
    with pytest.raises(TypeError):
        Qprime(True)               # bool excluded


def test_from_vec_round_trips_and_validates():
    qv = Qprime.from_vec({2: 2, 3: 1})
    assert qv.to_int() == 12
    assert qv == Qprime(12)
    # zero exponents dropped; empty dict == identity
    assert Qprime.from_vec({2: 0}).coords == {}
    assert Qprime.from_vec({}) == Qprime(1)
    # non-prime key rejected
    with pytest.raises(ValueError):
        Qprime.from_vec({4: 1})
    # negative exponent rejected
    with pytest.raises(ValueError):
        Qprime.from_vec({2: -1})


def test_coords_is_a_read_only_copy():
    q = Qprime(12)
    c = q.coords
    c[2] = 99                       # mutating the returned dict
    assert q.coords == {2: 2, 3: 1}  # carrier state unchanged


def test_equality_and_hash():
    assert Qprime(12) == Qprime(12)
    assert Qprime(12) != Qprime(18)
    assert hash(Qprime(12)) == hash(Qprime.from_vec({2: 2, 3: 1}))
    # two constructions of the same int hash + compare equal (usable as keys)
    s = {Qprime(60), Qprime(60), Qprime(2 * 2 * 3 * 5)}
    assert len(s) == 1


# ── the CAPSTONE: the harmonic ladder is now EMPTY ─────────────────────────
def test_harmonic_ladder_now_empty_no_open_class():
    # §74 / F923 capstone: NO class remains open on any rung.
    assert harmonics.HARMONIC_LADDER_OPEN_RUNGS == {2: (), 3: ()}
    # no rung carries any open class letter
    open_classes = [c for rung in harmonics.HARMONIC_LADDER_OPEN_RUNGS.values()
                    for c in rung]
    assert open_classes == []
    # the derived predicate agrees
    assert harmonics.harmonic_ladder_fully_closed() is True
