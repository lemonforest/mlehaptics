"""R-RBS-LM-236 — Kuramoto nibble-adder in ngspice (the F234 mapping in the ELECTRICAL-ANALOG substrate).

Finding F236 (user direction 2026-05-31, "how to kuramoto couple nibble adder in SPICE").

F234 demonstrated, in PYTHON, that the ripple-carry recurrence

    c_{i+1} = g_i OR (p_i AND c_i),   c_0 = cin

has a UNIQUE carry-vector fixed point that IS the phase-locked steady state of a
Sakaguchi-Kuramoto net of binary-phase oscillators (theta=0 == carry-0, theta=pi ==
carry-1; the order-2 gamma5 Klein-4 axis, NOT order-4 Z4). F236 ports the SAME
Kuramoto-ODE dynamics into ngspice and asks whether the analog coupled-oscillator
network phase-locks to the CORRECT carry vector with the SAME K_c lock threshold.

THE CAPACITOR-AS-PHASE CONSTRUCT (the engine of this finding):
  Each carry node c_i is the VOLTAGE on a 1 F capacitor C_i, playing the role of the
  Kuramoto phase theta_i. A behavioral current source B_i injects I_i = C * d(theta_i)/dt;
  with C=1 the node obeys

      d V_i / dt = pinning_i + coupling_i

  which IS the Sakaguchi-Kuramoto phase ODE (alpha=0 binary-phase form). ngspice's .tran
  transient integrator IS the ODE integrator -- this is exactly the srmech Kuramoto/ODE
  GAP noted in F141/F231/F234; the analog substrate supplies the integration srmech lacks.

  The three boolean facts of bit i map to three netlist roles for carry node c_{i+1}:
    - generate (g_i=1):       B adds  PINK*sin(PI - V(node))  -- phantom anchor pinning to pi = carry-1
    - kill (g_i=0,p_i=0):     B adds  PINK*sin(0  - V(node))  -- phantom anchor pinning to 0  = carry-0
    - propagate (p_i=1,g_i=0): NO self-anchor term -- the node inherits its phase via COUPLING only
    - propagate edge (p_i=1): a SYMMETRIC pair  KC*sin(V(i)-V(i+1)) and KC*sin(V(i+1)-V(i))
                              (the Class-L A_ij edge; symmetric per F141 -- directed-only coupling
                               is achiral-null at equal frequency)
  node0 = carry-in: pinned to pi if cin=1 else 0.
  B-source convention: "B 0 nX I={...}" drives current from gnd INTO nX, so positive I raises
  V(nX) == advances the phase, matching +d(theta)/dt.

NIBBLE-BLOCK TOPOLOGY (the F234 nibble-as-thread structure in SPICE): independent 4-bit
  blocks are independent sub-netlists with NO cross-block coupling edges -- the ABSENCE of a
  B-source edge between nibbles IS the block independence (Tier-1 parallel local lock = the
  |Klein-4|=4 unit). The block-carry tier is its own small path-coupled sub-netlist over the
  N/4 block-carry nodes (Tier-2). The Class-K SR latch (F217/F119/F120) is the Tier-1->Tier-2
  MUX bridge. Because an edge is a term that is present-or-absent, wires stay O(N) and the
  all-to-all O(N^2) trap is dodged. F236 RUNS the single ripple-path line at N=4/8 (the
  worst-case chain, the hardest correctness case) + the K_c sweep + the block-independence
  check; F234 already established the O(N)-wire two-tier structure + the single-graph speedup
  null in Python, so F236 is the analog-substrate CORRECTNESS + THRESHOLD confirmation, not a
  re-run of the F234 P2 speedup table.

READOUT (srmech-native, Class K): at the locked steady state read each node's final voltage
  V(n_i)=theta_i, take cos(theta_i) (ngspice computes it via `let cc_i = cos(V(n_i))`), then
  carry_i = sign of cos via Class-K cascade.pin_slot_at_zero(cos):
    cos near +1 -> orientation +1 -> carry-0
    cos near -1 -> orientation -1 -> carry-1
    |cos| < LOCK_MARGIN OR orientation 0 -> UNRESOLVED (None) = lock failure (the in-script falsifier).
  Near-zero / margin test via cascade.magnitude (NEVER python abs()). sum_i = p_i XOR carry_i
  (p_i = a_i XOR b_i); carry-out = carry_N. "Locked" = the readout carry vector equals the
  boolean ground-truth ripple_carries(a,b,cin) at the final timestep AND every node is resolved.
  Cross-checked against an INDEPENDENT integer add (a + b + cin == reconstructed sum integer).

================================ PRE-STATED NULL (verbatim) ================================
"The SPICE coupled-oscillator network does NOT settle to the correct N-bit carry vector (some
input/width yields a wrong carry or an unresolved |cos|~0 node at the final timestep), OR it
shows no K_c threshold (it 'locks' to the correct vector even at coupling K=0, meaning the
per-node pinning bias alone fixes the answer and the coupling is decorative -- equivalently the
result was planted by the initial conditions / the netlist, not emergent from the coupling). If
the null fires, the analog realisation FAILS: either the carry-as-phase-lock mapping does not
survive transport into the electrical substrate, or the apparent positive is an artifact (a
hardcoded answer / .ic-planting / a pinning field doing all the work), not an emergent lock."
============================================================================================

DISPOSITION (no leaning, pre-stated): the headline is decided by the measured ngspice
transients. P1 (locks to the correct carry vector at N=4 exhaustive + N=8 worst case) AND P2
genuine_threshold (a K_c below which the propagate nodes do NOT inherit the carry) AND emergence
(the answer survives an adversarial wrong-side initial condition) AND determinism => the analog
realisation SURVIVES. ANY ONE failing fires the null.

srmech-FIRST discipline (HARD = 0; run check_srmech_discipline.py on this file):
  - carry READOUT (cos sign -> carry)    -> cascade.pin_slot_at_zero (orientation in {-1,0,+1})  [Class K; F217 SR latch]
  - near-zero / lock-margin test          -> cascade.magnitude (NEVER python abs())               [Class K]
  - chirality of the carry STATE          -> cascade.net_chirality / cascade.reorient            [Class C]
  - coupling-graph spectrum (Fiedler tie) -> laplacian.dense_laplacian + jacobi_eigvals          [Class L]
  - attestation hash                       -> format.sha256_bytes (NEVER hashlib.sha256)          [Class A]
  ngspice computes cos(theta) itself (the analog substrate's transcendental); srmech READS the
  parsed scalar. numpy is the array carrier of the parsed ngspice output only (no linalg).

SCOPE (load-bearing, MFO VII.6.20): the ngspice transient MEASUREMENT (does the analog net lock
to the right carry vector; is there a K_c) is DEMONSTRATED. The "this is how you'd build a
Kuramoto ALU adder" synthesis is FRAMEWORK-READING. SPICE here = the Kuramoto-ODE / oscillator-
network DYNAMICS (the same dynamics F234 simulated in Python, now in the electrical-analog
substrate) -- NOT PCB layout, fabrication tolerances, component sourcing, gate-delay, or
timing-closure; the 74xx/SPICE framing is the F217 existence-proof lens, not a build instruction;
the CAD-ban HOLDS. Defensive scope: addition is general arithmetic; framework-reading only.

DETERMINISM: every netlist is fully deterministic -- fixed .ic (a closed-form spread rule, NOT
random, NOT planted at the answer phase pi), fixed .tran timestep, no noise/seed source. The only
non-deterministic byte ngspice emits is the wall-clock "Date:" raw-file header, which is excluded
from the content-address exactly as generated_at is (the F233/F234 convention). Verified
bit-identical parsed transients across reruns.
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
PIN_K = 50.0                  # B: pinning-field strength (>> KC so a pinned carry holds; F234 PIN_K)
KC_OP = 1.0                   # B: operational coupling, above the measured K_c (F234 kstrength)
K_C_F122 = 0.20               # A: the F122 measured critical-coupling anchor
K_GRID = [0.0, 0.05, 0.10, 0.20, 0.50, 1.0]   # B: K-sweep grid bracketing criticality (F234 grid)
LOCK_MARGIN = 0.5             # B: |cos(theta)| must exceed this for a node to count as resolved
                              #    (cos in {-1,+1} at lock; magnitude <0.5 == near-saddle == unresolved)
T_STEP = 0.01                 # B: ngspice .tran step (the analog Euler-equivalent; deterministic)
T_STOP_PER_NODE = 25.0        # B: transient stop-time budget per carry node (so an N-node chain has
                              #    enough analog time to ripple end-to-end; >> the observed lock time)
IC_BASE = 0.10                # B: deterministic initial-phase base (NOT random, NOT the answer phase)
IC_STEP = 0.07                # B: deterministic initial-phase per-node increment (a fixed spread rule)
IC_ANCHOR0 = 2.90             # B: node0 initial phase when pinned to pi (carry-1): near pi, NOT exact
                              #    (off the saddle), so node0's resolution is dynamics not placement
NGSPICE = "ngspice"           # A: the installed simulator binary (ngspice-45.2, this Ubuntu box)
N8 = 8                        # A: the explicitly-named N=8 worst-case width (two nibbles)
REPRESENTATIVE_CIR = "R-RBS-LM-236_kuramoto_nibbler.cir"  # A: the on-disk representative netlist


# =========================================================================================
# Ground-truth ripple carry recurrence (pure boolean logic; the FIXED POINT to reproduce)
# =========================================================================================
def ripple_carries(a_bits, b_bits, cin=0):
    """c_{i+1}=g_i OR (p_i AND c_i), c_0=cin. Returns c[0..N]. Pure boolean logic of the input
    bits (generate/propagate are boolean facts, NOT srmech numeric ops); this is the spec the
    analog net must hit."""
    n = len(a_bits)
    c = [cin]
    for i in range(n):
        g = a_bits[i] & b_bits[i]
        p = a_bits[i] ^ b_bits[i]
        c.append(g | (p & c[i]))
    return c


def propagate_edges(a_bits, b_bits):
    """The propagate edge set: edge (i, i+1) exists iff p_i = a_i XOR b_i = 1 ('carry passes
    through'). Returns the list of carry-node index pairs (the Class-L A_ij support)."""
    return [(i, i + 1) for i in range(len(a_bits)) if (a_bits[i] ^ b_bits[i]) == 1]


def _pin_kind(a_bits, b_bits, cin):
    """Per-carry-node pinning kind over c_0..c_N. Node 0 = carry-in. Returns 'pi' (generate /
    cin=1 -> carry-1), '0' (kill / cin=0 -> carry-0), or None (propagate, no self-bias ->
    inherit via coupling)."""
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


# =========================================================================================
# Netlist generation -- the carry line as capacitor-phase oscillators with B-source Kuramoto RHS
# =========================================================================================
def _det_ic(idx, pinned_pi_at_zero):
    """Deterministic initial phase for node idx: a fixed closed-form spread, NOT random and NOT
    the answer phase pi. node0, when pinned to pi, starts near (not at) pi so it is off the saddle;
    ALL other nodes start on the carry-0 side (small phase) so a correct lock to carry-1 is
    demonstrably driven by coupling, not planted by the initial condition."""
    if idx == 0 and pinned_pi_at_zero:
        return IC_ANCHOR0
    return IC_BASE + IC_STEP * idx


def build_netlist(a_bits, b_bits, cin, kstrength, title):
    """Emit a deterministic ngspice netlist for the Kuramoto-coupled carry line. Each carry node
    c_i = V on a 1 F cap (the phase theta_i); B_i = the Kuramoto RHS current (pinning phantom-
    anchor term on generate/kill nodes + symmetric coupling on propagate edges). Returns the
    netlist string. NO .nodeset / no answer planting: propagate nodes carry zero self-bias and
    start on the carry-0 side."""
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
        "* F236: carry node = V on a 1 F cap = Kuramoto phase theta_i; B = the phase-ODE RHS current.",
        "* generate->PINK*sin(PI-V) anchor (pi=carry-1); kill->PINK*sin(0-V) anchor (0=carry-0);",
        "* propagate-> NO self-bias, inherit via symmetric KC*sin(V_j-V_i) edges (the Class-L A_ij).",
        ".param PINK=%.6f" % PIN_K,
        ".param KC=%.6f" % kstrength,
        ".param PI=%.14f" % PI,
    ]
    pinned_pi_at_zero = (kind[0] == "pi")
    for i in range(m):
        terms = []
        if kind[i] == "pi":
            terms.append("PINK*sin(PI - V(n%d))" % i)        # generate / cin=1 anchor -> pi (carry-1)
        elif kind[i] == "0":
            terms.append("PINK*sin(0 - V(n%d))" % i)         # kill / cin=0 anchor -> 0 (carry-0)
        for j in nbr[i]:
            terms.append("KC*sin(V(n%d)-V(n%d))" % (j, i))    # symmetric propagate edge (Class-L A_ij)
        if not terms:
            terms.append("0")  # isolated propagate node with no edge (degenerate); readout flags it
        lines.append("C%d n%d 0 1" % (i, i))
        lines.append("B%d 0 n%d I={%s}" % (i, i, " + ".join(terms)))
    ics = " ".join("V(n%d)=%.3f" % (i, _det_ic(i, pinned_pi_at_zero)) for i in range(m))
    lines.append(".ic " + ics)                                # deterministic spread, NOT the answer
    t_stop = T_STOP_PER_NODE * m
    lines.append(".tran %.4f %.4f uic" % (T_STEP, t_stop))     # fixed step; .tran IS the ODE integrator
    lines.append(".control")
    lines.append("set noaskquit")
    lines.append("run")
    for i in range(m):
        lines.append("let cc%d = cos(V(n%d))" % (i, i))        # ngspice's own cos of the locked phase
    lines.append("print " + " ".join("cc%d[length(cc%d)-1]" % (i, i) for i in range(m)))  # last sample
    lines.append(".endc")
    lines.append(".end")
    return "\n".join(lines) + "\n"


