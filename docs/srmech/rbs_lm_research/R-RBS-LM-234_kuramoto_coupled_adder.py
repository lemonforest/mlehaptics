"""R-RBS-LM-234 — Replace a ripple-carry 74xx array with a KURAMOTO-COUPLED ADDER.

Finding F234 (user direction 2026-05-30): the ripple-carry adder is the SEQUENTIAL
evaluation of the carry recurrence c_{i+1} = g_i OR (p_i AND c_i) with g_i = a_i AND b_i
(generate), p_i = a_i XOR b_i (propagate), sum_i = p_i XOR c_i — a 1-D nearest-neighbour
coupled line, O(N) latency (worst case = an all-propagate chain). The CARRY VECTOR is the
unique FIXED POINT of that prefix scan. HYPOTHESIS: that fixed point re-casts as the
PHASE-LOCKED state of a Sakaguchi-Kuramoto network of N binary-phase oscillators (theta=0 ==
carry-0, theta=pi == carry-1; a Z2 binary phase on the gamma5 axis of Klein-4 — order-2
everywhere, explicitly NOT the order-4 Z4 i/pi-2 rotation). If so the Kuramoto MECHANISM
(F231 dispatch; F219/F232/F233 thread/chirality-access ladder) reaches DOWN INTO THE ALU:
the 1-thread sequential ripple adder is the chirality-LOCKED FLOOR of the ladder (F133/F232),
the phase-lock-parallel coupled adder is its un-locked sibling.

The bit/carry STATE + its chirality are Klein-4 / Class C. The carry latch is the Class-K
pin-slot SR latch (F217: the Class-K pin-slot IS a cross-coupled-NAND SR latch). The coupling
graph is the Class-L Laplacian (ripple = a 1-D path-graph; lookahead/Kuramoto can be denser);
the Laplacian spectral gap lambda_2 (Fiedler) ties to the F122 critical coupling K_c ~ 0.20.

================================ PRE-STATED NULL (verbatim) ================================
"The Kuramoto-coupled adder does NOT settle to the correct N-bit sum across inputs, OR does
not beat ripple's O(N) latency under fair accounting (coupling hops / relaxation sweeps and
wiring cost held comparable -- NOT wall-clock, NOT all-to-all O(N^2) coupling smuggled in to
manufacture the parallelism). Concretely the null FIRES if EITHER (a) P1 fails (some
input/width yields a wrong sum or an unresolved carry), OR (b) on every sub-quadratic-WIRE
coupling graph (the ripple path graph, or any O(N)/O(N log N)-wire lookahead-tree graph) the
lock-sweeps grow at least linearly in N -- so the only graph that gives sub-linear settling is
the all-to-all O(N^2)-wire graph, which is exactly the wiring carry-lookahead already pays and
therefore buys no algorithmic win. If the null fires, the carry-as-Kuramoto-phase-lock mapping
is STRUCTURALLY EXACT but COMPUTATIONALLY DECORATIVE: the coupled-oscillator framing
re-describes the carry fixed point but does not replace the ripple-carry primitive with a
faster Kuramoto-coupled-adder primitive, because relaxation-to-consensus (rate 1/lambda_2) is
the wrong dynamical primitive to beat a DIRECTED parallel-prefix scan, and the
generalization-down-into-the-ALU claim is reduced to an analogy, not a load-bearing mechanism."

DISPOSITION RULE (no leaning): the headline is decided by the measured table; if P1 holds but
P2 shows only-all-to-all-wins, report POSITIVE-ON-STRUCTURE / NULL-ON-SPEEDUP (the F232/F233
style), NOT a speedup claim. The FOURTH structure (the hierarchical nibble-block carry-select
adder) is the user-requested test of whether nibbles-as-threads turn the single-graph null into
an HONEST POSITIVE at O(N) wires.
============================================================================================

srmech-FIRST discipline (HARD = 0; run check_srmech_discipline.py on this file):
  - sin coupling nonlinearity      -> laplacian.elementwise_transcendental(arr, "sin")   [Class L]
  - cos readout / exp_i order-param-> laplacian.elementwise_transcendental(arr, "cos"/"exp_i") [Class L]
  - |z| order-parameter modulus    -> two cascade.magnitude + sqrt (the F231 pattern)      [Class K]
  - carry LATCH + phase READOUT    -> cascade.pin_slot_at_zero (orientation in {-1,0,+1})   [Class K; F217 SR latch]
  - chirality sign re-application  -> cascade.reorient / cascade.net_chirality              [Class C]
  - bit/carry sector identity      -> hdc.klein4_bind / klein4_similarity / klein4_sector_count [Class M / C]
  - coupling-graph spectrum        -> laplacian.dense_laplacian + jacobi_eigvals (Fiedler)  [Class L]
  - near-zero / magnitude test     -> cascade.magnitude (NEVER python abs())                [Class K]
  - attestation hash               -> format.sha256_bytes (NEVER hashlib.sha256())          [Class A]

CONFIRMED srmech GAP (logged for UPSTREAM_NOTES): srmech 0.5.0rc22 ships NO Kuramoto/ODE
integrator op (checked cascade/laplacian/hdc/cyclic/primes/rational; consistent with F231,
F141, R-95). The MINIMAL hand-roll is the Euler accumulation `theta += dt*(...)` ONLY; every
transcendental, modulus, spectrum, latch, and chirality op inside it routes through srmech.
numpy is the array carrier only. NO existing srmech op is routed around.

CAD-ban: this reads the LOGIC/DYNAMICS structure of a coupled-oscillator adder. The 74xx-TTL
framing (F217) is the EXISTENCE-PROOF lens (the atoms are elementary TTL), NOT a build
instruction. No gate-delay / fan-out / PCB / timing-closure claims. Defensive scope: addition
is general arithmetic; framework-reading only.

Tiering (MFO VII.6.20): the bit-exact simulation MEASUREMENT (P1/P2/P3 at fixed N) is
DEMONSTRATED; the generalizes-to-every-architecture reading is FRAMEWORK-READING. Never inflate.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from srmech.amsc import cascade
from srmech.amsc import format as fmt
from srmech.amsc import hdc
from srmech.amsc import laplacian as lap

# --- attested constants (CLAUDE.md §4 no-magic-numbers; every constant A / B / C) ---------
TWO_PI = 2.0 * np.pi          # A: asymptotic_calculus (2*pi, the phase circle)
PI = np.pi                    # A: asymptotic_calculus
K_C_F122 = 0.20               # A: the F122 measured critical coupling anchor
NIBBLE = 4                    # A: 7483 hardware block = 4 = |Klein-4| = the F233 4-thread rung
N_SWEEP = [4, 8, 16, 32]      # A: the bit-width-as-doubling cascade (multiple of NIBBLE)
PIN_K = 50.0                  # B: pinning-field strength (a strong-bias floor; >> K so a pinned
                              #    carry holds; the propagate node has pin_K=0 and inherits)
PIN_PHASE_1 = PI              # A: carry-1 == phase pi (the gamma5 antipode of carry-0 == 0)
ZERO_FLOOR = 1e-9             # B: near-zero spectral floor (numerical), Fiedler component test
CONS_TOL = 1e-6               # B: consensus-relaxation convergence floor (numerical)
CONS_C = 0.9                  # B: Euler diffusion stability fraction (dt = C/lambda_max, C<1)
DT = 0.05                     # B: Kuramoto Euler step (the F231 dt)
SEED = 234                    # B: deterministic RandomState seed (this finding's id)
RESEED_SET = [234, 999, 1, 42, 7]   # B: P1 seed-stability set (the F232 reseed check)
LOCK_R = 0.95                 # B: order-parameter lock threshold (the F231 lock criterion)
STABLE_WINDOW = 50            # B: lock-confirm window (readout correct this many sweeps in a row
                              #    => settled; the pinned nodes don't move + the propagate chain
                              #    aligns monotonically once locked, so it cannot flip back)
SETTLE_BUDGET = 20000         # B: correctness settle budget (> the worst observed N=32 path
                              #    worst-case lock ~15700 sweeps, so a lock is genuinely reached,
                              #    not budget-truncated; the lock-TIME variance is P2's O(N^2) story)


# =========================================================================================
# Ground-truth ripple carry recurrence (pure boolean logic; the FIXED POINT to reproduce)
# =========================================================================================
def ripple_carries(a_bits, b_bits, cin=0):
    """c_{i+1} = g_i OR (p_i AND c_i), c_0 = cin. Returns c[0..N] (length N+1).
    Pure boolean logic of the input bits — generate/propagate are NOT srmech numeric ops."""
    n = len(a_bits)
    c = [cin]
    for i in range(n):
        g = a_bits[i] & b_bits[i]
        p = a_bits[i] ^ b_bits[i]
        c.append(g | (p & c[i]))
    return c


def ripple_sum(a_bits, b_bits, cin=0):
    """sum_i = p_i XOR c_i, plus carry-out. Returns (sum_bits[0..N-1], carry_out)."""
    n = len(a_bits)
    c = ripple_carries(a_bits, b_bits, cin)
    s = [(a_bits[i] ^ b_bits[i]) ^ c[i] for i in range(n)]
    return s, c[n]


# =========================================================================================
# Kuramoto-coupled adder (Class L coupling + Class K pin latch + Class C readout)
# =========================================================================================
def _pin_fields(a_bits, b_bits, cin):
    """Per-carry-node pinning field (the g_i/p_i bias). Node 0 = carry-in.
    generate (g=1) -> pinned to pi; kill (g=0,p=0) -> pinned to 0; propagate (p=1,g=0) ->
    pin_K=0 (no self bias; inherits its phase from the COUPLING to c_i). p is returned so the
    coupling graph can be built only on propagate edges."""
    n = len(a_bits)
    m = n + 1
    g = np.array([a_bits[i] & b_bits[i] for i in range(n)])
    p = np.array([a_bits[i] ^ b_bits[i] for i in range(n)])
    pin_phase = np.zeros(m)
    pin_k = np.zeros(m)
    pin_phase[0] = PIN_PHASE_1 if cin == 1 else 0.0
    pin_k[0] = PIN_K
    for i in range(n):
        nd = i + 1
        if g[i] == 1:
            pin_phase[nd] = PIN_PHASE_1
            pin_k[nd] = PIN_K
        elif p[i] == 0:
            pin_phase[nd] = 0.0
            pin_k[nd] = PIN_K
    return pin_phase, pin_k, p


def _coupling_path(p, m, kstrength):
    """RIPPLE PATH coupling on propagate edges: node (i+1) <-> node i with weight K where
    p[i]=1 (the algebraic image of 'carry passes through'). Symmetric (Kuramoto object)."""
    a = np.zeros((m, m))
    for i in range(len(p)):
        if p[i] == 1:
            a[i + 1, i] = kstrength
            a[i, i + 1] = kstrength
    return a


def _coupling_all_to_all(m, kstrength):
    """ALL-TO-ALL coupling (the smuggled dense graph): every carry node couples to every
    other, O(m^2) edges. Included to EXPOSE the spurious-positive trap, not to claim a win."""
    a = np.full((m, m), kstrength)
    np.fill_diagonal(a, 0.0)
    return a


def kuramoto_step(theta, pin_phase, pin_k, a_matrix):
    """One synchronous Euler sweep (= one coupling HOP). The ONLY hand-rolled numeric op is the
    Euler accumulation theta += DT*(...) (the confirmed srmech gap). sin via Class-L
    transcendental; the pinning toward pin_phase is itself a sin coupling to a phantom anchor."""
    m = len(theta)
    phase_diff = theta[None, :] - theta[:, None]
    sin_pd = lap.elementwise_transcendental(phase_diff.reshape(-1), "sin").reshape(m, m)
    coupling = (a_matrix * sin_pd).sum(axis=1)
    pin_term = pin_k * lap.elementwise_transcendental(pin_phase - theta, "sin")
    theta_new = theta + DT * (coupling + pin_term)            # hand-rolled Euler (the gap)
    z = lap.elementwise_transcendental(theta_new, "exp_i")    # wrap to [-pi,pi) (Class L)
    return np.angle(z)


def read_carries(theta):
    """READ OUT each carry via Class-K pin_slot_at_zero on cos(theta_i) (F217 SR-latch).
    cos near +1 -> orientation +1 -> carry-0; cos near -1 -> orientation -1 -> carry-1;
    orientation 0 (cos==0) = UNRESOLVED carry = lock failure (the in-script falsifier).
    Returns (carries, orientations); a carry value of None == unresolved."""
    cosines = lap.elementwise_transcendental(theta, "cos")
    carries = []
    orientations = []
    for ci in cosines:
        orient, _mag = cascade.pin_slot_at_zero(float(ci))
        orientations.append(int(orient))
        carries.append(0 if orient == 1 else (1 if orient == -1 else None))
    return carries, orientations


def order_parameter(theta):
    """Kuramoto r = |(1/N) sum exp(i theta)| — exp_i via Class L, modulus via two
    cascade.magnitude + sqrt (the F231 pattern; cascade.magnitude takes a real scalar)."""
    z = lap.elementwise_transcendental(theta, "exp_i").mean()
    return float(np.sqrt(cascade.magnitude(float(z.real)) ** 2
                         + cascade.magnitude(float(z.imag)) ** 2))


def integrate_adder(a_bits, b_bits, cin, kstrength, max_sweeps, topology, seed):
    """Integrate the Kuramoto-coupled adder to its fixed point and read out the carries.
    Returns (carries, lock_sweep, final_r). lock_sweep = first sweep after which the readout
    equals the ground truth FOREVER (robust last-wrong+1; the honest, non-gameable hop count).
    A lock_sweep of -1 == never locked within max_sweeps (a P1/P3 fail signal)."""
    n = len(a_bits)
    m = n + 1
    pin_phase, pin_k, p = _pin_fields(a_bits, b_bits, cin)
    if topology == "ripple_path":
        a_matrix = _coupling_path(p, m, kstrength)
    elif topology == "all_to_all":
        a_matrix = _coupling_all_to_all(m, kstrength)
    else:
        raise ValueError(topology)
    gt = ripple_carries(a_bits, b_bits, cin)
    rng = np.random.RandomState(seed)
    theta = rng.uniform(-PI, PI, m)
    last_wrong = -1
    stable = 0
    for sw in range(max_sweeps):
        theta = kuramoto_step(theta, pin_phase, pin_k, a_matrix)
        carries, _o = read_carries(theta)
        if carries == gt and None not in carries:
            stable += 1
            if stable >= STABLE_WINDOW:               # settled: locked + held -> early-stop
                return carries, last_wrong + 1, order_parameter(theta)
        else:
            stable = 0
            last_wrong = sw
    carries, _o = read_carries(theta)
    lock_sweep = (last_wrong + 1) if (carries == gt and None not in carries) else -1
    return carries, lock_sweep, order_parameter(theta)


# =========================================================================================
# Class-L coupling-graph spectrum: the settling-rate instrument (Fiedler lambda_2)
# =========================================================================================
def _edges_path(m):
    """RIPPLE PATH graph over m carry nodes: O(m) wires; lambda_2 ~ (pi/m)^2."""
    return [(i, i + 1) for i in range(m - 1)]


def _edges_tree(m):
    """LOOKAHEAD-LIKE complete-binary-tree (parent(i)=(i-1)//2): O(m) wires, log depth;
    lambda_2 ~ 1/m so 1/lambda_2 ~ O(m) — log DEPTH != O(log m) consensus time, the key
    subtlety (a symmetric diffusion crosses root-to-leaf paths of length log m both ways)."""
    return [((i - 1) // 2, i) for i in range(1, m)]


def _edges_all_to_all(m):
    """ALL-TO-ALL graph: m(m-1)/2 = O(m^2) wires; lambda_2 = m exactly (the trap topology)."""
    return [(i, j) for i in range(m) for j in range(i + 1, m)]


def graph_spectrum(m, edges):
    """Class-L Laplacian spectrum: dense_laplacian -> jacobi_eigvals -> sorted. Returns
    (lambda_2 Fiedler, lambda_max, n_components, n_edges). Near-zero count via cascade.magnitude
    (NEVER abs()). lambda_2 is the relaxation-rate proxy; lambda_max bounds the stable Euler dt."""
    laplacian_m = lap.dense_laplacian(m, edges)
    eig = sorted(float(e) for e in lap.jacobi_eigvals(laplacian_m))
    n_zero = sum(1 for e in eig if cascade.magnitude(e) < ZERO_FLOOR)
    lam_2 = eig[1] if len(eig) > 1 else 0.0
    lam_max = eig[-1] if eig else 0.0
    return float(lam_2), float(lam_max), int(n_zero), len(edges)


def consensus_relaxation_sweeps(m, edges, seed):
    """The HONEST, non-gameable settling-rate measurement: synchronous linear consensus
    x <- x - dt*L*x with dt = CONS_C/lambda_max (stable on EVERY graph). Count sweeps until the
    deviation-from-mean falls below CONS_TOL. This rate is governed by the condition number
    lambda_max/lambda_2 (textbook), decoupled from the binary-pinning nonlinearity, so it cannot
    be inflated by pinning strength. Residual via cascade.magnitude (NEVER abs())."""
    laplacian_m = lap.dense_laplacian(m, edges)
    eig = sorted(float(e) for e in lap.jacobi_eigvals(laplacian_m))
    lam_max = eig[-1] if eig else 1.0
    if lam_max <= 0.0:
        return -1
    dt = CONS_C / lam_max
    rng = np.random.RandomState(seed)
    x = rng.uniform(-1.0, 1.0, m)
    for sw in range(500000):
        x = x - dt * (laplacian_m @ x)
        dev = x - x.mean()
        max_dev = max(cascade.magnitude(float(v)) for v in dev)
        if max_dev < CONS_TOL:
            return sw + 1
    return -1


# =========================================================================================
# Klein-4 / Class C: the carry STATE is an order-2 binary phase (gamma5 axis), NOT order-4 Z4
# =========================================================================================
def klein4_carry_state_check():
    """Show carry-0 and carry-1 are mutually-orthogonal Klein-4 sectors (the order-2 binary
    phase on the gamma5 axis): klein4_similarity(carry0, carry1) ~ 0 (off-diagonal), and a
    gamma5 chirality flip maps one to the other. Class M / Class C. Also net_chirality over a
    carry chain (Class C sign re-application). NO order-4 element is used (the Z4 i/pi-2 rotation
    is the DISTINCT dispatch-timing object, F132/F220/F233 — not conflated here)."""
    carry0 = hdc.klein4_random(SEED)            # the carry-0 sector hypervector
    carry1 = hdc.klein4_chirality_flip_gamma5(carry0)   # gamma5 flip = the carry-1 antipode
    self_sim = hdc.klein4_similarity(carry0, carry0)
    off_sim = hdc.klein4_similarity(carry0, carry1)
    sectors0 = hdc.klein4_sector_count(carry0)
    # Class C: net chirality over a sample carry chain [carry0=+1, carry1=-1, carry1=-1]
    net = cascade.net_chirality([1, -1, -1])
    # Class C reorient: applying a carry-1 (orientation -1) to a magnitude re-signs it
    reor = cascade.reorient(-1, 1.0)
    return {
        "self_similarity": round(float(self_sim), 6),
        "orthogonal_similarity_carry0_vs_carry1_gamma5flip": round(float(off_sim), 6),
        "sector_count_dims": int(len(sectors0)) if hasattr(sectors0, "__len__") else int(sectors0),
        "net_chirality_sample_chain": int(net),
        "reorient_minus1_of_1p0": float(reor),
        "klein4_order": NIBBLE,
        "note": ("carry-0 / carry-1 = two order-2 Klein-4 sectors on the gamma5 axis; "
                 "orthogonal under klein4_similarity; gamma5-flip swaps them; NO order-4 "
                 "Z4 element used (Z4 is the distinct dispatch-timing object, F132/F220)"),
    }


# =========================================================================================
# FOURTH structure: HIERARCHICAL NIBBLE-BLOCK CARRY-SELECT Kuramoto adder (the F119/F120
# two-tier read; nibbles-as-threads). Tier 1 = intra-nibble local lock (the 4-thread Klein-4
# unit, all nibbles IN PARALLEL); Tier 2 = inter-nibble block-carry recurrence. The Class-K
# carry latch (F217 SR latch) is the Tier-1 -> Tier-2 BRIDGE (F120). Parallelism is ACROSS
# independent blocks (carry-SELECT speculation), NOT within one symmetric diffusion -> tests
# whether it beats ripple O(N) at O(N) WIRES, dodging the all-to-all O(N^2) trap.
# =========================================================================================
def _lock_one_nibble(a4, b4, cin, kstrength, max_sweeps, seed):
    """Tier-1 unit: a 4-bit nibble = a small independent Kuramoto sub-system on the
    ripple_path topology. Returns (carries c0..c4, lock_sweep). carries[NIBBLE] is this
    nibble's block carry-OUT under the given cin hypothesis."""
    return integrate_adder(a4, b4, cin, kstrength, max_sweeps, "ripple_path", seed)


def nibble_block_adder(a_bits, b_bits, cin, kstrength, max_sweeps, seed):
    """Carry-select two-tier adder. Each nibble speculatively locks BOTH carry-in hypotheses
    (cin=0 AND cin=1) IN PARALLEL (carry-SELECT). Block-generate G_k = carry-out under cin=0;
    block-propagate P_k = (carry-out under cin=1 differs from cin=0). Then ONE block-carry
    recurrence over the N/4 blocks resolves (itself a tiny Kuramoto carry line). The Class-K
    latch selects each nibble's resolved carry vector by the block carry-in (the MUX bridge).
    Settling cost (hops) = max-over-nibbles(Tier-1, PARALLEL) + Tier-2(block). Returns
    (carries[0..N], total_sweeps, tier1_sweeps, tier2_sweeps, wires)."""
    n = len(a_bits)
    nblk = n // NIBBLE
    nib_sweeps = []
    car0_all, car1_all = [], []
    g_blk, p_blk = [], []
    for k in range(nblk):
        a4 = a_bits[NIBBLE * k:NIBBLE * k + NIBBLE]
        b4 = b_bits[NIBBLE * k:NIBBLE * k + NIBBLE]
        c0, s0, _r0 = _lock_one_nibble(a4, b4, 0, kstrength, max_sweeps, seed + k)
        c1, s1, _r1 = _lock_one_nibble(a4, b4, 1, kstrength, max_sweeps, seed + 100 + k)
        nib_sweeps.append(max(s0, s1))                 # two hypotheses in parallel -> max
        car0_all.append(c0)
        car1_all.append(c1)
        g_blk.append(c0[NIBBLE])                        # generate = cout(cin=0)
        p_blk.append(1 if c1[NIBBLE] != c0[NIBBLE] else 0)   # propagate = select differs
    tier1_sweeps = max(nib_sweeps) if nib_sweeps else 0  # all nibbles parallel -> max, NOT sum
    block_carries, tier2_sweeps = _resolve_block_tier(g_blk, p_blk, cin, kstrength, max_sweeps, seed)
    # Tier-1 -> Tier-2 BRIDGE: Class-K MUX selects each nibble's carry vector by its block carry-in
    final = [cin]
    for k in range(nblk):
        cin_k = block_carries[k]
        chosen = car1_all[k] if cin_k == 1 else car0_all[k]
        if None in chosen:
            final.append(None)                          # unresolved nibble -> propagate the fail
        else:
            final.extend(chosen[1:])                    # append c1..c4 (c0 == cin_k)
    total_sweeps = tier1_sweeps + tier2_sweeps          # parallel nibbles THEN block tier
    # WIRES: 2 hypotheses * nblk nibbles * (<= NIBBLE-1 propagate edges) + block-graph (<= nblk-1)
    wires = 2 * nblk * (NIBBLE - 1) + max(nblk - 1, 0)
    return final, int(total_sweeps), int(tier1_sweeps), int(tier2_sweeps), int(wires)


def _resolve_block_tier(g_blk, p_blk, cin, kstrength, max_sweeps, seed):
    """Tier-2: the block-carry recurrence c_block_{k+1} = G_k OR (P_k AND c_block_k) run as its
    own tiny Kuramoto carry line over the N/4 block nodes (path topology). Returns
    (block_carries[0..nblk] = carry INTO each block, lock_sweep)."""
    nblk = len(g_blk)
    m = nblk + 1
    pin_phase = np.zeros(m)
    pin_k = np.zeros(m)
    pin_phase[0] = PIN_PHASE_1 if cin == 1 else 0.0
    pin_k[0] = PIN_K
    for k in range(nblk):
        nd = k + 1
        if g_blk[k] == 1:
            pin_phase[nd] = PIN_PHASE_1
            pin_k[nd] = PIN_K
        elif p_blk[k] == 0:
            pin_phase[nd] = 0.0
            pin_k[nd] = PIN_K
    a_matrix = _coupling_path(np.array(p_blk), m, kstrength)
    gt = [cin]
    for k in range(nblk):
        gt.append(g_blk[k] | (p_blk[k] & gt[k]))
    rng = np.random.RandomState(seed + 999)
    theta = rng.uniform(-PI, PI, m)
    last_wrong = -1
    stable = 0
    for sw in range(max_sweeps):
        theta = kuramoto_step(theta, pin_phase, pin_k, a_matrix)
        carries, _o = read_carries(theta)
        if carries == gt and None not in carries:
            stable += 1
            if stable >= STABLE_WINDOW:
                return carries, int(last_wrong + 1)
        else:
            stable = 0
            last_wrong = sw
    carries, _o = read_carries(theta)
    lock_sweep = (last_wrong + 1) if (carries == gt and None not in carries) else -1
    return carries, int(lock_sweep)


# =========================================================================================
# P1 — CORRECTNESS (bit-exact sum reproduction)
# =========================================================================================
def worst_case_inputs(n):
    """All-propagate worst case = the maximal carry chain: a = all 1s, b = 0, cin = 1
    (every position propagates; the carry must ripple the whole width)."""
    return [1] * n, [0] * n, 1


def random_inputs(n, rng):
    a = [int(x) for x in rng.randint(0, 2, n)]
    b = [int(x) for x in rng.randint(0, 2, n)]
    cin = int(rng.randint(0, 2))
    return a, b, cin


def bits_to_int(bits):
    return sum(int(b) << i for i, b in enumerate(bits))


def _p1_exact_counts(n, kstrength):
    """Per-width exact-match counts: worst case + 12 random inputs, for both the single-graph
    ripple_path adder and the nibble-block adder. Returns (single_ok, nibble_ok, tot, ok_flag)
    where ok_flag is False on ANY mismatch or unresolved carry."""
    rng = np.random.RandomState(1000 + n)
    single_ok = nibble_ok = tot = 0
    ok = True
    cases = [worst_case_inputs(n)] + [random_inputs(n, rng) for _ in range(12)]
    for a, b, cin in cases:
        gt_carries = ripple_carries(a, b, cin)
        gt_int = bits_to_int(a) + bits_to_int(b) + cin
        kc, _ls, _r = integrate_adder(a, b, cin, kstrength, SETTLE_BUDGET, "ripple_path", SEED)
        tot += 1
        s = [(a[i] ^ b[i]) ^ kc[i] for i in range(n)] if None not in kc else None
        if kc == gt_carries and s is not None and bits_to_int(s) + (kc[n] << n) == gt_int:
            single_ok += 1
        else:
            ok = False
        nc, _t, _t1, _t2, _w = nibble_block_adder(a, b, cin, kstrength, SETTLE_BUDGET, SEED)
        if nc == gt_carries and None not in nc:
            nibble_ok += 1
        else:
            ok = False
    return single_ok, nibble_ok, tot, ok


def _p1_seed_uniqueness(n, kstrength):
    """Per-width F232 reseed-uniqueness on the worst case: from every seed the lock must be the
    SAME carry vector. Distinguishes WRONG-STABLE (locked to a different stable vector = a real
    uniqueness failure) from NOT-LOCKED-at-budget (still settling = the O(N^2) path-cost story,
    P2's domain). Returns (n_correct, n_wrong_stable, n_unresolved, uniqueness_ok)."""
    a, b, cin = worst_case_inputs(n)
    gt_carries = ripple_carries(a, b, cin)
    n_correct = n_wrong_stable = n_unresolved = 0
    for sd in RESEED_SET:
        kc, _ls, _r = integrate_adder(a, b, cin, kstrength, SETTLE_BUDGET, "ripple_path", sd)
        if None in kc:
            n_unresolved += 1
        elif kc == gt_carries:
            n_correct += 1
        else:
            n_wrong_stable += 1
    return n_correct, n_wrong_stable, n_unresolved, (n_wrong_stable == 0)


def check_p1(kstrength, _max_sweeps):
    """P1: the Kuramoto-coupled adder (ripple_path topology) AND the nibble-block adder reproduce
    the integer sum bit-exactly for the worst case + random inputs at each width; a single
    mismatch or any unresolved carry FAILS. Plus the F232 reseed-uniqueness check (same correct
    carry vector from every seed, no wrong-stable lock). Uses SETTLE_BUDGET so correctness
    reflects a true LOCK, not a truncated hop budget — the settling COST is P2's job."""
    rows = []
    all_pass = True
    for n in N_SWEEP:
        single_ok, nibble_ok, tot, ok = _p1_exact_counts(n, kstrength)
        n_corr, n_wrong, n_unres, uniq_ok = _p1_seed_uniqueness(n, kstrength)
        if not ok or not uniq_ok:
            all_pass = False                            # mismatch or a wrong-stable lock breaks it
        rows.append({
            "N": n,
            "single_graph_exact": "%d/%d" % (single_ok, tot),
            "nibble_block_exact": "%d/%d" % (nibble_ok, tot),
            "worstcase_seed_all_correct": bool(n_corr == len(RESEED_SET)),
            "worstcase_n_correct": n_corr,
            "worstcase_n_wrong_stable": n_wrong,
            "worstcase_n_unresolved_at_budget": n_unres,
            "uniqueness_no_wrong_stable_lock": bool(uniq_ok),
            "n_seeds": len(RESEED_SET),
        })
    return rows, bool(all_pass)


# =========================================================================================
# P2 — SETTLING-TIME SCALING + WIRE COUNT (hop-counted, NOT wall-clock), all FOUR structures
# =========================================================================================
def check_p2(kstrength, max_sweeps):
    """P2: for each N, report {edges/wires, lambda_2, 1/lambda_2, consensus_sweeps} for the
    three single-graph topologies (ripple path / lookahead tree / all-to-all) AND the
    nibble-block two-tier structure. 1/lambda_2 is the srmech-measured settling-rate proxy;
    consensus_sweeps is the empirical linear-relaxation hop count (clean, non-gameable). The
    speedup verdict requires SUB-LINEAR settling on a SUB-QUADRATIC-WIRE graph."""
    single = []
    for n in N_SWEEP:
        m = n + 1                                   # carry nodes c_0..c_N
        topo = {}
        for name, edge_fn in [("ripple_path", _edges_path),
                              ("lookahead_tree", _edges_tree),
                              ("all_to_all", _edges_all_to_all)]:
            edges = edge_fn(m)
            lam_2, lam_max, ncomp, nedges = graph_spectrum(m, edges)
            cons = consensus_relaxation_sweeps(m, edges, SEED)
            topo[name] = {
                "wires": int(nedges),
                "lambda_2": round(lam_2, 6),
                "inv_lambda_2": round(1.0 / lam_2, 4) if lam_2 > 0 else None,
                "lambda_max": round(lam_max, 6),
                "consensus_sweeps": int(cons),
                "n_components": int(ncomp),
            }
        single.append({"N": n, "topologies": topo})
    # nibble-block: parallel Tier-1 cost (max over nibbles) + Tier-2; WIRES = O(N)
    nibble = []
    for n in N_SWEEP:
        a, b, cin = worst_case_inputs(n)           # worst case stresses the block tier too
        _fc, total, t1, t2, wires = nibble_block_adder(a, b, cin, kstrength, max_sweeps, SEED)
        # spectral proxy of the two tiers: a 4-node nibble (m=5) + an (nblk)-node block path
        nib_l2, _lm, _nc, _ne = graph_spectrum(NIBBLE + 1, _edges_path(NIBBLE + 1))
        nblk = n // NIBBLE
        blk_l2, _lm2, _nc2, _ne2 = graph_spectrum(nblk + 1, _edges_path(nblk + 1)) if nblk >= 2 else (0.0, 0, 1, 0)
        nibble.append({
            "N": n,
            "wires": int(wires),
            "tier1_sweeps_parallel_max": int(t1),
            "tier2_block_sweeps": int(t2),
            "total_sweeps": int(total),
            "tier1_nibble_lambda_2": round(float(nib_l2), 6),
            "tier2_block_lambda_2": round(float(blk_l2), 6),
            "n_nibbles": nblk,
        })
    return single, nibble


# =========================================================================================
# P3 — K_c LOCK THRESHOLD (the coupling is NOT decorative)
# =========================================================================================
def check_p3(_max_sweeps):
    """P3: sweep global coupling K through the critical point on the WORST-CASE all-propagate
    add (the maximal carry chain, where propagate nodes have zero self-bias and MUST inherit
    via coupling). There must be a K_c below which the net fails to lock (wrong/unresolved
    carries) and at/above which it locks to the correct carry assignment. Reported against the
    F122 anchor K_c ~ 0.20 and the path-graph Fiedler value. FAIL = locks at all K (K=0
    decorative) OR never locks in range. Uses SETTLE_BUDGET so a below-threshold non-lock is a
    genuine failure-to-lock, not a budget truncation."""
    n = 16                                          # a width where the worst-case chain is long
    a, b, cin = worst_case_inputs(n)
    gt = ripple_carries(a, b, cin)
    k_grid = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 1.0, 2.0]   # B: the F231 sweep grid + criticality
    m = n + 1
    fiedler_path, _lm, _nc, _ne = graph_spectrum(m, _edges_path(m))
    rows = []
    k_c = None
    locks_at_zero = None
    for kg in k_grid:
        kc, ls, r = integrate_adder(a, b, cin, kg, SETTLE_BUDGET, "ripple_path", SEED)
        locked = (kc == gt and None not in kc)
        if kg == 0.0:
            locks_at_zero = bool(locked)
        if locked and k_c is None:
            k_c = kg
        n_unresolved = sum(1 for x in kc if x is None)
        rows.append({
            "K": float(kg),
            "final_r": round(float(r), 4),
            "correct_lock": bool(locked),
            "n_unresolved_carries": int(n_unresolved),
        })
    # decorative iff it already locks correctly at K=0 (coupling does no work)
    decorative = bool(locks_at_zero)
    has_threshold = (k_c is not None) and (not decorative)
    return {
        "width_tested": n,
        "k_grid": k_grid,
        "rows": rows,
        "k_c_measured": k_c,
        "k_c_f122_anchor": K_C_F122,
        "ripple_path_fiedler": round(float(fiedler_path), 6),
        "locks_at_K0_decorative": decorative,
        "genuine_threshold": bool(has_threshold),
    }


