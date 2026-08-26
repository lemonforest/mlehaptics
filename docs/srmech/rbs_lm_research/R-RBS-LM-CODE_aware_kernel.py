r"""R-RBS-LM-CODE — a CODE-aware kernel (Python `ast`, zero deps) reusing the v2
operator-signature engine. Proves F455's point: a programming language is a CLOSED
FINITE GRAMMAR, so we ENCODE it (chess route) — NO TRAINING DATA, just the grammar
shape. The recursive bind(operator-class, bundle(child-sigs)) over a parse tree is
grammar-agnostic; swap sympy's tree for an `ast` tree and the LaTeX-v2 engine becomes
a code kernel. The A-N class map for code constructs falls out naturally:
  if->C(branch/which-way) · for/while->I(loop/cyclic) · = ->A(assign/content-address)
  compare->K(boundary) · + - ->ALU · * ->M(product) · / ->N(ratio) · ** ->Jpow(power)
  call->M(apply) · def->DEF · name/const->symbol-free operand
C is the same pattern with pycparser (flagged). Run:
  /tmp/verify_srmech_071_sci/bin/python R-RBS-LM-CODE_aware_kernel.py
"""
import ast
import srmech
from srmech.amsc.hdc import bundle, bind, permute, similarity
from srmech.signal_processing import mint_vector

D = 8192
STRIDE = 2731
_BINMAP = {"Add": "ALU(add)", "Sub": "ALU(sub)", "Mult": "M(product)", "Div": "N(ratio)",
           "FloorDiv": "N(ratio)", "Mod": "I(mod)", "Pow": "Jpow(power)",
           "BitXor": "ALU(xor)", "BitAnd": "ALU(and)", "BitOr": "ALU(or)",
           "LShift": "shift", "RShift": "shift"}
_SKIP = (ast.expr_context, ast.operator, ast.unaryop, ast.cmpop, ast.boolop)


def aclass(n):
    if isinstance(n, ast.Name):
        return "OPERAND"
    if isinstance(n, ast.Constant):
        return "CONST"
    if isinstance(n, ast.arg):
        return "OPERAND"
    if isinstance(n, ast.BinOp):
        return _BINMAP.get(type(n.op).__name__, "BinOp")
    if isinstance(n, ast.AugAssign):
        return "A(assign)+" + _BINMAP.get(type(n.op).__name__, "")
    if isinstance(n, (ast.For, ast.While, ast.comprehension)):
        return "I(loop)"
    if isinstance(n, ast.If) or isinstance(n, ast.IfExp):
        return "C(branch)"
    if isinstance(n, ast.Compare):
        return "K(compare)"
    if isinstance(n, (ast.Assign, ast.AnnAssign)):
        return "A(assign)"
    if isinstance(n, ast.Call):
        return "M(apply)"
    if isinstance(n, ast.FunctionDef):
        return "DEF"
    if isinstance(n, ast.Return):
        return "RET"
    if isinstance(n, (ast.Module, ast.Expr)):
        return "GROUP"
    return type(n).__name__


def _kids(n):
    return [c for c in ast.iter_child_nodes(n) if not isinstance(c, _SKIP)]


def _bundle(vs):
    if not vs:
        return mint_vector("__noop__", D=D)
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def sig(n):
    cls = aclass(n)
    ch = _kids(n)
    if not ch:
        return mint_vector("LEAF:" + cls, D=D)          # symbol-free leaf
    return bind(mint_vector("OP:" + cls, D=D),
                _bundle([permute(sig(c), (i + 1) * STRIDE) for i, c in enumerate(ch)]))


def code_sig(src):
    return sig(ast.parse(src.strip()))


def classes_in(src):
    return sorted({aclass(n) for n in ast.walk(ast.parse(src.strip())) if _kids(n)})


def main():
    print(f"=== R-RBS-LM-CODE-aware kernel (Python ast, no training data)  (srmech {srmech.__version__}) ===\n")

    # ---- 1. RENAME-invariance (the code analogue of symbol-invariance) ----
    f1 = "def f(a, b):\n    return a + b"
    f2 = "def g(x, y):\n    return x + y"
    print(f"[1] rename-invariance: sim(f(a,b)=a+b, g(x,y)=x+y) = {similarity(code_sig(f1), code_sig(f2)):+.4f}  (expect ~1.0)")

    # ---- 2. A-N class map for code constructs (the artifact) ----
    sample = ("def h(xs):\n"
              "    s = 0\n"
              "    for x in xs:\n"
              "        if x > 0:\n"
              "            s = s + x * 2\n"
              "    return s")
    print(f"\n[2] A-N classes parsed from a loop+branch+arith fn:\n    {classes_in(sample)}")
    print("    (if->C(branch)  for->I(loop)  = ->A(assign)  > ->K(compare)  + ->ALU(add)  * ->M(product))")

    # ---- 3. structure-clustering: loop-sum vs recursive vs straight-arith ----
    groups = {
        "loop_sum": [
            "def a(xs):\n    s=0\n    for v in xs:\n        s=s+v\n    return s",
            "def b(ys):\n    t=0\n    for w in ys:\n        t=t+w\n    return t",   # same shape, renamed
        ],
        "recursive": [
            "def f(n):\n    if n<=1:\n        return 1\n    return n*f(n-1)",
            "def g(k):\n    if k<=1:\n        return 1\n    return k*g(k-1)",       # same shape, renamed
        ],
        "arith": [
            "def p(a,b,c):\n    return a*b+c",
            "def q(x,y,z):\n    return x*y+z",                                       # same shape, renamed
        ],
    }
    sigs = {g: [code_sig(s) for s in srcs] for g, srcs in groups.items()}
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
    print(f"\n[3] structure-clustering: within-group {wm:+.4f}  cross-group {cm:+.4f}  separation {wm-cm:+.4f}")
    print("    (renamed-but-same-algorithm cluster together; different algorithms separate)")

    # ---- 4. same task, different STRUCTURE -> different signature (reads structure, not intent) ----
    loop = "def s(xs):\n    t=0\n    for v in xs:\n        t=t+v\n    return t"
    call = "def s(xs):\n    return sum(xs)"
    print(f"\n[4] same task, diff structure: sim(loop-sum, sum(xs)) = {similarity(code_sig(loop), code_sig(call)):+.4f}")
    print("    (low — the kernel reads STRUCTURE, not intent; imperative loop != declarative call)")

    print("\nVERDICT: a programming language is a CLOSED FINITE GRAMMAR -> encode it (chess route),")
    print("  NO training data. The LaTeX-v2 engine is grammar-agnostic: ast tree in, A-N operator-")
    print("  signature out — rename-invariant, structure-clustering. C is the same via pycparser.")
    print("  (Code GRAMMAR = Route-1/encode; code SEMANTICS/'what it computes' = the Route-2 stories.)")


if __name__ == "__main__":
    main()