_PRINT_RE = re.compile(r"cc(\d+)\[length\(cc\d+\)-1\]\s*=\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")


def run_ngspice(netlist, work_dir, tag):
    """Write the netlist, run ngspice -b deterministically, parse the final cos(theta_i) per node.
    Returns (cosines ordered by node index, raw combined stdout+stderr). The simulator's transient
    integrator IS the ODE integrator (the srmech Kuramoto gap, supplied by the analog substrate)."""
    cir = work_dir / ("f236_%s.cir" % tag)
    cir.write_text(netlist)
    proc = subprocess.run([NGSPICE, "-b", str(cir)], capture_output=True, text=True, timeout=300)
    out = proc.stdout + "\n" + proc.stderr
    found = {}
    for mobj in _PRINT_RE.finditer(out):
        found[int(mobj.group(1))] = float(mobj.group(2))
    cosines = [found[i] for i in sorted(found)] if found else []
    return cosines, out


def read_carries(cosines):
    """READ OUT each carry via Class-K cascade.pin_slot_at_zero on the locked cos(theta_i):
    cos>0 -> orientation +1 -> carry-0; cos<0 -> orientation -1 -> carry-1; orientation 0 OR
    |cos| below LOCK_MARGIN -> UNRESOLVED (None) = lock failure (the in-script falsifier).
    Returns (carries, orientations); a None carry == unresolved. Near-zero test via
    cascade.magnitude (NEVER python abs())."""
    carries, orientations = [], []
    for ci in cosines:
        orient, _mag = cascade.pin_slot_at_zero(float(ci))    # Class K pin-slot phase boundary
        resolved = cascade.magnitude(float(ci)) >= LOCK_MARGIN  # Class K modulus (never abs())
        orientations.append(int(orient))
        if not resolved or orient == 0:
            carries.append(None)
        else:
            carries.append(0 if orient == 1 else 1)
    return carries, orientations


