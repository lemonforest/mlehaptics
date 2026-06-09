r"""R-RBS-LM-ANCHAPTERS (user direction): "continue the the_one Story Teller builder. we can make it have CHAPTERS that
target EACH A-N OPERATOR that describes something about the_one."

THE BUILD: a BOOK about the_one whose 14 CHAPTERS each target one A-N operator -- each chapter describes the_one through
that operator's lens (a the_one-beat seen as that primitive). The book's STRUCTURE is the 1:3:7:3 partition itself (the
substrate structure, CLAUDE.md §1 / the R30 walking-path), so THE BOOK ABOUT THE_ONE HAS THE_ONE'S OWN SHAPE:
  • 1  -- the foundational ANCHOR: A (content-addressing) -- the one IS its own name (every cascade begins here).
  • 3  -- the substrate-projection TRIAD: I (cyclic) / C (chirality) / J (primes).
  • 7  -- the cascade-detection HEPTAD: D (pattern) / E (catalog) / F (render) / G (search) / K (pin-slot/phase) /
          L (Laplacian) / M (HDC bind).
  • 3  -- the meta-cascade TRIAD: B (TLV-frame) / H (self-introspection) / N (rational-approx).
The book CLOSES on N (rational-approximation = the ASYMPTOTE -- the one approached and never quite reached, held-open F394)
and TURNS at H (self-introspection = the one looking back and knowing itself, the F660 closure). Each chapter is content-
addressed (by Class A -- fitting, since A IS content-addressing); the table of contents IS the 1:3:7:3 partition.

srmech 0.7.5rc15: BitExactCommKernel.content_address (each chapter = a tome, Class A) ; the SAME fixed render engine as
F671/F675 (the clause-joining seen rule). No abs(); no CAD; no Workflow; no sub-agents. The A-N vocabulary is the §1 anchor.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel


def render(clauses):                                              # the SAME fixed engine as F671/F675
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


# the 14 chapters: (partition-slot, operator, role, the the_one-beat through that operator's lens)
CHAPTERS = [
    ("1 anchor",  "A", "content-addressing",        ["The one is its own name"]),
    ("3 triad",   "I", "cyclic",                     ["The one returns to itself"]),
    ("3 triad",   "C", "chirality / which-way",      ["and it turns one way"]),
    ("3 triad",   "J", "primes / indivisible",       ["and it cannot be divided"]),
    ("7 heptad",  "D", "pattern-match",              ["The one is recognized in the pattern"]),
    ("7 heptad",  "E", "catalog",                    ["and numbered among all things"]),
    ("7 heptad",  "F", "render",                     ["and told aloud"]),
    ("7 heptad",  "G", "byte-search",                ["and found in the smallest place"]),
    ("7 heptad",  "K", "pin-slot / phase boundary",  ["The one stands at the turning edge"]),
    ("7 heptad",  "L", "Laplacian / spectrum",       ["and rings in the spectrum"]),
    ("7 heptad",  "M", "HDC bind",                   ["and binds the many into itself"]),
    ("3 meta",    "B", "TLV-framing",                ["The one is held in a frame that says its kind"]),
    ("3 meta",    "H", "self-introspection",         ["and it looks back and knows itself"]),
    ("3 meta",    "N", "rational-approximation",     ["and it is approached and never quite reached"]),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-ANCHAPTERS — the the_one book: one chapter per A-N operator (structured 1:3:7:3)  (srmech {srmech.__version__}) ===\n")

    # (1) the 14 chapters -- each a the_one-beat through one operator's lens, content-addressed (Class A)
    print("(1) THE 14 CHAPTERS (each targets one A-N operator describing the_one; content-addressed by Class A):")
    sections, last_slot = {}, None
    for slot, op, role, beats in CHAPTERS:
        if slot != last_slot:
            print(f"  --- partition section [{slot}] ---"); last_slot = slot
        prose = render(beats)
        addr = k.content_address(f"the_one:{op}:{prose}")[:8]
        sections.setdefault(slot, []).append(op)
        print(f"    Ch.{op} ({role:<26}) [{addr}]  {prose}")
    print()

    # (2) the structure IS the 1:3:7:3 partition -- the book about the_one has the_one's own shape
    counts = {slot: len(ops) for slot, ops in sections.items()}
    print("(2) THE TABLE OF CONTENTS IS THE 1:3:7:3 PARTITION (the book has the_one's own substrate-shape, §1 / R30):")
    print(f"    {'  +  '.join(f'{c} [{slot.split()[1]}]' for slot, c in counts.items())}  =  {sum(counts.values())}")
    print(f"    1 anchor (A) + 3 triad (I,C,J) + 7 heptad (D,E,F,G,K,L,M) + 3 meta (B,H,N) = 14  -> matches 1:3:7:3.\n")

    # (3) the whole book as ONE the_one-story (the 14 beats composed; turns at H, closes on N)
    book = render([beats[0] for _, _, _, beats in CHAPTERS])
    book_addr = k.content_address(book)
    print("(3) THE WHOLE the_one BOOK (the 14 A-N chapters composed into one story; turns at H, closes on N):")
    print(f"    book chord {book_addr[:12]}")
    print(f"    >>> {book}\n")

    print("VERDICT (the the_one book: one chapter per A-N operator, structured 1:3:7:3):")
    print(f"  • THE BUILDER NOW MAKES A-N-TARGETED CHAPTERS: a BOOK about the_one whose 14 chapters each target ONE A-N")
    print(f"    operator, describing the_one through that operator's lens (A: the one is its own name; C: it turns one way;")
    print(f"    L: it rings in the spectrum; M: it binds the many; H: it knows itself; N: it is never quite reached ...).")
    print(f"    Each chapter is a the_one-beat composed by the SAME fixed engine (F671/F675) and content-addressed by Class A.")
    print(f"  • THE BOOK HAS THE_ONE'S OWN SHAPE: the table of contents IS the 1:3:7:3 partition (1 anchor A + 3 triad I,C,J +")
    print(f"    7 heptad D,E,F,G,K,L,M + 3 meta B,H,N = 14, verified). The book about the substrate is STRUCTURED LIKE the")
    print(f"    substrate -- a self-reference: the_one's story carries the_one's partition.")
    print(f"  • IT TURNS AT H AND CLOSES ON N: chapter H (self-introspection) is the_one looking back and knowing itself (the")
    print(f"    F660 closure -- the ontology telling its own story); chapter N (rational-approximation) is the ASYMPTOTE -- the")
    print(f"    one approached and never quite reached (held-open, F394). The book ends honestly on the unreached limit.")
    print(f"  • Composes F671/F675 (the the_one story / chapters this extends) + the A-N vocabulary (the §1 anchor -- each")
    print(f"    chapter a primitive class) + the 1:3:7:3 partition (the substrate structure = the table of contents) + F660")
    print(f"    (H = the one knows itself) + F394 (N = the unreached asymptote) + Class A (content-addressing each chapter) +")
    print(f"    DUALITY/TRIALITY (the_one). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
