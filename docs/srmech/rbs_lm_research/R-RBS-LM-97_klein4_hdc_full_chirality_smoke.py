"""R-RBS-LM-97 — Klein-4 HDC binding prototype for full-chirality RBS-NN.

Per Finding 132 engineering proposal: extend srmech Class M with
Klein-4 (rank-2 abelian Z₂ × Z₂) binding alongside existing rank-1
abelian XOR (bipolar).

Klein-4 group elements map to (γ₅, iω₇) chirality sectors:
  (0, 0) = (+1, +1) = RH orient+ visible matter
  (0, 1) = (+1, −1) = RH orient− dark antimatter
  (1, 0) = (−1, +1) = LH orient+ visible antimatter
  (1, 1) = (−1, −1) = LH orient− dark matter

Klein-4 binding:
  Component-wise (Z₂ × Z₂)-XOR
  Self-inverse, abelian, associative, identity (0,0)

This smoke compares Klein-4 vs bipolar HDC on:
  1. Capacity: how many bound pairs can be retrieved at fixed D
  2. Similarity preservation: does Klein-4 mint+bundle preserve sim?
  3. Chirality-flip cost: Klein-4 native vs bipolar emulated
  4. Cross-sector retrieval: can chirality-flipped query find original?

Per MFO §VII.6.20 — form-iso engineering test, not substrate-identity claim.
"""

import json
from pathlib import Path

import numpy as np


# ===========================================================
# Klein-4 HDC primitives
# ===========================================================

# Each position is a 2-bit value (4 states): 0, 1, 2, 3
# Represented as uint8 with values in {0, 1, 2, 3}
# Decomposition: state = γ₅_bit * 2 + iω₇_bit
#   state 0 = (γ₅=0, iω₇=0) = (+1, +1) visible matter
#   state 1 = (γ₅=0, iω₇=1) = (+1, -1) dark antimatter
#   state 2 = (γ₅=1, iω₇=0) = (-1, +1) visible antimatter
#   state 3 = (γ₅=1, iω₇=1) = (-1, -1) dark matter


def klein4_random(D, rng):
    """Generate random Klein-4 hypervector of dimension D."""
    return rng.integers(0, 4, size=D, dtype=np.uint8)


def klein4_bind(a, b):
    """Klein-4 binding: component-wise XOR over (F₂)².

    For 2-bit values, XOR works directly: bit-pair XOR'd component-wise.
    """
    return np.bitwise_xor(a, b).astype(np.uint8)


def klein4_unbind(c, a):
    """Klein-4 unbind: self-inverse, so c ⊕ a = b if c = a ⊕ b."""
    return np.bitwise_xor(c, a).astype(np.uint8)


def klein4_similarity(a, b):
    """Match-fraction: fraction of positions where a == b."""
    return float((a == b).mean())


def klein4_bundle(*vecs):
    """Klein-4 bundle: majority vote per position per bit."""
    if len(vecs) == 0:
        raise ValueError("klein4_bundle requires at least one vector")
    # Stack and compute per-position majority for each of the 2 bits
    arr = np.stack([np.asarray(v, dtype=np.uint8) for v in vecs])
    # bit 0: state & 1
    # bit 1: state >> 1
    bit0_sum = (arr & 1).sum(axis=0)
    bit1_sum = ((arr >> 1) & 1).sum(axis=0)
    # Majority: if > half are 1, take 1; if exactly half, tie-break to 0 (arbitrary)
    half = len(vecs) // 2
    bit0_maj = (bit0_sum > half).astype(np.uint8)
    bit1_maj = (bit1_sum > half).astype(np.uint8)
    return (bit1_maj * 2 + bit0_maj).astype(np.uint8)


def klein4_chirality_flip_gamma5(v):
    """Flip γ₅ axis: XOR with (1, 0) at every position = XOR with 2."""
    return np.bitwise_xor(v, 2).astype(np.uint8)


def klein4_chirality_flip_omega7(v):
    """Flip iω₇ axis: XOR with (0, 1) at every position = XOR with 1."""
    return np.bitwise_xor(v, 1).astype(np.uint8)


def klein4_cpt_mirror(v):
    """Full CPT flip: both axes = XOR with (1, 1) = XOR with 3."""
    return np.bitwise_xor(v, 3).astype(np.uint8)


def klein4_sector_count(v):
    """Count how many positions in each (γ₅, iω₇) sector."""
    return [int((v == s).sum()) for s in range(4)]