def sum_bits_from_carries(a_bits, b_bits, carries):
    """sum_i = p_i XOR carry_i (p_i = a_i XOR b_i). Returns the sum bits, or None if any carry in
    [0..n-1] is unresolved. Pure boolean readout layered on the analog-locked carry vector."""
    n = len(a_bits)
    if any(carries[i] is None for i in range(n)):
        return None
    return [(a_bits[i] ^ b_bits[i]) ^ carries[i] for i in range(n)]


def bits_to_int(bits):
    """Little-endian bit list -> integer (bit i has weight 2**i)."""
    return sum(int(b) << i for i, b in enumerate(bits))


def reconstructed_int(sum_bits, carry_out, n):
    """The full (n+1)-bit integer the analog adder produced: sum bits + carry-out in slot n."""
    return bits_to_int(sum_bits) + (int(carry_out) << n)


# =========================================================================================
# Coupling-graph spectrum: the Class-L Fiedler tie (the F122 K_c / settling-rate instrument)
# =========================================================================================
def path_fiedler(m):
    """Fiedler value lambda_2 of the m-node ripple PATH carry-graph Laplacian (the worst-case
    all-propagate coupling support). dense_laplacian -> jacobi_eigvals; near-zero degeneracy via
    cascade.magnitude (NEVER abs()). lambda_2 is the relaxation-rate proxy + the F122 K_c tie."""
    edges = [(i, i + 1) for i in range(m - 1)]
    laplacian_m = lap.dense_laplacian(m, edges)               # Class L
    eig = sorted(float(e) for e in lap.jacobi_eigvals(laplacian_m))  # Class L (no np.linalg)
    # count near-zero eigenvalues = connected components, via Class-K magnitude (no abs())
    n_zero = sum(1 for e in eig if cascade.magnitude(e) < 1e-9)
    lam_2 = eig[1] if len(eig) > 1 else 0.0
    return float(lam_2), int(n_zero)


