"""rc144 Batch B6b — byte-identical parity for the 4 harder coder/DP C peers.

The 4 native symbols (jpeg deferred as float-DCT numeric, a later batch):
  1. closed_form_ops.arithmetic_coding.op -> srmech_arithmetic_encode
  2. closed_form_ops.lz77.op              -> srmech_lz77_encode
  3. closed_form_ops.viterbi.op           -> srmech_viterbi
  4. closed_form_ops.mlse.op              -> srmech_mlse

Each op is exercised native (HAS_NATIVE) vs FORCED-pure and must be
byte-identical (exact for the integer coders; deterministic-same-order
for the float trellis DP). numpy-free (per the test-for-numpy-free-module
discipline).
"""

from __future__ import annotations

import contextlib

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import arithmetic_coding as AC
from srmech.signal_processing.closed_form_ops import lz77 as LZ
from srmech.signal_processing.closed_form_ops import mlse as ML
from srmech.signal_processing.closed_form_ops import viterbi as VT

_GATES = (
    "has_native_arithmetic_encode",
    "has_native_lz77_encode",
    "has_native_viterbi",
    "has_native_mlse",
)
_HAVE = _native.HAS_NATIVE and all(
    hasattr(_native, g) and getattr(_native, g)() for g in _GATES
)

pytestmark = pytest.mark.skipif(
    not _HAVE, reason="native B6b coder/DP peers not built"
)


@contextlib.contextmanager
def _force_pure():
    saved = {g: getattr(_native, g) for g in _GATES}
    for g in _GATES:
        setattr(_native, g, lambda: False)
    try:
        yield
    finally:
        for g, fn in saved.items():
            setattr(_native, g, fn)


def _both(call):
    native = call()
    with _force_pure():
        pure = call()
    return native, pure


def test_arithmetic_coding_parity():
    # byte-identical native==pure encode (the parity DoD); several data shapes
    for data in (
        [1, 2, 1, 3, 1, 2, 1, 1, 2, 3, 3, 1, 5, 5, 2],
        [0, 0, 0, 0, 1],
        [7] * 20 + [3, 9, 3, 9],
    ):
        n, p = _both(lambda d=data: AC.op(list(d)))
        assert n == p


def test_lz77_parity_and_roundtrip():
    data = [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 4, 4, 4, 5, 6, 1, 2, 3]
    n, p = _both(lambda: LZ.op(list(data)))
    assert n == p
    enc = LZ.op(list(data))
    dec = LZ.op(enc, decode=True)
    assert list(dec) == data


def test_viterbi_parity():
    # 2-state / 2-observation HMM (log-probs)
    obs = [0, 1, 0, 1, 1, 0, 0, 1]
    transition_log_prob = [[-0.1, -2.3], [-2.3, -0.1]]
    emission_log_prob = [[-0.2, -1.6], [-1.6, -0.2]]
    initial_log_prob = [-0.7, -0.7]
    n, p = _both(
        lambda: VT.op(
            obs, transition_log_prob, emission_log_prob, initial_log_prob
        )
    )
    assert n == p


def test_mlse_parity():
    # binary alphabet over a 2-tap channel
    observations = [0.9, -1.1, 0.2, 1.0, -0.8, 0.3]
    channel_taps = [1.0, 0.4]
    alphabet = [-1, 1]
    n, p = _both(lambda: ML.op(observations, channel_taps, alphabet))
    assert n == p
