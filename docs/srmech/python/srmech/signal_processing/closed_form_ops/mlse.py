"""Path A MLSE — maximum-likelihood sequence estimator (channel equaliser variant).

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only.

Identity per the implementation plan §1: MLSE shares the Class L (trellis-
graph Laplacian) ∘ Class K (argmax) composition with Viterbi; the
distinction is the trellis-state space — for MLSE the state is the channel
memory rather than the convolutional-code state. Same algorithmic primitive,
different substrate interpretation.

⚠️ THE STATE IS THE WHOLE TAP WINDOW, WHICH IS THE THING rc424 GOT WRONG
(corrected rc425, `#T1112`). ``y_t = Σ_k taps[k]·s_{t−k}`` depends on all
``L`` symbols, and :func:`viterbi.op` takes a STATE-emission matrix, so every
symbol the emission reads has to be IN the state — the trellis therefore
carries ``s_t … s_{t−L+1}`` and has ``A**L`` states, not ``A**(L−1)``.
Through rc424 it held one symbol too few and the emission compensated by
applying ``taps[0]`` and ``taps[1]`` to the same entry, which decodes a
DIFFERENT channel (``[h0+h1, h2, …]`` with the memory shifted a step). That
was a silent wrong answer: measured against an exhaustive maximum-likelihood
search over the same observations it disagreed on 4 of 9 test channels,
returning a sequence of cost 13.0 where the transmitted one scored exactly
0.0 — and it agreed on every cursor-dominant channel, i.e. exactly the regime
where a plain slicer is also right, so the error hid wherever this op was not
earning its keep. Gated now by
``tests/test_signal_processing_path_a_baseline.py::
test_mlse_agrees_with_exhaustive_maximum_likelihood_rc425``.

Carrier-removal #564 (rc107): numpy-FREE — the trellis tables (transition /
emission / initial log-probs) are pure-Python list-of-lists built with the
Class-N ``rational.log`` cascade, the per-branch metric is an explicit
``|obs − expected|²`` multiply-add (squared distance, monotone in ``|·|`` so
no ``sqrt`` and no ``abs()``), and the trellis search itself is the already-
numpy-free :func:`viterbi.op` (which returns a plain ``list``). The no-ISI
fast path is a per-sample squared-distance argmin. No top-level
``import numpy``.

Path B dual in Phase 6 (same family as Viterbi).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Forney
(1972) MLSE channel-equaliser foundational paper.
"""

from __future__ import annotations

import ctypes
from typing import List

from srmech import _native
from srmech.math import rational as _srn

from .viterbi import op as viterbi_op

# Guard: only dispatch the trellis to C when its dense scratch is a sane size
# (n_states = A^memory can blow up); beyond this the pure trellis DP runs.
_MLSE_NATIVE_STATE_CAP = 65536

OPERATION_NAME = "mlse"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-trellis-amortise"
SSOT_CITATION = (
    "Forney (1972), 'Maximum-likelihood sequence estimation of digital "
    "sequences in the presence of intersymbol interference', IEEE Trans. "
    "Inf. Theory 18(3), 363-378. DOI 10.1109/TIT.1972.1054829 (Crossref)."
)


def _as_complex_list(v) -> List[complex]:
    """Coerce an array-like to a plain Python ``list[complex]`` (numpy-free)."""
    seq = v.tolist() if hasattr(v, "tolist") else list(v)
    return [complex(x) for x in seq]


