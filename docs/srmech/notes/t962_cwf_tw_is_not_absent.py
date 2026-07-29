"""`#T962` / `#T981` — is ``Tw`` ALGEBRAICALLY ABSENT from ``cwf_consistency_mod2``?

`#T981` recorded "Tw is ALGEBRAICALLY ABSENT from cwf_consistency_mod2's verdict
(290/290 identical without it)", and `#T962` then reasoned from it that the op
"may not be doing CWF at all", which would make its uncited Calugareanu-White-Fuller
name-drop *wrong* rather than merely unattested.

**The premise is false.** ``genome.py:1412`` reads

    consistent = ((tw_mod2 + wr_mod2) % 2 == lk_mod2)

so ``tw_mod2`` is literally in the verdict expression. The only way a 290-run
probe can be "identical without it" is if that corpus never produced
``tw_mod2 == 1`` -- which is what happens when Q8 gains are drawn from the
POSITIVE coset {1, i, j, k} only, since ``tw_mod2`` is the parity of the count
of gains in the NEGATIVE coset {-1, -i, -j, -k}.

This script exhibits the counterexample corpus. Exact integers, no float in the
geometry, no numpy, no ``abs()``.

Run:  PYTHONPATH=docs/srmech/python python docs/srmech/notes/t962_cwf_tw_is_not_absent.py
"""
from srmech.amsc import genome as G

# the 20 exact-INTEGER Pythagorean points on the radius-25 circle (the ring
# srmech.amsc.rational.relative_writhe uses at rational.py:3223)
C25 = [(25, 0), (24, 7), (20, 15), (15, 20), (7, 24), (0, 25), (-7, 24),
       (-15, 20), (-20, 15), (-24, 7), (-25, 0), (-24, -7), (-20, -15),
       (-15, -20), (-7, -24), (0, -25), (7, -24), (15, -20), (20, -15), (24, -7)]
N = 20
flat = [(6 * cx, 6 * cy, 0) for cx, cy in C25]          # relaxed planar minicircle


def torus_knot(p, q, sigma=1, R=3, r=1, M=N):
    pts = []
    for i in range(M):
        cp, sp = C25[(p * i) % N]
        cq, sq = C25[(q * i) % N]
        rad = R * 25 + r * cp
        pts.append((rad * cq, rad * sq, sigma * r * sp * 25))
    return pts


def ring(n):
    return [(i, (i + 1) % n) for i in range(n)]


ONEQ, NEGQ = (1.0, 0.0, 0.0, 0.0), (-1.0, 0.0, 0.0, 0.0)
IQ, JQ = (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0)

CASES = [
    ("all +1 gains, flat ring",       ring(20), [ONEQ] * 20,                  flat),
    ("ONE -1 gain, flat ring",        ring(20), [NEGQ] + [ONEQ] * 19,         flat),
    ("ONE -1 gain, trefoil(2,3)",     ring(20), [NEGQ] + [ONEQ] * 19,         torus_knot(2, 3, 1)),
    ("TWO -1 gains, flat ring",       ring(20), [NEGQ] * 2 + [ONEQ] * 18,     flat),
    ("THREE -1 gains, flat ring",     ring(20), [NEGQ] * 3 + [ONEQ] * 17,     flat),
    ("TWO i gains, flat ring",        ring(20), [IQ] * 2 + [ONEQ] * 18,       flat),
    ("i,j + one -1, flat ring",       ring(20), [IQ, JQ, NEGQ] + [ONEQ] * 17, flat),
    ("-1 and i,j gains, trefoil",     ring(20), [NEGQ, IQ, JQ] + [ONEQ] * 17, torus_knot(2, 3, 1)),
]


def main():
    print("case                            lk  tw  wr2 | WITH Tw | WITHOUT Tw | differs")
    print("-" * 80)
    n_diff = n_tw_one = 0
    for label, edges, gains, emb in CASES:
        r = G.cwf_consistency_mod2(edges, gains, embedding=emb)
        lk, tw, wr2 = r["lk_mod2"], r["tw_mod2"], r["wr_mod2"]
        with_tw = r["consistent"]
        # the counterfactual: the SAME check with the Tw term deleted
        without_tw = None if (lk is None or wr2 is None) else (wr2 % 2 == lk)
        differs = with_tw != without_tw
        n_tw_one += 1 if tw == 1 else 0
        n_diff += 1 if differs else 0
        print(f"{label:31s} {str(lk):3s} {str(tw):3s} {str(wr2):3s} | "
              f"{str(with_tw):7s} | {str(without_tw):10s} | {differs}")

    print()
    print(f"cases with tw_mod2 == 1                    : {n_tw_one} of {len(CASES)}")
    print(f"cases where DROPPING Tw flips the verdict  : {n_diff} of {len(CASES)}")
    print()
    print("VERDICT -- Tw is algebraically ABSENT?", n_diff == 0)
    print("  genome.py:1412 -> consistent = ((tw_mod2 + wr_mod2) % 2 == lk_mod2)")
    print()
    print("So the op IS computing Lk = Tw + Wr (mod 2) from three independent")
    print("reads, with Tw load-bearing. The remaining `#T962` defect is the")
    print("UNCITED name-drop, not a wrong one -- and the attestation chain")
    print("already exists in tree at")
    print("  docs/srmech/notes/nucleosome_turn_asymmetry_frame_spike.md:353")
    print("  Dennis & Hannay 2005, arXiv:math-ph/0503012v2 (OA, full text")
    print("  extracted) -- all three integral forms Tw / Wr / Lk;")
    print("  originals Calugareanu 1959/61, White 1969, Fuller 1971 recorded")
    print("  at :745 as 'no OA copy located'.")


if __name__ == "__main__":
    main()