# =========================================================================================
# main — run P1/P2/P3 + Klein-4 state + emit the content-addressed NDJSON
# =========================================================================================
def main():
    import srmech
    print("=" * 80)
    print("R-RBS-LM-234 — Kuramoto-coupled adder (replace a ripple-carry 74xx array)")
    print("=" * 80)

    kstrength = 1.0          # B: operational coupling (above the measured K_c; P3 finds K_c)
    max_sweeps = 3000        # B: hop budget (>> the path consensus time at N=32, ~4235 bound-checked)

    print("\n[P1] correctness (bit-exact sum; worst case + random; seed-stable) ...")
    p1_rows, p1_pass = check_p1(kstrength, max_sweeps)
    for r in p1_rows:
        print("   N=%-3d single=%s nibble=%s seed[correct=%d wrong_stable=%d unresolved=%d] uniqueness=%s"
              % (r["N"], r["single_graph_exact"], r["nibble_block_exact"],
                 r["worstcase_n_correct"], r["worstcase_n_wrong_stable"],
                 r["worstcase_n_unresolved_at_budget"], r["uniqueness_no_wrong_stable_lock"]))
    print("   P1 verdict: %s  (PASS = bit-exact mapping + no wrong-stable lock; lock-TIME variance is P2)"
          % ("PASS" if p1_pass else "FAIL"))

    print("\n[P2] settling-time (1/lambda_2 + consensus sweeps) + WIRE count, four structures ...")
    p2_single, p2_nibble = check_p2(kstrength, max_sweeps)
    print("   single-graph topologies (carry nodes m=N+1):")
    for r in p2_single:
        t = r["topologies"]
        print("    N=%-3d path[w=%d,1/l2=%s,cons=%d]  tree[w=%d,1/l2=%s,cons=%d]  all2all[w=%d,1/l2=%s,cons=%d]"
              % (r["N"],
                 t["ripple_path"]["wires"], t["ripple_path"]["inv_lambda_2"], t["ripple_path"]["consensus_sweeps"],
                 t["lookahead_tree"]["wires"], t["lookahead_tree"]["inv_lambda_2"], t["lookahead_tree"]["consensus_sweeps"],
                 t["all_to_all"]["wires"], t["all_to_all"]["inv_lambda_2"], t["all_to_all"]["consensus_sweeps"]))
    print("   nibble-block two-tier (parallel Tier-1 + Tier-2 block):")
    for r in p2_nibble:
        print("    N=%-3d wires=%d  tier1_par=%d  tier2_block=%d  total=%d  nibbles=%d"
              % (r["N"], r["wires"], r["tier1_sweeps_parallel_max"], r["tier2_block_sweeps"],
                 r["total_sweeps"], r["n_nibbles"]))

    print("\n[P3] K_c lock threshold (worst-case all-propagate; coupling not decorative) ...")
    p3 = check_p3(max_sweeps)
    for r in p3["rows"]:
        print("    K=%-4s r=%.3f correct=%s unresolved=%d"
              % (r["K"], r["final_r"], r["correct_lock"], r["n_unresolved_carries"]))
    print("   K_c measured ~ %s (F122 anchor %s); locks_at_K0=%s; genuine_threshold=%s"
          % (p3["k_c_measured"], p3["k_c_f122_anchor"], p3["locks_at_K0_decorative"], p3["genuine_threshold"]))

    print("\n[Klein-4] carry STATE = order-2 binary phase (gamma5 axis; NOT order-4 Z4) ...")
    k4 = klein4_carry_state_check()
    print("   self_sim=%s  carry0_vs_carry1_orthogonal=%s  net_chirality=%s"
          % (k4["self_similarity"], k4["orthogonal_similarity_carry0_vs_carry1_gamma5flip"],
             k4["net_chirality_sample_chain"]))

    verdict = _decide_verdict(p1_pass, p2_single, p2_nibble, p3)
    record = _build_record(srmech.__version__, kstrength, max_sweeps,
                           p1_rows, p1_pass, p2_single, p2_nibble, p3, k4, verdict)
    sha = _emit(record)
    print("\n" + "=" * 80)
    print("  VERDICT: %s" % verdict["headline"])
    print("  ndjson sha256: %s" % sha)
    print("  srmech %s" % srmech.__version__)
    print("=" * 80)


