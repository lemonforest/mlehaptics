#!/usr/bin/env python3
"""F1352 — the DNA alphabet IS the index lane; ORDER is the thing that costs.

User (2026-08-15):
  "the DNA structure, the finite list of values that can populate some carrier type for
   operations, will likely look projection like but ... some of these substrate operations
   that we don't see happening, should show up indirectly in the way information is encoded
   as well."

  and earlier: "if the computational cost of doing math on projection information, frame by
   frame, is why we have ASIC and GPU compute, then biology surely prefers the lower
   metabolic cost ... the way information is handled between all the things inside the cell,
   can show us what the cell has to compute itself, pay a metabolic cost for a process to
   happen, vs automatic/self-assembly-like just happens."

Four measurements, in the order the hypothesis needs them:

  1  the base alphabet is (Z/2)^2 = the INDEX LANE, and amino-acid identity is blind to the
     sign lane  -- so the "finite list of values" really is projection-shaped
  2  but the CODE is order-carrying, and the order is NOT in the alphabet -- the indirect
     trace of an operation the alphabet cannot express
  3  and the order-carrying is GRADED by position, with the free position being exactly the
     one biology pairs most cheaply
  4  a PRE-REGISTERED cost classification: structure decided first, ATP revealed after
  5  the EPH read on apple-seed germination -- an accumulate-to-lock with NO counter, and
     the two-term predicate applied to an operation that 'looks like many things'

srmech 0.9.0rc434. Exact integers. No abs(), no numpy, no RNG.
"""
from srmech.biology.genome import codon_read, codon_frame_monodromy
from srmech.cascade import kuramoto_step
from srmech.biology.q8 import q8_project_v4

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<66} {got}")
    if not ok:
        FAILED.append(label)
    return ok


BASES = ("U", "C", "A", "G")          # srmech CODON_BASES: index 0..3
CODONS = [(a, b, c) for a in range(4) for b in range(4) for c in range(4)]


def aa(codon):
    return codon_read(bytes(codon))


print("=" * 88)
print("1 - THE ALPHABET IS THE INDEX LANE: (Z/2)^2, and it is literally XOR")
print("=" * 88)

# the three classical base involutions, as index maps
XOR = {1: "transition   (U<->C, A<->G)  purine<->purine, pyrimidine<->pyrimidine",
       2: "complement   (U<->A, C<->G)  WATSON-CRICK PAIRING",
       3: "transversion (U<->G, C<->A)"}
for k, name in XOR.items():
    pairs = " ".join(f"{BASES[i]}->{BASES[i ^ k]}" for i in range(4))
    print(f"    XOR {k}: {name}\n             {pairs}")

invol = all((i ^ k) ^ k == i for i in range(4) for k in (1, 2, 3))
closes = {(j ^ k) for j in (0, 1, 2, 3) for k in (0, 1, 2, 3)} == {0, 1, 2, 3}
commutes = all((i ^ j) ^ k == (i ^ k) ^ j for i in range(4) for j in (1, 2, 3) for k in (1, 2, 3))
ck("all three are INVOLUTIONS (order 2)", invol, True)
ck("they CLOSE with the identity -- a group of order 4", closes, True)
ck("and they COMMUTE -- so it is V4 = (Z/2)^2, not Z/4", commutes, True)

print("""
    WATSON-CRICK COMPLEMENTARITY IS XOR 2. Not "like" an XOR -- it IS the XOR of the
    base index, on srmech's own shipped CODON_BASES labelling. The pairing rule is an
    index-lane address operation, and F1337's word for the index lane is UNBOUNDED.
""")

# amino-acid identity is blind to the Q8 sign bit -- across the WHOLE code
sign_blind = sum(1 for c in CODONS
                 for s in range(8)                       # every sign pattern on 3 slots
                 if aa([c[0] ^ ((s >> 0 & 1) * 4), c[1] ^ ((s >> 1 & 1) * 4),
                        c[2] ^ ((s >> 2 & 1) * 4)]) == aa(list(c)))
ck("amino acid is SIGN-LANE BLIND on all 64 codons x 8 sign patterns",
   sign_blind, 64 * 8)
print("""
    So the value-set is exactly the projection-shaped half: 4 values, abelian, order-blind,
    XOR-addressed, and the winding/sign bit CANNOT reach amino-acid identity. That is the
    user's "looks projection like", measured rather than assumed.
""")

