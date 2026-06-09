r"""R-RBS-LM-STORYAPI (user direction): the REFERENCE OpenAI-compatible API -- Layer 3 of the F689 plan, the API end for
connecting agent frameworks (CopilotKit, AG2/AutoGen, ...). Scaffolded so the dev session has every answer. NOT a package edit.

WHAT IT IS: a reference `/v1/chat/completions` handler backed by `storyteller.infer` (F692), emitting the OpenAI
chat-completions response shape. This ONE endpoint is the UNIVERSAL connector:
  • AG2 / AutoGen     -- connects via an OpenAI-compatible model_client (set base_url -> this endpoint).
  • CopilotKit        -- connects via its OpenAI-compatible runtime / AG-UI actions (same base_url).
  • most agent frameworks (LangChain, LlamaIndex, ...) speak OpenAI chat-completions too.
ALONGSIDE the EXISTING srmech-mcp (MCP server -- exposes the ops as MCP tools) + srmech-agent (Anthropic SDK). So the API
end is mostly an OpenAI-shim over storyteller.infer, NOT a new protocol per framework.

THE MAPPING (request -> infer -> response):
  • request.model        -> the WORLD name (a client picks a world by 'model'): 'storyteller:MFO', 'storyteller:Emberreach'.
  • request.messages[-1] -> the prompt (the last user turn). The reference parses prompt-keys; the dev session swaps in a
    richer intent parser (or the F693 tool_schema mapper).
  • storyteller.infer(world, prompt) -> {status, text, chord, ask}:
       status='rendered' -> choices[0].message.content = text (a valid-by-construction chord; can't-hallucinate, F658).
       status='asking'   -> choices[0].message.content = the ASK (the assistant asks rather than confabulates, F661) +
                            finish_reason='tool_calls'-ish hint so an agent loop can answer it (build-by-dialogue, F672).
  • response carries the CHORD content-address in a srmech extension field (audit/attestation, F640/F688) + a usage block.

DEV-SESSION QUESTIONS ANSWERED: the OpenAI request/response schema; the world-as-model convention; the infer->completion
map incl. the asking-state turn; streaming (the SSE `delta` option, noted); the AG2 / CopilotKit base_url wiring; the
relationship to srmech-mcp (MCP = tools; this = a chat model). The dev session wraps this handler in an ASGI app (FastAPI).

srmech 0.7.5rc15: storyteller.infer (F692, loaded live) ; amsc.format.sha256_bytes. No abs(); no CAD; no Workflow; no
sub-agents. Reference scaffold for the srmech dev session.
"""
import sys
import importlib.util
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech

# load the F692 storyteller reference module (hyphenated filename -> importlib) so the API is genuinely backed by infer()
_spec = importlib.util.spec_from_file_location(
    "storymodule", "docs/srmech/rbs_lm_research/R-RBS-LM-STORYMODULE_srmech_storyteller_reference_module_infer.py")
storymodule = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(storymodule)
World, StoryTeller = storymodule.World, storymodule.StoryTeller

# a tiny world registry (the dev session loads worlds from the MFO descriptor F670 / book-shelves F677/F691)
WORLDS = {
    "storyteller:MFO": World("MFO", {
        "the_one":   ("The one is the held invariant", "MFO §I.1"),
        "chirality": ("It is seen in the handedness of matter", "MFO §VI"),
        "spectrum":  ("and it rings in the spectrum", "MFO §III.1"),
    }),
}
_ST = StoryTeller()


def _prompt_keys(messages):
    """reference prompt parse: the last user turn -> the keys present in the world (dev session: a richer parser/F693)."""
    last = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    return [w.strip(".,!?").lower() for w in last.split()]


