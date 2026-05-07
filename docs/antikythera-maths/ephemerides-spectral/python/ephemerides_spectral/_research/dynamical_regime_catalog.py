"""Sol Dynamical-Regime Classifier — query surface for the v0.24.9
ship (eigenbasis-projection version of the v0.24.x if/else chain).

Promotes the v0.24.9 architectural commitment from research notebook
section 17.7 to a stable ship surface. Replaces the hand-coded
if/else chain that selects which v0.24.x methodology to apply with a
**learned eigenbasis projection** over the 9 v0.24.0-v0.24.8
labelled training examples.

Three bridge surfaces:

* :func:`get_dynamical_regime_eigenbasis` -- the standardised
  feature matrix + its principal-component eigendecomposition.
* :func:`classify_dynamical_regime` -- given a feature vector,
  returns the nearest-neighbour regime label + distances to every
  training example + projection diagnostics.
* :func:`list_dynamical_regimes` -- full enumeration of every
  v0.24.x regime + which catalog implements it.

Cross-channel reach: same eigenbasis machinery used by v0.18.0
body_architecture (resonance-graph Fiedler partition), v0.24.5
Hawaii (Earth-surface bounded-local Fiedler), and v0.24.7 Mars
Tharsis (Mars-surface bounded-local Fiedler) -- now applied to the
**v0.24.x catalogs themselves** as labelled training examples. The
classifier is the project's first explicit *meta-consumer* of the
v0.24.x methodology arc.

Reference: research notebook section 17.7.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from .dynamical_regime_data import (
    FORCING_CLASS_GRAVITATIONAL,
    FORCING_CLASS_NAMES,
    FORCING_CLASS_RADIATION,
    FORCING_CLASS_STELLAR_OSCILLATION,
    FORCING_CLASS_TECTONIC,
    FORCING_CLASS_VOLCANIC,
    N_FEATURES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    REGIME_EXAMPLES,
    SOURCES,
    RegimeExample,
)


# ---- Feature names (column labels for the 9 x N_FEATURES matrix) ----
FEATURE_NAMES: Tuple[str, ...] = (
    "time_scale_log_s",
    "spatial_scale_log_km",
    "stability_index",
    "has_commensurability",
    "prediction_track_signal",
    "dimensionality",
    "forcing_class_index",
)


def _feature_matrix() -> np.ndarray:
    """Stack every training example's feature vector into a
    (n_examples, N_FEATURES) matrix."""
    return np.array(
        [list(e.feature_vector()) for e in REGIME_EXAMPLES],
        dtype=np.float64,
    )


def _standardise(
    X: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Centre + scale a feature matrix to mean-zero unit-variance per
    feature. Returns (X_std, mean, scale)."""
    mean = X.mean(axis=0)
    centred = X - mean
    # Use ddof=0 to match a population std; we want the basis
    # reproducible across LAPACK pivoting, not statistically optimal.
    scale = centred.std(axis=0, ddof=0)
    # Guard against zero-variance features (would produce NaN). Use
    # 1.0 in that case so the column passes through unchanged.
    safe_scale = np.where(scale > 0.0, scale, 1.0)
    standardised = centred / safe_scale
    return standardised, mean, safe_scale


