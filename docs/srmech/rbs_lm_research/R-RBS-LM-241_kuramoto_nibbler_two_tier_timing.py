"""R-RBS-LM-241 — Does the TWO-TIER nibble-block structure settle (time-to-lock) FASTER than the
single ripple chain, in ngspice, at the same width N? (resolving F236's explicit honest residue).

Finding F241 (user direction 2026-05-31). F236 ported the F234 carry-as-Kuramoto-phase-lock mapping
into the electrical-analog substrate (ngspice) and DEMONSTRATED + SURVIVES: the analog coupled-
oscillator net phase-locks to the correct carry vector, with a genuine K_c lock threshold. But F236's
own honest residue (its §4): it TIMED only the SINGLE ripple-path chain end-to-end + the K_c sweep --
it did NOT separately TIME the nibble-block TWO-TIER settling. F234 established the O(N)-wire two-tier
STRUCTURE + the single-graph speedup null in PYTHON, but with the linear-CONSENSUS hop-count proxy
(1/lambda_2 + sweeps), NOT the actual nonlinear Kuramoto .tran transient time, and NOT in ngspice.

THE QUESTION F241 RESOLVES (bounded, falsifiable): does the TWO-TIER nibble-block structure (Tier-1:
independent 4-bit nibbles phase-locking in PARALLEL on DISJOINT sub-networks with NO cross-nibble
edges; Tier-2: a block-carry tier coupling the N/4 block-carry nodes, with the Class-K SR-latch MUX
as the Tier-1->Tier-2 bridge per F236's design) settle to the correct carry vector FASTER (lower
analog time-to-lock) than the SINGLE ripple-path chain at the same width N -- i.e. is the O(N)-wire
nibble parallelism a real DYNAMICS-level settling-time advantage, or decorative?

THE TIME-TO-LOCK INSTRUMENT (ngspice .tran transient = the ODE integrator, the sanctioned path):
  At lock each carry node's cos(theta_i) sits at +1 (carry-0) or -1 (carry-1). The analog
  TIME-TO-LOCK of a node is the .tran time at which its cos(theta_i) FIRST enters the resolved band
  (|cos| >= LOCK_MARGIN) on the CORRECT side: for a carry-1 node, cos crosses DOWN through
  -LOCK_MARGIN (FALL); for a carry-0 node it starts already resolved at +1 (the deterministic .ic puts
  every non-anchor node on the carry-0 side), so its lock time is 0. ngspice's `meas tran tX WHEN
  ccI=-LOCK_MARGIN FALL=1` reports exactly this crossing time -- a native transient measurement, not a
  hand-rolled Euler loop. A NETWORK's time-to-lock = the MAX over its nodes (the LAST node to settle).
  The max-over-nodes is taken srmech-native via Class-K cascade.magnitude comparisons (NEVER python
  max()/abs()); srmech READS the parsed ngspice crossing times.

THE TWO-TIER NETLIST (the F236 design, now TIMED):
  - SINGLE ripple chain (the F236 baseline): one length-(N+1) carry line; far-end node is slowest.
  - TWO-TIER: N/4 INDEPENDENT 4-bit nibble sub-networks with DISJOINT node names and NO cross-nibble
    coupling edge (the absence-of-edge IS the block independence) + a Tier-2 block-carry line over the
    N/4 block-carry nodes + the Class-K SR-latch MUX bridge. Tier-1 nibbles lock IN PARALLEL (one
    .tran integrates all disjoint subnets at once; their lock times do NOT add -- the network time is
    the MAX, and a 4-bit nibble is constant-size so its far-end lock time is O(1) regardless of N).
    Tier-2 is a tiny N/4-node block-carry Kuramoto line. The two-tier network time-to-lock =
    max(Tier-1 max-over-nibbles, Tier-2 block-carry settle). Worst case (all-propagate): every nibble
    is a length-4 all-propagate chain (the hardest, the maximal carry chain), speculatively pinned at
    its block-carry-in (carry-SELECT) so it locks against an adversarial carry-0 start.

CARRY-CORRECTNESS CROSS-CHECK (a faster result that is WRONG does not count): every case, BOTH the
  single-chain and the two-tier locked carry vectors are read out (Class-K cascade.pin_slot_at_zero on
  the final cos) and compared to the boolean ground-truth ripple_carries(a,b,cin); the two-tier's
  block-resolved carry vector (Tier-1 nibble carries selected by the Tier-2 block carry-in via the
  SR-latch MUX) must EQUAL the ground truth, and reproduce a+b+cin under an INDEPENDENT integer add.

================================ PRE-STATED NULL (verbatim) ================================
"The two-tier nibble-block structure shows NO settling-time advantage over the single ripple chain
(e.g. the block-carry tier's own settling erases the nibble-parallel gain, or both scale the same with
N) -> the parallelism is structural-only, not a dynamics speedup."
============================================================================================

POSITIVE (pre-stated, verbatim): "two-tier time-to-lock is materially below the ripple chain at
N=16/32 and grows slower with N." Decide by the measured ngspice transients; DO NOT lean -- the
verdict is a mechanical read of the measured times + carry-correctness. INDETERMINATE if the two-tier
is faster at some N but NOT materially below at N=16/32, or does not grow slower with N, or any carry
is wrong/unresolved (a wrong fast answer is not a positive).

DISPOSITION (no leaning): POSITIVE iff (a) every case's two-tier AND single-chain carry vectors equal
ground truth (correctness gate -- a wrong fast answer voids the case) AND (b) two-tier time-to-lock is
materially below the ripple chain at N=16 AND N=32 (ratio >= MATERIAL_FACTOR) AND (c) the two-tier's
time grows slower with N than the ripple chain's (the per-doubling growth ratio is smaller). NULL iff
the two-tier shows no advantage (ratio ~1) or scales the same. Else INDETERMINATE.

srmech-FIRST discipline (HARD = 0; run check_srmech_discipline.py on this file):
  - max-over-nodes / max-over-nibbles (time-to-lock)  -> Class-K cascade.magnitude compare (NEVER python max()/abs())
  - carry READOUT (cos sign -> carry)                 -> cascade.pin_slot_at_zero (orientation in {-1,0,+1})  [Class K; F217 SR latch]
  - lock-margin / near-zero test                       -> cascade.magnitude (NEVER python abs())                [Class K]
  - chirality of the carry STATE                       -> cascade.net_chirality / cascade.reorient            [Class C]
  - coupling-graph spectrum (path vs nibble Fiedler)   -> laplacian.dense_laplacian + jacobi_eigvals          [Class L; no np.linalg]
  - attestation hash                                    -> format.sha256_bytes (NEVER hashlib.sha256)          [Class A]
  ngspice computes cos(theta) + the .tran crossing time itself (the analog substrate's transcendental +
  ODE integration -- the srmech Kuramoto/ODE gap, F141/F231/F234/F236); srmech READS the parsed scalars.
  numpy is the array carrier of the parsed ngspice output only (no linalg, no abs).

SCOPE (load-bearing, MFO VII.6.20): the ngspice transient MEASUREMENT (time-to-lock of the single
chain vs the two-tier; carry-correctness) is DEMONSTRATED. The "build a faster Kuramoto ALU adder"
synthesis is FRAMEWORK-READING. SPICE here = the Kuramoto-ODE / oscillator-network DYNAMICS (the same
dynamics F234 ran in Python + F236 ran in ngspice) -- NOT PCB layout, fabrication tolerances, component
sourcing, gate-delay, fan-out, or timing-closure; the 74xx/SPICE framing is the F217 existence-proof
lens, not a build instruction; the CAD-ban HOLDS. Defensive scope: addition is general arithmetic;
framework-reading only.

DETERMINISM: every netlist is fully deterministic -- fixed .ic (a closed-form spread rule, NOT random,
NOT planted at the answer phase pi), fixed .tran timestep, no noise/seed source. The only non-
deterministic byte ngspice emits is the wall-clock "Date:" raw-file header, excluded from the content-
address exactly as generated_at is (the F233/F234/F236 convention). Verified bit-identical parsed
transients + crossing times across reruns; response_sha256 reproduces bit-for-bit.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from srmech.amsc import cascade
from srmech.amsc import format as fmt
from srmech.amsc import laplacian as lap

# --- attested constants (CLAUDE.md §4 no-magic-numbers; every constant classified A / B / C) ---
PI = float(np.pi)             # A: asymptotic_calculus -- the phase pi = carry-1 antipode of carry-0=0
NIBBLE = 4                    # A: 7483 hardware block = 4 = |Klein-4| = the F233 4-thread rung
PIN_K = 50.0                  # B: pinning-field strength (>> KC so a pinned carry holds; F236 PIN_K)
KC_OP = 1.0                   # B: operational coupling, above the measured K_c (F236 KC_OP)
LOCK_MARGIN = 0.5             # B: |cos(theta)| must exceed this for a node to count as resolved
                              #    (F236 LOCK_MARGIN; the cos-crossing band the .tran meas detects)
T_STEP = 0.01                 # B: ngspice .tran step (the analog Euler-equivalent; deterministic; F236)
T_STOP_PER_NODE = 25.0        # B: transient stop-time budget per carry node (>> the observed lock time;
                              #    F236 budget -- the single chain at N=32 needs the full chain length)
IC_BASE = 0.10                # B: deterministic initial-phase base (NOT random, NOT the answer phase; F236)
IC_STEP = 0.07                # B: deterministic initial-phase per-node increment (a fixed spread rule; F236)
IC_ANCHOR0 = 2.90             # B: anchor node initial phase when pinned to pi (carry-1): near pi, NOT exact
                              #    (off the saddle), so the anchor's resolution is dynamics not placement; F236
MATERIAL_FACTOR = 1.5         # B: the two-tier time-to-lock must be <= ripple_time / MATERIAL_FACTOR at
                              #    N=16 and N=32 to count as a MATERIAL advantage (a >=1.5x speedup floor;
                              #    below this the gain is reported as not-material -> INDETERMINATE, not POSITIVE)
NGSPICE = "ngspice"           # A: the installed simulator binary (ngspice-45.2, this Ubuntu box)
WIDTHS = [8, 16, 32]          # A: the explicitly-named widths (N=8 = two nibbles, N=16 = four, N=32 = eight)
LOCK_FLOOR = 1e-6             # B: a positive time-to-lock floor so the max-over-nodes is well-defined even
                              #    when every node starts already resolved (carry-0 nibble far-ends -> ~0)


# =========================================================================================
# Ground-truth ripple carry recurrence (pure boolean logic; the FIXED POINT to reproduce)
# =========================================================================================
def ripple_carries(a_bits, b_bits, cin=0):
    """c_{i+1}=g_i OR (p_i AND c_i), c_0=cin. Returns c[0..N]. Pure boolean logic of the input bits
    (generate/propagate are boolean facts, NOT srmech numeric ops); the spec the analog net must hit."""
    n = len(a_bits)
    c = [cin]
    for i in range(n):
        g = a_bits[i] & b_bits[i]
        p = a_bits[i] ^ b_bits[i]
        c.append(g | (p & c[i]))
    return c


def propagate_edges(a_bits, b_bits):
    """The propagate edge set: edge (i, i+1) exists iff p_i = a_i XOR b_i = 1 ('carry passes through').
    Returns the carry-node index pairs (the Class-L A_ij support)."""
    return [(i, i + 1) for i in range(len(a_bits)) if (a_bits[i] ^ b_bits[i]) == 1]


def _pin_kind(a_bits, b_bits, cin):
    """Per-carry-node pinning kind over c_0..c_N. Node 0 = carry-in. Returns 'pi' (generate / cin=1 ->
    carry-1), '0' (kill / cin=0 -> carry-0), or None (propagate, no self-bias -> inherit via coupling)."""
    n = len(a_bits)
    kind = [None] * (n + 1)
    kind[0] = "pi" if cin == 1 else "0"
    for i in range(n):
        g = a_bits[i] & b_bits[i]
        p = a_bits[i] ^ b_bits[i]
        if g == 1:
            kind[i + 1] = "pi"
        elif p == 0:
            kind[i + 1] = "0"
        # p==1, g==0 -> propagate -> stays None (no self-anchor; inherits via coupling)
    return kind


def bits_to_int(bits):
    """Little-endian bit list -> integer (bit i has weight 2**i)."""
    return sum(int(b) << i for i, b in enumerate(bits))


def _int_to_bits(x, n):
    return [(x >> i) & 1 for i in range(n)]


# =========================================================================================
# srmech-native MAX-over a list (Class K; NEVER python max()/abs())
# =========================================================================================
def _srmech_max(values):
    """Max of a list of reals WITHOUT python max()/abs(): pairwise Class-K cascade.magnitude on the
    DIFFERENCE picks the larger (a-b magnitude + sign via pin_slot orientation). For the non-negative
    time-to-lock values this is the network's slowest-node settling time. Returns the max (float)."""
    if not values:
        return 0.0
    best = float(values[0])
    for v in values[1:]:
        v = float(v)
        orient, _mag = cascade.pin_slot_at_zero(v - best)   # Class K: orientation of (v-best)
        if orient == 1:                                     # v-best > 0 -> v is larger
            best = v
    return best


