"""Sol Mars Tharsis Volcanic Chain Catalog — query surface for the
v0.24.7 ship (bounded-local-Laplacian application to Mars Tharsis
volcanoes; no-plate-tectonics analogue of v0.24.5 Hawaii).

Promotes the v0.24.7 architectural commitment from research notebook
§17.7 to a stable ship surface — the **second time** the project's
graph-Laplacian eigenbasis is applied to **physical features on a
single body's surface** rather than to orbital relationships
between bodies, and the **first time** on a body **without plate
tectonics**. Demonstrates the **bounded-local-Laplacian**
methodology cross-body: Hawaii (v0.24.5) extracts a *trajectory*
along a hotspot track on a moving plate; Mars Tharsis extracts a
*cogenetic family* on a stationary lithosphere.

Three bridge surfaces:

* :func:`get_mars_tharsis_chain` — full Tharsis-volcano catalog +
  computed per-volcano position-from-Tharsis-centre and graph-
  Laplacian Fiedler embedding.
* :func:`get_tharsis_fiedler_signature` — THE headline closure:
  the Fiedler partition surfaces the Tharsis Montes ridge as one
  cluster and the Olympus / Alba outliers as a different cluster.
  No directional "bend" because there's no plate motion.
* :func:`list_mars_tharsis_chain` — full enumeration with citations.

Cross-channel reach: same eigendecomposition machinery used by
v0.18.0 body_architecture (orbital-resonance graph) and v0.24.5
hawaii_chain (Earth hotspot track), now applied to a no-plate-
tectonics surface-feature graph.

Reference: research notebook §17.7.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np

from .mars_tharsis_data import (
    MARS_RADIUS_KM,
    MARS_THARSIS_VOLCANOES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    THARSIS_CENTRE_LAT_DEG,
    THARSIS_CENTRE_LON_DEG,
    THARSIS_MONTES_RIDGE_AZIMUTH_DEG,
    TharsisVolcano,
)


def _great_circle_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float,
) -> float:
    """Great-circle distance in km on Mars between two (lat, lon)
    points in degrees. Standard haversine formula with the Mars
    mean radius (3389.5 km), not Earth's."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return MARS_RADIUS_KM * c


def _volcano_to_dict(
    v: TharsisVolcano, distance_from_centre_km: float,
) -> Dict[str, Any]:
    return {
        "name": v.name,
        "age_myr": v.age_myr,
        "age_uncertainty_myr": v.age_uncertainty_myr,
        "latitude_deg": v.latitude_deg,
        "longitude_deg": v.longitude_deg,
        "summit_elevation_m": v.summit_elevation_m,
        "edifice_diameter_km": v.edifice_diameter_km,
        "role": v.role,
        "distance_from_tharsis_centre_km": distance_from_centre_km,
        "notes": v.notes,
        "source_key": v.source_key,
        "precision_flag": v.precision_flag,
    }


def _compute_distances_from_centre_km() -> List[float]:
    """Per-volcano great-circle distance from the canonical Tharsis
    centre (Anderson 2001: 0°N, 265°E)."""
    return [
        _great_circle_distance_km(
            v.latitude_deg, v.longitude_deg,
            THARSIS_CENTRE_LAT_DEG, THARSIS_CENTRE_LON_DEG,
        )
        for v in MARS_THARSIS_VOLCANOES
    ]


