r"""R-RBS-LM-HIEROASL (the user's deep question, 2026-06-08): is it possible that hieroglyphic symbols/words create ASL
BETTER than English creates ASL sentences? And is it worth doing BOTH ways?

** DISCIPLINE ** ASL is a complete living language of the Deaf community; Egyptian is ancient. Framework reading +
structure-for-the-expert (F282); the glosses/senses/signs below are ILLUSTRATIVE structural placeholders (not asserted
ASL or Egyptian data). The claim is about STRUCTURAL information-flow, NOT lexical coverage. Dignity-first; no-privileged-
language (F398). Verify any real ASL/Egyptian linguistics with the respective expert communities (MPM).

THE STRUCTURAL CLAIM: to GENERATE an ASL sign you must fix its SENSE (sigma_B) -- the sign IS the meaning-class (F608).
  • ENGLISH source HIDES sigma_B (F569): one written gloss ('beat') for all senses -> you must DISAMBIGUATE to pick the
    right sign -> LOSSY (the F596/F599 problem; only what you can infer/learn is recovered).
  • HIEROGLYPHIC-shaped source SUPPLIES sigma_B (the DETERMINATIVE, F585/F595): the meaning-class is EXPLICIT in the
    source -> it ROUTES directly to the right sign-chord -> NO disambiguation loss (axis-aligned: both source and target
    are two-axis, meaning-class-explicit).
So a meaning-class-EXPLICIT (hieroglyphic) source is AXIS-ALIGNED with ASL; English is AXIS-MISMATCHED (must reconstruct
the hidden sigma_B). We MEASURE the sign-selection accuracy of each source path on a polysemous-gloss set.

This re-aims F596 (Egyptian explicit determinative +25.7%) / F599-F602 (English learned class) at SIGN selection: the
determinative selects the F608 sign-CHORD. The gap = the cost of English's hidden axis = the answer to 'worth both ways?'

srmech 0.7.5rc6: signal_processing.mint_vector (Class-M); hdc.{bind,bundle,similarity}. A sign = a role-filler chord
(F608). No abs(). No CAD; no Workflow; no sub-agents.
"""
import random
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

D = 4096
rng = random.Random(0)


