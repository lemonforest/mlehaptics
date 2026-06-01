"""mechanism_loop_bind.py — Reaction MECHANISM = directed loop-bind cascade (F278 "SOON").

ITEM: stoichiometry reaction MECHANISM = loop-bind directed cascade (F278 sec-C "soon")
TASK: embed each mechanistic step as a random unit octonion; loop-bind in the documented
  order vs a wrong order -> cosine (predict < 1, order-distinct); confirm a commutative
  klein4_bundle washes the order; and demonstrate that NESTING (sub-steps) = non-associative
  bracketing.

BENIGN KNOWN MECHANISM: acid-catalysed ester hydrolysis (Fischer esterification reverse;
  4 documented steps, textbook SN-ac2 path, e.g. March's Advanced Organic Chemistry §10-12):
    Step 1: Protonation of carbonyl oxygen    (H+ attacks C=O lone pair)
    Step 2: Water nucleophilic addition       (H2O attacks activated C=O+)
    Step 3: Proton transfer                   (O-H rearrangement)
    Step 4: Tetrahedral collapse + departure  (C-O bond breaks, ester reformed or hydrolysed)
  The ORDER matters: protonation must precede nucleophilic attack (Step 1 < Step 2).
  Reference: March, J. "Advanced Organic Chemistry" 4th ed. (1992); Clayden et al.
  "Organic Chemistry" 2nd ed. (2012) §12.

STRUCTURAL ENCODING (what we're doing; NOT reaction prediction/design):
  Each step -> a random unit octonion (content-addressed seed; reproducible).
  loop_bind(s1, loop_bind(s2, loop_bind(s3, s4))) = the directed cascade in documented order.
  loop_bind(s2, loop_bind(s1, loop_bind(s3, s4))) = wrong order (Step 1 and Step 2 swapped).
  cosine_correct vs cosine_wrong: if order is encoded, cosine_correct > cosine_wrong.
  klein4_bundle([s1, s2, s3, s4]) = commutative majority-vote bundle (washes order -> same
    regardless of permutation -> confirms commutative vs non-commutative contrast).
  NESTING: steps 3+4 form a sub-reaction (the proton-transfer + collapse are one tetrahedral-
    intermediate block); non-associativity means loop_bind(loop_bind(s3, s4), s12_block) !=
    loop_bind(s3, loop_bind(s4, s12_block)). This is the sub-step bracketing residue.

SCOPE: structural encoding ONLY; benign textbook mechanism; no synthesis routes / prediction.
CLASS-K clean: inner products via np.dot (no abs()); sign handling via loop_conj (Class C).
SRMECH: native loop_bind / loop_associator / klein4_bundle from srmech.amsc.hdc.
"""
import sys
import numpy as np
sys.path.insert(0, '/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/rbs_lm_research')

from srmech.amsc.hdc import loop_bind, loop_conj, loop_associator, klein4_bundle, klein4_random
import loop_bind_moufang as oracle  # for consistency checks

DIM = 8   # octonion / k=7
K4DIM = 8  # klein4 hypervector dimension (same for comparability)

# ---------------------------------------------------------------------------
# Seed discipline: each step gets a deterministic seed (attested-B; reproducible).
# Seeds are NOT magic: each is the step index * 100 + 7, a trivial formula.
# ---------------------------------------------------------------------------
STEP_SEEDS = {
    "step1_protonation": 107,
    "step2_water_addition": 207,
    "step3_proton_transfer": 307,
    "step4_tetrahedral_collapse": 407,
}

def random_unit_octonion(seed: int) -> np.ndarray:
    """Random unit octonion from seed (attested-B; reproducible)."""
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(DIM)
    norm_sq = float(np.dot(v, v))  # Class-K clean (no abs())
    return v / np.sqrt(norm_sq)