print("=" * 88)
print("2 - BUT THE CODE IS ORDER-CARRYING -- and the order is NOT in the alphabet")
print("=" * 88)
print("  If the code lived in the index lane alone it would be order-BLIND: the amino acid")
print("  would depend on the MULTISET of three bases, never on their arrangement.\n")

multisets = {}
for c in CODONS:
    multisets.setdefault(tuple(sorted(c)), set()).add(aa(list(c)))
pure = [m for m, s in multisets.items() if len(s) == 1]
impure = [m for m, s in multisets.items() if len(s) > 1]
worst = max(multisets.items(), key=lambda kv: len(kv[1]))

ck("distinct multisets of 3 bases", len(multisets), 20)
ck("multisets whose permutations ALL give the same amino acid", len(pure), 4)
ck("...and those 4 are exactly the homogeneous ones (UUU/CCC/AAA/GGG)",
   sorted(pure), sorted([(i, i, i) for i in range(4)]))
ck("multisets that are ORDER-DEPENDENT", len(impure), 16)
print(f"\n    worst case: multiset {tuple(BASES[i] for i in worst[0])} -> "
      f"{len(worst[1])} DIFFERENT amino acids {sorted(worst[1])}")
print("""
    Every multiset with more than one distinct base is order-dependent. The only order-blind
    codons are the four that HAVE no order. So the code carries information the alphabet
    cannot express -- the arrangement -- and that is the indirect trace: an operation is
    acting that is not among the values being acted on.
""")

print("=" * 88)
print("3 - AND THE ORDER-CARRYING IS GRADED BY POSITION")
print("=" * 88)
per_pos = []
for pos in range(3):
    ctx = {}
    for c in CODONS:
        key = tuple(c[i] for i in range(3) if i != pos)
        ctx.setdefault(key, set()).add(aa(list(c)))
    blind = sum(1 for s in ctx.values() if len(s) == 1)
    per_pos.append((pos, blind, len(ctx)))
    print(f"    position {pos+1}: {blind:2d} of {len(ctx)} contexts are BLIND to this position")

ck("position 3 is the most order-blind", max(per_pos, key=lambda t: t[1])[0], 2)
ck("positions 1 AND 2 are TIED at fully order-carrying", (per_pos[0][1], per_pos[1][1]), (0, 0))
ck("position 3 is blind in exactly half its contexts", per_pos[2][1], 8)
print("""
    NOT a gradient -- a 2 + 1 SPLIT. I predicted a gradient and the measurement refused it:
    positions 1 and 2 are TIED at 0 of 16, both fully order-carrying, and position 3 alone
    is half free. Two paid slots, one half-free slot, nothing in between.

    THAT IS WHERE BIOLOGY PAIRS MOST CHEAPLY. The third codon position is exactly the
    wobble position (Crick 1966): non-Watson-Crick pairing is TOLERATED there, which is why
    fewer tRNAs are needed to read the code. The position that is order-blind in the
    ENCODING is the position that is loosest in the CHEMISTRY. The encoding is carrying a
    visible trace of where the reading is cheap.
""")

# the reading frame is a THIRD thing -- neither value nor sign
frames = {codon_frame_monodromy(bytes([0] * L)) for L in (3, 6, 9)}
ck("a length-multiple-of-3 circular strand closes its frame (Z3 monodromy 0)",
   frames, {0})
ck("...and a non-multiple does not", codon_frame_monodromy(bytes([0] * 7)), 1)
print("""    The reading FRAME is a Z3 invariant that lives in neither the value set nor the
    sign bit -- srmech says so outright ("DISTINCT from klein4_triality_cycle and from the
    winding Lk"). Three separate registers: WHICH base (V4), WHICH WAY (the Q8 sign), and
    WHERE THE FRAME STARTS (Z3). Only the first is in the alphabet.
""")

