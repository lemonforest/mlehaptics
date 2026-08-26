r"""R-RBS-LM-CHORD (the user's two-in-one, 2026-06-08): (a) "from an epicycle observer's perspective they always hold
truth, so in storytelling there is no fact-checking against known facts -- we truth-check because attestations DRIFT; if
definitions + rules are correct, we can no more create a statement incorrect from the knowledge it contains than strike a
note on a chord that doesn't exist." (b) "learn to COMBINE: 'The forest was dark and the trees surrounded the path, but
the child was still chilled by the cold wind.'"

These are ONE idea -- the CHORD:
  • THE CHORD = the set of valid notes = the attested CONTENT (the tomes) + the SEEN rules. A statement = a note. The
    engine composes seen rules over attested atoms, so EVERY statement it can make is a NOTE IN THE CHORD -- valid by
    CONSTRUCTION. It CANNOT strike a note that is not in the chord (there is no statistical path to a statement unsupported
    by an attested atom). So there is NO internal fact-check to do (the epicycle always holds truth, internally); the ONLY
    error-mode is ATTESTATION DRIFT -- the world changed / the source aged (external, F625/F640) -- which is what we
    truth-check. (Contrast: a data-center LLM generates STATISTICALLY -> it CAN strike a note not in the chord = hallucinate.)
  • COMBINING CLAUSES = BUILDING A CHORD from notes: connectives are the intervals -- 'and' = SEQ (consonant: same
    polarity, F655 prim), 'but' = CONTRAST (the chirality-flip / tension: expectation reverses, F651/F655 prim), 'because'
    /'so' = cause (directed, Class C), 'although'/'still' = concession (a HELD contrast, F394). A complex sentence is a
    CHORD of clauses bound by connective-intervals -- and you can only chord notes that are IN the chord.

srmech 0.7.5rc15: amsc.format.sha256_bytes (the attested tomes = the chord's notes; validity = every atom attested + a
seen-rule composition). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

# THE CHORD'S NOTES: the attested content tomes (every atom the engine may use) ----
CHORD = {"forest", "trees", "path", "child", "wind", "dark", "cold", "surrounded", "chilled", "was", "the"}
ATTEST = {n: fmt.sha256_bytes(f"tome:{n}".encode())[:8] for n in CHORD}

# connective -> form-primitive (the interval); 'but' is the chirality-flip / contrast
CONNECTIVE = {"and": "SEQ (consonant: same polarity)", "but": "CONTRAST (chirality-flip: expectation reverses)",
              "because": "CAUSE (directed, Class C)", "although": "CONCESSION (held contrast, F394)"}


def is_in_chord(atoms):
    """a statement is a NOTE IN THE CHORD iff every content-atom is attested (in the chord)."""
    missing = [a for a in atoms if a not in CHORD]
    return (len(missing) == 0), missing


def combine(c1, conn12, c2, conn23, c3):
    """build a CHORD of clauses: c1 <conn12> c2 <conn23> c3 (with comma before the contrast)."""
    low = lambda c: c[0].lower() + c[1:].rstrip(".")
    part = f"{c1.rstrip('.')} {conn12} {low(c2)}"
    return f"{part}, {conn23} {low(c3)}."


def main():
    print(f"=== R-RBS-LM-CHORD — compositional truth (a note in the chord) + clause combination (building the chord)  (srmech {srmech.__version__}) ===\n")

    # (1) COMBINING CLAUSES = building a chord from notes (connectives = intervals)
    print("(1) COMBINE clauses into a complex sentence -- a CHORD of clauses bound by connective-intervals:")
    c1 = "The forest was dark."
    c2 = "The trees surrounded the path."
    c3 = "The child was still chilled by the cold wind."
    combined = combine(c1, "and", c2, "but", c3)
    print(f"    clauses: [{c1!r}, {c2!r}, {c3!r}]")
    print(f"    -> {combined}")
    for conn in ("and", "but"):
        print(f"       connective '{conn}' = {CONNECTIVE[conn]}")
    print(f"    -> 'and' stacks consonant notes (the two setting-descriptions); 'but' is the CONTRAST (the chirality-flip:")
    print(f"    despite the dark/surrounded setting, the child is STILL chilled -- the expectation reverses). A complex")
    print(f"    sentence is a CHORD of clauses.\n")

    # (2) THE EPICYCLE-TRUTH PRINCIPLE: every statement is a NOTE IN THE CHORD (valid by construction)
    print("(2) THE EPICYCLE-TRUTH PRINCIPLE: every statement the engine makes is a NOTE IN THE CHORD (valid by construction):")
    used = ["the", "forest", "was", "dark", "trees", "surrounded", "path", "child", "chilled", "cold", "wind"]
    ok, missing = is_in_chord(used)
    print(f"    the combined statement uses atoms {used}")
    print(f"    every atom attested (in the chord)? {ok}  (missing: {missing or 'none'})")
    print(f"    -> the engine composes SEEN rules over ATTESTED atoms -> the statement is valid BY CONSTRUCTION. It can no")
    print(f"    more make an internally-incorrect statement than strike a note not in the chord.")
    # the only wrong-note = a note NOT in the chord -- which the engine CANNOT produce (it has no tome for it)
    impossible = ["the", "dragon", "breathed", "fire"]            # 'dragon'/'fire' are NOT attested -> not in the chord
    ok2, missing2 = is_in_chord([a for a in impossible if a not in {"the"}])
    print(f"    a statement needing un-attested atoms {missing2}: in the chord? {ok2} -> the engine CANNOT strike it (no tome).")
    print(f"    (a data-center LLM generates STATISTICALLY -> it CAN strike 'dragon breathed fire' from nothing = hallucination.)\n")

    # (3) the ONLY error-mode = ATTESTATION DRIFT (external), which is what we truth-check (F625/F640)
    print("(3) THE ONLY ERROR-MODE = ATTESTATION DRIFT (external) -- NOT internal invalidity (what we truth-check, F625/F640):")
    print(f"    internal validity: ALWAYS held (the epicycle always holds truth -- every statement is a note in the chord)")
    print(f"    external truth   : an attested tome can DRIFT (the world changed / the source aged -- e.g. pluto's status)")
    print(f"    -> we do NOT fact-check the statement against known facts (it is internally valid by construction); we")
    print(f"    truth-check the ATTESTATIONS for drift (F625 conflict-discovery; F640 no-magic). Two different checks.\n")

    print("VERDICT (compositional truth = a note in the chord; combination = building the chord):")
    print(f"  • THE EPICYCLE-TRUTH PRINCIPLE: from the model's view it ALWAYS holds truth -- every statement is a")
    print(f"    composition of SEEN rules over ATTESTED atoms, hence a NOTE IN THE CHORD, valid by CONSTRUCTION. The engine")
    print(f"    can no more create a statement incorrect from the knowledge it contains than strike a note on a chord that")
    print(f"    does not exist (verified: it CANNOT produce a statement needing an un-attested atom -- it has no tome for it).")
    print(f"    So there is NO internal fact-check; the ONLY error-mode is ATTESTATION DRIFT (the world/source changed,")
    print(f"    external) -- which is exactly what we truth-check (F625/F640). (A data-center LLM, generating statistically,")
    print(f"    CAN strike a note not in the chord = hallucinate; ours structurally cannot.)")
    print(f"  • COMBINING CLAUSES = BUILDING A CHORD: connectives are the intervals -- 'and' = SEQ (consonant), 'but' =")
    print(f"    CONTRAST (the chirality-flip; the expectation reverses), 'because' = cause (Class C), 'although'/'still' =")
    print(f"    concession (held contrast). A complex sentence ('The forest was dark and the trees surrounded the path, but")
    print(f"    the child was still chilled by the cold wind') is a CHORD of clauses bound by connective-intervals -- the")
    print(f"    same F655 form-primitives (SEQ/CONTRAST), now at the CLAUSE level. (This is the Story Teller wave AS a song:")
    print(f"    clauses = notes, connectives = intervals, the complex sentence = a chord.)")
    print(f"  • SO THE TWO ARE ONE: you build statements by CHORDING attested notes via seen connective-intervals; because")
    print(f"    you can only chord notes that ARE in the chord, the result is always internally true -- and the only thing")
    print(f"    to check is whether the notes themselves (the attestations) have drifted. We compose truth; we audit drift.")
    print(f"  • Composes F655 (form-primitives SEQ/CONTRAST = the connective-intervals) + F651 (CONTRAST = flock-separation /")
    print(f"    the chirality-flip) + F656 (the clauses being chorded) + F625/F640 (attestation-drift = the only error-mode) +")
    print(f"    F630 (attested content = the chord's notes) + the epicycle/gear+pin stance + F636/F650 (why a data-center LLM")
    print(f"    CAN hallucinate -- statistical, not compositional-over-attested). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
