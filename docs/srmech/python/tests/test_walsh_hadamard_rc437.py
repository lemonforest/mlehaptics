"""rc437 (`#T1142`) — the Walsh–Hadamard transform on the boolean cube (ℤ/2)ⁿ.

THE CORRECTNESS ARGUMENT IS THE CHARACTER VALUES, NOT THE INDEX LAW. The index
law here is XOR, and this file deliberately does not use that as evidence: a
census run in this project measured 200/200 random sign tables on the XOR lane
satisfying every structural predicate while 0/200 were associative, so XOR is a
valid REFUTER and an invalid CERTIFIER. What is asserted instead is

  1. the butterfly equals the literal ±1 CHARACTER SUM, computed here by an
     independent O(N²) oracle that shares no code with the shipped op
     (:func:`_dense_character_sum`), and
  2. the involution ``H·H = N·I``,

each with a perturbation control proving it can fail.
"""
from __future__ import annotations

import random

import pytest

from srmech.cascade.walsh_hadamard import (
    _wht_native,
    _wht_pure,
    walsh_hadamard_transform,
)
from srmech.math.q import Q

N_BITS = (0, 1, 2, 3, 4, 5, 6, 7, 8)


def _dense_character_sum(x):
    """THE ORACLE — the literal definition, O(N²), sharing no code with the op:

        X[k] = Σ_j x[j]·(−1)^{popcount(j & k)}

    Deliberately NOT the shipped butterfly and deliberately NOT built from
    ``kron``: an oracle that reuses the subject's own factorisation cannot
    witness the factorisation being wrong.
    """
    n = len(x)
    return [sum(x[j] * (-1 if bin(j & k).count("1") % 2 else 1) for j in range(n))
            for k in range(n)]


# ──────────────────────────────────────────────────────────────────────
# 1. The differential against the character-sum oracle.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n_bits", N_BITS)
def test_butterfly_equals_the_dense_character_sum(n_bits: int) -> None:
    n = 1 << n_bits
    rng = random.Random(1142 + n_bits)
    for _ in range(6):
        x = [rng.randint(-9, 9) for _ in range(n)]
        assert walsh_hadamard_transform(x) == _dense_character_sum(x)


def test_the_oracle_can_actually_disagree() -> None:
    """⚠️ NON-VACUITY. If the oracle returned the butterfly's own answer by
    construction the differential above would be worth nothing. Perturb ONE
    character value and the two must part company."""
    def bent_oracle(x):
        n = len(x)
        out = []
        for k in range(n):
            acc = 0
            for j in range(n):
                sign = -1 if bin(j & k).count("1") % 2 else 1
                if (j, k) == (1, 1):          # the planted single-cell flip
                    sign = -sign
                acc += x[j] * sign
            out.append(acc)
        return out

    x = [3, 1, 4, 1, 5, 9, 2, 6]
    assert walsh_hadamard_transform(x) == _dense_character_sum(x)
    assert walsh_hadamard_transform(x) != bent_oracle(x), (
        "a one-cell perturbation of the character table must change the answer, "
        "or this differential is blind")


def test_the_shipped_basis_vectors_ARE_plus_minus_one() -> None:
    """The correctness argument, made visible: transforming eⱼ returns the jth
    COLUMN of the character table, and every entry of it is +1 or −1 — no root
    of unity, no ring extension, nothing vector-valued."""
    n = 16
    for j in range(n):
        e_j = [1 if k == j else 0 for k in range(n)]
        col = walsh_hadamard_transform(e_j)
        assert set(col) <= {1, -1}, f"column {j} left {{+1,-1}}: {sorted(set(col))}"
        assert all(isinstance(v, int) for v in col)


# ──────────────────────────────────────────────────────────────────────
# 2. The involution — the "reversible basis-change" the HV carrier promises.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n_bits", N_BITS + (9,))
def test_involution_H_squared_is_N_times_identity(n_bits: int) -> None:
    n = 1 << n_bits
    rng = random.Random(770 + n_bits)
    x = [rng.randint(-50, 50) for _ in range(n)]
    assert walsh_hadamard_transform(walsh_hadamard_transform(x)) == [n * v for v in x]


