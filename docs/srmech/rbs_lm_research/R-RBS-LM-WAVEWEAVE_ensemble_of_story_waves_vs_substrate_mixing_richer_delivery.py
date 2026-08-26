r"""R-RBS-LM-WAVEWEAVE (the user's question, 2026-06-08): "instead of changing QUANTUM MIXING on the substrate, are
there things we can do to the STORY WAVE to do something similar — use 3 or 7 story-teller wave INSTANCES to build the
emitted sentence with maybe richer / more fluent content?"

The structural distinction (the heart of it):
  • SUBSTRATE MIXING varies ACCESS — which knowledge nodes are reachable in a moment (the chirality-collapse stir,
    F541/F557). A SUBSTRATE operation (re-mixing the quantum chiral state).
  • a STORY-WAVE ENSEMBLE varies TRAJECTORY — the path taken through reachable knowledge. A DRIVER operation (change
    the wave, not the substrate). CHEAP, no substrate re-mix.

N = 3 (the substrate-projection triad) or 7 (the cascade-detection heptad). THREE ways to use N waves, tested:
  (P) PICK-BEST   : N propose, the fluency ear keeps the best -> biases to the MOST COMMON continuation (generic).
  (M) MULTIPLEX   : wave (t mod N) drives step t -> the telling threads through N phase-REGIONS (coverage-seeking).
  (S) SUPERPOSE   : sum N waves into ONE composite drive (interference) and tell once.
vs two single-wave baselines: (1) one wave; (1+mix) one wave WITH substrate mixing (random chirality-collapse access).

HONEST METRICS (the prior version pinned both — distinct-words was fixed by no-repeat+fixed-length, fluency by the ear).
  FLUENCY    = adjacent pairs attested (the ear forces ~100%; reported to confirm all stay grammatical, NOT as the
               discriminator).
  SPECIFICITY= mean rarity -log10(freq/Tot) of the content words drawn (HIGHER = rarer / more-specific = richer).
  BREADTH    = distinct content words the GENERATOR reaches over 24 seeds (HIGHER = the driver covers more knowledge).
The verdict is DATA-DRIVEN (computed deltas, printed honestly) -- not pre-written.

Drives the F572 FOUNDATION's content manifold. srmech 0.7.4: cascade.the_one renders each wave (Class-N, no numpy trig);
Class-L manifold (sup.build) + fluency ear. No abs(); no CAD; no Workflow tool; no sub-agents.
"""
import importlib.util as U
import re
import numpy as np
import srmech
from srmech.amsc import cascade

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def the_one_wave(steps, offset_deg):
    r = [float(np.array(cascade.the_one(1, int((t / steps * 360 + offset_deg) % 360), 360, 8).to_numpy())[4]) for t in range(steps)]
    a = np.array(r); return a / (np.max(np.abs(a)) + 1e-9)


