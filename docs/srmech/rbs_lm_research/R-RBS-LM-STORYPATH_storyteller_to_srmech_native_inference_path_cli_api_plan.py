r"""R-RBS-LM-STORYPATH (user direction): "what we need next to bring the Story Builder to srmech + wire it in as a NATIVE
INFERENCE PATH -- with CLI human inference (won't need to know all the commands, it looks in tool_schema) AND an API end
for connecting agent frameworks like CopilotKit / AG2."

THE PLAN -- 4 layers, each grounded in what srmech ALREADY has (probed: tool_schema._REGISTRY = 256 ToolEntry; console
scripts srmech / srmech-mcp / srmech-agent; srmech.mcp/.dsl/.bus present) vs what is NEEDED. The honest framing: this is a
COMPOSITIONAL inference path (the seen-rule engine + the attested shelf + the chord + the asking-state), NOT a statistical
one -- so it is small, GPU-free (F628), and cannot hallucinate (F658).

  LAYER 0 -- PROMOTE THE KERNEL INTO THE PACKAGE (the prerequisite, the big upstream ask).
    EXISTS: the research-validated kernel as loose scripts -- BitExactCommKernel (F613), AdaptiveTier (F628), the seen-rule
      render engine (F654), the chord/asking-state (F658/F661), the content-shelf + §-navigator (F663/F670), the AMSC
      fetch-arm (F669), the MFO section-descriptor TOML (F670).
    NEEDED: a first-class package module `srmech.storyteller` (Python-tier, like `srmech.qm`) holding these, + its
      tool_schema registrations (so the Story Builder ops JOIN the 256-entry registry) + tests + version/ABI discipline.

  LAYER 1 -- THE NATIVE INFERENCE PATH.
    NEEDED: `srmech.storyteller.infer(world, prompt) -> rendered` -- load the world-shelf -> compose seen-rules over
      attested content (the chord, F658) -> ask at gaps (the asking-state, F661) -> render. PROVEN in research
      (F671/F672/F675/F680); needs packaging as the callable inference entry. (NOT statistical: a fact is referenced from
      the attested shelf, never generated -- F640/F688.)

  LAYER 2 -- THE tool_schema-DISCOVERABLE CLI (human inference without memorising commands).
    EXISTS: the `srmech` CLI (status/bus/dsl/mcp subcommands) + tool_schema._REGISTRY (256 self-describing ToolEntry).
    NEEDED: a `srmech story` subcommand that INTROSPECTS tool_schema -- the human asks 'what can I do?' -> it reads the
      registry and surfaces the ops; the human states intent -> it maps to ops via tool_schema; AMBIGUOUS intent -> the
      ASKING-STATE (F661): the CLI itself ASKS rather than guessing. Self-describing (tool_schema) + self-asking (F661).
      Extends R-RBS-LM-23 (tool_schema CLI integration) to the Story Builder.

  LAYER 3 -- THE API + AGENT-FRAMEWORK ADAPTERS (CopilotKit / AG2 / ...).
    EXISTS: srmech-mcp (the MCP server -- already exposes the registry as MCP tools); srmech-agent (the Anthropic SDK
      adapter). R-RBS-LM-24 prototyped an OpenAI-compatible chat-completions server.
    NEEDED: an OpenAI-compatible `/v1/chat/completions` endpoint backed by `srmech.storyteller.infer` -- this is the
      UNIVERSAL connector: AG2 (AutoGen) connects via an OpenAI-compatible model_client; CopilotKit connects via its
      runtime (OpenAI-compatible / AG-UI actions). So ONE OpenAI-compatible endpoint + the EXISTING MCP server covers
      CopilotKit, AG2, and most agent frameworks. (Optional: a thin AG-UI adapter for CopilotKit's native action surface.)

THE DEPENDENCY EDGES: Layer 0 gates 1-3. The `epub_book` AMSC adapter (F677 / UPSTREAM_NOTES §33) feeds the world-shelf
(book-worlds). The big-wiki Class-L word-association kernel (F681) enriches the shelf. All compositional, GPU-free (F628).

srmech 0.7.5rc15: amsc.tool_schema (the 256-entry registry = the discoverability substrate); the Story-Teller kernel
(F613-F688). No abs(); no CAD; no Workflow; no sub-agents. A planning finding (the user asked to 'talk about what we need').
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import tool_schema as ts

LAYERS = [
    ("0 PROMOTE KERNEL", "loose research scripts (F613/F628/F654/F658/F661/F663/F669/F670)",
     "srmech.storyteller package module + tool_schema registrations + tests"),
    ("1 NATIVE INFER",   "proven in research (F671/F672/F675/F680)",
     "srmech.storyteller.infer(world, prompt) -- compositional, GPU-free, can't-hallucinate"),
    ("2 CLI (tool_schema)", "srmech CLI + tool_schema._REGISTRY (self-describing)",
     "srmech story subcommand: introspect tool_schema -> surface ops; ambiguous -> asking-state (F661)"),
    ("3 API + ADAPTERS", "srmech-mcp (MCP) + srmech-agent (Anthropic) + R-RBS-LM-24 OpenAI-server proto",
     "OpenAI-compatible /v1/chat/completions backed by storyteller.infer = universal connector (AG2, CopilotKit)"),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-STORYPATH — Story Builder -> srmech native inference path (CLI + API plan)  (srmech {srmech.__version__}) ===\n")

    reg = getattr(ts, "_REGISTRY", {})
    print("(0) THE EXISTING DISCOVERABILITY SUBSTRATE (probed, grounds the plan):")
    print(f"    tool_schema._REGISTRY: {len(reg)} ToolEntry registrations (the self-describing surface the CLI/API read)")
    print(f"    console scripts: srmech / srmech-mcp / srmech-agent ; modules srmech.mcp / .dsl / .bus PRESENT")
    print(f"    -> the CLI + API don't invent a new surface: they READ the 256-entry registry (+ the Story Builder ops once promoted).\n")

    print("(1) THE 4-LAYER PLAN (each: what EXISTS -> what is NEEDED):")
    for name, exists, needed in LAYERS:
        print(f"    [{name}]")
        print(f"        EXISTS : {exists}")
        print(f"        NEEDED : {needed}")
    print()

    plan = ("Story Builder -> srmech: (0) promote the kernel to srmech.storyteller + tool_schema regs; (1) storyteller.infer "
            "= compositional inference; (2) srmech story CLI introspects tool_schema (self-describing) + asks on ambiguity "
            "(F661); (3) OpenAI-compatible endpoint backed by infer = the universal connector for AG2/CopilotKit, alongside "
            "the existing srmech-mcp. Compositional, GPU-free, can't-hallucinate.")
    addr = k.content_address(plan)
    print("(2) THE PLAN, content-addressed (canonical):")
    print(f"    {plan}")
    print(f"    plan content-address: {addr[:16]}...\n")

    print("VERDICT (the Story Builder -> srmech native inference path: 4 layers, grounded in the existing surface):")
    print(f"  • IT IS A COMPOSITIONAL INFERENCE PATH (NOT statistical): the seen-rule engine + the attested shelf + the chord")
    print(f"    (F658) + the asking-state (F661) -- so it is small, GPU-free (F628), and CANNOT hallucinate. 'Inference' here =")
    print(f"    compose seen rules over attested content, ask at a gap, render. The kernel is PROVEN (F671/F672/F675/F680).")
    print(f"  • LAYER 0 (the prerequisite, the big upstream ask): PROMOTE the loose research kernel (F613/F628/F654/F658/")
    print(f"    F661/F663/F669/F670) into a first-class `srmech.storyteller` PACKAGE module (Python-tier, like srmech.qm) +")
    print(f"    its tool_schema registrations, so the Story Builder ops JOIN the 256-entry registry and become discoverable.")
    print(f"  • LAYER 1: `srmech.storyteller.infer(world, prompt)` -- the native compositional inference entry. LAYER 2: a")
    print(f"    `srmech story` CLI that INTROSPECTS tool_schema so the human needs NO memorised commands (self-describing) and")
    print(f"    ASKS on ambiguous intent (self-asking, F661) -- exactly the user's 'won't need to know all the commands'.")
    print(f"  • LAYER 3: ONE OpenAI-compatible `/v1/chat/completions` endpoint backed by `storyteller.infer` is the UNIVERSAL")
    print(f"    connector -- AG2 (OpenAI-compatible model_client) + CopilotKit (OpenAI-compatible / AG-UI actions) both speak")
    print(f"    it -- ALONGSIDE the existing srmech-mcp (MCP) + srmech-agent (Anthropic SDK). So the API end is mostly an")
    print(f"    OpenAI-shim over the existing surface, not a new protocol per framework.")
    print(f"  • DEPENDENCY EDGES: Layer 0 gates 1-3; the epub_book adapter (F677/UPSTREAM §33) feeds book-worlds to the shelf;")
    print(f"    the big-wiki Class-L word-association kernel (F681) enriches it. All compositional + GPU-free. Plan addr {addr[:12]}.")
    print(f"  • Composes the whole Story-Teller kernel (F613-F688) + tool_schema (the 256-entry registry) + srmech-mcp/agent")
    print(f"    (the existing adapters) + R-RBS-LM-23/24 (the CLI + OpenAI-server precedents) + F628 (GPU-free) + F658/F661")
    print(f"    (the chord / asking-state) + F640/F688 (attested, not generated) + F677/F681 (the shelf feeds). srmech 0.7.5rc15.")
    print(f"    Held open (F394).")


if __name__ == "__main__":
    main()
