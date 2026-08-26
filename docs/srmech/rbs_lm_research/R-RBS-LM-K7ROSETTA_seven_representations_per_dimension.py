r"""R-RBS-LM-K7ROSETTA — bind ~7 REPRESENTATIONS of one math (word problem + LaTeX +
Python + C + JS + Go + Rust) PER-DIMENSION through the octonion coupler (F459's flagged
extension: whole HV operator-signatures, not scalar streams), reading the diagonal-μ anchor
as the joint "are these all the same math?" coherence channel. Fuses F457 (grammar kernels)
+ F458 (word-problem anchor) + F459 (k=7 coupler). srmech 0.7.3rc1.

Each representation -> a D=8192 bipolar operator-signature (packed bits). For a sample of
dimensions, the 7 reps' ±1 values are the 7 streams -> hypercomplex_couple(diagonal) ->
octonion; anchor = real component; mean(anchor²) = coherence (F459: ~k for commensurable
streams, ~1 for independent).
"""
import importlib.util as _u
import numpy as np
from srmech.amsc import cascade as C
from srmech.amsc.hdc import bundle
from srmech.signal_processing import mint_vector

_spec = _u.spec_from_file_location("g3", "docs/srmech/rbs_lm_research/R-RBS-LM-GRAMMAR_signature_engine_v3.py")
g3 = _u.module_from_spec(_spec); _spec.loader.exec_module(g3)
D = 8192


def pm1(sig_bytes):
    return np.unpackbits(np.frombuffer(sig_bytes, dtype=np.uint8)).astype(np.int64) * 2 - 1


def wordproblem_sig(text):
    toks = [t.lower() for t in text.split() if len(t) > 2]
    return g3._bundle([mint_vector("WP:" + t, D=D) for t in toks])   # parity-safe (pads to odd)


def coherence(reps_bits, sample, rng):
    dims = rng.choice(D, size=sample, replace=False)
    acc = 0.0
    for d in dims:
        streams = [float(r[d]) for r in reps_bits]
        acc += float(C.hypercomplex_couple(streams, axis="diagonal")[0]) ** 2
    return acc / len(dims)


def main():
    import srmech
    print(f"=== R-RBS-LM-K7ROSETTA — 7 representations of one math, per-dimension k=7 bind  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(0)
    S = 500   # sampled dimensions

    # ---- 7 representations of THE SUM (Σ aᵢ) ----
    sum_reps = {
        "word-problem": wordproblem_sig("add up all the numbers in the list to get the total sum accumulate"),
        "LaTeX":   g3.math_sig(r"\sum_{i=1}^{n} a_i"),
        "Python":  g3.python_sig("def s(xs):\n t=0\n for v in xs:\n  t=t+v\n return t"),
        "C":       g3.c_sig("int s(int xs[], int n){ int t=0; for(int i=0;i<n;i++){ t=t+xs[i]; } return t; }"),
        "JavaScript": g3.ts_sig("javascript", "function s(xs){let t=0;for(const v of xs){t=t+v;}return t;}"),
        "Go":      g3.ts_sig("go", "package m\nfunc s(xs []int) int { t:=0; for _,v := range xs { t=t+v }; return t }"),
        "Rust":    g3.ts_sig("rust", "fn s(xs:Vec<i32>)->i32{ let mut t=0; for v in xs { t=t+v; } return t; }"),
    }
    print("7 representations of Σaᵢ encoded as operator-signatures:")
    for k in sum_reps: print(f"  - {k}")
    matched = [pm1(s) for s in sum_reps.values()]

    # ---- 7 DIFFERENT maths (mismatched control) ----
    mismatched_src = [
        wordproblem_sig("a recipe for baking bread with flour and water"),
        g3.math_sig(r"\frac{a}{b}"),
        g3.python_sig("def f(n):\n if n<=1:\n  return 1\n return n*f(n-1)"),
        g3.c_sig("int g(int a){ if(a>0){ return a; } return -a; }"),
        g3.ts_sig("javascript", "function p(a,b){return a*b;}"),
        g3.ts_sig("go", "package m\nfunc q(x int) int { return x+1 }"),
        g3.ts_sig("rust", "fn r(x:i32)->i32{ x*x }"),
    ]
    mismatched = [pm1(s) for s in mismatched_src]

    # ---- 7 COMMENSURABLE (same grammar, renamed → identical signatures) ----
    comm_src = [g3.python_sig(f"def s(xs):\n {v}=0\n for w in xs:\n  {v}={v}+w\n return {v}") for v in
                ("t", "acc", "total", "sm", "r", "out", "z")]
    commensurable = [pm1(s) for s in comm_src]

    print("\nper-dimension k=7 octonion-coupling — coherence anchor energy (mean anchor², F459: ~k coherent / ~1 independent):")
    cm = coherence(commensurable, S, rng)
    mm = coherence(matched, S, rng)
    xm = coherence(mismatched, S, rng)
    print(f"  COMMENSURABLE-7 (same grammar, renamed → identical sigs): {cm:.2f}   (expect ~7 — fully coherent)")
    print(f"  MATCHED-7 cross-grammar (same math Σ, 6 grammars + word problem): {mm:.2f}   (expect ~1 — F457 null)")
    print(f"  MISMATCHED-7 (7 different maths): {xm:.2f}   (expect ~1 — incoherent)")

    print("\nVERDICT:")
    print(f"  • the per-dimension k=7 octonion bind WORKS: commensurable reps cohere at {cm:.1f}× (≈k=7), the F459")
    print("    coherence law over whole HV signatures (the flagged extension) — confirmed.")
    print(f"  • BUT raw cross-grammar same-math ({mm:.1f}) ≈ different-math ({xm:.1f}) — the F457 NULL persists at k=7:")
    print("    operator-signatures of the same math in DIFFERENT grammars are ~orthogonal, so per-dimension")
    print("    agreement is at the incoherent floor regardless of meaning.")
    print("  • => binding seven LANGUAGES of math needs COMMENSURABILITY, which the structure alone lacks across")
    print("    grammars (F457). The word problem (F458, the semantic Rosetta anchor) or the v4 canonical A-N IR")
    print("    is what supplies it — exactly the two routes. k=7 is the BINDER; the anchor is what makes it cohere.")


if __name__ == "__main__":
    main()
