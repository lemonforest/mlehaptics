"""§11.6 Phase A — partition detection in phase space.

For a sequence of per-ply 640-dim encodings, computes pairwise similarity
matrix, identifies phase clusters (sequences of consecutive plies with
internal similarity above τ), and records partition boundaries (drops
below τ between consecutive plies).

See PHASE_OPERATOR_SUPPLEMENT.md §11.6 for the experimental protocol.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PartitionResult:
    """Per-game partition structure at a specific threshold τ.

    similarity_matrix: (n_plies, n_plies) symmetric cosine-similarity matrix.
    cluster_ids: length-n_plies array; integer cluster assignment per ply.
    boundaries: list of ply indices where a cluster ends (right before
        the next starts).
    """
    similarity_matrix: np.ndarray
    cluster_ids: np.ndarray
    boundaries: list
    threshold: float


def pairwise_cosine(encodings: np.ndarray) -> np.ndarray:
    """Input: (n_plies, 640) array of per-ply encodings.
    Output: (n_plies, n_plies) symmetric cosine-similarity matrix.

    Handles zero-norm rows gracefully by returning 0.0 for those pairs
    (should not occur in practice but guards against encoder edge cases).
    """
    if encodings.ndim != 2:
        raise ValueError(
            f"encodings must be 2-D; got shape {encodings.shape}")
    norms = np.linalg.norm(encodings, axis=1)
    safe = norms > 0.0
    normalized = np.zeros_like(encodings, dtype=float)
    normalized[safe] = encodings[safe] / norms[safe, None]
    sim = normalized @ normalized.T
    # Re-zero any rows/cols where the source row had zero norm.
    if not safe.all():
        dead = ~safe
        sim[dead, :] = 0.0
        sim[:, dead] = 0.0
        # Diagonal for dead rows: define self-similarity as 0.0 too (the
        # vector carries no direction to be similar to).
    # Clip float drift strictly into [-1, 1].
    return np.clip(sim, -1.0, 1.0)


def detect_clusters(
    similarity_matrix: np.ndarray,
    threshold: float,
) -> tuple:
    """Identify maximal consecutive-ply clusters at a given threshold.

    A cluster is a maximal [start, end] range of consecutive plies such
    that similarity_matrix[i, j] >= threshold for all i, j in
    [start, end].

    Returns:
        cluster_ids: length-n_plies int array, cluster assignment per
                     ply (0-indexed within the game).
        boundaries:  sorted list of ply indices where cluster i ends
                     (so ply boundaries[k] is in cluster k, ply
                     boundaries[k]+1 is in cluster k+1, for
                     k < len(boundaries)).
    """
    n = similarity_matrix.shape[0]
    if n == 0:
        return np.zeros(0, dtype=int), []
    cluster_ids = np.zeros(n, dtype=int)
    boundaries: list = []
    current_id = 0
    cluster_start = 0
    for i in range(1, n):
        # Check that ply i has >=threshold similarity with every ply
        # currently in the active cluster [cluster_start, i-1].
        row_slice = similarity_matrix[i, cluster_start:i]
        if np.all(row_slice >= threshold):
            cluster_ids[i] = current_id
        else:
            boundaries.append(i - 1)
            current_id += 1
            cluster_start = i
            cluster_ids[i] = current_id
    return cluster_ids, boundaries


def run_partition_analysis(
    encodings: np.ndarray,
    thresholds: tuple = (0.70, 0.80, 0.85, 0.90, 0.95),
) -> dict:
    """Run cluster detection at each threshold in the sweep.

    Returns a dict mapping each τ to its PartitionResult.
    """
    sim = pairwise_cosine(encodings)
    out = {}
    for tau in thresholds:
        cluster_ids, boundaries = detect_clusters(sim, tau)
        out[tau] = PartitionResult(
            similarity_matrix=sim,
            cluster_ids=cluster_ids,
            boundaries=boundaries,
            threshold=float(tau),
        )
    return out


def per_ply_features(
    result: PartitionResult,
    ply_index: int,
) -> dict:
    """Compute the per-ply features required by the §11.6.3 Phase A
    schema for one ply at the given PartitionResult.

    distance_to_nearest_boundary is signed per §11.6.3:
        negative if the previous boundary (end of previous cluster) is
            nearer,
        positive if the next boundary (end of current cluster) is
            nearer,
        zero if this ply IS the boundary (last ply of its cluster).
    """
    n = result.cluster_ids.shape[0]
    if ply_index < 0 or ply_index >= n:
        raise IndexError(
            f"ply_index {ply_index} out of range [0, {n})")

    cid = int(result.cluster_ids[ply_index])
    mask = result.cluster_ids == cid
    cluster_indices = np.where(mask)[0]
    cluster_size = int(cluster_indices.size)

    # Boundary distance (signed).
    # Boundaries are ply indices that END their cluster.
    # If this ply IS a boundary, distance is 0.
    # Otherwise find the nearest prior boundary (before this ply) and
    # the next boundary (at or after this ply); report the signed
    # smaller magnitude.
    boundaries = result.boundaries
    if ply_index in boundaries:
        distance_to_nearest_boundary: int = 0
    else:
        prev_b = None
        next_b = None
        for b in boundaries:
            if b < ply_index:
                prev_b = b
            elif b >= ply_index:
                next_b = b
                break
        prev_dist = (
            ply_index - prev_b if prev_b is not None else None)
        next_dist = (
            next_b - ply_index if next_b is not None else None)

        if prev_dist is None and next_dist is None:
            # Single cluster, no boundaries at all.
            distance_to_nearest_boundary = n  # infinity sentinel
        elif prev_dist is None:
            distance_to_nearest_boundary = int(next_dist)
        elif next_dist is None:
            distance_to_nearest_boundary = -int(prev_dist)
        elif prev_dist <= next_dist:
            distance_to_nearest_boundary = -int(prev_dist)
        else:
            distance_to_nearest_boundary = int(next_dist)

    # Similarities to previous and next ply (by position in the game,
    # regardless of cluster membership).
    if ply_index > 0:
        similarity_to_previous_ply = float(
            result.similarity_matrix[ply_index, ply_index - 1])
    else:
        similarity_to_previous_ply = float("nan")
    if ply_index < n - 1:
        similarity_to_next_ply = float(
            result.similarity_matrix[ply_index, ply_index + 1])
    else:
        similarity_to_next_ply = float("nan")

    # Similarity to cluster centroid: mean cosine with every OTHER ply
    # in the same cluster. Singleton → define as 1.0.
    others = cluster_indices[cluster_indices != ply_index]
    if others.size == 0:
        similarity_to_cluster_centroid = 1.0
    else:
        similarity_to_cluster_centroid = float(
            np.mean(result.similarity_matrix[ply_index, others]))

    return {
        "cluster_id": cid,
        "cluster_size": cluster_size,
        "distance_to_nearest_boundary": distance_to_nearest_boundary,
        "similarity_to_previous_ply": similarity_to_previous_ply,
        "similarity_to_next_ply": similarity_to_next_ply,
        "similarity_to_cluster_centroid":
            similarity_to_cluster_centroid,
    }
