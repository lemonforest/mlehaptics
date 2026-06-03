"""#855 R1 / #812 — Loop-bind store capacity vs Klein-4 baseline.

The load-bearing question for the Klein-4-native instrument (F200/F158): does
the **non-associative octonionic loop-bind** cost capacity relative to the
**associative+commutative Klein-4 (Z2xZ2) XOR bind**, and does loop-bind NEED
cleanup memory (a codebook) to retrieve at all?

Associative-memory capacity test (closed-set), srmech-native on rc25:
  * store S = bundle/superpose K bound (key,value) pairs
  * recover each value v_i = unbind(key_i, S)
  * RAW fidelity   = similarity(v_i_hat, val_i)        (no cleanup)
  * CLEANUP acc    = nearest of the K stored values == val_i  (codebook NN)
  * sweep K; capacity = max K with cleanup-accuracy >= 0.90

Klein-4:  klein4_random / klein4_bind / klein4_bundle / klein4_unbind / klein4_similarity
Loop:     unit-octonion-block float vectors / loop_bind_hd / real superposition (np.sum --
          srmech ships NO loop bundle) / loop_unbind_hd / hdc.similarity

Recovery conventions (verified rc25 1-pair smoke): klein4_unbind(S,key) exact (1.0);
loop_unbind_hd(key,S) best (1-pair 0.9468 -- loop unbind is already LOSSY at K=1).

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R1_klein4_vs_loopbind_capacity.py
"""

import json
from pathlib import Path
import numpy as np

import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D = 8192                      # 1024 octonion blocks of 8
K_SWEEP = [2, 4, 8, 16, 32, 64, 128, 192]
TRIALS = 5
THRESHOLD = 0.90
BASE_SEED = 20260603


def unit_octonion_blocks(D, rng):
    """Random vector whose every 8-coordinate block is a UNIT octonion
    (loop_inv/unbind == conj on unit blocks; per UPSTREAM_NOTES §12.4)."""
    v = rng.standard_normal(D).reshape(-1, 8)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v.reshape(-1)


def run_klein4(K, seed):
    rng_seed = seed
    keys = [hdc.klein4_random(D, seed=rng_seed + i) for i in range(K)]
    vals = [hdc.klein4_random(D, seed=rng_seed + 10_000 + i) for i in range(K)]
    bound = [hdc.klein4_bind(keys[i], vals[i]) for i in range(K)]
    S = hdc.klein4_bundle(*bound)
    raw, correct = [], 0
    for i in range(K):
        rec = hdc.klein4_unbind(S, keys[i])
        raw.append(hdc.klein4_similarity(rec, vals[i]))
        sims = [hdc.klein4_similarity(rec, vals[j]) for j in range(K)]
        if int(np.argmax(sims)) == i:
            correct += 1
    return correct / K, float(np.mean(raw))


def run_loop(K, seed):
    rng = np.random.default_rng(seed)
    keys = [unit_octonion_blocks(D, rng) for _ in range(K)]
    vals = [unit_octonion_blocks(D, rng) for _ in range(K)]
    bound = [hdc.loop_bind_hd(keys[i], vals[i]) for i in range(K)]
    S = np.sum(bound, axis=0)            # real-vector superposition (no srmech loop bundle)
    raw, correct = [], 0
    for i in range(K):
        rec = hdc.loop_unbind_hd(keys[i], S)
        raw.append(hdc.similarity(rec, vals[i]))
        sims = [hdc.similarity(rec, vals[j]) for j in range(K)]
        if int(np.argmax(sims)) == i:
            correct += 1
    return correct / K, float(np.mean(raw))


def sweep(runner, label):
    print(f"\n=== {label} ===")
    print(f"  {'K':>4} | {'cleanup-acc':>11} | {'raw-sim':>8}")
    rows = []
    for K in K_SWEEP:
        accs, raws = [], []
        for t in range(TRIALS):
            a, r = runner(K, BASE_SEED + 1000 * t)
            accs.append(a); raws.append(r)
        ma, sa = float(np.mean(accs)), float(np.std(accs))
        mr = float(np.mean(raws))
        rows.append({"K": K, "cleanup_acc": ma, "cleanup_std": sa, "raw_sim": mr})
        print(f"  {K:>4} | {ma:>10.3f}±{sa:4.2f} | {mr:>8.4f}")
    cap = max([r["K"] for r in rows if r["cleanup_acc"] >= THRESHOLD], default=0)
    raw_cap = max([r["K"] for r in rows if r["raw_sim"] >= 0.10], default=0)
    print(f"  capacity (cleanup-acc>={THRESHOLD}): K={cap}   | raw-sim>=0.10 holds to K={raw_cap}")
    return {"rows": rows, "capacity_cleanup": cap, "raw_floor_K": raw_cap}


def main():
    print(f"#855 R1 / #812 — loop-bind vs Klein-4 capacity (srmech {srmech.__version__}, D={D}, trials={TRIALS})")
    k4 = sweep(run_klein4, "Klein-4 (Z2xZ2 XOR bind; associative+commutative)")
    lp = sweep(run_loop, "Loop-bind (octonionic Moufang; NON-associative)")

    print("\n=== verdict ===")
    print(f"  Klein-4 capacity (cleanup): K={k4['capacity_cleanup']}   raw-floor K={k4['raw_floor_K']}")
    print(f"  Loop-bind capacity (cleanup): K={lp['capacity_cleanup']}   raw-floor K={lp['raw_floor_K']}")
    needs_cleanup_loop = lp["rows"][0]["raw_sim"] < 0.99
    needs_cleanup_k4 = k4["rows"][0]["raw_sim"] < 0.99
    print(f"  loop NEEDS cleanup (raw K=2 sim {lp['rows'][0]['raw_sim']:.3f} < 0.99): {needs_cleanup_loop}")
    print(f"  klein4 NEEDS cleanup (raw K=2 sim {k4['rows'][0]['raw_sim']:.3f} < 0.99): {needs_cleanup_k4}")

    out = {
        "partition": "R-RBS-LM-R1 (#855 R1 / #812)", "srmech_version": srmech.__version__,
        "D": D, "trials": TRIALS, "threshold": THRESHOLD,
        "klein4": k4, "loop": lp,
        "loop_needs_cleanup": needs_cleanup_loop, "klein4_needs_cleanup": needs_cleanup_k4,
        "note": "srmech ships klein4_bundle but NO loop bundle; loop uses np real superposition.",
    }
    (HERE / "R-RBS-LM-R1_capacity_results.json").write_text(json.dumps(out, indent=2))
    print(f"\nResults: {HERE / 'R-RBS-LM-R1_capacity_results.json'}")


if __name__ == "__main__":
    main()
