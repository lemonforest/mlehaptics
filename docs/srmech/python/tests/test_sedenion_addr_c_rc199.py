"""Sedenion ADDRESS-ALGEBRA leaves — pure-vs-native parity (v0.9.0rc199).

make_class → C, leaf-batch 5/8 (#887): the 8 address-algebra ``sed_*`` leaves of
the ``sedenion_register.toml`` ``[class]`` each dispatch to a SINGLE dedicated C
peer when ``HAS_NATIVE`` (mostly marshalling glue over already-shipped kernels +
the ONE new ``srmech_sed_slots`` reshape), with the exact pure Python as the
fallback + parity oracle:

    sed_navmap          -> srmech_sedenion_navmap          (reused; EXACT)
    sed_navigate        -> srmech_sedenion_navigate        (reused; EXACT)
    sed_is_navigable    -> srmech_sedenion_is_navigable    (reused; EXACT)
    sed_carry           -> srmech_hamming_encode           (reused; EXACT)
    sed_correct         -> srmech_hamming_decode_correct   (reused; EXACT)
    sed_slots           -> srmech_sed_slots                (NEW;    EXACT)
    sed_couple_working  -> srmech_hypercomplex_couple_q61  (reused; NUM ≤1e-9)
    sed_uncouple_working-> srmech_hypercomplex_couple_q61  (reused; NUM ≤1e-9)

Every parity check toggles ``_native.HAS_NATIVE`` off to force the pure path and
compares against the (default) native path — so it PASSES (not skips) with the
native lib loaded, and is a no-op-equal (pure == pure) when there is no lib.
numpy-free.
"""
import contextlib

import pytest

from srmech import _native
from srmech.cascade.sedenion_register import (
    SedenionRegister, NUM_SLOTS,
    sed_navmap, sed_navigate, sed_is_navigable, sed_carry,
    sed_correct, sed_slots, sed_couple_working, sed_uncouple_working,
)


