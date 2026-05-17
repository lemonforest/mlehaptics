"""
Spike #43b — Sub-structural component identification INSIDE the larger graph-Laplacian picture.

Builds on Spike #43's whole-document signatures (R1-R5 / S1-S8).
NEW: sub-cascade decomposition via multiple structural views.

Methods applied to each substrate:
  M1 — Recursive Fiedler partition (dendrogram of nested structures)
  M2 — Louvain-style modularity (communities of chapters)
  M3 — Agglomerative hierarchical clustering on chapter HDC fingerprints
  M4 — Sub-cascade boundary detection (extends Spike #43 Anomaly 3 srmech topic-shift bump)
  M5 — Per-paragraph local Laplacian (within-chapter sub-structure)
  M6 — Spectral gap multi-scale analysis (lambda_2 vs lambda_3 vs lambda_4 ...)

Discipline:
- Closed-form deterministic; no SGD, no per-particle free parameters
- NDJSON output per [[feedback_ndjson_over_bloated_json]]
- 14-class A-N vocabulary; no new classes per [[feedback_no_privileged_primitive_classes]]
- Numpy for array ops; scipy.sparse.csgraph for Laplacian eigvals (n big enough that pure-python is slow)
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import scipy.sparse.csgraph as csgraph
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


# ------------------------------------------------------------------------
# Substrate loading
# ------------------------------------------------------------------------


CANONICAL_PATHS = {
    "mfo_notebook": (
        r"D:\GitHub\mlehaptics\docs\antikythera-maths\mfo_spectral_research_notebook.md",
        True,
        "canonical good — MFO spectral research notebook",
    ),
    "srmech_notebook": (
        r"D:\GitHub\mlehaptics\docs\srmech\srmech_research_notebook.md",
        True,
        "canonical good — srmech master architecture notebook",
    ),
    "spike_38b": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_38b_caffeine_form_function_remnants_2026-05-17.md",
        True,
        "canonical good — Spike #38b template",
    ),
    "spike_41": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_41_fibonacci_unity_2026-05-17.md",
        True,
        "canonical good — Spike #41",
    ),
    "spike_42": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_42_imprinting_cascade_entropy_reposture_2026-05-17.md",
        True,
        "canonical good — Spike #42",
    ),
    "spike_43": (
        r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_43_literature_spectral_shape_2026-05-17.md",
        True,
        "canonical good — Spike #43 (the foundation this work refines)",
    ),
}

CONTROL_PATHS = {
    "C1_paragraph_permute": r"D:\temp\spike_43\C1_paragraph_permute_mfo.md",
    "C2_concat_unrelated": r"D:\temp\spike_43\C2_concatenated_unrelated.md",
    "C3_word_salad": r"D:\temp\spike_43\C3_word_salad_mfo.md",
    "C4_linear_enumeration": r"D:\temp\spike_43\C4_linear_enumeration.md",
    "C5_llm_flat": r"D:\temp\spike_43\C5_llm_generated_flat.md",
}


@dataclass
class Substrate:
    name: str
    path: str
    text: str
    is_canonical_good: bool
    notes: str


def load_substrate(name: str, path: str, is_canonical_good: bool, notes: str) -> Substrate | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    return Substrate(name=name, path=path, text=text, is_canonical_good=is_canonical_good, notes=notes)


# ------------------------------------------------------------------------
# Tokenisation (matches Spike #43)
# ------------------------------------------------------------------------


def tokenize_chapters(text: str) -> list[tuple[str, str]]:
    """Split on top-level H2 (## )."""
    lines = text.split("\n")
    chapters = []
    cur_h = "[front-matter]"
    cur_b: list[str] = []
    for line in lines:
        if re.match(r"^## ", line):
            chapters.append((cur_h, cur_b))
            cur_h = line[3:].strip()
            cur_b = []
        else:
            cur_b.append(line)
    chapters.append((cur_h, cur_b))
    return [(h, "\n".join(b)) for h, b in chapters if b and any(l.strip() for l in b)]


def tokenize_paragraphs(body: str) -> list[str]:
    paras = re.split(r"\n\s*\n", body)
    return [p.strip() for p in paras if p.strip()]


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")


def tokenize_words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


# ------------------------------------------------------------------------
# HDC fingerprint per chapter (Class M; integer-ALU friendly)
# Use SplitMix64-style deterministic hashing per Spike #43 anomaly 1 fix.
# ------------------------------------------------------------------------


def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return x ^ (x >> 31)


HDC_DIM = 1024


def word_hv(word: str) -> np.ndarray:
    """Deterministic ±1 hypervector for word, length HDC_DIM."""
    seed = int.from_bytes(hashlib.sha256(word.encode("utf-8")).digest()[:8], "big")
    out = np.empty(HDC_DIM, dtype=np.int8)
    x = seed
    for i in range(HDC_DIM):
        x = splitmix64(x)
        out[i] = 1 if (x & 1) else -1
    return out


def chapter_hv(words: list[str]) -> np.ndarray:
    """Bundle word HVs via majority (sign of sum)."""
    if not words:
        return np.zeros(HDC_DIM, dtype=np.int8)
    acc = np.zeros(HDC_DIM, dtype=np.int64)
    seen_cache: dict[str, np.ndarray] = {}
    for w in words:
        hv = seen_cache.get(w)
        if hv is None:
            hv = word_hv(w)
            seen_cache[w] = hv
        acc += hv
    # Resolve ties to +1 (deterministic)
    sign = np.where(acc >= 0, 1, -1).astype(np.int8)
    return sign


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a.astype(np.int32), b.astype(np.int32))) / HDC_DIM


