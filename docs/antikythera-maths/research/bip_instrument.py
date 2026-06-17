"""Bit-Interleaved Phases (BIP) HDC Instrument — ALU-native implementation.

Phase composition lives in the cyclic group ``Z_{2^32}`` so that ``(phi_1 +
phi_2) mod 2^32`` is implicit ``uint32`` overflow — no explicit modulo,
no FPU.

Fixed-point design (Q-format)
-----------------------------

All "frequencies" are stored as **signed integers in residues per day**,
where one full revolution is ``MODULO = 2^32`` residues. The conversion
from a continuous angular rate ``omega`` (rad/day) is::

    omega_int = round(omega / (2 * pi) * MODULO)        # signed int64

Range / precision
~~~~~~~~~~~~~~~~~

* ``MODULO = 4_294_967_296`` residues per revolution.
* Earth's mean motion: ``2*pi/365.256 ≈ 0.01720 rad/day`` →
  ``0.01720 / (2*pi) * 2^32 ≈ 11_756_842`` residues/day.
* Smallest body period in BODIES (Phobos, 0.319 d) → ``~1.35e10`` residues/day,
  which is below ``2^34`` and therefore safe in ``int64`` for any
  ``delta_t`` short enough to keep ``omega_int * delta_t`` under ``2^63``.
  At ~10^10 residues/day, that ceiling is ~``9e8`` days = ~2.5 Myr —
  well outside the DE441 epoch.

Module-level guarantees:

* All ``omega_*`` arrays are ``int64`` with documented Q-format
  (``MODULO`` residues = full revolution).
* All phase accumulators are ``uint64`` so addition wraps cleanly within
  ``2^64`` even when the integrated step temporarily exceeds ``2^32``;
  the final reduction ``% MODULO`` collapses back to the cyclic group.
* ``encode_state`` runs under ``np.errstate(over='raise')`` so silent
  overflow becomes an explicit ``OverflowError`` rather than a hang.
"""

from __future__ import annotations

import math
import warnings
from array import array
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .bodies import BODIES, Body
from .laplacian import SolarSystemLaplacian, RESONANCES
from .ephemeris_loader import load_ephemeris, EphemerisBundle
from . import diagnosed_fibers as _patches

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D_DEFAULT: int = 65536
K_BITS: int = 32
MODULO: int = 2**K_BITS
REFERENCE_JD: float = 2451545.0

# Off-diagonal coupling LUT (integer cosine table over the cyclic group).
#
# Indexed by the top ``COSINE_LUT_BITS`` bits of a phase residue in Z_{2^32},
# returning ``int32`` values in the range [-COSINE_LUT_AMP, +COSINE_LUT_AMP].
# This replaces ``np.cos(...)`` in the breathing-coupling path — pure
# integer table lookup, no FPU.
#
# Size budget: 1024 × int32 = 4096 bytes. Well within the "256 KB hypervector"
# philosophy — three orders of magnitude smaller than the state itself.

COSINE_LUT_BITS: int = 10                  # 1024-entry table
COSINE_LUT_SIZE: int = 1 << COSINE_LUT_BITS
COSINE_LUT_AMP: int = 1 << 14              # ±16384 (Q1.14 in int32)


def _build_cosine_lut() -> array:
    """Precompute integer cosine table over the cyclic group Z_{2^COSINE_LUT_BITS}.

    Index ``k`` maps to ``cos(2*pi * k / 1024)`` quantised to ``int32`` in
    Q1.14 format. Computed once, at import time, with the FPU — but every
    runtime use is a pure integer index lookup.

    v0.31.0rc4: numpy-free. ``round()`` is round-half-to-even, identical
    to ``np.round``; ``math.cos`` shares libm with the previous numpy
    path, so the int32 table is byte-identical.
    """
    return array("i", [
        int(round(math.cos(2.0 * math.pi * k / COSINE_LUT_SIZE) * COSINE_LUT_AMP))
        for k in range(COSINE_LUT_SIZE)
    ])