def _mlse_native(obs, taps, alpha, T, A, memory, n_states):
    """Native MLSE → integer input-symbol index list (byte-identical to the
    pure trellis DP) or ``None`` (rc144 §B6b). The Class-N rational-log trellis
    CONSTANTS are computed here in Python (exactly as the pure kernel does) and
    passed to C as doubles, so every float value in the trellis — and thus the
    Viterbi path — is bit-identical. Complex arithmetic in C reproduces Python's
    ``complex.__mul__``. Guards the dense-scratch size (falls back to pure)."""
    if not _native.has_native_mlse() or T == 0 or A == 0:
        return None
    if n_states == 0 or n_states > _MLSE_NATIVE_STATE_CAP:
        return None
    # log CONSTANTS — only meaningful for the ISI trellis (memory > 0); the
    # no-ISI path ignores them. Computed with the SAME rational.log cascade.
    if memory > 0:
        log_a = float(_srn.log(float(A)))
        log_ns = float(_srn.log(float(n_states)))
    else:
        log_a = 0.0
        log_ns = 0.0
    obs_re = (ctypes.c_double * T)(*[x.real for x in obs])
    obs_im = (ctypes.c_double * T)(*[x.imag for x in obs])
    L = len(taps)
    taps_re = (ctypes.c_double * L)(*[x.real for x in taps])
    taps_im = (ctypes.c_double * L)(*[x.imag for x in taps])
    alpha_re = (ctypes.c_double * A)(*[x.real for x in alpha])
    alpha_im = (ctypes.c_double * A)(*[x.imag for x in alpha])
    dn = n_states * n_states + 2 * n_states * T + n_states
    dscratch = (ctypes.c_double * dn)()
    iscratch = (ctypes.c_int32 * (T * n_states + T))()
    # rc425 (`#T1112`): the trellis state is the FULL tap window (L symbols),
    # not L - 1, so the two shift-register tuples are L wide apiece.
    uscratch = (ctypes.c_uint32 * max(1, 2 * L))()
    out_path = (ctypes.c_int32 * T)()
    rc = _native.LIB.srmech_mlse(
        obs_re, obs_im, ctypes.c_uint32(T), taps_re, taps_im,
        ctypes.c_uint32(L), alpha_re, alpha_im, ctypes.c_uint32(A),
        ctypes.c_uint32(n_states), ctypes.c_double(log_a), ctypes.c_double(log_ns),
        dscratch, iscratch, uscratch, out_path)
    if rc != _native.SRMECH_OK:
        return None
    return [int(out_path[t]) for t in range(T)]