# ===========================================================
# Bipolar HDC primitives (reference)
# ===========================================================

def bipolar_random(D, rng):
    return rng.choice([-1, 1], size=D).astype(np.int8)


def bipolar_bind(a, b):
    """Component-wise sign-product = XOR over {-1, +1}."""
    return (a * b).astype(np.int8)


def bipolar_unbind(c, a):
    """Self-inverse for sign-product."""
    return (c * a).astype(np.int8)


def bipolar_similarity(a, b):
    """Cosine: dot / D."""
    return float(np.dot(a, b)) / len(a)


def bipolar_bundle(*vecs):
    """Sign of sum (majority vote)."""
    s = sum(vecs)
    return np.sign(s).astype(np.int8)


# ===========================================================
# Tests
# ===========================================================

def test_klein4_basic_properties(D=10000):
    print("=" * 78)
    print("TEST 1: Klein-4 basic properties")
    print("=" * 78)
    rng = np.random.default_rng(2026)
    a = klein4_random(D, rng)
    b = klein4_random(D, rng)
    c = klein4_random(D, rng)

    # Self-inverse: a ⊕ a = 0
    aa = klein4_bind(a, a)
    self_inv = (aa == 0).all()
    print(f"  Self-inverse a ⊕ a = identity: {self_inv}")

    # Commutativity: a ⊕ b = b ⊕ a
    ab = klein4_bind(a, b)
    ba = klein4_bind(b, a)
    commutative = (ab == ba).all()
    print(f"  Commutativity a ⊕ b = b ⊕ a: {commutative}")

    # Associativity: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)
    left = klein4_bind(klein4_bind(a, b), c)
    right = klein4_bind(a, klein4_bind(b, c))
    associative = (left == right).all()
    print(f"  Associativity: {associative}")

    # Random vector sector distribution should be ~uniform
    sectors = klein4_sector_count(a)
    print(f"  Random vector sector distribution (~D/4 each): {sectors}")
    print(f"    Expected ~{D//4} each; observed sum={sum(sectors)}")

    # Random pair similarity should be ~0.25 (1/4 chance per position)
    sim_random = klein4_similarity(a, b)
    print(f"  Random pair similarity: {sim_random:.4f} (expected ~0.25)")

    return {
        "self_inverse": bool(self_inv),
        "commutative": bool(commutative),
        "associative": bool(associative),
        "random_sectors": sectors,
        "random_similarity": sim_random,
    }


def test_capacity_klein4_vs_bipolar(D_klein=10000, D_bipolar=10000,
                                       n_bound_pairs=100):
    print()
    print("=" * 78)
    print("TEST 2: Capacity comparison Klein-4 vs bipolar")
    print("=" * 78)
    print(f"  Klein-4 D={D_klein}, bipolar D={D_bipolar}")
    print(f"  Storing {n_bound_pairs} bound (key, value) pairs in one bundle")
    print()

    rng = np.random.default_rng(2026)

    # Klein-4
    keys_k4 = [klein4_random(D_klein, rng) for _ in range(n_bound_pairs)]
    vals_k4 = [klein4_random(D_klein, rng) for _ in range(n_bound_pairs)]
    bindings_k4 = [klein4_bind(k, v) for k, v in zip(keys_k4, vals_k4)]
    bundle_k4 = klein4_bundle(*bindings_k4)

    # Retrieve each value
    k4_retrievals = []
    for k, v_true in zip(keys_k4, vals_k4):
        retrieved = klein4_unbind(bundle_k4, k)
        sim = klein4_similarity(retrieved, v_true)
        k4_retrievals.append(sim)
    k4_mean_sim = np.mean(k4_retrievals)
    k4_std_sim = np.std(k4_retrievals)

    # Bipolar
    rng2 = np.random.default_rng(2026)
    keys_bp = [bipolar_random(D_bipolar, rng2) for _ in range(n_bound_pairs)]
    vals_bp = [bipolar_random(D_bipolar, rng2) for _ in range(n_bound_pairs)]
    bindings_bp = [bipolar_bind(k, v) for k, v in zip(keys_bp, vals_bp)]
    bundle_bp = bipolar_bundle(*bindings_bp)

    bp_retrievals = []
    for k, v_true in zip(keys_bp, vals_bp):
        retrieved = bipolar_unbind(bundle_bp, k)
        sim = bipolar_similarity(retrieved, v_true)
        bp_retrievals.append(sim)
    bp_mean_sim = np.mean(bp_retrievals)
    bp_std_sim = np.std(bp_retrievals)

    print(f"  Klein-4 retrieval (chance = 0.25):")
    print(f"    mean={k4_mean_sim:.4f}  std={k4_std_sim:.4f}")
    print(f"    above-chance: {k4_mean_sim - 0.25:.4f}")
    print(f"  Bipolar retrieval (chance = 0.0):")
    print(f"    mean={bp_mean_sim:.4f}  std={bp_std_sim:.4f}")
    print(f"    above-chance: {bp_mean_sim:.4f}")

    # Normalize to "signal above chance" for fair comparison
    k4_signal = k4_mean_sim - 0.25       # 0 to 0.75 range (1 - 0.25)
    bp_signal = bp_mean_sim               # 0 to 1.0 range
    # Normalize: signal as fraction of max possible above chance
    k4_signal_normalized = k4_signal / 0.75
    bp_signal_normalized = bp_signal  # / 1.0

    print(f"\n  Normalized signal-above-chance:")
    print(f"    Klein-4:  {k4_signal_normalized:.4f}")
    print(f"    Bipolar:  {bp_signal_normalized:.4f}")

    return {
        "n_bound_pairs": n_bound_pairs,
        "D_klein": D_klein, "D_bipolar": D_bipolar,
        "klein4_mean_sim": k4_mean_sim, "klein4_std": k4_std_sim,
        "bipolar_mean_sim": bp_mean_sim, "bipolar_std": bp_std_sim,
        "klein4_signal_normalized": float(k4_signal_normalized),
        "bipolar_signal_normalized": float(bp_signal_normalized),
    }


