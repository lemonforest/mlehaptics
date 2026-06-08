r"""R-RBS-LM-SURROUNDINGS (the user's gap, 2026-06-08): the Story Teller (F654) needs to talk about the SURROUNDINGS too,
not just the protagonist's actions.

THE GAP + ITS NAME: F654's Story Teller only emits the FIGURE -- the one, doing things (agent -> action -> patient; a
directed board-walk, Class C). A real story also describes the GROUND -- the SURROUNDINGS the figure moves THROUGH. This
is the FIGURE / GROUND distinction, and the ground is a DIFFERENT clause-type:
  • FIGURE clauses (dynamic, F654): agent + action + patient -- 'The child entered the forest.' (a board-walk).
  • GROUND clauses (stative / spatial -- NEW): entity + STATE, or entity + SPATIAL-RELATION -- 'The forest was dark.' /
    'The trees surrounded the path.' These DESCRIBE the surroundings (the setting), they do not walk a figure through it.

THE ETAK READING: the surroundings ARE the islands / stars / sea the etak-navigator moves through -- the GROUND, the
reference-environment. In etak the canoe is held + the surroundings MOVE PAST (F635/F651); so 'talking about the
surroundings' = describing the islands the journey passes. The FIGURE is the board-walk (the one, dynamic); the GROUND is
the setting it moves through (stative). A scene = GROUND (establish the surroundings) + FIGURE (walk the one through them).

IT IS MORE SEEN RULES, DECLARED (F654/F655): the ground layer adds the stative BE (was/were, number-agreement), property
adjectives (dark/cold/tall -- Y-abstract), and spatial-relation verbs/preps (surround / border / beside / above). All
declared, not trained -- the same engine, a new clause-type.

srmech 0.7.5rc15: amsc.format.sha256_bytes (attested setting-content tomes). The engine = seen string cascades. No abs();
no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

CONTENT = {  # attested content tomes (F630): the SETTING entities (N/O/M classes) + properties (Y) + the figure
    "child": {"cls": "A-person", "pron": "she", "num": "sg"},
    "forest": {"cls": "M-plant", "num": "sg"}, "trees": {"cls": "M-plant", "num": "pl"},
    "path": {"cls": "O-place", "num": "sg"}, "wind": {"cls": "N-sky", "num": "sg"},
    "river": {"cls": "N-water", "num": "sg"}, "mountain": {"cls": "O-place", "num": "sg"},
    "fox": {"cls": "E-animal", "num": "sg"},
}
PROPS = ["dark", "cold", "tall", "deep", "wide", "quiet"]              # Y-abstract property adjectives (the GROUND's qualities)
IRREG_PAST = {"see": "saw", "find": "found", "come": "came", "run": "ran"}
def past(v):
    if v in IRREG_PAST: return IRREG_PAST[v]
    return v + ("d" if v.endswith("e") else "ed")

# ---- FIGURE clause (F654): the one doing things (dynamic board-walk) ----
def figure_clause(subj, verb, obj, subj_pron=False, obj_def=False):
    s = subj if subj_pron else f"the {subj}"
    o = f"the {obj}" if obj_def else f"a {obj}"
    sent = f"{s} {past(verb)} {o}."
    return sent[0].upper() + sent[1:]

# ---- GROUND clauses (NEW): describe the surroundings (stative + spatial) ----
def state(entity, adj):                                               # stative BE + property (number-agreement: was/were)
    be = "was" if CONTENT[entity]["num"] == "sg" else "were"
    return f"The {entity} {be} {adj}."

def locate(subj, rel, ground):                                        # spatial relation between two setting-entities
    return f"The {subj} {past(rel)} the {ground}."                    # 'The trees surrounded the path.'

def scene(ground_clauses, hero, figure_events):
    """a SCENE = GROUND (establish the surroundings) + FIGURE (walk the one through them)."""
    ground = " ".join(ground_clauses)
    fig = []
    for i, (v, o, d) in enumerate(figure_events):
        fig.append(figure_clause(hero, v, o) if i == 0
                   else figure_clause(CONTENT[hero]["pron"], v, o, subj_pron=True, obj_def=d))
    return ground + "  " + " ".join(fig)


def main():
    print(f"=== R-RBS-LM-SURROUNDINGS — the GROUND layer: how the Story Teller describes the surroundings  (srmech {srmech.__version__}) ===\n")

    # (1) the FIGURE / GROUND distinction -- two different clause-types
    print("(1) FIGURE vs GROUND -- two clause-types (the Story Teller had only the FIGURE; the GROUND is the surroundings):")
    print(f"    FIGURE (dynamic, F654): {figure_clause('child', 'enter', 'forest')}   (agent->action->patient, a board-walk)")
    print(f"    GROUND (stative, NEW) : {state('forest', 'dark')}             (entity + STATE -- describes the surroundings)")
    print(f"    GROUND (spatial, NEW) : {locate('trees', 'surround', 'path')}   (entity + SPATIAL-RELATION)\n")

    # (2) a SCENE = GROUND (establish surroundings) + FIGURE (walk the one through them)
    print("(2) A SCENE = GROUND (the surroundings) + FIGURE (the one moving through them):")
    sc = scene(
        [state("forest", "dark"), locate("trees", "surround", "path"), state("wind", "cold")],
        "child",
        [("enter", "forest", False), ("find", "fox", False)],
    )
    print(f"    {sc}")
    print(f"    -> the GROUND establishes WHERE + WHAT-IT-IS-LIKE (the surroundings); the FIGURE walks the one through it.")
    print(f"    Setting first (the islands), then the journey (the one) -- the etak reading: the surroundings the voyage passes.\n")

    # (3) attested setting-content + the new seen rules (declared, not trained)
    print("(3) SETTING-CONTENT is attested (F630); the GROUND clause-types are SEEN rules (declared, F654/F655):")
    for e in ["forest", "trees", "wind"]:
        addr = fmt.sha256_bytes(f"setting:{e}:{CONTENT[e]['cls']}".encode())[:8]
        print(f"    setting tome '{e}' [{CONTENT[e]['cls']}, {CONTENT[e]['num']}] -> attested addr {addr}")
    print(f"    new SEEN rules declared: stative BE (was/were + number-agreement), property adjectives (Y: {PROPS[:3]}...),")
    print(f"    spatial-relation verbs (surround/border/beside/above). Same engine -- a new clause-TYPE, declared not trained.\n")

    print("VERDICT (the Story Teller describes the surroundings via a GROUND layer -- the figure/ground distinction):")
    print(f"  • THE GAP NAMED + FILLED: F654 emitted only the FIGURE (the one + actions, a dynamic board-walk). The")
    print(f"    SURROUNDINGS are the GROUND -- a DIFFERENT clause-type: STATIVE (entity + state: 'The forest was dark.') and")
    print(f"    SPATIAL (entity + relation: 'The trees surrounded the path.'). A SCENE = GROUND (establish the surroundings)")
    print(f"    + FIGURE (walk the one through them) -- demonstrated as one coherent scene.")
    print(f"  • THE ETAK READING: the surroundings ARE the islands/stars/sea the etak-navigator moves through (the GROUND,")
    print(f"    the reference-environment held while the canoe stays fixed, F635/F651). 'Talking about the surroundings' =")
    print(f"    describing the islands the journey passes. FIGURE = the dynamic board-walk (the one); GROUND = the stative")
    print(f"    setting it moves through. (And the GROUND is spatial -- the same place ASL puts its LOCI, F637/F644.)")
    print(f"  • IT IS MORE SEEN RULES, DECLARED (F654/F655): the ground layer adds stative BE (number-agreement), property")
    print(f"    adjectives (Y-abstract), and spatial-relation verbs/preps -- all DECLARED, not trained; the setting-entities")
    print(f"    are attested content tomes (F630). Same engine, a new clause-TYPE -- exactly the F655 reduction (a new")
    print(f"    capability = declared seen rules + attested content, not a retrain).")
    print(f"  • Composes F654 (the FIGURE Story Teller this completes with a GROUND) + F633 (the clause board-walk) + F651")
    print(f"    (the setting per journey-leg) + F637/F644 (the spatial / loci reading) + F635 (etak: surroundings = the")
    print(f"    islands moving past) + F630 (attested setting-content) + F655 (new capability = declared rules). srmech")
    print(f"    0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
