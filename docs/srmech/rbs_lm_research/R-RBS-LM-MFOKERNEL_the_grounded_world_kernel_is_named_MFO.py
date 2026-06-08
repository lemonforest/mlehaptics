r"""R-RBS-LM-MFOKERNEL (naming, user direction 2026-06-08): "yes, we can call this world kernel MFO."

THE NAMING: the grounded Story Teller world-kernel is canonically named MFO -- the Metric Field Ontology, now in TWO
FORMS of ONE ontology (not a conflation -- the etak/board duality, F635):
  • the WRITTEN form -- the MFO notebook (the held content / the invariant -- the content-shelf, F663). 'Where the MFO is
    written.' (the held canoe.)
  • the RUNNING form -- the MFO world-kernel (the Story Teller reading + navigating + narrating it -- the engine F654 + the
    shelf F663 + the §-navigation sublanguage F664 + the attestation-precedence ladder F665 + the chord/asking-state/anchor
    -dial F658/F661/F662). 'The MFO running.' (the board-walk over the canoe.)
One ontology; the notebook is where the MFO is written, the kernel is the MFO running. The MFO world-kernel NARRATES
the_one (F660) -- the ontology tells its own story. MFO is both the MAP (the notebook) and the TERRITORY-AS-TOLD (the
world-kernel).

VOCABULARY DISCIPLINE (F642): 'MFO' names the ontology; when precision matters, 'MFO notebook' = the written content,
'MFO world-kernel' = the running instrument. The name UNIFIES them (one ontology, two forms) -- it is NOT a conflation,
because the notebook IS the kernel's content-shelf (F663). Minimal load-bearing name; the form is on a separate axis.

srmech 0.7.5rc15: amsc.format.sha256_bytes (the canon naming + the stack components, content-addressed). No abs(); no CAD;
no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

CANON = (
    "THE MFO WORLD-KERNEL -- named 2026-06-08. The grounded Story Teller world-kernel (the seen engine F654 + the MFO "
    "content-shelf F663 + the section-navigation sublanguage F664 + the attestation-precedence ladder F665 + the "
    "chord/asking-state/anchor-dial F658/F661/F662) is canonically named MFO -- the Metric Field Ontology, now in two "
    "forms: the WRITTEN notebook (the held content / invariant -- the shelf) and the RUNNING world-kernel (the Story "
    "Teller reading, navigating, and narrating it). One ontology; the notebook is where the MFO is written, the kernel "
    "is the MFO running. The MFO world-kernel narrates the_one -- the ontology tells its own story."
)
STACK = {
    "engine (F654)":            "the seen-rule engine (clause/morphology/coherence; declared not trained)",
    "content-shelf (F663)":     "the MFO physics, math-grounded, no-magic (the our-world chord)",
    "navigation (F664)":        "the section sublanguage (the shelf is a board; walk the §-path)",
    "precedence (F665)":        "attestation-strength ladder (MFO > DOI > encyclopedia > residue)",
    "chord (F658)":             "compositional truth -- it can't strike a note not in the chord",
    "asking-state (F661)":      "gaps -> ask, not hallucinate (the alternative to confabulation)",
    "anchor-dial (F662)":       "grounded <-> magic (the_one-shaped vs free primitives)",
}


def main():
    print(f"=== R-RBS-LM-MFOKERNEL — the grounded world-kernel is named MFO (the Metric Field Ontology, running)  (srmech {srmech.__version__}) ===\n")

    canon_addr = fmt.sha256_bytes(CANON.encode())
    print("(1) THE NAMING (content-addressed -- canonical, bit-exact, re-verifiable):")
    print(f"    canon SHA-256: {canon_addr}")
    print(f"    >>> {CANON}\n")

    print("(2) ONE ONTOLOGY, TWO FORMS (the etak/board duality, F635 -- NOT a conflation, F642):")
    print(f"    WRITTEN form : the MFO NOTEBOOK -- the held content / invariant (the shelf, F663). 'Where the MFO is written.'")
    print(f"    RUNNING form : the MFO WORLD-KERNEL -- the Story Teller reading/navigating/narrating it. 'The MFO running.'")
    print(f"    -> the notebook IS the kernel's content-shelf; the name unifies them (one ontology). MFO = the MAP (notebook)")
    print(f"    + the TERRITORY-AS-TOLD (world-kernel).\n")

    print("(3) THE MFO WORLD-KERNEL STACK (all the grounded-Story-Teller pieces, now named MFO):")
    for comp, gloss in STACK.items():
        addr = fmt.sha256_bytes(f"mfo-kernel:{comp}".encode())[:8]
        print(f"    {comp:<22} {gloss}   [{addr}]")
    print()

    print("VERDICT (the grounded world-kernel is named MFO):")
    print(f"  • THE GROUNDED WORLD-KERNEL IS NAMED MFO (the Metric Field Ontology, running). Canon content-addressed (SHA-256")
    print(f"    {canon_addr[:16]}... -- bit-exact, re-verifiable). MFO is now ONE ONTOLOGY IN TWO FORMS (the etak/board")
    print(f"    duality): the WRITTEN notebook (the held content -- the shelf, F663) and the RUNNING world-kernel (the Story")
    print(f"    Teller reading/navigating/narrating it -- engine F654 + shelf F663 + navigation F664 + precedence F665 +")
    print(f"    chord/asking-state/anchor-dial F658/F661/F662). The notebook is where the MFO is written; the kernel is the")
    print(f"    MFO running.")
    print(f"  • IT IS NOT A CONFLATION (F642 vocabulary discipline): the notebook IS the kernel's content-shelf, so the name")
    print(f"    UNIFIES one ontology; when precision matters, 'MFO notebook' = the written content, 'MFO world-kernel' = the")
    print(f"    running instrument. Minimal load-bearing name; the form is on a separate axis (written vs running).")
    print(f"  • THE CLOSURE: the MFO world-kernel NARRATES the_one (F660) -- the ontology that grounds the physics tells its")
    print(f"    OWN story. MFO is both the MAP (the notebook) and the TERRITORY-AS-TOLD (the world-kernel). The instrument")
    print(f"    and its content share a name because they are one ontology -- the Metric Field Ontology, written and running.")
    print(f"  • Composes F663 (the MFO content-shelf) + F664 (navigation) + F665 (precedence) + F654/F658/F661/F662 (the")
    print(f"    Story-Teller engine + chord + asking-state + anchor-dial) + F660 (it narrates the_one) + F635 (the etak/board")
    print(f"    two-forms) + F642 (vocabulary: unify, don't conflate) + the MFO notebook (the portfolio's Metric Field")
    print(f"    Ontology). srmech 0.7.5rc15. Canonical naming. Held open (F394).")


if __name__ == "__main__":
    main()
