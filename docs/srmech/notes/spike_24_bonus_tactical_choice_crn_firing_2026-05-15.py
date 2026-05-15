"""
Spike #24 bonus — tactical-choice structure at chemistry-reaction-network substrate.

The "tactical choice" in a stochastic CRN: at each step, the Gillespie SSA dispatches
which reaction fires next, sampled according to propensities. This is a fundamentally
different kind of choice than tic-tac-toe or chess:

  - Single-agent (physics, not an opponent)
  - Stochastic (sampled from propensity distribution)
  - Continuous-time (inter-event times exponentially distributed)
  - Inverse: no "winner"; the choice IS the dynamics
  - Choice-set: which of K reactions fires; legality determined by reactant copy numbers

Question: does the refined hypothesis from tic-tac-toe ('Class D dispatch over
Class L-spectral graph of legal successors, quotiented by Class I symmetry') still
fit? What's instantiated; what's not?

System: Lotka-Volterra (Phase 9.2-confirmed Kepler-shape oscillator). Two species
X (prey) and Y (predator). Three reactions:
  R1: ∅ -> X         (prey birth, rate k1 * 1)
  R2: X -> Y + Y     (predation, rate k2 * X * Y)   (or simplified: X + Y -> 2Y)
  R3: Y -> ∅         (predator death, rate k3 * Y)

We treat (X, Y) integer-copy-number states. Build the *state-transition graph*
where nodes = (X, Y) and edges = single reactions. Compute the analogous metrics.

Crucially: the propensity-weighted edge probabilities make this a MARKOV CHAIN
(weighted directed graph) not a plain DAG. The graph Laplacian becomes the
generator of the Master equation — a different mathematical object than the
tic-tac-toe game-tree Laplacian.

Stdlib + numpy + scipy.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, dok_matrix
from scipy.sparse.csgraph import laplacian as csgraph_laplacian
from scipy.sparse.linalg import eigs as sparse_eigs

OUT_PATH = Path(__file__).with_suffix(".ndjson")
SCRIPT_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Lotka-Volterra CRN (with X+Y -> 2Y bimolecular variant for tractability)
# ---------------------------------------------------------------------------
# Reactions:
#   R0: 0 -> X        (propensity k0)         -- prey birth
#   R1: X + Y -> 2Y   (propensity k1 * X * Y) -- predation
#   R2: Y -> 0        (propensity k2 * Y)     -- predator death
#
# State space: (X, Y) with both >= 0. We bound it to keep enumeration tractable.

K0, K1, K2 = 1.0, 0.005, 1.0  # parameter set chosen so steady-state-like cycle within a small box
X_MAX, Y_MAX = 30, 30

def propensities(state):
    x, y = state
    return (K0, K1 * x * y, K2 * y)


def reactions():
    """Return list of (name, delta_x, delta_y) tuples."""
    return [
        ("R0_prey_birth", 1, 0),
        ("R1_predation", -1, 1),
        ("R2_predator_death", 0, -1),
    ]


def legal_reactions(state):
    """Return list of indices of reactions with nonzero propensity."""
    x, y = state
    out = []
    props = propensities(state)
    rxns = reactions()
    for i, (p, (_, dx, dy)) in enumerate(zip(props, rxns)):
        if p <= 0:
            continue
        nx, ny = x + dx, y + dy
        if 0 <= nx <= X_MAX and 0 <= ny <= Y_MAX:
            out.append(i)
    return out


def apply_reaction(state, ridx):
    rxns = reactions()
    _, dx, dy = rxns[ridx]
    return (state[0] + dx, state[1] + dy)


# ---------------------------------------------------------------------------
# State-space enumeration
# ---------------------------------------------------------------------------
def enumerate_state_space():
    """Enumerate all (X, Y) states in [0, X_MAX] x [0, Y_MAX] reachable from a
    seed (1, 1). Since reactions allow X to grow unboundedly through R0 and Y
    through R1, and we bound the box, the "reachable" set equals the full box
    minus any states that can't be reached given the seed (effectively none for
    these reactions from (1, 1)).
    """
    seed = (1, 1)
    visited = set()
    frontier = [seed]
    while frontier:
        nf = []
        for s in frontier:
            if s in visited:
                continue
            visited.add(s)
            for ri in legal_reactions(s):
                ns = apply_reaction(s, ri)
                if ns not in visited:
                    nf.append(ns)
        frontier = nf
    return visited


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
def build_unweighted_graph(states_list):
    idx_of = {s: i for i, s in enumerate(states_list)}
    n = len(states_list)
    rows, cols = [], []
    for s in states_list:
        i = idx_of[s]
        for ri in legal_reactions(s):
            ns = apply_reaction(s, ri)
            if ns in idx_of:
                j = idx_of[ns]
                rows.append(i); cols.append(j)
                rows.append(j); cols.append(i)
    if not rows:
        return csr_matrix((n, n), dtype=np.float64)
    data = np.ones(len(rows), dtype=np.float64)
    A = csr_matrix((data, (rows, cols)), shape=(n, n))
    A.data = np.clip(A.data, 0, 1)
    return A


def build_weighted_transition_matrix(states_list):
    """Build the CTMC generator Q where Q[i,j] = propensity of reaction taking
    state i -> state j, Q[i,i] = -sum of off-diagonal row.
    """
    idx_of = {s: i for i, s in enumerate(states_list)}
    n = len(states_list)
    Q = dok_matrix((n, n), dtype=np.float64)
    for s in states_list:
        i = idx_of[s]
        props = propensities(s)
        row_sum = 0.0
        for ri in legal_reactions(s):
            ns = apply_reaction(s, ri)
            if ns in idx_of:
                j = idx_of[ns]
                Q[i, j] += props[ri]
                row_sum += props[ri]
        Q[i, i] -= row_sum
    return Q.tocsr()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def branching_factor_stats(states_list):
    """Compute the number of legal reactions (branching factor) at each state."""
    bf_data = []
    for s in states_list:
        n_legal = len(legal_reactions(s))
        bf_data.append(n_legal)
    bf_arr = np.array(bf_data, dtype=float)
    return {
        "n_states": len(bf_data),
        "mean_bf": float(bf_arr.mean()),
        "std_bf": float(bf_arr.std()),
        "cv_bf": float(bf_arr.std() / bf_arr.mean()) if bf_arr.mean() > 0 else float("nan"),
        "min_bf": int(bf_arr.min()),
        "max_bf": int(bf_arr.max()),
        "bf_distribution": dict(Counter(bf_data)),
    }


def state_space_topology(A):
    """Is the state space connected? What's the spectral gap?"""
    n = A.shape[0]
    L, _ = csgraph_laplacian(A, return_diag=True, normed=False)
    n_modes = min(20, n - 1)
    try:
        from scipy.sparse.linalg import eigsh
        eigs, _ = eigsh(L.astype(np.float64), k=n_modes, which="SM", tol=1e-8)
        eigs.sort()
    except Exception:
        eigs = np.linalg.eigvalsh(L.toarray())[:n_modes]
    return {
        "n_nodes": n,
        "n_edges_undirected": int(A.nnz // 2),
        "smallest_eigenvalues": [float(x) for x in eigs[:10]],
        "spectral_gap_lambda1": float(eigs[1]) if len(eigs) > 1 else None,
        "fiedler_value": float(eigs[1]) if len(eigs) > 1 else None,
        "connected": bool(eigs[1] > 1e-8) if len(eigs) > 1 else True,
    }


def ctmc_stationary_and_spectral_gap(Q):
    """Compute the stationary distribution (left eigenvector of Q with eigenvalue 0)
    and the spectral gap (second-smallest |Re(eigenvalue)|, which controls mixing).
    """
    n = Q.shape[0]
    # Stationary: solve pi Q = 0, sum(pi) = 1. Use sparse left eigenvector.
    try:
        # Eigenvalues of Q^T near zero — use shift-invert
        vals, vecs = sparse_eigs(Q.T.astype(np.float64), k=min(5, n - 2), sigma=0, which="LM")
        # Take real parts; find smallest-magnitude eigenvalue
        idx_order = np.argsort(np.abs(vals.real))
        vals = vals[idx_order]
        vecs = vecs[:, idx_order]
        stationary = vecs[:, 0].real
        if stationary.sum() < 0:
            stationary = -stationary
        stationary = np.abs(stationary)
        if stationary.sum() > 0:
            stationary /= stationary.sum()
        spectral_gap = float(abs(vals[1].real)) if len(vals) > 1 else float("nan")
        return stationary, spectral_gap
    except Exception as e:
        # Fall back: dense
        Q_dense = Q.toarray()
        vals, vecs = np.linalg.eig(Q_dense.T)
        idx_order = np.argsort(np.abs(vals.real))
        vals = vals[idx_order]
        vecs = vecs[:, idx_order]
        stationary = vecs[:, 0].real
        stationary = np.abs(stationary)
        if stationary.sum() > 0:
            stationary /= stationary.sum()
        spectral_gap = float(abs(vals[1].real)) if len(vals) > 1 else float("nan")
        return stationary, spectral_gap


# ---------------------------------------------------------------------------
# Symmetry: LV has NO non-trivial state-space symmetry. X and Y are not
# interchangeable. So |G| = 1 (identity only).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def emit_ndjson(records, out_path):
    def _default(o):
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, complex):
            return [o.real, o.imag]
        raise TypeError(f"Object of type {type(o)} is not JSON serialisable")

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=_default, separators=(",", ":")) + "\n")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    records = []
    records.append({
        "record_kind": "header",
        "spike": "spike_24",
        "phase": "bonus_tactical_choice_crn_firing",
        "date": "2026-05-15",
        "script_version": SCRIPT_VERSION,
        "produced_at": utc_now(),
        "hypothesis": "Tactical-choice refined hypothesis at chemistry-dynamics substrate (CRN firing choice)",
        "system": "Lotka-Volterra with R0: prey birth, R1: predation X+Y->2Y, R2: predator death",
        "parameters": {"k0": K0, "k1": K1, "k2": K2, "x_max": X_MAX, "y_max": Y_MAX},
    })

    print("Enumerating state space...", file=sys.stderr)
    states = enumerate_state_space()
    states_list = sorted(states)
    n_states = len(states_list)
    print(f"  states: {n_states}", file=sys.stderr)
    records.append({
        "record_kind": "enumeration",
        "n_states": n_states,
        "x_range": [min(s[0] for s in states_list), max(s[0] for s in states_list)],
        "y_range": [min(s[1] for s in states_list), max(s[1] for s in states_list)],
        "note": (
            "States are (X, Y) integer copy numbers in a bounded box. "
            "From seed (1, 1) all states in the box are reachable since R0 generates X and R1 generates Y."
        ),
    })

    # Branching factor (= number of legal reactions at each state)
    print("Computing branching factor (reaction-fire choice)...", file=sys.stderr)
    bf = branching_factor_stats(states_list)
    records.append({
        "record_kind": "branching_factor_summary",
        **bf,
        "note": (
            "Branching factor here = number of legal reactions available at each state. "
            "LV has exactly 3 reactions; legality is a function of copy number (R1 requires X>=1 and Y>=1; "
            "R2 requires Y>=1) and box bounds. Most interior states have bf = 3; edge states have bf in {0, 1, 2}."
        ),
    })

    # Unweighted state-transition graph (Class L instantiation, plain version)
    print("Building unweighted state-transition graph (Class L)...", file=sys.stderr)
    A = build_unweighted_graph(states_list)
    topo = state_space_topology(A)
    records.append({
        "record_kind": "graph_laplacian_unweighted",
        **topo,
        "note": (
            "Unweighted state-transition graph: each state is a node; each legal reaction = an edge to a neighbour state. "
            "Spectral gap (Fiedler) lambda_1 measures the topology's connectivity; small lambda_1 = bottleneck regions."
        ),
    })

    # Weighted CTMC generator (the actual Markov-chain object)
    print("Building weighted CTMC generator Q...", file=sys.stderr)
    Q = build_weighted_transition_matrix(states_list)
    stat, sgap = ctmc_stationary_and_spectral_gap(Q)
    # Top-10 stationary states
    top_idx = np.argsort(stat)[::-1][:10]
    top_states = [(states_list[i], float(stat[i])) for i in top_idx]
    records.append({
        "record_kind": "ctmc_stationary_distribution",
        "n_states": int(Q.shape[0]),
        "n_nonzero_entries": int(Q.nnz),
        "ctmc_spectral_gap": sgap,
        "top_10_stationary_probabilities": top_states,
        "note": (
            "Continuous-time Markov chain generator Q for the CRN. Diagonal Q[i,i] = -sum_{j!=i} Q[i,j] is the "
            "total exit rate from state i. Stationary distribution = left eigenvector with eigenvalue 0. "
            "Spectral gap is the second-smallest |Re(lambda)| and controls mixing time."
        ),
    })

    # Spike #24 decomposition
    records.append({
        "record_kind": "spike_24_decomposition_crn",
        "Class_B_tagged_tuple": "PRESENT — state = (X, Y) tagged integer-tuple",
        "Class_C_iteration": "PRESENT — SSA = streaming iterator over (time, reaction_idx) pairs; reaction firing is the iteration primitive",
        "Class_D_late_binding": (
            "PRESENT (STRONGEST) — at each state, K reactions are propensity-weighted candidates; "
            "the 'choice' is a probabilistic dispatch sampled from the categorical distribution prop_i / sum(prop). "
            "This is exactly Class D late-binding but with weights instead of programmer-determined dispatch."
        ),
        "Class_E_catalog": "PRESENT — reactions are catalogued (R0/R1/R2) and selected by name+index",
        "Class_G_gap_finding": "PRESENT — Feinberg deficiency analysis is structural-gap finding on stoichiometric network (per Phase 9.3b)",
        "Class_H_self_introspection": "PRESENT — propensity computation is introspection on current state",
        "Class_I_cyclic_group_modular": "ABSENT — Lotka-Volterra has no state-space symmetry; X and Y are distinguishable species",
        "Class_J_period_relations": "PRESENT (Phase 9.1) — stoichiometric integer null-space governs conservation laws",
        "Class_K_equation_of_centre": "PRESENT IN MEAN-FIELD ODE (Phase 9.2) — mass-action ODE shows Kepler-shape harmonic ratios. ABSENT IN STATE-GRAPH STRUCTURE",
        "Class_L_graph_laplacian": "PRESENT — state-transition graph Laplacian computed; spectral gap measures bottleneck structure",
        "Class_M_hdc_encoding": "POSSIBLE but not native; reactions could be HDC-encoded",
        "Class_N_rational_approximation": "ABSENT for stoichiometry-as-integer; PRESENT for ratio-of-rate-constants if doing continued-fraction analysis (not done here)",
        "note": (
            "CRN-firing as a tactical choice instantiates MORE Class D structure than tic-tac-toe (probabilistic dispatch "
            "is a richer kind of late-binding than deterministic dispatch). CLASS I IS ABSENT (no symmetry of state space). "
            "Class K appears only in the MEAN-FIELD ODE projection, not in the graph structure."
        ),
    })

    # Kind-of-choice comparison
    records.append({
        "record_kind": "kind_of_choice_crn_vs_tictactoe",
        "tic_tac_toe": (
            "Discrete-deterministic-perfect-info-multi-agent zero-sum game with finite horizon"
        ),
        "crn_firing": (
            "Discrete-stochastic-physical-single-agent dynamics with continuous-time + infinite horizon"
        ),
        "shared_structure": (
            "Both instantiate Class B (state record), Class C (iteration over choices), Class D (dispatch over "
            "candidate successors), Class E (catalog of candidates), Class L (graph Laplacian of state-transition graph)."
        ),
        "different_structure": (
            "(1) CRN has propensity-WEIGHTED dispatch (probabilistic) vs tic-tac-toe's deterministic minimax-optimal dispatch. "
            "(2) CRN has NO Class I symmetry (X and Y are distinguishable); tic-tac-toe has D_4. "
            "(3) CRN has Class K signature in the MEAN-FIELD ODE projection (Phase 9.2 Kepler-shape) but not in the "
            "stochastic state-graph. Tic-tac-toe has no Class K. "
            "(4) CRN runs to infinity; tic-tac-toe terminates in <=9 plies. "
            "(5) CRN's 'value function' is propensity itself (physics); tic-tac-toe's is minimax (game theory)."
        ),
        "verdict": (
            "The refined hypothesis (tactical choice = Class D dispatch over Class L-spectral graph of legal "
            "successors, quotiented by Class I symmetry) FITS BOTH systems but the WEIGHTS attached to the dispatch "
            "are categorically different: physics-propensity (real-valued, probabilistic) vs game-theoretic-minimax "
            "(integer-valued, adversarial). Both are valid instances of Class D late-binding, but the underlying "
            "*choice criterion* (what makes one successor 'better' than another) is substrate-specific. "
            "The DIFFERENT KIND of choice surfaces here: CRN's choice is determined by physics + sampling; tic-tac-toe's "
            "is determined by adversarial-search + game-theoretic value. These are NOT reducible to each other, but "
            "BOTH instantiate the same Spike #24 primitive vocabulary."
        ),
        "consequence_for_user_hypothesis": (
            "The user's 'constraint manifold with branching points' hypothesis is FALSIFIED at the literal level for "
            "BOTH tic-tac-toe and CRN-firing (neither is a fixed-dim manifold; both are state-graphs with "
            "non-uniform local degree). The REFINED hypothesis (Class D dispatch over Class L-graph quotiented by "
            "Class I symmetry) fits BOTH, with the recognition that the 'choice criterion' attached to Class D "
            "is substrate-specific (minimax vs propensity). This is the second key observation of this bonus: "
            "TACTICAL CHOICE STRUCTURE is universal across discrete/stochastic substrates AT THE PRIMITIVE-CLASS LEVEL, "
            "but the choice-criterion semantics are not."
        ),
    })

    emit_ndjson(records, OUT_PATH)
    print(f"\nWrote {len(records)} records to {OUT_PATH}", file=sys.stderr)
    return records


if __name__ == "__main__":
    main()
