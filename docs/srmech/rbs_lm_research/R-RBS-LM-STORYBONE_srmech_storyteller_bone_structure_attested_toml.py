r"""R-RBS-LM-STORYBONE (user direction): the BONE STRUCTURE -- a folder skeleton in the research target mirroring the
future `srmech.storyteller` package, each folder carrying a reference MD ('what this spot is for + where it should end up in
srmech space'), PLUS the ATTESTED TOML foundational forms. We take the bone to srmech; the dev session fleshes it out.

WHAT IT BUILDS: docs/srmech/rbs_lm_research/storyteller_bone/ -- a promotion-ready skeleton:
  storyteller_bone/
    README.md                  -- the promotion MAP (research-path -> srmech-path) + the bone's purpose
    kernel/README.md           -- F613 BitExactCommKernel + F628 AdaptiveTier   -> srmech/storyteller/kernel.py
    engine/README.md           -- F654 render + F658 chord + F661 asking-state  -> srmech/storyteller/engine.py
    infer/README.md            -- F692 storyteller.infer(world, prompt)         -> srmech/storyteller/infer.py
    adapters/README.md         -- F691 epub_book adapter                        -> srmech/amsc/adapters/epub_book.py
    wordassoc/README.md        -- F690 big-wiki Class-L kernel                  -> srmech/storyteller/wordassoc.py
    cli/README.md              -- F693 the `srmech story` CLI                   -> srmech/__main__.py (story subcommand)
    api/README.md              -- F694 OpenAI endpoint (AG2/CopilotKit)         -> srmech/storyteller/serve.py
    tool_schema/README.md      -- F692 STORYTELLER_TOOLS registrations          -> srmech/amsc/tool_schema (regs)
    descriptors/               -- THE ATTESTED TOML FOUNDATIONAL FORMS:
      README.md                -- what the descriptors are + where they land
      storyteller_world.descriptor.toml   -- an ATTESTED world descriptor (per-tome MPR attestation; like the F670 MFO §-descriptor)
      storyteller.amsc_catalog.toml       -- an AMSC catalog descriptor (the 6 mandatory sections; the foundational AMSC form)
      storyteller_ops.tool_schema.toml    -- the tool_schema op registrations as TOML

The reference IMPLEMENTATIONS stay as their committed findings (F690-F694); the bone POINTS to them (no duplication) and
adds the attested-TOML foundational forms. ATTESTED (the MPM discipline, F640/F669): each world tome carries a content_sha256
+ an attestation class; the AMSC catalog carries the 6 mandatory sections.

srmech 0.7.5rc15: amsc.format.sha256_bytes (content-address each tome -> the attested foundational form) ; tomllib (validate
the descriptors load). No abs(); no CAD; no Workflow; no sub-agents. Reproducible generator -- re-runs build the same bone.
"""
import os
import sys
import tomllib
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import format as fmt

BONE = "docs/srmech/rbs_lm_research/storyteller_bone"

# the promotion map: (folder, what, reference finding, srmech destination)
MAP = [
    ("kernel",      "the bit-exact comm kernel + the two-tier adaptive kernel", "F613 (bit_exact_comm_kernel.py) + F628 (adaptive_tier.py)", "srmech/storyteller/kernel.py"),
    ("engine",      "the seen-rule render engine + the chord + the asking-state", "F654/F658/F661 (in F692 STORYMODULE)", "srmech/storyteller/engine.py"),
    ("infer",       "the native compositional inference entry", "F692 (R-RBS-LM-STORYMODULE)", "srmech/storyteller/infer.py"),
    ("adapters",    "the epub_book AMSC adapter (book-worlds -> the shelf)", "F691 (R-RBS-LM-EPUBADAPTER)", "srmech/amsc/adapters/epub_book.py"),
    ("wordassoc",   "the big-wiki Class-L word-association kernel (shelf enrichment)", "F690 (R-RBS-LM-WIKIKERNEL)", "srmech/storyteller/wordassoc.py"),
    ("cli",         "the self-describing + self-asking `srmech story` CLI", "F693 (R-RBS-LM-STORYCLI)", "srmech/__main__.py (the `story` subcommand)"),
    ("api",         "the OpenAI-compatible endpoint (AG2 / CopilotKit)", "F694 (R-RBS-LM-STORYAPI)", "srmech/storyteller/serve.py (FastAPI/ASGI)"),
    ("tool_schema", "the STORYTELLER_TOOLS op registrations", "F692 STORYTELLER_TOOLS", "srmech/amsc/tool_schema (registrations)"),
    ("descriptors", "the ATTESTED TOML foundational forms (world / AMSC-catalog / tool-schema)", "this finding (F695)", "srmech/storyteller/_research/ (catalog + descriptor TOMLs)"),
]

