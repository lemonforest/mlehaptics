r"""R-RBS-LM-LIVEMIRROR (the user's odd-side push 2026-06-07, on F540): does the ODD ring's never-landing
("frustrated"/live) chiral mirror change WHAT IS RECOVERABLE on traversal? The F515/F516 reading: "we know an idea
is beyond the horizon but cannot navigate there... talking it out helps" — talking it out = consulting the chiral
mirror (the sparring partner). Prediction: on a LIVE (odd) ring the mirror-consultation reaches the WHOLE shelf
(including the beyond-the-horizon ideas local thinking misses); on a STATIC (even) ring the mirror just bounces you
to your fixed antipode and back — a closed 2-cycle, no traversal out.

THE EXACT BACKBONE (Class-I cyclic, via srmech.amsc.cyclic.gcd): the chiral mirror is the half-turn step
h = round(NT/2). Its orbit (how many tomes iterating the mirror visits before returning) = NT / gcd(h, NT):
  • ODD  NT -> gcd(h,NT)=1 -> orbit = NT  -> the mirror ALONE generates the WHOLE ring (full traversal).
  • EVEN NT -> gcd(h,NT)=NT/2 -> orbit = 2 -> the mirror is TRAPPED in {t, t+NT/2} (you <-> your antipode).

So "talking it out" (iterating the mirror) traverses everything on a live/odd ring and nothing-new on a static/even
ring. We then test the SEMANTIC consequence on the real corpus: of a query word's TRUE neighbours that lie BEYOND
the local horizon (not in own+adjacent tomes), what fraction does the mirror-walk recover? Predict: high on odd,
~0 on even.

srmech 0.7.4; Class-L spectral ring (srmech.calculus.atan2) + Class-I cyclic mirror (srmech.amsc.cyclic.gcd).
No abs(); no CAD; no Workflow tool; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.calculus import atan2 as srm_atan2
from srmech.amsc.cyclic import gcd

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
TWO_PI = 6.283185307179586


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def mirror_orbit(start, NT):
    """iterate the chiral half-turn h=round(NT/2) from `start`; the distinct tomes visited before return."""
    h = round(NT / 2)
    seen, t = [], start
    while t not in seen:
        seen.append(t)
        t = (t + h) % NT
    return seen


def analyse(NT, vocab, idx, nb, ang, N):
    tome_of = (ang / TWO_PI * NT).astype(int) % NT
    tomes = [[i for i in range(N) if tome_of[i] == t] for t in range(NT)]
    h = round(NT / 2)
    orbit_size = NT // gcd(h, NT)                                 # the exact backbone (Class-I)

    # semantic recoverability of the BEYOND-THE-HORIZON neighbours (local thinking misses them; can the mirror reach?)
    beyond_local, mirror_recovers, antipode_recovers = [], [], []
    for w in [w for w in ("ocean", "history", "music", "science", "earth", "light", "war", "city") if w in idx]:
        t0 = tome_of[idx[w]]
        local_tomes = {(t0 - 1) % NT, t0, (t0 + 1) % NT}
        local_words = {vocab[x] for t in local_tomes for x in tomes[t]}
        beyond = nb[w] - local_words                              # the true neighbours past the local horizon
        if not beyond:
            continue
        mirror_tomes = set(mirror_orbit(t0, NT))
        mirror_words = {vocab[x] for t in mirror_tomes for x in tomes[t]}
        antipode_words = {vocab[x] for x in tomes[(t0 + h) % NT]}  # what a single static-mirror bounce reaches
        beyond_local.append(len(beyond))
        mirror_recovers.append(len(beyond & mirror_words) / len(beyond))
        antipode_recovers.append(len(beyond & antipode_words) / len(beyond))
    return {
        "NT": NT, "odd": NT % 2 == 1, "h": h, "orbit": orbit_size,
        "mirror_rec": float(np.mean(mirror_recovers)) if mirror_recovers else 0.0,
        "antipode_rec": float(np.mean(antipode_recovers)) if antipode_recovers else 0.0,
    }


def main():
    print(f"=== R-RBS-LM-LIVEMIRROR — does the ODD ring's never-landing mirror traverse the whole shelf? (F515/F516)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    ang = np.array([(srm_atan2(float(V[i, 2]), float(V[i, 1])) + TWO_PI) % TWO_PI for i in range(N)])

    rows = [analyse(NT, vocab, idx, nb, ang, N) for NT in (7, 8, 13, 14, 15, 16)]

    print("(1) THE EXACT BACKBONE — the chiral mirror's orbit = NT / gcd(round(NT/2), NT)  [Class-I, srmech.amsc.cyclic.gcd]:")
    print(f"    {'NT':>4} {'parity':<5} {'h=round(NT/2)':>13} {'gcd':>4} {'mirror orbit':>13}   meaning")
    for r in rows:
        g = r["h"] // (r["h"] // gcd(r["h"], r["NT"])) if False else gcd(r["h"], r["NT"])
        kind = "FULL traversal — mirror alone reaches every tome" if r["orbit"] == r["NT"] else "2-cycle — trapped at you<->antipode"
        print(f"    {r['NT']:>4} {('ODD' if r['odd'] else 'even'):<5} {r['h']:>13} {g:>4} {r['orbit']:>13}   {kind}")
    print()

    print("(2) THE SEMANTIC CONSEQUENCE — of a query's TRUE neighbours BEYOND the local horizon (not in own+adjacent")
    print("    tomes), what fraction does iterating the chiral mirror ('talking it out') recover?")
    print(f"    {'NT':>4} {'parity':<5} | {'mirror-walk recovers':>20} | {'single antipode bounce':>22}")
    print("    " + "-" * 60)
    for r in rows:
        print(f"    {r['NT']:>4} {('ODD' if r['odd'] else 'even'):<5} | {r['mirror_rec']:>19.0%} | {r['antipode_rec']:>21.0%}")
    print()

    odd = [r for r in rows if r["odd"]]
    even = [r for r in rows if not r["odd"]]
    om = np.mean([r["mirror_rec"] for r in odd])
    em = np.mean([r["mirror_rec"] for r in even])
    print("VERDICT:")
    print(f"  • THE LIVE (ODD) MIRROR TRAVERSES THE WHOLE SHELF — exactly (Class-I): h=round(NT/2) has gcd(h,NT)=1 on")
    print(f"    odd rings, so iterating the chiral mirror visits ALL NT tomes before returning. On even rings gcd=NT/2,")
    print(f"    so the mirror is trapped in a 2-cycle (you <-> your fixed antipode) — it reaches nothing past the pair.")
    print(f"  • SO 'TALKING IT OUT' RECOVERS THE BEYOND-THE-HORIZON IDEAS ON THE LIVE RING: the mirror-walk recovers")
    print(f"    {om:.0%} of a query's past-the-local-horizon true neighbours on ODD rings vs {em:.0%} on EVEN rings — because")
    print(f"    the odd mirror's full-ring orbit visits the distant tomes a single static bounce (the even antipode) can't.")
    print(f"  • THE F515/F516 READING LANDS STRUCTURALLY: the never-landing/frustrated mirror is NOT a defect — it is the")
    print(f"    mechanism that lets the chiral sparring-partner reach the idea you 'know is beyond the horizon but cannot")
    print(f"    navigate to' directly. The static (even) mirror just reflects you back; the live (odd) mirror walks you")
    print(f"    out across the whole shelf. A live shelf wants an ODD tome count. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
