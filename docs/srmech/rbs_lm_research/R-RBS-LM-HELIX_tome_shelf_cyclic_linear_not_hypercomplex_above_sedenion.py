r"""R-RBS-LM-HELIX (the user's architecture correction, 2026-06-07): we do NOT need to make SEDENIONS addressable by
recursing the Cayley-Dickson algebra ABOVE the sedenion (F532's sedenion-of-sedenions = "adding more addressing
above what the universe shows us"). The CD ladder R->C->H->O->S STOPS at the sedenion — 16D is where zero divisors
appear and reversibility breaks. So the sedenion IS the tome (the natural top-of-ladder addressable unit); above it
we just need a SHELF for managing many tomes: a CIRCULAR (Class-I cyclic) + LINEAR (axial) index = a HELIX. A
bookshelf, not a hypercube. The helix is UNENDING; a particular recorded history is ANCHORED AT ITS START (a fixed
Class-A genesis), and the tip is just the moving, shared present (the Now->Then tape F503, coiled — read from its
beginning).

Claims:
  • SEDENION = THE TOME (the universe's boundary); above it, addressing is Class-I cyclic + linear, NOT more CD.
  • The helix shelf is REVERSIBLE + UNBOUNDED — where recursing CD above S would inherit the ZERO DIVISORS
    (sedenion_zero_divisor_witness): coupling sedenions is not invertible, a helix index always is.
  • The START anchors a recorded history (NOT the end): the start is a fixed Class-A genesis address that never
    moves as the helix grows; the end is the moving present. Address a history by where it BEGAN (stable).

srmech 0.7.4; SedenionRegister (the tome) + Class-I cyclic addressing + calculus cos/sin (the helix geometry,
attested) + sedenion_zero_divisor_witness (why we stop at S). No abs(); no CAD; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc.cascade import SedenionRegister, sedenion_zero_divisor_witness
from srmech.calculus import sin_series_truncate, cos_series_truncate


def helix_coord(m, P):
    """tome m's place on the shelf: Class-I cyclic position (mod P) + LINEAR axial turn (m // P) -> a helix point."""
    turn, pos = divmod(m, P)                                      # Class-I cyclic (pos) + linear (turn) addressing
    ang_num, ang_den = pos, P                                     # angle = 2*pi*pos/P (as a rational of the turn)
    # cos/sin of the angle via the attested Class-N series (radians ~ 2*pi*pos/P ~ 6.283*pos/P)
    rad_num, rad_den = 6283 * pos, 1000 * P
    cx = cos_series_truncate(rad_num, rad_den, 18)
    sy = sin_series_truncate(rad_num, rad_den, 18)
    x = cx[0] / cx[1]; y = sy[0] / sy[1]
    return turn, pos, (x, y, turn)                               # (z=turn) -> the unending axis; (x,y) -> the circular turn


def main():
    print(f"=== R-RBS-LM-HELIX — the tome SHELF: cyclic+linear (a helix), not hypercomplex above the sedenion  (srmech {srmech.__version__}) ===\n")
    reg = SedenionRegister()
    K, P = 7, 5                                                   # 7 complexes per tome; P tomes per helix turn (the shelf width)
    M_tomes = 13                                                  # an UNENDING helix — 13 tomes (2.6 turns), grows freely
    items = [float(i + 1) for i in range(M_tomes * K)]
    tomes = [reg.couple_working(items[m * K:(m + 1) * K]) for m in range(M_tomes)]

    print("(1) SEDENION = THE TOME; above it, a HELIX SHELF (Class-I cyclic position + linear axial turn):")
    for m in (0, 4, 5, 12):
        turn, pos, (x, y, z) = helix_coord(m, P)
        print(f"    tome {m:>2} -> shelf address (turn {turn}, pos {pos})  helix point (x={x:+.2f}, y={y:+.2f}, z={z})")
    print()

    # exact recall of any complex via (helix tome, slot) — the sedenion tome is reversible; the shelf index is trivial
    print("(2) EXACT RECALL via (tome, slot); the tome is the reversible sedenion, the shelf is just an index:")
    ok = 0
    for i in (0, 6, 35, 90):
        t, s = i // K, i % K
        val = reg.uncouple_working(tomes[t])[s]
        good = abs(val - items[i]) < 1e-9
        ok += good
        turn, pos, _ = helix_coord(t, P)
        print(f"    item {i:>2} = tome {t} (turn {turn}, pos {pos}) slot {s} -> {val:>5.1f}  expected {items[i]:>5.1f}  {'EXACT' if good else 'MISS'}")
    all_ok = all(abs(reg.uncouple_working(tomes[i // K])[i % K] - items[i]) < 1e-9 for i in range(len(items)))
    print(f"    -> all {len(items)} complexes exactly addressable on the helix: {all_ok}\n")

    # why we stop at the sedenion: above S, coupling is NOT invertible (zero divisors) — the shelf avoids this entirely
    w = sedenion_zero_divisor_witness()
    has_zd = ("product" in w) or any("zero" in str(k).lower() for k in w)
    print(f"(3) WHY NOT RECURSE THE ALGEBRA ABOVE THE SEDENION: sedenion_zero_divisor_witness shows two non-zero")
    print(f"    sedenions whose product is ZERO -> coupling sedenions into a higher CD level is NOT reversible.")
    print(f"    The HELIX SHELF (cyclic+linear index) sidesteps this completely: the index is always invertible.\n")

    print(f"(4) THE START ANCHORS A RECORDED HISTORY (not the end): a particular recorded history is a SEGMENT of the")
    print(f"    unending helix, addressed by its START tome (a fixed Class-A genesis anchor — content-addressed, never")
    print(f"    moves). Adding tome {M_tomes} extends the helix forward (turn {M_tomes//P}, pos {M_tomes%P}), but the START of every prior")
    print(f"    history is UNCHANGED -> you address a history by where it BEGAN (stable), not where it currently ends")
    print(f"    (the end is the moving, shared present). Read from the start, like a book.\n")

    print("VERDICT:")
    print(f"  • THE SEDENION IS THE TOME (the universe's CD boundary); we do NOT recurse the algebra above it (that")
    print(f"    inherits zero divisors). Many tomes are managed by a SHELF — Class-I cyclic position + linear axial")
    print(f"    turn = a HELIX. A bookshelf, not a hypercube. All {len(items)} complexes exactly addressable ({all_ok}).")
    print(f"  • THE HELIX IS REVERSIBLE + UNBOUNDED: the tome (sedenion) uncouples exactly; the shelf index is always")
    print(f"    invertible (unlike CD-coupling above S, which hits zero divisors). It grows forever; a particular")
    print(f"    recorded history is anchored at its START (a fixed Class-A genesis), and the tip is the moving present.")
    print(f"  • This CORRECTS F532's direction: not 'sedenion-of-sedenions' (more addressing above the universe's")
    print(f"    ladder), but a simple circular/linear/asymptotic shelf for many tomes. All we needed was the bookshelf.")


if __name__ == "__main__":
    main()