def random_klein4_vec(seed: int) -> np.ndarray:
    """Random Klein-4 hypervector (elements in {0,1,2,3}) from seed (attested-B)."""
    return klein4_random(K4DIM, rng=np.random.default_rng(seed))

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity via inner product (Class-K clean; no abs())."""
    # loop_conj gives the conjugate; for REAL-VALUED comparison just use np.dot on normalized
    # (the full octonion inner product <a, b> = Re(conj(a) * b) = dot(a, b) for real octonions)
    ab = float(np.dot(a, b))
    norm_a = np.sqrt(float(np.dot(a, a)))
    norm_b = np.sqrt(float(np.dot(b, b)))
    return ab / (norm_a * norm_b)

def normsq(v: np.ndarray) -> float:
    """Inner-product norm^2 — Class-K clean."""
    return float(np.dot(v, v))

# ---------------------------------------------------------------------------
# Consistency checks (oracle vs native; run before the experiment)
# ---------------------------------------------------------------------------
def check_consistency():
    """Verify native ops match oracle on the step vectors."""
    rng = np.random.default_rng(12345)
    e = lambda i: oracle.e(i)
    # 1. loop_bind: exact match on 8x8 basis (already verified globally, spot-check here)
    max_diff = 0.0
    for i in range(DIM):
        for j in range(DIM):
            diff = float(np.max(np.abs(loop_bind(e(i), e(j)) - oracle.loop_bind(e(i), e(j)))))
            if diff > max_diff:
                max_diff = diff
    lb_ok = max_diff < 1e-12
    # 2. loop_associator: exact match on random triples
    max_adiff = 0.0
    for _ in range(10):
        a, b, c = rng.standard_normal(DIM), rng.standard_normal(DIM), rng.standard_normal(DIM)
        diff = float(np.max(np.abs(loop_associator(a, b, c) - oracle.associator(a, b, c))))
        if diff > max_adiff:
            max_adiff = diff
    la_ok = max_adiff < 1e-10
    # 3. klein4_bundle commutativity: bundle([v,w]) == bundle([w,v]) for k4 vectors
    kv = klein4_random(K4DIM, rng=np.random.default_rng(77))
    kw = klein4_random(K4DIM, rng=np.random.default_rng(88))
    k4_ab = klein4_bundle(kv, kw)
    k4_ba = klein4_bundle(kw, kv)
    k4_comm_ok = np.array_equal(k4_ab, k4_ba)
    return {
        "loop_bind_8x8_max_diff": max_diff,
        "loop_bind_exact": lb_ok,
        "loop_associator_max_diff": max_adiff,
        "loop_associator_exact": la_ok,
        "klein4_bundle_commutative": k4_comm_ok,
    }

# ---------------------------------------------------------------------------
# Experiment 1: Directed order encoding
#   correct_cascade  = loop_bind(s1, loop_bind(s2, loop_bind(s3, s4)))
#   wrong_cascade    = loop_bind(s2, loop_bind(s1, loop_bind(s3, s4)))  [s1/s2 swapped]
# ---------------------------------------------------------------------------
def experiment_order_encoding(steps: dict) -> dict:
    """Encode the mechanism steps as a directed loop-bind cascade; test order sensitivity."""
    s1 = steps["step1_protonation"]
    s2 = steps["step2_water_addition"]
    s3 = steps["step3_proton_transfer"]
    s4 = steps["step4_tetrahedral_collapse"]

    # Correct order: right-associative fold (reads "s1 first, then s2, ...")
    correct = loop_bind(s1, loop_bind(s2, loop_bind(s3, s4)))
    # Wrong order: swap s1 and s2 (protonation <-> water attack — documented impossible order)
    wrong   = loop_bind(s2, loop_bind(s1, loop_bind(s3, s4)))

    # Cosine between correct and wrong
    cos_cw = cosine(correct, wrong)

    # Reference: cosine of correct cascade with itself = 1.0
    cos_self = cosine(correct, correct)

    # Are they distinct?
    order_distinguishable = cos_cw < cos_self - 1e-9

    # All 24 permutations of 4 steps -> spread of cosines vs correct
    from itertools import permutations
    step_list = [s1, s2, s3, s4]
    perm_cosines = []
    for perm in permutations(step_list):
        p = loop_bind(perm[0], loop_bind(perm[1], loop_bind(perm[2], perm[3])))
        perm_cosines.append(cosine(correct, p))
    # correct order perm has cosine == 1.0; rest should be < 1.0
    n_identity = sum(1 for c in perm_cosines if c > 1.0 - 1e-9)
    n_distinct  = sum(1 for c in perm_cosines if c < 1.0 - 1e-9)

    return {
        "correct_norm_sq": normsq(correct),
        "wrong_norm_sq": normsq(wrong),
        "cosine_correct_vs_wrong": cos_cw,
        "cosine_correct_vs_self": cos_self,
        "order_distinguishable": order_distinguishable,
        "n_permutations": len(perm_cosines),
        "n_perm_identity_cosine": n_identity,
        "n_perm_distinct": n_distinct,
        "min_perm_cosine": float(min(perm_cosines)),
        "max_perm_cosine": float(max(perm_cosines)),
    }

# ---------------------------------------------------------------------------
# Experiment 2: Klein-4 bundle washes the order
#   klein4_bundle([k1, k2, k3, k4]) should be invariant to permutation.
#   Each step encoded as a Klein-4 hypervector (same step seed, different space).
# ---------------------------------------------------------------------------
def experiment_klein4_order_wash(k4_steps: dict) -> dict:
    """Confirm klein4_bundle is order-invariant (commutative majority vote)."""
    from itertools import permutations
    step_list = list(k4_steps.values())
    ref_bundle = klein4_bundle(*step_list)
    all_same = True
    n_perm = 0
    for perm in permutations(step_list):
        p_bundle = klein4_bundle(*perm)
        n_perm += 1
        if not np.array_equal(ref_bundle, p_bundle):
            all_same = False
            break
    return {
        "n_permutations_checked": n_perm,
        "all_bundles_identical": all_same,
        "order_washed": all_same,
    }

# ---------------------------------------------------------------------------
# Experiment 3: Non-associative bracketing = sub-step nesting
#   Steps 3+4 form the "tetrahedral intermediate" sub-block.
#   sub_block_A = loop_bind(loop_bind(s3, s4), loop_bind(s1, s2))  [post then pre]
#   sub_block_B = loop_bind(s3, loop_bind(s4, loop_bind(s1, s2)))  [different bracketing]
#   These differ by the associator residue (Class-K non-zero outside Fano lines).
# ---------------------------------------------------------------------------
def experiment_bracketing_nesting(steps: dict) -> dict:
    """Non-associativity = the mechanism's nesting (sub-step bracketing) is distinct."""
    s1 = steps["step1_protonation"]
    s2 = steps["step2_water_addition"]
    s3 = steps["step3_proton_transfer"]
    s4 = steps["step4_tetrahedral_collapse"]

    # Two bracketings of the same 4 steps (different nesting trees)
    # Bracketing A: ((s3 * s4) * (s1 * s2)) — sub-block [3,4] then [1,2]
    brack_A = loop_bind(loop_bind(s3, s4), loop_bind(s1, s2))
    # Bracketing B: (s3 * (s4 * (s1 * s2))) — flat right-fold starting at s3
    brack_B = loop_bind(s3, loop_bind(s4, loop_bind(s1, s2)))

    cos_AB = cosine(brack_A, brack_B)

    # The associator residue for (s3, s4, loop_bind(s1,s2)) quantifies how distinct
    inner_block = loop_bind(s1, s2)
    assoc_resid = loop_associator(s3, s4, inner_block)
    assoc_norm_sq = normsq(assoc_resid)

    # Confirm native loop_associator == oracle associator on this specific triple
    oracle_resid = oracle.associator(s3, s4, inner_block)
    assoc_oracle_match = float(np.max(np.abs(assoc_resid - oracle_resid))) < 1e-10

    distinct_bracketings = cos_AB < 1.0 - 1e-9

    return {
        "brack_A_norm_sq": normsq(brack_A),
        "brack_B_norm_sq": normsq(brack_B),
        "cosine_A_vs_B": cos_AB,
        "distinct_bracketings": distinct_bracketings,
        "associator_residue_norm_sq": assoc_norm_sq,
        "associator_nonzero": assoc_norm_sq > 1e-9,
        "associator_oracle_match": assoc_oracle_match,
    }