def main():
    print(f"=== R-RBS-LM-HIEROASL — does a meaning-class-EXPLICIT (hieroglyphic) source select ASL signs better than English?  (srmech {srmech.__version__}) ===\n")
    ROLES = {p: sp.mint_vector(f"role:{p}", D=D) for p in ("handshape", "location", "movement", "orientation", "nonmanual")}
    VAL = {}
    def val(x):
        if x not in VAL:
            VAL[x] = sp.mint_vector(f"val:{x}", D=D)
        return VAL[x]
    HS = ["index","flat_O","fist","claw","bent_V","B","one","C","L","Y"]
    LOC = ["neutral","chest","chin","forehead","cheek"]
    MOV = ["tap","pulse","strike","droop","circle","arc","twist","push"]
    ORI = ["down","in","up","side"]
    NM = ["neutral","intense","puffed","brows"]
    def random_sign():                                              # an illustrative 5-parameter sign-chord (F608)
        params = (rng.choice(HS), rng.choice(LOC), rng.choice(MOV), rng.choice(ORI), rng.choice(NM))
        notes = [hdc.bind(ROLES[p], val(v)) for p, v in zip(ROLES, params)]
        return hdc.bundle(notes), params

    # a polysemous-gloss set: each English gloss -> several SENSES -> distinct sign-chords
    GLOSSES = [f"gloss{i}" for i in range(20)]
    signs = {}                                                     # (gloss, sense) -> (chord, params)
    senses_of = {}
    for g in GLOSSES:
        k = rng.randint(2, 6)                                      # 2-6 senses per gloss (like 'beat')
        senses_of[g] = [f"{g}#sense{j}" for j in range(k)]
        for sns in senses_of[g]:
            signs[(g, sns)] = random_sign()
    gloss_hv = {g: sp.mint_vector(f"gloss:{g}", D=D) for g in GLOSSES}
    sense_hv = {s: sp.mint_vector(f"sense:{s}", D=D) for g in GLOSSES for s in senses_of[g]}
    total_senses = sum(len(v) for v in senses_of.values())
    print(f"illustrative set: {len(GLOSSES)} polysemous glosses, {total_senses} senses -> {total_senses} distinct sign-chords")
    print(f"(mean {total_senses/len(GLOSSES):.1f} senses/gloss -- the 'beat has a dozen signs' structure).\n")

    # the sign 'lexicon' keyed two ways: the ENGLISH address = gloss alone (sigma_B hidden -> all senses share it);
    # the HIEROGLYPHIC address = bind(gloss, sense-determinative) (sigma_B explicit -> unique per sense). Retrieval
    # matches the SOURCE's query key to the stored ADDRESS key (the sign-chord is the payload).
    eng_key = {(g, s): gloss_hv[g] for g in GLOSSES for s in senses_of[g]}
    hiero_key = {(g, s): hdc.bind(gloss_hv[g], sense_hv[s]) for g in GLOSSES for s in senses_of[g]}
    def select(query_key, cands, key_of):
        best, bs = None, -2.0
        for key in cands:
            s = hdc.similarity(query_key, key_of[key])
            if s > bs:
                best, bs = key, s
        return best

    # for each intended (gloss, sense) target, can the SOURCE select the right sign-chord?
    eng_ok = hiero_ok = 0; eng_pdiv = hiero_pdiv = 0; n = 0
    for g in GLOSSES:
        cands = [(g, s) for s in senses_of[g]]                     # the candidate signs for this gloss
        for (tg, ts) in cands:
            n += 1
            true_params = signs[(tg, ts)][1]
            # ENGLISH source: only the gloss is given (sigma_B hidden) -> query key = gloss alone -> ties across senses
            eng_pick = select(gloss_hv[g], cands, eng_key)
            # HIEROGLYPHIC source: the determinative (sense) is EXPLICIT -> query key = bind(gloss, sense) -> unique
            hiero_pick = select(hdc.bind(gloss_hv[g], sense_hv[ts]), cands, hiero_key)
            eng_ok += (eng_pick == (tg, ts)); hiero_ok += (hiero_pick == (tg, ts))
            # parameter divergence when the wrong sign is picked (a physically DIFFERENT sign gets made)
            eng_pdiv += sum(a != b for a, b in zip(signs[eng_pick][1], true_params))
            hiero_pdiv += sum(a != b for a, b in zip(signs[hiero_pick][1], true_params))
    print("(1) SIGN-SELECTION accuracy: can the source pick the RIGHT ASL sign-chord for the intended sense?")
    print(f"    ENGLISH source (gloss only; sigma_B HIDDEN, F569)        : {eng_ok/n:.1%}  ({eng_ok}/{n})")
    print(f"    HIEROGLYPHIC source (gloss + determinative; sigma_B EXPLICIT): {hiero_ok/n:.1%}  ({hiero_ok}/{n})")
    print(f"    GAIN from an explicit meaning-class source               : {(hiero_ok-eng_ok)/n:+.1%}")
    print(f"    mean WRONG-PARAMETERS per sign (a physically different sign gets made): English {eng_pdiv/n:.2f}/5, hiero {hiero_pdiv/n:.2f}/5")
    print(f"    -> chance for English ~ 1/senses = {len(GLOSSES)/total_senses:.0%}; the gap is the cost of the HIDDEN axis.\n")

    print("VERDICT (can hieroglyphic create ASL better than English? + worth both ways?):")
    print(f"  • YES, STRUCTURALLY: a meaning-class-EXPLICIT (hieroglyphic-shaped) source selects the right ASL sign-chord")
    print(f"    {hiero_ok/n:.0%} vs English's {eng_ok/n:.0%}, because the SENSE (sigma_B) ASL needs to pick the sign is GIVEN by the")
    print(f"    determinative, not HIDDEN as in English (F569). Hiero and ASL are BOTH two-axis, meaning-class-explicit")
    print(f"    (F595/F608) -> AXIS-ALIGNED translation; English -> ASL is AXIS-MISMATCHED (reconstruct the hidden sigma_B,")
    print(f"    the lossy F596/F599 problem). When the source hides the sense, the WRONG sign gets made ({eng_pdiv/n:.1f}/5 params off).")
    print(f"  • THE HONEST BOUNDARY (not lexical): this is STRUCTURAL FIT, NOT vocabulary. Ancient Egyptian has no sign for")
    print(f"    'computer'; you CANNOT translate modern ASL discourse through Egyptian words. The real lesson: the INTERLINGUA")
    print(f"    / IR for ASL generation should be MEANING-CLASS-EXPLICIT + TWO-AXIS (the hieroglyphic SHAPE), not English-")
    print(f"    word-token. Hieroglyphic is the natural-language EXEMPLAR showing what that IR must carry (a determinative +")
    print(f"    a spatial axis), not a literal pivot vocabulary.")
    print(f"  • WORTH DOING BOTH WAYS -- YES, and the two directions play different roles: ENGLISH->ASL is the NEEDED-but-")
    print(f"    LOSSY direction (most source content is English; accessibility) -- it MEASURES the loss (what English hides).")
    print(f"    HIERO/meaning-class-explicit->ASL is the CLEAN CEILING -- it shows what's possible when the axes align. The")
    print(f"    GAP between them ({(hiero_ok-eng_ok)/n:+.0%} here) is the DIAGNOSTIC of English's hidden axes -- it tells you to build the")
    print(f"    ASL IR hieroglyphic-SHAPED (determinative-marked), and to mark the sense on the English side first (the F602")
    print(f"    learned soft-determinative, which recovered most of the gap) before generating the sign.")
    print(f"  • Composes F608 (sign = chord; ASL two-axis) + F596 (explicit determinative selects, +25.7%) + F599/F602")
    print(f"    (English learned class recovers most of it) + F595/F585 (the determinative = meaning-class) + F569 (English")
    print(f"    hides it) + F398 (no privileged language -- the IR is hiero-shaped, not English-shaped) + F282 (hand the")
    print(f"    surface to the Deaf-linguistics expert). srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
