"""F297 — is an organelle a 'gauge ball'? Two binding modes, the two the cosmos math has.

User (2026-06-02): organelles emerge like partitions; the same cosmos math for a single cell?
gauge-ball behavior in the bio substrate — that's an organelle maybe?

SHARP, FALSIFIABLE DISTINCTION (the honest read): there are TWO organelle binding modes, matching the
TWO ways physics binds a thing:
  (1) MEMBRANE-bound organelle (mito/plastid/ER) = held by a WALL = an imposed boundary = CLASS B
      self-partition (F296). 'Matter in a container.' Bound BY the external frame.
  (2) MEMBRANELESS organelle = biomolecular condensate (nucleolus / stress granule / P-body) = held by
      the constituents' MUTUAL MULTIVALENT SELF-INTERACTION, NO wall. = a GLUEBALL / GAUGE BALL: a thing
      self-bound by the field's own self-interaction, needing no external source.

So 'gauge ball = organelle' is RIGHT for the MEMBRANELESS organelle (condensate); the membrane organelle
is the Class-B wall. The test:
  A. WALL-bound (membrane): cycle C_n closed by ONE wall edge. Remove the wall -> open path P_n, λ₂ COLLAPSES.
     Bound by a single boundary edge (fragile to it) = container-bound.
  B. SELF-bound (condensate/gauge-ball): complete graph K_m (every constituent binds every other =
     multivalency), NO designated wall. λ₂ = m (high). Remove ANY edge -> still bound (λ₂ barely drops).
     Self-bound, distributed, no boundary edge = the glueball property (self-interaction binds it).
  C. GAUGE signature: the k=7 loop bind (Moufang, non-associative) IS the self-interaction op; loop_associator
     != 0 shows the gauge op self-binds NON-associatively (the glueball property), vs the membrane's
     ASSOCIATIVE nesting (TLV, associator = 0). Whether REAL condensate interactions are non-associative is
     the EXPERT's question (flagged, not asserted).

srmech-first (Class-L dense_laplacian/jacobi; loop_associator). Class-K clean. Scope: STRUCTURE-read +
cite-by-reference (LLPS/condensate biology is textbook; PDF-extraction-pending); the gauge-math identification
is a framework reading + the expert's test, NOT a claim condensates literally run QCD. Defensive; no-lineage.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc                                              # k=7 loop bind / associator
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals       # Class L


def lambda2(n, edges):
    ev = sorted(float(x) for x in jacobi_eigvals(dense_laplacian(n, edges)))
    return ev[1]


def complete_edges(m):
    return [(i, j) for i in range(m) for j in range(i + 1, m)]


def cycle_edges(n):
    return [(i, (i + 1) % n) for i in range(n)]


def path_edges(n):
    return [(i, i + 1) for i in range(n - 1)]


def main():
    print("=== F297 — organelle as gauge ball? two binding modes (wall vs self-bound) ===\n")
    n = 6

    # A — MEMBRANE-bound (Class B wall): cycle closed by one wall edge; remove it -> open, λ2 collapses
    wall_edge = (n - 1, 0)
    cyc = cycle_edges(n)
    l2_membrane = lambda2(n, cyc)
    l2_no_wall = lambda2(n, [e for e in cyc if e != wall_edge])      # remove the one closing/wall edge -> path
    print("--- A: MEMBRANE-bound organelle (Class B wall = imposed boundary) ---")
    print(f"  closed (wall present)  λ₂ = {l2_membrane:.3f}")
    print(f"  wall edge REMOVED      λ₂ = {l2_no_wall:.3f}   -> collapses ×{l2_membrane / l2_no_wall:.2f}")
    print(f"  => bound BY a single boundary edge (the wall); FRAGILE to it = container-bound (matter in a box).\n")

    # B — MEMBRANELESS condensate (gauge ball): complete graph (multivalent self-interaction), no wall
    m = 6
    K = complete_edges(m)
    l2_condensate = lambda2(m, K)
    # remove any one edge -> still bound (no single edge is 'the boundary')
    l2_minus1 = lambda2(m, K[1:])
    print("--- B: MEMBRANELESS condensate (gauge ball = self-bound by self-interaction, no wall) ---")
    print(f"  complete K_{m} (every constituent binds every other)  λ₂ = {l2_condensate:.3f}")
    print(f"  ANY one edge removed                                  λ₂ = {l2_minus1:.3f}   -> ×{l2_minus1 / l2_condensate:.2f} (robust)")
    print(f"  => bound by DISTRIBUTED self-interaction; NO boundary edge to remove = the glueball property")
    print(f"     (self-bound, no external source). This is the gauge-ball-structured organelle.\n")

    # C — the GAUGE (k=7) signature: the loop bind self-binds NON-associatively (glueball property)
    print("--- C: the gauge (k=7) signature — self-interaction is NON-associative (loop bind) vs associative wall ---")
    rng = np.random.default_rng(297)

    def e8(i):
        v = np.zeros(8); v[i] = 1.0; return v
    a, b, c = e8(1), e8(2), e8(4)
    assoc = hdc.loop_associator(a, b, c)                              # (ab)c - a(bc) for the k=7 op
    assoc_norm = float(np.dot(assoc, assoc)) ** 0.5                   # Class-K (no abs)
    print(f"  k=7 loop-bind associator ‖(ab)c − a(bc)‖ = {assoc_norm:.3f}  -> NON-ZERO = the gauge op SELF-binds")
    print(f"     non-associatively (the glueball/self-interaction property). The membrane (TLV nesting) is")
    print(f"     ASSOCIATIVE (associator = 0) = a passive wall, not a self-interaction. So the gauge ball needs")
    print(f"     the k=7 (non-associative) self-binding; the membrane organelle does not have it.\n")

    print("=== reading (honest) ===")
    print("  YES — for the MEMBRANELESS organelle (condensate): self-bound by multivalent self-interaction,")
    print("  no wall = the glueball/gauge-ball STRUCTURE. The MEMBRANE organelle is the Class-B wall (F296).")
    print("  The cell thus shows BOTH cosmos binding modes: container-bound matter (Class B) AND self-bound")
    print("  'field' (gauge ball / condensate). HONEST LIMITS: this is a STRUCTURAL match (self-bound-no-wall),")
    print("  not a claim condensates run k=7/QCD; whether the condensate self-interaction is genuinely")
    print("  NON-ASSOCIATIVE (a true gauge ball vs a generic self-bound aggregate) is the EXPERT's test.")
    print("  'Same cosmos math for a cell': PIECES yes (k=2 detect code, k=3 correct cycle, both binding modes);")
    print("  the FULL claim is unproven — and the k=7 gauge-rung identity for the condensate is the open question.")


if __name__ == "__main__":
    main()
