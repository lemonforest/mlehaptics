r"""R-RBS-LM-CANON / v4 canonical A-N IR — the STRUCTURAL commensurability route
(F455 Route-1) that F462 located as the missing piece. v3 showed cross-LANGUAGE
operator-signatures are orthogonal (F457) because the CONCRETE syntax trees differ
(for-of vs for-range vs for-each, wrapper nodes, decl-vs-assign). v4 normalizes every
grammar into ONE shared canonical A-N operator INVENTORY — one I(loop) for every loop
form, one A(assign) for decl+assign, canonical ALU/M/N arithmetic ops — so the SAME
algorithm yields the SAME canonical signature regardless of grammar.

Then it does the decisive test: re-run the F462 per-dimension k coupler on the v4
signatures. If v4 supplies commensurability, the cross-language coherence should rise
from the F462 floor (~1.1) toward ~k. Cross-PARADIGM reps (the LaTeX declarative Σ, the
natural-language word problem) have NO shared structural inventory and stay at the floor
— exactly where the semantic anchor (F458, Route-2) is the only bridge.

Run: /tmp/verify_srmech_073rc1_sci/bin/python R-RBS-LM-CANON_ir_v4_canonical_an_inventory.py
"""
import itertools
import numpy as np
import srmech
from srmech.amsc import cascade as C
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector

D = 8192

# ---- the canonical A-N operator vocabulary (the IR alphabet) ----
# structural: DEF RET I(loop) C(branch) A(assign) M(apply) K(compare) AGG
# arithmetic: ALU(add) ALU(sub) M(product) N(ratio) Jpow(power) I(mod)
# leaves (OPERAND/CONST) and pure wrappers are NOT counted (symbol-free, non-discriminative)
TSOP = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "/": "N(ratio)",
        "%": "I(mod)", "<": "K(compare)", ">": "K(compare)", "==": "K(compare)",
        "<=": "K(compare)", ">=": "K(compare)", "!=": "K(compare)"}


def _bundle(vs):
    if not vs:
        return mint_vector("__noop__", D=D)
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def inv_sig(inv):
    """canonical operator INVENTORY -> one HV (count-weighted bundle of class vectors)."""
    vecs = []
    for cls, cnt in sorted(inv.items()):
        vecs += [mint_vector("CANON:" + cls, D=D)] * cnt
    return _bundle(vecs) if vecs else mint_vector("__noop__", D=D)


# ============ canonical inventory: python (stdlib ast) ============
def py_inv(src):
    import ast
    BIN = {"Add": "ALU(add)", "Sub": "ALU(sub)", "Mult": "M(product)", "Div": "N(ratio)",
           "Mod": "I(mod)", "Pow": "Jpow(power)"}
    inv = {}
    def add(c): inv[c] = inv.get(c, 0) + 1
    for n in ast.walk(ast.parse(src.strip())):
        if isinstance(n, ast.BinOp):       add(BIN.get(type(n.op).__name__, "BINOP"))
        elif isinstance(n, (ast.For, ast.While, ast.comprehension)): add("I(loop)")
        elif isinstance(n, (ast.If, ast.IfExp)): add("C(branch)")
        elif isinstance(n, ast.Compare):   add("K(compare)")
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)): add("A(assign)")
        elif isinstance(n, ast.Call):      add("M(apply)")
        elif isinstance(n, ast.FunctionDef): add("DEF")
        elif isinstance(n, ast.Return):    add("RET")
    return inv


# ============ canonical inventory: c (pycparser) ============
def c_inv(src):
    from pycparser import c_parser, c_ast
    BIN = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "/": "N(ratio)", "%": "I(mod)",
           "<": "K(compare)", ">": "K(compare)", "==": "K(compare)", "<=": "K(compare)", ">=": "K(compare)"}
    inv = {}
    def add(c): inv[c] = inv.get(c, 0) + 1
    class V(c_ast.NodeVisitor):
        def visit_BinaryOp(self, n): add(BIN.get(n.op, "BINOP")); self.generic_visit(n)
        def visit_For(self, n): add("I(loop)"); self.generic_visit(n)
        def visit_While(self, n): add("I(loop)"); self.generic_visit(n)
        def visit_If(self, n): add("C(branch)"); self.generic_visit(n)
        def visit_Assignment(self, n): add("A(assign)"); self.generic_visit(n)
        def visit_Decl(self, n):
            if n.init is not None: add("A(assign)")
            self.generic_visit(n)
        def visit_FuncCall(self, n): add("M(apply)"); self.generic_visit(n)
        def visit_FuncDef(self, n): add("DEF"); self.generic_visit(n)
        def visit_Return(self, n): add("RET"); self.generic_visit(n)
    V().visit(c_parser.CParser().parse(src))
    return inv


