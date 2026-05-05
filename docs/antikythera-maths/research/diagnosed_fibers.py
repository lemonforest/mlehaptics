"""Diagnosed-fiber runtime patches — overlay on the spectral kernel.

Architectural premise (v0.4.0)
------------------------------

The spectral kernel — the static `RESONANCES` table, the Laplacian
construction, the integer Q-format frequencies — is **immutable
truth**. We don't mutate it to chase residuals.

Patches are *overlays*. They live in a module-level registry, are
authored as data (not code edits), and are summed into the encoded
phases at the END of the encode path. The base encoder bytes never
change. Inspired by Linux ksplice / kpatch.

Why this design
~~~~~~~~~~~~~~~

* **Reproducibility** — a published kernel hashes the same forever.
  A patch that breaks Mars by 3° is unloadable / disposable; the
  kernel keeps shipping clean.
* **Composition** — multiple patches stack on top. Order-independent
  for sinusoidal kinds (sin sums commute).
* **Diagnosis-driven authoring** — v0.3.1's
  `de441_error_spectrum.py` reports per-body FFT residual peaks. A
  patch's job is to subtract one of those peaks; whether the patch
  *helps* is then a measurable property (re-run the FFT, check the
  peak shrunk).

Patch kinds (v0.4.0)
~~~~~~~~~~~~~~~~~~~~

`SinusoidPatch`
    A diagonal correction: ``delta_phase_b(t) = A * sin(2π
    (t - REFERENCE_JD) / period + phi)`` added to body ``b``'s phase
    residue at encode time. Authored from a single body's FFT peak.

`CoupledSinusoidPatch`
    An off-diagonal correction tying two bodies. Same sinusoid, but
    applied with sign ``+1`` to ``body_a`` and ``correlation`` (``+1``
    same-sign or ``-1`` opposite-sign) to ``body_b``. Authored when
    the FFT shows the SAME peak in both bodies — the smoking-gun
    "missing coupling" signal. The Jupiter–Saturn 9.56-yr ±45° peaks
    are the exemplar (anti-correlated, libration in the J-S 5:2
    resonance).

Discipline
~~~~~~~~~~

* Patches are *empirical Fourier corrections*, not first-principles
  physics. They paper over a missing coupling in the static
  `RESONANCES` table or a missing PN term. A patch is a hypothesis —
  "this peak is a sin at this period" — that v0.4.x's first-principles
  derivation should ultimately replace.
* The C native backend (``backend="c"``) DOES NOT yet implement the
  overlay. With patches active, ``backend="c"`` transparently falls
  back to ``backend="bip"`` — guaranteeing correctness at the cost
  of the C path's speed. (v0.4.x phase F adds ABI v2 + ``es_apply_patch``
  for the C-side overlay.)

The runtime overlay registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Public API (also re-exported via ``ephemerides_spectral.bridge``):

    apply_patch(patch)           -> None
    list_patches()               -> List[Dict[str, Any]]
    clear_patches()              -> int      (count cleared)
    snapshot()                   -> Tuple[Patch, ...]   (immutable)
    get_catalog()                -> Dict[str, Patch]
    apply_catalog_patch(name)    -> None     (apply named bundled patch)

`evaluate_active_patches(jd_tdb, body_to_idx)` is the encoder hook —
returns ``{body_idx: int_residue_delta}`` summing all active patches.
The BIP encoder calls this at the end of its encode loop.

CATALOG (v0.4.0)
~~~~~~~~~~~~~~~~

Three patches authored from the v0.3.1 FFT analysis
(`results/de441_error_spectrum.md`):

* ``mars-7.96yr-diagonal``      diagonal Mars correction, A ≈ 3.45°
* ``mercury-10.69yr-diagonal``  diagonal Mercury correction, A ≈ 9.19°
* ``jupiter-saturn-9.56yr-coupled``
                                anti-correlated J-S libration
                                correction, A ≈ 45° each

Use ``apply_catalog_patch("mars-7.96yr-diagonal")`` to wire one in,
or ``apply_patch(SinusoidPatch(...))`` to author your own.
"""

from __future__ import annotations

import math
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Tuple, Union

# -- Q-format constants. Mirrors bip_instrument.py / es_encode.c. ---
# We DON'T import from ``bip_instrument`` to keep the dependency arrow
# clean (bip_instrument imports diagnosed_fibers; the reverse would
# create a cycle).
K_BITS: int = 32
MODULO: int = 2**K_BITS
REFERENCE_JD: float = 2451545.0


