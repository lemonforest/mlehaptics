"""Path A Viterbi decoder — closed-form trellis ML sequence detection.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational civilian-comms textbook reference only.

Identity per the implementation plan §1: Viterbi IS a Class L (trellis-graph
Laplacian: nodes are (time, state) pairs, edges are state transitions
weighted by branch metrics) ∘ Class K (argmax / pin-slot projection picking
the surviving path at each merge) composition.

The closed-form reference implements the canonical dynamic-programming
trellis search.

Path B dual in Phase 6 (Path B trellis as bundle of state hypotheses).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Viterbi
(1967) + Forney (1973).
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "viterbi"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-trellis-amortise"
SSOT_CITATION = (
    "Viterbi (1967), 'Error bounds for convolutional codes and an "
    "asymptotically optimum decoding algorithm', IEEE Trans. Inf. Theory "
    "13(2), 260-269. DOI 10.1109/TIT.1967.1054010 (Crossref). Forney "
    "(1973), 'The Viterbi algorithm', Proc. IEEE 61(3), 268-278. DOI "
    "10.1109/PROC.1973.9030."
)


def op(
    observations,
    transition_log_prob,
    emission_log_prob,
    initial_log_prob,
    *,
    D: int = 8192,
):
    """Most-likely state sequence given observations, in log-probability domain.

    Parameters
    ----------
    observations:
        Sequence of observation indices, length ``T``.
    transition_log_prob:
        ``(n_states, n_states)`` log P(next_state | curr_state) matrix.
    emission_log_prob:
        ``(n_states, n_obs_symbols)`` log P(obs | state) matrix.
    initial_log_prob:
        ``(n_states,)`` log P(initial state).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Integer state sequence of length ``T``.
    """
    obs = np.asarray(observations, dtype=np.int64)
    A = np.asarray(transition_log_prob, dtype=np.float64)
    B = np.asarray(emission_log_prob, dtype=np.float64)
    pi = np.asarray(initial_log_prob, dtype=np.float64)
    T = obs.shape[0]
    n_states = A.shape[0]
    if A.shape != (n_states, n_states):
        raise ValueError(f"transition matrix must be square; got {A.shape}")
    if B.shape[0] != n_states:
        raise ValueError(
            f"emission rows {B.shape[0]} != n_states {n_states}"
        )
    if pi.shape[0] != n_states:
        raise ValueError(f"initial pi length {pi.shape[0]} != n_states {n_states}")

    # Class L: trellis DP forward sweep over (time, state).
    delta = np.full((T, n_states), -np.inf, dtype=np.float64)
    psi = np.zeros((T, n_states), dtype=np.int64)
    delta[0] = pi + B[:, obs[0]]
    for t in range(1, T):
        # For each next-state s, find argmax over prev-state s' of
        # delta[t-1, s'] + A[s', s] + B[s, obs[t]]
        for s in range(n_states):
            scores = delta[t - 1] + A[:, s]
            best = int(np.argmax(scores))
            psi[t, s] = best
            delta[t, s] = scores[best] + B[s, obs[t]]

    # Class K: backtrace via argmax at terminal step.
    path = np.zeros(T, dtype=np.int64)
    path[-1] = int(np.argmax(delta[-1]))
    for t in range(T - 2, -1, -1):
        path[t] = psi[t + 1, path[t + 1]]
    return path