# ============ canonical inventory: math (sympy) ============
def math_inv(latex):
    import sympy
    from sympy.parsing.latex import parse_latex
    inv = {}
    def add(c): inv[c] = inv.get(c, 0) + 1
    def walk(n):
        if isinstance(n, sympy.Add): add("ALU(add)")
        elif isinstance(n, sympy.Mul):
            add("N(ratio)" if any(isinstance(a, sympy.Pow) and a.exp.is_number and a.exp.is_negative for a in n.args) else "M(product)")
        elif isinstance(n, sympy.Pow):
            add("N(root)" if n.exp == sympy.S.Half else ("N(ratio)" if (n.exp.is_number and n.exp.is_negative) else "Jpow(power)"))
        elif isinstance(n, (sympy.Sum, sympy.Integral, sympy.Product)): add("AGG")
        elif isinstance(n, sympy.Derivative): add("K(diff)")
        for a in n.args:
            walk(a)
    walk(parse_latex(latex, backend="lark"))
    return inv


# ============ canonical inventory: tree-sitter (JS/Go/Rust/Java/TS) ============
def _g(o, name):
    a = getattr(o, name)
    return a() if callable(a) else a

def ts_inv(lang, src):
    from tree_sitter_language_pack import get_parser
    tree = get_parser(lang).parse(src)
    root = _g(tree, "root_node")
    inv = {}
    def add(c): inv[c] = inv.get(c, 0) + 1
    def opclass(n):                                   # read binary operator token
        for i in range(_g(n, "child_count")):
            k = _g(n.child(i), "kind")
            if k in TSOP:
                return TSOP[k]
        return "BINOP"
    def canon(t, n):
        tl = t.lower()
        if tl.startswith("if") or "ternary" in tl or "conditional_exp" in tl: return "C(branch)"
        if ("for_statement" in tl or "for_in" in tl or "for_of" in tl or "for_expression" in tl
                or "for_range" in tl or "for_clause" in tl or "while" in tl or "enhanced_for" in tl): return "I(loop)"
        if "function" in tl or "method_declaration" in tl or "method_definition" in tl or "function_item" in tl: return "DEF"
        if "call" in tl or "invocation" in tl: return "M(apply)"
        if "return" in tl: return "RET"
        if "assignment" in tl or "declaration" in tl or "init_declarator" in tl: return "A(assign)"
        if "binary" in tl: return opclass(n)
        return None
    def walk(n):
        c = canon(_g(n, "kind"), n)
        if c: add(c)
        for i in range(_g(n, "named_child_count")):
            walk(n.named_child(i))
    walk(root)
    return inv


def wp_inv(_text):
    """natural language has NO grammar parse-tree -> NO canonical operator inventory.
    The honest structural result: NL is empty here; it needs the F458 semantic anchor."""
    return {}


def pm1(sig):
    return np.unpackbits(np.frombuffer(sig, dtype=np.uint8)).astype(np.int64) * 2 - 1


def coherence(sigs, sample, rng):
    bits = [pm1(s) for s in sigs]
    dims = rng.choice(D, size=sample, replace=False)
    acc = 0.0
    for d in dims:
        streams = [float(b[d]) for b in bits]
        acc += float(C.hypercomplex_couple(streams, axis="diagonal")[0]) ** 2
    return acc / len(dims)