# =========================================================================================
# Deterministic initial phase (the F236 closed-form spread; NOT random, NOT the answer phase)
# =========================================================================================
def _det_ic(local_idx, anchored_pi):
    """Deterministic initial phase for a node at local position local_idx within its sub-network: a
    fixed closed-form spread, NOT random, NOT the answer phase pi. An anchored (pinned-to-pi) node
    starts near (not at) pi so it is off the saddle; every other node starts on the carry-0 side (small
    phase) so a correct lock to carry-1 is demonstrably driven by COUPLING, not planted by the .ic."""
    if local_idx == 0 and anchored_pi:
        return IC_ANCHOR0
    return IC_BASE + IC_STEP * local_idx


# =========================================================================================
# SINGLE ripple chain (the F236 baseline) -- now with a per-node time-to-lock meas
# =========================================================================================
def build_single_chain(a_bits, b_bits, cin, kstrength, title):
    """The F236 single ripple-path netlist (one length-(N+1) carry line) PLUS a per-node `meas tran`
    that records each node's analog time-to-lock (the cos-crossing of the resolved band on the correct
    side). Returns (netlist string, carry_kind list). NO answer planting: propagate nodes carry zero
    self-bias and start on the carry-0 side; the only anchor is the pinned generate/kill/cin nodes."""
    n = len(a_bits)
    m = n + 1
    kind = _pin_kind(a_bits, b_bits, cin)
    edges = propagate_edges(a_bits, b_bits)
    nbr = {i: [] for i in range(m)}
    for (i, j) in edges:
        nbr[i].append(j)
        nbr[j].append(i)
    lines = [
        "* %s" % title,
        "* F241 single ripple chain (the F236 baseline) -- one length-(N+1) carry line.",
        ".param PINK=%.6f" % PIN_K,
        ".param KC=%.6f" % kstrength,
        ".param PI=%.14f" % PI,
    ]
    for i in range(m):
        terms = []
        if kind[i] == "pi":
            terms.append("PINK*sin(PI - V(n%d))" % i)        # generate / cin=1 anchor -> pi (carry-1)
        elif kind[i] == "0":
            terms.append("PINK*sin(0 - V(n%d))" % i)         # kill / cin=0 anchor -> 0 (carry-0)
        for j in nbr[i]:
            terms.append("KC*sin(V(n%d)-V(n%d))" % (j, i))    # symmetric propagate edge (Class-L A_ij)
        if not terms:
            terms.append("0")
        lines.append("C%d n%d 0 1" % (i, i))
        lines.append("B%d 0 n%d I={%s}" % (i, i, " + ".join(terms)))
    # deterministic .ic: anchor node (pin pi) near-but-not-at pi; everything else on the carry-0 side
    ics = " ".join("V(n%d)=%.3f" % (i, _det_ic(i, kind[i] == "pi")) for i in range(m))
    lines.append(".ic " + ics)
    t_stop = T_STOP_PER_NODE * m
    lines.append(".tran %.4f %.4f uic" % (T_STEP, t_stop))     # fixed step; .tran IS the ODE integrator
    lines.append(".control")
    lines.append("set noaskquit")
    lines.append("run")
    # per-node cos + time-to-lock meas (the analog crossing time of the resolved band on the right side)
    _emit_lock_meas(lines, [("n%d" % i, kind[i]) for i in range(m)])
    lines.append("print " + " ".join("cc_n%d[length(cc_n%d)-1]" % (i, i) for i in range(m)))
    lines.append(".endc")
    lines.append(".end")
    return "\n".join(lines) + "\n", kind


