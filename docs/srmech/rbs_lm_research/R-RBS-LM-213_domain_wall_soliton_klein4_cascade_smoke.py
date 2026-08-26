"""R-RBS-LM-213 — Composite-soliton (Z2)^n SSB cascade as an A-N cascade (FORM-reading demo).

srmech-native demonstration backing Finding 213. A *structure* (form) reading of an
ESTABLISHED field-theory result in A-N / cascade vocabulary -- NOT a claim about
field theory and NOT a derivation. The physics is published (Eto, Hamada & Nitta,
arXiv:2304.14143; phi^4 kink spectrum standard, arXiv:1205.3069 + Manton-Sutcliffe);
here we show the three structural pieces are GENUINE srmech primitives, and the
LOAD-BEARING claim is bit-exact:

  LOAD-BEARING  the soliton-cascade's MIDDLE rung (Z2)^2 IS Klein-4 = Z2 x Z2.
      We read the per-element Klein-4 multiplication straight off srmech's
      hdc.klein4_bind (component-wise (F2)^2-XOR) and show, bit-exact, that it
      reproduces the Z2 x Z2 Cayley table: abelian, associative, identity 0,
      EVERY non-identity element order EXACTLY 2 (the Klein-four signature that
      separates it from cyclic C4), and the two Z2 generators are exactly the
      two chirality axes gamma5 (mask 2) and iomega7 (mask 1) whose product is
      the CPT element 3. This is the (Z2)^2 of the SSB ladder, element for
      element, in the corpus's own Klein-4 sector algebra (F132/F200/F206).

  (a) each Z2-breaking in (Z2)^3 -> (Z2)^2 -> Z2 -> 1 = a Class-K pin-slot LATCH:
      a vacuum committing to one sign of a scalar field that had a +/- choice.
      srmech.amsc.cascade.pin_slot_at_zero(phi) -> (orientation, magnitude);
      orientation is +1 / 0-at-the-wall / -1 -- a field zero that latches a vacuum.

  (b) the domain-wall handedness / orientation (kink vs antikink, topological
      charge +/-1) = Class-C. srmech.amsc.cascade.net_chirality /
      srmech.amsc.cascade.reorient (Class C). A wall + antiwall (charge +1, -1)
      net to zero (annihilation-allowed); two like walls net to +1 (a stacked
      composite). [The TOTAL topological charge across the chain is the Class-C
      net handedness; sign-handling is Class K + Class C, never python abs().]

  (c) the wall's bound-state / fluctuation spectrum = Class-L. The phi^4 kink's
      second-order fluctuation operator is the Poschl-Teller Schrodinger operator
      -d^2/dx^2 + 4 - 6 sech^2(x) (standard; arXiv:1205.3069), whose DISCRETE
      spectrum contains a ZERO MODE (the translational Goldstone of the broken
      translation symmetry) and a bound shape mode. We discretize it to a
      symmetric tridiagonal operator and take its spectrum via the NATIVE Class-L
      Jacobi eigensolver -- the lowest eigenvalue sits at ~0 (the zero mode).

NO python primitives: no abs() (-> cascade.pin_slot_at_zero/magnitude),
no np.linalg.eig (-> laplacian.jacobi_eigvals), no hashlib.sha256.
Run:  <venv>/bin/python3 R-RBS-LM-213_domain_wall_soliton_klein4_cascade_smoke.py
Gate: <venv>/bin/python3 check_srmech_discipline.py R-RBS-LM-213_*.py  (expect 0 HARD)
"""
import itertools
import json
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.cascade import pin_slot_at_zero, reorient, net_chirality, magnitude
from srmech.amsc.hdc import (
    KLEIN4_STATES,
    klein4_bind,
    klein4_chirality_flip_gamma5,
    klein4_chirality_flip_omega7,
    klein4_cpt_mirror,
)
from srmech.amsc.laplacian import jacobi_eigvals, symmetric_eigendecompose

HERE = Path(__file__).parent


def _single(val):
    """A length-1 Klein-4 hypervector holding one sector value, so klein4_bind
    reads out the GROUP multiplication element-for-element (bit-exact)."""
    return np.array([val], dtype=np.int64)


