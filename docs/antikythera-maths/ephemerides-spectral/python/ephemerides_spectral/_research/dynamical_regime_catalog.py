"""Sol Dynamical-Regime Classifier — query surface for the v0.24.9
ship (eigenbasis-projection version of the v0.24.x if/else chain).

Promotes the v0.24.9 architectural commitment from research notebook
section 17.7 to a stable ship surface. Replaces the hand-coded
if/else chain that selects which v0.24.x methodology to apply with a
**learned eigenbasis projection** over the 9 v0.24.0-v0.24.8
labelled training examples.

This is **NOT machine learning** in the SGD sense
-----------------------------------------------------
The classifier looks like nearest-neighbour ML on the surface, but
the "training step" is a single closed-form symmetric eigendecomposition
of the standardised covariance matrix — routed through the **Class-L
srmech Jacobi solver** (``_cascade.symmetric_eigh``) since v0.30.0rc6,
bit-identical to the ``np.linalg.eigh`` it replaced. There is **no random
initialisation, no stochastic gradient descent, no hyperparameter
search, no validation split, no pseudorandom anywhere**. The
eigenbasis is a *property* of the labelled data, not a model fit
to it; identical inputs yield byte-identical bases across runs.
This is the spectral-methods discipline at work: classical math,
deterministic decomposition, exposed eigenstructure. The v0.24.10
calibration-ratio metric and OOS probe roster are likewise
deterministic — out-of-sample probes are *test vectors*, never
*training data*.

Bridge surfaces (v0.24.9 + v0.24.10 additions)
----------------------------------------------

* :func:`get_dynamical_regime_eigenbasis` -- the standardised
  feature matrix + its principal-component eigendecomposition.
* :func:`classify_dynamical_regime` -- given a feature vector,
  returns the nearest-neighbour regime label + distances to every
  training example + projection diagnostics + (v0.24.10) the
  calibration ratio and out-of-distribution flag.
* :func:`list_dynamical_regimes` -- full enumeration of every
  v0.24.x regime + which catalog implements it.
* :func:`run_dynamical_regime_probes` -- (v0.24.10) run every
  curated OOS probe through the classifier; return a results table
  with calibration ratios + OOD flags + match-vs-expected status.

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

from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import _cascade
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
from .dynamical_regime_probes_data import (
    OOD_CALIBRATION_RATIO_THRESHOLD,
    REGIME_PROBES,
    SOURCES as PROBE_SOURCES,
    RegimeProbe,
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


def _is_finite(x: float) -> bool:
    """``math.isfinite`` without importing ``math`` — ``True`` unless
    ``x`` is ``±inf`` or ``NaN`` (this module is numpy-free / math-free;
    its only continuous-math routes through :mod:`_cascade`)."""
    return x == x and float("-inf") < x < float("inf")


def _feature_matrix() -> List[List[float]]:
    """Stack every training example's feature vector into a
    (n_examples, N_FEATURES) row-major matrix (list of rows)."""
    return [list(e.feature_vector()) for e in REGIME_EXAMPLES]


def _standardise(
    X: Sequence[Sequence[float]],
) -> Tuple[List[List[float]], List[float], List[float]]:
    """Centre + scale a feature matrix to mean-zero unit-variance per
    feature. Returns ``(X_std, mean, scale)`` as plain Python lists.

    The per-feature ``scale`` is the **population** std (ddof = 0):
    ``√(mean of squared deviations)``, with the square root taken via the
    Class-N cascade (:func:`_cascade.sqrt`), not ``numpy`` — we want the
    basis reproducible, not statistically optimal.
    """
    n = len(X)
    d = len(X[0])
    mean = [sum(X[k][j] for k in range(n)) / n for j in range(d)]
    centred = [[X[k][j] - mean[j] for j in range(d)] for k in range(n)]
    var = [sum(centred[k][j] ** 2 for k in range(n)) / n for j in range(d)]
    # Guard against zero-variance features (would divide by zero). Use
    # scale 1.0 there so the column passes through unchanged. Class-N sqrt.
    scale = [_cascade.sqrt(v) if v > 0.0 else 1.0 for v in var]
    standardised = [
        [centred[k][j] / scale[j] for j in range(d)] for k in range(n)
    ]
    return standardised, mean, scale


def _principal_components(
    X_std: Sequence[Sequence[float]],
) -> Tuple[List[float], List[List[float]]]:
    """Principal-component decomposition of a standardised feature matrix.

    The classifier's single "training step" — a closed-form symmetric
    eigendecomposition of the standardised covariance — now routes through
    the **Class-L srmech Jacobi solver** (:func:`_cascade.symmetric_eigh`),
    not ``np.linalg.eigh``. On this small, well-conditioned covariance the
    two are bit-identical (verified: ``max |Δ eigenvalue| = 0``).

    Returns ``(eigenvalues_desc, eigenvectors_desc)``, sorted so the
    largest-variance component comes first. ``eigenvectors_desc[k]`` is
    principal component ``k`` (a length-``d`` list).

    Sign convention: each PC is sign-flipped (Class C orientation) so its
    largest-magnitude entry is positive — a stable basis across solver
    pivoting. The pivot is found by comparing squared entries (no
    ``abs()`` — magnitude lives in the square, per the cascade-honesty
    discipline).
    """
    n = len(X_std)
    d = len(X_std[0])
    # Covariance is (1/n) Xᵀ X for centred X.
    cov = [
        [sum(X_std[k][i] * X_std[k][j] for k in range(n)) / n
         for j in range(d)]
        for i in range(d)
    ]
    eigvals, eigvecs_cols = _cascade.symmetric_eigh(cov)  # ascending
    # Sort descending by eigenvalue.
    order = sorted(range(d), key=lambda i: eigvals[i], reverse=True)
    eigvals_desc = [eigvals[i] for i in order]
    eigvecs_desc = [eigvecs_cols[i] for i in order]
    # Sign convention: largest-magnitude entry of each PC is positive.
    for k in range(d):
        col = eigvecs_desc[k]
        i_max = max(range(d), key=lambda r: col[r] * col[r])
        if col[i_max] < 0.0:
            eigvecs_desc[k] = [-x for x in col]
    return eigvals_desc, eigvecs_desc


def _standardise_vector(
    feature_vector: Sequence[float],
    mean: Sequence[float],
    scale: Sequence[float],
) -> List[float]:
    """Centre + scale a single raw feature vector against a fitted basis."""
    return [(feature_vector[j] - mean[j]) / scale[j] for j in range(len(mean))]


def _project(
    feature_vector: Sequence[float],
    mean: Sequence[float],
    scale: Sequence[float],
    eigvecs: Sequence[Sequence[float]],
    n_components: int,
) -> List[float]:
    """Project a raw feature vector into the top-k eigenbasis.

    ``eigvecs`` is a list of columns (``eigvecs[k]`` = PC ``k``); the
    coordinate on PC ``k`` is the dot product of the standardised vector
    with that component.
    """
    std = _standardise_vector(feature_vector, mean, scale)
    d = len(std)
    return [
        sum(std[i] * eigvecs[k][i] for i in range(d))
        for k in range(n_components)
    ]


def _project_rows(
    X_std: Sequence[Sequence[float]],
    eigvecs: Sequence[Sequence[float]],
    n_components: int,
) -> List[List[float]]:
    """Project every standardised training row into the top-k eigenbasis."""
    d = len(X_std[0])
    return [
        [sum(row[i] * eigvecs[k][i] for i in range(d))
         for k in range(n_components)]
        for row in X_std
    ]


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

    total_variance = sum(eigvals)
    explained_ratio = (
        [v / total_variance for v in eigvals] if total_variance > 0 else
        [0.0 for _ in eigvals]
    )
    cumulative: List[float] = []
    running = 0.0
    for r in explained_ratio:
        running += r
        cumulative.append(running)

    top_components: List[Dict[str, Any]] = []
    for k in range(n_components):
        loadings = {
            name: float(eigvecs[k][i])
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
    proj_matrix = _project_rows(X_std, eigvecs, n_components)
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
    ood_threshold: float = OOD_CALIBRATION_RATIO_THRESHOLD,
) -> Dict[str, Any]:
    """Classify a feature vector against the v0.24.x training examples.

    Project the input feature vector into the top-k principal-component
    eigenbasis derived from the 9 v0.24.x training examples; return the
    nearest-neighbour regime label + distances to every training
    example + (v0.24.10) the calibration-ratio metric and out-of-
    distribution flag.

    This is the **eigenbasis-projection version of the v0.24.x if/else
    chain** -- the original framing replaced by the v0.24.9 ship.

    The v0.24.10 additions
    ----------------------
    * ``calibration_ratio`` = nearest_distance / 2nd_nearest_distance.
      Small (~0 for self-classification of training examples; < 0.5
      for confident in-distribution probes like Yellowstone or
      K-dwarf) means the classifier has a clear winner. Near 1 means
      the 1st-nearest and 2nd-nearest are essentially tied and the
      classifier is honestly saying "I don't know" (e.g., Vesta sits
      in feature-space terrain with no close training analog and
      gives ratio ~ 0.98).

    * ``nearest_neighbour_margin`` = 2nd_nearest_distance - nearest_distance.
      The absolute version of the same signal (in eigenbasis units).
      Larger margin = more confident.

    * ``out_of_distribution`` = ``calibration_ratio > ood_threshold``.
      The diagnostic was latent in ``distances_to_all`` from v0.24.9;
      v0.24.10 surfaces it as a first-class field.

    Parameters
    ----------
    feature_vector : sequence of 7 floats
        Feature vector with schema ``(time_scale_log_s,
        spatial_scale_log_km, stability_index, has_commensurability,
        prediction_track_signal, dimensionality, forcing_class_index)``.
    n_components : int, default 3
        Number of top principal components to use for the projection.
    ood_threshold : float, default OOD_CALIBRATION_RATIO_THRESHOLD (0.85)
        Calibration-ratio cutoff above which the input is flagged
        out-of-distribution. Empirically calibrated; see
        ``dynamical_regime_probes_data`` module docstring.

    Returns
    -------
    dict
        ``{ok, n_examples, input_features, projected_coordinates,
        nearest_regime: {...}, distances_to_all: [...],
        calibration_ratio, nearest_neighbour_margin,
        out_of_distribution, ood_threshold_used}``.

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
    training_proj = _project_rows(X_std, eigvecs, n_components)

    # Euclidean distances in the embedding (Class-N cascade sqrt).
    distances = [
        _cascade.sqrt(sum(
            (training_proj[i][c] - input_proj[c]) ** 2
            for c in range(n_components)
        ))
        for i in range(len(REGIME_EXAMPLES))
    ]

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

    nearest_idx = min(range(len(distances)), key=lambda i: distances[i])
    nearest = REGIME_EXAMPLES[nearest_idx]

    # --- v0.24.10: calibration-ratio metric ---
    nearest_distance = float(distances_list[0]["distance"])
    second_nearest_distance: float
    if len(distances_list) >= 2:
        second_nearest_distance = float(distances_list[1]["distance"])
    else:
        second_nearest_distance = float("inf")

    if second_nearest_distance > 0.0 and _is_finite(second_nearest_distance):
        calibration_ratio = nearest_distance / second_nearest_distance
    elif nearest_distance == 0.0:
        # Both zero — degenerate case; treat as confident match.
        calibration_ratio = 0.0
    else:
        calibration_ratio = float("inf")

    nearest_neighbour_margin = (
        second_nearest_distance - nearest_distance
        if _is_finite(second_nearest_distance) else float("inf")
    )

    out_of_distribution = bool(calibration_ratio > ood_threshold)

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
        # v0.24.10 calibration-metric additions
        "calibration_ratio": float(calibration_ratio),
        "nearest_neighbour_margin": float(nearest_neighbour_margin),
        "out_of_distribution": out_of_distribution,
        "ood_threshold_used": float(ood_threshold),
    }


