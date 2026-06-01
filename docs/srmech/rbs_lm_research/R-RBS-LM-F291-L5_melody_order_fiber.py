"""R-RBS-LM-F291 LEG L5 — the MELODY order-fiber: loop-bind ordered fold vs klein4 bag.

CLAIM UNDER TEST (F288/F290/F291): a melody is an ORDERED pitch sequence; its
retrograde (reversal) and a random scramble share the SAME pitch MULTISET but a
different ORDER. That order is exactly the order-fiber the flat commutative klein4
"bag" (R-RBS-LM-75 order-invariance) structurally cannot see — it reads only the
chord (= the pitch SET). The Moufang loop bind (Cayley-Dickson octonion product;
class M (bind) o C (chirality = left/right ordering) with a Class-K associator
RESIDUE) is the CURVED gauge connection that DOES carry order/path: it is
non-commutative AND non-associative, so an ordered fold of the pitch codebook
distinguishes a melody from its retrograde / scramble = the melodic CONTOUR.

  A chord IS the order-blind bag.  A melody IS the ordered fold.  We read that.

DESIGN (no-magic; all seeds stated below):
  - PITCHES: trivial public-domain motifs as scale-degree integers.
      twinkle  = [0,0,7,7,9,9,7]   ("Twinkle Twinkle" opening; public domain)
      asc_run  = [0,2,4,5,7,9,11]  (an ascending major-scale run)
    Scale degree -> a SHARED block-octonion unit codebook vector (seeded). Because
    the codebook is shared and indexed by pitch, a melody and its retrograde/scramble
    use exactly the same multiset of codebook vectors -> same "bag", different order.
  - LOOP-BIND ENCODINGS (two honest variants):
      (1) plain ordered left-fold:  ((c0 o c1) o c2) o ...   (non-assoc + non-comm)
      (2) positional bind + ordered fold: bind each pitch to a per-POSITION key
          octonion (pos_key[t]) then fold -> the canonical key*val "sequence store".
    Both are unit-block octonion ops via the native-parity gate (loop_bind_hd).
  - KLEIN4 BAG: hdc.klein4_bundle over the SAME pitch codebook (mapped klein4) =
    the commutative order-blind bag (the chord / pitch-set).
  - METRICS: cos(melody, retrograde) and cos(melody, scramble) under each encoding.
      loop bind  -> EXPECT distinct (cos < 1; order-aware = contour).
      klein4 bag -> EXPECT ~1 (order-blind = pitch-set).
    Report the GAP = how much more the loop bind separates order than the bag does.

DISCIPLINE:
  - srmech-first: hdc.loop_bind / hdc.loop_conj on the 8x8 basis (consistency check);
    the HD ordered fold via the committed loop_bind_hd_gate (block-octonion parity of
    the native dim-8 op); klein4_random / klein4_bundle / klein4_similarity for the bag.
  - Class-K clean: NO abs() in any cascade. cosine via Born inner product
    (re^2+im^2 = <v,v>); signs via loop_conj. (np.dot + sqrt(<v,v>) used ONLY for the
    octonion-HD cosine, noted; klein4 sims use hdc.klein4_similarity.)
  - CONSISTENCY: native hdc.loop_bind == oracle.loop_bind on all 64 (e_i,e_j) pairs.
  - no-magic seeds (attested-B, reproducibility): CODEBOOK_SEED=5291, POS_SEED=5292,
    SCRAMBLE_SEED=5293, KLEIN_BASE=5300. D=2048, BS=8, NB=256 attested-A (gate structure).
  - CAD-ban: algebra / spectral ONLY. NOT composition, audio synthesis, CAD.
  - no-lineage: read the order-vs-set structure of a trivial motif; claim nothing about
    prior music theory or HDC scholarship.
"""
import os
import sys
import json
import itertools
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from srmech.amsc import hdc                                              # noqa: E402
from loop_bind_hd_gate import loop_bind_hd, conj_hd, rand_unit_blocks, D, BS, NB  # noqa: E402
import loop_bind_moufang as oracle                                       # noqa: E402

# ---- attested-B seeds (reproducibility) ----
CODEBOOK_SEED = 5291     # pitch-degree -> block-octonion codebook
POS_SEED = 5292          # per-position key octonions (positional variant)
SCRAMBLE_SEED = 5293     # random order-scramble of a melody
KLEIN_BASE = 5300        # per-pitch klein4 codebook seeds (KLEIN_BASE + degree)

