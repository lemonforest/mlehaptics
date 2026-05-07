"""Sol Hawaiian-Emperor Chain Spectral Catalog — bounded-local
graph-Laplacian application to a hotspot-track on Earth's surface.

Real, sourced data for the v0.24.5 ship — the **sixth ship in v0.24.x**
and the **first time** the project's graph-Laplacian eigenbasis is
applied to **physical features on a single body's surface** rather
than to orbital relationships between bodies. Demonstrates the
**"chess-board / bounded-local-Laplacian"** insight: when the
phenomenon is bounded and local (a single hotspot track on Earth's
Pacific Plate), use a finite local graph rather than the global
spherical-harmonic basis.

Physics
-------
The **Hawaiian-Emperor seamount chain** is the canonical hotspot
track in plate tectonics: the **Pacific Plate** moves NW at ~10 cm/yr
over a roughly stationary mantle plume (the **Hawaii hotspot**), and
each volcano in the chain was created when its piece of the plate
was directly over the plume. As the plate moves, the hotspot stays
fixed in the deep mantle, and a chain of volcanoes forms — youngest
at the hotspot (Big Island, currently active; Loihi seamount about
to surface), oldest furthest from the hotspot (Meiji Seamount
~85 Myr, near the Aleutian Trench).

The **Hawaiian-Emperor bend** at ~47.5 Myr is a sharp ~60° kink in
the chain direction, marking either:

* a **Pacific Plate motion change** (classical view; Morgan 1971),
  or
* a **southward migration of the Hawaii plume itself** before
  ~50 Myr (Tarduno et al. 2003 paleomagnetic analysis showing
  Emperor-chain volcanoes formed at much higher paleolatitude than
  the present hotspot location).

Modern view (Sharp 2006 + Tarduno 2009): both effects contribute,
with plume motion dominating before the bend.

Coverage notes (v0.24.5)
------------------------
**18-seamount roster** spanning the full ~85 Myr chain, with
high-precision K-Ar / Ar-Ar / U-Pb ages from Sharp & Clague 2006,
O'Connor et al. 2013, Garcia et al. 2010, Clague 2010, and
Tarduno et al. 2003.

The catalog ships per-seamount: name, age (Myr), age uncertainty,
latitude / longitude, height above seafloor / above sea level
where applicable, source citation. The graph-Laplacian eigenbasis
analysis is computed on demand in the catalog wrapper from these
inputs (no precomputed eigenvectors stored in the data file).

**Not a re-derivation.** Ages are the published values from cited
papers; no fits or re-interpretations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---- Precision flags --------------------------------------------------
PRECISION_HIGH: str = "high"
PRECISION_MEDIUM: str = "medium"
PRECISION_LOW: str = "low"
PRECISION_NONE: str = "none"


# ---- Hawaiian-Emperor bend epoch (canonical) -------------------------
# Sharp 2006: 47.5 ± 1.0 Myr at the Daikakuji-Yuryaku transition.
HAWAIIAN_EMPEROR_BEND_AGE_MYR: float = 47.5
HAWAIIAN_EMPEROR_BEND_AGE_UNCERTAINTY_MYR: float = 1.0

# ---- Hawaii hotspot present location --------------------------------
HAWAII_HOTSPOT_LAT_DEG: float = 19.4               # Loihi seamount
HAWAII_HOTSPOT_LON_DEG: float = -155.3


@dataclass(frozen=True)
class Seamount:
    """One Hawaiian-Emperor chain seamount.

    Stores the published age + position + canonical reference.
    Geographic coordinates use east-positive / north-positive
    convention; west-Pacific Emperor seamounts have negative
    longitudes when their position lies past the antimeridian
    (we keep them as positive longitudes east of 0° for great-
    circle calculations to behave cleanly).
    """
    name: str
    age_myr: float                # K-Ar / Ar-Ar / U-Pb age
    age_uncertainty_myr: float    # 1-sigma
    latitude_deg: float           # north positive
    longitude_deg: float          # east positive (0 to 360 convention)
    arc: str                      # "emperor" | "bend" | "hawaiian"
    notes: Optional[str] = None
    source_key: str = ""
    precision_flag: str = PRECISION_HIGH


# ---------------------------------------------------------------------------
# Per-seamount roster (oldest → youngest along the chain)
# ---------------------------------------------------------------------------

HAWAIIAN_EMPEROR_SEAMOUNTS: List[Seamount] = [

    # ==== Emperor Seamount Chain (older arc, ~85 - 47.5 Myr) ========

    Seamount(
        name="meiji",
        age_myr=85.0,
        age_uncertainty_myr=2.0,
        latitude_deg=53.2,
        longitude_deg=164.7,
        arc="emperor",
        notes="Oldest dated seamount in the chain. Approaching the "
              "Aleutian Trench where it will be subducted. Age "
              "from drilled basement samples (ODP Leg 145).",
        source_key="keller_1995_meiji",
    ),

    Seamount(
        name="detroit",
        age_myr=75.8,
        age_uncertainty_myr=0.6,
        latitude_deg=51.5,
        longitude_deg=167.6,
        arc="emperor",
        notes="ODP Site 884 / 1203 basement age (Duncan & Keller "
              "2004). Tarduno 2003 paleolatitude ~36°N -- much "
              "higher than present Hawaii hotspot 19°N -- key "
              "evidence for plume southward migration.",
        source_key="duncan_keller_2004",
    ),

    Seamount(
        name="suiko",
        age_myr=64.7,
        age_uncertainty_myr=1.1,
        latitude_deg=44.6,
        longitude_deg=170.3,
        arc="emperor",
        notes="DSDP Site 433 basement. Paleolatitude ~27°N "
              "(Tarduno 2003).",
        source_key="duncan_clague_1985",
    ),

    Seamount(
        name="nintoku",
        age_myr=56.2,
        age_uncertainty_myr=0.6,
        latitude_deg=41.1,
        longitude_deg=170.5,
        arc="emperor",
        notes="ODP Site 1205 (Sharp & Clague 2006).",
        source_key="sharp_clague_2006",
    ),

    Seamount(
        name="koko",
        age_myr=48.1,
        age_uncertainty_myr=0.8,
        latitude_deg=35.3,
        longitude_deg=171.6,
        arc="emperor",
        notes="Last well-dated Emperor seamount before the bend. "
              "Sharp & Clague 2006 Ar-Ar.",
        source_key="sharp_clague_2006",
    ),

    # ==== Hawaiian-Emperor Bend at ~47.5 Myr =========================

    Seamount(
        name="daikakuji",
        age_myr=46.7,
        age_uncertainty_myr=0.5,
        latitude_deg=32.1,
        longitude_deg=172.3,
        arc="bend",
        notes="THE bend marker: just SE of the kink between Emperor "
              "and Hawaiian arcs. Sharp & Clague 2006 derives the "
              "canonical bend age 47.5 ± 1.0 Myr from Daikakuji - "
              "Koko age difference + chain geometry.",
        source_key="sharp_clague_2006",
    ),

    # ==== Hawaiian Ridge (younger arc, ~46.7 - 0 Myr) ================

    Seamount(
        name="yuryaku",
        age_myr=43.4,
        age_uncertainty_myr=1.6,
        latitude_deg=32.7,
        longitude_deg=172.7,
        arc="hawaiian",
        source_key="sharp_clague_2006",
    ),

    Seamount(
        name="kammu",
        age_myr=38.5,
        age_uncertainty_myr=2.0,
        latitude_deg=32.2,
        longitude_deg=173.0,
        arc="hawaiian",
        precision_flag=PRECISION_MEDIUM,
        source_key="o_connor_2013",
    ),

    Seamount(
        name="midway",
        age_myr=27.7,
        age_uncertainty_myr=0.6,
        latitude_deg=28.2,
        longitude_deg=182.6,        # = -177.4 (west of 180°)
        arc="hawaiian",
        notes="Atoll. Dated from drill-core basement (Dalrymple 1980 "
              "+ Sharp & Clague 2006 refinement).",
        source_key="sharp_clague_2006",
    ),

    Seamount(
        name="pearl_hermes",
        age_myr=20.0,
        age_uncertainty_myr=1.0,
        latitude_deg=27.8,
        longitude_deg=184.2,         # = -175.8
        arc="hawaiian",
        precision_flag=PRECISION_MEDIUM,
        source_key="clague_dalrymple_1989",
    ),

    Seamount(
        name="laysan",
        age_myr=19.9,
        age_uncertainty_myr=0.3,
        latitude_deg=25.8,
        longitude_deg=188.2,         # = -171.8
        arc="hawaiian",
        source_key="clague_dalrymple_1989",
    ),

    Seamount(
        name="necker",
        age_myr=10.3,
        age_uncertainty_myr=0.4,
        latitude_deg=23.6,
        longitude_deg=195.4,         # = -164.7
        arc="hawaiian",
        source_key="clague_dalrymple_1989",
    ),

    Seamount(
        name="niihau",
        age_myr=5.0,
        age_uncertainty_myr=0.2,
        latitude_deg=21.9,
        longitude_deg=199.7,         # = -160.3
        arc="hawaiian",
        source_key="clague_dalrymple_1989",
    ),

    Seamount(
        name="kauai",
        age_myr=4.7,
        age_uncertainty_myr=0.1,
        latitude_deg=22.0,
        longitude_deg=200.5,         # = -159.5
        arc="hawaiian",
        notes="Wai'ale'ale shield volcano (oldest of the main "
              "Hawaiian Islands). Garcia 2010 K-Ar.",
        source_key="garcia_2010",
    ),

    Seamount(
        name="oahu",
        age_myr=2.6,
        age_uncertainty_myr=0.1,
        latitude_deg=21.5,
        longitude_deg=202.1,         # = -157.9
        arc="hawaiian",
        notes="Wai'anae shield 3.9 Myr + Ko'olau shield 2.6 Myr. "
              "Use the Ko'olau (younger) value.",
        source_key="garcia_2010",
    ),

    Seamount(
        name="molokai",
        age_myr=1.7,
        age_uncertainty_myr=0.1,
        latitude_deg=21.1,
        longitude_deg=203.0,         # = -157.0
        arc="hawaiian",
        source_key="clague_2010",
    ),

    Seamount(
        name="maui_haleakala",
        age_myr=1.0,
        age_uncertainty_myr=0.1,
        latitude_deg=20.7,
        longitude_deg=203.7,         # = -156.3
        arc="hawaiian",
        notes="Haleakala East-Maui shield. West Maui shield is "
              "older (1.3 Myr).",
        source_key="clague_2010",
    ),

    Seamount(
        name="hawaii_kilauea",
        age_myr=0.0,
        age_uncertainty_myr=0.05,
        latitude_deg=19.4,
        longitude_deg=204.7,         # = -155.3
        arc="hawaiian",
        notes="Big Island. Kilauea + Mauna Loa currently active. "
              "Mauna Kea 0.5 Myr; Kohala 0.4 Myr. Kilauea is "
              "presently above the hotspot (within ~50 km of Loihi "
              "submarine seamount).",
        source_key="garcia_2010",
    ),
]


# ---------------------------------------------------------------------------
# SOURCES
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "sharp_clague_2006": (
        "Sharp W. D. & Clague D. A. (2006). 50-Ma initiation of "
        "Hawaiian-Emperor bend records major change in Pacific Plate "
        "motion. Science 313, 1281-1284. DOI: 10.1126/science.1128489. "
        "The canonical 47.5 Myr bend-age determination + Ar-Ar dates "
        "for Koko, Daikakuji, Yuryaku, Nintoku, Midway."
    ),
    "duncan_keller_2004": (
        "Duncan R. A. & Keller R. A. (2004). Radiometric ages for "
        "basement rocks from the Emperor Seamounts, ODP Leg 197. "
        "Geochem. Geophys. Geosyst. 5, Q08L03. "
        "DOI: 10.1029/2004GC000704. Detroit Seamount age."
    ),
    "duncan_clague_1985": (
        "Duncan R. A. & Clague D. A. (1985). Pacific Plate motion "
        "recorded by linear volcanic chains. In *The Ocean Basins "
        "and Margins* (vol. 7A), Plenum Press, 89-121. Pre-Sharp 2006 "
        "compilation; superseded for younger seamounts but still the "
        "standard for Suiko (DSDP Site 433)."
    ),
    "keller_1995_meiji": (
        "Keller R. A. et al. (1995). Late Cretaceous to Eocene "
        "volcanism in northeastern Hokkaido and offshore Japan, and "
        "implications for the Emperor seamount chain. ODP Leg 145 "
        "site reports. Meiji Seamount 85 Myr basement age."
    ),
    "o_connor_2013": (
        "O'Connor J. M. et al. (2013). Constraints on past plate and "
        "mantle motion from new ages for the Hawaiian-Emperor seamount "
        "chain. Geochem. Geophys. Geosyst. 14, 4564-4584. "
        "DOI: 10.1002/ggge.20267. Refined ages including Kammu."
    ),
    "clague_dalrymple_1989": (
        "Clague D. A. & Dalrymple G. B. (1989). Tectonics, "
        "geochronology, and origin of the Hawaiian-Emperor "
        "Volcanic Chain. In *The Geology of North America*, vol. N "
        "(Pacific Region), 188-217. Pearl-and-Hermes, Laysan, "
        "Necker, Niihau ages."
    ),
    "garcia_2010": (
        "Garcia M. O. et al. (2010). Petrology, geochemistry and "
        "geochronology of Kauai lavas over 4.5 Myr: implications for "
        "the origin of rejuvenated volcanism and the evolution of the "
        "Hawaiian plume. J. Petrol. 51, 1507-1540. "
        "DOI: 10.1093/petrology/egq027. Kauai, Oahu, Big Island."
    ),
    "clague_2010": (
        "Clague D. A. (2010). Geochronology and geochemistry of "
        "Hawaiian shield volcanism. Hawaiian Volcano Observatory + "
        "USGS data compilations. Molokai, Maui shield ages."
    ),
    "morgan_1971": (
        "Morgan W. J. (1971). Convection plumes in the lower mantle. "
        "Nature 230, 42-43. DOI: 10.1038/230042a0. The original "
        "mantle-plume hypothesis applied to Hawaii — context for "
        "the Pacific-Plate-over-stationary-plume interpretation."
    ),
    "tarduno_2003": (
        "Tarduno J. A. et al. (2003). The Emperor seamounts: "
        "southward motion of the Hawaiian hotspot plume in Earth's "
        "mantle. Science 301, 1064-1069. "
        "DOI: 10.1126/science.1086442. Paleomagnetic evidence that "
        "Emperor seamounts formed at much higher paleolatitude than "
        "the present hotspot — established that the bend reflects "
        "plume motion as well as plate-motion change."
    ),
}


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "HAWAIIAN_EMPEROR_BEND_AGE_MYR",
    "HAWAIIAN_EMPEROR_BEND_AGE_UNCERTAINTY_MYR",
    "HAWAII_HOTSPOT_LAT_DEG",
    "HAWAII_HOTSPOT_LON_DEG",
    "HAWAIIAN_EMPEROR_SEAMOUNTS",
    "SOURCES",
    "Seamount",
]
