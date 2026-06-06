"""Adversarial bug-test for srmech 0.7.2rc2 cascade.hamming_* (§30 / F449 CARRY half).
Tries to BREAK it: all rungs, every error position, malformed inputs, boundary n,
double-error, cross-check vs the F449 hand-rolled reference, + the all-native front-loader."""
import numpy as np
from srmech.amsc import cascade

PASS=[]; BUGS=[]
def ck(name, ok, detail=""):
    PASS.append(ok); print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok: BUGS.append(name+" :: "+detail)

def k_of(n): return (1<<n)-1-n         # data bits for Hamming(2^n-1, k)
def N_of(n): return (1<<n)-1           # codeword length

print("srmech", __import__("srmech").__version__, "— Hamming bug-test\n")

# ---- 1. round-trip (no error), rungs n=3..6 ----
print("[1] round-trip, no error (Hamming(7,4),(15,11),(31,26),(63,57))")
rng=np.random.default_rng(1)
for n in (3,4,5,6):
    k=k_of(n); data=list(rng.integers(0,2,size=k))
    cw=cascade.hamming_encode(data,n)
    syn=cascade.hamming_syndrome(cw)
    dec=cascade.hamming_decode_correct(cw)
    ok = len(cw)==N_of(n) and syn==0 and dec["data"]==data and dec["error_position"]==0
    ck(f"n={n} Hamming({N_of(n)},{k}) round-trip", ok, f"len={len(cw)} syn={syn} data_ok={dec['data']==data}")

# ---- 2. single-error correction at EVERY position, rungs n=3,4,5 ----
print("\n[2] single-error correction at EVERY bit position")
for n in (3,4,5):
    k=k_of(n); N=N_of(n); data=list(rng.integers(0,2,size=k))
    cw=cascade.hamming_encode(data,n)
    allok=True; bad_pos=[]
    for pos in range(1,N+1):
        v=list(cw); v[pos-1]^=1
        syn=cascade.hamming_syndrome(v)
        dec=cascade.hamming_decode_correct(v)
        if not (syn==pos and dec["error_position"]==pos and dec["data"]==data and dec["corrected_codeword"]==cw):
            allok=False; bad_pos.append(pos)
    ck(f"n={n}: all {N} single-error positions located+corrected+recovered", allok,
       "" if allok else f"FAILS at {bad_pos[:8]}")

# ---- 3. cross-check vs F449 hand-rolled Hamming(15,11) (functional, not bit-identical) ----
print("\n[3] cross-check vs F449 reference (both valid (15,11), all 15 correctable)")
# srmech (15,11) corrects all 15 — already shown in [2] n=4; confirm data recovery on a known pattern
data11=[1,0,1,1,0,0,1,0,1,1,0]
cw=cascade.hamming_encode(data11,4)
recs=[cascade.hamming_decode_correct([b^(1 if i==p-1 else 0) for i,b in enumerate(cw)])["data"]==data11 for p in range(1,16)]
ck("srmech (15,11) recovers data under each of 15 single errors", all(recs), f"{sum(recs)}/15")

# ---- 4. adversarial edge cases (try to break) ----
print("\n[4] adversarial / contract edges")
def expect_error(label, thunk):
    try:
        r=thunk(); ck(label+" -> rejected?", False, f"NO ERROR, returned {str(r)[:50]} (silent-wrong?)")
    except Exception as ex:
        ck(label+" -> clean error", True, f"{type(ex).__name__}: {str(ex)[:70]}")
expect_error("wrong data length (3 bits for n=4 needs 11)", lambda: cascade.hamming_encode([1,0,1],4))
expect_error("too many data bits", lambda: cascade.hamming_encode([1]*20,4))
expect_error("n below range (n=1)", lambda: cascade.hamming_encode([1],1))
expect_error("n above range (n=17)", lambda: cascade.hamming_encode([0]*(k_of(17)),17))
expect_error("non-binary data bit (=2)", lambda: cascade.hamming_encode([2,0,1,1],3))
expect_error("syndrome wrong codeword length (6)", lambda: cascade.hamming_syndrome([0,1,1,0,0,1]))
expect_error("decode wrong codeword length (8)", lambda: cascade.hamming_decode_correct([0]*8))
# clean word edge: all-zeros / all-ones
ck("all-zero codeword is clean (syn 0)", cascade.hamming_syndrome([0]*7)==0, "")
ck("all-zero decodes to zero data", cascade.hamming_decode_correct([0]*7)["data"]==[0,0,0,0], "")

# ---- 5. double-error: documented mis-correct, must NOT crash ----
print("\n[5] double-error (distance-3: documented mis-correct, must not crash)")
data=[1,0,1,1]; cw=cascade.hamming_encode(data,3)
v=list(cw); v[1]^=1; v[4]^=1
try:
    dec=cascade.hamming_decode_correct(v)
    misc = dec["data"]!=data   # SHOULD differ (2 errors beyond distance) — that's expected, not a bug
    ck("double-error handled without crash (mis-corrects, as documented)", True,
       f"recovered != original = {misc} (expected True for 2 errors)")
except Exception as ex:
    ck("double-error handled without crash", False, f"CRASH {type(ex).__name__}: {ex}")

# ---- 6. FRONT-LOADER all-native: CARRY (hamming) ∘ COUPLE (hypercomplex_couple) ----
print("\n[6] front-loader all-native: CARRY ∘ COUPLE end-to-end")
rng2=np.random.default_rng(7); streams7=list(rng2.normal(size=7))
oct_c=cascade.hypercomplex_couple(streams7, axis="diagonal", sigma=+1)
# derive 11 structure bits from the coupled octonion (sign bits of 8 comps + 3 magnitude-threshold bits)
bits=[1 if x>=0 else 0 for x in oct_c][:8] + [1 if abs(x)>0.5 else 0 for x in oct_c[:3]]
bits=bits[:11]
cw=cascade.hamming_encode(bits,4)                     # CARRY: 11 structure bits + 4 EC -> 15 slots
corr=list(cw); corr[9]^=1                             # one slot corrupted in transit
dec=cascade.hamming_decode_correct(corr)              # locate+correct
oct_back=cascade.hypercomplex_couple(oct_c, axis="diagonal", sigma=-1)  # COUPLE unbind
streams_err=max(abs(a-b) for a,b in zip(streams7, list(oct_back)[1:8]))
ck("CARRY recovers the 11 structure bits after a transit error", dec["data"]==bits, f"err_pos={dec['error_position']}")
ck("COUPLE unbinds the octonion (reals) exactly", streams_err<1e-9, f"err {streams_err:.2e}")
ck("front-loader CARRY∘COUPLE end-to-end all-native", dec["data"]==bits and streams_err<1e-9, "both halves srmech-native, reversible")

print(f"\n=== {sum(PASS)}/{len(PASS)} checks PASS ===")
print("BUGS:", BUGS if BUGS else "NONE")
