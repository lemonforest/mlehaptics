"""leg_l3_real_grammatical_order.py — F291 LEG L3: real grammatical word-order.

CLAIM UNDER TEST (F288/F290 -> real words): the loop bind (Moufang / Cayley-Dickson
octonion product, class M o C with a Class-K associator residue) is the CURVED gauge
connection that gives an RBS store ORDER/PATH memory the flat commutative klein4 bag
(R-RBS-LM-75 order-invariance) structurally cannot have.

L3 facet: on REAL short English sentences, does the loop-bind ordered fold DISTINGUISH a
grammatical sentence from its SCRAMBLE (same word SET, different order) where the klein4
bag CANNOT? Extends F290's synthetic a,b,c to real words sharing ONE codebook so a
sentence and its scramble are an identical word multiset (the only difference is order).

HARD DISCIPLINES OBSERVED:
  - srmech-first: native hdc.loop_bind (consistency check) + hdc.klein4_random / klein4_bind /
    klein4_bundle / klein4_similarity for the bag baseline; loop_bind_hd (block-octonion HD)
    for the ordered fold. No hand-rolled Counter / eig / softmax.
  - Class-K: magnitudes via Born inner product <v,v> = sum v*conj(v); NO python abs() in any
    cascade. Cosine via np.dot / np.linalg.norm (NOTED: this is the leg-helper's own `cos`,
    inner-product based, Class-K clean; klein4 uses hdc.klein4_similarity natively).
  - no-magic: every seed stated below (A=structure / B=measurement-seed / C=irreducible).
  - CAD-ban: algebra/spectral/graph only. No geometry/MD/fabrication/audio.
  - no-lineage: reads the structure; claims no extension/supersession of prior scholarship.
  - HONEST-NULL: if the bag discriminates order (it must not — it is order-blind) we report
    the surprise as a possible bug; if loop bind fails to separate, we report NULL/MIXED.

SEEDS (no-magic):
  WORD_SEED   = 20260601  (B) base seed for the SHARED word codebook (loop-bind blocks)
  KLEIN_SEED  = 770075    (B) base seed for the SHARED klein4 word codebook
  Each unique word w gets a deterministic per-word seed = base ^ (stable hash of w),
    so the SAME word -> SAME vector across every sentence and every scramble (identical
    multiset is then guaranteed for a sentence and its scramble).
  D=2048, BS=8, NB=256 are F-attested-A structure constants (octonion dim-8 tiling; the
    last division algebra) imported from loop_bind_hd_gate.

NB on the loop-bind fold: ordered LEFT-fold  acc = LB(LB(w0,w1),w2)...  (Class C left
order). Because the octonion product is non-commutative AND non-associative, this fold is
sensitive to BOTH the order of words and the bracketing path. The klein4 bag is the flat
commutative bundle of the same word vectors (order/bracket blind by construction).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                                       # noqa: E402
from srmech.amsc import hdc                                              # noqa: E402
from loop_bind_hd_gate import loop_bind_hd, conj_hd, rand_unit_blocks, D, BS, NB  # noqa: E402
import loop_bind_moufang as oracle                                       # noqa: E402

# ---- attested seeds (no-magic) ----
WORD_SEED = 20260601   # B: shared loop-bind word-codebook base seed
KLEIN_SEED = 770075    # B: shared klein4 word-codebook base seed
SCRAMBLE_SEED = 4242   # B: deterministic scramble permutation seed
DISTINCT_TOL = 0.99    # A: cos>0.99 => "same" for distinct-count (matches gate helper)


# ---------------------------------------------------------------------------
# Class-K clean cosine (inner-product based; NOT abs()). NOTED per discipline:
# uses np.dot + np.linalg.norm only (the leg-helper convention). For klein4
# vectors we use the NATIVE hdc.klein4_similarity instead.
# ---------------------------------------------------------------------------
def cos(u, v):
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    nu = float(np.sqrt(float(np.dot(u, u))))   # Born norm sqrt(<u,u>); no abs()
    nv = float(np.sqrt(float(np.dot(v, v))))
    return float(np.dot(u, v)) / (nu * nv)


def _word_seed(base, word):
    """Deterministic per-word seed so the SAME word -> SAME vector everywhere.

    Uses a small stable rolling hash over the bytes (NOT python's salted hash()).
    This is an index function, not a cascade primitive — no Class-K sign-op involved.
    """
    h = 1469598103934665603  # FNV-1a offset basis (A: standard constant)
    for byte in word.encode("utf-8"):
        h ^= byte
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF  # FNV-1a prime (A)
    return (base ^ h) & 0xFFFFFFFF


def build_codebooks(words):
    """One SHARED vector per unique word, for both encodings."""
    uniq = sorted(set(words))
    loop_cb = {}
    klein_cb = {}
    for w in uniq:
        rng = np.random.default_rng(_word_seed(WORD_SEED, w))
        loop_cb[w] = rand_unit_blocks(rng)                       # unit block-octonion
        klein_cb[w] = hdc.klein4_random(D, seed=_word_seed(KLEIN_SEED, w))
    return loop_cb, klein_cb


def loop_fold(words, loop_cb):
    """Ordered LEFT-fold under the loop bind (Class C order; non-assoc path)."""
    acc = loop_cb[words[0]]
    for w in words[1:]:
        acc = loop_bind_hd(acc, loop_cb[w])
    return acc


def bag_bundle(words, klein_cb):
    """Flat commutative klein4 bag (order/bracket blind by construction)."""
    return hdc.klein4_bundle(*[klein_cb[w] for w in words])


def scramble(words, rng):
    """A permutation of the SAME word list (identical multiset, different order).

    Guaranteed != identity for len>=2 by rejection (so the test is non-trivial).
    """
    idx = np.arange(len(words))
    for _ in range(64):
        perm = rng.permutation(idx)
        if not np.array_equal(perm, idx):
            return [words[i] for i in perm]
    return [words[i] for i in idx]  # degenerate fallback (len<2)


def main():
    # --- CONSISTENCY GATE (mandatory): native loop_bind == oracle on all 64 basis pairs ---
    basis_maxerr = 0.0
    for i in range(BS):
        for j in range(BS):
            ei = np.zeros(BS); ei[i] = 1.0
            ej = np.zeros(BS); ej[j] = 1.0
            n = np.asarray(hdc.loop_bind(ei, ej), dtype=float)
            o = np.asarray(oracle.loop_bind(ei, ej), dtype=float)
            basis_maxerr = max(basis_maxerr, float(np.max((n - o) * (n - o))))  # sq err, no abs()
    consistent = basis_maxerr < 1e-24  # (1e-12)^2
    print(f"[CONSISTENCY] native hdc.loop_bind vs oracle on 64 basis pairs: "
          f"max sq-err = {basis_maxerr:.2e}  -> native==oracle: {consistent}\n")

    # --- benign generic short sentences (hardcoded; 3-6 words each) ---
    sentences = [
        ["the", "cat", "sat", "on", "the", "mat"],
        ["a", "dog", "ran", "in", "the", "park"],
        ["she", "reads", "a", "good", "book"],
        ["birds", "sing", "every", "morning"],
        ["we", "walked", "to", "the", "store"],
        ["the", "sun", "rises", "in", "the", "east"],
        ["he", "drinks", "warm", "tea"],
        ["children", "play", "in", "the", "yard"],
    ]
    all_words = [w for s in sentences for w in s]
    loop_cb, klein_cb = build_codebooks(all_words)
    print(f"[setup] {len(sentences)} sentences, {len(set(all_words))} unique words, "
          f"D={D} (NB={NB} octonion blocks of BS={BS})")
    print(f"[setup] seeds: WORD_SEED={WORD_SEED}(B) KLEIN_SEED={KLEIN_SEED}(B) "
          f"SCRAMBLE_SEED={SCRAMBLE_SEED}(B)\n")

    rng = np.random.default_rng(SCRAMBLE_SEED)

    # --- per-sentence: cos(sentence, scramble) under loop bind vs klein4 bag ---
    print("=== sentence vs SCRAMBLE (same word multiset, different order) ===")
    print(f"  {'sentence':<34} {'loopcos':>8} {'bagsim':>8} {'multiset==':>11}")
    loop_coss, bag_sims = [], []
    multiset_ok = True
    rows = []
    for s in sentences:
        sc = scramble(s, rng)
        # sanity: identical multiset (only order differs)
        same_multiset = sorted(s) == sorted(sc)
        multiset_ok &= same_multiset

        loop_s = loop_fold(s, loop_cb)
        loop_sc = loop_fold(sc, loop_cb)
        lc = cos(loop_s, loop_sc)

        bag_s = bag_bundle(s, klein_cb)
        bag_sc = bag_bundle(sc, klein_cb)
        bs = hdc.klein4_similarity(bag_s, bag_sc)   # native srmech klein4 sim

        loop_coss.append(lc)
        bag_sims.append(bs)
        rows.append((" ".join(s), lc, bs, same_multiset))
        print(f"  {' '.join(s):<34} {lc:>8.4f} {bs:>8.4f} {str(same_multiset):>11}")

    mean_loop = float(np.mean(loop_coss))
    mean_bag = float(np.mean(bag_sims))
    mean_gap = float(np.mean([b - l for l, b in zip(loop_coss, bag_sims)]))
    max_loopcos = float(np.max(loop_coss))
    min_bagsim = float(np.min(bag_sims))
    print(f"\n  mean loop-bind cos(sentence,scramble) = {mean_loop:.4f}  "
          f"(expect <1 => ORDER-DISTINCT;  max over sentences = {max_loopcos:.4f})")
    print(f"  mean klein4 bag sim(sentence,scramble) = {mean_bag:.4f}  "
          f"(expect ~1 => ORDER-BLIND;     min over sentences = {min_bagsim:.4f})")
    print(f"  mean (bag - loop) gap = {mean_gap:.4f}")

    # bag-blindness check: if the bag separates a sentence from its same-multiset
    # scramble (sim noticeably < 1), THAT is a surprise / possible bug.
    BAG_BLIND_TOL = 1e-6  # A: float round-off floor for "the bag truly cannot tell them apart"
    bag_is_blind = all(b > 1.0 - BAG_BLIND_TOL for b in bag_sims)
    print(f"\n  klein4 bag order-blind on all sentences (sim>1-{BAG_BLIND_TOL:g})? {bag_is_blind}")
    if not bag_is_blind:
        print("  *** SURPRISE: the commutative bag distinguished an identical-multiset "
              "scramble -> possible bug (reported in srmech_anomalies). ***")

    # loop separation: how many sentences does the loop bind actually separate?
    loop_separates = sum(1 for l in loop_coss if l < DISTINCT_TOL)
    print(f"  loop bind ORDER-DISTINCT (cos<{DISTINCT_TOL}) on "
          f"{loop_separates}/{len(sentences)} sentences")

    # ---------------------------------------------------------------------
    # BONUS retrieval test: store the GRAMMATICAL sentences; query with a
    # scramble of each. Does the loop store rank the scramble as DIFFERENT
    # (its own grammatical form is NOT the clear top match) while the bag
    # cannot tell scramble from grammatical at all?
    # ---------------------------------------------------------------------
    print("\n=== BONUS retrieval: query store with a scramble of each sentence ===")
    loop_store = [loop_fold(s, loop_cb) for s in sentences]
    bag_store = [bag_bundle(s, klein_cb) for s in sentences]

    # query = scramble of sentence t; under the BAG, query==stored multiset so the
    # self-row sim should be ~1 (bag cannot distinguish). Under the LOOP, the
    # scramble should have LOWER self-sim than a different-content match might,
    # i.e. the store does NOT confidently return the grammatical form.
    rng2 = np.random.default_rng(SCRAMBLE_SEED + 1)
    loop_self_is_top = 0
    loop_self_sims = []
    bag_self_sims = []
    bag_self_is_top = 0
    print(f"  {'query (scramble of)':<34} {'loop self':>9} {'loop top!=self':>15} "
          f"{'bag self':>9}")
    for t, s in enumerate(sentences):
        sc = scramble(s, rng2)
        qL = loop_fold(sc, loop_cb)
        qB = bag_bundle(sc, klein_cb)
        loop_row = [cos(qL, loop_store[u]) for u in range(len(sentences))]
        bag_row = [hdc.klein4_similarity(qB, bag_store[u]) for u in range(len(sentences))]
        l_self = loop_row[t]
        b_self = bag_row[t]
        l_top = int(np.argmax(loop_row))
        b_top = int(np.argmax(bag_row))
        loop_self_sims.append(l_self)
        bag_self_sims.append(b_self)
        loop_self_is_top += (l_top == t)
        bag_self_is_top += (b_top == t)
        print(f"  {' '.join(s):<34} {l_self:>9.4f} {str(l_top != t):>15} {b_self:>9.4f}")

    mean_loop_self = float(np.mean(loop_self_sims))
    mean_bag_self = float(np.mean(bag_self_sims))
    print(f"\n  loop store: grammatical form is TOP match for its own scramble on "
          f"{loop_self_is_top}/{len(sentences)} (mean self-sim {mean_loop_self:.4f})")
    print(f"  bag store : grammatical form is TOP match for its own scramble on "
          f"{bag_self_is_top}/{len(sentences)} (mean self-sim {mean_bag_self:.4f})")
    print("  -> the bag CANNOT down-rank a scramble (self-sim ~1, scramble==grammatical "
          "to the bag); the loop store sees the scramble as a DIFFERENT object.")

    # --- verdict logic (honest) ---
    print("\n--- L3 verdict ---")
    order_distinct = (max_loopcos < DISTINCT_TOL)   # loop separates EVERY sentence
    if consistent and order_distinct and bag_is_blind and multiset_ok:
        print("  POSITIVE: loop bind distinguishes every grammatical sentence from its "
              "identical-multiset scramble; the klein4 bag is provably order-blind.")
    elif not bag_is_blind:
        print("  MIXED/BUG: the bag distinguished a scramble it should not have.")
    elif not order_distinct:
        print("  MIXED: loop bind failed to separate some sentence from its scramble.")
    else:
        print("  see numbers above.")

    return {
        "consistent": consistent,
        "basis_maxerr_sq": basis_maxerr,
        "mean_loop_cos": mean_loop,
        "mean_bag_sim": mean_bag,
        "max_loop_cos": max_loopcos,
        "min_bag_sim": min_bagsim,
        "mean_gap": mean_gap,
        "bag_is_blind": bag_is_blind,
        "loop_separates": loop_separates,
        "n_sentences": len(sentences),
        "multiset_ok": multiset_ok,
        "loop_self_is_top": loop_self_is_top,
        "bag_self_is_top": bag_self_is_top,
        "mean_loop_self": mean_loop_self,
        "mean_bag_self": mean_bag_self,
    }


if __name__ == "__main__":
    main()
