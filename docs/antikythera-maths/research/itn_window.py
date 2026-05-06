"""ITN pathway / Lagrange-tube window search (v0.8.x).

Mirrors the v0.3.1 ``find-syzygies`` discipline for the
**Interplanetary Transport Network**: enumerate launch windows in
closed-form from anchor body geometry, mirroring how
`find_syzygies` enumerates new-moon multiples from the
``LUNAR_REFERENCE_NEW_MOON_JD_TDB`` anchor.

First-cut implementation
========================

Full ITN tubes are stable/unstable manifolds of Lyapunov / halo
orbits in the Circular Restricted Three-Body Problem (CR3BP) — the
canonical Koon/Lo/Marsden/Ross 2011 framework. That's a multi-month
research-code lift.

This module ships the **closed-form Hohmann transfer-window
enumeration** as the first useful surface — the Hohmann window is
the lowest-effort transfer between two bodies and serves as the
analog of synodic-month enumeration in `find_syzygies`. The fields
``transfer_kind = "hohmann"`` and the placeholder ``gateway_lp =
"transfer-ellipse"`` reserve room for future low-energy /
heteroclinic-tube candidates that will land under the same surface.

The mathematical-physics framing
================================

For two bodies orbiting the Sun on near-circular orbits with
periods ``P_dep`` and ``P_tgt``:

  - **Synodic period** ``T_syn = 2π / |n_dep − n_tgt|`` where ``n``
    is mean motion (rad/day). Launch windows recur every T_syn.
  - **Hohmann transfer time** ``T_h = π × √(a_h³ / GM_sun)`` where
    ``a_h = (a_dep + a_tgt) / 2`` is the semi-major axis of the
    transfer ellipse. Half an ellipse: 180° around the Sun.
  - **Launch phase angle** Δφ_launch — the target must be ahead of
    departure by ``π − n_tgt × T_h`` at launch (so the target ends
    up exactly 180° around the Sun by the time the spacecraft
    arrives). For inner transfers (target at smaller orbit) the
    angle wraps negative — target behind departure.

The natural-symphony framing: each (dep, tgt) pair has a
gear-ratio relationship ``n_dep / n_tgt`` whose synodic beat is
the Hohmann window cadence. This module reads each body's mean
motion from the encoder's ``BODIES`` table and the J2000 mean
longitude from ``_data/initial_phases.json`` (the codegen-baked
output of v0.5.0+'s SPICE-free runtime).

Future extensions
=================

Once the Hohmann anchor is in place, follow-ups can layer:

  - **L1/L2 gateway designation** per CR3BP geometry of (dep, tgt)
    pair. Each gateway has a specific Jacobi constant; emit it as
    a candidate field.
  - **Multi-leg heteroclinic chains** — Sun-Earth L2 → Sun-Mars L1
    → Mars surface, etc. Combinatorial enumeration over the gateway
    graph; each leg an ITNCandidate.
  - **Energy-budget filtering** — only emit candidates whose
    cumulative Δv fits a caller-supplied budget.
  - **Ballistic-capture windows** at planetary L1 — Belbruno-style
    low-energy lunar capture, generalized.

Each future extension keeps the same dataclass + bridge surface;
only the `transfer_kind` enum + supplementary fields grow.

References
==========

  * Koon, Lo, Marsden, Ross (2011) — *Dynamical Systems, the
    Three-Body Problem and Space Mission Design.*
  * Lo (1997) — Genesis spacecraft trajectory design via L1/L2
    manifolds (the first practical use of ITN for a real mission).
  * Conley (1968) — manifold-connection theorems, the original
    mathematical foundation.

API
===

``find_itn_pathways(jd_lo, jd_hi, departure, target, ...)``
  Returns a list of :class:`ITNCandidate`.
  Closed-form synodic enumeration; no encoder calls.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .bodies import BODIES


# Reference JD for the body initial-phase calibration. Same as
# bip_instrument.REFERENCE_JD = J2000.0.
_REFERENCE_JD: float = 2451545.0

# Conversion factor for AU/yr velocity → km/s. Used in Hohmann Δv.
_AU_PER_YEAR_TO_KM_PER_SEC: float = 149_597_870.7 / (365.25 * 86400.0)

# AU³/yr² in heliocentric units; equals 4π² in those units (Kepler's 3rd).
_GM_SUN_AU3_YR2: float = 4.0 * math.pi * math.pi


@dataclass(frozen=True)
class ITNCandidate:
    """One ITN launch-window candidate.

    ``transfer_kind`` is "hohmann" in v0.8.x; future versions add
    "low-energy-l1", "heteroclinic-chain", etc. The dataclass shape
    is forward-compatible — extra fields can be added without
    breaking the JSON contract.
    """
    jd_tdb: float
    departure: str
    target: str
    transfer_kind: str
    transfer_time_days: float
    launch_phase_angle_deg: float
    actual_phase_angle_deg: float
    phase_residual_deg: float
    score: float
    estimated_dv_kms: float
    synodic_period_days: float
    gateway_lp: str = "transfer-ellipse"

    def to_dict(self) -> Dict[str, object]:
        return {
            "jd_tdb": float(self.jd_tdb),
            "departure": str(self.departure),
            "target": str(self.target),
            "transfer_kind": str(self.transfer_kind),
            "transfer_time_days": float(self.transfer_time_days),
            "launch_phase_angle_deg": float(self.launch_phase_angle_deg),
            "actual_phase_angle_deg": float(self.actual_phase_angle_deg),
            "phase_residual_deg": float(self.phase_residual_deg),
            "score": float(self.score),
            "estimated_dv_kms": float(self.estimated_dv_kms),
            "synodic_period_days": float(self.synodic_period_days),
            "gateway_lp": str(self.gateway_lp),
        }


def hohmann_transfer_time_days(period_dep_days: float,
                               period_tgt_days: float) -> float:
    """Half-period of a Hohmann transfer ellipse between two
    circular orbits with the given periods (days).

    Math: ``a_h = (a_dep + a_tgt) / 2``, where ``a_x = (T_x_yr)^(2/3)``
    in AU. Then ``T_h_yr = √(a_h³) / 2`` (half a period of the
    transfer ellipse).
    """
    p_dep_yr = period_dep_days / 365.25
    p_tgt_yr = period_tgt_days / 365.25
    a_dep = p_dep_yr ** (2.0 / 3.0)
    a_tgt = p_tgt_yr ** (2.0 / 3.0)
    a_h = (a_dep + a_tgt) / 2.0
    return math.sqrt(a_h ** 3) / 2.0 * 365.25


def hohmann_launch_phase_angle_rad(period_dep_days: float,
                                   period_tgt_days: float) -> float:
    """Required target-ahead-of-departure phase angle at Hohmann
    launch, radians.

    Positive value: target leads departure (outer transfer like
    Earth → Mars). Negative: target trails (inner transfer like
    Mars → Earth).

    Wrapped to [-π, π].
    """
    t_h = hohmann_transfer_time_days(period_dep_days, period_tgt_days)
    n_tgt = 2.0 * math.pi / period_tgt_days
    angle = math.pi - n_tgt * t_h
    # Wrap to [-π, π].
    return ((angle + math.pi) % (2.0 * math.pi)) - math.pi


def hohmann_total_dv_kms(period_dep_days: float,
                         period_tgt_days: float) -> float:
    """Total Hohmann Δv = |v_transfer_dep − v_circ_dep| + |v_transfer_tgt − v_circ_tgt|.

    In km/s, derived via vis-viva equation with heliocentric orbits
    only (no planetary gravity well — escape Δv from a planetary
    parking orbit is body-specific and not included here).
    """
    p_dep_yr = period_dep_days / 365.25
    p_tgt_yr = period_tgt_days / 365.25
    a_dep = p_dep_yr ** (2.0 / 3.0)
    a_tgt = p_tgt_yr ** (2.0 / 3.0)
    a_h = (a_dep + a_tgt) / 2.0

    v_c_dep = math.sqrt(_GM_SUN_AU3_YR2 / a_dep)
    v_t_dep = math.sqrt(_GM_SUN_AU3_YR2 * (2.0 / a_dep - 1.0 / a_h))
    dv1 = abs(v_t_dep - v_c_dep)

    v_c_tgt = math.sqrt(_GM_SUN_AU3_YR2 / a_tgt)
    v_t_tgt = math.sqrt(_GM_SUN_AU3_YR2 * (2.0 / a_tgt - 1.0 / a_h))
    dv2 = abs(v_t_tgt - v_c_tgt)

    return (dv1 + dv2) * _AU_PER_YEAR_TO_KM_PER_SEC


def synodic_period_days(period_a_days: float,
                        period_b_days: float) -> float:
    """Synodic period of two bodies. Always positive."""
    n_a = 2.0 * math.pi / period_a_days
    n_b = 2.0 * math.pi / period_b_days
    diff = abs(n_a - n_b)
    if diff < 1e-30:
        raise ValueError(
            "bodies have identical orbital periods; no synodic structure"
        )
    return 2.0 * math.pi / diff


def _load_initial_phases() -> Dict[str, int]:
    """Load body → uint32 J2000 mean-longitude residue from the
    codegen-baked initial_phases.json. Cached on first call.
    """
    global _INITIAL_PHASES_CACHE
    if _INITIAL_PHASES_CACHE is not None:
        return _INITIAL_PHASES_CACHE
    candidates = [
        # Published package location (when running from installed pkg).
        Path(__file__).resolve().parent.parent
        / "ephemerides-spectral" / "python"
        / "ephemerides_spectral" / "_data" / "initial_phases.json",
        # Direct package data (when running as installed package).
        Path(__file__).resolve().parent.parent
        / "_data" / "initial_phases.json",
    ]
    for p in candidates:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            _INITIAL_PHASES_CACHE = data["initial_phases"]
            return _INITIAL_PHASES_CACHE
    raise FileNotFoundError(
        "initial_phases.json not found in any expected location; "
        "run codegen/regenerate.py to emit it"
    )


_INITIAL_PHASES_CACHE: Optional[Dict[str, int]] = None


def _phi_at_jd_rad(body: str, jd_tdb: float) -> float:
    """Mean longitude of `body` at `jd_tdb` (TDB), in radians [0, 2π).

    Linear extrapolation from the J2000 anchor + 2π/period_days.
    Mirrors the BIP encoder's diagonal evolution (no breathing).
    """
    phases = _load_initial_phases()
    if body not in phases:
        raise ValueError(f"unknown body {body!r}")
    body_info = BODIES.get(body)
    if body_info is None or body_info.period_days <= 0.0:
        raise ValueError(f"body {body!r} has no orbital period in BODIES")
    phi0_rad = (phases[body] / float(1 << 32)) * 2.0 * math.pi
    n = 2.0 * math.pi / body_info.period_days
    delta = jd_tdb - _REFERENCE_JD
    return (phi0_rad + n * delta) % (2.0 * math.pi)


def _wrap_signed(x: float, half_period: float) -> float:
    """Wrap `x` into [-half_period, +half_period]."""
    full = 2.0 * half_period
    y = (x + half_period) % full
    return y - half_period


def find_itn_pathways(
    jd_lo: float,
    jd_hi: float,
    *,
    departure: str,
    target: str,
    threshold: float = 0.05,
    max_candidates: int = 1000,
) -> List[ITNCandidate]:
    """Enumerate Hohmann launch windows in [jd_lo, jd_hi] (TDB).

    Parameters
    ----------
    jd_lo, jd_hi : float
        Window boundaries in JD (TDB).
    departure, target : str
        Body names. Both must orbit the Sun (planet, dwarf-planet,
        or asteroid in BODIES); moon → moon transfers will require
        a future extension.
    threshold : float
        Score cutoff in [0, 1]. ``score = |phase_residual| / π``.
        0.05 → target within ~9° of ideal Hohmann phase angle (a
        wide first-quarter window). 0.02 → ~3.6° (tight window).
    max_candidates : int
        Safety cap for very-loose thresholds + multi-millennium windows.

    Returns
    -------
    List[ITNCandidate]
        Ordered by ``jd_tdb`` ascending. Empty if no windows in
        range or if the synodic period is degenerate.
    """
    if departure == target:
        raise ValueError("departure and target must differ")
    if jd_hi < jd_lo:
        raise ValueError(f"jd_hi {jd_hi} < jd_lo {jd_lo}")
    if threshold <= 0.0 or threshold > 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")
    dep_info = BODIES.get(departure)
    tgt_info = BODIES.get(target)
    if dep_info is None or tgt_info is None:
        raise ValueError(
            f"unknown body: departure={departure!r}, target={target!r}"
        )
    if dep_info.period_days <= 0.0 or tgt_info.period_days <= 0.0:
        raise ValueError("both bodies must have positive orbital periods")

    p_dep = dep_info.period_days
    p_tgt = tgt_info.period_days
    t_syn = synodic_period_days(p_dep, p_tgt)
    t_h = hohmann_transfer_time_days(p_dep, p_tgt)
    phi_launch = hohmann_launch_phase_angle_rad(p_dep, p_tgt)
    dv = hohmann_total_dv_kms(p_dep, p_tgt)

    # Solve for first jd_anchor where Δφ(jd) = phi_launch.
    # Δφ(jd) = phi_tgt(jd) - phi_dep(jd)
    #        = (phi_tgt0 - phi_dep0) + (n_tgt - n_dep) × (jd - REFERENCE_JD)
    phi_dep0 = _phi_at_jd_rad(departure, _REFERENCE_JD)
    phi_tgt0 = _phi_at_jd_rad(target, _REFERENCE_JD)
    delta_phi_0 = (phi_tgt0 - phi_dep0)  # raw, not mod-2π
    n_dep = 2.0 * math.pi / p_dep
    n_tgt = 2.0 * math.pi / p_tgt
    n_rel = n_tgt - n_dep  # relative angular rate (sign matters)

    # (n_rel) × (jd - REFERENCE_JD) ≡ phi_launch - delta_phi_0 (mod 2π)
    # → (jd - REFERENCE_JD) ≡ (phi_launch - delta_phi_0) / n_rel (mod T_syn)
    # Note: n_rel can be negative (target slower than departure ⟶
    # outer-bound transfer). T_syn = |2π / n_rel|.
    days_to_first = (phi_launch - delta_phi_0) / n_rel
    days_to_first %= t_syn
    if days_to_first < 0.0:
        days_to_first += t_syn
    jd_anchor = _REFERENCE_JD + days_to_first

    # Now walk synodic multiples that lie in [jd_lo, jd_hi].
    # First k such that jd_anchor + k × T_syn ≥ jd_lo:
    k_start = math.ceil((jd_lo - jd_anchor) / t_syn)
    k_end = math.floor((jd_hi - jd_anchor) / t_syn)

    out: List[ITNCandidate] = []
    if k_end < k_start:
        return out

    for k in range(int(k_start), int(k_end) + 1):
        jd = jd_anchor + k * t_syn
        if jd < jd_lo or jd > jd_hi:
            continue
        # Compute actual relative phase at this jd; should be very
        # close to phi_launch (synodic enumeration ⟶ close by
        # construction; modular round-off is the only residual).
        phi_dep = _phi_at_jd_rad(departure, jd)
        phi_tgt = _phi_at_jd_rad(target, jd)
        actual_rad = _wrap_signed(phi_tgt - phi_dep, math.pi)
        residual_rad = _wrap_signed(actual_rad - phi_launch, math.pi)
        score = abs(residual_rad) / math.pi
        if score >= threshold:
            # Floating-point round-off pushed this synodic-multiple
            # candidate just outside the threshold; skip rather than
            # emit a stale candidate.
            continue
        out.append(ITNCandidate(
            jd_tdb=float(jd),
            departure=departure,
            target=target,
            transfer_kind="hohmann",
            transfer_time_days=float(t_h),
            launch_phase_angle_deg=float(math.degrees(phi_launch)),
            actual_phase_angle_deg=float(math.degrees(actual_rad)),
            phase_residual_deg=float(math.degrees(residual_rad)),
            score=float(score),
            estimated_dv_kms=float(dv),
            synodic_period_days=float(t_syn),
            gateway_lp="transfer-ellipse",
        ))
        if len(out) >= max_candidates:
            return out
    return out


@dataclass(frozen=True)
class ITNChainCandidate:
    """One ITN multi-leg chain candidate (v0.17.0).

    Composed of one or more single-leg :class:`ITNCandidate` Hohmann
    windows stitched end-to-end via gravity-assist / synodic-sequencing
    at intermediate bodies. The chain is "resonance-graph" because each
    leg's (departure, target) pair carries a small-integer gear ratio
    (p, q) recovered as a rational approximation of the period ratio
    -- the same kind of integer signature the BIP cyclic-group encoder
    consumes on its primary surface (notebook §6).

    The dataclass shape is forward-compatible with future leg types
    (heteroclinic-tube, weak-stability-boundary, etc.) -- the per-leg
    ``transfer_kind`` field on :class:`ITNCandidate` already reserves
    that room.
    """
    jd_tdb_launch: float
    jd_tdb_arrival: float
    legs: tuple
    """Tuple[ITNCandidate, ...] -- each leg is a v0.8.1 Hohmann window."""
    total_dv_kms: float
    total_tof_days: float
    resonance_signature: tuple
    """Tuple[Tuple[int, int], ...] -- per-leg p:q gear-ratio integer
    approximation of period_dep / period_tgt. The cross-pollination
    point with the BIP encoder's cyclic-group machinery."""
    score: float
    """Sum of per-leg phase-residual scores, lower is better. Pin a
    deterministic RMS in a future tightening pass."""

    def to_dict(self) -> Dict[str, object]:
        return {
            "jd_tdb_launch": float(self.jd_tdb_launch),
            "jd_tdb_arrival": float(self.jd_tdb_arrival),
            "legs": [leg.to_dict() for leg in self.legs],
            "total_dv_kms": float(self.total_dv_kms),
            "total_tof_days": float(self.total_tof_days),
            "resonance_signature": [list(pq) for pq in self.resonance_signature],
            "score": float(self.score),
        }