# ------------------------------------------------------------------------
# Chapter similarity graph (Jaccard on top-vocab; threshold)
# ------------------------------------------------------------------------


def chapter_word_sets(chapters: list[tuple[str, str]], top_n: int = 100) -> list[set[str]]:
    """Top-N most frequent non-trivial words per chapter."""
    out = []
    for _, body in chapters:
        words = tokenize_words(body)
        counter = collections.Counter(words)
        # Filter very short tokens to avoid noise; matches Spike #43
        top_words = {w for w, _ in counter.most_common(top_n * 2) if len(w) >= 4}
        # Keep first top_n
        top_words = set(list(top_words)[:top_n])
        out.append(top_words)
    return out


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def chapter_similarity_matrix(chapters: list[tuple[str, str]]) -> np.ndarray:
    """Jaccard-on-top-vocab similarity matrix (symmetric, diag=1)."""
    word_sets = chapter_word_sets(chapters)
    n = len(word_sets)
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            v = jaccard(word_sets[i], word_sets[j])
            M[i, j] = M[j, i] = v
        M[i, i] = 1.0
    return M


def chapter_hv_similarity_matrix(chapters: list[tuple[str, str]]) -> np.ndarray:
    n = len(chapters)
    hvs = [chapter_hv(tokenize_words(b)) for _, b in chapters]
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            v = cosine(hvs[i], hvs[j])
            M[i, j] = M[j, i] = v
        M[i, i] = 1.0
    return M


# ------------------------------------------------------------------------
# M1 — Recursive Fiedler partition (dendrogram of nested structures)
# ------------------------------------------------------------------------


def laplacian_eigvals(W: np.ndarray) -> np.ndarray:
    """Symmetric graph Laplacian eigenvalues, ascending."""
    n = W.shape[0]
    if n == 0:
        return np.array([])
    D = np.diag(W.sum(axis=1))
    L = D - W
    eigs = np.linalg.eigvalsh(L)
    return np.sort(eigs)


def fiedler_vector(W: np.ndarray) -> np.ndarray | None:
    """Second-smallest eigenvector of graph Laplacian (algebraic connectivity)."""
    n = W.shape[0]
    if n < 2:
        return None
    D = np.diag(W.sum(axis=1))
    L = D - W
    eigvals, eigvecs = np.linalg.eigh(L)
    # Second smallest
    idx = np.argsort(eigvals)
    return eigvecs[:, idx[1]]


