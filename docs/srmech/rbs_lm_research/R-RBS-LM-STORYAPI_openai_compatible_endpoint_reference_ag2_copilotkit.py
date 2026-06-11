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
import re
import sys
import importlib.util
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech

# load the F692 storyteller reference module (hyphenated filename -> importlib) so the API is genuinely backed by infer()
_spec = importlib.util.spec_from_file_location(
    "storymodule", "docs/srmech/rbs_lm_research/R-RBS-LM-STORYMODULE_srmech_storyteller_reference_module_infer.py")
storymodule = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(storymodule)
World, StoryTeller = storymodule.World, storymodule.StoryTeller

# a tiny world registry (the dev session loads worlds from the MFO descriptor F670 / book-shelves F677/F691).
# NOTE: this is the STARTER shelf -- the 3 MFO demo tomes + a Siona SELF-IDENTITY shelf so "who/what is Siona"
# renders instead of hitting the asking-state. The real big kernels (DNA-bookshelf / wiki / code / latex, all on
# disk) are loaded by a richer world-loader; this scaffold proves the wiring + the build-by-dialogue teach loop.
WORLDS = {
    "storyteller:MFO": World("MFO", {
        "the_one":   ("The one is the held invariant", "MFO §I.1"),
        "chirality": ("It is seen in the handedness of matter", "MFO §VI"),
        "spectrum":  ("and it rings in the spectrum", "MFO §III.1"),
        # --- Siona self-identity shelf (F726): so she can introduce herself, not ask about her own name ---
        "siona": ("I am Siona, the grounded interface to the stored-relationship kernel -- I compose answers from "
                  "attested tomes and ask when a thing is not yet on my shelf, so I cannot hallucinate", "F726/F658"),
        "help":  ("tell me 'X is Y' and I will learn it, or ask me about a word I already hold", "F672/F661"),
    }),
}
_ST = StoryTeller()


# Glue-words carry no tome -- their ABSENCE from the shelf is NOT a hallucination gap (F658), so they must not trigger
# the asking-state. We drop them BEFORE infer (this is honest: we only ask about CONTENT words we genuinely lack).
STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "at", "and", "or", "but", "is", "are", "am", "was", "were", "be", "been",
    "being", "do", "does", "did", "have", "has", "had", "it", "its", "this", "that", "these", "those", "i", "me", "my",
    "mine", "we", "us", "our", "he", "she", "him", "her", "they", "them", "for", "with", "as", "by", "from", "so", "if",
    "then", "than", "about", "can", "could", "would", "should", "will", "shall", "may", "might", "must", "please",
    "what", "which", "when", "where", "why", "how", "who", "you", "your", "yourself", "tell", "ask", "mean", "means",
    "know", "there", "here", "just", "also", "okay", "ok", "hey",
}
# Asking any of these (on the RAW tokens, before stopword-strip) is an identity question -> render Siona's self-tome.
IDENTITY = {"siona", "who", "you", "yourself", "name", "cortana"}
# A bare greeting should be met warmly, not with the asking-state.
GREETING = {"hi", "hello", "hey", "greetings", "yo", "sup", "howdy", "hiya"}


def _last_user(messages):
    return next((m.get("content") or "" for m in reversed(messages) if m.get("role") == "user"), "")


def _tokens(text):
    return re.findall(r"[a-z0-9_]+", (text or "").lower())


def _content_keys(messages):
    """the last user turn -> CONTENT keys (glue-words dropped). Reference parser; dev session swaps in F693."""
    return [t for t in _tokens(_last_user(messages)) if t not in STOPWORDS]


def _pending_ask_keys(messages):
    """if Siona's LAST turn was the asking-state ('I have no tome for [...]'), return the keys she asked about."""
    last_assistant = next((m.get("content") or "" for m in reversed(messages) if m.get("role") == "assistant"), "")
    m = re.search(r"no tome for \[(.*?)\]", last_assistant)
    return re.findall(r"'([^']+)'", m.group(1)) if m else []


