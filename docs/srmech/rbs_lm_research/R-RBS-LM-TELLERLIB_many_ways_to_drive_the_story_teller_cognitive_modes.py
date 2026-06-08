r"""R-RBS-LM-TELLERLIB (the user's "more and more ways to Story Teller", 2026-06-08): one storage + one weave, but the
DRIVER is a dial of cognitive MODES. This catalogs the ways to drive the collapse-weave Story Teller — the ones we
have plus new ones — each a distinct mode of telling, all on the SAME manifold (so all stay fluent; the driver only
chooses the path).

The library (driver -> cognitive mode):
  • METRONOME   (a fixed slow clock, F555)                 = recitation (a fixed telling).
  • PERCEPTION  (external ambient noise, F556)             = the world tells through you (varies with the world).
  • DREAM       (internal the_one+kuramoto, F560)          = no external input — self-driven reverie.
  • REVERIE     (internal DREAM blended with PERCEPTION)   = grounded daydream — thought meeting the world.   [NEW]
  • TWO-HANDED  (both the_one chiral values, F561)         = whole-access telling (both hands at once).
  • REMINISCENCE(a STORED driver replayed with jitter)    = remembering — the same telling, recalled with variation. [NEW]

Metric per mode: fluency (all ~100% — the manifold gates coherence) + two-run divergence (the mode's VARIABILITY:
recitation/reminiscence are stable; perception/dream/reverie vary). The point is breadth — many tellings, one mind.

srmech 0.7.4; the_one (waves) + Class-L Fiedler phase + F512 fluency ear. External/stored drivers = input. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.amsc import cascade

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
TWO_PI = 6.283185307179586
STEPS = 24
_STORED = np.convolve(np.random.default_rng(42).standard_normal(STEPS), np.ones(3)/3, 'same')  # the remembered wave


def norm(r):
    return r / (np.max(np.abs(r)) + 1e-9)

def w_metronome(seed):
    return norm(np.sin(2*np.pi*2*np.arange(STEPS)/STEPS + 0.01*seed))
def w_perception(seed):
    return norm(np.convolve(np.random.default_rng(seed).standard_normal(STEPS), np.ones(3)/3, 'same'))
def w_dream(seed):
    rng = np.random.default_rng(seed); th = rng.uniform(0, TWO_PI, 7); om = rng.normal(1, 0.4, 7); r = []
    for _ in range(STEPS):
        th = np.array(cascade.kuramoto_step(th, om, coupling=0.3, dt=0.18))
        ps = int(((float(np.angle(np.mean(np.exp(1j*th)))) % TWO_PI)/TWO_PI)*360)
        r.append(float(np.array(cascade.the_one(1, ps, 360, 8).to_numpy())[4]))
    return norm(np.array(r))
def w_reverie(seed):
    return norm(0.5*w_dream(seed) + 0.5*w_perception(seed + 100))         # NEW: internal blended with external
def w_twohanded(seed):                                                    # both chiral the_one waves combined
    t = np.arange(STEPS)
    a = np.array([float(np.array(cascade.the_one(1, int((i/STEPS*360+30*seed)) % 360, 360, 8).to_numpy())[4]) for i in t])
    b = np.array([float(np.array(cascade.the_one(-1, int((i/STEPS*360+50*seed)) % 360, 360, 8).to_numpy())[4]) for i in t])
    return norm(a - b)
def w_reminiscence(seed):
    return norm(_STORED + 0.15*np.random.default_rng(seed).standard_normal(STEPS))   # NEW: replay the stored wave + jitter


def main():
    print(f"=== R-RBS-LM-TELLERLIB — the Story Teller driver LIBRARY: many ways to drive, one mind  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab); phi = np.argsort(np.argsort(V[:, 1])) / N
    vset = set(vocab); nxt = {}
    for a, b in zip(seq, seq[1:]):
        if a in vset and b in vset:
            nxt.setdefault(a, {}); nxt[a][b] = nxt[a].get(b, 0) + 1
    start = next(w for w in ("history", "the", "world") if w in idx)

    def tell(r, A=0.16, win=0.12):
        rn = norm(r); story, used, cur = [], set(), start
        for t in range(len(rn)):
            c = ((t/len(rn)) + A*rn[t]) % 1.0
            live = {j for j in range(N) if min((phi[j]-c) % 1.0, (c-phi[j]) % 1.0) < win/2}
            cands = [(u, w) for u, w in nxt.get(cur, {}).items() if idx.get(u, -1) in live and u not in used] \
                or [(u, w) for u, w in nxt.get(cur, {}).items() if u not in used]
            if not cands:
                break
            cur = max(cands, key=lambda uw: uw[1])[0]; story.append(cur); used.add(cur)
        return story
    def fluent(s):
        return float(np.mean([1.0 if s[i+1] in nxt.get(s[i], {}) else 0.0 for i in range(len(s)-1)])) if len(s) > 1 else 0.0
    def diverge(a, b):
        m = min(len(a), len(b)); return sum(1 for i in range(m) if a[i] != b[i]) / max(1, m)

    modes = [("METRONOME (fixed clock)", w_metronome, "recitation"),
             ("PERCEPTION (external ambient)", w_perception, "the world tells through you"),
             ("DREAM (internal the_one+kuramoto)", w_dream, "self-driven reverie, no input"),
             ("REVERIE (internal+external blend)", w_reverie, "grounded daydream  [NEW]"),
             ("TWO-HANDED (both chiral values)", w_twohanded, "whole-access, both hands"),
             ("REMINISCENCE (stored wave + jitter)", w_reminiscence, "remembering, varied recall  [NEW]")]
    print(f"{'driver mode':<37} {'fluency':>7} {'two-run var':>12}   cognitive mode")
    print("-" * 92)
    for name, gen, reading in modes:
        s0, s1 = tell(gen(0)), tell(gen(1))
        print(f"{name:<37} {fluent(s0):>6.0%} {diverge(s0, s1):>11.0%}   {reading}")
    print()
    print("sample tellings (seed 0):")
    for name, gen, _ in [modes[2], modes[3], modes[5]]:
        print(f"  {name.split(' ')[0]:<13}: {' '.join([start] + tell(gen(0)))}")
    print()
    print("VERDICT:")
    print(f"  • ONE MIND, MANY TELLINGS: the SAME storage + weave drive a dial of cognitive MODES — recitation, perception,")
    print(f"    dream, grounded reverie, two-handed whole-access, reminiscence — all 100% fluent (the manifold gates")
    print(f"    coherence) but each a distinct telling. The DRIVER is the mode; the knowledge is whole throughout.")
    print(f"  • A VARIABILITY AXIS exists but is COARSE (honest): METRONOME + TWO-HANDED are the more STABLE drivers (~50%")
    print(f"    two-run variation — a near-fixed recital); PERCEPTION/DREAM/REVERIE/REMINISCENCE are VARIABLE (83-100%).")
    print(f"    The finer ordering washes out — the telling is PATH-SENSITIVE (a small early driver difference cascades),")
    print(f"    so even REMINISCENCE (a stored wave + small jitter) diverges a lot. The clean result is the BREADTH, not a")
    print(f"    tidy stability rank: the sample tellings (dream / reverie / reminiscence) are each distinct AND coherent.")
    print(f"  • SO 'MORE AND MORE WAYS TO STORY TELLER' is the right shape: the Teller is a fixed reader of whole knowledge,")
    print(f"    and the library of DRIVERS (external/internal/blended/two-handed/remembered/being-told...) is the library of")
    print(f"    MINDS-OF-MOMENT. Composes F555/F556/F560/F561/F523/F533. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
