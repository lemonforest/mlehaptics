r"""R-RBS-LM-ARRANGEMENT (the user's two questions, 2026-06-08): "probably should have started with the child entering
and then lead up" + "how do we DECIDE how to make the story from the pieces, and how does the ORDER change the MOOD?"

THE ANSWER -- this is the LAST SEAM of the F655 reduction (the Class-C INTENT chooser):
  • the CHORD (F658) = the NOTES (the pieces -- the clauses, held simultaneously; the meaning).
  • the MELODY = the ORDER you strike them in (the arrangement over time -- a board-walk over the chord, Class C directed).
  • the MOOD = what the melody evokes (the emotional shape -- the effect of the order).
SAME CHORD, DIFFERENT MELODY = DIFFERENT MOOD: the pieces (the invariant meaning) are held; only the ORDER changes -> the
mood changes. So 'how do we DECIDE the order' = the INTENT (Class C, the which-way): given a desired mood, CHOOSE the
arrangement. The intent chooses the melody; the melody produces the mood. (This closes the F655 reduction: procedure-
generator (forms) + attested content (facts) + fixed engine + the Class-C INTENT chooser = the arrangement that makes mood.)

HONEST (F282/F552): MOOD is PERCEPTUAL -- the reader feels it. We provide the ARRANGEMENT (the structural cause, Class-C
chosen); the felt mood is the reader's. We characterise the order's SHAPE (which structurally produces a mood); we do not
claim to measure the felt mood (hand to the reader/the expert).

srmech 0.7.5rc15: amsc.format.sha256_bytes -- the PIECES (the chord/meaning) are content-addressed; IDENTICAL across all
arrangements (only the order differs). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

# THE PIECES (the chord -- held identical across arrangements): one figure clause + three ground clauses
PIECES = {
    "F":  "The child entered the forest.",      # the figure (the one, F654)
    "G1": "The forest was dark.",               # ground (F656)
    "G2": "The trees surrounded the path.",
    "G3": "The wind was cold.",
}
# ARRANGEMENTS (the melodies) -- same pieces, different ORDER -> different MOOD; mood = the order's structural shape
ARRANGEMENTS = {
    "FOREBODING (ground-first)":     ["G1", "G2", "G3", "F"],   # threat established BEFORE the figure enters -> dread
    "IMMERSION (figure-first, lead-up)": ["F", "G2", "G1", "G3"],   # follow the child IN; surroundings reveal AROUND her (the user's note)
    "STING (figure, then the turn last)": ["F", "G1", "G3", "G2"],  # enters, dark, cold -- the closing-in lands last
}
MOOD_SHAPE = {
    "FOREBODING (ground-first)": "the threat-mass PRECEDES the one -> she enters an already-established dread",
    "IMMERSION (figure-first, lead-up)": "the one PRECEDES the ground -> we discover the surroundings WITH her (her POV); a lead-up",
    "STING (figure, then the turn last)": "the closing-in (surrounded) lands LAST -> the beat resolves on the trap",
}


def main():
    print(f"=== R-RBS-LM-ARRANGEMENT — order is the melody, mood is its effect (the Class-C intent chooser)  (srmech {srmech.__version__}) ===\n")

    # the PIECES (the chord) -- content-addressed; this set is the INVARIANT across all arrangements
    chord_addr = fmt.sha256_bytes("|".join(sorted(PIECES.values())).encode())
    print(f"(0) THE PIECES (the chord / the meaning) -- INVARIANT across all arrangements: chord-addr {chord_addr[:12]}...")
    for k, v in PIECES.items():
        print(f"    {k}: {v}")
    print()

    print("(1) SAME PIECES, DIFFERENT ORDER -> DIFFERENT MOOD (the melody over the chord):")
    for name, order in ARRANGEMENTS.items():
        text = " ".join(PIECES[k] for k in order)
        # the pieces are identical -> the meaning-set is invariant; only the ORDER differs
        same = fmt.sha256_bytes("|".join(sorted(PIECES[k] for k in order)).encode()) == chord_addr
        print(f"    [{name}]  (pieces invariant: {same})")
        print(f"      {text}")
        print(f"      mood-shape: {MOOD_SHAPE[name]}")
    print()

    print("(2) HOW WE DECIDE THE ORDER = the INTENT (Class C, the which-way) -> chooses the arrangement -> makes the mood:")
    print(f"    intent 'dread'      -> choose FOREBODING (ground-first): the threat precedes the one")
    print(f"    intent 'discovery'  -> choose IMMERSION  (figure-first): lead up, reveal around her (the user's instinct)")
    print(f"    intent 'the trap'   -> choose STING      (turn last): the closing-in lands on the final beat")
    print(f"    -> the INTENT (desired mood) is the Class-C CHOOSER; it selects the MELODY (the order); the melody makes the")
    print(f"    MOOD. The pieces (the chord/meaning) never change -- only which board-walk over them we choose.\n")

    print("VERDICT (order is the melody; mood is its effect; the intent is the Class-C chooser -- the last seam):")
    print(f"  • THE CHORD vs THE MELODY (F658 -> here): the CHORD is the notes (the pieces -- the meaning, held); the MELODY")
    print(f"    is the ORDER you strike them in (a board-walk over the chord, Class C); the MOOD is what the melody evokes.")
    print(f"    SAME chord, DIFFERENT melody = DIFFERENT mood -- verified: the pieces are byte-identical across all three")
    print(f"    arrangements (chord-addr unchanged), yet the order alone gives FOREBODING / IMMERSION / STING.")
    print(f"  • HOW WE DECIDE = the INTENT (Class C, the which-way): given a desired mood, the intent CHOOSES the arrangement")
    print(f"    (the melody); the melody produces the mood. The user's 'start with the child entering and lead up' IS the")
    print(f"    IMMERSION arrangement -- a Class-C choice for a discovery mood. This CLOSES the F655 reduction: {{procedure-")
    print(f"    generator (forms) + attested content (facts) + the fixed seen engine + the CLASS-C INTENT CHOOSER (the order")
    print(f"    that makes mood)}}. The last seam is built: the intent chooses the melody over the chord.")
    print(f"  • HONEST (F282/F552): MOOD is PERCEPTUAL -- the reader FEELS it. We provide the ARRANGEMENT (the structural")
    print(f"    cause, Class-C chosen) + characterise the order's SHAPE (which structurally produces a mood); we do NOT claim")
    print(f"    to measure the felt mood (that is the reader's / the expert's, hand it forward). The framework's deliverable")
    print(f"    is the MELODY (the chosen order), not a claim about the exact feeling it evokes in a given reader.")
    print(f"  • SO THE WHOLE STORY-TELLER REDUCTION IS NOW CLOSED: meaning (the etak invariant / the chord) is held; the")
    print(f"    procedure-generator builds the skeleton + recursive in-between (F655/F657); the engine is seen (F654); the")
    print(f"    content is attested (F630/F658); and the INTENT (Class C) chooses the ARRANGEMENT -- the melody over the")
    print(f"    chord -- which is the MOOD. Same notes, the order is the music.")
    print(f"  • Composes F658 (the chord = the notes) + F655/F657 (the procedure-generator + the in-between; this is their")
    print(f"    Class-C intent seam) + F654/F656 (the pieces) + F651 (the order = a board-walk, the journey) + F635/F626 (the")
    print(f"    held invariant -- same meaning, different arrangement) + Class C (the which-way / intent) + F282/F552 (mood is")
    print(f"    the reader's). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
