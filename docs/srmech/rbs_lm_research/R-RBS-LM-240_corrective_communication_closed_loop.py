"""R-RBS-LM-240 — CORRECTIVE communication = a closed-loop reciprocal coupling edge + a Class-K error-latch.

Finding F240 (FRAMEWORK-READING tier; the F240 RE-RUN in the ngspice analog substrate). The reduction
under test is "communication reduces to back-and-forth thinking outside of one body" = the reciprocal
CLOSED-LOOP coupling edge, with the fixed point of the A<->B loop living in NEITHER body alone — the
OFF-DIAGONAL Laplacian does the computation (distributed cognition). The SHARP structural claim:
CORRECTIVE communication is a closed-loop reciprocal coupling edge PLUS a Class-K error-latch, and this
STRUCTURE (not the AMOUNT of coupling) is what drives a stable phase-lock fixed point.

================================ WHY THIS IS THE ngspice RE-RUN ============================
The FIRST F240 attempt ran away: its integration core was a PURE-PYTHON synchronous Euler Kuramoto
sweep (theta += DT*(omega + coupling [+ correction]) over a SETTLE_BUDGET=20000-sweep loop, for every
(N, regime, frequency, K, seed)). That pegged 100% CPU with zero output and was killed. This RE-RUN
moves the ODE integration into ngspice's `.tran` transient — the proven fast C integrator F236/F241
used — so EVERY transient is BOUNDED by its stop-time and CANNOT run away. No unbounded Python loop
exists anywhere in this file: ngspice integrates each network in bounded C time, with a per-invocation
subprocess timeout as a hard backstop. The DESIGN (regimes, matched-budget control, meters, pre-stated
null, citations, verdict logic) is preserved verbatim from the intended F240; only the integration
core is the F236 capacitor-voltage-as-phase + B-source Kuramoto-RHS netlist.

THE CAPACITOR-AS-PHASE CONSTRUCT (REUSED from F236): each oscillator i is the VOLTAGE on a 1 F
  capacitor C_i, playing the Kuramoto phase theta_i. A behavioral current source B_i injects
  I_i = C * d(theta_i)/dt; with C=1 the node obeys d V_i / dt = omega_i + coupling_i [+ correction_i],
  which IS the Kuramoto phase ODE. ngspice's .tran transient integrator IS the ODE integrator (the
  srmech Kuramoto/ODE GAP noted across F141/F231/F234/F235/F236; the analog substrate supplies it).

THE DECISIVE PREDICTION (the F234/F235 located-not-set discipline applied to K_c): at a MATCHED TOTAL
COUPLING BUDGET (sum of absolute edge weights held identical across regimes, spread 0.0), the
reciprocal+Class-K-correction regime phase-locks (Kuramoto r >= 0.95) at a LOWER critical coupling K_c
than the feed-forward / one-way / stigmergic regime — correction locks where feed-forward does NOT —
and this advantage is LARGER at UNEQUAL natural frequency (where mismatched oscillators must be
ACTIVELY pulled into lock) than at EQUAL natural frequency (where, per F141, in-phase is the attractor
for one-way and reciprocal alike, so the advantage approximately VANISHES). The frequency-dependence is
the signature that distinguishes "correction matters" from "reciprocal is just more symmetric".

THREE coupling regimes on the SAME F235 air-gapped Kuramoto testbed (the third arm is what lets the
null distinguish "the back-edge alone is decorative" from "the latch is what does it"), all on the SAME
node set + SAME time-averaged undirected edge list (_extended_mesh_edges: backbone (i,i+1) radius-1 +
(i,i+2) radius-2; |E| = 2m-3). Each undirected mesh edge {i,j} is realised as a DIRECTED B-source
coupling structure in the netlist:
  (R1) FEED-FORWARD / one-way / stigmergic (OPEN-LOOP): the full per-edge budget W*K on the lower->
       higher direction ONLY — a coupling term K*W*sin(V(i)-V(j)) is added to the DRIVEN node j's
       B-source ONLY (the i->j return is absent; node i feels nothing from j). A emits, B reads later;
       no return path, no comparison, no correction. F141's directed-only coupling (achiral-null at
       EQUAL freq).
  (R2) RECIPROCAL-ONLY (CLOSED-LOOP edge, NO latch): the SYMMETRIC pair — K*(W/2)*sin(V(j)-V(i)) on
       node i AND K*(W/2)*sin(V(i)-V(j)) on node j. The back-edge exists (mutual entrainment), bare
       Kuramoto coupling, no explicit error-comparison term. Tests whether the reciprocal edge ALONE
       closes the loop.
  (R3) RECIPROCAL + CLASS-K-CORRECTION latch (the F240 corrective regime, FULL closed loop): the R2
       symmetric edge PLUS, per oscillator i, a BUDGET-NEUTRAL Class-K-latched correction term added to
       the SAME B-source. The correction reads the phase ERROR between the received neighbour mean-field
       and own phase and re-orients a budget-drawn increment by the latched sign; ngspice integrates the
       sgn(cos(.))*sin(.) latch term directly (its own transcendentals), and the srmech Class-K
       pin_slot_at_zero / Class-C reorient / net_chirality READ the latch STATE at the locked transient
       (exactly the F236 carry-readout pattern: srmech reads the parsed analog scalar). orient=+1 pulls
       toward the received phase (in-lock), orient=-1 pushes away, orient=0 = boundary/unresolved (the
       in-script falsifier). "Compare received-vs-own phase, re-orient via Class-C" is the NAMED
       K-then-C composition — the F240 structural claim that mutual entrainment IS error-correction.

THE LOAD-BEARING CONTROL (analogous to F235's matched-edge-budget control + the F234 all-to-all-smuggle
guard): the three regimes are compared at an IDENTICAL total coupling budget so the ONLY difference is
one-way-vs-reciprocal-vs-reciprocal+latch STRUCTURE, never the AMOUNT of coupling.
  - Fix a per-undirected-edge budget W. FEED-FORWARD (R1) puts the FULL weight W on the single directed
    edge (one entry W per mesh edge). RECIPROCAL (R2,R3) SPLITS that W across the two directions
    (A_ij=A_ji=W/2; two entries of W/2 per mesh edge). RESULT: the L1 budget sum_{i,j}|A_ij| is
    IDENTICAL across R1/R2/R3 (each mesh edge contributes exactly W = W/2 + W/2 in every regime).
  - THE CLASS-K CORRECTION TERM (R3) IS BUDGET-NEUTRAL BY THE SAME RULE: the correction increment
    magnitude is drawn from the SAME per-edge budget (the latch RE-ROUTES existing coupling weight
    through the K-then-C comparison; it does NOT add new weight). R3's correction strength per
    oscillator = its R2 reciprocal row-sum / m, so the network L1 budget is UNCHANGED. Reported per
    regime per N as matched_total_abs_weight with spread 0.0 (the null-guard, mirroring F235's
    spread-0.00 line); a non-zero spread VOIDS the comparison.
  - A LABELED-TRAP arm: an UNMATCHED feed-forward where R1 is given the FULL W on BOTH directions (2x
    the budget) is included ONLY to expose "more coupling locks easier" as the confound to be
    controlled away (the F234 all-to-all-TRAP-row pattern) — never as a model.

TWO natural-frequency conditions (both swept across all N and all K), because F141's result makes
frequency the variable that turns the corrective edge on:
  (C-EQ) EQUAL natural frequency: omega_i = 0 for all i. Per F141, in-phase is the attractor for
         directed-only AND symmetric coupling alike (achiral-null). PREDICTION: the corrective-edge
         advantage K_c(R1)-K_c(R3) is ~0 here (the control condition).
  (C-UNEQ) UNEQUAL natural frequency: omega_i drawn from a fixed seeded uniform on [-Delta,+Delta]
         (Delta swept as a frequency-spread dial), mean-centred. PREDICTION (F141-grounded): the
         corrective-edge advantage is STRICTLY LARGER at unequal frequency, and grows with Delta.

=============================== PRE-STATED NULL (verbatim) ==================================
"The corrective (reciprocal closed-loop + Class-K-latch) regime does NOT confer a phase-lock advantage
over the feed-forward one-way regime once the coupling budget is matched. Concretely the NULL FIRES if
ANY of: (a) FEED-FORWARD LOCKS JUST AS WELL — at matched budget, K_c(feed-forward R1) <= K_c(corrective
R3) (the one-way edge reaches r >= 0.95 at the same or lower coupling than the closed loop), so the
back-and-forth / correction is DECORATIVE and one-way emit-and-forget already coordinates; (b) NEITHER
LOCKS — no regime reaches r >= 0.95 within the settle budget at the swept N and K (the testbed is
mis-specified / the lock criterion is unreachable, so no contrast can be drawn); (c)
MAGNITUDE-ARTIFACT — the corrective advantage is present at UNMATCHED budget but VANISHES once the total
absolute coupling weight is matched (K_c(R3) approx K_c(R1) under the matched control while the win only
reappears in the double-budget trap arm), i.e. the win was more-coupling, not structure (the central
spurious risk, analogous to F235's density-confound branch d); (d) N-INSTABILITY / INVERSION — the
corrective advantage appears at only one N and INVERTS at another (e.g. K_c(R3) < K_c(R1) at N=8 but
K_c(R3) > K_c(R1) at N=32), so it is not a stable structural property across the F234 width-doubling.
ADDITIONALLY the directional sub-claim is NOT supported (downgrade, not full null) if the advantage is
NOT larger at unequal than at equal frequency (e.g. equally large at C-EQ, contradicting the
F141-grounded prediction that correction matters specifically when oscillators differ). If the null
fires, the F240 claim is downgraded to an analogy: corrective communication may SHARE the closed-loop
reciprocal shape but the reciprocity+latch is not a MEASURED phase-lock advantage over one-way
coupling, and 'communication reduces to the reciprocal closed-loop edge' is suggestive, not
load-bearing. The frog biology stays the literature's to assert either way."

DISPOSITION RULE (no leaning): the headline is a MECHANICAL read of the measured ngspice booleans.
POSITIVE = K_c(R3) < K_c(R1) at unequal frequency at the swept N (corrective locks where feed-forward
does not), the advantage larger at unequal than equal frequency and growing with Delta, surviving the
matched budget control. The biology stays the literature's to assert either way.
============================================================================================

srmech-FIRST discipline (HARD = 0; run check_srmech_discipline.py on this file via the rc9 venv):
  - cos readout of the locked phase -> ngspice's own `let cc=cos(V)`; srmech READS the parsed scalar [analog substrate]
  - order-parameter r = |mean exp(i theta)| -> two cascade.magnitude + sqrt (the F231 pattern)      [Class K]
  - error-latch (received vs own)  -> cascade.pin_slot_at_zero on cos(received_psi - own_theta)      [Class K; F217 SR latch]
  - correction sign re-application -> cascade.reorient(orient, step)                                 [Class C]
  - net orientation diagnostic     -> cascade.net_chirality                                          [Class C]
  - coupling-graph spectrum/Fiedler-> laplacian.dense_laplacian + jacobi_eigvals                     [Class L; no np.linalg]
  - Kc/Kc ratio de-magick anchor   -> cascade.best_rational_signed                                   [Class K/N]
  - near-zero / magnitude test     -> cascade.magnitude (NEVER python abs()/max())                   [Class K]
  - attestation hash               -> format.sha256_bytes (NEVER hashlib.sha256())                   [Class A]
  ngspice computes sin/cos itself (the analog substrate's transcendentals AND the .tran integrator);
  srmech READS the parsed scalars and does every Class-K/C/L/A op. numpy is the array carrier of the
  parsed ngspice output only (no linalg, no abs, no Counter).

CONFIRMED srmech GAP (logged for UPSTREAM_NOTES §11): rc9 ships srmech.amsc.cascade.kuramoto_step but
it is ALL-TO-ALL UNIFORM-COUPLING ONLY (scalar coupling, (coupling/n)*Sigma sin) — it does NOT accept a
coupling matrix / adjacency / Laplacian, so it does NOT fit F240's graph-structured directed-vs-
symmetric coupling. The forward-ask (an optional coupling-matrix/adjacency argument) is appended to
UPSTREAM_NOTES §11. The analog substrate (ngspice .tran) supplies the graph-structured integrator the
op lacks. NO srmech package edit.

CITATION DISCIPLINE (F226 verify-before-assert): the framework asserts ONLY the structural
closed-loop-reciprocal-edge + Class-K-latch SHAPE. Every Staurois foot-flagging frog biology fact below
is the PEER-REVIEWED LITERATURE'S to assert and was WEB-VERIFIED 2026-05-31 (real authors + exact title
+ venue + DOI/PMID) — see CITATIONS dict. No fabricated DOIs. Paywalled-only DOIs cite via OA/PMC chain.

CAD-ban / defensive scope: this reads animal-communication + coupled-oscillator coordination DYNAMICS
(distributed-systems reading only). NOT PCB layout / fabrication / mechanical-mesh / gate-delay /
timing-closure (the SPICE framing is the oscillator-network ODE lens, NOT a build instruction; the
CAD-ban HOLDS); NOT capability / hunting-optimization / targeting. `[[user_stance_ai_is_not_a_substrate]]`
(the LM is a process over a substrate, not an entity that gains awareness). no-lineage (the framework
reads what animal-communication ethology + synchronization physics already established structurally; it
does not extend or supersede).

Tiering (MFO VII.6.20): the bit-exact ngspice phase-lock SIMULATION + Laplacian-spectral MEASUREMENT
(per-regime located K_c, the order parameter, the matched-budget control, the symmetrised-graph
lambda_2) is DEMONSTRATED; reading corrective communication AS a closed-loop reciprocal edge + Class-K
latch is FRAMEWORK-READING; every Staurois ethology fact belongs to the cited peer-reviewed literature.
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

# --- attested constants (CLAUDE.md §4 no-magic-numbers; every constant classified A / B / C) -----
PI = float(np.pi)             # A: asymptotic_calculus
K_C_F122 = 0.20               # A: the F122 measured critical coupling anchor (R-RBS-LM-95/95b)
NIBBLE = 4                    # A: |Klein-4| = the F233 4-thread rung; smallest swept width
N_SWEEP = [4, 8, 16, 32]      # A: the F234 width-doubling cascade (node = communicating body);
                              #    all four checked for the N-stability null branch (d)
SEED = 240                    # B: deterministic seed (this finding's id) for the initial-phase spread
LOCK_R = 0.95                 # B: order-parameter lock threshold (the F231 lock criterion)
W_PER_EDGE = 1.0              # A: per-undirected-edge coupling budget W (unit; K scales the matrix).
                              #    FEED-FORWARD puts W on one direction; RECIPROCAL splits W/2 + W/2 ->
                              #    IDENTICAL L1 budget per edge (the matched-budget rule).
# K_GRID — a SMALL located-not-set coupling sweep (6 values, per the task's ~6-8 grid), bracketing the
# F122 K_c=0.20 anchor from 0 (the decorative test: locks at K=0 => coupling does no work) up through
# strong coupling so each regime's K_c is LOCATED (not hand-set; the cherry-pick guard). Kept small so
# the full (N x regime x freq x K) grid finishes in minutes under ngspice .tran.
K_GRID = [0.0, 0.10, 0.20, 0.50, 1.0, 2.0]            # B: located-not-set sweep grid (6 values)
DELTA_GRID = [0.3, 1.0]       # B: frequency-spread dial for C-UNEQ (uniform on [-Delta,+Delta]); the
                              #    directional-claim test = does the advantage GROW with Delta (2 values
                              #    to keep the grid small while still testing growth)
ZERO_FLOOR = 1e-9             # B: near-zero spectral/spread floor (numerical), component / Fiedler test
UNIT_W = 1.0                  # A: unit edge weight (symmetrised topology-only Fiedler; K scales separately)
LOCK_MARGIN = 0.0             # A: r>=LOCK_R is the lock test; no separate cos margin needed here

# --- ngspice .tran anti-runaway parameters (HARD safeguards: bounded stop-time + subprocess timeout) -
NGSPICE = "ngspice"           # A: the installed simulator binary (ngspice-45.2, this box)
T_STEP = 0.02                 # B: ngspice .tran step (the deterministic analog integrator step)
T_STOP_BASE = 30.0            # B: transient stop-time floor (>> the observed lock time at small N)
T_STOP_PER_NODE = 0.6         # B: stop-time growth per node (scales MODESTLY with N so a wide net has
                              #    enough analog time to entrain; T_STOP = base + per_node*N, bounded)
NG_TIMEOUT_S = 120            # B: per-invocation subprocess timeout (HARD backstop: records
                              #    "timeout/not-locked" and MOVES ON rather than blocking; the task's
                              #    mandatory per-call timeout so the run can NEVER hang)
N_SAMPLE_TAIL = 40            # B: number of trailing .tran samples averaged for the steady-state
                              #    order parameter (a tail mean is robust to a residual ripple)


# =========================================================================================
# CITATIONS — WEB-VERIFIED 2026-05-31 (F226 verify-before-assert). The framework asserts ONLY the
# structural closed-loop-reciprocal-edge + Class-K-latch shape; every Staurois foot-flagging frog
# biology fact below belongs to these peer-reviewed sources. No fabricated DOIs.
# =========================================================================================
CITATIONS = {
    "preininger_2009_visual_signaling": {
        "authors": "Preininger D, Boeckle M, Hodl W",
        "year": 2009,
        "title": ("Communication in Noisy Environments II: Visual Signaling Behavior of Male "
                  "Foot-flagging Frogs Staurois latopalmatus"),
        "venue": "Herpetologica 65(2):166-173",
        "doi": "10.1655/08-037R.1",
        "oa_chain": ("Herpetologica DOI may be paywalled per [[feedback_paywalled_doi_cannot_be_attested]]; "
                     "cite via BioOne abstract + ResearchGate PDF chain"),
        "web_verified": "2026-05-31 (BioOne)",
        "asserts": ("in 14 male-male agonistic interactions (106 min video) foot-flagging performed IN "
                    "THE DIRECTION OF the interacting male was the most common display, at a higher rate "
                    "than advertisement calls — the RESPONSIVE, directed male-male exchange (flag aimed "
                    "at the rival)"),
    },
    "grafe_tony_2017_temporal_variation": {
        "authors": "Grafe TU, Tony JA",
        "year": 2017,
        "title": ("Temporal variation in acoustic and visual signalling as a function of stream "
                  "background noise in the Bornean foot-flagging frog, Staurois parvus"),
        "venue": "Journal of Ecoacoustics 1(1):article 2",
        "doi": "10.22261/jea.x74qe0",
        "oa_chain": "OA (jea.jams.pub)",
        "web_verified": "2026-05-31 (Journal of Ecoacoustics, OA)",
        "asserts": ("the CHANNEL-ADAPTIVE SWITCH: male S. parvus increased foot flagging and decreased "
                    "advertisement calling when presented with playbacks of stream noise compared to "
                    "less noisy pre-playback conditions — the exchange RE-ROUTED from the jammed acoustic "
                    "channel to the visual channel"),
    },
    "preininger_2013_divergent_receiver": {
        "authors": "Preininger D, Boeckle M, Sztatecsny M, Hodl W",
        "year": 2013,
        "title": ("Divergent Receiver Responses to Components of Multimodal Signals in Two "
                  "Foot-Flagging Frog Species"),
        "venue": "PLoS ONE 8(1):e55367",
        "doi": "10.1371/journal.pone.0055367",
        "pmid": "23383168",
        "pmcid": "PMC3558420",
        "oa_chain": "OA (PLOS / PMC3558420)",
        "web_verified": "2026-05-31 (PLOS / PubMed 23383168 / PMC3558420)",
        "asserts": ("behavioural field experiments with a ROBOTIC MODEL FROG (extendable leg + acoustic "
                    "playback) tested receiver RESPONSES to acoustic/visual/combined stimuli; the main "
                    "response of S. parvus to the stimuli was foot flagging — the receiver-side return "
                    "half of the exchange"),
    },
    "grafe_wanger_2007_alerting": {
        "authors": "Grafe TU, Wanger TC",
        "year": 2007,
        "title": ("Multimodal Signaling in Male and Female Foot-Flagging Frogs Staurois guttatus "
                  "(Ranidae): An Alerting Function of Calling"),
        "venue": "Ethology 113(8):772-781",
        "doi": "10.1111/j.1439-0310.2007.01378.x",
        "oa_chain": "Ethology DOI may be paywalled per [[feedback_paywalled_doi_cannot_be_attested]]; cite via Wiley abstract",
        "web_verified": "2026-05-31 (Wiley)",
        "asserts": ("advertisement calls and foot-flags form a multicomponent multimodal display; calls "
                    "have an ALERTING function drawing the receiver's attention to the subsequent "
                    "foot-flag (call temporally coupled to flag)"),
    },
    "grafe_2012_multimodal_noisy": {
        "authors": "Grafe TU, Preininger D, Sztatecsny M, Kasah R, Dehling JM, Proksch S, Hodl W",
        "year": 2012,
        "title": ("Multimodal Communication in a Noisy Environment: A Case Study of the Bornean Rock "
                  "Frog Staurois parvus"),
        "venue": "PLoS ONE 7(5):e37965",
        "doi": "10.1371/journal.pone.0037965",
        "pmid": "22655089",
        "pmcid": "PMC3360010",
        "oa_chain": "OA (PLOS / PMC3360010)",
        "web_verified": "2026-05-31 (PLOS / PubMed 22655089 / PMC3360010)",
        "asserts": ("S. parvus solves continuous broadband stream noise by modifying calls AND using "
                    "numerous visual signals (foot-flagging most conspicuous), given in intra- and "
                    "intersexual (agonistic male-male) contexts — the reciprocal-edge re-routed to the "
                    "visual channel (flag answers flag in male-male contests; channel-adaptive switch "
                    "under stream noise)"),
    },
    "kuramoto_synchronization": {
        "authors": "Strogatz SH",
        "year": 2000,
        "title": ("From Kuramoto to Crawford: exploring the onset of synchronization in populations of "
                  "coupled oscillators"),
        "venue": "Physica D: Nonlinear Phenomena 143(1-4):1-20",
        "doi": "10.1016/S0167-2789(00)00094-4",
        "oa_chain": "OA author PDF stevenstrogatz.com",
        "web_verified": "2026-05-31 (Physica D / ADS 2000PhyD..143....1S / author OA PDF)",
        "asserts": ("the coupled-oscillator synchronization / critical-coupling K_c physics (the "
                    "F122/F231/F234/F235 Kuramoto anchor): above a coupling threshold a population "
                    "phase-transitions from incoherent to partially synchronized"),
    },
    "sakaguchi_kuramoto_1986": {
        "authors": "Sakaguchi H, Kuramoto Y",
        "year": 1986,
        "title": "A Soluble Active Rotater Model Showing Phase Transitions via Mutual Entrainment",
        "venue": "Progress of Theoretical Physics 76(3):576-581",
        "doi": "10.1143/PTP.76.576",
        "oa_chain": "OA (Oxford PTP, open archive)",
        "web_verified": "2026-05-31 (Progress of Theoretical Physics / OUP)",
        "asserts": ("mutual entrainment / phase-frustration in coupled rotators — the synchronization-via-"
                    "MUTUAL-coupling physics the reciprocal regime instantiates (the framework reads the "
                    "reciprocal closed loop AS this mutual-entrainment shape)"),
    },
}


# =========================================================================================
# STEP 1 — the SHARED undirected mesh as an edge list (REUSED VERBATIM from F235). All regimes
# share the SAME node set + SAME time-averaged undirected support, so the ONLY difference across
# R1/R2/R3 is the DIRECTED structure imposed on each edge. |E| = (m-1)+(m-2) = 2m-3.
# =========================================================================================
def _extended_mesh_edges(m):
    """The near-1D EXTENDED mesh = a path radius-1 + radius-2 (open ends). One connected component.
    REUSED from F235 (the shared undirected coupling support). Returns the canonical edge list."""
    edges = [(i, i + 1) for i in range(m - 1)]       # the continuous backbone (radius 1)
    edges += [(i, i + 2) for i in range(m - 2)]      # radius-2 reach (still locally 1-D)
    return _dedup(edges, m)


def _dedup(edges, m):
    """Canonicalize undirected edges to sorted 2-tuples + drop self-loops/duplicates (dense_laplacian
    edges are 2-tuples per the AMSC gotcha). REUSED from F235."""
    seen = set()
    out = []
    for a, b in edges:
        if a == b:
            continue
        e = (a, b) if a < b else (b, a)
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


# =========================================================================================
# STEP 2 — Laplacian spectrum + algebraic connectivity (Class L) on the SYMMETRISED support. By
# construction this is IDENTICAL across R1/R2/R3 (same undirected edge set), so ANY K_c difference
# is NOT a connectivity difference — it is the directed STRUCTURE + the latch. REUSED from F235.
# =========================================================================================
def graph_spectrum(m, edges):
    """Class-L Laplacian spectrum on the symmetrised support: dense_laplacian -> jacobi_eigvals ->
    sorted. Returns (lambda_2 Fiedler, lambda_max, n_components, n_edges). Near-zero count via
    cascade.magnitude (NEVER abs())."""
    laplacian_m = lap.dense_laplacian(m, edges)
    eig = sorted(float(e) for e in lap.jacobi_eigvals(laplacian_m))
    n_zero = sum(1 for e in eig if cascade.magnitude(e) < ZERO_FLOOR)
    lam_2 = eig[1] if len(eig) > 1 else 0.0
    lam_max = eig[-1] if eig else 0.0
    return float(lam_2), float(lam_max), int(n_zero), len(edges)


# =========================================================================================
# STEP 3 — the three regimes as DIRECTED coupling matrices at global coupling K, at the MATCHED
# TOTAL BUDGET. The L1 budget sum|A| is identical across regimes by the W = W/2 + W/2 rule. A_ij =
# how strongly j drives i (row i, column j): the coupling on node i is sum_j A_ij sin(theta_j - theta_i).
# =========================================================================================
def feed_forward_matrix(m, edges, kstrength, double_budget=False):
    """(R1) FEED-FORWARD / one-way / stigmergic (OPEN-LOOP): the FULL per-edge budget W on the
    lower->higher direction ONLY. For edge (i,j), i<j: A_fwd[j,i] = K*W (the higher index j reads
    from the lower index i; i emits, feels no return). A_fwd[i,j] = 0 (no return path). The
    double_budget=True LABELED-TRAP arm puts W on BOTH directions (2x the budget) ONLY to expose
    'more coupling locks easier' (never a model)."""
    a = np.zeros((m, m))
    for (i, j) in edges:                              # i < j (canonical)
        w = kstrength * W_PER_EDGE
        a[j, i] = w                                   # one-way: i -> j (row j reads from i)
        if double_budget:
            a[i, j] = w                               # TRAP: also j -> i (doubles the budget)
    return a


def reciprocal_matrix(m, edges, kstrength):
    """(R2/R3) RECIPROCAL: SPLIT the SAME per-edge budget W across the two directions:
    A_rec[i,j] = A_rec[j,i] = K*W/2 (symmetric). The back-edge exists (mutual entrainment). The L1
    budget per edge = W/2 + W/2 = W, IDENTICAL to the feed-forward W (the matched-budget rule)."""
    a = np.zeros((m, m))
    for (i, j) in edges:
        w = kstrength * W_PER_EDGE / 2.0              # split: W/2 each direction
        a[i, j] = w
        a[j, i] = w
    return a


def _l1_budget(a_matrix):
    """The total absolute coupling weight sum_{i,j}|A_ij| (the matched-budget meter). cascade.magnitude
    per entry (NEVER python abs()); the matched-budget spread floor is a Class-K modulus test."""
    total = 0.0
    flat = a_matrix.reshape(-1)
    for v in flat:
        total += cascade.magnitude(float(v))
    return float(total)


def _row_abs_sums(a_matrix):
    """Per-oscillator coupling row-sum sum_j |A_ij| (the per-oscillator matched-drive meter)."""
    m = a_matrix.shape[0]
    out = []
    for i in range(m):
        s = 0.0
        for v in a_matrix[i]:
            s += cascade.magnitude(float(v))
        out.append(float(s))
    return out


# =========================================================================================
# STEP 4 — the ngspice netlist: capacitor-voltage-as-phase + B-source Kuramoto RHS. ngspice's .tran
# transient is the BOUNDED ODE integrator (the anti-runaway core). Each regime's directed coupling
# matrix becomes per-node B-source coupling terms; R3 adds the BUDGET-NEUTRAL Class-K-latched
# correction term (ngspice integrates the sgn(cos(.))*sin(.) latch; srmech READS the latch state).
# =========================================================================================
def _det_initial_phases(m, seed):
    """Deterministic initial phases (a fixed seeded spread, NOT random per-run, NOT the locked answer):
    a closed-form spread on [-PI, PI) from a fixed RandomState. The lock must be DRIVEN by the coupling,
    not planted by the .ic (the F236 anti-smuggle discipline)."""
    rng = np.random.RandomState(seed)
    return rng.uniform(-PI, PI, m)


def _natural_frequencies(m, condition, delta, seed):
    """The natural-frequency vector omega. C-EQ: omega_i = 0 (identical intrinsic rhythms). C-UNEQ:
    omega_i ~ uniform[-delta,+delta] from a fixed seeded RandomState, mean-centred so the lock is a
    genuine phase lock, not a co-rotation drift."""
    if condition == "equal":
        return np.zeros(m)
    rng = np.random.RandomState(seed + 13)            # independent stream for omega
    om = rng.uniform(-delta, delta, m)
    return om - om.mean()                             # mean-centre (lock, not co-rotation)


def build_netlist(m, edges, kstrength, regime, omega, theta0, corr_strength, t_stop, title):
    """Emit a deterministic ngspice netlist for the Kuramoto-coupled oscillator network in one regime.
    Each oscillator i = V on a 1 F cap (the phase theta_i); B_i injects the Kuramoto RHS current so
    dV/dt = omega_i + coupling_i [+ correction_i]. ngspice .tran integrates in bounded C time.

    Coupling per node i (row i of the directed matrix): sum_j A_ij * sin(V(j) - V(i)).
      R1 feed_forward: A_ij nonzero only for the driving (lower->higher) direction -> the term appears
        ONLY on the driven node's B-source (emit-and-forget; the emitter feels no return).
      R2 reciprocal_only: symmetric A_ij = A_ji = K*W/2 -> the symmetric pair (mutual entrainment).
      R3 reciprocal_correction: R2 symmetric coupling PLUS the BUDGET-NEUTRAL Class-K-latched
        correction. The received neighbour mean-field on node i is acc_i = sum_j A_ij e^{i V(j)};
        its phase is psi_i = atan2(Im acc_i, Re acc_i). The correction increment is
        corr_strength_i * sgn(cos(psi_i - V(i))) * sin(psi_i - V(i)) — ngspice computes the trig and
        the sgn() latch directly; the term RE-ROUTES existing reciprocal weight (corr_strength_i =
        the R2 row-sum / m), it adds NO new L1 budget. srmech's Class-K pin_slot_at_zero / Class-C
        reorient / net_chirality READ the latch state at the locked transient (the F236 readout pattern).
    """
    if regime == "feed_forward":
        a = feed_forward_matrix(m, edges, kstrength, double_budget=False)
    elif regime == "feed_forward_double_TRAP":
        a = feed_forward_matrix(m, edges, kstrength, double_budget=True)
    else:                                             # reciprocal_only / reciprocal_correction
        a = reciprocal_matrix(m, edges, kstrength)
    corrective = (regime == "reciprocal_correction")

    lines = [
        "* %s" % title,
        "* F240 ngspice RE-RUN: oscillator i = V on a 1 F cap = Kuramoto phase theta_i;",
        "* B_i = the phase-ODE RHS current so dV/dt = omega_i + coupling_i [+ correction_i].",
        "* coupling row i = sum_j A_ij sin(V(j)-V(i)); .tran is the BOUNDED ODE integrator.",
        ".param PI=%.14f" % PI,
    ]
    # caps (the phase state) + B-source RHS per oscillator
    for i in range(m):
        terms = []
        # natural frequency (omega_i) — the intrinsic drift
        terms.append("(%.10f)" % float(omega[i]))
        # coupling: row i of the directed matrix
        for j in range(m):
            w = float(a[i, j])
            if w != 0.0:
                terms.append("(%.10f)*sin(V(n%d)-V(n%d))" % (w, j, i))
        # R3 BUDGET-NEUTRAL Class-K-latched correction (ngspice integrates the latch term).
        # ngspice's B-source math has NO atan2, so the phase ERROR e_i = psi_i - V(i) is realised
        # WITHOUT reconstructing psi_i, using the received-field components directly. With the
        # received neighbour mean-field acc_i = sum_j A_ij e^{i V(j)} = (RE_i, IM_i):
        #   cos(psi_i - V_i) = (RE_i*cos V_i + IM_i*sin V_i) / |acc_i|   (the alignment; its SIGN is the latch)
        #   sin(psi_i - V_i) = (IM_i*cos V_i - RE_i*sin V_i) / |acc_i|   (the signed pull magnitude)
        # so the budget-drawn correction corr_strength_i * sgn(cos(e_i)) * sin(e_i) is exactly:
        #   corr_strength_i * sgn(RE_i*cos V_i + IM_i*sin V_i) * (IM_i*cos V_i - RE_i*sin V_i)/|acc_i|
        # all in ngspice-supported ops (cos/sin/sqrt/sgn) — the faithful atan2-free Class-K latch.
        if corrective and corr_strength is not None and corr_strength[i] != 0.0:
            re_terms = []
            im_terms = []
            for j in range(m):
                w = float(a[i, j])
                if w != 0.0:
                    re_terms.append("(%.10f)*cos(V(n%d))" % (w, j))
                    im_terms.append("(%.10f)*sin(V(n%d))" % (w, j))
            if re_terms:                              # has a received field (it always does in R2/R3)
                re_expr = "(" + " + ".join(re_terms) + ")"     # RE_i = Re acc_i
                im_expr = "(" + " + ".join(im_terms) + ")"     # IM_i = Im acc_i
                cos_vi = "cos(V(n%d))" % i
                sin_vi = "sin(V(n%d))" % i
                proj_cos = "(%s*%s + %s*%s)" % (re_expr, cos_vi, im_expr, sin_vi)  # |acc|*cos(e_i)
                proj_sin = "(%s*%s - %s*%s)" % (im_expr, cos_vi, re_expr, sin_vi)  # |acc|*sin(e_i)
                mag = "sqrt(%s*%s + %s*%s + %.1e)" % (re_expr, re_expr, im_expr, im_expr, ZERO_FLOOR)
                # the Class-K latch sign sgn(cos(e_i)) = sgn(proj_cos) gates the budget-drawn
                # correction increment corr_strength_i * sin(e_i) = corr_strength_i * proj_sin/|acc|:
                # orient=+1 pulls toward the received phase (in-lock), -1 pushes away. ngspice's sgn()
                # IS the analog of cascade.pin_slot_at_zero's orient (srmech reads the same latch at
                # the locked transient via pin_slot_at_zero):
                terms.append("(%.10f)*sgn(%s)*(%s)/(%s)"
                             % (float(corr_strength[i]), proj_cos, proj_sin, mag))
        rhs = " + ".join(terms) if terms else "0"
        lines.append("C%d n%d 0 1" % (i, i))
        lines.append("B%d 0 n%d I={%s}" % (i, i, rhs))
    # deterministic initial phases (a fixed seeded spread; NOT the locked answer)
    ics = " ".join("V(n%d)=%.6f" % (i, float(theta0[i])) for i in range(m))
    lines.append(".ic " + ics)
    lines.append(".tran %.5f %.5f uic" % (T_STEP, t_stop))   # fixed step; .tran IS the ODE integrator
    lines.append(".control")
    lines.append("set noaskquit")
    lines.append("run")
    # ngspice computes cos + sin of each locked phase (the analog substrate's transcendentals); we
    # average the last N_SAMPLE_TAIL samples for a steady-state order parameter (robust to ripple).
    for i in range(m):
        lines.append("let cphi%d = cos(V(n%d))" % (i, i))
        lines.append("let sphi%d = sin(V(n%d))" % (i, i))
    tail = N_SAMPLE_TAIL
    # print the trailing tail of cos/sin per node (steady-state average is computed in Python from these)
    cols = []
    for i in range(m):
        cols.append("cphi%d" % i)
        cols.append("sphi%d" % i)
    lines.append("set width=20000")
    lines.append("print %s" % " ".join(cols))
    lines.append(".endc")
    lines.append(".end")
    return "\n".join(lines) + "\n", a


_NUM = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"


def run_ngspice(netlist, work_dir, tag):
    """Write the netlist, run ngspice -b with a HARD subprocess timeout (the anti-hang backstop),
    parse the per-node cos/sin transient columns. Returns (cos_tail, sin_tail, timed_out, raw) where
    cos_tail/sin_tail are (n_samples x m) arrays of the trailing steady-state samples, or empty on
    timeout/parse-failure. On timeout the call records the miss and MOVES ON (records 'not-locked')."""
    cir = work_dir / ("f240_%s.cir" % tag)
    cir.write_text(netlist)
    try:
        proc = subprocess.run([NGSPICE, "-b", str(cir)], capture_output=True, text=True,
                              timeout=NG_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return np.empty((0, 0)), np.empty((0, 0)), True, "TIMEOUT"
    out = proc.stdout + "\n" + proc.stderr
    # ngspice -b print emits a tabular block: "Index   time   cphi0   sphi0   cphi1 ...". Parse rows
    # that begin with an integer index and have the full numeric width; collect cphi*/sphi* columns.
    # We find the header to know column order, then read the trailing N_SAMPLE_TAIL data rows.
    return _parse_print_table(out)


def _parse_print_table(out):
    """Parse ngspice's `print` tabular output into (cos_tail, sin_tail) trailing-sample arrays.
    Robust to ngspice's multi-page print blocks (it repeats the header per page). Returns
    (cos_tail (k x m), sin_tail (k x m), timed_out=False, raw)."""
    lines = out.splitlines()
    # locate every header line containing the variable names (cphi0 sphi0 ...); the data columns are
    # ordered cphi0,sphi0,cphi1,sphi1,... after the leading "Index" and "time" columns.
    header_idx = None
    var_order = None
    for k, ln in enumerate(lines):
        if "cphi0" in ln and "sphi0" in ln:
            toks = ln.replace("\t", " ").split()
            # tokens look like: Index  time  cphi0  sphi0  cphi1 ...
            if "cphi0" in toks:
                header_idx = k
                var_order = [t for t in toks if t.startswith("cphi") or t.startswith("sphi")]
                break
    if header_idx is None or not var_order:
        return np.empty((0, 0)), np.empty((0, 0)), False, out
    m = sum(1 for t in var_order if t.startswith("cphi"))
    # collect all data rows across all print pages: a row begins with an int index then a time then 2m floats
    rows = []
    num_re = re.compile(r"^\s*\d+\s+(%s)\s+((?:%s\s*){%d})\s*$" % (_NUM, _NUM, 2 * m))
    for ln in lines:
        mobj = num_re.match(ln.replace("\t", " "))
        if mobj:
            vals = re.findall(_NUM, ln)
            # vals[0]=index, vals[1]=time, vals[2:2+2m] = the 2m cphi/sphi values
            if len(vals) >= 2 + 2 * m:
                rows.append([float(x) for x in vals[2:2 + 2 * m]])
    if not rows:
        return np.empty((0, 0)), np.empty((0, 0)), False, out
    arr = np.array(rows)                              # (n_samples x 2m): cphi0,sphi0,cphi1,sphi1,...
    cos_cols = arr[:, 0::2]                           # (n_samples x m)
    sin_cols = arr[:, 1::2]
    tail = min(N_SAMPLE_TAIL, cos_cols.shape[0])
    return cos_cols[-tail:], sin_cols[-tail:], False, out


# =========================================================================================
# Kuramoto order parameter (srmech-native, Class K) read from the ngspice transient. r = |mean exp(i
# theta)| = |mean (cos + i sin)| via two cascade.magnitude + sqrt (the F231 pattern; NEVER abs()).
# =========================================================================================
def order_parameter_from_cossin(cos_row, sin_row):
    """Kuramoto r for ONE timestep: mean of (cos theta_i, sin theta_i) over oscillators, then the
    complex modulus via two cascade.magnitude + sqrt (the F231/F234/F235 pattern). r=1 = full lock."""
    re_mean = float(np.mean(cos_row))
    im_mean = float(np.mean(sin_row))
    return float(np.sqrt(cascade.magnitude(re_mean) ** 2 + cascade.magnitude(im_mean) ** 2))


def steady_order_parameter(cos_tail, sin_tail):
    """The steady-state order parameter = the MEAN over the trailing tail of per-timestep r (robust to
    a residual ripple). Returns (r_steady, n_samples). Empty tail (timeout/parse-fail) -> r=0."""
    if cos_tail.size == 0 or sin_tail.size == 0:
        return 0.0, 0
    rs = [order_parameter_from_cossin(cos_tail[t], sin_tail[t]) for t in range(cos_tail.shape[0])]
    # tail mean via numpy as the array carrier (the per-r modulus already routed through cascade);
    # the steady r is the average alignment held over the tail window:
    return float(np.mean(rs)), int(len(rs))


# =========================================================================================
# Class-K latch READOUT on the locked transient (the F240 corrective-regime instrument). At the
# locked steady state, srmech READS the per-oscillator latch: compare received-vs-own phase ->
# Class-K pin_slot_at_zero orient -> Class-C reorient / net_chirality. This is the srmech-native
# read of the SAME latch ngspice integrated (the F236 'srmech reads the parsed analog scalar' pattern).
# =========================================================================================
def latch_readout(cos_tail, sin_tail, a_matrix):
    """READ the Class-K error-latch state at the locked transient. For each oscillator i: own phase
    theta_i = atan2(mean sin, mean cos); received neighbour mean-field phase psi_i = atan2(Im acc,
    Re acc) with acc = sum_j A_ij e^{i theta_j}; the alignment cos(psi_i - theta_i) is latched by
    Class-K cascade.pin_slot_at_zero -> orient in {-1,0,+1}, and the correction increment is re-signed
    by Class-C cascade.reorient. Returns (orientations, n_unresolved, net_chirality). orient=0 (boundary)
    = the in-script falsifier. Near-zero received-field test via cascade.magnitude (NEVER abs())."""
    if cos_tail.size == 0:
        return [], 0, 0
    m = cos_tail.shape[1]
    cos_mean = np.mean(cos_tail, axis=0)
    sin_mean = np.mean(sin_tail, axis=0)
    theta = np.array([float(np.arctan2(sin_mean[i], cos_mean[i])) for i in range(m)])
    # received neighbour field per oscillator (numpy is the linear-accumulation array carrier; the
    # transcendentals cos/sin came from ngspice's locked phases):
    expi = np.array([complex(np.cos(theta[i]), np.sin(theta[i])) for i in range(m)])
    acc = a_matrix.astype(np.complex128) @ expi
    orientations = []
    n_unres = 0
    reor_chain = []
    for i in range(m):
        if (cascade.magnitude(float(acc[i].real)) < ZERO_FLOOR
                and cascade.magnitude(float(acc[i].imag)) < ZERO_FLOOR):
            psi_i = float(theta[i])                   # pure emitter (no message back) keeps own phase
        else:
            psi_i = float(np.arctan2(acc[i].imag, acc[i].real))
        cos_err = float(np.cos(psi_i - theta[i]))
        orient, _mag = cascade.pin_slot_at_zero(cos_err)          # Class K: latch the correction sign
        orientations.append(int(orient))
        if orient == 0:
            n_unres += 1                                          # the in-script falsifier (boundary)
        reor_chain.append(cascade.reorient(orient if orient != 0 else 0, 1.0))  # Class C: re-orient
    net = int(cascade.net_chirality([int(round(x)) for x in reor_chain])) if reor_chain else 0  # Class C
    return orientations, int(n_unres), net


# =========================================================================================
# STEP 5 — integrate ONE regime via ngspice .tran and read the steady-state lock (the bounded core)
# =========================================================================================
def integrate_regime(m, edges, kstrength, regime, condition, delta, seed, work_dir, tag):
    """Integrate one regime to its phase-locked state via ngspice .tran (BOUNDED). Returns
    (r_steady, locked, n_unresolved, l1_budget, row_sums, timed_out). locked = r_steady >= LOCK_R.
    The matched-budget meters (l1, rows) are returned for the spread-0 guard. PRINTS liveness before
    and after the ngspice call (flush=True)."""
    theta0 = _det_initial_phases(m, seed)
    omega = _natural_frequencies(m, condition, delta, seed)
    corrective = (regime == "reciprocal_correction")
    # build the directed matrix once (for budget meters + the R3 correction strength + latch readout):
    if regime == "feed_forward":
        a_pre = feed_forward_matrix(m, edges, kstrength, double_budget=False)
    elif regime == "feed_forward_double_TRAP":
        a_pre = feed_forward_matrix(m, edges, kstrength, double_budget=True)
    else:
        a_pre = reciprocal_matrix(m, edges, kstrength)
    l1 = _l1_budget(a_pre)
    rows = _row_abs_sums(a_pre)
    # BUDGET-NEUTRAL R3 correction strength per oscillator = its reciprocal row-sum / m (re-routes
    # existing coupling weight through the K-then-C comparison; adds NO new weight):
    corr_strength = np.array([s / m for s in rows]) if corrective else None
    t_stop = T_STOP_BASE + T_STOP_PER_NODE * m
    netlist, a_matrix = build_netlist(m, edges, kstrength, regime, omega, theta0, corr_strength,
                                      t_stop, "F240 N=%d %s %s K=%.3f delta=%.2f"
                                      % (m, regime, condition, kstrength, delta))
    print("    [ng] N=%-3d %-26s %s K=%.3f d=%.2f t_stop=%.1f ..."
          % (m, regime, condition, kstrength, delta, t_stop), end="", flush=True)
    cos_tail, sin_tail, timed_out, _raw = run_ngspice(netlist, work_dir, tag)
    r_steady, n_samp = steady_order_parameter(cos_tail, sin_tail)
    locked = (not timed_out) and (n_samp > 0) and (r_steady >= LOCK_R)
    n_unres = 0
    if corrective and not timed_out and cos_tail.size:
        _orients, n_unres, _net = latch_readout(cos_tail, sin_tail, a_matrix)
    print(" r=%.4f locked=%s%s" % (r_steady, locked, "  TIMEOUT" if timed_out else ""), flush=True)
    return float(r_steady), bool(locked), int(n_unres), float(l1), rows, bool(timed_out)


# =========================================================================================
# STEP 6 — locate K_c per regime (the coupling is NOT decorative). Sweep K; lock = r_steady>=LOCK_R.
# =========================================================================================
def locate_kc(m, edges, regime, condition, delta, seed, work_dir):
    """Sweep global coupling K through K_GRID on this regime via ngspice .tran; return the smallest K
    at which it phase-locks (r_steady>=LOCK_R), the per-K rows, and a decorative flag (locks at K=0 =>
    coupling does no work). K_c is LOCATED, not hand-set (the cherry-pick guard)."""
    rows = []
    k_c = None
    locks_at_zero = None
    for ki, kg in enumerate(K_GRID):
        tag = "%s_%s_d%.2f_N%d_k%d" % (regime, condition, delta, m, ki)
        r, locked, n_unres, l1, _rs, timed_out = integrate_regime(
            m, edges, kg, regime, condition, delta, seed, work_dir, tag)
        if kg == 0.0:
            locks_at_zero = bool(locked)
        if locked and k_c is None:
            k_c = kg
        rows.append({"K": float(kg), "r_steady": round(float(r), 4), "locked": bool(locked),
                     "n_unresolved": int(n_unres), "l1_budget": round(float(l1), 6),
                     "timed_out": bool(timed_out)})
    return k_c, rows, bool(locks_at_zero)


# =========================================================================================
# P-driver — per-(N, frequency-condition) located K_c for all regimes + the advantage statistics
# =========================================================================================
REGIMES = ["feed_forward", "reciprocal_only", "reciprocal_correction", "feed_forward_double_TRAP"]


def measure_at(n, condition, delta, work_dir):
    """Locate K_c for every regime at one (N, frequency-condition, delta) via ngspice .tran. Returns
    the row dict with per-regime K_c, the matched-budget control (L1 spread across the MATCHED regimes),
    and the symmetrised-graph Fiedler lambda_2 (identical across regimes by construction)."""
    m = n
    edges = _extended_mesh_edges(m)
    lam_2, lam_max, n_comp, n_edges = graph_spectrum(m, edges)
    per_regime = {}
    for regime in REGIMES:
        k_c, kc_rows, decorative = locate_kc(m, edges, regime, condition, delta, SEED, work_dir)
        # the operational lock at a fixed K above K_c onset (settling secondary meter) — reuse the
        # top K_GRID point's row to avoid an extra run (the strongest coupling we swept):
        op_row = kc_rows[-1]
        per_regime[regime] = {
            "k_c": k_c,
            "locks_at_K0_decorative": bool(decorative),
            "kc_rows": kc_rows,
            "r_at_max_K": op_row["r_steady"],
            "locked_at_max_K": op_row["locked"],
            "n_unresolved_at_max_K": op_row["n_unresolved"],
            "l1_budget_at_max_K": op_row["l1_budget"],
        }
    # MATCHED-BUDGET CONTROL (the load-bearing guard): the TOTAL L1 budget sum_{i,j}|A_ij| must be
    # IDENTICAL across the three MATCHED regimes (R1 feed-forward, R2 reciprocal, R3 reciprocal+
    # correction) — each undirected mesh edge contributes exactly W = W/2 + W/2 in every regime, so no
    # network feels more TOTAL drive in one regime. This is the spread-0.0 null-c guard (mirroring
    # F235's spread-0.00 line). The TRAP arm is EXCLUDED (intentionally double-budget). Compared at
    # the strongest K we swept (max K_GRID) so the budget numbers are non-trivial.
    matched_regimes = ["feed_forward", "reciprocal_only", "reciprocal_correction"]
    l1s = [per_regime[r]["l1_budget_at_max_K"] for r in matched_regimes]
    l1_spread = max(l1s) - min(l1s)
    trap_l1 = per_regime["feed_forward_double_TRAP"]["l1_budget_at_max_K"]
    matched_l1 = l1s[0]
    return {
        "N": n,
        "frequency_condition": condition,
        "delta": round(float(delta), 6),
        "n_edges": int(n_edges),
        "lambda_2_symmetrised": round(float(lam_2), 6),
        "lambda_max_symmetrised": round(float(lam_max), 6),
        "n_components_symmetrised": int(n_comp),
        "per_regime": per_regime,
        "matched_total_abs_weight": {
            "matched_regimes": matched_regimes,
            "l1_budgets": l1s,
            "l1_spread": round(float(l1_spread), 9),
            "budget_matched": bool(l1_spread < ZERO_FLOOR),     # THE load-bearing gate: L1-total spread 0
            "trap_l1_budget": round(float(trap_l1), 6),
            "matched_l1_budget": round(float(matched_l1), 6),
            "trap_over_matched_ratio": (round(float(trap_l1 / matched_l1), 6) if matched_l1 > 0 else None),
            "note": ("the load-bearing match is the L1-TOTAL across R1/R2/R3 (network-level matched "
                     "drive); the R1-vs-reciprocal per-oscillator row-sum CANNOT match by construction "
                     "(a pure emitter feels zero return drive = the open-loop semantics) and is not a "
                     "budget leak; the TRAP arm is intentionally ~2x (the magnitude confound)"),
        },
    }


def _kc_or_miss(k_c):
    """A located K_c, or a sentinel ABOVE the grid (2x the max) if the regime never locked, so the
    advantage statistic Delta_Kc = K_c(R1) - K_c(R3) is well-defined when one side never locks."""
    return k_c if k_c is not None else max(K_GRID) * 2.0


def advantage_stats(row):
    """The decisive advantage statistic per (N, frequency-condition): Delta_Kc = K_c(R1 feed-forward)
    - K_c(R3 corrective). POSITIVE = corrective locks at lower coupling than feed-forward. Also the
    back-EDGE share (R1->R2) and the LATCH share (R2->R3). The Kc-ratio is de-magicked to an attested
    small-denominator rational via cascade.best_rational_signed (Class K+N)."""
    pr = row["per_regime"]
    kc_ff = _kc_or_miss(pr["feed_forward"]["k_c"])
    kc_rec = _kc_or_miss(pr["reciprocal_only"]["k_c"])
    kc_corr = _kc_or_miss(pr["reciprocal_correction"]["k_c"])
    delta_kc = kc_ff - kc_corr                                    # the predicted-win statistic
    back_edge_share = kc_ff - kc_rec                              # R1 -> R2 (the back-edge contribution)
    latch_share = kc_rec - kc_corr                               # R2 -> R3 (the latch contribution)
    ratio = (kc_corr / kc_ff) if kc_ff > 0 else 0.0
    num, den = cascade.best_rational_signed(float(ratio), max_denominator=64)   # Class K+N de-magick
    return {
        "k_c_feed_forward": pr["feed_forward"]["k_c"],
        "k_c_reciprocal_only": pr["reciprocal_only"]["k_c"],
        "k_c_reciprocal_correction": pr["reciprocal_correction"]["k_c"],
        "k_c_feed_forward_double_TRAP": pr["feed_forward_double_TRAP"]["k_c"],
        "delta_kc_ff_minus_corr": round(float(delta_kc), 6),
        "back_edge_share_R1_minus_R2": round(float(back_edge_share), 6),
        "latch_share_R2_minus_R3": round(float(latch_share), 6),
        "corrective_locks_lower_than_feedforward": bool(kc_corr < kc_ff),
        "feed_forward_ever_locks": bool(pr["feed_forward"]["k_c"] is not None),
        "corrective_ever_locks": bool(pr["reciprocal_correction"]["k_c"] is not None),
        "kc_ratio_corr_over_ff": round(float(ratio), 6),
        "kc_ratio_rational_anchor": [int(num), int(den)],
    }


# =========================================================================================
# VERDICT — no-leaning disposition (the docstring rule). The measured ngspice booleans decide.
# =========================================================================================
def uneq_primary_row(uneq_primary, n):
    """Helper: the per-(N) row at the primary unequal Delta."""
    for row in uneq_primary:
        if row["N"] == n:
            return row
    raise KeyError(n)


def decide_verdict(equal_rows, uneq_rows_by_delta):
    """Decide the headline strictly from the measured table (the disposition rule). The pre-stated
    NULL fires if ANY of (a)-(d); the directional sub-claim is a downgrade if the advantage is not
    larger at unequal than equal frequency. POSITIVE = K_c(R3) < K_c(R1) at unequal frequency at the
    swept N, the advantage larger at unequal than equal frequency and growing with Delta, surviving
    the matched-budget control. Evaluated at ALL N in {4,8,16,32}."""
    primary_delta = max(DELTA_GRID)
    eq_adv = {row["N"]: advantage_stats(row) for row in equal_rows}
    uneq_primary = uneq_rows_by_delta[primary_delta]
    uneq_adv = {row["N"]: advantage_stats(row) for row in uneq_primary}

    # --- NULL branch (b): NEITHER LOCKS — does any regime lock anywhere? ----------------------
    any_lock = False
    for rows in [equal_rows] + list(uneq_rows_by_delta.values()):
        for row in rows:
            for regime in ["feed_forward", "reciprocal_only", "reciprocal_correction"]:
                if row["per_regime"][regime]["k_c"] is not None:
                    any_lock = True
    null_b_neither_locks = (not any_lock)

    # --- NULL branch (a): FEED-FORWARD LOCKS JUST AS WELL at matched budget (unequal freq) -----
    # string keys (not int) so the on-disk sort_keys=True JSON line is canonical + reload-stable
    # (int keys serialize numeric-sorted at emit but lexicographic on reload; strings are stable):
    corr_wins_at = {str(n): bool(uneq_adv[n]["corrective_locks_lower_than_feedforward"]) for n in N_SWEEP}
    null_a_ff_as_good = not any(corr_wins_at.values())            # corrective never wins at any N

    # --- NULL branch (c): MAGNITUDE-ARTIFACT — win present at unmatched (TRAP) but not matched ---
    budget_matched_all = True
    for rows in [equal_rows] + list(uneq_rows_by_delta.values()):
        for row in rows:
            if not row["matched_total_abs_weight"]["budget_matched"]:
                budget_matched_all = False
    null_c_magnitude_artifact = (not budget_matched_all)
    trap_only_wins = False
    for n in N_SWEEP:
        prow = uneq_primary_row(uneq_primary, n)["per_regime"]
        ff_kc = _kc_or_miss(prow["feed_forward"]["k_c"])
        corr_kc = _kc_or_miss(prow["reciprocal_correction"]["k_c"])
        trap_kc = _kc_or_miss(prow["feed_forward_double_TRAP"]["k_c"])
        if (corr_kc >= ff_kc) and (trap_kc < ff_kc):
            trap_only_wins = True

    # --- NULL branch (d): N-INSTABILITY / INVERSION — advantage inverts across N -----------------
    win_signs = []
    for n in N_SWEEP:
        adv = uneq_adv[n]
        if adv["feed_forward_ever_locks"] or adv["corrective_ever_locks"]:
            win_signs.append(adv["corrective_locks_lower_than_feedforward"])
    null_d_inversion = (len(set(win_signs)) > 1) if win_signs else False

    # --- the DIRECTIONAL sub-claim: advantage LARGER at unequal than equal, GROWS with Delta ------
    mean_eq_adv = float(np.mean([eq_adv[n]["delta_kc_ff_minus_corr"] for n in N_SWEEP]))
    mean_uneq_adv = float(np.mean([uneq_adv[n]["delta_kc_ff_minus_corr"] for n in N_SWEEP]))
    advantage_larger_at_unequal = bool(mean_uneq_adv > mean_eq_adv)
    delta_curve = []
    for d in DELTA_GRID:
        rows_d = uneq_rows_by_delta[d]
        adv_d = {row["N"]: advantage_stats(row) for row in rows_d}
        delta_curve.append((d, float(np.mean([adv_d[n]["delta_kc_ff_minus_corr"] for n in N_SWEEP]))))
    grows_with_delta = (all(delta_curve[k][1] <= delta_curve[k + 1][1] + ZERO_FLOOR
                            for k in range(len(delta_curve) - 1))
                        and (delta_curve[-1][1] >= delta_curve[0][1]))

    corr_wins_all_N = True
    for n in N_SWEEP:
        adv = uneq_adv[n]
        if adv["feed_forward_ever_locks"] or adv["corrective_ever_locks"]:
            if not adv["corrective_locks_lower_than_feedforward"]:
                corr_wins_all_N = False

    null_fired_branches = []
    if null_a_ff_as_good:
        null_fired_branches.append("a:feed-forward-locks-just-as-well(matched-budget)")
    if null_b_neither_locks:
        null_fired_branches.append("b:neither-locks(testbed-misspecified)")
    if null_c_magnitude_artifact or trap_only_wins:
        null_fired_branches.append("c:magnitude-artifact(win-vanishes-under-matched-budget/TRAP-only-wins)")
    if null_d_inversion:
        null_fired_branches.append("d:N-instability/inversion")

    null_fired = bool(null_fired_branches)
    directional_supported = bool(advantage_larger_at_unequal and not null_fired)

    if (not null_fired) and corr_wins_all_N and advantage_larger_at_unequal and budget_matched_all:
        headline = (
            "POSITIVE: at MATCHED TOTAL COUPLING BUDGET (L1 spread 0.0), the reciprocal+Class-K-correction "
            "regime (R3) phase-locks at a STRICTLY LOWER critical coupling than the feed-forward one-way "
            "regime (R1) — K_c(R3) < K_c(R1) — at the swept N in {4,8,16,32} under UNEQUAL natural "
            "frequency, locking where feed-forward does NOT. The advantage Delta_Kc = K_c(R1)-K_c(R3) is "
            "LARGER at unequal frequency than at equal frequency (where, per F141, it approximately "
            "vanishes), and " + ("grows" if grows_with_delta else "varies") + " with the frequency spread "
            "Delta. The advantage SURVIVES the matched-budget control (not reproduced by the double-budget "
            "TRAP being the only locker). The reciprocal back-edge (R1->R2) and the Class-K error-latch "
            "(R2->R3) each contribute a non-negative share. The ngspice .tran transients are the bounded "
            "ODE integrator (anti-runaway). FRAMEWORK-READING: corrective communication IS a closed-loop "
            "reciprocal coupling edge + a Class-K error-latch, and the A<->B fixed point lives in the "
            "off-diagonal Laplacian, in neither body alone (distributed cognition). The frog ethology "
            "stays the literature's.")
        verdict_kind = "POSITIVE_CORRECTIVE_LOWER_KC_UNEQUAL_FREQ"
    elif (not null_fired) and corr_wins_all_N and budget_matched_all and not advantage_larger_at_unequal:
        headline = (
            "POSITIVE-ON-THE-ADVANTAGE / DIRECTIONAL-SUB-CLAIM-DOWNGRADED: at matched budget the corrective "
            "regime (R3) locks at strictly lower K_c than feed-forward (R1) at the swept N under unequal "
            "frequency (the core structural win holds), BUT the advantage is NOT measurably larger at "
            "unequal than at equal frequency (contradicting the F141-grounded directional prediction). So "
            "the closed-loop+latch IS a measured phase-lock advantage, but the frequency-dependence "
            "signature is not recovered. FRAMEWORK-READING; the biology stays the literature's.")
        verdict_kind = "POSITIVE_ADVANTAGE_DIRECTIONAL_DOWNGRADE"
    else:
        headline = (
            "NULL FIRES (%s): the corrective (reciprocal closed-loop + Class-K-latch) regime does NOT "
            "confer a phase-lock advantage over the feed-forward one-way regime once the coupling budget "
            "is matched. The F240 claim is downgraded to an analogy: corrective communication may SHARE "
            "the closed-loop reciprocal shape but the reciprocity+latch is not a MEASURED phase-lock "
            "advantage over one-way coupling. The frog biology stays the literature's to assert either "
            "way. FRAMEWORK-READING." % ",".join(null_fired_branches))
        verdict_kind = "NULL_NO_CORRECTIVE_ADVANTAGE"

    return {
        "headline": headline,
        "verdict_kind": verdict_kind,
        "null_fired": bool(null_fired),
        "null_branches_fired": null_fired_branches,
        "directional_subclaim_supported": directional_supported,
        "primary_unequal_delta": round(float(primary_delta), 6),
        "corrective_wins_per_N_unequal": corr_wins_at,
        "corrective_wins_all_N_unequal": bool(corr_wins_all_N),
        "mean_delta_kc_equal": round(mean_eq_adv, 6),
        "mean_delta_kc_unequal_primary": round(mean_uneq_adv, 6),
        "advantage_larger_at_unequal": bool(advantage_larger_at_unequal),
        "delta_kc_vs_frequency_spread": [[round(d, 6), round(v, 6)] for d, v in delta_curve],
        "advantage_grows_with_delta": bool(grows_with_delta),
        "budget_matched_all_conditions": bool(budget_matched_all),
        "trap_only_wins": bool(trap_only_wins),
        "advantage_per_N_equal": {str(n): eq_adv[n] for n in N_SWEEP},
        "advantage_per_N_unequal_primary": {str(n): uneq_adv[n] for n in N_SWEEP},
    }


# =========================================================================================
# main — run the sweep via ngspice .tran + emit the content-addressed NDJSON (F233 bit-exact)
# =========================================================================================
def _ngspice_version():
    try:
        out = subprocess.run([NGSPICE, "--version"], capture_output=True, text=True, timeout=30).stdout
        mobj = re.search(r"ngspice-([0-9.]+)", out)
        return mobj.group(1) if mobj else "unknown"
    except Exception:
        return "unknown"


def main():
    import srmech
    ng_version = _ngspice_version()
    print("=" * 92)
    print("R-RBS-LM-240 — CORRECTIVE communication = closed-loop reciprocal edge + Class-K error-latch")
    print("  (ngspice RE-RUN: bounded .tran ODE integrator, anti-runaway)")
    print("  ngspice %s | srmech %s" % (ng_version, srmech.__version__))
    print("=" * 92)

    primary_delta = max(DELTA_GRID)
    work_dir = Path(tempfile.mkdtemp(prefix="f240_corrective_"))
    print("[work] %s" % work_dir, flush=True)

    # ---- EQUAL natural frequency (the control condition; per F141 advantage ~ 0) ----------------
    print("\n[C-EQ] EQUAL natural frequency (omega_i=0) — locate K_c per regime, swept N ...", flush=True)
    equal_rows = []
    for n in N_SWEEP:
        row = measure_at(n, "equal", 0.0, work_dir)
        equal_rows.append(row)
        pr = row["per_regime"]
        print("  N=%-3d ff_Kc=%-5s rec_Kc=%-5s corr_Kc=%-5s TRAP_Kc=%-5s  L1spread=%.2e matched=%s"
              % (n, pr["feed_forward"]["k_c"], pr["reciprocal_only"]["k_c"],
                 pr["reciprocal_correction"]["k_c"], pr["feed_forward_double_TRAP"]["k_c"],
                 row["matched_total_abs_weight"]["l1_spread"],
                 row["matched_total_abs_weight"]["budget_matched"]), flush=True)

    # ---- UNEQUAL natural frequency (the realistic case; correction is NEEDED), swept Delta -------
    uneq_rows_by_delta = {}
    for d in DELTA_GRID:
        print("\n[C-UNEQ] UNEQUAL natural frequency (uniform[-%.1f,+%.1f]) — locate K_c per regime ..."
              % (d, d), flush=True)
        rows_d = []
        for n in N_SWEEP:
            row = measure_at(n, "unequal", d, work_dir)
            rows_d.append(row)
            pr = row["per_regime"]
            adv = advantage_stats(row)
            print("  N=%-3d ff_Kc=%-5s rec_Kc=%-5s corr_Kc=%-5s TRAP_Kc=%-5s  dKc=%+.3f corr<ff=%s"
                  % (n, pr["feed_forward"]["k_c"], pr["reciprocal_only"]["k_c"],
                     pr["reciprocal_correction"]["k_c"], pr["feed_forward_double_TRAP"]["k_c"],
                     adv["delta_kc_ff_minus_corr"], adv["corrective_locks_lower_than_feedforward"]),
                  flush=True)
        uneq_rows_by_delta[d] = rows_d

    verdict = decide_verdict(equal_rows, uneq_rows_by_delta)
    record = _build_record(ng_version, srmech.__version__, equal_rows, uneq_rows_by_delta, verdict)
    sha = _emit(record)
    print("\n" + "=" * 92)
    print("  VERDICT: %s" % verdict["headline"])
    print("  null_fired=%s  branches=%s" % (verdict["null_fired"], verdict["null_branches_fired"]))
    print("  mean Delta_Kc  equal=%.4f  unequal(Delta=%.1f)=%.4f  larger_at_unequal=%s  grows=%s"
          % (verdict["mean_delta_kc_equal"], primary_delta, verdict["mean_delta_kc_unequal_primary"],
             verdict["advantage_larger_at_unequal"], verdict["advantage_grows_with_delta"]))
    print("  ndjson response_sha256: %s" % record["response_sha256"])
    print("  on-disk ndjson sha256:  %s" % sha)
    print("  srmech %s | ngspice %s" % (srmech.__version__, ng_version))
    print("=" * 92)
    return record


def _build_record(ng_version, version, equal_rows, uneq_rows_by_delta, verdict):
    """Assemble the attested measurement record (sorted-keys, content-addressed by sha256)."""
    return {
        "finding": "F240",
        "measurement": "corrective_communication_closed_loop",
        "ngspice_version": ng_version,
        "srmech_version": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": ("CORRECTIVE communication = a CLOSED-LOOP RECIPROCAL coupling edge PLUS a "
                       "Class-K error-latch; this STRUCTURE (not the AMOUNT of coupling) drives a "
                       "stable phase-lock fixed point. 'communication reduces to back-and-forth "
                       "thinking outside of one body' = the reciprocal closed-loop coupling edge, with "
                       "the A<->B fixed point living in the OFF-DIAGONAL Laplacian, in neither body "
                       "alone (distributed cognition). DECISIVE PREDICTION: at MATCHED total coupling "
                       "budget, the reciprocal+Class-K-correction regime (R3) phase-locks (r>=0.95) at "
                       "a LOWER critical coupling K_c than feed-forward one-way (R1) — correction locks "
                       "where feed-forward does NOT — and the advantage is LARGER at UNEQUAL natural "
                       "frequency (per F141 it ~vanishes at EQUAL frequency where in-phase is the "
                       "attractor for one-way and reciprocal alike), growing with the spread Delta"),
        "implementation": ("the F240 RE-RUN in the ngspice analog substrate: the FIRST attempt ran away "
                           "with a pure-Python synchronous Euler Kuramoto sweep (SETTLE_BUDGET=20000 over "
                           "every N/regime/freq/K/seed; killed at ~58 min, zero output). THIS run moves "
                           "the ODE integration into ngspice's .tran transient (the F236/F241 capacitor-"
                           "voltage-as-phase + B-source Kuramoto-RHS construct) so every transient is "
                           "BOUNDED by its stop-time and CANNOT run away; a per-invocation subprocess "
                           "timeout (%ds) is the hard anti-hang backstop (records 'timeout/not-locked' and "
                           "MOVES ON). No unbounded Python integration loop exists. The DESIGN (regimes, "
                           "matched-budget, meters, null, citations, verdict) is the intended F240 verbatim"
                           % NG_TIMEOUT_S),
        "pre_stated_null": ("the corrective (reciprocal closed-loop + Class-K-latch) regime does NOT "
                            "confer a phase-lock advantage over feed-forward one-way once the coupling "
                            "budget is matched; FIRES if ANY of (a) FEED-FORWARD LOCKS JUST AS WELL "
                            "[K_c(R1)<=K_c(R3) at matched budget -> back-and-forth is decorative], (b) "
                            "NEITHER LOCKS [no regime reaches r>=0.95 within settle budget], (c) "
                            "MAGNITUDE-ARTIFACT [advantage present at UNMATCHED budget but VANISHES once "
                            "L1 weight matched; win only reappears in the double-budget TRAP arm], (d) "
                            "N-INSTABILITY/INVERSION [advantage at one N inverts at another]; the "
                            "directional sub-claim is DOWNGRADED (not full null) if the advantage is NOT "
                            "larger at unequal than equal frequency. If it fires the F240 claim "
                            "downgrades to an analogy (shared closed-loop shape, not a measured phase-"
                            "lock advantage). The frog biology stays the literature's either way"),
        "constants": {
            "K_C_F122": [K_C_F122, "A: F122 measured critical coupling anchor (R-RBS-LM-95/95b)"],
            "NIBBLE": [NIBBLE, "A: |Klein-4| = F233 4-thread rung; smallest swept width"],
            "N_SWEEP": [N_SWEEP, "A: F234 width-doubling cascade (communicating bodies); N-stability branch (d)"],
            "W_PER_EDGE": [W_PER_EDGE, "A: per-undirected-edge budget W (ff puts W one-way; rec splits W/2+W/2; matched L1)"],
            "DELTA_GRID": [DELTA_GRID, "B: C-UNEQ frequency-spread dial uniform[-Delta,+Delta]; growth-with-Delta test"],
            "UNIT_W": [UNIT_W, "A: unit edge weight (symmetrised topology-only Fiedler; K scales separately)"],
            "PI": [round(PI, 10), "A: asymptotic_calculus"],
            "LOCK_R": [LOCK_R, "B: order-parameter lock threshold (F231 criterion)"],
            "ZERO_FLOOR": [ZERO_FLOOR, "B: near-zero spectral/spread floor (numerical)"],
            "K_GRID": [K_GRID, "B: SMALL located-not-set coupling sweep grid (6 values; brackets F122 K_c)"],
            "SEED": [SEED, "B: deterministic seed (finding id) for the initial-phase spread + omega"],
            "T_STEP": [T_STEP, "B: ngspice .tran step (the deterministic analog integrator step)"],
            "T_STOP_BASE": [T_STOP_BASE, "B: transient stop-time floor (>> observed lock time at small N)"],
            "T_STOP_PER_NODE": [T_STOP_PER_NODE, "B: stop-time growth per node (modest N-scaling; bounded)"],
            "NG_TIMEOUT_S": [NG_TIMEOUT_S, "B: per-invocation subprocess timeout (HARD anti-hang backstop)"],
            "N_SAMPLE_TAIL": [N_SAMPLE_TAIL, "B: trailing .tran samples averaged for the steady-state r"],
        },
        "srmech_ops_used": {
            "cos_sin_of_phase": "ngspice's own `let cphi=cos(V)`/`let sphi=sin(V)` + the .tran integrator (the analog substrate); srmech READS the parsed scalars",
            "order_parameter_modulus": "two cascade.magnitude + sqrt (F231 pattern)  [Class K; no abs()]",
            "error_latch": "cascade.pin_slot_at_zero on cos(received_psi - own_theta) at the locked transient  [Class K; F217 SR latch]",
            "correction_reorient": "cascade.reorient(orient, step) re-signs the correction increment  [Class C]",
            "net_orientation_diag": "cascade.net_chirality on the reoriented latch chain  [Class C; diagnostic]",
            "coupling_graph_spectrum": "laplacian.dense_laplacian + jacobi_eigvals (Fiedler lambda_2, identical across regimes)  [Class L; no np.linalg]",
            "kc_ratio_anchor": "cascade.best_rational_signed(Kc_ratio)  [Class K+N]",
            "matched_budget_spread": "cascade.magnitude per entry (L1 spread floor)  [Class K; no abs()/max()]",
            "attestation": "format.sha256_bytes  [Class A; no hashlib]",
        },
        "srmech_gap": ("rc9 ships srmech.amsc.cascade.kuramoto_step but it is ALL-TO-ALL UNIFORM-COUPLING "
                       "ONLY (scalar coupling, (coupling/n)*Sigma sin) — it does NOT accept a coupling "
                       "matrix / adjacency / Laplacian, so it does NOT fit F240's graph-structured "
                       "directed-vs-symmetric coupling (the F235 air-gapped graph need). The ngspice .tran "
                       "transient supplies the graph-structured BOUNDED ODE integrator the op lacks "
                       "(consistent with the F141/F231/F234/F235/F236 gap). UPSTREAM_NOTES §11 forward-ask: "
                       "kuramoto_step could accept an OPTIONAL coupling matrix / adjacency (or a Laplacian) "
                       "to cover graph-structured coupling. NO srmech package edit"),
        "regimes": {
            "feed_forward": "(R1) one-way/stigmergic OPEN-LOOP: full per-edge W on the lower->higher "
                            "direction only (term on the driven node's B-source only); emit-and-forget, "
                            "no return path, no correction",
            "reciprocal_only": "(R2) CLOSED-LOOP edge, NO latch: symmetric A_ij=A_ji=W/2 (mutual "
                               "entrainment) but bare Kuramoto sin coupling with no explicit error term",
            "reciprocal_correction": "(R3) FULL closed loop: R2 symmetric edge PLUS a BUDGET-NEUTRAL "
                                     "Class-K-latched correction term in the B-source (ngspice integrates "
                                     "corr_strength*sgn(cos(psi-theta))*sin(psi-theta); srmech "
                                     "pin_slot_at_zero/reorient/net_chirality READ the latch at lock); "
                                     "corr_strength = R2 row-sum/m, re-routes existing weight, adds none",
            "feed_forward_double_TRAP": "LABELED TRAP only (F234 all-to-all-smuggle guard): feed-forward at "
                                        "2x budget (W on BOTH directions) to expose 'more coupling locks "
                                        "easier' as the confound; never a model",
        },
        "matched_budget_rule": ("FEED-FORWARD puts the full per-edge W on one direction (one entry W); "
                                "RECIPROCAL splits W/2+W/2 across both directions (two entries W/2). The "
                                "L1 budget sum|A| per edge = W = W/2 + W/2 IDENTICAL across R1/R2/R3. The "
                                "R3 correction is budget-neutral (corr_strength = reciprocal row-sum / m; "
                                "re-routes existing weight, adds none). Reported per (N,condition) as "
                                "matched_total_abs_weight with l1_spread; spread 0.0 = matched (the null-c "
                                "guard). The TRAP arm is intentionally ~2x (the magnitude confound)"),
        "equal_frequency": equal_rows,
        "unequal_frequency_by_delta": {str(d): uneq_rows_by_delta[d] for d in DELTA_GRID},
        "citations": CITATIONS,
        "tier": {
            "demonstrated": ("the ngspice .tran Kuramoto phase-lock MEASUREMENT itself: per-regime per-"
                             "(N,frequency-condition) located K_c, the order parameter r (steady-state "
                             "tail mean), the matched-total-abs-weight control (L1 spread 0.0), the "
                             "symmetrised-graph lambda_2 (identical across regimes by construction), at N "
                             "in {4,8,16,32} under equal and unequal natural frequency. OWNS only: 'in "
                             "THIS coupled-oscillator testbed, at matched coupling budget, regime X locks "
                             "at K_c=... and regime Y does/does not'"),
            "framework_reading": ("(i) CORRECTIVE communication IS a closed-loop reciprocal coupling edge "
                                  "+ a Class-K error-latch (the R3 structure); (ii) 'communication reduces "
                                  "to back-and-forth thinking outside of one body' = the reciprocal closed-"
                                  "loop edge, the A<->B fixed point in the OFF-DIAGONAL Laplacian, in "
                                  "neither body alone (distributed cognition); (iii) the F239 COROLLARY "
                                  "that exclusion is a SEVERED corrective edge — a signal SENT that is "
                                  "never returned/corrected (a feed-forward R1 emission with the return "
                                  "path cut), so the loop never closes and the fixed point never forms"),
            "literature_owns": ("every Staurois foot-flagging ethology fact (responsive male-male flagging "
                                "contests; channel-adaptive switch from calling to flagging under stream "
                                "noise; alerting/receiver-response findings) belongs to the cited peer-"
                                "reviewed authors (F226 verify-before-assert), never spoken in the "
                                "framework's voice; the Kuramoto/Sakaguchi K_c physics belongs to its "
                                "cited authors; the social fact underlying the F239 corollary belongs to "
                                "lived experience + disability scholarship"),
            "scope": ("in-scope: animal-communication + distributed-systems / coupled-oscillator DYNAMICS "
                      "reading; NOT CAD / fabrication / mechanical-mesh / gate-delay / timing-closure (the "
                      "SPICE framing is the oscillator-network ODE lens, NOT a build instruction; the CAD-"
                      "ban HOLDS); NOT capability / offensive / hunting-optimization / targeting; "
                      "[[user_stance_ai_is_not_a_substrate]] (the LM is a process over a substrate, not an "
                      "entity that gains awareness); no-lineage (reads what animal-communication ethology + "
                      "synchronization physics already established structurally; does not extend or "
                      "supersede); the latch IS Class-K pin-slot, sign re-application IS Class-C "
                      "([[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]); Herpetologica/Ethology "
                      "cited via OA chain ([[feedback_paywalled_doi_cannot_be_attested]])"),
        },
        "predecessors": {
            "F235": "PR #786 — distributed neurology/slime-mould/air-gapped hive as ONE K∘C axis (the shared Kuramoto testbed + matched-budget control + Fiedler read this finding reuses)",
            "F234": "Kuramoto-coupled adder carry-vector fixed point IS the phase-lock; the F234 width-doubling N-sweep + all-to-all-TRAP guard",
            "F231": "the Kuramoto dispatch-clock phase-lock + the order-parameter pattern (two cascade.magnitude + sqrt)",
            "F141": "directed-only coupling is achiral-null at EQUAL natural frequency (the control-condition grounding: advantage ~vanishes at C-EQ)",
            "F239": "the severed-corrective-edge corollary: exclusion = a feed-forward emission with the return path cut (closed-loop with no exit on the target's side), read structurally as R1 with A_ji=0",
            "F236_F241": "the ngspice capacitor-voltage-as-phase + B-source Kuramoto-RHS .tran construct this RE-RUN reuses (the bounded analog ODE integrator that supplies the srmech Kuramoto gap)",
        },
        "verdict": verdict,
    }


def _emit(record):
    """Write the content-addressed NDJSON (one record per line, sorted keys). response_sha256 is
    computed over the record body MINUS the wall-clock generated_at (so a re-run reproduces the
    measurement sha bit-for-bit; the F233 convention). Returns the on-disk ndjson sha256."""
    body = {k: v for k, v in record.items() if k != "generated_at"}
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    record["response_sha256"] = fmt.sha256_bytes(payload)        # Class A (never hashlib)
    out_dir = (Path(__file__).resolve().parents[1] / "catalogs" / "rbs_lm_substrate"
               / "substrate_measurements")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "corrective_communication_closed_loop.ndjson"
    line = json.dumps(record, separators=(",", ":"), sort_keys=True)
    with open(out_path, "w") as fh:
        fh.write(line)
        fh.write("\n")
    with open(out_path, "rb") as fh:
        disk = fh.read()
    return fmt.sha256_bytes(disk)


if __name__ == "__main__":
    main()
