"""Sol Tidal Migration Catalog — per-pair tidal dissipation ↔ orbital
migration cross-channel coupling.

Real, sourced data for the v0.21.6 ship — the **sixth cross-channel
coupling surface** in the §17.4.2 v0.21.x sequence (after v0.21.5
auroral coupling).

Physics
-------
A satellite's tidal interaction with its parent body dissipates
mechanical energy (via the v0.21.4 ``RotationalConstraint`` Q-factor
mechanism) and transfers angular momentum between the parent's
rotation and the satellite's orbit. The observable signature is a
secular change in the satellite's semi-major axis — tidal migration.

Direction follows from the spin-orbit relation:
* If the satellite orbits *faster* than the parent rotates → tidal
  bulge lags the satellite, dragging it *inward* (Phobos-Mars,
  Triton-Neptune retrograde).
* If the satellite orbits *slower* than the parent rotates → tidal
  bulge leads the satellite, pulling it *outward* (Moon-Earth,
  Galileans, Titan-Saturn).
* If satellite is in tidal lock with parent → no migration
  (Charon-Pluto synchronous binary).

Resonance amplifies migration: when satellites are caught in mean-
motion resonance (Laplace 1:2:4 for the Galileans), tidal forcing
on one body propagates to all members of the resonance chain.

Coverage notes (v0.21.6)
------------------------
6 parent-satellite pairs with peer-reviewed measured migration rates:

- terra-luna: Williams 2014 / 2025 LLR catalog (3.8 cm/yr outward;
  the canonical case + the most-precisely-measured rate in the solar
  system).
- mars-phobos: Lainey 2007 secular orbital fit (1.9 cm/yr inward;
  tidal-disruption deadline ~50 Myr).
- jupiter (Laplace): Lainey 2009 Galilean astrometry — Io drifting
  outward, Europa nearly stationary, Ganymede inward; resonance
  currently slowly EXPANDING.
- saturn-titan: Lainey 2020 — Titan outward at 11 cm/yr (100× older
  estimates; implies resonance locking with Saturn interior modes,
  cross-references the Mankovich-Fuller 2021 v0.21.4 result).
- neptune-triton: Jacobson 2009 secular drift fit (negligible /
  inward; retrograde captured satellite, eventual Roche-limit
  disruption).
- pluto-charon: dual tidal lock; mutual synchronous; no migration
  observable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---- Precision flags per the §17.1.6 ship-readiness convention -------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Migration direction labels --------------------------------------
DIR_OUTWARD: str = "outward"
DIR_INWARD: str = "inward"
DIR_LOCKED: str = "locked"     # tidal lock, no migration


@dataclass(frozen=True)
class TidalMigration:
    """Per-pair tidal-dissipation-driven orbital-migration constraint.

    Stores the published secular migration rate (signed: positive =
    outward, negative = inward, zero = locked) for one parent-satellite
    pair, plus citation provenance.
    """
    pair_name: str          # canonical "parent-satellite" pair string
    parent_body: str
    satellite_body: str
    # Migration rate in cm/year. Signed: positive = outward; negative
    # = inward; zero = locked / synchronous.
    migration_rate_cm_per_year: float
    # Verbatim direction label (one of DIR_*).
    migration_direction: str
    # True if the pair is in observed mean-motion resonance with at
    # least one other body (e.g., Io is in Laplace resonance with
    # Europa + Ganymede).
    is_resonance_locked: bool = False
    # Verbatim notes string (often the resonance partners or the
    # disruption-deadline timescale).
    additional_constraint: str = ""
    precision_flag: str = PRECISION_HIGH
    notes: Optional[str] = None
    source_key: str = ""


# ---------------------------------------------------------------------------
# Per-pair tidal-migration entries — §17.4.2 v0.21.6 cross-channel ship
# ---------------------------------------------------------------------------

TIDAL_MIGRATIONS: List[TidalMigration] = [

    # ---- Earth-Moon — Williams 2014/2025 LLR -------------------------
    # The canonical case. Lunar Laser Ranging gives Moon outward
    # migration 3.83 ± 0.005 cm/yr — the most precisely measured
    # tidal-migration rate in the solar system. Driven by Earth's
    # tidal Q ≈ 280 from the Mathews 2002 free-core-nutation
    # constraint chain (cross-references v0.21.4).
    TidalMigration(
        pair_name="terra-luna",
        parent_body="terra",
        satellite_body="luna",
        migration_rate_cm_per_year=3.83,
        migration_direction=DIR_OUTWARD,
        is_resonance_locked=False,
        additional_constraint="Earth Q ≈ 280 (solid Earth + ocean tides)",
        precision_flag=PRECISION_HIGH,
        notes="Canonical case; LLR-measured rate is the most precise "
              "in the solar system. Drives Earth's spin-down + day "
              "lengthening. Cross-references v0.21.4 Earth Q.",
        source_key="williams_2014",
    ),

    # ---- Mars-Phobos — Lainey 2007 -----------------------------------
    # The famous "Phobos is doomed" case. Lainey 2007 fit Phobos
    # secular orbital evolution to give 1.9 cm/yr INWARD migration;
    # extrapolated forward gives ~50 Myr until tidal-disruption /
    # Roche-limit crossing. Phobos orbits faster than Mars rotates
    # (which is why direction is inward).
    TidalMigration(
        pair_name="mars-phobos",
        parent_body="mars",
        satellite_body="phobos",
        migration_rate_cm_per_year=-1.9,
        migration_direction=DIR_INWARD,
        is_resonance_locked=False,
        additional_constraint="tidal-disruption deadline ~50 Myr",
        precision_flag=PRECISION_HIGH,
        notes="Phobos orbits faster than Mars rotates → tidal bulge "
              "lags satellite → inward migration. Tidal disruption / "
              "Roche-limit crossing extrapolated to ~50 Myr.",
        source_key="lainey_2007",
    ),

    # ---- Jupiter Laplace — Lainey 2009 -------------------------------
    # The Galilean Laplace resonance (1:2:4 in mean motion of
    # Io:Europa:Ganymede). Lainey 2009 fit 117 years of astrometry
    # to show Io is currently drifting outward at ~3.6 cm/yr; the
    # resonance as a whole is slowly EXPANDING (not contracting as
    # older models had assumed). The headline of the v0.21.4 Q ~ 80
    # tidal dissipation finding.
    TidalMigration(
        pair_name="jupiter-io",
        parent_body="jupiter",
        satellite_body="io",
        migration_rate_cm_per_year=3.6,
        migration_direction=DIR_OUTWARD,
        is_resonance_locked=True,
        additional_constraint="Galilean Laplace resonance 1:2:4 with Europa + Ganymede; resonance currently expanding",
        precision_flag=PRECISION_HIGH,
        notes="Galilean Laplace 1:2:4 resonance currently EXPANDING "
              "(not contracting as classical theory assumed). Lainey "
              "2009 fit of 117 years of astrometry. Cross-references "
              "v0.21.4 Io Q ≈ 80.",
        source_key="lainey_2009_migration",
    ),

    # ---- Saturn-Titan — Lainey 2020 ----------------------------------
    # The headline. Lainey 2020 measured Titan's outward migration
    # at 11 cm/yr — 100× the rate predicted by older equilibrium-tide
    # theory. Implies that Saturn's interior is in resonance lock
    # with Titan's orbit, providing a much stronger angular-momentum
    # transfer than steady-state tidal dissipation. Cross-references
    # the Mankovich-Fuller 2021 v0.21.4 ring-seismology result.
    TidalMigration(
        pair_name="saturn-titan",
        parent_body="saturn",
        satellite_body="titan",
        migration_rate_cm_per_year=11.0,
        migration_direction=DIR_OUTWARD,
        is_resonance_locked=True,
        additional_constraint="resonance locking with Saturn interior modes",
        precision_flag=PRECISION_HIGH,
        notes="THE HEADLINE: 11 cm/yr is 100× older equilibrium-tide "
              "predictions. Implies Saturn interior resonance locking "
              "(cross-references v0.21.4 Mankovich-Fuller 2021 ring "
              "seismology). Lainey 2020.",
        source_key="lainey_2020_migration",
    ),

    # ---- Neptune-Triton — Jacobson 2009 ------------------------------
    # Triton is a captured Kuiper Belt object; retrograde orbit means
    # tidal-bulge geometry is reversed → secular drift is INWARD,
    # eventual Roche-limit disruption ~3.6 Gyr from now (becomes a
    # ring system).
    TidalMigration(
        pair_name="neptune-triton",
        parent_body="neptune",
        satellite_body="triton",
        migration_rate_cm_per_year=-0.5,
        migration_direction=DIR_INWARD,
        is_resonance_locked=False,
        additional_constraint="retrograde orbit; eventual Roche-limit disruption ~3.6 Gyr",
        precision_flag=PRECISION_MEDIUM,
        notes="Retrograde captured satellite. Tidal-bulge geometry "
              "reversed → inward migration. Will cross Roche limit "
              "in ~3.6 Gyr, becoming ring system. Jacobson 2009 fit.",
        source_key="jacobson_2009",
    ),

    # ---- Pluto-Charon — dual tidal lock ------------------------------
    # The unique solar-system case: BOTH bodies are tidally locked to
    # each other (dual-synchronous). No tidal migration; the system
    # has reached its tidal end-state already (mass ratio 0.12 puts
    # the barycentre outside Pluto, making it more like a binary
    # planet than a planet-with-moon). McKinnon 2017 New Horizons
    # interior-structure paper confirms.
    TidalMigration(
        pair_name="pluto-charon",
        parent_body="pluto",
        satellite_body="charon",
        migration_rate_cm_per_year=0.0,
        migration_direction=DIR_LOCKED,
        is_resonance_locked=False,
        additional_constraint="dual tidal lock — only such case in solar system",
        precision_flag=PRECISION_HIGH,
        notes="Unique dual-synchronous case in solar system. Both "
              "bodies tidally locked to each other; mass ratio 0.12 "
              "puts barycentre outside Pluto. End-state of tidal "
              "evolution; no further migration. McKinnon 2017.",
        source_key="mckinnon_2017",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES — every numeric value above must cite into this dict.
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "williams_2014": (
        "Williams J. G. & Boggs D. H. (2014). Tides on the Moon: "
        "Theory and determination of dissipation. JGR Planets 120, "
        "689-724. DOI: 10.1002/2014JE004755"
    ),
    "lainey_2007": (
        "Lainey V. et al. (2007). First numerical ephemerides of "
        "the Martian moons. A&A 465, 1075-1084. "
        "DOI: 10.1051/0004-6361:20065466"
    ),
    "lainey_2009_migration": (
        "Lainey V. et al. (2009). Strong tidal dissipation in Io and "
        "Jupiter from astrometric observations (orbital migration "
        "results for Galilean Laplace resonance). Nature 459, 957-959. "
        "DOI: 10.1038/nature08108"
    ),
    "lainey_2020_migration": (
        "Lainey V. et al. (2020). Resonance locking in giant planets "
        "indicated by the rapid orbital expansion of Titan. Nature "
        "Astronomy 4, 1053-1058. DOI: 10.1038/s41550-020-1120-5"
    ),
    "jacobson_2009": (
        "Jacobson R. A. (2009). The orbits of the Neptunian satellites "
        "and the orientation of the pole of Neptune. Astron. J. 137, "
        "4322-4329. DOI: 10.1088/0004-6256/137/5/4322"
    ),
    "mckinnon_2017": (
        "McKinnon W. B. et al. (2017). Origin of the Pluto-Charon "
        "system: Constraints from the New Horizons flyby. Icarus "
        "287, 2-11. DOI: 10.1016/j.icarus.2016.11.019"
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "DIR_OUTWARD",
    "DIR_INWARD",
    "DIR_LOCKED",
    "TIDAL_MIGRATIONS",
    "SOURCES",
    "TidalMigration",
]