def op(
    observations,
    channel_taps,
    alphabet,
    *,
    initial_state=None,
    D: int = 8192,
):
    """MLSE over a finite-state intersymbol-interference channel.

    Builds an explicit trellis from ``channel_taps`` and ``alphabet`` then
    runs the Class L + K trellis search via :func:`viterbi.op`.

    Parameters
    ----------
    observations:
        1-D received-sample array-like (complex).
    channel_taps:
        Channel impulse response ``[h_0, h_1, ..., h_{L-1}]``; ``L-1`` is
        the channel memory.
    alphabet:
        Iterable of complex symbol values (e.g., BPSK ``[-1, 1]`` or 4-PSK
        ``[1, j, -1, -j]``).
    initial_state:
        Optional initial state tuple; default = all-first-symbol state.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list
        Integer symbol-index sequence (indices into ``alphabet``) of length
        ``len(observations)`` (numpy-free, #564).
    """
    taps = _as_complex_list(channel_taps)
    alpha = _as_complex_list(alphabet)
    obs = _as_complex_list(observations)
    A = len(alpha)
    memory = len(taps) - 1
    if memory < 0:
        raise ValueError("channel_taps must have length >= 1")
    # ⚠️ rc425 (`#T1112`) — THE TRELLIS STATE SPANS THE WHOLE TAP WINDOW.
    #
    # Through rc424 this read ``n_states = A ** memory`` and the emission
    # summed ``taps[k + 1] * alpha[tup[k]]`` and then ADDED
    # ``taps[0] * alpha[tup[0]]`` — applying the cursor tap h0 and the first
    # post-cursor tap h1 to the SAME symbol. The trellis therefore decoded as
    # if the channel were ``[h0 + h1, h2, ...]`` with the memory shifted one
    # step, which is a different channel.
    #
    # It was a SILENT WRONG ANSWER, not a crash: measured on noiseless BPSK
    # where the transmitted sequence has branch-metric cost EXACTLY 0.0, the
    # rc424 trellis returned a sequence costing 13.0 for taps [0.5, 1.0], and
    # disagreed with an exhaustive maximum-likelihood search on 4 of 9 test
    # channels. It agreed only where the cursor tap dominates — which is
    # precisely the regime in which a plain symbol-by-symbol slicer is also
    # right, so the error hid wherever the op was not earning its keep.
    #
    # y_t = sum_{k=0}^{L-1} taps[k] * s_{t-k} depends on L symbols, so a
    # STATE-emission Viterbi needs all L of them in the state. Holding L - 1
    # made the emission unrepresentable and the old expression was an attempt
    # to fold the missing symbol into the ones that were there.
    width = len(taps)
    n_states = A ** width if memory > 0 else 1
    T = len(obs)

    native = _mlse_native(obs, taps, alpha, T, A, memory, n_states)  # rc144 §B6b
    if native is not None:
        return native

    if memory == 0:
        # No ISI; just minimum-distance decoding. Class K pin-slot argmin over
        # the squared Euclidean distance |obs − taps[0]·alpha|² (monotone in
        # |·|, so no sqrt / no abs(); strict `<` keeps the first-minimum index,
        # matching the prior np.argmin tie-break).
        out: List[int] = []
        for t in range(T):
            best_i = 0
            best_d2 = None
            for i in range(A):
                e = obs[t] - taps[0] * alpha[i]
                d2 = e.real * e.real + e.imag * e.imag
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best_i = i
            out.append(best_i)
        return out

    # General case: state = (s_t, s_{t-1}, ..., s_{t-memory}) — WIDTH symbols,
    # the full window y_t depends on. Index by integer, tup[0] most recent.
    def state_to_tuple(s: int) -> list:
        out = []
        x = s
        for _ in range(width):
            out.append(x % A)
            x //= A
        return out

    def tuple_to_state(t: list) -> int:
        s = 0
        for i in range(width - 1, -1, -1):
            s = s * A + t[i]
        return s

    # Build state transition matrix in log-prob (with -inf for invalid).
    # Transition (prev_state, input) -> next_state where the input becomes
    # the most-recent memory entry and the oldest is dropped.
    log_neg_inf = -1e18
    log_A = float(_srn.log(float(A)))  # Class-N log cascade (not libm) → float log-prob

    # Trans matrix: A_log[prev][next] = log P(next | prev) — equally likely
    # over the A possible input symbols, but only A out of n_states are
    # reachable from any prev. (list-of-lists; numpy-free carrier)
    A_log = [[log_neg_inf] * n_states for _ in range(n_states)]
    for prev_s in range(n_states):
        prev_tup = state_to_tuple(prev_s)
        for inp in range(A):
            new_tup = [inp] + prev_tup[:-1]
            new_s = tuple_to_state(new_tup)
            A_log[prev_s][new_s] = -log_A

    # Emission matrix: B_log[state][t] = -|obs[t] - expected_signal|^2,
    # where expected_signal = sum_k taps[k] * alpha[state_tup[k]]
    # and state_tup[0] is the most recent input.
    B_log = [[0.0] * T for _ in range(n_states)]
    for s in range(n_states):
        s_tup = state_to_tuple(s)
        # y_t = sum_k taps[k] * s_{t-k}, and s_tup[k] IS s_{t-k}. One loop over
        # the whole window — the rc424 form applied taps[0] and taps[1] to the
        # same symbol and never reached s_{t-memory} at all.
        expected = sum(taps[k] * alpha[s_tup[k]] for k in range(width))
        for t in range(T):
            e = obs[t] - expected
            # |z|² = real²+imag² (no abs())
            B_log[s][t] = -(e.real * e.real + e.imag * e.imag)

    # Initial state log-prob: uniform.
    pi_log = [-float(_srn.log(float(n_states)))] * n_states

    # Use viterbi with observations as time indices [0..T-1] and an emission
    # matrix indexed by [state][t]. viterbi expects B[state][obs_symbol]; we
    # treat obs_symbol == t. viterbi.op is numpy-free and returns a list.
    obs_indices = list(range(T))
    path = viterbi_op(obs_indices, A_log, B_log, pi_log, D=D)
    # Path is the state sequence; recover input sequence via state_tup[0].
    return [state_to_tuple(int(path[t]))[0] for t in range(T)]
