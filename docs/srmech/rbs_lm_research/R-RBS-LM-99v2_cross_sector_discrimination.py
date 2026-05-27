"""R-RBS-LM-99v2 — Cross-sector DISCRIMINATION test (refined falsification)

Path 3/6 refined. Previous v1 found same-sector and cross-sector sims
IDENTICAL — a structural consequence of Klein-4 being abelian. That's
a "trivially-works" outcome, not a falsifiable discrimination.

This v2 asks the right falsification question:

  When we query with a DIFFERENT sector than the one used to encode,
  do we recover the CHIRALITY-FLIPPED version of the concept (per F132
  prediction), and NOT the original concept (which would mean the
  chirality axis was decorative)?

Procedure per encoded concept C with sector A:
  query_same    = unbind(composite, A)         -> compare to C            (target = C)
  query_cross   = unbind(composite, A XOR 3)   -> compare to C            (target = C, predicted LOW)
  query_cross   = unbind(composite, A XOR 3)   -> compare to C XOR 3      (target = C_mirror, predicted HIGH)
  random vec    -> compare to C                                            (baseline)

Predictions (F132 chirality-axis operational):
  same-to-C            >>  random            (above-random retrieval works)
  cross-to-C           ≈   random            (cross-sector query does NOT match original)
  cross-to-C_mirror    >>  random            (cross-sector query DOES match the flipped concept)
  cross-to-C_mirror    ≈   same-to-C         (retrieval quality is symmetric across sectors)

If cross-to-C ≈ same-to-C, then the chirality axis is DECORATIVE (anything
unbinds anything).

If cross-to-C ≈ random AND cross-to-C_mirror ≈ same-to-C, then chirality
axis IS operational and (importantly) DISCRIMINATIVE.

This is the load-bearing F132 §7 test.
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


SECTOR_CPT_MIRROR = {0: 3, 1: 2, 2: 1, 3: 0}  # XOR with 3 = full CPT flip


def encode_concept(concept_seed: int, D: int) -> np.ndarray:
    rng = np.random.default_rng(concept_seed)
    return hdc.klein4_random(D, rng)


def apply_sector(hv: np.ndarray, sector: int) -> np.ndarray:
    D = len(hv)
    return hdc.klein4_bind(hv, np.full(D, sector, dtype=np.uint8))


def random_baseline_klein4(D: int, N_trials: int, rng) -> float:
    sims = []
    for _ in range(N_trials):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        sims.append(float(hdc.klein4_similarity(a, b)))
    return float(np.mean(sims))


def run_discrimination_test(D: int, N_concepts: int, rng):
    """The refined falsification test."""
    concepts = [encode_concept(i, D) for i in range(N_concepts)]
    sectors = [i % 4 for i in range(N_concepts)]

    tagged = [apply_sector(c, s) for c, s in zip(concepts, sectors)]
    composite = hdc.klein4_bundle(*tagged)

    same_to_C, cross_to_C, cross_to_Cmirror = [], [], []
    random_to_C = []

    for i, c in enumerate(concepts):
        own_sector = sectors[i]
        cpt_sector = SECTOR_CPT_MIRROR[own_sector]
        c_mirror = apply_sector(c, 3)

        # Same-sector unbind
        same_unbound = hdc.klein4_unbind(
            composite, np.full(D, own_sector, dtype=np.uint8)
        )
        same_to_C.append(float(hdc.klein4_similarity(same_unbound, c)))

        # Cross-sector unbind (CPT-mirror sector)
        cross_unbound = hdc.klein4_unbind(
            composite, np.full(D, cpt_sector, dtype=np.uint8)
        )
        cross_to_C.append(float(hdc.klein4_similarity(cross_unbound, c)))
        cross_to_Cmirror.append(float(hdc.klein4_similarity(cross_unbound, c_mirror)))

        # Random baseline: compare a fresh random vector to c
        random_vec = hdc.klein4_random(D, rng)
        random_to_C.append(float(hdc.klein4_similarity(random_vec, c)))

    return {
        "same_to_C": (float(np.mean(same_to_C)), float(np.std(same_to_C))),
        "cross_to_C": (float(np.mean(cross_to_C)), float(np.std(cross_to_C))),
        "cross_to_Cmirror": (float(np.mean(cross_to_Cmirror)), float(np.std(cross_to_Cmirror))),
        "random_to_C": (float(np.mean(random_to_C)), float(np.std(random_to_C))),
    }


def main():
    rng = np.random.default_rng(42)
    configs = [(1024, 8), (1024, 32), (4096, 8), (4096, 32), (16384, 8), (16384, 32)]

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print()
    print(f"{'D':>6} | {'N':>4} | {'same->C':>14} | {'cross->C':>14} | {'cross->C_mirror':>16} | {'random->C':>14}")
    print("-" * 100)

    results = []
    for D, N in configs:
        t0 = time.time()
        res = run_discrimination_test(D, N, rng)
        elapsed = time.time() - t0

        sc, sc_std = res["same_to_C"]
        cc, cc_std = res["cross_to_C"]
        cm, cm_std = res["cross_to_Cmirror"]
        rc, rc_std = res["random_to_C"]

        print(
            f"{D:>6} | {N:>4} | "
            f"{sc:>+0.4f} ± {sc_std:.3f} | "
            f"{cc:>+0.4f} ± {cc_std:.3f} | "
            f"{cm:>+0.4f} ± {cm_std:.3f}   | "
            f"{rc:>+0.4f} ± {rc_std:.3f}"
        )

        results.append({
            "D": D,
            "N": N,
            "same_to_C": res["same_to_C"],
            "cross_to_C": res["cross_to_C"],
            "cross_to_Cmirror": res["cross_to_Cmirror"],
            "random_to_C": res["random_to_C"],
            "elapsed_sec": elapsed,
        })

    print()
    print("=== Falsification verdict per F132 §7 prediction ===")
    print("F132 predicts:")
    print("  P1: same->C       >>  random->C       (above-random retrieval)")
    print("  P2: cross->C      ≈   random->C       (cross-sector does NOT recover original)")
    print("  P3: cross->Cmirr  >>  random->C       (cross-sector DOES recover flipped)")
    print("  P4: cross->Cmirr  ≈   same->C         (symmetric retrieval quality)")
    print()
    for r in results:
        D, N = r["D"], r["N"]
        sc = r["same_to_C"][0]
        cc = r["cross_to_C"][0]
        cm = r["cross_to_Cmirror"][0]
        rc = r["random_to_C"][0]

        # Tolerance: ±0.02 for "≈"; > 0.05 above for ">>"
        p1 = sc > rc + 0.05
        p2 = abs(cc - rc) < 0.02
        p3 = cm > rc + 0.05
        p4 = abs(cm - sc) < 0.02
        all_pass = p1 and p2 and p3 and p4
        verdict = "ALL F132 PREDICTIONS PASS" if all_pass else f"P1={p1}, P2={p2}, P3={p3}, P4={p4}"
        print(f"  D={D:>5}, N={N:>3}: {verdict}")
        if not p2:
            print(f"     cross->C={cc:+0.4f} vs random->C={rc:+0.4f} (gap={cc-rc:+0.4f})")
        if not p4:
            print(f"     cross->Cmirr={cm:+0.4f} vs same->C={sc:+0.4f} (gap={cm-sc:+0.4f})")

    out_path = Path(__file__).parent / "R-RBS-LM-99v2_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "configs": [{"D": D, "N": N} for D, N in configs],
        "seed": 42,
        "results": results,
    }, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
