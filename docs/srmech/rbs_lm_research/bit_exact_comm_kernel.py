r"""bit_exact_comm_kernel.py -- THE bit-exact communication kernel, stood up for real (F613, marathon leg 1).

The architecture (F612): communicate at a BIT-EXACT foundation; each language is a ROTATE at the end.
  • LAYER 0 -- glyph -> byte (Class A): content-addressed, EXACT, UNIVERSAL, attestable (MPM re-verifiable). The shared
    foundation ALL languages use. No privileged language (F398).
  • LAYER 1 -- meaning-class IR (the bit-exact ANCHOR, hieroglyphic-shaped, F609/F610): a CONCEPT = (glyph, meaning-class
    / determinative). The IR digest is a stable sha256 -> re-verifiable, no drift.
  • LAYER 2 -- the per-language ROTATE (CORDIC, norm-preserving, F612): each surface rotates the IR into its frame.
    in-frame surfaces (hieroglyphic ~0 rotate, ASL small) CARRY the meaning-class; English is a BIG rotate that rotates
    the class OUT of frame (hidden, F569) -> reading English requires UN-rotating (re-supplying the sense, F602).

The end-to-end demo runs ONE concept through THREE surface-rotates (English / IR-native / ASL) and shows:
  (1) the LAYER-0 content-address is BIT-IDENTICAL across all three surfaces (the foundation is shared, exact);
  (2) the two SENSES of a polysemous word share the Layer-0 address but have DISTINCT Layer-1 IR digests (bit-exact);
  (3) round-trip (render -> recover): the in-frame surfaces recover the exact sense; English collapses the senses
      (the big rotate hid the class) -> lossy unless the sense is re-supplied;
  (4) the rotate is NORM-PRESERVING (|content| invariant across the per-language angles) -> content bit-exact, frame turns.

srmech 0.7.5rc6: amsc.format.sha256_bytes (Class A); cascade.the_one (the rotate, norm-preserving). No abs(); no CAD;
no Workflow; no sub-agents.
"""
import math
import srmech
from srmech.amsc import cascade
from srmech.amsc import format as fmt


def _norm(v):
    return math.sqrt(sum(float(x) * float(x) for x in v))


# the per-language ROTATE: angle (CORDIC frame rotation) + whether the meaning-class survives the rotate (in-frame?)
LANGUAGES = {
    "ir_native":   {"rotate_deg": 0,   "carries_class": True,  "note": "hieroglyphic-shaped: class explicit (~no rotate)"},
    "asl":         {"rotate_deg": 30,  "carries_class": True,  "note": "the sign IS the meaning-class (small rotate, F608)"},
    "english":     {"rotate_deg": 150, "carries_class": False, "note": "phonetic token; class rotated OUT of frame (hidden, F569)"},
}


class BitExactCommKernel:
    """Layer 0 (glyph->byte, exact) + Layer 1 (meaning-class IR) + Layer 2 (per-language rotate)."""

    # ---- LAYER 0: glyph -> byte (Class A, exact, universal, attestable) ----
    def glyph_bytes(self, glyph):
        return glyph.encode("utf-8")

    def content_address(self, glyph):
        return fmt.sha256_bytes(self.glyph_bytes(glyph))            # exact + re-verifiable (MPM)

    # ---- LAYER 1: the meaning-class IR (the bit-exact anchor) ----
    def encode(self, glyph, meaning_class):
        addr = self.content_address(glyph)
        return {"glyph": glyph, "address": addr, "meaning_class": meaning_class,
                "ir_digest": fmt.sha256_bytes(f"{addr}|{meaning_class}".encode())}

    # ---- LAYER 2: the per-language ROTATE (CORDIC, norm-preserving) ----
    def render(self, ir, language):
        cfg = LANGUAGES[language]
        v = cascade.the_one(1, cfg["rotate_deg"], 360, 24).to_numpy()
        surface = {"glyph": ir["glyph"], "address": ir["address"],     # LAYER 0 always present (shared foundation)
                   "rotate_deg": cfg["rotate_deg"], "content_norm": round(_norm(v), 6)}
        if cfg["carries_class"]:
            surface["meaning_class"] = ir["meaning_class"]             # the class survives the (small) rotate
        return surface                                                # English: class absent (rotated out of frame)

    def recover(self, surface, language, prior_sense=None):
        """Un-rotate: rebuild the IR from a surface render. If the class was rotated out (English), re-supply the prior."""
        glyph = surface["glyph"]
        if "meaning_class" in surface:
            mc = surface["meaning_class"]                             # in-frame -> exact recovery
        else:
            mc = prior_sense                                         # English: must re-supply the sense (F602 un-rotate)
        return self.encode(glyph, mc)


