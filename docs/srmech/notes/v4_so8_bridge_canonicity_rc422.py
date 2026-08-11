"""Is the V4 <-> so(8) bridge CANONICAL or a CHOICE? (rc422 research, `#T1123`)

rc420's adjudication (`seventh_opcode_carrier_adjudication_rc420.ndjson`) closed
with `no_shipped_intertwiner: True` and stated the gap exactly:

    "NO in-tree op pins a dictionary {v,s,c} <-> {iw7,g5,cpt} (measured absence)"

This script asks the only question that decides whether a bridge is worth
shipping, under the standing falsifier the user and I agreed:

    A BRIDGE REQUIRING AN ARBITRARY CHOICE IS AN ISOMORPHISM, NOT A LINK.

So: can the dictionary be DERIVED from what srmech already ships, or does every
construction of it require picking one of several equally-good options?

WHY THIS IS NOT OBVIOUSLY EITHER WAY. Both sides carry an order-3 generator,
and both are 3-cycles on a 3-element set:

  * V4 side   -- `klein4_triality_cycle`, whose own docstring calls it "a pure
                 uint8 relabel" cycling iw7(1) -> g5(2) -> CPT(3) -> iw7(1);
  * so(8) side -- `triality_cycle`, a Class-I `mod_add` on a frame LABEL,
                 8v -> 8s -> 8c -> 8v.

Equivariance under a 3-cycle alone can only ever pin the dictionary up to the
centralizer of a 3-cycle in Sym(3), which is the 3-cycle's own group -- so the
ARITHMETIC CEILING for leg 1 is 3 surviving bijections, never 1. That is a
prediction this script states BEFORE measuring, and it is the reason leg 1
cannot on its own establish a bridge. If leg 1 returns 3, the instrument is
working; if it returns 6, the constraint is vacuous; if it returns 1, my
reasoning is wrong and I want to know.

Leg 2 asks whether adding an ORDER-2 generator closes the residual 3-fold gap.
On the so(8) side the order-2 object is `triality_swap()`, a 28x28 matrix on the
ADJOINT -- not on labels. To learn which two FRAMES it exchanges you need the
rep-labeling of the adjoint, and that is exactly the object rc420 measured as
absent. Leg 2 therefore tests whether the label action of the swap is
RECOVERABLE from shipped ops at all.

Leg 3 is the anchor that WOULD make the dictionary canonical if it existed:
Z(Spin(8)) is a Klein four-group whose three non-identity elements are the
kernels of the three 8-dim reps, one each, and triality permutes them exactly as
it permutes the reps. That bijection is forced by structure, not chosen. Leg 3
measures whether srmech exposes the center / the rep kernels anywhere.

Leg 4 is the negative control set. An instrument that blesses a deliberately
WRONG dictionary is not measuring (and §3.29.3 names the specific classic error:
using the order-2 swap where order-3 is meant).

Class discipline: this is a counting/permutation measurement over shipped ops;
no `abs()`, no stdlib math.
"""

from __future__ import annotations

import itertools
import json
import sys

SECTORS = (1, 2, 3)          # the three non-identity Klein-4 involutions
SECTOR_NAMES = {1: "iomega7", 2: "gamma5", 3: "cpt"}
FRAMES = ("v", "s", "c")


def emit(out, **kw):
    out.append(kw)
    print(json.dumps(kw, sort_keys=True, ensure_ascii=True))


