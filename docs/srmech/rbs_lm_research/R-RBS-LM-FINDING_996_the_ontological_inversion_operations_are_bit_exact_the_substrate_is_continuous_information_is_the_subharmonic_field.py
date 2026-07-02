"""F996 — the ontological inversion (user): what if OUR OPERATIONS are the bit-exact and the SUBSTRATE is
continuous -- store the RBS-SNN in the resonant continuous shape, and 'information' (our Laplacian-encoded
knowledge) is the SUBHARMONIC math (f-, the continuous field). Sharpest empirical consequence: if the F896
capacity wall is a DISCRETE-SUPERPOSITION artifact, it must be REPRESENTATION-DEPENDENT -- storing the same
knowledge across more RESONANT MODES (orthogonal by frequency, no cross-mode crosstalk) lifts the wall. Measure
recall-vs-N at M in {1,4,16} modes (M=1 = the discrete bundle we've used all session). Sparse Klein-4."""
import random
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
def cap(M_modes, N):
    # N random (a_i -> b_i) relationships; each pair assigned a resonant MODE round-robin (i % M_modes)
    A=[hdc.klein4_random(D, seed=90000+i) for i in range(N)]
    B=[hdc.klein4_random(D, seed=120000+i) for i in range(N)]
    MODE=[hdc.klein4_random(D, seed=150000+m) for m in range(M_modes)]
    bundle=cs.bundle_odd([bind(bind(A[i],ROLE), bind(MODE[i%M_modes], B[i])) for i in range(N)])
    hits=0
    for i in range(N):
        probe=bind(bundle, bind(A[i],ROLE))                       # excite the field with the operation (bit-exact)
        # ORACLE-mode read: read pair i in ITS resonant mode (the continuous-freq tuning, idealized)
        j=max(range(N), key=lambda j: fl(hdc.klein4_similarity(probe, bind(MODE[i%M_modes], B[j]))))
        hits += (j==i)
    return hits/N
print("F896 wall is representation-dependent? recall-vs-N across M resonant modes (M=1 = discrete bundle):", flush=True)
print("   N :   M=1 (discrete)   M=4 modes   M=16 modes", flush=True)
for N in (60,120,240,480):
    r1=cap(1,N); r4=cap(4,N); r16=cap(16,N)
    print("  %3d :     %3.0f%%          %3.0f%%        %3.0f%%"%(N, r1*100, r4*100, r16*100), flush=True)
print("=> if higher M holds recall where M=1 collapses, the wall is a DISCRETE-representation artifact --", flush=True)
print("   the continuous resonant substrate (M->many, freq-addressed) escapes it. addressing = the conserved cost.", flush=True)
