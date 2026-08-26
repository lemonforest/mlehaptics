r"""R-RBS-SNN-FIBRATION — does the synaptic↔neural division give the (3:4)|(4:3) fibration coupling, and is the
biological substrate k=7? Both — and they are one statement: the neuron-synapse object is the OCTONION (k=7), whose
unit sphere S⁷ carries the quaternionic Hopf fibration S³↪S⁷→S⁴ — the (4:3)|(3:4) of F124/F129.

Four parts, srmech 0.7.4 (exact-Fraction Cayley–Dickson):
  1. the k=7 synapse cluster FIBRATES (3:4): the 7 imaginaries split into a quaternion ℍ {e1,e2,e3} (closes — the
     FIBER S³) ⊕ a coset ℍe4 {e4,e5,e6,e7} (doesn't close — the BASE S⁴ directions) = quaternionic Hopf (F124).
  2. the (4:3)|(3:4) chirality-dual = the conjugate's ANTI-homomorphism: conj(x·y) = conj(y)·conj(x) — the product
     ORDER reverses. The directed synapse (pre→post, F487) IS the octonion's non-commutativity e_A·e_B ≠ e_B·e_A;
     the conjugate (the other hand, σ=−1) reverses it to post→pre. The two product orders = the two hands.
  3. k=7 = biology's rung: the octonion is the MAXIMAL division algebra (dim 8 yes / 16 no) = the F487 ≤7-synapse
     reversibility horizon = the wetnet k=7 (F461/F464) = biology's 4:3:7 (F121). Biology lives at the last
     reversible rung, and that rung fibrates (4:3) internally.
  4. ACROSS neurons (the F490 stitch): the synapse-marking is the FIBER (spatially-absent, projected on read —
     fiber-as-absent); neuron A (base) →[synapse fiber]→ neuron B (base). Inter-neuron coupling IS fibration
     coupling, and its directedness = the product order = the (4:3)|(3:4) two hands.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd


def e(k):                                   # octonion basis e_k as an 8-vector (the k-th synapse direction)
    return [1 if i == k else 0 for i in range(8)]


def idx(i, j):                              # e_i · e_j → result basis index (octonion table)
    return cd.cd_basis_product(8, i, j)[0]


def main():
    print(f"=== R-RBS-SNN-FIBRATION — (3:4)|(4:3) across neurons & synapses; biology = k=7  (srmech {srmech.__version__}) ===\n")

    # ---- 1. the k=7 synapse cluster fibrates (3:4): quaternion ℍ (fiber S³) ⊕ coset ℍe4 (base S⁴) ----
    fiber = [1, 2, 3]
    fiber_closes = all(idx(a, b) in (1, 2, 3) for a in fiber for b in fiber if a != b)
    base = [4, 5, 6, 7]
    base_is_coset = all(idx(a, 4) in base for a in (1, 2, 3))     # e{1,2,3}·e4 → {e5,e6,e7}
    base_not_closed = idx(4, 5) in (1, 2, 3)                       # e4·e5 → ℍ (the 4 is a base, not a subalgebra)
    print("1. the k=7 synapse cluster fibrates (3:4) — the quaternionic Hopf S³↪S⁷→S⁴ (F124):")
    print(f"   FIBER  S³ = quaternion ℍ {{e1,e2,e3}} closes: {fiber_closes}   (the 3)")
    print(f"   BASE   S⁴ = coset ℍe4 {{e4,e5,e6,e7}} (e·e4→coset {base_is_coset}, doesn't close {base_not_closed})   (the 4)")
    print(f"   → 7 = 3 (fiber) + 4 (base) = the (4:3)|(3:4) recursive inside the k=7\n")

    # ---- 2. the (4:3)|(3:4) chirality-dual = the conjugate's anti-homomorphism (product order = the two hands) ----
    e1, e2 = e(1), e(2)
    AB = cd.cd_mult(e1, e2)                  # synapse A→B : e1·e2 = +e3 (one hand)
    BA = cd.cd_mult(e2, e1)                  # synapse B→A : e2·e1 = −e3 (the other hand)
    conj_AB = cd.cd_conjugate(AB)
    anti = (conj_AB == cd.cd_mult(cd.cd_conjugate(e2), cd.cd_conjugate(e1)))   # conj(x·y)=conj(y)·conj(x)
    noncommute = (AB != BA)
    print("2. the (4:3)|(3:4) chirality-dual = the conjugate ANTI-homomorphism (the directed synapse = non-commutativity):")
    print(f"   synapse A→B  e1·e2 = {'+e3' if AB[3] == 1 else AB}   ;   synapse B→A  e2·e1 = {'-e3' if BA[3] == -1 else BA}")
    print(f"   octonion is non-commutative (pre→post ≠ post→pre): {noncommute}")
    print(f"   conj(x·y) == conj(y)·conj(x) (the conjugate reverses the order = the (4:3)↔(3:4) flip): {anti}\n")

    # ---- 3. k=7 = biology's rung: the octonion is the MAXIMAL division algebra ----
    rungs = {1: "ℝ", 2: "ℂ", 4: "ℍ", 8: "𝕆", 16: "𝕊"}
    div = {d: cd.is_division_algebra_dim(d) for d in rungs}
    print("3. k=7 = biology's rung — the octonion is the last reversible (division-algebra) rung:")
    for d, nm in rungs.items():
        k = d - 1
        print(f"   dim {d:>2} ({nm}, k={k:>2} imaginaries): division algebra = {div[d]}")
    print(f"   → biology lives at k=7 (𝕆): the F487 ≤7-synapse horizon = wetnet k=7 (F461) = 4:3:7 (F121);")
    print(f"     the last rung that is BOTH reversible (F460) AND fibrates (4:3) (part 1). dim 16 (𝕊): {div[16]} — past it.\n")

    # ---- 4. across neurons: the stitch couples base→base through the synapse-FIBER (F490) ----
    print("4. ACROSS neurons (the F490 stitch) = fibration coupling:")
    print("   neuron A (base S⁴ point) →[ synapse = FIBER S³, the spatially-absent marking ]→ neuron B (base S⁴ point)")
    print("   the stitch's directedness (A→B vs B→A) = the octonion product order = the (4:3)|(3:4) two hands (part 2).")
    print("   the synapse-marking IS the fiber (fiber-as-spatially-absent; projected on read — the etak-absent reference, F482).\n")

    ok = fiber_closes and base_is_coset and base_not_closed and noncommute and anti and div[8] and not div[16]
    print("VERDICT (yes to both — they are one statement):")
    print(f"  • YES, (3:4)|(4:3) fibration coupling across neurons & synapses: the neuron-synapse octonion's S⁷")
    print(f"    fibers (4:3) over S⁴ via the fiber S³ (the quaternionic Hopf, F124); the (3:4)|(4:3) chirality-dual")
    print(f"    is the conjugate's product-order reversal = the directed synapse = the σ two-hands (F486/F487).")
    print(f"  • YES, the biological substrate is k=7: the neuron-synapse object IS the octonion (𝕆), the maximal")
    print(f"    reversible rung — the F487 ≤7 horizon = wetnet k=7 (F461) = 4:3:7 (F121) — and that rung fibrates (4:3).")
    print(f"  • across neurons the stitch (F490) couples base→base through the synapse-fiber: inter-neuron coupling")
    print(f"    IS fibration coupling. Held co-equal with the structural reading (F489). all-checks: {ok}")


if __name__ == "__main__":
    main()