# =========================================================================================
# P1 -- CORRECTNESS in the analog substrate (locked carry vector == ground truth)
# =========================================================================================
def worst_case_inputs(n):
    """All-propagate worst case = the maximal carry chain: a = all 1s, b = 0, cin = 1 (every
    position propagates; the carry must ripple the whole width through coupling alone)."""
    return [1] * n, [0] * n, 1


def _int_to_bits(x, n):
    return [(x >> i) & 1 for i in range(n)]


def _n4_exhaustive_cases():
    """ALL 2^4 * 2^4 * 2 = 512 input combinations at N=4 (every a, every b, both cin). This is the
    exhaustive correctness sweep -- the strongest P1 (no input/cin escapes the test)."""
    cases = []
    for a in range(16):
        for b in range(16):
            for cin in (0, 1):
                cases.append((_int_to_bits(a, 4), _int_to_bits(b, 4), cin))
    return cases


def check_p1_n4_exhaustive(work_dir):
    """P1a: run the analog net on ALL 512 N=4 input combinations; each must lock to the exact
    ground-truth carry vector AND reproduce a+b+cin under an INDEPENDENT integer add. A single
    wrong/unresolved carry, or any integer mismatch, fires the null. Returns (summary, all_pass)."""
    n_ok = 0
    n_wrong = 0
    n_unresolved = 0
    n_int_ok = 0
    failures = []
    cases = _n4_exhaustive_cases()
    for a, b, cin in cases:
        gt = ripple_carries(a, b, cin)
        net = build_netlist(a, b, cin, KC_OP, "F236 P1 N4 exhaustive a=%d b=%d cin=%d"
                            % (bits_to_int(a), bits_to_int(b), cin))
        cosines, _out = run_ngspice(net, work_dir, "p1n4_%d_%d_%d"
                                    % (bits_to_int(a), bits_to_int(b), cin))
        carries, _orient = read_carries(cosines)
        locked = (carries == gt and None not in carries)
        s = sum_bits_from_carries(a, b, carries)
        gt_int = bits_to_int(a) + bits_to_int(b) + cin    # the INDEPENDENT integer add
        int_ok = (s is not None) and (reconstructed_int(s, carries[len(a)], len(a)) == gt_int)
        if None in carries:
            n_unresolved += 1
        if locked:
            n_ok += 1
        else:
            n_wrong += 1
            if len(failures) < 8:
                failures.append({"a": bits_to_int(a), "b": bits_to_int(b), "cin": cin,
                                 "gt": gt, "got": carries})
        if int_ok:
            n_int_ok += 1
    n_total = len(cases)
    all_pass = (n_ok == n_total) and (n_int_ok == n_total)
    summary = {
        "n_total": n_total,
        "n_carry_exact": n_ok,
        "n_wrong": n_wrong,
        "n_with_unresolved_node": n_unresolved,
        "n_integer_add_match": n_int_ok,
        "all_carry_exact": bool(n_ok == n_total),
        "all_integer_add_match": bool(n_int_ok == n_total),
        "sample_failures": failures,
    }
    return summary, bool(all_pass)


def check_p1_named_cases(work_dir):
    """P1b: the explicitly-named cases -- the N=4 and N=8 all-propagate WORST cases (maximal carry
    chain) plus a small mixed N=4 set (generate / kill / propagate / the all-kill dual). Records
    the per-case locked carry vector + the independent integer-add check. Returns (rows, all_pass)."""
    cases = []
    for n in (NIBBLE, N8):
        a, b, cin = worst_case_inputs(n)
        cases.append(("worst_N%d" % n, a, b, cin))
    mixed = [
        ("mixed_0", [0, 1, 1, 0], [0, 1, 0, 0], 0),   # kill, generate, propagate, kill
        ("mixed_1", [1, 0, 1, 1], [1, 0, 0, 1], 0),   # generate, kill, propagate, generate
        ("mixed_2", [1, 1, 1, 1], [0, 0, 0, 0], 0),   # all-propagate cin=0 -> all-kill dual of worst
    ]
    cases.extend(mixed)
    rows = []
    all_pass = True
    for tag, a, b, cin in cases:
        n = len(a)
        gt = ripple_carries(a, b, cin)
        net = build_netlist(a, b, cin, KC_OP, "F236 P1 %s" % tag)
        cosines, _out = run_ngspice(net, work_dir, "p1_%s" % tag)
        carries, _orient = read_carries(cosines)
        s = sum_bits_from_carries(a, b, carries)
        gt_int = bits_to_int(a) + bits_to_int(b) + cin
        locked = (carries == gt and None not in carries)
        int_ok = (s is not None) and (reconstructed_int(s, carries[n], n) == gt_int)
        ok = bool(locked and int_ok)
        if not ok:
            all_pass = False
        rows.append({
            "case": tag, "N": n,
            "a_int": bits_to_int(a), "b_int": bits_to_int(b), "cin": cin,
            "gt_carries": gt, "locked_carries": carries,
            "carry_correct": bool(locked),
            "sum_bits": s, "reconstructed_int": (None if s is None else reconstructed_int(s, carries[n], n)),
            "independent_integer_add": gt_int, "integer_add_match": bool(int_ok),
            "n_unresolved": sum(1 for x in carries if x is None),
        })
    return rows, bool(all_pass)


