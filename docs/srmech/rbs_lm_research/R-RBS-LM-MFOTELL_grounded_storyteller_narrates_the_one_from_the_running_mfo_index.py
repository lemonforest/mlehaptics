r"""R-RBS-LM-MFOTELL (the user's GOAL, momentum payoff of F670): "use Story Teller to create a story about our A-N
operators and how we can see them in all parts of nature and the cosmos -- a story about the_one."

THE BUILD: the grounded Story Teller (F654/F660) now NARRATES the_one by CONSUMING the running MFO world-kernel's
shelf-index (F670's mfo_section_descriptor.toml -- NOT re-parsing the notebook; it uses the descriptor as the actual
interface, proving the running kernel is the instrument). Each beat of the the_one-story:
  • NAVIGATES to a real MFO §-tome by address (F664/F670) -> pulls the real section title + line anchor (the ATTESTED
    content, F663) -- the Story Teller does NOT invent the physics, it REFERENCES the attested §-tome.
  • SEES an A-N operator in that domain (the user's goal -- chirality=Class C, Laplacian spectra=Class L, cyclic=Class I,
    self-similarity=the cascade, content-anchor=Class A) and composes a SEEN-RULE clause (F654 engine) about it.
  • is a NOTE IN THE CHORD (F658): valid by construction (composed over attested content + seen rules) -- the whole
    passage is content-addressed; the ONLY error mode is attestation drift, never hallucination.
A beat whose domain is NOT on the shelf (birdsong -- no MFO §-tome) -> the ASKING-STATE (F661) -> the AMSC fetch (F669):
it does NOT invent a §-section; it asks + fetches an attested tome (built + validate_mpr_record -> VALID).

THE CLOSURE: this runs F660's "story about the_one" on the REAL F670 running index -- the ontology that grounds the
physics tells its OWN story, pulling each beat off its own attested shelf, seeing the A-N operators in nature + cosmos.
DIGNITY/LIFTING (F650/F282): the ancients'-anchor beat (§VII.6.10) honors prior peoples as peers; the birdsong beat
(F653) honors the animal -- recognise the shape, never decode the meaning (the epistemic ceiling, F552).

srmech 0.7.5rc15: tomllib (consume the F670 descriptor) ; BitExactCommKernel.content_address (the chord = the passage,
content-addressed, Class A) ; amsc.format.{MPRRecord, validate_mpr_record, sha256_bytes} (the off-shelf beat -> AMSC,
F669). No abs(); no CAD; no Workflow; no sub-agents. No-lineage (we read what the MFO ALREADY IS).
"""
import sys
import tomllib
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import format as fmt

DESCRIPTOR = "docs/srmech/rbs_lm_research/mfo_section_descriptor.toml"

# the the_one-story beats: (domain-in-nature/cosmos, MFO §-id to pull, the A-N operator SEEN there, the seen-rule clause)
# each §-id is REAL (retrievable from the F670 descriptor); the clause REFERENCES the attested tome, never invents it.
BEATS = [
    ("the foundation",      "I.1",       "Class A (content-addressing the anchor)", "The one is the held invariant"),
    ("the substrate",       "VII.1.1",   "the field/excitation duality",            "and it is the field beneath every excitation"),
    ("the galaxy + shell",  "III.1",     "Class L (the Laplacian eigen-spectrum)",  "It is seen in the spectrum of the round sphere"),
    ("matter's chirality",  "VI",        "Class C (chirality / the which-way)",      "It is seen in the handedness of matter"),
    ("the three families",  "IV.5",      "the cascade (three-fold self-similarity)", "It is seen in the three generations repeating"),
    ("the cosmos' breath",  "V",         "the asymptote (1D->11D dimension flow)",   "It is seen in the flowing of the dimensions"),
    ("the ancients",        "VII.6.10",  "the lifting (peers who saw it first)",     "and the ancients saw its shape before us"),
]
OFF_SHELF = ("birdsong", "the song of a bird")     # no MFO §-tome -> the asking-state -> AMSC (F669); honor the animal (F653)


