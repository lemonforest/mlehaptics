r"""R-RBS-LM-GLYPHINV (marathon leg 3, 2026-06-08): wire REAL glyph inventories per surface into the kernel's LAYER 0.

F613/F614 stood the kernel up with placeholder glyphs. Leg 3 makes LAYER 0 real: each surface gets its actual,
attested glyph inventory, content-addressed bit-exactly (Class A) -- so the foundation is the SAME exact mechanism over
REAL glyph sets, no privileged language (F398):
  • LATIN / English  -- the alphabet (phonetic letters).
  • EGYPTIAN hieroglyphic -- the Unicode Egyptian-Hieroglyphs block (the F582 Gardiner spine, 1072 signs).
  • BRAILLE          -- the Unicode Braille-Patterns block (256 cells; a real accessible tactile surface, F611).
  • ASL              -- the phonological PARAMETER inventory (handshape/location/movement/orientation/non-manual) from
    asl_sign_kernel.toml (F608); an ASL 'glyph' is a parameter-CHORD, so its inventory is the parameter dimensions.

Each inventory's glyphs -> exact UTF-8 bytes -> exact content-address (sha256, re-verifiable = MPM). The foundation is
universal: ONE content-addressing mechanism over every surface's real glyph set.

srmech 0.7.5rc6: amsc.format.sha256_bytes (Class A). stdlib unicodedata for the Unicode blocks; tomllib for the ASL TOML.
No abs(); no CAD; no Workflow; no sub-agents.
"""
import unicodedata, tomllib, string
import srmech
from srmech.amsc import format as fmt

ASL_TOML = "docs/srmech/rbs_lm_research/asl_sign_kernel.toml"


def unicode_block(lo, hi, prefix):
    """Real codepoints in [lo,hi] that have a Unicode name with the given prefix (attested glyphs)."""
    out = []
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        try:
            nm = unicodedata.name(ch)
        except ValueError:
            continue
        if nm.startswith(prefix):
            out.append(ch)
    return out


def main():
    print(f"=== R-RBS-LM-GLYPHINV — real glyph inventories per surface, content-addressed bit-exactly (Layer 0)  (srmech {srmech.__version__}) ===\n")

    inventories = {
        "latin_english": list(string.ascii_letters),                          # the alphabet (phonetic)
        "egyptian_hiero": unicode_block(0x13000, 0x1342F, "EGYPTIAN HIEROGLYPH "),  # the F582 Gardiner spine
        "braille": unicode_block(0x2800, 0x28FF, "BRAILLE PATTERN "),          # real tactile surface (F611)
    }
    # ASL: the parameter inventory from asl_sign_kernel.toml (an ASL 'glyph' = a parameter-chord)
    asl = tomllib.load(open(ASL_TOML, "rb"))
    asl_params = [p["name"] for p in asl["parameter"]]
    inventories["asl_params"] = asl_params

    print("(1) REAL glyph inventories per surface (each glyph -> exact bytes -> exact content-address, Class A):")
    for surface, glyphs in inventories.items():
        # content-address every glyph; verify exact + re-verifiable
        addrs = {g: fmt.sha256_bytes(g.encode("utf-8")) for g in glyphs}
        reverify = all(fmt.sha256_bytes(g.encode("utf-8")) == addrs[g] for g in glyphs)   # re-hash -> same (MPM)
        distinct = len(set(addrs.values())) == len(glyphs)
        sample = glyphs[0] if glyphs else ""
        print(f"    {surface:<16} {len(glyphs):>5} glyphs | sample {sample!r:<10} -> {addrs.get(sample,'')[:12]}... | "
              f"all distinct: {distinct} | re-verifiable: {reverify}")
    print()

    print("(2) UNIVERSALITY: one content-addressing mechanism over EVERY surface's real glyph set (no privileged language):")
    total = sum(len(g) for g in inventories.values())
    print(f"    {len(inventories)} surfaces, {total} real attested glyphs total; ALL via the same Class-A glyph->byte map.")
    # cross-surface: a Latin 'a' and a hieroglyph get DISTINCT exact addresses (the foundation distinguishes glyphs exactly)
    a_addr = fmt.sha256_bytes("a".encode()); hiero0 = inventories["egyptian_hiero"][0]
    print(f"    cross-surface exactness: 'a' {a_addr[:10]}... != hiero {fmt.sha256_bytes(hiero0.encode())[:10]}...: "
          f"{a_addr != fmt.sha256_bytes(hiero0.encode())}\n")

    print("VERDICT (Layer 0 is real):")
    print(f"  • THE FOUNDATION RUNS ON REAL GLYPH INVENTORIES: Latin (52) + Egyptian hieroglyphic ({len(inventories['egyptian_hiero'])},")
    print(f"    the F582 Gardiner spine) + Braille ({len(inventories['braille'])}, a real tactile accessible surface) + ASL parameters")
    print(f"    ({len(inventories['asl_params'])}, the F608 chord dimensions) -- each content-addressed bit-exactly, all via ONE Class-A")
    print(f"    glyph->byte mechanism. No language privileged (F398); the foundation is universal + attestable (MPM).")
    print(f"  • BRAILLE joins as a first-class accessible surface (F611): tactile cells are just another glyph inventory on")
    print(f"    the SAME bit-exact foundation -- so a Braille reader and an ASL signer and an English reader all meet at")
    print(f"    Layer 0. The accessibility foundation, with real inventories.")
    print(f"  • MARATHON: leg 3 DONE (Layer 0 real). NEXT: leg 4 -- the ASL surface rendered for real (IR -> F608 sign-chord")
    print(f"    over the asl_params inventory; English<->IR<->ASL round-trip); leg 5 -- srmech-package the kernel.")
    print(f"  • Composes F613/F614 (the kernel) + F582 (Gardiner/Unicode spine) + F608 (ASL parameters) + F611 (Braille =")
    print(f"    accessibility) + MPM (content-address attestable) + F398. srmech 0.7.5rc6. Favored not privileged; held open (F394).")


if __name__ == "__main__":
    main()