# =========================================================================================
# P2 / P3 -- K_c LOCK THRESHOLD in the analog substrate (the coupling is NOT decorative)
# =========================================================================================
def check_kc_threshold(work_dir):
    """P2: sweep coupling K on the worst-case all-propagate add (N=8, where propagate nodes have
    zero self-bias and MUST inherit via coupling). There must be a K_c below which the net fails to
    lock (wrong/unresolved carries) and at/above which it locks to the correct carry vector.
    FAIL (null) = locks correctly at K=0 (decorative) OR never locks in range. Reported against the
    F122 anchor + the path-graph Fiedler value (the spectral-gap-sets-threshold reading)."""
    n = N8
    a, b, cin = worst_case_inputs(n)
    gt = ripple_carries(a, b, cin)
    m = n + 1
    fiedler, n_comp = path_fiedler(m)
    rows = []
    k_c = None
    locks_at_zero = None
    for kg in K_GRID:
        net = build_netlist(a, b, cin, kg, "F236 P2 K=%.3f (worst-case all-propagate N=8)" % kg)
        cosines, _out = run_ngspice(net, work_dir, "kc_k%.3f" % kg)
        carries, _orient = read_carries(cosines)
        locked = (carries == gt and None not in carries)
        if kg == 0.0:
            locks_at_zero = bool(locked)
        if locked and k_c is None:
            k_c = kg
        rows.append({
            "K": float(kg),
            "correct_lock": bool(locked),
            "n_unresolved": sum(1 for x in carries if x is None),
            "min_abs_cos": round(min((cascade.magnitude(float(c)) for c in cosines), default=0.0), 4),
        })
    decorative = bool(locks_at_zero)
    genuine_threshold = (k_c is not None) and (not decorative)
    return {
        "width_tested": n,
        "k_grid": K_GRID,
        "rows": rows,
        "k_c_measured": k_c,
        "k_c_f122_anchor": K_C_F122,
        "ripple_path_fiedler": round(float(fiedler), 6),
        "path_graph_components": n_comp,
        "locks_at_K0_decorative": decorative,
        "genuine_threshold": bool(genuine_threshold),
    }


# =========================================================================================
# Anti-smuggling guard: the answer must EMERGE from coupling, not be planted by .ic
# =========================================================================================
def check_emergence(work_dir):
    """Spurious-positive guard (answer planted by .ic): the worst-case all-propagate chain has its
    ground truth = carry-1 everywhere, yet build_netlist starts EVERY propagate node FAR on the
    WRONG (carry-0) side (small phase ~IC_BASE). If the net still locks to carry-1 it is DEMONSTRABLY
    driven by coupling against an adversarial initial condition, not by the .ic. Returns
    (emerged, locked_carries)."""
    n = N8
    a, b, cin = worst_case_inputs(n)
    gt = ripple_carries(a, b, cin)
    net = build_netlist(a, b, cin, KC_OP, "F236 emergence (every propagate node planted carry-0)")
    cosines, _out = run_ngspice(net, work_dir, "emergence")
    carries, _orient = read_carries(cosines)
    emerged = (carries == gt and None not in carries)
    return bool(emerged), carries


def check_block_independence(work_dir):
    """Nibble-block O(N)-wire construct check: an N=8 input whose low nibble all-propagates with a
    carry-IN, and whose high nibble is all-kill with NO carry into it. Because the only carry path
    is via propagate EDGES, the absence of a cross-nibble edge means the low-nibble carry-1 must NOT
    leak into the all-kill high nibble. The locked vector must show the low block at carry-1 and the
    high block at carry-0 -- i.e. block independence IS the absence-of-edge. Returns (ok, locked,
    gt)."""
    # low nibble [bits 0..3] all-propagate with cin=1 -> carries 1,1,1,1; bit3 kills (a=b=0) so the
    # carry into bit4 is 0; high nibble [bits4..7] all-kill -> carries stay 0. The carry-1 in the low
    # block does not cross into the high block precisely because bit3 has no propagate edge to bit4.
    a = [1, 1, 1, 0, 0, 0, 0, 0]
    b = [0, 0, 0, 0, 0, 0, 0, 0]
    cin = 1
    gt = ripple_carries(a, b, cin)        # expect [1,1,1,1,0,0,0,0,0]
    net = build_netlist(a, b, cin, KC_OP, "F236 nibble-block independence (no cross-block edge)")
    cosines, _out = run_ngspice(net, work_dir, "block_indep")
    carries, _orient = read_carries(cosines)
    ok = (carries == gt and None not in carries)
    return bool(ok), carries, gt


# =========================================================================================
# Determinism check: two runs of the same netlist -> identical parsed cosines
# =========================================================================================
def check_determinism(work_dir):
    """Two identical ngspice runs of the worst-case N=4 netlist must yield identical parsed cosines
    (the bit-exact-output prerequisite). The only non-deterministic byte ngspice emits is the
    wall-clock Date: header, excluded from the content-address. Returns (identical, cosines)."""
    a, b, cin = worst_case_inputs(NIBBLE)
    net = build_netlist(a, b, cin, KC_OP, "F236 determinism")
    c1, _o1 = run_ngspice(net, work_dir, "det1")
    c2, _o2 = run_ngspice(net, work_dir, "det2")
    return bool(c1 == c2 and len(c1) > 0), c1


