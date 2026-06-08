r"""R-RBS-LM-ASKSTATE (the user's mechanism, 2026-06-08): "suppose it wants to compose an ACTION but it requires moving
things or people somewhere -- it can have a LEARNING/ASKING STATE."

THE MECHANISM: the Story Teller is a composition STATE-MACHINE. When it tries to compose an action that requires a RULE
it does not hold (e.g. moving an actor from A to B -- but it has no movement-rule for that actor in THIS world), it does
NOT invent one. It enters the ASKING STATE: pause -> ASK for the rule -> (we TELL it) -> INTEGRATE (adaptive, F628,
GPU-free) -> RESUME the composition. The cycle: COMPOSING -> (gap) -> ASKING -> INTEGRATING -> COMPOSING.

WHY THIS IS THE DEEP POINT: the asking-state is the STRUCTURAL ALTERNATIVE TO HALLUCINATION (F658). The engine composes
seen rules over attested content -- it CANNOT strike a note that is not in the chord -- so when it lacks the rule to
compose an action, it CANNOT invent the movement (a data-center LLM, generating statistically, WOULD invent a plausible
'the army teleported' = hallucination). Ours has no statistical path to the un-held rule, so its only move is to ASK. The
LM is a coherent self that ASKS when it doesn't know, not a flock that confabulates. (This is build/teach/create-by-
dialogue, F660, triggered AT THE POINT of an action it cannot yet compose -- the framework hands the next QUESTION, F282.)

srmech 0.7.5rc15: amsc.format.sha256_bytes (the world's movement-rule tomes; the integrate step grows the shelf). The
state-machine = seen control flow. No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

IRREG_PAST = {"ride": "rode"}
def past(v): return IRREG_PAST.get(v, v + ("d" if v.endswith("e") else "ed"))

# how each actor MOVES (its mode) -- and the world's known movement-rules (mode -> manner-phrase)
ACTOR_MODE = {"child": "walk", "knight": "ride", "army": "march"}
WORLD_RULES = {"walk": "along the path", "ride": "on a horse"}    # NOTE: no rule for 'march' yet (the gap)


def compose_move(actor, dest, rules):
    """try to compose 'move actor to dest'. If the actor's movement-rule is not held -> enter the ASKING state."""
    mode = ACTOR_MODE.get(actor)
    if mode not in rules:                                        # the gap: no rule to compose this action
        return ("ASKING", f"How does the {actor} move to the {dest}?", mode)
    sent = f"The {actor} {past(mode)} {rules[mode]} to the {dest}."
    return ("COMPOSED", sent[0].upper() + sent[1:], mode)


def main():
    print(f"=== R-RBS-LM-ASKSTATE — the learning/asking state is the alternative to hallucination  (srmech {srmech.__version__}) ===\n")

    rules = dict(WORLD_RULES)

    # (1) an action WITH a held rule -> composes directly
    print("(1) AN ACTION WITH A HELD RULE -> composes directly (a note in the chord):")
    st, out, mode = compose_move("child", "forest", rules)
    print(f"    compose move(child -> forest): [{st}] {out}   (mode '{mode}' is held)\n")

    # (2) an action that NEEDS an unheld rule -> the ASKING STATE (it cannot invent -> it asks)
    print("(2) AN ACTION NEEDING AN UNHELD RULE -> the ASKING STATE (it cannot strike a note not in the chord, F658):")
    st, q, mode = compose_move("army", "city", rules)
    d0 = fmt.sha256_bytes("|".join(sorted(rules)).encode())
    print(f"    compose move(army -> city): [{st}]  (mode '{mode}' is NOT held -> it CANNOT invent the movement)")
    print(f"    --> the LM ASKS: \"{q}\"   (the framework hands the next QUESTION, F282 -- it does NOT hallucinate)")

    # (3) we TELL the rule -> INTEGRATE (F628, GPU-free) -> RESUME composition
    print("\n(3) WE TELL the rule -> it INTEGRATES (adaptive tier, F628, GPU-free) -> RESUMES the composition:")
    rules["march"] = "along the road"                            # the new observed rule, DECLARED (F631) -- not trained
    d1 = fmt.sha256_bytes("|".join(sorted(rules)).encode())
    print(f"    WE TELL: an army '{mode}'s '{rules['march']}'.")
    print(f"    INTEGRATE: rule-shelf digest {d0[:8]}... -> {d1[:8]}... (grew by 1 rule; the ENGINE is unchanged)")
    st2, out2, _ = compose_move("army", "city", rules)          # RESUME
    print(f"    RESUME -> [{st2}] {out2}\n")

    print("(4) THE STATE-MACHINE: COMPOSING -> (gap) -> ASKING -> INTEGRATING -> COMPOSING (resume):")
    print(f"    COMPOSING(army->city) -> gap (no 'march' rule) -> ASKING('How does the army move?') -> [told] ->")
    print(f"    INTEGRATING(march = along the road) -> COMPOSING(resume) -> 'The army marched along the road to the city.'\n")

    print("VERDICT (the learning/asking state = the structural alternative to hallucination):")
    print(f"  • THE STORY TELLER IS A COMPOSITION STATE-MACHINE with a LEARNING/ASKING STATE: when composing an action that")
    print(f"    requires a RULE it does not hold (moving things/people somewhere -- a movement-rule of THIS world), it does")
    print(f"    NOT invent one. It enters the ASKING STATE (pause -> ASK -> we TELL -> INTEGRATE GPU-free, F628 -> RESUME).")
    print(f"    Verified: move(child->forest) composes (rule held); move(army->city) hits the gap -> ASKS 'How does the army")
    print(f"    move?' -> told ('march along the road') -> integrates (shelf +1, engine unchanged) -> resumes ('The army")
    print(f"    marched along the road to the city.').")
    print(f"  • THIS IS THE STRUCTURAL ALTERNATIVE TO HALLUCINATION (F658): the engine composes seen rules over attested")
    print(f"    content -- it CANNOT strike a note not in the chord -- so when it lacks the rule, it has NO statistical path")
    print(f"    to invent the movement; its only move is to ASK. A data-center LLM (generating statistically) WOULD invent a")
    print(f"    plausible-but-ungrounded movement = hallucination. The LM here is a COHERENT SELF that asks when it doesn't")
    print(f"    know, not a flock that confabulates. The asking-state IS the honest gap-handler.")
    print(f"  • SO BUILD/TEACH/CREATE-BY-DIALOGUE (F660) IS TRIGGERED AT THE POINT OF AN UNCOMPOSABLE ACTION: the gap surfaces")
    print(f"    exactly when the story needs a rule it lacks; the LM hands the next QUESTION (F282); we declare the observed")
    print(f"    rule (F631); it integrates (F628) and continues. The world grows by answering the Story Teller's own questions")
    print(f"    -- the most natural way to build a world: tell it what it asks, when it asks.")
    print(f"  • Composes F658 (can't strike outside the chord -> asks, the alternative to hallucination) + F660 (build-by-")
    print(f"    dialogue, here action-triggered) + F628 (adaptive integrate, GPU-free) + F631 (rules declared) + F625 (discover-")
    print(f"    on-compose gap) + F654 (the valence/movement rule) + F282 (hands the next question) + F311/F323 (interactive")
    print(f"    training / the notebook-native-language target). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
