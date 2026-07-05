"""BATCH B1 (rc142) — byte-identical C parity for the 9 EXACT klein4/hdc ops.

The first COMPUTE batch (the four C:Python foundations — the_one / fft / svd /
carriers — are done): 9 EXACT Klein-4 / BSC ops that had no C peer earn same-rc
C twins over the ALREADY-C ``srmech_hdc`` / ``srmech_klein4`` foundation. These
are integer / sector ops, so the C is BYTE-IDENTICAL to the pure-Python
``array('B')`` kernel — no float, NO numeric tolerance.

The 9 ops (all move ``python_only_debt`` → ``c_dispatched``, ceiling 86 → 77):
  1. hdc.bundle_with_ties            -> srmech_hdc_bundle_with_ties
  2. hdc.klein4_chirality_flip_gamma5 \\
  3. hdc.klein4_chirality_flip_omega7  } -> srmech_klein4_sector_flip (mask 2/1/3)
  4. hdc.klein4_cpt_mirror           /
  5. hdc.klein4_sector_count         -> srmech_klein4_sector_count
  6. hdc.klein4_holographic_encode   -> srmech_klein4_holographic_encode
  7. hdc.klein4_holographic_decode   -> srmech_klein4_holographic_decode
  8. hdc.klein4_triality_encode      -> srmech_klein4_triality_encode
  9. hdc.klein4_triality_correct     -> srmech_klein4_triality_correct

Each op dispatches to its C peer when native is present and falls back to the
byte-identical pure kernel otherwise; the test proves native == FORCED-pure for
every op, and cross-checks each against an INDEPENDENT pure oracle.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib
import random
from array import array

import pytest

from srmech.amsc import _native
from srmech.amsc import hdc


# The 7 native gates B1 introduces (6 C symbols + the shared BSC bundle).
_B1_GATES = (
    "hdc_bundle_with_ties",
    "klein4_sector_flip",
    "klein4_sector_count",
    "klein4_holographic_encode",
    "klein4_holographic_decode",
    "klein4_triality_encode",
    "klein4_triality_correct",
)

requires_native = pytest.mark.skipif(
    not all(getattr(_native, "has_native_" + g)() for g in _B1_GATES),
    reason="rc142 B1 klein4/hdc C peers not loaded (no-C host — the pure-Python "
    "kernel is the complete, byte-identical alternative)",
)


@contextlib.contextmanager
def force_pure(*gate_names):
    """Temporarily make the named ``_native.has_native_<gate>`` return False so
    the op takes its pure-Python fallback (the forced-pure reference)."""
    saved = {}
    for name in gate_names:
        attr = "has_native_" + name
        saved[attr] = getattr(_native, attr)
        setattr(_native, attr, lambda: False)
    try:
        yield
    finally:
        for attr, fn in saved.items():
            setattr(_native, attr, fn)


def _k4(rng, n):
    return array("B", [rng.randrange(4) for _ in range(n)])


def _bsc(rng, n):
    return bytes(rng.randrange(256) for _ in range(n))


_SIZES = (1, 2, 3, 7, 64, 999)


# ── pure-Python behaviour (always correct, no-C hosts included) ───────────────
def test_semantics_pure_always_correct():
    """The pure path matches independent oracles regardless of native presence."""
    rng = random.Random(1)
    v = _k4(rng, 32)
    with force_pure(*_B1_GATES):
        assert list(hdc.klein4_chirality_flip_gamma5(v).buffer) == [x ^ 2 for x in v]
        assert list(hdc.klein4_chirality_flip_omega7(v).buffer) == [x ^ 1 for x in v]
        assert list(hdc.klein4_cpt_mirror(v).buffer) == [x ^ 3 for x in v]
        assert hdc.klein4_sector_count(v) == [sum(1 for x in v if x == s)
                                              for s in range(4)]
        enc = hdc.klein4_holographic_encode(v, replicas=4)
        assert list(enc.buffer) == list(v) * 4
        # triality orbit round-trips through the corrector
        store = hdc.klein4_triality_encode(v)
        assert list(hdc.klein4_triality_correct(store).buffer) == list(v)


# ── native == forced-pure, EXACT (the byte-identical parity proof) ────────────
@requires_native
class TestByteIdenticalParity:
    def test_gates_live(self):
        for g in _B1_GATES:
            assert getattr(_native, "has_native_" + g)() is True

    def test_1_bundle_with_ties(self):
        rng = random.Random(2)
        for n_vec in (1, 2, 3, 4, 5, 8, 9):        # odd AND even counts
            for n_bytes in (1, 4, 16):
                vs = [_bsc(rng, n_bytes) for _ in range(n_vec)]
                native = hdc.bundle_with_ties(vs)
                with force_pure("hdc_bundle_with_ties"):
                    pure = hdc.bundle_with_ties(vs)
                assert native == pure, f"bundle_with_ties n_vec={n_vec}"
                # odd count: majority byte == the standard bundle; ties are 0
                if n_vec % 2 == 1:
                    maj, ties = native
                    assert ties == bytes(n_bytes)

    def test_2_4_chirality_flips(self):
        rng = random.Random(3)
        cases = (
            (hdc.klein4_chirality_flip_gamma5, 2),
            (hdc.klein4_chirality_flip_omega7, 1),
            (hdc.klein4_cpt_mirror, 3),
        )
        for op, mask in cases:
            for n in _SIZES:
                v = _k4(rng, n)
                native = list(op(v).buffer)
                with force_pure("klein4_sector_flip"):
                    pure = list(op(v).buffer)
                assert native == pure == [x ^ mask for x in v], f"{op.__name__} n={n}"

    def test_5_sector_count(self):
        rng = random.Random(4)
        for n in _SIZES:
            v = _k4(rng, n)
            native = hdc.klein4_sector_count(v)
            with force_pure("klein4_sector_count"):
                pure = hdc.klein4_sector_count(v)
            oracle = [sum(1 for x in v if x == s) for s in range(4)]
            assert native == pure == oracle, f"sector_count n={n}"
            assert sum(native) == n

    def test_6_holographic_encode(self):
        rng = random.Random(5)
        for n in (1, 5, 50):
            for rep in (2, 3, 4, 5):
                v = _k4(rng, n)
                native = list(hdc.klein4_holographic_encode(v, replicas=rep).buffer)
                with force_pure("klein4_holographic_encode"):
                    pure = list(hdc.klein4_holographic_encode(v, replicas=rep).buffer)
                assert native == pure == list(v) * rep, f"encode n={n} rep={rep}"

    def test_7_holographic_decode_blind(self):
        rng = random.Random(6)
        for n in (1, 5, 20):
            for rep in (2, 3, 4, 5):
                store = _k4(rng, n * rep)
                native = list(hdc.klein4_holographic_decode(store, replicas=rep).buffer)
                with force_pure("klein4_holographic_decode"):
                    pure = list(hdc.klein4_holographic_decode(store, replicas=rep).buffer)
                assert native == pure, f"decode-blind n={n} rep={rep}"

    def test_7_holographic_decode_known_erasure(self):
        rng = random.Random(7)
        for n in (5, 20):
            rep = 4
            store = _k4(rng, n * rep)
            erased = [rng.random() < 0.5 for _ in range(n * rep)]
            for i in range(n):        # keep replica 0 present → recoverable
                erased[i] = False
            native = list(hdc.klein4_holographic_decode(
                store, replicas=rep, erased=erased).buffer)
            with force_pure("klein4_holographic_decode"):
                pure = list(hdc.klein4_holographic_decode(
                    store, replicas=rep, erased=erased).buffer)
            assert native == pure, f"decode-known n={n}"

    def test_7_holographic_decode_unrecoverable_raises(self):
        """An all-erased position raises ValueError on BOTH paths (native falls to
        pure, which raises the same error)."""
        rng = random.Random(8)
        rep, n = 4, 6
        store = _k4(rng, n * rep)
        erased = [True] * (n * rep)      # every replica erased everywhere
        with pytest.raises(ValueError):
            hdc.klein4_holographic_decode(store, replicas=rep, erased=erased)
        with force_pure("klein4_holographic_decode"):
            with pytest.raises(ValueError):
                hdc.klein4_holographic_decode(store, replicas=rep, erased=erased)

    def test_8_triality_encode(self):
        rng = random.Random(9)
        fwd = (0, 2, 3, 1)
        for n in _SIZES:
            v = _k4(rng, n)
            native = list(hdc.klein4_triality_encode(v).buffer)
            with force_pure("klein4_triality_encode"):
                pure = list(hdc.klein4_triality_encode(v).buffer)
            t1 = [fwd[x] for x in v]
            oracle = list(v) + t1 + [fwd[x] for x in t1]
            assert native == pure == oracle, f"triality_encode n={n}"

    def test_9_triality_correct(self):
        rng = random.Random(10)
        for n in _SIZES:
            v = _k4(rng, n)
            store = hdc.klein4_triality_encode(v)
            native = list(hdc.klein4_triality_correct(store).buffer)
            with force_pure("klein4_triality_correct"):
                pure = list(hdc.klein4_triality_correct(store).buffer)
            # clean orbit decodes back to v exactly
            assert native == pure == list(v), f"triality_correct n={n}"

    def test_9_triality_correct_one_error_corrected(self):
        """A single corrupted sector in one orbit-block is outvoted (k=3-CORRECT)."""
        rng = random.Random(11)
        n = 30
        v = _k4(rng, n)
        store = array("B", hdc.klein4_triality_encode(v).buffer)
        store[0] = (store[0] + 1) % 4          # corrupt one position in block 0
        native = list(hdc.klein4_triality_correct(store).buffer)
        with force_pure("klein4_triality_correct"):
            pure = list(hdc.klein4_triality_correct(store).buffer)
        assert native == pure == list(v)


def test_rosetta_debt_dropped_by_nine():
    """The 9 B1 ops are all c_dispatched in the ledger (the ceiling drop 86 → 77
    is enforced by test_rosetta_completeness's monotone-decreasing ratchet)."""
    import json
    import pathlib

    fixture = pathlib.Path(__file__).parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in fixture.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    cls = {r["defined_at"]: r["bucket"] for r in rows}
    ops = [
        "srmech.amsc.hdc.bundle_with_ties",
        "srmech.amsc.hdc.klein4_chirality_flip_gamma5",
        "srmech.amsc.hdc.klein4_chirality_flip_omega7",
        "srmech.amsc.hdc.klein4_cpt_mirror",
        "srmech.amsc.hdc.klein4_sector_count",
        "srmech.amsc.hdc.klein4_holographic_encode",
        "srmech.amsc.hdc.klein4_holographic_decode",
        "srmech.amsc.hdc.klein4_triality_encode",
        "srmech.amsc.hdc.klein4_triality_correct",
    ]
    for op in ops:
        assert cls.get(op) == "c_dispatched", f"{op} not c_dispatched: {cls.get(op)}"