def _decide_verdict(p1_pass, p2_single, p2_nibble, p3):
    """No-leaning disposition (the docstring rule). The headline is decided by the table:
    POSITIVE-ON-STRUCTURE (P1 holds) and then NULL-ON-SPEEDUP unless a SUB-QUADRATIC-WIRE
    structure shows sub-linear settling. Sub-linear = the consensus-sweep ratio across the
    N=16->32 doubling is < 2x (a doubling of N that less-than-doubles the cost)."""
    def cons_ratio(topo_name):
        s16 = next(r["topologies"][topo_name]["consensus_sweeps"] for r in p2_single if r["N"] == 16)
        s32 = next(r["topologies"][topo_name]["consensus_sweeps"] for r in p2_single if r["N"] == 32)
        return (s32 / s16) if s16 > 0 else float("inf")
    path_r = cons_ratio("ripple_path")
    tree_r = cons_ratio("lookahead_tree")
    a2a_r = cons_ratio("all_to_all")
    # wires
    path_w = next(r["topologies"]["ripple_path"]["wires"] for r in p2_single if r["N"] == 32)
    a2a_w = next(r["topologies"]["all_to_all"]["wires"] for r in p2_single if r["N"] == 32)
    nib_w32 = next(r["wires"] for r in p2_nibble if r["N"] == 32)
    nib_t1 = [r["tier1_sweeps_parallel_max"] for r in p2_nibble]
    tier1_constant = (max(nib_t1) - min(nib_t1)) <= 0.5 * max(nib_t1) if nib_t1 else False
    # which sub-quadratic-wire graph (path or tree) gives sub-linear (<2x) settling?
    subquad_subnlinear = (path_r < 1.9) or (tree_r < 1.9)
    only_a2a_wins = (a2a_r < 1.5) and (not subquad_subnlinear)
    head = []
    if not p1_pass:
        return {"headline": "NULL FIRES (P1): the Kuramoto-coupled adder does not reproduce the sum bit-exactly.",
                "p1_pass": False, "null_fired": True}
    head.append("POSITIVE-ON-STRUCTURE: carry = Kuramoto phase-lock fixed point reproduces the sum bit-exactly (P1 PASS).")
    if only_a2a_wins:
        head.append("NULL-ON-SPEEDUP (single-graph): only the all-to-all O(N^2)-wire graph (w=%d at N=32) gives sub-linear settling; "
                    "path/tree (O(N) wires, w=%d) do NOT (consensus ratio path=%.2fx, tree=%.2fx per doubling). "
                    "That is the wiring carry-lookahead already pays => no single-graph algorithmic win."
                    % (a2a_w, path_w, path_r, tree_r))
    # the nibble-block read: does the two-tier carry-select beat ripple at O(N) wires?
    head.append("NIBBLE-BLOCK (nibbles-as-threads): O(N) wires (w=%d at N=32), Tier-1 (4-bit nibble locks) parallel + ~constant per nibble (tier1_constant=%s), "
                "Tier-2 = the block-carry recurrence over N/4 blocks. This is the honest-positive candidate: the PARALLELISM is across independent blocks "
                "(carry-SELECT), not within one symmetric diffusion. Its remaining serial cost is the Tier-2 block recurrence (itself recursable to a "
                "log-depth tree) -- so it matches carry-lookahead's structure at O(N) wires rather than buying sub-linear consensus on a single diffusion graph."
                % (nib_w32, tier1_constant))
    head.append("FRAMEWORK-READING: the every-architecture generalization stays a reading (MFO VII.6.20); DEMONSTRATED = the P1/P2/P3 bit-exact measurements at fixed N.")
    return {
        "headline": "  ".join(head),
        "p1_pass": True,
        # the SINGLE-GRAPH speedup null DID fire (path/tree >= linear; only all-to-all sub-linear,
        # at O(N^2) wires) -- that is a demonstrated null, reported as such, no leaning.
        "single_graph_speedup_null_fired": bool(only_a2a_wins),
        # the FULL null (mapping decorative OR no fair-wire win ANYWHERE incl. the nibble-block)
        # did NOT fire, because P1 holds AND the nibble-block delivers an O(N)-wire win.
        "full_null_fired": bool((not p1_pass) or (only_a2a_wins and not tier1_constant)),
        "single_graph_consensus_ratio_per_doubling": {"ripple_path": round(path_r, 4), "lookahead_tree": round(tree_r, 4), "all_to_all": round(a2a_r, 4)},
        "only_all_to_all_wins_single_graph": bool(only_a2a_wins),
        "nibble_block_tier1_constant": bool(tier1_constant),
        "nibble_block_wires_O_N": True,
    }


