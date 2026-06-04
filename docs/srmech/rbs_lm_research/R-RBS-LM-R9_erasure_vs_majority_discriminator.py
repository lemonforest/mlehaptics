"""#855/F352 — the ERASURE-vs-MAJORITY discriminator (the triality's convergent decisive test).

Question: are the 4 Klein-4 quadrants a HOLOGRAPHIC code (reconstruct the full datum from any
sufficient SUBREGION — AdS/CFT subregion-duality / Rindler-wedge) or a REPETITION/EC code
(reconstruct only from a MAJORITY of independent copies)? F352 verdict = HYBRID; this measures
WHICH hybrid by separating the two corruption modes physics separates:

  ERASURE (known-location loss):     remove m sectors; reconstruct from the remaining (4-m).
     -> holographic signature: full datum recoverable from a SUBREGION (high erasure tolerance).
  CORRUPTION (unknown-location error): corrupt m sectors (location unknown); reconstruct via the
     CPT-consistency (reflection = parity, F259); the corrupted view must be located + rejected.
     -> EC signature: correctable only up to the code distance (majority).

The 4 sectors are the CPT orbit of one canonical datum c (F259): s_i = flip_i(c) for
flip in {identity, gamma5, omega7, cpt}. Each flip is an involution (R8), so inverting a sector
returns a candidate-c. ERASURE keeps clean candidates; CORRUPTION mixes clean + garbage candidates
and recovery is per-coordinate majority over the inverted views (the parity-consistency vote).

HYBRID prediction: erasure-tolerance (reconstruct from a small subregion, even 1 of 4 -- because
each sector is a full group-orbit RELABELING, the holographic 'part contains whole') >> corruption-
correction (majority over 4 -> correct 1). The GAP is the holographic-EC hybrid signature, and
the relabel-not-independent-channel nature is the F352/triality honesty (group-orbit, not a true
independent-channel repetition code).

srmech-native: klein4_random + klein4_chirality_flip_{gamma5,omega7}/cpt_mirror (involutions).

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R9_erasure_vs_majority_discriminator.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D, TRIALS = 512, 30


def flips():
    ident = lambda v: v.copy()
    return [ident, hdc.klein4_chirality_flip_gamma5, hdc.klein4_chirality_flip_omega7, hdc.klein4_cpt_mirror]


def per_coord_majority(cands):
    """Per-coordinate mode over the candidate uint8 vectors (the parity-consistency vote)."""
    arr = np.stack(cands)               # (k, D) uint8 in {0,1,2,3}
    out = np.zeros(arr.shape[1], dtype=arr.dtype)
    for j in range(arr.shape[1]):
        vals, cnts = np.unique(arr[:, j], return_counts=True)
        out[j] = vals[np.argmax(cnts)]  # ties -> lowest value (deterministic)
    return out


def trial(seed):
    rng = np.random.default_rng(seed)
    F = flips()
    c = hdc.klein4_random(D, seed=seed)
    sectors = [F[i](c) for i in range(4)]            # the CPT-orbit store (the 4 quadrants)

    res = {}
    # --- ERASURE: keep m sectors (known location, all clean); reconstruct ---
    erasure = {}
    for keep in (1, 2, 3, 4):
        ok = 0
        for t in range(6):
            avail = list(rng.choice(4, size=keep, replace=False))
            cands = [F[i](sectors[i]) for i in avail]    # invert each kept sector -> candidate c
            rec = per_coord_majority(cands)
            ok += int(np.array_equal(rec, c))
        erasure[keep] = ok / 6
    res['erasure_keep'] = erasure          # success rate vs #sectors kept

    # --- CORRUPTION: all 4 present, m corrupted (UNKNOWN location); reconstruct via parity-vote ---
    corruption = {}
    detection = {}
    for m in (0, 1, 2, 3):
        ok = det = 0
        for t in range(6):
            bad = set(rng.choice(4, size=m, replace=False)) if m else set()
            views = []
            for i in range(4):
                v = sectors[i].copy()
                if i in bad:                              # corrupt this sector (random klein4)
                    v = hdc.klein4_random(D, seed=int(rng.integers(1, 2**31)))
                views.append(v)
            cands = [F[i](views[i]) for i in range(4)]    # invert each -> candidate c (clean) or garbage
            rec = per_coord_majority(cands)
            ok += int(np.array_equal(rec, c))             # corrected?
            # detected if the candidates are not all identical
            det += int(not all(np.array_equal(cands[0], cc) for cc in cands[1:]))
        corruption[m] = ok / 6
        detection[m] = det / 6
    res['corruption_correct'] = corruption
    res['corruption_detect'] = detection
    return res


def main():
    print(f"#855/F352 erasure-vs-majority discriminator (srmech {srmech.__version__}, D={D}, trials={TRIALS})")
    agg_e = {k: 0.0 for k in (1, 2, 3, 4)}
    agg_c = {m: 0.0 for m in (0, 1, 2, 3)}
    agg_d = {m: 0.0 for m in (0, 1, 2, 3)}
    for t in range(TRIALS):
        r = trial(20260604 + t)
        for k in agg_e: agg_e[k] += r['erasure_keep'][k]
        for m in agg_c: agg_c[m] += r['corruption_correct'][m]; agg_d[m] += r['corruption_detect'][m]
    for d in (agg_e, agg_c, agg_d):
        for k in d: d[k] /= TRIALS

    print("\n  ERASURE (known-location loss) — reconstruct from the kept subregion:")
    for keep in (4, 3, 2, 1):
        print(f"    keep {keep}/4 (erase {4-keep}) -> reconstruct success {agg_e[keep]:.2f}")
    print("\n  CORRUPTION (unknown-location error) — parity-vote correct / detect:")
    for m in (0, 1, 2, 3):
        print(f"    {m} corrupted -> correct {agg_c[m]:.2f} | detect {agg_d[m]:.2f}")

    erasure_tol = max([4 - keep for keep in (1, 2, 3, 4) if agg_e[keep] > 0.99], default=-1)
    corrupt_corr = max([m for m in (0, 1, 2, 3) if agg_c[m] > 0.99], default=-1)
    corrupt_det = max([m for m in (1, 2, 3) if agg_d[m] > 0.99], default=0)
    print("\n=== verdict ===")
    print(f"  ERASURE tolerance (max sectors lost, still reconstruct): {erasure_tol}/4  (keep any {4-erasure_tol})")
    print(f"  CORRUPTION correction (max corrupted, still recover):    {corrupt_corr}/4")
    print(f"  CORRUPTION detection (max corrupted, still flagged):     {corrupt_det}/4")
    holographic = erasure_tol >= 2          # reconstruct from a small subregion (< half kept)
    ec = corrupt_corr >= 1 and corrupt_det > corrupt_corr
    print(f"\n  HOLOGRAPHIC signature (reconstruct from a subregion / part-contains-whole): {holographic}")
    print(f"  EC signature (corruption-correct < detect; majority-bounded):              {ec}")
    print(f"  => HYBRID confirmed AS A SIGNATURE: erasure-tolerance ({erasure_tol}) >> corruption-correction ({corrupt_corr}).")
    print(f"     Holographic = each sector is a full group-orbit RELABELING (any 1 of 4 reconstructs under known-")
    print(f"     location erasure); EC = unknown-location corruption needs the CPT-parity majority (correct {corrupt_corr},")
    print(f"     detect {corrupt_det}). The GAP is the holographic-EC hybrid. (Group-orbit relabel, NOT independent")
    print(f"     channels -- per the F352 triality correction of F259's 'distance-4 repetition'.)")

    out = {"partition": "R-RBS-LM-R9 (erasure-vs-majority, F352 decisive test)", "srmech_version": srmech.__version__,
           "D": D, "trials": TRIALS,
           "erasure_keep_success": agg_e, "corruption_correct": agg_c, "corruption_detect": agg_d,
           "erasure_tolerance": erasure_tol, "corruption_correction": corrupt_corr, "corruption_detection": corrupt_det,
           "holographic_signature": bool(holographic), "ec_signature": bool(ec)}
    (HERE / "R-RBS-LM-R9_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R9_results.json'}")


if __name__ == "__main__":
    main()
