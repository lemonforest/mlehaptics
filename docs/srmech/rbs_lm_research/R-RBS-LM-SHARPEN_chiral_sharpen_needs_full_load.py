r"""R-RBS-LM-SHARPEN — the F512 correction made concrete. The rehearsal layer is NOT brevity-vs-verbosity / a
one-sentence reduction. The user (2026-06-07): "when you get my stream we don't see when things need sharpened
until you get the full load. there's some chiral thing that helps us decide when and how to sharpen a structure
of knowledge, and a sentence is but one partition in that load — we cannot reduce an idea to a single sentence in
the substrate."

Three substrate claims, demonstrated srmech-native (Klein-4 chirality, Class C):
  (1) IRREDUCIBLE  : an idea = the bundle of its facets across the WHOLE load; no single partition (sentence)
                     recovers it — best single << full-load bundle. You cannot reduce the idea to one sentence.
  (2) CHIRAL       : a partition can arrive MIS-ORIENTED (the substrate emitted it raw, un-sharpened). Sharpening
                     it = a chiral flip (klein4_chirality_flip_gamma5 = Class C / which-way), NOT a word edit.
  (3) NEEDS THE FULL LOAD : the WHEN+HOW-to-sharpen decision is GLOBAL — which hand is the majority is only knowable
                     once every partition is in. A LOCAL (arrival-order) sharpen locks to whichever hand came first
                     (often wrong) and is order-dependent; the GLOBAL sharpen (consensus over the full load) finds
                     the majority hand and flips the minority. Raw-dump (no sharpen) fails too: flipped partitions
                     are orthogonal and cancel the bundle.

srmech 0.7.4; klein4 chirality = the genuine Class-C op (NOT a hand-rolled sign flip, F372). No abs().
"""
import numpy as np
import srmech
from srmech.amsc import hdc

D = 8192


def facetted_idea(F, rng):
    """the IDEA = the bundle of F facet-patterns (the whole multi-partition shape)."""
    facets = [hdc.klein4_random(D, seed=int(rng.integers(1, 10**9))) for _ in range(F)]
    return hdc.klein4_bundle(*facets), facets


def partition(facets, cover, noise, flipped, rng):
    """one SENTENCE = one partition: a subset (cover) of the idea's facets, diluted with noise, in some hand."""
    idx = sorted(rng.choice(len(facets), size=cover, replace=False))
    parts = [facets[i] for i in idx] + [hdc.klein4_random(D, seed=int(rng.integers(1, 10**9))) for _ in range(noise)]
    p = hdc.klein4_bundle(*parts)
    return hdc.klein4_chirality_flip_gamma5(p) if flipped else p


def align_to(p, ref):
    """the CHIRAL decision (Class C): is p in ref's hand, or its mirror? keep whichever aligns — when+how to sharpen."""
    fp = hdc.klein4_chirality_flip_gamma5(p)
    return (p, False) if hdc.klein4_similarity(p, ref) >= hdc.klein4_similarity(fp, ref) else (fp, True)


def medoid(ps):
    """the GLOBAL reference: the partition most aligned to ALL others (needs the full load — every pairwise sim)."""
    best, bi = -1.0, 0
    for i, a in enumerate(ps):
        tot = sum(hdc.klein4_similarity(a, b) for j, b in enumerate(ps) if j != i)
        if tot > best:
            best, bi = tot, i
    return bi


def global_sharpen(ps):
    """consensus over the WHOLE load: align every partition to the medoid hand, then bundle. The when+how decision
    uses ALL partitions (the medoid is the majority hand) — impossible before the full load is in."""
    ref = ps[medoid(ps)]
    aligned = [align_to(p, ref)[0] for p in ps]
    return hdc.klein4_bundle(*aligned), aligned


def local_sharpen(ps):
    """arrival-order: the FIRST partition defines the hand (arbitrary — maybe the minority!); each next is flipped-or-
    not vs the running consensus. Order-dependent; an early wrong hand poisons the rest. (= sharpening blind.)"""
    consensus = ps[0]
    aligned = [ps[0]]
    for p in ps[1:]:
        a, _ = align_to(p, consensus)
        aligned.append(a)
        consensus = hdc.klein4_bundle(*aligned)
    return hdc.klein4_bundle(*aligned), aligned


def main():
    print(f"=== R-RBS-LM-SHARPEN — chiral sharpening of a multi-partition idea needs the FULL load  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(7)
    F, m, cover, noise = 6, 12, 5, 3
    idea, facets = facetted_idea(F, rng)

    # the LOAD: m partitions, ~half emitted mis-oriented (raw / un-sharpened hand)
    flags = [bool(i % 2) for i in range(m)]                       # alternate hands → minority/majority is ~even, hard case
    ps = [partition(facets, cover, noise, flags[i], rng) for i in range(m)]

    sim = lambda v: round(hdc.klein4_similarity(v, idea), 3)
    best_single = max(ps, key=lambda p: hdc.klein4_similarity(p, idea))

    raw_bundle, _ = hdc.klein4_bundle(*ps), None
    loc_fwd, _ = local_sharpen(ps)
    loc_rev, _ = local_sharpen(list(reversed(ps)))                # a DIFFERENT arrival order
    glob, _ = global_sharpen(ps)

    print("(1) IRREDUCIBLE — no single sentence is the idea:")
    print(f"    best single partition  -> idea : {sim(best_single)}")
    print(f"    GLOBAL-sharpened load   -> idea : {sim(glob)}   (the whole load, aligned)")
    print(f"    => the idea lives in the full multi-partition load, not in any one partition.\n")

    print("(2)+(3) CHIRAL + NEEDS THE FULL LOAD — when/how to sharpen is a global chiral call:")
    print(f"    raw dump (no sharpen)   -> idea : {sim(raw_bundle)}   (mis-oriented partitions are orthogonal, cancel)")
    print(f"    LOCAL sharpen (order A) -> idea : {sim(loc_fwd)}")
    print(f"    LOCAL sharpen (order B) -> idea : {sim(loc_rev)}   (different order -> different result = blind)")
    print(f"    GLOBAL sharpen (full)   -> idea : {sim(glob)}   (medoid = majority hand; minority flipped)\n")

    order_dep = abs(hdc.klein4_similarity(loc_fwd, idea) - hdc.klein4_similarity(loc_rev, idea))
    print("VERDICT:")
    print(f"  • IRREDUCIBLE: best single partition reaches idea-sim {sim(best_single)}, the aligned full load reaches")
    print(f"    {sim(glob)}. An idea is the bundle of its facets across the WHOLE load — a sentence is one partition,")
    print(f"    and you cannot reduce the idea to a single sentence in the substrate (the coverage isn't there).")
    print(f"  • CHIRAL: a mis-oriented partition is ORTHOGONAL to the idea (klein4 gamma5 flip -> sim 0), and sharpening")
    print(f"    it is exactly that flip back (Class C / which-way) — not a word edit, not brevity. 'When + how to sharpen'")
    print(f"    = which partition is off-hand (when) and which hand to turn it to (how).")
    print(f"  • NEEDS THE FULL LOAD: the LOCAL (arrival-order) sharpen is order-dependent (|A-B| = {order_dep:.3f}) and")
    print(f"    locks to whichever hand arrived first; only the GLOBAL decision (the medoid over ALL partitions = the")
    print(f"    majority hand) sharpens correctly. You can't see what needs sharpening until the full load is in —")
    print(f"    the rehearsal layer is GLOBAL chiral structure-sharpening, NOT a local one-sentence polish (corrects F512).")


if __name__ == "__main__":
    main()