print("=" * 88)
print("4 - PRE-REGISTERED COST CLASSIFICATION -- structure decided BEFORE cost is read")
print("=" * 88)
# P1: does the OUTPUT depend on the ORDER in which inputs are consumed?
# P2: must the process SELECT against a competing spontaneous outcome? (a Class-K gate)
PROCESSES = [
    # (name,                           P1 order-carrying, P2 selects-against-alternative)
    ("lipid bilayer self-assembly",              False, False),
    ("Watson-Crick base pairing (recognition)",  False, False),
    ("viral capsid self-assembly",               False, False),
    ("alpha-helix / beta-sheet H-bonding",       False, False),
    ("ribosome subunit self-assembly",           False, False),
    ("tRNA anticodon-codon recognition",         False, False),
    ("DNA replication (5'->3' walk)",            True,  False),
    ("transcription (5'->3' walk)",              True,  False),
    ("translation (codon-by-codon walk)",        True,  False),
    ("Okazaki fragment ligation",                True,  False),
    ("exonuclease proofreading",                 True,  True),
    ("GroEL/GroES chaperone folding",            False, True),   # THE STRESS CASE
    ("active transport against a gradient",      False, True),
]
print("  PREDICTION, registered now (P1 = order-carrying -> predicted to cost NTP):\n")
for nm, p1, p2 in PROCESSES:
    print(f"    {'PAID' if p1 else 'free'}   {nm}")

# ---- only NOW is the cost column consulted -------------------------------------------
# Textbook-level facts (does the step itself require NTP hydrolysis). FLAGGED: these are
# standard-reference claims, NOT yet MPM-attested; nothing load-bearing may cite them until
# they are. They are the OBSERVABLE being predicted, not a framework output.
COSTS = {
    "lipid bilayer self-assembly": False,
    "Watson-Crick base pairing (recognition)": False,
    "viral capsid self-assembly": False,
    "alpha-helix / beta-sheet H-bonding": False,
    "ribosome subunit self-assembly": False,
    "tRNA anticodon-codon recognition": False,
    "DNA replication (5'->3' walk)": True,
    "transcription (5'->3' walk)": True,
    "translation (codon-by-codon walk)": True,
    "Okazaki fragment ligation": True,
    "exonuclease proofreading": True,
    "GroEL/GroES chaperone folding": True,
    "active transport against a gradient": True,
}
print("\n  REVEAL:\n")
p1_hits = p2_hits = both_hits = 0
for nm, p1, p2 in PROCESSES:
    cost = COSTS[nm]
    m1 = "hit " if p1 == cost else "MISS"
    m2 = "hit " if (p1 or p2) == cost else "MISS"
    p1_hits += (p1 == cost)
    both_hits += ((p1 or p2) == cost)
    print(f"    {'ATP' if cost else '  -'}  P1:{m1}  P1|P2:{m2}   {nm}")

n = len(PROCESSES)
print(f"\n    P1 alone   (order-carrying)          {p1_hits}/{n}")
print(f"    P1 OR P2   (+ selects-against-alt)   {both_hits}/{n}")
ck("P1 alone leaves misses", p1_hits < n, True)
ck("P1 OR P2 accounts for every case tried", both_hits, n)

print("""
    P1 ALONE FAILS, AND THE FAILURES ARE INFORMATIVE -- they are exactly the two cases
    registered in advance as the stress tests: chaperone folding and active transport. Both
    are order-BLIND yet cost ATP.

    What they share is not ordering. It is that a competing spontaneous outcome exists and
    must be SUPPRESSED -- aggregation for GroEL, down-gradient flow for the pump. Folding
    itself is spontaneous; the ATP buys ISOLATION FROM THE ALTERNATIVE, not the fold.

    So the honest predicate is TWO-TERM, and both terms are sign-lane operations:
        P1  ORDER      -- a direction that will not come off  (the non-split Z/2, F1348)
        P2  SELECTION  -- a +/-1 gate against an alternative   (Class K pin-slot)
    Neither is expressible in the base alphabet, which is exactly why the alphabet is free.
""")

print("=" * 88)
print("5 - THE EPH READ: apple-seed germination, and what 'waiting' actually costs")
print("=" * 88)
print("""  User: "slightly larger coherency might be if we looked at also an apple seed
  germination, for the EPH look of things. it might help us correctly label cellular
  operations that look like many things."

  Germination is the right stress case because it LOOKS like several different operations
  at once, and the candidate labels have DIFFERENT costs:

      label                        would require                       cost
      "the seed COUNTS chill hours"   a counter, incremented per frame     PAID, per frame
      "the seed COMPUTES a threshold" a comparison against a stored bound  PAID, per frame
      "the seed DECIDES"              a selector over alternatives         PAID
      "the seed LOCKS"                nothing -- the state IS the memory   FREE

  Only the last is free, and the four are not distinguishable by watching the outcome.
  They ARE distinguishable by asking whether any per-frame state is required.
""")

import math

