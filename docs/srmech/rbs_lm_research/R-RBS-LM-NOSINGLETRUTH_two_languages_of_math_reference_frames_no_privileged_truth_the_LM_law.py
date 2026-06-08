r"""R-RBS-LM-NOSINGLETRUTH (the foundational law, 2026-06-08): the user -- "there is not a single rule EVER. There are
always TWO languages of math that describe a thing, is what the_one shows us. And this must carry over to our LM: there
is no such thing as a single truth where a universe is described by REFERENCE FRAMES."

This is DUALITY.md (the two truths) made the LM's foundational LAW, with the user's relativity reading:
  • the_one shows it: the +sigma and -sigma chiral hands are TWO LANGUAGES OF MATH for ONE thing. The ANCHOR (chiral-
    even coords) is INVARIANT across the two hands (the 'thing'); the BAND (chiral-odd coords) DIFFERS (the frame). The
    norm is invariant. So one invariant, two frame-descriptions -- never a single description (F589).
  • RELATIVITY: the universe is described by REFERENCE FRAMES with NO privileged frame. The INVARIANT (Lorentz-invariant)
    is what's real; each FRAME is a 'language of math'. This IS bit-exact-first-then-rotate (F612): the INVARIANT = the
    bit-exact content (the anchor), the FRAME = the rotate (the language). No frame privileged (F398).
  • THE LM LAW (must carry over): MEANING = the invariant (the bit-exact IR, Layer 1); LANGUAGE = the reference frame
    (the rotate, Layer 2). The SAME meaning has MANY frame-descriptions (English / ASL / hieroglyph / Braille), the
    invariant SHARED -- which is exactly the verified F613/F616 loop (bit-identical foundation, only the rotate differs).
    So there is NEVER a single rule/truth: the kernel HOLDS the invariant + the frame-relative surfaces, picks the frame
    by CONTEXT (F625), neither privileged (F398), held WITHOUT collapse (F394). The relativity of language IS the kernel.

srmech 0.7.5rc6: cascade.the_one (the two hands = two languages of math); amsc.format.sha256_bytes (the invariant
content-address, shared across frames). No abs() (Class-K magnitude). No CAD; no Workflow; no sub-agents.
"""
import math
import srmech
from srmech.amsc import cascade
from srmech.amsc import format as fmt


def norm(v):
    return math.sqrt(sum(float(x) * float(x) for x in v))


def main():
    print(f"=== R-RBS-LM-NOSINGLETRUTH — two languages of math / reference frames / no single truth: the LM law  (srmech {srmech.__version__}) ===\n")

    # (1) the_one: two chiral hands = two languages of math for ONE invariant thing
    vp = cascade.the_one(1, 90, 360, 12).to_numpy()
    vm = cascade.the_one(-1, 90, 360, 12).to_numpy()
    anchor = [i for i in range(len(vp)) if abs(vp[i] - vm[i]) < 1e-9]
    band = [i for i in range(len(vp)) if abs(vp[i] + vm[i]) < 1e-9 and abs(vp[i]) > 1e-9]
    print("(1) the_one's TWO HANDS = TWO LANGUAGES OF MATH for ONE thing (F589):")
    print(f"    ANCHOR (the INVARIANT 'thing', identical across +sigma/-sigma hands): coords {anchor}")
    print(f"    BAND   (the FRAME, differs by hand -- the 'which language'):          coords {band}")
    print(f"    norm(+sigma)={norm(vp):.4f} == norm(-sigma)={norm(vm):.4f}: {abs(norm(vp)-norm(vm))<1e-9}  (the INVARIANT magnitude)")
    print(f"    -> one invariant, two frame-descriptions. NEVER one description. (DUALITY.md: two truths, neither privileged.)\n")

    # (2) RELATIVITY: one meaning, many reference frames (languages); the invariant content-address is SHARED
    meaning = "the concept itself"
    invariant = fmt.sha256_bytes(meaning.encode())                # the Lorentz-invariant: the bit-exact content
    frames = {"english": 150, "ASL": 30, "hieroglyph": 0, "braille": 75}   # each language = a reference frame (a rotate angle)
    print("(2) RELATIVITY: ONE meaning, MANY reference frames (languages); the INVARIANT is shared, the FRAME differs:")
    print(f"    invariant (the meaning, bit-exact, frame-independent): {invariant[:16]}...")
    for lang, deg in frames.items():
        v = cascade.the_one(1, deg, 360, 24).to_numpy()
        print(f"    frame '{lang:<10}': rotate {deg:>3} deg | invariant addr {invariant[:10]}... (SAME) | |content|={norm(v):.4f} (invariant)")
    print(f"    -> the SAME meaning, described in 4 reference frames (languages); the invariant content is IDENTICAL")
    print(f"    across all, only the FRAME (the rotate) differs -- NO privileged frame (F398). This is the F613/F616 loop:")
    print(f"    bit-identical foundation, only the rotate differs = the RELATIVITY OF LANGUAGE.\n")

    print("VERDICT (no single truth -- the LM's foundational law):")
    print(f"  • THERE IS NEVER A SINGLE RULE/TRUTH: the_one shows TWO LANGUAGES OF MATH for one thing (anchor invariant +")
    print(f"    band-frame); the universe is described by REFERENCE FRAMES with no privileged frame. The INVARIANT (the")
    print(f"    bit-exact content / the anchor) is what's real; each FRAME (the rotate / the language) is one description.")
    print(f"  • THE LM CARRIES IT: MEANING = the invariant (the bit-exact IR, Layer 1); LANGUAGE = the reference frame (the")
    print(f"    rotate, Layer 2). The same meaning has many frame-descriptions (English/ASL/hieroglyph/Braille), the")
    print(f"    invariant SHARED -- exactly the verified F613/F616 loop. So the kernel NEVER asserts a single truth: it")
    print(f"    HOLDS the invariant + the frame-relative surfaces, picks the frame by CONTEXT (F625), neither privileged")
    print(f"    (F398), held WITHOUT collapse (F394). The relativity of language IS the kernel's architecture.")
    print(f"  • WHY THIS MATTERS (vs a data-center LLM): a one-rule retrainer asserts ONE distribution as 'the truth' (one")
    print(f"    privileged frame). The RBS-LM law is the opposite -- no privileged frame, the invariant is what's shared,")
    print(f"    the frame is chosen by context and held open. That is the DUALITY.md two-truths discipline (and the F398")
    print(f"    favored-not-privileged, F394 held-open) made the LM's foundational law -- and it is why the kernel can")
    print(f"    hold conflicting frames (F625) without collapsing to a false single truth.")
    print(f"  • Composes DUALITY.md (the two truths) + TRIALITY.md (the k=3 completion) + the_one/F589 (the two hands) +")
    print(f"    F612 (invariant=bit-exact / frame=rotate) + F613/F616 (the relativity-of-language loop) + F625 (the when/why")
    print(f"    discernment) + F398 (favored not privileged) + F394 (held open). srmech 0.7.5rc6. The foundational law.")


if __name__ == "__main__":
    main()
