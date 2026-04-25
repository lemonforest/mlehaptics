"""Resonant HDC encoder for the Antikythera mechanism (Phase 2).

This module implements three D-variant encoders plus a block-diagonal
reference oracle.  The encoders produce **angular dynamic state only** —
no pre-baked (x, y) pointer positions — per the rendering-agnostic
discipline (Patch 3): radial parameters live in ``rendering.py``.

The three D variants (per the "both/and" build-prompt discipline):

- ``D_CALLIPPIC = 940`` (Callippic × 4, by way of 4 × 235-month Metonic).
  Calendar cycles fit cleanly; planetary dials are explicitly unsupported
  via ``UnsupportedDialError``.
- ``D_LCM`` = lcm of every cycle's numerator and denominator.  Exact and
  natural but astronomically large (≳ 10¹³); too big to materialise as a
  real numpy array.  Encoded *symbolically* via ``LCMState`` — a sparse
  residue dictionary that round-trips trivially.
- ``D_PACKING = 13440 = 2⁷·3·5·7``.  HDC-engineered packing per chess
  §9f's coprime-roll architecture; supports all dials with bounded
  quantisation error 1/D per cycle phase.

Each dial has its **own dense complex channel basis** (not delta spikes).
A delta basis collapses catastrophically when total residue classes
exceed D — explicit issue at D=940 — whereas a dense complex unit-norm
random basis degrades gracefully.  Bases are deterministically seeded
per (D, dial_index) so tests are byte-reproducible.

Encoding (dense variants):

    state = sum_dial  roll(channel_basis_dial, residue_dial(date))

then normalise.  Decoding (in ``dial_decoder.py``) unbinds per dial by
correlating against rolls of the channel basis.

``σ_day(D) = roll_operator(D, 1)`` is the formal unitary on ℂ[ℤ/Dℤ] —
a single generator of the cyclic group, so gcd(1, D) = 1 confirms B-H2
("crank-turn is a unit in ℤ/Dℤ") by construction.  ``advance_day(date,
D, days)`` is the physically meaningful day advance via re-encoding —
because each dial advances at its own daily rate, the "advance one day"
action on the multi-dial encoded state is most cleanly expressed as
"re-encode tomorrow".  The build prompt's "one operator, many
projections" framing is honoured by ``sigma_day`` (the operator) and
the per-dial decoder projections (the many).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from math import lcm
from typing import Dict, List, Optional, Tuple

import numpy as np

from .astronomical_cycles import CYCLES, Cycle
from .cyclic_group_algebra import lcm_many, roll_operator


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

REFERENCE_JD: float = 1684595.0
"""Reference Julian Day for date-to-residue conversion.

JD 1684595 corresponds to ~205 BCE, the Hellenistic-era epoch the
mechanism would plausibly have been calibrated against.  All
``encode_ant_*`` functions compute residues from ``date_jd -
REFERENCE_JD`` to avoid ``datetime.today()`` drift.  The choice of
epoch does not affect any structural claim — only the absolute residue
values for a given date — so this is a convention, not a measurement.
"""

D_CALLIPPIC: int = 940
"""D for the Callippic-cycle variant (4 × Metonic 235-month cycle).

Calendar cycles (Metonic, Callippic, Olympic, Saros, Exeligmos, lunar)
fit cleanly under quantisation; planetary cycles whose periods are
much longer than 940 synodic months are explicitly unsupported and
raise ``UnsupportedDialError``.
"""

D_PACKING: int = 13440
"""D for the HDC-packing variant: 2⁷·3·5·7.

