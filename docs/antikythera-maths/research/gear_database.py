"""Antikythera gear database — tooth counts with provenance.

Single source of truth for the tooth counts used throughout the project.
Three reconstructions are tabulated where they differ:

- Freeth 2021 (`Scientific Reports` 11:5821) — current authoritative,
  default for the hypothesis battery.
- Wright (2005-2012) — alternative reconstruction, consulted where it
  differs.
- Price (1974) — foundational but superseded on specific counts; included
  for historical context only.

Each entry is a ``Gear`` with fields:
- ``name``: short identifier (e.g. "b1", "e2", "127t_lunar").
- ``teeth``: dict {reconstruction_name: count} — reconstructions that do
  not specify a count are simply absent from the dict.
- ``role``: one-line semantic role (e.g. "Main sun gear", "Saros pointer").
- ``fragment``: which surviving Antikythera fragment it's attested in
  (A, B, C, D) or ``None`` if reconstructed / Freeth-inferred.
- ``notes``: provenance comment.

See also: ``astronomical_cycles.py`` for which gears drive which dials.

Design note: Only tooth counts are first-class here.  The gear-topology
DAG (who meshes with whom, on which axle) is in a dedicated structure
below; the DAG is simplified to the essential meshes for hypothesis
testing and does not attempt a full mechanical reconstruction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


FREETH_2021 = "Freeth2021"
WRIGHT = "Wright"
PRICE_1974 = "Price1974"


@dataclass(frozen=True)
class Gear:
    name: str
    teeth: Dict[str, int]
    role: str
    fragment: Optional[str] = None
    notes: str = ""

    def canonical_count(self, prefer: str = FREETH_2021) -> int:
        """Return the canonical tooth count, preferring ``prefer`` if set."""
        if prefer in self.teeth:
            return self.teeth[prefer]
        # fall back to any available count
        return next(iter(self.teeth.values()))


# ---------------------------------------------------------------------------
# Main drive train + calendar
# ---------------------------------------------------------------------------

MAIN_TRAIN: List[Gear] = [
    Gear(
        name="a1",
        teeth={FREETH_2021: 48, WRIGHT: 48},
        role="Crown gear / hand-crank input (count uncertain, ~48)",
        fragment="A",
        notes="Uncertain; Freeth 2021 uses 48, Wright concurs.",
    ),
    Gear(
        name="b1",
        teeth={FREETH_2021: 224, WRIGHT: 223, PRICE_1974: 223},
        role="Main sun gear, largest surviving (4-spoked)",
        fragment="A",
        notes="Freeth 2021 argues 224 for exact Callippic alignment; Wright/Price report 223.",
    ),
    Gear(
        name="b2",
        teeth={FREETH_2021: 64},
        role="Pinion on sun gear shaft driving Metonic train",
        fragment="A",
    ),
    # Metonic train
    Gear(
        name="e2",
        teeth={FREETH_2021: 32, WRIGHT: 32},
        role="Metonic train input",
        fragment="A",
    ),
    Gear(
        name="e5",
        teeth={FREETH_2021: 53, WRIGHT: 53},
        role="Metonic train intermediate (the famous '53' — prime factor)",
        fragment="A",
        notes="Critical prime factor; 53 = 19·235/(5·95) piece of Metonic ratio.",
    ),
    Gear(
        name="k1",
        teeth={FREETH_2021: 96},
        role="Metonic train intermediate",
        fragment="A",
    ),
    Gear(
        name="e6",
        teeth={FREETH_2021: 53, WRIGHT: 53},
        role="Metonic train output partner (second 53-tooth wheel)",
        fragment="A",
    ),
    Gear(
        name="l1",
        teeth={FREETH_2021: 38},
        role="Metonic spiral driver",
        fragment="B",
    ),
    Gear(
        name="l2",
        teeth={FREETH_2021: 53},
        role="Metonic spiral driver intermediate",
        fragment="B",
    ),
    Gear(
        name="m1",
        teeth={FREETH_2021: 96},
        role="Metonic spiral output",
        fragment="B",
    ),
    Gear(
        name="metonic_display",
        teeth={FREETH_2021: 235},
        role="Metonic 235-month display scale (conceptual — spiral marks)",
        fragment="B",
        notes="Not a gear per se — 235 marks on the Metonic spiral. "
              "Included so the SSOT has the count.",
    ),
]

# ---------------------------------------------------------------------------
# Lunar system — includes the key T-breaking pin-and-slot
# ---------------------------------------------------------------------------

LUNAR_TRAIN: List[Gear] = [
    Gear(
        name="c1",
        teeth={FREETH_2021: 38, WRIGHT: 38},
        role="Lunar train input from sun gear",
        fragment="A",
    ),
    Gear(
        name="c2",
        teeth={FREETH_2021: 48, WRIGHT: 48},
        role="Lunar intermediate",
        fragment="A",
    ),
    Gear(
        name="d1",
        teeth={FREETH_2021: 24, WRIGHT: 24},
        role="Lunar drive to pin-and-slot",
        fragment="A",
    ),
    Gear(
        name="d2",
        teeth={FREETH_2021: 127, WRIGHT: 127, PRICE_1974: 127},
        role="Sidereal-month lunar gear (= 254/2)",
        fragment="A",
        notes="One of the three large primes in the mechanism (127, 223, 53). "
              "Encodes sidereal/synodic commensurability.",
    ),
    Gear(
        name="e1",
        teeth={FREETH_2021: 32},
        role="Pin-and-slot drive gear A",
        fragment="A",
    ),
    Gear(
        name="e3",
        teeth={FREETH_2021: 50, WRIGHT: 50},
        role="Pin-and-slot epicycle A (one of four 50-tooth wheels)",
        fragment="A",
    ),
    Gear(
        name="e4",
        teeth={FREETH_2021: 50, WRIGHT: 50},
        role="Pin-and-slot epicycle B",
        fragment="A",
    ),
    Gear(
        name="k2",
        teeth={FREETH_2021: 50, WRIGHT: 50},
        role="Pin-and-slot epicycle C",
        fragment="A",
    ),
    # k1 is in MAIN_TRAIN; add counterpart for pin-and-slot
    Gear(
        name="e_eccentric",
        teeth={FREETH_2021: 50, WRIGHT: 50},
        role="Pin-and-slot epicycle D (4th 50-tooth wheel in pin-and-slot)",
        fragment="A",
        notes="The pin-and-slot epicycle uses four 50-tooth wheels; one "
              "carries the offset pin that engages the slot of the driven wheel.",
    ),
    # Saros / eclipse subsystem
    Gear(
        name="f1",
        teeth={FREETH_2021: 53, WRIGHT: 53},
        role="Saros train input (another 53-tooth)",
        fragment="A",
    ),
    Gear(
        name="f2",
        teeth={FREETH_2021: 30},
        role="Saros intermediate",
        fragment="A",
    ),
    Gear(
        name="g1",
        teeth={FREETH_2021: 54},
        role="Saros intermediate",
        fragment="A",
    ),
    Gear(
        name="g2",
        teeth={FREETH_2021: 20},
        role="Saros intermediate",
        fragment="A",
    ),
    Gear(
        name="h1",
        teeth={FREETH_2021: 60},
        role="Saros spiral driver",
        fragment="A",
    ),
    Gear(
        name="h2",
        teeth={FREETH_2021: 15},
        role="Saros spiral driver intermediate",
        fragment="A",
    ),
    Gear(
        name="i1",
        teeth={FREETH_2021: 60},
        role="Saros spiral output",
        fragment="A",
    ),
    Gear(
        name="saros_display",
        teeth={FREETH_2021: 223},
        role="Saros 223-month display scale (conceptual — spiral marks)",
        fragment="B",
        notes="223 is prime — one of the three large primes.  It is a genuine "
              "fact of celestial mechanics, not a design choice.",
    ),
    Gear(
        name="exeligmos_display",
        teeth={FREETH_2021: 669},
        role="Exeligmos 669-month scale (conceptual — 3 × Saros)",
        fragment="B",
        notes="669 = 3 · 223.  The factor of 3 makes Exeligmos a clean "
              "harmonic of Saros.",
    ),
]

# ---------------------------------------------------------------------------
# Planetary system (Freeth 2021 reconstruction — treat as NOVEL)
# ---------------------------------------------------------------------------

PLANETARY: List[Gear] = [
    Gear(
        name="frag_d_63",
        teeth={FREETH_2021: 63, WRIGHT: 63},
        role="Fragment D 63-tooth gear (Venus/planetary)",
        fragment="D",
        notes="63 = 7·9 = 7·3^2.  The 7 is shared with other planetary trains "
              "per Freeth 2021 (H-A2 load-bearing).",
    ),
    # Venus period-relation encoding
    Gear(
        name="venus_289",
        teeth={FREETH_2021: 289},
        role="Venus 289-synodic-period numerator (conceptual)",
        fragment=None,
        notes="Not attested physically; Freeth 2021 derives 289 = 17^2 from the "
              "proposed (289, 462) period relation.  See cycle table.",
    ),
    Gear(
        name="venus_462",
        teeth={FREETH_2021: 462},
        role="Venus 462-year denominator (conceptual)",
        fragment=None,
        notes="462 = 2·3·7·11; Freeth 2021 proposes shared factor 7 with other "
              "planets and shared factor 11 as the Venus-specific discriminator.",
    ),
    Gear(
        name="saturn_427",
        teeth={FREETH_2021: 427},
        role="Saturn 427-synodic-period numerator (conceptual)",
        fragment=None,
        notes="Not attested; Freeth 2021 derives 427 = 7·61 from (427, 442).",
    ),
    Gear(
        name="saturn_442",
        teeth={FREETH_2021: 442},
        role="Saturn 442-year denominator (conceptual)",
        fragment=None,
        notes="442 = 2·13·17; shared factor 17 with Venus (289 = 17^2).",
    ),
    # Mars (per Freeth 2021 proposed reconstruction)
    Gear(
        name="mars_133",
        teeth={FREETH_2021: 133},
        role="Mars synodic numerator (conceptual)",
        fragment=None,
        notes="133 = 7·19; 7 is shared planetary prime.",
    ),
    Gear(
        name="mars_125",
        teeth={FREETH_2021: 125},
        role="Mars synodic denominator (conceptual)",
        fragment=None,
        notes="125 = 5^3 (Greek was precise on Mars synodic BUT lacked equants).",
    ),
    # Jupiter
    Gear(
        name="jupiter_76",
        teeth={FREETH_2021: 76},
        role="Jupiter synodic numerator (conceptual)",
        fragment=None,
        notes="76 = 4·19.  Shared factor 19 with Metonic.",
    ),
    Gear(
        name="jupiter_83",
        teeth={FREETH_2021: 83},
        role="Jupiter synodic denominator (conceptual)",
        fragment=None,
        notes="83 is prime.",
    ),
    # Mercury
    Gear(
        name="mercury_145",
        teeth={FREETH_2021: 145},
        role="Mercury synodic numerator (conceptual)",
        fragment=None,
        notes="145 = 5·29.",
    ),
    Gear(
        name="mercury_46",
        teeth={FREETH_2021: 46},
        role="Mercury synodic denominator (conceptual)",
        fragment=None,
        notes="46 = 2·23.",
    ),
]


# ---------------------------------------------------------------------------
# Assembled database
# ---------------------------------------------------------------------------

ALL_GEARS: List[Gear] = MAIN_TRAIN + LUNAR_TRAIN + PLANETARY


def gear_by_name(name: str) -> Gear:
    """Look up a gear by name."""
    for g in ALL_GEARS:
        if g.name == name:
            return g
    raise KeyError(f"No gear named {name!r}")


def tooth_count_list(reconstruction: str = FREETH_2021,
                     include_planetary: bool = True) -> List[int]:
    """List of all tooth counts under a given reconstruction.

    If ``include_planetary`` is False, the (more speculative) planetary
    period-relation counts are omitted — useful for tests that should only
    reflect physically-attested counts.
    """
    gears = MAIN_TRAIN + LUNAR_TRAIN
    if include_planetary:
        gears = gears + PLANETARY
    out: List[int] = []
    for g in gears:
        if reconstruction in g.teeth:
            out.append(g.teeth[reconstruction])
    return out


def known_disagreements() -> List[Tuple[str, Dict[str, int]]]:
    """Gears where reconstructions disagree on tooth count."""
    out: List[Tuple[str, Dict[str, int]]] = []
    for g in ALL_GEARS:
        counts = set(g.teeth.values())
        if len(counts) > 1:
            out.append((g.name, dict(g.teeth)))
    return out


# ---------------------------------------------------------------------------
# Gear-topology edges (simplified — essential meshes for hypothesis testing)
# ---------------------------------------------------------------------------
#
# Each edge is (driver, driven, ratio_hint).  Ratio hint is optional and
# primarily for the graph export; actual ratios are computed from tooth
# counts at runtime.  Axle-sharing is encoded by an edge with ratio None.

MESH_EDGES: List[Tuple[str, str, Optional[str]]] = [
    # Main drive
    ("a1", "b1", "crank -> sun"),
    ("b1", "b2", None),                      # axle
    ("b2", "e2", "sun -> Metonic input"),
    ("e2", "e5", "-> first 53"),
    ("e5", "k1", "53 -> 96"),
    ("k1", "e6", None),                      # axle
    ("e6", "l1", "second 53 -> 38"),
    ("l1", "l2", None),                      # axle
    ("l2", "m1", "53 -> 96 metonic output"),
    # Lunar
    ("b1", "c1", "sun -> lunar 38"),
    ("c1", "c2", None),
    ("c2", "d1", "-> 24"),
    ("d1", "d2", "24 -> 127 (sidereal)"),
    ("d2", "e1", "127 -> 32 pin-and-slot drive"),
    ("e1", "e3", "pin-and-slot epicycle A"),
    ("e3", "e4", "pin-and-slot epicycle B (offset)"),
    ("e4", "k2", "pin-and-slot epicycle C"),
    # Saros
    ("e5", "f1", "53 -> 53 Saros input"),
    ("f1", "f2", None),
    ("f2", "g1", "-> 54"),
    ("g1", "g2", None),
    ("g2", "h1", "-> 60"),
    ("h1", "h2", None),
    ("h2", "i1", "-> 60 Saros output"),
]


if __name__ == "__main__":
    # Quick provenance / consistency report when run standalone.
    print(f"Antikythera gear database")
    print(f"  Main train gears:      {len(MAIN_TRAIN)}")
    print(f"  Lunar train gears:     {len(LUNAR_TRAIN)}")
    print(f"  Planetary gears:       {len(PLANETARY)}")
    print(f"  Total:                 {len(ALL_GEARS)}")
    print(f"  Unique Freeth counts:  {sorted(set(tooth_count_list(FREETH_2021)))}")
    print()
    print("Reconstruction disagreements:")
    for name, counts in known_disagreements():
        print(f"  {name:20s}  {counts}")
    print()
    print("Mesh edges:", len(MESH_EDGES))
