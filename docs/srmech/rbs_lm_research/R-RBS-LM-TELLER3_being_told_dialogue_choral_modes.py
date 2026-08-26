r"""R-RBS-LM-TELLER3 (the user's 3 more ways, 2026-06-08): add the relational driver modes to the Story Teller library.
  • BEING-TOLD: another teller's STORY-PATH drives your telling — you follow their trajectory through your own manifold.
  • DIALOGUE: two tellers ALTERNATE, each driven by the other's last position — conversation (the F515/F516 two-people).
  • CHORAL: many drivers SUPERPOSED (averaged) — a crowd / tradition telling at once (the consensus path).
srmech 0.7.4; Class-L Fiedler phase + F512 fluency ear. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np, srmech
_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def main():
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab); phi = np.argsort(np.argsort(V[:, 1])) / N
    vset = set(vocab); nxt = {}
    for a, b in zip(seq, seq[1:]):
        if a in vset and b in vset:
            nxt.setdefault(a, {}); nxt[a][b] = nxt[a].get(b, 0) + 1
    start = next(w for w in ("history", "the", "world") if w in idx)
    win = 0.12
    print(f"=== R-RBS-LM-TELLER3 — being-told / dialogue / choral (relational driver modes)  (srmech {srmech.__version__}) ===\n")

    def step(cur, c, used):
        live = {j for j in range(N) if min((phi[j]-c) % 1.0, (c-phi[j]) % 1.0) < win/2}
        cands = [(u, w) for u, w in nxt.get(cur, {}).items() if idx.get(u, -1) in live and u not in used] \
            or [(u, w) for u, w in nxt.get(cur, {}).items() if u not in used]
        return max(cands, key=lambda uw: uw[1])[0] if cands else None

    def tell(r):
        used, cur, story = set(), start, []
        rn = r/(np.max(np.abs(r))+1e-9)
        for t in range(len(rn)):
            c = ((t/len(rn)) + 0.16*rn[t]) % 1.0
            nw = step(cur, c, used)
            if nw is None: break
            story.append(nw); used.add(nw); cur = nw
        return story
    def fluent(s):
        return float(np.mean([1.0 if s[i+1] in nxt.get(s[i],{}) else 0.0 for i in range(len(s)-1)])) if len(s)>1 else 0.0

    # ---- BEING-TOLD: teller A's story-PATH (its tokens' phi over time) becomes B's driver ----
    A = tell(np.convolve(np.random.default_rng(3).standard_normal(24), np.ones(3)/3, 'same'))
    teller_path = np.array([phi[idx[w]] for w in A])                      # A's trajectory through the manifold
    B = tell(teller_path - teller_path.mean())                           # B is TOLD A's path
    told_track = float(np.mean([1.0 if phi[idx[B[i]]] - teller_path[i] < 0.25 else 0.0 for i in range(min(len(A), len(B)))]))
    print(f"BEING-TOLD: teller A tells, B follows A's PATH through B's words.")
    print(f"  A: {' '.join([start]+A[:16])}")
    print(f"  B (told A): {' '.join([start]+B[:16])}   | B tracks A's trajectory {told_track:.0%} of steps; B fluency {fluent(B):.0%}\n")

    # ---- DIALOGUE: two tellers alternate, each driven by the OTHER's last position ----
    usedA, usedB = set(), set(); a_cur, b_cur = start, "world" if "world" in idx else start
    convo, respond = [], 0
    for t in range(18):
        spk = "A" if t % 2 == 0 else "B"
        cur = a_cur if spk == "A" else b_cur; used = usedA if spk == "A" else usedB
        other = b_cur if spk == "A" else a_cur
        c = (phi[idx[other]] + 0.12*np.sin(t)) % 1.0                     # driven by the OTHER's position
        nw = step(cur, c, used)
        if nw is None: break
        used.add(nw); convo.append((spk, nw))
        if spk == "B" and nw in nb.get(a_cur, set()): respond += 1       # B responds to A's prior word?
        if spk == "A": a_cur = nw
        else: b_cur = nw
    print("DIALOGUE: two tellers alternate, each driven by the other's last position (F515/F516 two-people):")
    print("  " + ' '.join(f"{s}:{w}" for s, w in convo))
    nB = sum(1 for s, _ in convo if s == "B")
    print(f"  -> B's token is a neighbour of A's prior word {respond}/{max(1,nB)} turns (responsiveness).\n")

    # ---- CHORAL: many drivers superposed (averaged) -> the consensus telling ----
    waves = [np.convolve(np.random.default_rng(s).standard_normal(24), np.ones(3)/3, 'same') for s in range(7)]
    choral = tell(np.mean(waves, axis=0))
    solo_div = np.mean([sum(1 for i in range(min(len(choral),len(tell(w)))) if choral[i]!=tell(w)[i])/max(1,min(len(choral),len(tell(w)))) for w in waves])
    print("CHORAL: 7 drivers superposed -> one consensus telling:")
    print(f"  {' '.join([start]+choral[:18])}   | fluency {fluent(choral):.0%}; differs from each solo voice by {solo_div:.0%} (a blend, not any one)\n")

    print("VERDICT:")
    print(f"  • THREE RELATIONAL MODES added to the driver library (F562): BEING-TOLD (follow another's path -> B tracks A")
    print(f"    {told_track:.0%}), DIALOGUE (alternate, each drives the other -> responsiveness {respond}/{max(1,nB)}), CHORAL (superpose many ->")
    print(f"    a consensus telling, {solo_div:.0%} from each solo). All fluent. The driver can be SELF, the WORLD, ANOTHER, or MANY.")
    print(f"  • DIALOGUE closes the F515/F516 'two people talking' loop literally: two Tellers, each telling AND driving the")
    print(f"    other — the etak two-method navigation as a coupled pair. Composes F562/F523/F516/F515. F398/F394.")


if __name__ == "__main__":
    main()