def test_involution_control_a_bent_transform_breaks_it() -> None:
    """⚠️ NON-VACUITY for the involution: a transform with ONE butterfly pass
    dropped is still self-consistent-looking but is not an involution."""
    def short_wht(data):
        out = list(data)
        n = len(out)
        half = 1
        while half < n // 2:                  # one pass short, on purpose
            width = half * 2
            for base in range(0, n, width):
                for j in range(base, base + half):
                    a, b = out[j], out[j + half]
                    out[j], out[j + half] = a + b, a - b
            half = width
        return out

    x = [3, 1, 4, 1, 5, 9, 2, 6]
    assert walsh_hadamard_transform(walsh_hadamard_transform(x)) == [8 * v for v in x]
    assert short_wht(short_wht(x)) != [8 * v for v in x]


# ──────────────────────────────────────────────────────────────────────
# 3. Refusals — a different GROUP is not silently substituted.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_len", (0, 3, 5, 6, 7, 9, 12))
def test_non_power_of_two_length_is_REFUSED_not_padded(bad_len: int) -> None:
    """Zero-padding would answer for (ℤ/2)^⌈log2 N⌉ while the caller asked about
    something that is not a cube at all. The op refuses instead."""
    with pytest.raises(ValueError, match="power of two"):
        walsh_hadamard_transform([1] * bad_len)


