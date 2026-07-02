"""rc104 — hdc.klein4_bundle accepts HV wrappers via the bundle(Sequence) list form.

Issue #1234 Item 4 / F1005 / UPSTREAM §82. `klein4_bind` / `klein4_similarity`
already take HV wrapper objects (`type(klein4_random(...))`) directly; the natural
bundle call `klein4_bundle([hv1, hv2, …])` — mirroring the base `bundle(Sequence)`
list API — used to fail because `klein4_bundle(*vectors)` is VARARGS, so the whole
list was handed to `_as_klein4_buf` which then tried `int(hv)`. The fix accepts the
single-sequence-of-vectors call form (a lone list/tuple whose first element is a
vector container), routing each vector through the SAME `_as_klein4_buf` HV-coercion.

Discipline: additive only — every pre-existing call form must be byte-for-byte
unchanged; HV inputs must equal `.tolist()`-ed inputs byte-identically, including
under every `sectors=` / `parallel=` / `mode=` variant.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

from array import array

import pytest

from srmech.amsc import hdc


def _b(hv):
    """Raw bytes of an HV result — the byte-identity comparison key."""
    return hv.tobytes()


# The flag-variant matrix the equivalence must hold across (chunk + chirality,
# each lane count / parallel alias). All must be bit-identical on HV vs .tolist().
_FLAG_VARIANTS = (
    {},
    {"sectors": 1},
    {"sectors": 2},
    {"sectors": 4},
    {"parallel": True},
    {"parallel": False},
    {"mode": "chunk"},
    {"mode": "chirality"},
    {"sectors": 1, "mode": "chirality"},
    {"sectors": 4, "mode": "chirality"},
)


# ── the DoD ────────────────────────────────────────────────────────────────

def test_dod_list_of_random_hvs_bundles_without_tolist():
    """DoD: klein4_bundle([klein4_random(D), klein4_random(D)]) works, no .tolist()."""
    D = 128
    out = hdc.klein4_bundle([hdc.klein4_random(D, seed=1),
                             hdc.klein4_random(D, seed=2)])
    assert isinstance(out, hdc.HV)
    assert len(out) == D
    assert out.sectors == 4


# ── HV-list == varargs == tolist, byte-identical ─────────────────────────────

def _hvs(D, seeds):
    return [hdc.klein4_random(D, seed=s) for s in seeds]


def test_list_form_equals_varargs_form():
    """klein4_bundle([h1, h2, …]) is byte-identical to klein4_bundle(h1, h2, …)."""
    for seeds in ((1, 2), (1, 2, 3), (5, 6, 7, 8), (9, 10, 11, 12, 13)):
        hvs = _hvs(96, seeds)
        assert _b(hdc.klein4_bundle(hvs)) == _b(hdc.klein4_bundle(*hvs))


def test_hv_inputs_equal_tolist_inputs_all_flag_variants():
    """HV inputs == .tolist()-ed inputs, byte-identical, across every flag variant
    AND against the already-working unpacked-varargs form."""
    hvs = _hvs(120, (1, 2, 3))
    lists = [h.tolist() for h in hvs]
    for kw in _FLAG_VARIANTS:
        hv_list = _b(hdc.klein4_bundle(hvs, **kw))
        tolist_list = _b(hdc.klein4_bundle(lists, **kw))
        varargs = _b(hdc.klein4_bundle(*hvs, **kw))
        assert hv_list == tolist_list, f"HV != tolist for {kw}"
        assert hv_list == varargs, f"list-form != varargs for {kw}"


def test_mixed_list_hv_and_plain_list():
    """A mixed input list (HV + plain int-list, freely mixed) works and matches the
    all-HV / all-list bundles byte-for-byte."""
    hvs = _hvs(80, (4, 5, 6))
    lists = [h.tolist() for h in hvs]
    mixed = [hvs[0], lists[1], hvs[2]]        # HV, list, HV
    mixed2 = [lists[0], hvs[1], lists[2]]     # list, HV, list
    ref = _b(hdc.klein4_bundle(hvs))
    assert _b(hdc.klein4_bundle(mixed)) == ref
    assert _b(hdc.klein4_bundle(mixed2)) == ref
    # also under a chirality variant
    ref_c = _b(hdc.klein4_bundle(hvs, mode="chirality", sectors=4))
    assert _b(hdc.klein4_bundle(mixed, mode="chirality", sectors=4)) == ref_c


def test_single_hv_in_a_list_is_itself():
    """Bundling a single HV (in a list) returns that HV's value — parity with the
    bare single-HV varargs call."""
    h = hdc.klein4_random(64, seed=77)
    assert _b(hdc.klein4_bundle([h])) == h.tobytes()
    assert _b(hdc.klein4_bundle(h)) == h.tobytes()


def test_list_of_bytes_and_arrays_vectors():
    """The list form also accepts bytes / array('B') vector elements (mirrors the
    HV path — any vector container is a valid element)."""
    v0 = bytes([0, 1, 2, 3, 0, 1, 2, 3])
    v1 = array("B", [3, 2, 1, 0, 3, 2, 1, 0])
    out_list = hdc.klein4_bundle([v0, v1])
    out_var = hdc.klein4_bundle(v0, v1)
    assert _b(out_list) == _b(out_var)


# ── regressions: pre-existing forms byte-for-byte unchanged ──────────────────

def test_regression_single_int_vector_stays_one_vector():
    """A lone list of ints is ONE vector (its first element is a scalar int) — the
    established behaviour. Bundling one vector returns it unchanged."""
    assert hdc.klein4_bundle([0, 1, 2, 3]).tolist() == [0, 1, 2, 3]
    assert hdc.klein4_bundle([3, 3, 0, 1, 2]).tolist() == [3, 3, 0, 1, 2]


def test_regression_bare_vector_containers_unchanged():
    """Bare (unwrapped) single-vector calls in every container type stay one vector."""
    assert hdc.klein4_bundle(bytes([0, 1, 2, 3])).tolist() == [0, 1, 2, 3]
    assert hdc.klein4_bundle(array("B", [3, 2, 1, 0])).tolist() == [3, 2, 1, 0]
    h = hdc.klein4_random(32, seed=3)
    assert hdc.klein4_bundle(h).tobytes() == h.tobytes()


def test_regression_varargs_majority_unchanged():
    """Varargs of int-vectors still per-bit-majority as before."""
    out = hdc.klein4_bundle([0, 0, 1], [0, 1, 1], [1, 1, 1])
    assert out.tolist() == [0, 1, 1]


def test_regression_empty_and_error_paths():
    """Empty / no-arg / out-of-range paths raise ValueError exactly as before."""
    with pytest.raises(ValueError):
        hdc.klein4_bundle()
    with pytest.raises(ValueError):
        hdc.klein4_bundle([])
    with pytest.raises(ValueError):
        hdc.klein4_bundle([[0, 1, 4], [0, 1, 2]])   # 4 outside {0,1,2,3}
    with pytest.raises(ValueError):
        hdc.klein4_bundle([0, 1, 4])                 # single vector, out of range


def test_regression_length_mismatch_still_raises():
    """Unequal vector lengths in the list form raise the length-mismatch error."""
    with pytest.raises(ValueError):
        hdc.klein4_bundle([hdc.klein4_random(16, seed=1),
                           hdc.klein4_random(32, seed=2)])


def test_mode_validation_unchanged_on_list_form():
    """An invalid mode= still raises even via the list form."""
    with pytest.raises(ValueError):
        hdc.klein4_bundle([hdc.klein4_random(16, seed=1),
                           hdc.klein4_random(16, seed=2)], mode="bogus")
