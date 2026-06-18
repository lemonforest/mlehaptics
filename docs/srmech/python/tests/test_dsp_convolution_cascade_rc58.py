"""rc58 — numpy-free convolution / correlation cascade for the DSP layer.

``srmech.signal_processing._dsp_cascades.{convolve,correlate}`` replace the
``np.convolve`` / ``np.correlate`` callsites in the fir / multirate / polyphase
/ matched_filter ops.  They are the substrate-native cascade (Class I cyclic
shift ∘ Class M scaled accumulate); NumPy is no longer involved at all.

These tests pin value-fidelity to a hand-written textbook reference (the
double-loop convolution + NumPy's exact ``full`` / ``same`` / ``valid`` crop
rule, mirrored from ``_dsp_cascades``) across every length relationship, edge
mode and dtype (real / complex / integer), plus the routed-op round trips.

numpy-free: inputs are plain Python lists; the oracle is the pure-Python
``_ref_convolve`` / ``_ref_correlate`` below (NOT ``np.convolve``); equality is
an element-wise ``abs(a-b) < tol`` loop.
"""

from __future__ import annotations

import random

import pytest

from srmech.signal_processing import _dsp_cascades as dsp

# (len_a, len_b) pairs exercising na>nb, na<nb, na==nb, and the singleton edges.
_LENGTHS = [
    (7, 3), (3, 7), (5, 5), (8, 1), (1, 8), (10, 4), (4, 10),
    (6, 6), (2, 9), (9, 2), (11, 5), (5, 11), (1, 1), (3, 1), (1, 3),
]
_MODES = ["full", "same", "valid"]


# ──────────────────────────────────────────────────────────────────────
# Pure-Python reference oracle (numpy-free).
# ──────────────────────────────────────────────────────────────────────
def _conj(x):
    return x.conjugate() if isinstance(x, complex) else x


def _full_convolve(a, b):
    """Textbook double-loop convolution: full[i+j] += a[i]·b[j]."""
    a = list(a)
    b = list(b)
    na, nb = len(a), len(b)
    length = na + nb - 1
    full = [0] * length if length > 0 else []
    for i in range(na):
        for j in range(nb):
            full[i + j] += a[i] * b[j]
    return full


def _ref_convolve(a, b, mode):
    """Pure-Python ``np.convolve`` equivalent (full / same / valid)."""
    a = list(a)
    b = list(b)
    na, nb = len(a), len(b)
    full = _full_convolve(a, b)
    if mode == "full":
        return full
    if mode == "same":
        target = max(na, nb)
        start = (len(full) - target) // 2
        return full[start:start + target]
    if mode == "valid":
        target = max(na, nb) - min(na, nb) + 1
        start = min(na, nb) - 1
        return full[start:start + target]
    raise ValueError(mode)


def _ref_correlate(a, v, mode):
    """Pure-Python ``np.correlate`` equivalent — conjugate-and-reverse v,
    then convolve; NumPy's exact ``same``-mode crop (centred on the longer
    of the two, mirrored from _dsp_cascades)."""
    a = list(a)
    v = list(v)
    na, nv = len(a), len(v)
    vrc = [_conj(x) for x in v][::-1]
    full = _full_convolve(a, vrc)
    if mode == "full":
        return full
    if mode == "valid":
        target = max(na, nv) - min(na, nv) + 1
        start = min(na, nv) - 1
        return full[start:start + target]
    if mode == "same":
        target = max(na, nv)
        diff = len(full) - target
        start = diff // 2 if na >= nv else (diff + 1) // 2
        return full[start:start + target]
    raise ValueError(mode)


def _make(n, kind, seed):
    rng = random.Random(seed)
    if kind == "int":
        return [rng.randint(-5, 5) for _ in range(n)]
    real = [rng.gauss(0.0, 1.0) for _ in range(n)]
    if kind == "complex":
        return [r + 1j * rng.gauss(0.0, 1.0) for r in real]
    return real