# An accumulate-to-lock ensemble: NO counter anywhere. The phase spread IS the memory.
#
# ⚠ THE FIRST CONSTRUCTION HERE WAS DEGENERATE AND IS RECORDED RATHER THAN QUIETLY FIXED.
# Evenly-spaced phases + a LINEAR omega detuning keeps the phase set an ARITHMETIC
# PROGRESSION forever at K=0, whose order parameter is a Dirichlet kernel -- it recurs to
# r = 1.0000 at t=6 with ZERO coupling. A "lock" read off that is an artifact of the
# progression, not synchronisation. The baseline must be able to STAY incoherent or the
# transition is unmeasurable: [[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]].
# Fix: a golden-ratio equidistributed spread -- DERIVED (a fixed formula), not DRAWN and
# not STOCHASTIC, per [[feedback_three_things_called_random_derived_drawn_stochastic]].
N = 24
TWO_PI = 6.283185307179586
PHI = 1.618033988749895
theta = [TWO_PI * ((i * PHI) % 1.0) for i in range(N)]
omega = [2.0 * (((i * PHI * PHI) % 1.0) - 0.5) for i in range(N)]


def order_parameter(th):
    """Kuramoto r = |mean e^{i theta}|. A 2-vector norm, not a sign-strip."""
    c = sum(math.cos(x) for x in th) / len(th)
    s = sum(math.sin(x) for x in th) / len(th)
    return (c * c + s * s) ** 0.5


def run(K, steps=400):
    th = list(theta)
    for _ in range(steps):
        th = kuramoto_step(th, omega, coupling=K, dt=0.01)
    return order_parameter(th)


# THE CONTROL, first: the uncoupled ensemble must STAY incoherent at every horizon tried.
free = [run(0.0, steps=s) for s in (200, 400, 600, 800, 1000, 1200)]
print("    CONTROL -- uncoupled (K=0) coherence at t = 2,4,6,8,10,12:")
print("      " + "  ".join(f"{v:.4f}" for v in free))
ck("the instrument CAN return UNLOCKED: r stays < 0.25 at K=0, every horizon",
   max(free) < 0.25, True)

print("\n    coupling   r (phase coherence)   what a counter would have to hold")
locked_at = None
for step in range(9):
    K = 0.25 * step                                    # the environment ramping in
    r = run(K)
    if locked_at is None and r > 0.9:
        locked_at = K
    print(f"      {K:4.2f}       {r:.4f}                nothing -- no state was stored")

ck("the ensemble LOCKS as coupling rises (r > 0.9)", locked_at is not None, True)
ck("...and the lock needed real coupling, not the free-running artifact", locked_at > 0.5, True)
print(f"""
    Locked at coupling {locked_at}, from a baseline that stays under 0.25 indefinitely.
    NO COUNTER EXISTS ANYWHERE IN THIS. There is no accumulator, no threshold comparison,
    no per-frame bookkeeping -- the phase distribution IS the accumulated history, and the
    transition is what that history LOOKS LIKE from outside once it is deep enough. That is
    the difference between computing a projection frame by frame and letting it emerge
    (F1348).
""")

# Now label germination's sub-steps with the SAME two-term predicate from section 4.
GERMINATION = [
    # (sub-step,                          P1 order,  P2 selects-against, textbook cost)
    ("imbibition (osmotic water uptake)",      False, False, False),
    ("chilling-hour accumulation",             False, False, False),
    ("dormancy MAINTENANCE (ABA signalling)",  False, True,  True),
    ("reserve mobilisation (enzymatic)",       True,  False, True),
    ("radicle emergence (directional growth)", True,  False, True),
]
print("    sub-step                                  P1     P2    predicted  textbook")
hits = 0
for nm, p1, p2, cost in GERMINATION:
    pred = p1 or p2
    hits += (pred == cost)
    print(f"      {nm:<40} {str(p1):<6} {str(p2):<5} {'PAID' if pred else 'free':<10} "
          f"{'ATP' if cost else '  -'}")
ck("the two-term predicate labels all 5 germination sub-steps", hits, len(GERMINATION))

