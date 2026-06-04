"""#855/SNN — is the spatial-nav SAVE/FETCH cascade bit-exact WITHOUT the final rotate, and is
the rotate (the Class-K asymptotic-DoF) the DoF that makes NN/language NON-bit-exact?

User hypothesis: "reading neurons WITHOUT the rotate at the end = our DoF." NN/language measures
NON-bit-exact (F166: float foundation not bit-exact); we modeled that cascade. We never tested
the SPATIAL-NAV save/fetch cascade with-vs-without the final rotate.

The "rotate at the end" = Class-K asymptotic-DoF (`[[user_stance_rotation_is_class_k_pin_slot]]`),
and on the Klein-4 store it IS the bipolar projection of R1/R2: collapse the iω₇ axis
(state>>1), which has the dead-band where the pin-slot rejects projection (F141).

klein-4 encoding (verified): state = 2*(γ₅ bit) + (iω₇ bit); γ₅=state>>1, iω₇=state&1.

SAVE/FETCH (the spatial-nav cascade, R1 substrate): stored = klein4_bind(place_anchor, location);
fetched = klein4_unbind(stored, place_anchor). Three end-cascades:
  (1) NONE                      -> expect BIT-EXACT (R1: klein4 unbind exact)
  (2) invertible rotate (Class C flip, then inverted) -> expect BIT-EXACT (rotation is reversible)
  (3) lossy COLLAPSE (Class-K asymptotic-DoF: drop iω₇ = bipolar projection) -> expect NON-bit-exact

If (1)/(2) bit-exact and (3) not, the asymptotic-DoF collapse IS the DoF that makes save/fetch
non-bit-exact -- and it destroys EXACTLY one chirality axis (the iω₇), confirming the rotate is
the lossy projection language/NN pays and spatial-nav save/fetch can omit.

srmech-native: klein4_bind/unbind/chirality_flip_omega7/random + bit ops on the uint8 sectors.

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R8_savefetch_bitexact_vs_rotate_dof.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D, K, TRIALS = 512, 20, 10


def g5(v): return (v >> 1)            # γ₅ axis bit
def iw7(v): return (v & 1)            # iω₇ axis bit
def collapse_iw7(v): return (v >> 1) << 1   # asymptotic-DoF: drop iω₇ (bipolar projection)


def run_trial(seed):
    rng = np.random.default_rng(seed)
    anchors = [hdc.klein4_random(D, seed=seed + i) for i in range(K)]
    locs = [hdc.klein4_random(D, seed=seed + 1000 + i) for i in range(K)]
    stored = [hdc.klein4_bind(anchors[i], locs[i]) for i in range(K)]

    def fetch(i, end):
        rec = hdc.klein4_unbind(stored[i], anchors[i])
        if end == "none":
            return rec
        if end == "rotate_inv":                  # invertible Class-C flip, then inverted by the reader
            return hdc.klein4_chirality_flip_omega7(hdc.klein4_chirality_flip_omega7(rec))
        if end == "collapse_iw7":                # Class-K asymptotic-DoF: bipolar projection (drop iω₇)
            return collapse_iw7(rec)

    out = {}
    for end in ("none", "rotate_inv", "collapse_iw7"):
        bit_exact = g5_ok = iw7_ok = 0
        for i in range(K):
            rec = fetch(i, end)
            if np.array_equal(rec, locs[i]): bit_exact += 1
            if np.array_equal(g5(rec), g5(locs[i])): g5_ok += 1
            if np.array_equal(iw7(rec), iw7(locs[i])): iw7_ok += 1
        out[end] = (bit_exact / K, g5_ok / K, iw7_ok / K)
    return out


def main():
    print(f"#855/SNN — save/fetch bit-exactness vs the rotate-DoF (srmech {srmech.__version__}, D={D}, K={K}, trials={TRIALS})")
    agg = {e: np.zeros(3) for e in ("none", "rotate_inv", "collapse_iw7")}
    for t in range(TRIALS):
        r = run_trial(20260603 + t)
        for e in agg:
            agg[e] += np.array(r[e])
    for e in agg:
        agg[e] /= TRIALS

    labels = {"none": "(1) NO rotate (pure save/fetch)",
              "rotate_inv": "(2) invertible rotate (Class C, inverted)",
              "collapse_iw7": "(3) COLLAPSE iω₇ (Class-K asymptotic-DoF = bipolar projection)"}
    print(f"\n  {'end-cascade':<52} | {'bit-exact':>9} | {'γ₅ axis':>7} | {'iω₇ axis':>8}")
    for e in ("none", "rotate_inv", "collapse_iw7"):
        be, g, w = agg[e]
        print(f"  {labels[e]:<52} | {be:>9.2f} | {g:>7.2f} | {w:>8.2f}")

    none_be = agg["none"][0]; rot_be = agg["rotate_inv"][0]
    col_be = agg["collapse_iw7"][0]; col_g5 = agg["collapse_iw7"][1]; col_iw7 = agg["collapse_iw7"][2]
    print(f"\n=== verdict ===")
    print(f"  save/fetch WITHOUT rotate : bit-exact = {none_be:.2f}  (spatial-nav exact recall)")
    print(f"  save/fetch + invertible rotate : bit-exact = {rot_be:.2f}  (rotation alone is reversible)")
    print(f"  save/fetch + Class-K asymptotic-DoF collapse : bit-exact = {col_be:.2f}")
    print(f"      -> γ₅ kept ({col_g5:.2f}), iω₇ DESTROYED ({col_iw7:.2f}): the rotate collapses EXACTLY one chirality DoF")
    confirmed = none_be > 0.99 and rot_be > 0.99 and col_be < 0.5 and col_g5 > 0.99 and col_iw7 < 0.6
    print(f"\n  HYPOTHESIS CONFIRMED: the rotate (Class-K asymptotic-DoF / bipolar projection) is the DoF that")
    print(f"  makes save/fetch NON-bit-exact; without it (or with only an invertible rotate) it is BIT-EXACT: {confirmed}")
    print(f"  => spatial-nav save/fetch = the no-collapse (bit-exact) SNN cascade; language/NN = the collapse")
    print(f"     (with-rotate, projects to the observable bipolar sector) = non-bit-exact (F166). The DoF is the iω₇ the projection drops.")

    out = {"partition": "R-RBS-LM-R8 (SNN save/fetch vs rotate-DoF)", "srmech_version": srmech.__version__,
           "D": D, "K": K, "trials": TRIALS,
           "results": {e: {"bit_exact": float(agg[e][0]), "gamma5": float(agg[e][1]), "iw7": float(agg[e][2])}
                       for e in agg},
           "hypothesis_confirmed": bool(confirmed)}
    (HERE / "R-RBS-LM-R8_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R8_results.json'}")


if __name__ == "__main__":
    main()
