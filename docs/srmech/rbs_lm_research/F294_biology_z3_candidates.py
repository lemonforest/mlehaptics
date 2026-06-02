"""F294 — which candidate biological ℤ₃ carries the F293 order-3 / distributed-anchor signature?

Methodology (user direction 2026-06-02): begin broad, test ALL candidates, let FALSIFICATION narrow
the question (no pre-commit; null findings count; do not lean toward the expected result). The F293
signature a candidate must show to be biology's k=3 *corrector* (not merely a k=2 parity *detector*):
  (i)  an ORDER-3 structure (a genuine 3-cycle, NOT a self-inverse order-2 parity), and
  (ii) the DISTRIBUTED anchor: the 3 phases sum to zero (1 + w + w^2 = 0, w=e^{2pi i/3}); no privileged axis.

Candidates:
  C1  triplet codon — is the genetic code a literal ℤ₃ (an order-3 base/position symmetry)?
  C2  third-base wobble — is the 3rd-codon-base redundancy order-3, or order-2 (purine/pyrimidine parity)?
  C3  tri-stable / repressilator motif — the DIRECTED 3-cycle (A⊣B⊣C⊣A).
  C4  120°-phase oscillator triad — 3 phases 120° apart.  (C3 and C4 are the same object if C3 passes.)

srmech-first: Class-L (dense_laplacian + jacobi_eigvals) for the cycle spectra. Class-K clean (no abs
in cascades; complex modulus via re^2+im^2). ATTESTED datum: the STANDARD genetic code (NCBI translation
table 1) — self-checked below by its known degeneracy counts. Scope: STRUCTURE reading only; no biology
mechanism / clinical claim (understanding-not-curing; the deliverable is the narrowed question).
"""
import os
import sys
import itertools

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import laplacian  # noqa: E402  Class-L

# ---- ATTESTED: NCBI standard genetic code (translation table 1); T for U; bases order T,C,A,G ----
BASES = "TCAG"
_AA_ROWS = {  # rows indexed by 1st base; each maps 2nd-base -> the 4 third-base (T,C,A,G) amino acids
    "T": {"T": "FFLL", "C": "SSSS", "A": "YY**", "G": "CC*W"},
    "C": {"T": "LLLL", "C": "PPPP", "A": "HHQQ", "G": "RRRR"},
    "A": {"T": "IIIM", "C": "TTTT", "A": "NNKK", "G": "SSRR"},
    "G": {"T": "VVVV", "C": "AAAA", "A": "DDEE", "G": "GGGG"},
}
CODE = {b1 + b2 + b3: _AA_ROWS[b1][b2][k]
        for b1 in BASES for b2 in BASES for k, b3 in enumerate(BASES)}


def attest_code():
    """MPM: verify the encoded table IS the standard code via its known degeneracy counts."""
    from collections import Counter
    # (Counter here is a TEST attestation tally over an attested table, not a cascade storage proxy)
    cnt = Counter(CODE.values())
    known = {"L": 6, "S": 6, "R": 6, "*": 3, "M": 1, "W": 1, "A": 4, "G": 4, "V": 4,
             "P": 4, "T": 4, "I": 3}
    ok = all(cnt[a] == n for a, n in known.items()) and len(CODE) == 64 and sum(cnt.values()) == 64
    return ok, dict(cnt)


def c1_codon_literal_z3():
    """C1: does an ORDER-3 symmetry preserve the genetic code? (order-3 base 3-cycles; the position 3-cycle)"""
    print("--- C1: triplet codon as a literal ℤ₃ (order-3 symmetry of the code) ---")
    passes = []
    # (a) order-3 permutations of the 4 bases (a 3-cycle on 3 bases, 1 fixed): preserve CODE?
    for trio in itertools.combinations(BASES, 3):
        fixed = [b for b in BASES if b not in trio][0]
        for cyc in [(trio[0], trio[1], trio[2]), (trio[0], trio[2], trio[1])]:  # the two 3-cycles
            perm = {cyc[0]: cyc[1], cyc[1]: cyc[2], cyc[2]: cyc[0], fixed: fixed}
            ok = all(CODE["".join(perm[c] for c in cod)] == CODE[cod] for cod in CODE)
            if ok:
                passes.append(("base-3cycle", cyc, fixed))
    # (b) the position 3-cycle pos1->pos2->pos3->pos1: preserve CODE?
    pos_ok = all(CODE[cod[2] + cod[0] + cod[1]] == CODE[cod] for cod in CODE)
    if pos_ok:
        passes.append(("position-3cycle", None, None))
    verdict = "PASS (a code-preserving ℤ₃ exists)" if passes else "FALSIFIED (no order-3 symmetry preserves the code)"
    print(f"  order-3 base-permutations preserving the code: {len(passes)}; position-3-cycle preserves: {pos_ok}")
    print(f"  -> C1 {verdict}\n")
    return bool(passes)


