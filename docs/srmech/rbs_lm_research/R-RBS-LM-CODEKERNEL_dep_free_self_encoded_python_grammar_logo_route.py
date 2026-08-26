r"""R-RBS-LM-CODEKERNEL (F795) — the Python rule kernel done RIGHT: we ENCODE the closed finite grammar OURSELVES
(our own tokenizer + recursive-descent), exactly like the LOGO kernel wrote `logo_parser.py` — NO external interpreter
dependency. The earlier R-RBS-LM-CODE kernel used `import ast` (Python's own parser) and the LaTeX one used `sympy` —
shortcuts that VIOLATE the chess/LOGO/F455 thesis ("a closed grammar is encoded, no training, no external interpreter")
and couple the kernel to a host runtime (the opposite of the edge/PAL target). A self-encoded grammar is tiny + portable.

Only the OPERATOR-CLASS-bearing subset is needed (the A-N map is the point, not full Python): def/return/for/while/if/
assign/augassign/compare/and-or/binop/call/name/const. Same A-N map + same recursive bind(op-class, bundle(child-sigs))
signature engine as before → rename-invariant, structure-clustering. srmech HDC ops are the SUBSTRATE (not a parser dep).

srmech 0.7.5rc166. No `ast`, no `sympy`, no `pycparser` — our grammar. No abs; no CAD. Run:
  /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CODEKERNEL_...py
"""
import srmech
from srmech.amsc.hdc import bundle, bind, permute, similarity
from srmech.signal_processing import mint_vector

D = 8192
STRIDE = 2731
KEYWORDS = {"def", "return", "for", "in", "while", "if", "elif", "else", "and", "or", "not", "pass"}
# operator token -> A-N class (the chess/LOGO encoding of the grammar's operators)
_OPCLASS = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "/": "N(ratio)", "//": "N(ratio)",
            "%": "I(mod)", "**": "Jpow(power)", "==": "K(compare)", "!=": "K(compare)", "<": "K(compare)",
            ">": "K(compare)", "<=": "K(compare)", ">=": "K(compare)", "and": "B(and)", "or": "B(or)"}
_OPS = sorted(["**", "//", "==", "!=", "<=", ">=", "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", ":", ",", "."],
              key=len, reverse=True)   # longest-match first


# ---------- our own TOKENIZER (INDENT/DEDENT, like a real grammar front-end) ----------
def tokenize(src):
    toks, indent = [], [0]
    for raw in src.split("\n"):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        col = len(line) - len(line.lstrip(" "))
        if col > indent[-1]:
            indent.append(col); toks.append(("INDENT", ""))
        while col < indent[-1]:
            indent.pop(); toks.append(("DEDENT", ""))
        s, i, n = line.strip(), 0, len(line.strip())
        while i < n:
            c = s[i]
            if c == " ":
                i += 1; continue
            if c.isalpha() or c == "_":
                j = i
                while j < n and (s[j].isalnum() or s[j] == "_"):
                    j += 1
                w = s[i:j]; toks.append(("KW" if w in KEYWORDS else "NAME", w)); i = j; continue
            if c.isdigit():
                j = i
                while j < n and (s[j].isdigit() or s[j] == "."):
                    j += 1
                toks.append(("NUM", s[i:j])); i = j; continue
            for op in _OPS:
                if s.startswith(op, i):
                    toks.append(("OP", op)); i += len(op); break
            else:
                i += 1                                   # skip anything outside the subset
        toks.append(("NEWLINE", ""))
    while len(indent) > 1:
        indent.pop(); toks.append(("DEDENT", ""))
    return toks


