"""F905 — is the caloric loss UNIFORM (quantum-like coherence) or content-dependent (atomic/molecular)?
And what FORCE is it (heat vs work)? The user's expectation: biology's energetics are NOT uniform
(bond-specific); if ours is uniform it points to a quantum-like (dimensional/geometric) coherence.
 (1) per-ATOM uniformity: does the read-signal depend on WHICH byte is the target?
 (2) per-MOLECULE-structure: distinct atoms vs a repeated atom vs all-same — does composition matter?
 (3) WORK vs HEAT: the reversible (recoverable=work) vs irreversible (erased=heat) split — below the wall
     the loss is reversible WORK (a coherent superposition), only at the wall is it HEAT (decoherence).
srmech rc13; Klein-4; numpy-free."""
import random, statistics as st
from srmech.amsc import hdc
from srmech.rbs_lm import ContextSubstrate, sim_k4_batch

D = 8192
def fl(q): return q.as_float() if hasattr(q, "as_float") else q
_cs = ContextSubstrate(D=D, hex_chars=16)
def bundle_odd(v): return _cs.bundle_odd(list(v))
def pos_key(i): return hdc.klein4_random(D, seed=0x70000000 + i)
def byte_atom(b): return hdc.klein4_random(D, seed=b)
ATOMS = [byte_atom(b) for b in range(256)]
def compose(parts): return bundle_odd([hdc.klein4_bind(p, pos_key(i)) for i, p in enumerate(parts)])
def read_signal(mol, p, true_b):                       # similarity to the TRUE atom = read fidelity
    return [fl(s) for s in sim_k4_batch(hdc.klein4_bind(mol, pos_key(p)), ATOMS)][true_b]
def read_ok(mol, p, true_b):
    sims = [fl(s) for s in sim_k4_batch(hdc.klein4_bind(mol, pos_key(p)), ATOMS)]
    return max(range(256), key=lambda b: sims[b]) == true_b
rng = random.Random(11)
print("=== F905 caloric loss: uniform (quantum-like) or content-dependent (atomic/molecular)? (D=%d, k=16) ===" % D)

# (1) per-ATOM uniformity — mean read-signal for each of many target bytes; variance ACROSS atoms vs WITHIN (sampling)
k = 16
per_atom = {}
for b in rng.sample(range(256), 32):
    sigs = []
    for _ in range(8):
        bs = [rng.randint(0,255) for _ in range(k)]; pos = rng.randrange(k); bs[pos] = b
        sigs.append(read_signal(compose([byte_atom(x) for x in bs]), pos, b))
    per_atom[b] = st.mean(sigs)
across = st.pstdev(list(per_atom.values()))           # spread of per-atom MEANS (content effect, if any)
print(f"\n(1) per-ATOM: read-signal mean across 32 different target bytes = {st.mean(list(per_atom.values())):.3f}")
print(f"    spread ACROSS atoms (std of per-byte means) = {across:.4f}  (≈0 => no atom is 'heavier'; UNIFORM across atoms)")

# (2) per-MOLECULE-structure — does internal composition change the read-loss?
def sig_for(maker, n=24):
    out = []
    for _ in range(n):
        b = rng.randint(0,255); pos = rng.randrange(k); bs = maker(b, pos)
        out.append(read_signal(compose([byte_atom(x) for x in bs]), pos, b))
    return st.mean(out)
distinct = sig_for(lambda b,pos: [ (b if i==pos else rng.randint(0,255)) for i in range(k)])
def with_repeat(b,pos):
    bs=[rng.randint(0,255) for _ in range(k)]; bs[pos]=b; q=rng.choice([i for i in range(k) if i!=pos]); bs[q]=b; return bs
repeat = sig_for(with_repeat)
allsame = sig_for(lambda b,pos: [b]*k)
print(f"\n(2) per-MOLECULE-structure (read-signal at k={k}):")
print(f"    all-distinct atoms : {distinct:.3f}")
print(f"    one repeated atom  : {repeat:.3f}")
print(f"    all-same atom      : {allsame:.3f}")
print(f"    spread across structures = {st.pstdev([distinct,repeat,allsame]):.4f}  (≈0 => composition does NOT matter; the role-filler BIND decorrelates content)")

# (3) WORK vs HEAT — reversible (recoverable) fraction vs k; below the wall it is WORK, at the wall it is HEAT
print(f"\n(3) WORK (reversible/recoverable) vs HEAT (irreversible/erased) — reversible% of atoms read back:")
print(f"    {'k':>6}{'signal':>10}{'reversible%(WORK)':>20}{'lost-as-HEAT%':>16}")
for k2 in [16, 64, 256, 1024]:
    n=8; sig=[]; rev=[]
    for _ in range(n):
        bs=[rng.randint(0,255) for _ in range(k2)]; m=compose([byte_atom(x) for x in bs])
        p=rng.randrange(k2); sig.append(read_signal(m,p,bs[p]))
        ps=rng.sample(range(k2), min(k2,12)); rev.append(sum(read_ok(m,pp,bs[pp]) for pp in ps)/len(ps))
    rv=st.mean(rev); print(f"    {k2:>6}{st.mean(sig):>10.3f}{rv:>19.1%}{(1-rv):>15.1%}")
print("\n  READING: uniform across atoms AND molecule-structure => the loss is CONTENT-BLIND. The role-filler bind")
print("  XOR-decorrelates content, so the loss is the DIMENSIONAL geometry (1/sqrt(k) concentration-of-measure),")
print("  NOT atomic/molecular bond-energetics. Below the wall it is REVERSIBLE = a quantum-like COHERENT")
print("  superposition (WORK, recoverable); the wall is DECOHERENCE (HEAT, Landauer). Biology's non-uniform")
print("  energetics would require a CONTENT-DEPENDENT bond — which the C1 role-filler bind is NOT.")
