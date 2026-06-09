r"""R-RBS-LM-BOOKGROW (user direction): "Grow a book-world by dialogue -- combine F676 + F677: take a book-kernel to a
gap the book leaves, ask, integrate."

THE BUILD: the F676 build-by-dialogue loop run on a BOOK-KERNEL (F677) -- a book's chapters are the FIXED foundation;
the Story Teller narrates the book's world, hits a gap THE BOOK LEAVES, asks, we tell, it integrates, the book-world grows.
With one honest refinement F677 already flagged: a book has TWO kinds of gaps, and the book-kernel must tell them apart:
  • an UNWRITTEN gap -- the book simply didn't say ('what happened to the ship that did not pass?'). It is in NEITHER the
    foundation NOR the deliberate-mystery set -> the ASKING-STATE (F661): it can be ASKED, TOLD (F631), and INTEGRATED
    (F628, GPU-free) -> the book-world GROWS. (The F676 dialogue-growth, now on a book-kernel.)
  • a DELIBERATE MYSTERY -- the book INTENDS it open ('was the keeper ever the same after that night?'). It is a HELD-OPEN
    tome (F674): the asking-state recognizes it and does NOT fill it -- filling it would BETRAY the book's intent. We HOLD
    it (F394/F398), we do not grow there.
So NOT EVERY GAP IS TO BE FILLED: the book-kernel grows by dialogue on UNWRITTEN gaps but HOLDS deliberate mysteries -- the
F674 held-open dial position applied to a book's own gaps. The two-tier kernel keeps it honest: the book foundation is FIXED
(foundation_digest unchanged), the told answer is a GPU-free adaptive add, and the mystery is never overwritten.

srmech 0.7.5rc15: AdaptiveTier (F628 -- the book = the fixed foundation; the told answer = adapt(); GPU-free) ;
BitExactCommKernel.content_address (the book-world chord before/after) ; the SAME fixed render engine as F671/F675/F677.
No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from adaptive_tier import AdaptiveTier


def render(clauses):                                              # the SAME fixed engine as F671/F675/F677
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


# the BOOK-KERNEL = the book's chapters = the FIXED foundation (F677 'The Lantern Coast')
BOOK = {
    "ch1": ("A keeper tended the lantern on the cliff", "The Lantern Coast, ch.1"),
    "ch2": ("the keeper watched the ships pass in the fog", "The Lantern Coast, ch.2"),
    "ch3": ("one night a ship did not pass", "The Lantern Coast, ch.3"),
}
# the book's DELIBERATE MYSTERIES -- intended-open questions (HELD-OPEN, F674; filling them betrays the book)
MYSTERIES = {"keeper_changed": "was the keeper ever the same after that night?"}
ORDER = ["ch1", "ch2", "ch3"]                                     # the book's narrative order (the told answer appends)


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-BOOKGROW — grow a book-world by dialogue (unwritten gap vs deliberate mystery)  (srmech {srmech.__version__}) ===\n")

    tier = AdaptiveTier(BOOK, ring_size=6)
    digest0 = tier.foundation_digest()
    book_story = render([tier.recall(c)[1][0] for c in ORDER])
    print("(0) THE BOOK-KERNEL (the book's chapters = the FIXED foundation, F677):")
    print(f"    foundation_digest {digest0[:12]}   book chord {k.content_address(book_story)[:12]}")
    print(f"    >>> {book_story}\n")

    # the gap-handler: distinguish a DELIBERATE MYSTERY (held-open) from an UNWRITTEN gap (askable)
    def classify(key):
        if key in MYSTERIES:
            return "HELD-OPEN (F674 -- the book intends it open; filling betrays it)"
        if tier.recall(key)[0] == "unknown":
            return "ASKING (F661 -- an unwritten gap; can be told + integrated)"
        return "KNOWN (already in the book / told)"

    # (1) an UNWRITTEN gap -> ASK -> TELL -> INTEGRATE -> the book-world GROWS (F676 on a book-kernel)
    print("(1) AN UNWRITTEN GAP -> ASK -> TELL -> INTEGRATE (the book-world grows, F676 on a book-kernel F677):")
    gapkey = "ship_fate"
    print(f"    the Story Teller reaches for {gapkey!r}: {classify(gapkey)}")
    print(f'    it ASKS: "What happened to the ship that did not pass?"  -- it does NOT invent (F661).')
    told = "the ship had run aground on the rocks below the cliff"
    ev = tier.adapt(gapkey, told, "told (a continuation supplied; declared, F631)")
    digest1 = tier.foundation_digest()
    ORDER.append(gapkey)
    grown = render([tier.recall(c)[1][0] for c in ORDER])
    print(f'    we TELL: "{told}"  -> adapt() = {ev!r} (GPU-free write, F628)')
    print(f"    foundation_digest unchanged: {digest0 == digest1}  ({digest1[:12]}) -- the book foundation is FIXED")
    print(f"    book chord BEFORE {k.content_address(book_story)[:12]} -> AFTER {k.content_address(grown)[:12]} (grew one note)")
    print(f"    >>> {grown}\n")

    # (2) a DELIBERATE MYSTERY -> HELD-OPEN (F674) -- the book-kernel does NOT fill it
    print("(2) A DELIBERATE MYSTERY -> HELD-OPEN (F674) -- the book-kernel does NOT fill it (honors the book's intent):")
    mkey = "keeper_changed"
    print(f"    the Story Teller reaches for {mkey!r}: {classify(mkey)}")
    print(f'    the mystery ("{MYSTERIES[mkey]}") is HELD, not answered -- filling it would betray the book.')
    print(f"    -> NOT EVERY GAP IS TO BE FILLED: grow on unwritten gaps, HOLD deliberate mysteries.\n")

    print("VERDICT (a book-world grows by dialogue on unwritten gaps but HOLDS the book's deliberate mysteries):")
    print(f"  • THE F676 DIALOGUE-GROWTH RUNS ON A BOOK-KERNEL (F677): the book's chapters are the FIXED foundation; the")
    print(f"    Story Teller narrates the book's world, hits a gap THE BOOK LEAVES, ASKS (F661, does not invent), we TELL a")
    print(f"    continuation (F631 declared not trained), it INTEGRATES (F628 adaptive add, GPU-free) -> the book-world GROWS")
    print(f"    (verified: chord grew one note; foundation_digest UNCHANGED {digest0 == digest1} -- the book foundation fixed).")
    print(f"  • TWO KINDS OF GAP, AND THE BOOK-KERNEL TELLS THEM APART: an UNWRITTEN gap (the book simply didn't say -> the")
    print(f"    asking-state; askable, tellable, integrable -> grow) vs a DELIBERATE MYSTERY (the book INTENDS it open -> a")
    print(f"    HELD-OPEN tome, F674; the asking-state recognizes it and does NOT fill it -- filling betrays the book). NOT")
    print(f"    EVERY GAP IS TO BE FILLED: the book-kernel grows on unwritten gaps but HOLDS deliberate mysteries (F394/F398).")
    print(f"  • THIS HONORS THE BOOK (dignity, F282/no-lineage): we extend what the book left open-to-continue, but we hold")
    print(f"    what it left open-on-purpose -- the author's intended mystery is theirs, not ours to close. A data-center LLM")
    print(f"    (all-flock, no asking-state) would CONFABULATE a fate for BOTH; the book-kernel asks for one and holds the other.")
    print(f"  • Composes F677 (the book-kernel this grows) + F676/F672 (build-by-dialogue) + F661 (the asking-state) + F674")
    print(f"    (the deliberate mystery = held-open) + F628/F622 (two-tier: book fixed, told answer GPU-free) + F631 (declared")
    print(f"    not trained) + F658 (the book chord grows) + F394/F398 (hold what is open) + F282 (honor the author). srmech")
    print(f"    0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