def test_chirality_flip_cost(D=10000):
    print()
    print("=" * 78)
    print("TEST 3: Chirality flip operations")
    print("=" * 78)

    rng = np.random.default_rng(2026)
    v = klein4_random(D, rng)
    sectors_before = klein4_sector_count(v)
    print(f"  Original sectors: {sectors_before}")

    v_gamma5 = klein4_chirality_flip_gamma5(v)
    sectors_g5 = klein4_sector_count(v_gamma5)
    print(f"  After γ₅ flip:    {sectors_g5}")
    # γ₅ flip should swap sectors 0↔2 and 1↔3
    expected_g5 = [sectors_before[2], sectors_before[3],
                   sectors_before[0], sectors_before[1]]
    g5_correct = sectors_g5 == expected_g5
    print(f"    Expected swap 0↔2, 1↔3: {g5_correct}")

    v_omega7 = klein4_chirality_flip_omega7(v)
    sectors_o7 = klein4_sector_count(v_omega7)
    print(f"  After iω₇ flip:   {sectors_o7}")
    expected_o7 = [sectors_before[1], sectors_before[0],
                   sectors_before[3], sectors_before[2]]
    o7_correct = sectors_o7 == expected_o7
    print(f"    Expected swap 0↔1, 2↔3: {o7_correct}")

    v_cpt = klein4_cpt_mirror(v)
    sectors_cpt = klein4_sector_count(v_cpt)
    print(f"  After CPT mirror:  {sectors_cpt}")
    expected_cpt = [sectors_before[3], sectors_before[2],
                    sectors_before[1], sectors_before[0]]
    cpt_correct = sectors_cpt == expected_cpt
    print(f"    Expected swap 0↔3, 1↔2: {cpt_correct}")

    return {
        "gamma5_flip_correct": g5_correct,
        "omega7_flip_correct": o7_correct,
        "cpt_mirror_correct": cpt_correct,
    }


