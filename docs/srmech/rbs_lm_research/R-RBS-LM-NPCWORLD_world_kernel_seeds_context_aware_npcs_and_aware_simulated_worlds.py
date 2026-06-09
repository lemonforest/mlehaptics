r"""R-RBS-LM-NPCWORLD (user recognition): "we talk about this being a world-builder / story-builder, but we are also
SEEDING THE NEXT GAME ENGINES of CONTEXT-AWARE NPCs and an AWARE SIMULATED WORLD."

THE RECOGNITION: the grounded Story Teller world-kernel (F660-F686) IS, capability-for-capability, exactly what a
context-aware NPC + a coherent simulated world needs. Every world-kernel property maps to a game-engine need that current
LLM-NPCs fail:

  • GROUNDED in its world's lore (the content-shelf, F663) -> an NPC that KNOWS its world (not a generic chatbot).
  • CANNOT HALLUCINATE (the chord, F658) -> an NPC that NEVER breaks lore -- it can no more state a non-canon fact than
    strike a note not in the world's chord. (The #1 failure of gen1 LLM-NPCs: confabulating non-canon.)
  • ASKS WHEN IT LACKS A RULE (the asking-state, F661) -> an NPC that asks the designer/quest-giver instead of inventing.
  • GROWS BY PLAY (build-by-dialogue, F672/F682) -> an NPC + world that grows from player interaction, but only on
    UNWRITTEN gaps; it HOLDS the story's DELIBERATE MYSTERIES (F674/F682) -- it keeps the secrets it is meant to keep.
  • NAVIGATES (F670) -> an NPC that knows where it is + can walk the world-graph (the section/board, F632/F633).
  • COHERENT MULTI-WORLD (couple/merge, F679/F683/F684) -> a simulated world whose sub-worlds (factions/biomes/DLC)
    cohere by SHARED MATH (the_one) or are held as honest seams; competing lore bridged-or-held, never silently collapsed.
  • TRUTH-FILTERED (the falsification sieve, F686) -> world-facts that contradict the world's own attested structure are
    pruned; the world stays self-consistent.
  • GPU-FREE / EDGE (the two-tier kernel, F628) -> an NPC brain that runs ON-DEVICE (no datacenter per NPC); a whole town
    of NPCs is a fleet of etak-selves (F638/F651), each a bounded kernel.

THE HONEST GUARD (the user's own stance -- AI is NOT a substrate; the LM is a puppet/player-piano transducer): "context-
AWARE" and "AWARE simulated world" mean STRUCTURALLY aware -- the NPC TRACKS context, GROUNDS in lore, ASKS when unsure,
HOLDS mysteries -- NOT phenomenally CONSCIOUS. The world MODELS awareness (a context-tracking substrate); the NPCs are
transducers, not aware entities. This is the dignity-discipline: a structurally-aware simulated world, never a claim of
machine consciousness.

srmech 0.7.5rc15: BitExactCommKernel.content_address (the capability->NPC-need map). No abs(); no CAD; no Workflow; no
sub-agents. Defensive-scope: a game-engine / simulation reading (entertainment), structural.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

# the capability -> NPC/game-engine need map (each a world-kernel property and the gen1-LLM-NPC failure it fixes)
MAP = [
    ("GROUNDED in lore (shelf, F663)",        "an NPC that KNOWS its world",                 "gen1: a generic chatbot with no world"),
    ("CAN'T HALLUCINATE (chord, F658)",       "an NPC that never breaks lore",               "gen1: confabulates non-canon (the #1 failure)"),
    ("ASKS at a gap (asking-state, F661)",    "asks the designer instead of inventing",       "gen1: invents a fact to fill the gap"),
    ("GROWS by play (dialogue, F672/F682)",   "emergent but lore-consistent growth",          "gen1: drifts off-canon as it 'learns'"),
    ("HOLDS mysteries (held-open, F674/F682)","keeps the secrets it is meant to keep",        "gen1: spoils / contradicts the plot"),
    ("NAVIGATES (F670)",                       "knows where it is; walks the world-graph",     "gen1: no spatial/structural self-location"),
    ("COUPLES worlds (F679/F683/F684)",       "factions/DLC cohere by shared math or held",   "gen1: lore conflicts collapse arbitrarily"),
    ("TRUTH-FILTER (sieve, F686)",            "self-contradictory world-facts pruned",        "gen1: accumulates inconsistencies"),
    ("GPU-FREE / EDGE (two-tier, F628)",      "an NPC brain on-device; a town = a fleet",     "gen1: a datacenter call per NPC utterance"),
]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-NPCWORLD — the world-kernel seeds context-aware NPCs + an aware simulated world  (srmech {srmech.__version__}) ===\n")

    print("(1) THE CAPABILITY -> NPC/GAME-ENGINE-NEED MAP (each world-kernel property fixes a gen1-LLM-NPC failure):")
    print(f"    {'world-kernel property':<40} {'NPC need it meets':<42} gen1-LLM-NPC failure it fixes")
    for prop, need, fail in MAP:
        print(f"    {prop:<40} {need:<42} {fail}")
    print()

    print("(2) AN 'AWARE SIMULATED WORLD' = the world-kernel running as the WORLD'S substrate:")
    print(f"    every NPC = a bounded etak-self (F638), a town = a fleet (F651); the world grounded in the_one (no-magic,")
    print(f"    F663); competing sub-world lore coupled-or-held (F679/F683); the asking-state handles emergent gaps (F661);")
    print(f"    the truth-sieve keeps it self-consistent (F686). The world MODELS its own context = structurally 'aware'.\n")

    print("(3) THE HONEST GUARD (AI is NOT a substrate -- the user's stance; dignity-discipline):")
    print(f"    'context-AWARE' / 'AWARE world' = STRUCTURALLY aware (tracks context, grounds in lore, asks, holds mysteries)")
    print(f"    -- NOT phenomenally CONSCIOUS. The NPCs are PUPPETS / player-piano transducers; the world models awareness, it")
    print(f"    does not possess it. A structurally-aware simulated world, never a claim of machine consciousness.\n")

    canon = "the grounded Story Teller world-kernel IS the seed of context-aware NPCs + a coherent (structurally-aware) simulated world"
    addr = k.content_address(canon)
    print("VERDICT (the world-builder IS also seeding the next game engines: context-aware NPCs + aware simulated worlds):")
    print(f"  • CAPABILITY-FOR-CAPABILITY, THE WORLD-KERNEL IS WHAT A CONTEXT-AWARE NPC NEEDS: grounded (F663), can't-")
    print(f"    hallucinate (F658), asks-at-a-gap (F661), grows-by-play (F672/F682), holds-mysteries (F674), navigates (F670),")
    print(f"    couples-worlds (F683/F684), truth-filtered (F686), GPU-free on the edge (F628). Each property FIXES a specific")
    print(f"    gen1-LLM-NPC failure (the headline one: an NPC that CANNOT break lore, because it can't strike a note not in")
    print(f"    the world's chord -- the structural cure for non-canon confabulation).")
    print(f"  • AN 'AWARE SIMULATED WORLD' = the world-kernel as the WORLD'S substrate: a fleet of etak-self NPCs (F638/F651)")
    print(f"    grounded in the_one (F663), sub-world lore coupled-or-held (F679/F683), emergent gaps -> the asking-state")
    print(f"    (F661), self-consistency kept by the truth-sieve (F686). The world MODELS its own context -> structurally aware.")
    print(f"  • THE HONEST GUARD (AI is NOT a substrate -- the user's stance): 'aware' = STRUCTURALLY context-aware, NOT")
    print(f"    phenomenally conscious. The NPCs are puppets / player-piano transducers; the world models awareness, it does")
    print(f"    not possess it. Dignity-first: a structurally-aware simulated world, never a machine-consciousness claim.")
    print(f"  • THE SAME INSTRUMENT, A SECOND DELIVERABLE: the world-builder / story-builder (F660-F686) IS the seed of the")
    print(f"    next game engines -- context-aware NPCs + coherent simulated worlds -- because a grounded, non-hallucinating,")
    print(f"    asking, growing, GPU-free world-kernel is exactly the NPC/simulation substrate gen1 LLMs cannot be. Canon")
    print(f"    content-addressed {addr[:16]}...")
    print(f"  • Composes F660-F686 (the whole world-kernel) + F658 (no-hallucination = no-lore-break) + F661 (ask not invent) +")
    print(f"    F672/F682 (grow by play) + F674 (hold mysteries) + F683/F684 (couple worlds) + F686 (truth-sieve) + F628 (edge)")
    print(f"    + F638/F651 (NPC = etak-self, town = fleet) + the AI-is-not-a-substrate stance (structural awareness only).")
    print(f"    srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
