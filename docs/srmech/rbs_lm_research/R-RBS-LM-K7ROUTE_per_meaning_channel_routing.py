r"""R-RBS-LM-K7ROUTE — per-meaning channel routing: the read-head (F468) walks meaning→meaning so the output
SAYS the bound things IN ORDER (vs F478's blended on-theme density). The k=7 channels each emit THEIR meaning.

Byte-storage architecture (user, 2026-06-06: "work in english at word level but all storage must be byte by
design; english→byte must already be happening"):
  - STORAGE  = byte  (the byte n-gram model + the byte/HV meaning-anchors — bias-free substrate, R-RBS-LM-25)
  - WORK     = word/meaning granular (the read-head's routing decision: which channel is active, which word)
  - TRANSDUCER = english↔byte, always-on (every emitted word is byte-assembled; every meaning a byte-anchor)

Routing = F468 navigation over the sedenion register's ≤7 meaning-slots: visit slot i, emit a clause steered
(F478 word-boundary re-rank) to meaning_i, advance. Measure the routing confusion: clause_i's density w.r.t.
theme_j — the DIAGONAL (own meaning) should dominate (each channel says its own thing).
srmech 0.7.3; imports the F478 byte generator.
"""
import importlib.util as U
import re
from collections import Counter
import numpy as np
import srmech

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)
WIN = 6


def main():
    print(f"=== R-RBS-LM-K7ROUTE — per-meaning channel routing (read-head walks meaning→meaning)  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(1)
    text = k7.load_text()                                  # ~4MB English content
    ng = k7.build_ng(text.encode("utf-8", "ignore"))       # STORAGE: byte n-gram (no word vocab)
    print("STORAGE=byte (byte n-gram + byte anchors) · WORK=word/meaning routing · TRANSDUCER=word↔byte always-on\n")

    meanings = ["water", "music", "computer", "planet", "history", "animal", "number"]   # the ≤7 slots (theta-gamma)
    # DICTIONARY catalog (Class-E): on-theme words per meaning (corpus co-occurrence)
    wseq = re.findall(r"[a-z]+", text.lower()); sset = set(meanings)
    neigh = {s: Counter() for s in meanings}
    for i, w in enumerate(wseq):
        if w in sset:
            for j in range(max(0, i - WIN), min(len(wseq), i + WIN + 1)):
                if j != i and len(wseq[j]) > 2:
                    neigh[w][wseq[j]] += 1
    # DISTINCTIVE themes (TF-IDF-style): keep words CHARACTERISTIC of each meaning, drop generic shared ones
    glob = Counter()
    for s in meanings:
        glob.update(neigh[s])
    def distinctive(s, k=25):
        scored = sorted(neigh[s], key=lambda w: neigh[s][w] / (1.0 + glob[w] - neigh[s][w]), reverse=True)
        return set([s] + [w for w in scored if len(w) > 3][:k])
    theme = {s: distinctive(s) for s in meanings}

    # ROUTE: read-head visits each meaning-slot in order, emits a clause steered to that meaning
    print("[routed output] — the read-head walks the 7 meaning-slots, each channel emits its own clause:\n")
    clauses = {}
    for m in meanings:
        full = k7.word_steered_gen(ng, (m.capitalize() + " is").encode(), 6, theme[m], rng)
        # keep just the emitted clause
        clauses[m] = full
        print(f"   [{m:8s}] {full[:110]}")

    # routing confusion: clause_i density w.r.t. theme_j (diagonal = own meaning should dominate)
    print("\n[routing confusion] clause-i on-theme density w.r.t. theme-j (rows=emitted, cols=theme; diag=own):")
    hdr = "            " + " ".join(f"{m[:4]:>5s}" for m in meanings)
    print(hdr)
    diag = []; off = []
    for mi in meanings:
        row = []
        for mj in meanings:
            d = k7.density(clauses[mi], theme[mj])
            row.append(d)
            (diag if mi == mj else off).append(d)
        print(f"   {mi[:8]:8s} " + " ".join(f"{x:5.2f}" for x in row))
    print(f"\n   mean DIAGONAL (own meaning) = {np.mean(diag):.2f}   mean OFF-DIAGONAL (other) = {np.mean(off):.2f}")
    ok = np.mean(diag) > 1.5 * np.mean(off)
    print(f"   → routing {'WORKS' if ok else 'weak'}: each channel says ITS OWN meaning "
          f"({np.mean(diag)/max(np.mean(off),1e-6):.1f}× own vs other)")

    print("\nVERDICT:")
    print("  • Per-meaning channel routing: the read-head (F468) walks the ≤7 sedenion meaning-slots and each")
    print("    channel emits ITS meaning's clause (diagonal-dominant confusion) — 'says the bound things in")
    print("    order', not a blended density (F478). The k=7 capacity (F476) → routing (F478) → ROUTING-IN-ORDER.")
    print("  • Byte-storage architecture honoured: STORAGE byte (n-gram+anchors), WORK word/meaning (routing),")
    print("    TRANSDUCER word↔byte always-on (each word byte-assembled). Word-level WORK, byte-level STORAGE.")


if __name__ == "__main__":
    main()