def _best_rational_approx(ratio: float, max_int: int = 30) -> tuple:
    """Best small-integer (p, q) with 1 ≤ p, q ≤ max_int minimising
    ``|p/q − ratio|``. Reduced to lowest terms via gcd.

    The returned (p, q) is the "gear ratio" in the sense
    ``p × period_dep ≈ q × period_tgt``, i.e. p revolutions of the
    departure body equal q revolutions of the target. Earth → Mars
    recovers (8, 15); Earth → Jupiter recovers (1, 12) ≈ Jupiter's
    ~12-yr orbit; Jupiter → Saturn recovers (2, 5) -- the famous
    Jupiter-Saturn 2:5 great-inequality resonance.
    """
    if ratio <= 0.0 or not math.isfinite(ratio):
        return (0, 0)
    best_p, best_q = 1, 1
    best_err = abs(1.0 - ratio)
    for q in range(1, max_int + 1):
        p = max(1, round(ratio * q))
        if p > max_int:
            continue
        err = abs(p / q - ratio)
        if err < best_err:
            best_err, best_p, best_q = err, p, q
    g = math.gcd(best_p, best_q)
    return (best_p // g, best_q // g)


def find_itn_chains(
    jd_lo: float,
    jd_hi: float,
    *,
    departure: str,
    target: str,
    intermediates: Optional[List[str]] = None,
    max_legs: int = 4,
    dv_budget_kms: float = 30.0,
    tof_budget_days: float = 365.25 * 20.0,
    threshold: float = 0.05,
    max_chains: int = 200,
    max_intermediate_windows: int = 8,
) -> List[ITNChainCandidate]:
    """Multi-leg ITN chain search via Dijkstra-style graph search on
    the (body, epoch) state space.

    Each "leg" is a closed-form Hohmann window from
    :func:`find_itn_pathways`. Legs stitch end-to-end at intermediate
    bodies; the cumulative Δv and time-of-flight are budget-bounded.
    Each leg carries a small-integer (p, q) gear-ratio "resonance
    signature" (period_dep / period_tgt as a rational), which is the
    cross-pollination point with the BIP cyclic-group encoder.

    Parameters
    ----------
    jd_lo, jd_hi : float
        Search window [jd_lo, jd_hi] in JD (TDB).
    departure, target : str
        Body names from BODIES; both must orbit the Sun.
    intermediates : Optional[List[str]]
        Bodies allowed as intermediate stops. None ⇒ all heliocentric
        bodies in BODIES (planets + dwarf planets + asteroids), minus
        ``departure`` and ``target``. Pass a smaller list to constrain
        the search; pass ``[]`` to force a single-leg direct chain.
    max_legs : int
        Hard cap on legs per chain. Default 4 — tunable for
        Cassini-class V-V-E-J-S sequences (max_legs ≥ 5).
    dv_budget_kms : float
        Cumulative-Δv ceiling. Default 30.0 km/s (loose; Earth → Pluto
        direct is ~25 km/s Hohmann, leaving room for one assist).
    tof_budget_days : float
        Cumulative time-of-flight ceiling. Default 20 yr.
    threshold : float
        Per-leg phase-residual cutoff (passed through to
        :func:`find_itn_pathways`).
    max_chains : int
        Cap on total chains returned (Dijkstra-style; lowest-Δv first).
    max_intermediate_windows : int
        Per-(body, epoch) cap on enumerated next-leg windows. Keeps the
        search tractable on multi-decade horizons; default 8 covers a
        comfortable Cassini-class search.

    Returns
    -------
    List[ITNChainCandidate]
        Chains ordered by ``total_dv_kms`` ascending (Dijkstra
        guarantees optimal-first emission). Empty if no chain fits the
        budgets.

    Notes
    -----
    Algorithm: priority-queue graph search. Each state is
    ``(current_body, current_jd, total_dv, legs)``. Successors are
    Hohmann windows from current_body to any (intermediate ∪ target),
    starting at or after current_jd. Dijkstra invariant on
    total_dv_kms guarantees the first-popped target node is the
    optimal-Δv chain.

    The synodic enumeration in :func:`find_itn_pathways` is exact and
    closed-form, so each leg's existence is decidable in constant time
    per synodic period. The graph search itself is ``O(B^L × W)``
    worst case where B = |intermediates|, L = max_legs, W = windows
    per leg -- bounded by ``max_intermediate_windows`` per node and by
    ``max_chains`` overall. In practice the budgets prune aggressively.
    """
    import heapq

    if departure == target:
        raise ValueError("departure and target must differ")
    if jd_hi < jd_lo:
        raise ValueError(f"jd_hi {jd_hi} < jd_lo {jd_lo}")
    if max_legs < 1:
        raise ValueError(f"max_legs must be ≥ 1, got {max_legs}")
    if dv_budget_kms <= 0.0:
        raise ValueError(f"dv_budget_kms must be > 0, got {dv_budget_kms}")
    if tof_budget_days <= 0.0:
        raise ValueError(f"tof_budget_days must be > 0, got {tof_budget_days}")

    # Default intermediates: all heliocentric bodies in BODIES (planets,
    # dwarf planets, asteroids) excluding departure / target / Sun.
    if intermediates is None:
        intermediates = sorted(
            k for k, b in BODIES.items()
            if b.category in ("planet", "asteroid")
            and k not in (departure, target)
        )
    else:
        intermediates = list(intermediates)
        for body in intermediates:
            if body in (departure, target):
                raise ValueError(
                    f"intermediate {body!r} cannot equal departure/target"
                )
            if body not in BODIES:
                raise ValueError(f"unknown intermediate body: {body!r}")

    # Reachable next-bodies from any node = intermediates ∪ {target}.
    next_bodies = list(intermediates) + [target]

    # Dijkstra priority queue. Items are
    # (total_dv, counter, total_tof, n_legs, head_body, head_jd,
    #  legs_tuple, resonance_tuple, score_sum)
    # heapq is a min-heap on the first element by default, so total_dv
    # leads. The monotonic counter at position 1 is the FIFO
    # tiebreaker -- it MUST precede the non-comparable ITNCandidate
    # payload tuples or heapq's lexicographic compare will try to
    # order ITNCandidate vs ITNCandidate and TypeError out. Standard
    # priority-queue-with-non-comparable-payload idiom.
    pq: List = []
    counter = 0
    heapq.heappush(
        pq,
        (0.0, counter, 0.0, 0, departure, float(jd_lo),
         tuple(), tuple(), 0.0),
    )

    out: List[ITNChainCandidate] = []
    while pq and len(out) < max_chains:
        (total_dv, _ctr, total_tof, n_legs, head_body, head_jd,
         legs_tuple, res_tuple, score_sum) = heapq.heappop(pq)

        # Goal check.
        if head_body == target and n_legs >= 1:
            out.append(ITNChainCandidate(
                jd_tdb_launch=float(legs_tuple[0].jd_tdb),
                jd_tdb_arrival=float(head_jd),
                legs=legs_tuple,
                total_dv_kms=float(total_dv),
                total_tof_days=float(total_tof),
                resonance_signature=res_tuple,
                score=float(score_sum),
            ))
            continue

        if n_legs >= max_legs:
            continue

        # Expand: enumerate Hohmann windows from head_body to each
        # candidate next_body in [head_jd, jd_hi].
        for next_body in next_bodies:
            if next_body == head_body:
                continue
            try:
                windows = find_itn_pathways(
                    head_jd, jd_hi,
                    departure=head_body, target=next_body,
                    threshold=threshold,
                    max_candidates=max_intermediate_windows,
                )
            except ValueError:
                # Bodies share orbital period (degenerate synodic),
                # or one is non-heliocentric. Skip silently.
                continue

            for leg in windows:
                leg_dv = leg.estimated_dv_kms
                leg_tof = leg.transfer_time_days + (leg.jd_tdb - head_jd)
                new_dv = total_dv + leg_dv
                new_tof = total_tof + leg_tof
                if new_dv > dv_budget_kms:
                    continue
                if new_tof > tof_budget_days:
                    continue

                p_dep = BODIES[head_body].period_days
                p_tgt = BODIES[next_body].period_days
                pq_ratio = _best_rational_approx(p_dep / p_tgt)
                arrival_jd = leg.jd_tdb + leg.transfer_time_days

                counter += 1
                heapq.heappush(pq, (
                    float(new_dv),
                    counter,
                    float(new_tof),
                    n_legs + 1,
                    next_body,
                    float(arrival_jd),
                    legs_tuple + (leg,),
                    res_tuple + (pq_ratio,),
                    float(score_sum + leg.score),
                ))

    return out


__all__ = [
    "ITNCandidate",
    "ITNChainCandidate",
    "hohmann_transfer_time_days",
    "hohmann_launch_phase_angle_rad",
    "hohmann_total_dv_kms",
    "synodic_period_days",
    "find_itn_pathways",
    "find_itn_chains",
]