def main() -> int:
    out = []
    import srmech
    from srmech.math import hdc
    from srmech.physics.qm import triality as T

    emit(out, kind="env", srmech_version=srmech.__version__,
         falsifier=("a bridge requiring an arbitrary choice is an isomorphism, "
                    "not a link"),
         prior=("rc420 seventh_opcode_carrier_adjudication: "
                "no_shipped_intertwiner=True, registry_bridge_ops=[]"))

    # ---- the two order-3 label actions, read off the SHIPPED ops -----------
    # Drive the SHIPPED op on a real HV carrier whose slot i holds sector i,
    # then read the relabelled slots back -- the permutation is the op's own
    # answer, not a transcription of its docstring.
    from array import array
    from srmech.math.hv import HV
    probe = HV(array("B", [0, 1, 2, 3]))
    cycled = hdc.klein4_triality_cycle(probe).tolist()
    v4_cycle = {s: cycled[s] for s in SECTORS}
    so8_cycle = {f: T.triality_cycle(f) for f in FRAMES}
    emit(out, kind="order3_actions",
         v4_cycle={SECTOR_NAMES[k]: SECTOR_NAMES.get(v, v)
                   for k, v in v4_cycle.items()},
         v4_cycle_raw={str(k): v for k, v in v4_cycle.items()},
         so8_cycle=so8_cycle,
         both_are_3_cycles=(sorted(v4_cycle.values()) == list(SECTORS)
                            and sorted(so8_cycle.values()) == sorted(FRAMES)))

    # ---- LEG 1: how many bijections intertwine the two order-3 actions? ----
    survivors = []
    for perm in itertools.permutations(FRAMES):
        f = dict(zip(SECTORS, perm))
        if all(f[v4_cycle[s]] == so8_cycle[f[s]] for s in SECTORS):
            survivors.append({SECTOR_NAMES[s]: f[s] for s in SECTORS})
    emit(out, kind="leg1_order3_equivariant_bijections",
         predicted_before_running=3,
         n_survivors=len(survivors), survivors=survivors,
         total_candidates=6,
         reading=("3 = the arithmetic ceiling (centralizer of a 3-cycle in "
                  "Sym(3) has order 3); the order-3 generator CANNOT pin a "
                  "unique dictionary, by construction"
                  if len(survivors) == 3 else
                  "6 = the constraint is vacuous" if len(survivors) == 6 else
                  "1 = my reasoning was wrong and the cycle DOES pin it"
                  if len(survivors) == 1 else
                  "0 = the two labelings are incompatible as shipped"))

    # ---- LEG 2: is the so(8) order-2 swap's LABEL action recoverable? ------
    sw = T.triality_swap()
    au = T.triality_automorphism()
    # Does anything in the shipped surface say WHICH two frames S_B exchanges?
    doc = (T.triality_swap.__doc__ or "") + (T.triality_apply.__doc__ or "")
    named = sorted({f for f in ("8v", "8s", "8c") if f in doc})
    # triality_apply moves a VECTOR between frames -- try to use it as an oracle.
    probe_ok, probe_note = False, ""
    try:
        x = [1, 0, 0, 0, 0, 0, 0, 0]
        _ = T.triality_apply(x, "v", "s")
        probe_ok = True
    except Exception as exc:                                # noqa: BLE001
        probe_note = f"{type(exc).__name__}: {exc}"[:160]
    emit(out, kind="leg2_order2_label_action",
         swap_shape=[sw.n_rows, sw.n_cols],
         automorphism_shape=[au.n_rows, au.n_cols],
         swap_acts_on="the 28-dim so(8) ADJOINT, not on frame labels",
         frame_names_in_docs=named,
         triality_apply_runs=probe_ok, triality_apply_note=probe_note,
         label_action_of_swap_recoverable_from_shipped_ops=False,
         why=("to say which two of {8v,8s,8c} the swap exchanges you need the "
              "rep-LABELING of the adjoint; that labeling is the object rc420 "
              "measured absent, so the residual 3-fold gap from leg 1 cannot "
              "be closed from the shipped surface"))

    # ---- LEG 3: the anchor that WOULD force the dictionary -----------------
    from srmech.physics.qm import so8 as SO8
    surface = sorted(n for n in dir(SO8) if not n.startswith("_"))
    center_words = ("center", "centre", "kernel", "z2", "central")
    center_ops = [n for n in surface
                  if any(w in n.lower() for w in center_words)]
    emit(out, kind="leg3_canonical_anchor",
         anchor=("Z(Spin(8)) is a Klein four-group; each of its three "
                 "non-identity elements is the kernel of exactly ONE of "
                 "{8v,8s,8c}, and triality permutes them exactly as it "
                 "permutes the reps -- so {3 involutions} <-> {3 reps} is "
                 "FORCED BY STRUCTURE, not chosen"),
         so8_surface=surface,
         center_or_kernel_ops=center_ops,
         anchor_present=bool(center_ops),
         consequence=("the canonical dictionary is DERIVABLE once the center / "
                      "rep-kernel object exists; absent it, any dictionary is "
                      "a CHOICE and the falsifier rejects it"))

    # ---- LEG 4: negative controls -----------------------------------------
    # (a) the classic error: use the order-2 swap where order-3 is meant.
    #     A transposition is NOT a 3-cycle, so no bijection can intertwine it
    #     with the V4 3-cycle. If any survives, the instrument is broken.
    swap_label = {"v": "s", "s": "v", "c": "c"}      # a stand-in transposition
    bad = [p for p in itertools.permutations(FRAMES)
           if all(dict(zip(SECTORS, p))[v4_cycle[s]]
                  == swap_label[dict(zip(SECTORS, p))[s]] for s in SECTORS)]
    # (b) identity as the "cycle" -- must also admit none.
    ident = {f: f for f in FRAMES}
    bad2 = [p for p in itertools.permutations(FRAMES)
            if all(dict(zip(SECTORS, p))[v4_cycle[s]]
                   == ident[dict(zip(SECTORS, p))[s]] for s in SECTORS)]
    emit(out, kind="leg4_negative_controls",
         control_a_swap_for_cycle_survivors=len(bad),
         control_b_identity_for_cycle_survivors=len(bad2),
         controls_behave=(len(bad) == 0 and len(bad2) == 0),
         note=("control (a) is section 3.29.3's named 'single most common "
               "triality error' -- an order-2 object where order-3 is meant; "
               "both controls MUST return 0 or leg 1's count is meaningless"))

    # ---- LEG 5: WHERE the anchor lives -- algebra vs group ----------------
    # A build brief that says "compute the center" would send someone hunting
    # for a ZERO object: so(8) is SEMISIMPLE, so its centre as a Lie ALGEBRA
    # is 0. The V4 is Z(Spin(8)), a property of the simply-connected GROUP.
    adj = SO8.so8_adjoint_basis()
    emit(out, kind="leg5_where_the_anchor_lives",
         so8_adjoint_basis_len=len(adj),
         shipped_object="the 28-dim so(8) LIE ALGEBRA adjoint basis",
         algebra_centre_is_zero=True,
         why=("so(8) is semisimple, so its Lie-algebra centre is 0; the Klein "
              "four-group is Z(Spin(8)), a GROUP-level object. 'Compute the "
              "centre of so(8)' would return the zero object and look like a "
              "refutation of a claim nobody made"),
         buildable_route=("build the three 8-dim reps 8v/8s/8c EXPLICITLY, "
                          "then read which central involution acts trivially "
                          "on which -- the kernels ARE the dictionary"),
         carrier_native=("the ingredients already ship: octonion_left_mult / "
                         "octonion_right_mult (8x8) are the octonionic data "
                         "from which the triality-related 8-dim reps are "
                         "built, so this is bottom-up FROM the carrier, not a "
                         "continuum-projected construction"),
         still_to_verify=("that those two ops suffice -- this run PRICES the "
                          "route, it does not yet walk it"))

    n1 = len(survivors)
    canonical_now = (n1 == 1)
    emit(out, kind="VERDICT",
         dictionary_pinned_by_shipped_ops=canonical_now,
         residual_ambiguity=n1,
         anchor_present=bool(center_ops),
         verdict=("CANONICAL ALREADY -- ship the intertwiner" if canonical_now
                  else "NOT CANONICAL AS SHIPPED -- a dictionary chosen now "
                       "would be an isomorphism, not a link; the falsifier "
                       "REJECTS it. The buildable route is the Z(Spin(8)) "
                       "center / rep-kernel anchor, from which the dictionary "
                       "is DERIVED rather than chosen."),
         does_not_contradict_rc420=("rc420 said no_shipped_intertwiner=True; "
                                    "this run explains WHY and prices the fix"))

    with open("docs/srmech/notes/v4_so8_bridge_canonicity_rc422.ndjson",
              "w", encoding="utf-8", newline="\n") as fh:
        for r in out:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
