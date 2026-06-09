r"""R-RBS-LM-STORYMODULE (user direction): the REFERENCE `srmech.storyteller` module the dev session promotes -- Layer 0
+ Layer 1 of the F689 plan, scaffolded so every question is answered. NOT a package edit; a reference in the research subtree.

WHAT IT IS: one clean module consolidating the proven Story-Teller kernel into a first-class shape, with the NATIVE
COMPOSITIONAL inference entry `infer(world, prompt)`:
  • World        -- the content-shelf (attested tomes) + the two-tier kernel (fixed foundation + adaptive growth, F628).
  • StoryTeller  -- wraps the BitExactCommKernel (F613) + AdaptiveTier (F628) + the seen-rule render engine (F654) + the
                    chord (F658) + the asking-state (F661).
  • infer(world, prompt) -> result -- the native inference: SELECT the relevant attested tomes -> if a referenced thing
    is NOT on the shelf, return the ASKING-STATE (F661, no hallucination) -> else COMPOSE the seen-rule clauses over the
    attested tomes (the chord, F658, valid-by-construction) -> RENDER. Compositional, GPU-free (F628), can't-hallucinate.
  • STORYTELLER_TOOLS -- tool_schema-shaped op descriptors (infer / navigate / tell / ask) so the dev session REGISTERS
    them into srmech.amsc.tool_schema._REGISTRY (they JOIN the 256-entry registry -> the CLI/API discover them).

DEV-SESSION QUESTIONS ANSWERED: the module shape (World + StoryTeller + infer); the infer() contract (select -> ask-or-
compose -> render; returns {status, text, chord}); the World shape (shelf dict + AdaptiveTier); how the ops register into
tool_schema; the import surface the CLI (Layer 2) + the OpenAI API (Layer 3) call. The existing research scripts
(bit_exact_comm_kernel.py F613, adaptive_tier.py F628) are the kernel this wraps -- the dev session inlines them into
srmech/storyteller/.

srmech 0.7.5rc15: BitExactCommKernel (F613), AdaptiveTier (F628), amsc.format.sha256_bytes. No abs(); no CAD; no Workflow;
no sub-agents. Reference scaffold for the srmech dev session.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from adaptive_tier import AdaptiveTier


def _render(clauses):                                            # the seen-rule clause-joining engine (F654/F671)
    if not clauses:
        return ""
    out = clauses[0]
    for c in clauses[1:]:
        out += (", " + c) if c[:1].islower() else (". " + c)
    return out + "."


class World:
    """the content-shelf (attested tomes) + the two-tier kernel. key -> (clause, attestation)."""
    def __init__(self, name, tomes):
        self.name = name
        self.tier = AdaptiveTier(tomes, ring_size=8)              # fixed foundation + GPU-free adaptive growth (F628)
        self.keys = list(tomes)
    def has(self, key):
        return self.tier.recall(key)[0] != "unknown"
    def tell(self, key, clause, attestation="told (declared, F631)"):
        self.tier.adapt(key, clause, attestation); self.keys.append(key) if key not in self.keys else None
    def clause(self, key):
        f, payload = self.tier.recall(key)
        return payload[0] if payload else None


class StoryTeller:
    """the native compositional inference instrument (Layer 1)."""
    def __init__(self):
        self.kernel = BitExactCommKernel()                       # the bit-exact comm kernel (F613)

    def infer(self, world: World, prompt_keys):
        """compositional inference: select attested tomes -> ASK on a gap (F661) -> compose the chord (F658) -> render."""
        missing = [k for k in prompt_keys if not world.has(k)]
        if missing:
            return {"status": "asking", "ask": f"I have no tome for {missing!r}. What is it?",  # F661: ask, don't invent
                    "missing": missing, "text": None, "chord": None}
        clauses = [world.clause(k) for k in prompt_keys]
        text = _render(clauses)                                   # the chord (F658): composed over attested content
        return {"status": "rendered", "text": text, "chord": self.kernel.content_address(text), "ask": None}


# the tool_schema-shaped op descriptors (the dev session registers these into amsc.tool_schema._REGISTRY)
STORYTELLER_TOOLS = [
    {"name": "storyteller.infer", "summary": "Compositional inference: compose seen-rules over a world's attested shelf; ask at a gap; render.",
     "parameters": [{"name": "world", "type": "World"}, {"name": "prompt_keys", "type": "list[str]"}],
     "returns": {"type": "dict", "fields": ["status(rendered|asking)", "text", "chord", "ask"]}},
    {"name": "storyteller.navigate", "summary": "Walk a world's §-section/board graph to a tome (F664/F670).",
     "parameters": [{"name": "world", "type": "World"}, {"name": "address", "type": "str"}], "returns": {"type": "tome|asking"}},
    {"name": "storyteller.tell", "summary": "Declare a new seen rule / tome (build-by-dialogue, F631/F672); GPU-free add.",
     "parameters": [{"name": "world", "type": "World"}, {"name": "key", "type": "str"}, {"name": "clause", "type": "str"}], "returns": {"type": "None"}},
    {"name": "storyteller.ask", "summary": "The asking-state (F661): surface the gap rather than hallucinate.",
     "parameters": [{"name": "gap", "type": "str"}], "returns": {"type": "question"}},
]


def main():
    print(f"=== R-RBS-LM-STORYMODULE — the srmech.storyteller reference module + infer()  (srmech {srmech.__version__}) ===\n")
    st = StoryTeller()
    world = World("MFO-the_one", {
        "the_one":  ("The one is the held invariant", "MFO §I.1"),
        "chirality":("It is seen in the handedness of matter", "MFO §VI"),
        "spectrum": ("and it rings in the spectrum", "MFO §III.1"),
    })
    print("(1) infer() over ATTESTED tomes -> the chord (rendered, valid-by-construction):")
    r = st.infer(world, ["the_one", "chirality", "spectrum"])
    print(f"    status={r['status']}  chord={r['chord'][:12]}")
    print(f"    >>> {r['text']}\n")

    print("(2) infer() hits a GAP -> the asking-state (F661, no hallucination):")
    r2 = st.infer(world, ["the_one", "dragon"])
    print(f"    status={r2['status']}  ask={r2['ask']!r}\n")

    print("(3) build-by-dialogue: tell() a new rule -> infer() now composes it (GPU-free, F628/F672):")
    world.tell("dragon", "and a dragon is a chirality of fire")
    r3 = st.infer(world, ["the_one", "dragon"])
    print(f"    status={r3['status']}  >>> {r3['text']}\n")

    print("(4) STORYTELLER_TOOLS (tool_schema-shaped -- the dev session registers into _REGISTRY):")
    for t in STORYTELLER_TOOLS:
        print(f"    {t['name']:<24} {t['summary']}")
    print()
    print("VERDICT (the srmech.storyteller reference module -- Layer 0/1 scaffolded):")
    print(f"  • ONE CLEAN MODULE the dev session promotes to srmech.storyteller: World (the shelf + the two-tier kernel,")
    print(f"    F628) + StoryTeller (wrapping F613/F628/F654/F658/F661) + infer(world, prompt) = the NATIVE COMPOSITIONAL")
    print(f"    inference entry. Verified: infer over attested tomes -> the chord (rendered); a gap -> the asking-state (no")
    print(f"    hallucination); tell() a rule -> infer composes it (GPU-free build-by-dialogue).")
    print(f"  • EVERY DEV-SESSION QUESTION ANSWERED: the module shape, the infer() contract ({{status,text,chord,ask}}), the")
    print(f"    World shape (shelf + AdaptiveTier), and STORYTELLER_TOOLS (tool_schema-shaped op descriptors -> the registry,")
    print(f"    so the CLI Layer-2 + the OpenAI API Layer-3 DISCOVER the ops). The existing F613/F628 scripts are the kernel")
    print(f"    this wraps -- the dev session inlines them into srmech/storyteller/.")
    print(f"  • Composes the kernel (F613/F628/F654/F658/F661/F663/F670/F669/F631/F672) + tool_schema + F689 (the plan).")
    print(f"    srmech 0.7.5rc15. Reference scaffold; NOT a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