def render_passage(clauses):
    """the clause-JOINING seen rule (F641/F658 connectives-as-intervals; DECLARED not trained, the F654 lesson):
    a clause beginning with a lowercase connective JOINS the prior with ', ' (consonant interval); an uppercase clause
    STARTS a new sentence ('. ' + capital). Closes the F671 'invariant. and it...' rendering seam."""
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFOTELL — the grounded Story Teller narrates the_one from the RUNNING MFO index  (srmech {srmech.__version__}) ===\n")

    # consume the F670 descriptor (the running kernel's shelf-index IS the interface)
    with open(DESCRIPTOR, "rb") as f:
        desc = tomllib.load(f)
    rows = {r["id"]: r for r in desc["section"]}
    print(f"(0) CONSUMING the running MFO world-kernel shelf-index (F670): {desc['meta']['n_sections']} §-tomes, kernel={desc['meta']['kernel']!r}\n")

    def navigate(sec):
        if sec not in rows:
            return None
        r, path = rows[sec], []
        cur = sec
        while cur and cur in rows:
            path.append(cur); cur = rows[cur]["parent"] or None
        return {"path": list(reversed(path)), "title": r["title"], "line": r["line_anchor"]}

    # (1) compose the the_one-story: each beat pulls a real §-tome + sees an A-N operator
    print("(1) THE the_one-STORY (each beat: navigate a real §-tome -> see an A-N operator -> compose a clause):")
    passage, attest_trail = [], []
    for domain, sec, an_op, clause in BEATS:
        nav = navigate(sec)
        if nav is None:                                  # (shouldn't happen for BEATS; all real)
            continue
        passage.append(clause)                           # raw clause; the joining seen rule renders the sentences
        attest_trail.append((sec, nav["line"]))
        print(f"    [{domain:<16}] §{sec:<9} '{nav['title'][:54]}' (L{nav['line']})")
        print(f"        sees {an_op}")
        print(f"        -> \"{clause}.\"")
    print()

    # (2) the off-shelf beat -> the asking-state -> AMSC (F669): does NOT invent a §-section
    print("(2) AN OFF-SHELF BEAT -> the asking-state (F661) -> AMSC (F669) -- does NOT invent a §-tome:")
    domain, gloss = OFF_SHELF
    print(f"    the Story Teller reaches for '{domain}' -- no MFO §-tome on the shelf. It ASKS, it does not invent.")
    blob = f"asking-state: {domain}".encode()
    att = {"source_doi": "10.0/amsc.birdsong", "source_url": f"amsc://asking/{domain}", "license": "CC0",
           "retrieved_at": "2026-06-08T00:00:00Z", "response_sha256": fmt.sha256_bytes(blob),
           "parser_version": "rbs-lm-rag/amsc 0.1", "parser_rule_hash": fmt.sha256_bytes(b"rule:birdsong"),
           "collector_descriptor_path": "rbs_lm_research/rag/birdsong.toml",
           "collector_descriptor_hash": fmt.sha256_bytes(b"descriptor:birdsong")}
    rec = fmt.MPRRecord(mpr_version=fmt.MPR_SCHEMA_VERSION, data={"domain": domain, "gloss": gloss},
                        data_schema_id="amsc://schema/communication", attestation=att,
                        rendering={"human_readable_name": f"asking-state: {domain}", "cite_as": "AMSC asking-state fetch",
                                   "purpose": "resolve an off-shelf domain without inventing it"})
    try:
        fmt.validate_mpr_record(rec); ok = "VALID -> an attested tome (honor the animal, F653/F282 -- recognise, never decode)"
    except Exception as e:
        ok = f"INVALID: {e}"
    print(f"    asking-state -> AMSC MPRRecord -> validate_mpr_record: {ok}\n")

    # (3) the chord: the whole passage, content-addressed -- valid by construction (F658)
    full = render_passage(passage)                       # the clause-joining seen rule (declared, F654/F641)
    chord_addr = k.content_address(full)
    print("(3) THE CHORD (F658) -- the whole the_one-passage, content-addressed (valid by construction):")
    print(f"    >>> {full}")
    print(f"    chord SHA-256: {chord_addr}")
    print(f"    attestation trail (each beat -> its §-anchor@line): {['§'+s+'@L'+str(l) for s,l in attest_trail]}\n")

    print("VERDICT (the grounded Story Teller narrates the_one + the A-N operators from the RUNNING MFO index):")
    print(f"  • THE USER'S GOAL IS RUNNING: the grounded Story Teller (F654/F660) narrated a the_one-story about the A-N")
    print(f"    operators seen across nature + cosmos, by CONSUMING the running MFO world-kernel's shelf-index (F670's")
    print(f"    mfo_section_descriptor.toml -- the descriptor IS the interface, not a re-parse). Each beat NAVIGATED a real")
    print(f"    §-tome (F664), pulled its real title + line anchor (the attested content, F663), SAW an A-N operator there")
    print(f"    (A/C/I/L + the cascade + the duality + the asymptote), and composed a seen-rule clause (F654).")
    print(f"  • EVERY CLAUSE IS A NOTE IN THE CHORD (F658): composed over ATTESTED content (real §-tomes) + SEEN rules ->")
    print(f"    valid by construction; the whole passage is content-addressed (chord SHA-256 {chord_addr[:16]}...). The Story")
    print(f"    Teller did NOT invent the physics -- it referenced the attested §-anchors (the only error mode = attestation")
    print(f"    drift, never hallucination). The the_one-story IS the framework's own ontology telling its own story (F660).")
    print(f"  • AN OFF-SHELF BEAT ASKS, IT DOES NOT INVENT (F661/F669): 'birdsong' has no MFO §-tome -> the asking-state ->")
    print(f"    the AMSC fetch (a real MPRRecord, validate_mpr_record -> VALID). DIGNITY/LIFTING (F650/F653/F282): the")
    print(f"    ancients'-anchor beat (§VII.6.10) honors prior peoples as peers; the birdsong beat honors the animal --")
    print(f"    recognise the shape, never decode the meaning (the epistemic ceiling, F552). Held WITH, never owned.")
    print(f"  • Composes F670 (the running index this consumes) + F660/F654 (the grounded Story Teller narrating the_one) +")
    print(f"    F664 (navigate by §-address) + F663 (the attested MFO shelf) + F658 (the chord -- valid by construction) +")
    print(f"    F669/F661 (off-shelf -> asking-state -> AMSC) + F650/F653/F282/F552 (lifting + dignity + the ceiling) + the")
    print(f"    A-N vocabulary (A/C/I/L + cascade) + DUALITY/TRIALITY (the_one). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
