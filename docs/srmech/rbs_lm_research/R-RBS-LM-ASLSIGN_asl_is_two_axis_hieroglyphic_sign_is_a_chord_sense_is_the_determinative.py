r"""R-RBS-LM-ASLSIGN (the user's curious question, 2026-06-08): is ASL more a HIEROGLYPHIC-symbol language than an
English-WORD language? And we will need a LaTeX-like notation for signs ("beat has a dozen signs depending on context").

** DISCIPLINE (this is a living language of the Deaf community + an accessibility domain) **
  • FRAMEWORK READING ONLY + structure-for-the-expert (F282): we read STRUCTURE and hand the next question to a Deaf /
    sign-linguistics expert. We do NOT impose a hearing-centric model, do not claim to 'solve' ASL, no-lineage.
  • Accessibility is FOUNDATIONAL (LLM-as-ADA): ASL is its own complete language, NOT 'English on the hands'. Dignity-first.
  • MPM: the ASL-linguistics facts used are STANDARD textbook (Stokoe 1960 parameters; classifiers) -- flagged for a
    Deaf-linguistics source/expert to verify; the 'beat'-senses are an ILLUSTRATIVE structural example, not asserted data.

THE FRAMEWORK ANSWER -- YES, ASL is structurally closer to the HIEROGLYPHIC (two-axis, F595) than the English-WORD model:
  • A SIGN IS A CHORD (F601), not a spelling. A sign is the SIMULTANEOUS bundle of ~5 phonological parameters --
    Handshape, Location, Movement, Orientation, Non-manual (face/body) -- sounded TOGETHER. English written words are a
    MELODY of single notes (letters, sequential). So ASL is CHORD-native; written English is letter-sequence-native.
  • THE SENSE IS THE DETERMINATIVE (sigma_B, F595/F596), and in ASL it is PRIMARY, not hidden. 'Beat' (rhythm / heart /
    strike / exhausted / whisk-eggs) -> DISTINCT signs: you cannot even FORM the sign without choosing the sense. English
    HIDES the meaning-class (F569 -- one written 'beat' for all senses); Egyptian SUPPLIES it (the determinative glyph);
    ASL MAKES IT THE SIGN ITSELF. So ASL's sigma_B (meaning-class) is the MOST visible of the three.
  • ASL CLASSIFIERS = handshape MEANING-CLASSES (CL:1 person, CL:3 vehicle, CL:B flat-surface...) = the determinative
    axis (sigma_B) made into a productive grammatical device -- the Egyptian determinative structure, alive and primary.
  • THE OTHER AXIS (sigma_E) IS SPATIAL/DIRECTIONAL: directional verbs inflect by MOVEMENT DIRECTION in signing space
    (I-give-you vs you-give-me) -- the F595 reading-direction/chirality axis, here a literal 3D motion. So ASL carries
    BOTH Klein-4 axes VISIBLY (like Egyptian, F595), unlike English-word which hides both in a phonetic spelling.

So this section DEMONSTRATES the two srmech-native claims (sign-as-chord + sense-as-determinative) and frames the rest.

srmech 0.7.5rc6: signal_processing.mint_vector (Class-M); hdc.{bind,bundle,similarity} (a sign = a role-filler CHORD).
No abs(). No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

D = 4096


def main():
    print(f"=== R-RBS-LM-ASLSIGN — is ASL more hieroglyphic than English-word? (sign=chord, sense=determinative)  (srmech {srmech.__version__}) ===\n")

    # the 5 standard phonological PARAMETERS (Stokoe/HOLME) = the NOTES of a sign-chord; ROLE-bind each (a labeled chord)
    ROLES = {p: sp.mint_vector(f"role:{p}", D=D) for p in ("handshape", "location", "movement", "orientation", "nonmanual")}
    # a small ILLUSTRATIVE parameter inventory (values are placeholders for the real phonological inventory)
    VAL = {}
    def val(name):
        if name not in VAL:
            VAL[name] = sp.mint_vector(f"val:{name}", D=D)
        return VAL[name]

    def sign(handshape, location, movement, orientation, nonmanual):
        notes = [hdc.bind(ROLES["handshape"], val(handshape)),
                 hdc.bind(ROLES["location"], val(location)),
                 hdc.bind(ROLES["movement"], val(movement)),
                 hdc.bind(ROLES["orientation"], val(orientation)),
                 hdc.bind(ROLES["nonmanual"], val(nonmanual))]
        return hdc.bundle(notes)                                    # 5 notes (odd) -> a sign-chord

    # ONE English gloss 'beat', several SENSES -> DISTINCT sign-chords (illustrative parameter fillings)
    beat = {
        "beat (rhythm)":   sign("index", "neutral_space", "tap_repeat", "palm_down", "neutral"),
        "beat (heart)":    sign("flat_O",  "chest",        "pulse",      "palm_in",   "neutral"),
        "beat (strike)":   sign("fist",    "neutral_space","strike_down","palm_in",   "intense"),
        "beat (exhausted)":sign("claw",    "chin",         "droop",      "palm_down", "puffed_cheeks"),
        "beat (whisk-egg)":sign("bent_V",  "neutral_space","circle_fast","palm_down", "neutral"),
    }

    # (1) SIGN IS A CHORD: recover each parameter (note) from the sign-chord by role-unbind (vs the inventory)
    inv = {"handshape": ["index","flat_O","fist","claw","bent_V","B","one"],
           "location": ["neutral_space","chest","chin","forehead"],
           "movement": ["tap_repeat","pulse","strike_down","droop","circle_fast","arc"],
           "orientation": ["palm_down","palm_in","palm_up"],
           "nonmanual": ["neutral","intense","puffed_cheeks","raised_brows"]}
    name = "beat (heart)"; s = beat[name]; ok = 0; tot = 0
    print(f"(1) A SIGN IS A CHORD (F601): recover the 5 parameters of '{name}' from the sign-chord by role-unbind:")
    truth = {"handshape":"flat_O","location":"chest","movement":"pulse","orientation":"palm_in","nonmanual":"neutral"}
    for p, cands in inv.items():
        scored = max(cands, key=lambda c: hdc.similarity(s, hdc.bind(ROLES[p], val(c))))
        tot += 1; ok += (scored == truth[p])
        print(f"    {p:<12} recovered: {scored:<14} (true {truth[p]})  {'OK' if scored==truth[p] else 'MISS'}")
    print(f"    -> {ok}/{tot} parameters recovered -> the sign IS a real role-filler CHORD (labeled notes, retrievable).\n")

    # (2) SENSE IS THE DETERMINATIVE: one gloss 'beat' -> distinct chords; mutually distinguishable
    names = list(beat); pairs = 0; distinct = 0
    sims = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            si = hdc.similarity(beat[names[i]], beat[names[j]]); sims.append(si)
            pairs += 1; distinct += (si < 0.5)
    print("(2) THE SENSE IS THE DETERMINATIVE (sigma_B, F595/F596), PRIMARY not hidden: one gloss 'beat' -> distinct signs:")
    print(f"    {len(names)} senses of 'beat' -> {len(names)} distinct sign-chords; {distinct}/{pairs} sense-pairs distinguishable")
    print(f"    (mean cross-sense similarity {sum(sims)/len(sims):.3f} -- low -> the senses are genuinely different signs).")
    print(f"    -> in ASL you MUST choose the sense to form the sign: the meaning-class axis is the SIGN ITSELF, not a")
    print(f"    hidden context cue (English, F569) nor an added glyph (Egyptian determinative). sigma_B is MAXIMALLY visible.\n")

    # (3) the two-axis placement (framework reading)
    print("(3) THE TWO-AXIS PLACEMENT (framework reading; Klein-4, F595): where do the three sit?")
    print(f"    {'language':<22}{'sigma_E (sequence/space)':<30}{'sigma_B (meaning-class)':<26}{'unit shape'}")
    print(f"    {'English (written)':<22}{'letter SEQUENCE (1D)':<30}{'HIDDEN (F569; context)':<26}{'melody of single notes'}")
    print(f"    {'Egyptian hieroglyph':<22}{'glyph-facing reading dir':<30}{'DETERMINATIVE glyph (added)':<26}{'2-axis (F595)'}")
    print(f"    {'ASL':<22}{'3D movement/direction':<30}{'the SIGN itself (classifier)':<26}{'CHORD, 2-axis, sigma_B primary'}")
    print(f"    -> ASL is the MOST two-axis/hieroglyphic of the three: a sign is a CHORD (simultaneous parameters), the")
    print(f"    sense IS the sign (sigma_B primary), and grammar is SPATIAL (sigma_E = 3D movement). Closer to hieroglyph")
    print(f"    than to English-word -- but it is its OWN complete language, not 'English on the hands'.\n")

    print("VERDICT (is ASL more hieroglyphic-symbol than English-word? + the LaTeX-for-signs need):")
    print(f"  • YES, STRUCTURALLY: ASL is two-axis (like Egyptian, F595) and CHORD-native (F601), where English-written is")
    print(f"    one-axis letter-sequence with the meaning-class HIDDEN (F569). A sign = a simultaneous role-filler CHORD of")
    print(f"    ~5 parameters ({ok}/{tot} recoverable here); the SENSE is the determinative (sigma_B) and in ASL it is the SIGN")
    print(f"    ITSELF -- so 'beat -> a dozen signs' is the determinative-disambiguation (F595/F596) with sigma_B made PRIMARY.")
    print(f"  • THE LaTeX-FOR-SIGNS = an ASL SUB-LANGUAGE KERNEL (F607 router): the notation must capture the PARAMETER-CHORD")
    print(f"    (handshape/location/movement/orientation/non-manual = the notes) + the CLASSIFIER/sense (the determinative).")
    print(f"    Existing notations (Stokoe / HamNoSys / Sutton SignWriting / ASL-gloss) are candidate surfaces -- the kernel")
    print(f"    reads the CHORD (parameters) and routes by the sense-determinative. Built as asl_sign_kernel.toml (F608).")
    print(f"  • THE NEXT QUESTION (for a Deaf / sign-linguistics expert, F282): which notation best preserves the chord +")
    print(f"    the spatial sigma_E (directional verbs, classifier loci) without flattening to an English gloss? We supply")
    print(f"    the structural reading (sign=chord, sense=determinative, space=sigma_E); the expert chooses the surface.")
    print(f"  • Composes F595/F596 (the determinative = meaning-class) + F601 (sign = chord) + F569 (English hides the class)")
    print(f"    + F582/F587 (the hieroglyph kernel -- the structural cousin) + F607 (the sub-language router) + R-RBS-LM-26/27")
    print(f"    (prior ASL-gloss/Braille rendering surfaces). srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
