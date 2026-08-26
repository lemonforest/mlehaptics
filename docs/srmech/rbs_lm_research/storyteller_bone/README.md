# `storyteller_bone/` — the srmech.storyteller bone structure

*A promotion-ready SKELETON mirroring the future `srmech.storyteller` package. We take this bone to srmech; the dev
session fleshes it out and consolidates the leftover research scripts. The reference IMPLEMENTATIONS live as their
committed findings (F690–F694); each folder's README points to its reference + names its srmech destination.*

## Promotion map (research → srmech)

| bone folder | what it is | reference impl | lands in srmech |
|---|---|---|---|
| `kernel/` | the bit-exact comm kernel + the two-tier adaptive kernel | F613 (bit_exact_comm_kernel.py) + F628 (adaptive_tier.py) | `srmech/storyteller/kernel.py` |
| `engine/` | the seen-rule render engine + the chord + the asking-state | F654/F658/F661 (in F692 STORYMODULE) | `srmech/storyteller/engine.py` |
| `infer/` | the native compositional inference entry | F692 (R-RBS-LM-STORYMODULE) | `srmech/storyteller/infer.py` |
| `adapters/` | the epub_book AMSC adapter (book-worlds -> the shelf) | F691 (R-RBS-LM-EPUBADAPTER) | `srmech/amsc/adapters/epub_book.py` |
| `wordassoc/` | the big-wiki Class-L word-association kernel (shelf enrichment) | F690 (R-RBS-LM-WIKIKERNEL) | `srmech/storyteller/wordassoc.py` |
| `cli/` | the self-describing + self-asking `srmech story` CLI | F693 (R-RBS-LM-STORYCLI) | `srmech/__main__.py (the `story` subcommand)` |
| `api/` | the OpenAI-compatible endpoint (AG2 / CopilotKit) | F694 (R-RBS-LM-STORYAPI) | `srmech/storyteller/serve.py (FastAPI/ASGI)` |
| `tool_schema/` | the STORYTELLER_TOOLS op registrations | F692 STORYTELLER_TOOLS | `srmech/amsc/tool_schema (registrations)` |
| `descriptors/` | the ATTESTED TOML foundational forms (world / AMSC-catalog / tool-schema) | this finding (F695) | `srmech/storyteller/_research/ (catalog + descriptor TOMLs)` |

**Honest framing:** the Story Teller is a COMPOSITIONAL inference path (seen-rule engine + attested shelf + chord +
asking-state) — GPU-free, can't-hallucinate. Not a statistical model. (F689 the plan; UPSTREAM_NOTES §33/§34.)