def test_cross_sector_retrieval(D=10000, n_pairs=50):
    print()
    print("=" * 78)
    print("TEST 4: Cross-sector retrieval")
    print("=" * 78)
    print(f"  Encode in visible sector, query in CPT-mirrored sector")
    print()

    rng = np.random.default_rng(2026)
    keys = [klein4_random(D, rng) for _ in range(n_pairs)]
    vals = [klein4_random(D, rng) for _ in range(n_pairs)]
    bindings = [klein4_bind(k, v) for k, v in zip(keys, vals)]
    bundle = klein4_bundle(*bindings)

    # Same-sector retrieval (baseline)
    same_sector = []
    for k, v_true in zip(keys, vals):
        retrieved = klein4_unbind(bundle, k)
        sim = klein4_similarity(retrieved, v_true)
        same_sector.append(sim)
    same_mean = np.mean(same_sector)

    # CPT-mirror retrieval: query with CPT-mirrored key,
    # expect to retrieve CPT-mirrored value
    cpt_retrievals_self = []  # vs true value
    cpt_retrievals_mirror = []  # vs cpt-mirrored value
    for k, v_true in zip(keys, vals):
        k_mirror = klein4_cpt_mirror(k)
        retrieved = klein4_unbind(bundle, k_mirror)
        # Compare to true value (should be low — wrong key)
        sim_self = klein4_similarity(retrieved, v_true)
        # Compare to mirrored value (should be... interesting)
        v_mirror = klein4_cpt_mirror(v_true)
        sim_mirror = klein4_similarity(retrieved, v_mirror)
        cpt_retrievals_self.append(sim_self)
        cpt_retrievals_mirror.append(sim_mirror)

    print(f"  Same-sector retrieval (baseline): {same_mean:.4f}")
    print(f"  CPT-mirrored key, vs true value:  {np.mean(cpt_retrievals_self):.4f}")
    print(f"  CPT-mirrored key, vs cpt-mirrored value: {np.mean(cpt_retrievals_mirror):.4f}")
    print()

    # Insight: bundle ⊕ cpt_mirror(k) should equal cpt_mirror(bundle ⊕ k)
    # because XOR is commutative with the CPT flip pattern
    # So cpt_mirror retrieval recovers cpt_mirror of original retrieval
    print(f"  Algebraic check: cpt_mirror is a substrate-symmetry")
    print(f"  bundle ⊕ cpt(k) = cpt(bundle) ⊕ k? testing first pair...")
    k0, v0 = keys[0], vals[0]
    lhs = klein4_bind(bundle, klein4_cpt_mirror(k0))
    rhs = klein4_bind(klein4_cpt_mirror(bundle), k0)
    eq = (lhs == rhs).all()
    print(f"    Equal: {eq}")

    return {
        "same_sector_mean": float(same_mean),
        "cpt_key_vs_true": float(np.mean(cpt_retrievals_self)),
        "cpt_key_vs_mirror": float(np.mean(cpt_retrievals_mirror)),
        "cpt_substrate_symmetry": bool(eq),
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-97 — Klein-4 HDC binding prototype for full-chirality RBS-NN")
    print("=" * 78)
    print()

    basic = test_klein4_basic_properties()
    capacity = test_capacity_klein4_vs_bipolar()
    flips = test_chirality_flip_cost()
    cross = test_cross_sector_retrieval()

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print()
    print(f"  Basic properties: self-inverse={basic['self_inverse']}, "
          f"commutative={basic['commutative']}, "
          f"associative={basic['associative']}")
    print(f"  Random sector uniformity:        {basic['random_sectors']}")
    print(f"  Capacity (signal above chance):")
    print(f"    Klein-4:  {capacity['klein4_signal_normalized']:.4f}")
    print(f"    Bipolar:  {capacity['bipolar_signal_normalized']:.4f}")
    print(f"  Chirality flips correct: γ₅={flips['gamma5_flip_correct']}, "
          f"iω₇={flips['omega7_flip_correct']}, CPT={flips['cpt_mirror_correct']}")
    print(f"  CPT substrate symmetry algebraically verified: "
          f"{cross['cpt_substrate_symmetry']}")
    print()

    all_pass = (
        basic['self_inverse'] and basic['commutative'] and basic['associative']
        and flips['gamma5_flip_correct'] and flips['omega7_flip_correct']
        and flips['cpt_mirror_correct'] and cross['cpt_substrate_symmetry']
    )

    if all_pass:
        print("  PASS: Klein-4 HDC satisfies all algebraic properties.")
        print("  Chirality-flip operations work natively as XOR with sector masks.")
        print("  CPT substrate-symmetry verified algebraically.")
    else:
        print("  FAIL: One or more algebraic properties broken — investigate.")

    print()
    print("  This prototypes the Class M rank-2 abelian variant.")
    print("  Per [[user_stance_canonical_two_variant_dial_class_m]] integer-ladder.")
    print("  Per [[feedback_no_privileged_primitive_classes]] — no new class.")
    print()

    out_path = Path(__file__).parent / "R-RBS-LM-97_klein4_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "basic_properties": basic,
            "capacity_comparison": capacity,
            "chirality_flip_operations": flips,
            "cross_sector_retrieval": cross,
            "all_algebraic_properties_pass": all_pass,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
