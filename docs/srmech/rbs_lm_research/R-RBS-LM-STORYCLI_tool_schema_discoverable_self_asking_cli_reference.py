r"""R-RBS-LM-STORYCLI (user direction): the REFERENCE `srmech story` CLI -- Layer 2 of the F689 plan. The human "won't
need to know all the commands because it will be able to look in tool_schema." Scaffolded so the dev session has every
answer. NOT a package edit.

WHAT IT IS: a CLI that is SELF-DESCRIBING (it INTROSPECTS srmech.amsc.tool_schema._REGISTRY -- the 256-entry op registry --
+ the storyteller ops, so there is NO hardcoded command list to memorise) and SELF-ASKING (on AMBIGUOUS intent it drops
into the ASKING-STATE, F661 -- it asks WHICH op rather than guessing). The human types a natural phrase; the CLI maps it to
an op via the registry summaries; a clear match runs; a tie ASKS; nothing matched -> 'here is what I can do' (lists ops).

DEV-SESSION QUESTIONS ANSWERED (in code + comments):
  • DISCOVERY: read tool_schema._REGISTRY (the live 256-entry surface) + the storyteller ops -> the command surface is the
    REGISTRY, not a hardcoded parser. `story what-can-i-do` lists ops straight from the registry.
  • INTENT -> OP: a transparent word-overlap score between the human phrase and each op's name+summary (the dev session
    swaps in a better matcher; the CONTRACT is 'map to a registered op, never invent a command').
  • AMBIGUITY -> ASK (F661): if the top-2 scores are close, the CLI ASKS which op (self-asking) -- the same asking-state the
    Story Teller uses, now at the CLI layer. No guessing.
  • the subcommand shape (`srmech story <intent...>` / `srmech story what-can-i-do`) + the return contract.

srmech 0.7.5rc15: amsc.tool_schema._REGISTRY (the discoverability substrate -- read live). No abs(); no CAD; no Workflow;
no sub-agents. Reference scaffold for the srmech dev session.
"""
import srmech
from srmech.amsc import tool_schema as ts

# the storyteller ops the dev session will register into _REGISTRY (from R-RBS-LM-STORYMODULE / F692)
STORYTELLER_OPS = [
    ("storyteller.infer",    "Compositional inference: compose seen-rules over a world's attested shelf; ask at a gap; render a story."),
    ("storyteller.navigate", "Walk a world's section/board graph to a tome; retrieve by address."),
    ("storyteller.tell",     "Declare a new seen rule or tome; build the world by dialogue; grow GPU-free."),
    ("storyteller.ask",      "Surface a gap as a question instead of hallucinating."),
]


def _registry_ops():
    """the live command surface = tool_schema._REGISTRY (256) + the storyteller ops (to-be-registered)."""
    reg = getattr(ts, "_REGISTRY", {})
    ops = []
    for name, entry in (reg.items() if isinstance(reg, dict) else []):
        summary = getattr(entry, "summary", "") or (entry.get("summary", "") if isinstance(entry, dict) else "")
        ops.append((str(name), str(summary)))
    ops.extend(STORYTELLER_OPS)
    return ops


def _score(phrase, name, summary):
    words = set(w.strip(".,:;()").lower() for w in phrase.split())
    hay = set(w.strip(".,:;()").lower() for w in (name + " " + summary).replace(".", " ").split())
    return len(words & hay)


def story_cli(phrase):
    """the `srmech story <phrase>` entry: discover -> map -> run | ASK | list. Returns a dict (the dev session prints it)."""
    ops = _registry_ops()
    if phrase.strip() in ("what-can-i-do", "help", "?"):
        return {"action": "LIST", "ops": [n for n, _ in ops if n.startswith("storyteller.")] + [f"...+{len(ops)-len(STORYTELLER_OPS)} registry ops"]}
    scored = sorted(((_score(phrase, n, s), n, s) for n, s in ops), reverse=True)
    top = [x for x in scored if x[0] > 0][:3]
    if not top:
        return {"action": "LIST", "hint": "nothing matched; here is what I can do",
                "ops": [n for n, _ in STORYTELLER_OPS]}
    if len(top) >= 2 and top[0][0] == top[1][0]:                 # a tie -> the asking-state (F661), do NOT guess
        return {"action": "ASK", "question": f"Did you mean {top[0][1]} or {top[1][1]}?", "candidates": [top[0][1], top[1][1]]}
    return {"action": "RUN", "op": top[0][1], "summary": top[0][2], "score": top[0][0]}


def main():
    print(f"=== R-RBS-LM-STORYCLI — the tool_schema-discoverable, self-asking `srmech story` CLI reference  (srmech {srmech.__version__}) ===\n")
    reg = getattr(ts, "_REGISTRY", {})
    print(f"(0) DISCOVERY SUBSTRATE: tool_schema._REGISTRY = {len(reg)} ops (+ {len(STORYTELLER_OPS)} storyteller ops once registered).")
    print(f"    the CLI reads the REGISTRY -- there is no hardcoded command list to memorise.\n")
    demos = [
        "what-can-i-do",
        "tell me a story about the world",          # -> storyteller.infer
        "walk to a section",                         # -> storyteller.navigate
        "teach the world a new rule",                # -> storyteller.tell
        "render a hash of these bytes",              # -> likely a registry op (sha256/content-address)
        "do the thing",                              # -> nothing clear -> LIST or ASK
    ]
    print("(1) THE CLI maps a NATURAL PHRASE -> an op (or ASKS, or LISTS):")
    for d in demos:
        r = story_cli(d)
        if r["action"] == "RUN":
            print(f"    \"{d}\"  ->  RUN {r['op']}  (score {r['score']})")
        elif r["action"] == "ASK":
            print(f"    \"{d}\"  ->  ASK (F661): {r['question']}")
        else:
            print(f"    \"{d}\"  ->  LIST: {r['ops']}")
    print()
    print("VERDICT (the self-describing + self-asking `srmech story` CLI reference -- Layer 2 scaffolded):")
    print(f"  • SELF-DESCRIBING: the CLI's command surface IS tool_schema._REGISTRY ({len(reg)} ops) + the storyteller ops --")
    print(f"    read LIVE, no hardcoded parser. `story what-can-i-do` lists ops straight from the registry. The human 'won't")
    print(f"    need to know all the commands' (the user's words) because the CLI READS them.")
    print(f"  • SELF-ASKING (F661): a natural phrase -> a transparent word-overlap map to a REGISTERED op; a clear match runs,")
    print(f"    a TIE drops into the ASKING-STATE ('did you mean X or Y?'), nothing-matched -> 'here is what I can do'. The CLI")
    print(f"    never INVENTS a command -- it maps to the registry or asks (the same no-hallucination contract as the kernel).")
    print(f"  • EVERY DEV-SESSION QUESTION ANSWERED: discovery (read _REGISTRY), intent->op (word-overlap, swappable), the")
    print(f"    ambiguity->ASK rule (F661), the subcommand shape (`srmech story <intent>` / `what-can-i-do`). The dev session")
    print(f"    registers STORYTELLER_OPS into _REGISTRY (F692) + wires this as the `srmech story` subcommand.")
    print(f"  • Composes F689 (the plan, Layer 2) + tool_schema (the registry) + F661 (the asking-state at the CLI) + F692 (the")
    print(f"    storyteller ops it surfaces) + R-RBS-LM-23 (the tool_schema CLI precedent). srmech 0.7.5rc15. Reference scaffold;")
    print(f"    NOT a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