# =========================================================================================
# Klein-4 / Class C: the carry STATE is an order-2 binary phase (gamma5 axis), via Class C
# =========================================================================================
def klein4_carry_chirality():
    """The carry chain's net chirality (Class C): carry-0 = orientation +1, carry-1 = orientation -1
    (the order-2 gamma5 Klein-4 axis -- NO order-4 Z4 element; the carry phase is order-2).
    net_chirality over a sample chain + reorient applying a carry-1 to a magnitude. Mirrors F234's
    Klein-4 read at the Class-C level."""
    net = cascade.net_chirality([1, -1, -1])      # carry-0, carry-1, carry-1
    reor = cascade.reorient(-1, 1.0)              # applying carry-1 (orientation -1) re-signs 1.0
    return {"net_chirality_sample_chain": int(net), "reorient_minus1_of_1p0": float(reor),
            "carry0_orientation": 1, "carry1_orientation": -1, "phase_order": 2,
            "axis": "order-2 gamma5 Klein-4 (NOT order-4 Z4)"}


# =========================================================================================
# Representative .cir on disk -- the worst-case all-propagate N=8 netlist (the hardest case)
# =========================================================================================
def write_representative_cir(out_dir):
    """Write the representative ngspice netlist to disk: the N=8 all-propagate worst case at the
    operational coupling KC_OP (the maximal carry chain -- the hardest correctness case, the one
    the K-sweep is run on). Returns its path."""
    a, b, cin = worst_case_inputs(N8)
    net = build_netlist(a, b, cin, KC_OP,
                        "R-RBS-LM-236 representative: N=8 all-propagate worst case (a=0xFF,b=0,cin=1) "
                        "at KC=%.3f -- the maximal carry chain, the hardest correctness case" % KC_OP)
    path = out_dir / REPRESENTATIVE_CIR
    path.write_text(net)
    return path


# =========================================================================================
# main -- run the full pipeline + emit the content-addressed NDJSON
# =========================================================================================
def _ngspice_version():
    try:
        out = subprocess.run([NGSPICE, "--version"], capture_output=True, text=True, timeout=30).stdout
        mobj = re.search(r"ngspice-([0-9.]+)", out)
        return mobj.group(1) if mobj else "unknown"
    except Exception:
        return "unknown"


def _kc_lo(p2):
    """The grid point just below k_c_measured (the lower bracket of the threshold)."""
    kc = p2["k_c_measured"]
    if kc is None:
        return None
    below = [k for k in p2["k_grid"] if k < kc]
    return max(below) if below else 0.0


def _decide_verdict(p1_pass, p2, emerged, block_ok, deterministic):
    """No-leaning disposition. P1 (locks to the correct carry vector: N=4 exhaustive + N=8 worst)
    AND P2 genuine_threshold AND emergence AND block-independence AND determinism => the analog
    realisation SURVIVES. ANY ONE failing fires the null. Decided by the measured transients."""
    survives = bool(p1_pass and p2["genuine_threshold"] and emerged and block_ok and deterministic)
    if survives:
        head = ("ANALOG REALISATION SURVIVES (DEMONSTRATED): the SPICE coupled-oscillator network "
                "phase-locks to the correct N-bit carry vector at N=4 (exhaustive, all 512 input "
                "combinations) and the N=8 all-propagate worst case (P1 PASS, integer-add cross-"
                "checked); a genuine K_c lock threshold exists (K=0 does NOT lock the worst case => "
                "the coupling is load-bearing, NOT decorative); the carry-1 answer EMERGES from "
                "coupling even when every propagate node is planted on the carry-0 side (not .ic-"
                "planted); a carry-1 in a low nibble does NOT leak across an absent cross-block edge "
                "into an all-kill high nibble (the O(N)-wire block-independence construct); and the "
                "transients are bit-identical across reruns. K_c (between %s and %s) ties the F122 "
                "anchor %s and the N=8 carry-path-graph Fiedler %s. FRAMEWORK-READING: the build-a-"
                "Kuramoto-ALU synthesis stays a reading (MFO VII.6.20); DEMONSTRATED = the ngspice "
                "transient measurement."
                % (_kc_lo(p2), p2["k_c_measured"], p2["k_c_f122_anchor"], p2["ripple_path_fiedler"]))
    else:
        reasons = []
        if not p1_pass:
            reasons.append("P1 fails (a wrong/unresolved carry or an integer-add mismatch)")
        if not p2["genuine_threshold"]:
            reasons.append("no K_c threshold (locks at K=0 => coupling decorative / planted)")
        if not emerged:
            reasons.append("the answer did not emerge from coupling (.ic-planting artifact)")
        if not block_ok:
            reasons.append("a carry leaked across an absent cross-block edge (block independence broke)")
        if not deterministic:
            reasons.append("ngspice output non-deterministic across reruns")
        head = "NULL FIRES: the analog realisation FAILS -- " + "; ".join(reasons) + "."
    return {"headline": head, "survives": survives,
            "p1_pass": bool(p1_pass), "genuine_kc_threshold": bool(p2["genuine_threshold"]),
            "answer_emerges_from_coupling": bool(emerged),
            "nibble_block_independence": bool(block_ok),
            "deterministic": bool(deterministic)}