# ──────────────────────────────────────────────────────────────────────
# Patch dataclasses
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SinusoidPatch:
    """Diagonal sinusoidal correction on a single body.

    At encode JD ``t`` (TDB), adds

        delta_residue = round(A_residue * sin(2π Δt / period + phi))

    to ``phases[body_idx]``, where ``A_residue = round(amplitude_deg /
    360 × 2^32)`` is the amplitude in residue units and ``Δt = t -
    REFERENCE_JD``.

    Authored from a single-body FFT peak (e.g. Mars at 7.96 yr,
    amplitude 3.45° in v0.3.1's ``de441_error_spectrum``).
    """

    name: str
    body: str
    amplitude_deg: float
    period_days: float
    phase_rad: float = 0.0
    notes: str = ""
    kind: str = field(default="sinusoid", init=False)

    def evaluate(
        self, jd_tdb: float, body_to_idx: Mapping[str, int]
    ) -> Dict[int, int]:
        if self.body not in body_to_idx:
            return {}
        delta_t = float(jd_tdb) - REFERENCE_JD
        ang = 2.0 * math.pi * delta_t / float(self.period_days) + float(self.phase_rad)
        amp_residue = int(round(float(self.amplitude_deg) / 360.0 * MODULO))
        delta = int(round(amp_residue * math.sin(ang)))
        return {body_to_idx[self.body]: delta}


@dataclass(frozen=True)
class CoupledSinusoidPatch:
    """Off-diagonal sinusoidal correction tying two bodies.

    Applied with sign ``+1`` to ``body_a`` and ``correlation`` to
    ``body_b`` — ``correlation = -1`` is the default (anti-correlated
    libration in a mean-motion resonance, which is what J-S 5:2 shows
    in the v0.3.1 FFT analysis).

    The ``correlation`` value must be ``+1`` or ``-1``.
    """

    name: str
    body_a: str
    body_b: str
    amplitude_deg: float
    period_days: float
    phase_rad: float = 0.0
    correlation: int = -1
    notes: str = ""
    kind: str = field(default="coupled-sinusoid", init=False)

    def __post_init__(self) -> None:
        if self.correlation not in (-1, 1):
            raise ValueError(
                f"correlation must be -1 or +1, got {self.correlation!r}"
            )

    def evaluate(
        self, jd_tdb: float, body_to_idx: Mapping[str, int]
    ) -> Dict[int, int]:
        out: Dict[int, int] = {}
        if self.body_a not in body_to_idx and self.body_b not in body_to_idx:
            return out
        delta_t = float(jd_tdb) - REFERENCE_JD
        ang = 2.0 * math.pi * delta_t / float(self.period_days) + float(self.phase_rad)
        amp_residue = int(round(float(self.amplitude_deg) / 360.0 * MODULO))
        delta = int(round(amp_residue * math.sin(ang)))
        if self.body_a in body_to_idx:
            out[body_to_idx[self.body_a]] = delta
        if self.body_b in body_to_idx:
            out[body_to_idx[self.body_b]] = self.correlation * delta
        return out


Patch = Union[SinusoidPatch, CoupledSinusoidPatch]


# ──────────────────────────────────────────────────────────────────────
# Module-level registry
# ──────────────────────────────────────────────────────────────────────

# Lock guards mutation. Reads (snapshot, evaluate_active_patches) take
# the lock briefly to grab a tuple snapshot, then iterate without
# holding it — patches are immutable dataclasses so the snapshot is
# safe to use lock-free.
_LOCK = threading.RLock()
_ACTIVE: List[Patch] = []


def apply_patch(patch: Patch) -> None:
    """Register a patch in the runtime overlay.

    Raises ``ValueError`` if a patch with the same ``name`` is
    already active. (Same name twice is almost always a bug; clear
    first if you mean to replace.)
    """
    if not isinstance(patch, (SinusoidPatch, CoupledSinusoidPatch)):
        raise TypeError(
            f"apply_patch expects a SinusoidPatch or CoupledSinusoidPatch, "
            f"got {type(patch).__name__}"
        )
    with _LOCK:
        if any(p.name == patch.name for p in _ACTIVE):
            raise ValueError(
                f"patch named {patch.name!r} is already active; "
                f"clear_patches() first or pick a unique name"
            )
        _ACTIVE.append(patch)


def clear_patches() -> int:
    """Remove all active patches; return the count cleared."""
    with _LOCK:
        n = len(_ACTIVE)
        _ACTIVE.clear()
    return n