def recursive_fiedler_dendrogram(
    W: np.ndarray, indices: list[int] | None = None, depth: int = 0, max_depth: int = 5
) -> dict:
    """Recursively bisect via Fiedler sign; return dendrogram dict."""
    if indices is None:
        indices = list(range(W.shape[0]))
    n = len(indices)
    if n <= 1 or depth >= max_depth:
        return {"depth": depth, "indices": indices, "n": n, "leaf": True}
    sub_W = W[np.ix_(indices, indices)]
    fv = fiedler_vector(sub_W)
    if fv is None:
        return {"depth": depth, "indices": indices, "n": n, "leaf": True}
    pos = [indices[i] for i in range(n) if fv[i] >= 0]
    neg = [indices[i] for i in range(n) if fv[i] < 0]
    # Don't split if either side is empty
    if not pos or not neg:
        return {"depth": depth, "indices": indices, "n": n, "leaf": True, "unsplittable": True}
    # Spectral gap at this cut
    L_sub = np.diag(sub_W.sum(axis=1)) - sub_W
    eigs = np.sort(np.linalg.eigvalsh(L_sub))
    spectral_gap = float(eigs[2] - eigs[1]) if len(eigs) >= 3 else 0.0
    return {
        "depth": depth,
        "indices": indices,
        "n": n,
        "spectral_gap": spectral_gap,
        "lambda_2": float(eigs[1]) if len(eigs) >= 2 else 0.0,
        "lambda_3": float(eigs[2]) if len(eigs) >= 3 else 0.0,
        "left": recursive_fiedler_dendrogram(W, pos, depth + 1, max_depth),
        "right": recursive_fiedler_dendrogram(W, neg, depth + 1, max_depth),
        "leaf": False,
    }


def dendrogram_max_depth(tree: dict) -> int:
    if tree.get("leaf"):
        return tree["depth"]
    return max(dendrogram_max_depth(tree["left"]), dendrogram_max_depth(tree["right"]))


def dendrogram_leaf_count(tree: dict) -> int:
    if tree.get("leaf"):
        return 1
    return dendrogram_leaf_count(tree["left"]) + dendrogram_leaf_count(tree["right"])


def dendrogram_stable_depth(tree: dict, min_gap: float = 0.01) -> int:
    """Deepest depth at which spectral_gap > min_gap (stable partition)."""
    if tree.get("leaf"):
        return -1
    gap = tree.get("spectral_gap", 0.0)
    if gap < min_gap:
        return tree["depth"]
    left_d = dendrogram_stable_depth(tree["left"], min_gap)
    right_d = dendrogram_stable_depth(tree["right"], min_gap)
    return max(tree["depth"], left_d, right_d)


def collect_dendrogram_stats(tree: dict) -> dict:
    leaves = []
    def walk(t):
        if t.get("leaf"):
            leaves.append(t["n"])
        else:
            walk(t["left"]); walk(t["right"])
    walk(tree)
    return {
        "max_depth": dendrogram_max_depth(tree),
        "leaf_count": dendrogram_leaf_count(tree),
        "leaf_sizes": leaves,
        "stable_depth_001": dendrogram_stable_depth(tree, 0.01),
        "stable_depth_010": dendrogram_stable_depth(tree, 0.10),
        "top_lambda_2": tree.get("lambda_2", 0.0),
        "top_lambda_3": tree.get("lambda_3", 0.0),
        "top_spectral_gap": tree.get("spectral_gap", 0.0),
    }


# ------------------------------------------------------------------------
# M2 — Louvain-style modularity (greedy single-pass; deterministic)
# ------------------------------------------------------------------------


def modularity(W: np.ndarray, community: np.ndarray) -> float:
    """Newman modularity Q = (1/2m) sum_ij [W_ij - k_i k_j / 2m] delta(c_i, c_j).
    Vectorised: build delta matrix once."""
    m2 = float(W.sum())
    if m2 == 0:
        return 0.0
    k = W.sum(axis=1)
    # delta_ij = 1 if community[i]==community[j] else 0
    delta = (community[:, None] == community[None, :]).astype(np.float64)
    expected = np.outer(k, k) / m2
    Q = float(((W - expected) * delta).sum()) / m2
    return Q