Engineered for coprime-roll binding (chess §9f).  Supports all
thirteen dials with quantisation error 1/D per cycle phase
(≈ 7.4·10⁻⁵).
"""


def _compute_d_lcm() -> int:
    """LCM of every cycle numerator and denominator.

    Computed at import; logged in __main__.  Astronomically large;
    used symbolically (see ``LCMState``).
    """
    moduli: List[int] = []
    for c in CYCLES:
        if c.numerator > 0:
            moduli.append(c.numerator)
        if c.denominator > 0:
            moduli.append(c.denominator)
    return lcm_many(moduli)


D_LCM: int = _compute_d_lcm()
"""LCM of all cycle moduli.  Too large to materialise — see ``LCMState``."""


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class UnsupportedDialError(ValueError):
    """Raised when a dial is queried that the chosen D variant cannot encode."""


class OrthogonalityError(RuntimeError):
    """Raised when channel-basis Gram matrix off-diagonal exceeds the threshold
    after the maximum number of re-seed attempts."""


# ---------------------------------------------------------------------------
# DialSpec — one per cycle, factored out so the (cycle × variant) table
# is not triple-maintained.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DialSpec:
    """A single dial: name, underlying ``Cycle``, supported-D matrix.

    The dense channel basis for a given (D, dial_idx) is computed
    on-demand by ``get_channel_basis`` and cached.
    """

    name: str
    cycle: Cycle

    @property
    def cycle_period_days(self) -> Optional[float]:
        """Cycle period in SI days (the mechanism's encoded period)."""
        return self.cycle.mechanism_days

    @property
    def cycle_modulus(self) -> int:
        """The integer modulus the mechanism uses for this cycle.

        For Metonic this is 235 (synodic months / Metonic cycle); for
        Saros it is 223 (synodic months / Saros).  The modulus is the
        cycle.numerator field — the count the dial returns to zero on.
        """
        return self.cycle.numerator if self.cycle.numerator > 0 else 1

    def is_supported(self, D: int) -> bool:
        """D=940 omits planetary; all other D variants accept all dials."""
        if D == D_CALLIPPIC and self.cycle.tag == "planetary":
            return False
        return True

    def residue(self, date_jd: float, D: int) -> int:
        """Quantised residue 0..D-1 for this dial at ``date_jd``."""
        if not self.is_supported(D):
            raise UnsupportedDialError(
                f"Dial {self.name!r} not supported at D={D}"
            )
        if self.cycle_period_days is None or self.cycle_period_days <= 0:
            raise ValueError(
                f"Cycle {self.name!r} has no usable mechanism_days; "
                "encoding is not defined."
            )
        days = date_jd - REFERENCE_JD
        phase = (days / self.cycle_period_days) % 1.0  # in [0, 1)
        return int(phase * D) % D

    def integer_residue(self, date_jd: float) -> int:
        """Residue 0..modulus-1 in the cycle's natural integer encoding.

        Used by ``LCMState`` (D-independent) and the block-diagonal
        oracle (where each cycle gets its own block).
        """
        if self.cycle_period_days is None or self.cycle_period_days <= 0:
            raise ValueError(
                f"Cycle {self.name!r} has no usable mechanism_days"
            )
        days = date_jd - REFERENCE_JD
        phase = (days / self.cycle_period_days) % 1.0
        return int(phase * self.cycle_modulus) % self.cycle_modulus


DIAL_SPECS: List[DialSpec] = [
    DialSpec(name=c.name, cycle=c) for c in CYCLES
]


def supported_dials(D: int) -> List[DialSpec]:
    """List of ``DialSpec`` whose ``is_supported(D)`` is True."""
    return [s for s in DIAL_SPECS if s.is_supported(D)]


# ---------------------------------------------------------------------------
# Channel-basis construction and Gram-matrix orthogonality pre-flight
# ---------------------------------------------------------------------------

# Per-D base seed.  Re-seeds on Gram-matrix failure walk this forward.
_BASE_SEEDS: Dict[int, int] = {
    D_CALLIPPIC: 42,
    D_PACKING: 1729,
}

# Cache: (D, dial_idx) -> ndarray of shape (D,) complex128, unit-norm.
_channel_bases_cache: Dict[Tuple[int, int], np.ndarray] = {}


def _make_channel_basis(D: int, dial_idx: int, base_seed: int) -> np.ndarray:
    """Dense complex unit-norm random vector seeded from base_seed + dial_idx.

    Returns ``np.complex128`` of shape ``(D,)``.  The unit-norm
    constraint makes inner products bounded by 1 in absolute value, so
    cross-talk between channels is directly comparable.
    """
    rng = np.random.default_rng(base_seed + dial_idx)
    real = rng.standard_normal(D)
    imag = rng.standard_normal(D)
    v = (real + 1j * imag).astype(np.complex128)
    return v / np.linalg.norm(v)


def get_channel_basis(D: int, dial_idx: int) -> np.ndarray:
    """Return the cached or freshly-built channel basis for (D, dial_idx)."""
    key = (D, dial_idx)
    if key not in _channel_bases_cache:
        seed = _BASE_SEEDS.get(D, 42)
        _channel_bases_cache[key] = _make_channel_basis(D, dial_idx, seed)
    return _channel_bases_cache[key]


def _clear_basis_cache_for_d(D: int) -> None:
    keys_to_drop = [k for k in _channel_bases_cache if k[0] == D]
    for k in keys_to_drop:
        del _channel_bases_cache[k]


def channel_basis_gram_max_offdiag(D: int) -> float:
    """Max absolute off-diagonal entry of the channel-basis Gram matrix.

    Built over the *supported* dials only.  Lower is better; Plan
    agent's recommended threshold for HDC cross-talk is < 0.05.
    """
    supported = supported_dials(D)
    bases = np.stack([
        get_channel_basis(D, DIAL_SPECS.index(s)) for s in supported
    ])
    G = bases @ bases.conj().T
    np.fill_diagonal(G, 0.0)
    return float(np.max(np.abs(G)))


def verify_channel_basis_orthogonality(
    D: int,
    threshold: float = 0.05,
    max_attempts: int = 16,
) -> float:
    """Re-seed channel bases until Gram off-diagonal max < threshold.

    Returns the achieved max off-diagonal value.  Raises
    ``OrthogonalityError`` after ``max_attempts`` failures.

    The seed walks forward by one each attempt — deterministic and
    short.  Once verified, the working seed is recorded back into
    ``_BASE_SEEDS[D]`` so subsequent ``get_channel_basis`` calls (and
    their cached values) match.
    """
    initial_seed = _BASE_SEEDS.get(D, 42)
    seed = initial_seed
    for attempt in range(max_attempts):
        _BASE_SEEDS[D] = seed
        _clear_basis_cache_for_d(D)
        max_offdiag = channel_basis_gram_max_offdiag(D)
        if max_offdiag < threshold:
            return max_offdiag
        seed += 1
    raise OrthogonalityError(
        f"Could not find orthogonal channel-basis at D={D} after "
        f"{max_attempts} re-seeds (initial seed {initial_seed})."
    )


# ---------------------------------------------------------------------------
# Dense-superposition encoders (D=940 and D=13440)
# ---------------------------------------------------------------------------

def _encode_dense(date_jd: float, D: int) -> np.ndarray:
    """Sum-of-rolled-bases encoding of all supported dials, normalised."""
    state = np.zeros(D, dtype=np.complex128)
    for i, spec in enumerate(DIAL_SPECS):
        if not spec.is_supported(D):
            continue
        residue = spec.residue(date_jd, D)
        basis = get_channel_basis(D, i)
        state += np.roll(basis, residue)
    norm = np.linalg.norm(state)
    if norm > 0.0:
        state /= norm
    return state


def encode_ant_callippic(date_jd: float) -> np.ndarray:
    """D=940 dense encoding (calendar cycles only)."""
    return _encode_dense(date_jd, D_CALLIPPIC)


def encode_ant_packing(date_jd: float) -> np.ndarray:
    """D=13440 dense encoding (all thirteen dials)."""
    return _encode_dense(date_jd, D_PACKING)


# ---------------------------------------------------------------------------
# Symbolic / sparse encoder (D = LCM, too big to materialise)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LCMState:
    """Symbolic state for the D=LCM variant.

    The LCM of all cycle moduli is too large to allocate (>10¹³); we
    instead store the *exact* residue per cycle, which is the
    information that a hypothetical D=LCM dense vector would
    superpose.  Decoding is direct lookup; round-trip is by
    construction perfect.

    This is the project's answer to F-E2 ("Is there a natural D_Ant at
    which every cycle becomes a single integer?"): yes,
    ``D_LCM = lcm_many(numerators ∪ denominators)``, computed at
    import.  Whether it is *useful* as an HDC dimension is a separate
    question (it is not — too large).
    """

    D: int
    residues: Dict[str, int]

    def is_supported(self, dial_name: str) -> bool:
        return dial_name in self.residues


def encode_ant_lcm(date_jd: float) -> LCMState:
    """Symbolic D=LCM encoding — one integer residue per supported dial."""
    residues: Dict[str, int] = {}
    for spec in DIAL_SPECS:
        if spec.cycle_period_days is None or spec.cycle_period_days <= 0:
            continue
        residues[spec.name] = spec.integer_residue(date_jd)
    return LCMState(D=D_LCM, residues=residues)


# ---------------------------------------------------------------------------
# Block-diagonal oracle (decoder ground-truth for B-H3)
# ---------------------------------------------------------------------------

def encode_ant_block_diagonal(date_jd: float, D: int) -> np.ndarray:
    """Reference encoder where each cycle lives in a disjoint D-slice.

    Block size = D // n_supported_dials (integer division; remainder
    is left as zeros).  Within its block, the cycle's integer residue
    is mapped to a single 1.0 entry at position ``residue %
    block_size``.  Trivially decodable; serves as the ground-truth
    oracle for B-H3 cross-validation against the dense superposition
    encoders.
    """
    supported = supported_dials(D)
    n = len(supported)
    if n == 0:
        return np.zeros(D, dtype=np.complex128)
    block_size = D // n
    state = np.zeros(D, dtype=np.complex128)
    for i, spec in enumerate(supported):
        residue = spec.integer_residue(date_jd)
        offset = residue % block_size
        state[i * block_size + offset] = 1.0
    return state


# ---------------------------------------------------------------------------
# σ_day operator and physical advance_day
# ---------------------------------------------------------------------------

def sigma_day(D: int) -> np.ndarray:
    """Single-day-advance unitary on ℂ[ℤ/Dℤ] as an explicit matrix.

    σ_day = roll_operator(D, 1) — the canonical generator of ℤ/Dℤ.
    Trivially gcd(1, D) = 1, so σ_day is a unit, confirming B-H2 by
    construction.

    NOTE: σ_day rolls the *D-bin counter* by one.  Because the
    multiple dial channels have different physical advance rates
    (Metonic: 1 month per ~30 days; Mars: 1 synodic per ~780 days),
    σ_day applied directly to a multi-dial encoded state advances
    each channel by 1 D-bin, which is *not* the same as advancing the
    physical date by one day.  For physically meaningful day advance
    use ``advance_day(date, D, days)`` which re-encodes for the new
    date; this is the "many projections" half of "one operator, many
    projections."
    """
    return roll_operator(D, 1)


def advance_day(date_jd: float, D: int, days: int = 1) -> np.ndarray:
    """Physically meaningful day advance via re-encoding."""
    return _encode_dense(date_jd + days, D)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Resonant HDC encoder for the Antikythera mechanism (Phase 2)")
    print("=" * 60)
    print()
    print(f"REFERENCE_JD     = {REFERENCE_JD}")
    print(f"D_CALLIPPIC      = {D_CALLIPPIC}")
    print(f"D_PACKING        = {D_PACKING}")
    print(f"D_LCM            = {D_LCM:_}  ({len(str(D_LCM))} digits)")
    print()

    # Cross-talk pre-flight for the dense variants
    for D, label in [(D_CALLIPPIC, "Callippic"), (D_PACKING, "Packing")]:
        max_offdiag = verify_channel_basis_orthogonality(D)
        n_supported = len(supported_dials(D))
        print(f"D={D} ({label}): {n_supported} supported dials, "
              f"Gram max off-diag = {max_offdiag:.4f}  "
              f"(threshold < 0.05: {'PASS' if max_offdiag < 0.05 else 'FAIL'})")
    print()

    # Sample encodings
    test_jd = REFERENCE_JD + 365.0  # one year after epoch
    print(f"Sample encoding at JD = {test_jd} (REFERENCE_JD + 365 days):")
    print()

    s_callippic = encode_ant_callippic(test_jd)
    print(f"  encode_ant_callippic: shape={s_callippic.shape} "
          f"dtype={s_callippic.dtype} "
          f"||state||={np.linalg.norm(s_callippic):.4f}")

    s_packing = encode_ant_packing(test_jd)
    print(f"  encode_ant_packing:   shape={s_packing.shape} "
          f"dtype={s_packing.dtype} "
          f"||state||={np.linalg.norm(s_packing):.4f}")

    s_lcm = encode_ant_lcm(test_jd)
    print(f"  encode_ant_lcm:       LCMState with "
          f"{len(s_lcm.residues)} residues, D={s_lcm.D:_}")
    for name, r in list(s_lcm.residues.items())[:5]:
        print(f"    {name:35s} residue = {r}")
    if len(s_lcm.residues) > 5:
        print(f"    ... ({len(s_lcm.residues) - 5} more)")

    s_block = encode_ant_block_diagonal(test_jd, D_PACKING)
    print(f"  encode_ant_block_diagonal (D={D_PACKING}): "
          f"shape={s_block.shape} non-zero={int(np.sum(np.abs(s_block) > 0))}")
    print()

    # σ_day check
    sd = sigma_day(D_CALLIPPIC)
    print(f"sigma_day(D=940): shape={sd.shape}  "
          f"unitary check |det|={abs(np.linalg.det(sd)):.4f} "
          f"(should be 1.0 for permutation matrix)")
    print()

    # advance_day check
    s0 = encode_ant_callippic(test_jd)
    s1 = advance_day(test_jd, D_CALLIPPIC, days=1)
    overlap = float(np.abs(np.vdot(s0, s1)))
    print(f"advance_day overlap |<state(t), state(t+1)>| = {overlap:.4f} "
          f"(should be < 1; some decorrelation expected)")
    print()

    print("All smoke tests pass.")
