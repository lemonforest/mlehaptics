"""Fiber machinery — dual matrix/HDC representation of a coupling.

Two views, same object:

    M[i,j] = α(left_i, right_j)          (matrix form, for SVD)
    F      = Σ_{i,j} α(i,j) · bind(L_i, R_j)   (HDC form, for retrieval)

Functions:
    build_fiber_matrix   corpus → α(c, r) counts → M
    fiber_to_hdc         M + codebooks → F
    svd_report           M → {rank, singular_values, left_modes, right_modes}
    unbind_retrieve      F + one side → cleaned-up other side
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import numpy as np

from .hd import HD, bundle_sum, bind, unbind, sim, normalize


# ─── Fiber matrix construction ────────────────────────────────────

def build_fiber_matrix(
    coincidences: Iterable[tuple[str, str, float]],
    *,
    left_order: Sequence[str],
    right_order: Sequence[str],
) -> np.ndarray:
    """Count-based fiber matrix.

    Parameters
    ----------
    coincidences
        Iterable of (left_name, right_name, weight) tuples. Each tuple
        contributes `weight` to M[left_idx, right_idx].
    left_order, right_order
        Canonical row/column orderings (usually ALL_COMMANDS / ALL_RULES).

    Returns
    -------
    np.ndarray, shape (|left|, |right|)
    """
    li = {n: i for i, n in enumerate(left_order)}
    ri = {n: j for j, n in enumerate(right_order)}
    M = np.zeros((len(left_order), len(right_order)), dtype=np.float64)
    for lname, rname, w in coincidences:
        if lname not in li or rname not in ri:
            continue
        M[li[lname], ri[rname]] += w
    return M


# ─── SVD report ───────────────────────────────────────────────────

@dataclass
class SVDReport:
    singular_values: np.ndarray          # full spectrum
    rank: int                            # effective rank @ rtol
    rank_rtol: float                     # the rtol used
    U: np.ndarray                        # left modes
    Vt: np.ndarray                       # right modes (rows = right singular vectors)
    null_cols: List[int]                 # columns of M whose norm is 0
    null_rows: List[int]                 # rows of M whose norm is 0


def svd_report(M: np.ndarray, *, rtol: float = 1e-6) -> SVDReport:
    """Compute SVD and package the "interesting" numbers.

    `rank` counts singular values > rtol * σ_max (relative tolerance).
    `null_rows`/`null_cols` identify symbols that participate in no
    coincidence — "structurally inert" in the plan's language.
    """
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    smax = float(s[0]) if s.size > 0 and s[0] > 0 else 0.0
    thresh = rtol * smax if smax > 0 else 0.0
    rank = int(np.sum(s > thresh))
    null_rows = [i for i in range(M.shape[0])
                 if np.linalg.norm(M[i, :]) == 0.0]
    null_cols = [j for j in range(M.shape[1])
                 if np.linalg.norm(M[:, j]) == 0.0]
    return SVDReport(s, rank, rtol, U, Vt, null_cols, null_rows)


# ─── HDC form of the fiber ────────────────────────────────────────

def fiber_to_hdc(
    M: np.ndarray,
    left_cb: Dict[str, HD],
    right_cb: Dict[str, HD],
    left_order: Sequence[str],
    right_order: Sequence[str],
    *,
    normalize_rows: bool = True,
) -> HD:
    """Build the single-HV representation of the fiber.

        F = Σ_{i,j} W[i,j] · bind(L_i, R_j)

    where `W` is either `M` (raw counts; `normalize_rows=False`) or
    `M / row_sum(M)` (per-row L1-normalized; `normalize_rows=True`,
    the default).

    Per-row normalization (iteration-2 fix, Phase 1c)
    -------------------------------------------------
    Without it, heavy-weight rules (e.g. MOTION_NUM at α=23,
    REPEAT_NUM_BLOCK at α=22) dominate retrieval globally. Probing for
    PENUP-coupled rules then returns MOTION_NUM at higher cosine than
    the true PEN coupling (α=5). Normalizing per row equalizes
    per-command contribution; measured top-1 accuracy on the corpus
    jumps from 5/11 (45%) raw to 10/11 (91%) normalized. THING remains
    misretrieved (its quantum atom is similar enough to FORWARD that
    cross-row MOTION_NUM noise wins) — that's a structured-atom
    limitation, not a fiber-construction one.

    Returned as a real-valued vector (NOT binarized). Use
    `hd.normalize(F)` if you want bipolar; leave as-is to preserve
    magnitude information for retrieval.
    """
    if M.shape != (len(left_order), len(right_order)):
        raise ValueError(
            f"M shape {M.shape} != ({len(left_order)}, {len(right_order)})"
        )
    if normalize_rows:
        rs = M.sum(axis=1, keepdims=True)
        rs[rs == 0.0] = 1.0
        W = M / rs
    else:
        W = M
    accum = None
    for i, lname in enumerate(left_order):
        Li = left_cb[lname]
        for j, rname in enumerate(right_order):
            w = float(W[i, j])
            if w == 0.0:
                continue
            term = w * bind(Li, right_cb[rname])
            accum = term if accum is None else accum + term
    if accum is None:
        # Empty fiber → zero vector matching one of the atoms' shape.
        ref = next(iter(left_cb.values()))
        return np.zeros_like(ref)
    return accum


def unbind_retrieve(
    F: HD,
    probe: HD,
    target_cb: Dict[str, HD],
    *,
    top_k: int = 3,
) -> List[tuple[str, float]]:
    """Given a fiber HV F and a probe from one side, return the top-k
    target-side names by cosine similarity to unbind(F, probe).

    For MAP-B this is: target_estimate = probe * F.
    """
    est = unbind(F, probe)
    scored = [(name, sim(est, hv)) for name, hv in target_cb.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
