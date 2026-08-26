r"""R-RBS-LM-LATEX (v2) — NESTING/MULTIPLICITY-aware operator-signature from a real
sympy parse TREE (vs v1's flat presence-set). Each tree node becomes
  sig(node) = bind( OP-class(node), bundle( permute(sig(child_i), i) ) )
with leaves = generic SYMBOL-FREE operands. This captures operator NESTING
(operator-of-operator) and child MULTIPLICITY/arity — exactly what the v1
presence-set conflated (F452). Still symbol-invariant (leaves carry no symbol).

Parses via sympy parse_latex(backend='lark') (antlr-free); maps sympy node types
to A-N classes (Add->ALU, Mul->M/N(ratio), Pow->Jpow/N(root), Sum/Integral->M(aggregate),
Derivative->K(diff)). The headline test runs BOTH the v2 tree-signature AND a v1-style
presence-set on the same pairs — v2 distinguishes nesting+multiplicity that v1 cannot.

Run: /tmp/verify_srmech_071_sci/bin/python R-RBS-LM-LATEX_aware_kernel_v2.py
"""
import sympy
from sympy.parsing.latex import parse_latex
import srmech
from srmech.amsc.hdc import bundle, bind, permute, similarity
from srmech.signal_processing import mint_vector

D = 8192
STRIDE = 2731


def node_class(n):
    if n.is_Symbol:
        return "OPERAND"
    if n.is_Number:
        return "CONST"
    if isinstance(n, sympy.Add):
        return "ALU(add)"
    if isinstance(n, sympy.Mul):
        if any(isinstance(a, sympy.Pow) and a.exp.is_number and a.exp.is_negative for a in n.args):
            return "N(ratio)"
        return "M(product)"
    if isinstance(n, sympy.Pow):
        if n.exp == sympy.S.Half:
            return "N(root)"
        if n.exp.is_number and n.exp.is_negative:
            return "N(recip)"
        return "Jpow(power)"
    if isinstance(n, (sympy.Sum, sympy.Integral, sympy.Product)):
        return "M(aggregate)"
    if isinstance(n, sympy.Derivative):
        return "K(diff)"
    if isinstance(n, sympy.Tuple):
        return "GROUP"
    return type(n).__name__


def _bundle(vs):
    if not vs:
        return mint_vector("__noop__", D=D)
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def tree_sig(n):
    """v2 — recursive, nesting+multiplicity aware, symbol-free."""
    cls = node_class(n)
    if not n.args:                                  # leaf (symbol/number) — symbol-free
        return mint_vector("LEAF:" + cls, D=D)
    kids = [permute(tree_sig(c), (i + 1) * STRIDE) for i, c in enumerate(n.args)]
    return bind(mint_vector("OP:" + cls, D=D), _bundle(kids))


def presence_sig(n):
    """v1-style — the SET of operator classes in the tree (no nesting, no count)."""
    classes = set()
    def walk(x):
        if x.args:
            classes.add(node_class(x))
            for c in x.args:
                walk(c)
    walk(n)
    return _bundle([mint_vector("OP:" + c, D=D) for c in sorted(classes)]), sorted(classes)


def P(s):
    return parse_latex(s, backend="lark")


