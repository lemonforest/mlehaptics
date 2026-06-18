"""Path A MLSE — maximum-likelihood sequence estimator (channel equaliser variant).

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only.

Identity per the implementation plan §1: MLSE shares the Class L (trellis-
graph Laplacian) ∘ Class K (argmax) composition with Viterbi; the
distinction is the trellis-state space — for MLSE the state is the channel
memory rather than the convolutional-code state. Same algorithmic primitive,
different substrate interpretation.

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

from typing import List

from srmech.amsc import rational as _srn

from .viterbi import op as viterbi_op

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
    n_states = A ** memory if memory > 0 else 1
    T = len(obs)

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

    # General case: state = (s_{t-1}, ..., s_{t-memory}). Index by integer.
    def state_to_tuple(s: int) -> list:
        out = []
        x = s
        for _ in range(memory):
            out.append(x % A)
            x //= A
        return out

    def tuple_to_state(t: list) -> int:
        s = 0
        for i in range(memory - 1, -1, -1):
            s = s * A + t[i]
        return s

    # Build state transition matrix in log-prob (with -inf for invalid).
    # Transition (prev_state, input) -> next_state where the input becomes
    # the most-recent memory entry and the oldest is dropped.
    log_neg_inf = -1e18
    log_A = _srn.log(float(A))  # Class-N log cascade (not libm)

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
        expected = sum(taps[k + 1] * alpha[s_tup[k]] for k in range(memory))
        expected += taps[0] * alpha[s_tup[0]]
        for t in range(T):
            e = obs[t] - expected
            # |z|² = real²+imag² (no abs())
            B_log[s][t] = -(e.real * e.real + e.imag * e.imag)

    # Initial state log-prob: uniform.
    pi_log = [-_srn.log(float(n_states))] * n_states

    # Use viterbi with observations as time indices [0..T-1] and an emission
    # matrix indexed by [state][t]. viterbi expects B[state][obs_symbol]; we
    # treat obs_symbol == t. viterbi.op is numpy-free and returns a list.
    obs_indices = list(range(T))
    path = viterbi_op(obs_indices, A_log, B_log, pi_log, D=D)
    # Path is the state sequence; recover input sequence via state_tup[0].
    return [state_to_tuple(int(path[t]))[0] for t in range(T)]
