"""rc28 ASK verification: (1) byte/glyph C1 enc graduation (F899/§68/§69); (2) RBSLMInferenceSubstrate runs
on byte/glyph; (3) word-hash dual kept; (4) full eigensolver gap (>256); (5) sim_k4_batch hot-path; (6) the
4-layer pieces present (cd_mult, sedenion_register)."""
import inspect
from srmech.rbs_lm import substrate as S, RBSLMInferenceSubstrate, sim_k4_batch
from srmech.amsc import hdc, cascade
def fl(q): return q.as_float() if hasattr(q,"as_float") else q
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
D=8192
P=lambda ok: "PASS" if ok else "**FAIL**"

# (1) byte/glyph enc is the default + graded similarity (vs word-hash chance ~0.25)
cs=S.ContextSubstrate(D=D, hex_chars=16)
mode=getattr(cs,"enc_mode","?")
bg=sim(cs.enc("cat"), cs.enc("cot")); bg2=sim(cs.enc("walk"), cs.enc("walked")); un=sim(cs.enc("cat"), cs.enc("dog"))
print(f"(1) byte/glyph default enc: enc_mode={mode!r} -> {P(mode=='byteglyph')}")
print(f"    graded similarity: cat/cot={bg:.3f}, walk/walked={bg2:.3f}, cat/dog={un:.3f}  -> {P(bg>0.45 and un<0.35)}")

# (2) RBSLMInferenceSubstrate now runs on byte/glyph by default
params={"substrate":{"D":D,"token_seed_hex_chars":16},
        "inference":{"instrument":{"operating_k":2,"operating_temperature":0.0,"memory_capacity":256,"default_max_tokens":4,"learn_seed":1}}}
sub=RBSLMInferenceSubstrate.from_params(params)
submode=getattr(sub.ctx,"enc_mode","?")
sub.learn("the cat sat on the mat the cat ran".split()); gen=sub.infer(["the","cat"],max_tokens=3)
print(f"(2) RBSLMInferenceSubstrate.ctx.enc_mode={submode!r}; learn+infer -> {gen}  -> {P(submode=='byteglyph' and len(gen)>2)}")

# (3) word-hash dual still available (the explicit fast atom-mode)
try:
    cw=S.ContextSubstrate(D=D, hex_chars=16, enc_mode="wordhash")
    wh=sim(cw.enc("cat"), cw.enc("cot"))
    print(f"(3) word-hash dual kept (enc_mode='wordhash'): cat/cot={wh:.3f} (~chance) -> {P(wh<0.35)}")
except Exception as e:
    print(f"(3) word-hash dual: **FAIL** {type(e).__name__}: {e}")

# (4) full eigensolver gap (>256): symmetric eigendecompose on n=300
from srmech.amsc import laplacian as La
eigops=[n for n in dir(La) if "eig" in n.lower()]
print(f"(4) eig surface: {eigops}")
n=300
# build a simple symmetric tridiagonal matrix as a Mat (diag 2, off -1)
from srmech.amsc.mat import Mat
rows=[[ (2.0 if i==j else (-1.0 if (i-j) in (-1,1) else 0.0)) for j in range(n)] for i in range(n)]
M=Mat(rows)
try:
    fn = getattr(La,"symmetric_eigendecompose",None) or getattr(La,"mat_eigvals",None) or getattr(La,"jacobi_eigvals",None)
    res=fn(M)
    vals=res[0] if isinstance(res,tuple) else res
    nv=len(vals) if hasattr(vals,"__len__") else "?"
    print(f"    {fn.__name__}(n={n}) -> {nv} eigenvalues  -> {P(nv==n)}  (>256 bound: gap closed)")
except Exception as e:
    print(f"    n={n} eigensolve: **FAIL** {type(e).__name__}: {str(e)[:120]}")

# (5) sim_k4_batch hot-path: does it return floats now?
out=sim_k4_batch(cs.enc("cat"), [cs.enc("cot"), cs.enc("dog")])
t=type(out[0]).__name__
print(f"(5) sim_k4_batch return elem type: {t}  -> {P(t in ('float','Q'))} (float = the hot-path float-batch we asked)")

# (6) the other 3 layers present
print(f"(6) layers present: cd_mult={P(hasattr(cascade,'cd_mult'))}, sedenion_register={P(hasattr(cascade,'sedenion_register'))}, encode_word_byteglyph={P(hasattr(S,'encode_word_byteglyph'))}")
from srmech.rbs_lm import substrate as S, sim_k4_batch
from srmech.amsc import hdc, cascade, laplacian as La
from srmech.amsc.mat import Mat
P=lambda ok:"PASS" if ok else "**FAIL**"
cs=S.ContextSubstrate(D=8192, hex_chars=16)

# (4) full eigensolver gap: n=300 symmetric tridiagonal (> old n<=256 Jacobi bound)
for n in (300, 512):
    rows=[[ (2.0 if i==j else (-1.0 if (i-j) in (-1,1) else 0.0)) for j in range(n)] for i in range(n)]
    M=Mat.from_rows(rows)
    try:
        vals,vecs=La.symmetric_eigendecompose(M)
        nv=len(vals)
        # tridiag(2,-1) eigenvalues are 2-2cos(k*pi/(n+1)) in [0,4]; check count + range
        lo=min(float(x) for x in vals); hi=max(float(x) for x in vals)
        print(f"(4) symmetric_eigendecompose(n={n}) -> {nv} eigenvalues in [{lo:.3f},{hi:.3f}]  -> {P(nv==n and 0<=lo and hi<=4.01)}")
    except Exception as e:
        print(f"(4) n={n}: **FAIL** {type(e).__name__}: {str(e)[:140]}")

# (5) sim_k4_batch hot-path return type
out=sim_k4_batch(cs.enc("cat"), [cs.enc("cot"), cs.enc("dog")])
t=type(out[0]).__name__
print(f"(5) sim_k4_batch elem type: {t} (float=native float-batch hot-path; Q=still object) -> {P(t=='float')}")

# (6) the 4 layers + the byte/glyph object fn
print(f"(6) layers: cd_mult={P(hasattr(cascade,'cd_mult'))} sedenion_register={P(hasattr(cascade,'sedenion_register'))} "
      f"encode_word_byteglyph={P(hasattr(S,'encode_word_byteglyph'))} mat_eigvals={P(hasattr(La,'mat_eigvals'))}")
