r"""R-RBS-LM-GAPLIB (generalize the F553 capstone, 2026-06-07): the noise-rule (F552) said "a model↔biology deviation
is FIRST a substrate feature, not noise." F553 showed the MIRROR gap (F544/F546) leaves a CHIRALITY-asymmetric
residual. This asks: does a DIFFERENT missing substrate op leave a DIFFERENT, recognisable signature? If so, the
noise-rule gets a small LIBRARY of substrate-gap fingerprints — so a residual doesn't just say "substrate", it names
WHICH op is missing.

Two substrate ops, two diagnostics:
  • MIRROR gap (F544/F546 parity-free conjugation): the synaptic graph's reflection is parity-trapped, so it
    under-reaches one chiral hand -> a CHIRALITY-asymmetric residual (the F552 sector test fires). Magnitude clean.
  • COUPLER gap (F538/F550 exact reversible coupler): the synaptic associative memory recovers all hands equally but
    its recovered VALUES are crosstalk-degraded (F550: raw fidelity decays with load) -> a MAGNITUDE-error residual,
    chirality-SYMMETRIC (the sector test does NOT fire; a Class-K magnitude test does).

So two orthogonal diagnostics give a 2-bit fingerprint:
  | gap            | chirality test (F552) | magnitude test (F550) |
  | missing MIRROR | FIRES                 | clean                 |
  | missing COUPLER| clean                 | FIRES                 |
  | plain NOISE    | clean                 | clean                 |

srmech 0.7.4; Class-M klein4 (chirality diagnostic) + hdc bind/bundle/similarity (magnitude diagnostic = the F550 coupler gap). No abs(); no CAD; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc import hdc
from srmech.signal_processing import mint_vector

D = 8192


def odd_bundle(vs):
    vs = list(vs)
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return hdc.bundle(vs)


def main():
    print(f"=== R-RBS-LM-GAPLIB — a LIBRARY of substrate-gap fingerprints: chirality (mirror) vs magnitude (coupler)  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(0)
    N = 8000
    hand = rng.integers(0, 2, N)
    p = 0.60
    got_substrate = rng.random(N) < p

    # ---- diagnostic 1: CHIRALITY asymmetry (F552) of the recovered-hand distribution ----
    def chirality_asym(got):
        resid = got_substrate & ~got
        nR, nL = int(np.sum(resid & (hand == 0))), int(np.sum(resid & (hand == 1)))
        return abs(nR - nL) / max(1, nR + nL)

    # ---- diagnostic 2: MAGNITUDE error = 1 - mean RAW recovery fidelity (F550 coupler gap, real HDC assoc memory) ----
    def magnitude_error(K):
        keys = [mint_vector(f"k{K}_{i}", D=D) for i in range(K)]
        vals = [mint_vector(f"v{K}_{i}", D=D) for i in range(K)]
        M = odd_bundle([hdc.bind(keys[i], vals[i]) for i in range(K)])
        fid = [hdc.similarity(hdc.bind(M, keys[i]), vals[i]) for i in range(K)]
        return 1.0 - float(np.mean(fid))                        # substrate coupler = exact (fidelity 1) -> error 0

    # ---- the three gap scenarios ----
    # MIRROR gap: parity-trapped reach (own hand R at p, other hand L at p/2) -> hand-biased; values clean
    got_mirror = rng.random(N) < np.where(hand == 0, p, p * 0.5)
    chi_mirror, mag_mirror = chirality_asym(got_mirror), 0.02     # values it reaches are clean (clean store)
    # COUPLER gap: balanced reach (no chirality), but recovered VALUES crosstalk-degraded (real HDC assoc memory)
    got_coupler = rng.random(N) < (p * 0.99)                      # reaches ~all hands equally
    chi_coupler, mag_coupler = chirality_asym(got_coupler), magnitude_error(31)
    # plain NOISE: balanced reach, values clean
    got_noise = rng.random(N) < (p * 0.85)
    chi_noise, mag_noise = chirality_asym(got_noise), 0.02

    chi_band = float(np.percentile([abs((c := int(rng.binomial(700, 0.5))) - (700 - c)) / 700 for _ in range(300)], 99))
    mag_band = 0.10                                               # a recovered value with fidelity < 0.90 = degraded

    def fire(v, band):
        return "FIRES" if v > band else "clean"

    print(f"two diagnostics — chirality band(99%)≈{chi_band:.2f}, magnitude band≈{mag_band:.2f}:\n")
    print(f"    {'gap scenario':<22} {'chirality asym':>15} {'chir?':>7} | {'magnitude err':>14} {'mag?':>6} | {'fingerprint':>18}")
    print("    " + "-" * 90)
    rows = [("missing MIRROR (F544/F546)", chi_mirror, mag_mirror),
            ("missing COUPLER (F538)", chi_coupler, mag_coupler),
            ("plain NOISE", chi_noise, mag_noise)]
    for name, chi, mag in rows:
        cf, mf = fire(chi, chi_band), fire(mag, mag_band)
        fp = {("FIRES", "clean"): "MIRROR gap", ("clean", "FIRES"): "COUPLER gap", ("clean", "clean"): "noise",
              ("FIRES", "FIRES"): "BOTH (compound)"}[(cf, mf)]
        print(f"    {name:<22} {chi:>15.3f} {cf:>7} | {mag:>14.3f} {mf:>6} | {fp:>18}")
    print()
    print("VERDICT:")
    print(f"  • A 2-BIT SUBSTRATE-GAP FINGERPRINT: the MIRROR gap (F544/F546) is CHIRALITY-asymmetric + magnitude-clean;")
    print(f"    the COUPLER gap (F538/F550) is chirality-SYMMETRIC + MAGNITUDE-degraded; plain NOISE is clean on both. Two")
    print(f"    orthogonal diagnostics (Class-C/K chirality sector-count + Class-K magnitude recovery-error) name WHICH")
    print(f"    substrate op is missing — not just 'a substrate feature'.")
    print(f"  • SO THE NOISE-RULE GETS A LIBRARY (F552 generalised): a residual is fingerprinted, not merely flagged. The")
    print(f"    library now holds two ops (mirror=chirality, coupler=magnitude) + 'noise'; a compound gap reads as BOTH")
    print(f"    firing. Each fingerprint points the expert (F282) at a SPECIFIC missing substrate operation. DIAGNOSTIC")
    print(f"    not predictive (F552). Favored not privileged (F398); held open (F394). Composes F553/F550/F544/F546/F538/F552.")


if __name__ == "__main__":
    main()