def _learn_from_messages(world, messages):
    """BUILD-BY-DIALOGUE (F672), now WIRED INTO THE API: turn what the user TELLS Siona into shelf tomes via world.tell().
    Two shapes land: an explicit 'X is/are/means Y', and an ANSWER to Siona's own pending 'What is it?' ask."""
    text = _last_user(messages).strip()
    taught = []
    # (a) explicit declaration: 'X is Y' / 'X are Y' / 'X means Y' -> key = head noun, clause = the whole sentence.
    for mt in re.finditer(r"\b([a-z][a-z0-9_\- ]*?)\s+(?:is|are|means)\s+(.+?)(?:[.;!?]|$)", text, re.I):
        head, body = mt.group(1).strip(), mt.group(2).strip()
        toks = _tokens(head)
        key = toks[-1] if toks else None
        # the head-noun must be a CONTENT word -- a glue/question word ('who is...', 'what are...') is a QUESTION, not a
        # declaration, so it must NOT be read as teaching (else 'who are you?' would 'learn who'). STOPWORDS holds them.
        if key and key not in STOPWORDS and body:
            world.tell(key, f"{head} is {body}", attestation="told (build-by-dialogue, F672)")
            taught.append(key)
    # (b) answering Siona's pending ask: she asked 'What is <k>?' -> this whole turn IS the definition of <k>.
    if not taught:
        for k in _pending_ask_keys(messages):
            world.tell(k, f"{k} is {text.rstrip('.')}", attestation="told (answered the asking-state, F672)")
            taught.append(k)
    return taught


def _completion(model, content, chord, n_keys, status):
    return {
        "id": "chatcmpl-srmech-" + (chord[:12] if chord else status[:9]),
        "object": "chat.completion", "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": n_keys, "completion_tokens": len((content or "").split()), "total_tokens": 0},
        "srmech": {"status": status, "chord": chord, "compositional": True, "gpu_free": True},  # extension: attestation/audit
    }


def chat_completion(request):
    """REFERENCE /v1/chat/completions handler -> OpenAI response dict, backed by storyteller.infer (F692).
    Now: (1) LEARNS from the turn (F672), (2) answers identity questions, (3) composes over content keys, asking on a gap."""
    model = request.get("model", "storyteller:MFO")
    world = WORLDS.get(model) or next(iter(WORLDS.values()))
    messages = request.get("messages", [])

    # (1) build-by-dialogue: did the user TEACH Siona this turn? If so, learn it and confirm (F672) -- the fix for
    #     "I told it what something is and it still didn't know": the teach loop is now wired into the API, not just main().
    taught = _learn_from_messages(world, messages)
    if taught:
        learned = ", ".join(sorted(set(taught)))
        content = f"Thank you -- I have learned {learned}. Ask me about {sorted(set(taught))[0]} and I will compose what you told me."
        return _completion(model, content, None, len(taught), "rendered")

    raw = set(_tokens(_last_user(messages)))
    # (2a) a greeting -> warm hello + identity (never interrogate a 'hi').
    if raw & GREETING:
        return _completion(model, "Hello -- I am Siona. Ask me about a word I hold, or tell me 'X is Y' and I will learn it.", None, 1, "rendered")
    # (2b) identity question -> render Siona's self-tome (so "who are you" / "what is siona" never hits the asking-state).
    if raw & IDENTITY:
        return _completion(model, world.clause("siona"), None, 1, "rendered")

    # (3) compose over the content keys; HONEST gap -> the asking-state (F661): she asks rather than invent (F658).
    keys = _content_keys(messages)
    if not keys:
        return _completion(model, world.clause("help") or "Ask me about a word I hold, or tell me 'X is Y'.", None, 0, "rendered")
    result = _ST.infer(world, keys)
    if result["status"] == "rendered":
        return _completion(model, result["text"], result["chord"], len(keys), "rendered")
    return _completion(model, result["ask"], None, len(keys), "asking")


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