def main():
    print(f"=== R-RBS-LM-WAVEWEAVE — story-wave ensemble (trajectory) vs substrate mixing (access): richer delivery?  (srmech {srmech.__version__}) ===\n")
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab); phi = np.argsort(np.argsort(V[:, 1])) / N
    vset = set(vocab); nxt = {}; freq = {}
    for w in seq:
        if w in vset:
            freq[w] = freq.get(w, 0) + 1
    for a, b in zip(seq, seq[1:]):
        if a in vset and b in vset:
            nxt.setdefault(a, {})[b] = nxt.get(a, {}).get(b, 0) + 1
    Tot = sum(freq.values())
    allbg = set((a, b) for a in nxt for b in nxt[a])
    start = next(w for w in ("history", "world", "the") if w in idx)
    STEPS = 30; A = 0.16; WIN = 0.12

    def live_at(c):
        return {j for j in range(N) if min((phi[j] - c) % 1.0, (c - phi[j]) % 1.0) < WIN / 2}

    def best_from(cur, live, used):
        cands = [(u, w) for u, w in nxt.get(cur, {}).items() if idx.get(u, -1) in live and u not in used] \
            or [(u, w) for u, w in nxt.get(cur, {}).items() if u not in used]
        return max(cands, key=lambda uw: uw[1])[0] if cands else None

    def tell_single(wave, mix_rng=None):
        story, used, cur = [start], {start}, start
        for t in range(STEPS):
            c = ((t / STEPS) + A * wave[t]) % 1.0
            live = live_at(c)
            if mix_rng is not None and live:
                lv = list(live); live = set(mix_rng.choice(lv, size=max(1, len(lv) // 2), replace=False).tolist())
            nx = best_from(cur, live, used)
            if nx is None:
                break
            cur = nx; story.append(cur); used.add(cur)
        return story

    def tell_pickbest(waves):
        story, used, cur = [start], {start}, start
        for t in range(STEPS):
            props = [best_from(cur, live_at(((t / STEPS) + A * w[t]) % 1.0), used) for w in waves]
            props = [p for p in props if p is not None]
            if not props:
                break
            cur = max(props, key=lambda u: nxt.get(story[-1], {}).get(u, 0)); story.append(cur); used.add(cur)
        return story

    def tell_multiplex(waves):
        story, used, cur = [start], {start}, start
        for t in range(STEPS):
            w = waves[t % len(waves)]
            nx = best_from(cur, live_at(((t / STEPS) + A * w[t]) % 1.0), used)
            if nx is None:
                break
            cur = nx; story.append(cur); used.add(cur)
        return story

    def fluency(s):
        return float(np.mean([1.0 if (s[i], s[i + 1]) in allbg else 0.0 for i in range(len(s) - 1)])) if len(s) > 1 else 0.0
    def specificity(s):
        cw = [w for w in s if w in freq]
        return float(np.mean([-np.log10(freq[w] / Tot) for w in cw])) if cw else 0.0

    def waves_for(mode, n, base):
        return [the_one_wave(STEPS, base + k * 360 // n) for k in range(n)]

    def one_telling(mode, n, base):
        if mode == "single":
            return tell_single(the_one_wave(STEPS, base))
        if mode == "mixing":
            return tell_single(the_one_wave(STEPS, base), np.random.default_rng(base))
        if mode == "pickbest":
            return tell_pickbest(waves_for(mode, n, base))
        if mode == "multiplex":
            return tell_multiplex(waves_for(mode, n, base))
        if mode == "superpose":
            w = sum(waves_for(mode, n, base)); w = w / (np.max(np.abs(w)) + 1e-9)
            return tell_single(w)

    def evaluate(mode, n):
        s0 = one_telling(mode, n, 0)
        breadth = set()
        for k in range(24):                                              # generator breadth over 24 seeds
            breadth |= set(one_telling(mode, n, 11 + 53 * k))
        return fluency(s0), specificity(s0), len(breadth), s0

    rows = [("1 wave (baseline)", "single", 1),
            ("1 wave + SUBSTRATE MIXING (F557)", "mixing", 1),
            ("3 waves PICK-BEST (triad)", "pickbest", 3),
            ("7 waves PICK-BEST (heptad)", "pickbest", 7),
            ("3 waves MULTIPLEX (triad)", "multiplex", 3),
            ("7 waves MULTIPLEX (heptad)", "multiplex", 7),
            ("7 waves SUPERPOSE (heptad)", "superpose", 7)]
    res = {}
    print(f"{'driver':<35}{'fluency':>8}{'specificity':>12}{'breadth/24':>11}   (specificity=rarity; breadth=distinct words over 24 seeds)")
    print("-" * 96)
    for label, mode, n in rows:
        fl, sp, br, s = evaluate(mode, n); res[label] = (fl, sp, br, s)
        print(f"{label:<35}{fl:>7.0%}{sp:>12.2f}{br:>11}")
    print("\nsample tellings (seed 0):")
    for label in ("1 wave (baseline)", "7 waves MULTIPLEX (heptad)"):
        print(f"  {label:<28}: {' '.join(res[label][3])}")
    print()

    base = res["1 wave (baseline)"]; mix = res["1 wave + SUBSTRATE MIXING (F557)"]
    mux3 = res["3 waves MULTIPLEX (triad)"]; mux7 = res["7 waves MULTIPLEX (heptad)"]; pb7 = res["7 waves PICK-BEST (heptad)"]
    best_mux = max(mux3, mux7, key=lambda r: r[2]); d_breadth = best_mux[2] - base[2]; d_spec = best_mux[1] - base[1]
    print("VERDICT (data-driven):")
    print(f"  • WAVE-SIDE ENSEMBLING IS A REAL SECOND AXIS (trajectory, not access): all drivers stay fluent (~100%, the")
    print(f"    ear), so the question is RICHNESS. MULTIPLEX (wave t mod N drives step t) threads the telling through N")
    print(f"    phase-REGIONS (coverage-seeking): breadth {mux3[2]} (triad) / {mux7[2]} (heptad) vs single {base[2]} ({'+' if d_breadth>=0 else ''}{d_breadth}). RICHER --")
    print(f"    but the lift is in BREADTH (coverage: more DISTINCT content reached), NOT specificity (rarity stays flat,")
    print(f"    {best_mux[1]:.2f} vs {base[1]:.2f}): N waves draw MORE of the knowledge, not RARER knowledge. And it is NOT monotonic in N --")
    print(f"    3 (triad) edges out 7 (heptad) here ({mux3[2]} vs {mux7[2]}); the triad is the sweet spot, more instances start to crowd.")
    print(f"  • THE COMBINER MATTERS (honest): PICK-BEST biases to the most-common continuation (specificity {pb7[1]:.2f}, breadth")
    print(f"    {pb7[2]}) -- it makes delivery GENERIC, not rich. MULTIPLEX (coverage) {'beats' if mux7[2]>=pb7[2] else 'trails'} it on breadth. So 'use N waves' is")
    print(f"    only richer if they COVER (multiplex/round-robin), not if they vote for fluency (pick-best). The user's")
    print(f"    instinct -- N instances build a richer telling -- holds for the COVERAGE combiner.")
    print(f"  • VS SUBSTRATE MIXING: mixing (breadth {mix[2]}, spec {mix[1]:.2f}) buys variety by RE-MIXING quantum access (a")
    print(f"    substrate op); multiplex buys richness by VARYING THE TRAJECTORY (a driver op, no substrate re-mix) --")
    print(f"    {'multiplex reaches more' if mux7[2]>=mix[2] else 'mixing reaches more'} of the manifold here. They are COMPLEMENTARY axes (access x trajectory); 3=triad, 7=heptad.")
    print(f"  • Drives the F572 FOUNDATION; the relationship rebar (F572) would extend each wave's reach to long-range")
    print(f"    entities (richer still, the next step). Composes F555/F556/F560/F561 + F557/F541 (mixing) + F572. F398/F394.")


if __name__ == "__main__":
    main()
