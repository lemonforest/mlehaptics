r"""R-RBS-LM-LATEX (v1) — a LaTeX-AWARE kernel: parse math notation into an A-N
OPERATOR-SIGNATURE (symbol-free) and bind via srmech, testing the F445 cross-domain
invariant FOR MATH — same operator structure, different symbols => same signature.

Math notation IS operator/operand/grammar (F406's three alphabets): \frac \sum \int
\partial are OPERATORS; variables/numbers are OPERANDS; braces/sub/superscript are
GRAMMAR. So instead of STRIPPING math (the word-kernel), parse the OPERATORS into A-N
classes and bind the signature — then two expressions sharing operator structure align
even with zero shared symbols (the operator-signature addressing of F317/F426).

v1 = a MULTISET-of-operators signature (which operators, symbol-free). A nesting/tree-
aware signature (sympy parse tree) is v2 — flagged.

Run: /tmp/verify_srmech_071_sci/bin/python R-RBS-LM-LATEX_aware_kernel_v1.py
"""
import re
import numpy as np
import srmech
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector

D = 8192

# --- the research artifact: LaTeX operator -> A-N class (framework reading, F398 favored-not-privileged) ---
OP_CLASS = {
    "frac": "N(ratio)", "over": "N(ratio)", "/": "N(ratio)", "sqrt": "N(root)",
    "sum": "M(aggregate)", "prod": "M(aggregate)", "int": "M(aggregate)", "oint": "M(aggregate)",
    "cdot": "M(product)", "times": "M(product)", "*": "M(product)",
    "+": "ALU(add)", "-": "ALU(sub)",
    "partial": "K(diff)", "nabla": "K(diff)", "prime": "K(diff)",
    "_": "I(index)", "^": "Jpow(power)", "exp": "Jpow(power)", "log": "N(log)",
    "=": "A(relation)", "lim": "N(limit)", "infty": "N(limit)",
}
_CMD = re.compile(r"\\([a-zA-Z]+)")
_SYM = re.compile(r"[+\-=^_/*]")


def operators(latex):
    ops = []
    for m in _CMD.finditer(latex):
        if m.group(1) in OP_CLASS:
            ops.append(m.group(1))
    for m in _SYM.finditer(latex):
        ops.append(m.group(0))
    return ops


def _bundle(vs):
    if not vs:
        return mint_vector("__noop__", D=D)
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:                     # pad with a NEUTRAL sentinel, not a
        vs = vs + [mint_vector("__pad__", D=D)]   # content element (avoids majority bias)
    return bundle(vs)


def op_signature(latex):
    ops = operators(latex)
    # PRESENCE signature: which operators are present (symbol-free, count-free) — the
    # operator-structure invariant. (multiplicity / nesting = v2 tree-aware refinement.)
    present = sorted(set(ops))
    hv = _bundle([mint_vector("OP:" + o, D=D) for o in present])
    classes = sorted({OP_CLASS.get(o, o) for o in ops})
    return hv, ops, classes


def main():
    print(f"=== R-RBS-LM-LATEX-aware kernel v1  (srmech {srmech.__version__}) ===\n")

    GROUPS = {
        "RATIO  (\\frac)": [r"\frac{a}{b}", r"\frac{x+1}{y-2}", r"\frac{p}{q}"],
        "SUM    (\\sum)":  [r"\sum_{i=1}^{n} a_i", r"\sum_{k} b_k", r"\sum x_j"],
        "INT    (\\int)":  [r"\int_0^1 f \, dx", r"\int g \, dt"],
    }
    # show the operator-signature (class multiset) per expression
    print("operator-signatures (A-N class multiset, symbol-free):")
    for g, exprs in GROUPS.items():
        for e in exprs:
            _, ops, cls = op_signature(e)
            print(f"  {g:14s} {e:28s} ops={ops}  classes={cls}")

    # ---- 1. SYMBOL-INVARIANCE: same operators, different symbols -> ~identical signature ----
    a, _, _ = op_signature(r"\frac{a}{b}")
    b, _, _ = op_signature(r"\frac{zzz}{qqq}")
    sym_inv = similarity(a, b)
    print(f"\n[1] symbol-invariance: sim(\\frac{{a}}{{b}}, \\frac{{zzz}}{{qqq}}) = {sym_inv:+.4f}  (expect ~1.0)")

    # ---- 2. CROSS-DOMAIN shared operator: arithmetic ratio vs calculus ratio (zero shared symbols) ----
    arith, _, ca = op_signature(r"\frac{a}{b}")
    calc, _, cc = op_signature(r"\frac{\partial f}{\partial x}")
    cross = similarity(arith, calc)
    print(f"[2] cross-domain shared \\frac: sim(arith \\frac{{a}}{{b}}, calc \\frac{{∂f}}{{∂x}}) = {cross:+.4f}")
    print(f"     arith classes={ca}   calc classes={cc}  (shared N(ratio); calc adds K(diff))")

    # ---- 3. DIFFERENT structure: ratio vs sum vs int -> low ----
    s_ratio, _, _ = op_signature(r"\frac{a}{b}")
    s_sum, _, _ = op_signature(r"\sum_{i=1}^{n} a_i")
    s_int, _, _ = op_signature(r"\int_0^1 f \, dx")
    print(f"[3] different structure:  ratio·sum={similarity(s_ratio, s_sum):+.4f}  "
          f"ratio·int={similarity(s_ratio, s_int):+.4f}  sum·int={similarity(s_sum, s_int):+.4f}")

    # ---- 4. group cohesion: within-group mean sim vs cross-group mean sim ----
    sigs = {g: [op_signature(e)[0] for e in exprs] for g, exprs in GROUPS.items()}
    within = []
    cross_g = []
    gl = list(sigs)
    for gi, g in enumerate(gl):
        vs = sigs[g]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                within.append(similarity(vs[i], vs[j]))
        for h in gl[gi + 1:]:
            for u in vs:
                for w in sigs[h]:
                    cross_g.append(similarity(u, w))
    wm = sum(within) / len(within); cm = sum(cross_g) / len(cross_g)
    print(f"\n[4] within-group mean sim = {wm:+.4f}   cross-group mean sim = {cm:+.4f}   "
          f"separation = {wm - cm:+.4f}")

    print("\nVERDICT: LaTeX-aware operator-signature is", "SYMBOL-INVARIANT + structure-clustering ✓"
          if (sym_inv > 0.99 and wm > cm and cross > cm) else "needs work ✗")
    print("  (math notation parsed as A-N operators (F406); signature ignores symbols, clusters by")
    print("   operator structure, and links cross-domain expressions sharing operators — the F445")
    print("   cross-domain invariant, for equations. v1=multiset; nesting/tree signature = v2.)")


if __name__ == "__main__":
    main()