@contextlib.contextmanager
def force_pure():
    """Force the whole native stack to the pure Python fallback by dropping
    ``_native.HAS_NATIVE`` for the duration (every dispatch guard + every
    ``has_native_*`` helper reads it at call time)."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved


_HAS_SED_SLOTS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_sed_slots")
)


def _within_tol(a, b, tol=1e-9):
    assert len(a) == len(b), f"length mismatch: {len(a)} vs {len(b)}"
    for x, y in zip(a, b):
        d = x - y
        d = d if d >= 0.0 else -d          # Class-K magnitude; never abs()
        assert d <= tol, f"|{x} - {y}| = {d} > {tol}"


def _register():
    r = SedenionRegister()
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(10, "gamma")
    r.write(7, "delta", sign=-1)
    return r


# ── the 6 EXACT leaves: native == pure BYTE-IDENTICAL ─────────────────────────

def test_navmap_native_equals_pure():
    for j in range(NUM_SLOTS):
        native = sed_navmap(j)
        with force_pure():
            pure = sed_navmap(j)
        assert native == pure
        # structural: a signed permutation e_i·e_j = sign·e_{i^j}
        assert sorted(k for k, _ in native.values()) == list(range(NUM_SLOTS))
        for i, (k, s) in native.items():
            assert k == (i ^ j) and s in (1, -1)


def test_navigate_native_equals_pure():
    r = _register()
    slots = r.slots()
    for j in range(NUM_SLOTS):
        native = sed_navigate(j, r.D, r.codebook, slots)
        with force_pure():
            pure = sed_navigate(j, r.D, r.codebook, slots)
        assert native == pure
        assert native["D"] == r.D                      # D passes through
        assert native["codebook"] == dict(r.codebook)  # codebook passes through
        # the routed slots agree with the pure class method
        assert native["slots"] == r.navigate(j)._slots


def test_navigate_empty_register_native_equals_pure():
    native = sed_navigate(1, 8192, {}, {})
    with force_pure():
        pure = sed_navigate(1, 8192, {}, {})
    assert native == pure == {"D": 8192, "codebook": {}, "slots": {}}


def test_is_navigable_native_equals_pure():
    # a single basis e_j is navigable; the all-zero direction is not
    for j in range(NUM_SLOTS):
        e = [0] * NUM_SLOTS
        e[j] = 1
        native = sed_is_navigable(e)
        with force_pure():
            pure = sed_is_navigable(e)
        assert native == pure is True
    zero = [0] * NUM_SLOTS
    native = sed_is_navigable(zero)
    with force_pure():
        pure = sed_is_navigable(zero)
    assert native == pure is False


def test_carry_native_equals_pure():
    for bits in ([1, 0, 1, 1], [0, 0, 0, 0], [1, 1, 1, 1]):
        native = sed_carry(bits)                    # Hamming(7,4) default n=3
        with force_pure():
            pure = sed_carry(bits)
        assert native == pure
        assert len(native) == 7


def test_correct_native_equals_pure():
    clean = sed_carry([1, 0, 1, 1])
    cases = [clean]
    for flip in range(len(clean)):                     # inject each single error
        bad = list(clean)
        bad[flip] ^= 1
        cases.append(bad)
    for cw in cases:
        native = sed_correct(cw)
        with force_pure():
            pure = sed_correct(cw)
        assert native == pure
        assert set(native) == {"data", "error_position", "corrected_codeword"}
        # the corrected word always recovers the clean codeword (distance-3 SEC)
        assert native["corrected_codeword"] == clean


def test_slots_native_equals_pure():
    r = _register()
    native = sed_slots(r.slots())
    with force_pure():
        pure = sed_slots(r.slots())
    assert native == pure == r.slots()
    # STR "0".."15" keys (the mval round-trip) normalise to int keys identically
    str_keyed = {str(k): v for k, v in r.slots().items()}
    native_s = sed_slots(str_keyed)
    with force_pure():
        pure_s = sed_slots(str_keyed)
    assert native_s == pure_s == r.slots()
    assert all(type(k) is int for k in native_s)


def test_slots_empty_native_equals_pure():
    assert sed_slots({}) == {}
    assert sed_slots(None) == {}


@pytest.mark.skipif(not _HAS_SED_SLOTS, reason="libsrmech predates srmech_sed_slots (rc199)")
def test_sed_slots_out_of_domain_defers_to_pure():
    """An out-of-range slot / sign is beyond the C domain → srmech_sed_slots
    returns None and the Python caller runs the un-validated pure reshape
    (inform-don't-limit), so the leaf still returns the (looser) result."""
    assert _native.sed_slots_c([99], [1]) is None          # slot out of [0,16)
    assert _native.sed_slots_c([0], [2]) is None            # sign not +-1
    # the leaf itself still normalises via the pure branch
    assert sed_slots({99: ("x", 1)}) == {99: ("x", 1)}


# ── the 2 NUM leaves: native == pure WITHIN-TOL (≤1e-9 float projection) ───────

def test_couple_working_native_within_tol_of_pure():
    for vals in ([1.0, 2.0, 3.0], [0.5, -1.5, 2.25, 3.0, -4.0, 5.0, 6.0]):
        native = sed_couple_working(vals)
        with force_pure():
            pure = sed_couple_working(vals)
        _within_tol(native, pure)


def test_uncouple_working_native_within_tol_of_pure():
    word = sed_couple_working([0.5, -1.5, 2.25, 3.0, -4.0, 5.0, 6.0])
    native = sed_uncouple_working(word)
    with force_pure():
        pure = sed_uncouple_working(word)
    _within_tol(native, pure)


def test_couple_uncouple_round_trip_recovers_streams():
    vals = [0.5, -1.5, 2.25, 3.0, -4.0, 5.0, 6.0]
    rec = sed_uncouple_working(sed_couple_working(vals))
    _within_tol(rec, vals)


# ── ledger / classification sanity (the 8 stay standalone-ready) ──────────────

def test_address_leaves_are_standalone_ready_in_ledger():
    import json
    from pathlib import Path
    rows = {
        json.loads(l)["defined_at"]: json.loads(l)
        for l in (Path(__file__).resolve().parent
                  / "rosetta_classification.ndjson").read_text(
                      encoding="utf-8").splitlines() if l.strip()
    }
    base = "srmech.cascade.sedenion_register."
    for leaf in ("sed_navmap", "sed_navigate", "sed_is_navigable", "sed_carry",
                 "sed_correct", "sed_couple_working", "sed_uncouple_working"):
        assert rows[base + leaf]["bucket"] == "composition_of_c"
    # sed_slots is a pure accessor that composes the srmech_sed_slots C peer
    assert rows[base + "sed_slots"]["bucket"] == "non_compute"
    assert rows[base + "sed_slots"]["non_compute_kind"] == "composes_c"
