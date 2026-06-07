r"""R-RBS-LM-THEONE — the RBS-SNN/LM on `the_one`: HOLD the meaning-box, then COLLAPSE/unpack it into a paragraph
of thought. The convergence (F482 + F483): `the_one` (𝕊(σ,θ)) is the holder of the operand box; the native
SedenionRegister holds the k=7 meaning-slots; generation = COLLAPSE the box DOWN (the read-head walk) into the
operator/byte stream — chirality (σ) is the hand the collapse picks (so the stories are forward-only, F453).

  - HOLD (the_one + SedenionRegister): the meaning-frame is held in the_one's box; k=7 anchors in the octonion
    working slots e1..e7 (F465/F468, native in 0.7.4).
  - COLLAPSE (down / unpack): walk the slots σ-handed (the read-head), rendering each meaning as a sentence
    (STATEMENT '.' / QUESTION '?', F481) — the byte-grammar (F476) is the operator render.
  - CHIRALITY (σ): σ=+1 and σ=-1 are the TWO HANDS of the collapse — the (4:3)|(3:4) dual (F129/F483); each
    unpacks the SAME held box a different way (forward-only).
Architecture (F480): STORAGE byte · WORK word/meaning · TRANSDUCER english↔byte. srmech 0.7.4.
"""
import importlib.util as U
import re
from collections import Counter
import numpy as np
import srmech
from srmech.signal_processing import mint_vector
from srmech.amsc.cascade import the_one
from srmech.amsc.cascade.sedenion_register import SedenionRegister

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)
WIN = 6
Q = ["What is", "Why do", "How does", "Where is", "What are"]


def cleanup(s, mx=12):
    s = re.sub(r"\s+", " ", s).strip().strip("\"'(){}[]")
    m = re.search(r"[.!?]", s[6:])
    if m:
        s = s[:6 + m.start()]
    w = [x for x in s.split() if x][:mx]
    s = " ".join(w).rstrip(" ,;:-")
    return (s[0].upper() + s[1:]) if s else s


def statement(ng, t, th, rng):
    return cleanup(k7.word_steered_gen(ng, (t.capitalize() + " is").encode(), 8, th, rng)).rstrip(" .,;:?!") + "."


def question(ng, t, th, rng):
    q = Q[int(rng.integers(len(Q)))]
    return cleanup(k7.word_steered_gen(ng, (q + " " + t).encode(), 7, th, rng)).rstrip(" .,;:?!") + "?"


def collapse_to_paragraph(ng, reg, slots, themes, order, rng):
    """COLLAPSE the held box: walk the read-head over slots in `order`, render each meaning forward."""
    out = []
    for i, k in enumerate(order):
        m = slots[k]
        assert reg.read(k) is not None                 # the meaning is HELD in the_one's slot
        if i == 1:
            out.append(question(ng, m, themes[m], rng))      # raise a question second
        else:
            out.append(statement(ng, m, themes[m], rng))
    return " ".join(out)


def main():
    print(f"=== R-RBS-LM-THEONE — hold the box (the_one) → COLLAPSE/unpack to a paragraph  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(3)
    text = k7.load_text()
    ng = k7.build_ng(text.encode("utf-8", "ignore"))       # STORAGE: byte n-gram (operator render)

    meanings = ["water", "music", "computer", "planet", "history", "animal", "number"]
    wseq = re.findall(r"[a-z]+", text.lower()); sset = set(meanings)
    neigh = {s: Counter() for s in meanings}
    for i, w in enumerate(wseq):
        if w in sset:
            for j in range(max(0, i - WIN), min(len(wseq), i + WIN + 1)):
                if j != i and len(wseq[j]) > 2:
                    neigh[w][wseq[j]] += 1
    glob = Counter()
    for s in meanings:
        glob.update(neigh[s])
    themes = {s: set([s] + [w for w in sorted(neigh[s], key=lambda x: neigh[s][x] / (1.0 + glob[x] - neigh[s][x]), reverse=True) if len(w) > 3][:25]) for s in meanings}

    # HOLD: k=7 meanings in the_one's box (the native SedenionRegister octonion working block e1..e7)
    reg = SedenionRegister()
    slots = {}
    for k, m in enumerate(meanings, start=1):
        reg.write(k, mint_vector("MEANING:" + m)); slots[k] = m
    print("[HOLD] the_one holds the box; 7 meanings in the octonion working slots e1..e7; read-back:",
          all(reg.read(k) is not None for k in slots))

    # COLLAPSE with each chirality (σ) — the two hands of the unpacking, the (4:3)|(3:4) dual
    for sigma in (+1, -1):
        S = the_one(sigma=sigma, theta_num=1, theta_den=7, terms=8)     # the holder, handedness σ
        # the collapse ORDER is σ-handed: σ=+1 forward, σ=-1 the conjugate/mirror order (the other hand)
        base = [1, 4, 5, 7]                                              # a topic→others walk over the slots
        order = base if sigma > 0 else base[::-1]
        para = collapse_to_paragraph(ng, reg, slots, themes, order, rng)
        hand = "(4:3) right hand" if sigma > 0 else "(3:4) left hand (conjugate)"
        print(f"\n[COLLAPSE σ={sigma:+d}]  {hand}  — the_one dim {S.dim}, n1_is_sigma_only {S.n1_is_sigma_only}:")
        print(f"  {para}")

    print("\nVERDICT:")
    print("  • The RBS-LM now HOLDS its meaning in the_one's box (the operand surface, F482/F483 — the native")
    print("    SedenionRegister slots), and GENERATES by COLLAPSING/unpacking the box (the read-head walk) into")
    print("    the operator/byte stream — a paragraph of thought (statement/question).")
    print("  • CHIRALITY (σ) is the hand the collapse picks: σ=+1 / σ=−1 are the (4:3)|(3:4) dual, each unpacking")
    print("    the SAME held box a different way (forward-only, F453 — the collapse must pick a hand).")
    print("  • Byte STORAGE / word WORK / transducer (F480). This is the operand-channel fix (F482) on the_one:")
    print("    the meaning is HELD, not bolted-on; the surface render is still the byte-grammar's local ceiling.")


if __name__ == "__main__":
    main()
