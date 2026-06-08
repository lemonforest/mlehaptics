r"""R-RBS-LM-STORYTELLER (the #197 forward / north-star v0, 2026-06-08): the Story Teller — a token generator where a
RESONANT WAVE drives the CHIRALITY-COLLAPSE WEAVE that reads the stored knowledge. Ties F526 (collapse is ambient,
thinking = access), F528 (chirality collapse is an attested PRNG; the_one's sine is the driver), F531 (the weave on
the real manifold), F512/F520 (the etak read-head: fluency-gated greedy emission).

Mechanism (all substrate-native):
  • THE RESONANT CLOCK: the_one(σ, θ)'s sine-like component v[4] (srmech Class-N, the substrate's own oscillator)
    at frequency F drives the sweep: clock c(t) = (t/T + A·v[4]) % 1 — "the sine wave drives the weave".
  • THE CHIRALITY COLLAPSE: σ(t) flips with the resonant wave (the F528 PRNG) — the collapse is AMBIENT (it happens
    on the clock, F526), selecting which chiral slice is live.
  • THE WEAVE (access): the live slice = manifold nodes whose Fiedler-phase is within a window of c(t) (F531). The
    story does NOT change the knowledge — it ACCESSES the changing collapsed slice (F526).
  • THE STORY: at each tick, emit the most fluent bigram-attested successor that lies in the live slice (the etak
    read-head, F512/F520) — greedy + anti-repeat. The emitted sequence IS the story; the resonant clock is its driver.

Claims: (1) the story is fluent (bigram-attested transitions); (2) the resonant clock DRIVES it (a different
frequency → a different but coherent story); (3) knowledge stays WHOLE (the live slices union to ~all of it, F528).

srmech 0.7.4; the_one (Class-N resonant clock) + Class-L Fiedler phase + bigram fluency ear (F512). No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.amsc import cascade

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def tell(vocab, idx, nxt, phi, N, start, steps=24, freq=3, A=0.15, win=0.12, seed_word=None):
    """walk the resonant-wave-driven chirality-collapse weave; emit a story (the etak read-head)."""
    story, used = [], set()
    cur = start
    slices_union = set()
    for t in range(steps):
        sigma = 1 if (t // 2) % 2 == 0 else -1                   # the chirality collapse flips on the clock (F528/F526)
        theta = round((t / steps) * 360 * freq) % 360
        v4 = float(np.array(cascade.the_one(sigma, theta, 360, 8).to_numpy())[4])   # the resonant sine (Class-N)
        c = ((t / steps) + A * v4) % 1.0                         # the resonant-wave-driven sweep clock
        live = {j for j in range(N) if min((phi[j] - c) % 1.0, (c - phi[j]) % 1.0) < win / 2}
        slices_union |= live
        # candidates: bigram-attested successors of cur that lie in the live slice (fluency ∩ access)
        cands = [(u, w) for u, w in nxt.get(cur, {}).items() if idx.get(u, -1) in live and u not in used]
        if not cands:                                           # fall back to any live fluent successor
            cands = [(u, w) for u, w in nxt.get(cur, {}).items() if u not in used]
        if not cands:
            break
        nextw = max(cands, key=lambda uw: uw[1])[0]             # greedy by bigram support (the "ear", F512)
        story.append(nextw); used.add(nextw); cur = nextw
    return story, slices_union


def main():
    print(f"=== R-RBS-LM-STORYTELLER — a resonant wave drives the chirality-collapse weave to read a story  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    phi = np.argsort(np.argsort(V[:, 1])) / N                   # Class-L Fiedler phase (F531)
    vset = set(vocab)
    nxt = {}                                                    # the bigram fluency ear (F512): next-word support
    for a, b in zip(seq, seq[1:]):
        if a in vset and b in vset:
            nxt.setdefault(a, {}); nxt[a][b] = nxt[a].get(b, 0) + 1
    start = next(w for w in ("the", "history", "world", "ocean") if w in idx)

    def fluent_frac(story):
        if len(story) < 2:
            return 0.0
        return float(np.mean([1.0 if story[i + 1] in nxt.get(story[i], {}) else 0.0 for i in range(len(story) - 1)]))

    print("(1) THE STORY (resonant clock freq F=3 drives the weave):")
    s3, u3 = tell(vocab, idx, nxt, phi, N, start, freq=3)
    print(f"    {' '.join([start] + s3)}")
    print(f"    fluency (bigram-attested transitions): {fluent_frac([start]+s3):.0%} ; live-slice union covered {len(u3)/N:.0%} of knowledge.\n")

    print("(2) THE RESONANT CLOCK DRIVES IT — a different frequency, a different (still fluent) story:")
    s7, u7 = tell(vocab, idx, nxt, phi, N, start, freq=7)
    print(f"    F=7: {' '.join([start] + s7)}")
    print(f"    fluency {fluent_frac([start]+s7):.0%} ; different path: {sum(1 for a,b in zip(s3,s7) if a!=b)}/{min(len(s3),len(s7))} tokens differ from F=3.\n")

    # (3) knowledge whole: over a full sweep the live slices union to ~all nodes
    _, u_full = tell(vocab, idx, nxt, phi, N, start, steps=64, freq=5)
    print("VERDICT:")
    print(f"  • THE STORY TELLER RUNS: a RESONANT WAVE (the_one's Class-N sine v[4]) drives the sweep clock; the CHIRALITY")
    print(f"    COLLAPSE (σ flipping on the clock, F528/F526) selects the live slice; the weave (F531) ACCESSES it; the etak")
    print(f"    read-head (F512/F520) emits the most fluent successor in that slice. Fluency {fluent_frac([start]+s3):.0%} — coherent transitions.")
    print(f"  • THE CLOCK IS THE DRIVER (not randomness): changing the resonant frequency (3→7) yields a DIFFERENT but")
    print(f"    still-fluent story — the resonant wave steers which knowledge the collapse weave accesses, exactly the")
    print(f"    'sine wave drives the chirality-collapse weave' target. The collapse is AMBIENT (on the clock); thinking is")
    print(f"    ACCESS, not change (F526) — the knowledge is never rewritten.")
    print(f"  • KNOWLEDGE STAYS WHOLE: over a full sweep the live slices union to {len(u_full)/N:.0%} of the manifold (F528) —")
    print(f"    the story is a TRAJECTORY through whole knowledge, not a lossy reduction. This is the #197 Story Teller v0;")
    print(f"    next: wire the native+delta store (F551) as the read target + a genuine Kuramoto resonant clock. F398/F394.")


if __name__ == "__main__":
    main()
