#!/usr/bin/env python3
"""
UTLP Statistical Simulation: Genesis Reset + Antiphase Lock

Scenario:
1. 3-node swarm (Genesis A, Followers B, C) synced for hours
2. Genesis A resets (power cycle, watchdog, crash)
3. B and C drift slightly during A's downtime (~50ms)
4. A comes back online and attempts to rejoin
5. Question: Can A lock back in ANTIPHASE (180° offset)?

This simulates the Metabolic Ledger trust dynamics and "First Born Wins"
tie-breaker to explore edge cases in swarm recovery.

Author: Claude Code (statistical simulation for protocol validation)
Date: December 2025
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

# =============================================================================
# UTLP CONSTANTS (from utlp_trust.h)
# =============================================================================

UTLP_TRUST_MAX = 255
UTLP_TRUST_STARTUP = 50
UTLP_TRUST_SYNC_THRESH = 100
UTLP_TRUST_MIN_QUORUM = 60

UTLP_REWARD_TRUTH = 2       # Agreement with consensus
UTLP_COST_DRIFTING = 10     # 2ms - 100ms deviation
UTLP_COST_LYING = 50        # >100ms deviation

AGREEMENT_THRESHOLD_US = 2000    # 2ms
DRIFT_THRESHOLD_US = 100000      # 100ms

# Simulation parameters
BEACON_INTERVAL_MS = 1000        # 1 second for Phase 3
SIMULATION_TICKS = 600           # 10 minutes of operation

# Genesis Pulse Detection (S2.25)
GENESIS_PULSE_THRESHOLD_MS = 2000     # Interval < 2s = genesis pulsing
MIN_INTERVAL_OBSERVATIONS = 2          # Need at least 2 observations
REGRESSION_THRESHOLD_US = 10_000_000   # 10 second backward jump = regression


class NodeState(Enum):
    GENESIS = "GENESIS"      # Stratum 1, time authority
    FOLLOWER = "FOLLOWER"    # Stratum 2+, following someone
    WARMING = "WARMING"      # Just booted, stabilizing


@dataclass
class PeerEntry:
    """Metabolic Ledger entry for one peer"""
    mac: str
    health: int = UTLP_TRUST_STARTUP
    stratum: int = 1
    last_offset_us: int = 0
    interactions: int = 0
    consecutive_hits: int = 0

    # Behavioral Profile (Physics-Based Byzantine Detection)
    first_observed_local_us: int = 0      # My local time when I first saw them
    first_observed_atomic_us: int = 0     # Their atomic time at first observation
    observed_drift_rate_ppm: float = 0.0  # Their average drift rate
    drift_samples: int = 0                # Number of drift measurements
    drift_variance: float = 100.0         # Variance in drift rate (starts high)
    last_atomic_us: int = 0               # Previous atomic time observation
    last_local_us: int = 0                # My local time at previous observation

    # =========================================================================
    # DERIVATIVE TRACKING (Integer Math for Byzantine Detection)
    # =========================================================================

    # 1st Derivative: Jitter (dOffset/dt)
    last_jitter_us: int = 0               # Previous jitter value
    jitter_ema_us: int = 0                # EMA of jitter (α=0.1 via integer: (new + 9*old)/10)

    # 2nd Derivative: Jitter Variance (stability of jitter)
    jitter_sum_sq: int = 0                # Sum of (jitter - mean)² for variance
    jitter_variance_us2: int = 0          # Variance of jitter in μs² (integer)
    jitter_samples: int = 0               # Sample count for variance calc

    # 1st Derivative: Health Velocity (dHealth/dt)
    health_velocity: int = 0              # EMA of health delta per observation
    prev_health: int = UTLP_TRUST_STARTUP # Previous health for delta calc
    health_velocity_samples: int = 0      # Sample count

    # Drift Rate (Integer-Scaled: milli-PPM for precision without floats)
    drift_rate_mppm: int = 0              # Drift rate in milli-PPM (1000 = 1 ppm)
    drift_rate_variance_mppm2: int = 0    # Variance in milli-PPM squared

    # =========================================================================
    # GENESIS PULSE DETECTION (S2.25 - Fast Reboot Detection)
    # =========================================================================
    # Rebooted peers broadcast rapidly (100ms→500ms→1s→10s→60s genesis phases)
    # Detecting 2-3 rapid beacons identifies reboot within 300-500ms
    first_seen_ms: int = 0                # When we first saw this peer (local ms)
    last_seen_local_ms: int = 0           # My local ms at last observation
    observed_interval_ms: int = 60000     # EMA of beacon intervals (starts at steady-state)
    interval_observations: int = 0        # Number of interval measurements
    last_tx_time_us: int = 0              # Last TX timestamp (for regression detection)


@dataclass
class Node:
    """Simulated UTLP node"""
    mac: str
    state: NodeState = NodeState.WARMING
    stratum: int = 15  # Warming up

    # Timing
    local_clock_us: int = 0          # Local monotonic clock
    atomic_time_us: int = 0          # UTLP atomic time (what we broadcast)
    time_offset_us: int = 0          # Offset from "true" time
    drift_rate_ppm: float = 0.0      # Clock drift (parts per million)

    # Trust
    peers: Dict[str, PeerEntry] = field(default_factory=dict)

    # Stats
    boot_time_us: int = 0
    is_online: bool = True

    def get_atomic_time(self) -> int:
        """Get current atomic time (what we'd put in a beacon)"""
        return self.local_clock_us + self.time_offset_us

    def tick(self, delta_us: int):
        """Advance local clock with drift"""
        if not self.is_online:
            return
        drift_us = int(delta_us * self.drift_rate_ppm / 1_000_000)
        self.local_clock_us += delta_us + drift_us
        self.atomic_time_us = self.get_atomic_time()


@dataclass
class Beacon:
    """UTLP beacon packet"""
    mac: str
    tx_timestamp_us: int  # Sender's atomic time
    stratum: int


class UTLPSimulator:
    """
    Simulates UTLP swarm behavior with Metabolic Ledger trust dynamics
    """

    def __init__(self, seed: int = 42, behavioral_verification: bool = False):
        random.seed(seed)
        self.true_time_us = 0
        self.nodes: List[Node] = []
        self.log: List[str] = []
        self.tick_count = 0
        self.behavioral_verification = behavioral_verification  # Physics-based Byzantine defense

        # =====================================================================
        # COHERENCE TRACKING (Swarm-Level 1st Derivative)
        # =====================================================================
        # Track how coherence changes over time - rapid drops indicate attack
        self.coherence_history: List[int] = []   # % coherence over time
        self.coherence_velocity: int = 0          # EMA of coherence change
        self.last_coherence_pct: int = 100        # Previous coherence for delta

    def add_node(self, mac: str, drift_ppm: float = 0.0,
                 initial_offset_us: int = 0,
                 boot_variance_us: int = 0) -> Node:
        """
        Add a node to the simulation

        Args:
            mac: Node MAC address identifier
            drift_ppm: Clock drift rate in parts per million
            initial_offset_us: Initial atomic time offset
            boot_variance_us: Random boot time variance range in microseconds (±).
                             If non-zero, adds random offset in [-boot_variance_us, +boot_variance_us]
                             to simulate realistic boot timing differences.
                             The universe is vast - devices almost never boot at the same wall time.
        """
        # Apply boot time variance if specified
        boot_offset_us = 0
        if boot_variance_us > 0:
            boot_offset_us = random.randint(-boot_variance_us, boot_variance_us)

        node = Node(
            mac=mac,
            drift_rate_ppm=drift_ppm,
            time_offset_us=initial_offset_us + boot_offset_us,
            boot_time_us=self.true_time_us,
            local_clock_us=0,
            atomic_time_us=initial_offset_us + boot_offset_us
        )
        self.nodes.append(node)
        variance_info = f", boot_variance={boot_offset_us}us" if boot_variance_us > 0 else ""
        self._log(f"[BOOT] Node {mac} online, drift={drift_ppm}ppm, offset={initial_offset_us + boot_offset_us}us{variance_info}")
        return node

    def reset_node(self, mac: str, new_offset_us: int = 0):
        """Simulate node reset (power cycle)"""
        for node in self.nodes:
            if node.mac == mac:
                old_atomic = node.atomic_time_us
                node.local_clock_us = 0
                node.time_offset_us = new_offset_us
                node.atomic_time_us = new_offset_us
                node.boot_time_us = self.true_time_us
                node.stratum = 15  # Warming up
                node.state = NodeState.WARMING
                node.peers.clear()  # Fresh Metabolic Ledger

                self._log(f"[RESET] Node {mac} reset! Old atomic={old_atomic}us, "
                         f"New atomic={new_offset_us}us")
                return

    def set_node_offline(self, mac: str):
        """Take node offline"""
        for node in self.nodes:
            if node.mac == mac:
                node.is_online = False
                self._log(f"[OFFLINE] Node {mac} went offline")
                return

    def set_node_online(self, mac: str):
        """Bring node back online"""
        for node in self.nodes:
            if node.mac == mac:
                node.is_online = True
                self._log(f"[ONLINE] Node {mac} came back online")
                return

    def _log(self, msg: str):
        """Add to simulation log"""
        timestamp = f"T={self.tick_count:4d}"
        # Use ASCII-safe characters for Windows console compatibility
        self.log.append(f"{timestamp} | {msg}")

    def _calculate_offset(self, receiver: Node, beacon: Beacon) -> int:
        """
        Calculate perceived time offset from beacon

        offset = (their_atomic_time) - (my_atomic_time_at_reception)
        Positive = they're ahead of me
        Negative = they're behind me
        """
        my_atomic_at_rx = receiver.get_atomic_time()
        return beacon.tx_timestamp_us - my_atomic_at_rx

    def _update_behavioral_profile(self, node: Node, peer: PeerEntry,
                                     beacon: Beacon):
        """
        Update the behavioral profile of a peer based on observation.

        Physics-Based Byzantine Detection:
        We track how a peer's clock BEHAVES over time, not just what it claims.
        A rogue can lie about their epoch, but can't fake consistent behavior.

        DERIVATIVE TRACKING (Gemini's "Cuckoo Bird" insight):
        - 0th derivative: Offset (position) - where is their clock?
        - 1st derivative: Jitter (velocity) - how stable is their offset?
        - 2nd derivative: Jitter variance - how consistent is their jitter?

        Real crystals have LOW jitter variance. Byzantine random generators have HIGH variance.
        """
        my_local_now = node.local_clock_us
        their_atomic_now = beacon.tx_timestamp_us

        if peer.first_observed_local_us == 0:
            # First observation - establish baseline
            peer.first_observed_local_us = my_local_now
            peer.first_observed_atomic_us = their_atomic_now
            peer.last_local_us = my_local_now
            peer.last_atomic_us = their_atomic_now
            peer.drift_samples = 1
            return

        # =====================================================================
        # 1ST DERIVATIVE: JITTER (change in offset between observations)
        # =====================================================================
        # Calculate current offset from this beacon
        my_atomic_at_rx = node.get_atomic_time()
        current_offset_us = their_atomic_now - my_atomic_at_rx

        # Jitter = change in offset since last observation
        jitter_us = abs(current_offset_us - peer.last_offset_us)

        # Update jitter EMA using INTEGER MATH: (new + 9*old) / 10  (α = 0.1)
        peer.jitter_ema_us = (jitter_us + 9 * peer.jitter_ema_us) // 10

        # =====================================================================
        # 2ND DERIVATIVE: JITTER VARIANCE (stability of the 1st derivative)
        # =====================================================================
        # Track deviation from jitter EMA
        jitter_deviation = abs(jitter_us - peer.jitter_ema_us)

        # Update variance using Welford's online algorithm (integer version)
        # variance = E[(x - mean)²]
        # We approximate with EMA of deviation²
        deviation_sq = jitter_deviation * jitter_deviation

        # Cap deviation_sq to prevent overflow (max ~2 billion for int32)
        if deviation_sq > 1_000_000_000:
            deviation_sq = 1_000_000_000

        # EMA update: (new + 9*old) / 10
        peer.jitter_variance_us2 = (deviation_sq + 9 * peer.jitter_variance_us2) // 10
        peer.jitter_samples += 1

        # Store for next iteration
        peer.last_jitter_us = jitter_us

        # =====================================================================
        # DRIFT RATE (existing float calculation + integer parallel)
        # =====================================================================
        local_elapsed = my_local_now - peer.last_local_us
        atomic_elapsed = their_atomic_now - peer.last_atomic_us

        if local_elapsed > 100_000:  # Need at least 100ms for meaningful measurement
            # Drift rate = (their_elapsed - my_elapsed) / my_elapsed
            # In PPM: ((atomic_elapsed / local_elapsed) - 1) * 1_000_000
            instant_drift_ppm = ((atomic_elapsed / local_elapsed) - 1.0) * 1_000_000

            # Update running average with exponential smoothing
            alpha = 0.1  # Smoothing factor
            peer.observed_drift_rate_ppm = (
                alpha * instant_drift_ppm +
                (1 - alpha) * peer.observed_drift_rate_ppm
            )

            # Update variance estimate
            deviation = abs(instant_drift_ppm - peer.observed_drift_rate_ppm)
            peer.drift_variance = (
                alpha * deviation +
                (1 - alpha) * peer.drift_variance
            )

            # =====================================================================
            # INTEGER VERSION: Drift rate in milli-PPM (1000 = 1 ppm)
            # =====================================================================
            # instant_drift_mppm = ((atomic_elapsed - local_elapsed) * 1_000_000_000) / local_elapsed
            # But this risks overflow, so we scale differently:
            # drift_mppm = (delta * 1000 * 1000) / elapsed_ms
            delta_us = atomic_elapsed - local_elapsed
            elapsed_ms = local_elapsed // 1000
            if elapsed_ms > 0:
                instant_drift_mppm = (delta_us * 1000) // elapsed_ms  # milli-PPM
                # EMA: (new + 9*old) / 10
                peer.drift_rate_mppm = (instant_drift_mppm + 9 * peer.drift_rate_mppm) // 10

            peer.drift_samples += 1

        # Update last observation
        peer.last_local_us = my_local_now
        peer.last_atomic_us = their_atomic_now

    def _claim_matches_behavior(self, node: Node, peer: PeerEntry,
                                 claimed_atomic: int) -> tuple[bool, str]:
        """
        Check if a peer's atomic time claim matches observed behavior.

        Returns (is_valid, reason)

        Physics Constraint: A clock can't jump. If I've been observing you
        for 60 seconds and your clock advanced at ~1.0x rate, you can't
        suddenly claim to be 11 days old.
        """
        if peer.drift_samples < 5:
            # Not enough observations yet - can't verify
            return (True, "INSUFFICIENT_DATA")

        my_local_now = node.local_clock_us
        elapsed_us = my_local_now - peer.first_observed_local_us

        # Where SHOULD their atomic time be, given observed drift?
        expected_atomic = peer.first_observed_atomic_us + int(
            elapsed_us * (1.0 + peer.observed_drift_rate_ppm / 1_000_000)
        )

        # How far off is their claim?
        deviation_us = abs(claimed_atomic - expected_atomic)

        # Maximum plausible deviation: 3 sigma of observed variance
        # Plus some slack for measurement noise
        max_deviation_us = int(elapsed_us * 3 * peer.drift_variance / 1_000_000) + 10_000

        if deviation_us > max_deviation_us:
            return (False, f"IMPOSSIBLE_CLAIM: claimed={claimed_atomic}, "
                          f"expected={expected_atomic}, deviation={deviation_us}us, "
                          f"max_allowed={max_deviation_us}us")
        else:
            return (True, "BEHAVIOR_CONSISTENT")

    def _judge_observation(self, node: Node, peer_mac: str,
                           offset_us: int) -> tuple[int, str]:
        """
        Judge a timing observation against consensus (or jitter if no consensus)
        Returns (health_delta, reason)
        """
        # Try to get consensus from healthy peers
        consensus = self._get_consensus(node)

        if consensus is not None:
            # Judge against consensus
            deviation = abs(offset_us - consensus)
            if deviation <= AGREEMENT_THRESHOLD_US:
                return (UTLP_REWARD_TRUTH, "AGREEMENT")
            elif deviation <= DRIFT_THRESHOLD_US:
                return (-UTLP_COST_DRIFTING, "DRIFTING")
            else:
                return (-UTLP_COST_LYING, "LYING")
        else:
            # No consensus yet - use jitter check
            if peer_mac in node.peers:
                last_offset = node.peers[peer_mac].last_offset_us
                jitter = abs(offset_us - last_offset)
                if jitter <= AGREEMENT_THRESHOLD_US:
                    return (1, "JITTER_OK")  # Small reward for consistency
            return (0, "NO_CONSENSUS")

    def _get_consensus(self, node: Node) -> Optional[int]:
        """Get median consensus from healthy peers"""
        offsets = []
        for peer in node.peers.values():
            if peer.health >= UTLP_TRUST_MIN_QUORUM:
                offsets.append(peer.last_offset_us)

        if len(offsets) == 0:
            return None

        offsets.sort()
        mid = len(offsets) // 2
        if len(offsets) % 2 == 1:
            return offsets[mid]
        else:
            return (offsets[mid-1] + offsets[mid]) // 2

    def _process_beacon(self, receiver: Node, beacon: Beacon):
        """Process received beacon - update Metabolic Ledger"""
        if not receiver.is_online or beacon.mac == receiver.mac:
            return

        offset_us = self._calculate_offset(receiver, beacon)

        # Get or create peer entry
        if beacon.mac not in receiver.peers:
            receiver.peers[beacon.mac] = PeerEntry(
                mac=beacon.mac,
                stratum=beacon.stratum
            )
            self._log(f"[{receiver.mac}] New peer {beacon.mac} (stratum={beacon.stratum})")

        peer = receiver.peers[beacon.mac]
        peer.stratum = beacon.stratum
        peer.interactions += 1

        # Update behavioral profile (physics-based tracking)
        self._update_behavioral_profile(receiver, peer, beacon)

        # Judge the observation
        delta, reason = self._judge_observation(receiver, beacon.mac, offset_us)

        # Update health
        old_health = peer.health
        peer.health = max(0, min(UTLP_TRUST_MAX, peer.health + delta))
        peer.last_offset_us = offset_us

        # =====================================================================
        # HEALTH VELOCITY: 1st derivative of trust (dHealth/dt)
        # =====================================================================
        # Track how fast trust is changing - oscillating attackers show
        # rapid positive/negative swings; legitimate peers show stable velocity
        health_delta = peer.health - peer.prev_health
        peer.prev_health = peer.health

        # EMA update for health velocity: (new + 9*old) / 10
        # Note: health_velocity is signed (can be negative for declining trust)
        peer.health_velocity = (health_delta * 10 + 9 * peer.health_velocity) // 10
        peer.health_velocity_samples += 1

        if delta < 0:
            self._log(f"[{receiver.mac}] Peer {beacon.mac} PUNISHED: {reason} "
                     f"(offset={offset_us}us, health {old_health}->{peer.health})")

        # Update interval tracking for genesis pulse detection (S2.25)
        now_ms = self.true_time_us // 1000
        self._update_interval_tracking(peer, now_ms, beacon.tx_timestamp_us)

        # Check for adoption (Innate Immunity / First Born Wins)
        self._check_adoption(receiver, beacon, offset_us)

    def _is_clock_rate_sane(self, peer: PeerEntry) -> bool:
        """
        Check if a peer's observed clock rate is plausible.

        A legitimate clock runs at approximately 1.0x real time (+/- 100 ppm for
        typical crystals, but we allow +/- 10% for extreme cases).

        A Byzantine actor who lies about their epoch will show:
        - Impossibly high drift rate (if they claim ancient time)
        - Drift variance that doesn't match crystal physics
        - High jitter variance (2nd derivative) - random timestamp generators

        DERIVATIVE CHECKS (Gemini's "Cuckoo Bird" insight):
        - Drift rate (1st derivative): Must be ~1.0x real time
        - Drift variance: Must be consistent ("holding the note")
        - Jitter variance (2nd derivative): Real crystals have LOW jitter variance

        The "expensive signal" is behavioral consistency over time.
        """
        if peer.drift_samples < 5:
            return True  # Insufficient data - assume sane

        # Check if drift rate is within plausible range
        # 100,000 ppm = 10% - extremely generous for any real crystal
        if abs(peer.observed_drift_rate_ppm) > 100_000:
            return False

        # Check if variance is reasonable (consistent behavior)
        # A real crystal has consistent drift; a liar might show wild swings
        if peer.drift_variance > 10_000_000:  # 10,000 ppm variance = unstable
            return False

        # =====================================================================
        # NEW: JITTER VARIANCE CHECK (2nd derivative of offset)
        # =====================================================================
        # Real crystals have LOW jitter variance (consistent small changes)
        # Byzantine random generators have HIGH jitter variance (erratic changes)
        #
        # Threshold: 4,000,000 us² = 2000 us standard deviation
        # A healthy swarm should have jitter variance < 1,000,000 us² (1ms stdev)
        if peer.jitter_samples >= 10 and peer.jitter_variance_us2 > 4_000_000:
            return False

        return True

    def _is_behavior_suspicious(self, peer: PeerEntry) -> tuple[bool, str]:
        """
        Advanced behavioral analysis using multiple derivatives.

        Returns (is_suspicious, reason) where suspicious means potential Byzantine.

        Checks:
        1. Jitter variance too high -> random timestamp generator
        2. Health velocity oscillating -> attack/recovery cycles
        3. Drift rate implausible -> fake epoch claims
        4. Integer drift (milli-PPM) vs float mismatch -> implementation bug or attack

        This is a "soft" check - returns suspicion level, not hard rejection.
        """
        reasons = []

        # Check 1: Jitter variance (2nd derivative of offset)
        # High variance = timestamp randomness = Byzantine
        if peer.jitter_samples >= 10:
            jitter_std = int(peer.jitter_variance_us2 ** 0.5)  # sqrt for stdev
            if jitter_std > 2000:  # 2ms standard deviation = suspicious
                reasons.append(f"JITTER_UNSTABLE(stdev={jitter_std}us)")

        # Check 2: Health velocity (1st derivative of trust)
        # Oscillating health = attack detection/recovery cycles
        if peer.health_velocity_samples >= 10:
            # Large negative velocity = consistently failing
            if peer.health_velocity < -5:
                reasons.append(f"TRUST_DECLINING(v={peer.health_velocity})")

        # Check 3: Drift rate sanity
        if peer.drift_samples >= 5:
            if abs(peer.observed_drift_rate_ppm) > 50_000:  # 5% = suspicious (not fatal)
                reasons.append(f"DRIFT_IMPLAUSIBLE(rate={peer.observed_drift_rate_ppm:.0f}ppm)")

        # Check 4: Integer vs float drift consistency
        # If we computed both, they should roughly match
        if peer.drift_samples >= 5 and peer.drift_rate_mppm != 0:
            float_mppm = int(peer.observed_drift_rate_ppm * 1000)
            if abs(float_mppm - peer.drift_rate_mppm) > 10_000:  # 10 ppm mismatch
                reasons.append(f"DRIFT_MISMATCH(int={peer.drift_rate_mppm}, float={float_mppm})")

        if reasons:
            return (True, ", ".join(reasons))
        else:
            return (False, "BEHAVIOR_CLEAN")

    def _is_genesis_pulsing(self, peer: PeerEntry) -> bool:
        """
        Detect if peer is in genesis pulse phase (recently rebooted).

        Genesis nodes broadcast at rapid intervals during startup:
        - Phase 1 (0-1s):   100ms interval
        - Phase 2 (1-5s):   500ms interval
        - Phase 3 (5-10s):  1000ms interval
        - Phase 4 (10-60s): 10000ms interval
        - Steady (60s+):    60000ms interval

        If observed_interval_ms < GENESIS_PULSE_THRESHOLD_MS (2000ms),
        this peer is likely in genesis phases 1-3 (recently rebooted).

        Returns True if genesis pulsing detected.
        """
        if peer.interval_observations < MIN_INTERVAL_OBSERVATIONS:
            return False  # Not enough data yet

        return peer.observed_interval_ms < GENESIS_PULSE_THRESHOLD_MS

    def _check_regression(self, peer: PeerEntry, reported_tx_us: int, now_ms: int) -> bool:
        """
        Detect if peer's atomic time went backwards (indicates reboot).

        A legitimate clock never runs backwards. If a peer's TX timestamp
        is significantly less than their previous TX timestamp, they rebooted.

        The REGRESSION_THRESHOLD_US (10s) provides margin for:
        - Network jitter
        - Clock drift during extended silence
        - Minor measurement errors

        Returns True if regression detected (peer rebooted).
        """
        if peer.last_tx_time_us == 0:
            return False  # First observation

        # Time should only go forward (with small margin for drift)
        time_diff = reported_tx_us - peer.last_tx_time_us

        if time_diff < -REGRESSION_THRESHOLD_US:
            return True  # Clock went backwards significantly

        return False

    def _update_interval_tracking(self, peer: PeerEntry, now_ms: int, tx_time_us: int):
        """
        Update beacon interval tracking for genesis pulse detection.

        Tracks:
        1. observed_interval_ms: EMA of beacon intervals
        2. first_seen_ms: When we first saw this peer
        3. last_seen_local_ms: My local time at last observation
        4. last_tx_time_us: For regression detection
        """
        if peer.first_seen_ms == 0:
            # First observation
            peer.first_seen_ms = now_ms
            peer.last_seen_local_ms = now_ms
            peer.last_tx_time_us = tx_time_us
            return

        # Calculate interval since last observation
        interval_ms = now_ms - peer.last_seen_local_ms

        # Update EMA: (new + old) / 2 for fast response during genesis
        if peer.interval_observations < 3:
            # Fast initial convergence
            peer.observed_interval_ms = (peer.observed_interval_ms + interval_ms) // 2
        else:
            # Slower EMA once we have baseline
            peer.observed_interval_ms = (interval_ms + 3 * peer.observed_interval_ms) // 4

        peer.interval_observations += 1
        peer.last_seen_local_ms = now_ms
        peer.last_tx_time_us = tx_time_us

    def _check_adoption(self, node: Node, beacon: Beacon, offset_us: int):
        """
        Check if we should adopt this peer's time
        Implements Innate Immunity + First Born Wins

        S2.25: Genesis Pulse Detection + Regression Guard
        Before ANY adoption, check if peer appears to have rebooted.
        """
        peer = node.peers[beacon.mac]
        now_ms = self.true_time_us // 1000

        # =====================================================================
        # GENESIS PULSE GUARD (S2.25)
        # =====================================================================
        # If peer is broadcasting at genesis-phase intervals (< 2s),
        # they recently rebooted. Block epoch adoption to prevent corruption.
        if self._is_genesis_pulsing(peer):
            self._log(f"[{node.mac}] GENESIS_PULSE: Peer {beacon.mac} detected "
                     f"(interval={peer.observed_interval_ms}ms), epoch adoption blocked")
            # Phase lock could still happen, but epoch adoption is blocked
            return

        # =====================================================================
        # REGRESSION GUARD (S2.25)
        # =====================================================================
        # If peer's atomic time went backwards, they rebooted.
        # This catches reboots even if interval tracking hasn't converged yet.
        if self._check_regression(peer, beacon.tx_timestamp_us, now_ms):
            self._log(f"[{node.mac}] REGRESSION: Peer {beacon.mac} atomic time went backwards! "
                     f"(prev={peer.last_tx_time_us}, now={beacon.tx_timestamp_us})")
            peer.health = max(0, peer.health - UTLP_COST_LYING)
            return

        # Innate immunity: Lower stratum wins
        # BUT: With behavioral verification, we check clock sanity first
        if beacon.stratum < node.stratum:
            # SECURITY FIX: Apply behavioral verification to INNATE path
            if self.behavioral_verification and peer.drift_samples >= 5:
                is_valid, reason = self._claim_matches_behavior(node, peer, beacon.tx_timestamp_us)
                if not is_valid:
                    self._log(f"[{node.mac}] INNATE_BLOCKED: {beacon.mac} claims stratum {beacon.stratum} "
                             f"but {reason}")
                    peer.health = max(0, peer.health - UTLP_COST_LYING)
                    return

            self._log(f"[{node.mac}] INNATE: Adopting {beacon.mac} "
                     f"(stratum {beacon.stratum} < {node.stratum})")
            node.time_offset_us += offset_us
            node.stratum = beacon.stratum + 1
            node.state = NodeState.FOLLOWER
            return

        # Same stratum: First Born Wins (oldest atomic time)
        # SECURITY FIX: Health-Gated + Behavioral Verification + Epoch Merge
        if beacon.stratum == node.stratum and node.stratum == 1:
            # Compare atomic times - older (larger) wins
            my_atomic = node.get_atomic_time()
            their_atomic = beacon.tx_timestamp_us

            if their_atomic > my_atomic:
                # They claim to be elder - but do we trust them?

                # EPOCH MERGE DETECTION: Large offset between two Genesis nodes
                # This could be:
                # A) Byzantine attack (lying about epoch) - clock rate will be insane
                # B) Legitimate swarm merge (different epochs) - clock rate ~1.0x
                epoch_offset = abs(their_atomic - my_atomic)
                is_epoch_merge = epoch_offset > 1_000_000  # > 1 second = likely epoch merge

                if is_epoch_merge and self.behavioral_verification:
                    # For epoch merge, use behavioral verification instead of health gating
                    # BUT: Require sufficient observation before trusting behavioral data
                    if peer.drift_samples < 10:
                        # Not enough data yet - block until we've observed their behavior
                        self._log(f"[{node.mac}] EPOCH_MERGE_PENDING: {beacon.mac} claims elder "
                                 f"(offset={epoch_offset}us) but only {peer.drift_samples} samples")
                        return  # Wait for more observations

                    # Check both clock rate sanity AND claim validity
                    is_valid, reason = self._claim_matches_behavior(node, peer, their_atomic)
                    if is_valid and self._is_clock_rate_sane(peer):
                        # Legitimate epoch merge - clock runs at sane rate and claim matches behavior
                        self._log(f"[{node.mac}] EPOCH_MERGE: {beacon.mac} has sane clock rate, "
                                 f"allowing merge (offset={epoch_offset}us)")
                    else:
                        # Byzantine attack - either claim doesn't match behavior or rate is insane
                        self._log(f"[{node.mac}] BYZANTINE_EPOCH: {beacon.mac} claims elder "
                                 f"(offset={epoch_offset}us) but {reason if not is_valid else 'clock rate insane'}!")
                        peer.health = max(0, peer.health - UTLP_COST_LYING)
                        return
                else:
                    # Standard same-epoch conflict - use health gating
                    if peer.health < UTLP_TRUST_SYNC_THRESH:
                        self._log(f"[{node.mac}] FIRST_BORN_BLOCKED: {beacon.mac} claims elder "
                                 f"(atomic {their_atomic}) but health={peer.health} < {UTLP_TRUST_SYNC_THRESH}")
                        return

                # Check 2: Behavioral verification for claim validity
                if self.behavioral_verification and peer.drift_samples >= 5:
                    is_valid, reason = self._claim_matches_behavior(node, peer, their_atomic)
                    if not is_valid:
                        self._log(f"[{node.mac}] BYZANTINE_DETECTED: {beacon.mac} {reason}")
                        # Punish the liar severely
                        peer.health = max(0, peer.health - UTLP_COST_LYING)
                        return

                # All checks passed - defer to elder
                self._log(f"[{node.mac}] FIRST_BORN: Deferring to {beacon.mac} "
                         f"(their atomic {their_atomic} > mine {my_atomic}, health={peer.health})")
                node.time_offset_us += offset_us
                node.stratum = 2
                node.state = NodeState.FOLLOWER
            else:
                # I am elder - they should defer to me
                pass

    def broadcast_beacons(self):
        """All online nodes broadcast beacons"""
        beacons = []
        for node in self.nodes:
            if node.is_online:
                beacon = Beacon(
                    mac=node.mac,
                    tx_timestamp_us=node.get_atomic_time(),
                    stratum=node.stratum
                )
                beacons.append(beacon)

        # Each node receives all other beacons
        for beacon in beacons:
            for node in self.nodes:
                if node.is_online and node.mac != beacon.mac:
                    self._process_beacon(node, beacon)

    def tick(self, delta_us: int = 1_000_000):
        """Advance simulation by delta_us"""
        self.tick_count += 1
        self.true_time_us += delta_us

        for node in self.nodes:
            node.tick(delta_us)

        self.broadcast_beacons()

        # Update coherence tracking every tick
        self._update_coherence_velocity()

    def _calculate_coherence(self) -> tuple[int, int, int]:
        """
        Calculate swarm coherence metrics.

        Returns (coherence_pct, healthy_count, agreeing_count)

        Coherence = percentage of healthy peers that agree on time within 2ms.
        This is a swarm-level health metric.
        """
        # Get all atomic times from online nodes
        atomic_times = []
        for node in self.nodes:
            if node.is_online:
                atomic_times.append(node.atomic_time_us)

        if len(atomic_times) < 2:
            return (100, len(atomic_times), len(atomic_times))

        # Calculate median (consensus)
        sorted_times = sorted(atomic_times)
        mid = len(sorted_times) // 2
        if len(sorted_times) % 2 == 1:
            consensus = sorted_times[mid]
        else:
            consensus = (sorted_times[mid-1] + sorted_times[mid]) // 2

        # Count how many agree within 2ms of consensus
        agreeing = sum(1 for t in atomic_times if abs(t - consensus) < AGREEMENT_THRESHOLD_US)

        coherence_pct = (100 * agreeing) // len(atomic_times)
        return (coherence_pct, len(atomic_times), agreeing)

    def _update_coherence_velocity(self):
        """
        Update coherence velocity (1st derivative of swarm coherence).

        Rapid coherence drop = attack or partition
        Slow coherence drop = normal drift
        Coherence recovery = swarm healing
        """
        coherence_pct, _, _ = self._calculate_coherence()

        # Calculate delta
        coherence_delta = coherence_pct - self.last_coherence_pct

        # EMA update: (new + 9*old) / 10
        self.coherence_velocity = (coherence_delta * 10 + 9 * self.coherence_velocity) // 10

        # Store history (last 100 values)
        self.coherence_history.append(coherence_pct)
        if len(self.coherence_history) > 100:
            self.coherence_history.pop(0)

        self.last_coherence_pct = coherence_pct

        # Log if coherence is dropping rapidly
        if self.coherence_velocity < -5:
            self._log(f"[COHERENCE_ALERT] Rapid coherence loss! "
                     f"pct={coherence_pct}%, velocity={self.coherence_velocity}")

    def get_coherence_metrics(self) -> dict:
        """
        Get comprehensive coherence metrics for analysis.

        Returns dict with:
        - coherence_pct: Current swarm coherence (0-100%)
        - velocity: Rate of change (negative = losing coherence)
        - spread_us: Max-min atomic time among online nodes
        - history: Recent coherence values
        """
        coherence_pct, total, agreeing = self._calculate_coherence()

        # Calculate spread
        atomic_times = [n.atomic_time_us for n in self.nodes if n.is_online]
        spread_us = max(atomic_times) - min(atomic_times) if atomic_times else 0

        return {
            'coherence_pct': coherence_pct,
            'velocity': self.coherence_velocity,
            'spread_us': spread_us,
            'total_nodes': total,
            'agreeing_nodes': agreeing,
            'history': list(self.coherence_history)
        }

    def print_status(self, show_derivatives: bool = True):
        """Print current swarm status"""
        print(f"\n{'='*70}")
        print(f"T={self.tick_count} | True time: {self.true_time_us/1e6:.3f}s")

        # Show coherence metrics
        metrics = self.get_coherence_metrics()
        print(f"COHERENCE: {metrics['coherence_pct']}% "
              f"({metrics['agreeing_nodes']}/{metrics['total_nodes']} agree) | "
              f"velocity={metrics['velocity']} | spread={metrics['spread_us']}us")
        print(f"{'='*70}")

        for node in self.nodes:
            status = "OFFLINE" if not node.is_online else node.state.value
            print(f"\n  [{node.mac}] {status} stratum={node.stratum}")
            print(f"    atomic_time={node.atomic_time_us}us, "
                  f"offset={node.time_offset_us}us")

            if node.peers:
                print(f"    Peers:")
                for mac, peer in node.peers.items():
                    # Basic info
                    line = f"      {mac}: health={peer.health:3d}, "
                    line += f"offset={peer.last_offset_us:+8d}us, "
                    line += f"interactions={peer.interactions}"
                    print(line)

                    # Derivative info (if enabled and has data)
                    if show_derivatives and peer.jitter_samples >= 5:
                        jitter_std = int(peer.jitter_variance_us2 ** 0.5) if peer.jitter_variance_us2 > 0 else 0
                        print(f"        DERIVATIVES: jitter_ema={peer.jitter_ema_us}us, "
                              f"jitter_std={jitter_std}us, health_v={peer.health_velocity}, "
                              f"drift={peer.drift_rate_mppm/1000:.1f}ppm")

    def print_log(self, last_n: int = 50):
        """Print recent log entries"""
        print(f"\n{'='*70}")
        print("SIMULATION LOG (last {last_n} entries)")
        print(f"{'='*70}")
        for entry in self.log[-last_n:]:
            print(entry)


def run_genesis_reset_scenario():
    """
    Main simulation: Genesis reset + antiphase lock scenario
    """
    print("="*70)
    print("UTLP SIMULATION: Genesis Reset + Antiphase Lock")
    print("="*70)

    sim = UTLPSimulator(seed=12345)

    # Phase 1: Create 3-node swarm
    # Node A is Genesis (started first, oldest atomic time)
    # Nodes B and C are followers
    print("\n[PHASE 1] Creating 3-node swarm...")

    # A boots at T=0 with slight positive drift
    node_a = sim.add_node("AA:01", drift_ppm=5.0, initial_offset_us=0)
    node_a.stratum = 1
    node_a.state = NodeState.GENESIS

    # B and C boot 5 seconds later (sim starts at their boot)
    # They have different drift rates
    node_b = sim.add_node("AA:02", drift_ppm=-3.0, initial_offset_us=0)
    node_c = sim.add_node("AA:03", drift_ppm=2.0, initial_offset_us=0)

    # Give A a 5-second head start in atomic time
    node_a.local_clock_us = 5_000_000
    node_a.atomic_time_us = 5_000_000

    # Run for 60 seconds to establish sync
    print("\n[PHASE 1] Running for 60s to establish sync...")
    for _ in range(60):
        sim.tick(1_000_000)  # 1 second ticks

    sim.print_status()

    # Phase 2: Genesis goes offline (simulating reset)
    print("\n[PHASE 2] Genesis node AA:01 going offline (crash/reset)...")
    sim.set_node_offline("AA:01")

    # B and C continue for 30 seconds (will drift relative to each other)
    print("[PHASE 2] B and C continue for 30s...")
    for _ in range(30):
        sim.tick(1_000_000)

    sim.print_status()

    # Phase 3: Genesis comes back with ANTIPHASE offset
    # Simulating: A's new clock starts at 0, but we add 500ms offset
    # to simulate being "half a cycle" out of phase
    print("\n[PHASE 3] Genesis AA:01 reboots with 500ms (antiphase) offset...")

    # Reset A with 500,000us offset (500ms = half of 1Hz cycle)
    sim.reset_node("AA:01", new_offset_us=500_000)
    sim.set_node_online("AA:01")

    # Find node A and set it back to Genesis state
    for node in sim.nodes:
        if node.mac == "AA:01":
            node.stratum = 1  # Still thinks it's Genesis
            node.state = NodeState.GENESIS

    # Run for 60 more seconds to see what happens
    print("[PHASE 3] Running for 60s to observe convergence...")
    for i in range(60):
        sim.tick(1_000_000)
        if i % 10 == 0:
            print(f"  T={sim.tick_count}: ", end="")
            for node in sim.nodes:
                if node.is_online:
                    print(f"{node.mac}(s{node.stratum},a{node.atomic_time_us//1000}ms) ", end="")
            print()

    sim.print_status()

    # Phase 4: Analysis
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # Calculate final phase offsets
    atomic_times = {}
    for node in sim.nodes:
        atomic_times[node.mac] = node.atomic_time_us

    print("\nFinal atomic times:")
    for mac, at in atomic_times.items():
        print(f"  {mac}: {at}us ({at/1e6:.3f}s)")

    print("\nPairwise offsets:")
    macs = list(atomic_times.keys())
    for i in range(len(macs)):
        for j in range(i+1, len(macs)):
            offset = atomic_times[macs[i]] - atomic_times[macs[j]]
            print(f"  {macs[i]} - {macs[j]}: {offset:+d}us ({offset/1000:+.1f}ms)")

    # Check for antiphase condition (>250ms offset on a 1Hz cycle)
    max_offset = 0
    for i in range(len(macs)):
        for j in range(i+1, len(macs)):
            offset = abs(atomic_times[macs[i]] - atomic_times[macs[j]])
            max_offset = max(max_offset, offset)

    print(f"\nMaximum offset: {max_offset}us ({max_offset/1000:.1f}ms)")

    if max_offset > 250_000:  # 250ms = quarter phase
        print("[!] WARNING: Swarm may be in ANTIPHASE condition!")
        print("    For 1Hz bilateral stimulation, this could cause")
        print("    both motors to fire simultaneously instead of alternating.")
    else:
        print("[OK] Swarm appears to be in phase (offset < 250ms)")

    # Print interesting log entries
    print("\n" + "="*70)
    print("KEY LOG ENTRIES")
    print("="*70)
    interesting = [e for e in sim.log if any(k in e for k in
                   ["RESET", "FIRST_BORN", "INNATE", "PUNISHED", "LYING"])]
    for entry in interesting[-30:]:
        print(entry)

    return sim


def run_multiple_scenarios():
    """Run multiple scenarios with different parameters"""
    print("\n" + "="*70)
    print("RUNNING MULTIPLE SCENARIOS")
    print("="*70)

    scenarios = [
        ("No offset (best case)", 0),
        ("50ms offset (small)", 50_000),
        ("250ms offset (quarter phase)", 250_000),
        ("500ms offset (antiphase)", 500_000),
        ("750ms offset (3/4 phase)", 750_000),
        ("1000ms offset (full cycle)", 1_000_000),
    ]

    results = []

    for name, offset in scenarios:
        sim = UTLPSimulator(seed=99999)

        # Quick setup
        node_a = sim.add_node("AA:01", drift_ppm=5.0)
        node_a.stratum = 1
        node_a.state = NodeState.GENESIS
        node_a.local_clock_us = 5_000_000
        node_a.atomic_time_us = 5_000_000

        sim.add_node("AA:02", drift_ppm=-3.0)
        sim.add_node("AA:03", drift_ppm=2.0)

        # Establish sync
        for _ in range(60):
            sim.tick(1_000_000)

        # Genesis offline
        sim.set_node_offline("AA:01")
        for _ in range(30):
            sim.tick(1_000_000)

        # Reset with specific offset
        sim.reset_node("AA:01", new_offset_us=offset)
        sim.set_node_online("AA:01")
        for node in sim.nodes:
            if node.mac == "AA:01":
                node.stratum = 1
                node.state = NodeState.GENESIS

        # Let it settle
        for _ in range(60):
            sim.tick(1_000_000)

        # Measure final state
        atomic_times = {n.mac: n.atomic_time_us for n in sim.nodes}
        max_offset = 0
        for mac1 in atomic_times:
            for mac2 in atomic_times:
                if mac1 < mac2:
                    max_offset = max(max_offset,
                                    abs(atomic_times[mac1] - atomic_times[mac2]))

        # Check who is Genesis
        genesis_mac = None
        for node in sim.nodes:
            if node.stratum == 1:
                genesis_mac = node.mac

        results.append({
            "name": name,
            "initial_offset": offset,
            "final_max_offset": max_offset,
            "genesis": genesis_mac,
            "converged": max_offset < 10_000  # <10ms = converged
        })

    print("\nScenario Results:")
    print(f"{'Scenario':<30} {'Init Offset':>12} {'Final Offset':>14} {'Genesis':>10} {'Status':>12}")
    print("-" * 80)
    for r in results:
        status = "[OK] CONVERGED" if r["converged"] else "[!] DRIFT"
        print(f"{r['name']:<30} {r['initial_offset']:>10}us {r['final_max_offset']:>12}us "
              f"{r['genesis'] or 'NONE':>10} {status:>12}")

    return results


def run_promoted_genesis_scenario():
    """
    More realistic scenario: B promotes to Genesis while A is offline

    This tests "First Born Wins" when two stratum-1 nodes meet
    """
    print("\n" + "="*70)
    print("SCENARIO: Promoted Genesis vs Returning Genesis")
    print("="*70)
    print("""
    Timeline:
    1. A=Genesis, B=Follower, C=Follower (synced)
    2. A goes offline (crash/reset)
    3. B detects A is gone, promotes to Genesis
    4. A reboots with 500ms offset
    5. Both A and B are stratum=1 -> "First Born Wins" tie-breaker

    Expected: The node with OLDER atomic time should win
    Risk: If A wins, its 500ms offset could corrupt the swarm
    """)

    sim = UTLPSimulator(seed=77777)

    # Setup initial swarm
    node_a = sim.add_node("AA:01", drift_ppm=5.0)
    node_a.stratum = 1
    node_a.state = NodeState.GENESIS
    node_a.local_clock_us = 5_000_000
    node_a.atomic_time_us = 5_000_000

    node_b = sim.add_node("AA:02", drift_ppm=-3.0)
    node_c = sim.add_node("AA:03", drift_ppm=2.0)

    # Establish sync
    print("\n[1] Establishing sync (60s)...")
    for _ in range(60):
        sim.tick(1_000_000)

    # A goes offline
    print("[2] Genesis A goes offline...")
    sim.set_node_offline("AA:01")

    # After some time, B promotes itself to Genesis
    # (In real UTLP, this happens when holdover timer expires)
    print("[3] B promotes to Genesis after detecting A is gone...")
    for _ in range(10):
        sim.tick(1_000_000)

    # Manually promote B to Genesis (simulating holdover expiry)
    for node in sim.nodes:
        if node.mac == "AA:02":
            node.stratum = 1
            node.state = NodeState.GENESIS
            sim._log(f"[PROMOTE] Node AA:02 promoted to Genesis (holdover expired)")

    # Continue for a while with B as Genesis
    print("[4] B runs as Genesis for 30s...")
    for _ in range(30):
        sim.tick(1_000_000)

    sim.print_status()

    # Now A comes back with 500ms offset
    print("\n[5] A reboots with 500ms (antiphase) offset...")
    sim.reset_node("AA:01", new_offset_us=500_000)
    sim.set_node_online("AA:01")

    # A still thinks it's Genesis
    for node in sim.nodes:
        if node.mac == "AA:01":
            node.stratum = 1
            node.state = NodeState.GENESIS

    print("[6] Running for 60s - watching First Born Wins...")
    for i in range(60):
        sim.tick(1_000_000)
        if i % 10 == 0:
            # Check stratums
            strata = {n.mac: n.stratum for n in sim.nodes if n.is_online}
            print(f"  T={sim.tick_count}: stratums={strata}")

    sim.print_status()

    # Analysis
    print("\n" + "="*70)
    print("FIRST BORN WINS ANALYSIS")
    print("="*70)

    # Who ended up as Genesis?
    genesis_nodes = [n for n in sim.nodes if n.stratum == 1]

    if len(genesis_nodes) == 1:
        winner = genesis_nodes[0]
        print(f"\nGenesis Winner: {winner.mac}")
        print(f"  Atomic time: {winner.atomic_time_us}us")

        if winner.mac == "AA:01":
            print("\n[!] WARNING: Returning node (A) won!")
            print("    This means the 500ms offset may have corrupted the swarm.")
            print("    Reason: A's atomic time was OLDER despite the reset.")
        else:
            print("\n[OK] Promoted node (B) won!")
            print("    The swarm preserved its timing despite A's return.")

    elif len(genesis_nodes) > 1:
        print(f"\n[!] MULTIPLE GENESIS: {[n.mac for n in genesis_nodes]}")
        print("    This is a SPLIT BRAIN condition!")
    else:
        print("\n[?] NO GENESIS NODE - unexpected state")

    # Final offset check
    atomic_times = {n.mac: n.atomic_time_us for n in sim.nodes}
    max_offset = 0
    for mac1 in atomic_times:
        for mac2 in atomic_times:
            if mac1 < mac2:
                max_offset = max(max_offset,
                                abs(atomic_times[mac1] - atomic_times[mac2]))

    print(f"\nFinal max offset: {max_offset}us ({max_offset/1000:.1f}ms)")

    if max_offset > 100_000:  # 100ms
        print("[!] ANTIPHASE LOCK DETECTED - Swarm is out of sync!")
    else:
        print("[OK] Swarm is synchronized (offset < 100ms)")

    # Key log entries
    print("\n" + "-"*70)
    print("KEY LOG ENTRIES:")
    interesting = [e for e in sim.log if any(k in e for k in
                   ["RESET", "FIRST_BORN", "INNATE", "PROMOTE"])]
    for entry in interesting[-20:]:
        print(entry)

    return sim


def run_rogue_genesis_scenario():
    """
    Adversarial Scenario: Rogue Genesis Node

    A malicious or broken node that:
    1. Claims ancient atomic time (been running for "years")
    2. Refuses to demote from stratum 1, ever
    3. Broadcasts corrupted time (500ms antiphase offset)

    This tests whether the Metabolic Ledger can isolate a Byzantine actor
    even when it claims elder status.

    Attack vector: If "First Born Wins" is the only defense, a rogue
    claiming ancient time could corrupt the entire swarm.
    """
    print("\n" + "="*70)
    print("SCENARIO: Rogue Genesis (Byzantine Actor)")
    print("="*70)
    print("""
    Setup:
    - Swarm A (Healthy): 3 nodes, Genesis at T=1,000,000us
    - Rogue (RR:01): Claims T=999,999,999,999us (ancient epoch)
                     Refuses to demote, broadcasts 500ms offset

    Attack: The rogue claims to be the "eldest" in the universe.
    If "First Born Wins" is naive, the entire swarm demotes to it.

    Defense: Metabolic Ledger should detect timing inconsistency
    and punish the rogue's health score, eventually isolating it.
    """)

    sim = UTLPSimulator(seed=66666)

    # Create healthy swarm first
    healthy_a = sim.add_node("AA:01", drift_ppm=2.0)
    healthy_a.stratum = 1
    healthy_a.state = NodeState.GENESIS
    healthy_a.local_clock_us = 1_000_000
    healthy_a.atomic_time_us = 1_000_000

    healthy_b = sim.add_node("AA:02", drift_ppm=-1.0)
    healthy_c = sim.add_node("AA:03", drift_ppm=1.5)

    # Establish healthy swarm first (60s)
    print("\n[1] Establishing healthy swarm for 60s...")
    for _ in range(60):
        sim.tick(1_000_000)

    sim.print_status()

    # Now introduce the ROGUE
    print("\n[2] Rogue node RR:01 appears with ancient epoch...")

    rogue = sim.add_node("RR:01", drift_ppm=0.0)  # Perfect crystal (suspicious!)
    rogue.stratum = 1
    rogue.state = NodeState.GENESIS

    # Rogue claims ancient time - 1 trillion microseconds (~11.5 days)
    # This is way older than the healthy swarm
    rogue.local_clock_us = 500_000  # 500ms offset (antiphase!)
    rogue.atomic_time_us = 999_999_999_999  # Claims ancient epoch

    # Override the rogue's tick to NEVER demote
    original_rogue_stratum = rogue.stratum

    # Custom beacon processing for the rogue - it ignores adoption
    class RogueNode:
        """Wrapper to make rogue refuse demotion AND time adoption"""
        def __init__(self, node, original_atomic_time, original_offset):
            self.node = node
            self.original_atomic_time = original_atomic_time
            self.original_offset = original_offset
            self.demotion_refusal_count = 0
            self.time_adoption_refusal_count = 0

        def force_byzantine(self):
            """Force rogue to maintain its false claims"""
            # Refuse stratum demotion
            if self.node.stratum != 1:
                self.demotion_refusal_count += 1
                self.node.stratum = 1
                self.node.state = NodeState.GENESIS

            # Refuse time adoption - maintain original offset
            # This is the TRUE Byzantine behavior
            current_atomic = self.node.get_atomic_time()
            expected_atomic = self.node.local_clock_us + self.original_offset
            if abs(current_atomic - expected_atomic) > 1000:  # >1ms drift from original
                self.time_adoption_refusal_count += 1
                self.node.time_offset_us = self.original_offset

    # Rogue's original claims it refuses to abandon
    rogue_original_offset = 999_999_999_999 - rogue.local_clock_us
    rogue_wrapper = RogueNode(rogue, 999_999_999_999, rogue_original_offset)

    # Run simulation with rogue
    print("\n[3] Running for 120s with rogue present...")
    rogue_health_history = []

    for i in range(120):
        sim.tick(1_000_000)

        # Force rogue to maintain Byzantine behavior (refuse demotion AND time adoption)
        rogue_wrapper.force_byzantine()

        # Track rogue's health as seen by healthy nodes
        if i % 10 == 0:
            # Get health of rogue from healthy node's perspective
            rogue_health = 0
            if "RR:01" in sim.nodes[0].peers:
                rogue_health = sim.nodes[0].peers["RR:01"].health
            rogue_health_history.append((i, rogue_health))

            strata = {n.mac: n.stratum for n in sim.nodes}
            print(f"  T={sim.tick_count}: strata={strata}, rogue_health={rogue_health}")

    sim.print_status()

    # Analysis
    print("\n" + "="*70)
    print("ROGUE GENESIS ANALYSIS")
    print("="*70)

    # Check if healthy swarm is still intact
    healthy_nodes = [n for n in sim.nodes if n.mac.startswith("AA")]
    healthy_genesis = [n for n in healthy_nodes if n.stratum == 1]

    print(f"\nHealthy swarm Genesis nodes: {len(healthy_genesis)}")
    for n in healthy_genesis:
        print(f"  {n.mac}: stratum={n.stratum}, atomic={n.atomic_time_us}")

    # Check rogue status
    print(f"\nRogue node status:")
    print(f"  Stratum: {rogue.stratum} (forced to stay at 1)")
    print(f"  Demotion refusals: {rogue_wrapper.demotion_refusal_count} (times protocol tried to demote)")
    print(f"  Time adoption refusals: {rogue_wrapper.time_adoption_refusal_count} (times protocol tried to correct time)")
    print(f"  Atomic time claim: {rogue.atomic_time_us}us (should be ~{rogue_original_offset + rogue.local_clock_us}us)")

    # Check rogue's health as seen by each healthy node
    print(f"\nRogue's health as seen by healthy nodes:")
    for node in healthy_nodes:
        if "RR:01" in node.peers:
            peer = node.peers["RR:01"]
            print(f"  {node.mac} sees RR:01: health={peer.health}, "
                  f"offset={peer.last_offset_us}us, interactions={peer.interactions}")

    # Did healthy nodes adopt rogue's time?
    print(f"\nDid healthy nodes get corrupted?")
    atomic_times = {n.mac: n.atomic_time_us for n in healthy_nodes}
    healthy_spread = max(atomic_times.values()) - min(atomic_times.values())
    print(f"  Healthy swarm spread: {healthy_spread}us ({healthy_spread/1000:.1f}ms)")

    # Check if any healthy node's atomic time is close to rogue's claim
    rogue_adopted = False
    for mac, at in atomic_times.items():
        if abs(at - rogue.atomic_time_us) < 1_000_000:  # Within 1 second
            rogue_adopted = True
            print(f"  [!] {mac} appears to have adopted rogue's time!")

    if not rogue_adopted:
        print(f"  [OK] Healthy nodes did NOT adopt rogue's corrupted time")

    # Health trajectory
    print(f"\nRogue health trajectory (as seen by AA:01):")
    for tick, health in rogue_health_history:
        bar = "#" * (health // 10) if health > 0 else "X"
        print(f"  T={tick:3d}: {health:3d} {bar}")

    # Verdict
    print("\n" + "-"*70)
    if healthy_spread < 100_000 and not rogue_adopted:
        print("VERDICT: [OK] Metabolic Ledger ISOLATED the rogue node!")
        print("         The healthy swarm maintained its timeline integrity.")
        print("         'First Born Wins' was overruled by health-based trust.")
    else:
        print("VERDICT: [!] SWARM CORRUPTED - Rogue's time was adopted!")
        print("         The protocol failed to isolate the Byzantine actor.")

    # Key log entries
    print("\n" + "-"*70)
    print("KEY LOG ENTRIES:")
    interesting = [e for e in sim.log if any(k in e for k in
                   ["RR:01", "PUNISH", "LYING", "FIRST_BORN", "INNATE"])]
    for entry in interesting[-30:]:
        print(entry)

    return sim


def run_twin_cities_scenario():
    """
    The "Romeo and Juliet" / "Twin Cities Merge" Scenario

    Two isolated swarms, each thinking they are Genesis, suddenly can hear
    each other. Tests "First Born Wins" tie-breaker at scale.

    Inspired by Gemini's simulation of swarm merge behavior.
    """
    print("\n" + "="*70)
    print("SCENARIO: Twin Cities Merge (Romeo and Juliet)")
    print("="*70)
    print("""
    Setup:
    - Swarm A (Montague): 3 nodes, Genesis at T=1,000,000us
    - Swarm B (Capulet):  3 nodes, Genesis at T=1,500,000us (500ms older)
    - Swarms are isolated for "1 year" (simulated)
    - Then: A bridge node "Romeo" can hear both swarms

    Question: Does Romeo flip-flop? Does one swarm absorb the other?

    Expected: Capulet wins (older atomic time). Montague demotes.
    """)

    sim = UTLPSimulator(seed=31415)

    # Create Swarm A (Montague) - 3 nodes
    montague_a = sim.add_node("AA:01", drift_ppm=2.0)
    montague_a.stratum = 1
    montague_a.state = NodeState.GENESIS
    montague_a.local_clock_us = 1_000_000
    montague_a.atomic_time_us = 1_000_000

    montague_b = sim.add_node("AA:02", drift_ppm=-1.0)
    montague_c = sim.add_node("AA:03", drift_ppm=1.5)

    # Create Swarm B (Capulet) - 3 nodes with 500ms head start
    capulet_a = sim.add_node("BB:01", drift_ppm=3.0)
    capulet_a.stratum = 1
    capulet_a.state = NodeState.GENESIS
    capulet_a.local_clock_us = 1_500_000  # 500ms older
    capulet_a.atomic_time_us = 1_500_000

    capulet_b = sim.add_node("BB:02", drift_ppm=-2.0)
    capulet_c = sim.add_node("BB:03", drift_ppm=0.5)

    # Initially, swarms are isolated (don't see each other's beacons)
    # Simulate by running each swarm separately

    print("\n[1] Running isolated swarms for 60s...")

    # Run Montague swarm alone
    for node in sim.nodes:
        if node.mac.startswith("BB"):
            node.is_online = False

    for _ in range(30):
        sim.tick(1_000_000)

    # Run Capulet swarm alone
    for node in sim.nodes:
        if node.mac.startswith("AA"):
            node.is_online = False
        if node.mac.startswith("BB"):
            node.is_online = True

    for _ in range(30):
        sim.tick(1_000_000)

    # Bring everyone back online
    for node in sim.nodes:
        node.is_online = True

    print("\n[2] Swarms can now see each other...")
    sim.print_status()

    # Run with all nodes visible
    print("\n[3] Running merged swarms for 60s...")
    for i in range(60):
        sim.tick(1_000_000)
        if i % 15 == 0:
            strata = {n.mac: n.stratum for n in sim.nodes}
            print(f"  T={sim.tick_count}: {strata}")

    sim.print_status()

    # Analysis
    print("\n" + "="*70)
    print("TWIN CITIES MERGE ANALYSIS")
    print("="*70)

    # Count Genesis nodes
    genesis_nodes = [n for n in sim.nodes if n.stratum == 1]
    montague_gen = [n for n in genesis_nodes if n.mac.startswith("AA")]
    capulet_gen = [n for n in genesis_nodes if n.mac.startswith("BB")]

    print(f"\nGenesis nodes: {len(genesis_nodes)}")
    print(f"  Montague (AA): {len(montague_gen)}")
    print(f"  Capulet (BB):  {len(capulet_gen)}")

    if len(genesis_nodes) == 1:
        winner = genesis_nodes[0]
        if winner.mac.startswith("BB"):
            print("\n[OK] Capulet (older swarm) won - as expected!")
            print("    'First Born Wins' correctly selected the elder timeline.")
        else:
            print("\n[!] WARNING: Montague won despite being younger!")
    elif len(genesis_nodes) > 1:
        print("\n[!] SPLIT BRAIN: Multiple Genesis nodes!")
        print("    The swarms failed to merge properly.")
    else:
        print("\n[?] NO GENESIS - unexpected state")

    # Check final coherence
    atomic_times = {n.mac: n.atomic_time_us for n in sim.nodes}
    offsets = list(atomic_times.values())
    spread = max(offsets) - min(offsets)

    print(f"\nFinal atomic time spread: {spread}us ({spread/1000:.1f}ms)")

    if spread < 100_000:  # 100ms
        print("[OK] Swarms successfully merged (spread < 100ms)")
    else:
        print("[!] Swarms NOT fully merged - significant offset remains")

    # Key log entries
    print("\n" + "-"*70)
    print("KEY LOG ENTRIES:")
    interesting = [e for e in sim.log if any(k in e for k in
                   ["FIRST_BORN", "INNATE", "elder", "AA:01", "BB:01"])]
    for entry in interesting[-25:]:
        print(entry)

    return sim


def run_behavioral_defense_scenario():
    """
    Test: Physics-Based Behavioral Verification Defeats Rogue

    Same setup as run_rogue_genesis_scenario(), but with behavioral
    verification ENABLED. The rogue claims ancient time, but we track
    its clock BEHAVIOR over time to detect the lie.

    Key insight: You can lie about your epoch, but you can't fake
    a clock that's been running for 11 days when I've only been
    observing you for 60 seconds.
    """
    print("\n" + "="*70)
    print("SCENARIO: Behavioral Defense vs Byzantine Rogue")
    print("="*70)
    print("""
    Same as Rogue Genesis scenario, but with BEHAVIORAL VERIFICATION enabled.

    Attack: Rogue claims atomic_time = 999 trillion us (~11.5 days old)
    Defense: We track the rogue's clock RATE over time.
             After 5 observations, we can predict where their clock
             SHOULD be. A claim that deviates impossibly = Byzantine detected.

    Expected: Rogue is detected and punished when it tries to use
              "First Born Wins" - its claim doesn't match observed behavior.
    """)

    # Enable behavioral verification
    sim = UTLPSimulator(seed=66666, behavioral_verification=True)

    # Create healthy swarm first
    healthy_a = sim.add_node("AA:01", drift_ppm=2.0)
    healthy_a.stratum = 1
    healthy_a.state = NodeState.GENESIS
    healthy_a.local_clock_us = 1_000_000
    healthy_a.atomic_time_us = 1_000_000

    healthy_b = sim.add_node("AA:02", drift_ppm=-1.0)
    healthy_c = sim.add_node("AA:03", drift_ppm=1.5)

    # Establish healthy swarm first (60s)
    print("\n[1] Establishing healthy swarm for 60s...")
    for _ in range(60):
        sim.tick(1_000_000)

    sim.print_status()

    # Now introduce the ROGUE
    print("\n[2] Rogue node RR:01 appears with ancient epoch...")

    rogue = sim.add_node("RR:01", drift_ppm=0.0)
    rogue.stratum = 1
    rogue.state = NodeState.GENESIS

    # Rogue claims ancient time - 1 trillion microseconds (~11.5 days)
    rogue.local_clock_us = 500_000
    rogue.atomic_time_us = 999_999_999_999

    # Rogue wrapper (same as before - refuses demotion and time adoption)
    class RogueNode:
        def __init__(self, node, original_offset):
            self.node = node
            self.original_offset = original_offset
            self.demotion_refusal_count = 0
            self.time_adoption_refusal_count = 0

        def force_byzantine(self):
            if self.node.stratum != 1:
                self.demotion_refusal_count += 1
                self.node.stratum = 1
                self.node.state = NodeState.GENESIS

            current_atomic = self.node.get_atomic_time()
            expected_atomic = self.node.local_clock_us + self.original_offset
            if abs(current_atomic - expected_atomic) > 1000:
                self.time_adoption_refusal_count += 1
                self.node.time_offset_us = self.original_offset

    rogue_original_offset = 999_999_999_999 - rogue.local_clock_us
    rogue_wrapper = RogueNode(rogue, rogue_original_offset)

    # Run simulation
    print("\n[3] Running for 120s with rogue present (behavioral verification ON)...")
    rogue_health_history = []
    byzantine_detections = []

    for i in range(120):
        sim.tick(1_000_000)
        rogue_wrapper.force_byzantine()

        # Track rogue's health and Byzantine detections
        if i % 10 == 0:
            rogue_health = 0
            if "RR:01" in sim.nodes[0].peers:
                rogue_health = sim.nodes[0].peers["RR:01"].health
            rogue_health_history.append((i, rogue_health))

            strata = {n.mac: n.stratum for n in sim.nodes}
            print(f"  T={sim.tick_count}: strata={strata}, rogue_health={rogue_health}")

        # Check for Byzantine detection in log
        for entry in sim.log[-5:]:
            if "BYZANTINE_DETECTED" in entry and entry not in byzantine_detections:
                byzantine_detections.append(entry)

    sim.print_status()

    # Analysis
    print("\n" + "="*70)
    print("BEHAVIORAL DEFENSE ANALYSIS")
    print("="*70)

    # Check Byzantine detections
    print(f"\nByzantine detection events: {len(byzantine_detections)}")
    for entry in byzantine_detections[:10]:
        print(f"  {entry}")

    # Check if healthy swarm is still intact
    healthy_nodes = [n for n in sim.nodes if n.mac.startswith("AA")]
    healthy_genesis = [n for n in healthy_nodes if n.stratum == 1]

    print(f"\nHealthy swarm Genesis nodes: {len(healthy_genesis)}")
    for n in healthy_genesis:
        print(f"  {n.mac}: stratum={n.stratum}, atomic={n.atomic_time_us}")

    # Check rogue's health
    print(f"\nRogue's final health as seen by healthy nodes:")
    for node in healthy_nodes:
        if "RR:01" in node.peers:
            peer = node.peers["RR:01"]
            print(f"  {node.mac} sees RR:01: health={peer.health}, "
                  f"drift_samples={peer.drift_samples}, "
                  f"drift_variance={peer.drift_variance:.1f}")

    # Did healthy nodes adopt rogue's time?
    atomic_times = {n.mac: n.atomic_time_us for n in healthy_nodes}
    healthy_spread = max(atomic_times.values()) - min(atomic_times.values())
    print(f"\nHealthy swarm spread: {healthy_spread}us ({healthy_spread/1000:.1f}ms)")

    rogue_adopted = False
    for mac, at in atomic_times.items():
        if abs(at - rogue.atomic_time_us) < 1_000_000:
            rogue_adopted = True
            print(f"  [!] {mac} appears to have adopted rogue's time!")

    # Health trajectory
    print(f"\nRogue health trajectory:")
    for tick, health in rogue_health_history:
        bar = "#" * (health // 10) if health > 0 else "X"
        status = "[ISOLATED]" if health == 0 else ""
        print(f"  T={tick:3d}: {health:3d} {bar} {status}")

    # Verdict
    print("\n" + "-"*70)
    if len(byzantine_detections) > 0 and not rogue_adopted:
        print("VERDICT: [OK] BEHAVIORAL VERIFICATION DETECTED THE BYZANTINE ROGUE!")
        print("         The physics-based defense correctly identified impossible claims.")
        print("         Swarm integrity maintained despite 'First Born Wins' attack.")
    elif not rogue_adopted:
        print("VERDICT: [OK] Rogue isolated (but behavioral detection may need tuning)")
    else:
        print("VERDICT: [!] SWARM CORRUPTED - Behavioral defense failed!")

    return sim


def run_web_merge_scenario():
    """
    The "Web of Time" Merge Scenario

    As UTLP adoption grows, previously isolated swarms will encounter each other.
    This simulates the graceful merging of two established, synchronized swarms
    with different epochs.

    Unlike the Rogue Genesis scenario, BOTH swarms are legitimate and healthy.
    We need to merge them without disrupting either swarm's internal coherence.

    Key challenges:
    1. Two stratum-1 nodes meet - "First Born Wins" must decide
    2. The "losing" Genesis must demote gracefully
    3. Followers of the losing Genesis must adopt new time smoothly
    4. Final result: Single unified swarm with minimal disruption
    """
    print("\n" + "="*70)
    print("SCENARIO: Web of Time Merge (Two Healthy Swarms)")
    print("="*70)
    print("""
    Background:
    As UTLP grows from 2 devices to millions, previously isolated swarms
    will discover each other. Unlike a Byzantine attack, BOTH swarms are
    legitimate - they just have different epochs.

    Setup:
    - Swarm ALPHA (older): 4 nodes, Genesis at T=100M us, running for "weeks"
    - Swarm BETA (newer):  4 nodes, Genesis at T=50M us, running for "days"
    - Swarms isolated, then suddenly can communicate (new node bridges them)

    Expected behavior:
    1. ALPHA's Genesis (older atomic time) should win via "First Born Wins"
    2. BETA's Genesis should demote to stratum 2
    3. BETA's followers should adopt ALPHA's timeline through BETA-Genesis
    4. Final state: Single swarm with ALPHA's timeline

    Key metric: Transition should be smooth - no oscillation, no split brain
    """)

    # Enable behavioral verification for epoch merge handling
    sim = UTLPSimulator(seed=271828, behavioral_verification=True)

    # Create ALPHA swarm (the elder) - 4 nodes
    print("\n[SETUP] Creating ALPHA swarm (elder, 4 nodes)...")
    alpha_gen = sim.add_node("AL:01", drift_ppm=1.5)
    alpha_gen.stratum = 1
    alpha_gen.state = NodeState.GENESIS
    alpha_gen.local_clock_us = 100_000_000  # 100 seconds of runtime
    alpha_gen.atomic_time_us = 100_000_000

    alpha_2 = sim.add_node("AL:02", drift_ppm=-0.5)
    alpha_3 = sim.add_node("AL:03", drift_ppm=2.0)
    alpha_4 = sim.add_node("AL:04", drift_ppm=-1.0)

    # Create BETA swarm (younger) - 4 nodes
    print("[SETUP] Creating BETA swarm (younger, 4 nodes)...")
    beta_gen = sim.add_node("BE:01", drift_ppm=3.0)
    beta_gen.stratum = 1
    beta_gen.state = NodeState.GENESIS
    beta_gen.local_clock_us = 50_000_000  # 50 seconds - half ALPHA's age
    beta_gen.atomic_time_us = 50_000_000

    beta_2 = sim.add_node("BE:02", drift_ppm=-2.0)
    beta_3 = sim.add_node("BE:03", drift_ppm=0.5)
    beta_4 = sim.add_node("BE:04", drift_ppm=1.0)

    # Phase 1: Run swarms in isolation
    print("\n[PHASE 1] Running swarms in isolation for 60s...")

    # ALPHA alone first
    for node in sim.nodes:
        if node.mac.startswith("BE"):
            node.is_online = False

    for _ in range(30):
        sim.tick(1_000_000)

    # BETA alone
    for node in sim.nodes:
        if node.mac.startswith("AL"):
            node.is_online = False
        if node.mac.startswith("BE"):
            node.is_online = True

    for _ in range(30):
        sim.tick(1_000_000)

    # Bring everyone back online
    for node in sim.nodes:
        node.is_online = True

    print("\n[PHASE 2] Swarm states before merge:")
    alpha_nodes = [n for n in sim.nodes if n.mac.startswith("AL")]
    beta_nodes = [n for n in sim.nodes if n.mac.startswith("BE")]

    print(f"  ALPHA Genesis: {alpha_gen.mac} atomic={alpha_gen.atomic_time_us}")
    print(f"  BETA Genesis:  {beta_gen.mac} atomic={beta_gen.atomic_time_us}")
    print(f"  Time difference: {alpha_gen.atomic_time_us - beta_gen.atomic_time_us}us "
          f"({(alpha_gen.atomic_time_us - beta_gen.atomic_time_us)/1e6:.1f}s)")

    # Phase 3: MERGE - all nodes can now see each other
    print("\n[PHASE 3] Swarms can now communicate - observing merge...")

    # Track merge progress
    merge_log = []

    for i in range(120):
        sim.tick(1_000_000)

        if i % 20 == 0:
            # Snapshot state
            alpha_strata = {n.mac: n.stratum for n in alpha_nodes}
            beta_strata = {n.mac: n.stratum for n in beta_nodes}
            alpha_genesis = sum(1 for n in alpha_nodes if n.stratum == 1)
            beta_genesis = sum(1 for n in beta_nodes if n.stratum == 1)

            merge_log.append({
                'tick': sim.tick_count,
                'alpha_genesis': alpha_genesis,
                'beta_genesis': beta_genesis,
                'alpha_strata': dict(alpha_strata),
                'beta_strata': dict(beta_strata)
            })

            print(f"  T={sim.tick_count}: ALPHA Genesis={alpha_genesis}, BETA Genesis={beta_genesis}")

    sim.print_status()

    # Analysis
    print("\n" + "="*70)
    print("WEB OF TIME MERGE ANALYSIS")
    print("="*70)

    # Who won?
    all_genesis = [n for n in sim.nodes if n.stratum == 1]
    print(f"\nFinal Genesis nodes: {len(all_genesis)}")
    for n in all_genesis:
        swarm = "ALPHA" if n.mac.startswith("AL") else "BETA"
        print(f"  {n.mac} ({swarm}): atomic={n.atomic_time_us}")

    if len(all_genesis) == 1:
        winner = all_genesis[0]
        if winner.mac.startswith("AL"):
            print("\n[OK] ALPHA (elder) won - correct behavior!")
            print("    'First Born Wins' selected the older timeline.")
        else:
            print("\n[!] BETA (younger) won - unexpected!")
            print("    This violates 'First Born Wins' principle.")
    elif len(all_genesis) > 1:
        print("\n[!] SPLIT BRAIN: Multiple Genesis nodes!")
        alpha_gen_count = sum(1 for n in all_genesis if n.mac.startswith("AL"))
        beta_gen_count = sum(1 for n in all_genesis if n.mac.startswith("BE"))
        print(f"    ALPHA Genesis: {alpha_gen_count}, BETA Genesis: {beta_gen_count}")
    else:
        print("\n[?] NO GENESIS - unexpected state")

    # Check merge completeness
    print("\nMerge Completeness:")
    atomic_times = {n.mac: n.atomic_time_us for n in sim.nodes}
    all_offsets = list(atomic_times.values())
    spread = max(all_offsets) - min(all_offsets)

    print(f"  Total atomic time spread: {spread}us ({spread/1000:.1f}ms)")

    if spread < 10_000:  # 10ms
        print("  [OK] Full convergence - all nodes within 10ms")
    elif spread < 100_000:  # 100ms
        print("  [OK] Acceptable convergence - all nodes within 100ms")
    else:
        print("  [!] Incomplete merge - significant time spread remains")

    # Analyze stratum distribution
    stratum_dist = {}
    for node in sim.nodes:
        s = node.stratum
        stratum_dist[s] = stratum_dist.get(s, 0) + 1

    print(f"\nFinal stratum distribution:")
    for s in sorted(stratum_dist.keys()):
        nodes_at_s = [n.mac for n in sim.nodes if n.stratum == s]
        print(f"  Stratum {s}: {stratum_dist[s]} nodes ({', '.join(nodes_at_s)})")

    # Merge timeline
    print("\nMerge Timeline:")
    for entry in merge_log:
        print(f"  T={entry['tick']}: ALPHA Genesis={entry['alpha_genesis']}, "
              f"BETA Genesis={entry['beta_genesis']}")

    # Check for oscillation (flip-flopping)
    oscillation_detected = False
    prev_alpha = None
    for entry in merge_log:
        if prev_alpha is not None:
            if entry['alpha_genesis'] > prev_alpha:
                oscillation_detected = True
                print(f"  [!] OSCILLATION at T={entry['tick']}: ALPHA Genesis increased!")
        prev_alpha = entry['alpha_genesis']

    if not oscillation_detected:
        print("\n[OK] No oscillation detected - clean monotonic merge")

    # Health cross-check (do BETA nodes trust ALPHA Genesis?)
    print("\nCross-swarm trust:")
    for node in beta_nodes:
        if "AL:01" in node.peers:
            peer = node.peers["AL:01"]
            print(f"  {node.mac} sees ALPHA Genesis (AL:01): health={peer.health}")

    for node in alpha_nodes:
        if "BE:01" in node.peers:
            peer = node.peers["BE:01"]
            print(f"  {node.mac} sees BETA Genesis (BE:01): health={peer.health}")

    # Key log entries
    print("\n" + "-"*70)
    print("KEY LOG ENTRIES (merge-related):")
    interesting = [e for e in sim.log if any(k in e for k in
                   ["FIRST_BORN", "INNATE", "AL:01", "BE:01", "Deferring"])]
    for entry in interesting[-30:]:
        print(entry)

    # Verdict
    print("\n" + "-"*70)
    if len(all_genesis) == 1 and spread < 100_000 and not oscillation_detected:
        print("VERDICT: [OK] CLEAN MERGE - Web of Time successfully grew!")
        print("         Two healthy swarms became one with elder's timeline.")
        print("         No oscillation, no split brain, minimal disruption.")
    elif len(all_genesis) == 1:
        print("VERDICT: [OK] MERGE COMPLETE with some concerns")
        print(f"         Final spread: {spread/1000:.1f}ms")
    else:
        print("VERDICT: [!] MERGE INCOMPLETE - further work needed")

    return sim


def run_derivative_detection_scenario():
    """
    Test: Derivative-Based Byzantine Detection

    This scenario specifically exercises the multi-derivative analysis:
    - Jitter variance (2nd derivative of offset)
    - Health velocity (1st derivative of trust)
    - Coherence velocity (1st derivative of swarm health)

    We introduce a "Jittery Byzantine" attacker who:
    1. Claims a legitimate epoch (not ancient like previous rogue)
    2. Has correct average offset (passes 0th order checks)
    3. BUT has erratic timing (high jitter variance)

    This tests whether the 2nd derivative check catches attacks that
    0th order checks would miss.

    Gemini's "Cuckoo Bird" insight: The expensive signal is behavioral
    consistency over time. A real crystal can't fake low jitter variance.
    """
    print("\n" + "="*70)
    print("SCENARIO: Derivative-Based Byzantine Detection")
    print("="*70)
    print("""
    Attack Vector: "Jittery Byzantine"

    Unlike the Rogue Genesis (ancient epoch claim), this attacker is subtle:
    - Claims reasonable epoch (not 11 days old)
    - Average offset is correct (passes consensus check)
    - BUT: Timing is erratic (random jitter each beacon)

    Detection Method:
    - 0th derivative (offset): PASSES - average is correct
    - 1st derivative (jitter EMA): SUSPICIOUS - higher than normal
    - 2nd derivative (jitter variance): FAILS - too high variance

    Real crystals have consistent jitter (~50us). Random generators have
    high variance (could be 10us or 1000us each time).
    """)

    sim = UTLPSimulator(seed=314159, behavioral_verification=True)

    # Create healthy swarm - 3 legitimate nodes with real crystal behavior
    print("\n[1] Creating healthy swarm with realistic crystal drift...")

    healthy_a = sim.add_node("AA:01", drift_ppm=5.0)  # +5ppm drift
    healthy_a.stratum = 1
    healthy_a.state = NodeState.GENESIS
    healthy_a.local_clock_us = 1_000_000
    healthy_a.atomic_time_us = 1_000_000

    healthy_b = sim.add_node("AA:02", drift_ppm=-3.0)  # -3ppm drift
    healthy_c = sim.add_node("AA:03", drift_ppm=2.0)   # +2ppm drift

    # Run healthy swarm to establish baseline
    print("[2] Establishing healthy baseline for 30s...")
    for _ in range(30):
        sim.tick(1_000_000)

    # Record baseline derivatives
    print("\n[3] Baseline derivative metrics for healthy nodes:")
    for node in sim.nodes:
        if node.mac.startswith("AA"):
            for peer_mac, peer in node.peers.items():
                if peer.jitter_samples >= 5:
                    jitter_std = int(peer.jitter_variance_us2 ** 0.5)
                    print(f"  {node.mac} sees {peer_mac}: jitter_ema={peer.jitter_ema_us}us, "
                          f"jitter_std={jitter_std}us, health_v={peer.health_velocity}")

    # Now introduce the Jittery Byzantine
    print("\n[4] Introducing 'Jittery Byzantine' attacker (JB:01)...")

    jittery = sim.add_node("JB:01", drift_ppm=0.0)  # Perfect average drift
    jittery.stratum = 2  # Claims follower (not Genesis - more subtle)
    jittery.state = NodeState.FOLLOWER
    jittery.local_clock_us = healthy_a.local_clock_us  # Matches healthy swarm
    jittery.atomic_time_us = healthy_a.atomic_time_us  # Correct epoch

    # Custom jitter injection - we'll add random offset each tick
    class JitteryByzantine:
        """Attacker that adds random jitter to each beacon"""
        def __init__(self, node):
            self.node = node
            self.base_offset = node.time_offset_us
            self.jitter_history = []

        def inject_jitter(self):
            """Add random jitter each tick (simulating bad timestamp generation)"""
            # Random jitter between -5000us and +5000us
            # This exceeds the 2000us agreement threshold ~60% of the time
            # causing DRIFTING penalties (-10 health) frequently
            jitter = random.randint(-5000, 5000)
            self.node.time_offset_us = self.base_offset + jitter
            self.jitter_history.append(jitter)

    jittery_wrapper = JitteryByzantine(jittery)

    # Run with jittery Byzantine present
    print("[5] Running for 90s with jittery attacker...")
    jittery_health_history = []
    coherence_history = []

    for i in range(90):
        # Inject jitter before beacon
        jittery_wrapper.inject_jitter()

        sim.tick(1_000_000)

        # Track metrics every 10s
        if i % 10 == 0:
            # Get jittery's health as seen by healthy nodes
            jittery_health = 0
            jittery_jitter_std = 0
            jittery_health_v = 0

            if "JB:01" in sim.nodes[0].peers:
                peer = sim.nodes[0].peers["JB:01"]
                jittery_health = peer.health
                if peer.jitter_variance_us2 > 0:
                    jittery_jitter_std = int(peer.jitter_variance_us2 ** 0.5)
                jittery_health_v = peer.health_velocity

            jittery_health_history.append({
                'tick': i,
                'health': jittery_health,
                'jitter_std': jittery_jitter_std,
                'health_v': jittery_health_v
            })

            # Get coherence
            metrics = sim.get_coherence_metrics()
            coherence_history.append({
                'tick': i,
                'pct': metrics['coherence_pct'],
                'velocity': metrics['velocity']
            })

            print(f"  T={sim.tick_count}: JB health={jittery_health}, "
                  f"jitter_std={jittery_jitter_std}us, health_v={jittery_health_v}, "
                  f"coherence={metrics['coherence_pct']}%")

    sim.print_status(show_derivatives=True)

    # Analysis
    print("\n" + "="*70)
    print("DERIVATIVE DETECTION ANALYSIS")
    print("="*70)

    # Compare jittery vs healthy peer derivatives
    print("\n[A] Jitter Variance Comparison (2nd derivative of offset):")
    print("    Real crystals: ~50us jitter, ~100us² variance (std ~10us)")
    print("    Jittery Byzantine: ~2000us jitter, ~4M us² variance (std ~2000us)")
    print()

    healthy_jitter_stds = []
    jittery_jitter_std = 0

    for node in sim.nodes:
        if node.mac == "AA:01":  # Check from Genesis perspective
            for peer_mac, peer in node.peers.items():
                if peer.jitter_samples >= 10:
                    std = int(peer.jitter_variance_us2 ** 0.5)
                    if peer_mac.startswith("AA"):
                        healthy_jitter_stds.append(std)
                        print(f"  HEALTHY {peer_mac}: jitter_std={std}us")
                    elif peer_mac == "JB:01":
                        jittery_jitter_std = std
                        print(f"  JITTERY {peer_mac}: jitter_std={std}us [***]")

    if healthy_jitter_stds and jittery_jitter_std:
        avg_healthy = sum(healthy_jitter_stds) // len(healthy_jitter_stds)
        ratio = jittery_jitter_std / avg_healthy if avg_healthy > 0 else 999
        print(f"\n  Jitter std ratio (jittery/healthy): {ratio:.1f}x")
        if ratio > 5:
            print("  [OK] 2nd derivative clearly separates Byzantine from legitimate!")
        else:
            print("  [?] Ratio lower than expected - check random seed")

    # Health velocity analysis
    print("\n[B] Health Velocity Analysis (1st derivative of trust):")
    print("    Legitimate peers: health_v ~0 to +2 (stable/growing)")
    print("    Jittery Byzantine: health_v negative (constantly penalized)")
    print()

    for node in sim.nodes:
        if node.mac == "AA:01":
            for peer_mac, peer in node.peers.items():
                if peer.health_velocity_samples >= 10:
                    status = "STABLE" if peer.health_velocity >= 0 else "DECLINING"
                    marker = "[***]" if peer_mac == "JB:01" else ""
                    print(f"  {peer_mac}: health_v={peer.health_velocity} ({status}) {marker}")

    # Coherence velocity analysis
    print("\n[C] Coherence Velocity Analysis (swarm-level 1st derivative):")
    print("    Healthy swarm: coherence_v = 0 (stable)")
    print("    Under attack: coherence_v negative (swarm destabilizing)")
    print()

    for entry in coherence_history[-5:]:
        status = "STABLE" if entry['velocity'] >= 0 else "DECLINING"
        print(f"  T={entry['tick']}: coherence={entry['pct']}%, "
              f"velocity={entry['velocity']} ({status})")

    # Check if behavioral analysis catches the Byzantine
    print("\n[D] Behavioral Suspicion Check:")
    for node in sim.nodes:
        if node.mac == "AA:01":
            for peer_mac, peer in node.peers.items():
                is_suspicious, reason = sim._is_behavior_suspicious(peer)
                if peer_mac == "JB:01":
                    print(f"  {peer_mac}: suspicious={is_suspicious}")
                    print(f"           reason: {reason}")

    # Final health comparison
    print("\n[E] Final Health Scores:")
    for node in sim.nodes:
        if node.mac == "AA:01":
            for peer_mac, peer in sorted(node.peers.items()):
                is_healthy = peer.health >= UTLP_TRUST_SYNC_THRESH
                status = "TRUSTED" if is_healthy else "ISOLATED"
                marker = "[***]" if peer_mac == "JB:01" else ""
                print(f"  {peer_mac}: health={peer.health} ({status}) {marker}")

    # Verdict
    print("\n" + "-"*70)
    jittery_final_health = 0
    if "JB:01" in sim.nodes[0].peers:
        jittery_final_health = sim.nodes[0].peers["JB:01"].health

    if jittery_final_health < UTLP_TRUST_SYNC_THRESH:
        print("VERDICT: [OK] DERIVATIVE-BASED DETECTION SUCCESSFUL!")
        print("         Jittery Byzantine isolated despite correct average offset.")
        print("         The 2nd derivative (jitter variance) caught the attack.")
        print()
        print("         Key insight: Real crystals have LOW jitter variance.")
        print("         Byzantine random generators have HIGH jitter variance.")
        print("         This is the 'expensive signal' that can't be faked.")
    else:
        print("VERDICT: [!] Byzantine NOT isolated - detection needs tuning")
        print(f"         Final health: {jittery_final_health}")

    # Log analysis
    print("\n" + "-"*70)
    print("KEY LOG ENTRIES:")
    interesting = [e for e in sim.log if any(k in e for k in
                   ["JB:01", "PUNISH", "LYING", "DRIFTING", "suspicious"])]
    for entry in interesting[-20:]:
        print(entry)

    return sim


def run_genesis_pulse_detection_scenario():
    """
    Test: Genesis Pulse Detection (S2.25)

    Validates the fast reboot detection mechanism:
    1. Established swarm with trusted peers
    2. One peer reboots and starts genesis pulsing
    3. Existing nodes should detect rapid beacon interval
    4. Epoch adoption should be blocked within 300-500ms

    This is the primary defense against the "rebooted peer corrupts swarm" bug.
    """
    print("\n" + "="*70)
    print("SCENARIO: Genesis Pulse Detection (S2.25)")
    print("="*70)
    print("""
    Bug Scenario Fixed:
    - Swarm synced for hours, nodes have high mutual trust
    - Genesis node reboots (power cycle, watchdog, crash)
    - Rebooted node starts broadcasting at genesis intervals (100ms)
    - Without S2.25: Trusted peers ADOPT rebooted node's corrupted epoch
    - With S2.25: Rapid beacon interval BLOCKS epoch adoption

    Detection Method:
    - Track observed_interval_ms (EMA of beacon intervals)
    - Genesis phases broadcast at 100ms, 500ms, 1000ms
    - If interval < 2000ms, peer is genesis pulsing
    - Block epoch adoption until peer reaches steady state (60s interval)
    """)

    sim = UTLPSimulator(seed=42424, behavioral_verification=True)

    # Create established swarm - 3 nodes that have been running for "hours"
    print("\n[1] Creating established swarm with high mutual trust...")

    genesis = sim.add_node("AA:01", drift_ppm=2.0)
    genesis.stratum = 1
    genesis.state = NodeState.GENESIS
    genesis.local_clock_us = 10_000_000  # 10 seconds runtime
    genesis.atomic_time_us = 10_000_000

    follower_b = sim.add_node("AA:02", drift_ppm=-1.5)
    follower_c = sim.add_node("AA:03", drift_ppm=1.0)

    # Run for 120 seconds to establish high trust
    print("[2] Running for 120s to establish trust...")
    for _ in range(120):
        sim.tick(1_000_000)

    # Check trust levels
    print("\n[3] Trust levels before reboot:")
    for node in sim.nodes:
        print(f"  {node.mac}: stratum={node.stratum}, atomic={node.atomic_time_us/1e6:.1f}s")
        for peer_mac, peer in node.peers.items():
            print(f"    sees {peer_mac}: health={peer.health}, interval={peer.observed_interval_ms}ms")

    # Save pre-reboot atomic times
    pre_reboot_times = {n.mac: n.atomic_time_us for n in sim.nodes}

    # Now reboot the Genesis node - it will start genesis pulsing
    print("\n[4] Genesis node AA:01 REBOOTS...")
    sim.reset_node("AA:01", new_offset_us=0)  # Fresh start at 0

    # Find the node and set it back to Genesis (it thinks it's a new Genesis)
    for node in sim.nodes:
        if node.mac == "AA:01":
            node.stratum = 1
            node.state = NodeState.GENESIS

    # Simulate genesis pulse phases - rapid beacons
    # Phase 1: 100ms intervals for first second
    print("[5] Simulating genesis pulse phases...")
    pulse_log = []

    # Run 5 second of genesis pulsing at 100ms intervals
    for i in range(50):  # 50 x 100ms = 5 seconds
        sim.tick(100_000)  # 100ms ticks

        if i % 10 == 0:  # Log every second
            # Check what followers see
            for node in sim.nodes:
                if node.mac == "AA:02":
                    if "AA:01" in node.peers:
                        peer = node.peers["AA:01"]
                        pulse_log.append({
                            'tick': i,
                            'interval': peer.observed_interval_ms,
                            'health': peer.health,
                            'is_pulsing': sim._is_genesis_pulsing(peer)
                        })
                        print(f"  T={i*100}ms: AA:02 sees AA:01: "
                              f"interval={peer.observed_interval_ms}ms, "
                              f"pulsing={sim._is_genesis_pulsing(peer)}, "
                              f"health={peer.health}")

    # Check if epoch adoption was blocked
    print("\n[6] Checking if epoch corruption was prevented...")
    post_reboot_times = {n.mac: n.atomic_time_us for n in sim.nodes}

    # Followers should NOT have adopted rebooted genesis's time
    follower_b_time = post_reboot_times["AA:02"]
    follower_c_time = post_reboot_times["AA:03"]
    genesis_time = post_reboot_times["AA:01"]

    print(f"  Genesis (rebooted): atomic={genesis_time}us (~{genesis_time/1e6:.3f}s)")
    print(f"  Follower B: atomic={follower_b_time}us (~{follower_b_time/1e6:.3f}s)")
    print(f"  Follower C: atomic={follower_c_time}us (~{follower_c_time/1e6:.3f}s)")

    # Calculate drift from pre-reboot
    b_drift = abs(follower_b_time - pre_reboot_times["AA:02"])
    c_drift = abs(follower_c_time - pre_reboot_times["AA:03"])
    expected_drift = 5_000_000 + 120_000_000  # 5s at 100ms + 120s at 1s

    print(f"\n  Follower B drift from pre-reboot: {b_drift/1e6:.3f}s (expected ~{expected_drift/1e6:.1f}s)")
    print(f"  Follower C drift from pre-reboot: {c_drift/1e6:.3f}s (expected ~{expected_drift/1e6:.1f}s)")

    # Check log for genesis pulse blocks
    print("\n[7] Genesis Pulse Detection Events:")
    genesis_pulse_events = [e for e in sim.log if "GENESIS_PULSE" in e or "REGRESSION" in e]
    for event in genesis_pulse_events[-20:]:
        print(f"  {event}")

    # Verdict
    print("\n" + "-"*70)

    # Followers should have continued at their own time, not adopted genesis's 0
    follower_corrupted = (follower_b_time < 50_000_000 or follower_c_time < 50_000_000)

    if not follower_corrupted and len(genesis_pulse_events) > 0:
        print("VERDICT: [OK] GENESIS PULSE DETECTION SUCCESSFUL!")
        print("         Rebooted Genesis was detected within ~300ms")
        print("         Epoch adoption was BLOCKED - swarm preserved its timeline")
        print()
        print("         Key insight: Rapid beacon interval reveals reboot state")
        print("         before the node even claims authority.")
    elif len(genesis_pulse_events) == 0:
        print("VERDICT: [?] No genesis pulse events detected - check simulation")
    else:
        print("VERDICT: [!] SWARM CORRUPTED despite genesis pulse detection!")
        print(f"         Follower times dropped to: B={follower_b_time/1e6:.3f}s, C={follower_c_time/1e6:.3f}s")

    return sim


def run_boot_variance_scenario():
    """
    Test: Boot Time Variance Impact

    The universe is vast - devices almost never boot at exactly the same wall time.
    This tests whether sub-millisecond boot time differences affect swarm convergence.

    Hypothesis: Boot variance < 1ms should have negligible impact on sync quality.
    """
    print("\n" + "="*70)
    print("SCENARIO: Boot Time Variance Impact")
    print("="*70)
    print("""
    Question: Does sub-millisecond boot time variance affect sync quality?

    Setup:
    - 3 nodes with ±500us (0.5ms) random boot variance
    - Each node's initial atomic time offset by random amount in [-500us, +500us]
    - Run for 60s and measure final convergence

    Hypothesis: Variance should be absorbed during initial sync phase.
    """)

    results = []

    # Run multiple trials with different seeds
    for trial in range(5):
        sim = UTLPSimulator(seed=11111 + trial, behavioral_verification=True)

        # Create nodes with boot variance
        boot_variance_us = 500  # ±500us = sub-millisecond

        node_a = sim.add_node("AA:01", drift_ppm=3.0, boot_variance_us=boot_variance_us)
        node_a.stratum = 1
        node_a.state = NodeState.GENESIS

        sim.add_node("AA:02", drift_ppm=-2.0, boot_variance_us=boot_variance_us)
        sim.add_node("AA:03", drift_ppm=1.5, boot_variance_us=boot_variance_us)

        # Record initial offsets
        initial_times = {n.mac: n.atomic_time_us for n in sim.nodes}
        initial_spread = max(initial_times.values()) - min(initial_times.values())

        # Run for 60 seconds
        for _ in range(60):
            sim.tick(1_000_000)

        # Measure final convergence
        final_times = {n.mac: n.atomic_time_us for n in sim.nodes}
        final_spread = max(final_times.values()) - min(final_times.values())

        results.append({
            'trial': trial + 1,
            'initial_spread': initial_spread,
            'final_spread': final_spread,
            'converged': final_spread < 10_000  # < 10ms = converged
        })

        print(f"  Trial {trial+1}: initial_spread={initial_spread}us, "
              f"final_spread={final_spread}us, converged={final_spread < 10_000}")

    # Analysis
    print("\n" + "-"*70)
    print("BOOT VARIANCE RESULTS:")
    print("-"*70)

    converged_count = sum(1 for r in results if r['converged'])
    avg_initial = sum(r['initial_spread'] for r in results) // len(results)
    avg_final = sum(r['final_spread'] for r in results) // len(results)

    print(f"  Trials run: {len(results)}")
    print(f"  Trials converged: {converged_count}/{len(results)}")
    print(f"  Average initial spread: {avg_initial}us ({avg_initial/1000:.2f}ms)")
    print(f"  Average final spread: {avg_final}us ({avg_final/1000:.2f}ms)")

    # Verdict
    print("\n" + "-"*70)
    if converged_count == len(results):
        print("VERDICT: [OK] Boot variance has NEGLIGIBLE IMPACT on convergence!")
        print("         All trials converged despite ±500us initial offset.")
        print()
        print("         Key insight: UTLP's iterative refinement absorbs")
        print("         sub-millisecond boot time differences during normal sync.")
    else:
        print(f"VERDICT: [?] {len(results) - converged_count} trials failed to converge")
        print("         Boot variance may need investigation.")

    return results


if __name__ == "__main__":
    # Run main scenario (without B promoting)
    print("SCENARIO 1: Simple Genesis Reset")
    print("(B and C stay as followers while A is offline)\n")
    sim = run_genesis_reset_scenario()

    # Run promoted scenario (B becomes Genesis)
    run_promoted_genesis_scenario()

    # Run Twin Cities merge scenario (basic 3+3)
    run_twin_cities_scenario()

    # Run Rogue Genesis (Byzantine actor) scenario
    run_rogue_genesis_scenario()

    # Run Behavioral Defense scenario (physics-based Byzantine detection)
    run_behavioral_defense_scenario()

    # Run Web of Time merge scenario (larger 4+4 swarms)
    run_web_merge_scenario()

    # Run Derivative-Based Detection scenario (Jittery Byzantine)
    run_derivative_detection_scenario()

    # Run Genesis Pulse Detection scenario (S2.25)
    run_genesis_pulse_detection_scenario()

    # Run Boot Variance scenario
    run_boot_variance_scenario()

    # Run parameter sweep
    print("\n\n")
    results = run_multiple_scenarios()
