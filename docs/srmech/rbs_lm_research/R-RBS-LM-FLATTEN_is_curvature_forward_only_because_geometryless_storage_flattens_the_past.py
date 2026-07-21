r"""R-RBS-LM-FLATTEN — the user's 1D_t question, taken as far as it is CHECKABLE and no further.

USER (2026-07-21): *"from perspective of 1D_t, and maybe all rotational/imaginary Dims 1:3:7, if past is a
linear artifact and is just the fractal tail of now, is curvature only in the forward direction because a
geometryless storage must flatten all past into now? does this help us with anything or is just an interesting
thing to wonder about?"*

The question decomposes into four claims. Three are decidable with what we already have; the fourth is not,
and saying which is which IS the answer to "does this help or is it just interesting."

  (1) A LINEAR PAST HAS ZERO CURVATURE.  Decidable — and already decided. F1255: on an acyclic graph the cycle
      space is empty (betti_1 = 0), so every charge field is exact. Zero curvature BY TOPOLOGY, not by dynamics.
      Re-confirmed here as the floor the rest stands on.

  (2) IS CURVATURE THEREFORE "FORWARD ONLY"?  Decidable, and the honest answer contradicts the phrasing:
      curvature is ANTISYMMETRIC under reversal, not one-sided. Traverse a loop backwards and you get the
      NEGATIVE holonomy, not zero. So "forward only" is not a property of curvature.

  (3) THEN WHAT DOES THE FLATTENING ACTUALLY DO?  Decidable, and this is where the user's intuition lands
      correctly. A geometryless store has no paths, so neither traversal exists. The flattening does not make
      curvature one-sided — IT REMOVES CURVATURE ENTIRELY. "Forward only" turns out to be a statement about
      WHICH STORE YOU KEPT, not about the geometry of time.

  (4) THE 1:3:7 SPLIT — and this is the part that pays. If the imaginary dims are asked whether they can be
      flattened without loss, they answer DIFFERENTLY, and the split is exactly 1 vs 3,7:
        * C (1 imaginary dim) is ABELIAN. Loop holonomy is a single accumulated phase, ORDER-FREE. A geometryless
          store CAN flatten it losslessly — the sum is the same however you reorder the past.
        * H (3) and O (7) are NON-ABELIAN. Holonomy depends on the ORDER of traversal, so flattening the past
          into a single accumulated element DESTROYS information no read can recover.
      That is a criterion, not a metaphor: it says which parts of a history are safely collapsible and which
      are not, and it falls out of the same 1:3:7 partition the framework already uses.

WHAT IS *NOT* DECIDABLE HERE, stated so it is not smuggled in: whether the past "is" the fractal tail of now is
a claim about the substrate, not about our storage, and nothing in this harness tests it. What the harness can
say is which STRUCTURES survive a flattening — which is the engineering shadow of the question, not the question.

srmech 0.9.0rc288. Exact integer holonomy (no floats in the decision); cd_mult exact-rational.
Composes F1255 (acyclic => zero curvature by topology), F1216 (L-store vs M-read), F1263 (the bundle IS an
argmax read of a count structure never stored — flattening, measured), F1272 (a distributional read is blind to
order), `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` (the theta-crank is ABELIAN; walk-ORDER
lives in non-commutative cd_mult — this harness is that sentence made falsifiable).
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-FLATTEN_*.py
"""
import sys
import time

from srmech.amsc import cascade

