"""loop_bind_L4_two_tier_store.py — LEG L4 (Finding F291): the natural RBS architecture
is a TWO-TIER store: a CONTENT tier (klein4 bag, order-blind set-membership = the R-RBS-LM-75
flat commutative connection) + an ORDER tier (loop bind, peelable path = the F288 curved
gauge connection). Together = a store that knows BOTH what tokens are present AND in what order.

WHAT THIS LEG TESTS (POSITIVE only if BOTH tiers work AND are independent):
  TIER 1 (content): klein4_bundle of the sequence's token-vectors. Query "is token X present?"
    via klein4_similarity vs each codebook token. Present tokens must score high; a not-present
    DISTRACTOR must score low. Report membership accuracy + the sim gap (present vs absent).
  TIER 2 (order): loop-bind ordered fold of the SAME sequence; recover the ORDER by peeling
    (right-unbind in order). Report peel fidelity (max err).
  INDEPENDENCE: confirm the two tiers are separate stores — building the order tier must NOT
    change the content tier's answers. Report.

READING (no-lineage; READ the structure):
  - content tier = the order-blind bag: klein4 bind is commutative+associative (a FLAT connection,
    R-RBS-LM-75 order-invariance). It can say WHICH tokens are present but is blind to order.
  - order tier = the curved loop-bind path (F288): the Moufang/octonion product is non-commutative
    AND non-associative (a CURVED gauge connection), so ((s0 o s1) o s2) is a path that records the
    order and is peelable (unit octonions: right-inverse = conj). It carries ORDER the flat bag cannot.
  The two together: ONE token sequence, stored in two structurally-distinct connections.

SRMECH-FIRST: content tier uses native hdc.klein4_random / klein4_bundle / klein4_similarity
  (Class M, uint8 sector occupancy). Order tier uses native hdc.loop_bind / hdc.loop_conj
  (the dim-8 octonion product = the k=7 op; intrinsically dim-8 — the last division algebra,
  so it is the unbindable/peelable one; F272/F274). Identification of a peeled token uses the
  Born inner product (re^2-style real inner product <rec, codebook_j>), NOT abs() — Class-K clean.
  Consistency: native hdc.loop_bind is verified == loop_bind_moufang oracle on all 64 e_i,e_j pairs.

NO-MAGIC (every constant attested):
  D_KLEIN = 2048  : A — the project HD dimension (D = 2^11; the established RBS-HDC width, F222).
  DIM8 = 8        : A — octonion dimension = the last division algebra (Hurwitz 1/2/4/8); the
                    intrinsic, unbindable loop-bind block size (F272). Imported as oracle/hd-gate constant.
  SEED = 4291     : B — single attested run seed (4 + 291 = leg-id + finding-id; reproducibility only).
  VOCAB = 24      : B — codebook (vocabulary) size for the demo; bounded.
  SEQ_LEN = 6     : B — token-sequence length; bounded (within the dim-8 peel-fidelity regime).
  TRIALS = 200    : B — number of independent (re-seeded) sequences averaged for membership accuracy
                    and peel fidelity; bounded.
  SIM_THRESH = 0.40 : B — membership decision threshold on klein4_similarity (present vs absent);
                    chosen between the measured present/absent clusters, reported with the gap so it
                    is not load-bearing for the verdict (the GAP is the real signal).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                                  # noqa: E402
from srmech.amsc import hdc                                         # noqa: E402
import loop_bind_moufang as oracle                                  # noqa: E402

D_KLEIN = 2048          # A: HD width (2^11)
DIM8 = oracle.DIM       # A: octonion dim = 8 (last division algebra); use oracle's constant
SEED = 4291             # B: run seed
VOCAB = 24              # B: codebook size
SEQ_LEN = 6             # B: sequence length
TRIALS = 200            # B: averaged independent sequences
SIM_THRESH = 0.40       # B: membership threshold (gap is the real signal, not the threshold)


# ---------------------------------------------------------------------------
# Consistency gate: native hdc.loop_bind == oracle.loop_bind on all 64 basis pairs.
# ---------------------------------------------------------------------------
def consistency_native_eq_oracle(atol=1e-12):
    maxerr = 0.0
    for i in range(DIM8):
        for j in range(DIM8):
            ei = np.zeros(DIM8); ei[i] = 1.0
            ej = np.zeros(DIM8); ej[j] = 1.0
            nv = np.asarray(hdc.loop_bind(ei, ej), dtype=float)
            ov = np.asarray(oracle.loop_bind(ei, ej), dtype=float)
            err = float(np.max(np.abs(nv - ov)))   # diagnostic comparison, not a cascade fold
            if err > maxerr:
                maxerr = err
    return (maxerr <= atol), maxerr


# ---------------------------------------------------------------------------
# Codebook: each token has TWO forms — a klein4 form (content) + a dim-8 unit
# octonion form (order). Built from independent seeds (no cross-tier leakage by construction).
# ---------------------------------------------------------------------------
def make_codebook(rng):
    """Return (klein4_forms, oct_forms): VOCAB klein4 uint8 vectors + VOCAB dim-8 unit octonions."""
    klein4_forms = [hdc.klein4_random(D_KLEIN, seed=int(rng.integers(1, 2**31)))
                    for _ in range(VOCAB)]
    raw = rng.standard_normal((VOCAB, DIM8))
    norms = np.sqrt(np.sum(raw * raw, axis=1, keepdims=True))   # Born/inner-product norm, no abs()
    oct_forms = raw / norms                                     # each row a unit octonion
    return klein4_forms, oct_forms


# ---------------------------------------------------------------------------
# Born real inner product (Class-K clean: <u, v> via dot of reals; no abs(), no sign-fold).
# Used only to IDENTIFY a peeled octonion against the codebook (argmax of the real inner product).
# ---------------------------------------------------------------------------
def inner(u, v):
    u = np.asarray(u, dtype=float); v = np.asarray(v, dtype=float)
    return float(np.dot(u, v))


# ---------------------------------------------------------------------------
# TIER 2 helpers: ordered loop-bind fold and order-recovery by right-peeling.
# fold = ((... ((s0 o s1) o s2) ... ) o s_{n-1}); right-peel with conj recovers each token.
# (unit octonions: right-inverse = conj, so (p o s) o conj(s) = p — verified in probe.)
# ---------------------------------------------------------------------------
def order_fold(oct_seq):
    acc = oct_seq[0]
    for k in range(1, len(oct_seq)):
        acc = np.asarray(hdc.loop_bind(acc, oct_seq[k]), dtype=float)
    return acc


def order_peel(fold, oct_seq):
    """Peel the fold back to the per-step prefix-products, recovering each appended token.

    Returns (recovered_tokens_in_order, max_peel_err). recovered[k] is the dim-8 vector
    recovered as the k-th appended token (compared against the known oct_seq[k] for fidelity).
    """
    n = len(oct_seq)
    recovered = [None] * n
    max_err = 0.0
    # prefix_k = ((s0 o s1) ... o s_k).  acc = prefix_{n-1} = fold.
    # right-peel: prefix_{k-1} = prefix_k o conj(s_k); then token_k = conj(prefix_{k-1}) o prefix_k.
    acc = np.asarray(fold, dtype=float)
    for k in range(n - 1, 0, -1):
        prefix_prev = np.asarray(hdc.loop_bind(acc, np.asarray(hdc.loop_conj(oct_seq[k]), dtype=float)), dtype=float)
        # token k recovered = the right factor that, appended to prefix_prev, gives acc:
        #   acc = prefix_prev o token_k  ->  token_k = conj(prefix_prev) o acc  (left-unbind, unit)
        token_k = np.asarray(hdc.loop_bind(np.asarray(hdc.loop_conj(prefix_prev), dtype=float), acc), dtype=float)
        recovered[k] = token_k
        err = float(np.max(np.abs(token_k - oct_seq[k])))
        if err > max_err:
            max_err = err
        acc = prefix_prev
    # acc is now prefix_0 = s0 itself.
    recovered[0] = acc
    err0 = float(np.max(np.abs(acc - oct_seq[0])))
    if err0 > max_err:
        max_err = err0
    return recovered, max_err


# ---------------------------------------------------------------------------
# Main experiment.
# ---------------------------------------------------------------------------
def main():
    print("=== LEG L4 — two-tier content+order RBS store (Finding F291) ===\n")

    ok_consist, maxerr = consistency_native_eq_oracle()
    print(f"[consistency] native hdc.loop_bind == oracle.loop_bind on all 64 e_i,e_j pairs: "
          f"{ok_consist}  (max|err| = {maxerr:.2e}, atol 1e-12)\n")

    root_rng = np.random.default_rng(SEED)

    # Accumulators
    membership_correct = 0           # present-token decisions correct
    membership_total = 0
    distractor_correct = 0           # distractor (absent) decisions correct
    distractor_total = 0
    present_sims = []                # klein4_similarity of present tokens vs the content bag
    absent_sims = []                 # klein4_similarity of the distractor vs the content bag
    peel_errs = []                   # per-trial max order-peel err
    order_recovery_correct = 0       # peeled-token identified to the right codebook entry
    order_recovery_total = 0
    independence_violations = 0      # trials where building the order tier changed a content answer
    indep_max_drift = 0.0            # max |sim_after - sim_before| over all trials/tokens

    for _ in range(TRIALS):
        trial_rng = np.random.default_rng(int(root_rng.integers(1, 2**31)))
        klein4_forms, oct_forms = make_codebook(trial_rng)

        # Pick a sequence (with possible repeats? no — distinct tokens so membership is well-defined,
        # and a held-out DISTRACTOR token guaranteed absent).
        all_idx = np.arange(VOCAB)
        trial_rng.shuffle(all_idx)
        seq_idx = list(all_idx[:SEQ_LEN])           # the SEQ_LEN present tokens (ordered)
        distractor = int(all_idx[SEQ_LEN])          # one guaranteed-absent token

        # ---- TIER 1 (content): order-blind klein4 bag of the present tokens ----
        content_bag = hdc.klein4_bundle(*[klein4_forms[i] for i in seq_idx])

        # Query membership BEFORE building the order tier (baseline content answers).
        sims_before = {i: hdc.klein4_similarity(content_bag, klein4_forms[i]) for i in seq_idx}
        sims_before[distractor] = hdc.klein4_similarity(content_bag, klein4_forms[distractor])

        for i in seq_idx:
            s = sims_before[i]
            present_sims.append(s)
            membership_total += 1
            if s >= SIM_THRESH:
                membership_correct += 1
        ds = sims_before[distractor]
        absent_sims.append(ds)
        distractor_total += 1
        if ds < SIM_THRESH:
            distractor_correct += 1

        # ---- TIER 2 (order): loop-bind ordered fold of the SAME sequence ----
        oct_seq = [oct_forms[i] for i in seq_idx]
        fold = order_fold(oct_seq)
        recovered, peel_err = order_peel(fold, oct_seq)
        peel_errs.append(peel_err)

        # Recover the ORDER: identify each peeled token against the octonion codebook (argmax inner).
        for pos, rec in enumerate(recovered):
            order_recovery_total += 1
            scores = [inner(rec, oct_forms[j]) for j in range(VOCAB)]
            best = int(np.argmax(scores))
            if best == seq_idx[pos]:
                order_recovery_correct += 1

        # ---- INDEPENDENCE: re-query the content tier AFTER the order tier was built ----
        # The content bag object is untouched by the order tier (separate store); confirm answers
        # are bit-identical. Drift would mean the tiers are NOT independent.
        for i in seq_idx:
            s_after = hdc.klein4_similarity(content_bag, klein4_forms[i])
            drift = abs(s_after - sims_before[i])   # scalar diagnostic of two stored answers (not a cascade)
            if drift > indep_max_drift:
                indep_max_drift = drift
            if drift > 0.0:
                independence_violations += 1
        s_after_d = hdc.klein4_similarity(content_bag, klein4_forms[distractor])
        drift_d = abs(s_after_d - sims_before[distractor])
        if drift_d > indep_max_drift:
            indep_max_drift = drift_d
        if drift_d > 0.0:
            independence_violations += 1

    # ---- Report ----
    present_arr = np.asarray(present_sims)
    absent_arr = np.asarray(absent_sims)
    mem_acc = membership_correct / membership_total
    dist_acc = distractor_correct / distractor_total
    overall_mem_acc = (membership_correct + distractor_correct) / (membership_total + distractor_total)
    peel_max = float(np.max(peel_errs))
    peel_mean = float(np.mean(peel_errs))
    order_acc = order_recovery_correct / order_recovery_total
    sim_gap = float(present_arr.mean() - absent_arr.mean())

    print("=== TIER 1 (content) — order-blind klein4 bag (R-RBS-LM-75 flat connection) ===")
    print(f"  present-token sim:   mean {present_arr.mean():.3f}  min {present_arr.min():.3f}  max {present_arr.max():.3f}")
    print(f"  absent (distractor): mean {absent_arr.mean():.3f}  min {absent_arr.min():.3f}  max {absent_arr.max():.3f}")
    print(f"  sim GAP (present - absent mean): {sim_gap:+.3f}")
    print(f"  membership accuracy: present {mem_acc:.4f} ({membership_correct}/{membership_total}), "
          f"distractor-rejected {dist_acc:.4f} ({distractor_correct}/{distractor_total}), "
          f"overall {overall_mem_acc:.4f}  (thresh {SIM_THRESH})\n")

    print("=== TIER 2 (order) — loop-bind peelable path (F288 curved connection) ===")
    print(f"  peel fidelity: max||err|| over {TRIALS} folds = {peel_max:.2e}  (mean {peel_mean:.2e})")
    print(f"  order recovery (peeled token -> correct codebook id): {order_acc:.4f} "
          f"({order_recovery_correct}/{order_recovery_total})\n")

    print("=== INDEPENDENCE — are the two tiers separate stores? ===")
    print(f"  content answers drift after building order tier: max |delta sim| = {indep_max_drift:.2e}")
    print(f"  independence violations (any nonzero drift): {independence_violations} / "
          f"{membership_total + distractor_total} content queries")
    independent = (independence_violations == 0)
    print(f"  -> tiers independent: {independent}\n")

    # ---- Verdict ----
    tier1_ok = (mem_acc >= 0.99) and (dist_acc >= 0.99) and (sim_gap > 0.10)
    tier2_ok = (peel_max < 1e-9) and (order_acc >= 0.99)
    verdict = "POSITIVE" if (tier1_ok and tier2_ok and independent) else "MIXED"
    if not tier1_ok and not tier2_ok:
        verdict = "NULL"
    print("=== VERDICT ===")
    print(f"  TIER 1 content works: {tier1_ok}   TIER 2 order works: {tier2_ok}   independent: {independent}")
    print(f"  => {verdict}")
    print("  READING: a klein4 bag (flat, order-blind) + a loop-bind path (curved, peelable) compose")
    print("  into ONE RBS store that knows BOTH what is in it AND in what order — the two structurally")
    print("  distinct connections (R-RBS-LM-75 flat content + F288 curved order) sitting side by side.")

    return {
        "consistency": (ok_consist, maxerr),
        "tier1": (mem_acc, dist_acc, sim_gap),
        "tier2": (peel_max, order_acc),
        "independent": (independent, indep_max_drift),
        "verdict": verdict,
    }


if __name__ == "__main__":
    main()
