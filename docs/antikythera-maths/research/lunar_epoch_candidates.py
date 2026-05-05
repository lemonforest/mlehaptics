"""Phase A research: score candidate epochs for Sol Terra-Luna Time (STLT).

Task #95 — find a celestially-significant, Greek-historically-attested
epoch for Sol Terra-Luna Time, additive to the existing J2000 anchor
that most Sol Time members borrow from Terra. STLT is the first Sol
Time member following the moons-stuck-to-parent `Sol <Parent>-<Body>
Time` convention (Luna's primary lunar-time entry), so a
historically-anchored zero is more natural than borrowing J2000 from
modern astronomy.

This script enumerates four candidate epochs spanning Greek and pre-
Greek antiquity, scores each one against our spectral kernel + skyfield
ground truth, and dumps a markdown report in
``docs/antikythera-maths/figures/lunar_epoch_candidates.md``.

The four candidates:

  1. **Antikythera Saros anchor** — 23 August 205 BCE solar eclipse.
     Per Freeth & Jones (2012), "The Cosmos in the Antikythera
     Mechanism," the device's Saros dial is calibrated against this
     specific eclipse. Project-resonant (the device is the literal
     namesake of ``docs/antikythera-maths/``).

  2. **Meton's summer solstice** — 27 June 432 BCE (Athens). Origin of
     the Metonic cycle (235 synodic months ≈ 19 tropical years, off by
     ~2 hours). Anchors the cycle the Antikythera *encodes* on its
     Metonic dial — deeper than anchoring at the Saros dial's start.
     `Z_5` of our `Z_60 = Z_4 × Z_3 × Z_5` natural-resonance group
     is the Metonic-aligned component.

  3. **Hipparchus's calibration eclipse** — 25 January 141 BCE lunar
     eclipse (Almagest VI.5; Hipparchus used it for his lunar theory).
     Tightest tie to the Greek mathematical-astronomy tradition.

  4. **Babylonian Mardokempad eclipse** — 19 March 721 BCE lunar
     eclipse (Almagest IV.6; the earliest Babylonian eclipse Ptolemy
     cites from Hipparchus's catalogue, from Mardokempad's first
     regnal year). Predates Greek astronomy proper but is the
     foundational record Hipparchus calibrated against.

Output: nearest-syzygy match, score (rad), kind, JD_TDB, calendar date
in proleptic Julian calendar, +/- offset from candidate. Plus a
solstice diagnostic for Meton (solar ecliptic longitude at candidate).

Run:

    python lunar_epoch_candidates.py

Writes to:

    ../figures/lunar_epoch_candidates.md  (relative to this script)

No CLI args; the candidate set is hardcoded. To add a candidate, append
to ``CANDIDATES`` below and re-run.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Bridge into the package; we want find_syzygies + the existing
# ephemeris loader for skyfield ground truth.
_PKG_PARENT = Path(__file__).resolve().parents[1] / "ephemerides-spectral" / "python"
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from ephemerides_spectral import bridge  # noqa: E402

try:
    from skyfield.api import Loader  # type: ignore[import-untyped]
    HAS_SKYFIELD = True
except ImportError:
    HAS_SKYFIELD = False


# ──────────────────────────────────────────────────────────────────────
# Calendar-to-JD conversion
# ──────────────────────────────────────────────────────────────────────
#
# For ancient dates we use the proleptic Julian calendar (extended
# backwards from the Julian calendar's 45 BCE introduction). This
# matches the convention NASA's Five Millennium Catalog of Solar
# Eclipses uses for dates before 1582 (Gregorian reform).
#
# Year numbering: astronomical, where 1 BCE = year 0, 2 BCE = -1, etc.
# So 205 BCE → -204, 432 BCE → -431, etc.

def proleptic_julian_to_jd(
    year: int, month: int, day: int,
    hour: int = 12, minute: int = 0,
) -> float:
    """Convert proleptic Julian calendar date to JD (UTC noon = 0.0).

    Implementation per Meeus, *Astronomical Algorithms*, ch. 7,
    formula for Julian calendar (NOT the Gregorian one — the proleptic
    Julian rule is what NASA uses for pre-1582 dates).

    `year` is in astronomical year numbering: 1 BCE = 0, 2 BCE = -1.
    """
    if month <= 2:
        year_adj = year - 1
        month_adj = month + 12
    else:
        year_adj = year
        month_adj = month
    # Proleptic Julian calendar formula — no Gregorian century correction.
    jd = (math.floor(365.25 * (year_adj + 4716))
          + math.floor(30.6001 * (month_adj + 1))
          + day - 1524.5)
    # Add fractional day for hour:minute.
    jd += (hour + minute / 60.0) / 24.0
    return jd


# ──────────────────────────────────────────────────────────────────────
# Candidate definitions
# ──────────────────────────────────────────────────────────────────────

@dataclass
class Candidate:
    """One epoch candidate to score.

    Most candidates are calendar-date-anchored (solar/lunar/solstice).
    The "midpoint" kind is *derived* — its JD_TDB is the arithmetic
    mean of two other candidates' JDs. This lets us model the
    Hipparchus-Babylonian transmission baseline directly.
    """
    name: str                      # short label (e.g. "Antikythera-205BCE")
    descriptor: str                # human-readable description
    calendar_year: int = 0         # astronomical year numbering (ignored for midpoint)
    calendar_year_label: str = ""  # how Greeks/historians cite it (e.g. "205 BCE")
    month: int = 0
    day: int = 0
    hour: int = 12                 # noon proleptic Julian by default
    kind: str = "solar"            # "solar", "lunar", "solstice", "midpoint"
    citation: str = ""             # source for the date
    notes: str = ""
    # For kind="midpoint": names of the two anchor candidates to average.
    midpoint_of: Tuple[str, str] = ("", "")
    # Cached resolved JD (so midpoint candidates can defer until parents resolved).
    _resolved_jd: Optional[float] = field(default=None, init=False, repr=False)

    def jd_tdb(self, registry: Optional[Dict[str, "Candidate"]] = None) -> float:
        """Candidate JD_TDB (treating proleptic Julian noon as TDB).

        For 2000+ year-old events, the TDB-UTC offset (~tens of seconds)
        is well below the precision of historical-eclipse dating, so we
        equate proleptic Julian noon with TDB noon for the candidate.
        Ground-truth comparisons against skyfield use the same convention.

        For kind="midpoint", resolves the two parent candidates from
        ``registry`` and returns the arithmetic mean of their JDs.
        """
        if self._resolved_jd is not None:
            return self._resolved_jd
        if self.kind == "midpoint":
            if registry is None:
                raise ValueError(
                    f"midpoint candidate {self.name!r} needs a registry "
                    "to resolve its parents")
            a_name, b_name = self.midpoint_of
            jd_a = registry[a_name].jd_tdb(registry)
            jd_b = registry[b_name].jd_tdb(registry)
            self._resolved_jd = 0.5 * (jd_a + jd_b)
            return self._resolved_jd
        self._resolved_jd = proleptic_julian_to_jd(
            self.calendar_year, self.month, self.day,
            hour=self.hour,
        )
        return self._resolved_jd


CANDIDATES: List[Candidate] = [
    Candidate(
        name="Antikythera-205BCE",
        descriptor="Antikythera mechanism Saros-dial anchor (Freeth & Jones 2012)",
        calendar_year=-204,  # 205 BCE in astronomical numbering
        calendar_year_label="205 BCE",
        month=8, day=23,
        kind="solar",
        citation="Freeth, T. & Jones, A. (2012). 'The Cosmos in the "
                 "Antikythera Mechanism'. ISAW Papers 4. Proposes "
                 "this date as the calibration anchor of the device's "
                 "Saros dial.",
        notes="Solar eclipse over the eastern Mediterranean. Project-"
              "resonant — the device is the namesake of "
              "docs/antikythera-maths/. Contested anchor (some scholars "
              "argue ~178 BCE based on different inscription readings).",
    ),
    Candidate(
        name="Meton-432BCE",
        descriptor="Meton of Athens summer solstice (origin of the Metonic cycle)",
        calendar_year=-431,  # 432 BCE
        calendar_year_label="432 BCE",
        month=6, day=27,
        kind="solstice",
        citation="Ptolemy, Almagest III.1, citing Meton's solstice "
                 "observation. Standard date per modern reconstructions; "
                 "see Goldstein & Bowen (1989).",
        notes="Meton calibrated his 19-year cycle (235 synodic months "
              "≈ 19 tropical years, off by ~2 hours) against this "
              "summer solstice. The Antikythera mechanism's Metonic "
              "dial encodes Meton's cycle — anchoring at Meton's "
              "solstice is anchoring at the cycle the Antikythera "
              "ultimately encodes. Z_5 of our Z_60 = Z_4 × Z_3 × Z_5 "
              "natural-resonance group is the Metonic-aligned component.",
    ),
    Candidate(
        name="Hipparchus-141BCE",
        descriptor="Hipparchus's calibration lunar eclipse (Almagest VI.5)",
        calendar_year=-140,  # 141 BCE
        calendar_year_label="141 BCE",
        month=1, day=27,
        hour=22,  # roughly mid-eclipse evening per Almagest
        kind="lunar",
        citation="Ptolemy, Almagest VI.5, transmitting Hipparchus's "
                 "observation. Used by Hipparchus for his lunar-theory "
                 "calibration.",
        notes="Greek mathematical-astronomy tradition's tightest tie. "
              "Hipparchus published the 'star catalogue' tradition that "
              "Ptolemy inherits; this eclipse is one of the calibration "
              "anchors for the lunar parameters the catalogue rests on.",
    ),
    Candidate(
        name="Mardokempad-721BCE",
        descriptor="Earliest Babylonian eclipse Ptolemy cites (Almagest IV.6)",
        calendar_year=-720,  # 721 BCE
        calendar_year_label="721 BCE",
        month=3, day=19,
        hour=21,  # evening of the lunar eclipse per cuneiform records
        kind="lunar",
        citation="Ptolemy, Almagest IV.6: 'in Mardokempad's year 1, "
                 "month Thoth 29-30 [Egyptian], a great eclipse of the "
                 "Moon began'. Earliest entry in the Babylonian eclipse "
                 "archive cited by Hipparchus.",
        notes="Pre-Greek; the foundational Babylonian record Hellenistic "
              "astronomers calibrated against. 2700+ years before J2000 — "
              "still well within DE441 coverage (-13200 BCE → +17191 CE).",
    ),
    Candidate(
        name="Transmission-Midpoint",
        descriptor="Hipparchus-Babylonian transmission baseline midpoint",
        kind="midpoint",
        midpoint_of=("Mardokempad-721BCE", "Hipparchus-141BCE"),
        citation="Derived. The arithmetic mean of the JDs of the earliest "
                 "Babylonian eclipse Hipparchus cites (Mardokempad 721 BCE) "
                 "and Hipparchus's own calibration eclipse (141 BCE). "
                 "Models the *center of mass* of the eclipse archive that "
                 "Greek mathematical astronomy was built on.",
        notes="The empirical question this candidate exposes: does the "
              "Hipparchus-Babylonian baseline midpoint land at or near "
              "Meton's 432 BCE solstice? If so, Meton's anchor is "
              "*independently validated* as the foundational center of "
              "Greek astronomy — it sits at the temporal center of mass "
              "of the eclipse archive Hellenistic astronomers calibrated "
              "against. If not, the midpoint is its own candidate worth "
              "considering on its own merits.",
    ),
]


# ──────────────────────────────────────────────────────────────────────
# Scoring
# ──────────────────────────────────────────────────────────────────────

@dataclass
class Score:
    """Result of scoring one candidate."""
    candidate: Candidate
    candidate_jd: float
    nearest_syzygy_jd: Optional[float] = None
    nearest_syzygy_kind: Optional[str] = None
    nearest_syzygy_score: Optional[float] = None  # rad; lower = stronger
    nearest_syzygy_offset_days: Optional[float] = None  # signed
    solar_longitude_deg: Optional[float] = None  # for solstice candidates
    solstice_offset_deg: Optional[float] = None  # |solar_lon - 90| or |- 270|
    error: Optional[str] = None


def score_eclipse_candidate(c: Candidate, registry: Dict[str, Candidate]) -> Score:
    """Match a candidate eclipse against find_syzygies output.

    Window-size note: at multi-millennium horizons our spectral encoder
    drifts (per the v0.3.0 DE441 sweep — Moon median ~62° at ±14000 yr).
    That moves predicted eclipse times tens of days away from actual.
    For pre-Common-Era lunar candidates we widen the search window to
    ±60 days so the right eclipse stays inside the window even with
    drift; we still pick the *nearest* match by JD.
    """
    candidate_jd = c.jd_tdb(registry)
    # Window scales with how far back we are from J2000. At ±2000 yr
    # the Moon drift can be ~60° → ~10 days; at ±2700 yr it's larger.
    # Use a generous ±60 days for ancient candidates and ±10 days for
    # candidates within ±500 yr of J2000 (current Sol Time horizon).
    years_from_j2000 = abs(candidate_jd - 2451545.0) / 365.25
    window = 60.0 if years_from_j2000 > 500 else 10.0
    kind_filter = c.kind  # "solar" or "lunar"
    result = bridge.find_syzygies(
        jd_lo=candidate_jd - window,
        jd_hi=candidate_jd + window,
        kind=kind_filter,
        threshold=0.5,  # widest threshold; we're characterising, not filtering
        max_candidates=20,
        # Explicit "bip" sidesteps the same backend="auto" latent bug
        # class fixed for get_breathing_modulation in v0.9.2.
        # find_syzygies still has the issue; queued for v0.10.0 fix.
        backend="bip",
    )
    if not result.get("ok"):
        return Score(candidate=c, candidate_jd=candidate_jd,
                     error=result.get("error", "find_syzygies failed"))
    cands = result.get("candidates", [])
    if not cands:
        return Score(candidate=c, candidate_jd=candidate_jd,
                     error=f"no syzygy in ±{window:.0f}d window")
    # Pick the candidate nearest to the target JD by absolute offset.
    best = min(cands, key=lambda d: abs(d["jd_tdb"] - candidate_jd))
    return Score(
        candidate=c,
        candidate_jd=candidate_jd,
        nearest_syzygy_jd=best["jd_tdb"],
        nearest_syzygy_kind=best["kind"],
        nearest_syzygy_score=best["score"],
        nearest_syzygy_offset_days=best["jd_tdb"] - candidate_jd,
    )


#: IAU 2006 precession rate of the equinoxes, deg/yr. Equivalent to
#: 50.290966 arcsec/yr. For ancient candidates the equinox sits this
#: many degrees rotated from its J2000 position.
_PRECESSION_DEG_PER_YEAR: float = 50.290966 / 3600.0


def _precession_correction_deg(jd_tdb: float) -> float:
    """Equinox displacement (deg) at jd_tdb relative to J2000.

    Positive at past dates (JD < J2000): the equinox of date sits at
    larger ecliptic longitude than the J2000 equinox. To compare a
    J2000-frame solar longitude against the *epoch-of-date* solstice
    cardinals (90° / 270°), subtract this correction first.

    First-order linear precession is fine for ±3000 yr at the precision
    we care about (~degree-level for solstice diagnostics). Full IAU
    2006 precession would add ~0.01° at -2400 yr.
    """
    years = (jd_tdb - 2451545.0) / 365.25
    return -years * _PRECESSION_DEG_PER_YEAR  # past dates → positive


def score_solstice_candidate(c: Candidate, registry: Dict[str, Candidate]) -> Score:
    """For solstice candidates, compare solar ecliptic longitude vs. 90°.

    Summer solstice at northern latitudes → solar ecliptic longitude
    = 90° in the *epoch-of-date* frame. We compute solar longitude
    via skyfield (which returns the J2000 frame) and subtract the
    precession correction to reach the epoch-of-date frame, then
    compare to the nearest cardinal (90° summer / 270° winter).

    Falls back to a low-precision mean longitude if skyfield is not
    available (the script can still run; the report just notes the
    skyfield ground truth was unavailable).
    """
    candidate_jd = c.jd_tdb(registry)
    score = Score(candidate=c, candidate_jd=candidate_jd)
    if not HAS_SKYFIELD:
        score.error = "skyfield unavailable; solstice score skipped"
        return score
    try:
        from ephemerides_spectral._research.ephemeris_loader import (  # type: ignore[import-untyped]
            load_ephemeris,
        )
        bundle = load_ephemeris("de441")
        if bundle is None:
            score.error = "load_ephemeris returned None (skyfield/kernel unavailable)"
            return score
        ts = bundle.ts
        sun = bundle.sun
        terra = bundle.terra
        t = ts.tdb_jd(candidate_jd)
        # Sun's apparent ecliptic longitude as observed from Terra.
        astrometric = terra.at(t).observe(sun).apparent()
        ecliptic_lat, ecliptic_lon, _ = astrometric.ecliptic_latlon()
        lon_j2000 = float(ecliptic_lon.degrees) % 360.0
        # Convert to epoch-of-date frame so 90° = summer solstice in the
        # year of the candidate. Without this, ancient dates pick up
        # ~33° of precession drift (50.29″/yr × 2432 yr ≈ 33.97° at
        # 432 BCE) and the offset is dominated by precession, not by
        # any mismatch between the candidate date and the actual solstice.
        lon_of_date = (lon_j2000 - _precession_correction_deg(candidate_jd)) % 360.0
        score.solar_longitude_deg = lon_of_date
        # Distance to nearest solstice (90° or 270°). Summer = 90°.
        offsets = [
            (lon_of_date - 90.0 + 180.0) % 360.0 - 180.0,
            (lon_of_date - 270.0 + 180.0) % 360.0 - 180.0,
        ]
        score.solstice_offset_deg = min(offsets, key=abs)
    except Exception as exc:  # pragma: no cover - environmental
        score.error = f"skyfield path failed: {type(exc).__name__}: {exc}"
    return score


def score_midpoint_candidate(c: Candidate, registry: Dict[str, Candidate]) -> Score:
    """Score a derived-midpoint candidate.

    Reports:
      - The midpoint JD itself (≥6 sig figs).
      - Solar ecliptic longitude at the midpoint (skyfield).
      - Distance from the nearest other candidate's JD (so we can
        say "this midpoint lands within X days of Meton's solstice"
        — the empirical claim the user wants to test).
      - Nearest spectral-kernel syzygy (in case the midpoint
        accidentally lands on one).
    """
    candidate_jd = c.jd_tdb(registry)
    score = Score(candidate=c, candidate_jd=candidate_jd)
    # Borrow the solstice scorer's solar-longitude path.
    if HAS_SKYFIELD:
        try:
            from ephemerides_spectral._research.ephemeris_loader import (  # type: ignore[import-untyped]
                load_ephemeris,
            )
            bundle = load_ephemeris("de441")
            if bundle is None:
                score.error = "load_ephemeris returned None (skyfield/kernel unavailable)"
                raise RuntimeError(score.error)
            ts = bundle.ts
            sun = bundle.sun
            terra = bundle.terra
            t = ts.tdb_jd(candidate_jd)
            astrometric = terra.at(t).observe(sun).apparent()
            _, ecliptic_lon, _ = astrometric.ecliptic_latlon()
            lon_j2000 = float(ecliptic_lon.degrees) % 360.0
            lon_of_date = (lon_j2000 - _precession_correction_deg(candidate_jd)) % 360.0
            score.solar_longitude_deg = lon_of_date
            offsets = [
                (lon_of_date - 90.0 + 180.0) % 360.0 - 180.0,
                (lon_of_date - 270.0 + 180.0) % 360.0 - 180.0,
            ]
            score.solstice_offset_deg = min(offsets, key=abs)
        except Exception as exc:  # pragma: no cover - environmental
            score.error = f"skyfield path failed: {type(exc).__name__}: {exc}"
    # Also enumerate any nearby syzygy in case the midpoint lands on one.
    syz_result = bridge.find_syzygies(
        jd_lo=candidate_jd - 30.0,
        jd_hi=candidate_jd + 30.0,
        kind="all",
        threshold=0.5,
        max_candidates=20,
        backend="bip",
    )
    if syz_result.get("ok") and syz_result.get("candidates"):
        nearest = min(syz_result["candidates"],
                      key=lambda d: abs(d["jd_tdb"] - candidate_jd))
        score.nearest_syzygy_jd = nearest["jd_tdb"]
        score.nearest_syzygy_kind = nearest["kind"]
        score.nearest_syzygy_score = nearest["score"]
        score.nearest_syzygy_offset_days = nearest["jd_tdb"] - candidate_jd
    return score


def score_candidate(c: Candidate, registry: Dict[str, Candidate]) -> Score:
    if c.kind in ("solar", "lunar"):
        return score_eclipse_candidate(c, registry)
    if c.kind == "solstice":
        return score_solstice_candidate(c, registry)
    if c.kind == "midpoint":
        return score_midpoint_candidate(c, registry)
    return Score(candidate=c, candidate_jd=c.jd_tdb(registry),
                 error=f"unknown kind {c.kind!r}")


# ──────────────────────────────────────────────────────────────────────
# Markdown report
# ──────────────────────────────────────────────────────────────────────

def render_report(scores: List[Score], registry: Dict[str, Candidate]) -> str:
    # Compute the empirical claim: how far apart are the Hipparchus-Babylonian
    # transmission midpoint and Meton's solstice?
    meton_score = next((s for s in scores if s.candidate.name == "Meton-432BCE"), None)
    midpoint_score = next((s for s in scores if s.candidate.name == "Transmission-Midpoint"), None)
    midpoint_minus_meton_days: Optional[float] = None
    midpoint_minus_meton_years: Optional[float] = None
    if meton_score and midpoint_score:
        midpoint_minus_meton_days = midpoint_score.candidate_jd - meton_score.candidate_jd
        midpoint_minus_meton_years = midpoint_minus_meton_days / 365.25

    out: List[str] = []
    out.append("# Sol Terra-Luna Time (STLT) — Epoch Candidate Report")
    out.append("")
    out.append("**Generated by** `research/lunar_epoch_candidates.py`. ")
    out.append("**Task** [#95: STLT — Antikythera-anchored Terra-Luna system clock]")
    out.append("(see ROADMAP.md and the v0.10.0 ship plan).")
    out.append("")
    out.append("**Purpose:** rank Greek-historical and pre-Greek lunar / solar / "
               "solstice events as candidate STLT zero-points. The chosen anchor "
               "becomes the additive `STLT_EPOCH_ANTIKYTHERA_JD_TDB` constant in "
               "`time_scales.py`; the existing J2000-anchored Sol Times stay the "
               "default. Frame is *house epoch*, not a claim to be NASA's eventual "
               "LCT (Lunar Coordinated Time) standard.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Candidate Summary")
    out.append("")
    out.append("| Candidate | Date (proleptic Julian) | JD_TDB | Kind | "
               "Spectral score (rad) | Offset from kernel | Notes |")
    out.append("|---|---|---|---|---|---|---|")
    for s in scores:
        c = s.candidate
        date = f"{c.calendar_year_label} {c.month:02d}-{c.day:02d}"
        jd_str = f"{s.candidate_jd:.4f}"
        if s.error:
            score_str = "—"
            offset_str = f"⚠ {s.error}"
        elif c.kind in ("solar", "lunar"):
            score_str = f"{s.nearest_syzygy_score:.4f}" if s.nearest_syzygy_score is not None else "—"
            if s.nearest_syzygy_offset_days is not None:
                offset_str = f"{s.nearest_syzygy_offset_days:+.3f} d"
            else:
                offset_str = "—"
        elif c.kind == "solstice":
            if s.solstice_offset_deg is not None:
                score_str = f"{abs(s.solstice_offset_deg):.4f}°"
                offset_str = f"solar λ = {s.solar_longitude_deg:.3f}°"
            else:
                score_str = "—"
                offset_str = "—"
        else:
            score_str = "—"
            offset_str = "—"
        notes_short = c.notes.split(".")[0] + "." if c.notes else ""
        out.append(f"| **{c.name}** | {date} | {jd_str} | {c.kind} | "
                   f"{score_str} | {offset_str} | {notes_short} |")
    out.append("")
    out.append("Lower spectral score = stronger syzygy alignment. For solstice "
               "candidates, the score is the solar ecliptic longitude's offset "
               "from 90° (summer) or 270° (winter), in degrees. For the "
               "midpoint candidate, the score is the same solar-longitude "
               "offset as solstices (in case the midpoint *also* lands at a "
               "solstice — testable empirical question).")
    out.append("")
    if midpoint_minus_meton_days is not None:
        out.append("---")
        out.append("")
        out.append("## The empirical claim")
        out.append("")
        out.append(f"**Hipparchus-Babylonian midpoint − Meton's solstice = "
                   f"`{midpoint_minus_meton_days:+.2f}` days "
                   f"(`{midpoint_minus_meton_years:+.3f}` years).**")
        out.append("")
        if abs(midpoint_minus_meton_years) < 5.0:
            out.append("The transmission midpoint lands within five years of "
                       "Meton's solstice — a striking convergence. Greek "
                       "mathematical astronomy's eclipse-archive *center of "
                       "mass* sits at the same temporal point as its earliest "
                       "named solar-cycle anchor. This is the kind of "
                       "convergence that argues for Meton as the deepest "
                       "STLT epoch: he sits at the empirical center of the "
                       "tradition, not arbitrarily early in it.")
        elif abs(midpoint_minus_meton_years) < 50.0:
            out.append("The transmission midpoint lands within ~50 years of "
                       "Meton's solstice. Suggestive but not as tight as the "
                       "convergence the user hypothesized; worth thinking "
                       "about whether to use the midpoint *itself* as the "
                       "anchor (a derived value with a clean narrative) or "
                       "Meton's solstice (closer to a single observable event).")
        else:
            out.append("The transmission midpoint and Meton's solstice differ "
                       "by more than ~50 years; the convergence hypothesis "
                       "is not supported. The midpoint and Meton are "
                       "independent candidates on their own merits.")
        out.append("")
    out.append("---")
    out.append("")
    for s in scores:
        out.extend(_render_candidate_detail(s))
        out.append("")
    out.append("---")
    out.append("")
    out.append("## Recommendation")
    out.append("")
    out.append("The right choice is judgement-grade and depends on which cycle "
               "we want STLT to encode at its zero:")
    out.append("")
    out.append("- **Antikythera Saros anchor (205 BCE):** ties STLT to the "
               "Saros cycle (223 synodic months ≈ 18.03 tropical years). "
               "Project-resonant. Single eclipse — high information density.")
    out.append("")
    out.append("- **Meton's solstice (432 BCE):** ties STLT to the Metonic "
               "cycle (235 synodic months ≈ 19.00 tropical years; the "
               "lunar-solar reconciliation Meton calibrated). Anchors the "
               "*cycle* the Antikythera Metonic dial encodes. Resonates with "
               "our `Z_60 = Z_4 × Z_3 × Z_5` natural-resonance group's `Z_5` "
               "Metonic factor.")
    out.append("")
    out.append("- **Hipparchus (141 BCE):** tightest Greek-mathematical-astronomy "
               "tie. Hipparchus's lunar-theory calibration anchor.")
    out.append("")
    out.append("- **Mardokempad (721 BCE):** the oldest defensible anchor; "
               "predates Greek astronomy proper but is the foundational "
               "Babylonian record Hipparchus calibrated against.")
    out.append("")
    out.append("Human picks. The script's job is to verify all four are "
               "celestially genuine in our spectral kernel + ground-truth "
               "convention, and to expose the JDs to ≥6 significant figures "
               "for the eventual `time_scales.py` constant.")
    out.append("")
    return "\n".join(out)


def _render_candidate_detail(s: Score) -> List[str]:
    c = s.candidate
    out: List[str] = []
    out.append(f"## `{c.name}` — {c.descriptor}")
    out.append("")
    if c.kind == "midpoint":
        a, b = c.midpoint_of
        out.append(f"**Derived candidate.** JD_TDB = (JD(`{a}`) + JD(`{b}`)) / 2.")
    else:
        out.append(f"**Calendar date** (proleptic Julian, astronomical year "
                   f"numbering): year **{c.calendar_year}** "
                   f"(= {c.calendar_year_label}), month {c.month:02d}, "
                   f"day {c.day:02d}, hour {c.hour:02d}.")
    out.append("")
    out.append(f"**JD_TDB:** `{s.candidate_jd:.6f}`")
    out.append("")
    out.append(f"**Kind:** `{c.kind}`")
    out.append("")
    if c.citation:
        out.append(f"**Citation:** {c.citation}")
        out.append("")
    if c.notes:
        out.append(f"**Notes:** {c.notes}")
        out.append("")
    if s.error:
        out.append(f"⚠ **Scoring error:** {s.error}")
        out.append("")
    elif c.kind in ("solar", "lunar"):
        if s.nearest_syzygy_jd is not None:
            out.append(f"**Nearest spectral-kernel syzygy:** "
                       f"JD `{s.nearest_syzygy_jd:.6f}` "
                       f"(kind=`{s.nearest_syzygy_kind}`, "
                       f"score=`{s.nearest_syzygy_score:.6f}` rad, "
                       f"offset `{s.nearest_syzygy_offset_days:+.4f}` days "
                       f"from the historical date).")
        out.append("")
    elif c.kind == "solstice":
        if s.solar_longitude_deg is not None:
            out.append(f"**Solar ecliptic longitude (skyfield):** "
                       f"`{s.solar_longitude_deg:.4f}°`. ")
            out.append(f"**Offset from nearest solstice:** "
                       f"`{s.solstice_offset_deg:+.4f}°` "
                       f"({'summer' if abs((s.solstice_offset_deg or 0) - 0) <= 90 else 'winter'} "
                       f"solstice = nearest cardinal).")
        out.append("")
    elif c.kind == "midpoint":
        if s.solar_longitude_deg is not None:
            out.append(f"**Solar ecliptic longitude at midpoint (skyfield):** "
                       f"`{s.solar_longitude_deg:.4f}°`.")
            if s.solstice_offset_deg is not None:
                out.append(f"**Distance from nearest solstice:** "
                           f"`{abs(s.solstice_offset_deg):.4f}°`.")
            out.append("")
        if s.nearest_syzygy_jd is not None:
            out.append(f"**Nearest spectral-kernel syzygy:** "
                       f"JD `{s.nearest_syzygy_jd:.6f}` "
                       f"(kind=`{s.nearest_syzygy_kind}`, "
                       f"score=`{s.nearest_syzygy_score:.6f}` rad, "
                       f"offset `{s.nearest_syzygy_offset_days:+.4f}` days "
                       f"from the midpoint JD).")
            out.append("")
    return out


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not HAS_SKYFIELD:
        print("⚠ skyfield not available — solstice scoring will skip; "
              "syzygy scoring still runs from the bundled BIP backend.",
              file=sys.stderr)
    registry: Dict[str, Candidate] = {c.name: c for c in CANDIDATES}
    scores: List[Score] = []
    for c in CANDIDATES:
        label = c.calendar_year_label or "(derived)"
        print(f"Scoring candidate {c.name} ({label}, {c.kind})...",
              file=sys.stderr)
        s = score_candidate(c, registry)
        scores.append(s)
        if s.error:
            print(f"  ⚠ {s.error}", file=sys.stderr)
        elif c.kind in ("solar", "lunar"):
            print(f"  → JD {s.nearest_syzygy_jd:.6f}, "
                  f"score {s.nearest_syzygy_score:.4f} rad, "
                  f"offset {s.nearest_syzygy_offset_days:+.3f} d",
                  file=sys.stderr)
        elif c.kind == "solstice" and s.solar_longitude_deg is not None:
            print(f"  → solar λ = {s.solar_longitude_deg:.3f}°, "
                  f"offset {s.solstice_offset_deg:+.3f}° from nearest solstice",
                  file=sys.stderr)
        elif c.kind == "midpoint":
            print(f"  → midpoint JD {s.candidate_jd:.6f}",
                  file=sys.stderr)
            if s.solar_longitude_deg is not None:
                print(f"    solar λ at midpoint = {s.solar_longitude_deg:.3f}°",
                      file=sys.stderr)
    report = render_report(scores, registry)
    out_path = Path(__file__).resolve().parent.parent / "figures" / "lunar_epoch_candidates.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
