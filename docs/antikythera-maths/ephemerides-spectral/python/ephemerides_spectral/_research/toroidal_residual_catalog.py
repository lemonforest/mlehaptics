"""Sol Toroidal-Residual Catalog — query surface for the v0.24.4 ship
(per-body classification on the Chandrasekhar 1969 ellipsoidal-
equilibrium sequence).

Promotes the v0.24.4 architectural commitment from research notebook
§17.7 to a stable ship surface — the explicit codification of the
**rotation-makes-the-torus / self-gravity-rounds-it** insight.

Where v0.24.0 / v0.24.1 / v0.24.2 / v0.24.3 each shipped a body's
**dynamical** spectrum (action-angle modes, secular frequencies,
helioseismic modes), v0.24.4 ships a body's **shape spectrum** —
the deviation from a perfect sphere, captured quantitatively by the
J₂ gravitational quadrupole coefficient interpreted as a position
on the Maclaurin → Jacobi → bar → ring/torus equilibrium sequence.

Three bridge surfaces:

* :func:`get_toroidal_residual` — per-body shape classification.
* :func:`get_chandrasekhar_sequence_thresholds` — bifurcation
  threshold constants in the rotation parameter q.
* :func:`list_toroidal_residuals` — full catalog enumeration.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .toroidal_residual_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    Q_JACOBI_BAR_INSTABILITY,
    Q_MACLAURIN_JACOBI_BIFURCATION,
    Q_ROCHE_FISSION,
    SOURCES,
    TOROIDAL_RESIDUALS,
    ToroidalResidual,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, ToroidalResidual] = {
    t.body: t for t in TOROIDAL_RESIDUALS
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(t: ToroidalResidual) -> Dict[str, Any]:
    return {
        "body": t.body,
        "rotation_period_days": t.rotation_period_days,
        "equatorial_radius_km": t.equatorial_radius_km,
        "GM_m3_s2": t.GM_m3_s2,
        "rotation_parameter_q": t.rotation_parameter_q,
        "J2_observed": t.J2_observed,
        "moment_of_inertia_factor": t.moment_of_inertia_factor,
        "regime": t.regime,
        "fossil_figure": t.fossil_figure,
        "notes": t.notes,
        "source_key": t.source_key,
        "precision_flag": t.precision_flag,
    }


def get_toroidal_residual(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body classification on the Chandrasekhar ellipsoidal-
    equilibrium sequence.

    Each body's quantitative position on the **Maclaurin → Jacobi →
    bar → ring/torus** equilibrium sequence:

    * **q = ω²R³/(GM)** — dimensionless rotation parameter; the
      ratio of centrifugal acceleration at the equator to gravity.
      Drives the body along the equilibrium sequence as q increases.
    * **J₂_observed** — measured gravitational quadrupole (v0.20.0
      geodetic catalog reference value).
    * **moment-of-inertia factor C/MR²** — interior-density
      concentration; uniform density I_M = 2/5; centrally
      concentrated I_M < 2/5.
    * **regime** — `"sphere"` / `"maclaurin"` / `"jacobi"` /
      `"bar"` / `"ring"` based on q vs the bifurcation thresholds.
    * **fossil_figure** — `True` for bodies whose observed J₂ much
      exceeds rotation-equilibrium prediction (Luna, Mercury); their
      shape was set by historical rotation, not present rotation.

    Headlines:
      * **Saturn closest to Maclaurin-Jacobi bifurcation** — q ≈ 0.155
        vs threshold q = 0.187. Most oblate Solar-System body.
      * **Earth canonical Maclaurin** — q ≈ 0.0035, J₂ ≈ q/3 (matches
        Darwin-Radau for I_M = 0.33).
      * **Luna fossil figure** — observed J₂ ≈ 25× current-rotation
        prediction. Shape frozen when Luna was closer to Earth.
      * **Mercury fossil figure** — J₂ ≈ 50× current 3:2-locked
        rotation prediction. Shape from earlier faster-rotation
        epoch.
      * **Venus essentially spherical** — q ~ 10⁻⁷. The slow
        retrograde rotator's figure is dominated by self-gravity to
        an extreme degree.

    Cross-channel: this is the **shape-side counterpart** to the
    v0.24.0-v0.24.3 dynamical-spectrum surfaces. Together they
    decompose a body's complete state-vector: dynamical (mode
    frequencies) + shape (rotation-residual quadrupole).

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, residual: {...}}``.
        Full roster: ``{ok, n_bodies, regime_distribution, bodies}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Toroidal-Residual "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "residual": _to_dict(_BY_BODY[name]),
        }

    # Roster summary
    by_regime: Dict[str, List[str]] = {}
    for t in TOROIDAL_RESIDUALS:
        by_regime.setdefault(t.regime, []).append(t.body)

    bodies = {name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES}
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "regime_distribution": {
            regime: sorted(bs) for regime, bs in by_regime.items()
        },
        "bodies": bodies,
    }


def get_chandrasekhar_sequence_thresholds() -> Dict[str, Any]:
    """Chandrasekhar 1969 ellipsoidal-equilibrium sequence
    bifurcation thresholds — the constants that classify the regimes.

    The sequence: Sphere → Maclaurin → Jacobi → bar → ring/torus.

    Threshold values in the dimensionless rotation parameter q:

    * **q < 0.001**: effectively spherical (centrifugal force
      negligible)
    * **0.001 ≤ q < 0.187**: Maclaurin oblate spheroid (axially
      symmetric)
    * **q = 0.187**: Maclaurin-Jacobi bifurcation (Maclaurin
      sequence becomes secularly unstable)
    * **0.187 ≤ q < 0.27**: Jacobi triaxial ellipsoid (a ≠ b ≠ c)
    * **q = 0.27**: bar instability (Jacobi sequence becomes
      dynamically unstable)
    * **0.27 ≤ q < 0.36**: bar
    * **q = 0.36**: Roche / fission (matter at equator unbinds)
    * **q ≥ 0.36**: ring/torus (the body literally fissions)

    The user's insight in the notebook: **rotation forces the body
    toward the toroidal end of this sequence; self-gravity restores
    it toward the spherical end**. J₂ is the quantitative measure
    of where in the sequence the body sits.

    Returns
    -------
    dict
        ``{ok, q_maclaurin_jacobi, q_jacobi_bar, q_roche_fission,
        regimes: [{name, q_lower, q_upper, description}...]}``.

    References
    ----------
    Chandrasekhar S. (1969). *Ellipsoidal Figures of Equilibrium*,
    Yale University Press.

    Lai D., Rasio F. A., Shapiro S. L. (1994). Ellipsoidal figures
    of equilibrium: Compressible models. ApJS 88, 205-252.
    """
    return {
        "ok": True,
        "q_maclaurin_jacobi": Q_MACLAURIN_JACOBI_BIFURCATION,
        "q_jacobi_bar": Q_JACOBI_BAR_INSTABILITY,
        "q_roche_fission": Q_ROCHE_FISSION,
        "regimes": [
            {
                "name": "sphere",
                "q_lower": 0.0,
                "q_upper": 0.001,
                "description": (
                    "Effectively spherical; centrifugal force "
                    "negligible relative to self-gravity."
                ),
            },
            {
                "name": "maclaurin",
                "q_lower": 0.001,
                "q_upper": Q_MACLAURIN_JACOBI_BIFURCATION,
                "description": (
                    "Maclaurin oblate spheroid: axially symmetric; "
                    "equatorial bulge proportional to q. Rotational "
                    "kinetic energy small relative to gravitational "
                    "binding."
                ),
            },
            {
                "name": "jacobi",
                "q_lower": Q_MACLAURIN_JACOBI_BIFURCATION,
                "q_upper": Q_JACOBI_BAR_INSTABILITY,
                "description": (
                    "Jacobi triaxial ellipsoid: a ≠ b ≠ c. The "
                    "Maclaurin sequence has become secularly "
                    "unstable; the body has bifurcated to a "
                    "three-axis equilibrium. Haumea-class."
                ),
            },
            {
                "name": "bar",
                "q_lower": Q_JACOBI_BAR_INSTABILITY,
                "q_upper": Q_ROCHE_FISSION,
                "description": (
                    "Bar instability: the Jacobi sequence has "
                    "become dynamically unstable; the body "
                    "elongates into a bar shape and may fission."
                ),
            },
            {
                "name": "ring",
                "q_lower": Q_ROCHE_FISSION,
                "q_upper": float("inf"),
                "description": (
                    "Roche-limit / fission: matter at the equator "
                    "is unbound by centrifugal force; the body "
                    "literally fissions into a ring/torus. Saturn's "
                    "rings sit inside the Roche limit."
                ),
            },
        ],
    }


def list_toroidal_residuals() -> Dict[str, Any]:
    """Full catalog enumeration of every body's toroidal-residual
    classification."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "residuals": [_to_dict(t) for t in TOROIDAL_RESIDUALS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "Q_MACLAURIN_JACOBI_BIFURCATION",
    "Q_JACOBI_BAR_INSTABILITY",
    "Q_ROCHE_FISSION",
    "TOROIDAL_RESIDUALS",
    "SOURCES",
    "ToroidalResidual",
    "get_toroidal_residual",
    "get_chandrasekhar_sequence_thresholds",
    "list_toroidal_residuals",
]
