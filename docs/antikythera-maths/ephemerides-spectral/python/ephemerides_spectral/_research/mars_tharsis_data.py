"""Sol Mars Tharsis Volcanic Chain Spectral Catalog — bounded-local
graph-Laplacian application to a Tharsis-region volcanic feature
on a body **without plate tectonics**.

Real, sourced data for the v0.24.7 ship — the **eighth ship in v0.24.x**
and the **second time** the project's graph-Laplacian eigenbasis is
applied to **physical features on a single body's surface** rather
than to orbital relationships between bodies. Where v0.24.5 Hawaii
catalogued a hotspot track on a body **with** plate tectonics, this
v0.24.7 ship catalogues the Mars Tharsis montes — a hotspot family
on a body **without** plate tectonics — making the bounded-local
Laplacian methodology cross-body.

Physics
-------
Mars has **no plate tectonics**: its lithosphere is a single
unbroken shell. The same mantle-plume mechanism that produces
hotspot **chains** on Earth (Pacific Plate moving over a stationary
Hawaii plume) instead produces **stationary super-volcanoes** on
Mars: a plume sitting under the same patch of crust for ~Gyr
timescales builds **one giant volcano** rather than a chain of
smaller ones. **Olympus Mons** (~22 km from base to summit, 600 km
diameter, the largest known volcano in the Solar System) is the
direct consequence — it would be a chain on Earth, but on Mars the
plume never moved relative to the lithosphere.

The **Tharsis Montes** (Arsia / Pavonis / Ascraeus) are three
shield volcanoes aligned **NE-SW along a ridge** at ~3400 km
spacing through the western Tharsis region. The alignment
reflects **deep mantle plume structure** (Anderson 2001;
Plescia 2004) rather than plate motion — the plumes themselves
form a roughly linear arrangement under the lithosphere.
**Alba Mons** (north of the Tharsis Montes; formerly Alba Patera)
is a much older, much broader, much shorter shield volcano
(~1500 km diameter, ~6.8 km elevation), representing an earlier
phase of Tharsis volcanism. **Olympus Mons** sits NW of the
Tharsis Montes ridge, on the Tharsis bulge's NW flank.

Coverage notes (v0.24.7)
------------------------
**5-volcano roster** spanning the major Tharsis edifices, with
crater-count ages from Hartmann & Neukum 2001, Werner 2009, and
Plescia 2004, summit positions from Smith et al. 2001 (MGS MOLA
topography), and surface elevations from MOLA (Smith 2001).

The catalog ships per-volcano: name, surface age (Myr), age
uncertainty, latitude / longitude, summit elevation, edifice
diameter, source citation. The graph-Laplacian eigenbasis
analysis is computed on demand in the catalog wrapper from these
inputs (no precomputed eigenvectors stored in the data file).

**Not a re-derivation.** Ages are crater-count surface ages from
the cited papers; edifices' ages reflect their *youngest* surface
flows, not their initial construction (which extends back into
the Noachian / early Hesperian).

Cross-channel reach
-------------------
Direct parallel to v0.24.5 Hawaii: **same eigendecomposition
machinery, different tectonic regime**. Hawaii's Fiedler
partition surfaces a *spatial gap along a 1D track*; the bend
lives in *age-vs-arc-length residuals*. Mars Tharsis's Fiedler
partition surfaces the *Tharsis Montes ridge as one cluster + the
Olympus / Alba outliers as a different cluster* — and there is
no "bend" because there's no plate motion. The age-vs-distance
relation is **not** a chronologically-ordered chain but a
roughly-uniform *family* of cogenetic features. The Hawaii
bounded-local-Laplacian extracts a *trajectory*; the Mars
bounded-local-Laplacian extracts a *cogenetic family*.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Mars Tharsis hotspot region centre (canonical) -----------------
# Anderson 2001: Tharsis bulge centre ~0°N 265°E (just SE of Pavonis).
THARSIS_CENTRE_LAT_DEG: float = 0.0
THARSIS_CENTRE_LON_DEG: float = 265.0

# ---- Mars mean radius -----------------------------------------------
MARS_RADIUS_KM: float = 3389.5

# ---- Tharsis Montes ridge azimuth (NE-SW) ---------------------------
# Plescia 2004: the Arsia → Ascraeus axis runs at ~040° azimuth
# (measured from north, clockwise). Used as the canonical "ridge
# direction" against which the Olympus / Alba outliers are residuals.
THARSIS_MONTES_RIDGE_AZIMUTH_DEG: float = 40.0


@dataclass(frozen=True)
class TharsisVolcano:
    """One Mars Tharsis-region shield volcano.

    Stores the published surface age + summit position + canonical
    reference. Geographic coordinates use east-positive (0 to 360)
    / north-positive convention (Mars planetographic standard,
    matching MOLA dataset).

    The ``role`` field labels the volcano's structural role in the
    Tharsis system: "tharsis_montes" for the three aligned
    Pavonis/Ascraeus/Arsia ridge volcanoes; "olympus_outlier" for
    the NW-flank Olympus Mons super-volcano; "alba_outlier" for
    the much older / broader Alba Mons. The Fiedler partition is
    expected to surface this structural distinction.
    """
    name: str
    age_myr: float                # crater-count surface age
    age_uncertainty_myr: float    # 1-sigma crater-count uncertainty
    latitude_deg: float           # summit latitude, north positive
    longitude_deg: float          # summit longitude, east 0-360
    summit_elevation_m: float     # summit above MOLA datum
    edifice_diameter_km: float    # base diameter
    role: str                     # see docstring
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# ---------------------------------------------------------------------------
# Per-volcano roster
# ---------------------------------------------------------------------------

MARS_THARSIS_VOLCANOES: List[TharsisVolcano] = [

    # ==== Tharsis Montes (NE-SW ridge, three aligned shields) =========

    TharsisVolcano(
        name="arsia_mons",
        age_myr=130.0,
        age_uncertainty_myr=20.0,
        latitude_deg=-8.4,
        longitude_deg=239.9,
        summit_elevation_m=17761.0,
        edifice_diameter_km=435.0,
        role="tharsis_montes",
        notes="Southernmost of the three Tharsis Montes. Largest "
              "summit caldera (~110 km diameter); flank vents on "
              "SW slope. Hartmann & Neukum 2001 crater-count "
              "age for youngest surface flows.",
        source_key="hartmann_neukum_2001",
    ),

    TharsisVolcano(
        name="pavonis_mons",
        age_myr=100.0,
        age_uncertainty_myr=20.0,
        latitude_deg=1.5,
        longitude_deg=247.2,
        summit_elevation_m=14058.0,
        edifice_diameter_km=375.0,
        role="tharsis_montes",
        notes="Central Tharsis Mons (its name means 'peacock' in "
              "Latin). Sits almost exactly on the Mars equator. "
              "Werner 2009 crater-count age.",
        source_key="werner_2009",
    ),

    TharsisVolcano(
        name="ascraeus_mons",
        age_myr=100.0,
        age_uncertainty_myr=30.0,
        latitude_deg=11.8,
        longitude_deg=255.5,
        summit_elevation_m=18225.0,
        edifice_diameter_km=460.0,
        role="tharsis_montes",
        notes="Northernmost of the three Tharsis Montes; tallest "
              "of the three. Hartmann & Neukum 2001.",
        source_key="hartmann_neukum_2001",
    ),

    # ==== Olympus Mons (NW outlier; the super-volcano) ================

    TharsisVolcano(
        name="olympus_mons",
        age_myr=150.0,
        age_uncertainty_myr=50.0,
        latitude_deg=18.65,
        longitude_deg=226.2,
        summit_elevation_m=21229.0,
        edifice_diameter_km=600.0,
        role="olympus_outlier",
        notes="THE Solar-System-scale super-volcano: ~22 km from "
              "base to summit (taller than Earth's Mount Everest "
              "is above sea level by 2.5x), 600 km base diameter, "
              "encircled by a 6-km-high basal scarp. Direct "
              "consequence of stationary plume + no plate tectonics: "
              "the same plume that produced the Hawaiian-Emperor "
              "chain on Earth would build ONE Olympus-Mons-scale "
              "volcano on Mars. Hartmann 2005 crater-count age for "
              "youngest summit flows; older flank flows extend back "
              "to ~3 Gyr.",
        source_key="hartmann_2005",
    ),

    # ==== Alba Mons (older, broader N outlier) ========================

    TharsisVolcano(
        name="alba_mons",
        age_myr=1500.0,
        age_uncertainty_myr=300.0,
        latitude_deg=40.5,
        longitude_deg=250.4,
        summit_elevation_m=6800.0,
        edifice_diameter_km=1500.0,
        role="alba_outlier",
        notes="Formerly 'Alba Patera'. Largest volcano in the Solar "
              "System by *base area* (~1500 km diameter), but only "
              "~6.8 km tall — a vastly broader / shorter geometry "
              "than the Tharsis Montes. Represents an EARLIER phase "
              "of Tharsis volcanism (mid-Hesperian). Plescia 2004 "
              "crater-count surface age.",
        source_key="plescia_2004",
        precision_flag=PRECISION_MEDIUM,
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "hartmann_neukum_2001": (
        "Hartmann W. K. & Neukum G. (2001). Cratering chronology "
        "and the evolution of Mars. Space Science Reviews 96, "
        "165-194. DOI: 10.1023/A:1011945222010. The canonical "
        "Mars crater-count chronology calibration; surface ages "
        "for Arsia / Pavonis / Ascraeus."
    ),
    "hartmann_2005": (
        "Hartmann W. K. (2005). Martian cratering 8: Isochron "
        "refinement and the chronology of Mars. Icarus 174, "
        "294-320. DOI: 10.1016/j.icarus.2004.11.023. Refined "
        "crater-count chronology + Olympus Mons youngest-surface "
        "age (~150 Myr summit flows; older flank record)."
    ),
    "werner_2009": (
        "Werner S. C. (2009). The global martian volcanic "
        "evolutionary history. Icarus 201, 44-68. "
        "DOI: 10.1016/j.icarus.2008.12.019. High-resolution "
        "crater-count surface ages for the Tharsis Montes; "
        "established Pavonis Mons youngest activity ~100 Myr."
    ),
    "plescia_2004": (
        "Plescia J. B. (2004). Morphometric properties of Martian "
        "volcanoes. Journal of Geophysical Research 109, E03003. "
        "DOI: 10.1029/2002JE002031. The canonical morphometric "
        "compilation: edifice diameters, summit elevations, "
        "slopes, caldera dimensions for all major Mars volcanoes; "
        "Alba Mons surface age."
    ),
    "smith_2001_mola": (
        "Smith D. E. et al. (2001). Mars Orbiter Laser Altimeter: "
        "Experiment summary after the first year of global "
        "mapping of Mars. Journal of Geophysical Research 106, "
        "23689-23722. DOI: 10.1029/2000JE001364. The canonical "
        "MOLA topography dataset; summit positions and elevations."
    ),
    "anderson_2001": (
        "Anderson R. C. et al. (2001). Primary centers and "
        "secondary concentrations of tectonic activity through "
        "time in the western hemisphere of Mars. Journal of "
        "Geophysical Research 106, 20563-20585. "
        "DOI: 10.1029/2000JE001278. Tharsis-bulge tectonic "
        "history; identifies Tharsis Montes ridge as a deep "
        "mantle structural feature, not a plate-motion track."
    ),
    "carr_head_2010": (
        "Carr M. H. & Head J. W. (2010). Geologic history of "
        "Mars. Earth and Planetary Science Letters 294, 185-203. "
        "DOI: 10.1016/j.epsl.2009.06.042. Synthesis of Mars "
        "geological evolution; Tharsis volcanism in context of "
        "no-plate-tectonics regime."
    ),
    "morgan_1971": (
        "Morgan W. J. (1971). Convection plumes in the lower "
        "mantle. Nature 230, 42-43. DOI: 10.1038/230042a0. The "
        "original mantle-plume hypothesis applied to Hawaii — "
        "context for the Mars no-plate-tectonics contrast: same "
        "plume mechanism, different lithosphere regime."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MARS_RADIUS_KM",
    "THARSIS_CENTRE_LAT_DEG",
    "THARSIS_CENTRE_LON_DEG",
    "THARSIS_MONTES_RIDGE_AZIMUTH_DEG",
    "MARS_THARSIS_VOLCANOES",
    "SOURCES",
    "TharsisVolcano",
]
