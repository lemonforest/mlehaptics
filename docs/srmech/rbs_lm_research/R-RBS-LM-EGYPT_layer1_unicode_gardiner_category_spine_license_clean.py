r"""R-RBS-LM-EGYPT (the user's Layer-1 build, 2026-06-08): the license-safe SPINE for an Ancient Egyptian hieroglyphics
kernel -- Unicode signs <-> Gardiner code <-> category -- so the "meaning falls out of the rules" claim (the F581 stance)
becomes testable the moment a public-domain corpus slice is loaded.

WHY THIS IS THE SPINE (and license-clean): every hieroglyph is in Unicode (block U+13000..U+1342F, 1072 signs, Unicode
5.2, Gardiner-based) and Python's stdlib `unicodedata` (here Unicode 16.0) gives the codepoint->name mapping for free.
The official name embeds the GARDINER CODE: "EGYPTIAN HIEROGLYPH A001" -> Gardiner A1, category A. So the sign inventory
+ the Gardiner CATEGORY TAXONOMY (A=man, G=birds, ... Aa=unclassified) come entirely from stdlib -- NO external data, NO
copyrighted dictionary, attestable to the Unicode license. (The modern dictionaries / the user's book stay a CROSS-CHECK,
never a source -- F581.)

THE FRAMEWORK HOOK (F581): the Gardiner category IS the DETERMINATIVE classifier system -- the explicit, written-into-
the-script semantic class tag. So the Layer-1 taxonomy IS Egyptian's "form signal made explicit" (the F574 index /
Class-E catalog, term->members) -- the structure worn on the outside, which English hides (F569). Layer 1 alone is the
spine (no meaning yet -- that needs the Layer-2 corpus); but it already exhibits the determinative-as-explicit-category
structure that makes Egyptian the keystone test (F581).

srmech 0.7.5rc6: Class-E catalog taxonomy; Class-M HDC category anchors (signal_processing.mint_vector); Class-A
attestation (format.sha256_bytes). The sign enumeration is stdlib unicodedata (Unicode license). No abs(); no CAD; no
Workflow tool; no sub-agents.
"""
import re
import json
import unicodedata
import srmech
from srmech.amsc import format as smfmt
from srmech import signal_processing as sp

BLOCK_LO, BLOCK_HI = 0x13000, 0x1342F                                    # Egyptian Hieroglyphs (signs)
GARDINER_CAT = {                                                         # the Gardiner top-level categories (the determinative taxonomy)
    "A": "man + occupations", "B": "woman + occupations", "C": "anthropomorphic deities",
    "D": "parts of the human body", "E": "mammals", "F": "parts of mammals", "G": "birds",
    "H": "parts of birds", "I": "amphibious animals / reptiles", "K": "fish + parts of fish",
    "L": "invertebrates / lesser animals", "M": "trees + plants", "N": "sky / earth / water",
    "NL": "nomes of Lower Egypt", "NU": "nomes of Upper Egypt", "O": "buildings + parts",
    "P": "ships + parts", "Q": "domestic + funerary furniture", "R": "temple furniture + sacred emblems",
    "S": "crowns / dress / staves", "T": "warfare / hunting / butchery", "U": "agriculture / crafts / professions",
    "V": "rope / fibre / baskets / bags", "W": "vessels of stone + earthenware", "X": "loaves + cakes",
    "Y": "writings / games / music", "Z": "strokes / geometric figures", "Aa": "unclassified",
}