_COSINE_LUT: array = _build_cosine_lut()


def cos_lut(phase_uint32: int, n_lobes: int = 1) -> int:
    """Integer cosine of an ``n_lobes``-fold phase residue in Z_{2^32}.

    ``cos_lut(phi, n)`` returns ``round(cos(n * 2*pi*phi/2^32) * COSINE_LUT_AMP)``
    via integer arithmetic only. Used by the breathing-coupling term, which
    needs ``cos(5*phi_J - 2*phi_S)`` for the Jupiter-Saturn 5:2 resonance.

    v0.31.0rc4: numpy-free. The uint32 multiply + mask is replicated
    with Python ``int`` arithmetic and an explicit ``& (MODULO - 1)``
    fixed-width reduction.
    """
    folded = (int(phase_uint32) * int(n_lobes)) & (MODULO - 1)
    idx = folded >> (K_BITS - COSINE_LUT_BITS)
    return int(_COSINE_LUT[idx])

# ---------------------------------------------------------------------------
# EphemerisBIPInstrument
# ---------------------------------------------------------------------------

class EphemerisBIPInstrument:
    """FPU-less dynamic BIP instrument for the Sol Star System."""

    def __init__(self, D: int = D_DEFAULT, kernel: str = "de441", force_high_res: bool = False):
        self.D = D
        self.kernel = kernel
        self.laplacian = SolarSystemLaplacian()
        self.body_names = self.laplacian.body_names
        self.body_to_idx = self.laplacian.body_to_idx
        
        # 0. Data Directory
        research_dir = Path(__file__).resolve().parent
        project_root = research_dir.parents[2]
        data_dir = str(project_root / "skyfield_data")

        # 1. Ephemeris.
        # v0.5.2: try to load the supplementary moon kernels too. If
        # they're not on disk, ephemeris_loader logs a debug message
        # and continues without them — the bundle is still functional
        # for the planetary bodies, and moons fall back to the
        # period-based initial-phase stub as in v0.5.1.
        _SATELLITE_KERNELS = ["mar099s", "jup365", "sat441"]
        try:
            self.bundle: Optional[EphemerisBundle] = load_ephemeris(
                kernel=kernel, data_dir=data_dir,
                auxiliary_kernels=_SATELLITE_KERNELS,
            )
        except ValueError:
            self.bundle = None
        if self.bundle is None:
            if force_high_res: raise RuntimeError("High-res kernel missing.")
            self.bundle = load_ephemeris(
                kernel="de421", data_dir=data_dir,
                auxiliary_kernels=_SATELLITE_KERNELS,
            )
        
        # 2. HDC Bases & Calibration
        self.channel_bases = self._initialize_bases()
        self.initial_phases_int = self._calibrate_initial_phases(REFERENCE_JD)

        # 3. Fixed-point integer frequencies (Q-format: MODULO residues = 2*pi rad)
        # omega_diag[i] = residues/day for body i, signed int64.
        # v0.31.0rc4: the Laplacian matrices are now list[list[complex]];
        # add the trunk + PN diagonals element-wise (not list-concat).
        n = self.laplacian.n
        L_trunk = self.laplacian.L_trunk
        L_pn = self.laplacian.L_pn
        combined_diag = [L_trunk[i][i] + L_pn[i][i] for i in range(n)]
        self.omega_diag = self._scale_diagonal_from_diag(combined_diag)

    def _scale_diagonal_from_diag(self, diag: List[complex]) -> array:
        """Complex diagonal -> int64 residues/day (``array('q')``).

        The conversion is ``omega_int = round(omega_rad_per_day / (2*pi) * MODULO)``.
        Periods are validated: any frequency that rounds to zero residues/day is
        flagged so the caller knows the body's mean motion is below the
        Q-format's resolution floor (``1 / MODULO`` ≈ 2.3e-10 rev/day,
        i.e. ~13 Gyr period — never trips for real bodies).

        v0.31.0rc4: numpy-free. ``round()`` is round-half-to-even,
        identical to ``np.round``; magnitude via plain ``abs()`` on a
        float (no Class-K cascade rule — this is ephemerides float math,
        not a srmech cascade).
        """
        omega_rad_per_day = [z.real for z in diag]
        omega_int = array("q", [
            int(round(w / (2.0 * math.pi) * MODULO)) for w in omega_rad_per_day
        ])
        # Guard the resolution floor.
        offenders = [
            self.body_names[i]
            for i in range(len(omega_int))
            if abs(omega_rad_per_day[i]) > 0 and omega_int[i] == 0
        ]
        if offenders:
            warnings.warn(
                f"Q-format underflow: bodies {offenders} have mean motions below "
                f"1 residue/day; bump K_BITS or use a higher-resolution Q-format.",
                RuntimeWarning, stacklevel=2,
            )
        return omega_int

    def _load_baked_initial_phases(self) -> Optional[array]:
        """Load codegen-baked initial phases from `_data/initial_phases.json`.

        Returns the per-body uint32 phase array if the JSON is present
        AND its body roster matches this instrument's body roster
        exactly; otherwise returns None and the caller falls through
        to live SPICE calibration. Body-roster mismatch (e.g., user
        adding a body in the research source without re-running
        codegen) should not silently use stale baked values.
        """
        # The JSON is shipped beside this module under the wheel layout:
        #   ephemerides_spectral/_research/bip_instrument.py     (this)
        #   ephemerides_spectral/_data/initial_phases.json       (sibling)
        # In the research source tree (no wheel install), the JSON
        # doesn't exist and we fall through to SPICE calibration —
        # exactly what codegen needs to BUILD the JSON in the first
        # place.
        import json
        candidates: List[Path] = []
        here = Path(__file__).resolve().parent
        # Wheel layout: _research/ next to _data/
        candidates.append(here.parent / "_data" / "initial_phases.json")
        # Research source-tree layout: docs/.../ephemerides-spectral/python/ephemerides_spectral/_data/
        candidates.append(here.parents[2] / "ephemerides-spectral" / "python"
                          / "ephemerides_spectral" / "_data" / "initial_phases.json")
        for path in candidates:
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            baked_names = list(payload.get("body_names", []))
            if baked_names != list(self.body_names):
                # Body-roster drift — refuse to use stale baked values.
                continue
            phases_dict = payload.get("initial_phases", {})
            arr = array("I", [0]) * len(self.body_names)
            for i, name in enumerate(self.body_names):
                if name not in phases_dict:
                    return None  # roster mismatch
                arr[i] = int(phases_dict[name]) & (MODULO - 1)
            return arr
        return None

    def _initialize_bases(self) -> Dict[str, array]:
        """Per-body integer channel bases (``array('I')`` in [0, MODULO)).

        v0.31.0rc4: numpy-free. The legacy path seeded these via
        ``numpy.random.default_rng(2026+i).integers(...)`` (PCG64), a
        stream that can't be reproduced without numpy. These integer
        bases are used ONLY by ``run_dimensional_expansion_sweep`` (the
        ``__main__`` benchmark demo) — they are NOT on any shipped
        bridge/encode_state path, and no test pins their bytes. The
        splitmix64 stream (the same portable PRNG the HD-lift channel
        bases use) supplies a deterministic numpy-free replacement.
        """
        from .portable_prng import splitmix64_next
        bases: Dict[str, array] = {}
        for i, body in enumerate(self.body_names):
            state = (2026 + i) & ((1 << 64) - 1)
            phases = array("I", [0]) * self.D
            for k in range(self.D):
                state, u = splitmix64_next(state)
                phases[k] = u & (MODULO - 1)
            bases[body] = phases
        return bases

    def _calibrate_initial_phases(self, jd: float) -> array:
        """Calibrate the phase angles (mapped to Z_{2^K}) from ephemeris truth.

        Resolution order:
        1. Codegen-baked ``_data/initial_phases.json`` from the wheel
           (when present). This is the published-kernel SSOT — the
           SAME values the C codegen bakes into ``es_initial_phases[]``,
           so Python BIP and native C are byte-identical even when no
           SPICE kernel is staged at runtime.
        2. Live SPICE calibration via skyfield (when the bundle loaded).
           Used at codegen time to GENERATE the JSON; also used if a
           caller explicitly wants to recalibrate against a different
           kernel.
        3. Zero phases (last-resort fallback only fires if the wheel
           shipped without ``_data/initial_phases.json`` — broken
           install).
        """
        baked = self._load_baked_initial_phases()
        if baked is not None:
            return baked
        if self.bundle is None:
            return array("I", [0]) * len(self.body_names)

        ts = self.bundle.ts
        t = ts.tt_jd(jd)
        phases = array("I", [0]) * len(self.body_names)
        
        moon_parent_map = {
            "luna": "terra",
            "phobos": "mars", "deimos": "mars",
            # Jovian moons — Galileans + inner regulars (v0.5.0)
            "metis": "jupiter", "adrastea": "jupiter",
            "amalthea": "jupiter", "thebe": "jupiter",
            "io": "jupiter", "europa": "jupiter",
            "ganymede": "jupiter", "callisto": "jupiter",
            # Saturnian moons — classical 9 + co-orbitals (v0.5.0)
            "mimas": "saturn", "enceladus": "saturn",
            "tethys": "saturn", "dione": "saturn", "rhea": "saturn",
            "titan": "saturn", "hyperion": "saturn",
            "iapetus": "saturn", "phoebe": "saturn",
            "janus": "saturn", "epimetheus": "saturn",
            # Uranus / Neptune
            "titania": "uranus", "triton": "neptune",
        }

        for i, name in enumerate(self.body_names):
            body_info = BODIES.get(name)
            if not body_info: continue

            try:
                target_key = name.upper()
                if body_info.category == "planet": target_key += " BARYCENTER"
                # v0.5.2: bundle.lookup searches main + auxiliary
                # ephemerides (mar099s, jup365, sat441 for moons).
                # v0.9.0: bundle.lookup translates internal terra/luna
                # to JPL-side EARTH/MOON.
                target = self.bundle.lookup(target_key)

                if body_info.category == "planet":
                    center = self.bundle.lookup("sun")
                elif body_info.category == "moon":
                    parent_name = moon_parent_map.get(name, "terra")
                    parent_key = parent_name.upper()
                    if parent_name in ["terra", "mars", "jupiter", "saturn", "uranus", "neptune"]:
                         parent_key += " BARYCENTER"
                    center = self.bundle.lookup(parent_key)
                else:
                    center = self.bundle.lookup("sun")

                astrometric = center.at(t).observe(target)
                _, lon, _ = astrometric.ecliptic_latlon()
                # Map [0, 2pi) -> [0, MODULO)
                phases[i] = int((lon.radians / (2.0 * math.pi)) * MODULO) % MODULO
                
            except (KeyError, ValueError):
                if body_info.period_days > 0:
                    phases[i] = int((jd % body_info.period_days) / body_info.period_days * MODULO) % MODULO
                else:
                    phases[i] = 0
                
        return phases

    def _get_scaled_coupling(self, b1: str, b2: str) -> int:
        """Off-diagonal coupling weight in residues/day, signed int64."""
        idx1 = self.body_to_idx[b1]
        idx2 = self.body_to_idx[b2]
        val = self.laplacian.L_static[idx1][idx2].real
        return int(round(val / (2.0 * math.pi) * MODULO))

    # Phase 9 breathing parameters. ``BREATHING_AMP_NUM/DEN`` is the
    # fractional modulation depth expressed as integers (10% = 1/10).
    _CHUNK_DAYS: int = 30
    _BREATHING_AMP_NUM: int = 1
    _BREATHING_AMP_DEN: int = 10

    # Empirical envelope: omega_diag has Phobos at ~1.35e10 residues/day, so
    # ``omega * (delta_t_days - num_steps*chunk)`` and ``omega * step`` must
    # stay below 2^63 = 9.22e18. ``num_steps * step`` is bounded by
    # ``|delta_t_days|``; so the int64 multiply is safe as long as
    # ``|delta_t_days| * 1.35e10 < 2^63``, i.e. ``|delta_t_days| < ~6.8e8``.
    # ~1.86 Myr — well outside any DE441 use case.
    _INT64_DELTA_DAYS_LIMIT: float = 6.8e8

    # uint64 / int64 fixed-width masks (v0.31.0rc4: explicit, numpy-free).
    _U64_MASK: int = (1 << 64) - 1
    _I64_MIN: int = -(1 << 63)
    _I64_MAX: int = (1 << 63) - 1

    def encode_state(self, date_jd: float) -> array:
        """Phase 9 breathing evolution — pure integer ALU, no FPU.

        Returns an ``array('I')`` of per-body uint32 phase residues (one
        per body, alphabetical order).

        The encode path is wrapped in a defensive guard:

        * Bounds-check on ``|delta_t_days|`` so the int64 frequency multiply
          stays in range — fails fast with ``OverflowError`` if exceeded.
        * The signed int64 frequency multiply is range-checked explicitly
          (the v0.31.0rc4 numpy-free replacement for the old
          ``np.errstate(over='raise')`` saturation trap): any product
          outside ``[-2**63, 2**63)`` raises ``OverflowError``.
        * The uint64 phase accumulation wraps via an explicit
          ``& 0xFFFFFFFFFFFFFFFF`` mask — the wraparound *is* the
          cyclic-group reduction we want.

        v0.4.0: after the base encode, ``diagnosed_fibers.evaluate_active_patches``
        is queried; any active runtime patches contribute residue deltas
        that are summed onto the phase accumulator BEFORE the final
        ``& (MODULO - 1)`` reduction. With no patches active the encode
        is byte-identical to v0.3.1.
        """
        delta_t_days = float(date_jd - REFERENCE_JD)
        if not math.isfinite(delta_t_days):
            raise OverflowError(
                f"Non-finite delta_t_days={delta_t_days} for date_jd={date_jd}"
            )
        if abs(delta_t_days) > self._INT64_DELTA_DAYS_LIMIT:
            raise OverflowError(
                f"|date_jd - REFERENCE_JD| = {abs(delta_t_days):.3g} days "
                f"exceeds the int64 envelope ({self._INT64_DELTA_DAYS_LIMIT:.3g} d "
                f"≈ 1.86 Myr). The Q-format conversion ``omega * delta_t`` would "
                f"saturate. Stay inside the DE441 epoch or chunk the request."
            )
        return self._encode_state_impl(delta_t_days, date_jd=date_jd)

    def _i64_mul_checked(self, a: int, b: int) -> int:
        """Signed int64 multiply with an explicit overflow trap.

        Replicates ``np.errstate(over='raise')`` around an int64 product:
        the result must fit in the signed 64-bit range or this raises
        ``OverflowError`` (the same surface the old numpy path exposed).
        """
        r = a * b
        if not (self._I64_MIN <= r <= self._I64_MAX):
            raise OverflowError(
                f"int64 overflow in Q-format multiply: {a} * {b} = {r}"
            )
        return r

    def _encode_state_impl(self, delta_t_days: float, *, date_jd: float) -> array:
        # Integer chunk count + signed integer step direction.
        # delta_t_days has fractional sub-day content; we keep that as
        # a single trailing "remainder" step so the chunked loop only
        # ever multiplies by integers.
        chunk = self._CHUNK_DAYS
        sign = 1 if delta_t_days >= 0.0 else -1
        abs_days = abs(delta_t_days)
        num_steps = int(abs_days // chunk)
        remainder_days = abs_days - num_steps * chunk
        step_signed = sign * chunk  # Python int, +30 or -30

        u64 = self._U64_MASK
        n_bodies = len(self.body_names)

        # Phase accumulator: list of Python ints in [0, 2**64), initialised
        # from the calibrated uint32 phases. (uint64 cyclic group.)
        curr_phases = [int(p) for p in self.initial_phases_int]

        # Per-step trunk increment in int64 (signed). The multiply is the
        # only place silent overflow would *corrupt* the result; trap it
        # explicitly. Store as two's-complement uint64 for the wrapping add.
        omega = self.omega_diag                        # int64, residues/day
        trunk_step_u64 = [
            self._i64_mul_checked(int(omega[i]), step_signed) & u64
            for i in range(n_bodies)
        ]

        # Pre-resolve resonance entries: (idx_a, idx_b, n_a, m_b, base_nudge)
        # where base_nudge = scaled_coupling * step_signed in residues/chunk.
        resonance_table: List[Tuple[int, int, int, int, int]] = []
        for r in RESONANCES:
            if r.body_a not in self.body_to_idx or r.body_b not in self.body_to_idx:
                continue
            ia = self.body_to_idx[r.body_a]
            ib = self.body_to_idx[r.body_b]
            scaled = self._get_scaled_coupling(r.body_a, r.body_b)
            if scaled == 0:
                # No static weight to modulate — the breathing path would
                # be a no-op. _define_couplings ensures every resonance
                # pair has a non-zero weight, so this is a hard guard
                # against silent drift.
                continue
            base_nudge = scaled * step_signed
            resonance_table.append((ia, ib, r.n_a, r.m_b, base_nudge))

        mod_mask = MODULO - 1
        for _ in range(num_steps):
            # 1. Diagonal evolution: cyclic addition in Z_{2^64}.
            #    Final reduction to Z_{2^32} happens once at the end.
            for i in range(n_bodies):
                curr_phases[i] = (curr_phases[i] + trunk_step_u64[i]) & u64

            # 2. Breathing coupling — pure integer LUT, walked over the
            #    full RESONANCES table.
            for ia, ib, n_a, m_b, base_nudge in resonance_table:
                phi_a = curr_phases[ia] & mod_mask
                phi_b = curr_phases[ib] & mod_mask
                res_phase = (n_a * phi_a - m_b * phi_b) & mod_mask

                # cos_lut returns Q1.14 int in [-AMP, +AMP].
                # Modulation depth: 1 + (NUM/DEN) * cos.
                # Integer nudge = base + (NUM * base * cos) / (DEN * AMP).
                cos_q14 = cos_lut(res_phase, n_lobes=1)
                breath = (
                    self._BREATHING_AMP_NUM * base_nudge * cos_q14
                ) // (self._BREATHING_AMP_DEN * COSINE_LUT_AMP)
                nudge = base_nudge + breath

                nudge_u64 = nudge & u64  # two's-complement uint64 of a signed int
                curr_phases[ia] = (curr_phases[ia] + nudge_u64) & u64
                curr_phases[ib] = (curr_phases[ib] + nudge_u64) & u64

        # Sub-chunk remainder: one float multiply for the final
        # fractional-day fragment. The signed multiply runs under the
        # strict int64 trap; the uint64 add wraps in the cyclic group.
        # ``round()`` is round-half-to-even, identical to ``np.round``;
        # the float64 product ``omega[i] * (sign * remainder_days)`` is
        # bit-identical to numpy's int64*float64 -> float64.
        if remainder_days > 0.0:
            scale = sign * remainder_days
            for i in range(n_bodies):
                rstep = round(int(omega[i]) * scale)
                if not (self._I64_MIN <= rstep <= self._I64_MAX):
                    raise OverflowError(
                        f"int64 overflow in remainder multiply for body {i}"
                    )
                curr_phases[i] = (curr_phases[i] + (rstep & u64)) & u64

        # v0.4.0 runtime kernel patching — overlay step.
        # Active diagnosed-fiber patches contribute per-body residue
        # deltas that are SUMMED into the phase accumulator BEFORE the
        # final cyclic-group reduction. With zero patches active this
        # loop is a no-op and the encode is byte-identical to v0.3.1.
        if _patches.has_active_patches():
            overlay = _patches.evaluate_active_patches(date_jd, self.body_to_idx)
            for body_idx, delta_residue in overlay.items():
                delta_u64 = int(delta_residue) & u64
                curr_phases[body_idx] = (curr_phases[body_idx] + delta_u64) & u64

        return array("I", [(p & mod_mask) for p in curr_phases])

    def bind(self, phase_vec_a, phase_vec_b) -> array:
        """FPU-less binding: Modular addition."""
        return array("I", [
            (int(a) + int(b)) % MODULO
            for a, b in zip(phase_vec_a, phase_vec_b)
        ])

    def get_resolution(self, body: str = "terra") -> float:
        """Seconds per 1-unit residue shift."""
        body_info = BODIES.get(body.lower())
        if not body_info or body_info.period_days <= 0: return 0.0
        return (body_info.period_days * 86400.0) / MODULO

# ---------------------------------------------------------------------------
# Benchmark & Expansion Sweep
# ---------------------------------------------------------------------------

def run_dimensional_expansion_sweep():
    print("RBS-HDC Dimensional Expansion Sweep (ALU-Native Synthesis)")
    print("=" * 110)
    print(f"{'D (log2)':<10} {'D (size)':<12} {'Size (MB)':<12} {'Time (ms)':<12} {'Terra (441)':<15} {'Terra (442)':<15} {'SNR':<10}")
    print("-" * 110)
    
    import time
    powers = [16, 17, 18, 19, 20]
    results = []
    
    # Resolve data_dir
    research_dir = Path(__file__).resolve().parent
    project_root = research_dir.parents[2]
    data_dir = str(project_root / "skyfield_data")

    for p in powers:
        D = 2**p
        size_mb = (D * 4) / (1024 * 1024)
        
        instrument = EphemerisBIPInstrument(D=D, kernel="de441")
        test_jd = REFERENCE_JD + (20.0 * 365.25)
        
        start = time.perf_counter()
        phases = instrument.encode_state(test_jd)
        # Superpose the integer bases (uint32 cyclic add) — numpy-free.
        state = array("I", [0]) * D
        u32 = MODULO - 1
        for i, name in enumerate(instrument.body_names):
            base = instrument.channel_bases[name]
            ph = int(phases[i])
            for k in range(D):
                state[k] = (state[k] + base[k] + ph) & u32
        enc_time = (time.perf_counter() - start) * 1000

        # 3. DE441 Truth
        ts = instrument.bundle.ts
        t = ts.tt_jd(test_jd)
        astrometric = instrument.bundle.sun.at(t).observe(instrument.bundle.earth)
        _, lon, _ = astrometric.ecliptic_latlon()
        truth_rad = lon.radians

        idx_earth = instrument.body_names.index("terra")
        bip_earth_rad = (phases[idx_earth] / MODULO) * 2.0 * math.pi
        err_441 = abs((bip_earth_rad - truth_rad + math.pi) % (2.0 * math.pi) - math.pi)

        # 4. DE442 Truth
        bundle_442 = load_ephemeris(kernel="de442", data_dir=data_dir)
        err_442 = 0.0
        if bundle_442:
            t_442 = bundle_442.ts.tt_jd(test_jd)
            astrometric_442 = bundle_442.sun.at(t_442).observe(bundle_442.earth)
            _, lon_442, _ = astrometric_442.ecliptic_latlon()
            err_442 = abs((bip_earth_rad - lon_442.radians + math.pi) % (2.0 * math.pi) - math.pi)
        
        # 5. SNR
        snr = D / (len(instrument.body_names) - 1)
        
        print(f"{p:<10} {D:<12} {size_mb:<12.2f} {enc_time:<12.3f} {err_441:<15.8f} {err_442:<15.8f} {snr:<10.0f}")
        results.append((p, size_mb, enc_time, err_441, err_442, snr))

    return results

if __name__ == "__main__":
    run_dimensional_expansion_sweep()