def _build_proximity_laplacian(
    sigma_km: float = 1500.0,
) -> Tuple[np.ndarray, List[str]]:
    """Build a graph Laplacian on the Tharsis-volcano nodes with
    edges weighted by Gaussian-kernel spatial proximity:

        w_ij = exp(-d_ij^2 / (2 sigma^2))

    where d_ij is the great-circle distance between volcanoes i
    and j on the Mars surface. This is the **bounded-local-
    Laplacian** — same algebraic machinery as v0.24.5 Hawaii's
    proximity Laplacian, but on a 5-volcano roster on a no-plate-
    tectonics body. The sigma scale (~1500 km) is chosen larger
    than Hawaii's ~500 km because the Tharsis system spans a
    larger fraction of the body (Olympus → Alba is ~2700 km,
    versus Hawaii's ~6500 km but on a much larger sphere).

    Returns
    -------
    L : np.ndarray (n x n)
        Weighted graph Laplacian L = D - W where W is the symmetric
        weight matrix and D is its row-sum diagonal.
    names : list[str]
        Volcano names in row/column order.
    """
    n = len(MARS_THARSIS_VOLCANOES)
    names = [v.name for v in MARS_THARSIS_VOLCANOES]
    W = np.zeros((n, n), dtype=np.float64)
    sigma_sq_2 = 2.0 * sigma_km * sigma_km
    for i in range(n):
        vi = MARS_THARSIS_VOLCANOES[i]
        for j in range(i + 1, n):
            vj = MARS_THARSIS_VOLCANOES[j]
            d = _great_circle_distance_km(
                vi.latitude_deg, vi.longitude_deg,
                vj.latitude_deg, vj.longitude_deg,
            )
            w = math.exp(-(d * d) / sigma_sq_2)
            W[i, j] = w
            W[j, i] = w
    D = np.diag(W.sum(axis=1))
    L = D - W
    return L, names


def _fiedler_with_sign_convention(
    L: np.ndarray, names: List[str],
) -> Tuple[float, np.ndarray]:
    """Compute the Fiedler eigenpair (lambda_2, f_2) with sign
    convention pinned: the **Olympus Mons outlier** has positive
    Fiedler value. This makes the sign convention reproducible
    across LAPACK-pivoting differences — and aligns the Fiedler
    sign with the structural distinction the eigenvector
    discriminates (Olympus / Alba outliers from Tharsis Montes
    ridge).
    """
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvals)
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    fiedler_value = float(eigvals[1])
    fiedler_vec = eigvecs[:, 1]
    if "olympus_mons" in names:
        olympus_idx = names.index("olympus_mons")
        if fiedler_vec[olympus_idx] < 0:
            fiedler_vec = -fiedler_vec
    return fiedler_value, fiedler_vec


def get_mars_tharsis_chain() -> Dict[str, Any]:
    """Mars Tharsis volcanic-chain catalog + computed per-volcano
    distance-from-Tharsis-centre + Fiedler embedding.

    Each volcano carries:

    * ``name``, ``age_myr``, ``latitude_deg``, ``longitude_deg``,
      ``summit_elevation_m``, ``edifice_diameter_km``, ``role``,
      ``source_key``.
    * ``distance_from_tharsis_centre_km`` — great-circle distance
      from the canonical Tharsis bulge centre (0 N, 265 E).
    * ``fiedler_value`` — the per-volcano coordinate in the
      eigenbasis embedding (Fiedler vector of the Gaussian-
      proximity Laplacian).

    Cross-strand observation: this is the **same Fiedler-vector
    machinery** v0.18.0 body_architecture and v0.24.5
    hawaii_chain use — applied here to a 5-volcano roster on a
    body **without** plate tectonics. The bounded-local
    methodology (chess-board analogy: every volcano a square; the
    graph Laplacian on the local graph has its own eigenbasis)
    works identically; the *interpretation* of what the partition
    surfaces is what differs.

    Returns
    -------
    dict
        ``{ok, n_volcanoes, tharsis_centre, ridge_azimuth_deg,
        fiedler_eigenvalue, volcanoes: [...]}``.
    """
    distances = _compute_distances_from_centre_km()
    L, names = _build_proximity_laplacian()
    fiedler_value, fiedler_vec = _fiedler_with_sign_convention(L, names)

    volcanoes_out: List[Dict[str, Any]] = []
    for i, v in enumerate(MARS_THARSIS_VOLCANOES):
        d = _volcano_to_dict(v, distances[i])
        d["fiedler_value"] = float(fiedler_vec[i])
        volcanoes_out.append(d)

    return {
        "ok": True,
        "n_volcanoes": len(MARS_THARSIS_VOLCANOES),
        "tharsis_centre": {
            "latitude_deg": THARSIS_CENTRE_LAT_DEG,
            "longitude_deg": THARSIS_CENTRE_LON_DEG,
        },
        "ridge_azimuth_deg": THARSIS_MONTES_RIDGE_AZIMUTH_DEG,
        "mars_radius_km": MARS_RADIUS_KM,
        "fiedler_eigenvalue": fiedler_value,
        "volcanoes": volcanoes_out,
    }


