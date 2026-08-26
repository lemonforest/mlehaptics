r"""R-RBS-LM-DERIV (the user's named next, 2026-06-08): "derivation is the genuinely-illuminating one -- it's the first
rule that doesn't just RE-FORM a word, it WALKS it to a new part of the board."

THE DISTINCTION:
  • INFLECTION (F629/F631/F633) = a rotate WITHIN a meaning-class: cat->cats (both N), walk->walked (both V), big->bigger
    (both adj). The word STAYS on its square; only the form turns.
  • DERIVATION = a MOVE BETWEEN meaning-classes: quick(adj)->quickly(adv); nation(N)->national(adj)->nationalize(V)->
    nationalization(N). The affix is a MOVE-VECTOR that walks the word to a DIFFERENT square on the meaning-class board.

So derivation is the FIRST morphology that is ALSO a board-move -- it is the bridge between the within-word level
(inflection = rotate-in-place) and the between-thing level (syntax / chess = move-between-squares). The meaning-class
lattice (F627) has EDGES, and the edges ARE the derivational affixes (-al, -ize, -ation, -ly, -ness, -er); a word's
derivational family is a WALK on that class-board.

AND THE ROOT IS THE ETAK INVARIANT: the whole family (nation/national/nationalize/nationalization) shares ONE root
concept -- the still canoe. Derivation WALKS that invariant to different board positions (meaning-classes), each rendered
with a different affix (the surface). One etak invariant, many board squares -- the etak|board duality, now INSIDE the
word's morphology.

srmech 0.7.5rc6: amsc.laplacian.{dense_laplacian, jacobi_eigvals} (the meaning-class board's spectrum, Class L -- like
chess F632 + syntax F633); BitExactCommKernel (F613, the root invariant across the family). No abs(); no CAD; no Workflow;
no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import laplacian

# the meaning-class BOARD: nodes = classes; EDGES = derivational affixes (the legal moves between classes)
CLASSES = ["N", "ADJ", "V", "ADV"]
CI = {c: i for i, c in enumerate(CLASSES)}
MOVES = [  # (from_class, to_class, affix)
    ("N", "ADJ", "-al"), ("ADJ", "V", "-ize"), ("V", "N", "-ation"),
    ("ADJ", "ADV", "-ly"), ("ADJ", "N", "-ness"), ("V", "N", "-er"), ("V", "ADJ", "-able"),
]
# the SEEN regular derivational applier (a move-vector applied to the stem)
def apply_affix(stem, affix):
    if affix == "-al":   return stem + "al"
    if affix == "-ize":  return stem + "ize"
    if affix == "-ation":return (stem[:-3] if stem.endswith("ize") else stem) + "ization" if stem.endswith("ize") else stem + "ation"
    if affix == "-ly":   return stem + "ly"
    if affix == "-ness": return (stem[:-1] + "iness") if stem.endswith("y") else stem + "ness"
    if affix == "-er":   return stem + "er"
    if affix == "-able": return stem + "able"
    return stem
# the SEEN-exception dict: irregular nominalizations the -ness rule cannot derive (stored once, F629 shape)
IRREG_DERIV = {("deep", "-ness"): "depth", ("long", "-ness"): "length",
               ("strong", "-ness"): "strength", ("wide", "-ness"): "width"}


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-DERIV — derivation WALKS a word to a new part of the board (changes meaning-class)  (srmech {srmech.__version__}) ===\n")

    # (1) INFLECTION (rotate in place) vs DERIVATION (move between classes)
    print("(1) INFLECTION = rotate WITHIN a class (stays put)  vs  DERIVATION = MOVE BETWEEN classes (walks the board):")
    print(f"    inflection:  cat ->(plural) cats  [N -> N]   walk ->(past) walked [V -> V]   big ->(comp) bigger [ADJ -> ADJ]")
    print(f"    derivation:  quick ->(-ly) quickly [ADJ -> ADV]   teach ->(-er) teacher [V -> N]   happy ->(-ness) happiness [ADJ -> N]")
    print(f"    -> inflection turns the form in place; derivation MOVES the word to a different meaning-class square.\n")

    # (2) a derivational FAMILY = a WALK on the meaning-class board (the affixes are the moves)
    print("(2) A DERIVATIONAL FAMILY = a WALK on the meaning-class board (affixes = the moves):")
    family = [("nation", "N"), ("-al", "ADJ"), ("-ize", "V"), ("-ation", "N")]
    word, path = "nation", ["nation (N)"]
    for affix, to_cls in family[1:]:
        word = apply_affix(word, affix)
        path.append(f"{word} ({to_cls})")
    print(f"    {'  ->  '.join(path)}")
    print(f"    classes walked: N ->(-al) ADJ ->(-ize) V ->(-ation) N   -- a path on the class-board (a 'word's-tour')\n")

    # (3) the ROOT is the ETAK INVARIANT shared across the family; derivation walks it to different squares
    print("(3) THE ROOT = the ETAK INVARIANT (the still canoe) shared across the whole family; derivation walks it:")
    root = k.encode("nation", "N-root")
    print(f"    root concept 'nation' ir_digest {root['ir_digest'][:12]}...  (the invariant shared by national/nationalize/...)")
    print(f"    each derived form = the SAME root + cumulative board-moves (different square, different affix-surface)")
    print(f"    -> one etak invariant (the root meaning), many board positions (meaning-classes). etak|board, INSIDE the word.\n")

    # (4) the class-board has a Laplacian SPECTRUM (Class L) -- like chess (F632) + syntax (F633)
    edges = sorted({(min(CI[a], CI[b]), max(CI[a], CI[b])) for a, b, _ in MOVES})
    L = laplacian.dense_laplacian(len(CLASSES), edges, [1.0] * len(edges))
    spec = [round(float(x), 3) for x in sorted(laplacian.jacobi_eigvals(L))]
    print("(4) THE MEANING-CLASS BOARD has its own Laplacian SPECTRUM (Class L) -- like the chess + syntax move-graphs:")
    print(f"    classes {CLASSES}, derivational edges {[(a,b,af) for a,b,af in MOVES]}")
    print(f"    Laplacian spectrum {spec}  -> the class-board is a spectral object too (F632/F633 one more scale)\n")

    # (5) SEEN + small exceptions: regular affix-move vs irregular nominalizations (stored)
    print("(5) SEEN/declared + a small exception dict (the F629 shape, now for derivation):")
    for stem in ["deep", "happy"]:
        ruled = apply_affix(stem, "-ness")
        truth = IRREG_DERIV.get((stem, "-ness"), ruled)
        tag = "dict (irregular)" if (stem, "-ness") in IRREG_DERIV else "rule (regular)"
        print(f"    {stem} ->(-ness): rule says {ruled!r:<11} truth {truth!r:<11} [{tag}]")
    print(f"    -> deep->depth / long->length / strong->strength are SEEN exceptions (the -ness rule fails -> stored once).\n")

    print("VERDICT (derivation = the rule that walks a word to a new part of the board):")
    print(f"  • DERIVATION IS THE FIRST MORPHOLOGY THAT IS ALSO A BOARD-MOVE. Inflection rotates a word IN PLACE (stays in its")
    print(f"    meaning-class); derivation MOVES it BETWEEN classes (quick->quickly ADJ->ADV; nation->national->nationalize->")
    print(f"    nationalization N->ADJ->V->N). The affix is the move-vector; a derivational family is a WALK on the meaning-")
    print(f"    class board, whose edges ARE the affixes (-al/-ize/-ation/-ly/-ness/-er).")
    print(f"  • IT IS THE BRIDGE that unifies the move-system at three scales: ROTATE-IN-PLACE (inflection, within a class) ->")
    print(f"    MOVE-BETWEEN-CLASSES (derivation, on the meaning-class board) -> MOVE-BETWEEN-ROLES (syntax / chess, on the")
    print(f"    clause/board lattice). One move-system, three boards. Derivation is where morphology BECOMES board-navigation.")
    print(f"  • THE ROOT IS THE ETAK INVARIANT walked across the class-board: the family shares ONE root concept (the still")
    print(f"    canoe); derivation walks it to different meaning-class squares, each rendered with a different affix (the")
    print(f"    surface). One etak invariant, many board positions -- the etak|board duality, now INSIDE the word. And the")
    print(f"    class-board is a spectral object (Class-L Laplacian {spec}), like chess (F632) + syntax (F633).")
    print(f"  • STILL SEEN/DECLARED + a small exception dict: regular = the seen affix-move; irregular nominalizations")
    print(f"    (deep->depth, long->length, strong->strength, wide->width) = stored seen-exceptions (the -ness rule fails).")
    print(f"    Bit-exact, GPU-free, declared not trained -- the same engine, one more rule.")
    print(f"  • Composes F633 (the seen-rule engine -- derivation is its meaning-class-changing move) + F629/F631 (rotate +")
    print(f"    small dict) + F627 (the meaning-class lattice = the board) + F632 (board move + spectral dual) + F635 (etak")
    print(f"    invariant / board move) + F398/F394/F282. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