def load_bearing_middle_rung_is_klein4():
    """LOAD-BEARING: the (Z2)^2 middle rung IS Klein-4 = Z2 x Z2, bit-exact.

    Read the Klein-4 group multiplication straight off srmech's klein4_bind and
    show it is, element for element, the Z2 x Z2 Cayley table -- the (Z2)^2 of the
    composite-soliton SSB ladder, in the corpus's own sector algebra.
    """
    states = list(KLEIN4_STATES)  # (0, 1, 2, 3)

    # Cayley table from srmech klein4_bind (component-wise (F2)^2-XOR)
    cayley = {}
    for a, b in itertools.product(states, states):
        cayley[(a, b)] = int(klein4_bind(_single(a), _single(b))[0])

    # Reference Z2 x Z2 = (F2)^2 XOR (integer XOR on 2-bit sector ints)
    ref_xor_match = all(cayley[(a, b)] == (a ^ b)
                        for a, b in itertools.product(states, states))

    # Group axioms, read off the table (bit-exact)
    identity = next(e for e in states if all(cayley[(e, b)] == b for b in states))
    self_inverse = {a: cayley[(a, a)] for a in states}
    abelian = all(cayley[(a, b)] == cayley[(b, a)]
                  for a, b in itertools.product(states, states))
    associative = all(
        cayley[(cayley[(a, b)], c)] == cayley[(a, cayley[(b, c)])]
        for a, b, c in itertools.product(states, states, states)
    )
    # The Klein-four discriminator: EVERY non-identity element has order EXACTLY 2
    # (this is what separates V = Z2 x Z2 from the cyclic group C4, which has
    # order-4 elements). F200's "no order-3 element" is the order-2-vs-order-3
    # cousin of this same fact.
    every_nonid_order_exactly_2 = all(
        self_inverse[a] == identity and a != identity
        for a in states if a != identity
    )
    has_order4_element = any(  # must be False for Klein-4 (True only for C4)
        cayley[(cayley[(cayley[(a, a)], a)], a)] == identity
        and cayley[(a, a)] != identity
        for a in states
    )

    # The two Z2 generators = the two chirality axes; their product = CPT.
    g5 = int(klein4_chirality_flip_gamma5(_single(0))[0])   # expect 2 (bit-1 mask)
    w7 = int(klein4_chirality_flip_omega7(_single(0))[0])   # expect 1 (bit-0 mask)
    cpt = int(klein4_cpt_mirror(_single(0))[0])             # expect 3 (both)
    direct_product = (cayley[(g5, w7)] == cpt)              # gamma5 * iomega7 = CPT

    is_klein4 = bool(
        ref_xor_match and abelian and associative and identity == 0
        and every_nonid_order_exactly_2 and not has_order4_element
        and g5 == 2 and w7 == 1 and cpt == 3 and direct_product
    )

    return {
        "claim": "(Z2)^2 middle rung == Klein-4 == Z2 x Z2, bit-exact via klein4_bind",
        "cayley_rows": [[cayley[(a, b)] for b in states] for a in states],
        "klein4_bind_equals_F2sq_XOR": ref_xor_match,
        "identity_element": identity,
        "a_times_a_for_each": self_inverse,
        "abelian": abelian,
        "associative": associative,
        "every_nonidentity_element_order_exactly_2": every_nonid_order_exactly_2,
        "has_order4_element_must_be_false_for_klein4": has_order4_element,
        "gamma5_generator_mask": g5,
        "omega7_generator_mask": w7,
        "cpt_element": cpt,
        "gamma5_times_omega7_equals_cpt": direct_product,
        "MIDDLE_RUNG_IS_KLEIN4": is_klein4,
    }


def part_a_each_z2_breaking_is_class_k_latch():
    """(a) each SSB step in (Z2)^3 -> (Z2)^2 -> Z2 -> 1 = a Class-K pin-slot LATCH.

    At each rung a scalar field that HAD a discrete +/- choice commits to one sign
    in the vacuum. The order field phi(x) sweeps across the wall: it is +v on one
    side, 0 AT the wall (the field zero -- the wall sits on the unstable maximum),
    -v on the other. Class-K pin_slot_at_zero(phi) returns orientation +1 / 0 / -1,
    i.e. the wall is the latch point of the vacuum's sign choice. Each of the three
    nested walls (mother / daughter / granddaughter) is one such latch.
    """
    rungs = [
        ("rung1_mother_wall_(Z2)^3->(Z2)^2", "domain wall (O(N) -> O(N-1) ESB)"),
        ("rung2_daughter_wall_(Z2)^2->Z2", "string-as-wall-inside-mother-wall"),
        ("rung3_granddaughter_(Z2)->1", "monopole-as-kink-inside-daughter"),
    ]
    # the SAME normalized order-field profile across any wall: +v ... 0 ... -v
    phi_profile = [1.0, 0.5, 0.0, -0.5, -1.0]
    out = {}
    for tag, descr in rungs:
        orientations = []
        latched_at_index = None
        for i, phi in enumerate(phi_profile):
            orient, mag = pin_slot_at_zero(phi)  # Class K pin-slot at zero
            orientations.append(orient)
            if orient == 0 and latched_at_index is None:
                latched_at_index = i  # the field zero == the wall == the latch
        out[tag] = {
            "soliton": descr,
            "phi_profile": phi_profile,
            "orientation_sequence": orientations,   # +1 ... 0 ... -1
            "latched_at_index": latched_at_index,
            "is_latched_vacuum_choice": (
                1 in orientations and -1 in orientations and 0 in orientations
            ),
        }
    return out


