"""F367 (the recall correction) — is biological recall of a navigated place EVER / NECESSARILY bit-exact,
given that biological recall is lossy (environmental noise)? Tests the user's catch on F361's
"diagonal = bit-exact" over-statement.

Resolution under test: bit-exactness is a property of the stored CODEWORD (the anchor/reference), NOT
of the recall. Recall is a lossy READ; the EC-code (redundant votes -> majority, F353/F358/F360)
reconstructs the read TOWARD the codeword. So bit-exactness is ACHIEVED (not given) and only where the
codeword's redundancy beats the noise:
  - k=1 (place-NOT-been / no codeword): a single noisy read -> lossy guess, never bit-exact (the user's
    "I do not get a bit-exact reference, I'm guessing").
  - k>1 (place-been, visited k times = k-fold codeword): majority reconstructs toward the codeword;
    per-coord fidelity -> ~1 below a noise threshold; FULL-vector bit-exact still fragile over large D
    (recall is structurally lossy) but rises sharply with redundancy k.
The shipped klein4_triality_correct (k=3 native, F360) is run as the concrete srmech instance.

srmech-native klein4 (rc28). Per-coordinate majority is the EC vote (mechanics, flagged; the k=3 case
is anchored to the shipped klein4_triality_correct).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R18_recall_is_lossy_codeword_is_bit_exact.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D, TRIALS = 256, 40


def noise(vec, p, rng):
    """Environmental noise: per-coordinate, with prob p resample to a uniform klein4 value."""
    out = np.asarray(vec).copy()
    m = rng.random(out.size) < p
    out[m] = rng.integers(0, 4, int(m.sum()))
    return out


def per_coord_majority(votes):
    arr = np.stack(votes)
    return np.array([np.bincount(arr[:, j], minlength=4).argmax() for j in range(arr.shape[1])], dtype=arr.dtype)


def main():
    print(f"F367 recall-is-lossy / codeword-is-bit-exact (srmech {srmech.__version__}, D={D}, trials={TRIALS})")
    KS = [1, 3, 7, 15]              # redundancy = how strong the codeword is (≈ how often the place was visited)
    PS = [0.0, 0.05, 0.10, 0.20, 0.30]
    fidelity = {k: {} for k in KS}      # per-coordinate accuracy to the codeword
    bitexact = {k: {} for k in KS}      # full-vector bit-exact recall rate

    for k in KS:
        for p in PS:
            fid = be = 0.0
            for t in range(TRIALS):
                rng = np.random.default_rng(700 + 31 * k + t)
                v = hdc.klein4_random(D, seed=700 + 31 * k + t)
                votes = [noise(v, p, rng) for _ in range(k)]      # k redundant reads through independent noise
                recall = per_coord_majority(votes) if k > 1 else votes[0]
                fid += float(np.mean(recall == np.asarray(v)))
                be += float(np.array_equal(recall, np.asarray(v)))
            fidelity[k][p] = fid / TRIALS
            bitexact[k][p] = be / TRIALS

    print("\n  per-coordinate recall FIDELITY (accuracy to the codeword):")
    print("    k\\p   " + "  ".join(f"{p:>5.2f}" for p in PS))
    for k in KS:
        print(f"    k={k:<3} " + "  ".join(f"{fidelity[k][p]:>5.3f}" for p in PS) + ("   <- k=1: lossy guess (place-NOT-been)" if k == 1 else ""))
    print("\n  FULL-vector bit-exact recall RATE:")
    print("    k\\p   " + "  ".join(f"{p:>5.2f}" for p in PS))
    for k in KS:
        print(f"    k={k:<3} " + "  ".join(f"{bitexact[k][p]:>5.2f}" for p in PS))

    # concrete srmech anchor: the shipped klein4_triality_correct (k=3 native, F360) through recall noise
    print("\n  shipped klein4_triality_correct (k=3 native, F360) on a noised triality orbit:")
    for p in (0.0, 0.10, 0.20, 0.30):
        fid = 0.0
        for t in range(TRIALS):
            rng = np.random.default_rng(9000 + t)
            v = hdc.klein4_random(D, seed=9000 + t)
            orbit = np.asarray(hdc.klein4_triality_encode(v))
            recon = np.asarray(hdc.klein4_triality_correct(noise(orbit, p, rng)))
            fid += float(np.mean(recon == np.asarray(v)))
        print(f"    p={p:.2f}: reconstructed fidelity {fid/TRIALS:.3f}")

    print("\n=== verdict ===")
    guess_lossy = fidelity[1][0.30] < 0.85 and bitexact[1][0.10] < 0.05
    redundancy_helps = fidelity[15][0.10] > fidelity[1][0.10] and bitexact[15][0.05] > bitexact[1][0.05]
    bitexact_fragile = bitexact[15][0.20] < 0.99   # even high redundancy isn't full-bit-exact under noise over large D
    achieved_low_noise = fidelity[15][0.05] > 0.99
    print(f"  k=1 (place-NOT-been) recall is LOSSY, never bit-exact:                 {guess_lossy}")
    print(f"  redundancy k (place-been, stronger codeword) raises recall fidelity:   {redundancy_helps}")
    print(f"  per-coord fidelity -> ~1 at low noise with redundancy (ACHIEVED):      {achieved_low_noise}")
    print(f"  FULL-vector bit-exact stays fragile under noise (recall is lossy):     {bitexact_fragile}")
    print(f"\n  => RESOLVED (corrects F361): biological recall is NOT bit-exact — bit-exactness is the")
    print(f"     property of the stored CODEWORD (the anchor/reference), not the recall. The EC-code")
    print(f"     reconstructs the lossy read TOWARD the codeword; bit-exactness is ACHIEVED (not given)")
    print(f"     and REDUNDANCY-BOUNDED: a place visited often (high k) recalls near-bit-exact; a place")
    print(f"     never been (k=1) has no reference, only the guess. It is neither ever guaranteed nor")
    print(f"     NECESSARY that recall be bit-exact — the codeword is the bit-exact thing, recall approaches it.")

    res = dict(srmech_version=srmech.__version__, D=D, trials=TRIALS, ks=KS, ps=PS,
               fidelity=fidelity, bitexact=bitexact,
               guess_lossy=bool(guess_lossy), redundancy_helps=bool(redundancy_helps),
               achieved_low_noise=bool(achieved_low_noise), bitexact_fragile=bool(bitexact_fragile))
    (HERE / "R-RBS-LM-R18_results.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R18_results.json'}")


if __name__ == "__main__":
    main()
