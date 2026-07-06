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

import ctypes

from srmech.amsc import _native

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


def _viterbi_native(obs, A, B, pi, T, n_states):
    """Native log-domain trellis DP → integer state list (byte-identical to the
    pure DP — the float adds accumulate in the SAME order and the per-merge
    argmax is the first-maximal Class-K pin-slot) or ``None`` (rc144 §B6b). The
    ``obs`` are validated in-range so the C never reads B out of bounds (the
    pure path would IndexError on the same input, so returning ``None`` keeps
    the behaviour identical)."""
    if not _native.has_native_viterbi() or T == 0 or n_states == 0:
        return None
    n_obs = len(B[0])
    if n_obs == 0 or any(len(row) != n_obs for row in B):
        return None
    for x in obs:
        if x < 0 or x >= n_obs:
            return None
    flat_a = [A[i][j] for i in range(n_states) for j in range(n_states)]
    flat_b = [B[s][c] for s in range(n_states) for c in range(n_obs)]
    c_a = (ctypes.c_double * (n_states * n_states))(*flat_a)
    c_b = (ctypes.c_double * (n_states * n_obs))(*flat_b)
    c_pi = (ctypes.c_double * n_states)(*pi)
    c_obs = (ctypes.c_int32 * T)(*obs)
    delta = (ctypes.c_double * (T * n_states))()
    psi = (ctypes.c_int32 * (T * n_states))()
    path = (ctypes.c_int32 * T)()
    rc = _native.LIB.srmech_viterbi(
        c_obs, ctypes.c_uint32(T), c_a, c_b, c_pi, ctypes.c_uint32(n_states),
        ctypes.c_uint32(n_obs), delta, psi, path)
    if rc != _native.SRMECH_OK:
        return None
    return [int(path[t]) for t in range(T)]


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
    list
        Integer state sequence of length ``T`` (numpy-free, #564).
    """
    # numpy-free list carriers (#564): the trellis tables are list-of-lists, the
    # branch metrics are explicit Class-M multiply-adds, and the per-merge
    # argmax is the Class-K pin-slot expressed as Python max() over the score
    # range (first-maximal tie-break, matching np.argmax).
    obs = [int(x) for x in observations]
    A = [[float(v) for v in row] for row in transition_log_prob]
    B = [[float(v) for v in row] for row in emission_log_prob]
    pi = [float(v) for v in initial_log_prob]
    T = len(obs)
    n_states = len(A)
    if len(A) != n_states or any(len(row) != n_states for row in A):
        raise ValueError("transition matrix must be square")
    if len(B) != n_states:
        raise ValueError(f"emission rows {len(B)} != n_states {n_states}")
    if len(pi) != n_states:
        raise ValueError(f"initial pi length {len(pi)} != n_states {n_states}")

    native = _viterbi_native(obs, A, B, pi, T, n_states)   # rc144 §B6b
    if native is not None:
        return native

    neg_inf = float("-inf")
    # Class L: trellis DP forward sweep over (time, state).
    delta = [[neg_inf] * n_states for _ in range(T)]
    psi = [[0] * n_states for _ in range(T)]
    for s in range(n_states):
        delta[0][s] = pi[s] + B[s][obs[0]]
    for t in range(1, T):
        # For each next-state s, find argmax over prev-state s' of
        # delta[t-1, s'] + A[s', s] + B[s, obs[t]]
        for s in range(n_states):
            scores = [delta[t - 1][i] + A[i][s] for i in range(n_states)]
            best = max(range(n_states), key=lambda i: scores[i])
            psi[t][s] = best
            delta[t][s] = scores[best] + B[s][obs[t]]

    # Class K: backtrace via argmax at terminal step.
    path = [0] * T
    path[T - 1] = max(range(n_states), key=lambda i: delta[T - 1][i])
    for t in range(T - 2, -1, -1):
        path[t] = psi[t + 1][path[t + 1]]
    return path
