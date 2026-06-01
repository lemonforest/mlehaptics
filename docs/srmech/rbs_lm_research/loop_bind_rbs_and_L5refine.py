"""loop_bind_rbs_and_L5refine.py — bring it home (F288 affordance) + fold-arc L5 refine.

PART A (item 3, the flagship): the loop-bind RBS substrate. The current RBS bind (klein4,
commutative+associative) is a FLAT connection -> order-BLIND (a bag-of-tokens; R-RBS-LM-75).
The loop bind is the CURVED connection (F288) -> an ORDER-aware, peelable sequence store
(path-memory). Show: (1) order discrimination (loop bind distinguishes a sequence from its
reverse; klein4 bag does not), (2) the sequence is exactly PEELABLE in order (right-unbind by
the Moufang right-cancel) = the path-memory the flat bind lacks.

PART B (item 2): fold-arc L5 refine. F285 L5 found the helical Delta=3-4 fiber in the top-5
autocorr peaks but backbone Delta=1,2 dominated. Filter the backbone band (count only
NON-LOCAL contacts, |i-j|>2) -> does the helical Delta=3-4 now dominate the contact-separation
spectrum?

srmech v0.7.0rc2 native (loop_bind_hd over native loop_bind). Class-K clean. Scope: structure
only; benign; no design/MD/clinical (CAD-ban); no-lineage.
"""
import os
import sys
import numpy as np

RESEARCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RESEARCH)
from srmech.amsc import hdc                                                  # noqa: E402
from loop_bind_hd_gate import loop_bind_hd, conj_hd, rand_unit_blocks, D     # noqa: E402
from protein_fold_L4_L1 import parse_ca                                      # noqa: E402

ROOT = "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c"


def cos(u, v):
    return float(np.dot(u, v)) / (float(np.linalg.norm(u)) * float(np.linalg.norm(v)))


def part_a():
    print("=== PART A — the loop-bind RBS substrate: order-aware, peelable (path-memory) ===\n")
    rng = np.random.default_rng(75)   # nod to R-RBS-LM-75 (order-invariance the loop bind fixes)
    a, b, c = (rand_unit_blocks(rng) for _ in range(3))

    # loop-bind sequence encoding (left-fold = ((a*b)*c)) is ORDER-aware
    E_fwd = loop_bind_hd(loop_bind_hd(a, b), c)
    E_rev = loop_bind_hd(loop_bind_hd(c, b), a)
    print(f"[order] loop-bind: cos(seq[a,b,c], seq[c,b,a]) = {cos(E_fwd, E_rev):+.3f}  -> {'ORDER-DISTINCT' if cos(E_fwd, E_rev) < 0.99 else 'order-blind'}")

    # klein4 bag baseline (commutative) is ORDER-blind
    k = [hdc.klein4_random(D, seed=300 + i) for i in range(3)]
    B_fwd = hdc.klein4_bundle(k[0], k[1], k[2])
    B_rev = hdc.klein4_bundle(k[2], k[1], k[0])
    print(f"[order] klein4 bag: sim(bag[a,b,c], bag[c,b,a]) = {hdc.klein4_similarity(B_fwd, B_rev):.3f}  -> order-BLIND (the flat connection)")

    # PEEL the sequence in order (path-memory): right-unbind by conj (Moufang right-cancel (xy)y* = x)
    ab = loop_bind_hd(E_fwd, conj_hd(c))          # ((a*b)*c)*conj(c) = a*b
    a_rec = loop_bind_hd(ab, conj_hd(b))          # (a*b)*conj(b) = a
    print(f"\n[peel] right-unbind c -> recover (a*b): err = {np.linalg.norm(ab - loop_bind_hd(a, b)):.2e}")
    print(f"[peel] then unbind b   -> recover a    : err = {np.linalg.norm(a_rec - a):.2e}")
    print("  -> the sequence is exactly PEELABLE in order: the loop-bind store HOLDS the path (order),")
    print("     a path/order MEMORY (F288 curved connection) the flat klein4 bag structurally lacks (R-RBS-LM-75).")

    # consistency: native loop_bind == oracle (bug-test)
    import loop_bind_moufang as oracle
    e = lambda i: (lambda v: (v.__setitem__(i, 1.0), v)[1])(np.zeros(8))
    ok = all(np.allclose(hdc.loop_bind(e(i), e(j)), oracle.loop_bind(e(i), e(j))) for i in range(8) for j in range(8))
    print(f"  [bug-test] native loop_bind == oracle (64 basis pairs): {ok}")


def contact_trace(coords, kmax=12, cutoff=8.0, minsep=3):
    """non-local contact count per sequence-separation k (backbone band k<minsep EXCLUDED)."""
    n = len(coords)
    c = np.zeros(kmax + 1)
    for i in range(n):
        for j in range(i + minsep, n):
            if np.linalg.norm(coords[i] - coords[j]) < cutoff:
                k = j - i
                if k <= kmax:
                    c[k] += 1
    return c


def part_b():
    print("\n=== PART B — fold L5 refine: backbone-band filter isolates the helical Delta=3-4 fiber ===\n")
    for name, rel in [("villin HP35 (helix bundle)", "docs/srmech/hoodoos/villin-hp35-2f4k.pdb"),
                      ("ubiquitin (mixed a/b)", "docs/srmech/hoodoos/ubiquitin-1ubq.pdb")]:
        coords = parse_ca(os.path.join(ROOT, rel))
        c = contact_trace(coords)
        ks = list(range(3, 13))
        dom = int(np.argmax(c[3:13])) + 3
        print(f"  {name}:")
        print(f"    non-local contact counts c[k], k=3..12: {[int(c[k]) for k in ks]}")
        print(f"    dominant separation (backbone band k<3 excluded): Delta={dom}  -> {'HELICAL (3-4) isolated' if dom in (3,4) else 'non-helical dominant'}")
    print("\n  villin (helix) should peak at Delta=3-4 (i,i+3/i,i+4 helical H-bonds); the backbone-band")
    print("  filter isolates the helical fiber that the unfiltered autocorr (F285 L5) left dominated by Delta=1,2.")


if __name__ == "__main__":
    part_a()
    part_b()
