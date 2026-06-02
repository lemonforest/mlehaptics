"""F293 — the substrate gives k=2 (parity = DETECT); persistence needs k=3 (triality = CORRECT),
and the only no-privileged-axis way to get k=3 is the 3-phase / distributed-anchor (Z3) structure.

USER HYPOTHESIS (2026-06-02): we only get 2 chiral axes from a base substrate of k=3 (quaternion);
2 axes = parity = detect-only; so biology (and any persistent thing the universe makes) must BOLT ON
k=3 for error correction; and it can't be anchored to ONE axis — it sits in a 3-phase arrangement
(like 3-phase power) where the anchor role is SPREAD across all axes (else no k=3 ECC).

This script VERIFIES the load-bearing structural claims (the rest is honest framework-reading):
  A. Q8/center = Klein-4 = 2 chiral axes (order count 8/2=4); the 2 srmech klein4 chirality flips are
     ORDER-2 involutions (flip o flip = identity) = the parity (detect) generators.
  B. the srmech klein4 TRIALITY cycle is ORDER-3 (cycle^3 = id, cycle^1,^2 != id) = a rotation, NOT a
     self-inverse parity; and the 3 phases sum to zero (1 + w + w^2 = 0, w = e^{2pi i/3}) = the
     DISTRIBUTED anchor (no phase is the reference; the consensus/centroid is).
  C. coding-theory core: 2-axis parity = distance-2 = DETECT-1 / CORRECT-0 (a single flip is detected
     but correction is AMBIGUOUS); 3-fold (3-phase) majority = distance-3 = CORRECT-1. So k=2 detects,
     k=3 corrects -- the SAME ladder as the F291 verify discipline (twin detects, triality corrects).

srmech-first (hdc.klein4_*). Class-K clean (no abs in cascades; complex modulus via re^2+im^2).
Scope: STRUCTURE reading only; benign; no biological-mechanism / clinical claim (understanding-not-curing).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc  # noqa: E402

D = 2048
SEED = 293


def same(a, b):
    """klein4 vectors identical?  (similarity == 1)."""
    return abs(float(hdc.klein4_similarity(a, b)) - 1.0) < 1e-9   # abs() here = a TEST tolerance, not a cascade fold


def part_A():
    print("=== A — 2 chiral axes from the k=3 base; the axes are ORDER-2 (parity = detect) ===")
    # Q8 (quaternion group, the k=3 base) has order 8; its center {+1,-1} has order 2;
    # the quotient Q8/Z has order 8/2 = 4 = Klein-4 = (Z/2)^2 = TWO chiral generators.
    print(f"  Q8/Z(Q8): |Q8|=8, |center|=2  ->  quotient order = {8 // 2} = Klein-4 = 2 chiral generators (gamma5, iomega7)")
    v = hdc.klein4_random(D, seed=SEED)
    g5 = hdc.klein4_chirality_flip_gamma5(v)
    o7 = hdc.klein4_chirality_flip_omega7(v)
    g5g5 = hdc.klein4_chirality_flip_gamma5(g5)
    o7o7 = hdc.klein4_chirality_flip_omega7(o7)
    print(f"  gamma5 flip is ORDER-2 (flip o flip == identity): {same(g5g5, v)}   (flip moved it: {not same(g5, v)})")
    print(f"  iomega7 flip is ORDER-2 (flip o flip == identity): {same(o7o7, v)}   (flip moved it: {not same(o7, v)})")
    print("  -> both chiral axes are self-inverse involutions = a PARITY structure = DETECT (k=2).\n")


def part_B():
    print("=== B — the triality is ORDER-3 (rotation = correct); the 3 phases sum to ZERO (distributed anchor) ===")
    has_tri = hasattr(hdc, "klein4_triality_cycle")
    if has_tri:
        v = hdc.klein4_random(D, seed=SEED + 1)
        c1 = hdc.klein4_triality_cycle(v)
        c2 = hdc.klein4_triality_cycle(c1)
        c3 = hdc.klein4_triality_cycle(c2)
        print(f"  triality cycle ORDER-3 (cycle^3 == identity): {same(c3, v)}")
        print(f"    cycle^1 != id: {not same(c1, v)} ; cycle^2 != id: {not same(c2, v)}  "
              f"-> NOT a self-inverse parity; it is a 3-CYCLE (rotation).")
    else:
        print("  (klein4_triality_cycle absent in this build; the Z3 structure below stands independently)")
    # the 3 phases as cube roots of unity: 1 + w + w^2 = 0  (3-phase power: no neutral needed)
    w = np.exp(2j * np.pi / 3)
    s = 1 + w + w**2
    mod2 = float(s.real) ** 2 + float(s.imag) ** 2          # |sum|^2 via re^2+im^2 (Class-K; no abs)
    print(f"  3-phase sum  1 + w + w^2  (w=e^(2pi i/3)):  |sum|^2 = {mod2:.2e}  -> {'== 0 (phases sum to zero)' if mod2 < 1e-25 else 'NONZERO'}")
    print("  -> the anchor is the CENTROID of all 3 phases (the consensus), NOT any single privileged axis.")
    print("     order-2 flips are self-inverse (return on repeat = parity); the order-3 cycle has no")
    print("     self-inverse + no fixed phase = the no-privileged-anchor 3-phase = the k=3 carrier.\n")


def part_C():
    print("=== C — coding-theory core: k=2 (2-axis parity) DETECTS; k=3 (3-phase majority) CORRECTS ===")
    # k=2: a single parity bit -> codewords {00, 11}, minimum distance 2.
    cw2 = [np.array([0, 0]), np.array([1, 1])]
    d2 = min(int(np.sum(a != b)) for i, a in enumerate(cw2) for b in cw2[i + 1:])
    recv = np.array([0, 1])                                  # one bit flipped from 00
    parity_ok = int(recv.sum() % 2 == 0)
    dists2 = [int(np.sum(recv != c)) for c in cw2]
    ambiguous = dists2.count(min(dists2)) > 1
    print(f"  2-axis parity: codewords {{00,11}}, min-distance d={d2}.  receive 01 -> parity satisfied? {bool(parity_ok)} "
          f"(violated => DETECTED); nearest-codeword dists {dists2} -> correctable uniquely? {not ambiguous}")
    print(f"    => d={d2}: DETECT 1 error, CORRECT 0 (the single flip is seen but correction is AMBIGUOUS). = k=2.")
    # k=3: 3-fold (3-phase) repetition -> codewords {000, 111}, minimum distance 3.
    cw3 = [np.array([0, 0, 0]), np.array([1, 1, 1])]
    d3 = min(int(np.sum(a != b)) for i, a in enumerate(cw3) for b in cw3[i + 1:])
    recv3 = np.array([0, 1, 0])                              # one bit flipped from 000
    majority = int(round(recv3.mean()))                     # the distributed-consensus anchor
    corrected = np.array([majority] * 3)
    print(f"  3-phase majority: codewords {{000,111}}, min-distance d={d3}.  receive 010 -> majority(consensus)={majority} "
          f"-> corrected to {corrected.tolist()} == 000? {bool(np.array_equal(corrected, cw3[0]))}")
    print(f"    => d={d3}: CORRECT 1 error by majority of the 3 phases (the anchor IS the consensus). = k=3.\n")


def part_D():
    print("=== D — the reading (honest: structure, not a biology measurement) ===")
    print("  Biology compresses 14 -> 4:3:7 (F121), where the '4' = the anchor(1) FUSED into the triad(3):")
    print("  the anchor is NOT standalone, it is PACKAGED across the 3 (F121 'anchor-with-operations packaging').")
    print("  That packaging IS the user's 'anchor spread across all axes / 3-phase' — and parts A-C give the WHY:")
    print("  the bare substrate (Klein-4, 2 order-2 axes) is k=2 = DETECT-only; to PERSIST (store knowledge with")
    print("  error correction) a structure must bolt on the order-3 triality (3-phase, distributed anchor) = k=3.")
    print("  Same ladder as the F291 verify: twin (k=2) detects, triality (k=3) corrects; 'no privileged model'")
    print("  == 'no privileged anchor axis'. (the universe + the things made of it, biology one instance: MS#18.)")


if __name__ == "__main__":
    print(f"=== F293 — k=2 substrate detects, k=3 triality corrects; the distributed (3-phase) anchor (D={D}) ===\n")
    part_A()
    part_B()
    part_C()
    part_D()