def list_patches() -> List[Dict[str, Any]]:
    """Return a JSON-friendly list of active patches (Pyodide-safe)."""
    with _LOCK:
        return [_patch_to_dict(p) for p in _ACTIVE]


def snapshot() -> Tuple[Patch, ...]:
    """Return an immutable tuple snapshot of active patches.

    Encoder hook: take a snapshot once, iterate without holding the
    registry lock during the encode loop.
    """
    with _LOCK:
        return tuple(_ACTIVE)


def evaluate_active_patches(
    jd_tdb: float, body_to_idx: Mapping[str, int]
) -> Dict[int, int]:
    """Sum every active patch's contribution at this JD.

    Returns a ``{body_idx: int_residue_delta}`` dict. The BIP encoder
    adds the per-body delta into ``curr_phases[body_idx]`` AFTER the
    base encode loop has finished — pure overlay, no mutation of
    base state.
    """
    out: Dict[int, int] = {}
    for patch in snapshot():
        contributions = patch.evaluate(jd_tdb, body_to_idx)
        for body_idx, delta in contributions.items():
            out[body_idx] = out.get(body_idx, 0) + int(delta)
    return out


def has_active_patches() -> bool:
    """Cheap check — used by backend dispatchers to gate the C path."""
    with _LOCK:
        return bool(_ACTIVE)


def _patch_to_dict(patch: Patch) -> Dict[str, Any]:
    d = asdict(patch)
    # asdict drops ``kind`` because it's an init=False field — re-add
    # it explicitly so JSON consumers can dispatch on the kind string.
    d["kind"] = patch.kind
    return d


# ──────────────────────────────────────────────────────────────────────
# Catalog — bundled patches authored from v0.3.1 FFT findings
# ──────────────────────────────────────────────────────────────────────

#: Bundled patches derived from the v0.3.1 ``de441_error_spectrum``
#: analysis (results/de441_error_spectrum.md). Each is a hypothesis
#: targeting one FFT residual peak. Use ``apply_catalog_patch("name")``
#: to load by string; iterate ``CATALOG.values()`` for all of them.
CATALOG: Dict[str, Patch] = {
    "mars-7.96yr-diagonal": SinusoidPatch(
        name="mars-7.96yr-diagonal",
        body="mars",
        amplitude_deg=3.45,
        period_days=2907.3,
        notes=(
            "Empirical correction for Mars FFT residual at 7.96 yr "
            "(ranks 1-2 in the v0.3.1 spectrum, amplitude 3.45 deg). "
            "Probably a missing Mars-Saturn or Mars-Jupiter sub-resonance "
            "not in the v0.2.0 RESONANCES table."
        ),
    ),
    "mercury-10.69yr-diagonal": SinusoidPatch(
        name="mercury-10.69yr-diagonal",
        body="mercury",
        amplitude_deg=9.19,
        period_days=3905.1,
        notes=(
            "Empirical correction for Mercury's 10.69 yr residual peak "
            "(rank 1 in the v0.3.1 spectrum, amplitude 9.19 deg). "
            "Likely a higher-order PN beat with Jupiter that the v0.1.0 "
            "L_pn entry (43 arcsec/century perihelion advance) misses."
        ),
    ),
    "jupiter-saturn-9.56yr-coupled": CoupledSinusoidPatch(
        name="jupiter-saturn-9.56yr-coupled",
        body_a="jupiter",
        body_b="saturn",
        amplitude_deg=45.0,
        period_days=3490.9,
        correlation=-1,
        notes=(
            "Smoking-gun missing-coupling signal from v0.3.1's FFT. "
            "Jupiter and Saturn show identical 9.56 yr peaks at ~45 deg "
            "amplitude (the J-S 5:2 conjunction beat). The v0.2.0 "
            "alpha=0.1 modulation depth undershoots the actual libration "
            "by ~5x. Anti-correlated correction shrinks both peaks "
            "simultaneously (libration is +Jupiter / -Saturn around the "
            "5:2 mean-motion resonance)."
        ),
    ),
}


