#!/usr/bin/env python3
"""R-RBS-LM-220 — Does a COMPLETE A-N ISA need a 7th, order-3 "triality" opcode
(qm.triality), distinct from the 6 order-2 lean atoms — OR is triality COMPOSABLE
from the 6 (which would FALSIFY F219 sec3)?

This sharpens F219 sec3's claim. F219 said "bit-dancing composes Z2's into (Z2)^n,
which has only order-1 and order-2 elements — no order-3, ever". F215 showed the 6
lean atoms ARE the Klein-4 regular rep (permutation matrices) + sign ops + parity map.

The honest group-theory caveat F219 GLOSSED: order-2 generators that DON'T commute CAN
make an order-3 element (e.g. two transpositions in S3 multiply to a 3-cycle). The "no
order-3" claim is AUTOMATIC only for the ABELIAN (Z2)^n. So the whole finding turns on:
ARE THE 6 LEAN ATOMS, AS OPERATORS, A 2-GROUP? -- exactly what this script computes,
bit-exact, by generating their matrix group under closure.

  Step 1. Reconstruct the 6 atoms as the EXACT matrices F215 used:
            * K4BIND, K4FLIP  = Klein-4 regular rep (4x4 permutation matrices,
              klein4_bind = XOR confirmed; flips = the 3 sector involutions).
            * SGNTEST/SGNAPPLY/MAG = the sign Z2 = diag(+/-1) on a 1-dim line.
            * PARRED (net_chirality) = product/parity of +/-1 -> also the sign Z2.
          Carrier: the Klein-4 sector (4-dim regular rep of Z2 x Z2) (+) a signed line
          (1-dim, the +/-1 sign group). The combined faithful carrier is 4 (+) 1 = 5-dim
          block-diagonal (and we ALSO compute the 4-dim Klein-4 part alone, since the
          sign ops are a separate Z2 factor that trivially cannot add order-3).

  Step 2. Compute the GROUP they generate under matrix product (bounded BFS closure).
          Report |G|. srmech-native: sign-folding via cascade.magnitude (Class K, never
          abs()); equality via exact integer matrices (permutation + diag(+/-1) are
          integer, so closure is EXACT -- no float tolerance needed).

  Step 3. Bit-exact:
            (a) is G ABELIAN?
            (b) does G contain ANY order-3 element (g^3=I, g!=I, g^2!=I)?
            (c) is the order-3 triality operator (qm.triality_automorphism, tau^3=I)
                in / reachable from G? (carrier-dimension argument: tau is 28x28,
                Fix(tau)=g2 dim 14; the lean carrier is 5-dim -- different rep.)

  PRE-STATED OUTCOMES (decided BEFORE running; nulls/falsifications COUNT):
    * CONFIRMS F219: the atoms generate a 2-GROUP (every element order a power of 2;
      NO order-3) -> triality is a GENUINE separate 7th order-3 primitive the ISA needs;
      F219 sec3 holds, now RIGOROUSLY, and for the RIGHT reason ("the permutation part is
      a 2-group / signs only add order-2 factors", NOT loosely "product of Z2's").
    * FALSIFIES/REFINES F219: the atoms are NON-ABELIAN and generate an order-3 element /
      reach triality -> triality is composable from the 6; F219 sec3 was TOO STRONG ->
      say so plainly and propose the corrected statement.

srmech-native throughout:
  - klein4_bind / klein4_chirality_flip_* : srmech.amsc.hdc  (the EXACT atom semantics)
  - cascade sign ops                      : srmech.amsc.cascade.{pin_slot_at_zero,
                                            reorient, net_chirality, magnitude}
  - triality order-3 operator             : srmech.qm.triality.triality_automorphism
  - sign-folding / magnitude              : srmech.amsc.cascade.magnitude (Class K; no abs())
  - any spectral rank (diagnostic only)   : srmech.amsc.laplacian.* (NOT np.linalg.eig)

CAD/VLSI/fab ban holds (no chip, no transistor counts). PR #687 STAYS DRAFT.

Citation for triality/octonion order-3: John C. Baez, "The Octonions", Bull. Amer.
Math. Soc. 39 (2002) 145-205, arXiv:math/0105155 (sec 2.4: Out(Spin(8)) = S3, the
order-3 outer automorphism). Author/title/arXiv-ID verified against the srmech
triality_automorphism docstring SSoT, which cites Baez (2002) sec2.4 + Cartan (1925).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np

from srmech.amsc import cascade, hdc, laplacian
from srmech.qm import triality

RECORDS = []


def emit(kind, **payload):
    RECORDS.append({"r": "R-RBS-LM-220", "kind": kind, **payload})


def max_magnitude(arr):
    """Max element-magnitude via Class-K cascade.magnitude (NEVER abs()/np.abs)."""
    flat = np.asarray(arr, dtype=float).reshape(-1)
    m = 0.0
    for x in flat:
        mag = cascade.magnitude(float(x))  # Class K modulus-fold, not abs()
        if mag > m:
            m = mag
    return m


# ===========================================================================
# Step 1. Reconstruct the 6 lean atoms as the EXACT matrices F215 used.
# ===========================================================================
# These are INTEGER matrices (permutations + diag(+/-1)), so the group closure is
# EXACT -- we key elements by their integer-tuple, no float tolerance in the group law.

# --- Klein-4 sector carrier: the regular rep of Z2 x Z2 (4x4 permutation matrices) ---
# Element g in {0,1,2,3} (2-bit sector tag gamma5 x iomega7). Left-mult by g is the
# permutation x -> g XOR x.  klein4_bind IS bitwise XOR (F215/F208 confirmed).
def klein4_left_mult(g):
    """4x4 permutation matrix: the regular-rep action x -> klein4_bind(g, x) = g XOR x."""
    P = np.zeros((4, 4), dtype=np.int64)
    for x in range(4):
        P[g ^ x, x] = 1  # XOR action == klein4_bind(g, x); the bind IS bitwise XOR
    return P


# Confirm klein4_bind == XOR over the 2-bit sector (so the regular rep is faithful).
_a = np.array([0, 1, 2, 3, 0, 1, 2, 3], dtype=np.int64)
_b = np.array([0, 0, 0, 0, 1, 2, 3, 1], dtype=np.int64)
_bind = np.asarray(hdc.klein4_bind(_a, _b))
_bind_is_xor = bool(np.array_equal(_bind, np.bitwise_xor(_a, _b)))
emit("klein4_bind_is_xor", confirmed=_bind_is_xor,
     note="K4BIND = bitwise XOR on the 2-bit sector (Klein-4 group op); regular rep is faithful")

# Confirm the 3 flips ARE the Klein-4 involutions XOR-with-{01,10,11} (F215 used these as
# permutation matrices). We read the actual srmech semantics over sectors 0..3.
_flip_maps = {}
for name, fn in [("gamma5", hdc.klein4_chirality_flip_gamma5),
                 ("omega7", hdc.klein4_chirality_flip_omega7),
                 ("cpt", hdc.klein4_cpt_mirror)]:
    _flip_maps[name] = [int(np.asarray(fn(np.array([s])))[0]) for s in range(4)]
emit("klein4_flip_semantics", maps=_flip_maps,
     note="flip_gamma5 = XOR 0b10? read from srmech; each is a Klein-4 involution (an order-2 "
          "permutation) on the 2-bit sector -- a GROUP element of the regular rep")

# Map each flip to its XOR-constant g (so K4FLIP atoms are left_mult(g) permutation matrices).
def flip_to_xor_const(mapping):
    # mapping[x] = g XOR x  => g = mapping[0] (since 0 XOR g = g)
    g = mapping[0]
    # verify it is XOR-with-g for all x
    assert all(mapping[x] == (g ^ x) for x in range(4)), "flip is not XOR-with-constant"
    return g


_flip_consts = {n: flip_to_xor_const(m) for n, m in _flip_maps.items()}
emit("klein4_flip_xor_consts", consts=_flip_consts,
     note="each K4FLIP = left_mult(g) for g in {gamma5,omega7,cpt}; all order-2 permutations")

# K4BIND: binding by a NON-identity sector. The bind is parameterised by its operand;
# as a group GENERATOR the reachable set of left-mults is generated by the single-axis
# binds left_mult(0b01) and left_mult(0b10) (which also equal two of the flips). We take
# the FULL generating set of the Klein-4 regular rep: the two single-axis generators
# (this is exactly "K4BIND/K4FLIP imposing the Z2 x Z2 structure on the bit-pair", F219 sec2).
K4_GEN_CONSTS = [0b01, 0b10]  # the two Z2 generators of Klein-4 = Z2 x Z2
K4_GENERATORS = [klein4_left_mult(g) for g in K4_GEN_CONSTS]
# (left_mult(0b11) = left_mult(0b01) @ left_mult(0b10) is generated, = the CPT flip.)

# --- Sign carrier: the +/-1 sign group as diag(+/-1) on a 1-dim line ---
# SGNTEST (pin_slot_at_zero) extracts (sign, magnitude); SGNAPPLY (reorient) re-applies a
# captured +/-1; MAG (magnitude) clears the sign bit; PARRED (net_chirality) reduces a list
# of +/-1 to its product (parity). As a LINEAR OPERATOR on the signed line, the only
# non-trivial group element any of these produces is the sign flip s -> -s = diag(-1):
#   * SGNAPPLY(-1, .) = multiply by -1            -> diag(-1)   [order-2]
#   * SGNAPPLY(+1, .) = identity                  -> diag(+1)   [identity]
#   * MAG             = project to |.| (s -> +|s|)-> NOT invertible / NOT a group element
#                       (it is a fold, not a rotation; on the +/-1 ABSTRACT line its
#                        invertible-group content is exactly {+1} restricted, contributing
#                        no new group element beyond the sign Z2)
#   * SGNTEST/PARRED  = READ-OUT ops (sign bit / parity) -- they EMIT a +/-1, they do not
#                       act as a new linear operator on the carrier; the +/-1 they emit is
#                       fed to SGNAPPLY, whose group content is the sign Z2 (diag(+/-1)).
# So the sign atoms' GROUP content on the carrier is exactly the order-2 sign flip diag(-1).
SIGN_FLIP = np.array([[-1]], dtype=np.int64)   # diag(-1) -- the sign Z2 generator
SIGN_ID = np.array([[1]], dtype=np.int64)

# Confirm the srmech sign-atom semantics that justify "group content = sign Z2".
emit("sign_atom_semantics",
     pin_slot_at_zero_neg=cascade.pin_slot_at_zero(-3.5),      # (-1, 3.5): sign + magnitude
     reorient_neg=cascade.reorient(-1, 7.0),                   # -7.0: re-apply -1 = diag(-1)
     net_chirality=cascade.net_chirality([-1, 1, -1, -1]),     # -1: product/parity
     magnitude=cascade.magnitude(-3.5),                        # 3.5: clear sign bit (a fold)
     note="SGNAPPLY(reorient) realises the sign Z2 = diag(+/-1); SGNTEST/PARRED are read-outs "
          "that EMIT +/-1; MAG is a non-invertible fold -> the sign atoms' GROUP content on the "
          "signed line is exactly the order-2 sign flip diag(-1)")

# --- The combined faithful carrier: Klein-4 sector (4d) (+) signed line (1d) = 5d ---
def embed(P4, s1):
    """Block-diagonal embed: 4x4 Klein-4 permutation (+) 1x1 sign element -> 5x5 integer."""
    M = np.zeros((5, 5), dtype=np.int64)
    M[:4, :4] = P4
    M[4, 4] = s1[0, 0]
    return M


I4 = np.eye(4, dtype=np.int64)

# The full lean-atom generating set on the 5-dim carrier:
#   K4BIND/K4FLIP -> Klein-4 generators acting on the sector block (sign block = identity)
#   SGNAPPLY      -> sign flip acting on the sign block (sector block = identity)
GENERATORS_5D = []
gen_labels = []
for g, lab in zip(K4_GEN_CONSTS, ["K4_gen_axis1(0b01)", "K4_gen_axis2(0b10)"]):
    GENERATORS_5D.append(embed(klein4_left_mult(g), SIGN_ID))
    gen_labels.append(lab)
GENERATORS_5D.append(embed(I4, SIGN_FLIP))
gen_labels.append("SGNAPPLY(diag(-1))")

emit("generators", carrier="Klein-4 sector (4d regular rep of Z2xZ2) (+) signed line (1d) = 5d",
     n_generators=len(GENERATORS_5D), generator_labels=gen_labels,
     note="K4BIND/K4FLIP -> the two single-axis Klein-4 generators (Z2 x Z2) on the sector "
          "block; SGNAPPLY -> diag(-1) on the sign line. SGNTEST/PARRED/MAG add no NEW group "
          "element (read-outs + a non-invertible fold). All generators are integer + order-2.")


# ===========================================================================
# Step 2. Compute the group generated under matrix product (bounded BFS closure).
# ===========================================================================
def mat_key(M):
    """Exact integer hash key for a matrix (permutation + diag(+/-1) are integer)."""
    return tuple(int(x) for x in M.reshape(-1))


def generate_group(generators, dim, cap=100000):
    """BFS closure of the matrix group generated by `generators` (and the identity).

    Integer matrices -> exact equality (no tolerance). Returns the list of group elements.
    Bounded by `cap` (the lean group is tiny; cap is a safety bound only).
    """
    I = np.eye(dim, dtype=np.int64)
    seen = {mat_key(I): I}
    frontier = [I]
    while frontier:
        new_frontier = []
        for M in frontier:
            for G in generators:
                P = (M @ G) % 0 if False else (M @ G)  # exact integer matmul
                k = mat_key(P)
                if k not in seen:
                    seen[k] = P
                    new_frontier.append(P)
                    if len(seen) > cap:
                        raise RuntimeError("group exceeded cap -- not finite as expected")
        frontier = new_frontier
    return list(seen.values())


# Group generated by the FULL lean-6 (5d carrier):
G_full = generate_group(GENERATORS_5D, 5)
emit("group_order_full", order=len(G_full),
     note="|G| generated by K4BIND/K4FLIP (Klein-4) + SGNAPPLY (sign Z2) on the 5d carrier")

# Group generated by the Klein-4 part ALONE (4d carrier), for clarity:
G_k4 = generate_group(K4_GENERATORS, 4)
emit("group_order_klein4_only", order=len(G_k4),
     note="|G| of the Klein-4 sector part alone (should be 4 = Z2 x Z2)")


# ===========================================================================
# Step 3. Bit-exact tests on the generated group G_full.
# ===========================================================================
I5 = np.eye(5, dtype=np.int64)


def is_identity(M):
    return mat_key(M) == mat_key(I5)


# (a) ABELIAN? -- every pair of generators (hence elements) commutes?
abelian = True
max_commutator = 0
for i in range(len(G_full)):
    for j in range(i + 1, len(G_full)):
        A, B = G_full[i], G_full[j]
        comm = A @ B - B @ A
        mc = max_magnitude(comm)        # Class-K magnitude, never abs()
        if mc > max_commutator:
            max_commutator = mc
        if mc > 0:
            abelian = False
emit("group_abelian", abelian=bool(abelian), max_commutator_magnitude=float(max_commutator),
     note="ABELIAN iff every pair commutes (max commutator magnitude == 0)")

# (b) ANY order-3 element? g^3 = I, g != I, g^2 != I.  Also tabulate the full ORDER SPECTRUM.
def element_order(M, max_order=64):
    P = M.copy()
    for k in range(1, max_order + 1):
        if is_identity(P):
            return k
        P = P @ M
    return None  # > max_order (would indicate non-finite; shouldn't happen)


order_spectrum = {}
order3_elements = 0
for M in G_full:
    o = element_order(M)
    order_spectrum[o] = order_spectrum.get(o, 0) + 1
    if o == 3:
        order3_elements += 1

# Every order a power of 2 ?  (i.e. is it a 2-GROUP)
def is_pow2(n):
    return n is not None and n >= 1 and (n & (n - 1)) == 0  # 1,2,4,8,... ; 1 = 2^0


all_orders_pow2 = all(is_pow2(o) for o in order_spectrum)
emit("group_order_spectrum",
     order_spectrum={str(k): v for k, v in sorted(order_spectrum.items(), key=lambda kv: (kv[0] is None, kv[0]))},
     n_order3_elements=order3_elements,
     every_element_order_is_power_of_2=bool(all_orders_pow2),
     is_2_group=bool(all_orders_pow2),
     note="a 2-GROUP has every element order a power of 2 (no order-3). The RIGHT reason for "
          "'no order-3' is THIS (the group is a 2-group), not loosely 'product of Z2's'.")

# (c) Is the order-3 triality operator IN / reachable from G_full?
tau = np.asarray(triality.triality_automorphism(), dtype=float)
I28 = np.eye(28)
tau2 = tau @ tau
tau3 = tau2 @ tau
tau_is_order3 = (max_magnitude(tau3 - I28) < 1e-9
                 and max_magnitude(tau2 - I28) > 1e-9
                 and max_magnitude(tau - I28) > 1e-9)
emit("triality_operator_order3_confirm",
     tau_shape=list(tau.shape),
     tau_cubed_is_identity=bool(max_magnitude(tau3 - I28) < 1e-9),
     tau_squared_is_identity=bool(max_magnitude(tau2 - I28) < 1e-9),
     tau_is_identity=bool(max_magnitude(tau - I28) < 1e-9),
     tau_is_genuine_order3=bool(tau_is_order3),
     note="qm.triality_automorphism: 28x28, tau^3=I, tau^2!=I, tau!=I (Baez 2002 sec2.4, "
          "Out(Spin(8))=S3); Fix(tau)=g2 dim 14")

# Reachability is decided on TWO grounds, both DEMONSTRATED:
#   (1) CARRIER DIMENSION: tau is a 28x28 operator; the lean group lives on a 5-dim carrier.
#       They are operators on DIFFERENT representation spaces -- tau is simply not an element
#       of GL(5) at all, so it cannot literally be in G_full.
#   (2) ORDER OBSTRUCTION: even abstractly (independent of carrier dim), if G_full is a
#       2-group it has NO order-3 element, so NO homomorphic image / subgroup of G_full can
#       BE the order-3 cyclic group <tau> = Z3. An order-3 element is not a product of
#       order-2 ones inside a 2-group: |Z3| = 3 does not divide any power of 2 (Lagrange).
triality_reachable = (not all_orders_pow2)  # reachable ONLY if G_full is NOT a 2-group
emit("triality_reachable_from_lean6",
     carrier_dim_lean=5, carrier_dim_triality=28,
     lean_group_is_2_group=bool(all_orders_pow2),
     triality_reachable=bool(triality_reachable),
     reasons=["carrier-dim mismatch: tau in GL(28), lean group in GL(5) (different rep)",
              "order obstruction: a 2-group has no order-3 element; 3 does not divide 2^k "
              "(Lagrange) -- no subgroup/quotient of a 2-group is Z3 = <tau>"],
     note="triality is reachable from the lean-6 ONLY if the lean group is NOT a 2-group")


# ===========================================================================
# VERDICT
# ===========================================================================
confirms_f219 = bool(all_orders_pow2 and order3_elements == 0 and not triality_reachable)
emit("VERDICT",
     group_order=len(G_full),
     abelian=bool(abelian),
     order3_present=bool(order3_elements > 0),
     is_2_group=bool(all_orders_pow2),
     triality_reachable=bool(triality_reachable),
     CONFIRMS_F219=confirms_f219,
     verdict=(
         "CONFIRMS F219 sec3 (now RIGOROUS): the 6 lean atoms generate a 2-GROUP "
         f"(|G|={len(G_full)}, order spectrum all powers of 2, ZERO order-3 elements). "
         "Triality (qm.triality, tau^3=I) is a GENUINE separate 7th order-3 primitive the "
         "complete A-N ISA needs -- it is the ONLY way to the 3rd chiral axis, NOT composable "
         "from the 6 order-2 atoms. The RIGHT reason is 'the lean group is a 2-group' (the "
         "permutation part is the Klein-4 2-group; the sign ops add only an order-2 factor), "
         "NOT the loose 'product of Z2's'. The honest caveat (non-commuting order-2 gens CAN "
         "make order-3, e.g. two transpositions -> a 3-cycle in S3) is CHECKED and does NOT "
         "apply here: the lean generators commute / their group is a 2-group, so no order-3 "
         "arises."
         if confirms_f219 else
         "FALSIFIES/REFINES F219 sec3: the 6 lean atoms are NON-ABELIAN and generate an "
         f"order-3 element (|G|={len(G_full)}; order spectrum {sorted(order_spectrum)}). "
         "Triality is COMPOSABLE from the 6 -- F219 sec3's 'no order-3 by composition' was "
         "TOO STRONG. Corrected statement: the lean group is NOT a 2-group; an order-3 chiral "
         "axis IS reachable by composing the (non-commuting) order-2 atoms."))


# ---------------------------------------------------------------------------
# Write NDJSON
# ---------------------------------------------------------------------------
def main():
    ts = datetime.now(timezone.utc).isoformat()
    out_path = __file__.rsplit("/", 1)[0] + "/R-RBS-LM-220_results.ndjson"
    with open(out_path, "w") as fh:
        fh.write(json.dumps({"r": "R-RBS-LM-220", "kind": "_meta", "generated_at": ts,
                             "srmech_surfaces": ["amsc.hdc.klein4_bind",
                                                 "amsc.hdc.klein4_chirality_flip_*",
                                                 "amsc.cascade.{pin_slot_at_zero,reorient,"
                                                 "net_chirality,magnitude}",
                                                 "qm.triality.triality_automorphism",
                                                 "amsc.laplacian.* (diagnostic)"]}) + "\n")
        for rec in RECORDS:
            fh.write(json.dumps(rec, default=str) + "\n")

    print("=" * 74)
    print("R-RBS-LM-220  lean-6 group closure  vs  order-3 triality opcode")
    print("=" * 74)
    print(f"klein4_bind == XOR (regular rep faithful): {_bind_is_xor}")
    print(f"carrier: Klein-4 sector (4d) (+) signed line (1d) = 5d block-diagonal")
    print(f"|G| (full lean-6, 5d): {len(G_full)}    |G_klein4 only|: {len(G_k4)}")
    print(f"(a) abelian?            {abelian}   (max commutator magnitude {max_commutator})")
    spectrum_str = ", ".join(f"order{ k}:{v}" for k, v in sorted(order_spectrum.items(),
                             key=lambda kv: (kv[0] is None, kv[0])))
    print(f"(b) order spectrum:     {{{spectrum_str}}}")
    print(f"    order-3 elements:   {order3_elements}    is-2-group (all orders 2^k): {all_orders_pow2}")
    print(f"(c) triality tau:       28x28, tau^3=I & tau^2!=I & tau!=I = {tau_is_order3}")
    print(f"    triality reachable from lean-6: {triality_reachable}  "
          f"(carrier 5 vs 28; order obstruction)")
    print("-" * 74)
    if confirms_f219:
        print("VERDICT: CONFIRMS F219 sec3 (now RIGOROUS). The lean-6 are a 2-GROUP; ZERO")
        print("         order-3 elements. Triality (qm.triality, tau^3=I) is a GENUINE separate")
        print("         7th ORDER-3 primitive the complete A-N ISA needs -- the only way to the")
        print("         3rd chiral axis, NOT composable from the 6 order-2 atoms. Right reason:")
        print("         the lean group is a 2-group (3 does not divide 2^k, Lagrange).")
    else:
        print("VERDICT: FALSIFIES/REFINES F219 sec3. The lean-6 generate an order-3 element;")
        print("         triality IS composable. F219 sec3 was too strong; corrected above.")
    print(f"NDJSON -> {out_path}")


if __name__ == "__main__":
    main()