def greedy_louvain_pass(W: np.ndarray, max_passes: int = 10, max_n: int = 60) -> np.ndarray:
    """Greedy modularity optimisation; deterministic node order; single agglomeration pass.

    For n > max_n, we coarsen to top max_n nodes by degree first (treats other nodes
    as forming a residual community via average-linkage to the coarsened set).

    Sufficient for finding partition structure; not chasing modularity optimum.
    """
    n = W.shape[0]
    if n > max_n:
        # Coarsen: pick top max_n by degree; rest get assigned to nearest in the coarsened set
        deg = W.sum(axis=1)
        top_idx = np.argsort(-deg)[:max_n]
        top_set = set(top_idx.tolist())
        coarse_W = W[np.ix_(top_idx, top_idx)]
        coarse_comm = _louvain_inner(coarse_W, max_passes)
        # Assign remaining nodes to community of their nearest top-node
        community = np.zeros(n, dtype=int)
        top_pos = {orig: pos for pos, orig in enumerate(top_idx.tolist())}
        for i in range(n):
            if i in top_set:
                community[i] = coarse_comm[top_pos[i]]
            else:
                # Find best similarity to any top node
                sims = W[i, top_idx]
                best_top = int(np.argmax(sims))
                community[i] = coarse_comm[best_top]
        # Relabel
        unique = sorted(set(community.tolist()))
        relabel = {c: i for i, c in enumerate(unique)}
        return np.array([relabel[c] for c in community])
    else:
        return _louvain_inner(W, max_passes)


def _louvain_inner(W: np.ndarray, max_passes: int = 10) -> np.ndarray:
    n = W.shape[0]
    community = np.arange(n)
    for _ in range(max_passes):
        improved = False
        for i in range(n):
            best_q = modularity(W, community)
            best_c = community[i]
            # Try moving i to community of each unique neighbour
            neighbours = np.where(W[i] > 0)[0]
            tried_communities = set()
            for j in neighbours:
                if i == j:
                    continue
                cj = community[j]
                if cj == community[i] or cj in tried_communities:
                    continue
                tried_communities.add(cj)
                trial = community.copy()
                trial[i] = cj
                q = modularity(W, trial)
                if q > best_q + 1e-9:
                    best_q = q
                    best_c = cj
                    improved = True
            community[i] = best_c
        if not improved:
            break
    # Relabel
    unique = sorted(set(community.tolist()))
    relabel = {c: i for i, c in enumerate(unique)}
    return np.array([relabel[c] for c in community])


def community_stats(community: np.ndarray) -> dict:
    sizes = collections.Counter(community.tolist())
    return {
        "n_communities": len(sizes),
        "community_sizes": sorted(sizes.values(), reverse=True),
        "largest_community_frac": max(sizes.values()) / len(community) if len(community) else 0.0,
    }


# ------------------------------------------------------------------------
# M3 — Agglomerative hierarchical clustering on chapter HDC fingerprints
# ------------------------------------------------------------------------


def hdc_dendrogram(W_hdc: np.ndarray) -> dict:
    """Average-linkage agglomerative clustering on (1 - cosine_sim) distance."""
    n = W_hdc.shape[0]
    if n < 2:
        return {"linkage_matrix": [], "n": n}
    # Convert similarity in [-1, 1] -> distance in [0, 2]
    D = 1.0 - W_hdc
    np.fill_diagonal(D, 0.0)
    # Ensure symmetry + non-negative
    D = np.clip((D + D.T) / 2, 0.0, None)
    # Condensed distance for scipy
    condensed = squareform(D, checks=False)
    Z = sch.linkage(condensed, method="average")
    # Auto-cluster cuts at varying inconsistency
    cuts_2 = sch.fcluster(Z, t=2, criterion="maxclust")
    cuts_3 = sch.fcluster(Z, t=3, criterion="maxclust")
    cuts_5 = sch.fcluster(Z, t=5, criterion="maxclust")
    # Cophenetic correlation: how faithfully the dendrogram preserves pairwise distance
    coph_corr, _ = sch.cophenet(Z, condensed)
    return {
        "n": n,
        "n_clusters_at_2": int(cuts_2.max()),
        "n_clusters_at_3": int(cuts_3.max()),
        "n_clusters_at_5": int(cuts_5.max()),
        "cluster_2_sizes": sorted(collections.Counter(cuts_2.tolist()).values(), reverse=True),
        "cluster_3_sizes": sorted(collections.Counter(cuts_3.tolist()).values(), reverse=True),
        "cluster_5_sizes": sorted(collections.Counter(cuts_5.tolist()).values(), reverse=True),
        "cophenetic_correlation": float(coph_corr),
        "linkage_heights": Z[:, 2].tolist(),
    }