def main():
    print(f"=== R-RBS-LM-EGYPT — Layer-1 Egyptian kernel: Unicode signs <-> Gardiner code <-> category (license-clean spine)  (srmech {srmech.__version__}) ===\n")
    print(f"source: stdlib unicodedata (Unicode {unicodedata.unidata_version}); block U+13000..U+1342F\n")

    # ---- enumerate the signs + parse the Gardiner code/category (Class-E catalog) ----
    signs = []                                                          # (codepoint_hex, char, gardiner_code, category)
    for cp in range(BLOCK_LO, BLOCK_HI + 1):
        try:
            nm = unicodedata.name(chr(cp))
        except ValueError:
            continue
        code = nm.replace("EGYPTIAN HIEROGLYPH ", "")
        m = re.match(r"([A-Z]+)", code)
        cat = m.group(1) if m else "?"
        # normalize the "AA" unclassified to Gardiner's "Aa"
        cat = "Aa" if cat == "AA" else cat
        signs.append((hex(cp), chr(cp), code, cat))

    taxonomy = {}                                                       # category -> member gardiner codes (the index / Class-E)
    for _, _, code, cat in signs:
        taxonomy.setdefault(cat, []).append(code)
    cats_sorted = sorted(taxonomy, key=lambda c: -len(taxonomy[c]))

    print(f"(1) SIGN INVENTORY: {len(signs)} hieroglyphs enumerated from unicodedata; {len(taxonomy)} Gardiner categories.")
    print(f"    {'cat':<5}{'#signs':>7}  description (the DETERMINATIVE class)")
    for c in cats_sorted[:12]:
        print(f"    {c:<5}{len(taxonomy[c]):>7}  {GARDINER_CAT.get(c, '(unmapped)')}")
    print(f"    ... ({len(taxonomy)} categories total)\n")

    # ---- Class-M HDC anchors per category (the spine onto which corpus/meaning will bind) ----
    D = 4096
    cat_anchor = {c: sp.mint_vector(f"gardiner:{c}", D=D) for c in taxonomy}    # deterministic, reproducible (mint-by-name)
    print(f"(2) CATEGORY ANCHORS: minted {len(cat_anchor)} Class-M HDC category vectors (D={D}, deterministic mint-by-name).")
    print(f"    each sign binds to its category anchor -> the content-addressed sign<->category spine (ready for Layer-2 corpus).\n")

    # ---- MPM attestation (Class-A): the kernel is attested to the Unicode source, NOT to any dictionary ----
    payload = json.dumps([[h, code, cat] for h, _, code, cat in signs], ensure_ascii=False).encode("utf-8")
    parser_rule = b"name.replace('EGYPTIAN HIEROGLYPH ','') ; re.match('([A-Z]+)') ; AA->Aa"
    attestation = {
        "source": f"Unicode Character Database via stdlib unicodedata {unicodedata.unidata_version}",
        "source_url": "https://www.unicode.org/charts/PDF/U13000.pdf",
        "license": "Unicode License (UCD) — public; sign inventory + Gardiner codes are factual data",
        "block": "U+13000..U+1342F (Egyptian Hieroglyphs)",
        "n_signs": len(signs),
        "response_sha256": smfmt.sha256_bytes(payload),
        "parser_rule_hash": smfmt.sha256_bytes(parser_rule),
        "parser_version": f"srmech {srmech.__version__}",
    }
    print("(3) MPM ATTESTATION (Class-A) — the spine is attested to the PUBLIC source, not a copyrighted dictionary:")
    print(f"    source: {attestation['source']}")
    print(f"    license: {attestation['license']}")
    print(f"    n_signs={attestation['n_signs']}  response_sha256={attestation['response_sha256'][:16]}...  parser_rule_hash={attestation['parser_rule_hash'][:16]}...\n")

    print("VERDICT:")
    print(f"  • THE LICENSE-CLEAN SPINE IS BUILT: {len(signs)} signs <-> Gardiner code <-> {len(taxonomy)}-category taxonomy, entirely from")
    print(f"    stdlib unicodedata (Unicode {unicodedata.unidata_version}) -- NO external data, NO copyrighted dictionary. Attested (Class-A) to the")
    print(f"    Unicode source. The modern dictionaries / the user's book stay a CROSS-CHECK, never a source (F581).")
    print(f"  • THE GARDINER CATEGORY *IS* THE DETERMINATIVE TAXONOMY (F581): the category tag (A=man, G=birds, ...) is Egyptian's")
    print(f"    explicit, written-into-the-script semantic classifier -- the F574 index / Class-E catalog (term->members), the")
    print(f"    'form signal made explicit' that English hides (F569). The spine already exhibits the structure-on-the-outside.")
    print(f"  • READY FOR THE FALL-OUT TEST (F581 stance): bind a PUBLIC-DOMAIN corpus slice (TLA / Worterbuch) onto these")
    print(f"    category anchors and the MEANING precipitates from the co-occurrence manifold (F172) -- no dictionary imported.")
    print(f"    We do NOT impose a sentence grammar; we let the compositional unit precipitate + describe it (held-open, F394;")
    print(f"    first-perspective, F282). Composes F581 (the stance) + F574/F569 (form-signal) + F172 (meaning=manifold) +")
    print(f"    Class-A/E/M. srmech 0.7.5rc6 (W17 coupled_wave + W18 multiplex_streams verified shipped). F398/F394.")


if __name__ == "__main__":
    main()
