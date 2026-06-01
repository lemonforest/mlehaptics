"""F291 LEG L1 (FLAGSHIP) — autoregressive order-memory.

QUESTION: does the order-AWARE loop-bind context store improve NEXT-token
prediction over the order-BLIND klein4 bag, on a task where ORDER carries
information (TASK-A), and do they TIE when order is irrelevant (TASK-B)?

STRUCTURE READ (no-lineage): the Moufang loop bind (Cayley-Dickson octonion
product, class M o C with a Class-K associator residue, F271/F272) is
NON-COMMUTATIVE: loop_bind(x,y) != loop_bind(y,x). The flat commutative klein4
bind/bundle bag is order-INVARIANT (R-RBS-LM-75): klein4_bundle(x,y) ==
klein4_bundle(y,x). So a 2nd-order rule next=f(prev2,prev1) with f(x,y)!=f(y,x)
is exactly the discriminator: the bag CONFLATES context (x,y) with (y,x) ->
collisions in the associative store -> wrong cleanup; the loop-bind key keeps
them DISTINCT keys -> clean retrieval. This leg measures whether that distinction
turns into measured next-token accuracy.

PIPELINE (all stores share the SAME training pairs + the SAME metric):
  - 12 symbols, two parallel codebooks:
      octonion: rand_unit_blocks(rng)        (unit block-octonion, D=2048)
      klein4  : hdc.klein4_random(D, seed)   (uint8 in {0,1,2,3}, D=2048)
    plus a parallel VALUE codebook for each algebra (the "next-token" targets).
  - For each (prev2, prev1) -> next training pair:
      LOOP store    : key = loop_bind_hd(oct[prev2], oct[prev1])  (ORDERED, M o C)
                      bind key to oct-value(next), superpose (sum) over pairs.
      KLEIN4-BAG    : key = hdc.klein4_bundle(k4[prev2], k4[prev1]) (ORDER-BLIND)
                      klein4_bind key to k4-value(next), klein4_bundle-superpose.
      OCT-BAG (ctrl): key = unit-blocks(oct[prev2] + oct[prev1])   (ORDER-BLIND
                      but SAME OCTONION ALGEBRA + SAME VALUE CODEBOOK as LOOP).
                      CAVEAT measured: the commutative SUM key has much worse
                      key-separation than the loop product (mean|cos| 0.17 vs
                      0.02; some distinct pairs sum-COLLIDE, cos=1.0) -> OCT-BAG
                      conflates beyond just swaps, so it is a LOWER bound, not a
                      clean order-isolation. The non-commutativity and the
                      key-spreading are the SAME property of the product (can't
                      be cleanly separated by a commutative octonion combiner).
      KLEIN4-POSTAG : key = klein4_bundle(klein4_bind(k4[prev2],P0),
                      (CONTROL)            klein4_bind(k4[prev1],P1))  -- the
                      standard VSA position-role trick that makes the SAME klein4
                      algebra ORDER-AWARE (sim(key(x,y),key(y,x))=0.56<1). This is
                      the clean isolation: KLEIN4-BAG vs KLEIN4-POSTAG differ ONLY
                      in order-awareness, SAME algebra/capacity -> the order effect
                      with no octonion-vs-klein4 confound.
  - INFERENCE: encode the query context the same way, retrieve predicted next:
      LOOP / OCT-BAG : rec = unbind_hd(key, store) ; argmax cosine over oct VALUE.
      KLEIN4-BAG     : rec = hdc.klein4_unbind(store, key) ; argmax
                       klein4_similarity over k4 VALUE codebook.
  - METRIC: next-token accuracy = (# correct argmax) / (# query contexts).

TASK-A (ORDER-DEPENDENT): next = f(prev2, prev1), f deterministic, f(x,y)!=f(y,x)
  for (nearly) all pairs. Training set includes BOTH (x,y) and (y,x) contexts so
  the bag's conflation actually bites.
TASK-B (ORDER-INDEPENDENT): next = g({prev2,prev1}), g order-blind (g(x,y)=g(y,x)).
  Same two contexts (x,y) and (y,x) map to the SAME next -> no conflation penalty.

HONEST expectation: LOOP beats BAG on TASK-A; they TIE on TASK-B. If LOOP does
NOT beat BAG on TASK-A this is a NULL/MIXED -> reported honestly.

DISCIPLINE:
  - srmech-first: keys/values/binds/cleanup via hdc.* and the committed HD gate
    (block-octonion loop_bind_hd, which is the D=2048 realization of the native
    hdc.loop_bind, F291 #811 gate). klein4_* for the bag side. The ONLY hand
    cosine is np.dot/np.linalg.norm on the OCTONION value cleanup (klein4 side
    uses hdc.klein4_similarity); noted at the callsite.
  - Class-K: no abs(); octonion magnitude via Born inner product re^2+im^2 (np.dot
    of a vector with itself); sign handling via conj (conj_hd / hdc.loop_conj).
  - CONSISTENCY: native hdc.loop_bind == oracle.loop_bind on all 64 e_i,e_j basis
    pairs (atol 1e-12) is verified and reported.
  - no-magic seeds (all attested-B): SEED_OCT=4040, SEED_K4_BASE=5050,
    SEED_RULE_A=6061, SEED_RULE_B=7071. Structure constants attested-A:
    V=12 symbols, D=2048/BS=8/NB=256 (block-octonion tiling, F291 gate),
    octonion DIM=8 (last division algebra, F270).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from srmech.amsc import hdc  # noqa: E402  (klein4_* + native loop_bind/loop_conj)
from loop_bind_hd_gate import (  # noqa: E402  (D=2048 block-octonion gate, F291 #811)
    loop_bind_hd,
    unbind_hd,
    conj_hd,
    rand_unit_blocks,
    D,
    BS,
    NB,
)
import loop_bind_moufang as oracle  # noqa: E402  (dim-8 parity oracle)

# ----------------------------------------------------------------------------
# Attested constants (no-magic).
#   A = structure-cascade ; B = measurement/seed.
# ----------------------------------------------------------------------------
V = 12               # A: vocabulary size (~12 symbols, bounded testbed)
DIM8 = 8             # A: octonion dimension = last division algebra (F270)
SEED_OCT = 4040      # B: octonion token + value codebook seed
SEED_K4_BASE = 5050  # B: klein4 token + value codebook seed base (per-symbol offset)
SEED_RULE_A = 6061   # B: TASK-A rule-table seed (order-DEPENDENT f)
SEED_RULE_B = 7071   # B: TASK-B rule-table seed (order-BLIND g)
SEED_POS0 = 800001   # B: klein4 POSITION-0 role vector (prev2 slot)
SEED_POS1 = 800002   # B: klein4 POSITION-1 role vector (prev1 slot)
N_SEEDS = 3          # A: codebook re-draws to average out single-seed luck (bounded)


# ----------------------------------------------------------------------------
# Consistency gate: native hdc.loop_bind == oracle.loop_bind on the 8x8 basis.
# ----------------------------------------------------------------------------
def _basis8(i):
    v = np.zeros(DIM8)
    v[i] = 1.0
    return v


def check_native_eq_oracle():
    max_err = 0.0
    for i in range(DIM8):
        for j in range(DIM8):
            a = np.asarray(hdc.loop_bind(_basis8(i), _basis8(j)), dtype=float)
            b = np.asarray(oracle.loop_bind(_basis8(i), _basis8(j)), dtype=float)
            diff = a - b
            # Class-K clean magnitude: Born inner product <d,d>, no abs().
            max_err = max(max_err, float(np.dot(diff, diff)) ** 0.5)
    return max_err, (max_err < 1e-12)


# ----------------------------------------------------------------------------
# Codebooks.
# ----------------------------------------------------------------------------
def build_codebooks(off=0):
    """Return (oct_tok, k4_tok, oct_val, k4_val): each a list of V hypervectors.

    tok = the embedding used to FORM context keys.
    val = the "next-token" target embedding the store binds keys to and that
          cleanup runs over. Distinct codebook so a token's key-role and
          value-role vectors are independent (standard VSA practice).
    off = per-seed offset (no-magic: derived from the attested seed bases) so
          multiple codebook draws average out single-seed luck."""
    rng = np.random.default_rng(SEED_OCT + off)
    oct_tok = [rand_unit_blocks(rng) for _ in range(V)]
    oct_val = [rand_unit_blocks(rng) for _ in range(V)]
    # klein4 codebooks: independent seeds per symbol (no-magic: derived offsets).
    base = SEED_K4_BASE + 100000 * off
    k4_tok = [hdc.klein4_random(D, seed=base + s) for s in range(V)]
    k4_val = [hdc.klein4_random(D, seed=base + 1000 + s) for s in range(V)]
    return oct_tok, k4_tok, oct_val, k4_val


# ----------------------------------------------------------------------------
# Rule tables.
# ----------------------------------------------------------------------------
def rule_table_order_dependent():
    """f[(x,y)] -> next, deterministic, with f(x,y) != f(y,x) for ~all x!=y.

    Construction: f(x,y) = T[(2*x + 3*y) mod V] for a fixed permutation T. The
    asymmetric linear form 2x+3y means swapping x,y shifts the index by (x-y),
    so f(x,y)!=f(y,x) whenever (x-y) mod V != 0 AND T separates the two indices
    (T is a permutation -> it does). Diagonal x==y trivially symmetric.
    """
    rng = np.random.default_rng(SEED_RULE_A)
    T = rng.permutation(V)
    f = {}
    for x in range(V):
        for y in range(V):
            f[(x, y)] = int(T[(2 * x + 3 * y) % V])
    return f


def rule_table_order_blind():
    """g[(x,y)] -> next, order-blind: g(x,y) == g(y,x).

    g(x,y) = T[(x + y) mod V] (symmetric in x,y) for a fixed permutation T.
    """
    rng = np.random.default_rng(SEED_RULE_B)
    T = rng.permutation(V)
    g = {}
    for x in range(V):
        for y in range(V):
            g[(x, y)] = int(T[(x + y) % V])
    return g


def all_ordered_contexts():
    """Every ordered (prev2, prev1) pair over V symbols. Excludes diagonal
    x==y so the order-test is on genuinely-orderable pairs (x!=y); both (x,y)
    AND (y,x) are present -> the bag's conflation is exercised."""
    return [(x, y) for x in range(V) for y in range(V) if x != y]


