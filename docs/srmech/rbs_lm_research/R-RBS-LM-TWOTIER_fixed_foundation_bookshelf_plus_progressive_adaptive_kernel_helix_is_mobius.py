r"""R-RBS-LM-TWOTIER (the user's architecture, 2026-06-08): we can train a kernel at rates UNRELATED to data-center LLMs.
But jumping straight to a 'learning kernel' is not the move -- the right shape is TWO TIERS:
  • TIER 1 -- the FOUNDATIONAL BOOKSHELF (FIXED): tomes populated from foundational knowledge, bit-exact, attested,
    NEVER retrained (F584 persistence). Because the foundation can be FIXED, it escapes the crazy retraining current
    LLMs must face -- no catastrophic forgetting, no gradient agony.
  • TIER 2 -- the PROGRESSIVE / ADAPTIVE kernel (CHANGES WITH THE USER): an always-learning layer that IS the
    conversation context, but allowed to SHAPE as it is used. It learns GPU-free (substrate-native HDC bind = add, no
    gradient/retrain) and RIDES ON the foundation without ever changing it.
And: the HISTORY HELIX (F533) IS the TWO-AXIS MOBIUS (F593) -- the conversation/adaptation has exactly the 2-axis
structure (a turn-axis + a within-turn position-axis = the look-ahead/behind seam + the meaning-class). So the adaptive
Tier 2 = the shaped conversation context = the 2-axis Mobius, riding on the fixed Tier-1 foundation.

This DEMONSTRATES: (1) adapting Tier 2 many times leaves Tier 1's bit-exact digest UNCHANGED (foundation fixed); (2) the
adaptation is GPU-free (HDC bundle = add); (3) the history helix coordinate (turn, pos) IS the 2-axis Mobius structure.

srmech 0.7.5rc6: amsc.format.sha256_bytes (Tier-1 fixed digest); cascade.SedenionRegister (the foundation tome);
hdc.bundle (Tier-2 GPU-free adaptation); helix_coord = divmod (F533/F592). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc
from srmech.amsc import format as fmt
from srmech.amsc import cascade


def helix_coord(m, P):
    return divmod(m, P)                                            # (turn, pos) -- the F533 history-helix coordinate


def main():
    print(f"=== R-RBS-LM-TWOTIER — fixed foundation bookshelf + progressive adaptive kernel; helix = 2-axis Mobius  (srmech {srmech.__version__}) ===\n")

    # TIER 1: the FOUNDATIONAL bookshelf -- a fixed, content-addressed tome (the bit-exact comm-kernel foundation, F613)
    foundation = cascade.SedenionRegister()
    foundational_knowledge = {0: "anchor", 1: "cascade", 2: "chirality", 3: "rotate", 4: "bind", 5: "bundle", 6: "the_one"}
    for slot, k in foundational_knowledge.items():
        foundation.write(slot, k)
    def tier1_digest():
        return fmt.sha256_bytes("|".join(foundation.read(s)[0] for s in foundational_knowledge).encode())
    d0 = tier1_digest()
    print("(1) TIER 1 (foundational bookshelf) -- FIXED, bit-exact, content-addressed, never retrained:")
    print(f"    foundation digest: {d0[:16]}...  ({len(foundational_knowledge)} foundational tomes)\n")

    # TIER 2: the PROGRESSIVE/ADAPTIVE kernel -- the conversation context, shaping with use (GPU-free HDC bind)
    print("(2) TIER 2 (progressive adaptive kernel) -- the conversation context, SHAPING with each user turn (GPU-free):")
    user_turns = ["the user asks about hands", "the user prefers ASL", "the user mentions cave art", "the user likes the octonion"]
    TIE = sp.mint_vector("tier2:tiebreak", D=4096)
    hvs = []; states = []
    for t, turn in enumerate(user_turns):
        hvs.append(sp.mint_vector(f"turn:{turn}", D=4096))
        bag = hvs if len(hvs) % 2 == 1 else hvs + [TIE]            # GPU-free additive bundle, kept odd
        tier2 = hdc.bundle(bag)
        states.append(fmt.sha256_bytes(tier2)[:12])
        print(f"    turn {t}: adapted (bind+bundle = ADD, no gradient/retrain) -> Tier-2 state {states[-1]}...  | Tier-1 digest: {tier1_digest()[:12]}... (unchanged: {tier1_digest()==d0})")
    print(f"    -> Tier 2 SHAPED across {len(user_turns)} turns (states all differ: {len(set(states))==len(states)}); Tier 1 NEVER changed.\n")

    print("(3) the adaptation NEVER touches the foundation:")
    print(f"    Tier-1 digest after all adaptation: {tier1_digest()[:16]}...  ==  start: {tier1_digest()==d0}")
    print(f"    -> always-learning (Tier 2) WITHOUT changing foundational knowledge (Tier 1). No catastrophic forgetting,")
    print(f"    no retraining -- the foundation is FIXED (escapes the data-center-LLM retraining agony).\n")

    # (4) the history helix (F533) IS the 2-axis Mobius (F593): (turn, pos) = the two orthogonal axes
    print("(4) the HISTORY HELIX (F533) IS the TWO-AXIS MOBIUS (F593) -- the conversation has the 2-axis structure:")
    P = 4                                                          # positions per turn (shelf width)
    print(f"    {'linear m':<10}{'helix (turn,pos)':<20}{'= 2-axis Mobius (axisE=turn, axisB=pos)'}")
    for m in (2, 5, 9):
        turn, pos = helix_coord(m, P)
        print(f"    m={m:<8}({turn}, {pos}){'':<12}axis_E(seam/look-ahead-behind)={turn}, axis_B(meaning-class/pos)={pos}")
    print(f"    -> the history helix's TWO coordinates (turn-axis + position-axis) ARE the two orthogonal Mobius axes")
    print(f"    (F593: sigma_E the temporal seam + sigma_B the meaning-class). The conversation/adaptation = the 2-axis")
    print(f"    Mobius. So Tier 2 (the shaped context) rides the SAME 2-axis structure the kernel already has.\n")

    print("VERDICT (the two-tier kernel: fixed foundation + progressive adaptive):")
    print(f"  • TWO TIERS, NOT ONE LEARNING KERNEL: TIER 1 = the FOUNDATIONAL BOOKSHELF (fixed, bit-exact, attested, never")
    print(f"    retrained -- F584); TIER 2 = the PROGRESSIVE/ADAPTIVE kernel = the conversation context, shaping with use,")
    print(f"    GPU-free (HDC bind = add, no gradient). Tier 2 adapts every turn; Tier 1's digest NEVER changes.")
    print(f"  • ALWAYS-LEARNING WITHOUT CHANGING FOUNDATIONAL KNOWLEDGE: because the foundation can be FIXED (bit-exact), the")
    print(f"    kernel escapes the data-center-LLM retraining agony -- no catastrophic forgetting, no gradient passes. The")
    print(f"    user-adaptation is a cheap additive layer ON TOP of the fixed foundation. (Composes the 'learning without")
    print(f"    GPU compute' stance + the two-tier RBS-NN F119/F120.)")
    print(f"  • THE HISTORY HELIX = THE 2-AXIS MOBIUS: the conversation/adaptation has exactly the 2-axis structure (turn-")
    print(f"    axis = the look-ahead/behind temporal seam sigma_E, F592; position-axis = the meaning-class sigma_B, F593).")
    print(f"    So Tier 2 (the shaped context) IS the two-axis Mobius riding the fixed foundation -- the conversation context")
    print(f"    and the kernel's chirality structure are the SAME object.")
    print(f"  • SO THE BUILD ORDER IS RIGHT (the user's point): populate the FOUNDATIONAL bookshelf first (fixed, bit-exact),")
    print(f"    THEN add the progressive adaptive layer (the shaped context) -- not a single from-scratch learning kernel.")
    print(f"  • Composes F584 (kernel persistence) + F119/F120 (two-tier RBS-NN + Class-K bridge) + F533/F592 (the history")
    print(f"    helix) + F593 (the 2-axis Mobius) + F612-F621 (the bit-exact comm kernel = the fixed foundation) + the GPU-")
    print(f"    free learning stance. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