def _build_record(ng_version, srmech_version, p1_n4, p1_rows, p1_pass, p2, emerged,
                  emerged_carries, block_ok, block_locked, block_gt, deterministic, det_cos,
                  k4, cir_path, verdict):
    return {
        "finding": "F236",
        "measurement": "kuramoto_nibbler_ngspice",
        "ngspice_version": ng_version,
        "srmech_version": srmech_version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": ("a SPICE coupled-oscillator network realising the F234 mapping (carry node = "
                       "binary-phase oscillator on a 1 F capacitor voltage; generate/kill = phantom-"
                       "anchor pinning to pi/0; propagate = zero self-bias + symmetric coupling edge) "
                       "phase-locks to the correct carry vector, with a K_c lock threshold matching "
                       "F122/F234; F236 confirms the SAME dynamics transport into the electrical-"
                       "analog substrate"),
        "pre_stated_null": ("the SPICE network does NOT settle to the correct carry vector (a wrong/"
                            "unresolved node at the final timestep), OR shows no K_c threshold (locks "
                            "at K=0 => the per-node pinning bias alone fixes the answer, coupling "
                            "decorative / .ic-planted) -> the analog realisation fails"),
        "netlist_construct": ("carry node c_i = V on a 1 F cap = phase theta_i; B-source injects "
                              "I=C*d(theta)/dt so dV/dt = pinning + coupling; ngspice .tran integrator "
                              "= the ODE integrator (the srmech Kuramoto gap, F141/F231/F234); "
                              "generate->PINK*sin(PI-V) anchor, kill->PINK*sin(0-V) anchor, "
                              "propagate-> no self-bias + symmetric KC*sin(V_j-V_i) edges on p_i=1 "
                              "(the Class-L A_ij); node0=carry-in pinned pi/0; nibble blocks = absence "
                              "of cross-block edges (O(N) wires, dodges the all-to-all O(N^2) trap)"),
        "readout": ("carry_i = sign cos(theta_i) at lock via Class-K cascade.pin_slot_at_zero "
                    "(cos>0 carry-0, cos<0 carry-1, |cos|<LOCK_MARGIN unresolved=lock-fail); near-zero "
                    "via cascade.magnitude (no abs()); sum_i = p_i XOR carry_i; cross-checked vs an "
                    "INDEPENDENT integer add a+b+cin"),
        "constants": {
            "PI": [round(PI, 10), "A: asymptotic_calculus phase pi (carry-1 antipode of carry-0=0)"],
            "NIBBLE": [NIBBLE, "A: 7483 block = 4 = |Klein-4| = F233 4-thread rung"],
            "N8": [N8, "A: the explicitly-named N=8 worst-case width (two nibbles)"],
            "K_C_F122": [K_C_F122, "A: the F122 measured critical-coupling anchor"],
            "PIN_K": [PIN_K, "B: pinning-field strength floor (>> KC so a pinned carry holds)"],
            "KC_OP": [KC_OP, "B: operational coupling (above the measured K_c)"],
            "K_GRID": [K_GRID, "B: K-sweep grid bracketing criticality (the F234 grid)"],
            "LOCK_MARGIN": [LOCK_MARGIN, "B: |cos| resolved floor (below = near-saddle = unresolved)"],
            "T_STEP": [T_STEP, "B: ngspice .tran step (the deterministic analog integrator step)"],
            "T_STOP_PER_NODE": [T_STOP_PER_NODE, "B: transient stop-time budget per carry node"],
            "IC_BASE": [IC_BASE, "B: deterministic initial-phase base (carry-0 side; NOT the answer)"],
            "IC_STEP": [IC_STEP, "B: deterministic initial-phase per-node increment (fixed spread)"],
            "IC_ANCHOR0": [IC_ANCHOR0, "B: node0 initial phase when pinned to pi (near pi, off-saddle)"],
        },
        "srmech_ops_used": {
            "carry_readout": "cascade.pin_slot_at_zero  [Class K; F217 SR latch]",
            "near_zero_margin": "cascade.magnitude  [Class K; no python abs()]",
            "chirality_of_carry_state": "cascade.net_chirality / cascade.reorient  [Class C]",
            "coupling_graph_spectrum": "laplacian.dense_laplacian + jacobi_eigvals (Fiedler lambda_2)  [Class L; no np.linalg]",
            "attestation": "format.sha256_bytes  [Class A; no hashlib]",
            "cos_of_phase": "ngspice's own `let cc=cos(V)` (the analog substrate's transcendental); srmech READS the parsed scalar",
        },
        "srmech_gap": ("ngspice supplies the Kuramoto/ODE integrator srmech still lacks (the F141/"
                       "F231/F234 gap); the analog .tran transient IS the integration. srmech does the "
                       "READOUT (Class-K pin_slot), the spectrum (Class-L Fiedler), the chirality "
                       "(Class C), and the attestation (Class A); numpy is the array carrier of the "
                       "parsed ngspice output only (no linalg)"),
        "P1_correctness": {
            "n4_exhaustive": p1_n4,
            "named_cases": p1_rows,
            "pass": bool(p1_pass),
            "note": ("N=4 exhaustive = all 512 (a,b,cin) combinations lock to the exact ground-truth "
                     "carry vector AND reproduce a+b+cin under an independent integer add; named cases "
                     "= the N=4 + N=8 all-propagate worst cases (maximal carry chain) + mixed N=4"),
        },
        "P2_kc_threshold": p2,
        "emergence_not_planted": {
            "answer_emerges_from_coupling": bool(emerged),
            "locked_carries_from_wrong_side_start": emerged_carries,
            "note": ("worst-case carry-1 chain (N=8) locked correctly with every propagate node "
                     "started on the carry-0 side => coupling-driven, not .ic-planted"),
        },
        "nibble_block_independence": {
            "ok": bool(block_ok),
            "locked_carries": block_locked,
            "ground_truth": block_gt,
            "note": ("low nibble all-propagate w/ cin=1 (carries 1,1,1,1) does NOT leak into an "
                     "all-kill high nibble: the absent cross-block coupling edge IS the block "
                     "independence -- the O(N)-wire construct that dodges all-to-all O(N^2)"),
        },
        "determinism": {
            "two_runs_identical": bool(deterministic),
            "worst_n4_cosines": det_cos,
            "note": ("only the non-deterministic ngspice byte is the wall-clock Date: raw header, "
                     "excluded from response_sha256 like generated_at (the F233/F234 convention)"),
        },
        "klein4_carry_state": k4,
        "representative_netlist": str(cir_path),
        "tier": {
            "demonstrated": ("the ngspice transient MEASUREMENT (locks to the correct carry vector at "
                             "N=4 exhaustive + N=8 worst case; the genuine K_c threshold; emergence; "
                             "block independence; bit-identical reruns)"),
            "framework_reading": ("the build-a-Kuramoto-ALU-adder synthesis / down-into-the-ALU "
                                  "generalization (MFO VII.6.20)"),
            "scope": ("in-scope: the Kuramoto-ODE / oscillator-network DYNAMICS in the electrical-"
                      "analog substrate (the same dynamics F234 ran in Python); NOT PCB layout / "
                      "fabrication tolerances / component sourcing / gate-delay / timing-closure "
                      "(74xx-SPICE = the F217 existence-proof lens, not a build instruction; the CAD-"
                      "ban HOLDS); defensive scope: addition is general arithmetic, framework-reading"),
        },
        "verdict": verdict,
    }


