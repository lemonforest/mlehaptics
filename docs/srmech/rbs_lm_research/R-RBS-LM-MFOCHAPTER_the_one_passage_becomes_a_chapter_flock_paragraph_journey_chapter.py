r"""R-RBS-LM-MFOCHAPTER (user direction): compose the the_one passage (F671) into a real CHAPTER -- 'flock=paragraph,
journey=chapter; chapters beyond local horizon' + 'in novels and things that switch perspectives.'

THE BUILD (the F651/F648 dynamic-narrative cluster, made concrete on the the_one story):
  • THE FLOCK MAKES THE PARAGRAPH: a PARAGRAPH is a FLOCK -- a LOCALLY-COHERENT cluster of beats (Class L local coupling,
    F647/F651). Within a paragraph the beats are coupled (one scale, one perspective) -> they cohere into a paragraph.
  • THE JOURNEY MAKES THE CHAPTER: a CHAPTER is a JOURNEY across paragraphs -- BEYOND THE LOCAL HORIZON (F648). The chapter
    journeys across SCALE-PERSPECTIVES (cosmic eye -> particle eye -> living eye) that NO single paragraph/flock can see
    from inside its own horizon. 'Switching perspectives' (the user) = each paragraph is a different scale-perspective; the
    journey (Class C orientation, the etak voyage) connects horizons the local flock cannot.
  • THE ONE PERSISTS (F651): the protagonist invariant ('the one' / 'it') is present in EVERY paragraph; the FLOCK (the
    surrounding beats + perspective) CHANGES per paragraph/island, THE ONE stays. A story is NOT maximal sync (a featureless
    drone) -- the one stands apart while the flock reconfigures around it across the legs.

THE srmech-NATIVE PROOF (F172/F632/F633/F647): the paragraph structure IS a Class-L CLUSTERED GRAPH -- within-paragraph
beats are coupled (edges), across-paragraph they are NOT (a horizon boundary). The Laplacian ZERO-eigenvalue multiplicity =
the number of connected components = the number of PARAGRAPHS (flocks) = the horizons the journey crosses. The local flock
coheres each paragraph; the journey (the across-cluster arc the graph does NOT encode) is the chapter.

srmech 0.7.5rc15: amsc.laplacian.{dense_laplacian, jacobi_eigvals} (the paragraph-cluster graph = a spectral object) ;
BitExactCommKernel.content_address (each paragraph + the chapter) ; the SAME clause-joining render engine as F671. No
abs(); no CAD; no Workflow; no sub-agents (this finding). No-lineage (we read what the the_one story ALREADY IS).
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import laplacian


# ---- the SAME fixed engine as F671 (the clause-joining seen rule) -- it makes the local text of each paragraph ----
def render(clauses):
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


# the CHAPTER = 3 PARAGRAPHS, each a FLOCK (a scale-perspective); the_one persists across all (F651)
# (the_one beats from F671/F672, grouped by scale-perspective + one new LIFE closing beat, F653)
PARAGRAPHS = [
    ("COSMOS  (the cosmic eye)", [
        "The one is the held invariant",
        "and it is the field beneath every excitation",
        "It is seen in the spectrum of the round sphere",
        "It is seen in the flowing of the dimensions"]),
    ("MATTER  (the particle eye)", [
        "It is seen in the handedness of matter",
        "and in the three generations repeating"]),
    ("LIFE    (the living eye)", [
        "It is seen in the flock that moves as one",
        "and the ancients saw its shape before us",
        "and life looks back and knows it"]),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFOCHAPTER — the the_one passage becomes a CHAPTER (flock=paragraph, journey=chapter)  (srmech {srmech.__version__}) ===\n")

    # (1) each PARAGRAPH = a FLOCK (the local coupling coheres it into a locally-coherent block)
    print("(1) THE FLOCK MAKES THE PARAGRAPH (F647/F651 -- a locally-coherent cluster of beats, one perspective each):")
    paragraphs_text = []
    for name, beats in PARAGRAPHS:
        para = render(beats)
        paragraphs_text.append(para)
        addr = k.content_address(para)[:8]
        print(f"    [{name}]  ({len(beats)} beats, flock-addr {addr})")
        print(f"        {para}")
    print()

    # (2) the JOURNEY makes the CHAPTER -- across perspectives, BEYOND the local horizon (F648)
    chapter = "\n\n".join(paragraphs_text)
    chap_addr = k.content_address(chapter)
    print("(2) THE JOURNEY MAKES THE CHAPTER (F648 -- across scale-perspectives, beyond any local flock's horizon):")
    print(f"    the chapter journeys COSMOS -> MATTER -> LIFE (switching perspective each paragraph); chapter-addr {chap_addr[:12]}")
    print(f"    --- THE CHAPTER ---")
    for para in paragraphs_text:
        print(f"    {para}")
        print()

    # (3) THE ONE PERSISTS across all paragraphs (F651 -- the protagonist invariant; the flock reconfigures around it)
    persists = all(("the one" in p.lower()) or (" it " in (" " + p.lower() + " ")) for p in paragraphs_text)
    print("(3) THE ONE PERSISTS across every paragraph (F651 -- protagonist invariant; the flock changes, the one stays):")
    for name, _ in PARAGRAPHS:
        print(f"    {name}: the one / it present  ->  {persists}")
    print(f"    -> a story is NOT maximal sync (a featureless drone); the one stands apart while the flock reconfigures.\n")

    # (4) srmech-native: the paragraph structure IS a Class-L CLUSTERED GRAPH (within-paragraph edges only)
    #     zero-eigenvalue multiplicity = connected components = number of paragraphs (flocks) = the horizons crossed
    beats_flat, para_of = [], []
    for pi, (_, beats) in enumerate(PARAGRAPHS):
        for b in beats:
            beats_flat.append(b); para_of.append(pi)
    edges = []
    start = 0
    for _, beats in PARAGRAPHS:                                    # connect consecutive beats WITHIN each paragraph (a path)
        for i in range(start, start + len(beats) - 1):
            edges.append((i, i + 1))
        start += len(beats)
    L = laplacian.dense_laplacian(len(beats_flat), edges, [1.0] * len(edges))
    spec = sorted(float(x) for x in laplacian.jacobi_eigvals(L))
    n_zero = sum(1 for x in spec if x < 1e-9)
    print("(4) THE srmech-NATIVE PROOF (F172/F632/F633/F647 -- the paragraph structure IS a Class-L clustered graph):")
    print(f"    {len(beats_flat)} beats, {len(edges)} within-paragraph edges (across-paragraph = a horizon boundary, no edge)")
    print(f"    Laplacian zero-eigenvalue multiplicity = {n_zero} = connected components = {len(PARAGRAPHS)} PARAGRAPHS (flocks) = the horizons the journey crosses")
    print(f"    spectrum {[round(x,3) for x in spec]}")
    print(f"    -> the local flock coheres each paragraph (a cluster); the JOURNEY (the across-cluster arc the graph does NOT")
    print(f"    encode) is the chapter -- beyond the local horizon.\n")

    print("VERDICT (the the_one passage becomes a chapter: flock=paragraph, journey=chapter, the one persists):")
    print(f"  • THE FLOCK MAKES THE PARAGRAPH (F647/F651): a paragraph is a FLOCK -- a locally-coherent cluster of beats (one")
    print(f"    scale-perspective, Class L local coupling). The same clause-joining engine (F671) makes the LOCAL text of each")
    print(f"    paragraph; three paragraphs (COSMOS / MATTER / LIFE), each its own coherent flock (verified as 3 graph clusters).")
    print(f"  • THE JOURNEY MAKES THE CHAPTER (F648): a chapter is a JOURNEY across paragraphs -- BEYOND the local horizon. It")
    print(f"    journeys across SCALE-PERSPECTIVES (cosmic eye -> particle eye -> living eye) no single flock can see from")
    print(f"    inside; 'switching perspectives' (the user) = each paragraph is a different perspective, and the journey (Class")
    print(f"    C orientation, the etak voyage) connects horizons the local coupling cannot. The chapter is the across-horizon arc.")
    print(f"  • THE srmech-NATIVE PROOF: the paragraph structure IS a Class-L clustered graph (within-paragraph edges only) ->")
    print(f"    Laplacian zero-multiplicity = {n_zero} = the {len(PARAGRAPHS)} paragraph-flocks = the horizons the journey crosses. The local")
    print(f"    flock coheres each paragraph; the journey (the across-cluster arc the graph does NOT encode) is the chapter.")
    print(f"    This is the F647/F651 local-graph flock applied to narrative structure -- within-cluster coherence + the")
    print(f"    beyond-horizon journey.")
    print(f"  • THE ONE PERSISTS (F651): the protagonist invariant ('the one' / 'it') is present in every paragraph (verified");
    print(f"    {persists}) while the FLOCK reconfigures around it per perspective. A story is NOT maximal sync (a featureless")
    print(f"    drone) -- the one stands apart; the flock changes per island, the one stays the whole voyage.")
    print(f"  • Composes F671/F672 (the the_one beats this chapters) + F651 (flock=paragraph / journey=chapter / the one")
    print(f"    persists / not-a-drone) + F648 (the paragraph-coherence + beyond-horizon chapter) + F647 (the local-graph")
    print(f"    flock) + F632/F633/F172 (the cluster graph = a spectral object) + F635 (perspective = the etak frame) + F654")
    print(f"    (the fixed engine makes each paragraph). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