# ──────────────────────────────────────────────────────────────────────
# CATALOG_V2 — phase-recovered, LS-fit, measured-vindicated (v0.5.2)
# ──────────────────────────────────────────────────────────────────────
#
# v0.4.0 catalog patches were authored from FFT magnitudes only. The
# v0.5.1 patch-shrinks-residual benchmark measured them and found the
# methodology had two bugs (amplitude off by 2×, phase wrongly assumed
# 0) and one wrong assumption (J-S correlation = +1, not -1).
#
# v0.5.2's LS-fit catalog fixes both:
#   - amplitude/period/phase/correlation extracted via `scipy.optimize
#     .curve_fit` on a sinusoid at the target period (not from the
#     FFT-bin magnitude); skips bin leakage entirely
#   - the cancellation phase is the fitted phase + π (anti-phase)
#
# All four targeted bodies hit ≥96% shrinkage in the verifier
# (Mars 99.2%, Mercury 99.9%, Jupiter 97.6%, Saturn 96.0%). The
# original v0.4.0 catalog stays in CATALOG for backwards compatibility;
# CATALOG_V2 is the *measured-to-work* set.
#
# Each entry's `notes` field carries the measured shrinkage% as a
# regression-test gate. Future catalog additions should pin their
# measured shrinkage the same way.
CATALOG_V2: Dict[str, Patch] = {
    "mars-7.96yr-diagonal-v2": SinusoidPatch(
        name="mars-7.96yr-diagonal-v2",
        body="mars",
        amplitude_deg=10.6890,
        period_days=2902.74,
        phase_rad=0.3378,  # cancellation phase: fitted + π, mod 2π
        notes=(
            "v0.5.2 LS-fit recovery against the v0.5.0 38-body encoder. "
            "Targets Mars's 7.96 yr FFT residual peak; LS fit recovered "
            "amp 10.69 deg (vs FFT-bin-only 3.45 deg, off by 3x due to "
            "bin leakage), period 2902.74 d (-4.6 d from bin-rounded). "
            "MEASURED SHRINKAGE: 99.2% (3.45 deg -> 0.03 deg) in the "
            "v0.5.2 verify-recovered-patches benchmark."
        ),
    ),
    "mercury-10.69yr-diagonal-v2": SinusoidPatch(
        name="mercury-10.69yr-diagonal-v2",
        body="mercury",
        amplitude_deg=23.4815,
        period_days=3898.87,
        phase_rad=3.0538,
        notes=(
            "v0.5.2 LS-fit recovery against the v0.5.0 38-body encoder. "
            "Mercury's 10.69 yr peak; LS recovered amp 23.48 deg (vs "
            "FFT-bin 9.19 deg) and period 3898.87 d (-6.2 d from "
            "bin-rounded 3905.08 d). The original v0.4.0 patch had "
            "phase=0 which actively REINFORCED the residual (-50% "
            "shrinkage); v0.5.2's phase=3.05 rad (175 deg) is the "
            "cancellation phase. MEASURED SHRINKAGE: 99.9% (9.19 deg "
            "-> 0.008 deg)."
        ),
    ),
    "jupiter-saturn-9.56yr-coupled-v2": CoupledSinusoidPatch(
        name="jupiter-saturn-9.56yr-coupled-v2",
        body_a="jupiter",
        body_b="saturn",
        amplitude_deg=113.2947,
        period_days=3495.81,
        phase_rad=6.0191,
        correlation=+1,  # IN-PHASE, NOT anti-correlated as v0.4.0 assumed
        notes=(
            "v0.5.2 LS-fit recovery against the v0.5.0 38-body encoder. "
            "EMPIRICAL FINDING: J-S residuals at 9.56 yr are IN-PHASE "
            "(correlation = +1), NOT anti-correlated as the v0.4.0 "
            "libration assumption had it. Recovered amp 113.29 deg "
            "(vs FFT-bin 45 deg). MEASURED SHRINKAGE: Jupiter 97.6%, "
            "Saturn 96.0% in the v0.5.2 verify-recovered-patches "
            "benchmark — both peaks collapsed in lockstep, the way an "
            "in-phase coupled patch should."
        ),
    ),
    # ──────────────────────────────────────────────────────────────────
    # v0.5.5 (Phase C) — moon catalog patches authored from the v0.5.3
    # corrected residuals via the same LS-fit pipeline that vindicated
    # the planet patches. 5 of 6 moon targets land ≥93%; Hyperion (the
    # canonical chaotic rotator) tops out at 75% with a single sinusoid
    # and is queued for a follow-up multi-component or coupled-T-H patch.
    # ──────────────────────────────────────────────────────────────────
    "dione-1.06yr-diagonal-v2": SinusoidPatch(
        name="dione-1.06yr-diagonal-v2",
        body="dione",
        amplitude_deg=3.5738,
        period_days=387.04,
        phase_rad=1.5027,
        notes=(
            "v0.5.5 (Phase C) LS-fit recovery against the v0.5.3 corrected "
            "moon residuals. Targets Dione's dominant 387.04-d peak. "
            "Recovered amp 3.57 deg (vs FFT-bin 1.17 deg, 3x bin leakage). "
            "MEASURED SHRINKAGE: 98.2% (1.17 deg -> 0.02 deg); RMS residual "
            "2.535 deg -> 0.199 deg in the v0.5.5 verify-moon-patches "
            "benchmark."
        ),
    ),
    "tethys-0.38yr-diagonal-v2": SinusoidPatch(
        name="tethys-0.38yr-diagonal-v2",
        body="tethys",
        amplitude_deg=3.5733,
        period_days=138.24,
        phase_rad=1.1054,
        notes=(
            "v0.5.5 (Phase C). Tethys's dominant 138.24-d peak. "
            "Recovered amp 3.57 deg (vs FFT-bin 1.75 deg, 2x bin leakage). "
            "MEASURED SHRINKAGE: 93.8% (1.75 deg -> 0.11 deg); RMS residual "
            "2.944 deg -> 1.511 deg."
        ),
    ),
    "enceladus-0.39yr-diagonal-v2": SinusoidPatch(
        name="enceladus-0.39yr-diagonal-v2",
        body="enceladus",
        amplitude_deg=3.5751,
        period_days=141.94,
        phase_rad=1.3156,
        notes=(
            "v0.5.5 (Phase C). Enceladus's dominant 141.94-d peak. "
            "Recovered amp 3.58 deg (vs FFT-bin 1.52 deg, 2.4x bin leakage). "
            "MEASURED SHRINKAGE: 98.9% (1.52 deg -> 0.02 deg); RMS residual "
            "2.569 deg -> 0.458 deg. The patched peak demoted below "
            "the K-th-strongest patched peak (upper bound)."
        ),
    ),
    "titan-0.69yr-diagonal-v2": SinusoidPatch(
        name="titan-0.69yr-diagonal-v2",
        body="titan",
        amplitude_deg=3.3130,
        period_days=252.74,
        phase_rad=0.2929,
        notes=(
            "v0.5.5 (Phase C). Titan's dominant 252.74-d peak. "
            "Recovered amp 3.31 deg (vs FFT-bin 1.56 deg, 2.1x bin leakage). "
            "MEASURED SHRINKAGE: 95.5% (1.56 deg -> 0.07 deg); RMS residual "
            "3.388 deg -> 2.447 deg."
        ),
    ),
    "iapetus-0.22yr-diagonal-v2": SinusoidPatch(
        name="iapetus-0.22yr-diagonal-v2",
        body="iapetus",
        amplitude_deg=3.2636,
        period_days=79.34,
        phase_rad=3.6725,
        notes=(
            "v0.5.5 (Phase C). Iapetus's dominant 79.34-d peak. "
            "Recovered amp 3.26 deg (vs FFT-bin 1.58 deg, 2.1x bin leakage). "
            "MEASURED SHRINKAGE: 98.6% (1.58 deg -> 0.02 deg); RMS residual "
            "2.497 deg -> 0.954 deg."
        ),
    ),
}


#: Combined view of all bundled catalogs. Keys from CATALOG and
#: CATALOG_V2 are disjoint (the v2 entries carry the ``-v2`` suffix).
COMBINED_CATALOG: Dict[str, Patch] = {**CATALOG, **CATALOG_V2}


def get_catalog() -> Dict[str, Patch]:
    """Return a copy of every bundled patch (v1 + v2 combined).

    v0.4.0 entries (no suffix) stay for backwards compatibility.
    v0.5.2 entries (``-v2`` suffix) are the measured-to-work set —
    each has ≥96% shrinkage on its targeted FFT residual peak.
    """
    return dict(COMBINED_CATALOG)


def apply_catalog_patch(name: str) -> Patch:
    """Load a named bundled patch into the overlay registry.

    Looks up `name` in the combined catalog (v1 + v2). Returns the
    patch object that was applied. Raises ``KeyError`` if no catalog
    entry has that name; raises ``ValueError`` if it's already active
    (same as ``apply_patch``).
    """
    if name not in COMBINED_CATALOG:
        raise KeyError(
            f"no catalog patch named {name!r}; "
            f"available: {sorted(COMBINED_CATALOG.keys())}"
        )
    patch = COMBINED_CATALOG[name]
    apply_patch(patch)
    return patch