def test_float_input_is_REFUSED() -> None:
    with pytest.raises(ValueError, match="exact-integer"):
        walsh_hadamard_transform([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(ValueError, match="exact-integer"):
        walsh_hadamard_transform([1, 2, 3, 4.5])


def test_non_integral_exact_Q_is_REFUSED_but_integral_Q_is_taken() -> None:
    with pytest.raises(ValueError, match="exact-integer"):
        walsh_hadamard_transform([Q(1, 2), Q(1), Q(1), Q(1)])
    assert walsh_hadamard_transform([Q(3), Q(1), Q(4), Q(1)]) == \
        walsh_hadamard_transform([3, 1, 4, 1])


def test_bool_truth_tables_are_accepted() -> None:
    """A cube signal is very often a truth table, and ``bool`` IS an ``int``."""
    assert walsh_hadamard_transform([True, False, True, True]) == \
        walsh_hadamard_transform([1, 0, 1, 1])


# ──────────────────────────────────────────────────────────────────────
# 4. Exactness + the two co-equal implementations.
# ──────────────────────────────────────────────────────────────────────

def test_the_answer_is_exact_int_never_float() -> None:
    out = walsh_hadamard_transform([3, 1, 4, 1, 5, 9, 2, 6])
    assert all(type(v) is int for v in out), [type(v).__name__ for v in out]


def test_bignum_magnitudes_stay_exact() -> None:
    """Past the int64 domain the arbitrary-precision body runs, and it is the
    COMPLETE alternative implementation — same values, no truncation."""
    big = 1 << 200
    assert walsh_hadamard_transform([big, 0, 0, 0]) == [big] * 4
    rng = random.Random(5)
    x = [rng.randint(-(1 << 90), 1 << 90) for _ in range(8)]
    assert walsh_hadamard_transform(x) == _dense_character_sum(x)


def test_native_declines_outside_the_int64_domain() -> None:
    """The magnitude guard must ROUTE, not truncate: the native peer returns
    None above the bound so the bignum body takes over."""
    assert _wht_native([1 << 200, 0, 0, 0]) is None


@pytest.mark.parametrize("n_bits", N_BITS)
def test_the_PURE_body_matches_the_oracle_on_EVERY_host(n_bits: int) -> None:
    """⚠️ THE SHADOWED-BODY GATE, and it exists because the obvious test does
    not cover this.

    MEASURED while building rc437: with a native ``libsrmech`` present,
    ``_wht_native`` preempts, so planting a dropped-butterfly-pass defect in
    ``_wht_pure`` left :func:`test_butterfly_equals_the_dense_character_sum`
    fully GREEN (9 passed) — the public op never reached the broken body. The
    native-vs-pure differential below does catch it (8 failed), but only while
    the two bodies DIVERGE; a defect present in both would pass there too.

    This test calls ``_wht_pure`` directly against the independent character-sum
    oracle, so the pure implementation is measured on a native host as well as
    on a pure / Pyodide checkout, and neither co-equal projection is graded only
    against the other.
    """
    n = 1 << n_bits
    rng = random.Random(6660 + n_bits)
    for _ in range(6):
        x = [rng.randint(-9, 9) for _ in range(n)]
        assert _wht_pure(x) == _dense_character_sum(x)


@pytest.mark.parametrize("n_bits", N_BITS)
def test_native_and_pure_are_byte_identical_when_both_run(n_bits: int) -> None:
    """ADR-0009: the two implementations are co-equal projections of one
    capability. Where the native peer is present it must agree exactly; where it
    is absent (pure / Pyodide checkout) this degenerates to a skip, never to a
    weaker assertion."""
    n = 1 << n_bits
    rng = random.Random(4370 + n_bits)
    for _ in range(4):
        x = [rng.randint(-10 ** 6, 10 ** 6) for _ in range(n)]
        nat = _wht_native(x)
        if nat is None:
            pytest.skip("no native libsrmech with srmech_walsh_hadamard_i64")
        assert nat == _wht_pure(x)


def test_n_equals_one_is_the_trivial_group_not_an_error() -> None:
    """(ℤ/2)⁰ is the one-element group: zero butterfly passes, identity."""
    assert walsh_hadamard_transform([7]) == [7]


# ──────────────────────────────────────────────────────────────────────
# 5. The shipped promise this op was built to make true.
# ──────────────────────────────────────────────────────────────────────

def test_the_HV_carrier_bridge_promise_names_a_REACHABLE_op() -> None:
    """``introspect/carrier_schema.py`` has told every reader of
    ``describe()["carriers"]["HV"]`` that the L↔M bridge is "the reversible
    spectral basis-change (eigen / Walsh-Hadamard)" — while ZERO public
    callables implemented the Walsh-Hadamard half. The prose and the op now ship
    together; this gate keeps them together.

    ⚠️ IT ASSERTS ON BOTH SURFACES, and that is not belt-and-braces. On a native
    host ``carrier_schema()`` answers from the COMPILED
    ``srmech_carrier_registry.c`` table, so reverting the Python source alone
    left this test GREEN when it was checked against the public surface only
    (measured during the rc437 build). Asserting the private source table too
    means a source revert is caught even against a stale ``.so``, and asserting
    the public surface too means a regen-but-do-not-rebuild is caught as well.
    """
    from srmech.introspect.carrier_schema import _CARRIERS, carrier_schema

    named = "srmech.cascade.walsh_hadamard.walsh_hadamard_transform"
    source_desc = _CARRIERS["HV"]["description"]      # the HAND-WRITTEN source
    live_desc = carrier_schema()["HV"]["description"]  # what describe() emits

    for label, desc in (("carrier_schema.py source", source_desc),
                        ("the live describe() surface", live_desc)):
        assert "Walsh-Hadamard" in desc, f"{label}: the bridge sentence is gone"
        assert named in desc, (
            f"{label}: the HV bridge sentence names Walsh-Hadamard but not the "
            f"op that implements it — that is the unkept-promise shape rc437 "
            f"closed, and it shipped for as long as it did precisely because "
            f"nothing compared the two.")

    from srmech.introspect.tool_schema import get_tool_schema
    assert named in {e.name for e in get_tool_schema().tools}, (
        f"{named} is named in shipped carrier prose but is not registered")