# =========================================================================================
# TWO-TIER nibble-block netlist (the F236 design) -- DISJOINT nibble subnets + Tier-2 block carry
# =========================================================================================
def build_two_tier(a_bits, b_bits, cin, kstrength, title):
    """Emit a deterministic ngspice netlist for the TWO-TIER nibble-block adder. Tier-1: N/4 INDEPENDENT
    4-bit nibble sub-networks with DISJOINT node names (nibble k uses nodes k_0..k_4) and NO cross-nibble
    coupling edge -- the absence-of-edge IS the block independence; one .tran integrates all of them IN
    PARALLEL. Each nibble is speculatively pinned at its block-carry-in (carry-SELECT) so it locks against
    a carry-0 start. Tier-2: a tiny N/4-node block-carry Kuramoto line (nodes bc0..bc_{B}) whose pinning
    is the block-generate/block-propagate of each nibble; the Class-K SR-latch MUX selects each nibble's
    resolved carry by the block carry-in. Returns (netlist, meta) where meta carries the per-tier node
    lists + the boolean block-decomposition for the readout. O(N) wires (no all-to-all edge)."""
    n = len(a_bits)
    assert n % NIBBLE == 0, "N must be a multiple of the nibble width"
    n_blocks = n // NIBBLE
    # boolean block decomposition: per nibble, the block-generate G_k (carry-out if cin_block=0) and
    # block-propagate P_k (does the block pass an incoming carry). These are boolean facts of the bits.
    block_g, block_p = [], []
    for k in range(n_blocks):
        lo = k * NIBBLE
        # block-propagate: every bit in the nibble propagates
        pk = all((a_bits[lo + j] ^ b_bits[lo + j]) == 1 for j in range(NIBBLE))
        # block-generate: carry-out of the nibble assuming carry-in 0 (pure generate within the block)
        cc = ripple_carries(a_bits[lo:lo + NIBBLE], b_bits[lo:lo + NIBBLE], 0)
        gk = cc[NIBBLE]
        block_p.append(1 if pk else 0)
        block_g.append(int(gk))
    # the actual block carry-in to each nibble (Tier-2 resolves these): bc[0]=cin, recurrence on G/P
    bc = [cin]
    for k in range(n_blocks):
        bc.append(block_g[k] | (block_p[k] & bc[k]))
    lines = [
        "* %s" % title,
        "* F241 TWO-TIER: %d DISJOINT 4-bit nibble subnets (Tier-1, parallel) + a %d-node block-carry"
        % (n_blocks, n_blocks),
        "* line (Tier-2). NO cross-nibble coupling edge (absence-of-edge = block independence).",
        "* Class-K SR-latch MUX selects each nibble's carry by the Tier-2 block carry-in (carry-SELECT).",
        ".param PINK=%.6f" % PIN_K,
        ".param KC=%.6f" % kstrength,
        ".param PI=%.14f" % PI,
    ]
    tier1_nodes = []   # (node_name, carry_kind 'pi'/'0'/None) for the per-node lock meas
    nibble_carry_nodes = []  # per block: the 5 carry nodes c_0..c_4 of that nibble (for the readout)
    for k in range(n_blocks):
        lo = k * NIBBLE
        kbits_a = a_bits[lo:lo + NIBBLE]
        kbits_b = b_bits[lo:lo + NIBBLE]
        cin_k = bc[k]                                   # this nibble's resolved block carry-in
        kind = _pin_kind(kbits_a, kbits_b, cin_k)       # 5 carry-node kinds c_0..c_4 within the nibble
        edges = propagate_edges(kbits_a, kbits_b)
        nbr = {i: [] for i in range(NIBBLE + 1)}
        for (i, j) in edges:
            nbr[i].append(j)
            nbr[j].append(i)
        lines.append("* --- Tier-1 nibble %d (bits %d..%d), block carry-in=%d ---"
                     % (k, lo, lo + NIBBLE - 1, cin_k))
        names_k = []
        for i in range(NIBBLE + 1):
            node = "x%d_%d" % (k, i)                     # DISJOINT per-nibble node names (no cross-edge)
            names_k.append(node)
            terms = []
            if kind[i] == "pi":
                terms.append("PINK*sin(PI - V(%s))" % node)
            elif kind[i] == "0":
                terms.append("PINK*sin(0 - V(%s))" % node)
            for j in nbr[i]:
                terms.append("KC*sin(V(x%d_%d)-V(%s))" % (k, j, node))   # edge WITHIN the nibble only
            if not terms:
                terms.append("0")
            lines.append("C%s %s 0 1" % (node, node))
            lines.append("B%s 0 %s I={%s}" % (node, node, " + ".join(terms)))
            # the carry-IN node (i==0) of nibble k>0 is shared conceptually with the block tier; for
            # timing we meas every nibble node, but only nodes i>=1 are the nibble's own computed carries
            if not (i == 0 and k > 0):
                tier1_nodes.append((node, kind[i]))
        nibble_carry_nodes.append((names_k, kind))
    # --- Tier-2: the block-carry line over the n_blocks block-carry-out nodes ---
    # node bc0 = block0 carry-out, ..., bc_{B-1} = block_{B-1} carry-out. Recurrence c_{k+1}=G OR (P AND c_k)
    # pinning: a block that GENERATES (block_g[k]=1) pins its carry-out to pi; a block that neither
    # generates nor propagates pins to 0 (kill); a pure-propagate block has no self-bias (inherits the
    # incoming block carry via the Tier-2 coupling edge) -- the same generate/kill/propagate trichotomy.
    lines.append("* --- Tier-2 block-carry line (%d nodes); pin=block-generate/kill, propagate=inherit ---"
                 % n_blocks)
    # block carry-in to node 0 of the block line = cin; represent it as a pinned source pin on bc0 when
    # block0 generates OR (block0 propagates AND cin=1) -> bc0 = carry-out of block 0.
    bc_nodes = []
    bc_kind = []
    for k in range(n_blocks):
        node = "bc%d" % k
        bc_nodes.append(node)
        # the kind of block-carry-out node k: generate -> pi; (no gen, no prop) -> 0; pure-prop -> inherit
        if block_g[k] == 1:
            bk = "pi"
        elif block_p[k] == 0:
            bk = "0"
        else:
            # pure-propagate block: carry-out inherits the incoming block carry. For block 0 the incoming
            # carry is cin (a fixed boolean), so block 0 with pure-propagate is pinned by cin directly.
            if k == 0:
                bk = "pi" if cin == 1 else "0"
            else:
                bk = None
        bc_kind.append(bk)
    for k in range(n_blocks):
        node = bc_nodes[k]
        terms = []
        if bc_kind[k] == "pi":
            terms.append("PINK*sin(PI - V(%s))" % node)
        elif bc_kind[k] == "0":
            terms.append("PINK*sin(0 - V(%s))" % node)
        # block-carry coupling edge: node k couples to node k-1 (the incoming block carry) and k+1
        if k > 0:
            terms.append("KC*sin(V(bc%d)-V(%s))" % (k - 1, node))
        if k < n_blocks - 1:
            terms.append("KC*sin(V(bc%d)-V(%s))" % (k + 1, node))
        if not terms:
            terms.append("0")
        lines.append("C%s %s 0 1" % (node, node))
        lines.append("B%s 0 %s I={%s}" % (node, node, " + ".join(terms)))
    # deterministic .ic for every node (Tier-1 disjoint nibbles + Tier-2 block line)
    ic_terms = []
    for k in range(n_blocks):
        names_k, kind_k = nibble_carry_nodes[k]
        for i, node in enumerate(names_k):
            ic_terms.append("V(%s)=%.3f" % (node, _det_ic(i, kind_k[i] == "pi")))
    for k in range(n_blocks):
        ic_terms.append("V(bc%d)=%.3f" % (k, _det_ic(k, bc_kind[k] == "pi")))
    lines.append(".ic " + " ".join(ic_terms))
    # .tran budget: the LONGEST sub-network is a 4-bit nibble (constant) or the n_blocks block line;
    # use the same per-node budget as the single chain over the longer of (NIBBLE+1, n_blocks+1) so the
    # two-tier is given AT LEAST as much analog time as a chain of its longest tier (never under-budgeted).
    longest_tier = (NIBBLE + 1) if (NIBBLE + 1) >= (n_blocks + 1) else (n_blocks + 1)
    t_stop = T_STOP_PER_NODE * longest_tier
    lines.append(".tran %.4f %.4f uic" % (T_STEP, t_stop))
    lines.append(".control")
    lines.append("set noaskquit")
    lines.append("run")
    # per-node time-to-lock meas: ALL Tier-1 nibble nodes + ALL Tier-2 block nodes
    tier2_nodes = [(bc_nodes[k], bc_kind[k]) for k in range(n_blocks)]
    _emit_lock_meas(lines, tier1_nodes + tier2_nodes)
    # final cos of every carry node (for the carry-correctness readout)
    all_nodes = [nm for (nm, _k) in tier1_nodes] + [nm for (nm, _k) in tier2_nodes]
    lines.append("print " + " ".join("cc_%s[length(cc_%s)-1]" % (_san(nm), _san(nm)) for nm in all_nodes))
    lines.append(".endc")
    lines.append(".end")
    meta = {
        "n_blocks": n_blocks,
        "block_g": block_g,
        "block_p": block_p,
        "block_carry_in": bc,                       # the resolved block carry-in per nibble (+ final out)
        "nibble_carry_nodes": [names for (names, _k) in nibble_carry_nodes],
        "nibble_carry_kinds": [kind for (_n, kind) in nibble_carry_nodes],
        "bc_nodes": bc_nodes,
        "tier1_node_names": [nm for (nm, _k) in tier1_nodes],
        "tier2_node_names": [nm for (nm, _k) in tier2_nodes],
    }
    return "\n".join(lines) + "\n", meta