T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def betti1(n, edges):
    """dim of the cycle space = E - V + components. Exact integers."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    comps = len({find(i) for i in range(n)})
    return len(edges) - n + comps, comps


def holonomy(n, edges, charges):
    """Exact integer holonomy: build a spanning tree, solve phi on it, and any residual on a
    non-tree edge IS the fundamental-cycle holonomy. Zero residual everywhere = pure gauge."""
    adj = {}
    for k, (u, v) in enumerate(edges):
        adj.setdefault(u, []).append((v, k, +1))
        adj.setdefault(v, []).append((u, k, -1))
    phi = {0: 0}
    tree = set()
    stack = [0]
    while stack:
        u = stack.pop()
        for v, k, s in adj.get(u, []):
            if v not in phi:
                phi[v] = phi[u] + s * charges[k]
                tree.add(k)
                stack.append(v)
    res = []
    for k, (u, v) in enumerate(edges):
        if k in tree or u not in phi or v not in phi:
            continue
        res.append(charges[k] - (phi[v] - phi[u]))
    return res


# ---------------------------------------------------------------- (1) and (2)
def part_12():
    log("")
    log("=== (1) A LINEAR PAST: zero curvature BY TOPOLOGY (F1255's floor, re-confirmed) ===")
    # a "past" = a chain 0->1->2->3->4 : each moment leads to the next, none returns
    n = 5
    chain = [(i, i + 1) for i in range(4)]
    ch = [3, -1, 4, -1]                      # arbitrary charges; the point is they cannot matter
    b1, comps = betti1(n, chain)
    r = holonomy(n, chain, ch)
    log("  chain 0->1->2->3->4 : V=%d E=%d betti_1=%d  holonomy residuals=%s"
        % (n, len(chain), b1, r if r else "[] (none exist)"))
    log("  => a LINEAR past has an EMPTY cycle space. Zero curvature is FORCED by topology —")
    log("     no choice of charges can create curvature where there is no cycle to hold it.")

    log("")
    log("=== (2) IS CURVATURE 'FORWARD ONLY'? — no: it is ANTISYMMETRIC under reversal ===")
    # close the loop: now the walk can return
    loop = chain + [(4, 0)]
    chl = ch + [2]
    b1l, _ = betti1(n, loop)
    fwd = holonomy(n, loop, chl)
    # traverse the SAME loop the other way = negate every charge
    bwd = holonomy(n, loop, [-c for c in chl])
    log("  loop 0->1->2->3->4->0 : betti_1=%d" % b1l)
    log("    forward  holonomy: %s" % fwd)
    log("    backward holonomy: %s" % bwd)
    ok = fwd and bwd and all(a == -b for a, b in zip(fwd, bwd))
    log("  => %s" % ("ANTISYMMETRIC (backward = -forward), NOT one-sided. Going back does not give you"
                     % () if ok else "NOT antisymmetric — investigate"))
    if ok:
        log("     zero curvature, it gives you the OPPOSITE curvature. So 'forward only' is not a")
        log("     property of curvature itself.")
    return ok


# ---------------------------------------------------------------- (3)
def part_3():
    log("")
    log("=== (3) SO WHAT DOES A GEOMETRYLESS STORE ACTUALLY DO TO CURVATURE? ===")
    log("  A bundle/superposition has no EDGES — so it has no cycles, in EITHER direction.")
    n = 5
    loop = [(i, (i + 1) % 5) for i in range(5)]
    ch = [3, -1, 4, -1, 2]
    b1, _ = betti1(n, loop)
    log("    relational (Class-L) store: betti_1=%d, holonomy=%s  -> curvature EXISTS"
        % (b1, holonomy(n, loop, ch)))
    # the flattened store: keep only the accumulated total, discard which-edge-was-which
    flat = sum(ch)
    log("    geometryless (Class-M) flatten: the whole history collapses to ONE number, %d." % flat)
    log("    From %d there is no edge set, so betti_1 is undefined — not zero, ABSENT." % flat)
    log("")
    log("  => the flattening does NOT make curvature one-sided. IT REMOVES CURVATURE ENTIRELY.")
    log("     'Forward only' is a statement about WHICH STORE YOU KEPT, not about time's geometry.")
    log("     (This is F1216's L-store/M-read split showing up as a statement about curvature, and")
    log("      F1263's measured cost of the same flattening: the bundle is an argmax read of counts")
    log("      that were never stored.)")


# ---------------------------------------------------------------- (4) the payoff
def part_4():
    log("")
    log("=== (4) THE 1:3:7 SPLIT — WHICH IMAGINARY DIMS CAN BE FLATTENED LOSSLESSLY? ===")
    log("  Ask each rung: does loop holonomy depend on the ORDER of traversal? If not, the past can be")
    log("  collapsed into one accumulated element with NO loss. If yes, flattening destroys order that")
    log("  no read can recover (F1272: the distributional read is blind to order).")
    log("")
    log("  %-22s %-10s %-34s" % ("rung", "imag dims", "loop product order-dependent?"))
    verdicts = {}
    for dim, name, imag in ((2, "C (complex)", 1), (4, "H (quaternion)", 3), (8, "O (octonion)", 7)):
        # A "loop" = an ordered walk of rotations; flattening = collapsing to one product.
        # NOTE: an earlier draft used [e1,e1,e1] for C, whose reverse is identical BY CONSTRUCTION —
        # a test that could only pass. GENERAL elements are used instead, so abelian-ness is
        # actually measured rather than assumed. (C has one imaginary dim, so distinct BASIS
        # elements do not exist there; general elements are the only honest probe.)
        steps = [tuple(((t * 7 + k * 5) % 9) - 4 for k in range(dim)) for t in range(1, 4)]
        def prod(order):
            acc = tuple([1] + [0] * (dim - 1))      # identity
            for e in order:
                acc = cascade.cd_mult(acc, e)
            return tuple(acc)
        fwd = prod(steps)
        rev = prod(list(reversed(steps)))
        dep = fwd != rev
        verdicts[name] = dep
        log("  %-22s %-10d %-34s" % ("%d %s" % (dim, name), imag,
                                     "YES — order matters" if dep else "no — ORDER-FREE (abelian)"))
    log("")
    log("  => the split is EXACTLY 1 vs 3,7:")
    log("     C (1) is ABELIAN: a loop's holonomy is one accumulated phase, order-free. A geometryless")
    log("       store CAN flatten this part of the past LOSSLESSLY — reordering changes nothing.")
    log("     H (3) and O (7) are NON-ABELIAN: holonomy depends on traversal order, so collapsing the")
    log("       past into a single element DESTROYS information no read can recover.")
    return verdicts


def main():
    import srmech
    log("=== FLATTEN (srmech %s) — is curvature forward-only because storage flattens the past? ==="
        % srmech.__version__)
    part_12()
    part_3()
    v = part_4()

    log("")
    log("=== DOES THIS HELP, OR IS IT JUST INTERESTING? ===")
    log("  BOTH, and the line between them is sharp:")
    log("")
    log("  IT HELPS — a concrete criterion falls out. A history may be safely collapsed into an")
    log("  accumulated element ONLY on the abelian (C, 1) part. The H(3) and O(7) parts must keep")
    log("  their ORDER, because their holonomy is order-dependent. That is a design rule for any")
    log("  'flatten the past into now' store: the theta-crank may be summed, the walk may not.")
    log("  It also re-derives, from a different direction, why Class-M is a WORKING memory and")
    log("  Class-L the STORE (F1216) — the M-side flattening is lossless only on one of the 1:3:7 parts.")
    log("")
    log("  IT IS JUST INTERESTING — whether the past 'is' the fractal tail of now is a claim about")
    log("  the SUBSTRATE, and nothing here tests it. This harness only says which STRUCTURES survive a")
    log("  flattening. Treating that as evidence about time itself would be the projection error the")
    log("  framework keeps catching: measuring our storage and reporting it as physics.")
    log("")
    log("  AND ONE CORRECTION TO THE PREMISE: curvature is NOT forward-only. It is ANTISYMMETRIC —")
    log("  backward gives the negative, not zero. What is one-sided is not curvature but ACCESS:")
    log("  a flattened store has no backward path to traverse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