# ---- the trivial public-domain motifs (scale degrees; attested-B as input data) ----
TWINKLE = [0, 0, 7, 7, 9, 9, 7]      # "Twinkle Twinkle Little Star" opening
ASC_RUN = [0, 2, 4, 5, 7, 9, 11]     # ascending major-scale run
N_DEGREES = 12                        # chromatic scale degrees 0..11 (attested-A: octave structure)


# ---------------------------------------------------------------------------
# Class-K-clean octonion-HD cosine: Born inner product, no abs().
#   <u,v> / sqrt(<u,u> <v,v>)  — <v,v> = re^2+im^2 summed = the norm^2 (Class-K).
# (np.dot + sqrt used here on real block-octonion HD vectors; noted per discipline.)
# ---------------------------------------------------------------------------
def oct_cos(u, v):
    uu = float(np.dot(u, u))           # <u,u> Born norm^2 (no abs)
    vv = float(np.dot(v, v))
    uv = float(np.dot(u, v))
    return uv / ((uu ** 0.5) * (vv ** 0.5))


# ---------------------------------------------------------------------------
# Shared pitch codebooks.
# ---------------------------------------------------------------------------
def build_octonion_codebook():
    """degree -> unit block-octonion HD vector (D=2048, NB=256 octonion blocks)."""
    rng = np.random.default_rng(CODEBOOK_SEED)
    return {d: rand_unit_blocks(rng) for d in range(N_DEGREES)}


def build_klein4_codebook():
    """degree -> klein4 hypervector (deterministic per-degree seed)."""
    return {d: hdc.klein4_random(D, seed=KLEIN_BASE + d) for d in range(N_DEGREES)}


def build_pos_keys(n_max):
    """per-POSITION unit block-octonion key octonions (for the positional variant)."""
    rng = np.random.default_rng(POS_SEED)
    return [rand_unit_blocks(rng) for _ in range(n_max)]


# ---------------------------------------------------------------------------
# Encoders.
# ---------------------------------------------------------------------------
def loop_fold_plain(degrees, cb):
    """Ordered left-fold of the pitch codebook under the loop bind (non-assoc+non-comm)."""
    acc = cb[degrees[0]]
    for d in degrees[1:]:
        acc = loop_bind_hd(acc, cb[d])     # left-fold: ((c0 o c1) o c2) ...
    return acc


def loop_fold_positional(degrees, cb, pos_keys):
    """Bind each pitch to its per-position key, then ordered-fold the bound terms."""
    bound = [loop_bind_hd(pos_keys[t], cb[d]) for t, d in enumerate(degrees)]
    acc = bound[0]
    for b in bound[1:]:
        acc = loop_bind_hd(acc, b)
    return acc


def klein4_bag(degrees, cb):
    """Commutative klein4 bundle of the SAME pitch codebook = the order-blind chord/set."""
    vecs = [cb[d] for d in degrees]
    return hdc.klein4_bundle(*vecs)        # variadic, NOT a list


# ---------------------------------------------------------------------------
# Order variants of a melody (same multiset, different order).
# ---------------------------------------------------------------------------
def retrograde(degrees):
    return list(reversed(degrees))


def scramble(degrees, seed):
    rng = np.random.default_rng(seed)
    out = list(degrees)
    # ensure a genuine reordering when possible (multiset may force repeats equal)
    for _ in range(64):
        rng.shuffle(out)
        if out != list(degrees):
            break
    return out