# ---------------------------------------------------------------------------
# Jacobi sum sanity: no Laplacian used here; instead check that the
# klein4_bundle is deterministic and permutation-invariant (the analogue
# of trace == 2|E| for the commutative-reference path).
# ---------------------------------------------------------------------------
def experiment_klein4_bundle_internal_consistency(k4_steps: dict) -> dict:
    """Internal consistency: klein4_bundle is deterministic and permutation-invariant."""
    step_list = list(k4_steps.values())
    bundle = klein4_bundle(*step_list)
    deterministic_ok = np.array_equal(bundle, klein4_bundle(*step_list))
    from itertools import permutations
    perm_consistent = all(np.array_equal(bundle, klein4_bundle(*p)) for p in permutations(step_list))
    return {
        "deterministic": deterministic_ok,
        "permutation_invariant": perm_consistent,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("mechanism_loop_bind.py — Reaction MECHANISM = directed loop-bind cascade")
    print("F278 sec-C 'SOON': mechanism step order encoded via loop-bind non-commutativity")
    print("=" * 70)
    print()
    print("Mechanism: acid-catalysed ester hydrolysis (SN-ac2 path, textbook)")
    print("  Step 1: Protonation of carbonyl oxygen")
    print("  Step 2: Water nucleophilic addition")
    print("  Step 3: Proton transfer")
    print("  Step 4: Tetrahedral collapse + departure")
    print("  Reference: March's Advanced Organic Chemistry 4th ed. §10-12; Clayden §12")
    print()

    # Build step vectors: octonion (loop_bind cascade) and Klein-4 (commutative reference)
    steps    = {k: random_unit_octonion(v) for k, v in STEP_SEEDS.items()}
    k4_steps = {k: random_klein4_vec(v)    for k, v in STEP_SEEDS.items()}
    # Verify unit norm for octonions (Class-K clean: norm_sq check, no abs())
    for name, v in steps.items():
        ns = normsq(v)
        assert abs(ns - 1.0) < 1e-12, f"step {name} not unit: norm_sq={ns}"

    # --- Consistency checks ---
    print("--- CONSISTENCY CHECKS (native vs oracle) ---")
    cc = check_consistency()
    print(f"  loop_bind 8x8 max |native-oracle|: {cc['loop_bind_8x8_max_diff']:.2e}  -> {'PASS' if cc['loop_bind_exact'] else 'FAIL'}")
    print(f"  loop_associator max |native-oracle|: {cc['loop_associator_max_diff']:.2e}  -> {'PASS' if cc['loop_associator_exact'] else 'FAIL'}")
    print(f"  klein4_bundle commutative on pair: {cc['klein4_bundle_commutative']}")
    print()

    # --- Experiment 1: Order encoding ---
    print("--- EXPERIMENT 1: Order encoding (loop_bind directed cascade) ---")
    r1 = experiment_order_encoding(steps)
    print(f"  correct cascade norm_sq: {r1['correct_norm_sq']:.6f}  (expect 1.0 for unit octonion product)")
    print(f"  wrong cascade norm_sq:   {r1['wrong_norm_sq']:.6f}")
    print(f"  cosine(correct, correct): {r1['cosine_correct_vs_self']:.6f}  (expect 1.0)")
    print(f"  cosine(correct, wrong):   {r1['cosine_correct_vs_wrong']:.6f}  (expect < 1.0)")
    print(f"  order_distinguishable: {r1['order_distinguishable']}")
    print(f"  all 24 permutations: {r1['n_perm_identity_cosine']} at cosine=1.0, {r1['n_perm_distinct']} distinct")
    print(f"  cosine range over permutations: [{r1['min_perm_cosine']:.4f}, {r1['max_perm_cosine']:.4f}]")
    print()

    # --- Experiment 2: Klein-4 order wash ---
    print("--- EXPERIMENT 2: Klein-4 bundle washes the order ---")
    print("  (same steps encoded as Klein-4 hypervectors; commutative majority-vote reference)")
    r2 = experiment_klein4_order_wash(k4_steps)
    print(f"  {r2['n_permutations_checked']} permutations checked")
    print(f"  all_bundles_identical: {r2['all_bundles_identical']}  -> order washed: {r2['order_washed']}")
    print()

    # --- Experiment 3: Non-associative bracketing = sub-step nesting ---
    print("--- EXPERIMENT 3: Non-associative bracketing = sub-step nesting ---")
    r3 = experiment_bracketing_nesting(steps)
    print(f"  Bracketing A: (s3*s4)*(s1*s2)  norm_sq: {r3['brack_A_norm_sq']:.6f}")
    print(f"  Bracketing B: s3*(s4*(s1*s2))  norm_sq: {r3['brack_B_norm_sq']:.6f}")
    print(f"  cosine(A, B): {r3['cosine_A_vs_B']:.6f}  -> distinct: {r3['distinct_bracketings']}")
    print(f"  associator residue norm_sq: {r3['associator_residue_norm_sq']:.6f}  -> nonzero: {r3['associator_nonzero']}")
    print(f"  associator oracle match: {r3['associator_oracle_match']}")
    print()

    # --- Internal consistency ---
    print("--- INTERNAL CONSISTENCY: klein4_bundle ---")
    r4 = experiment_klein4_bundle_internal_consistency(k4_steps)
    print(f"  deterministic: {r4['deterministic']}")
    print(f"  permutation_invariant: {r4['permutation_invariant']}")
    print()

    # --- Reading ---
    print("=" * 70)
    print("READING:")
    print()
    print("  The MECHANISM is the DIRECTED CASCADE.")
    print("  loop_bind(s1, loop_bind(s2, loop_bind(s3, s4))) encodes the documented")
    print("  step ORDER; swapping any two steps yields a distinct cascade (cosine < 1).")
    print("  This is the loop-bind non-commutativity (Class C) carrying the direction.")
    print()
    print("  The COMMUTATIVE reference (klein4_bundle) WASHES the order: all 24")
    print("  permutations yield the same bundle. Contrast confirms the order-encoding")
    print("  is a property of the non-commutative loop-bind, not the bundle.")
    print()
    print("  The NESTING (sub-step grouping) = NON-ASSOCIATIVE BRACKETING.")
    print("  Different bracketings of the same steps produce distinct cascades;")
    print("  the associator residue (Class-K boundary) is nonzero, quantifying the")
    print("  nesting information encoded by the bracket placement.")
    print()
    print("  Framework reading: mechanism step order + sub-step nesting are BOTH")
    print("  structurally encoded in the loop-bind directed cascade. Balancing (F278)")
    print("  = the conservation codeword (Class L/N/I); mechanism = the directed cascade")
    print("  (Class M∘C with Class-K associator residue). Two orthogonal cascades,")
    print("  same reaction, different structural aspects.")
    print("=" * 70)

    return {
        "consistency": cc,
        "order_encoding": r1,
        "klein4_order_wash": r2,
        "bracketing_nesting": r3,
        "bundle_internal": r4,
    }


if __name__ == "__main__":
    main()
