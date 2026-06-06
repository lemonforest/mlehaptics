"""Sol Saturn Ring System Catalog — query surface for the v0.30.0 ship
(temporal-spectrum catalog of a **multi-regime body**).

Promotes the staged Saturn-ring data (the 12 hand-coded
``RingFeature`` rows + the dual-authored AMSC NDJSON at
``research/attested/saturn_rings/``) from a dual-author *parity
fixture* to a full **query surface** — the per-feature regime
partition, the integer ``(p:q)`` mean-motion **resonance closure
invariant**, and the **bounded-local-Laplacian** eigenbasis on the
radial feature graph.

Where the v0.24.x per-body dynamical-spectrum ships each decomposed
*one* body into action-angle (Mercury / Luna / Mars) or continuum
normal modes (Sun helioseismology), the Saturn ring system is a
**multi-regime** object: its 12 catalogued features partition across
four dynamically distinct regimes that the v0.24.x family met
separately —

* ``rigid_body_action_angle_stable`` — gaps + boundaries held by a
  single resonance / embedded shepherd (Cassini Division, Encke,
  Keeler, Pan, Daphnis, the Mimas anchor); the Mercury/Luna/Mars
  rigid-body regime.
* ``rigid_body_action_angle_mutual_lock`` — the A-ring outer edge,
  confined by the 7:6 resonance with the **Janus–Epimetheus
  co-orbital pair** (the v0.24.11 Pluto–Charon mutual-lock regime,
  applied to a ring edge).
* ``temporal_quasi_periodic_cycle`` — the F-ring core +
  Prometheus/Pandora shepherds, modulated on the shepherds' synodic
  beat (the v0.24.8 Axial-Seamount / v0.24.12 Loki-Patera temporal
  regime).
* ``bounded_local_laplacian_family`` — the B-ring inner / C-ring
  outer boundaries, structural edges of the dense rings read through
  the ring's own eigenmode spacing (the v0.24.5 Hawaii bounded-local
  Laplacian regime).

Three query surfaces (plus the enumeration):

* :func:`get_saturn_ring_features` — the 12 features + the regime
  partition + ring-system constants.
* :func:`get_ring_resonance_closure` — THE closure invariant: the
  integer ``(p:q)`` Lindblad commensurabilities predict the observed
  ring boundaries from the perturbing moons' semi-major axes to
  ``< 1 %``; the sub-percent residual is **bounded by the leading
  Saturn-J₂ epicyclic-frequency correction** ``(3/2) J₂ (R/a)²`` —
  the oblateness signature the staged data flagged.
* :func:`get_ring_radial_laplacian` — the bounded-local-Laplacian
  eigenbasis on the radial feature graph (the v0.24.5 Hawaii
  machinery applied to ring radii): the Fiedler vector bisects the
  ring system at its largest radial gap (the C/B inner edges vs the
  Cassini-and-outward features).
* :func:`list_saturn_ring_features` — full enumeration + citations.

Scope note (``docs/antikythera-maths/CLAUDE.md``): this is the
**algebra / eigenbasis** reading — rational ``(p:q)`` mean-motion
locks, a first-order ``J₂`` oblateness scale, and a graph-Laplacian
spectrum on the radial feature positions. It is **not** a
particle-collision / self-gravity-wake / viscous-spreading
microsimulation (that is CAD-grade ring-particle dynamics, a
different discipline).

``the_one`` cross-reference (task #524): the ``(p:q)`` resonance is
an **epicyclic commensurability** — the ``n=1`` / ℂ degenerate case
of ``srmech.amsc.cascade.the_one`` ``S(σ,θ)`` (0 Fano planes; only
the single rotation + the Class-K sign σ). The octonion machinery
of ``the_one`` does not earn its keep on a scalar ring resonance;
where it activates is the 3-co-spinning-plane ``k=3`` multipole
triad (the giant-planet field), audited separately.

Reference: research notebook §18 (Saturn rings); §17.7 (the v0.24.x
dynamical-spectrum family).
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import _cascade
from .geodetic_catalog_data import GRAVITY_MODELS
from .saturn_rings_data import (
    SATURN_RING_FEATURES,
    SOURCES,
    RingFeature,
    feature_to_data_dict,
)


# ---------------------------------------------------------------------------
# Saturn oblateness constants — reused from the in-repo Geodetic Catalog
# (own-work-primary attestation: the v0.20.0 GravityModel for Saturn
# carries the Cassini Grand Finale value, Iess et al. 2019). No new
# external source: J₂ and the reference radius are the geodetic
# catalogue's already-attested numbers, read here so the ring closure
# invariant and the geodetic catalogue can never drift apart.
# ---------------------------------------------------------------------------

_SATURN_GRAVITY = next(g for g in GRAVITY_MODELS if g.body == "saturn")

#: Saturn's unnormalised J₂ (Cassini-Iess-2019; via the Geodetic Catalog).
SATURN_J2: float = float(_SATURN_GRAVITY.J2)

#: Saturn's gravity-expansion reference radius in km (Cassini-Iess-2019).
SATURN_REFERENCE_RADIUS_KM: float = float(_SATURN_GRAVITY.reference_radius_km)


# ---------------------------------------------------------------------------
# Perturbing-moon semi-major axes — JPL SSD planetary satellite mean
# elements (ssd.jpl.nasa.gov/sats/elem; SAT441 for Mimas, SAT415 for
# the Janus–Epimetheus co-orbitals; epoch 2000-01-01.5 TDB). Cited via
# the ``jpl_ssd_sat_elements`` key in ``saturn_rings_data.SOURCES``.
# Mimas keeps the value the data module's anchor row already adopts.
# ---------------------------------------------------------------------------

MOON_SEMI_MAJOR_AXIS_KM: Dict[str, float] = {
    "mimas": 185539.0,
    "janus": 151460.0,
    "epimetheus": 151410.0,
}

#: Map a feature's ``associated_body`` to the moon whose orbit raises
#: the resonance. The A-ring's 7:6 edge is confined by the
#: Janus–Epimetheus co-orbital pair; the standard treatment uses
#: Janus's orbit (the inner member through most of the swap cycle).
_ASSOCIATED_BODY_TO_MOON: Dict[str, str] = {
    "mimas": "mimas",
    "janus_epimetheus": "janus",
}


def _feature_to_dict(f: RingFeature) -> Dict[str, Any]:
    """Render a RingFeature to its AMSC-shape dict.

    Reuses :func:`saturn_rings_data.feature_to_data_dict` so this
    catalogue and the dual-author NDJSON emit byte-identical row
    content (the dual-author diff test is the ratchet).
    """
    return feature_to_data_dict(f)


def _regime_partition() -> Dict[str, List[str]]:
    """Group the 12 features by ``regime_label`` (deterministic order)."""
    out: Dict[str, List[str]] = {}
    for f in SATURN_RING_FEATURES:
        label = f.regime_label or "unclassified"
        out.setdefault(label, []).append(f.name)
    return {label: out[label] for label in sorted(out)}


def _predicted_resonance_radius_km(a_moon_km: float, p: int, q: int) -> float:
    """Naïve-Kepler location of an interior ``p:q`` mean-motion
    resonance with a moon of semi-major axis ``a_moon_km``.

    A ring particle at the ``p:q`` inner Lindblad resonance orbits ``p``
    times for every ``q`` moon orbits, so its mean motion is ``(p/q)``
    the moon's and (Kepler's third law, ``n ∝ a^{-3/2}``) its
    semi-major axis is

        a_res = a_moon · (q/p)^(2/3).

    This is the point-mass commensurability (Murray & Dermott 1999
    §8.6); Saturn's oblateness shifts it by the J₂ term surfaced in
    :func:`get_ring_resonance_closure`. The ``(q/p)^(2/3)`` power is the
    Class-N exp∘log cascade (:func:`_cascade.pow_frac`), not ``**``.
    """
    return a_moon_km * _cascade.pow_frac(q, p, 2, 3)


def _j2_frequency_correction(a_km: float) -> float:
    """Leading fractional J₂ epicyclic-frequency correction
    ``(3/2) J₂ (R/a)²`` at orbital radius ``a_km`` — the dimensionless
    scale of Saturn's oblateness perturbation to the radial epicyclic
    frequency (and hence to the Lindblad-resonance location) at that
    radius. The residual of the naïve-Kepler prediction is bounded by
    this scale.
    """
    ratio = SATURN_REFERENCE_RADIUS_KM / a_km
    return 1.5 * SATURN_J2 * ratio * ratio


def get_saturn_ring_features() -> Dict[str, Any]:
    """The Saturn ring system catalogue — 12 features + the regime
    partition + ring-system constants.

    The **multi-regime** headline of v0.30.0: where each v0.24.x
    per-body ship decomposed one body into a single dynamical regime,
    Saturn's rings span four — every feature carries a ``regime_label``
    naming which v0.24.x regime it instantiates (rigid-body action-angle
    stable / mutual-lock / temporal quasi-periodic / bounded-local
    Laplacian).

    Returns
    -------
    dict
        ``{ok, body, n_features, n_regimes, regimes, features,
        constants}`` — ``regimes`` maps each regime label to its member
        feature names; ``features`` is the full AMSC-shape roster.
    """
    regimes = _regime_partition()
    return {
        "ok": True,
        "body": "saturn",
        "subject": "ring_system",
        "n_features": len(SATURN_RING_FEATURES),
        "n_regimes": len(regimes),
        "regimes": regimes,
        "features": [_feature_to_dict(f) for f in SATURN_RING_FEATURES],
        "constants": {
            "saturn_j2": SATURN_J2,
            "saturn_reference_radius_km": SATURN_REFERENCE_RADIUS_KM,
            "moon_semi_major_axis_km": dict(MOON_SEMI_MAJOR_AXIS_KM),
        },
    }


def get_ring_resonance_closure() -> Dict[str, Any]:
    """The ``(p:q)`` mean-motion resonance closure invariant — THE
    headline of v0.30.0.

    For every ring **boundary** held by an integer ``p:q`` Lindblad
    resonance with a moon of known semi-major axis, compute the
    naïve-Kepler resonance location ``a_moon · (q/p)^(2/3)`` and compare
    it to the observed boundary radius. Two such boundaries are
    catalogued:

    * Cassini Division inner edge — 2:1 with **Mimas**.
    * A-ring outer edge — 7:6 with the **Janus–Epimetheus** pair.

    The integer commensurabilities predict the observed architecture to
    ``< 1 %``. The sub-percent residual is **bounded by the leading
    Saturn-J₂ epicyclic-frequency correction** ``(3/2) J₂ (R/a)²`` at
    each radius — i.e. the residual is the oblateness signature, not a
    failure of the resonance model. This is the ring-system analogue of
    Luna's Saros integer triple and the Sun's Tassoul asymptotic
    relation: small integers + one physical correction reproduce the
    structure.

    The ``Mimas 2:1`` *resonance anchor* row stores a literature
    predicted location; its cross-check (the catalogue's fresh
    ``(q/p)^(2/3)`` computation vs the stored value) agrees to
    ``< 0.1 %``.

    Returns
    -------
    dict
        ``{ok, body, n_resonances, max_residual_pct, resonances,
        anchor_cross_check, interpretation}``.
    """
    resonances: List[Dict[str, Any]] = []
    anchor_cross_check: Dict[str, Any] = {}
    max_residual_pct = 0.0

    for f in SATURN_RING_FEATURES:
        if f.resonance_p is None or f.resonance_q is None:
            continue
        moon_key = _ASSOCIATED_BODY_TO_MOON.get(f.associated_body or "")
        if moon_key is None or moon_key not in MOON_SEMI_MAJOR_AXIS_KM:
            continue
        a_moon = MOON_SEMI_MAJOR_AXIS_KM[moon_key]
        predicted = _predicted_resonance_radius_km(
            a_moon, f.resonance_p, f.resonance_q,
        )

        if f.feature_type == "resonance_anchor":
            # The row's own radius is itself a literature predicted
            # location — cross-check our fresh computation against it.
            stored = f.radial_distance_km
            diff = stored - predicted
            anchor_cross_check = {
                "name": f.name,
                "moon": moon_key,
                "resonance": f"{f.resonance_p}:{f.resonance_q}",
                "computed_radius_km": predicted,
                "stored_radius_km": stored,
                "difference_km": diff,
                "difference_pct": 100.0 * abs(diff) / stored,
            }
            continue

        observed = f.radial_distance_km
        residual = observed - predicted
        residual_pct = 100.0 * abs(residual) / observed
        j2_scale_pct = 100.0 * _j2_frequency_correction(observed)
        max_residual_pct = max(max_residual_pct, residual_pct)
        resonances.append({
            "name": f.name,
            "feature_type": f.feature_type,
            "moon": moon_key,
            "resonance": f"{f.resonance_p}:{f.resonance_q}",
            "moon_semi_major_axis_km": a_moon,
            "predicted_radius_km": predicted,
            "observed_radius_km": observed,
            "residual_km": residual,
            "residual_pct": residual_pct,
            "j2_frequency_correction_pct": j2_scale_pct,
            "residual_within_j2_scale": residual_pct < j2_scale_pct,
        })

    return {
        "ok": True,
        "body": "saturn",
        "n_resonances": len(resonances),
        "max_residual_pct": max_residual_pct,
        "resonances": resonances,
        "anchor_cross_check": anchor_cross_check,
        "interpretation": (
            "Integer (p:q) inner-Lindblad commensurabilities predict the "
            "observed Saturn ring boundaries from the perturbing moons' "
            "semi-major axes to < 1%. The sub-percent residual is bounded "
            "by the leading Saturn-J2 epicyclic-frequency correction "
            "(3/2) J2 (R/a)^2 at each radius — the oblateness signature, "
            "not a failure of the resonance model. Small integers + one "
            "physical correction reproduce the architecture (the "
            "ring-system analogue of Luna's Saros triple and the Sun's "
            "Tassoul asymptotic relation)."
        ),
    }


# ---------------------------------------------------------------------------
# Bounded-local-Laplacian on the radial feature graph (v0.24.5 Hawaii
# machinery applied to ring radii). The Gaussian-proximity Laplacian
# build + eigendecomposition route through the Class-L cascade helper
# (srmech.amsc.laplacian, via _cascade.gaussian_proximity_eigs) — no raw
# numpy eigh.
# ---------------------------------------------------------------------------


def _largest_radial_gap() -> Dict[str, Any]:
    """The largest consecutive radial gap in the ring feature roster —
    the spatial seam the Fiedler vector bisects at."""
    ordered = sorted(SATURN_RING_FEATURES, key=lambda f: f.radial_distance_km)
    best_gap = -1.0
    best: Dict[str, Any] = {}
    for inner, outer in zip(ordered[:-1], ordered[1:]):
        gap = outer.radial_distance_km - inner.radial_distance_km
        if gap > best_gap:
            best_gap = gap
            best = {
                "between": [inner.name, outer.name],
                "gap_km": gap,
                "inner_radius_km": inner.radial_distance_km,
                "outer_radius_km": outer.radial_distance_km,
            }
    return best


def get_ring_radial_laplacian() -> Dict[str, Any]:
    """Bounded-local-Laplacian eigenbasis on the radial feature graph.

    Builds the Gaussian-proximity graph Laplacian on the 12 features
    ordered by radial distance and reads its Fiedler eigenpair. For a
    quasi-1D feature chain the Fiedler vector is roughly monotonic with
    a single sign change, bisecting the ring system at its **largest
    radial gap** — the ~25 000 km seam between the C/B-ring inner edges
    (~92 000 km) and the Cassini Division and everything outward
    (≥ ~117 000 km). The eigenvalue gap ``λ₃ − λ₂`` measures how cleanly
    the bisection cuts.

    Same machinery as v0.18.0 body_architecture (orbital-resonance
    graph) and v0.24.5 Hawaii (hotspot trail), here on ring radii —
    the project's eigenbasis applied to a single body's ring structure.

    Returns
    -------
    dict
        ``{ok, body, n_features, sigma_km, fiedler_eigenvalue,
        next_eigenvalue, eigenvalue_gap, fiedler_partition,
        n_sign_changes, largest_radial_gap, features}``.
    """
    sigma_km = 10000.0
    ordered = sorted(SATURN_RING_FEATURES, key=lambda f: f.radial_distance_km)
    radii = [f.radial_distance_km for f in ordered]
    names = [f.name for f in ordered]
    # Class-L build + eigendecompose via the cascade helper
    # (srmech.amsc.laplacian.dense_laplacian + symmetric_eigendecompose);
    # eigvals ascending, V columns the eigenvectors.
    eigvals, eigvecs = _cascade.gaussian_proximity_eigs(radii, sigma_km)
    lambda_2 = float(eigvals[1])
    lambda_3 = float(eigvals[2])
    fiedler = eigvecs[:, 1]
    # Sign convention (Class-C reorient): pin the innermost feature
    # (smallest radius, first in the radial ordering) to a non-negative
    # Fiedler value, so the partition is reproducible across pivoting.
    if fiedler[0] < 0:
        fiedler = -fiedler

    # Walk the radial ordering and count sign changes (expect ~1 for a
    # quasi-1D chain). Group features into the two Fiedler clusters.
    inner_group: List[str] = []
    outer_group: List[str] = []
    sign_changes = 0
    for i, name in enumerate(names):
        if fiedler[i] >= 0:
            inner_group.append(name)
        else:
            outer_group.append(name)
        if i > 0 and (fiedler[i] * fiedler[i - 1]) < 0:
            sign_changes += 1

    features_out = [
        {
            "name": names[i],
            "radial_distance_km": radii[i],
            "fiedler_value": float(fiedler[i]),
        }
        for i in range(len(names))
    ]

    return {
        "ok": True,
        "body": "saturn",
        "n_features": len(SATURN_RING_FEATURES),
        "sigma_km": sigma_km,
        "fiedler_eigenvalue": lambda_2,
        "next_eigenvalue": lambda_3,
        "eigenvalue_gap": lambda_3 - lambda_2,
        "fiedler_partition": {
            "inner": inner_group,
            "outer": outer_group,
        },
        "n_sign_changes": sign_changes,
        "largest_radial_gap": _largest_radial_gap(),
        "features": features_out,
    }


def list_saturn_ring_features() -> Dict[str, Any]:
    """Full enumeration of Saturn ring-system features + citations."""
    return {
        "ok": True,
        "body": "saturn",
        "n_features": len(SATURN_RING_FEATURES),
        "n_sources": len(SOURCES),
        "features": [_feature_to_dict(f) for f in SATURN_RING_FEATURES],
    }


__all__ = [
    "SATURN_J2",
    "SATURN_REFERENCE_RADIUS_KM",
    "MOON_SEMI_MAJOR_AXIS_KM",
    "SATURN_RING_FEATURES",
    "SOURCES",
    "RingFeature",
    "get_saturn_ring_features",
    "get_ring_resonance_closure",
    "get_ring_radial_laplacian",
    "list_saturn_ring_features",
]