# ------------------------------------------------------------------------
# M4 — Sub-cascade boundary detection (extends Spike #43 Anomaly 3)
# Adjacent-chapter HV cosine; look for sudden drops (topic-shift boundaries).
# ------------------------------------------------------------------------


def adjacent_hv_cosine_sequence(chapters: list[tuple[str, str]]) -> list[float]:
    n = len(chapters)
    if n < 2:
        return []
    hvs = [chapter_hv(tokenize_words(b)) for _, b in chapters]
    return [cosine(hvs[i], hvs[i + 1]) for i in range(n - 1)]


def detect_sub_cascade_boundaries(seq: list[float], drop_threshold: float = 0.05) -> dict:
    """Boundary = position where cosine drops > drop_threshold below local mean."""
    if not seq:
        return {"n_boundaries": 0, "boundary_positions": [], "max_drop": 0.0}
    if len(seq) < 2:
        return {"n_boundaries": 0, "boundary_positions": [], "max_drop": 0.0}
    arr = np.array(seq)
    # Look at z-score drops
    mean = arr.mean()
    std = arr.std() if arr.std() > 0 else 1.0
    boundaries = [int(i) for i in range(len(arr)) if (mean - arr[i]) > drop_threshold]
    z_min = float((mean - arr.min()) / std) if std > 0 else 0.0
    return {
        "n_boundaries": len(boundaries),
        "boundary_positions": boundaries,
        "max_drop": float(mean - arr.min()),
        "max_drop_zscore": z_min,
        "mean_cosine": float(mean),
        "min_cosine": float(arr.min()),
    }


# ------------------------------------------------------------------------
# M5 — Per-paragraph local Laplacian (within-chapter sub-structure)
# Pick the LARGEST chapter; build paragraph-similarity graph; spectral analysis.
# ------------------------------------------------------------------------


def paragraph_similarity_graph(paragraphs: list[str], top_n: int = 50) -> np.ndarray:
    """Jaccard on top-vocab per paragraph."""
    word_sets = []
    for p in paragraphs:
        words = tokenize_words(p)
        counter = collections.Counter(words)
        top = {w for w, _ in counter.most_common(top_n) if len(w) >= 4}
        word_sets.append(top)
    n = len(word_sets)
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            v = jaccard(word_sets[i], word_sets[j])
            M[i, j] = M[j, i] = v
        M[i, i] = 1.0
    return M


def within_chapter_laplacian_analysis(chapters: list[tuple[str, str]]) -> dict:
    """Pick the largest chapter; analyse its paragraph-graph spectral structure."""
    if not chapters:
        return {"valid": False}
    # Largest chapter by paragraph count
    sizes = [(i, len(tokenize_paragraphs(b))) for i, (_, b) in enumerate(chapters)]
    sizes.sort(key=lambda x: -x[1])
    largest_idx = sizes[0][0]
    largest_n = sizes[0][1]
    if largest_n < 4:
        return {"valid": False, "reason": "largest chapter has <4 paragraphs"}
    paragraphs = tokenize_paragraphs(chapters[largest_idx][1])
    W = paragraph_similarity_graph(paragraphs)
    eigs = laplacian_eigvals(W)
    if len(eigs) < 4:
        return {"valid": False}
    return {
        "valid": True,
        "chapter_index": int(largest_idx),
        "chapter_heading": chapters[largest_idx][0][:80],
        "n_paragraphs": largest_n,
        "lambda_1": float(eigs[0]),
        "lambda_2": float(eigs[1]),
        "lambda_3": float(eigs[2]),
        "lambda_4": float(eigs[3]),
        "lambda_2_3_gap": float(eigs[2] - eigs[1]),
        "lambda_3_4_gap": float(eigs[3] - eigs[2]),
        "spectral_radius": float(eigs[-1]),
        "n_zero_eigs": int(np.sum(eigs < 1e-9)),  # connected components
    }


# ------------------------------------------------------------------------
# M6 — Spectral gap multi-scale analysis (lambda_2 / lambda_3 / lambda_4 ratios)
# ------------------------------------------------------------------------


