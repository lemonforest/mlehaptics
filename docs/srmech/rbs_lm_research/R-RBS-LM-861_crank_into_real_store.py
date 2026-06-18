"""F861: crank the REAL Klein-4 D=10000 store (not the the_one 14-D proxy).
New chirality-native continuous-phase op: phase = fraction of slots flipped into
the gamma5 sector (circular half-window population code) -- the F844-848 missing
primitive. Drive each real clump-HV by gear-rate=mass; read arrangement-evolution,
syzygy, massless center, dark-star on the actual store. srmech-native, sparse.
"""
from srmech.amsc import hdc
from srmech.amsc.hv import HV
from srmech.rbs_lm import substrate as S

D = 10000
GAMMA5 = 2                         # V4 element whose XOR-bind flips {0<->2,1<->3}
HALF = D // 2

def phase_key(frac):
    """circular half-window of gamma5 (sector 2) starting at frac*D, identity (0) else."""
    start = int(round(frac * D)) % D
    seq = [0] * D
    for j in range(HALF):
        seq[(start + j) % D] = GAMMA5
    return HV.from_sequence(seq)

def phase_state(hv, frac):
    """rotate a real clump-HV to crank-phase 'frac' (turns in [0,1)) via population code."""
    return hdc.klein4_bind(hv, phase_key(frac % 1.0))

# --- op self-check: circular, syzygy at dphase=0, smooth ---
base = hdc.klein4_random(D, seed=11)
print("chirality-native continuous-phase op (circular half-window gamma5 population code):")
for df in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9]:
    s = hdc.klein4_similarity(phase_state(base, 0.0), phase_state(base, df))
    print(f"  dphase={df:.2f} turn  sim={s:+.3f}   (circular: 0->1, .5->0, .9~.2)")

# --- build the REAL clumps from the actual ContextSubstrate (F859 cells) ---
cs = S.ContextSubstrate(D=D, hex_chars=16)
CELLS = {
    "hub":       (["the", "and", "united", "states", "war", "list", "language"], 34534),
    "scaffold":  (["december", "july", "state", "north", "october", "august", "system", "september"], 10604),
    "antiquity": (["ancient", "mythology", "greek", "sun"], 7078),
    "computing": (["computer", "mario", "internet"], 2968),
    "windows":   (["windows", "microsoft", "software"], 455),
    "liverpool": (["liverpool", "football", "club"], 291),
}
M_REF = 10604
clump = {n: cs.bundle_odd([cs.enc(t) for t in toks]) for n, (toks, _) in CELLS.items()}
rate = {n: m / M_REF for n, (_, m) in CELLS.items()}     # gear-rate = mass ratio (turns per crank-turn)
print("\ngear-rates (turns per crank-turn = mass/ref):")
for n in CELLS: print(f"  {n:10s} rate={rate[n]:.3f}")

RES = ["scaffold", "antiquity", "computing", "windows", "liverpool"]   # de-lensed (resolvable) cells
def states(theta, sigma=+1):
    return {n: phase_state(clump[n], sigma * rate[n] * theta) for n in RES}

def pair_sims(st):
    out = []
    for i in range(len(RES)):
        for j in range(i + 1, len(RES)):
            out.append(hdc.klein4_similarity(st[RES[i]], st[RES[j]]))
    return out

print("\n=== FORWARD crank on the REAL D=10000 store ===")
print("Theta(turn) | mean pairwise sim | min..max | massless-center read (max sim of all-bundle to any clump)")
rows = []
for k in range(0, 13):
    theta = k / 12.0
    st = states(theta)
    ps = pair_sims(st)
    mean_s = sum(ps) / len(ps)
    B = cs.bundle_odd([st[n] for n in RES])           # the 'center' = bundle of all clump-states
    center = max(hdc.klein4_similarity(B, st[n]) for n in RES)
    rows.append((theta, mean_s, center))
    print(f"   {theta:.3f}    |     {mean_s:+.3f}       | {min(ps):+.2f}..{max(ps):+.2f} |  {center:.3f}")

syz = max(rows, key=lambda r: r[1]); spr = min(rows, key=lambda r: r[1])
print(f"\nsyzygy (max mean pairwise sim): Theta={syz[0]:.3f}  mean={syz[1]:.3f}  (clumps in-phase = aligned)")
print(f"max spread (min mean sim):      Theta={spr[0]:.3f}  mean={spr[1]:.3f}")
cmin = min(rows, key=lambda r: r[2]); cmax = max(rows, key=lambda r: r[2])
print(f"massless center: bundle->clump max-sim ranges {cmin[2]:.3f} (diffuse/massless @Theta={cmin[0]:.2f}) .. {cmax[2]:.3f} (coherent @Theta={cmax[0]:.2f})")

# arrangement reconfigures (not rigid): does a specific pair's sim move across the crank?
pair_track = [hdc.klein4_similarity(states(k/12.0)["scaffold"], states(k/12.0)["computing"]) for k in range(13)]
print(f"\narrangement reconfigures? sim(scaffold,computing) range over crank: "
      f"{min(pair_track):+.2f}..{max(pair_track):+.2f}  span={max(pair_track)-min(pair_track):.2f} "
      f"({'RECONFIGURES' if max(pair_track)-min(pair_track) > 0.1 else 'rigid'})")

# backward crank mirrors
print("\n=== BACKWARD crank (sigma=-1) mirrors forward ===")
for k in [3, 6, 9]:
    th = k / 12.0
    f = states(th, +1)["scaffold"]; b = states(th, -1)["scaffold"]
    # forward phase = +rate*th ; backward = -rate*th ; their sim to the unmoved base should match
    sf = hdc.klein4_similarity(clump["scaffold"], f); sb = hdc.klein4_similarity(clump["scaffold"], b)
    print(f"  Theta={th:.3f}: sim(base,fwd)={sf:+.3f}  sim(base,bwd)={sb:+.3f}  (equal = mirror)")

# dark-star: turns-per-crank and Nyquist sampling each cell needs
print("\n=== DARK-STAR: phase-rate horizon on the real store ===")
print("  cell        turns/crank   Nyquist samples needed (2x rate)")
for n in CELLS:
    print(f"  {n:10s}    {rate[n]:5.2f}        {max(1, int(round(2*rate[n]))):3d}")
print("  the hub races 3.26 turns/crank -> needs the most samples to resolve; at any fixed")
print("  sampling budget it aliases FIRST = unresolvable = the dark-star (de-lensing target).")
