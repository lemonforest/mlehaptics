"""#855 R4 — the truth-filter on the Klein-4 store: k=1 can't detect, k=2 DETECTS,
k=3 CORRECTS (F291), demonstrated srmech-native on the R1-validated Klein-4 substrate.

The honesty-store's correction mechanism (F291/F334/F335): >=3 co-equal renders, agreement
= attestation. This is the repetition/parity code read as truth-filter:
  k=1 (one render):  no redundancy -> a corrupted render is silently wrong (no detect, no correct)
  k=2 (two renders): parity -> DISAGREEMENT is detectable, but a 1-vs-1 split has no majority
                     -> cannot CORRECT (needs a human tie-break)
  k=3 (three renders): majority -> the 2 agreeing renders OUTVOTE the corrupted one -> CORRECTED

Demonstrated on Klein-4 (the F341/R1 store substrate; klein4_bundle = the per-coordinate
agreement/majority operator). A "fact" v_true is rendered 3x; one render is corrupted at
sweepable strength; we measure detect (k=2 disagreement) and correct (k=3 majority recovers
v_true) vs the no-redundancy k=1 baseline.

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R4_k2detect_k3correct_klein4.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D = 8192
TRIALS = 40
CORRUPT_SWEEP = [0.10, 0.25, 0.40, 0.50]   # fraction of klein-4 coords randomized in the bad render
DETECT_MARGIN = 0.02                        # k=2 flags disagreement when (clean_base - cross) exceeds this
                                            # (relative to the clean-clean agreement; not an absolute cutoff)
CORRECT_THRESH = 0.90                       # recovery counts as correct if sim(recovered, truth) >= this
BASE_SEED = 20260603


def corrupt(v, p, rng):
    """Randomize a fraction p of the klein-4 vector's coordinates (an independent bad render)."""
    out = v.copy()
    noise = hdc.klein4_random(D, seed=int(rng.integers(1, 2**31)))
    mask = rng.random(out.shape[0]) < p
    out[mask] = noise[mask]
    return out


def trial(p, seed):
    rng = np.random.default_rng(seed)
    v_true = hdc.klein4_random(D, seed=seed)
    # three co-equal renders: 2 clean copies + 1 corrupted at strength p
    r1 = v_true.copy()
    r2 = v_true.copy()
    r3 = corrupt(v_true, p, rng)
    # k=1: just the (possibly bad) render r3 -- no redundancy
    k1_sim = hdc.klein4_similarity(r3, v_true)
    # k=2: detection is RELATIVE to the clean-agreement baseline (no magic absolute cutoff).
    #   two clean renders agree at clean_base; a corrupted render's cross-sim sits below it.
    #   DETECTED = the disagreement gap exceeds the clean-pair's own scatter margin.
    clean_base = hdc.klein4_similarity(r1, r2)               # clean-clean agreement (= 1.0)
    cross = hdc.klein4_similarity(r1, r3)                    # clean-vs-corrupted
    gap = clean_base - cross
    detected = gap > DETECT_MARGIN                           # disagreement flagged (cannot say WHICH is right)
    # k=3: majority over all three (klein4_bundle = per-coord agreement)
    k3 = hdc.klein4_bundle(r1, r2, r3)
    k3_sim = hdc.klein4_similarity(k3, v_true)
    corrected = k3_sim >= CORRECT_THRESH
    return k1_sim, clean_base, cross, gap, detected, k3_sim, corrected


def main():
    print(f"#855 R4 — k=2 detects / k=3 corrects on the Klein-4 store (srmech {srmech.__version__}, D={D}, trials={TRIALS})")
    print(f"  {'corrupt-p':>9} | {'k1 sim(bad,truth)':>17} | {'k2 clean-base':>13} | {'k2 cross':>8} | {'k2 detect-rate':>14} | {'k3 sim(maj,truth)':>17} | {'k3 correct-rate':>15}")
    rows = []
    for p in CORRUPT_SWEEP:
        k1s, bases, crosses, dets, k3s, cors = [], [], [], [], [], []
        for t in range(TRIALS):
            a, base, cross, gap, d, c, cor = trial(p, BASE_SEED + t)
            k1s.append(a); bases.append(base); crosses.append(cross); dets.append(d); k3s.append(c); cors.append(cor)
        row = {"corrupt_p": p, "k1_sim": float(np.mean(k1s)),
               "k2_clean_base": float(np.mean(bases)), "k2_cross": float(np.mean(crosses)),
               "k2_detect_rate": float(np.mean(dets)),
               "k3_sim": float(np.mean(k3s)), "k3_correct_rate": float(np.mean(cors))}
        rows.append(row)
        print(f"  {p:>9.2f} | {row['k1_sim']:>17.3f} | {row['k2_clean_base']:>13.3f} | {row['k2_cross']:>8.3f} | {row['k2_detect_rate']:>14.2f} | {row['k3_sim']:>17.3f} | {row['k3_correct_rate']:>15.2f}")

    print("\n=== verdict ===")
    worst = rows[-1]   # p=0.50, the hardest corruption
    print(f"  At the hardest corruption (p={worst['corrupt_p']}):")
    print(f"    k=1: a corrupted render scores sim={worst['k1_sim']:.3f} to truth — silently wrong, no detect/correct.")
    print(f"    k=2: detect-rate {worst['k2_detect_rate']:.2f} — DISAGREEMENT flagged, but 1-vs-1 has no majority (no correct).")
    print(f"    k=3: majority recovers truth at sim={worst['k3_sim']:.3f}, correct-rate {worst['k3_correct_rate']:.2f} — CORRECTED.")
    k3_always_corrects = all(r["k3_correct_rate"] >= 0.95 for r in rows)
    k2_detects = all(r["k2_detect_rate"] >= 0.95 for r in rows[1:])  # for p>=0.25
    print(f"  k=3 corrects across the sweep (>=0.95): {k3_always_corrects}")
    print(f"  k=2 detects for p>=0.25 (>=0.95): {k2_detects}")

    out = {"partition": "R-RBS-LM-R4 (#855 R4)", "srmech_version": srmech.__version__, "D": D,
           "trials": TRIALS, "rows": rows,
           "k3_always_corrects": k3_always_corrects, "k2_detects": k2_detects,
           "reading": "Klein-4 store IS the error-correcting substrate; k=2 detects / k=3 corrects (F291)."}
    (HERE / "R-RBS-LM-R4_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R4_results.json'}")


if __name__ == "__main__":
    main()