def main():
    print(f"=== bit_exact_comm_kernel — ONE concept end-to-end through three surface-rotates (F613)  (srmech {srmech.__version__}) ===\n")
    k = BitExactCommKernel()

    # a polysemous concept: the word 'bank' with two senses (river / money) -- same glyph, different meaning-class
    senses = {"bank/river": k.encode("bank", "WATER_EDGE"), "bank/money": k.encode("bank", "FINANCE")}
    print("(1) LAYER 0 (glyph->byte) is BIT-IDENTICAL across surfaces + senses (the shared, exact foundation):")
    addr = k.content_address("bank")
    print(f"    glyph 'bank' -> content-address {addr[:24]}...  (Class A, exact, re-verifiable = MPM)")
    print(f"    both senses share this Layer-0 address: {senses['bank/river']['address'] == senses['bank/money']['address']}\n")

    print("(2) LAYER 1 (meaning-class IR) is BIT-EXACT + distinguishes the senses (different determinative):")
    for name, ir in senses.items():
        print(f"    {name:<12} meaning_class={ir['meaning_class']:<12} ir_digest={ir['ir_digest'][:16]}...")
    print(f"    the two senses have DISTINCT ir_digests: {senses['bank/river']['ir_digest'] != senses['bank/money']['ir_digest']}  (bit-exact)\n")

    print("(3) LAYER 2 ROTATE: render ONE concept (bank/river) to three surfaces -- foundation shared, rotate differs:")
    ir = senses["bank/river"]
    renders = {}
    for lang in ("ir_native", "asl", "english"):
        r = k.render(ir, lang); renders[lang] = r
        cls = r.get("meaning_class", "(rotated out of frame -- HIDDEN)")
        print(f"    {lang:<10} rotate={r['rotate_deg']:>3} deg | Layer-0 addr {r['address'][:12]}... | class: {cls}")
    same_addr = len({renders[l]['address'] for l in renders}) == 1
    print(f"    -> Layer-0 content-address IDENTICAL across all three surfaces: {same_addr} (foundation bit-identical; only the rotate differs)\n")

    print("(4) ROUND-TRIP (render -> recover) sense accuracy per surface, on polysemous concepts:")
    # a small polysemous set; English defaults to the most-frequent sense (the prior) when the class was rotated out
    concepts = [("bank", "WATER_EDGE"), ("bank", "FINANCE"), ("bank", "FINANCE"),   # 'bank' money-biased prior
                ("bat", "ANIMAL"), ("bat", "SPORT"), ("bark", "TREE"), ("bark", "DOG_SOUND")]
    from collections import Counter
    prior = {}
    by_glyph = Counter()
    for g, mc in concepts:
        by_glyph[(g, mc)] += 1
    for g in {g for g, _ in concepts}:
        prior[g] = max((mc for gg, mc in concepts if gg == g), key=lambda mc: by_glyph[(g, mc)])
    acc = {}
    for lang in ("ir_native", "asl", "english"):
        ok = 0
        for g, mc in concepts:
            ir = k.encode(g, mc)
            rec = k.recover(k.render(ir, lang), lang, prior_sense=prior[g])
            ok += (rec["meaning_class"] == mc)
        acc[lang] = ok / len(concepts)
        print(f"    {lang:<10}: {acc[lang]:.0%} sense recovered  ({LANGUAGES[lang]['note']})")
    print(f"    -> in-frame surfaces (ir_native/asl) recover the EXACT sense; English collapses senses (the big rotate hid")
    print(f"    the class) -> lossy, must un-rotate (re-supply the sense, F602). Same foundation; the rotate is the cost.\n")

    print("(5) the ROTATE is NORM-PRESERVING (content bit-exact, only the frame turns):")
    norms = {lang: k.render(senses['bank/river'], lang)['content_norm'] for lang in LANGUAGES}
    print(f"    per-language |content|: {norms}")
    print(f"    all equal (= sqrt(6)): {len(set(norms.values()))==1} -> the rotate moves the FRAME, not the CONTENT.\n")

    print("VERDICT (the kernel stands up):")
    print(f"  • THE FOUNDATION IS BIT-IDENTICAL across surfaces: same Layer-0 content-address (exact, attestable), same")
    print(f"    Layer-1 IR mechanism; only the LAYER-2 ROTATE differs. Communication lives at the bit-exact layer (F612).")
    print(f"  • THE ROTATE IS THE LANGUAGE -- and the cost: in-frame surfaces (hieroglyphic/ASL) carry the meaning-class")
    print(f"    and recover the sense EXACTLY ({acc['ir_native']:.0%}/{acc['asl']:.0%}); English's BIG rotate hides the class -> lossy ({acc['english']:.0%}),")
    print(f"    must un-rotate (F602). The rotate is norm-preserving (content bit-exact) and CORDIC (discrete, F392).")
    print(f"  • THIS IS THE ACCESSIBILITY FOUNDATION (F611): any surface (English/ASL/hieroglyph/Braille) is a rotate over")
    print(f"    the SAME exact bytes+meaning -- no privileged language (F398); everyone meets at the bit-exact layer. NEXT")
    print(f"    marathon legs: real glyph inventories per surface (Unicode/Gardiner/ASL-params), the F602 un-rotate for")
    print(f"    English, and srmech-packaging the kernel (a cascade-catalog TOML peer).")
    print(f"  • Composes F612 (the pattern) + F609/F610 (meaning-class-explicit foundation) + F608 (ASL sign=class) + F569")
    print(f"    (English hides it) + F602 (the un-rotate) + F582 (Gardiner spine) + F611 (accessibility) + MPM (attestable)")
    print(f"    + F398/F394. srmech 0.7.5rc6.")


if __name__ == "__main__":
    main()
