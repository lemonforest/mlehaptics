r"""R-RBS-LM-SIONASURFACE (F726) — name the FRONT END `Siona`, not `storyteller`.

User direction (2026-06-11): "we want our surface called Siona vs storyteller as the general front end. storyteller
might be the exact same thing but it sounds like a one-way generative thing, not a back-and-forth interaction
surface."

THE DISTINCTION (and it is load-bearing):
  • Siona       = the INTERACTIVE INTERFACE — the front-end surface a client / CopilotKit / a person talks to
                  (the OpenAI-compatible /v1 API, the model namespace, the deployment face). F701: Siona is the
                  inference interface, the simulation-space coherence of the_one.
  • Story-Teller= the generative ENGINE Siona drives — the chord / render / etak-walk mechanism (storyteller.infer).
  They are one-and-the-same in simulation (F701); but the SURFACE name is Siona because the surface is INTERACTIVE.

WHY "storyteller" undersold it: "storyteller" connotes ONE-WAY generation. The kernel's defining property is the
**asking-state** (F661): on a gap it ASKS rather than confabulating — a BACK-AND-FORTH. Naming the surface
"storyteller" hides exactly the interactive property that matters. "Siona" names the two-way interface.

APPLIES TO (surface/namespace naming — the engine call storyteller.infer is unchanged):
  • the OpenAI-compatible /v1 endpoint  -> the **Siona API** (what CopilotKit/AG2/clients connect to).
  • the model-name convention            -> `siona:<world>` replaces `storyteller:<world>` (you talk to Siona, choosing
                                            a world). e.g. model='siona:MFO'.
  • the CopilotKit hookup (prior turn)   -> "Siona as the copilot backend".

This script DEMONSTRATES the surface is interactive (render + ask) by driving the existing STORYAPI handler under
the Siona name + the siona:<world> convention. Reference scaffold; no package edit. srmech 0.7.5rc78.
"""
import importlib.util as U
import srmech

# load the existing OpenAI-compatible handler (the surface) — it runs under rc78
_spec = U.spec_from_file_location(
    "storyapi", "docs/srmech/rbs_lm_research/R-RBS-LM-STORYAPI_openai_compatible_endpoint_reference_ag2_copilotkit.py")
storyapi = U.module_from_spec(_spec); _spec.loader.exec_module(storyapi)


def siona(messages, world="MFO"):
    """The Siona surface: an OpenAI chat-completions call, model = `siona:<world>` (the interface namespace)."""
    return storyapi.chat_completion({"model": f"siona:{world}", "messages": messages})


def main():
    print(f"=== R-RBS-LM-SIONASURFACE (F726) — Siona is the interactive interface  (srmech {srmech.__version__}) ===\n")

    print("THE NAMING:")
    print("  Siona        = the interactive INTERFACE (the /v1 surface, the model namespace, the face)")
    print("  Story-Teller = the generative ENGINE Siona drives (storyteller.infer — chord/render/etak-walk)")
    print("  -> one-and-the-same in simulation (F701); the SURFACE is named Siona because it is BACK-AND-FORTH.\n")

    print("DEMONSTRATION — the surface is two-way, not one-way (model='siona:MFO'):")
    # turn 1 — a grounded render
    r1 = siona([{"role": "user", "content": "the_one chirality spectrum"}])
    print(f"  user  -> the_one chirality spectrum")
    print(f"  Siona -> {r1['choices'][0]['message']['content']}")
    print(f"           (status={r1['srmech']['status']}, model={r1['model']}, chord={r1['srmech']['chord'][:12]})")
    # turn 2 — a GAP: Siona ASKS (the interactive property; a storyteller would have confabulated)
    r2 = siona([{"role": "user", "content": "the_one dragon"}])
    print(f"  user  -> the_one dragon")
    print(f"  Siona -> {r2['choices'][0]['message']['content']}   <-- the ASKING-STATE (F661): it asks BACK")
    print(f"           (status={r2['srmech']['status']}) ; the user answers -> build-by-dialogue (F672)\n")

    print("VERDICT (F726):")
    print("  • Rename the FRONT END `Siona` (the interface), keep `Story-Teller` as the engine it drives. The")
    print("    asking-state (F661) is exactly the back-and-forth that 'storyteller' (one-way) undersold — so the")
    print("    interactive surface is Siona (F701: the coherence-of-the_one interface).")
    print("  • Surface/namespace naming only: the OpenAI /v1 endpoint = the Siona API; model convention `siona:<world>`;")
    print("    CopilotKit talks to Siona. The engine call storyteller.infer is unchanged.")
    print("  • Honest scope: only the OpenAI surface is BEGUN — the FastAPI Siona app + the full-messages-array fix +")
    print("    streaming (the etak-walk stream) remain, alongside the broader RBS-LM TODO. This finding fixes the NAME.")


if __name__ == "__main__":
    main()