def part_b_wall_handedness_is_class_c():
    """(b) domain-wall handedness (kink vs antikink, topological charge +/-1) = Class-C.

    A kink carries topological charge +1, an antikink -1 (the wall's orientation /
    which-way; Manton-Sutcliffe). The TOTAL topological charge of a multi-wall
    composite is the Class-C net handedness of the per-wall orientations. A
    wall+antiwall pair (+1, -1) nets to -1*... product -> -1 here is the *parity*;
    we report BOTH the multiplicative net handedness (Class C net_chirality, a
    parity) and the additive total charge (signed sum via Class-K/Class-C, never
    abs()). Re-applying a wall's captured orientation to a tension increment is
    cascade.reorient (Class C).
    """
    # Three nested walls of the generic (Z2)^3 composite, all same handedness
    # (a coherently-stacked mother/daughter/granddaughter): charges +1, +1, +1
    nested_charges = [1, 1, 1]
    net_handedness_nested = net_chirality(nested_charges)  # Class C: product (parity)

    # A wall + antiwall (kink + antikink): charges +1, -1 -> opposite handedness,
    # annihilation-allowed. Net parity = product = -1; additive total charge = 0.
    pair_charges = [1, -1]
    net_handedness_pair = net_chirality(pair_charges)      # Class C parity = -1

    # additive total topological charge WITHOUT python abs(): re-apply each
    # orientation to a unit charge magnitude via Class-C reorient, then signed-sum.
    unit = 1.0
    nested_total_charge = float(np.sum([reorient(o, unit) for o in nested_charges]))
    pair_total_charge = float(np.sum([reorient(o, unit) for o in pair_charges]))

    return {
        "nested_wall_charges": nested_charges,
        "nested_net_handedness_classC_parity": net_handedness_nested,   # +1
        "nested_total_topological_charge": nested_total_charge,         # +3
        "wall_antiwall_charges": pair_charges,
        "wall_antiwall_net_handedness_classC_parity": net_handedness_pair,  # -1
        "wall_antiwall_total_topological_charge": pair_total_charge,    # 0 (annihilation-allowed)
        # Class K magnitude (NOT abs): the pair's total charge magnitude is 0,
        # the nested triple's is 3 -- chirality distinguishes them.
        "chirality_distinguishes_composites": (
            magnitude(nested_total_charge - pair_total_charge) > 1e-9
        ),
    }


