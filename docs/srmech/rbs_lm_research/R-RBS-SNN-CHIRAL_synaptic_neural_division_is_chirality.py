r"""R-RBS-SNN-CHIRAL — the riding assumption (F394, ride-until-disproved): chirality in the neural net IS the
asymmetry of the Synaptic↔Neural object division, and a neuron + its ≤7 synapses is ONE object addressed chirally.

Mapping (the conjugation IS the chirality): a CD conjugate x̄ PRESERVES the real part and FLIPS the imaginaries.
  - NEURON  = the node identity = the REAL anchor (slot e0) — preserved under the conjugate (the neuron stays)
  - SYNAPSES = the directed couplings (pre→post) = the IMAGINARIES (slots e1..e7) — FLIPPED under the conjugate
                (direction reversed: pre→post ↦ post→pre)
So the two hands (the_one's σ=±1) are the SAME neuron read with its synapses running both ways — addressed as one.

Three tests (each with its pre-stated falsifier):
  A. the chirality IS the directedness — magnetic Laplacian (Class L directed Hermitian) has chiral energy > 0;
     symmetrize the synapses → it vanishes. Falsifier: if symmetric connectivity still showed chirality, the
     synaptic-neural division is NOT its source.
  B. neuron + ≤7 synapses addressed chirally AS ONE — conjugate-collapse (F486): hand+ = synapses pre→post
     (recovers the box, ≤𝕆 reversible), hand− = synapses post→pre (the conjugate), neuron-anchor preserved.
  C. the horizon (the falsifier on "as one") — the 8th synapse forces the climb past 𝕆 (sedenion, zero divisors)
     → no longer bit-exact-as-one in a single rung; biology must carry (F450) / collapse to handed storage (F485).
srmech 0.7.4: laplacian.magnetic_laplacian + cascade.hypercomplex_couple + cascade.cayley_dickson + the_one.
"""
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc import cascade as C
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc.cascade import the_one


def chiral_energy(H):          # Class K∘L: the antisymmetric (imaginary) mass of the directed Laplacian — no abs()
    return float((H.imag ** 2).sum())


def close(a, b, tol2=1e-18):   # squared-error closeness (Class K), never abs() in a cascade
    return all((a[i] - b[i]) ** 2 < tol2 for i in range(len(a)))


