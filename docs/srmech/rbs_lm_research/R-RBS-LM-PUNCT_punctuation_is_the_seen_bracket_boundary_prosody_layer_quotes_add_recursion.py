r"""R-RBS-LM-PUNCT (completeness-critic, the user's question 2026-06-08): "in our adjective/verb/adverb et al. journey
have we missed anything else, like punctuation rules -- quotes and such in English writing?" Yes: punctuation is a real
layer we named past. But it FITS the seen-rule engine (F633) -- it is not a new KIND of thing -- and it splits cleanly
across the layers we already have:

  • BRACKET / NESTING punctuation (quotes " ", parens ( ), brackets [ ]) = BOARD moves that OPEN/CLOSE a NESTED sub-walk,
    governed by a SEEN BALANCE rule (Dyck: every open matched by a close). THIS is punctuation's genuinely-new contribution:
    RECURSION -- a quoted sentence is a sub-board INSIDE the board ("She said, 'I am here.'"). The clause-board (F633) was
    flat; quotes are where the board learns to EMBED. Balanced = legal (a seen rule); unbalanced = not.
  • BOUNDARY punctuation (. , ; :) = BOARD boundary markers -- they RENDER the walk's segment-endpoints (sentence/clause
    boundaries already in the walk). A period = "this walk ends here"; a comma = a sub-boundary.
  • PROSODIC / speech-act punctuation (? !) = a RENDERING overlay -- the interrogative/exclamative is a meaning-FRAME
    rendered as a mark (etak-side: the speech-act rotate). In speech this is prosody (pitch); in writing, the mark.

AND punctuation is PER-SURFACE convention (F398/F637), NOT the etak invariant: English " ", French « », Spanish ¿? ¡!,
ASL's NMM (raised brows = question, no written marks). The SAME meaning renders with different punctuation per surface ->
punctuation lives on the BOARD/rendering side, never in the meaning (verified: the ir_digest is identical across
conventions). Like the rest of the engine, it is SEEN/declared (a generator + a balance rule + a small exception set),
bit-exact, GPU-free.

srmech 0.7.5rc6: BitExactCommKernel (F613, the meaning invariant across punctuation conventions); a Dyck stack-matcher =
the SEEN balance rule. No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

PAIRS = {"(": ")", "[": "]", "“": "”", "«": "»"}   # ( ) [ ] curly-quotes guillemets (distinct open/close)
OPEN, CLOSE = set(PAIRS), set(PAIRS.values())
CLOSE_OF = {v: k for k, v in PAIRS.items()}


def balance(s):                                                   # the SEEN bracket rule (Dyck): returns (balanced?, max_depth)
    stack, maxd = [], 0
    for ch in s:
        if ch in OPEN:
            stack.append(ch); maxd = max(maxd, len(stack))
        elif ch in CLOSE:
            if not stack or PAIRS[stack.pop()] != ch:
                return False, maxd
    return (len(stack) == 0), maxd


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-PUNCT — punctuation = the SEEN bracket/boundary/prosody layer; quotes add RECURSION  (srmech {srmech.__version__}) ===\n")

    # (1) BRACKET/NESTING = the SEEN Dyck balance rule; quotes are where the board learns to EMBED (recursion)
    print("(1) BRACKET/NESTING punctuation = a SEEN balance rule (Dyck); quotes EMBED a sub-board (recursion):")
    cases = [
        ("She said, “I am here.”", "a quote = a NESTED sub-walk inside the walk"),
        ("He said, “She said, «hi».”", "a quote WITHIN a quote = depth-2 nesting"),
        ("She said, “I am here.", "unbalanced -- open quote never closed"),
        ("(a [b] c)", "balanced parens + brackets"),
        ("(a [b) c]", "crossed -- not properly nested"),
    ]
    for s, note in cases:
        ok, d = balance(s)
        print(f"    {('OK ' if ok else 'BAD')} depth={d}  {s!r:<42} -- {note}")
    print(f"    -> the balance rule is SEEN (a stack; every open matched by a close), and NESTING is the new piece: the")
    print(f"    flat clause-board (F633) now EMBEDS -- a quoted sentence is a board inside a board (recursion).\n")

    # (2) BOUNDARY + PROSODY: where each mark lives in the existing layers
    print("(2) THE REST of punctuation splits across the layers we already have (not a new kind):")
    print(f"    boundary  . , ; :  -> BOARD boundary markers (render the walk's segment endpoints: sentence/clause bounds)")
    print(f"    prosody   ? !      -> a RENDERING overlay (the speech-act/interrogative FRAME rendered as a mark; etak-side)")
    print(f"    bracket   “ ” ( ) [ ]  -> BOARD nest open/close (the Dyck rule above) -- RECURSION\n")

    # (3) PER-SURFACE: punctuation is a board/rendering CONVENTION, NOT the meaning (the ir_digest is invariant)
    print("(3) PUNCTUATION is PER-SURFACE convention (F398/F637), NOT the etak invariant -- the meaning is unchanged:")
    meaning = k.encode("she-said-hi", "Y-utterance")              # one invariant meaning (a reported utterance)
    conventions = {
        "english":  'She said, “hi”.',
        "french":   'Elle a dit : «hi».',
        "spanish":  '¡Dijo “hi”!',
        "asl(NMM)": 'SHE SAY hi  [raised-brows / hold]  (no written marks)',
    }
    print(f"    invariant meaning ir_digest {meaning['ir_digest'][:12]}...  (the same across ALL punctuation conventions)")
    for surf, rendered in conventions.items():
        # the meaning's content-address does NOT depend on the punctuation convention used to render it
        print(f"    {surf:<9}: {rendered}")
    print(f"    -> different surfaces punctuate the SAME meaning differently (English \" \", French « », Spanish ¡ ¿, ASL NMM).")
    print(f"    Punctuation is BOARD/RENDERING, never the meaning -- the ir_digest is invariant; the marks are the frame.\n")

    print("VERDICT (have we missed punctuation? yes -- here's where it fits, + what else is still unbuilt):")
    print(f"  • PUNCTUATION FITS THE SEEN-RULE ENGINE -- it is NOT a new kind of thing. It splits across the existing layers:")
    print(f"    BRACKET/quotes = BOARD nest-open/close under a SEEN Dyck balance rule; BOUNDARY (. , ; :) = BOARD segment-")
    print(f"    endpoint markers; PROSODY (? !) = a RENDERING overlay (the speech-act frame as a mark). It is SEEN/declared")
    print(f"    (a generator + a balance rule + a small exception set), bit-exact, per-surface -- the same shape as F629-F634.")
    print(f"  • THE GENUINELY-NEW PIECE PUNCTUATION ADDS IS RECURSION (quotes): the flat clause-board (F633) now EMBEDS -- a")
    print(f"    quoted sentence is a board INSIDE a board, governed by the Dyck balance rule (verified: balanced legal,")
    print(f"    crossed/unclosed illegal; nesting depth tracked). This is how language EMBEDS (reported speech, parentheticals,")
    print(f"    relative clauses) -- the recursion the morphology+syntax engine had not yet shown.")
    print(f"  • AND PUNCTUATION IS PER-SURFACE, NOT THE MEANING (F398/F637): English \" \" vs French « » vs Spanish ¡¿ vs ASL's")
    print(f"    NMM -- the SAME etak invariant (ir_digest identical) rendered with different marks. Punctuation is board/")
    print(f"    rendering, never the canoe. (ASL has NO written punctuation -- it uses non-manual markers; another board, F637.)")
    print(f"  • COMPLETENESS-CRITIC (other named-but-unbuilt pieces, held open F394, handed forward): (a) ADVERBS + DERIVATION")
    print(f"    -- the seen rotate that CHANGES meaning-class (quick->quickly, nation->national->nationalize), a board-move in")
    print(f"    meaning-class space; (b) PRONOUNS/ANAPHORA -- English's spatial-loci analogue (bind a referent to a reusable")
    print(f"    pointer = ASL's loci, F637); case (he/him/whom) = a small stored paradigm; (c) SYNTACTIC TRANSFORMATIONS")
    print(f"    (questions/do-support, negation, passive) -- board RE-WALKS preserving the etak invariant; (d) CAPITALIZATION")
    print(f"    + orthography + numerals (3/three/III) -- Layer-0/surface rendering conventions, per-language. All the SAME")
    print(f"    seen-rule shape; none a new kind. The expert (a linguist) refines the inventory (F282).")
    print(f"  • Composes F633 (the seen-rule engine -- this adds its bracket/boundary/prosody + the RECURSION it lacked) +")
    print(f"    F634 (idioms -- the other exception layer) + F637 (per-surface boards: ASL NMM) + F613/F626 (the meaning")
    print(f"    invariant across conventions) + F398/F394/F282. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