def _principal_components(
    X_std: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the principal-component decomposition of a standardised
    feature matrix.

    Returns (eigenvalues_desc, eigenvectors_desc), both sorted so the
    largest-eigenvalue / largest-variance component comes first. The
    columns of ``eigenvectors_desc`` are the principal components
    (one per column).

    Sign convention: each principal component is sign-flipped to make
    its largest-magnitude entry positive. This produces a stable basis
    across LAPACK-pivoting differences.
    """
    # Covariance is (1/n) X^T X for centred X.
    n = X_std.shape[0]
    cov = (X_std.T @ X_std) / n
    eigvals, eigvecs = np.linalg.eigh(cov)
    # Sort descending by eigenvalue.
    order = np.argsort(eigvals)[::-1]
    eigvals_desc = eigvals[order]
    eigvecs_desc = eigvecs[:, order]
    # Sign convention: largest-magnitude entry of each PC is positive.
    for k in range(eigvecs_desc.shape[1]):
        col = eigvecs_desc[:, k]
        i_max = int(np.argmax(np.abs(col)))
        if col[i_max] < 0.0:
            eigvecs_desc[:, k] = -col
    return eigvals_desc, eigvecs_desc


def _project(
    feature_vector: Sequence[float],
    mean: np.ndarray,
    scale: np.ndarray,
    eigvecs: np.ndarray,
    n_components: int,
) -> np.ndarray:
    """Project a raw feature vector into the top-k eigenbasis."""
    raw = np.asarray(feature_vector, dtype=np.float64)
    centred = raw - mean
    standardised = centred / scale
    return standardised @ eigvecs[:, :n_components]


def _example_to_dict(e: RegimeExample) -> Dict[str, Any]:
    return {
        "name": e.name,
        "ship_version": e.ship_version,
        "regime_label": e.regime_label,
        "description": e.description,
        "catalog_module": e.catalog_module,
        "feature_vector": list(e.feature_vector()),
        "forcing_class_name": FORCING_CLASS_NAMES.get(
            e.forcing_class_index, "unknown",
        ),
        "notes": e.notes,
        "source_key": e.source_key,
        "precision_flag": e.precision_flag,
    }


def get_dynamical_regime_eigenbasis(
    n_components: int = 3,
) -> Dict[str, Any]:
    """The standardised feature matrix + its principal-component
    eigendecomposition.

    Parameters
    ----------
    n_components : int, default 3
        Number of top principal components to project onto. With 9
        training examples and 7 features, the matrix has at most 7
        non-trivial eigenmodes; the top 2-3 typically explain
        nearly all the variance.

    Returns
    -------
    dict
        ``{ok, n_examples, n_features, n_components,
        feature_names, eigenvalues, explained_variance_ratio,
        cumulative_explained_variance, top_components,
        training_projections: [...]}``.

        ``top_components`` is a list of ``n_components`` dicts; each
        dict has ``component_index``, ``eigenvalue``,
        ``explained_variance_ratio``, ``loadings`` (per-feature).

        ``training_projections`` is a list of ``n_examples`` dicts;
        each dict has ``name``, ``regime_label``, ``coordinates``
        (the projection into the top-k eigenbasis).
    """
    n_components = int(min(n_components, N_FEATURES))
    X = _feature_matrix()
    X_std, mean, scale = _standardise(X)
    eigvals, eigvecs = _principal_components(X_std)

    total_variance = float(eigvals.sum())
    explained_ratio = (
        eigvals / total_variance if total_variance > 0 else
        np.zeros_like(eigvals)
    )
    cumulative = np.cumsum(explained_ratio)

    top_components: List[Dict[str, Any]] = []
    for k in range(n_components):
        loadings = {
            name: float(eigvecs[i, k])
            for i, name in enumerate(FEATURE_NAMES)
        }
        top_components.append({
            "component_index": k,
            "eigenvalue": float(eigvals[k]),
            "explained_variance_ratio": float(explained_ratio[k]),
            "cumulative_explained_variance": float(cumulative[k]),
            "loadings": loadings,
        })

    # Project every training example into the top-k eigenbasis.
    training_projections: List[Dict[str, Any]] = []
    proj_matrix = X_std @ eigvecs[:, :n_components]
    for i, e in enumerate(REGIME_EXAMPLES):
        training_projections.append({
            "name": e.name,
            "ship_version": e.ship_version,
            "regime_label": e.regime_label,
            "coordinates": [float(v) for v in proj_matrix[i]],
        })

    return {
        "ok": True,
        "n_examples": len(REGIME_EXAMPLES),
        "n_features": N_FEATURES,
        "n_components": n_components,
        "feature_names": list(FEATURE_NAMES),
        "eigenvalues": [float(v) for v in eigvals],
        "explained_variance_ratio": [float(v) for v in explained_ratio],
        "cumulative_explained_variance": [
            float(v) for v in cumulative
        ],
        "top_components": top_components,
        "training_projections": training_projections,
    }


def classify_dynamical_regime(
    feature_vector: Sequence[float],
    n_components: int = 3,
) -> Dict[str, Any]:
    """Classify a feature vector against the v0.24.x training examples.

    Project the input feature vector into the top-k principal-component
    eigenbasis derived from the 9 v0.24.x training examples; return the
    nearest-neighbour regime label + distances to every training
    example.

    This is the **eigenbasis-projection version of the v0.24.x if/else
    chain** -- the original framing replaced by the v0.24.9 ship.

    Parameters
    ----------
    feature_vector : sequence of 7 floats
        Feature vector with schema ``(time_scale_log_s,
        spatial_scale_log_km, stability_index, has_commensurability,
        prediction_track_signal, dimensionality, forcing_class_index)``.
    n_components : int, default 3
        Number of top principal components to use for the projection.

    Returns
    -------
    dict
        ``{ok, n_examples, input_features, projected_coordinates,
        nearest_regime: {name, ship_version, regime_label,
        catalog_module, distance, ...}, distances_to_all: [...]}``.

    Raises
    ------
    ValueError
        If ``feature_vector`` is not exactly N_FEATURES (= 7) long.
    """
    if len(feature_vector) != N_FEATURES:
        raise ValueError(
            f"feature_vector must be length {N_FEATURES} "
            f"(got {len(feature_vector)})"
        )
    n_components = int(min(n_components, N_FEATURES))

    X = _feature_matrix()
    X_std, mean, scale = _standardise(X)
    eigvals, eigvecs = _principal_components(X_std)

    # Project the input + every training example into the top-k basis.
    input_proj = _project(
        feature_vector, mean, scale, eigvecs, n_components,
    )
    training_proj = X_std @ eigvecs[:, :n_components]

    # Euclidean distances in the embedding.
    diffs = training_proj - input_proj  # (n_examples, n_components)
    distances = np.sqrt((diffs ** 2).sum(axis=1))

    distances_list: List[Dict[str, Any]] = []
    for i, e in enumerate(REGIME_EXAMPLES):
        distances_list.append({
            "name": e.name,
            "ship_version": e.ship_version,
            "regime_label": e.regime_label,
            "distance": float(distances[i]),
            "training_coordinates": [
                float(v) for v in training_proj[i]
            ],
        })
    distances_list.sort(key=lambda d: d["distance"])

    nearest_idx = int(np.argmin(distances))
    nearest = REGIME_EXAMPLES[nearest_idx]

    return {
        "ok": True,
        "n_examples": len(REGIME_EXAMPLES),
        "n_components": n_components,
        "feature_names": list(FEATURE_NAMES),
        "input_features": [float(v) for v in feature_vector],
        "projected_coordinates": [float(v) for v in input_proj],
        "nearest_regime": {
            "name": nearest.name,
            "ship_version": nearest.ship_version,
            "regime_label": nearest.regime_label,
            "description": nearest.description,
            "catalog_module": nearest.catalog_module,
            "distance": float(distances[nearest_idx]),
        },
        "distances_to_all": distances_list,
    }


def list_dynamical_regimes() -> Dict[str, Any]:
    """Full enumeration of every labelled v0.24.x regime + citations."""
    return {
        "ok": True,
        "n_regimes": len(REGIME_EXAMPLES),
        "n_features": N_FEATURES,
        "n_sources": len(SOURCES),
        "feature_names": list(FEATURE_NAMES),
        "regimes": [_example_to_dict(e) for e in REGIME_EXAMPLES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "FEATURE_NAMES",
    "REGIME_EXAMPLES",
    "SOURCES",
    "RegimeExample",
    "get_dynamical_regime_eigenbasis",
    "classify_dynamical_regime",
    "list_dynamical_regimes",
]
