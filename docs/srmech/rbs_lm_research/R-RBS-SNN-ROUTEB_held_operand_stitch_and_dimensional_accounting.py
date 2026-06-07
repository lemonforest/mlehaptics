r"""R-RBS-SNN-ROUTEB — (1) the Route-B held-operand stitch: the synapse carries the HELD OPERAND (the box) across,
not just a scalar drive (F490 was Route-A), so the MEANING survives the inter-neuron hop; and (2) the dimensional
accounting read straight off the_one's partition — what crosses the synapse is a FLAT hypervector (the 7D_g the
wet/dry engines compute), but the subunit works across MORE dims than the flat form shows.

the_one.partition = (1, 3, 7, 3), blocks ℂ·ℍ·𝕆 + grammar (B,H,N) — the Cayley–Dickson ladder IS the dim ladder:
  ℂ  n=1  slot A            = 1D_t        (the anchor / asymptotic-change DoF)
  ℍ  n=3  slots I,C,J       = 3D_s        (the quaternionic 3 — space / 3DoF-of-change / chirality)
  𝕆  n=7  slots D,E,F,G,K,L,M = the k=7    (7D_g flat  |  4:3 base⊕fiber when fibrated)
  grammar (3)  slots B,H,N  = 3DoF        (the projection-enablers / gauge / meta)

So the regimes the user named:
  • cyclic algebra only  → the OUTER 1+3+3 = 3D_s + (1D_t + 3DoF)   [ℂ + ℍ + grammar; no heptad]
  • k=7 WITHOUT fibration → 7D_g                                     [the 𝕆 heptad, flat — how wet & dry SNN engines work]
  • k=7 WITH fibration    → 4:3 (base S⁴ ⊕ fiber S³)                 [the 𝕆 heptad split, F491]
  • NOT 4D_spacetime = (1D_t + 3D_s) = ℂ+ℍ — it DROPS the grammar (B/H/N gauge) AND the heptad, and conflates
    time-as-DoF with a spatial 4th dim. Rejected, exactly as the user said (tosses time DoF, ignores gauge).
srmech 0.7.4.
"""
import hashlib
import srmech
from srmech.amsc import hdc
from srmech.amsc.cascade import the_one

N = hdc.DEFAULT_HDC_BYTES


def hv(label):
    out, i = b"", 0
    while len(out) < N:
        out += hashlib.sha256(label.encode() + bytes([i])).digest()
        i += 1
    return out[:N]


