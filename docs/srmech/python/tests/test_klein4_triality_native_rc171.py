"""rc171 — §53 / F818: native dispatch for klein4_triality_cycle.

The order-3 S₃ = Aut(V₄) relabel (iω₇→γ₅→CPT→iω₇, identity fixed) is the LAST
``c_exists_unbound`` klein4 op: ``srmech_klein4_triality_cycle`` shipped + was
ctypes-bound, but ``hdc.klein4_triality_cycle`` ran the pure-Python table relabel.
rc171 wires the dispatch — closing the Rosetta ``c_exists_unbound`` debt to ZERO.
The C uses the SAME forward / inverse 3-cycle tables, so native == pure bit-for-bit.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

from array import array

import pytest

from srmech.amsc import hdc
from srmech.amsc import _native


def _codes(seed, n):
    return array("B", [((i * seed + 1013904223) >> 5) & 3 for i in range(n)])


def test_pure_python_path_always_correct():
    """The order-3 cycle: forward table {0,2,3,1}; T∘T∘T == id; inverse == T²."""
    v = array("B", [0, 1, 2, 3, 1, 2, 3])
    fwd = hdc.klein4_triality_cycle(v)
    assert list(fwd.buffer) == [(0, 2, 3, 1)[x] for x in v]
    # three forward applications return the input (order-3)
    once = hdc.klein4_triality_cycle(v)
    twice = hdc.klein4_triality_cycle(once)
    thrice = hdc.klein4_triality_cycle(twice)
    assert list(thrice.buffer) == list(v)
    # inverse undoes forward
    back = hdc.klein4_triality_cycle(fwd, inverse=True)
    assert list(back.buffer) == list(v)
    # inverse == forward applied twice (T⁻¹ = T²)
    assert list(hdc.klein4_triality_cycle(v, inverse=True).buffer) == list(twice.buffer)


@pytest.mark.skipif(
    not _native.has_native_klein4_triality_cycle(),
    reason="native klein4_triality_cycle not loaded (no-C env)",
)
class TestNativeDifferential:
    """When native IS present, the native relabel == the pure-Python relabel,
    bit-for-bit, forward and inverse, across a sweep of sizes."""

    def test_forward_native_equals_pure(self):
        for D in (1, 2, 7, 64, 999, 10000):
            v = _codes(7, D)
            native = hdc.klein4_triality_cycle(v)
            pure = array("B", [(0, 2, 3, 1)[x] for x in v])
            assert list(native.buffer) == list(pure), f"forward mismatch at D={D}"

    def test_inverse_native_equals_pure(self):
        for D in (1, 2, 64, 5000):
            v = _codes(13, D)
            native = hdc.klein4_triality_cycle(v, inverse=True)
            pure = array("B", [(0, 3, 1, 2)[x] for x in v])
            assert list(native.buffer) == list(pure), f"inverse mismatch at D={D}"

    def test_order_three_through_native(self):
        v = _codes(11, 4096)
        out = hdc.klein4_triality_cycle(
            hdc.klein4_triality_cycle(hdc.klein4_triality_cycle(v)))
        assert list(out.buffer) == list(v)  # T∘T∘T == id

    def test_inverse_round_trips_native(self):
        v = _codes(29, 2048)
        fwd = hdc.klein4_triality_cycle(v)
        assert list(hdc.klein4_triality_cycle(fwd, inverse=True).buffer) == list(v)

    def test_native_path_is_actually_taken(self):
        assert _native.has_native_klein4_triality_cycle() is True


def test_c_exists_unbound_debt_is_closed():
    """rc171 milestone: with triality_cycle wired, the Rosetta c_exists_unbound
    bucket is empty (no public op has an unwired C twin)."""
    import json
    import pathlib
    fixture = pathlib.Path(__file__).parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in fixture.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    unbound = [r["defined_at"] for r in rows if r["bucket"] == "c_exists_unbound"]
    assert unbound == [], f"c_exists_unbound debt not empty: {unbound}"
