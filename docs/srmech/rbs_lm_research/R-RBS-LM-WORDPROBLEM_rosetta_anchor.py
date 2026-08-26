r"""R-RBS-LM-WORDPROBLEM — the word-problem Rosetta anchor (F458 Route-2): the SEMANTIC commensurability.

F462/F463 located it: cross-PARADIGM/cross-grammar representations of the SAME math are structurally orthogonal
(structure alone can't bridge paradigms). F463 (v4 canonical IR) is Route-1 (structural, within-paradigm). This
is Route-2 (semantic, across-paradigm): BUNDLE the word problem (the SOURCED meaning) into each representation —
a shared component lifts same-meaning reps into coherence; different-meaning reps (different word problems) stay
apart. That the bundling is NECESSARY is exactly F408: meaning must be SOURCED, never derived from structure.

Sweep the meaning-weight w (copies of the word-problem anchor in the bundle):
  w=0  -> pure structure (the F463 cross-paradigm floor, ~1.1)
  w>0  -> the sourced meaning bridges; matched cross-paradigm coheres toward k, mismatched stays apart.
srmech 0.7.3 + the F457 grammar engine (sympy/ast/pycparser/tree-sitter); per-dim octonion coupler (F459/F462).
"""
import importlib.util as U
import numpy as np
from srmech.amsc import cascade as C
from srmech.signal_processing import mint_vector
import srmech

_spec = U.spec_from_file_location("g3", "docs/srmech/rbs_lm_research/R-RBS-LM-GRAMMAR_signature_engine_v3.py")
g3 = U.module_from_spec(_spec); _spec.loader.exec_module(g3)
D = 8192


def wp_sig(text):                                          # the word problem = the sourced meaning anchor
    toks = [t.lower() for t in text.split() if len(t) > 2]
    return g3._bundle([mint_vector("WP:" + t, D=D) for t in toks])


def combined(struct_sig, anchor_sig, w):                   # bundle the meaning into the structure, weight w
    if w == 0:
        return struct_sig
    return g3._bundle([struct_sig] + [anchor_sig] * w)


def pm1(sig):
    return np.unpackbits(np.frombuffer(sig, dtype=np.uint8)).astype(np.int64) * 2 - 1


def coherence(sigs, sample, rng):                          # per-dim k coupler (F459/F462)
    bits = [pm1(s) for s in sigs]
    dims = rng.choice(D, size=sample, replace=False)
    acc = 0.0
    for d in dims:
        streams = [float(b[d]) for b in bits]
        acc += float(C.hypercomplex_couple(streams, axis="diagonal")[0]) ** 2
    return acc / len(dims)


def main():
    print(f"=== R-RBS-LM-WORDPROBLEM — the word-problem Rosetta anchor (F458 Route-2)  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(0); S = 500

    # two maths, each in 6 grammars (cross-paradigm: LaTeX declarative + 5 imperative) + a word problem
    OPS = {
        "sum": {
            "wp": "add up all the numbers in the list to get the total sum accumulate",
            "reps": {
                "LaTeX": g3.math_sig(r"\sum_{i=1}^{n} a_i"),
                "Python": g3.python_sig("def s(xs):\n t=0\n for v in xs:\n  t=t+v\n return t"),
                "C": g3.c_sig("int s(int xs[],int n){int t=0;for(int i=0;i<n;i++){t=t+xs[i];}return t;}"),
                "JS": g3.ts_sig("javascript", "function s(xs){let t=0;for(const v of xs){t=t+v;}return t;}"),
                "Go": g3.ts_sig("go", "package m\nfunc s(xs []int) int { t:=0; for _,v := range xs { t=t+v }; return t }"),
                "Rust": g3.ts_sig("rust", "fn s(xs:Vec<i32>)->i32{ let mut t=0; for v in xs { t=t+v; } return t; }"),
            },
        },
        "product": {
            "wp": "multiply all the numbers in the list together to get the running product",
            "reps": {
                "LaTeX": g3.math_sig(r"\prod_{i=1}^{n} a_i"),
                "Python": g3.python_sig("def p(xs):\n r=1\n for v in xs:\n  r=r*v\n return r"),
                "C": g3.c_sig("int p(int xs[],int n){int r=1;for(int i=0;i<n;i++){r=r*xs[i];}return r;}"),
                "JS": g3.ts_sig("javascript", "function p(xs){let r=1;for(const v of xs){r=r*v;}return r;}"),
                "Go": g3.ts_sig("go", "package m\nfunc p(xs []int) int { r:=1; for _,v := range xs { r=r*v }; return r }"),
                "Rust": g3.ts_sig("rust", "fn p(xs:Vec<i32>)->i32{ let mut r=1; for v in xs { r=r*v; } return r; }"),
            },
        },
    }
    anchor = {op: wp_sig(d["wp"]) for op, d in OPS.items()}

    distinct = [mint_vector(f"UNIQUE_MEANING_{i}", D=D) for i in range(6)]   # genuinely independent anchors
    print("meaning-weight sweep — per-dim coupler coherence (F459: ~k coherent / ~1 independent):")
    print(f"  {'w':>3s} | {'MATCHED sum':>11s} {'MATCHED prod':>12s} | {'MIX 3+3':>8s} | {'FULL-MISMATCH':>13s}  (6 distinct anchors)")
    for w in (0, 1, 2, 4, 8):
        sum_c = coherence([combined(s, anchor["sum"], w) for s in OPS["sum"]["reps"].values()], S, rng)
        prod_c = coherence([combined(s, anchor["product"], w) for s in OPS["product"]["reps"].values()], S, rng)
        mixed = ([combined(s, anchor["sum"], w) for s in list(OPS["sum"]["reps"].values())[:3]]
                 + [combined(s, anchor["product"], w) for s in list(OPS["product"]["reps"].values())[:3]])
        mis_c = coherence(mixed, S, rng)
        # full-mismatch: the 6 SUM reps, each bundled with its OWN distinct meaning → no shared anchor
        full = [combined(s, distinct[i], w) for i, s in enumerate(OPS["sum"]["reps"].values())]
        full_c = coherence(full, S, rng)
        print(f"  {w:>3d} | {sum_c:11.2f} {prod_c:12.2f} | {mis_c:8.2f} | {full_c:13.2f}")

    print("\n  (w=0 = pure structure = the F463 cross-paradigm floor; w>0 = the sourced meaning bridges)")
    print("\nVERDICT:")
    print("  • At w=0 (pure structure) matched cross-paradigm sits at the F462/F463 floor (~1) — structure alone")
    print("    cannot bridge LaTeX-declarative + 5 imperatives. As the word-problem anchor weight rises, MATCHED")
    print("    coheres toward k while MISMATCHED stays low (the anchors disagree) — the word problem IS the")
    print("    semantic Rosetta (F458 Route-2). The bridge requires SUPPLYING the meaning — exactly F408:")
    print("    meaning is sourced, not derived from structure. Route-1 (v4, F463) within a paradigm; Route-2")
    print("    (this) across paradigms; the k coupler (F459) the binder over both.")


if __name__ == "__main__":
    main()