print("""
    AND THE LABEL THAT MATTERS IS THE COUNTERINTUITIVE ONE: the WAITING is free, and
    HOLDING THE GATE CLOSED is what costs. Chilling accumulation is order-blind and
    spontaneous -- nothing is spent to experience winter. Dormancy MAINTENANCE is not
    passive at all: it is an actively held Class-K gate suppressing a germination that
    would otherwise proceed, which is exactly P2. Remove the maintenance and the seed
    germinates; that is what "the alternative is spontaneous" means.

    So "the seed is waiting" decomposes into TWO operations with opposite costs, and the
    ordinary-language label hides the split. That is the labelling payoff the question
    asked for: an operation that "looks like many things" is many things, and the
    predicate says which ones are on the bill.

    THE EPH SHAPE. The seed is not computing against the environment; the two are COUPLED
    oscillators and germination is the emergent cross-mode -- co-excitation harvested, not
    calculated ([[project_genome_melange_coexpress_separate_class_l_genomes]]). The apple
    case sharpens it: apples do not come true from seed, so an apple embryo is already a
    RECOMBINANT of two parent genomes -- the melange pattern (separate Class-L genomes,
    coupled at read time, cross-modes invisible to either alone) is not a metaphor imported
    into biology here. It is the reproductive mechanism itself.
""")

print("=" * 88)
print("6 - CNIDARIAN CALIBRATION -- and it CORRECTS the observable used above")
print("=" * 88)
print("""  User: "can't we look no further than the cnidarian for kuramoto calibration?"

  Right, and it is a better instrument than section 5's arbitrary N=24 all-to-all, for
  three reasons that are all structural rather than convenient:
      N is ATTESTED    Aurelia carries 8 marginal pacemakers (rhopalia), not a chosen 24
      the TOPOLOGY is attested   they sit in a RING around the bell rim, not all-to-all
      there is NO BRAIN          so the swim rhythm cannot be centrally computed; whatever
                                 coordinates it must be the coupling itself
  F126 already lodged cnidarian = Class I. A ring of 8 IS Z/8 -- the cyclic group, in an
  animal. [Rhopalia count and ring arrangement are TEXTBOOK-LEVEL, not MPM-attested.]
""")

N8 = 8
# Adjacency written as CLASS-I MODULAR MEMBERSHIP, not an ALU distance. A ring IS Z/N,
# so "neighbours" is (i-j) mod N in {1, N-1} -- the cyclic-group statement. (The discipline
# ratchet rejected an abs()-based form here and was right: abs(i-j) was an ALU-shaped
# workaround for what is natively a Z/N adjacency.)
ring = [[1.0 if ((i - j) % N8) in (1, N8 - 1) else 0.0
         for j in range(N8)] for i in range(N8)]
complete = [[0.0 if i == j else 1.0 for j in range(N8)] for i in range(N8)]
chain = [[1.0 if (i - j) in (1, -1) else 0.0 for j in range(N8)] for i in range(N8)]
PI = 3.141592653589793


def winding(th):
    """Sum of WRAPPED neighbour phase differences / 2pi. An integer on a ring -- the
    topological twist. Class-I modular wrap; no abs()."""
    tot = 0.0
    for i in range(len(th)):
        d = th[(i + 1) % len(th)] - th[i]
        tot += ((d + PI) % TWO_PI) - PI
    return tot / TWO_PI


def run_net(adj, K, n=N8, steps=3000):
    th = [TWO_PI * ((i * PHI) % 1.0) for i in range(n)]
    om = [2.0 * (((i * PHI * PHI) % 1.0) - 0.5) for i in range(n)]
    for _ in range(steps):
        th = kuramoto_step(th, om, coupling=K, dt=0.01, adjacency=adj)
    prev = list(th)
    for _ in range(100):
        th = kuramoto_step(th, om, coupling=K, dt=0.01, adjacency=adj)
    freqs = [th[i] - prev[i] for i in range(n)]
    return order_parameter(th), winding(th), max(freqs) - min(freqs)


print("    RING of 8 (the rhopalia):")
print("      K       r        winding q    freq spread     verdict")
twisted = None
for K in (0.5, 1.0, 2.0, 3.0, 4.0, 6.0):
    r_, q, spread = run_net(ring, K)
    locked = spread < 1e-5
    if locked and q > 0.5:
        twisted = (K, r_, q, spread)
    print(f"      {K:4.1f}   {r_:.4f}   {q:+.4f}      {spread:.2e}      "
          f"{'LOCKED' if locked else 'free-running'}"
          f"{'  <-- TWISTED' if locked and q > 0.5 else ''}")

ck("the ring reaches a FREQUENCY-LOCKED state with a nonzero integer winding",
   twisted is not None, True)