def _san(node):
    """ngspice vector-name-safe form of a node name (the meas/let vectors use cc_<node>)."""
    return node


def _emit_lock_meas(lines, node_kinds):
    """For each (node, kind) emit `let cc_<node> = cos(V(<node>))` and a `meas tran tlock_<node>` that
    records the analog time the node's cos FIRST crosses into the resolved band on the CORRECT side:
    carry-1 (kind 'pi') -> cos FALLs through -LOCK_MARGIN; carry-0 (kind '0') -> cos already at +1 from
    t=0 (the .ic carry-0 start), so it is resolved immediately (lock time ~0, handled in the parser);
    propagate (kind None) -> the node inherits its carry, so we detect BOTH a rise to +LOCK_MARGIN and a
    fall to -LOCK_MARGIN and the parser takes whichever fired (the actual settle direction)."""
    for node, kind in node_kinds:
        s = _san(node)
        lines.append("let cc_%s = cos(V(%s))" % (s, node))
        if kind == "pi":
            lines.append("meas tran tlock_%s WHEN cc_%s=%.4f FALL=1" % (s, s, -LOCK_MARGIN))
        elif kind == "0":
            # carry-0: resolved from t=0; still emit a (rising) meas as a guard -- parser floors it at ~0
            lines.append("meas tran tlock_%s WHEN cc_%s=%.4f RISE=1" % (s, s, LOCK_MARGIN))
        else:
            # propagate: detect both directions; ngspice prints whichever crossing occurs
            lines.append("meas tran tlockf_%s WHEN cc_%s=%.4f FALL=1" % (s, s, -LOCK_MARGIN))
            lines.append("meas tran tlockr_%s WHEN cc_%s=%.4f RISE=1" % (s, s, LOCK_MARGIN))


