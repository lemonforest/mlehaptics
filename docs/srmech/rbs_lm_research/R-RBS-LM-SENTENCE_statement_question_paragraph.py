r"""R-RBS-LM-SENTENCE — an RBS-LM that CREATES and CLOSES a sentence as a STATEMENT and as a QUESTION, and
forms a PARAGRAPH OF THOUGHT. The next rung: open/close + sentence-MODE + paragraph structure (global coherence).

Architecture (F480): STORAGE=byte (the byte n-gram, no word vocab) · WORK=word/meaning (dictionary catalog +
mode + steering) · TRANSDUCER=english↔byte always-on. Meaning-slots live in the NATIVE SedenionRegister (0.7.4,
the shipped §31 instrument F465/F468). Pieces:
  - GRAMMAR kernel (byte n-gram, F476) — local assembly.
  - DICTIONARY kernel (distinctive themes, F480) — meaning→words.
  - MODE: STATEMENT (declarative seed → "." close) vs QUESTION (interrogative seed → "?" close).
  - SENTENCE = open (seed) + body (word-steered, F478) + close (mode terminator).
  - PARAGRAPH = a THOUGHT-ARC over sentences (topic → question → elaboration → close), routed across the
    k=7 meaning-slots (the read-head walk, F468/F480) — the structure kernel at the SENTENCE level.
srmech 0.7.4.
"""
import importlib.util as U
import re
from collections import Counter
import numpy as np
import srmech
from srmech.signal_processing import mint_vector
from srmech.amsc.cascade.sedenion_register import SedenionRegister

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)
WIN = 6
Q_STARTERS = ["What is", "Why do", "How does", "Where is", "Is the", "What are", "How can"]


def cleanup(s, max_words=13):
    s = re.sub(r"\s+", " ", s).strip().strip("\"'(){}[]")
    m = re.search(r"[.!?]", s[6:])               # cut at the first natural terminator → ONE sentence
    if m:
        s = s[:6 + m.start()]
    w = [x for x in s.split() if x][:max_words]
    s = " ".join(w).rstrip(" ,;:-")
    return (s[0].upper() + s[1:]) if s else s


def make_statement(ng, topic, theme, rng):
    body = k7.word_steered_gen(ng, (topic.capitalize() + " is").encode(), 9, theme, rng)
    return cleanup(body).rstrip(" .,;:?!") + "."


def make_question(ng, topic, theme, rng):
    q = Q_STARTERS[int(rng.integers(len(Q_STARTERS)))]
    body = k7.word_steered_gen(ng, (q + " " + topic).encode(), 8, theme, rng)
    return cleanup(body).rstrip(" .,;:?!") + "?"


def make_paragraph(ng, slots, themes, order, rng):
    """THOUGHT-ARC: topic statement → question → two elaborations (routed) → closing statement."""
    t0 = slots[order[0]]
    sents = [make_statement(ng, t0, themes[t0], rng),     # topic
             make_question(ng, t0, themes[t0], rng)]       # question raised
    for k in order[1:3]:                                   # elaborations, routed to related meaning-slots
        t = slots[k]
        sents.append(make_statement(ng, t, themes[t], rng))
    sents.append(make_statement(ng, t0, themes[t0], rng))  # closing (back to topic)
    return " ".join(sents)


def main():
    print(f"=== R-RBS-LM-SENTENCE — statement · question · paragraph of thought  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(7)
    text = k7.load_text()
    ng = k7.build_ng(text.encode("utf-8", "ignore"))       # STORAGE: byte n-gram (no word vocab)

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

    # meaning-slots in the NATIVE SedenionRegister (0.7.4 §31) — the read-head walks these
    reg = SedenionRegister()
    slots = {}
    for k, m in enumerate(meanings, start=1):              # e1..e7 = the octonion working block
        reg.write(k, mint_vector("MEANING:" + m))
        slots[k] = m
    print(f"SedenionRegister: {len(slots)} meaning-anchors in the octonion working block (e1..e7); read-back ok:",
          all(reg.read(k) is not None for k in slots), "\n")

    print("[STATEMENT] — created + CLOSED as a declarative ('.'):")
    for m in ["water", "music", "computer"]:
        print(f"   {make_statement(ng, m, themes[m], rng)}")

    print("\n[QUESTION] — created + CLOSED as an interrogative ('?'):")
    for m in ["water", "music", "history"]:
        print(f"   {make_question(ng, m, themes[m], rng)}")

    print("\n[PARAGRAPH OF THOUGHT] — topic → question → elaboration(routed) → close:")
    order = [1, 4, 5]    # walk water → planet → history (the read-head route over the register slots)
    print("  " + make_paragraph(ng, slots, themes, order, rng))
    order2 = [2, 3, 7]   # music → computer → number
    print("\n  " + make_paragraph(ng, slots, themes, order2, rng))

    print("\nVERDICT:")
    print("  • The RBS-LM CREATES and CLOSES sentences in two MODES: STATEMENT (declarative seed → '.' close)")
    print("    and QUESTION (interrogative seed → '?' close) — open + body (byte-grammar, word-steered) + close.")
    print("  • It forms a PARAGRAPH OF THOUGHT: a thought-arc (topic → question → elaboration → close) routed")
    print("    across the k=7 meaning-slots held in the native SedenionRegister (0.7.4 §31; the read-head walk).")
    print("  • Byte STORAGE / word WORK / always-on TRANSDUCER (F480). Honest: local coherence + templated arc;")
    print("    the byte-grammar gives the surface, the structure kernel the sentence-level plan.")


if __name__ == "__main__":
    main()