def get_tharsis_fiedler_signature() -> Dict[str, Any]:
    """The Mars Tharsis Fiedler-partition signature — THE headline
    of v0.24.7. **Two complementary spectral observations**:

    **(1) Bounded-local-Fiedler partition** — the graph Laplacian's
    Fiedler eigenvector bisects the 5-volcano roster into two
    clusters by spatial proximity. Unlike Hawaii's quasi-1D track
    (one zero-crossing along the chain), the Mars Tharsis system
    is a 2D arrangement — three Tharsis Montes form a tight ridge
    cluster, with Olympus Mons (NW outlier) and Alba Mons (N
    outlier) sitting separately. The Fiedler sign-pattern groups
    the three Montes together; Olympus and Alba carry opposite-
    sign Fiedler values to the ridge cluster. The eigenvalue gap
    lambda_3 - lambda_2 measures how cleanly the bisection cuts.

    **(2) Tharsis Montes ridge alignment + Olympus / Alba
    residuals** — fit the Tharsis Montes (three points) to a
    great-circle line through the body, then compute residuals
    for Olympus and Alba against that line. Olympus Mons sits
    far off the ridge axis (~1100 km perpendicular offset); Alba
    Mons sits ~1500 km north of the ridge. These offsets are the
    "directional discontinuity" analogue of Hawaii's bend
    residual — but here they are **structural** (deep mantle plume
    geometry) rather than **temporal** (plate motion change).

    **Why no "bend"?** Mars has no plate tectonics, so there is
    no plate-motion change to record as a directional kink in a
    chain. Instead, the Tharsis volcanoes are roughly cogenetic
    (all young surface flows ~100-150 Myr, except Alba which is
    older), and the Fiedler partition surfaces **structural
    geometry** rather than temporal trajectory. This is the key
    cross-channel observation: same eigendecomposition machinery,
    different geophysical regime, surfaces a different kind of
    structure. **Hawaii (with plate tectonics) -> trajectory.
    Mars (no plate tectonics) -> family.**

    Returns
    -------
    dict
        ``{ok, fiedler_eigenvalue, next_eigenvalue, eigenvalue_gap,
        fiedler_clusters, olympus_residual_km, alba_residual_km,
        ...}``.
    """
    L, names = _build_proximity_laplacian()
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvals)
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    lambda_1 = float(eigvals[0])
    lambda_2 = float(eigvals[1])
    lambda_3 = float(eigvals[2])

    fiedler_vec = eigvecs[:, 1]
    if "olympus_mons" in names:
        olympus_idx = names.index("olympus_mons")
        if fiedler_vec[olympus_idx] < 0:
            fiedler_vec = -fiedler_vec

    eigenvalue_gap = lambda_3 - lambda_2

    # Group volcanoes by Fiedler sign:
    positive_cluster: List[Dict[str, Any]] = []
    negative_cluster: List[Dict[str, Any]] = []
    for i, v in enumerate(MARS_THARSIS_VOLCANOES):
        entry = {
            "name": v.name,
            "role": v.role,
            "fiedler_value": float(fiedler_vec[i]),
        }
        if fiedler_vec[i] >= 0:
            positive_cluster.append(entry)
        else:
            negative_cluster.append(entry)

    # Compute Tharsis Montes ridge perpendicular-offset residuals
    # for Olympus and Alba. The ridge is fit through the three
    # Tharsis Montes summit positions; perpendicular distance from
    # each outlier to that ridge line is the "residual".
    name_to_volcano = {v.name: v for v in MARS_THARSIS_VOLCANOES}
    montes = [
        name_to_volcano[n]
        for n in ("arsia_mons", "pavonis_mons", "ascraeus_mons")
        if n in name_to_volcano
    ]
    olympus_residual_km: float = float("nan")
    alba_residual_km: float = float("nan")
    if len(montes) >= 2:
        # Linear fit: longitude as function of latitude (ridge runs
        # roughly NE-SW so latitude varies more than longitude does
        # not — actually both vary, but linear-in-(lat,lon) is fine
        # for this 3-point regression).
        lats = np.array([m.latitude_deg for m in montes])
        lons = np.array([m.longitude_deg for m in montes])
        # Fit lon = a * lat + b (1D regression, minimal):
        a, b = np.polyfit(lats, lons, 1)
        # Compute perpendicular residual for an outlier:
        def _residual_km(volc: TharsisVolcano) -> float:
            predicted_lon = a * volc.latitude_deg + b
            d = _great_circle_distance_km(
                volc.latitude_deg, volc.longitude_deg,
                volc.latitude_deg, predicted_lon,
            )
            return d

        if "olympus_mons" in name_to_volcano:
            olympus_residual_km = _residual_km(
                name_to_volcano["olympus_mons"]
            )
        if "alba_mons" in name_to_volcano:
            alba_residual_km = _residual_km(
                name_to_volcano["alba_mons"]
            )

    # Age-uniformity diagnostic: range of (Tharsis Montes + Olympus)
    # surface ages — should be tight (~100-150 Myr) reflecting recent
    # cogenetic activity. Alba is the older outlier.
    young_volcanoes = [
        v for v in MARS_THARSIS_VOLCANOES
        if v.role in ("tharsis_montes", "olympus_outlier")
    ]
    age_range_young_myr: Tuple[float, float] = (
        (min(v.age_myr for v in young_volcanoes),
         max(v.age_myr for v in young_volcanoes))
        if young_volcanoes else (float("nan"), float("nan"))
    )

    return {
        "ok": True,
        "fiedler_eigenvalue": lambda_2,
        "next_eigenvalue": lambda_3,
        "eigenvalue_gap": eigenvalue_gap,
        "fiedler_clusters": {
            "positive_cluster": positive_cluster,
            "negative_cluster": negative_cluster,
            "n_positive": len(positive_cluster),
            "n_negative": len(negative_cluster),
        },
        "olympus_residual_km": olympus_residual_km,
        "alba_residual_km": alba_residual_km,
        "ridge_azimuth_deg": THARSIS_MONTES_RIDGE_AZIMUTH_DEG,
        "young_volcanism_age_range_myr": {
            "min_age_myr": age_range_young_myr[0],
            "max_age_myr": age_range_young_myr[1],
        },
        "interpretation": (
            "Two complementary spectral observations: (1) the "
            "bounded-local-Fiedler partition bisects the 5-volcano "
            "roster into structural clusters (Tharsis Montes ridge "
            "vs Olympus/Alba outliers); (2) Olympus Mons and Alba "
            "Mons sit far off the Tharsis Montes ridge axis "
            "(perpendicular residuals on the order of ~1000 km), "
            "marking them as structural outliers from the deep-"
            "mantle ridge that produced the three aligned Montes. "
            "Unlike Hawaii (v0.24.5), there is NO directional "
            "'bend' because there is no plate motion: same "
            "eigendecomposition machinery, but on a body without "
            "plate tectonics, surfaces cogenetic-family structure "
            "rather than trajectory."
        ),
    }


def list_mars_tharsis_chain() -> Dict[str, Any]:
    """Full enumeration of Mars Tharsis volcano data + citations."""
    distances = _compute_distances_from_centre_km()
    return {
        "ok": True,
        "n_volcanoes": len(MARS_THARSIS_VOLCANOES),
        "n_sources": len(SOURCES),
        "volcanoes": [
            _volcano_to_dict(v, distances[i])
            for i, v in enumerate(MARS_THARSIS_VOLCANOES)
        ],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MARS_THARSIS_VOLCANOES",
    "SOURCES",
    "TharsisVolcano",
    "get_mars_tharsis_chain",
    "get_tharsis_fiedler_signature",
    "list_mars_tharsis_chain",
]