@pytest.mark.parametrize("na,nb", _LENGTHS)
@pytest.mark.parametrize("kind", ["real", "complex", "int"])
@pytest.mark.parametrize("mode", _MODES)
def test_convolve_matches_reference(na, nb, kind, mode):
    a = _make(na, kind, seed=na * 100 + nb)
    b = _make(nb, kind, seed=nb * 100 + na + 1)
    got = dsp.convolve(a, b, mode)
    ref = _ref_convolve(a, b, mode)
    assert len(got) == len(ref)
    assert all(abs(g - r) < 1e-12 for g, r in zip(got, ref))


@pytest.mark.parametrize("na,nb", _LENGTHS)
@pytest.mark.parametrize("kind", ["real", "complex", "int"])
@pytest.mark.parametrize("mode", _MODES)
def test_correlate_matches_reference(na, nb, kind, mode):
    a = _make(na, kind, seed=na * 200 + nb)
    v = _make(nb, kind, seed=nb * 200 + na + 1)
    got = dsp.correlate(a, v, mode)
    ref = _ref_correlate(a, v, mode)
    assert len(got) == len(ref)
    assert all(abs(g - r) < 1e-12 for g, r in zip(got, ref))


def test_correlate_conjugates_v():
    # correlate conjugates the second arg; verify on a complex template.
    a = [1 + 1j, 2 - 1j, 0 + 3j]
    v = [1j, 2 + 0j]
    got = dsp.correlate(a, v, "full")
    ref = _ref_correlate(a, v, "full")
    assert all(abs(g - r) < 1e-12 for g, r in zip(got, ref))


def test_convolve_dtype_preserved_for_integers():
    a = [1, 2, 3]
    b = [1, 1]
    # numpy-free dsp.convolve preserves int-ness (int*int+int stays int).
    out = dsp.convolve(a, b, "full")
    assert all(isinstance(v, int) for v in out)
    assert out == _ref_convolve(a, b, "full")


def test_empty_input_rejected():
    with pytest.raises(ValueError):
        dsp.convolve([], [1.0], "full")


def test_bad_mode_rejected():
    with pytest.raises(ValueError):
        dsp.convolve([1.0, 2.0], [1.0], "wraparound")
    with pytest.raises(ValueError):
        dsp.correlate([1.0, 2.0], [1.0], "wraparound")


def test_non_1d_rejected():
    m = [[1.0, 1.0], [1.0, 1.0]]
    with pytest.raises(ValueError):
        dsp.convolve(m, [1.0], "full")
    with pytest.raises(ValueError):
        dsp.correlate(m, [1.0], "valid")


def test_routed_fir_matches_reference():
    from srmech.signal_processing.closed_form_ops import fir
    sig = _make(50, "real", seed=7)
    taps = _make(9, "real", seed=8)
    for mode in _MODES:
        out = fir.op(sig, taps, mode=mode)
        ref = _ref_convolve(sig, taps, mode)
        assert len(out) == len(ref)
        assert all(abs(o - r) < 1e-12 for o, r in zip(out, ref))


def test_routed_matched_filter_paths_match_reference_and_each_other():
    from srmech.signal_processing.closed_form_ops import matched_filter as mf_a
    from srmech.signal_processing.path_b_ops import matched_filter as mf_b
    sig = _make(40, "real", seed=11)
    tmpl = _make(7, "real", seed=12)
    ref = _ref_correlate(sig, tmpl, "valid")
    out_a = mf_a.op(sig, tmpl, mode="valid")
    out_b = mf_b.op(sig, tmpl, mode="valid")
    assert all(abs(o - r) < 1e-12 for o, r in zip(out_a, ref))
    assert all(abs(o - r) < 1e-12 for o, r in zip(out_b, ref))
    assert all(abs(a - b) < 1e-12 for a, b in zip(out_a, out_b))


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