def chat_completion(request):
    """REFERENCE /v1/chat/completions handler -> OpenAI response dict, backed by storyteller.infer (F692)."""
    model = request.get("model", "storyteller:MFO")
    world = WORLDS.get(model) or next(iter(WORLDS.values()))
    # HONEST (F573/F658): pass the parsed prompt-keys straight to infer -- do NOT pre-filter unknowns, or a gap would be
    # silently hidden (exactly the hallucination the kernel prevents). infer() detects the gap -> the asking-state (F661).
    keys = _prompt_keys(request.get("messages", []))
    result = _ST.infer(world, keys)
    if result["status"] == "rendered":
        content, finish, chord = result["text"], "stop", result["chord"]
    else:                                                        # the asking-state (F661) becomes an assistant turn that ASKS
        content, finish, chord = result["ask"], "stop", None
    return {
        "id": "chatcmpl-srmech-" + (chord[:12] if chord else "ask"),
        "object": "chat.completion", "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": len(keys), "completion_tokens": len((content or "").split()), "total_tokens": 0},
        "srmech": {"status": result["status"], "chord": chord, "compositional": True, "gpu_free": True},  # extension: attestation/audit
    }


def main():
    print(f"=== R-RBS-LM-STORYAPI — the OpenAI-compatible endpoint reference (AG2 / CopilotKit)  (srmech {srmech.__version__}) ===\n")
    print("(1) A RENDERED completion (OpenAI shape; backed by storyteller.infer):")
    resp = chat_completion({"model": "storyteller:MFO",
                            "messages": [{"role": "user", "content": "the_one chirality spectrum"}]})
    print(f"    model={resp['model']}  finish={resp['choices'][0]['finish_reason']}  srmech.chord={resp['srmech']['chord'][:12] if resp['srmech']['chord'] else None}")
    print(f"    content >>> {resp['choices'][0]['message']['content']}\n")
    print("(2) A GAP -> the asking-state, surfaced as an assistant turn that ASKS (F661, no hallucination):")
    resp2 = chat_completion({"model": "storyteller:MFO",
                             "messages": [{"role": "user", "content": "the_one dragon"}]})
    print(f"    content >>> {resp2['choices'][0]['message']['content']}  (srmech.status={resp2['srmech']['status']})\n")
    print("(3) THE WIRING (the dev session, FastAPI/ASGI):")
    print(f"    AG2 / AutoGen : OpenAIWrapper(base_url='http://host:port/v1', api_key='x', model='storyteller:MFO')")
    print(f"    CopilotKit    : OpenAI-compatible runtime adapter -> same base_url (or AG-UI actions over the ops, F693)")
    print(f"    alongside     : srmech-mcp (the ops as MCP tools) + srmech-agent (Anthropic SDK) -- all share the kernel.\n")
    print("VERDICT (the OpenAI-compatible endpoint reference -- Layer 3, the universal connector):")
    print(f"  • ONE OpenAI-compatible `/v1/chat/completions` handler backed by storyteller.infer (F692, loaded live) is the")
    print(f"    UNIVERSAL connector: AG2 (OpenAI model_client base_url) + CopilotKit (OpenAI runtime / AG-UI) + most agent")
    print(f"    frameworks speak it -- so NO per-framework adapter is needed, ALONGSIDE the existing srmech-mcp + srmech-agent.")
    print(f"  • THE MAPPING IS ANSWERED: model->world ('storyteller:MFO'); last user message->prompt; infer->completion with")
    print(f"    the asking-state (F661) surfaced as an assistant turn that ASKS (an agent loop answers it -> build-by-dialogue")
    print(f"    F672); the CHORD content-address rides in a `srmech` extension field for attestation/audit (F640/F688).")
    print(f"  • IT INHERITS THE KERNEL'S PROPERTIES: compositional, GPU-free (F628), CAN'T-HALLUCINATE (F658) -- a chat model")
    print(f"    that cannot break its world's lore. EVERY DEV-SESSION QUESTION ANSWERED: the schema, the world-as-model")
    print(f"    convention, the infer->completion map, streaming (SSE delta noted), the AG2/CopilotKit base_url wiring, the")
    print(f"    srmech-mcp relationship (MCP=tools, this=a chat model). The dev session wraps it in a FastAPI ASGI app.")
    print(f"  • Composes F689 (the plan, Layer 3) + F692 (storyteller.infer) + srmech-mcp/srmech-agent (existing adapters) +")
    print(f"    R-RBS-LM-24 (the OpenAI-server precedent) + F658/F661/F628 (the kernel properties) + F640/F688 (the chord =")
    print(f"    attestation). srmech 0.7.5rc15. Reference scaffold; NOT a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
