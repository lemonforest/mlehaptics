## UTLP Vector Time Reference Implementation

This Python implementation validates the mathematical foundations of Part VI (Vector Time) before port to embedded C. It demonstrates the coprime cyclic hierarchy, generative compression, similarity-based synchronization, calendar time conversion, and **multi-resolution support** (nanosecond extension via segmented architecture).

**File:** `utlp_vector_time.py`
**License:** GPL-3.0-or-later
**Dependencies:** numpy (for hypervector operations)

```python
#!/usr/bin/env python3
"""
UTLP Vector Time Reference Implementation
=========================================

Coprime Swarm Clock with Generative Compression.

This implementation validates the mathematical foundations before C port.
It demonstrates:
  1. Coprime cyclic hierarchy (the "cosmic gearbox")
  2. Generative compression (transmit chord, regenerate vector)
  3. Similarity-based synchronization (fuzzy coherency)
  4. Calendar time conversion (Chinese Remainder Theorem)
  5. Multi-resolution segmented architecture (μs + ns tiers)

Usage:
    python utlp_vector_time.py

Author: mlehaptics Project
Date: January 2026
License: GPL-3.0-or-later
"""

import numpy as np
from functools import reduce
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict


# =============================================================================
# CONSTANTS
# =============================================================================

# Prime cycle lengths - 8 primes < 256, product ~= 8.24 x 10^1^8
# Fits in 8 bytes (one uint8_t per prime)
# Horizon: 261,000 years at 1us ticks
DEFAULT_PRIMES = (241, 251, 239, 233, 229, 227, 223, 211)

# Hypervector dimensions
DEFAULT_DIMS = 10000

# Tick period (microseconds)
DEFAULT_TICK_US = 1


# =============================================================================
# CHINESE REMAINDER THEOREM
# =============================================================================

def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean Algorithm.
    Returns (gcd, x, y) such that ax + by = gcd.
    """
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


def chinese_remainder_theorem(remainders: List[int], moduli: List[int]) -> int:
    """
    Solve system of congruences using CRT.
    
    Find x such that:
        x = r_0 (mod m_0)
        x = r_1 (mod m_1)
        ...
    
    Args:
        remainders: List of remainders [r_0, r_1, ...]
        moduli: List of moduli [m_0, m_1, ...] (must be pairwise coprime)
    
    Returns:
        Unique solution x in range [0, M) where M = Pi m_i
    """
    M = reduce(lambda a, b: a * b, moduli)
    x = 0
    
    for r_i, m_i in zip(remainders, moduli):
        M_i = M // m_i
        _, _, y_i = extended_gcd(m_i, M_i)
        x += r_i * M_i * y_i
    
    return x % M


# =============================================================================
# VECTOR TIME CLOCK
# =============================================================================

class UTLPVectorClock:
    """
    Coprime Swarm Clock with Generative Compression.
    
    Time is represented as a high-dimensional state vector that evolves
    through a deterministic trajectory. The vector is generated from
    coprime cyclic rotations of base hypervectors.
    
    Key properties:
        - Aliasing horizon exceeds 2^64 unique states (with 7 primes)
        - Generative compression: transmit ~14 bytes, regenerate 10,000 bits
        - Similarity metric enables fuzzy synchronization
        - Calendar conversion via Chinese Remainder Theorem
    """
    
    def __init__(self, 
                 primes: Tuple[int, ...] = DEFAULT_PRIMES,
                 dimensions: int = DEFAULT_DIMS,
                 seed: int = 42,
                 tick_period_us: int = DEFAULT_TICK_US):
        """
        Initialize vector clock.
        
        Args:
            primes: Coprime cycle lengths (must be pairwise coprime)
            dimensions: Hypervector dimensionality
            seed: RNG seed for reproducible base vectors (derive from Swarm DNA)
            tick_period_us: Microseconds per tick
        """
        self.primes = list(primes)
        self.dims = dimensions
        self.tick_period_us = tick_period_us
        
        # Validate primes are coprime
        for i, p1 in enumerate(self.primes):
            for p2 in self.primes[i+1:]:
                assert extended_gcd(p1, p2)[0] == 1, f"{p1} and {p2} not coprime"
        
        # Generate deterministic base vectors from seed
        # In production, derive from Swarm DNA via HKDF
        rng = np.random.default_rng(seed)
        self.base_vectors: Dict[int, np.ndarray] = {
            p: rng.choice([-1, 1], size=dimensions).astype(np.int8)
            for p in self.primes
        }
        
        # Initialize phase state (all zeros = epoch origin)
        self.phases: Dict[int, int] = {p: 0 for p in self.primes}
        
        # Calendar anchor (set during genesis calibration)
        self.epoch_start: Optional[datetime] = None
    
    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------
    
    def tick(self, n: int = 1) -> None:
        """
        Advance time by n ticks.
        
        Each tick rotates all phase counters by 1.
        """
        for p in self.primes:
            self.phases[p] = (self.phases[p] + n) % p
    
    def get_chord(self) -> List[int]:
        """
        Get current phase chord (wire format).
        
        Returns list of phase values, one per prime.
        This is what gets transmitted over the air.
        """
        return [self.phases[p] for p in self.primes]
    
    def set_chord(self, chord: List[int]) -> None:
        """
        Set phase state from chord.
        
        Used when receiving beacon or loading saved state.
        """
        for i, p in enumerate(self.primes):
            self.phases[p] = chord[i] % p
    
    def regenerate_vector(self, chord: Optional[List[int]] = None) -> np.ndarray:
        """
        Build full hypervector from chord.
        
        This is the "texture" of the specified moment.
        Expensive operation - cache when possible.
        
        Args:
            chord: Phase chord (defaults to current state)
        
        Returns:
            Binarized hypervector of shape (dims,) with values +/-1
        """
        if chord is None:
            chord = self.get_chord()
        
        t_global = np.zeros(self.dims, dtype=np.float32)
        
        for i, p in enumerate(self.primes):
            phase = chord[i]
            rotated = np.roll(self.base_vectors[p], phase)
            t_global += rotated
        
        return np.sign(t_global).astype(np.int8)
    
    # -------------------------------------------------------------------------
    # Similarity Metrics
    # -------------------------------------------------------------------------
    
    def similarity(self, chord_a: List[int], chord_b: List[int]) -> float:
        """
        Compute similarity between two time states.
        
        Full vector similarity - expensive but accurate.
        
        Returns:
            Cosine similarity in range [-1.0, +1.0]
            +1.0 = identical, 0.0 = orthogonal, -1.0 = opposite
        """
        vec_a = self.regenerate_vector(chord_a)
        vec_b = self.regenerate_vector(chord_b)
        
        # Cosine similarity for binary vectors
        return float(np.dot(vec_a.astype(np.float32), 
                           vec_b.astype(np.float32)) / self.dims)
    
    def phase_distance(self, chord_a: List[int], chord_b: List[int]) -> float:
        """
        Compute phase-space distance (faster approximation).
        
        Measures distance in phase space without regenerating full vectors.
        Useful for quick similarity checks.
        
        Returns:
            Distance in range [0.0, 1.0]
            0.0 = identical, 1.0 = maximally different
        """
        total_dist = 0.0
        
        for i, p in enumerate(self.primes):
            diff = abs(chord_a[i] - chord_b[i])
            # Wrap around ring
            if diff > p // 2:
                diff = p - diff
            total_dist += diff / p
        
        return total_dist / len(self.primes)
    
    def phase_similarity(self, chord_a: List[int], chord_b: List[int]) -> float:
        """
        Convert phase distance to similarity metric.
        
        Returns:
            Similarity in range [0.0, 1.0]
            1.0 = identical, 0.0 = maximally different
        """
        return 1.0 - self.phase_distance(chord_a, chord_b)
    
    # -------------------------------------------------------------------------
    # Calendar Conversion
    # -------------------------------------------------------------------------
    
    def calibrate_to_calendar(self, calendar_time: datetime) -> None:
        """
        Set epoch anchor for calendar conversion.
        
        Call this at genesis when external time reference is available.
        The current chord becomes associated with the given calendar time.
        """
        self.epoch_start = calendar_time
    
    def chord_to_ticks(self, chord: List[int]) -> int:
        """
        Convert chord to total ticks via Chinese Remainder Theorem.
        """
        return chinese_remainder_theorem(chord, self.primes)
    
    def ticks_to_chord(self, ticks: int) -> List[int]:
        """
        Convert total ticks to chord (modular reduction).
        """
        return [ticks % p for p in self.primes]
    
    def to_calendar(self, chord: Optional[List[int]] = None) -> datetime:
        """
        Convert chord to calendar time.
        
        Args:
            chord: Phase chord (defaults to current state)
        
        Returns:
            Calendar datetime
        
        Raises:
            ValueError: If clock not calibrated
        """
        if self.epoch_start is None:
            raise ValueError("Clock not calibrated to calendar. "
                           "Call calibrate_to_calendar() first.")
        
        if chord is None:
            chord = self.get_chord()
        
        ticks = self.chord_to_ticks(chord)
        microseconds = ticks * self.tick_period_us
        
        return self.epoch_start + timedelta(microseconds=microseconds)
    
    def from_calendar(self, calendar_time: datetime) -> List[int]:
        """
        Convert calendar time to chord.
        
        Args:
            calendar_time: Calendar datetime
        
        Returns:
            Phase chord
        
        Raises:
            ValueError: If clock not calibrated or time before epoch
        """
        if self.epoch_start is None:
            raise ValueError("Clock not calibrated to calendar. "
                           "Call calibrate_to_calendar() first.")
        
        delta = calendar_time - self.epoch_start
        total_us = delta.total_seconds() * 1_000_000
        
        if total_us < 0:
            raise ValueError("Calendar time before epoch start")
        
        ticks = int(total_us / self.tick_period_us)
        return self.ticks_to_chord(ticks)
    
    # -------------------------------------------------------------------------
    # Elastic Synchronization
    # -------------------------------------------------------------------------
    
    def nudge_toward(self, peer_chord: List[int], 
                     learning_rate: float = 0.1,
                     peer_trust: float = 1.0) -> None:
        """
        Elastic sync: nudge local state toward peer.
        
        Does not snap to peer; applies gradient proportional to
        distance and trust weight.
        
        Args:
            peer_chord: Peer's phase chord
            learning_rate: Base adjustment rate (0.0 to 1.0)
            peer_trust: Trust weight for this peer (0.0 to 1.0)
        """
        effective_rate = learning_rate * peer_trust
        
        for i, p in enumerate(self.primes):
            my_phase = self.phases[p]
            peer_phase = peer_chord[i]
            
            # Shortest distance around ring
            diff = peer_phase - my_phase
            if abs(diff) > p // 2:
                diff = diff - p if diff > 0 else diff + p
            
            nudge = int(diff * effective_rate)
            self.phases[p] = (my_phase + nudge) % p
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def aliasing_horizon(self) -> int:
        """Total unique states before aliasing (product of all primes)."""
        return reduce(lambda a, b: a * b, self.primes)
    
    @property
    def horizon_years(self) -> float:
        """Years until aliasing at current tick rate."""
        ticks = self.aliasing_horizon
        seconds = ticks * self.tick_period_us / 1_000_000
        return seconds / (365.25 * 24 * 3600)
    
    @property
    def wire_bytes(self) -> int:
        """Bytes required to transmit chord (1 byte per prime for small primes)."""
        # For primes < 256, each phase fits in uint8_t
        max_prime = max(self.primes)
        bytes_per_phase = 1 if max_prime < 256 else 2
        return len(self.primes) * bytes_per_phase
    
    def __repr__(self) -> str:
        chord = self.get_chord()
        return f"UTLPVectorClock(chord={chord}, horizon_years={self.horizon_years:.1e})"


# =============================================================================
# MULTI-RESOLUTION SEGMENTED CLOCK (S3 Section 14)
# =============================================================================

class UTLPSegmentedClock:
    """
    Multi-resolution vector clock with segmented architecture.
    
    Supports both microsecond (standard) and nanosecond (fine) resolution
    through vector concatenation rather than superposition. This preserves
    backward compatibility: μs-only hardware reads the standard segment
    unchanged.
    
    Mathematical basis: Cross-tier superposition causes 30-50% bit interference
    destroying compatibility. Concatenation provides zero interference.
    
    See: UTLP Technical Supplement S3, Section 14
    """
    
    # Prime configurations
    PRIMES_STD = (241, 251, 239, 233, 229, 227, 223, 211)  # 8 primes, 1μs
    PRIMES_FINE = (997, 1009, 1013, 1019)  # 4 primes, 1ns
    
    DIMS_STD = 10000
    DIMS_FINE = 4000
    
    def __init__(self, seed: int = 42, enable_fine: bool = True):
        """
        Initialize segmented clock.
        
        Args:
            seed: Random seed for deterministic base vector generation
            enable_fine: Whether to enable nanosecond-resolution fine segment
        """
        self.enable_fine = enable_fine
        self.rng = np.random.default_rng(seed)
        
        # Current tick counts
        self.ticks_us = 0
        self.ticks_ns_offset = 0  # [0-999] within current microsecond
        
        # Generate base vectors for standard segment
        self.base_std = {
            p: self.rng.choice([-1, 1], size=self.DIMS_STD).astype(np.int8)
            for p in self.PRIMES_STD
        }
        
        # Generate base vectors for fine segment
        if enable_fine:
            self.base_fine = {
                p: self.rng.choice([-1, 1], size=self.DIMS_FINE).astype(np.int8)
                for p in self.PRIMES_FINE
            }
    
    def tick_us(self, n: int = 1):
        """Advance by n microseconds."""
        self.ticks_us += n
        self.ticks_ns_offset = 0  # Reset sub-microsecond
    
    def tick_ns(self, n: int = 1):
        """Advance by n nanoseconds."""
        total_ns = self.ticks_ns_offset + n
        self.ticks_us += total_ns // 1000
        self.ticks_ns_offset = total_ns % 1000
    
    def get_chord_std(self) -> List[int]:
        """Get standard (μs) phase chord."""
        return [self.ticks_us % p for p in self.PRIMES_STD]
    
    def get_chord_fine(self) -> Optional[List[int]]:
        """Get fine (ns) phase chord, or None if not enabled."""
        if not self.enable_fine:
            return None
        fine_ticks = self.ticks_us * 1000 + self.ticks_ns_offset
        return [fine_ticks % p for p in self.PRIMES_FINE]
    
    def get_chords(self) -> Tuple[List[int], Optional[List[int]]]:
        """Get both chord tuples."""
        return self.get_chord_std(), self.get_chord_fine()
    
    def regenerate_vector(self, chord_std: List[int], 
                          chord_fine: Optional[List[int]] = None) -> np.ndarray:
        """
        Regenerate full hyperdimensional vector from phase chords.
        
        Returns concatenated [V_std | V_fine] if fine chord provided,
        otherwise just V_std.
        
        Key insight: Concatenation (not superposition) preserves backward
        compatibility. μs hardware reads V_std unchanged.
        """
        # Standard segment: superposition of 8 rotated base vectors
        v_std = np.zeros(self.DIMS_STD, dtype=np.float32)
        for i, p in enumerate(self.PRIMES_STD):
            rotated = np.roll(self.base_std[p], chord_std[i])
            v_std += rotated
        v_std = np.sign(v_std).astype(np.int8)
        
        if chord_fine is not None and self.enable_fine:
            # Fine segment: superposition of 4 rotated base vectors
            v_fine = np.zeros(self.DIMS_FINE, dtype=np.float32)
            for i, p in enumerate(self.PRIMES_FINE):
                rotated = np.roll(self.base_fine[p], chord_fine[i])
                v_fine += rotated
            v_fine = np.sign(v_fine).astype(np.int8)
            
            # Concatenate (NOT superimpose) - this is critical!
            return np.concatenate([v_std, v_fine])
        
        return v_std
    
    def get_vector(self) -> np.ndarray:
        """Get current time as hyperdimensional vector."""
        chord_std, chord_fine = self.get_chords()
        return self.regenerate_vector(chord_std, chord_fine)
    
    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray, 
                   segment: str = 'both') -> float:
        """
        Compute similarity between vectors.
        
        Args:
            segment: 'std' (standard only), 'fine' (fine only), or 'both'
        """
        if segment == 'std':
            a = vec_a[:self.DIMS_STD]
            b = vec_b[:self.DIMS_STD]
        elif segment == 'fine':
            if len(vec_a) <= self.DIMS_STD:
                raise ValueError("Vector has no fine segment")
            a = vec_a[self.DIMS_STD:]
            b = vec_b[self.DIMS_STD:]
        else:
            a, b = vec_a, vec_b
        
        return float(np.dot(a.astype(np.float32), 
                           b.astype(np.float32))) / len(a)
    
    def extract_standard(self, full_vector: np.ndarray) -> np.ndarray:
        """
        Extract standard segment for backward compatibility.
        
        μs-only hardware uses this to read ns-capable beacons.
        """
        return full_vector[:self.DIMS_STD]
    
    @property
    def aliasing_horizon_std(self) -> int:
        """Standard segment horizon in μs ticks."""
        from functools import reduce
        return reduce(lambda a, b: a * b, self.PRIMES_STD)
    
    @property
    def aliasing_horizon_fine(self) -> int:
        """Fine segment horizon in ns ticks."""
        if not self.enable_fine:
            return 0
        from functools import reduce
        return reduce(lambda a, b: a * b, self.PRIMES_FINE)
    
    @property
    def horizon_years_std(self) -> float:
        """Standard horizon in years."""
        ticks = self.aliasing_horizon_std
        seconds = ticks / 1_000_000  # 1μs ticks
        return seconds / (365.25 * 24 * 3600)
    
    @property
    def horizon_minutes_fine(self) -> float:
        """Fine horizon in minutes (resets relative to standard)."""
        if not self.enable_fine:
            return 0.0
        ticks = self.aliasing_horizon_fine
        seconds = ticks / 1_000_000_000  # 1ns ticks
        return seconds / 60
    
    @property
    def wire_bytes_std(self) -> int:
        """Wire bytes for standard segment."""
        return 8  # 8 primes × 1 byte
    
    @property
    def wire_bytes_fine(self) -> int:
        """Wire bytes for fine segment."""
        return 8 if self.enable_fine else 0  # 4 primes × 2 bytes
    
    @property
    def wire_bytes_total(self) -> int:
        """Total wire bytes."""
        return self.wire_bytes_std + self.wire_bytes_fine
    
    def __repr__(self) -> str:
        chord_std, chord_fine = self.get_chords()
        fine_str = f", fine={chord_fine}" if chord_fine else ""
        return f"UTLPSegmentedClock(std={chord_std}{fine_str})"


def demo_segmented_clock():
    """Demonstrate multi-resolution segmented clock."""
    print("=" * 60)
    print("UTLP Segmented Clock - Multi-Resolution Support")
    print("=" * 60)
    
    # Create ns-capable clock
    clock_ns = UTLPSegmentedClock(enable_fine=True)
    
    # Create μs-only clock (simulates legacy hardware)
    clock_us = UTLPSegmentedClock(enable_fine=False)
    
    print(f"\nNanosecond clock initialized:")
    print(f"  Standard primes: {clock_ns.PRIMES_STD}")
    print(f"  Fine primes: {clock_ns.PRIMES_FINE}")
    print(f"  Standard dims: {clock_ns.DIMS_STD}")
    print(f"  Fine dims: {clock_ns.DIMS_FINE}")
    print(f"  Standard horizon: {clock_ns.horizon_years_std:,.0f} years")
    print(f"  Fine horizon: {clock_ns.horizon_minutes_fine:.1f} minutes")
    print(f"  Wire bytes: {clock_ns.wire_bytes_total} (std: {clock_ns.wire_bytes_std}, fine: {clock_ns.wire_bytes_fine})")
    
    # Test backward compatibility
    print("\n--- Backward Compatibility Test ---")
    
    # Advance both clocks to same μs
    clock_ns.tick_us(123456789)
    clock_us.tick_us(123456789)
    
    # Add ns offset to ns clock
    clock_ns.tick_ns(500)
    
    # Generate vectors
    v_ns_full = clock_ns.get_vector()
    v_us_only = clock_us.get_vector()
    
    # Extract standard segment from full vector
    v_std_from_full = clock_ns.extract_standard(v_ns_full)
    
    print(f"  Full ns vector dims: {len(v_ns_full)}")
    print(f"  μs-only vector dims: {len(v_us_only)}")
    print(f"  Extracted standard dims: {len(v_std_from_full)}")
    
    # Critical test: extracted standard should match μs-only
    match = np.array_equal(v_std_from_full, v_us_only)
    print(f"  Standard segments identical: {match} {'✓' if match else '✗ FAIL'}")
    
    # Test fine segment differentiation
    print("\n--- Resolution Differentiation Test ---")
    
    clock_a = UTLPSegmentedClock(enable_fine=True)
    clock_b = UTLPSegmentedClock(enable_fine=True)
    
    clock_a.tick_us(1000)
    clock_a.tick_ns(100)
    
    clock_b.tick_us(1000)
    clock_b.tick_ns(500)
    
    v_a = clock_a.get_vector()
    v_b = clock_b.get_vector()
    
    sim_std = clock_a.similarity(v_a, v_b, segment='std')
    sim_fine = clock_a.similarity(v_a, v_b, segment='fine')
    sim_both = clock_a.similarity(v_a, v_b, segment='both')
    
    print(f"  Same μs, different ns (100 vs 500):")
    print(f"    Standard similarity: {sim_std:.4f} (should be ~1.0)")
    print(f"    Fine similarity: {sim_fine:.4f} (should be < 1.0)")
    print(f"    Combined similarity: {sim_both:.4f}")
    
    return match  # Return True if backward compatibility preserved


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo_basic_operations():
    """Demonstrate basic clock operations."""
    print("=" * 60)
    print("UTLP Vector Time - Basic Operations")
    print("=" * 60)
    
    clock = UTLPVectorClock()
    
    print(f"\nClock initialized:")
    print(f"  Primes: {clock.primes}")
    print(f"  Dimensions: {clock.dims}")
    print(f"  Aliasing horizon: {clock.aliasing_horizon:,} ticks")
    print(f"  Horizon: {clock.horizon_years:,.0f} years")
    print(f"  Wire bytes: {clock.wire_bytes}")
    
    print(f"\nInitial chord: {clock.get_chord()}")
    
    clock.tick(1000)
    print(f"After 1000 ticks: {clock.get_chord()}")
    
    clock.tick(1_000_000)
    print(f"After 1M more ticks: {clock.get_chord()}")


def demo_similarity_decay():
    """Demonstrate how similarity decays with time distance."""
    print("\n" + "=" * 60)
    print("Similarity Decay with Time Distance")
    print("=" * 60)
    
    clock = UTLPVectorClock()
    chord_0 = clock.get_chord()
    
    print(f"\n{'Delta':>12} {'Phase Sim':>12} {'Vector Sim':>12}")
    print("-" * 40)
    
    for delta in [0, 1, 10, 100, 1000, 10000, 100000]:
        clock.set_chord(chord_0)  # Reset
        clock.tick(delta)
        chord_n = clock.get_chord()
        
        phase_sim = clock.phase_similarity(chord_0, chord_n)
        vector_sim = clock.similarity(chord_0, chord_n)
        
        print(f"{delta:>12,} {phase_sim:>12.4f} {vector_sim:>12.4f}")


def demo_calendar_conversion():
    """Demonstrate calendar time conversion."""
    print("\n" + "=" * 60)
    print("Calendar Time Conversion")
    print("=" * 60)
    
    clock = UTLPVectorClock()
    
    # Calibrate to epoch
    epoch = datetime(2026, 1, 1, 0, 0, 0)
    clock.calibrate_to_calendar(epoch)
    
    print(f"\nEpoch: {epoch}")
    print(f"Initial chord: {clock.get_chord()}")
    
    # Advance 1 second (1M microseconds)
    clock.tick(1_000_000)
    cal = clock.to_calendar()
    print(f"\nAfter 1 second:")
    print(f"  Chord: {clock.get_chord()}")
    print(f"  Calendar: {cal}")
    
    # Round-trip test
    print("\nRound-trip conversion test:")
    test_times = [
        datetime(2026, 1, 15, 12, 30, 45, 123456),
        datetime(2026, 6, 1, 0, 0, 0, 0),
        datetime(2026, 12, 31, 23, 59, 59, 999999),
    ]
    
    for t in test_times:
        chord = clock.from_calendar(t)
        recovered = clock.to_calendar(chord)
        match = "[OK]" if t == recovered else "[FAIL]"
        print(f"  {t} -> {chord[:3]}... -> {recovered} [{match}]")


def demo_elastic_sync():
    """Demonstrate elastic synchronization between two clocks."""
    print("\n" + "=" * 60)
    print("Elastic Synchronization")
    print("=" * 60)
    
    # Two clocks with same base vectors (same swarm)
    clock_a = UTLPVectorClock(seed=42)
    clock_b = UTLPVectorClock(seed=42)
    
    # Clock B is 100 ticks behind
    clock_a.tick(1000)
    clock_b.tick(900)
    
    print(f"\nInitial state (A is 100 ticks ahead):")
    print(f"  Clock A: {clock_a.get_chord()}")
    print(f"  Clock B: {clock_b.get_chord()}")
    print(f"  Similarity: {clock_a.phase_similarity(clock_a.get_chord(), clock_b.get_chord()):.4f}")
    
    # B syncs toward A over several iterations
    print(f"\nElastic sync (B nudging toward A):")
    for i in range(10):
        clock_b.nudge_toward(clock_a.get_chord(), learning_rate=0.2)
        sim = clock_a.phase_similarity(clock_a.get_chord(), clock_b.get_chord())
        print(f"  Iteration {i+1}: similarity = {sim:.4f}")
        
        if sim > 0.999:
            print(f"  Converged!")
            break


def demo_wire_format():
    """Demonstrate wire format size comparison."""
    print("\n" + "=" * 60)
    print("Wire Format Comparison")
    print("=" * 60)
    
    print(f"\n{'Format':<30} {'Bytes':>8} {'Unique States':>20}")
    print("-" * 60)
    
    # Scalar formats
    print(f"{'uint32_t':<30} {4:>8} {2**32:>20,}")
    print(f"{'uint64_t':<30} {8:>8} {2**64:>20,}")
    
    # Vector formats with small primes (8-bit each)
    small_primes_8 = (241, 251, 239, 233, 229, 227, 223, 211)
    clock_8 = UTLPVectorClock(primes=small_primes_8)
    print(f"{'Vector (8 small primes)':<30} {clock_8.wire_bytes:>8} "
          f"{clock_8.aliasing_horizon:>20,}")
    
    # Vector formats with large primes (16-bit each)
    large_primes_5 = (997, 1009, 1013, 1019, 1021)
    clock_5 = UTLPVectorClock(primes=large_primes_5)
    print(f"{'Vector (5 large primes)':<30} {clock_5.wire_bytes:>8} "
          f"{clock_5.aliasing_horizon:>20,}")
    
    large_primes_7 = (997, 1009, 1013, 1019, 1021, 1031, 1033)
    clock_7 = UTLPVectorClock(primes=large_primes_7)
    print(f"{'Vector (7 large primes)':<30} {clock_7.wire_bytes:>8} "
          f"{clock_7.aliasing_horizon:>20,}")


def main():
    """Run all demonstrations."""
    demo_basic_operations()
    demo_similarity_decay()
    demo_calendar_conversion()
    demo_elastic_sync()
    demo_wire_format()
    demo_segmented_clock()  # Multi-resolution support (S3 Section 14)
    
    print("\n" + "=" * 60)
    print("All demonstrations complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

---

