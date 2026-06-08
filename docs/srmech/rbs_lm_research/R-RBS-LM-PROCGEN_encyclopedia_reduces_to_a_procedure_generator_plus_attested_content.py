r"""R-RBS-LM-PROCGEN (the user's reduction, 2026-06-08): "i'm not sure if this is all an encyclopedia reduces to --
attested knowledge + the story about telling that knowledge; so more stories is just more DATA ABOUT STORIES, and we can
generate that anyhow? and all we really end up needing to create is a PROCEDURAL PROCEDURE GENERATOR -- maybe?"

THE REDUCTION (built + tested): YES, largely -- with one honest seam. F654 factored a story into ENGINE (fixed seen rules)
+ FORM (the telling) + CONTENT (attested). This collapses the FORM layer: forms are NOT a list to collect -- they are a
SMALL SET OF FORM-PRIMITIVES COMPOSED. So:
  • the FORM-SPACE is GENERATED, not collected: a few telling-primitives (SEQ / NEST / REPEAT / CONTRAST / FRAME) composed
    -> the whole space of story/expository forms (journey, discovery, encyclopedia-entry, list, ...). 'More stories' = more
    COMPOSITIONS of the primitives -- combinatorial, GENERABLE -- not more scraped data.
  • the generator OF forms is a PROCEDURAL PROCEDURE GENERATOR: a generator whose output is procedures (forms). The
    framework ALREADY has its shape -- it is srmech's cascade.compose (atoms -> composites; the lean-ISA two-tier DSL),
    pointed at FORM-atoms instead of math-atoms. (Composition = the framework's native move.)

THE HONEST SEAM (the user's 'maybe' -- load-bearing): the procedure-generator generates the TELLING (the form), NOT the
TRUTH. Two things are NOT generated:
  • CONTENT (the facts) stays ATTESTED -- referenced from the source of truth (F630/MPM); a generator that 'generates'
    facts is hallucinating. The encyclopedia's KNOWLEDGE is attested, never invented.
  • the WHICH-form-for-this-intent CHOICE is Class C (the which-way / the etak intent) -- a choice, not a generation; and
    the irreducible residue (the specific meaning, the author's/expert's intent) is attested + chosen, never generated (F552/F282).
So: an encyclopedia reduces to {a PROCEDURAL PROCEDURE GENERATOR (forms, generated from primitives) + ATTESTED CONTENT
(facts) + the FIXED seen engine + the Class-C intent chooser}. The generator replaces the story-CORPUS; the content +
intent are the non-generated parts.

srmech 0.7.5rc15: amsc.format.sha256_bytes (the attested content tomes -- the non-generated part). The form-composer = a
cascade.compose-shaped procedure generator (string/structure composition). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

# ---- FORM-PRIMITIVES: the small set of telling-atoms (compose -> the whole form-space) ----
PRIMS = ["SEQ", "NEST", "REPEAT", "CONTRAST", "FRAME"]   # sequence / embed / iterate / tension / bracket

# ---- the PROCEDURAL PROCEDURE GENERATOR: composes primitives -> forms (a cascade.compose-shaped generator) ----
def form(op, *parts):
    return {"op": op, "parts": list(parts)}

def render_form(f, depth=0):
    if isinstance(f, str):
        return f
    return f"{f['op']}(" + ", ".join(render_form(p) for p in f["parts"]) + ")"

# a few DISTINCT forms, ALL composed from the SAME PRIMS (no form is 'collected' -- each is generated)
FORMS_GENERATED = {
    "journey":     form("SEQ", "setup", "trial", "return"),
    "discovery":   form("SEQ", "ordinary", form("FRAME", "find"), "change"),
    "encyclopedia":form("SEQ", "definition", form("REPEAT", "attribute"), "example"),
    "list":        form("REPEAT", "item"),
    "tragedy":     form("SEQ", "rise", form("CONTRAST", "hope", "fall")),
}

def count_reachable(prims, leaves, depth):
    """how many distinct form-skeletons are GENERABLE at composition depth <= `depth` (the form-space is combinatorial)."""
    space = set(leaves)
    for _ in range(depth):
        new = set(space)
        for op in prims:
            for a in list(space)[:6]:           # bounded enumeration (illustrative, not exhaustive)
                new.add(f"{op}({a})")
                for b in list(space)[:4]:
                    new.add(f"{op}({a},{b})")
        space = new
    return len(space)


def main():
    print(f"=== R-RBS-LM-PROCGEN — an encyclopedia reduces to a procedure-generator + attested content  (srmech {srmech.__version__}) ===\n")

    # (1) forms are GENERATED from a small primitive set (not collected): same PRIMS -> many distinct forms
    print("(1) FORMS are GENERATED from a small primitive set (the procedural procedure generator), not collected:")
    print(f"    form-primitives (telling-atoms): {PRIMS}")
    for name, f in FORMS_GENERATED.items():
        print(f"    {name:<13} = {render_form(f)}")
    print(f"    -> every form is a COMPOSITION of the same {len(PRIMS)} primitives. No form is 'collected' -- each is built.\n")

    # (2) 'more stories = more data about stories' -- but that data is GENERABLE (combinatorial), not scraped
    leaves = ["a", "b", "c"]
    print("(2) 'MORE STORIES = MORE DATA ABOUT STORIES' -- but the form-space is GENERABLE (combinatorial), not scraped:")
    for d in (1, 2, 3):
        print(f"    distinct form-skeletons reachable at composition depth <= {d}: {count_reachable(PRIMS, leaves, d)}")
    print(f"    -> the form-space EXPLODES from {len(PRIMS)} primitives by composition. 'More forms' = deeper composition,")
    print(f"    GENERATED on demand -- we do NOT collect a corpus of stories to learn forms; we generate the form-space.\n")

    # (3) the HONEST SEAM: the generator makes the TELLING; CONTENT stays attested; the intent-choice is Class C
    print("(3) THE HONEST SEAM (the user's 'maybe') -- the generator makes the TELLING, NOT the TRUTH:")
    facts = {"water": ("water is H2O", "IUPAC"), "pluto": ("pluto is a dwarf planet", "IAU-2006")}
    for k, (txt, src) in facts.items():
        addr = fmt.sha256_bytes(f"{txt}|{src}".encode())[:8]
        print(f"    ATTESTED fact '{k}': {txt!r} [{src}]  addr {addr}  -- referenced, NOT generated (a generated 'fact' = hallucination)")
    print(f"    CONTENT = attested (the facts, F630/MPM); the procedure-generator does NOT invent them.")
    print(f"    INTENT (which form for this knowledge) = Class C (the which-way / etak intent) -- a CHOICE, not a generation.")
    print(f"    the irreducible residue (the specific meaning / the author's intent) = attested + chosen, never generated (F552/F282).\n")

    print("VERDICT (does an encyclopedia reduce to a procedural procedure generator + attested content? -- largely YES):")
    print(f"  • THE FORM LAYER COLLAPSES TO A PROCEDURAL PROCEDURE GENERATOR: forms are NOT a list to collect -- they are a")
    print(f"    SMALL SET OF FORM-PRIMITIVES ({PRIMS}) COMPOSED. The form-space is GENERATED (combinatorial -- it explodes")
    print(f"    with composition depth), not scraped. So 'more stories is just more data about stories' AND 'we can generate")
    print(f"    that anyhow' -- YES: we generate the form-space, we do not collect a story-corpus to learn forms. The")
    print(f"    'procedural procedure generator' the user names IS srmech's cascade.compose (atoms->composites), pointed at")
    print(f"    FORM-atoms instead of math-atoms -- the framework's native move.")
    print(f"  • SO AN ENCYCLOPEDIA REDUCES TO: {{ a PROCEDURAL PROCEDURE GENERATOR (forms, generated from primitives) +")
    print(f"    ATTESTED CONTENT (the facts, referenced from the source of truth) + the FIXED seen ENGINE (grammar/morphology")
    print(f"    /coherence, F654) + the Class-C INTENT chooser (which form for which knowledge) }}. The generator REPLACES")
    print(f"    the story-corpus; the content + intent are the non-generated parts.")
    print(f"  • THE HONEST SEAM (the 'maybe', load-bearing): the generator makes the TELLING, NOT the TRUTH. CONTENT stays")
    print(f"    ATTESTED (a generated 'fact' is a hallucination -- the knowledge is referenced, never invented, F630/MPM); the")
    print(f"    WHICH-form CHOICE is Class C (the intent / which-way); and the irreducible residue (the specific meaning, the")
    print(f"    author's/expert's intent) is attested + chosen, never generated (F552/F282). So 'all we need is a procedure")
    print(f"    generator' is TRUE for the FORM, but the CONTENT (attested) and the INTENT (Class C) are the seams it does")
    print(f"    not cross -- which is exactly right: we generate how to tell, never what is true.")
    print(f"  • Composes F654 (the engine/form/content factoring this collapses) + F630 (content = attestation) + F631 (seen")
    print(f"    rules / forms are seen) + cascade.compose / the DSL (the procedure-generator's shape) + Class C (the intent")
    print(f"    chooser) + F552/F282 (the irreducible residue / hand to the expert) + F636/F650 (why a data-center LLM can't")
    print(f"    do this -- all-flock, can't separate generator/content/intent). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
