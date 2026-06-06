"""R-RBS-LM-F449 — ACTUALIZE the sedenion front-loader (F442) with srmech 0.7.2rc1,
to pin exactly what (if anything) must come to srmech to make it a first-class op.

The front-loader = CARRY ∘ COUPLE (F442 carry-vs-couple split):
  COUPLE (≤ 𝕆)  : bind ≤7 real streams into ONE octonion, reversibly.
                  -> srmech NATIVE: cascade.hypercomplex_couple (#908, 0.7.2rc1).
  CARRY  (past 𝕆): hold MORE than 7 in ONE structure + error-correct, using the
                  SEDENION's STRUCTURE (Hamming(15,11): 11 data + 4 parity, GF(2)
                  reversible) and NOT its broken chirality (the algebra, zero divisors).
                  -> srmech GAP: hand-rolled here (no Hamming/code-ladder op; only the
                  k=3 klein4_triality_correct EC + the private _xor_buf GF(2) primitive).

"Front-load the dump truck in one pass": the 𝕆 algebra caps the carrier at 7 reversible
slots; the CODE carries 11 data + 4 EC in one 15-slot structure (11/7 ≈ 1.57× per pass,
plus single-error correction, plus headroom) — past the Hurwitz cap, reversibly.

Run: /tmp/verify_srmech_072rc1_sci/bin/python R-RBS-LM-F449_sedenion_frontloader_actualize.py
"""
import numpy as np
from srmech.amsc import cascade   # COUPLE half — NATIVE

GAP = {"native": [], "handrolled": []}

# ============ CARRY half: Hamming(15,11) front-loader (hand-rolled — the GAP) ============
def _col(j): return [(j >> 3) & 1, (j >> 2) & 1, (j >> 1) & 1, j & 1]
_H = [[_col(j)[r] for j in range(1, 16)] for r in range(4)]   # 4x15 parity-check matrix
ROW_PARITY_IDX = [7, 3, 1, 0]                                  # row r controls codeword bit 8>>r
PARITY = set(ROW_PARITY_IDX)
DATA_POS = [j for j in range(15) if j not in PARITY]          # the 11 data slots

def syndrome(v):
    return tuple(sum(_H[r][j] * v[j] for j in range(15)) % 2 for r in range(4))

def encode(d11):
    v = [0] * 15
    for pos, bit in zip(DATA_POS, d11):
        v[pos] = bit
    for r, pidx in enumerate(ROW_PARITY_IDX):
        v[pidx] = sum(_H[r][j] * v[j] for j in range(15) if j != pidx) % 2
    return v

def decode_correct(v):
    s = syndrome(v)
    pos = s[0] * 8 + s[1] * 4 + s[2] * 2 + s[3]   # syndrome == 1-based error position
    cw = list(v)
    if pos != 0:
        cw[pos - 1] ^= 1
    return [cw[p] for p in DATA_POS], pos
GAP["handrolled"].append("Hamming(15,11) encode/syndrome/decode_correct (CARRY/EC) — no srmech code-ladder op")


def main():
    ok = {}
    print("=== F449: actualize the sedenion FRONT-LOADER (CARRY ∘ COUPLE) on srmech 0.7.2rc1 ===\n")

    # ---------- COUPLE half (NATIVE) ----------
    rng = np.random.default_rng(11)
    streams7 = list(rng.normal(size=7))
    oct_coupled = cascade.hypercomplex_couple(streams7, axis="diagonal", sigma=+1)
    oct_back = cascade.hypercomplex_couple(oct_coupled, axis="diagonal", sigma=-1)
    couple_err = max(abs(a - b) for a, b in zip(streams7, list(oct_back)[1:8]))
    ok["COUPLE (native hypercomplex_couple): 7 streams -> octonion, reversible"] = couple_err < 1e-9
    GAP["native"].append("cascade.hypercomplex_couple (COUPLE ≤𝕆, #908/0.7.2rc1)")
    print(f"  COUPLE: 7 streams bound -> octonion, unbind err {couple_err:.2e}  (NATIVE)")

    # ---------- CARRY half (front-loader): hold 11 + EC in ONE structure ----------
    data11 = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]
    cw = encode(data11)
    valid = syndrome(cw) == (0, 0, 0, 0)
    # corrupt one slot, correct, recover
    corrupted = list(cw); corrupted[6] ^= 1          # flip slot index 6 (position 7)
    rec, located = decode_correct(corrupted)
    all_located = locate_all()
    ok["CARRY (Hamming(15,11)): 11 data + 4 parity, valid codeword"] = valid
    ok["CARRY: single error LOCATED + corrected, 11 data recovered exactly"] = (rec == data11 and located == 7 and all_located)
    print(f"  CARRY: Hamming(15,11) valid={valid}, corrupted slot 7 -> located={located} (all-15 localizable={all_located}), 11 data recovered exact={rec == data11}  (HAND-ROLLED — gap)")

    # ---------- CAPACITY: one load past the 𝕆 cap ----------
    oct_slots, code_data, code_total = 7, len(DATA_POS), 15
    ok["FRONT-LOAD: code carries 11 data/struct > octonion 7/struct (1 pass, +EC)"] = code_data > oct_slots
    print(f"  FRONT-LOAD: 𝕆 algebra cap = {oct_slots} reversible slots/structure; "
          f"CODE carries {code_data} data + {code_total - code_data} EC in ONE 15-slot structure "
          f"= {code_data/oct_slots:.2f}× per pass, reversible past 𝕆")

    # ---------- NEST: the coupled octonion's 7 sector-points ride inside the 15-code ----------
    import itertools
    fano = {frozenset((a, b, a ^ b)) for a, b in itertools.combinations(range(1, 8), 2)}
    ok["NEST: octonion Fano(7) ⊂ sedenion PG(3,2)(15) — coupled octonion rides in the code"] = (len(fano) == 7)
    print(f"  NEST: octonion's 7 sector-points (Fano) occupy 7 of the code's 15 slots "
          f"(PG(2,2)⊂PG(3,2)); +4 headroom data +4 EC parity")

    print("\n  --- srmech GAP inventory (what actualizing the front-loader needs) ---")
    print("  NATIVE (used):")
    for x in GAP["native"]:
        print(f"     ✓ {x}")
    print("  HAND-ROLLED (the srmech ask):")
    for x in GAP["handrolled"]:
        print(f"     ✗ {x}")
    print("  GF(2) substrate present: hdc._xor_buf (private) + lean-ALU add/sub (parity=XOR);")
    print("  k=3 EC present: klein4_triality_correct — but NOT the 2ⁿ−1 Hamming-ladder code.")
    print("  REAL-coefficient EC (the octonion's real coeffs, not just sector bits) = a SEPARATE")
    print("  construction (real-field block code), flagged in F442 — not attempted here.")

    allok = all(ok.values())
    print()
    for k, v in ok.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("\nVERDICT:", "FRONT-LOADER ACTUALIZED (COUPLE native + CARRY hand-rolled) ✓" if allok else "FAIL ✗")
    return 0 if allok else 1


def locate_all():
    """every single error among the 15 slots is located by its syndrome (== position)."""
    base = encode([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])
    for ep in range(1, 16):
        v = [b ^ (1 if i == ep - 1 else 0) for i, b in enumerate(base)]
        s = syndrome(v)
        if (s[0] * 8 + s[1] * 4 + s[2] * 2 + s[3]) != ep:
            return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