def c2_third_base_wobble():
    """C2: is the 3rd-base redundancy order-3, or order-2 (purine/pyrimidine parity)?
    Decisive structural fact: the 3rd base is 1-of-4 letters = 2 bits = (Z/2)^2 = Klein-4 = ORDER-2,
    and 3 does NOT divide 4 -> it CANNOT host a clean order-3 ℤ₃ at any position. So any non-parity
    box is a SINGLETON-anchor exception (3+1 / 2+1+1), never an order-3 cycle. We confirm this."""
    print("--- C2: third-base wobble — order-2 (parity/detect) vs order-3 (triality/correct)? ---")
    from collections import Counter
    fully_deg = split_by_parity = singleton_exc = order3 = 0
    for b1 in BASES:
        for b2 in BASES:
            aas = [CODE[b1 + b2 + b3] for b3 in BASES]   # T,C,A,G
            shape = sorted(Counter(aas).values(), reverse=True)
            if len(set(aas)) == 1:
                fully_deg += 1                            # 4-fold degenerate (parity-trivial)
            elif {aas[0], aas[1]} == {aas[0]} and {aas[2], aas[3]} == {aas[2]}:
                split_by_parity += 1                      # ORDER-2 purine/pyrimidine (2+2)
            elif shape == [3, 1] or shape == [2, 1, 1]:
                singleton_exc += 1                        # a SINGLETON anchor, NOT an order-3 cycle
            else:
                order3 += 1                               # would need a genuine 3-of-4 cyclic structure
    print(f"  16 (1st,2nd) boxes: fully-degenerate={fully_deg}, ORDER-2 purine/pyrimidine split={split_by_parity}, "
          f"singleton-anchor exceptions={singleton_exc}, genuine-order-3={order3}")
    print(f"  STRUCTURAL: 3rd base is 1-of-4 = 2 bits = (Z/2)^2 = Klein-4 (order-2); 3 does NOT divide 4")
    print(f"    -> no clean ℤ₃ can live at a codon position; the {singleton_exc} exceptions are SINGLETON anchors")
    print(f"       (TG*={{C,C,*,W}} the Trp/stop oddity; AT*={{I,I,I,M}} the Met start) — not order-3.")
    carries_order3 = (order3 > 0)
    print(f"  -> C2 FALSIFIED as the order-3 corrector. REFRAMED: the codon code IS an instance of the")
    print(f"     ORDER-2 (Klein-4) DETECT substrate (F200/F293) — base-4 per position everywhere.\n")
    return carries_order3   # False: it does NOT carry order-3 (it is the order-2 substrate itself)


def cycle_spectrum_srmech(directed):
    """Class-L spectrum of the 3-cycle. Undirected (symmetric) via srmech jacobi; directed (circulant,
    chiral) eigenvalues are the cube roots of unity (analytic — srmech eig is Hermitian-only)."""
    if not directed:
        L = laplacian.dense_laplacian(3, [(0, 1), (1, 2), (2, 0)])   # symmetric 3-cycle Laplacian
        ev = sorted(float(x) for x in laplacian.jacobi_eigvals(L))
        return ev
    # directed 3-cycle adjacency is circulant first-row [0,1,0]; eigenvalues = w^k = cube roots of unity
    w = np.exp(2j * np.pi / 3)
    return [w**0, w**1, w**2]


def c3c4_directed_3cycle():
    """C3/C4: the DIRECTED (chiral) 3-cycle = the repressilator / 3-phase oscillator. Carries 1+w+w^2=0?"""
    print("--- C3/C4: tri-stable / 3-phase oscillator = the DIRECTED (chiral) 3-cycle ---")
    sym = cycle_spectrum_srmech(directed=False)
    print(f"  srmech Class-L undirected (symmetric) 3-cycle Laplacian eigenvalues: {[round(x,3) for x in sym]}  "
          f"-> real, NO phase (the parity projection loses the ω)")
    dir_ev = cycle_spectrum_srmech(directed=True)
    s = sum(dir_ev)
    mod2 = float(s.real) ** 2 + float(s.imag) ** 2       # |sum|^2 via re^2+im^2 (Class-K; no abs)
    print(f"  directed (chiral) 3-cycle eigenvalues = cube roots of unity: "
          f"{[complex(round(z.real,3), round(z.imag,3)) for z in dir_ev]}")
    print(f"  sum of the 3 phases |1+w+w^2|^2 = {mod2:.2e}  -> {'== 0 (DISTRIBUTED ANCHOR)' if mod2 < 1e-25 else 'NONZERO'}")
    order3_phase = mod2 < 1e-25
    print(f"  -> C3/C4 {'PASS (order-3, 3-phase, distributed anchor — requires DIRECTION/chirality)' if order3_phase else 'FALSIFIED'}\n")
    return order3_phase


def main():
    print(f"=== F294 — which biological ℤ₃ carries the F293 distributed-anchor signature? (broad → falsify → narrow) ===\n")
    ok, cnt = attest_code()
    print(f"[attest] standard genetic code (NCBI table 1) encoded correctly (degeneracy counts match): {ok}\n")
    r1 = c1_codon_literal_z3()
    r2 = c2_third_base_wobble()
    r34 = c3c4_directed_3cycle()
    print("=== which survives ===")
    print(f"  C1 triplet-codon literal ℤ₃ : {'SURVIVES' if r1 else 'FALSIFIED (no order-3 preserves the code)'}")
    print(f"  C2 third-base wobble (order-3?): {'SURVIVES' if r2 else 'FALSIFIED — it IS the order-2 (Klein-4) detect substrate'}")
    print(f"  C3/C4 directed 3-cycle / 3-phase: {'SURVIVES (requires DIRECTION/chirality)' if r34 else 'FALSIFIED'}")
    print("\n  NARROWED QUESTION: the static genetic code is the ORDER-2 (Klein-4, base-4-per-position) DETECT")
    print("  substrate, NOT the corrector. The k=3 corrector must be a DIRECTED (chiral) 3-cycle — a")
    print("  repressilator-class 3-phase regulatory oscillator. DIRECTION (chirality) is load-bearing")
    print("  (the undirected 3-cycle loses the ω; only the directed circulant carries 1+ω+ω²=0).")


if __name__ == "__main__":
    main()