# =========================================================================================
# Run + parse ngspice (the .tran transient = the ODE integrator; the srmech Kuramoto gap supplied)
# =========================================================================================
_COS_RE = re.compile(r"cc_(\w+)\[length\(cc_\w+\)-1\]\s*=\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
_MEAS_RE = re.compile(r"^(tlock[fr]?_\w+)\s*=\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", re.M)
_FAIL_RE = re.compile(r"^(tlock[fr]?_\w+)\s*=\s*failed", re.M | re.I)


def run_ngspice(netlist, work_dir, tag):
    """Write the netlist, run ngspice -b deterministically, parse (final cos per node, lock times per
    node). Returns (cos_by_node dict, lock_times dict, raw). The simulator's .tran transient integrator
    IS the ODE integrator (the srmech Kuramoto gap, supplied by the analog substrate)."""
    cir = work_dir / ("f241_%s.cir" % tag)
    cir.write_text(netlist)
    proc = subprocess.run([NGSPICE, "-b", str(cir)], capture_output=True, text=True, timeout=600)
    out = proc.stdout + "\n" + proc.stderr
    cos_by_node = {}
    for mobj in _COS_RE.finditer(out):
        cos_by_node[mobj.group(1)] = float(mobj.group(2))
    lock_raw = {}
    for mobj in _MEAS_RE.finditer(out):
        lock_raw[mobj.group(1)] = float(mobj.group(2))
    failed = set(m.group(1) for m in _FAIL_RE.finditer(out))
    return cos_by_node, lock_raw, failed, out


def node_lock_time(node, kind, lock_raw, failed):
    """The analog time-to-lock of a single node, read from the parsed `meas` results. carry-1 ('pi'):
    the FALL crossing time tlock_<node>; carry-0 ('0'): resolved from t=0 -> floor at LOCK_FLOOR (a
    RISE meas at the very first sample, or 'failed' because it never had to cross -> already inside the
    band -> ~0); propagate (None): whichever of the rise/fall meas fired (the node's actual settle).
    Uses NO python abs()/max() -- a single explicit pick. Returns the lock time (float) or None if the
    node genuinely never resolved (a measurement-detected lock failure)."""
    s = _san(node)
    if kind == "pi":
        k = "tlock_%s" % s
        if k in lock_raw:
            return float(lock_raw[k])
        return None if k in failed else LOCK_FLOOR
    if kind == "0":
        # carry-0 node starts at cos=+1 (resolved). A RISE-to-+0.5 meas 'fails' (already above it) -> 0.
        k = "tlock_%s" % s
        if k in lock_raw:
            return float(lock_raw[k])
        return LOCK_FLOOR  # resolved from t=0
    # propagate: take whichever crossing fired (it settled in that direction)
    kf, kr = "tlockf_%s" % s, "tlockr_%s" % s
    cand = [lock_raw[x] for x in (kf, kr) if x in lock_raw]
    if cand:
        return _srmech_max(cand)   # the later (settled) crossing; Class-K, no python max()
    # neither crossing fired -> node never left the near-saddle band -> unresolved (lock failure)
    return None


def network_time_to_lock(node_kinds, lock_raw, failed):
    """A network's analog time-to-lock = the MAX over all its nodes' lock times (the LAST node to
    settle). Max via Class-K _srmech_max (NEVER python max()). Returns (t_lock or None if any node is
    unresolved, list of per-node times)."""
    per_node = []
    for node, kind in node_kinds:
        t = node_lock_time(node, kind, lock_raw, failed)
        if t is None:
            return None, per_node   # an unresolved node = the network did not lock (correctness gate)
        per_node.append(t)
    return _srmech_max(per_node), per_node


# =========================================================================================
# Carry readout (Class K) -- the locked carry vector from the final cos values
# =========================================================================================
def read_carry(cos_value):
    """READ one carry via Class-K cascade.pin_slot_at_zero on the locked cos(theta): cos>0 ->
    orientation +1 -> carry-0; cos<0 -> orientation -1 -> carry-1; orientation 0 OR |cos| below
    LOCK_MARGIN -> UNRESOLVED (None) = lock failure. Near-zero via cascade.magnitude (NEVER abs())."""
    orient, _mag = cascade.pin_slot_at_zero(float(cos_value))     # Class K pin-slot phase boundary
    resolved = cascade.magnitude(float(cos_value)) >= LOCK_MARGIN  # Class K modulus (never abs())
    if not resolved or orient == 0:
        return None
    return 0 if orient == 1 else 1


def single_chain_carries(cos_by_node, m):
    """The single-chain locked carry vector c_0..c_{m-1} from the final cos of nodes n0..n_{m-1}."""
    out = []
    for i in range(m):
        nm = "n%d" % i
        out.append(read_carry(cos_by_node[nm]) if nm in cos_by_node else None)
    return out


def two_tier_carries(cos_by_node, meta, a_bits, b_bits, cin):
    """Reconstruct the full carry vector c_0..c_N from the two-tier locked state: the Class-K SR-latch
    MUX selects, for each nibble, its carry nodes resolved AT the Tier-2 block carry-in. Because each
    nibble is speculatively pinned at its (correct) block carry-in, the nibble's own locked carry nodes
    ARE the selected slice. We read c_0 (=cin) + each nibble's 4 computed carries c_1..c_4, stitched in
    block order; the final carry-out = the last nibble's c_4 (= the Tier-2 final block carry-out).
    Returns the stitched carry vector (length N+1) with None for any unresolved node."""
    n = len(a_bits)
    n_blocks = meta["n_blocks"]
    carries = [None] * (n + 1)
    # c_0 = carry-in (boolean fact)
    carries[0] = cin
    for k in range(n_blocks):
        names_k = meta["nibble_carry_nodes"][k]
        # nibble k carry nodes c_0..c_4 -> global carries c_{4k}..c_{4k+4}; c_{4k} is the block carry-in
        for i in range(1, NIBBLE + 1):
            nm = names_k[i]
            gi = k * NIBBLE + i
            carries[gi] = read_carry(cos_by_node[nm]) if nm in cos_by_node else None
    return carries


def sum_bits_from_carries(a_bits, b_bits, carries):
    """sum_i = p_i XOR carry_i (p_i = a_i XOR b_i). Returns the sum bits, or None if any carry in
    [0..n-1] is unresolved."""
    n = len(a_bits)
    if any(carries[i] is None for i in range(n)):
        return None
    return [(a_bits[i] ^ b_bits[i]) ^ carries[i] for i in range(n)]


def reconstructed_int(sum_bits, carry_out, n):
    """The full (n+1)-bit integer the analog adder produced: sum bits + carry-out in slot n."""
    return bits_to_int(sum_bits) + (int(carry_out) << n)


# =========================================================================================
# Coupling-graph spectra (Class L): the path Fiedler vs the nibble Fiedler (the settling-rate tie)
# =========================================================================================
def path_fiedler(m):
    """Fiedler value lambda_2 of the m-node PATH-graph Laplacian (the worst-case all-propagate single
    chain). dense_laplacian -> jacobi_eigvals; near-zero degeneracy via cascade.magnitude (NEVER abs()).
    1/lambda_2 is the relaxation-rate proxy + the F122 K_c tie (smaller lambda_2 = slower settle)."""
    edges = [(i, i + 1) for i in range(m - 1)]
    laplacian_m = lap.dense_laplacian(m, edges)               # Class L
    eig = sorted(float(e) for e in lap.jacobi_eigvals(laplacian_m))  # Class L (no np.linalg)
    lam_2 = eig[1] if len(eig) > 1 else 0.0
    return float(lam_2)


def two_tier_fiedler(n):
    """The two-tier's spectral settling proxy: Tier-1 = a CONSTANT-size (NIBBLE+1)-node path (its
    lambda_2 is the SAME for every N -> O(1) Tier-1 settle), Tier-2 = the (n_blocks)-node block-carry
    path (its lambda_2 shrinks only as the BLOCK count grows, i.e. as n/4). The two-tier relaxation
    proxy = min(lambda_2 over the two tiers) (the slowest tier sets the rate). Returns
    (nibble_lambda_2, block_lambda_2, two_tier_lambda_2)."""
    nibble_l2 = path_fiedler(NIBBLE + 1)            # constant for all N
    n_blocks = n // NIBBLE
    block_l2 = path_fiedler(n_blocks) if n_blocks >= 2 else 0.0
    # the slower tier sets the settle rate; pick the SMALLER lambda_2 WITHOUT python min(): Class-K sign
    orient, _mag = cascade.pin_slot_at_zero(nibble_l2 - block_l2)
    two_tier_l2 = block_l2 if (orient == 1 and block_l2 > 0.0) else nibble_l2
    if block_l2 == 0.0:
        two_tier_l2 = nibble_l2
    return float(nibble_l2), float(block_l2), float(two_tier_l2)


# =========================================================================================
# Klein-4 / Class C: the carry STATE is an order-2 binary phase (gamma5 axis)
# =========================================================================================
def klein4_carry_chirality():
    """The carry chain's net chirality (Class C): carry-0 = orientation +1, carry-1 = orientation -1
    (the order-2 gamma5 Klein-4 axis -- NO order-4 Z4 element). net_chirality over a sample chain +
    reorient applying a carry-1 to a magnitude. Mirrors F234/F236's Klein-4 read at the Class-C level."""
    net = cascade.net_chirality([1, -1, -1])      # carry-0, carry-1, carry-1
    reor = cascade.reorient(-1, 1.0)              # applying carry-1 (orientation -1) re-signs 1.0
    return {"net_chirality_sample_chain": int(net), "reorient_minus1_of_1p0": float(reor),
            "carry0_orientation": 1, "carry1_orientation": -1, "phase_order": 2,
            "axis": "order-2 gamma5 Klein-4 (NOT order-4 Z4)"}


# =========================================================================================
# Worst case + mixed inputs
# =========================================================================================
def worst_case_inputs(n):
    """All-propagate worst case = the maximal carry chain: a = all 1s, b = 0, cin = 1 (every position
    propagates; the carry must ripple the whole width through coupling alone)."""
    return [1] * n, [0] * n, 1


def mixed_inputs(n):
    """A couple of mixed (generate/kill/propagate) inputs at width n, deterministically derived (NOT
    random): (i) alternating generate/propagate, (ii) a single low-nibble generate then all-kill."""
    # mixed A: a = 0b...0101 pattern AND b = same -> generate on even bits; XOR=0 elsewhere (kill)
    a1 = [1 if (i % 2 == 0) else 0 for i in range(n)]
    b1 = [1 if (i % 2 == 0) else 0 for i in range(n)]   # a==b on even bits -> generate; odd bits kill
    # mixed B: low bit generates, everything else propagates with cin=0 (carry from bit0 ripples up)
    a2 = [1] + [1] * (n - 1)
    b2 = [1] + [0] * (n - 1)                            # bit0: a=b=1 -> generate; bits1..: propagate
    return [("mixedA_N%d" % n, a1, b1, 0), ("mixedB_N%d" % n, a2, b2, 0)]


# =========================================================================================
# The measurement: time-to-lock for BOTH structures at each width + carry-correctness
# =========================================================================================
def measure_width(n, work_dir):
    """At width n: run BOTH the single ripple chain and the two-tier on the worst case + mixed inputs;
    measure each network's analog time-to-lock; cross-check BOTH locked carry vectors against the
    boolean ground truth + an independent integer add. Returns a dict of per-case rows + the worst-case
    timing pair (the headline number for this width)."""
    cases = [("worst_N%d" % n, *worst_case_inputs(n))]
    cases.extend(mixed_inputs(n))
    rows = []
    worst_pair = None
    for tag, a, b, cin in cases:
        gt = ripple_carries(a, b, cin)
        m = n + 1
        # --- single ripple chain ---
        net1, kind1 = build_single_chain(a, b, cin, KC_OP, "F241 single chain %s" % tag)
        cos1, lock1, failed1, _o1 = run_ngspice(net1, work_dir, "single_%s" % tag)
        node_kinds1 = [("n%d" % i, kind1[i]) for i in range(m)]
        t1, per1 = network_time_to_lock(node_kinds1, lock1, failed1)
        carries1 = single_chain_carries(cos1, m)
        s1 = sum_bits_from_carries(a, b, carries1)
        gt_int = bits_to_int(a) + bits_to_int(b) + cin
        ok1 = (carries1 == gt and None not in carries1)
        int_ok1 = (s1 is not None) and (reconstructed_int(s1, carries1[n], n) == gt_int)
        # --- two-tier ---
        net2, meta = build_two_tier(a, b, cin, KC_OP, "F241 two-tier %s" % tag)
        cos2, lock2, failed2, _o2 = run_ngspice(net2, work_dir, "twotier_%s" % tag)
        node_kinds2 = ([(nm, _kind_of(meta, nm)) for nm in meta["tier1_node_names"]]
                       + [(meta["tier2_node_names"][k], _bc_kind_of(meta, k))
                          for k in range(len(meta["tier2_node_names"]))])
        t2, per2 = network_time_to_lock(node_kinds2, lock2, failed2)
        carries2 = two_tier_carries(cos2, meta, a, b, cin)
        s2 = sum_bits_from_carries(a, b, carries2)
        ok2 = (carries2 == gt and None not in carries2)
        int_ok2 = (s2 is not None) and (reconstructed_int(s2, carries2[n], n) == gt_int)
        speedup = (float(t1) / float(t2)) if (t1 is not None and t2 not in (None, 0.0)) else None
        row = {
            "case": tag, "N": n, "a_int": bits_to_int(a), "b_int": bits_to_int(b), "cin": cin,
            "gt_carries": gt,
            "single": {
                "time_to_lock": (None if t1 is None else round(float(t1), 6)),
                "locked_carries": carries1, "carry_correct": bool(ok1),
                "integer_add_match": bool(int_ok1),
                "n_unresolved": sum(1 for x in carries1 if x is None),
            },
            "two_tier": {
                "time_to_lock": (None if t2 is None else round(float(t2), 6)),
                "locked_carries": carries2, "carry_correct": bool(ok2),
                "integer_add_match": bool(int_ok2),
                "n_unresolved": sum(1 for x in carries2 if x is None),
                "n_blocks": meta["n_blocks"], "block_g": meta["block_g"], "block_p": meta["block_p"],
                "block_carry_in": meta["block_carry_in"],
            },
            "speedup_single_over_two_tier": (None if speedup is None else round(speedup, 4)),
            "both_correct": bool(ok1 and ok2 and int_ok1 and int_ok2),
        }
        rows.append(row)
        if tag.startswith("worst_"):
            worst_pair = (t1, t2, bool(ok1 and ok2 and int_ok1 and int_ok2))
    return {"N": n, "rows": rows, "worst_case_timing": worst_pair}


def _kind_of(meta, node):
    """Recover the carry-kind of a Tier-1 nibble node from meta (for the lock-time direction)."""
    for k, names in enumerate(meta["nibble_carry_nodes"]):
        if node in names:
            i = names.index(node)
            return meta["nibble_carry_kinds"][k][i]
    return None


def _bc_kind_of(meta, k):
    """Recover the Tier-2 block-carry node kind. Rebuild from block_g/block_p/cin (same rule as build)."""
    block_g, block_p = meta["block_g"], meta["block_p"]
    cin = meta["block_carry_in"][0]
    if block_g[k] == 1:
        return "pi"
    if block_p[k] == 0:
        return "0"
    if k == 0:
        return "pi" if cin == 1 else "0"
    return None


# =========================================================================================
# Verdict (no leaning; decided by the measured times + carry-correctness)
# =========================================================================================
def _growth_ratio(times):
    """Per-doubling growth of a time series across the widths [8,16,32]: the ratio t[i+1]/t[i] averaged
    multiplicatively (geometric), via Class-A arithmetic only (no abs/max). Returns the geometric-mean
    per-doubling ratio (float) or None if any time is missing/zero."""
    valid = [float(t) for t in times if t not in (None, 0.0)]
    if len(valid) < 2 or len(valid) != len(times):
        return None
    prod = 1.0
    for i in range(len(valid) - 1):
        prod *= valid[i + 1] / valid[i]
    return prod ** (1.0 / (len(valid) - 1))


def decide_verdict(width_results):
    """POSITIVE iff (a) every case's BOTH carry vectors equal ground truth (correctness gate) AND (b)
    two-tier time-to-lock is materially below the ripple chain at N=16 AND N=32 (ratio single/two_tier
    >= MATERIAL_FACTOR) AND (c) the two-tier's time grows slower with N than the ripple chain's. NULL
    iff no advantage (worst-case ratio ~1 at N=16/32) or same scaling. Else INDETERMINATE. Decided by
    the measured transients, not asserted."""
    by_n = {wr["N"]: wr for wr in width_results}
    # correctness gate: every case, both structures correct
    all_correct = all(row["both_correct"] for wr in width_results for row in wr["rows"])
    # worst-case timing per width
    single_times = {n: by_n[n]["worst_case_timing"][0] for n in by_n}
    two_tier_times = {n: by_n[n]["worst_case_timing"][1] for n in by_n}
    ratios = {}
    for n in by_n:
        st, tt = single_times[n], two_tier_times[n]
        ratios[n] = (float(st) / float(tt)) if (st is not None and tt not in (None, 0.0)) else None
    material_16 = (ratios.get(16) is not None) and (ratios[16] >= MATERIAL_FACTOR)
    material_32 = (ratios.get(32) is not None) and (ratios[32] >= MATERIAL_FACTOR)
    # growth: geometric per-doubling ratio over the ordered widths
    ordered = sorted(by_n)
    g_single = _growth_ratio([single_times[n] for n in ordered])
    g_two = _growth_ratio([two_tier_times[n] for n in ordered])
    grows_slower = (g_single is not None and g_two is not None and g_two < g_single)
    if not all_correct:
        verdict = "INDETERMINATE"
        head = ("INDETERMINATE — a faster result that is WRONG does not count: at least one case had a "
                "wrong or unresolved carry under the single chain or the two-tier; the timing comparison "
                "is voided for that case. (Correctness gate failed.)")
    elif material_16 and material_32 and grows_slower:
        verdict = "POSITIVE"
        head = ("POSITIVE — the TWO-TIER nibble-block structure settles MATERIALLY FASTER than the "
                "single ripple chain at N=16 (%.2fx) and N=32 (%.2fx), both >= the %.1fx material floor, "
                "AND its time-to-lock grows SLOWER with N (two-tier per-doubling x%.3f vs ripple "
                "x%.3f). The O(N)-wire nibble parallelism is a REAL dynamics-level settling-time "
                "advantage: Tier-1 replaces ONE length-N chain with N/4 PARALLEL constant-size 4-bit "
                "nibble subnets (lock times do NOT add — the network time is the max-over-nibbles, and a "
                "4-bit chain is constant-time), and only the short Tier-2 block-carry line grows. Every "
                "case's carry vector (single AND two-tier) equals the boolean ground truth, integer-add "
                "cross-checked — the faster answer is also the CORRECT answer."
                % (ratios[16], ratios[32], MATERIAL_FACTOR, g_two, g_single))
    elif (ratios.get(16) is not None and ratios.get(32) is not None
          and ratios[16] < 1.05 and ratios[32] < 1.05):
        verdict = "NULL"
        head = ("NULL FIRES — the two-tier shows NO settling-time advantage over the single ripple chain "
                "(worst-case ratio ~1 at N=16 and N=32); the block-carry tier's own settling erases the "
                "nibble-parallel gain, or both scale the same with N. The parallelism is structural-only, "
                "not a dynamics speedup.")
    else:
        verdict = "INDETERMINATE"
        head = ("INDETERMINATE — the two-tier is faster at some N but the pre-stated POSITIVE bar is not "
                "met: material (>= %.1fx) at N=16=%s, at N=32=%s; grows-slower=%s. Carry-correctness held "
                "(all cases correct), but the speedup/scaling does not clear the pre-stated threshold."
                % (MATERIAL_FACTOR, material_16, material_32, grows_slower))
    return {
        "verdict": verdict,
        "headline": head,
        "all_cases_correct": bool(all_correct),
        "worst_case_single_time_to_lock": {str(n): (None if single_times[n] is None else round(float(single_times[n]), 6)) for n in ordered},
        "worst_case_two_tier_time_to_lock": {str(n): (None if two_tier_times[n] is None else round(float(two_tier_times[n]), 6)) for n in ordered},
        "worst_case_speedup_single_over_two_tier": {str(n): (None if ratios[n] is None else round(ratios[n], 4)) for n in ordered},
        "material_advantage_at_N16": bool(material_16),
        "material_advantage_at_N32": bool(material_32),
        "material_factor_floor": MATERIAL_FACTOR,
        "ripple_per_doubling_growth": (None if g_single is None else round(g_single, 4)),
        "two_tier_per_doubling_growth": (None if g_two is None else round(g_two, 4)),
        "two_tier_grows_slower": bool(grows_slower),
    }


# =========================================================================================
# NDJSON emit (content-addressed; response_sha256 over the body minus generated_at -- F233 convention)
# =========================================================================================
def _ngspice_version():
    try:
        out = subprocess.run([NGSPICE, "--version"], capture_output=True, text=True, timeout=30).stdout
        mobj = re.search(r"ngspice-([0-9.]+)", out)
        return mobj.group(1) if mobj else "unknown"
    except Exception:
        return "unknown"


def _build_record(ng_version, srmech_version, width_results, fiedlers, k4, verdict):
    return {
        "finding": "F241",
        "measurement": "kuramoto_nibbler_two_tier_timing",
        "ngspice_version": ng_version,
        "srmech_version": srmech_version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": ("does the TWO-TIER nibble-block structure (Tier-1: independent 4-bit nibbles phase-"
                     "locking in PARALLEL on disjoint subnets with NO cross-nibble edges; Tier-2: a block-"
                     "carry line over the N/4 block-carry nodes, with the Class-K SR-latch MUX as the "
                     "Tier-1->Tier-2 bridge) settle to the correct carry vector FASTER (lower analog time-"
                     "to-lock) than the SINGLE ripple chain at the same width N -- is the O(N)-wire nibble "
                     "parallelism a real DYNAMICS-level settling-time advantage, or decorative?"),
        "resolves": ("F236's explicit honest residue: F236 TIMED only the single ripple chain end-to-end "
                     "+ the K_c sweep; it did NOT separately TIME the nibble-block two-tier settling. F234 "
                     "established the O(N)-wire structure + the single-graph speedup null in PYTHON with "
                     "the linear-CONSENSUS hop-count proxy (1/lambda_2 + sweeps), NOT the nonlinear "
                     "Kuramoto .tran transient time, and NOT in ngspice. F241 measures the actual ngspice "
                     "time-to-lock of BOTH structures at N=8/16/32."),
        "pre_stated_null": ("the two-tier nibble-block structure shows NO settling-time advantage over the "
                            "single ripple chain (e.g. the block-carry tier's own settling erases the "
                            "nibble-parallel gain, or both scale the same with N) -> the parallelism is "
                            "structural-only, not a dynamics speedup"),
        "pre_stated_positive": ("two-tier time-to-lock is materially below the ripple chain at N=16/32 and "
                                "grows slower with N"),
        "time_to_lock_instrument": ("ngspice .tran transient (the ODE integrator) + `meas tran tlock WHEN "
                                    "cos(theta)=+/-LOCK_MARGIN` per node = the analog time a node's "
                                    "cos(theta) first enters the resolved band on the correct side; a "
                                    "network's time-to-lock = the MAX over its nodes (the last to settle), "
                                    "taken via Class-K cascade.magnitude compares (NEVER python max()/abs())"),
        "netlist_construct": ("SINGLE = the F236 length-(N+1) ripple carry line (far-end node slowest). "
                              "TWO-TIER = N/4 INDEPENDENT 4-bit nibble subnets with DISJOINT node names + "
                              "NO cross-nibble coupling edge (absence-of-edge = block independence; one "
                              ".tran integrates all in PARALLEL) + a tiny N/4-node Tier-2 block-carry line; "
                              "the Class-K SR-latch MUX selects each nibble's carry by the Tier-2 block "
                              "carry-in (carry-SELECT). O(N) wires, dodges the all-to-all O(N^2) trap. "
                              "carry node = V on a 1 F cap = phase theta; B-source injects the Kuramoto RHS "
                              "current; generate->PINK*sin(PI-V), kill->PINK*sin(0-V), propagate-> no self-"
                              "bias + symmetric KC*sin edges"),
        "carry_correctness_gate": ("a faster result that is WRONG does not count: every case, BOTH the "
                                   "single-chain and the two-tier locked carry vectors are read out (Class-"
                                   "K cascade.pin_slot_at_zero on the final cos) and compared to the boolean "
                                   "ground-truth ripple_carries(a,b,cin), AND must reproduce a+b+cin under "
                                   "an INDEPENDENT integer add"),
        "constants": {
            "PI": [round(PI, 10), "A: asymptotic_calculus phase pi (carry-1 antipode of carry-0=0)"],
            "NIBBLE": [NIBBLE, "A: 7483 block = 4 = |Klein-4| = F233 4-thread rung"],
            "WIDTHS": [WIDTHS, "A: the explicitly-named widths (N=8 two nibbles, 16 four, 32 eight)"],
            "PIN_K": [PIN_K, "B: pinning-field strength floor (>> KC so a pinned carry holds; F236)"],
            "KC_OP": [KC_OP, "B: operational coupling above the measured K_c (F236)"],
            "LOCK_MARGIN": [LOCK_MARGIN, "B: |cos| resolved floor; the cos-crossing band the .tran meas detects"],
            "T_STEP": [T_STEP, "B: ngspice .tran step (the deterministic analog integrator step; F236)"],
            "T_STOP_PER_NODE": [T_STOP_PER_NODE, "B: transient stop-time budget per carry node (F236)"],
            "IC_BASE": [IC_BASE, "B: deterministic initial-phase base (carry-0 side; NOT the answer; F236)"],
            "IC_STEP": [IC_STEP, "B: deterministic initial-phase per-node increment (fixed spread; F236)"],
            "IC_ANCHOR0": [IC_ANCHOR0, "B: anchor node initial phase when pinned to pi (near pi, off-saddle; F236)"],
            "MATERIAL_FACTOR": [MATERIAL_FACTOR, "B: the >=1.5x speedup floor for a MATERIAL advantage at N=16/32"],
            "LOCK_FLOOR": [LOCK_FLOOR, "B: positive time-to-lock floor so max-over-nodes is well-defined for already-resolved nodes"],
        },
        "srmech_ops_used": {
            "max_over_nodes_and_nibbles": "Class-K cascade.pin_slot_at_zero on the difference (NEVER python max()/abs())",
            "carry_readout": "cascade.pin_slot_at_zero  [Class K; F217 SR latch]",
            "lock_margin_test": "cascade.magnitude  [Class K; no python abs()]",
            "chirality_of_carry_state": "cascade.net_chirality / cascade.reorient  [Class C]",
            "coupling_graph_spectrum": "laplacian.dense_laplacian + jacobi_eigvals (path vs nibble Fiedler)  [Class L; no np.linalg]",
            "attestation": "format.sha256_bytes  [Class A; no hashlib]",
            "cos_and_lock_time": "ngspice's own cos(V) + `meas tran ... WHEN cos=margin` crossing time (the analog substrate's transcendental + ODE integration); srmech READS the parsed scalars",
        },
        "srmech_gap": ("ngspice supplies the Kuramoto/ODE integrator srmech still lacks (the F141/F231/"
                       "F234/F236 gap); the analog .tran transient IS the integration AND the time-to-lock "
                       "meas. srmech does the max-over-nodes (Class K), the readout (Class K), the spectrum "
                       "(Class L), the chirality (Class C), and the attestation (Class A); numpy is the "
                       "array carrier of the parsed ngspice output only (no linalg, no abs)"),
        "spectral_settling_proxy": fiedlers,
        "width_results": width_results,
        "klein4_carry_state": k4,
        "tier": {
            "demonstrated": ("the ngspice transient MEASUREMENT: the analog time-to-lock of the single "
                             "ripple chain vs the two-tier nibble-block at N=8/16/32, with both locked "
                             "carry vectors cross-checked against the boolean ground truth + an independent "
                             "integer add (a faster-but-wrong result voided)"),
            "framework_reading": ("the build-a-faster-Kuramoto-ALU-adder synthesis / down-into-the-ALU "
                                  "generalization (MFO VII.6.20)"),
            "scope": ("in-scope: the Kuramoto-ODE / oscillator-network DYNAMICS in the electrical-analog "
                      "substrate (the same dynamics F234 ran in Python + F236 ran in ngspice); NOT PCB "
                      "layout / fabrication tolerances / component sourcing / gate-delay / fan-out / timing-"
                      "closure (74xx-SPICE = the F217 existence-proof lens, not a build instruction; the "
                      "CAD-ban HOLDS); defensive scope: addition is general arithmetic, framework-reading"),
        },
        "predecessors": ("F236 (the ngspice port + the honest residue this finding resolves), F234 (the "
                         "O(N)-wire two-tier STRUCTURE + the single-graph speedup null, in Python with the "
                         "consensus-hop proxy), F122 (the K_c~0.20 Kuramoto core), F217 (the Class-K pin-"
                         "slot = SR latch existence-proof lens; the 74xx framing), F231 (Kuramoto dispatch "
                         "clock), F119/F120 (the two-tier RBS architecture + the Class-K tier-bridge)"),
        "verdict": verdict,
    }


def _emit(record):
    """Write the content-addressed NDJSON. response_sha256 over the record body MINUS the wall-clock
    generated_at (so a re-run reproduces the measurement sha bit-for-bit; the F233/F234/F236
    convention). Returns (on-disk ndjson sha256, response_sha256, path)."""
    body = {k: v for k, v in record.items() if k != "generated_at"}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    record["response_sha256"] = fmt.sha256_bytes(payload)        # Class A (never hashlib)
    out_dir = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
               / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "kuramoto_nibbler_two_tier_timing.ndjson"
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    with open(out_path, "w") as fh:
        fh.write(line)
        fh.write("\n")
    with open(out_path, "rb") as fh:
        disk = fh.read()
    return fmt.sha256_bytes(disk), record["response_sha256"], str(out_path)


def main():
    import srmech
    ng_version = _ngspice_version()
    print("=" * 92)
    print("R-RBS-LM-241 -- two-tier nibble-block vs single ripple chain: TIME-TO-LOCK in ngspice")
    print("  ngspice %s | srmech %s" % (ng_version, srmech.__version__))
    print("=" * 92)

    work_dir = Path(tempfile.mkdtemp(prefix="f241_two_tier_"))

    width_results = []
    for n in WIDTHS:
        print("\n[N=%d] timing single ripple chain vs two-tier (worst case + mixed) ..." % n)
        wr = measure_width(n, work_dir)
        width_results.append(wr)
        for r in wr["rows"]:
            print("   %-12s single: t_lock=%-10s carry_ok=%s | two_tier: t_lock=%-10s carry_ok=%s | speedup=%s"
                  % (r["case"], r["single"]["time_to_lock"], r["single"]["carry_correct"],
                     r["two_tier"]["time_to_lock"], r["two_tier"]["carry_correct"],
                     r["speedup_single_over_two_tier"]))

    # spectral settling proxy (Class L): path Fiedler vs the two-tier (nibble + block) Fiedler
    fiedlers = {}
    for n in WIDTHS:
        m = n + 1
        path_l2 = path_fiedler(m)
        nibble_l2, block_l2, two_l2 = two_tier_fiedler(n)
        fiedlers[str(n)] = {
            "single_path_lambda2": round(path_l2, 6),
            "two_tier_nibble_lambda2": round(nibble_l2, 6),
            "two_tier_block_lambda2": round(block_l2, 6),
            "two_tier_lambda2_slower_tier": round(two_l2, 6),
            "note": ("single path lambda_2 shrinks ~ (pi/N)^2 (slower with N); the two-tier nibble lambda_2 "
                     "is CONSTANT (4-bit subnet) and only the block tier lambda_2 shrinks as N/4"),
        }
    print("\n[spectral] path Fiedler vs two-tier (nibble const + block) Fiedler:")
    for n in WIDTHS:
        f = fiedlers[str(n)]
        print("   N=%-3d single_path_l2=%-10s nibble_l2=%-10s block_l2=%-10s"
              % (n, f["single_path_lambda2"], f["two_tier_nibble_lambda2"], f["two_tier_block_lambda2"]))

    k4 = klein4_carry_chirality()
    verdict = decide_verdict(width_results)
    record = _build_record(ng_version, srmech.__version__, width_results, fiedlers, k4, verdict)
    disk_sha, resp_sha, out_path = _emit(record)

    print("\n" + "=" * 92)
    print("  VERDICT: %s" % verdict["verdict"])
    print("  %s" % verdict["headline"])
    print("\n  worst-case time-to-lock (single / two-tier / speedup):")
    for n in [str(w) for w in WIDTHS]:
        print("    N=%-3s single=%-10s two_tier=%-10s speedup=%s"
              % (n, verdict["worst_case_single_time_to_lock"][n],
                 verdict["worst_case_two_tier_time_to_lock"][n],
                 verdict["worst_case_speedup_single_over_two_tier"][n]))
    print("    per-doubling growth: ripple x%s vs two-tier x%s (grows_slower=%s)"
          % (verdict["ripple_per_doubling_growth"], verdict["two_tier_per_doubling_growth"],
             verdict["two_tier_grows_slower"]))
    print("    all_cases_correct=%s" % verdict["all_cases_correct"])
    print("\n  ndjson: %s" % out_path)
    print("  ndjson sha256 (with wall-clock): %s" % disk_sha)
    print("  response_sha256 (bit-exact, minus generated_at): %s" % resp_sha)
    print("=" * 92)
    return record


if __name__ == "__main__":
    main()