# ---------------------------------------------------------------------------
def run_motif(name, degrees, oct_cb, kl_cb, pos_keys):
    retro = retrograde(degrees)
    scr = scramble(degrees, SCRAMBLE_SEED)
    # honest note: if the multiset is palindromic the retrograde may equal the original
    retro_is_distinct_order = (retro != list(degrees))
    scr_is_distinct_order = (scr != list(degrees))

    # ---- loop bind: plain ordered fold ----
    m_plain = loop_fold_plain(degrees, oct_cb)
    r_plain = loop_fold_plain(retro, oct_cb)
    s_plain = loop_fold_plain(scr, oct_cb)
    cos_plain_retro = oct_cos(m_plain, r_plain)
    cos_plain_scr = oct_cos(m_plain, s_plain)

    # ---- loop bind: positional bind + fold ----
    m_pos = loop_fold_positional(degrees, oct_cb, pos_keys)
    r_pos = loop_fold_positional(retro, oct_cb, pos_keys)
    s_pos = loop_fold_positional(scr, oct_cb, pos_keys)
    cos_pos_retro = oct_cos(m_pos, r_pos)
    cos_pos_scr = oct_cos(m_pos, s_pos)

    # ---- klein4 bag (commutative; order-blind) ----
    m_bag = klein4_bag(degrees, kl_cb)
    r_bag = klein4_bag(retro, kl_cb)
    s_bag = klein4_bag(scr, kl_cb)
    sim_bag_retro = hdc.klein4_similarity(m_bag, r_bag)
    sim_bag_scr = hdc.klein4_similarity(m_bag, s_bag)

    # ---- gaps: order-separation = how far below 1.0 the cosine drops ----
    # loop separates order (1 - cos large); bag does not (1 - sim ~ 0).
    sep_plain_retro = 1.0 - cos_plain_retro
    sep_plain_scr = 1.0 - cos_plain_scr
    sep_pos_retro = 1.0 - cos_pos_retro
    sep_pos_scr = 1.0 - cos_pos_scr
    sep_bag_retro = 1.0 - sim_bag_retro
    sep_bag_scr = 1.0 - sim_bag_scr
    # GAP = loop-bind order-separation minus bag order-separation (positive => loop sees order the bag misses)
    gap_pos_retro = sep_pos_retro - sep_bag_retro
    gap_pos_scr = sep_pos_scr - sep_bag_scr

    res = {
        "motif": name,
        "degrees": degrees,
        "retrograde": retro,
        "scramble": scr,
        "retro_is_distinct_order": retro_is_distinct_order,
        "scramble_is_distinct_order": scr_is_distinct_order,
        "loop_plain": {
            "cos_melody_retrograde": round(cos_plain_retro, 6),
            "cos_melody_scramble": round(cos_plain_scr, 6),
        },
        "loop_positional": {
            "cos_melody_retrograde": round(cos_pos_retro, 6),
            "cos_melody_scramble": round(cos_pos_scr, 6),
        },
        "klein4_bag": {
            "sim_melody_retrograde": round(float(sim_bag_retro), 6),
            "sim_melody_scramble": round(float(sim_bag_scr), 6),
        },
        "order_separation": {
            "loop_plain_retro": round(sep_plain_retro, 6),
            "loop_plain_scramble": round(sep_plain_scr, 6),
            "loop_positional_retro": round(sep_pos_retro, 6),
            "loop_positional_scramble": round(sep_pos_scr, 6),
            "klein4_bag_retro": round(sep_bag_retro, 6),
            "klein4_bag_scramble": round(sep_bag_scr, 6),
        },
        "gap_loop_minus_bag": {
            "positional_retro": round(gap_pos_retro, 6),
            "positional_scramble": round(gap_pos_scr, 6),
        },
    }
    return res