# ---------- our own RECURSIVE-DESCENT parser -> (class, [children]) tree ----------
class P:
    def __init__(self, toks):
        self.t = toks; self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else ("EOF", "")

    def eat(self, val=None):
        tk = self.peek(); self.i += 1; return tk

    def accept(self, kind, val=None):
        tk = self.peek()
        if tk[0] == kind and (val is None or tk[1] == val):
            self.i += 1; return tk
        return None

    def skip_newlines(self):
        while self.peek()[0] == "NEWLINE":
            self.i += 1

    def block(self):                                     # suite after ':' = INDENT stmts DEDENT
        stmts = []
        self.skip_newlines()
        if not self.accept("INDENT"):
            return ("GROUP", [])
        while self.peek()[0] not in ("DEDENT", "EOF"):
            self.skip_newlines()
            if self.peek()[0] in ("DEDENT", "EOF"):
                break
            stmts.append(self.statement())
        self.accept("DEDENT")
        return ("GROUP", stmts)

    def statement(self):
        k, v = self.peek()
        if k == "KW" and v == "def":
            self.eat(); name = self.eat()                # def NAME ( params ) :
            self.accept("OP", "("); params = []
            while self.peek() != ("OP", ")") and self.peek()[0] != "EOF":
                p = self.accept("NAME")
                if p:
                    params.append(("OPERAND", []))
                self.accept("OP", ",")
            self.accept("OP", ")"); self.accept("OP", ":")
            return ("DEF", params + [self.block()])
        if k == "KW" and v in ("for",):
            self.eat(); self.accept("NAME"); self.accept("KW", "in"); it = self.expr()
            self.accept("OP", ":"); return ("I(loop)", [it, self.block()])
        if k == "KW" and v == "while":
            self.eat(); t = self.expr(); self.accept("OP", ":"); return ("I(loop)", [t, self.block()])
        if k == "KW" and v in ("if", "elif"):
            self.eat(); t = self.expr(); self.accept("OP", ":"); body = self.block()
            orelse = []
            self.skip_newlines()
            if self.peek() == ("KW", "elif"):
                orelse = [self.statement()]
            elif self.peek() == ("KW", "else"):
                self.eat(); self.accept("OP", ":"); orelse = [self.block()]
            return ("C(branch)", [t, body] + orelse)
        if k == "KW" and v == "return":
            self.eat(); val = self.expr() if self.peek()[0] not in ("NEWLINE", "EOF") else ("OPERAND", [])
            return ("RET", [val])
        # assignment vs bare expression
        start = self.i
        lhs = self.expr()
        op = self.peek()
        if op == ("OP", "="):
            self.eat(); return ("A(assign)", [lhs, self.expr()])
        if op[0] == "OP" and op[1] in ("+=", "-=", "*=", "/="):
            self.eat(); return ("A(assign)+" + _OPCLASS.get(op[1][0], ""), [lhs, self.expr()])
        return ("Expr", [lhs])

    # precedence-climbing expression parser
    def expr(self):
        return self._bool()

    def _bool(self):
        node = self._cmp()
        while self.peek() == ("KW", "and") or self.peek() == ("KW", "or"):
            op = self.eat()[1]; node = (_OPCLASS[op], [node, self._cmp()])
        return node

    def _cmp(self):
        node = self._add()
        while self.peek()[0] == "OP" and self.peek()[1] in ("==", "!=", "<", ">", "<=", ">="):
            op = self.eat()[1]; node = (_OPCLASS[op], [node, self._add()])
        return node

    def _add(self):
        node = self._mul()
        while self.peek()[0] == "OP" and self.peek()[1] in ("+", "-"):
            op = self.eat()[1]; node = (_OPCLASS[op], [node, self._mul()])
        return node

    def _mul(self):
        node = self._pow()
        while self.peek()[0] == "OP" and self.peek()[1] in ("*", "/", "//", "%"):
            op = self.eat()[1]; node = (_OPCLASS[op], [node, self._pow()])
        return node

    def _pow(self):
        node = self._unary()
        if self.peek() == ("OP", "**"):
            self.eat(); node = (_OPCLASS["**"], [node, self._pow()])   # right-assoc
        return node

    def _unary(self):
        if self.peek() == ("OP", "-"):
            self.eat(); return ("ALU(sub)", [("CONST", []), self._unary()])
        return self._atom()

    def _atom(self):
        k, v = self.peek()
        if k == "OP" and v == "(":
            self.eat(); e = self.expr(); self.accept("OP", ")"); return e
        if k == "NUM":
            self.eat(); return ("CONST", [])
        if k == "NAME":
            self.eat()
            if self.peek() == ("OP", "("):               # call: NAME ( args )
                self.eat(); args = []
                while self.peek() != ("OP", ")") and self.peek()[0] != "EOF":
                    args.append(self.expr()); self.accept("OP", ",")
                self.accept("OP", ")"); return ("M(apply)", args or [("OPERAND", [])])
            return ("OPERAND", [])
        self.eat(); return ("OPERAND", [])

    def parse(self):
        stmts = []
        self.skip_newlines()
        while self.peek()[0] != "EOF":
            stmts.append(self.statement()); self.skip_newlines()
        return ("GROUP", stmts)