def multi_scale_spectral_gaps(W: np.ndarray) -> dict:
    eigs = laplacian_eigvals(W)
    if len(eigs) < 5:
        return {"valid": False, "n": len(eigs)}
    return {
        "valid": True,
        "n": len(eigs),
        "lambda_1": float(eigs[0]),
        "lambda_2": float(eigs[1]),
        "lambda_3": float(eigs[2]),
        "lambda_4": float(eigs[3]),
        "lambda_5": float(eigs[4]),
        "lambda_n": float(eigs[-1]),
        "gap_2_3": float(eigs[2] - eigs[1]),
        "gap_3_4": float(eigs[3] - eigs[2]),
        "gap_4_5": float(eigs[4] - eigs[3]),
        "ratio_l2_l3": float(eigs[1] / eigs[2]) if eigs[2] > 0 else 0.0,
        "ratio_l3_l4": float(eigs[2] / eigs[3]) if eigs[3] > 0 else 0.0,
        "n_zero_eigs": int(np.sum(eigs < 1e-9)),
        "spectral_radius": float(eigs[-1]),
        # The "knee" — how quickly do gaps decay? Indicates multi-scale richness.
        "gap_decay_2_to_4": float(eigs[2] - eigs[1]) / max(float(eigs[3] - eigs[2]), 1e-9),
    }


# ------------------------------------------------------------------------
# Per-substrate full sub-structural fingerprint
# ------------------------------------------------------------------------


def analyse_substrate(sub: Substrate) -> dict:
    chapters = tokenize_chapters(sub.text)
    n_chap = len(chapters)
    if n_chap < 3:
        return {
            "substrate": sub.name,
            "n_chapters": n_chap,
            "valid": False,
            "reason": "too few chapters for sub-structural analysis",
        }
    W_jac = chapter_similarity_matrix(chapters)
    W_hdc = chapter_hv_similarity_matrix(chapters)

    dendro = recursive_fiedler_dendrogram(W_jac)
    dendro_stats = collect_dendrogram_stats(dendro)

    community = greedy_louvain_pass(W_jac)
    comm_stats = community_stats(community)

    hdc_clust = hdc_dendrogram(W_hdc)

    adj_cos = adjacent_hv_cosine_sequence(chapters)
    sub_cascades = detect_sub_cascade_boundaries(adj_cos)

    within = within_chapter_laplacian_analysis(chapters)

    multi_gaps = multi_scale_spectral_gaps(W_jac)

    return {
        "substrate": sub.name,
        "is_canonical_good": sub.is_canonical_good,
        "notes": sub.notes,
        "n_chapters": n_chap,
        "n_words": len(tokenize_words(sub.text)),
        "M1_recursive_fiedler": dendro_stats,
        "M2_louvain_modularity": comm_stats,
        "M3_hdc_hierarchical": hdc_clust,
        "M4_sub_cascade_boundaries": sub_cascades,
        "M5_within_chapter": within,
        "M6_multi_scale_gaps": multi_gaps,
    }


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------


def main():
    out_dir = Path(r"D:\temp\spike_43b")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "spike_43b_substructural_records_2026-05-17.ndjson"

    records: list[dict] = []

    # Canonical good
    for name, (path, good, notes) in CANONICAL_PATHS.items():
        sub = load_substrate(name, path, good, notes)
        if sub is None:
            sys.stderr.write(f"[skip] {name} (file not found at {path})\n")
            continue
        sys.stderr.write(f"[analyse] {name} ({len(sub.text)} bytes)\n")
        rec = analyse_substrate(sub)
        rec["substrate_class"] = "canonical_good"
        records.append(rec)

    # Constructed controls
    for name, path in CONTROL_PATHS.items():
        sub = load_substrate(name, path, False, "constructed control from Spike #43")
        if sub is None:
            sys.stderr.write(f"[skip] {name} (file not found at {path})\n")
            continue
        sys.stderr.write(f"[analyse] {name} (control, {len(sub.text)} bytes)\n")
        rec = analyse_substrate(sub)
        rec["substrate_class"] = "constructed_control"
        records.append(rec)

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    sys.stderr.write(f"\nWrote {len(records)} records to {out_path}\n")
    return records


if __name__ == "__main__":
    main()