def part_c_kink_fluctuation_spectrum_is_class_l():
    """(c) the wall's bound-state / fluctuation spectrum = Class-L spectral object.

    The phi^4 kink's second-order fluctuation operator is the Poschl-Teller
    Schrodinger operator  H = -d^2/dx^2 + 4 - 6 sech^2(x)  (standard result;
    arXiv:1205.3069 Alonso-Izquierdo & Mateos-Guilarte; Manton-Sutcliffe).
    Its DISCRETE spectrum has a ZERO MODE (eigenvalue ~0 -- the translational
    Goldstone mode from the broken translation invariance that the wall creates)
    and a bound 'shape' mode (eigenvalue 3) below the continuum (>= 4). We
    discretize H to a symmetric tridiagonal operator and take its spectrum via
    the NATIVE Class-L Jacobi eigensolver. The point is structural: the wall
    PUBLISHES its bound-state structure as a Class-L (eigenvalue) object, the way
    every srmech storage substrate publishes its signature as a Laplacian/
    Hermitian eigenspectrum. Bit-exact, no np.linalg.eig.
    """
    n = 160
    L = 12.0
    x = np.linspace(-L, L, n)
    dx = float(x[1] - x[0])
    # phi^4 kink fluctuation potential (the V0=4 asymptote, 6 sech^2 well)
    V = 4.0 - 6.0 / np.cosh(x) ** 2

    # symmetric tridiagonal H = -d2/dx2 + V (finite-difference Laplacian + V)
    H = np.zeros((n, n), dtype=float)
    inv_dx2 = 1.0 / (dx * dx)
    for i in range(n):
        H[i, i] = 2.0 * inv_dx2 + V[i]
        if i + 1 < n:
            H[i, i + 1] = -inv_dx2
            H[i + 1, i] = -inv_dx2

    # Class L spectral decomposition -- NATIVE Jacobi (no np.linalg.eig)
    eigvals = jacobi_eigvals(H)  # ndarray, ascending
    eigvals_sorted = np.sort(np.asarray(eigvals))

    # cross-check the SAME native module reconstructs H (bit-exact)
    vals2, vecs = symmetric_eigendecompose(H)
    recon = vecs @ np.diag(vals2) @ vecs.T
    recon_max_err = float(np.max(np.abs(recon - H)))

    lowest = float(eigvals_sorted[0])
    # the analytic Poschl-Teller bound spectrum is {0, 3}; the zero mode is the
    # Goldstone of broken translation. magnitude() (Class K), not abs().
    zero_mode_present = bool(magnitude(lowest) < 0.05)  # ~0 within FD discretization
    return {
        "operator": "phi^4 kink fluctuation: -d^2/dx^2 + 4 - 6 sech^2(x) (Poschl-Teller)",
        "n_grid": int(n),
        "lowest_6_eigenvalues": [float(v) for v in eigvals_sorted[:6]],
        "lowest_eigenvalue": lowest,
        "zero_mode_present_translational_goldstone": zero_mode_present,
        "analytic_bound_spectrum": [0.0, 3.0],
        "continuum_threshold": 4.0,
        "spectrum_is_discrete_below_continuum": bool(
            len(set(np.round(eigvals_sorted[eigvals_sorted < 4.0 - 1e-6], 6))) >= 1
        ),
        "native_recon_max_abs_err": recon_max_err,  # ~machine eps -> bit-exact
        "class_L_native": True,
    }


def main():
    records = []

    load_bearing = load_bearing_middle_rung_is_klein4()
    records.append({"record": "load_bearing_middle_rung_is_klein4", **load_bearing})

    a = part_a_each_z2_breaking_is_class_k_latch()
    records.append({"record": "a_each_z2_breaking_is_class_K_latch", "rungs": a})

    b = part_b_wall_handedness_is_class_c()
    records.append({"record": "b_wall_handedness_is_class_C", **b})

    c = part_c_kink_fluctuation_spectrum_is_class_l()
    records.append({"record": "c_kink_fluctuation_spectrum_is_class_L", **c})

    header = {
        "record": "attestation",
        "script": "R-RBS-LM-213_domain_wall_soliton_klein4_cascade_smoke.py",
        "finding": "R-RBS-LM-FINDING_213",
        "srmech_version": srmech.__version__,
        "reading": "FORM-reading of established field-theory physics (composite "
                   "(Z2)^n soliton SSB cascade) in A-N / Klein-4 vocabulary; "
                   "NOT a field-theory claim, NOT a derivation.",
        "ssb_ladder": "(Z2)^3 -> (Z2)^2 -> Z2 -> 1",
        "load_bearing_claim_held": load_bearing["MIDDLE_RUNG_IS_KLEIN4"],
        "sources": [
            "Eto, Hamada & Nitta, arXiv:2304.14143 (the (Z2)^n composite-soliton SSB cascade)",
            "Alonso-Izquierdo & Mateos-Guilarte, arXiv:1205.3069 / Ann. Phys. 327 (2012) 2251 "
            "(phi^4 kink Poschl-Teller fluctuation operator)",
            "Manton & Sutcliffe, Topological Solitons, CUP 2004 (kink charge +/-1, fluctuation spectrum)",
            "Vilenkin & Shellard, Cosmic Strings and Other Topological Defects, CUP 1994 (domain-wall SSB)",
        ],
    }

    out_records = [header] + records
    out_path = HERE / "R-RBS-LM-213_results.ndjson"
    with open(out_path, "w") as fh:
        for rec in out_records:
            fh.write(json.dumps(rec) + "\n")

    # human-readable echo
    print(json.dumps({"attestation": header, "records": records}, indent=2))
    print("\nLOAD-BEARING (Z2)^2 == Klein-4 held:", load_bearing["MIDDLE_RUNG_IS_KLEIN4"])
    print("wrote", out_path.name)


if __name__ == "__main__":
    main()