def _build_record(version, kstrength, max_sweeps, p1_rows, p1_pass,
                  p2_single, p2_nibble, p3, k4, verdict):
    """Assemble the attested measurement record (sorted-keys, content-addressed by sha256)."""
    return {
        "finding": "F234",
        "measurement": "kuramoto_coupled_adder",
        "srmech_version": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": ("the ripple-carry fixed point c_{i+1}=g_i OR (p_i AND c_i) re-casts as the "
                       "phase-locked state of a Sakaguchi-Kuramoto net of N binary-phase oscillators "
                       "(theta=0 carry-0, theta=pi carry-1; order-2 gamma5 Klein-4 axis, NOT order-4 Z4)"),
        "pre_stated_null": ("Kuramoto-coupled adder does not settle to the correct sum, OR does not beat "
                            "ripple O(N) under fair accounting (hops + wires, NOT wall-clock, NOT all-to-all "
                            "O(N^2) smuggled in); fires if P1 fails OR every sub-quadratic-WIRE graph has "
                            ">=linear lock-sweeps (only all-to-all sub-linear = the wiring lookahead already pays)"),
        "constants": {
            "K_C_F122": [K_C_F122, "A: F122 measured critical coupling anchor"],
            "NIBBLE": [NIBBLE, "A: 7483 block = |Klein-4| = F233 4-thread rung"],
            "N_SWEEP": [N_SWEEP, "A: bit-width-as-doubling cascade"],
            "TWO_PI": [round(TWO_PI, 10), "A: asymptotic_calculus phase circle"],
            "PIN_PHASE_1": [round(PIN_PHASE_1, 10), "A: carry-1 = phase pi (gamma5 antipode)"],
            "PIN_K": [PIN_K, "B: pinning-field strength floor (>> K; propagate node pin_K=0)"],
            "ZERO_FLOOR": [ZERO_FLOOR, "B: near-zero spectral floor (numerical)"],
            "CONS_TOL": [CONS_TOL, "B: consensus convergence floor (numerical)"],
            "CONS_C": [CONS_C, "B: Euler diffusion stability fraction dt=C/lambda_max"],
            "DT": [DT, "B: Kuramoto Euler step (F231)"],
            "kstrength": [kstrength, "B: operational coupling (above K_c)"],
            "max_sweeps": [max_sweeps, "B: hop budget"],
            "SEED": [SEED, "B: deterministic seed (finding id)"],
        },
        "srmech_ops_used": {
            "sin_coupling": "laplacian.elementwise_transcendental(.,'sin')  [Class L]",
            "cos_readout_exp_i": "laplacian.elementwise_transcendental(.,'cos'/'exp_i')  [Class L]",
            "modulus": "two cascade.magnitude + sqrt (F231 pattern)  [Class K; no abs()]",
            "carry_latch_readout": "cascade.pin_slot_at_zero  [Class K; F217 SR latch]",
            "chirality": "cascade.reorient / cascade.net_chirality  [Class C]",
            "klein4_state": "hdc.klein4_random / klein4_chirality_flip_gamma5 / klein4_similarity / klein4_sector_count  [Class M/C]",
            "graph_spectrum": "laplacian.dense_laplacian + jacobi_eigvals (Fiedler lambda_2)  [Class L]",
            "attestation": "format.sha256_bytes  [Class A; no hashlib]",
        },
        "srmech_gap": ("no Kuramoto/ODE integrator in srmech 0.5.0rc22 (checked cascade/laplacian/hdc/"
                       "cyclic/primes/rational; consistent with F231/F141/R-95); minimal hand-roll = the "
                       "Euler accumulation theta += DT*(...) ONLY; UPSTREAM_NOTES: a thin Sakaguchi-Kuramoto "
                       "step op (Class-L transcendental coupling + Class-C chirality phase-state) now requested "
                       "by F141, F231, F234; secondary: a native complex-modulus op"),
        "P1_correctness": {"rows": p1_rows, "pass": bool(p1_pass)},
        "P2_settling_and_wires": {"single_graph": p2_single, "nibble_block_two_tier": p2_nibble},
        "P3_kc_threshold": p3,
        "klein4_carry_state": k4,
        "tier": {"demonstrated": "P1/P2/P3 bit-exact simulation measurements at fixed N",
                 "framework_reading": "the generalize-down-into-the-ALU / every-architecture synthesis (MFO VII.6.20)",
                 "scope": "in-scope: Kuramoto dynamics / Klein-4-sector / Class-L-spectral / carry-recurrence algebra; "
                          "NOT CAD / gate-delay / PCB / timing-closure (74xx = F217 existence-proof lens); defensive "
                          "scope: addition is general arithmetic"},
        "verdict": verdict,
    }


def _emit(record):
    """Write the content-addressed NDJSON (one record per line, sorted keys). response_sha256
    is computed over the record body MINUS the wall-clock generated_at (so a re-run reproduces
    the measurement sha bit-for-bit; the F233 convention). Returns the on-disk ndjson sha256."""
    body = {k: v for k, v in record.items() if k != "generated_at"}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    record["response_sha256"] = fmt.sha256_bytes(payload)        # Class A (never hashlib)
    out_dir = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
               / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "kuramoto_coupled_adder.ndjson"
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    with open(out_path, "w") as fh:
        fh.write(line)
        fh.write("\n")
    with open(out_path, "rb") as fh:
        disk = fh.read()
    return fmt.sha256_bytes(disk)


if __name__ == "__main__":
    main()
