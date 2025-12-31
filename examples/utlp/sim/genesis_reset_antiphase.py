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

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.true_time_us = 0
        self.nodes: List[Node] = []
        self.log: List[str] = []
        self.tick_count = 0

    def add_node(self, mac: str, drift_ppm: float = 0.0,
                 initial_offset_us: int = 0) -> Node:
        """Add a node to the simulation"""
        node = Node(
            mac=mac,
            drift_rate_ppm=drift_ppm,
            time_offset_us=initial_offset_us,
            boot_time_us=self.true_time_us,
            local_clock_us=0,
            atomic_time_us=initial_offset_us
        )
        self.nodes.append(node)
        self._log(f"[BOOT] Node {mac} online, drift={drift_ppm}ppm, offset={initial_offset_us}us")
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

        # Judge the observation
        delta, reason = self._judge_observation(receiver, beacon.mac, offset_us)

        # Update health
        old_health = peer.health
        peer.health = max(0, min(UTLP_TRUST_MAX, peer.health + delta))
        peer.last_offset_us = offset_us

        if delta < 0:
            self._log(f"[{receiver.mac}] Peer {beacon.mac} PUNISHED: {reason} "
                     f"(offset={offset_us}us, health {old_health}→{peer.health})")

        # Check for adoption (Innate Immunity / First Born Wins)
        self._check_adoption(receiver, beacon, offset_us)

    def _check_adoption(self, node: Node, beacon: Beacon, offset_us: int):
        """
        Check if we should adopt this peer's time
        Implements Innate Immunity + First Born Wins
        """
        peer = node.peers[beacon.mac]

        # Innate immunity: Lower stratum always wins
        if beacon.stratum < node.stratum:
            self._log(f"[{node.mac}] INNATE: Adopting {beacon.mac} "
                     f"(stratum {beacon.stratum} < {node.stratum})")
            node.time_offset_us += offset_us
            node.stratum = beacon.stratum + 1
            node.state = NodeState.FOLLOWER
            return

        # Same stratum: First Born Wins (oldest atomic time)
        if beacon.stratum == node.stratum and node.stratum == 1:
            # Compare atomic times - older (larger) wins
            my_atomic = node.get_atomic_time()
            their_atomic = beacon.tx_timestamp_us

            if their_atomic > my_atomic:
                # They are elder - I defer
                self._log(f"[{node.mac}] FIRST_BORN: Deferring to {beacon.mac} "
                         f"(their atomic {their_atomic} > mine {my_atomic})")
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

    def print_status(self):
        """Print current swarm status"""
        print(f"\n{'='*70}")
        print(f"T={self.tick_count} | True time: {self.true_time_us/1e6:.3f}s")
        print(f"{'='*70}")

        for node in self.nodes:
            status = "OFFLINE" if not node.is_online else node.state.value
            print(f"\n  [{node.mac}] {status} stratum={node.stratum}")
            print(f"    atomic_time={node.atomic_time_us}us, "
                  f"offset={node.time_offset_us}us")

            if node.peers:
                print(f"    Peers:")
                for mac, peer in node.peers.items():
                    print(f"      {mac}: health={peer.health:3d}, "
                          f"offset={peer.last_offset_us:+8d}us, "
                          f"interactions={peer.interactions}")

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


if __name__ == "__main__":
    # Run main scenario (without B promoting)
    print("SCENARIO 1: Simple Genesis Reset")
    print("(B and C stay as followers while A is offline)\n")
    sim = run_genesis_reset_scenario()

    # Run promoted scenario (B becomes Genesis)
    run_promoted_genesis_scenario()

    # Run parameter sweep
    print("\n\n")
    results = run_multiple_scenarios()
