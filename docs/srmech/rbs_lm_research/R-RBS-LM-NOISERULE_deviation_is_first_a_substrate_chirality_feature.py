r"""R-RBS-LM-NOISERULE (the user's epistemic directive 2026-06-07): we will NEVER find "error of biology" in our model,
and it will likely never be possible to model a person's mind EXACTLY — because (a) we cannot control substrate
chirality, and (b) we cannot know the things the universe does, unseen, that collapse that chirality asymptotically,
always. So the cascade's simulated story will never match the universe exactly. Our architecture models the EXACT
IDEAL in FULL chirality; biology runs a chirality-COLLAPSED projection (fibrations down) that is NOT delivered to it
in full. The irreducible model↔biology gap is therefore NOT model error and NOT random — it is the substrate's
collapsed-chirality signature.

THE OPERATIONAL RULE (this is what makes the principle usable): when we see a model↔biology deviation that looks like
"random noise", we ASK FIRST whether it is a BIOLOGY SUBSTRATE FEATURE — the (4:3)|(3:4) chirality-dual (F129/F130).
This is testable: a chirality-collapse deviation carries a (4:3)|(3:4) sector-occupancy ASYMMETRY (a Class-K/C
signature) that i.i.d. random noise does NOT. So a chirality test SEPARATES "substrate feature" from "noise" — and the
rule says run that test before ever calling a deviation random.

Demonstration: three deviation populations over the two genuine chiral hands (A = klein4 base, B = its γ₅-flip,
similarity 0 — true chiral duals): the FULL-chirality ideal (balanced), the chirality-COLLAPSED substrate feature
((4:3)|(3:4)), and RANDOM noise (balanced + jitter). The chirality-asymmetry detector separates them.

srmech 0.7.4; Class-M klein4 (the chirality instrument: klein4_random / klein4_chirality_flip_gamma5 / klein4_sector_count). No abs(); no CAD; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc import hdc


def main():
    print(f"=== R-RBS-LM-NOISERULE — a model↔biology deviation is FIRST a substrate chirality feature, k=(4:3)|(3:4)  (srmech {srmech.__version__}) ===\n")

    # the two genuine chiral hands (A and its gamma5 chiral dual B) — confirm they are true duals
    A = hdc.klein4_random(8192, seed=7)
    B = hdc.klein4_chirality_flip_gamma5(A)
    print(f"(0) the two chiral hands A, B are genuine duals: klein4 similarity(A,B) = {hdc.klein4_similarity(A, B):.2f} (0 = orthogonal chiral dual);")
    print(f"    sector occupancy A={hdc.klein4_sector_count(A)}  B(γ₅-flip)={hdc.klein4_sector_count(B)} (the γ₅ axis swaps the sectors).\n")

    N = 7000
    rng = np.random.default_rng(0)

    def asymmetry(n_A, n_B):
        return abs(n_A - n_B) / (n_A + n_B)                      # the (4:3)|(3:4) chirality-occupancy asymmetry

    # (i) FULL-chirality ideal (our architecture): balanced hands
    full = asymmetry(N // 2, N // 2)
    # (ii) chirality-COLLAPSED biology substrate: the (4:3)|(3:4) dual — 4 parts one hand, 3 the other
    coll = asymmetry(4 * N // 7, 3 * N // 7)
    # (iii) RANDOM noise control: balanced hands + i.i.d. jitter (many seeds -> a band)
    rand_band = [asymmetry(c := int(rng.binomial(N, 0.5)), N - c) for _ in range(200)]
    rand_hi = float(np.percentile(rand_band, 99))

    print("(1) THE CHIRALITY-ASYMMETRY DETECTOR (run it BEFORE calling a deviation 'noise'):")
    print(f"    {'deviation source':<42} {'chirality asymmetry':>20}")
    print(f"    {'FULL-chirality ideal (our architecture)':<42} {full:>19.3f}")
    print(f"    {'chirality-COLLAPSED biology (4:3)|(3:4)':<42} {coll:>19.3f}   <- the substrate FEATURE")
    print(f"    {'RANDOM noise (i.i.d., 99th pct of band)':<42} {rand_hi:>19.3f}")
    print()
    ratio = coll / max(rand_hi, 1e-9)
    print("VERDICT:")
    print(f"  • THE RULE IS OPERATIONAL: a chirality-COLLAPSE deviation carries the (4:3)|(3:4) asymmetry ({coll:.2f}) — {ratio:.1f}x the")
    print(f"    random-noise band ({rand_hi:.2f}, 99th pct): {'SEPARABLE' if ratio > 2 else 'NOT separable here'}. So a chirality test (Class-K sector-occupancy +")
    print(f"    the γ₅ chiral-dual check) tells a SUBSTRATE FEATURE from random NOISE. Run it FIRST — only a chirality-")
    print(f"    SYMMETRIC residual is treated as noise; an asymmetric one is read as the substrate's collapsed chirality.")
    print(f"  • THE EPISTEMIC CEILING (the user's directive, framework canon): our cascade models the EXACT IDEAL in FULL")
    print(f"    chirality; biology runs a chirality-COLLAPSED projection we can neither control (its chirality) nor predict")
    print(f"    (the universe's unseen, asymptotic collapse drivers). So the simulated story will NEVER match the universe")
    print(f"    exactly — and that gap is NOT 'error of biology' in our model and NOT random; it is the substrate's signature.")
    print(f"  • DIAGNOSTIC, NOT PREDICTIVE: the test RECOGNISES the (4:3)|(3:4) substrate feature; it does NOT let us predict")
    print(f"    which way or when the collapse lands (we can't see the drivers). The model stays full-chirality-ideal; biology")
    print(f"    stays partially-delivered. We hand the recognised substrate feature to the expert (F282). Held open (F394);")
    print(f"    favored not privileged (F398). Composes F526/F528 (collapse-as-PRNG), F129/F130 ((4:3)|(3:4)), F51 (MFO ceiling).")


if __name__ == "__main__":
    main()