# the world's foundational tomes (the attested form -- class A, our-math, F665/F640)
TOMES = [
    ("the_one",   "The one is the held invariant",            "MFO §I.1"),
    ("chirality", "It is seen in the handedness of matter",   "MFO §VI"),
    ("spectrum",  "and it rings in the spectrum",             "MFO §III.1"),
]


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_bone():
    # top README -- the promotion map
    rows = "\n".join(f"| `{f}/` | {what} | {ref} | `{dst}` |" for f, what, ref, dst in MAP)
    _w(f"{BONE}/README.md",
       "# `storyteller_bone/` — the srmech.storyteller bone structure\n\n"
       "*A promotion-ready SKELETON mirroring the future `srmech.storyteller` package. We take this bone to srmech; the dev\n"
       "session fleshes it out and consolidates the leftover research scripts. The reference IMPLEMENTATIONS live as their\n"
       "committed findings (F690–F694); each folder's README points to its reference + names its srmech destination.*\n\n"
       "## Promotion map (research → srmech)\n\n"
       "| bone folder | what it is | reference impl | lands in srmech |\n|---|---|---|---|\n" + rows + "\n\n"
       "**Honest framing:** the Story Teller is a COMPOSITIONAL inference path (seen-rule engine + attested shelf + chord +\n"
       "asking-state) — GPU-free, can't-hallucinate. Not a statistical model. (F689 the plan; UPSTREAM_NOTES §33/§34.)\n")
    # per-folder READMEs
    for f, what, ref, dst in MAP:
        if f == "descriptors":
            continue
        _w(f"{BONE}/{f}/README.md",
           f"# `{f}/` — {what}\n\n"
           f"**Reference implementation:** {ref}\n\n"
           f"**Lands in srmech:** `{dst}`\n\n"
           f"This folder is a BONE — the reference impl is the committed finding above. The dev session lifts it here,\n"
           f"applies the srmech package discipline (tests, version/ABI, JPL-clean if it gets a C surface), and wires it in.\n"
           f"Compositional / GPU-free / can't-hallucinate (F628/F658). Held open (F394).\n")
    # descriptors/ README + the attested TOML foundational forms
    _w(f"{BONE}/descriptors/README.md",
       "# `descriptors/` — the attested TOML foundational forms\n\n"
       "The MPM-attested TOML 'bone' the dev session fills. Three forms:\n\n"
       "- **`storyteller_world.descriptor.toml`** — an attested World descriptor (per-tome content_sha256 + attestation\n"
       "  class; the shelf the Story Teller narrates). Peer to the F670 MFO §-section descriptor. → a `srmech.storyteller`\n"
       "  World loader reads it.\n"
       "- **`storyteller.amsc_catalog.toml`** — an AMSC catalog descriptor (the 6 mandatory sections). → `srmech.amsc`\n"
       "  registers the storyteller as an attested data source.\n"
       "- **`storyteller_ops.tool_schema.toml`** — the tool_schema op registrations as TOML. → `srmech.amsc.tool_schema`.\n\n"
       "All ATTESTED (F640/F669): a tome without a content-address / a source without attestation is not real.\n")
    # the attested world descriptor TOML (content-address each tome)
    tome_blocks = []
    for key, clause, anchor in TOMES:
        sha = fmt.sha256_bytes(clause.encode())
        tome_blocks.append(
            f'[[tome]]\nkey = "{key}"\nclause = "{clause}"\nanchor = "{anchor}"\nattestation_class = "A"  '
            f'# our math (F665/F640)\ncontent_sha256 = "{sha}"\n')
    _w(f"{BONE}/descriptors/storyteller_world.descriptor.toml",
       "# storyteller_world.descriptor.toml — an ATTESTED World descriptor (foundational form).\n"
       "# Lands in srmech: a srmech.storyteller World loader reads this (peer to the F670 MFO section-descriptor).\n\n"
       '[meta]\nkernel = "storyteller"\nworld = "MFO"\ndescriptor_version = "0.1"\n'
       'attestation_class = "A"  # class-A: attested-through-our-math (F665/F640)\n'
       'source = "MFO spectral research notebook"\n\n' + "\n".join(tome_blocks))
    # the AMSC catalog descriptor (the 6 mandatory sections, per the CLAUDE.md AMSC gotchas)
    _w(f"{BONE}/descriptors/storyteller.amsc_catalog.toml",
       "# storyteller.amsc_catalog.toml — an AMSC catalog descriptor (the foundational AMSC form; 6 mandatory sections).\n"
       "# Lands in srmech: srmech.amsc.catalog.register_attested_root registers the storyteller as an attested source.\n\n"
       '[source]\nhuman_readable_name = "RBS-LM Story Teller world-kernel"  # NOT \'name\' (AMSC gotcha)\n'
       'description = "the grounded compositional Story Teller (F613-F688)"\n\n'
       '[fetch]\nndjson_path = "storyteller_worlds.ndjson"  # load-bearing (AMSC gotcha)\nmode = "literature_curated"\n\n'
       '[attestation]\nlicense = "framework-internal (class-A)"\nsource_kind = "our-math"\n\n'
       '[schema]\ndata_schema_id = "rbs-lm://schema/storyteller-world"\n\n'
       '[rendering]\ncite_as = "RBS-LM Story Teller (F613-F689)"\npurpose = "a grounded world-kernel content-shelf"\n\n'
       '[provenance]\nparser_version = "srmech.storyteller 0.1 (reference)"\nfindings = "F613-F695"\n')
    # the tool_schema op registrations as TOML
    ops = [("storyteller.infer", "compose seen-rules over a world's attested shelf; ask at a gap; render"),
           ("storyteller.navigate", "walk a world's section/board graph to a tome"),
           ("storyteller.tell", "declare a new seen rule / tome (build-by-dialogue); GPU-free add"),
           ("storyteller.ask", "surface a gap as a question instead of hallucinating")]
    op_blocks = "\n".join(f'[[op]]\nname = "{n}"\nsummary = "{s}"\n' for n, s in ops)
    _w(f"{BONE}/descriptors/storyteller_ops.tool_schema.toml",
       "# storyteller_ops.tool_schema.toml — the Story Teller op registrations.\n"
       "# Lands in srmech: the dev session converts these to ToolEntry and registers into amsc.tool_schema._REGISTRY.\n\n"
       + op_blocks)