# ---------------------------------------------------------------------------
# v0.24.10 — OOS probe roster runner
# ---------------------------------------------------------------------------


def _probe_to_dict(p: RegimeProbe) -> Dict[str, Any]:
    return {
        "name": p.name,
        "description": p.description,
        "feature_vector": list(p.feature_vector()),
        "expected_regime": p.expected_regime,
        "ood_expected": p.ood_expected,
        "notes": p.notes,
        "source_key": p.source_key,
        "precision_flag": p.precision_flag,
    }


def run_dynamical_regime_probes(
    n_components: int = 3,
    ood_threshold: float = OOD_CALIBRATION_RATIO_THRESHOLD,
) -> Dict[str, Any]:
    """Run every curated OOS probe through the v0.24.9 classifier.

    For each probe, project its feature vector into the top-k
    eigenbasis, classify against the v0.24.0-v0.24.8 training set,
    and record the nearest regime + calibration ratio + match-vs-
    expected status. Returns a results table suitable for
    ratchet-pinning the classifier's behaviour on real bodies.

    The probes are **not training data** -- they're test vectors. The
    classifier's eigenbasis is computed only from the 9 training
    examples in :data:`REGIME_EXAMPLES`; probes are projected into
    that basis without ever altering it.

    Parameters
    ----------
    n_components : int, default 3
        Number of top PCs to use for projection (matches the
        :func:`classify_dynamical_regime` default).
    ood_threshold : float, default OOD_CALIBRATION_RATIO_THRESHOLD (0.85)
        Calibration-ratio cutoff for OOD flagging.

    Returns
    -------
    dict
        ``{ok, n_probes, n_components, ood_threshold,
        probes: [...], summary: {...}}``.

        Each entry in ``probes`` carries the probe's identity +
        feature vector + expected regime/OOD status + the
        classifier's actual output (nearest regime, calibration
        ratio, OOD flag, match-vs-expected booleans).

        ``summary`` aggregates: ``n_matches_expected``,
        ``n_correctly_flagged_ood``, ``n_unexpected_classifications``.
    """
    probe_results: List[Dict[str, Any]] = []
    n_matches = 0
    n_correct_ood = 0
    n_unexpected = 0

    for p in REGIME_PROBES:
        result = classify_dynamical_regime(
            feature_vector=p.feature_vector(),
            n_components=n_components,
            ood_threshold=ood_threshold,
        )
        classified_regime = result["nearest_regime"]["regime_label"]
        classified_name = result["nearest_regime"]["name"]
        cal_ratio = result["calibration_ratio"]
        ood_flag = result["out_of_distribution"]

        # Match-vs-expected logic: a probe matches its expectation if
        #   - expected_regime is set AND classifier returns it AND not OOD; OR
        #   - ood_expected is True AND classifier flags out_of_distribution.
        # Probes with expected_regime=None and ood_expected=False are
        # "let classifier surprise us" cases -- they ratchet the current
        # behaviour but don't have a pass/fail expectation.
        matches_expected: Optional[bool] = None
        if p.expected_regime is not None and not p.ood_expected:
            matches_expected = (
                classified_regime == p.expected_regime
                and not ood_flag
            )
            if matches_expected:
                n_matches += 1
            else:
                n_unexpected += 1
        elif p.ood_expected:
            matches_expected = bool(ood_flag)
            if matches_expected:
                n_correct_ood += 1
            else:
                n_unexpected += 1

        probe_results.append({
            "name": p.name,
            "description": p.description,
            "expected_regime": p.expected_regime,
            "ood_expected": p.ood_expected,
            "classified_regime": classified_regime,
            "classified_training_example": classified_name,
            "matches_expected": matches_expected,
            "calibration_ratio": cal_ratio,
            "out_of_distribution": ood_flag,
            "nearest_distance": result["nearest_regime"]["distance"],
            "second_nearest_distance": (
                result["distances_to_all"][1]["distance"]
                if len(result["distances_to_all"]) >= 2 else None
            ),
            "second_nearest_regime": (
                result["distances_to_all"][1]["regime_label"]
                if len(result["distances_to_all"]) >= 2 else None
            ),
            "feature_vector": list(p.feature_vector()),
            "source_key": p.source_key,
        })

    return {
        "ok": True,
        "n_probes": len(REGIME_PROBES),
        "n_components": n_components,
        "ood_threshold": float(ood_threshold),
        "probes": probe_results,
        "summary": {
            "n_matches_expected": n_matches,
            "n_correctly_flagged_ood": n_correct_ood,
            "n_unexpected_classifications": n_unexpected,
        },
    }


def list_dynamical_regime_probes() -> Dict[str, Any]:
    """Full enumeration of every OOS probe + citations.

    Pure data-side enumerator (does NOT run the classifier). Useful
    for inspecting the curated probe roster without paying the
    eigendecomposition cost.
    """
    return {
        "ok": True,
        "n_probes": len(REGIME_PROBES),
        "n_sources": len(PROBE_SOURCES),
        "ood_threshold": OOD_CALIBRATION_RATIO_THRESHOLD,
        "probes": [_probe_to_dict(p) for p in REGIME_PROBES],
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
    "REGIME_PROBES",
    "OOD_CALIBRATION_RATIO_THRESHOLD",
    "SOURCES",
    "PROBE_SOURCES",
    "RegimeExample",
    "RegimeProbe",
    "get_dynamical_regime_eigenbasis",
    "classify_dynamical_regime",
    "list_dynamical_regimes",
    "run_dynamical_regime_probes",
    "list_dynamical_regime_probes",
]
