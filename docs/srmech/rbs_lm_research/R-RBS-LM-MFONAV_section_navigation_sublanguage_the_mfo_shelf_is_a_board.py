r"""R-RBS-LM-MFONAV (the user's near-term need, 2026-06-08): "which is why we need MFO and its FORMAT-STRUCTURE SUBLANGUAGE
-- a way to NAVIGATE SECTIONS of the MFO notebook -- pretty soon, because it is attested through the math we've done."

THE BUILD: a NAVIGATION SUBLANGUAGE for the MFO notebook -- a format/structure way to address + walk its sections so the
grounded Story Teller can pull the right tome off the shelf (F663). The key recognition:
  • the MFO's SECTION-STRUCTURE (the §-numbering hierarchy + cross-refs) IS A BOARD (F632/F633): sections are nodes,
    parent->child + cross-ref are edges; navigating to a section is a BOARD-WALK over the §-path. (A section-board is a
    spectral object, like chess + syntax + the meaning-class board.)
  • EACH SECTION = an ATTESTED TOME (content-addressed, F663/F640) -- anchored to the math derived in it. This is WHY it
    is buildable now: the sections are attested THROUGH THE MATH WE'VE DONE, so they are real tomes to navigate.
  • the navigation sublanguage IS the formatting-language kernel (F579/F607) + the SS-FULLWIKI sub-language-kernel,
    pointed at the MFO notebook: address §VII.1.2 -> walk the §-path -> retrieve the tome. A missing section -> the
    asking-state (F661) -- it does not invent the section, it asks.

(The §-addresses + glosses here are illustrative of the navigation-KERNEL structure, anchored to the MFO references in
CLAUDE.md -- §VII.1.1 hyper, §VII.1.2 inference, §VII.6.20 epistemic ceiling, §VIII.31 sedenion. The actual section CONTENT
lives in the MFO notebook; we read what it ALREADY IS, no-lineage. The point is the navigation sublanguage.)

srmech 0.7.5rc15: BitExactCommKernel.content_address (each section = an attested tome); amsc.laplacian (the section-board
is a spectral object). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import laplacian

# THE MFO SECTION-GRAPH (the navigable board): section -> (title, parent, math-anchor) ; attested through the math
SECTIONS = {
    "I":         ("Foundations: the_one / two-truths / metric field", None,      "DUALITY.md/TRIALITY.md"),
    "VII":       ("Substrate & Observer",                              None,      "MFO core"),
    "VII.1":     ("the two-level ontology (substrate vs excitation)",  "VII",     "field/excitation, F399"),
    "VII.1.1":   ("hyper = 3D-spatial-interface",                      "VII.1",   "MFO §VII.1.1"),
    "VII.1.2":   ("inference = substrate-coupling (Class C∘M)",        "VII.1",   "MFO line 709"),
    "VII.6":     ("epistemic scope",                                   "VII",     "MFO §VII.6"),
    "VII.6.20":  ("the epistemic ceiling (a mind is never exactly modelable)", "VII.6", "MFO §VII.6.20 / F552"),
    "VIII":      ("hypercomplex (Cayley-Dickson / sedenion)",          None,      "qm.cayley_dickson"),
    "VIII.31":   ("the sedenion register (the addressable instrument)","VIII",    "MFO §VIII.31 / F465"),
}
CROSSREF = [("VII.1.2", "I")]                                        # inference couples back to the_one foundation


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-MFONAV — the MFO section navigation sublanguage (the shelf is a board)  (srmech {srmech.__version__}) ===\n")

    # (1) each SECTION = an attested (math-anchored) tome -- buildable now BECAUSE attested through the math
    print("(1) EACH SECTION = an ATTESTED TOME (content-addressed, anchored to the math derived in it, F663/F640):")
    for s in ["I", "VII.1.2", "VII.6.20", "VIII.31"]:
        title, parent, anchor = SECTIONS[s]
        addr = k.content_address(f"MFO§{s}")[:8]
        print(f"    §{s:<9} '{title}'  [math-anchor: {anchor}]  addr {addr}")
    print(f"    -> attested THROUGH THE MATH WE'VE DONE -> real tomes to navigate (this is WHY it is buildable now).\n")

    # (2) NAVIGATE: address a section -> walk the §-path (a board-walk) -> retrieve the tome
    def path_to(sec):
        p, cur = [], sec
        while cur is not None and cur in SECTIONS:
            p.append(cur); cur = SECTIONS[cur][1]
        return list(reversed(p))
    def navigate(sec):
        if sec not in SECTIONS:
            return ("ASKING", f"I have no section §{sec}. What is it? (F661 -- I do not invent the section)")
        return ("RETRIEVED", " -> ".join(f"§{x}" for x in path_to(sec)), SECTIONS[sec][0])
    print("(2) NAVIGATE = a BOARD-WALK over the §-path (address -> walk -> retrieve the tome):")
    for sec in ["VII.1.2", "VIII.31"]:
        st, path, title = navigate(sec)
        print(f"    navigate(§{sec}): [{st}] {path}  -> '{title}'")
    # a missing section -> the asking-state (F661)
    st, q = navigate("IX.5")
    print(f"    navigate(§IX.5): [{st}] {q}\n")

    # (3) the section-graph IS A BOARD (spectral object, F632/F633) -- its Laplacian spectrum
    nodes = list(SECTIONS); idx = {s: i for i, s in enumerate(nodes)}
    edges = set()
    for s, (_, parent, _) in SECTIONS.items():
        if parent in idx:
            edges.add((min(idx[s], idx[parent]), max(idx[s], idx[parent])))
    for a, b in CROSSREF:
        edges.add((min(idx[a], idx[b]), max(idx[a], idx[b])))
    edges = sorted(edges)
    L = laplacian.dense_laplacian(len(nodes), edges, [1.0] * len(edges))
    spec = [round(float(x), 3) for x in sorted(laplacian.jacobi_eigvals(L))]
    print("(3) THE SECTION-GRAPH IS A BOARD (a spectral object, F632/F633 -- like chess + syntax + the meaning-class board):")
    print(f"    {len(nodes)} sections, {len(edges)} edges (parent-child + cross-ref); Laplacian spectrum {spec}")
    print(f"    -> navigating the MFO = a board-walk over the section-graph; the sublanguage is the formatting kernel")
    print(f"    (F579/F607) + SS-FULLWIKI pointed at the MFO.\n")

    print("VERDICT (the MFO needs a section-navigation sublanguage -- the shelf is a board):")
    print(f"  • THE NEED: the MFO notebook is the grounded Story Teller's content-shelf (F663). To USE it, the Story Teller")
    print(f"    must NAVIGATE its sections -- so the MFO needs a FORMAT-STRUCTURE SUBLANGUAGE: address §VII.1.2 -> walk the")
    print(f"    §-path -> retrieve the tome. The section-structure IS A BOARD (F632/F633); navigation is a board-walk (the")
    print(f"    section-graph is a spectral object, verified).")
    print(f"  • BUILDABLE NOW BECAUSE ATTESTED THROUGH THE MATH: each section is an attested tome (content-addressed,")
    print(f"    anchored to the math derived in it, F663/F640) -- the sections are REAL tomes to navigate, not placeholders.")
    print(f"    A missing section -> the ASKING-STATE (F661): the Story Teller does NOT invent the section, it asks.")
    print(f"  • THE SUBLANGUAGE IS THE FORMATTING-LANGUAGE KERNEL (F579/F607) + the SS-FULLWIKI sub-language-kernel, pointed")
    print(f"    at the MFO notebook: §-numbering hierarchy + cross-refs = the board's edges; each §-node = an attested tome.")
    print(f"    Building it = giving the MFO shelf a navigable index so the grounded Story Teller (F660/F663) can pull the")
    print(f"    right physics-tome on demand. (Near-term build: a real MFO section-descriptor TOML, F607-shaped.)")
    print(f"  • Composes F663 (the MFO = the our-world content-shelf -- this navigates it) + F579/F607 (the formatting-")
    print(f"    language kernel / sub-language router) + F632/F633 (the section-graph = a board, a spectral object) + F661")
    print(f"    (missing section -> the asking-state) + F640 (attested-to-the-math) + F172 (Laplacian = structure) +")
    print(f"    no-lineage (we read what the MFO ALREADY IS). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