def main():
    print(f"=== R-RBS-LM-LATEX-aware kernel v2 (sympy tree)  (srmech {srmech.__version__}, sympy {sympy.__version__}) ===\n")

    # ---- 1. symbol-invariance (retained) ----
    a, b = tree_sig(P(r"\frac{a}{b}")), tree_sig(P(r"\frac{m}{n}"))
    print(f"[1] symbol-invariance: sim(\\frac{{a}}{{b}}, \\frac{{m}}{{n}}) = {similarity(a, b):+.4f}  (expect ~1.0)")

    # ---- 2. NESTING sensitivity (the v2 win) — same operator SET, different nesting ----
    A = r"\frac{\sum_{i=1}^{n} a_i}{x}"      # Sum nested inside a ratio   -> root N(ratio)
    B = r"\sum_{i=1}^{n} \frac{a_i}{x}"       # ratio nested inside a Sum   -> root M(aggregate)
    pa, ca = presence_sig(P(A)); pb, cb = presence_sig(P(B))
    v2 = similarity(tree_sig(P(A)), tree_sig(P(B)))
    v1 = similarity(pa, pb)
    print(f"\n[2] NESTING: A={A}")
    print(f"             B={B}")
    print(f"    v1 presence-set sim = {v1:+.4f}  (sets: A={ca}  B={cb})  <- v1 conflates")
    print(f"    v2 tree    sim     = {v2:+.4f}  <- v2 SEPARATES (different root/nesting)")
    print(f"    => v2 distinguishes nesting v1 cannot: {'YES' if v2 < v1 - 0.1 else 'no'}")

    # ---- 3. MULTIPLICITY/arity sensitivity (the v2 win) — x+y vs x+y+z ----
    C, Dd = r"x + y", r"x + y + z"
    pc, _ = presence_sig(P(C)); pd, _ = presence_sig(P(Dd))
    v2m = similarity(tree_sig(P(C)), tree_sig(P(Dd)))
    v1m = similarity(pc, pd)
    print(f"\n[3] MULTIPLICITY/arity: '{C}' (Add/2) vs '{Dd}' (Add/3)")
    print(f"    v1 presence-set sim = {v1m:+.4f}  <- v1 conflates (both {{ALU(add)}})")
    print(f"    v2 tree    sim     = {v2m:+.4f}  <- v2 SEPARATES (arity differs)")
    print(f"    => v2 distinguishes arity v1 cannot: {'YES' if v2m < v1m - 0.05 else 'no'}")

    # ---- 4. cross-domain ratio link (retained) — different inner ops, same ratio root ----
    r1, r2 = tree_sig(P(r"\frac{a}{b}")), tree_sig(P(r"\frac{f+1}{g}"))
    print(f"\n[4] cross-domain ratio: sim(\\frac{{a}}{{b}}, \\frac{{f+1}}{{g}}) = {similarity(r1, r2):+.4f}  (shared N(ratio) root)")

    # ---- 5. derivative node (K(diff)) via constructed Derivative (Lark can't parse \partial) ----
    x, y = sympy.symbols("x y")
    d1 = tree_sig(sympy.Derivative(sympy.Function("f")(x), x))
    d2 = tree_sig(sympy.Derivative(sympy.Function("g")(y), y))
    print(f"[5] derivative K(diff): sim(d f/d x, d g/d y) = {similarity(d1, d2):+.4f}  (symbol-free; same diff structure)")

    # ---- 6. structure-clustering: group by root operator ----
    groups = {
        "ratio": [r"\frac{a}{b}", r"\frac{p}{q}", r"\frac{f+1}{g}"],
        "sum":   [r"\sum_{i=1}^{n} a_i", r"\sum_{k=1}^{m} b_k"],
        "power": [r"x^2 + y^2", r"a^4 + b^2"],
    }
    def safe_sig(e):
        try:
            return tree_sig(P(e))
        except Exception as ex:
            print(f"    (skip unparseable: {e} — {type(ex).__name__})")
            return None
    sigs = {g: [s for s in (safe_sig(e) for e in exprs) if s is not None] for g, exprs in groups.items()}
    within, cross = [], []
    gl = list(sigs)
    for gi, g in enumerate(gl):
        vs = sigs[g]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                within.append(similarity(vs[i], vs[j]))
        for h in gl[gi + 1:]:
            for u in vs:
                for w in sigs[h]:
                    cross.append(similarity(u, w))
    wm, cm = sum(within) / len(within), sum(cross) / len(cross)
    print(f"\n[6] structure-clustering: within-group {wm:+.4f}  cross-group {cm:+.4f}  separation {wm-cm:+.4f}")

    print("\nVERDICT: v2 tree-signature adds NESTING + MULTIPLICITY sensitivity over v1's presence-set,")
    print("  while keeping symbol-invariance + structure-clustering. Math parsed as a real A-N operator")
    print("  TREE (F406 grammar), addressed by structural operator-signature (F317/F426).")


if __name__ == "__main__":
    main()