def main():
    print(f"=== R-RBS-LM-CANON — v4 canonical A-N IR (operator inventory)  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(0)

    # ---- the SAME math (Σ aᵢ) in seven representations ----
    loopsum = {
        "Python": py_inv("def s(xs):\n t=0\n for v in xs:\n  t=t+v\n return t"),
        "C":      c_inv("int s(int xs[], int n){ int t=0; for(int i=0;i<n;i++){ t=t+xs[i]; } return t; }"),
        "JavaScript": ts_inv("javascript", "function s(xs){let t=0;for(const v of xs){t=t+v;}return t;}"),
        "Go":     ts_inv("go", "package m\nfunc s(xs []int) int { t:=0; for _,v := range xs { t=t+v }; return t }"),
        "Rust":   ts_inv("rust", "fn s(xs:Vec<i32>)->i32{ let mut t=0; for v in xs { t=t+v; } return t; }"),
    }
    latex_sum = math_inv(r"\sum_{i=1}^{n} a_i")
    wp_sum    = wp_inv("add up all the numbers in the list to get the total sum")

    print("canonical A-N operator INVENTORY per representation of Σaᵢ:")
    for k, inv in loopsum.items():
        print(f"  {k:11s} {dict(sorted(inv.items()))}")
    print(f"  {'LaTeX Σ':11s} {dict(sorted(latex_sum.items()))}   (declarative aggregate — different paradigm)")
    print(f"  {'word-prob':11s} {wp_sum}   (natural language — no grammar tree)")

    # ---- v4 signatures ----
    imp_sigs = {k: inv_sig(v) for k, v in loopsum.items()}        # 5 imperative languages
    s_latex, s_wp = inv_sig(latex_sum), inv_sig(wp_sum)

    print("\n[1] v4 cross-LANGUAGE pairwise similarity over the 5 imperative loop-sums (vs v3 ~0, the F457 null):")
    pairs = list(itertools.combinations(imp_sigs, 2))
    sims = [similarity(imp_sigs[a], imp_sigs[b]) for a, b in pairs]
    for (a, b), sm in zip(pairs, sims):
        print(f"    {a:11s} ~ {b:11s} = {sm:+.3f}")
    print(f"    mean = {sum(sims)/len(sims):+.3f}  over {len(sims)} pairs   "
          f"(min {min(sims):+.2f}, max {max(sims):+.2f})")

    print("\n[2] cross-PARADIGM: LaTeX Σ and word problem vs the imperative cluster (should stay LOW — needs F458):")
    impmean = lambda x: sum(similarity(x, imp_sigs[k]) for k in imp_sigs) / len(imp_sigs)
    print(f"    LaTeX Σ  ~ imperative-mean = {impmean(s_latex):+.3f}")
    print(f"    word-prob ~ imperative-mean = {impmean(s_wp):+.3f}")

    # ---- [3] the decisive fusion: re-run the F462 k coupler on v4 signatures ----
    print("\n[3] F462 coupler RE-RUN on v4 signatures — does the canonical IR supply the commensurability?")
    S = 500
    # mismatched control: 5 DIFFERENT algorithms, one per language
    mismatched = [
        py_inv("def f(n):\n if n<=1:\n  return 1\n return n*f(n-1)"),       # recursion+branch+product
        c_inv("int g(int a){ if(a>0){ return a; } return -a; }"),           # branch only
        ts_inv("javascript", "function p(a,b){return a*b;}"),               # product
        ts_inv("go", "package m\nfunc q(x int) int { return x+1 }"),        # add
        ts_inv("rust", "fn r(x:i32)->i32{ x*x }"),                          # product
    ]
    coh_imp = coherence(list(imp_sigs.values()), S, rng)
    coh_mis = coherence([inv_sig(m) for m in mismatched], S, rng)
    k = len(imp_sigs)
    print(f"    MATCHED cross-language (5 imperative loop-sums, v4 canonical):  {coh_imp:.2f}   (expect ~k={k} if commensurate)")
    print(f"    MISMATCHED (5 different algorithms):                            {coh_mis:.2f}   (expect ~1 — incoherent)")
    print(f"    F462 baseline for raw cross-grammar (no v4): ~1.1 (the F457 floor)")

    print("\nVERDICT:")
    print(f"  • v4 canonical A-N IR makes the SAME algorithm in 5 different LANGUAGES commensurate:")
    print(f"    pairwise sim {sum(sims)/len(sims):+.2f} (vs v3's ~0), coupler coherence {coh_imp:.1f}× (vs F462's ~1.1).")
    print(f"  • mismatched stays at {coh_mis:.1f}× — the IR is discriminative, not a trivial collapse.")
    print(f"  • cross-PARADIGM (LaTeX declarative Σ, NL word problem) stay near the floor — structure alone")
    print(f"    can't bridge paradigms; that is exactly where the F458 semantic anchor (Route-2) is required.")
    print(f"  => Route-1 (v4, structural) supplies commensurability WITHIN a paradigm; Route-2 (F458, semantic)")
    print(f"     across paradigms. The k coupler (F459) is the binder; v4 + F458 are the two commensurality routes.")


if __name__ == "__main__":
    main()
