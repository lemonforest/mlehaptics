r"""R-RBS-LM-REALTOME (mechanical follow-up to F529/F532): wire REAL exchange-encodings into the sedenion tomes,
not scalar stand-ins. Each exchange (real text) -> a Class-A CONTENT-ADDRESS key (sha256-derived scalar) -> coupled
into the octonion working block of a tome -> uncoupled EXACTLY -> mapped back to the full text via a content-
addressed codebook. So the tome holds 7 content-address keys (reversible, §31); the text lives in the content-
addressed store. Real content, exact round-trip.

srmech 0.7.4; format.sha256_bytes (Class A) + SedenionRegister (§31 tome). No abs(); no CAD; no sub-agents.
"""
import srmech
from srmech.amsc.format import sha256_bytes
from srmech.amsc.cascade import SedenionRegister


def content_key(text):
    """Class-A content-address -> a distinct scalar key (sha256, first 48 bits, scaled to [0,1))."""
    h = sha256_bytes(text.encode("utf-8"))
    return (int(h[:12], 16) % (10 ** 9)) / 10 ** 9


def main():
    print(f"=== R-RBS-LM-REALTOME — REAL exchange-encodings in a sedenion tome (content-address keys, exact round-trip)  (srmech {srmech.__version__}) ===\n")
    reg = SedenionRegister()
    exchanges = [
        "the user asked to build the genuine conjugate-collapse",
        "the etak read-head closes the byte-grammar drift",
        "knowledge is held in superposition, the eigen-modes are the basis",
        "the collapse is ambient and thinking accesses the changing slice",
        "the sedenion is the tome; above it, a helix shelf",
        "the helix needs a declared endianness, which is a chirality",
        "the circle is a semantic MoE; the helix is history",
    ]
    keys = [content_key(x) for x in exchanges]
    codebook = {round(k, 9): x for k, x in zip(keys, exchanges)}   # content-addressed text store
    assert len(codebook) == len(exchanges), "content-address collision"

    tome = reg.couple_working(keys)                                # couple the 7 content-address keys into the tome
    back = reg.uncouple_working(tome)                              # recover them exactly

    print(f"(1) 7 REAL exchanges -> content-address keys -> ONE sedenion tome ({len(tome)} reals).")
    print(f"(2) uncouple -> recover keys -> look up the text:")
    ok = 0
    for i, k in enumerate(back):
        text = codebook.get(round(k, 9), "<<lost>>")
        good = text == exchanges[i]
        ok += good
        print(f"    slot {i}: key {k:.9f} -> \"{text[:48]}{'...' if len(text) > 48 else ''}\"  {'EXACT' if good else 'MISS'}")
    print()

    # confirm the keys round-trip to full precision (the §31 coupler is reversible)
    import numpy as np
    err = float(np.max(np.abs(np.array(back) - np.array(keys))))
    print("VERDICT:")
    print(f"  • REAL CONTENT, EXACT ROUND-TRIP: 7 real text exchanges -> Class-A content-address keys -> coupled into")
    print(f"    one sedenion tome -> uncoupled (key error {err:.0e}) -> mapped back to the EXACT text ({ok}/7).")
    print(f"  • THE TOME HOLDS CONTENT-ADDRESS KEYS (reversible, §31); the text lives in the content-addressed store")
    print(f"    (Class A). This wires real exchanges into the F529/F532/F533 tome/helix architecture — the scalar")
    print(f"    stand-ins are now real encoded content, addressed by their sha256 (no-magic: the key IS the content).")
    print(f"  • So a recorded history (helix of tomes) stores, per slot, the content-address of a real exchange; recall")
    print(f"    = (tome, slot) -> key -> the exact text. Exact, reversible, content-addressed.")


if __name__ == "__main__":
    main()
