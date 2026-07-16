r"""R-RBS-LM-CENTROMERE-CHIRALITY — does a CENTROMERE anchor carry a chromosome's GLOBAL orientation-chirality
(the (γ₅, iω₇) 4-way which-way of the whole strand) more cheaply than encoding it per-leaf in Klein-4 — and at what
robustness? A read-INDEPENDENT structural measurement (bits spent + recover-check fidelity FIRST), per the standing
discipline, BEFORE any "should this be a srmech primitive" decision.

The framework question (user, 2026-07-16): "could we use centromeres for chirality, instead of / to decrease G4 DNA?"
The two-level chirality distinction (ADR-0004): G4/Klein-4 = LOCAL per-leaf sector chirality; the centromere =
GLOBAL per-chromosome positional chirality (the p:q arm-ratio sets the strand's handedness ONCE). So the honest test
is: for the GLOBAL orientation component (constant along the strand), how do the encodings compare on cost AND on
robustness to corruption?

Three encodings of one global 4-way orientation `o ∈ {0,1,2,3}` over a chromosome of N leaves:
  A. PER-LEAF Klein-4  — o in a dedicated sector of EVERY leaf (N symbols). Recover = majority over all N (this is
     `klein4_triality_correct`'s 2-of-3 generalised to N-of-N). Cost = 2N bits. Distributed -> robust.
  B. CENTROMERE INDEX  — ONE mark carrying o (+ its position). Cost = ceil(log2 N)+2 bits. Cheapest; single point.
  C. CENTROMERE ARRAY  — a LOCALISED array of R repeats of o (biology's α-satellite is a repeat array, not one mark).
     Recover = majority over the R. Cost = ceil(log2 N)+2R bits. The middle: cheaper than per-leaf, more robust than
     a single mark — but LOCALISED, so a burst at the locus hits it (biology localises + heterochromatin-protects it).

Two corruption models: RANDOM (each symbol -> a random other w.p. f) and BURST (a contiguous run wiped to one wrong
value — the localisation stress test). We report the fraction of trials the 4-way orientation is recovered EXACTLY.

srmech 0.9.0rc253. No ALU magnitude-builtin; seeded RNG (attested, reproducible); majority = the EC read (Class K+C),
not a Counter storage proxy. Composes ADR-0004 (DNA+G4), F291 (k=3 triality EC), F135 (two-level chirality), §55.1.
Run:  /tmp/srmech_v/venv/bin/python3 R-RBS-LM-CENTROMERE-CHIRALITY_*.py
"""
import math
import random
import sys

import srmech


def majority4(votes):
    """The EC read: the most-supported 4-way sector (klein4_triality_correct's 2-of-3, generalised to N-of-array)."""
    return max(range(4), key=lambda v: sum(1 for x in votes if x == v))


def corrupt_random(symbols, o, f, rng):
    return [rng.choice([v for v in range(4) if v != o]) if rng.random() < f else s for s in symbols]


def corrupt_burst(symbols, span, rng):
    """Wipe a contiguous run of `span` symbols (starting at a random offset) to one fixed wrong value."""
    n = len(symbols)
    if span <= 0:
        return list(symbols)
    start = rng.randrange(n)
    wrong = rng.randrange(4)
    out = list(symbols)
    for k in range(span):
        out[(start + k) % n] = wrong
    return out


def trial_fidelity(N, R, T, model, level, seed):
    """Return (A, B, C) exact-orientation-recovery fractions over T trials at corruption `level`."""
    rng = random.Random(seed)
    c0 = (N - R) // 2                       # the centromere array occupies leaves [c0, c0+R) — mid-strand, localised
    okA = okB = okC = 0
    for _ in range(T):
        o = rng.randrange(4)
        A = [o] * N                          # per-leaf: every leaf carries o
        B = [o]                              # single centromere mark
        Cfull = [0] * N
        for k in range(c0, c0 + R):
            Cfull[k] = o                     # the localised repeat array (rest of the strand is data, not orientation)
        if model == "random":
            A = corrupt_random(A, o, level, rng)
            B = corrupt_random(B, o, level, rng)
            Cfull = corrupt_random(Cfull, o, level, rng)
        else:                                 # burst: a run of length `level` (given as an int span) wiped
            A = corrupt_burst(A, level, rng)
            Cfull = corrupt_burst(Cfull, level, rng)
        okA += (majority4(A) == o)
        okB += (B[0] == o)
        arr = Cfull[c0:c0 + R]
        okC += (majority4(arr) == o)
    return okA / T, okB / T, okC / T


def main():
    N = 300                                  # a typical body length in leaves
    R = 15                                    # centromere repeat-array size (~ sqrt(N)/1.15; biology: thousands)
    T = 4000
    bitsA = 2 * N
    bitsB = math.ceil(math.log2(N)) + 2
    bitsC = math.ceil(math.log2(N)) + 2 * R
    print(f"=== R-RBS-LM-CENTROMERE-CHIRALITY (srmech {srmech.__version__}) — GLOBAL 4-way orientation, N={N} leaves, {T} trials ===")
    print(f"bits to store the global which-way:  A per-leaf={bitsA}   B cent-index={bitsB}   C cent-array(R={R})={bitsC}"
          f"   (C is {bitsA / bitsC:.1f}x cheaper than A)")

    print("\nRANDOM corruption (each symbol -> a random other w.p. f) — exact-orientation recovery:")
    print(f"{'f':>6} {'A per-leaf':>11} {'B index':>9} {'C array':>9}")
    for f in (0.0, 0.10, 0.20, 0.30, 0.40, 0.49):
        a, b, c = trial_fidelity(N, R, T, "random", f, seed=1080 + int(f * 100))
        print(f"{f:>6.2f} {a:>11.3f} {b:>9.3f} {c:>9.3f}")

    print("\nBURST corruption (a contiguous run of `span` leaves wiped) — localisation stress test:")
    print(f"{'span':>6} {'span/N':>7} {'A per-leaf':>11} {'C array(localised)':>19}")
    for span in (30, 75, 150, 200):
        a, _b, c = trial_fidelity(N, R, T, "burst", span, seed=2080 + span)
        print(f"{span:>6} {span / N:>7.2f} {a:>11.3f} {c:>19.3f}")

    print("\nVERDICT (read-independent, cost + robustness):")
    print("- C (centromere repeat-array) recovers the GLOBAL orientation at ~%.0fx fewer bits than per-leaf, with"
          " near-identical robustness to RANDOM noise (majority over R)." % (bitsA / bitsC))
    print("- B (single index) is cheapest but fragile (dies at the first hit).")
    print("- The centromere's ONLY weakness is a BURST at its locus — biology answers exactly this by LOCALISING +")
    print("  heterochromatin-protecting the centromere. For a STORAGE format (not a noisy channel) the burst risk is")
    print("  controllable, so the centromere carries the global which-way far cheaper than per-leaf Klein-4;")
    print("  Klein-4 (G4) stays the carrier for LOCAL chirality that genuinely VARIES along the strand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