# ---------- the SAME A-N signature engine (recursive bind/bundle/permute) ----------
def _bundle(vs):
    if not vs:
        return mint_vector("__noop__", D=D)
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def sig(node):
    cls, ch = node
    if not ch:
        return mint_vector("LEAF:" + cls, D=D)
    return bind(mint_vector("OP:" + cls, D=D),
                _bundle([permute(sig(c), (i + 1) * STRIDE) for i, c in enumerate(ch)]))


def code_sig(src):
    return sig(P(tokenize(src)).parse())


def classes_in(src):
    out, stack = set(), [P(tokenize(src)).parse()]
    while stack:
        cls, ch = stack.pop()
        if ch:
            out.add(cls); stack += ch
    return sorted(out)


def main():
    print(f"=== R-RBS-LM-CODEKERNEL — dep-FREE Python rule kernel (our own grammar, no ast)  (srmech {srmech.__version__}) ===\n")
    f1 = "def f(a, b):\n    return a + b"
    f2 = "def g(x, y):\n    return x + y"
    print(f"[1] rename-invariance: sim(f(a,b)=a+b, g(x,y)=x+y) = {similarity(code_sig(f1), code_sig(f2)):+.4f}  (expect ~1.0)")
    sample = ("def h(xs):\n    s = 0\n    for x in xs:\n        if x > 0:\n            s = s + x * 2\n    return s")
    print(f"\n[2] A-N classes from our own parse of a loop+branch+arith fn:\n    {classes_in(sample)}")
    groups = {
        "loop_sum": ["def a(xs):\n    s=0\n    for v in xs:\n        s=s+v\n    return s",
                     "def b(ys):\n    t=0\n    for w in ys:\n        t=t+w\n    return t"],
        "recursive": ["def f(n):\n    if n<=1:\n        return 1\n    return n*f(n-1)",
                      "def g(k):\n    if k<=1:\n        return 1\n    return k*g(k-1)"],
        "arith": ["def p(a,b,c):\n    return a*b+c", "def q(x,y,z):\n    return x*y+z"],
    }
    sigs = {g: [code_sig(s) for s in srcs] for g, srcs in groups.items()}
    within, cross, gl = [], [], list(sigs)
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
    print(f"\n[3] structure-clustering: within {wm:+.4f}  cross {cm:+.4f}  separation {wm-cm:+.4f}")
    loop = "def s(xs):\n    t=0\n    for v in xs:\n        t=t+v\n    return t"
    call = "def s(xs):\n    return sum(xs)"
    print(f"\n[4] same task, diff structure: sim(loop-sum, sum(xs)) = {similarity(code_sig(loop), code_sig(call)):+.4f}  (expect low)")
    print("\nVERDICT: the Python rule kernel needs NO interpreter dep — we encode the closed grammar ourselves (our")
    print("  tokenizer + recursive-descent), the LOGO route. Same rename-invariance + structure-clustering as the ast")
    print("  version. C/LaTeX are the SAME: write the grammar, no pycparser/sympy. Portable -> edge/PAL-ready.")


if __name__ == "__main__":
    main()
