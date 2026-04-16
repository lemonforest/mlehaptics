"""F₂ fiber: rule-HV × geometry-HV.

Per-program data: (syntax_rule_counts, geom_hv). We build two views of F₂:

    M₂ ∈ ℝ^{|rules| × ENCODING_DIM}
        row j = Σ_{p: r_j in p} geom_hv_p

    F₂ HV — the HDC-form fiber:
        F₂ = Σ_p syn_hv_p ⊗ geom_hv_p   (symbolic)

    where the left side is a rule-HV bundle and the right is a 640-dim
    geometry HV. For the HDC form we'd need a joint space of the two
    dimensions — but since they're different dims (D vs 640), we keep
    the matrix view for analysis and use the matrix directly for
    projection / retrieval.

SVD of M₂ exposes the rule-subspaces most correlated with geometric
features. We expect rank ≤ 5-7 dominant modes clustering by symmetry.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from logo_ast import (
    Program, Block, RepeatStmt, MotionStmt, IfStmt, NumLit, BinOp, ALL_RULES,
    walk,
)
from logo_encode_syntax import rule_sequence

# ─── Value-enriched feature names ─────────────────────────────────
#
# Rule-count alone cannot distinguish `REPEAT 3 [...]` from `REPEAT 4
# [...]` — they're the same rule. The symmetry number n IS the
# discriminating information. We enrich the Part-B feature vector with
# categorical buckets over numeric literals appearing as immediate
# arguments to REPEAT, motions, and IF.
#
# The chosen buckets cover the polygon family's REPEAT counts and a
# few scales of motion steps / turn angles. Anything outside goes in
# an "other" bucket.

REPEAT_COUNT_BUCKETS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 24, 36, 60, 72, 90, 144, 180, 360]


def _bucket_repeat_count(v: float) -> str:
    iv = int(round(v))
    if iv in REPEAT_COUNT_BUCKETS:
        return f"repeat_n={iv}"
    return "repeat_n=other"


# Extra rule-like keys injected into the feature axis.
EXTRA_FEATURES: List[str] = (
    [f"repeat_n={n}" for n in REPEAT_COUNT_BUCKETS]
    + ["repeat_n=other"]
)

# Extended order used for F₂ matrix rows.
EXTENDED_ORDER: List[str] = list(ALL_RULES) + EXTRA_FEATURES


@dataclass
class F2Payload:
    """Collected data for building F₂."""
    names: List[str] = field(default_factory=list)
    rule_counts: List[Counter] = field(default_factory=list)   # per program
    geom_hvs: List[np.ndarray] = field(default_factory=list)   # per program (640,)

    def add(self, name: str, rc: Counter, g: np.ndarray) -> None:
        self.names.append(name)
        self.rule_counts.append(rc)
        self.geom_hvs.append(g)

    def __len__(self) -> int:
        return len(self.names)


def build_f2_matrix(
    payload: F2Payload,
    *,
    right_order: Sequence[str] = ALL_RULES,
    normalize_geom: bool = True,
    normalize_counts: bool = True,
) -> np.ndarray:
    """M₂[rule, geom_dim] = Σ_p count(rule in p) · geom_hv_p[geom_dim].

    Orientation: rows indexed by rule (Part B), columns by geometry
    dimension. SVD left-singular vectors are patterns over rules; right
    singular vectors are patterns over geometry dims.

    Normalization (both default-on):
        normalize_geom    — unit-norm each program's geometry HV before
                             accumulation. Without this, programs with
                             larger traces (REPEAT 360) dominate every
                             row shared with other programs.
        normalize_counts  — divide each program's feature-count vector
                             by its L1 norm so every program contributes
                             equal "weight" to M, independent of its
                             total statement count.
    """
    if not payload.geom_hvs:
        raise ValueError("payload is empty")
    D_geom = payload.geom_hvs[0].size
    M = np.zeros((len(right_order), D_geom), dtype=np.float64)
    rmap = {r: i for i, r in enumerate(right_order)}
    for rc, g in zip(payload.rule_counts, payload.geom_hvs):
        if normalize_geom:
            gn = float(np.linalg.norm(g))
            g_scaled = g / gn if gn > 0.0 else g
        else:
            g_scaled = g
        if normalize_counts:
            total = float(sum(rc.values()))
            inv = 1.0 / total if total > 0.0 else 0.0
        else:
            inv = 1.0
        for r, c in rc.items():
            if r in rmap:
                M[rmap[r]] += (c * inv) * g_scaled
    return M


def project_program(
    rc: Counter,
    U: np.ndarray,
    *,
    right_order: Sequence[str] = ALL_RULES,
    top_modes: int = 5,
) -> np.ndarray:
    """Project a program's rule-count vector onto F₂'s top rule modes.

    `U` is the left-singular-vector matrix from SVD of M₂. Result is a
    `top_modes`-dim feature vector (signed).
    """
    v = np.zeros(len(right_order), dtype=np.float64)
    for r, c in rc.items():
        if r in right_order:
            v[right_order.index(r)] = c
    return U[:, :top_modes].T @ v


def program_rule_counts(prog: Program) -> Counter:
    """Wrapper around rule_sequence for F₂ ingestion."""
    return Counter(rule_sequence(prog))


def program_features(prog: Program) -> Counter:
    """Value-enriched syntax feature vector for F₂.

    Combines:
      - rule_sequence counts (all ALL_RULES)
      - repeat-count literal-value buckets: for every REPEAT whose
        count is a literal, bump `repeat_n=<bucket>` by 1.

    Keyed by strings from EXTENDED_ORDER.
    """
    feats = Counter(rule_sequence(prog))
    for n in walk(prog):
        if isinstance(n, RepeatStmt) and isinstance(n.count, NumLit):
            feats[_bucket_repeat_count(n.count.value)] += 1
    return feats
