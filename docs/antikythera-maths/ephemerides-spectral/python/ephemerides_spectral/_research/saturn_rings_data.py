"""Saturn ring system — hand-coded data module (v0.24.x discipline).

Phase 3 of the dual-author Saturn ring exercise (PR #284 backfill
review). The same 12 ring-feature rows that the AMSC literature_curated
catalogue ships at ``research/attested/saturn_rings/ring_feature.ndjson``
are also encoded here in the v0.24.x ``_research/<topic>_data.py`` style:
inline @dataclass + List + SOURCES dict, hand-authored from the cited
literature.

Why both
--------
The pre-v1.0 architectural review (PR #284 ROADMAP entry) asks
whether to migrate the v0.24.x hand-coded catalogues to AMSC-backed
NDJSON before declaring v1.0 stable. The decision is MPM-screened,
not architect-driven: each catalogue is dual-authored once, and the
two paths' resulting NDJSON output is diff-checked. Agreement is
empirical evidence the descriptor schema is rich enough; specific
divergences are the data the screening exposes.

Saturn rings is the first dual-author exercise. This module is the
hand-coded path; the AMSC path lives at
``research/attested/saturn_rings/`` (descriptor.toml + NDJSON +
schema). The diff test in ``tests/test_saturn_rings_dual_author.py``
loads both, normalises them to the same dict shape, and asserts
field-by-field agreement on every row.

What dual-author validates
--------------------------
- The descriptor schema can express what the v0.24.x ``_data.py``
  pattern expressed (every numeric / categorical field round-trips).
- The literature_curated adapter's NDJSON shape matches what an
  inline @dataclass + List would have produced.
- Schema additions (per-row date/version fields from PR #289) are
  consistent across both paths — no field is "AMSC only" or
  "hand-coded only" at this row granularity.
- New rows added to one path can be immediately mirrored to the
  other; divergence between paths surfaces as test failure.

Sources cited (per-row source DOIs in the catalogue match these):

* **Tiscareno 2013** *Annu. Rev. Earth Planet. Sci.* 41:289-316.
  DOI 10.1146/annurev-earth-050212-124230. Saturn ring structure
  review. Cited for: Cassini Division inner edge, A-ring outer
  edge, B-ring inner edge, C-ring outer edge.
* **Showalter 1991** *Nature* 351:709-713. DOI 10.1038/351709a0.
  Pan discovery from Voyager imagery. Cited for: Encke Gap, Pan.
* **Porco et al. 2005** *Science* 307:1226-1236. DOI
  10.1126/science.1108993. Daphnis discovery from Cassini imagery.
  Cited for: Keeler Gap, Daphnis.
* **Spitale & Porco 2009** *AJ* 138:1520-1528. DOI
  10.1088/0004-6256/138/5/1520. F-ring shepherd modulation
  modelling. Cited for: F-ring core, Prometheus, Pandora.
* **Murray-Dermott 1999** *Solar System Dynamics*, Cambridge UP.
  ISBN 978-0521575973. Textbook Lindblad resonance derivation.
  Cited for: Mimas 2:1 mean-motion resonance anchor.

Cross-references
----------------
* AMSC path: ``research/attested/saturn_rings/`` — descriptor TOML +
  JSON Schema + NDJSON. The literature_curated adapter consumes the
  NDJSON; bridge.get_attested_dataset("saturn_rings") returns the
  same row content this module encodes.
* Notebook §18.4 — descriptor schema spec.
* Notebook §18.9 — applicability of AMSC beyond classic spectral
  targets.
* PR #284 — pre-v1.0 backfill review (MPM-screened decision pending).
* PR #286 — Phase 1 ship (AMSC literature_curated adapter +
  saturn_rings descriptor + 12-row bootstrap NDJSON).
* PR #289 — Phase 2 ship (per-row date/version fields + SSOT-driven
  validation simulation + J₂-corrected Kepler).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Row dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RingFeature:
    """One Saturn ring-system feature.

    Mirrors the ``saturn_rings.ring_feature.v1`` JSON Schema (see
    ``research/attested/saturn_rings/ring_feature.schema.json``).
    Required fields are the ones every feature shares; optional
    fields are populated where the feature_type and the cited source
    supply them.
    """

    name: str
    feature_type: str          # "ring_boundary" | "ring_gap" | "resonance_anchor" | "shepherd_moon" | "ring_edge_structure"
    radial_distance_km: float
    source_doi: str
    source_published_date: str
    entered_locally_at: str
    width_km: Optional[float] = None
    associated_body: Optional[str] = None
    resonance_p: Optional[int] = None
    resonance_q: Optional[int] = None
    regime_label: Optional[str] = None
    source_version: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Saturn ring features — 12 rows
# ---------------------------------------------------------------------------

SATURN_RING_FEATURES: List[RingFeature] = [

    RingFeature(
        name="Cassini Division inner edge",
        feature_type="ring_boundary",
        radial_distance_km=117580.0,
        width_km=4500.0,
        associated_body="mimas",
        resonance_p=2,
        resonance_q=1,
        regime_label="rigid_body_action_angle_stable",
        source_doi="10.1146/annurev-earth-050212-124230",
        source_published_date="2013-05-30",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="B-ring outer edge / Cassini Division inner edge sustained by 2:1 inner Lindblad resonance with Mimas. Tiscareno 2013 review cites canonical location; Murray-Dermott 1999 §10.4 derives the location from Mimas's mean motion.",
    ),

    RingFeature(
        name="A-ring outer edge",
        feature_type="ring_boundary",
        radial_distance_km=136775.0,
        width_km=None,
        associated_body="janus_epimetheus",
        resonance_p=7,
        resonance_q=6,
        regime_label="rigid_body_action_angle_mutual_lock",
        source_doi="10.1146/annurev-earth-050212-124230",
        source_published_date="2013-05-30",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="A-ring outer edge confined by 7:6 inner Lindblad resonance with the Janus-Epimetheus co-orbital pair. The shared-resonance shape is itself a v0.24.x rigid-body-mutual-lock signature (cousin of v0.24.11 Pluto-Charon). Saturn J₂ shifts the predicted Kepler location; the ~1.5% offset from naïve Kepler is the diagnostic the validation simulation will surface.",
    ),

    RingFeature(
        name="Encke Gap",
        feature_type="ring_gap",
        radial_distance_km=133589.0,
        width_km=325.0,
        associated_body="pan",
        resonance_p=None,
        resonance_q=None,
        regime_label="rigid_body_action_angle_stable",
        source_doi="10.1038/351709a0",
        source_published_date="1991-09-26",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="Embedded gap maintained by the embedded shepherd Pan. Showalter 1991 — discovery of Pan from Voyager imagery; Pan's gravity opens the ~325 km gap and accumulates a tenuous ringlet at its co-orbital L4/L5 points.",
    ),

    RingFeature(
        name="Keeler Gap",
        feature_type="ring_gap",
        radial_distance_km=136505.0,
        width_km=35.0,
        associated_body="daphnis",
        resonance_p=None,
        resonance_q=None,
        regime_label="rigid_body_action_angle_stable",
        source_doi="10.1126/science.1108993",
        source_published_date="2005-05-06",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="Embedded gap maintained by Daphnis. Porco et al. 2005 — Daphnis discovery from Cassini imagery. The ~35 km gap is far narrower than the Encke; Daphnis's smaller mass (relative to Pan) is the ratio.",
    ),

    RingFeature(
        name="Pan",
        feature_type="shepherd_moon",
        radial_distance_km=133584.0,
        width_km=None,
        associated_body="pan",
        resonance_p=None,
        resonance_q=None,
        regime_label="rigid_body_action_angle_stable",
        source_doi="10.1038/351709a0",
        source_published_date="1991-09-26",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="Shepherd moon that maintains the Encke Gap. Ravioli-shaped equatorial ridge accreted from ring particles (Charnoz 2007). Mean orbital radius cited from JPL HORIZONS / IAU 2015.",
    ),

    RingFeature(
        name="Daphnis",
        feature_type="shepherd_moon",
        radial_distance_km=136505.0,
        width_km=None,
        associated_body="daphnis",
        resonance_p=None,
        resonance_q=None,
        regime_label="rigid_body_action_angle_stable",
        source_doi="10.1126/science.1108993",
        source_published_date="2005-05-06",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="Shepherd moon that maintains the Keeler Gap. Discovery via Cassini imagery (Porco et al. 2005). Daphnis's eccentric/inclined orbit produces the famous edge-wave structure on the Keeler gap walls — visible as scalloping in ISS images.",
    ),

    RingFeature(
        name="F-ring core",
        feature_type="ring_boundary",
        radial_distance_km=140180.0,
        width_km=50.0,
        associated_body="prometheus_pandora",
        resonance_p=None,
        resonance_q=None,
        regime_label="temporal_quasi_periodic_cycle",
        source_doi="10.1088/0004-6256/138/5/1520",
        source_published_date="2009-11-01",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="F-ring core radius (Spitale & Porco 2009). Quasi-periodic temporal modulation driven by the orbital beat between the two shepherd moons (Prometheus inner, Pandora outer). The temporal regime label connects this row to v0.24.8 Axial Seamount and v0.24.12 Loki Patera as cross-system temporal-cycle exemplars.",
    ),

    RingFeature(
        name="Prometheus",
        feature_type="shepherd_moon",
        radial_distance_km=139380.0,
        width_km=None,
        associated_body="prometheus",
        resonance_p=None,
        resonance_q=None,
        regime_label="temporal_quasi_periodic_cycle",
        source_doi="10.1088/0004-6256/138/5/1520",
        source_published_date="2009-11-01",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="F-ring inner shepherd. Spitale & Porco 2009 modelling shows Prometheus's orbital motion drags streamers from F-ring core every synodic-period encounter — direct temporal-cycle observable.",
    ),

    RingFeature(
        name="Pandora",
        feature_type="shepherd_moon",
        radial_distance_km=141720.0,
        width_km=None,
        associated_body="pandora",
        resonance_p=None,
        resonance_q=None,
        regime_label="temporal_quasi_periodic_cycle",
        source_doi="10.1088/0004-6256/138/5/1520",
        source_published_date="2009-11-01",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="F-ring outer shepherd. Spitale & Porco 2009 — together with Prometheus, the synodic period defines the F-ring's quasi-periodic structural modulation. Cross-channel observation: same shape as Janus-Epimetheus mutual coupling, applied to a ring rather than an outer-edge confinement.",
    ),

    RingFeature(
        name="Mimas 2:1 mean-motion resonance anchor",
        feature_type="resonance_anchor",
        radial_distance_km=116930.0,
        width_km=None,
        associated_body="mimas",
        resonance_p=2,
        resonance_q=1,
        regime_label="rigid_body_action_angle_stable",
        source_doi="isbn:978-0521575973",
        source_published_date="1999-02-13",
        entered_locally_at="2026-05-08",
        source_version="1st edition",
        notes="Predicted location of the 2:1 inner Lindblad resonance with Mimas: a_resonance = a_Mimas * (1/2)^(2/3) = 185539 * 0.6300 = 116930 km. Naïve Kepler — does not include Saturn J₂ correction. Compared to the observed Cassini Division inner edge (117580 km), the offset (~650 km) is the J₂-induced shift; the validation simulation reproduces the offset closed-form. Source: Murray-Dermott 1999 *Solar System Dynamics* Cambridge UP, §8.6 + §10.4.",
    ),

    RingFeature(
        name="B-ring inner edge",
        feature_type="ring_boundary",
        radial_distance_km=92000.0,
        width_km=None,
        associated_body=None,
        resonance_p=None,
        resonance_q=None,
        regime_label="bounded_local_laplacian_family",
        source_doi="10.1146/annurev-earth-050212-124230",
        source_published_date="2013-05-30",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="B-ring inner boundary. Tiscareno 2013 review. Not maintained by a single resonance — a structural boundary of the densest part of the rings. Connected to the bounded-local-Laplacian family regime via the ring system's spectral structure (the ring as a continuous structure with eigenmode spacing set by Saturn's gravitational potential).",
    ),

    RingFeature(
        name="C-ring outer edge",
        feature_type="ring_boundary",
        radial_distance_km=91975.0,
        width_km=None,
        associated_body=None,
        resonance_p=None,
        resonance_q=None,
        regime_label="bounded_local_laplacian_family",
        source_doi="10.1146/annurev-earth-050212-124230",
        source_published_date="2013-05-30",
        entered_locally_at="2026-05-08",
        source_version=None,
        notes="C-ring outer boundary, immediately interior to the B-ring inner edge. Tiscareno 2013 review. The C-ring/B-ring transition is the optical-depth jump from ~0.1 to ~1+ — historically the basis for distinguishing the two rings.",
    ),

]


# ---------------------------------------------------------------------------
# Source citation roster
# ---------------------------------------------------------------------------

SOURCES: Dict[str, str] = {
    "tiscareno_2013_annual_review": (
        "Tiscareno M.S. (2013). Planetary rings. *Annu. Rev. Earth "
        "Planet. Sci.* 41:289-316. "
        "DOI: 10.1146/annurev-earth-050212-124230."
    ),
    "showalter_1991_pan_discovery": (
        "Showalter M.R. (1991). Visual detection of 1981S13, "
        "Saturn's eighteenth satellite, and its role in the Encke "
        "gap. *Nature* 351:709-713. DOI: 10.1038/351709a0."
    ),
    "porco_2005_daphnis_discovery": (
        "Porco C.C. et al. (2005). Cassini imaging science: initial "
        "results on Saturn's rings and small satellites. *Science* "
        "307:1226-1236. DOI: 10.1126/science.1108993."
    ),
    "spitale_porco_2009_fring": (
        "Spitale J.N., Porco C.C. (2009). Time variability in "
        "Saturn's F ring. *AJ* 138:1520-1528. "
        "DOI: 10.1088/0004-6256/138/5/1520."
    ),
    "murray_dermott_1999_textbook": (
        "Murray C.D., Dermott S.F. (1999). *Solar System Dynamics*. "
        "Cambridge University Press. ISBN 978-0521575973. "
        "Textbook reference for Lindblad resonance derivations."
    ),
}


def feature_to_data_dict(feature: RingFeature) -> Dict[str, object]:
    """Convert a hand-coded RingFeature to the same dict shape that
    bridge.get_attested_dataset('saturn_rings') returns in each row's
    `data` block.

    Used by the dual-author diff test in
    tests/test_saturn_rings_dual_author.py to normalise the two paths
    to a comparable shape before field-by-field comparison.

    The dict order matches the JSON Schema field declaration order
    (which the AMSC NDJSON also follows on commit), so a sorted-key
    comparison agrees byte-for-byte.
    """
    return {
        "name": feature.name,
        "feature_type": feature.feature_type,
        "radial_distance_km": feature.radial_distance_km,
        "width_km": feature.width_km,
        "associated_body": feature.associated_body,
        "resonance_p": feature.resonance_p,
        "resonance_q": feature.resonance_q,
        "regime_label": feature.regime_label,
        "source_doi": feature.source_doi,
        "source_published_date": feature.source_published_date,
        "entered_locally_at": feature.entered_locally_at,
        "source_version": feature.source_version,
        "notes": feature.notes,
    }


__all__ = [
    "RingFeature",
    "SATURN_RING_FEATURES",
    "SOURCES",
    "feature_to_data_dict",
]