def main():
    print(f"=== R-RBS-LM-STORYBONE — the srmech.storyteller bone structure + attested TOML  (srmech {srmech.__version__}) ===\n")
    build_bone()
    # validate: the bone exists + the TOMLs load + the world descriptor is attested
    folders = [f for f, *_ in MAP]
    present = [f for f in folders if os.path.isdir(f"{BONE}/{f}")]
    print(f"(1) BONE STRUCTURE built at {BONE}/ -- {len(present)}/{len(folders)} folders + READMEs: {present}")
    tomls = ["storyteller_world.descriptor.toml", "storyteller.amsc_catalog.toml", "storyteller_ops.tool_schema.toml"]
    print("(2) THE ATTESTED TOML FOUNDATIONAL FORMS (validate they load + carry attestation):")
    for t in tomls:
        with open(f"{BONE}/descriptors/{t}", "rb") as fh:
            d = tomllib.load(fh)
        print(f"    {t}: loads OK  keys={list(d)}")
    with open(f"{BONE}/descriptors/storyteller_world.descriptor.toml", "rb") as fh:
        wd = tomllib.load(fh)
    attested = all("content_sha256" in tm and tm.get("attestation_class") for tm in wd["tome"])
    print(f"    world descriptor: {len(wd['tome'])} tomes, all attested (content_sha256 + class): {attested}")
    print(f"    AMSC catalog: 6 mandatory sections present: {all(s in tomllib.load(open(BONE+'/descriptors/storyteller.amsc_catalog.toml','rb')) for s in ['source','fetch','attestation','schema','rendering','provenance'])}\n")

    print("VERDICT (the srmech.storyteller bone structure + attested TOML foundational forms):")
    print(f"  • A PROMOTION-READY SKELETON: storyteller_bone/ mirrors the future srmech.storyteller package -- 9 folders, each")
    print(f"    with a reference README ('what this spot is for' + the reference finding + 'where it ends up in srmech').")
    print(f"    The reference IMPLEMENTATIONS stay as committed findings (F690-F694); the bone POINTS to them (no duplication).")
    print(f"  • THE ATTESTED TOML FOUNDATIONAL FORMS (the user's 'foundational forms'): a world descriptor (per-tome content-")
    print(f"    address + attestation class -- ATTESTED, F640/F669; peer to the F670 MFO §-descriptor), an AMSC catalog (the 6")
    print(f"    mandatory sections), and the tool_schema op registrations -- all validated to load. The dev session fills them.")
    print(f"  • THE BONE IS WHAT WE TAKE TO SRMECH: PR #687 carries it; the dev session lifts each folder to its srmech")
    print(f"    destination (per the promotion map), applies the package discipline, and consolidates the leftover research")
    print(f"    scripts. Every 'where does this go' question is answered IN the bone.")
    print(f"  • Composes F689 (the plan) + F690-F694 (the references the bone points to) + F670 (the descriptor-TOML peer) +")
    print(f"    F640/F669 (attested foundational forms) + the AMSC catalog discipline + UPSTREAM_NOTES §33/§34. srmech 0.7.5rc15.")
    print(f"    Reference scaffold; NOT a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