# ----------------------------------------------------------------------------
# LOOP store (order-aware, M o C) and BAG store (order-blind klein4).
# ----------------------------------------------------------------------------
def unit_blocks(vec):
    """Per-block unit-normalize a D-vector -> each octonion block is unit (so the
    block-octonion loop bind stays invertible). Class-K clean: block magnitude is
    the Born norm sqrt(<b,b>), no abs(); zero blocks left as-is (norm forced 1)."""
    b = vec.reshape(NB, BS)
    n = np.linalg.norm(b, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (b / n).reshape(D)


def _oct_key(p2, p1, oct_tok, ordered):
    """ORDERED loop-bind key (M o C) or ORDER-BLIND unit-block sum key, same algebra."""
    if ordered:
        return loop_bind_hd(oct_tok[p2], oct_tok[p1])
    # order-blind: unit-normalized SUM is commutative (key(x,y)==key(y,x)) yet a
    # valid unit-block octonion -> unbind_hd still inverts it.
    return unit_blocks(oct_tok[p2] + oct_tok[p1])


def build_oct_store(pairs, rule, oct_tok, oct_val, ordered):
    """Superpose loop_bind(oct-key, value(next)) over all pairs.

    ordered=True  -> LOOP store (ORDERED key, M o C).
    ordered=False -> OCT-BAG control (ORDER-BLIND key, same octonion algebra).
    store = sum_pairs loop_bind_hd(key, oct_val[next])."""
    store = np.zeros(D)
    for (p2, p1) in pairs:
        key = _oct_key(p2, p1, oct_tok, ordered)
        nxt = rule[(p2, p1)]
        store = store + loop_bind_hd(key, oct_val[nxt])
    return store


def oct_predict(p2, p1, store, oct_tok, oct_val, ordered):
    """Unbind the oct key, argmax cosine over the octonion VALUE codebook.

    cosine here is np.dot / np.linalg.norm on octonion HD vectors (NOTED hand
    cosine: octonion blocks are real R^8, no klein4 sim applies; magnitude is
    the Born norm sqrt(<v,v>), Class-K clean, no abs())."""
    key = _oct_key(p2, p1, oct_tok, ordered)
    rec = unbind_hd(key, store)
    rn = float(np.dot(rec, rec)) ** 0.5
    best, best_c = -1, -2.0
    for s in range(V):
        vv = oct_val[s]
        c = float(np.dot(rec, vv)) / (rn * (float(np.dot(vv, vv)) ** 0.5))
        if c > best_c:
            best_c, best = c, s
    return best


def build_bag_store(pairs, rule, k4_tok, k4_val):
    """Superpose klein4_bind(order-blind-key, value(next)) over all pairs.

    key = klein4_bundle(k4_tok[prev2], k4_tok[prev1])  (ORDER-BLIND bag).
    store = klein4_bundle over pairs of klein4_bind(key, k4_val[next]).
    """
    bound = []
    for (p2, p1) in pairs:
        key = hdc.klein4_bundle(k4_tok[p2], k4_tok[p1])  # variadic, 2 args
        nxt = rule[(p2, p1)]
        bound.append(hdc.klein4_bind(key, k4_val[nxt]))
    # klein4_bundle is variadic, NOT a list -> splat.
    return hdc.klein4_bundle(*bound)


def bag_predict(p2, p1, store, k4_tok, k4_val):
    """Unbind the order-blind key, argmax klein4_similarity over k4 VALUE codebook."""
    key = hdc.klein4_bundle(k4_tok[p2], k4_tok[p1])
    rec = hdc.klein4_unbind(store, key)
    best, best_c = -1, -2.0
    for s in range(V):
        c = hdc.klein4_similarity(rec, k4_val[s])
        if c > best_c:
            best_c, best = c, s
    return best


def _postag_key(p2, p1, k4_tok, pos0, pos1):
    """ORDER-AWARE klein4 key via position roles (standard VSA trick):
    key = bundle( bind(tok[p2], P0), bind(tok[p1], P1) ). Same klein4 algebra
    as KLEIN4-BAG; the ONLY difference is the position binding -> isolates order."""
    return hdc.klein4_bundle(hdc.klein4_bind(k4_tok[p2], pos0),
                             hdc.klein4_bind(k4_tok[p1], pos1))


def build_postag_store(pairs, rule, k4_tok, k4_val, pos0, pos1):
    bound = []
    for (p2, p1) in pairs:
        key = _postag_key(p2, p1, k4_tok, pos0, pos1)
        bound.append(hdc.klein4_bind(key, k4_val[rule[(p2, p1)]]))
    return hdc.klein4_bundle(*bound)


def postag_predict(p2, p1, store, k4_tok, k4_val, pos0, pos1):
    key = _postag_key(p2, p1, k4_tok, pos0, pos1)
    rec = hdc.klein4_unbind(store, key)
    best, best_c = -1, -2.0
    for s in range(V):
        c = hdc.klein4_similarity(rec, k4_val[s])
        if c > best_c:
            best_c, best = c, s
    return best


# ----------------------------------------------------------------------------
# Drive a task.
# ----------------------------------------------------------------------------
def run_task(rule, oct_tok, k4_tok, oct_val, k4_val, pos0, pos1):
    pairs = all_ordered_contexts()  # train AND test on every ordered context
    loop_store = build_oct_store(pairs, rule, oct_tok, oct_val, ordered=True)
    octbag_store = build_oct_store(pairs, rule, oct_tok, oct_val, ordered=False)
    k4bag_store = build_bag_store(pairs, rule, k4_tok, k4_val)
    postag_store = build_postag_store(pairs, rule, k4_tok, k4_val, pos0, pos1)

    loop_ok = octbag_ok = k4bag_ok = postag_ok = 0
    # diagnostic: how many ordered contexts are genuinely order-discriminating
    # (f(x,y) != f(y,x)) -> the contexts where an order-blind key MUST collide.
    disc = 0
    # swap-confusion: on order-discriminating contexts where KLEIN4-BAG is WRONG,
    # how often does it emit the SWAPPED answer f(p1,p2)? -> the conflation fingerprint.
    k4bag_swap_hits = 0
    k4bag_wrong_on_disc = 0
    for (p2, p1) in pairs:
        nxt = rule[(p2, p1)]
        swapped = rule[(p1, p2)]
        is_disc = (nxt != swapped)
        if is_disc:
            disc += 1
        loop_ok += int(oct_predict(p2, p1, loop_store, oct_tok, oct_val, True) == nxt)
        octbag_ok += int(oct_predict(p2, p1, octbag_store, oct_tok, oct_val, False) == nxt)
        k4_pred = bag_predict(p2, p1, k4bag_store, k4_tok, k4_val)
        k4bag_ok += int(k4_pred == nxt)
        postag_ok += int(postag_predict(p2, p1, postag_store, k4_tok, k4_val, pos0, pos1) == nxt)
        if is_disc and k4_pred != nxt:
            k4bag_wrong_on_disc += 1
            if k4_pred == swapped:
                k4bag_swap_hits += 1
    n = len(pairs)
    swap_rate = (k4bag_swap_hits / k4bag_wrong_on_disc) if k4bag_wrong_on_disc else 0.0
    return {
        "n_contexts": n,
        "n_order_discriminating": disc,
        "loop_acc": loop_ok / n,
        "octbag_acc": octbag_ok / n,     # order-blind, same octonion algebra (lower bound)
        "k4bag_acc": k4bag_ok / n,       # literal R-RBS-LM-75 order-blind baseline
        "postag_acc": postag_ok / n,     # CLEAN order-isolation: klein4 made order-aware
        "k4bag_wrong_on_disc": k4bag_wrong_on_disc,
        "k4bag_swap_confusion_rate": swap_rate,  # fraction of bag errors = the swapped answer
    }


def run_task_avg(rule, pos0, pos1):
    """Average run_task over N_SEEDS independent codebook draws (bounded)."""
    keys = ["loop_acc", "octbag_acc", "k4bag_acc", "postag_acc",
            "k4bag_swap_confusion_rate"]
    acc = {k: 0.0 for k in keys}
    tot_wrong = 0
    last = None
    for off in range(N_SEEDS):
        oct_tok, k4_tok, oct_val, k4_val = build_codebooks(off=off)
        r = run_task(rule, oct_tok, k4_tok, oct_val, k4_val, pos0, pos1)
        # weight swap-rate by the count of bag-errors it was computed over
        for k in keys:
            if k == "k4bag_swap_confusion_rate":
                acc[k] += r[k] * r["k4bag_wrong_on_disc"]
            else:
                acc[k] += r[k]
        tot_wrong += r["k4bag_wrong_on_disc"]
        last = r
    out = {k: (acc[k] / N_SEEDS) for k in keys if k != "k4bag_swap_confusion_rate"}
    out["k4bag_swap_confusion_rate"] = (acc["k4bag_swap_confusion_rate"] / tot_wrong) if tot_wrong else 0.0
    out["n_contexts"] = last["n_contexts"]
    out["n_order_discriminating"] = last["n_order_discriminating"]
    out["k4bag_wrong_on_disc_total"] = tot_wrong
    return out


def main():
    print("=" * 74)
    print("F291 L1 — autoregressive order-memory: loop-bind key vs klein4 bag")
    print("=" * 74)

    max_err, consistent = check_native_eq_oracle()
    print(f"\n[CONSISTENCY] native hdc.loop_bind == oracle.loop_bind on 64 basis "
          f"pairs: max||err||={max_err:.2e}  -> {consistent}")

    oct_tok, k4_tok, oct_val, k4_val = build_codebooks()
    pos0 = hdc.klein4_random(D, seed=SEED_POS0)
    pos1 = hdc.klein4_random(D, seed=SEED_POS1)
    print(f"[codebooks] V={V} symbols; octonion D={D} ({NB} blocks x BS={BS}); "
          f"klein4 D={D} uint8; accuracies averaged over {N_SEEDS} codebook draws")

    # sanity: the HD loop bind is genuinely non-commutative at this D
    nc = float(np.dot(loop_bind_hd(oct_tok[0], oct_tok[1]),
                      loop_bind_hd(oct_tok[1], oct_tok[0])))
    a01 = loop_bind_hd(oct_tok[0], oct_tok[1])
    a10 = loop_bind_hd(oct_tok[1], oct_tok[0])
    cos_nc = nc / ((float(np.dot(a01, a01)) ** 0.5) * (float(np.dot(a10, a10)) ** 0.5))
    print(f"[non-commutativity] cos(tok0*tok1, tok1*tok0) = {cos_nc:+.3f} (<1 -> ordered)")
    # klein4 bundle order-invariance (the structural reason BAG conflates)
    inv = hdc.klein4_similarity(hdc.klein4_bundle(k4_tok[0], k4_tok[1]),
                                hdc.klein4_bundle(k4_tok[1], k4_tok[0]))
    print(f"[klein4 bag invariance] sim(bag(0,1), bag(1,0)) = {inv:+.3f} "
          f"(==1 -> order-blind, conflates)")

    def show(tag, res, expect_disc):
        print(f"  contexts={res['n_contexts']}  order-discriminating="
              f"{res['n_order_discriminating']}{expect_disc}")
        print(f"  LOOP-bind key   (octonion, ORDERED, F290 op) acc = {res['loop_acc']:.3f}")
        print(f"  KLEIN4-POSTAG   (klein4,   ORDER-AWARE ctrl)  acc = {res['postag_acc']:.3f}")
        print(f"  KLEIN4-BAG      (klein4,   order-blind R-75)  acc = {res['k4bag_acc']:.3f}")
        print(f"  OCT-BAG         (octonion, order-blind, lb)   acc = {res['octbag_acc']:.3f}")
        if res["k4bag_wrong_on_disc_total"]:
            print(f"  [swap-confusion] of {res['k4bag_wrong_on_disc_total']} KLEIN4-BAG errors on "
                  f"order-discriminating contexts (all seeds), {res['k4bag_swap_confusion_rate']*100:.0f}% "
                  f"emit the SWAPPED answer f(p1,p2) (chance ~{100.0/(V-1):.0f}%)")

    print("\n--- TASK-A (ORDER-DEPENDENT: next=f(prev2,prev1), f(x,y)!=f(y,x)) ---")
    rule_a = rule_table_order_dependent()
    res_a = run_task_avg(rule_a, pos0, pos1)
    show("A", res_a, "")

    print("\n--- TASK-B (ORDER-INDEPENDENT: next=g({prev2,prev1}), g(x,y)==g(y,x)) ---")
    rule_b = rule_table_order_blind()
    res_b = run_task_avg(rule_b, pos0, pos1)
    show("B", res_b, " (expect 0)")

    print("\n--- SUMMARY ---")
    print("  HEADLINE (F290/F288): octonion ORDERED loop-bind vs klein4 order-blind bag")
    print(f"    TASK-A  loop={res_a['loop_acc']:.3f}  k4-bag={res_a['k4bag_acc']:.3f}  "
          f"(loop-minus-bag={res_a['loop_acc']-res_a['k4bag_acc']:+.3f})")
    print(f"    TASK-B  loop={res_b['loop_acc']:.3f}  k4-bag={res_b['k4bag_acc']:.3f}  "
          f"(loop-minus-bag={res_b['loop_acc']-res_b['k4bag_acc']:+.3f})")
    print("  CLEAN ORDER-ISOLATION (same klein4 algebra): POSTAG (order-aware) vs BAG (order-blind)")
    a_iso = res_a["postag_acc"] - res_a["k4bag_acc"]
    b_iso = res_b["postag_acc"] - res_b["k4bag_acc"]
    print(f"    TASK-A  postag={res_a['postag_acc']:.3f}  bag={res_a['k4bag_acc']:.3f}  "
          f"(ORDER effect={a_iso:+.3f})")
    print(f"    TASK-B  postag={res_b['postag_acc']:.3f}  bag={res_b['k4bag_acc']:.3f}  "
          f"(ORDER effect={b_iso:+.3f})")

    a_head_beats = res_a["loop_acc"] > res_a["k4bag_acc"]
    a_order_beats = a_iso > 0.05          # clean: order-awareness helps when order informs
    # tie-check Class-K clean: squared deviation < threshold^2 (no abs() fold)
    b_order_ties = (b_iso * b_iso) < (0.05 * 0.05)  # order-awareness neutral when order is irrelevant
    print(f"\n  [VERDICT LOGIC]")
    print(f"  HEADLINE TASK-A loop BEATS klein4-bag: {a_head_beats}")
    print(f"  ISOLATED  TASK-A order-aware BEATS order-blind (same algebra): {a_order_beats}")
    print(f"  ISOLATED  TASK-B order-aware ~TIES order-blind (same algebra): {b_order_ties}")
    if a_head_beats and a_order_beats and b_order_ties:
        print("  VERDICT signal: POSITIVE — order memory improves NEXT-token emission exactly "
              "when order informs, neutral when it doesn't (algebra-confound controlled out).")
    elif a_head_beats and a_order_beats:
        print("  VERDICT signal: MIXED — order effect clearly present on A; TASK-B not a perfectly "
              "clean tie (capacity floor differs).")
    else:
        print("  VERDICT signal: NULL/MIXED — order-aware did NOT beat order-blind where order informs.")

    return {"consistency": consistent, "max_err": max_err,
            "task_a": res_a, "task_b": res_b}


if __name__ == "__main__":
    main()