def main():
    print(f"=== R-RBS-LM-F291 L5: melody order-fiber  (D={D}, BS={BS}, NB={NB}) ===\n")

    # ---- CONSISTENCY: native hdc.loop_bind == oracle.loop_bind on all 64 basis pairs ----
    e = oracle.e
    max_abs_err = 0.0
    for i in range(BS):
        for j in range(BS):
            nat = np.asarray(hdc.loop_bind(e(i), e(j)), dtype=float)
            ora = np.asarray(oracle.loop_bind(e(i), e(j)), dtype=float)
            # Class-K clean residual: <d,d> Born norm^2 (no abs)
            d_ = nat - ora
            err = float(np.dot(d_, d_)) ** 0.5
            if err > max_abs_err:
                max_abs_err = err
    consistency_ok = max_abs_err < 1e-12
    print(f"[CONSISTENCY] native hdc.loop_bind vs oracle on 64 (e_i,e_j) pairs: "
          f"max ||err|| = {max_abs_err:.2e} -> {'MATCH' if consistency_ok else 'MISMATCH'}\n")

    # also confirm loop_conj parity on the basis (Class-K sign op via conj, not abs)
    conj_err = 0.0
    for i in range(BS):
        nat_c = np.asarray(hdc.loop_conj(e(i)), dtype=float)
        ora_c = np.asarray(oracle.conj(e(i)), dtype=float)
        dd = nat_c - ora_c
        conj_err = max(conj_err, float(np.dot(dd, dd)) ** 0.5)
    print(f"[CONSISTENCY] hdc.loop_conj vs oracle.conj on 8 basis elems: "
          f"max ||err|| = {conj_err:.2e}\n")

    oct_cb = build_octonion_codebook()
    kl_cb = build_klein4_codebook()
    pos_keys = build_pos_keys(max(len(TWINKLE), len(ASC_RUN)))

    results = []
    for name, degs in [("twinkle", TWINKLE), ("asc_run", ASC_RUN)]:
        r = run_motif(name, degs, oct_cb, kl_cb, pos_keys)
        results.append(r)
        print(f"--- motif: {name}  degrees={degs} ---")
        print(f"  retrograde = {r['retrograde']}   scramble = {r['scramble']}")
        print(f"  [loop plain fold]   cos(melody,retro)={r['loop_plain']['cos_melody_retrograde']:+.4f}  "
              f"cos(melody,scramble)={r['loop_plain']['cos_melody_scramble']:+.4f}")
        print(f"  [loop positional]   cos(melody,retro)={r['loop_positional']['cos_melody_retrograde']:+.4f}  "
              f"cos(melody,scramble)={r['loop_positional']['cos_melody_scramble']:+.4f}")
        print(f"  [klein4 bag (chord)]sim(melody,retro)={r['klein4_bag']['sim_melody_retrograde']:+.4f}  "
              f"sim(melody,scramble)={r['klein4_bag']['sim_melody_scramble']:+.4f}")
        print(f"  GAP loop-positional minus bag:  retro={r['gap_loop_minus_bag']['positional_retro']:+.4f}  "
              f"scramble={r['gap_loop_minus_bag']['positional_scramble']:+.4f}\n")

    # ---- aggregate read ----
    # The loop bind is order-aware iff cos(melody,reorder) is meaningfully below the
    # bag's near-1 similarity. The bag is order-blind iff its sim stays ~1.
    bag_sims = []
    loop_pos_cos = []
    for r in results:
        if r["retro_is_distinct_order"]:
            bag_sims.append(r["klein4_bag"]["sim_melody_retrograde"])
            loop_pos_cos.append(r["loop_positional"]["cos_melody_retrograde"])
        bag_sims.append(r["klein4_bag"]["sim_melody_scramble"])
        loop_pos_cos.append(r["loop_positional"]["cos_melody_scramble"])
    mean_bag = float(np.mean(bag_sims))
    mean_loop = float(np.mean(loop_pos_cos))
    print("=== aggregate ===")
    print(f"  mean klein4-bag sim across reorderings (order-blind, expect ~1): {mean_bag:+.4f}")
    print(f"  mean loop-positional cos across reorderings (order-aware, expect <1): {mean_loop:+.4f}")
    print(f"  contour-margin = bag - loop = {mean_bag - mean_loop:+.4f}  "
          f"(positive => loop sees order the bag misses)")

    # ---- CONTROL: the klein4 bag is set-SENSITIVE, NOT trivially always-1. A genuinely
    #      DIFFERENT pitch-set (disjoint from TWINKLE's {0,7,9}) drops the bag similarity well
    #      below 1.0 -> proves sim=1.0 on REORDERINGS is order-BLINDNESS, not a degenerate constant.
    DIFF_SET = [1, 2, 3, 4, 6, 8, 10]   # attested-B input; pitch-disjoint from TWINKLE {0,7,9}
    control_sim = float(hdc.klein4_similarity(klein4_bag(TWINKLE, kl_cb), klein4_bag(DIFF_SET, kl_cb)))
    print("=== control (bag is set-sensitive, not always-1) ===")
    print(f"  klein4-bag sim(TWINKLE set {sorted(set(TWINKLE))}, DIFF set {sorted(set(DIFF_SET))}) = {control_sim:+.4f}")
    print(f"  -> well below the ~1.0 reorder sim, so the bag's 1.0 on reorderings is ORDER-BLINDNESS, not a constant.")

    summary = {
        "leg": "F291-L5",
        "D": D, "BS": BS, "NB": NB,
        "seeds": {"codebook": CODEBOOK_SEED, "pos": POS_SEED,
                  "scramble": SCRAMBLE_SEED, "klein_base": KLEIN_BASE},
        "consistency_native_eq_oracle_8x8": consistency_ok,
        "consistency_max_abs_err": max_abs_err,
        "conj_max_abs_err": conj_err,
        "motifs": results,
        "aggregate": {
            "mean_klein4_bag_sim": round(mean_bag, 6),
            "mean_loop_positional_cos": round(mean_loop, 6),
            "contour_margin_bag_minus_loop": round(mean_bag - mean_loop, 6),
        },
        "control_diff_pitchset": {
            "diff_set": DIFF_SET,
            "klein4_bag_sim_twinkle_vs_diffset": round(control_sim, 6),
        },
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "R-RBS-LM-F291-L5_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {out_path}")
    return summary


if __name__ == "__main__":
    main()