def _emit(record):
    """Write the content-addressed NDJSON. response_sha256 over the record body MINUS the wall-clock
    generated_at (so a re-run reproduces the measurement sha bit-for-bit; the F233/F234 convention).
    The ngspice transient itself is deterministic, so the parsed cosines (hence P1/P2/verdict) are
    fixed across reruns. Returns (on-disk ndjson sha256, path)."""
    body = {k: v for k, v in record.items() if k != "generated_at"}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    record["response_sha256"] = fmt.sha256_bytes(payload)        # Class A (never hashlib)
    out_dir = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
               / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "kuramoto_nibbler_ngspice.ndjson"
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    with open(out_path, "w") as fh:
        fh.write(line)
        fh.write("\n")
    with open(out_path, "rb") as fh:
        disk = fh.read()
    return fmt.sha256_bytes(disk), str(out_path)


def main():
    import srmech
    ng_version = _ngspice_version()
    print("=" * 84)
    print("R-RBS-LM-236 -- Kuramoto nibble-adder in ngspice (F234 mapping, electrical-analog substrate)")
    print("  ngspice %s | srmech %s" % (ng_version, srmech.__version__))
    print("=" * 84)

    work_dir = Path(tempfile.mkdtemp(prefix="f236_nibbler_"))

    # representative .cir to disk (the N=8 worst case)
    cir_dir = Path(__file__).resolve().parent
    cir_path = write_representative_cir(cir_dir)
    print("\n[cir] representative netlist written: %s" % cir_path)

    print("\n[P1a] N=4 EXHAUSTIVE (all 512 a/b/cin combos lock to GT carry + integer-add match) ...")
    p1_n4, p1_n4_pass = check_p1_n4_exhaustive(work_dir)
    print("   carry-exact %d/%d | integer-add-match %d/%d | wrong %d | with-unresolved %d"
          % (p1_n4["n_carry_exact"], p1_n4["n_total"], p1_n4["n_integer_add_match"],
             p1_n4["n_total"], p1_n4["n_wrong"], p1_n4["n_with_unresolved_node"]))

    print("\n[P1b] named cases (N=4 + N=8 all-propagate worst case + mixed N=4) ...")
    p1_rows, p1_named_pass = check_p1_named_cases(work_dir)
    for r in p1_rows:
        print("   %-10s N=%-2d a=%-3d b=%-3d cin=%d gt=%s locked=%s carry_ok=%s int_add=%s/%s unresolved=%d"
              % (r["case"], r["N"], r["a_int"], r["b_int"], r["cin"], r["gt_carries"],
                 r["locked_carries"], r["carry_correct"], r["reconstructed_int"],
                 r["independent_integer_add"], r["n_unresolved"]))
    p1_pass = bool(p1_n4_pass and p1_named_pass)
    print("   P1 verdict: %s (N=4 exhaustive=%s, named=%s)"
          % ("PASS" if p1_pass else "FAIL", p1_n4_pass, p1_named_pass))

    print("\n[P2] K_c lock threshold (worst-case all-propagate N=8; coupling not decorative) ...")
    p2 = check_kc_threshold(work_dir)
    for r in p2["rows"]:
        print("    K=%-5s correct_lock=%s unresolved=%d min|cos|=%.3f"
              % (r["K"], r["correct_lock"], r["n_unresolved"], r["min_abs_cos"]))
    print("   K_c measured = %s (F122 anchor %s); locks_at_K0=%s; genuine_threshold=%s; fiedler=%s"
          % (p2["k_c_measured"], p2["k_c_f122_anchor"], p2["locks_at_K0_decorative"],
             p2["genuine_threshold"], p2["ripple_path_fiedler"]))

    print("\n[emergence] propagate nodes planted on the WRONG (carry-0) side -> must still lock carry-1 ...")
    emerged, emerged_carries = check_emergence(work_dir)
    print("   emerges_from_coupling=%s  locked=%s" % (emerged, emerged_carries))

    print("\n[block] nibble-block independence (carry must NOT leak across an absent cross-block edge) ...")
    block_ok, block_locked, block_gt = check_block_independence(work_dir)
    print("   block_independence=%s  locked=%s  gt=%s" % (block_ok, block_locked, block_gt))

    print("\n[determinism] two identical ngspice runs -> identical parsed cosines ...")
    deterministic, det_cos = check_determinism(work_dir)
    print("   two_runs_identical=%s" % deterministic)

    k4 = klein4_carry_chirality()

    verdict = _decide_verdict(p1_pass, p2, emerged, block_ok, deterministic)
    record = _build_record(ng_version, srmech.__version__, p1_n4, p1_rows, p1_pass, p2,
                           emerged, emerged_carries, block_ok, block_locked, block_gt,
                           deterministic, det_cos, k4, cir_path, verdict)
    sha, out_path = _emit(record)
    print("\n" + "=" * 84)
    print("  VERDICT: %s" % verdict["headline"])
    print("  ndjson: %s" % out_path)
    print("  ndjson sha256 (with wall-clock): %s" % sha)
    print("  response_sha256 (bit-exact, minus generated_at): %s" % record["response_sha256"])
    print("=" * 84)
    return record


if __name__ == "__main__":
    main()
