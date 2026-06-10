"""rc58 — numpy-free convolution / correlation cascade for the DSP layer.

``srmech.signal_processing._dsp_cascades.{convolve,correlate}`` replace the
``np.convolve`` / ``np.correlate`` callsites in the fir / multirate / polyphase
/ matched_filter ops.  They are the substrate-native cascade (Class I cyclic
shift ∘ Class M scaled accumulate); NumPy is a carrier only.

These tests pin value-fidelity to NumPy across every length relationship, edge
mode (``full`` / ``same`` / ``valid``) and dtype (real / complex / integer),
plus the routed-op round trips and the ratchet bookkeeping.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.signal_processing import _dsp_cascades as dsp

# (len_a, len_b) pairs exercising na>nb, na<nb, na==nb, and the singleton edges.
_LENGTHS = [
    (7, 3), (3, 7), (5, 5), (8, 1), (1, 8), (10, 4), (4, 10),
    (6, 6), (2, 9), (9, 2), (11, 5), (5, 11), (1, 1), (3, 1), (1, 3),
]
_MODES = ["full", "same", "valid"]


def _make(n, kind, seed):
    rng = np.random.default_rng(seed)
    if kind == "int":
        return rng.integers(-5, 6, n)
    real = rng.standard_normal(n)
    if kind == "complex":
        return real + 1j * rng.standard_normal(n)
    return real


@pytest.mark.parametrize("na,nb", _LENGTHS)
@pytest.mark.parametrize("kind", ["real", "complex", "int"])
@pytest.mark.parametrize("mode", _MODES)
def test_convolve_matches_numpy(na, nb, kind, mode):
    a = _make(na, kind, seed=na * 100 + nb)
    b = _make(nb, kind, seed=nb * 100 + na + 1)
    got = dsp.convolve(a, b, mode)
    ref = np.convolve(a, b, mode)
    assert got.shape == ref.shape
    assert np.allclose(got, ref, atol=1e-12)


@pytest.mark.parametrize("na,nb", _LENGTHS)
@pytest.mark.parametrize("kind", ["real", "complex", "int"])
@pytest.mark.parametrize("mode", _MODES)
def test_correlate_matches_numpy(na, nb, kind, mode):
    a = _make(na, kind, seed=na * 200 + nb)
    v = _make(nb, kind, seed=nb * 200 + na + 1)
    got = dsp.correlate(a, v, mode)
    ref = np.correlate(a, v, mode)
    assert got.shape == ref.shape
    assert np.allclose(got, ref, atol=1e-12)


def test_correlate_conjugates_v():
    # NumPy correlate conjugates the second arg; verify on a complex template.
    a = np.array([1 + 1j, 2 - 1j, 0 + 3j])
    v = np.array([1j, 2 + 0j])
    assert np.allclose(dsp.correlate(a, v, "full"), np.correlate(a, v, "full"))


def test_convolve_dtype_preserved_for_integers():
    a = np.array([1, 2, 3], dtype=np.int64)
    b = np.array([1, 1], dtype=np.int64)
    out = dsp.convolve(a, b, "full")
    assert np.issubdtype(out.dtype, np.integer)
    assert list(out) == list(np.convolve(a, b, "full"))


def test_empty_input_rejected():
    with pytest.raises(ValueError):
        dsp.convolve(np.array([]), np.array([1.0]), "full")


def test_bad_mode_rejected():
    with pytest.raises(ValueError):
        dsp.convolve(np.array([1.0, 2.0]), np.array([1.0]), "wraparound")
    with pytest.raises(ValueError):
        dsp.correlate(np.array([1.0, 2.0]), np.array([1.0]), "wraparound")


def test_non_1d_rejected():
    m = np.ones((2, 2))
    with pytest.raises(ValueError):
        dsp.convolve(m, np.array([1.0]), "full")
    with pytest.raises(ValueError):
        dsp.correlate(m, np.array([1.0]), "valid")


def test_routed_fir_matches_numpy():
    from srmech.signal_processing.closed_form_ops import fir
    sig = _make(50, "real", seed=7)
    taps = _make(9, "real", seed=8)
    for mode in _MODES:
        out = fir.op(sig, taps, mode=mode)
        assert np.allclose(out, np.convolve(sig, taps, mode), atol=1e-12)


def test_routed_matched_filter_paths_match_numpy_and_each_other():
    from srmech.signal_processing.closed_form_ops import matched_filter as mf_a
    from srmech.signal_processing.path_b_ops import matched_filter as mf_b
    sig = _make(40, "real", seed=11)
    tmpl = _make(7, "real", seed=12)
    ref = np.correlate(sig, tmpl, "valid")
    out_a = mf_a.op(sig, tmpl, mode="valid")
    out_b = mf_b.op(sig, tmpl, mode="valid")
    assert np.allclose(out_a, ref, atol=1e-12)
    assert np.allclose(out_b, ref, atol=1e-12)
    assert np.allclose(out_a, out_b, atol=1e-12)


def test_helper_is_carrier_only_no_math_tokens():
    # The cascade must not reintroduce a counted matmul/ufunc token in its
    # source body (docstrings excluded — the ratchet counts those too, so we
    # assert the module contributes zero matmul matches package-wide).
    import re
    import pathlib
    src = pathlib.Path(dsp.__file__).read_text(encoding="utf-8")
    matmul = [
        re.compile(r" @[ =]"),
        re.compile(
            r"\b(?:np|numpy)\.(?:matmul|einsum|kron|convolve|correlate|outer"
            r"|tensordot|vdot|inner|cross)\b"
        ),
        re.compile(r"\.dot\("),
    ]
    assert sum(len(p.findall(src)) for p in matmul) == 0
