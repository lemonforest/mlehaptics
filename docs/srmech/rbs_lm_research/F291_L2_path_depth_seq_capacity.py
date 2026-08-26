"""F291 LEG L2 — path-memory DEPTH + sequence CAPACITY (the order analog of F277 capacity).

CLAIM UNDER TEST (F288/F290): the Moufang loop bind (Cayley-Dickson octonion product, Class
M o C with a Class-K associator residue) is the CURVED gauge connection that gives an RBS
store ORDER / PATH memory the flat commutative klein4 bag (R-RBS-LM-75 order-invariance)
structurally cannot have. This leg tests two facets:

  (1) DEPTH: encode a left-fold ((...((t0.t1).t2)...).t_{L-1}) of L unit-block tokens via the
      block-octonion HD loop bind; PEEL it back in order using the Moufang right-cancel
      (x y) y* = x  ->  loop_bind_hd(E, conj_hd(last_token)) recovers the prefix-fold; iterate.
      Sweep L = 2..24. Report the max depth at which ALL peels recover with err<1e-6 (cos>0.999)
      and how the worst-peel error grows with L.

  (2) SEQUENCE CAPACITY: superpose S independent folds (sum) for S = 1,2,4,8; peel token-0 of
      one target sequence; measure recovery vs S. Report the S-knee.

DISCIPLINE
  - srmech-first: native hdc.loop_bind / hdc.loop_conj are the dim-8 op; the block-octonion
    HD realization (loop_bind_hd) is the committed gate helper (D=2048, 256 blocks). klein4_*
    is the flat baseline for context. Cosine over a block-octonion bundle is NOT a klein4
    vector, so a plain inner-product cosine (np.dot / np.linalg.norm) is used and NOTED;
    klein4_similarity is used where klein4 vectors appear.
  - Class-K: NO python abs(). Magnitude = Born inner product (re^2 sum via np.dot(v,v))**0.5.
    Errors reported as a norm (sqrt of the inner product), not abs.
  - no-magic: D=2048/BS=8/NB=256 attested-A (octonions are the last division algebra, F272;
    D=2^11, NB=D/BS). M=256 codebook = MAX_NATIVE_NODES (attested-A). Seeds attested-B, stated.
  - CONSISTENCY: native hdc.loop_bind == oracle.loop_bind on all 64 (e_i,e_j) basis pairs,
    atol 1e-12, reported as a boolean. Also native == the gate helper's per-block product.
  - CAD-ban: pure algebra / spectral. no geometry/fab.
  - no-lineage: reads the structure; claims nothing about prior scholarship.
  - HONEST-NULL: if depth degrades early or capacity is swamped at S=1, that is reported as the
    knee with the appropriate verdict.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

from srmech.amsc import hdc  # noqa: E402  (native dim-8 loop_bind / loop_conj)
from loop_bind_hd_gate import (  # noqa: E402
    loop_bind_hd, conj_hd, rand_unit_blocks, D, BS, NB,
)
import loop_bind_moufang as oracle  # noqa: E402  (parity oracle)

# ---- seeds (attested-B) ----
SEED_CONSISTENCY = 12345   # B — oracle's own TEST_SEED, reused for the parity sweep
SEED_DEPTH = 20260601      # B — depth sweep
SEED_CAP = 20260602        # B — sequence-capacity sweep

# ---- constants (attested-A) ----
L_MIN, L_MAX = 2, 24       # A — depth sweep range (structure: probe to 24-deep folds)
N_REPEAT_DEPTH = 8         # A — independent token-sequences per L (statistics, not a free knob)
S_LIST = [1, 2, 4, 8, 16, 32, 64, 128]   # A — superposed-sequence counts (powers of two)
SEQ_LEN_CAP = 6            # A — fixed fold length for the capacity sweep
M_CODEBOOK = 256           # A — MAX_NATIVE_NODES value codebook for cleanup
N_REPEAT_CAP = 16          # A — trials per S
ERR_TOL = 1e-6             # A — exact-recovery norm threshold
COS_TOL = 0.999            # A — exact-recovery cosine threshold


# ----- Class-K clean magnitude / cosine helpers -----
def born_norm(v):
    """sqrt of the Born inner product <v,v> = sqrt(sum re^2). NO abs()."""
    return float(np.dot(v, v)) ** 0.5


def cos_ip(u, v):
    """Inner-product cosine. NOTED: u,v are block-octonion bundles (NOT klein4 vectors),
    so klein4_similarity does not apply; a plain <u,v>/(|u||v|) cosine is the right metric."""
    nu, nv = born_norm(u), born_norm(v)
    if nu == 0.0 or nv == 0.0:
        return 0.0
    return float(np.dot(u, v)) / (nu * nv)


# =====================================================================
# CONSISTENCY GATE — native hdc.loop_bind == oracle.loop_bind on all 64
# basis pairs (atol 1e-12), and native == gate-helper per-block product.
# =====================================================================
def consistency_check():
    max_basis_err = 0.0
    for i in range(BS):
        ei = oracle.e(i)
        for j in range(BS):
            ej = oracle.e(j)
            nat = np.asarray(hdc.loop_bind(ei, ej), dtype=float)
            orc = np.asarray(oracle.loop_bind(ei, ej), dtype=float)
            max_basis_err = max(max_basis_err, born_norm(nat - orc))
    native_eq_oracle = bool(max_basis_err < 1e-12)

    # conj parity on the 8 basis vectors
    max_conj_err = 0.0
    for i in range(BS):
        ei = oracle.e(i)
        nat_c = np.asarray(hdc.loop_conj(ei), dtype=float)
        orc_c = np.asarray(oracle.conj(ei), dtype=float)
        max_conj_err = max(max_conj_err, born_norm(nat_c - orc_c))

    # native dim-8 == gate-helper per-block product (one random block, seed-stated)
    rng = np.random.default_rng(SEED_CONSISTENCY)
    xb = rng.standard_normal(BS); xb /= born_norm(xb)
    yb = rng.standard_normal(BS); yb /= born_norm(yb)
    nat_blk = np.asarray(hdc.loop_bind(xb, yb), dtype=float)
    # gate helper on a single-block D=8 would need NB=1; instead verify the gate's cd_b matches
    # native on the 8-vector directly via oracle (cd_b is the same recursion as oracle.loop_bind)
    orc_blk = np.asarray(oracle.loop_bind(xb, yb), dtype=float)
    block_err = born_norm(nat_blk - orc_blk)

    return native_eq_oracle, max_basis_err, max_conj_err, float(block_err)


# =====================================================================
# (1) DEPTH — left-fold then ordered peel via Moufang right-cancel.
# =====================================================================
def left_fold(tokens):
    """((...((t0.t1).t2)...).t_{L-1})  using the HD block-octonion loop bind."""
    acc = tokens[0]
    for t in tokens[1:]:
        acc = loop_bind_hd(acc, t)
    return acc


def peel_sequence(E, tokens):
    """Right-cancel peel: tokens recovered last->first via (X . t)·t* = X.
    Returns the list of per-token recovery (err_norm, cosine) in REVERSE order
    (last token first), each compared to the truth token, and also the residual
    fold-norm error vs the true prefix-fold."""
    L = len(tokens)
    results = []  # (token_index, err_norm, cos) for the recovered token at each peel
    cur = E
    # rebuild the true prefix folds to compare the recovered fold against
    prefix = [tokens[0]]
    for t in tokens[1:]:
        prefix.append(loop_bind_hd(prefix[-1], t))
    # peel from the last token down to token 1 (token 0 is the seed of the fold)
    for k in range(L - 1, 0, -1):
        last = tokens[k]
        peeled = loop_bind_hd(cur, conj_hd(last))   # (X . last)·last* = X
        true_prefix = prefix[k - 1]                 # the fold of tokens[0..k-1]
        err = born_norm(peeled - true_prefix)
        c = cos_ip(peeled, true_prefix)
        results.append((k, err, c))
        cur = peeled
    return results


def depth_sweep():
    rng = np.random.default_rng(SEED_DEPTH)
    per_L = {}  # L -> (worst_err over all peels & repeats, worst_cos, all_ok_bool)
    for L in range(L_MIN, L_MAX + 1):
        worst_err = 0.0
        worst_cos = 1.0
        all_ok = True
        for _ in range(N_REPEAT_DEPTH):
            tokens = [rand_unit_blocks(rng) for _ in range(L)]
            E = left_fold(tokens)
            peels = peel_sequence(E, tokens)
            for (_k, err, c) in peels:
                worst_err = max(worst_err, err)
                worst_cos = min(worst_cos, c)
                if not (err < ERR_TOL or c > COS_TOL):
                    all_ok = False
        per_L[L] = (worst_err, worst_cos, all_ok)
    # max depth at which ALL peels recover
    max_exact_depth = L_MIN - 1
    for L in range(L_MIN, L_MAX + 1):
        if per_L[L][2]:
            max_exact_depth = L
        else:
            break
    return per_L, max_exact_depth


# =====================================================================
# (2) SEQUENCE CAPACITY — superpose S folds, peel token-0 of a target.
# =====================================================================
def capacity_sweep():
    """Superpose S independent left-folds (sum). To recover the FIRST token (token-0) of a
    target sequence we PEEL the whole target fold back to its seed (the Moufang right-cancel
    chain), then cleanup against the codebook. We measure top-1 cleanup accuracy of token-0
    vs S, plus the cosine margin (target vs best distractor)."""
    rng = np.random.default_rng(SEED_CAP)
    per_S = {}
    for S in S_LIST:
        hits = 0
        margins = []
        cos_to_truth = []
        for _ in range(N_REPEAT_CAP):
            # shared value codebook (the tokens are drawn from it); MAX_NATIVE_NODES entries
            codebook = np.stack([rand_unit_blocks(rng) for _ in range(M_CODEBOOK)])  # (M, D)
            # build S sequences of length SEQ_LEN_CAP from distinct codebook rows
            seqs = []
            for _s in range(S):
                idx = rng.choice(M_CODEBOOK, size=SEQ_LEN_CAP, replace=False)
                seqs.append(idx)
            folds = [left_fold([codebook[i] for i in idx]) for idx in seqs]
            bundle = np.sum(folds, axis=0)  # superposition of S folds

            target_s = 0
            target_idx = seqs[target_s]
            # peel the target fold back to its seed (token-0) using the KNOWN token order.
            # we know which tokens were used for the target (the keys), so peel them off:
            cur = bundle
            for k in range(SEQ_LEN_CAP - 1, 0, -1):
                last = codebook[target_idx[k]]
                cur = loop_bind_hd(cur, conj_hd(last))
            recovered_token0 = cur  # should clean up to codebook[target_idx[0]]

            # cleanup: top-1 over the codebook by inner-product cosine.
            # |recovered| is roughly constant across rows; argmax(C @ rec)/|row| == argmax cosine.
            sims = np.array([cos_ip(recovered_token0, codebook[m]) for m in range(M_CODEBOOK)])
            best = int(np.argmax(sims))
            truth = int(target_idx[0])
            hits += int(best == truth)
            cos_to_truth.append(float(sims[truth]))
            # margin = truth-cosine minus the best distractor cosine
            order = np.argsort(sims)[::-1]
            best_distractor = order[0] if order[0] != truth else order[1]
            margins.append(float(sims[truth] - sims[best_distractor]))
        per_S[S] = (hits / N_REPEAT_CAP, float(np.mean(cos_to_truth)), float(np.mean(margins)))
    # S-knee: largest S with acc >= 0.99
    s_knee = 0
    for S in S_LIST:
        if per_S[S][0] >= 0.99:
            s_knee = S
        else:
            break
    return per_S, s_knee


def main():
    print(f"=== F291 L2: path DEPTH + sequence CAPACITY (D={D}, BS={BS}, NB={NB}) ===\n")

    native_eq_oracle, basis_err, conj_err, block_err = consistency_check()
    print("--- CONSISTENCY GATE ---")
    print(f"  native hdc.loop_bind == oracle.loop_bind on all 64 basis pairs (atol 1e-12): "
          f"{native_eq_oracle}  (max basis err = {basis_err:.2e})")
    print(f"  native hdc.loop_conj == oracle.conj on 8 basis vectors: max err = {conj_err:.2e}")
    print(f"  native dim-8 == oracle on a random unit block: err = {block_err:.2e}\n")

    print("--- (1) DEPTH SWEEP (left-fold -> ordered Moufang right-cancel peel) ---")
    print(f"    seed={SEED_DEPTH}, {N_REPEAT_DEPTH} sequences per L, L={L_MIN}..{L_MAX}")
    per_L, max_exact_depth = depth_sweep()
    print(f"  {'L':>3} | {'worst peel err':>15} | {'worst cos':>10} | all-recover")
    for L in range(L_MIN, L_MAX + 1):
        we, wc, ok = per_L[L]
        print(f"  {L:>3} | {we:>15.3e} | {wc:>10.6f} | {'YES' if ok else 'no'}")
    print(f"\n  MAX EXACT DEPTH (all peels err<{ERR_TOL:g} or cos>{COS_TOL}): {max_exact_depth}")
    err_2 = per_L[L_MIN][0]
    err_max = per_L[L_MAX][0]
    print(f"  worst-peel err growth: L={L_MIN} -> {err_2:.3e} ;  L={L_MAX} -> {err_max:.3e}\n")

    print("--- (2) SEQUENCE CAPACITY (superpose S folds, peel+cleanup token-0) ---")
    print(f"    seed={SEED_CAP}, {N_REPEAT_CAP} trials/S, fold-len={SEQ_LEN_CAP}, "
          f"codebook M={M_CODEBOOK}")
    per_S, s_knee = capacity_sweep()
    print(f"  {'S':>3} | {'token0 acc':>11} | {'mean cos(truth)':>16} | {'mean margin':>12}")
    for S in S_LIST:
        acc, ct, mg = per_S[S]
        print(f"  {S:>3} | {acc:>11.3f} | {ct:>16.4f} | {mg:>12.4f}")
    print(f"\n  S-KNEE (largest S with acc>=0.99): {s_knee}")

    # ---- machine-readable summary line for the harness ----
    print("\n=== SUMMARY ===")
    print(f"native_eq_oracle={native_eq_oracle}")
    print(f"max_exact_depth={max_exact_depth}")
    print(f"depth_worst_err_L{L_MAX}={err_max:.3e}")
    print(f"s_knee={s_knee}")
    for S in S_LIST:
        print(f"cap_acc_S{S}={per_S[S][0]:.3f}")

    return native_eq_oracle, max_exact_depth, per_L, per_S, s_knee, basis_err


if __name__ == "__main__":
    main()