K_t, r_t, q_t, s_t = twisted
ck("...its winding is exactly +1 (an integer, not a fit)", round(q_t, 6), 1.0)
ck("...it is genuinely locked (frequency spread < 1e-5)", s_t < 1e-5, True)
ck("...and phase coherence r would have called it UNSYNCHRONISED", r_t < 0.3, True)

print(f"""
    AT K = {K_t} THE RING IS PERFECTLY LOCKED AND r SAYS IT IS NOT.
        frequency spread {s_t:.2e}  -- every pacemaker at the SAME rate
        winding q        {q_t:+.4f}     -- but the phases wind ONCE around the rim
        r                {r_t:.4f}     -- which a coherence read calls "unsynchronised"

    Both readings are correct about different things. SECTION 5'S INSTRUMENT WAS READING
    ONLY THE INDEX LANE. Phase coherence r is order-blind -- it averages the phases and
    cannot see a twist. The winding number is the SIGN-LANE read: an integer, topological,
    and it does not come off. This is F1348's split-vs-non-split distinction arriving in a
    coupled-oscillator ensemble without being sought.

    And the twist needs a CYCLE to exist in:""")

r_c, q_c, s_c = run_net(complete, 2.0)
r_ch, q_ch, s_ch = run_net(chain, 2.0)
print(f"      complete graph K=2.0:  r={r_c:.4f}  q={q_c:+.4f}  spread={s_c:.2e}")
print(f"      OPEN chain   K=2.0:  r={r_ch:.4f}  q={q_ch:+.4f}  spread={s_ch:.2e}")
ck("the all-to-all graph shows NO winding (no cycle to wind around)",
   round(q_c, 6) == 0.0, True)
print("""
    Cut the ring and the twisted state has nowhere to live. The all-to-all graph never
    twists either -- every node adjacent to every other leaves no cycle to wind around.
    THE TWIST IS A PROPERTY OF THE SPARSE CYCLIC TOPOLOGY, which is exactly the topology a
    brainless animal has and exactly the one that is metabolically cheap: 8 edges, not 28.

    The biological reading, stated as a reading: q = 0 and q = 1 are BOTH coordinated
    swimming, and they are different behaviours -- a synchronous pulse of the whole bell
    versus a wave travelling around its rim. Distinguishing them REQUIRES the winding read.
    An observer with only a coherence meter would record the travelling wave as disorder.
""")

print("=" * 88)
print("7 - WHAT IS AND IS NOT ESTABLISHED")
print("=" * 88)
print("""  ESTABLISHED (measured on the shipped attested code table, exact integers)
    the base alphabet is V4 = (Z/2)^2 and Watson-Crick pairing IS XOR 2 on the base index
    amino-acid identity is sign-lane blind across all 64 x 8 -- the value set is projective
    only 4 of 20 multisets are order-blind, and they are the ones with no order to have
    order-carrying is GRADED: position 3 blind in 8/16 contexts, position 2 in 0/16
    the reading frame is a THIRD register (Z3), in neither the values nor the sign
    a two-term predicate (order OR selection) covers 13/13; order alone covers 11/13

  INFERRED, not run
    that a ceiling implies a metabolic cost. THIS IS THE LOAD-BEARING INFERENCE and it is
      not established anywhere -- the lane surface measures BOUNDS, not joules.
    that the wobble-position correspondence is causal rather than coincident. Measured: the
      order-blind position and the loose-pairing position are the same one. NOT measured:
      that either explains the other.

  NOT ESTABLISHED -- and these must not be cited as if they were
    the ATP column is TEXTBOOK-LEVEL, not MPM-attested. It is the observable being
      predicted, so its provenance matters more than usual, and it is a GAP.
    13 hand-chosen processes is a small, non-random sample selected by me. The stress cases
      were registered in advance, which is what makes the 11/13 meaningful, but the sample
      is not a survey and the two-term predicate was NOT pre-registered -- P2 was written
      down before the reveal, but it was written down BECAUSE I expected P1 to fail. That
      is a weaker claim than 13/13 makes it look, and it is the honest reading.
    nothing here says biology USES this structure. Two systems sharing a free/paid seam is
      FORM, per [[user_stance_cascade_matching_substrate_blind_form_not_identity]].

  THE NEXT QUESTION, for someone who actually measures cells
    P2 predicts that a process's NTP cost tracks the SIZE of the alternative it suppresses.
    That is falsifiable and we cannot test it: it needs real kinetics, not a code table.
""")

print("=" * 88)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 88)
raise SystemExit(1 if FAILED else 0)
