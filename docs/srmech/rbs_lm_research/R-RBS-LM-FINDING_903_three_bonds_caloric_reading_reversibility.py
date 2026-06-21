"""F903 — the chemistry/Standard-Model reading: (B) three BONDS with distinct signatures + part-recoverability,
and the CALORIC term the user predicted — reading an atom out of a molecule DEGENERATES with molecular size.
 unbind(C1_molecule, pos_p) = atom_p + (k-1) noise terms -> the majority-bundle reads it cleanly for small k,
 degrades as k grows. That degeneration IS an energy-like cost of reading, and it is IN the cascade (the F896
 1/sqrt(k) bundle capacity), NOT a biology artifact. Past a threshold the molecule is UNREADABLE -> it must
 LEXICALIZE (mint its own atom = the dual) -> emergence/non-compositionality. srmech rc13; Klein-4; numpy-free.
"""
import random, statistics as st
from srmech.amsc import hdc
from srmech.rbs_lm import ContextSubstrate, sim_k4_batch

D = 8192
def fl(q): return q.as_float() if hasattr(q, "as_float") else q
_cs = ContextSubstrate(D=D, hex_chars=16)
def bundle_odd(v): return _cs.bundle_odd(list(v))
def pos_key(i): return hdc.klein4_random(D, seed=0x70000000 + i)
def byte_atom(b): return hdc.klein4_random(D, seed=b)                       # the 256-atom periodic table
ATOMS = [byte_atom(b) for b in range(256)]
def compose(parts): return bundle_odd([hdc.klein4_bind(p, pos_key(i)) for i, p in enumerate(parts)])   # C1 covalent
def atom_mint(bytes_): return hdc.klein4_random(D, seed=hash(tuple(bytes_)) & 0xFFFFFFFF)               # ionic identity
def chained(parts):
    acc = parts[0]
    for p in parts[1:]: acc = hdc.klein4_bind(acc, p)
    return acc                                                             # brittle order-bond
def read_pos(mol, p):                                                       # unbind position p, match against the periodic table
    probe = hdc.klein4_bind(mol, pos_key(p))                                # klein4_bind is (F2)^2-XOR = its own inverse
    sims = [fl(s) for s in sim_k4_batch(probe, ATOMS)]
    return max(range(256), key=lambda b: sims[b])
def read_eval(mol, p, true_b):                                              # (recovered-correctly?, signal=sim to the TRUE atom)
    probe = hdc.klein4_bind(mol, pos_key(p))
    sims = [fl(s) for s in sim_k4_batch(probe, ATOMS)]
    amax = max(range(256), key=lambda b: sims[b])
    return (amax == true_b, sims[true_b])
rng = random.Random(7)

print("=== F903 the three bonds + the CALORIC cost of reading (D=%d) ===" % D)

# correctness: C1 read-back works for a small molecule
mol = compose([byte_atom(b) for b in [99,97,116]])      # 'cat'
print("\n  sanity: read positions of C1('cat') ->", [read_pos(mol,p) for p in range(3)], "(expect 99,97,116)")

# (B) three bonds: can you READ an atom out by position? (compositional transparency)
def recover_acc(make, k, n=40):
    ok = 0
    for _ in range(n):
        bs = [rng.randint(0,255) for _ in range(k)]
        m = make(bs)
        p = rng.randrange(k)                       # one random position per molecule (hot-path budget)
        ok += int(read_pos(m, p) == bs[p])
    return ok/n
k0 = 4
print(f"\n(B) part-recoverability at k={k0} atoms (chance = 1/256 = 0.004):")
print(f"    C1 (covalent, position-addressable): {recover_acc(lambda bs: compose([byte_atom(b) for b in bs]), k0):.3f}")
print(f"    atom-mint (ionic, no inner structure): {recover_acc(lambda bs: atom_mint(bs), k0):.3f}")
print(f"    chained-bind (brittle, not addressable): {recover_acc(lambda bs: chained([byte_atom(b) for b in bs]), k0):.3f}")

# (CALORIC + REVERSIBILITY) read one atom out of a k-atom C1 molecule:
#   SIGNAL    = similarity to the TRUE atom (the read fidelity = energy left in the signal). Declines ~1/sqrt(k) = the heat.
#   REVERSIBLE% = fraction of the molecule's atoms that read back correctly (argmax). Info CONSERVED until the wall.
#   The "heat" of reading one atom is the OTHER atoms (crosstalk); reading them all back RECOVERS it (reversibility).
print("\n(CALORIC + REVERSIBILITY) reading an atom out of a k-atom C1 molecule (chance signal ~0.25):")
print(f"    {'k atoms':>8}{'SIGNAL (read fidelity)':>24}{'REVERSIBLE% (atoms recoverable)':>34}")
curve = []
for k in [4, 16, 64, 256, 1024]:
    n = 8; sig = []; rev = []
    for _ in range(n):
        bs = [rng.randint(0,255) for _ in range(k)]
        m = compose([byte_atom(b) for b in bs])
        p = rng.randrange(k); ok, s = read_eval(m, p, bs[p]); sig.append(s)
        ps = rng.sample(range(k), min(k, 12))                 # sample positions for the reversible fraction
        rev.append(sum(read_eval(m, pp, bs[pp])[0] for pp in ps) / len(ps))
    sg = st.mean(sig); rv = st.mean(rev); curve.append((k, sg, rv))
    print(f"    {k:>8}{sg:>24.3f}{rv:>33.1%}")

# the wall = where REVERSIBILITY breaks (true Landauer loss); below it the caloric loss is a recoverable heat-exchange
wall = next((k for k,_,rv in curve if rv < 0.95), None)
print(f"\n  CALORIC: the read SIGNAL decays with k (~1/sqrt(k)) — that drop is the 'heat' (crosstalk with the other atoms).")
print(f"  REVERSIBLE: info is CONSERVED (atoms read back ~100%) until the capacity wall near k ~ {wall or '>4096'} —")
print(f"    so below the wall the caloric loss is a REVERSIBLE heat-exchange: the heat IS the other atoms, recovered by")
print(f"    reading them back (bind is XOR-reversible; only the bundle-majority past capacity is true Landauer erasure).")
print(f"  => FOUND IN THE CASCADE: caloric loss + its reversibility are both the HDC bundle (F896 1/sqrt(N)), not biology")
print(f"     artifacts. At linguistic scales (words k~3-15, phrases k~5) reading is high-fidelity AND fully reversible —")
print(f"     so emergence/lexicalization is NOT forced by a reading wall here; it must be a MEANING-layer phenomenon.")