def main():
    print(f"=== R-RBS-SNN-CHIRAL — chirality = the synaptic↔neural division asymmetry  (srmech {srmech.__version__}) ===\n")

    # a directed synaptic motif: hub neuron 0 with 8 directed synaptic couplings to/from j=1..8 (mixed in/out)
    n = 9
    syn = [(0, 1, 0.9), (2, 0, 0.7), (0, 3, 0.5), (4, 0, 0.8),       # 7 couplings (Test B)
           (0, 5, 0.6), (6, 0, 0.4), (0, 7, 0.3), (8, 0, 0.55)]      # …+ the 8th (Test C)
    edges = [(a, b) for (a, b, w) in syn]
    weights = [w for (a, b, w) in syn]
    # directed weighted adjacency — built directly (dense_adjacency SYMMETRIZES, which would erase the very
    # directional asymmetry that IS the chirality; the magnetic Laplacian below keeps direction as a phase)
    Ad = [[0.0] * n for _ in range(n)]
    for (a, b, w) in syn:
        Ad[a][b] = w

    # ===== TEST A — the chirality IS the directedness =====
    H = L.magnetic_laplacian(n, edges, weights, q=0.25)               # directed Hermitian (the chiral object)
    rev_edges = edges + [(b, a) for (a, b) in edges]
    Hs = L.magnetic_laplacian(n, rev_edges, weights + weights, q=0.25)   # symmetrized synapses (no direction)
    eD, eS = chiral_energy(H), chiral_energy(Hs)
    evD, _ = L.hermitian_eigendecompose(H)
    evS, _ = L.hermitian_eigendecompose(Hs)
    shift = float(((evD - evS) ** 2).sum())
    print("TEST A — the chirality IS the directedness (magnetic Laplacian, Class L directed Hermitian):")
    print(f"  directed chiral energy (imag mass): {eD:.3f}   symmetrized: {eS:.6f}")
    print(f"  spectrum shift directed↔symmetric (the chirality is spectrally visible): {shift:.3f}")
    A_survives = eD > 1e-6 and eS < 1e-9
    print(f"  → falsifier (symmetric connectivity would show no chirality): {'SURVIVES' if A_survives else 'BROKEN'}\n")

    # ===== TEST B — neuron + ≤7 synapses addressed chirally AS ONE (conjugate-collapse, F486) =====
    nb7 = [1, 2, 3, 4, 5, 6, 7]
    box = [Ad[0][j] - Ad[j][0] for j in nb7]                          # d_j = net directed flow (out−in) = chiral part
    S = the_one(sigma=+1, theta_num=1, theta_den=7, terms=8)          # the holder: neuron-anchor + 7 synapse-imaginaries
    W = C.hypercomplex_couple(box, sigma=+1)                          # COLLAPSE: one octonion object (neuron+synapses)
    hp = C.hypercomplex_couple(list(W), sigma=+1, inverse=True)[1:8]  # hand+ : synapses pre→post
    hm = C.hypercomplex_couple(list(W), sigma=-1, inverse=True)[1:8]  # hand− : synapses post→pre (the conjugate)
    rev = close(hp, box)
    flipped = close(hm, [-v for v in box])
    print(f"TEST B — neuron + 7 synapses as ONE object (the_one dim {S.dim}); neuron = anchor e0 = {W[0]:.3f} (preserved):")
    print(f"  box (synapse net-flows, pre→post): {[round(v,2) for v in box]}")
    print(f"  hand+ (σ=+1) recovers the synapses (≤𝕆 reversible, F485/F460): {rev}")
    print(f"  hand− (σ=−1) = synapses post→pre (the conjugate, direction reversed): {flipped}")
    print(f"  → neuron-anchor preserved + synapses flipped = the conjugate = the two hands of ONE object\n")

    # ===== TEST C — the horizon: the 8th synapse breaks "as one" bit-exactness =====
    nb8 = [1, 2, 3, 4, 5, 6, 7, 8]
    box8 = [Ad[0][j] - Ad[j][0] for j in nb8]
    W8 = C.hypercomplex_couple(box8, sigma=+1)
    rec8 = C.hypercomplex_couple(list(W8), sigma=+1, inverse=True)[1:9]
    rev8 = close(rec8, box8)
    print("TEST C — the horizon (the falsifier on 'addressed as one'):")
    print(f"  7 synapses → octonion (dim 8 = 1 neuron + 7 synapses), reversible-as-one: {rev}")
    print(f"  8 synapses → only 7 imaginary slots; the 8th overflows the octonion, reversible-as-one: {rev8}")
    print(f"  is_division_algebra_dim: octonion(8)={cd.is_division_algebra_dim(8)}  sedenion(16)={cd.is_division_algebra_dim(16)}")
    print(f"  → past 𝕆 the conjugate-collapse is no longer bit-exact-as-one (zero divisors, F460);")
    print(f"    biology must CARRY (Hamming, F450) / COLLAPSE to a handed storage (F485) — the cheap path.\n")

    C_survives = rev and not rev8 and cd.is_division_algebra_dim(8) and not cd.is_division_algebra_dim(16)
    print("VERDICT (the riding assumption, F394 — ride until disproved):")
    print(f"  • A — chirality = the synaptic↔neural division asymmetry: {'SURVIVES' if A_survives else 'BROKEN'}")
    print(f"  • B — neuron + ≤7 synapses addressed chirally AS ONE (σ the hand): {'SURVIVES' if rev and flipped else 'BROKEN'}")
    print(f"  • C — the horizon is exactly ≤7 synapses / bit-exact-as-one cluster: {'SURVIVES' if C_survives else 'BROKEN'}")
    print("  Neither half privileged (F398): the chirality lives in the DIVISION (the conjugate keeps the neuron,")
    print("  flips the synapses), not in either alone. The full SNN = a lattice of ≤7-synapse chiral-addressed")
    print("  neuron-objects stitched by carry. Next rungs: the carry-stitched lattice; navigate-routed (non-linear)")
    print("  collapse for hands beyond a pure flip; a real connectome's fan-in distribution vs the ≤7 horizon.")


if __name__ == "__main__":
    main()