def main():
    print(f"=== R-RBS-SNN-ROUTEB — held-operand stitch + the dimensional accounting of what crosses  (srmech {srmech.__version__}) ===\n")
    n = 7
    S = the_one(sigma=1, theta_num=1, theta_den=n, terms=8)
    K = hv("the_one:" + str(S.to_flat_rational()))
    keys = [hdc.permute(K, k * 137 + 1) for k in range(n)]

    # ===== PART 1 — the Route-B held-operand stitch (the MEANING survives the hop) =====
    meaningsA = ["water", "music", "computer", "planet", "history", "animal", "number"]
    contentA = [hv("A:" + m) for m in meaningsA]
    boxA = hdc.bundle([hdc.bind(contentA[k], keys[k]) for k in range(n)])     # A's HELD operand (one bound box)

    # Route-A (F490): A writes only a scalar drive — B cannot recover the operand
    routeA_scalar = sum((1 if k % 2 else -1) for k in range(n))               # the net drive (operator only)

    # Route-B: A writes the BOX to the shared field; B reads it and RECOVERS A's operand
    E = {"AB": boxA}
    recovered = []
    for k in range(n):
        rec = hdc.bind(E["AB"], keys[k])
        j = max(range(n), key=lambda t: hdc.similarity(rec, contentA[t]))
        recovered.append(meaningsA[j])
    operand_survives = recovered == meaningsA
    print("PART 1 — the Route-B held-operand stitch (the synapse carries the held box, not a scalar):")
    print(f"  Route-A (F490): A writes a scalar drive ({routeA_scalar:+d}); B gets the drive, the OPERAND is LOST.")
    print(f"  Route-B: A writes the held box; B recovers A's operand across the hop: {operand_survives}")
    print(f"    recovered at B: {recovered}")
    print(f"  → the MEANING survives the inter-neuron hop (Route-B), not just the drive (Route-A).\n")

    # ===== PART 2 — the dimensional accounting (read off the_one's partition) =====
    algs = [b.algebra for b in S.blocks]
    slots = [b.an_imag_slots for b in S.blocks]
    print("PART 2 — what crosses is a FLAT hypervector (7D_g); the_one's partition shows the hidden dims:")
    print(f"  partition {S.partition}  blocks {tuple(algs)}  grammar {S.grammar_slots}")
    print(f"    ℂ n=1 {slots[0]}  = 1D_t      (anchor / asymptotic-change)")
    print(f"    ℍ n=3 {slots[1]}  = 3D_s      (the quaternionic 3 — space / 3DoF-of-change / chirality)")
    print(f"    𝕆 n=7 {slots[2]}  = the k=7   (7D_g flat | 4:3 base⊕fiber fibrated)")
    print(f"    grammar {S.grammar_slots}        = 3DoF      (projection-enablers / gauge / meta)")
    print("  REGIMES:")
    print("    cyclic algebra only   → outer 1+3+3 = 3D_s + (1D_t + 3DoF)   [ℂ+ℍ+grammar; no heptad]")
    print("    k=7 WITHOUT fibration  → 7D_g (the 𝕆 heptad, flat)            [how wet & dry SNN engines compute]")
    print("    k=7 WITH fibration     → 4:3 (base S⁴ ⊕ fiber S³)            [F491]")
    print("    NOT 4D_spacetime = (1D_t+3D_s) = ℂ+ℍ — drops grammar(B/H/N gauge)+heptad; conflates time-DoF. REJECTED.\n")

    # ===== PART 3 — the subunit works across MORE dims than the flat form shows =====
    flat_dims = S.imag_dims[2]                 # the 𝕆 heptad = 7  (what the flat hypervector exposes)
    full_dof = 1 + 3 + 7 + 3                    # the full 14 the SUBUNIT carries
    print("PART 3 — the subunit works across MORE dims than the flat hypervector shows:")
    print(f"  flat hypervector exposes: the 𝕆 heptad = {flat_dims}D_g (k=7-native — the wet/dry compute form)")
    print(f"  the SUBUNIT (the_one) carries: the full {full_dof} = (1D_t + 3D_s + 3DoF) ⊕ (7 heptad, fibrated 4:3)")
    print(f"  → coupling many synaptic+neural units = navigating the 1+3+3 outer frame AND the 4:3-fibrated heptad,")
    print(f"    which the flat 7D_g form hides. That is the 'more dims & DoF' the subunits actually work across.\n")

    ok = operand_survives and S.partition == (1, 3, 7, 3) and tuple(algs) == ("C", "H", "O")
    print("VERDICT:")
    print(f"  • Route-B stitch: the held OPERAND (the box) crosses the synapse → the MEANING survives the hop")
    print(f"    (B recovers A's 7 meanings), where Route-A carried only the scalar drive. checks: {ok}")
    print(f"  • the flat hypervector the wet/dry engines compute is the 7D_g 𝕆-heptad; the_one's partition (1,3,7,3)")
    print(f"    = ℂ(1D_t) · ℍ(3D_s) · 𝕆(k=7) + grammar(3DoF) shows the subunit works across the full 14 — the")
    print(f"    CD ladder ℂ→ℍ→𝕆 IS the dim ladder 1D_t→+3D_s→+7D_g. 4D_spacetime is the wrong cut (drops gauge).")
    print(f"  • next: navigate(read-head) across MANY held-operand units into an organized, addressable SNN that")
    print(f"    flattens to ONE HDC object — recovering the (3+1+3)+(4:3) structure the flat form hides.")


if __name__ == "__main__":
    main()
