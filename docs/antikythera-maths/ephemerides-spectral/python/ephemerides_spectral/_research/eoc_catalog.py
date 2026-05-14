"""EOC patch catalog generator — Phase 10a closed-form Kepler series.

Turns each row of :mod:`._research.secular_elements_data` into an
:class:`EccentricityCorrectionPatch`, one per body. The generator is
closed-form algebra: no fits, no free parameters; everything derives
from the body's labelled secular elements `(e, M₀, n)` via Kepler's
equation.

Architecture
------------

The catalog distinguishes three modes:

1. **Generate one patch per body**: :func:`build_eoc_patch(body)` —
   constructs a fully-configured patch for one body, ready to pass to
   :func:`diagnosed_fibers.apply_patch`.

2. **Bulk catalog access**: :data:`EOC_CATALOG` — dict of all 51 patches
   keyed by body name (Sun excluded; e ≡ 0). Iterate to apply every
   patch at once, or pick subsets by body / parent / frame.

3. **Selective registration**: :func:`apply_eoc_patches(bodies=None,
   frame=None, parent=None)` — convenience wrapper for the bridge
   surface; registers a subset (default all 50) of the catalog into
   the diagnosed-fibers overlay.

Coverage discipline (no MVP framing)
------------------------------------

Every body in the BIP roster with non-zero eccentricity gets a patch.
Even Triton (e ≈ 1.6e-5) and Tethys (e ≈ 1e-4) — bodies where the EOC
contribution is below the BIP's design precision floor (0.012° at
+20 yr) — still get patches; the closed-form algebra is cheap and the
discipline applies uniformly. The catalog ships **51 patches** for the
51 non-Sun bodies in the 52-body BIP roster (Sun has e ≡ 0; the roster
total is unchanged at 52).

The Newton-Kepler evaluator inside :class:`EccentricityCorrectionPatch`
is exact at any eccentricity, so bodies are not stratified by an
"order=N" choice the way a power-series implementation would require.
Nereid's e = 0.7507 is handled by the same single patch type as
Earth's e = 0.0167 — same dataclass, same evaluator, same labelled-
physics provenance.

Reference frames
----------------

The patch evaluator adds the correction to the body's phase residue in
the BIP encoder's body-table frame:

* For ``frame == "heliocentric_ecliptic"`` rows (13 bodies: 9 planets
  + 4 asteroids), the patch adds to the body's heliocentric ecliptic
  longitude — matching what the BIP encoder calibrates at J2000.

* For ``frame == "parent_centric_ecliptic"`` rows (38 moons), the
  patch adds to the body's parent-centric ecliptic longitude — also
  matching the BIP's per-moon calibration.

The patch is frame-agnostic by construction (it operates on phase
residues, not Cartesian state), so as long as the secular-elements
catalog and the BIP encoder agree on the frame for each body, the
patches compose correctly.

Apply ordering
--------------

EOC patches commute (sins sum); ordering within the
diagnosed-fibers registry doesn't matter. EOC patches also compose
cleanly with the v0.5.x `CATALOG_V2` LS-fit patches — the empirical
fits target *residual* peaks after first-order Kepler is removed, so
applying EOC then `CATALOG_V2` gives the combined correction. Tests
pin this composition.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional

from .diagnosed_fibers import (
    EccentricityCorrectionPatch,
    apply_patch,
    list_patches,
    clear_patches,
)
from .secular_elements_data import (
    SECULAR_ELEMENTS,
    SecularElements,
    SOURCES as SECULAR_SOURCES,
)


def build_eoc_patch(body: str) -> EccentricityCorrectionPatch:
    """Construct an EOC patch for `body` from its secular elements.

    The patch's parameters are derived closed-form from the body's
    `(e, M₀, n)` triple — no LS fit, no free parameters, no
    measurement.

    Raises ``KeyError`` if `body` is not in :data:`SECULAR_ELEMENTS`
    (i.e. the Sun, which has e ≡ 0 and needs no EOC patch).
    """
    row = SECULAR_ELEMENTS[body]
    return EccentricityCorrectionPatch(
        name=f"{body}-eoc-newton-kepler",
        body=body,
        eccentricity=row.e,
        mean_anomaly_at_j2000_rad=row.mean_anomaly_at_j2000_rad(),
        n_rad_per_day=math.radians(row.n_deg_per_day),
        notes=(
            f"Phase 10a (v0.28.0rc1) closed-form Kepler EOC for {body}. "
            f"Newton-iteration on E - e·sin(E) = M, half-angle true-"
            f"anomaly formula, J2000-anchored. e = {row.e:.6f}; "
            f"M₀ = {row.mean_anomaly_at_j2000_deg():.4f}°; "
            f"P_orb = {row.orbital_period_days_from_n():.3f} d. "
            f"Source: {row.source_key} "
            f"(see _research.secular_elements_data.SOURCES). "
            f"Frame: {row.frame}; parent: {row.parent}."
        ),
    )


# Bulk catalog — one patch per non-Sun body
EOC_CATALOG: Dict[str, EccentricityCorrectionPatch] = {
    body: build_eoc_patch(body) for body in SECULAR_ELEMENTS.keys()
}


def list_eoc_patches() -> List[Dict[str, object]]:
    """Return JSON-friendly dicts describing every patch in the catalog.

    Used by the bridge surface :func:`bridge.list_eoc_patches`.
    """
    out: List[Dict[str, object]] = []
    for body, patch in sorted(EOC_CATALOG.items()):
        row = SECULAR_ELEMENTS[body]
        out.append(
            {
                "name": patch.name,
                "body": patch.body,
                "kind": patch.kind,
                "eccentricity": patch.eccentricity,
                "mean_anomaly_at_j2000_deg": math.degrees(
                    patch.mean_anomaly_at_j2000_rad
                ),
                "mean_anomaly_at_j2000_rad": patch.mean_anomaly_at_j2000_rad,
                "n_deg_per_day": math.degrees(patch.n_rad_per_day),
                "n_rad_per_day": patch.n_rad_per_day,
                "period_days": 2.0 * math.pi / patch.n_rad_per_day,
                "frame": row.frame,
                "parent": row.parent,
                "source_key": row.source_key,
                "notes": patch.notes,
            }
        )
    return out


def get_eoc_patch(body: str) -> Dict[str, object]:
    """Return a JSON-friendly dict for one body's EOC patch.

    Used by the bridge surface :func:`bridge.get_eoc_patch`.
    """
    if body not in EOC_CATALOG:
        raise KeyError(
            f"no EOC patch for body {body!r}; "
            f"the catalog covers {len(EOC_CATALOG)} bodies "
            f"(Sun excluded because e ≡ 0). "
            f"Available: {sorted(EOC_CATALOG.keys())}"
        )
    patch = EOC_CATALOG[body]
    row = SECULAR_ELEMENTS[body]
    return {
        "name": patch.name,
        "body": patch.body,
        "kind": patch.kind,
        "eccentricity": patch.eccentricity,
        "mean_anomaly_at_j2000_deg": math.degrees(
            patch.mean_anomaly_at_j2000_rad
        ),
        "mean_anomaly_at_j2000_rad": patch.mean_anomaly_at_j2000_rad,
        "n_deg_per_day": math.degrees(patch.n_rad_per_day),
        "n_rad_per_day": patch.n_rad_per_day,
        "period_days": 2.0 * math.pi / patch.n_rad_per_day,
        "frame": row.frame,
        "parent": row.parent,
        "source_key": row.source_key,
        "source_citation": SECULAR_SOURCES.get(row.source_key, ""),
        "notes": patch.notes,
    }


def apply_eoc_patches(
    bodies: Optional[Iterable[str]] = None,
    frame: Optional[str] = None,
    parent: Optional[str] = None,
) -> List[str]:
    """Register a selection of EOC patches into the diagnosed-fibers
    overlay registry.

    Selection criteria (intersected if multiple given):

    * ``bodies``: explicit list / iterable of body names. If omitted,
      every body in the catalog is selected.
    * ``frame``: filter by frame string
      (``"heliocentric_ecliptic"`` or ``"parent_centric_ecliptic"``).
    * ``parent``: filter to moons of a specific parent body
      (e.g. ``"jupiter"`` for the 7 Jovian moons).

    Returns the list of patch names that were registered.

    Raises ``ValueError`` if any patch's name collides with an already-
    active patch in the registry — the user must :func:`clear_patches`
    or pick a different selection first.
    """
    selected: List[str] = []
    for body, patch in sorted(EOC_CATALOG.items()):
        if bodies is not None and body not in bodies:
            continue
        row = SECULAR_ELEMENTS[body]
        if frame is not None and row.frame != frame:
            continue
        if parent is not None and row.parent != parent:
            continue
        selected.append(body)

    registered: List[str] = []
    for body in selected:
        patch = EOC_CATALOG[body]
        apply_patch(patch)
        registered.append(patch.name)
    return registered


def clear_eoc_patches() -> int:
    """Remove EVERY EOC patch from the diagnosed-fibers overlay.

    Note: this clears only EOC patches (kind == ``"eccentricity-
    correction"``). Other active patches (sinusoid, coupled-sinusoid)
    are left in place. To clear everything use
    :func:`diagnosed_fibers.clear_patches`.

    Returns the count of EOC patches that were removed.
    """
    # We can't easily remove a single patch from the registry without
    # extending diagnosed_fibers, so the safe minimum-touch approach
    # is: snapshot, partition by kind, clear all, re-register non-EOC.
    from . import diagnosed_fibers as df  # local import to avoid cycle

    snap = df.snapshot()
    eoc_count = sum(1 for p in snap if p.kind == "eccentricity-correction")
    if eoc_count == 0:
        return 0
    non_eoc = [p for p in snap if p.kind != "eccentricity-correction"]
    df.clear_patches()
    for p in non_eoc:
        df.apply_patch(p)
    return eoc_count


def count() -> int:
    """Number of bodies in the EOC catalog (= BIP roster minus Sun)."""
    return len(EOC_CATALOG)


def heliocentric_bodies() -> List[str]:
    """Bodies whose EOC patches operate in the heliocentric ecliptic
    frame (9 planets + 4 asteroids = 13)."""
    return sorted(
        body
        for body, row in SECULAR_ELEMENTS.items()
        if row.frame == "heliocentric_ecliptic"
    )


def parent_centric_bodies(parent: Optional[str] = None) -> List[str]:
    """Bodies whose EOC patches operate in the parent-centric frame.

    Optionally filter by parent body name (e.g. ``"jupiter"`` returns
    the 7 Jovian moons in the catalog).
    """
    return sorted(
        body
        for body, row in SECULAR_ELEMENTS.items()
        if row.frame == "parent_centric_ecliptic"
        and (parent is None or row.parent == parent)
    )
