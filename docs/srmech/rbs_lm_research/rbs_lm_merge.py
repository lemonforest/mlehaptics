"""R-RBS-LM-33 — Instrument merging + weak-coupling truncation.

Per user direction 2026-05-25: *"with ephemerides-spectral, we added other
ephemeris data into our RBS-HDC instrument, we should be able to merge
models on demand if we keep each one in it's own RBS-LM, and our RBS-NN
now becomes adaptive in real time? opens the door to training from a
source repo maybe if we truncate weak coupling and then surgically graft
in new knowledge?"*

The ephemerides-spectral discipline (R-RBS-LM-12 §6 referenced; sister
notebook docs/antikythera-maths/ephemerides_spectral_research_notebook.md):
multiple data sources are bound into one RBS-HDC instrument. Bundle is
associative — bundle(a, b, c) = bundle(bundle(a, b), c) — so we can
compose after-the-fact.

For RBS-LM:
  - Each knowledge domain (notebook content / ASL corpus / RAG document
    set / etc.) gets its own 1024-byte instrument
  - Merge via per-bit weighted majority
  - "Weak coupling" — bits where bindings disagree heavily (≈ 50/50);
    these are the most vulnerable to interference + the lowest-load-bearing
  - "Surgical graft" — truncate weak bits in a base instrument, then merge
    in a new domain's bindings → strong base retained, new knowledge added

Per `[[user_stance_ai_is_not_a_substrate]]` continuity: merging instruments
doesn't make the cascade smarter; it makes the input wider. The cascade
still does discrete bind/bundle/popcount; the structural ceiling per
R-RBS-LM-19 still bounds top-end content disambiguation.

Honest framework reading:
  - Merge ≠ training. Merging adds bindings; it doesn't reshape weights.
  - Truncate doesn't "forget" specific knowledge; it removes the noisy
    floor that prevents new bindings from imprinting cleanly.
  - The path enables INCREMENTAL knowledge addition (the user's "training
    from a source repo" framing) without re-running the full Path D pipeline.

Usage:
    from rbs_lm_merge import (
        merge_instruments,
        weak_coupling_mask,
        truncate_weak_coupling,
        graft_new_knowledge,
    )

    merged = merge_instruments([inst_a, inst_b], n_obs=[647, 443])
    weak = weak_coupling_mask(observations, instrument, D=8192)
    truncated = truncate_weak_coupling(inst_a, observations_a, threshold=0.55)
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import D  # noqa: E402


# -------------------------------------------------------------------------
# Core merge operation
# -------------------------------------------------------------------------

def merge_instruments(instruments, n_obs=None):
    """Merge N instruments into one via per-bit weighted majority.

    If n_obs is provided (parallel list of integers, one per instrument),
    the merge weights each instrument's bits by its observation count.
    This makes the merge equivalent to bundling all underlying bindings
    if each instrument was a bundle of n_obs bindings.

    If n_obs is None, all instruments count equally (uniform majority).

    Args:
        instruments: list of bytes objects, each D/8 bytes
        n_obs: optional list of int; one per instrument

    Returns: D/8-byte merged instrument

    Per `[[user_stance_ai_is_not_a_substrate]]`: this is composition, not
    learning. The cascade reads the merged instrument the same way it
    reads any other instrument.
    """
    if len(instruments) == 0:
        raise ValueError("merge_instruments requires at least 1 instrument")
    if len(instruments) == 1:
        return instruments[0]

    if n_obs is None:
        n_obs = [1] * len(instruments)
    if len(n_obs) != len(instruments):
        raise ValueError(f"n_obs ({len(n_obs)}) must be parallel to "
                         f"instruments ({len(instruments)})")

    # Stack as (N_instruments, D) bit arrays
    arrays = []
    for inst in instruments:
        bits = np.unpackbits(np.frombuffer(inst, dtype=np.uint8), bitorder="big")
        arrays.append(bits.astype(np.int32))
    stacked = np.stack(arrays, axis=0)  # (N_inst, D)

    # Per-bit weighted sum: sum_{i} n_obs[i] * stacked[i, b]
    weights = np.array(n_obs, dtype=np.int32).reshape(-1, 1)
    weighted_sum = (stacked * weights).sum(axis=0)  # (D,)
    total_weight = sum(n_obs)

    # Majority: bit = 1 if weighted_sum > total_weight / 2
    merged_bits = (2 * weighted_sum > total_weight).astype(np.uint8)
    return np.packbits(merged_bits, bitorder="big").tobytes()


# -------------------------------------------------------------------------
# Weak-coupling identification
# -------------------------------------------------------------------------

def weak_coupling_mask(observations, vocab_table, D=D, threshold=0.6):
    """Identify bits where the underlying bindings barely agreed.

    For each bit position b in [0, D), measure what fraction of the encoded
    bindings have that bit set. If the fraction is between (1-threshold)
    and threshold, the bit is WEAK (close to 50/50).

    Args:
        observations: list of (context_tokens, next_token) pairs
        vocab_table: byte vocab table (R-RBS-LM-25); used to re-encode bindings
        threshold: agreement threshold; default 0.6 means bits with 40-60% set are weak

    Returns: D-length bool array; True at weak-coupling bits.

    For very small N this is unreliable (e.g., 3 observations can produce
    pathological 33/66 patterns); recommend N >= 50.
    """
    from rbs_lm_bytes import encode_observation_bytes

    if len(observations) < 5:
        raise ValueError(f"need >= 5 observations for reliable weak-coupling "
                         f"detection (got {len(observations)})")

    # Encode all bindings; stack as (N, D) bit array
    rows = []
    for ctx, nxt in observations:
        binding = encode_observation_bytes(ctx, nxt, vocab_table, D)
        bits = np.unpackbits(np.frombuffer(binding, dtype=np.uint8), bitorder="big")
        rows.append(bits)
    binding_matrix = np.stack(rows, axis=0)  # (N, D)

    # Per-bit fraction of 1s
    fraction_ones = binding_matrix.mean(axis=0)
    weak = (fraction_ones > (1 - threshold)) & (fraction_ones < threshold)
    return weak


# -------------------------------------------------------------------------
# Truncate weak coupling
# -------------------------------------------------------------------------

def truncate_weak_coupling(instrument, observations, vocab_table, D=D,
                            threshold=0.6, randomize=False, seed=42):
    """Zero (or randomize) the weak-coupling bits of an instrument.

    Args:
        instrument: D/8-byte source instrument
        observations: the (context, next_token) pairs that produced it
        threshold: see weak_coupling_mask
        randomize: if True, replace weak bits with random ±; if False, set to 0
        seed: random seed if randomize=True

    Returns: new D/8-byte instrument with weak bits replaced.

    Operational note: zeroing weak bits is NOT "forgetting weak knowledge".
    It's removing the noisy floor so new bindings can imprint cleanly when
    merged via graft_new_knowledge.
    """
    weak = weak_coupling_mask(observations, vocab_table, D=D, threshold=threshold)
    inst_bits = np.unpackbits(np.frombuffer(instrument, dtype=np.uint8),
                               bitorder="big").astype(np.uint8)

    if randomize:
        rng = np.random.default_rng(seed)
        replacement = rng.integers(0, 2, size=weak.sum(), dtype=np.uint8)
    else:
        replacement = np.zeros(weak.sum(), dtype=np.uint8)

    inst_bits[weak] = replacement
    return np.packbits(inst_bits, bitorder="big").tobytes()


# -------------------------------------------------------------------------
# Surgical graft of new knowledge
# -------------------------------------------------------------------------

def graft_new_knowledge(
    base_instrument,
    base_observations,
    new_observations,
    vocab_table,
    D=D,
    truncate_base: bool = True,
    truncate_threshold: float = 0.6,
):
    """Combine base instrument's strong-coupling bits with new bindings.

    1. Optionally truncate weak bits in base_instrument
    2. Encode new_observations as a patch instrument
    3. Merge truncated_base + patch via weighted majority

    Args:
        base_instrument: existing 1024-byte RBS-LM instrument
        base_observations: the (context, next_token) pairs that produced it
        new_observations: new (context, next_token) pairs to add
        vocab_table: byte vocab table
        truncate_base: whether to zero out weak-coupling bits in base first
        truncate_threshold: weak-coupling threshold

    Returns: D/8-byte instrument carrying base's strong signal + new bindings.
    """
    from rbs_lm_bytes import encode_observation_bytes
    from rbs_lm_encoder import hierarchical_bundle

    if truncate_base and len(base_observations) >= 5:
        base = truncate_weak_coupling(
            base_instrument, base_observations, vocab_table,
            D=D, threshold=truncate_threshold,
        )
    else:
        base = base_instrument

    # Encode new observations as a patch instrument
    new_bindings = [
        encode_observation_bytes(ctx, nxt, vocab_table, D)
        for ctx, nxt in new_observations
    ]
    if len(new_bindings) == 0:
        return base
    patch = hierarchical_bundle(new_bindings)

    # Merge: each represents N bindings (base has len(base_observations);
    # patch has len(new_observations))
    return merge_instruments([base, patch],
                              n_obs=[len(base_observations), len(new_observations)])


# -------------------------------------------------------------------------
# Self-test
# -------------------------------------------------------------------------

def _self_test():
    print(f"=== R-RBS-LM-33 instrument merge self-test ===\n")

    from rbs_lm_bytes import compute_byte_vocab_table, encode_observation_bytes
    from rbs_lm_encoder import hierarchical_bundle

    vocab_table = compute_byte_vocab_table(D)
    print(f"  byte vocab: {vocab_table.shape}")

    # Two domains: a small cooking corpus + a small astronomy corpus
    cooking_obs = []
    text = b"beat eggs until foamy add butter mix flour bake at 350F"
    for i in range(0, len(text) - 12, 4):
        cooking_obs.append((list(text[i:i+12]), text[i+12]))

    astronomy_obs = []
    text = b"andromeda galaxy 2.5 million light years from earth"
    for i in range(0, len(text) - 12, 4):
        astronomy_obs.append((list(text[i:i+12]), text[i+12]))

    print(f"  cooking obs:   {len(cooking_obs)}")
    print(f"  astronomy obs: {len(astronomy_obs)}")

    # Encode each as an instrument
    inst_cooking = hierarchical_bundle(
        [encode_observation_bytes(c, n, vocab_table, D) for c, n in cooking_obs]
    )
    inst_astronomy = hierarchical_bundle(
        [encode_observation_bytes(c, n, vocab_table, D) for c, n in astronomy_obs]
    )
    print(f"  cooking inst:   {len(inst_cooking)} bytes")
    print(f"  astronomy inst: {len(inst_astronomy)} bytes")

    # Test 1: merge two domains
    print(f"\n  Test 1: merge_instruments (uniform vs weighted)")
    merged_uniform = merge_instruments([inst_cooking, inst_astronomy])
    merged_weighted = merge_instruments(
        [inst_cooking, inst_astronomy],
        n_obs=[len(cooking_obs), len(astronomy_obs)]
    )
    h_uniform_vs_weighted = int(np.bitwise_count(
        np.frombuffer(merged_uniform, dtype=np.uint8) ^
        np.frombuffer(merged_weighted, dtype=np.uint8)
    ).sum())
    print(f"    uniform vs weighted Hamming dist: {h_uniform_vs_weighted} (D={D})")
    if len(cooking_obs) == len(astronomy_obs):
        print(f"    (expected ~0 since N's are equal)")
    else:
        print(f"    (N's differ → weighting matters)")

    # Test 2: merged vs source — is the merged equally similar to both inputs?
    print(f"\n  Test 2: similarity of merge to each source")
    def sim(a, b):
        return 1.0 - 2.0 * int(np.bitwise_count(
            np.frombuffer(a, dtype=np.uint8) ^
            np.frombuffer(b, dtype=np.uint8)
        ).sum()) / D
    s_cook = sim(merged_weighted, inst_cooking)
    s_astr = sim(merged_weighted, inst_astronomy)
    print(f"    merged vs cooking:   {s_cook:+.4f}")
    print(f"    merged vs astronomy: {s_astr:+.4f}")
    print(f"    cooking vs astronomy: {sim(inst_cooking, inst_astronomy):+.4f} (sanity: ~0 random)")

    # Test 3: weak coupling mask
    print(f"\n  Test 3: weak_coupling_mask (threshold 0.6)")
    weak = weak_coupling_mask(cooking_obs, vocab_table, D=D, threshold=0.6)
    n_weak = int(weak.sum())
    print(f"    weak bits: {n_weak}/{D} ({100*n_weak/D:.1f}%)")
    print(f"    strong bits: {D - n_weak}/{D} ({100*(D-n_weak)/D:.1f}%)")

    # Test 4: truncate weak coupling
    print(f"\n  Test 4: truncate_weak_coupling")
    trunc_zero = truncate_weak_coupling(inst_cooking, cooking_obs, vocab_table,
                                         D=D, threshold=0.6, randomize=False)
    trunc_rand = truncate_weak_coupling(inst_cooking, cooking_obs, vocab_table,
                                         D=D, threshold=0.6, randomize=True)
    s_trunc_zero = sim(trunc_zero, inst_cooking)
    s_trunc_rand = sim(trunc_rand, inst_cooking)
    print(f"    trunc(zero) vs original:  {s_trunc_zero:+.4f}  ({n_weak} bits zeroed)")
    print(f"    trunc(rand) vs original:  {s_trunc_rand:+.4f}  ({n_weak} bits randomized)")

    # Test 5: graft new knowledge
    print(f"\n  Test 5: graft_new_knowledge")
    grafted = graft_new_knowledge(
        base_instrument=inst_cooking,
        base_observations=cooking_obs,
        new_observations=astronomy_obs,
        vocab_table=vocab_table, D=D,
        truncate_base=True, truncate_threshold=0.6,
    )
    print(f"    grafted vs cooking (base):    {sim(grafted, inst_cooking):+.4f}")
    print(f"    grafted vs astronomy (added): {sim(grafted, inst_astronomy):+.4f}")
    print(f"    grafted vs merged (no trunc): {sim(grafted, merged_weighted):+.4f}")

    grafted_no_trunc = graft_new_knowledge(
        base_instrument=inst_cooking,
        base_observations=cooking_obs,
        new_observations=astronomy_obs,
        vocab_table=vocab_table, D=D,
        truncate_base=False,
    )
    print(f"    grafted(no-trunc) vs merged:  {sim(grafted_no_trunc, merged_weighted):+.4f}")
    print(f"    → grafted(no-trunc) should = merge directly: sim 1.0 expected")

    # Test 6: empty / single edge cases
    print(f"\n  Test 6: edge cases")
    single = merge_instruments([inst_cooking])
    print(f"    merge of single: same as input? {single == inst_cooking}")
    try:
        merge_instruments([])
        print(f"    empty list: should have raised — DID NOT")
    except ValueError as e:
        print(f"    empty list raises ValueError as expected: {str(e)[:60]}")
    try:
        merge_instruments([inst_cooking, inst_astronomy], n_obs=[1])
        print(f"    mismatched n_obs: should have raised — DID NOT")
    except ValueError as e:
        print(f"    mismatched n_obs raises ValueError: {str(e)[:60]}")


if __name__ == "__main__":
    _self_test()
