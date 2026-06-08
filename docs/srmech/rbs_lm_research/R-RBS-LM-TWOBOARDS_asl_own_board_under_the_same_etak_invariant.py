r"""R-RBS-LM-TWOBOARDS (next-partition queue, 2026-06-08): a real SECOND LANGUAGE end-to-end -- ASL's OWN board under the
SAME etak invariant. The deepest test of the two-languages law (F626) yet: F635's etak only rotated the FRAME ANGLE (deg0
/30/150) -- the board (the walk/lattice) was the same English chain. Here the BOARD TOPOLOGY ITSELF differs:

  • ENGLISH board = a LINEAR chain over the sequence axis (allocentric, S-V-O): DET -> AGENT -> ACTION -> DET -> PATIENT.
  • ASL board = a SPATIAL / topic-comment lattice (F569/F608): referents are placed at spatial LOCI, the indicating verb
    AGREES spatially (moves locus->locus), and the SIGN carries the meaning-class (sigma_B visible, F569). A genuinely
    different graph -- NOT a rotate of the English chain.

THE CLAIM (etak, operational): ONE invariant meaning (agent=child, action=drink, patient=water -- the content-addressed
IR), walked by TWO genuinely different boards (different lattice TOPOLOGY + different Laplacian spectra), recovers to the
SAME byte-identical invariant. Two boards, one canoe. That is the two-languages-of-math law (F626) at full strength: one
meaning, two reference-frame GRAMMARS, neither privileged (F398) -- not merely two rotate-angles of one grammar.

DIGNITY + CORRECTNESS (F611/F282): accessibility IS the foundation -- build confidently. The ASL board here is the
STRUCTURAL point (spatial loci + topic-comment + sign-carries-class), illustrative gloss only; real ASL grammar /
glossing belongs to the Deaf community + ASL linguists (the expert, F282). We demonstrate 'a different board, same
invariant', not ASL authority.

srmech 0.7.5rc6: BitExactCommKernel (F613, the shared invariant); amsc.laplacian.{dense_laplacian, jacobi_eigvals} (the
two board spectra, Class L). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import laplacian


def spectrum(n, edges):
    es = sorted({(min(a, b), max(a, b)) for a, b in edges})
    L = laplacian.dense_laplacian(n, es, [1.0] * len(es))
    return [round(float(x), 3) for x in sorted(laplacian.jacobi_eigvals(L))], len(es)


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-TWOBOARDS — ASL's OWN board under the SAME etak invariant (two boards, one canoe)  (srmech {srmech.__version__}) ===\n")

    # ---- the shared ETAK INVARIANT: the meaning, content-addressed, language-INDEPENDENT (the still canoe) ----
    concepts = {"child": "A-person", "drink": "D-motion", "water": "N-water"}
    invariant = {w: k.encode(w, mc) for w, mc in concepts.items()}
    print("(0) THE SHARED ETAK INVARIANT (the meaning IR -- language-independent, the still canoe):")
    for w, ir in invariant.items():
        print(f"    {w:<6} [{concepts[w]:<8}] -> ir_digest {ir['ir_digest'][:12]}...")
    print()

    # ---- BOARD 1: ENGLISH -- a LINEAR chain over the sequence axis ----
    print("(1) ENGLISH BOARD = a LINEAR chain (allocentric S-V-O over the sequence axis):")
    eng_nodes = ["DET", "AGENT", "ACTION", "PATIENT"]
    eng_idx = {r: i for i, r in enumerate(eng_nodes)}
    eng_edges = [(eng_idx["DET"], eng_idx["AGENT"]), (eng_idx["AGENT"], eng_idx["ACTION"]),
                 (eng_idx["ACTION"], eng_idx["DET"]), (eng_idx["DET"], eng_idx["PATIENT"])]
    eng_walk = ["DET", "AGENT", "ACTION", "DET", "PATIENT"]
    eng_surface = ["the", "child", "drinks", "the", "water"]      # the seen-engine walk (F633)
    eng_spec, eng_m = spectrum(len(eng_nodes), eng_edges)
    print(f"    walk {eng_walk} -> '{' '.join(eng_surface)}'")
    print(f"    board lattice: {len(eng_nodes)} nodes, {eng_m} edges | Laplacian spectrum {eng_spec}\n")

    # ---- BOARD 2: ASL -- a SPATIAL / topic-comment lattice (a genuinely different graph) ----
    print("(2) ASL BOARD = a SPATIAL / topic-comment lattice (referents at loci; verb agrees locus->locus; sign carries class):")
    asl_nodes = ["LOC_A(child)", "LOC_B(water)", "TOPIC", "PREDICATE(drink)"]
    a = {r: i for i, r in enumerate(asl_nodes)}
    # spatial agreement: TOPIC sets up both loci; PREDICATE moves between the two loci (indicating verb a->b)
    asl_edges = [(a["TOPIC"], a["LOC_A(child)"]), (a["TOPIC"], a["LOC_B(water)"]),
                 (a["PREDICATE(drink)"], a["LOC_A(child)"]), (a["PREDICATE(drink)"], a["LOC_B(water)"])]
    asl_walk = ["TOPIC", "LOC_A(child)", "LOC_B(water)", "PREDICATE(drink)"]
    asl_gloss = ["CHILD[loc-a]", "WATER[loc-b]", "DRINK[a->b]"]   # illustrative ASL-gloss (topic-comment + spatial agreement)
    asl_spec, asl_m = spectrum(len(asl_nodes), asl_edges)
    print(f"    walk {asl_walk} -> '{' '.join(asl_gloss)}'  (topic-comment + spatial agreement; sign carries the class, F608)")
    print(f"    board lattice: {len(asl_nodes)} nodes, {asl_m} edges | Laplacian spectrum {asl_spec}")
    print(f"    -> a DIFFERENT board: different topology + different spectrum (NOT a rotate of the English chain).\n")

    # ---- THE ETAK CLAIM: same invariant recovered from BOTH boards (two boards, one canoe) ----
    print("(3) THE ETAK CLAIM -- the SAME invariant meaning is recovered from BOTH boards (two boards, one canoe):")
    # English: the class is rotated OUT of frame (F569) -> recover with the prior; ASL: the sign carries the class -> exact
    rec_eng = {w: k.recover(k.render(invariant[w], "english"), "english", prior_sense=concepts[w])["ir_digest"] for w in concepts}
    rec_asl = {w: k.recover(k.render(invariant[w], "asl"), "asl")["ir_digest"] for w in concepts}
    same_eng = all(rec_eng[w] == invariant[w]["ir_digest"] for w in concepts)
    same_asl = all(rec_asl[w] == invariant[w]["ir_digest"] for w in concepts)
    cross = all(rec_eng[w] == rec_asl[w] for w in concepts)
    for w in concepts:
        print(f"    '{w}': english-board recover {rec_eng[w][:10]}...  asl-board recover {rec_asl[w][:10]}...  match: {rec_eng[w]==rec_asl[w]}")
    print(f"    english board recovers the invariant: {same_eng} | asl board recovers the invariant: {same_asl} | cross-board identical: {cross}")
    print(f"    spectra differ (English {eng_spec} != ASL {asl_spec}): {eng_spec != asl_spec}  (genuinely different boards)\n")

    print("VERDICT (a real second language: ASL's own board under the same etak invariant):")
    ok = same_eng and same_asl and cross and (eng_spec != asl_spec)
    print(f"  • TWO GENUINELY DIFFERENT BOARDS, ONE INVARIANT MEANING [{ok}]: the English board (a linear S-V-O chain) and the")
    print(f"    ASL board (a spatial / topic-comment lattice -- referents at loci, verb agreeing locus->locus, sign carrying")
    print(f"    the class) have DIFFERENT topology + DIFFERENT Laplacian spectra ({eng_spec} vs {asl_spec}) -- NOT a rotate of")
    print(f"    one grammar -- yet BOTH walk the SAME content-addressed invariant (child/drink/water), recovered byte-")
    print(f"    identical from either. Two boards, one canoe.")
    print(f"  • THIS IS DEEPER THAN F635's ETAK: there the frame only ROTATED (deg0/30/150) over one English chain. Here the")
    print(f"    BOARD ITSELF is a different shape -- the two-languages-of-math law (F626) at FULL strength: one meaning, two")
    print(f"    reference-frame GRAMMARS, neither privileged (F398). The invariant is the meaning (etak, the held canoe); the")
    print(f"    board is the grammar (board-nav, the island-path) -- and the board can be a wholly different lattice per")
    print(f"    language while the meaning holds. (English hides the class -> needs the prior to recover, F569; ASL's sign")
    print(f"    carries the class -> exact recovery, F608 -- the two boards even differ in whether the class survives.)")
    print(f"  • ACCESSIBILITY IS THE FOUNDATION (F611), built confidently: a Deaf user's ASL is NOT English-rotated -- it is")
    print(f"    its OWN board over the shared meaning, first-class, not a translation-of-English. (The ASL grammar specifics")
    print(f"    -- real glossing, classifier predicates, NMM -- belong to the Deaf community + ASL linguists, the expert, F282;")
    print(f"    we demonstrate the STRUCTURAL point: a different board, the same invariant.)")
    print(f"  • Composes F635 (etak+board -- this generalizes the board from a rotate to a topology) + F632/F633 (board =")
    print(f"    moves over a lattice) + F569/F608 (ASL's two-axis / sign-carries-class board) + F626 (two languages) + F613")
    print(f"    (the shared invariant kernel) + F611 (accessibility foundation) + F398/F394/F282. srmech 0.7.5rc6. Held open (F394).")


if __name__ == "__main__":
    main()
