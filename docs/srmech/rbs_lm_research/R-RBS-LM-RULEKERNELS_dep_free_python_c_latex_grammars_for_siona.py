r"""R-RBS-LM-RULEKERNELS (F796) — the SHARED, importable rule-kernel module: dep-FREE self-encoded grammars for
PYTHON, C, and LaTeX-math, each a genuine RBS-HDC instrument (our own tokenizer + recursive-descent → A-N operator
signatures via srmech HDC). NO `ast`, NO `sympy`, NO `pycparser` — the LOGO route (F795). This is the genome-facing
component Siona imports (like the markup grammar): she carries the construct→A-N vocabulary AND can structurally READ
code/math handed to her.

A programming/markup language is a CLOSED FINITE GRAMMAR → encode it, no training (chess/LOGO/F455). The same A-N map
across all three: if→C(branch) · for/while→I(loop) · =→A(assign) · compare→K · +-→ALU · *→M(product) · /,\frac→N(ratio)
· **,^→Jpow(power) · &&/||→B · call→M(apply) · def/funcdef→DEF · return→RET.

srmech 0.7.5rc166 substrate (HDC bind/bundle/permute — NOT a parser dep). No abs; no CAD. Self-test:
  /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-RULEKERNELS_...py
"""
import srmech
from srmech.amsc.hdc import bundle, bind, permute, similarity
from srmech.signal_processing import mint_vector

D = 8192
STRIDE = 2731

# ============================ shared A-N signature engine ============================
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


def classes_in(node):
    out, stack = set(), [node]
    while stack:
        cls, ch = stack.pop()
        if ch:
            out.add(cls); stack += ch
    return sorted(out)


# the A-N operator map shared by the grammars (construct → class + gloss) — the genome vocabulary
CONSTRUCT_CLASSES = {
    "if/?:":          ("C(branch)",  "a which-way branch — Class C (chirality/intent)"),
    "for/while":      ("I(loop)",    "a cyclic repeat — Class I (cyclic group)"),
    "= (assign)":     ("A(assign)",  "bind a value to a name — Class A (content-address)"),
    "== < > compare": ("K(compare)", "a boundary test — Class K (pin-slot/phase-boundary)"),
    "+ -":            ("ALU(add/sub)", "add/subtract — the bit-exact ALU"),
    "*":              ("M(product)", "product/apply — Class M (HDC bind)"),
    "/ \\frac":       ("N(ratio)",   "ratio/division — Class N (rational approx)"),
    "** ^ (power)":   ("Jpow(power)", "power — Class J (primes/exponent)"),
    "&& ||":          ("B(bool)",    "boolean compose — Class B (TLV-framing)"),
    "call f(...)":    ("M(apply)",   "apply a function — Class M"),
    "def/func":       ("DEF",        "define a procedure (an anchor)"),
    "return":         ("RET",        "yield the result"),
}


# ============================ PYTHON (indentation grammar) ============================
_PY_KW = {"def", "return", "for", "in", "while", "if", "elif", "else", "and", "or", "not", "pass"}
_PY_OPCLASS = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "/": "N(ratio)", "//": "N(ratio)",
               "%": "I(mod)", "**": "Jpow(power)", "==": "K(compare)", "!=": "K(compare)", "<": "K(compare)",
               ">": "K(compare)", "<=": "K(compare)", ">=": "K(compare)", "and": "B(and)", "or": "B(or)"}
_PY_OPS = sorted(["**", "//", "==", "!=", "<=", ">=", "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", ":", ",", "."],
                 key=len, reverse=True)


def _py_tokens(src):
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
                w = s[i:j]; toks.append(("KW" if w in _PY_KW else "NAME", w)); i = j; continue
            if c.isdigit():
                j = i
                while j < n and (s[j].isdigit() or s[j] == "."):
                    j += 1
                toks.append(("NUM", s[i:j])); i = j; continue
            for op in _PY_OPS:
                if s.startswith(op, i):
                    toks.append(("OP", op)); i += len(op); break
            else:
                i += 1
        toks.append(("NEWLINE", ""))
    while len(indent) > 1:
        indent.pop(); toks.append(("DEDENT", ""))
    return toks


class _Parser:
    """precedence-climbing recursive descent, parametrised by the token-kind/op tables of each language."""
    def __init__(self, toks, opclass, block_kind="indent"):
        self.t, self.i, self.OPC, self.bk = toks, 0, opclass, block_kind

    def pk(self):
        return self.t[self.i] if self.i < len(self.t) else ("EOF", "")

    def eat(self):
        tk = self.pk(); self.i += 1; return tk

    def acc(self, kind, val=None):
        tk = self.pk()
        if tk[0] == kind and (val is None or tk[1] == val):
            self.i += 1; return tk
        return None

    def _skip(self):
        while self.pk()[0] == "NEWLINE":
            self.i += 1


def _py_parse(toks):
    P = _Parser(toks, _PY_OPCLASS)

    def block():
        P._skip()
        if not P.acc("INDENT"):
            return ("GROUP", [])
        st = []
        while P.pk()[0] not in ("DEDENT", "EOF"):
            P._skip()
            if P.pk()[0] in ("DEDENT", "EOF"):
                break
            st.append(stmt())
        P.acc("DEDENT"); return ("GROUP", st)

    def stmt():
        k, v = P.pk()
        if (k, v) == ("KW", "def"):
            P.eat(); P.eat(); P.acc("OP", "(")
            params = []
            while P.pk() != ("OP", ")") and P.pk()[0] != "EOF":
                if P.acc("NAME"):
                    params.append(("OPERAND", []))
                P.acc("OP", ",")
            P.acc("OP", ")"); P.acc("OP", ":"); return ("DEF", params + [block()])
        if (k, v) == ("KW", "for"):
            P.eat(); P.acc("NAME"); P.acc("KW", "in"); it = expr(); P.acc("OP", ":"); return ("I(loop)", [it, block()])
        if (k, v) == ("KW", "while"):
            P.eat(); t = expr(); P.acc("OP", ":"); return ("I(loop)", [t, block()])
        if k == "KW" and v in ("if", "elif"):
            P.eat(); t = expr(); P.acc("OP", ":"); body = block(); orelse = []
            P._skip()
            if P.pk() == ("KW", "elif"):
                orelse = [stmt()]
            elif P.pk() == ("KW", "else"):
                P.eat(); P.acc("OP", ":"); orelse = [block()]
            return ("C(branch)", [t, body] + orelse)
        if (k, v) == ("KW", "return"):
            P.eat(); val = expr() if P.pk()[0] not in ("NEWLINE", "EOF") else ("OPERAND", []); return ("RET", [val])
        lhs = expr()
        if P.pk() == ("OP", "="):
            P.eat(); return ("A(assign)", [lhs, expr()])
        if P.pk()[0] == "OP" and P.pk()[1] in ("+=", "-=", "*=", "/="):
            P.eat(); return ("A(assign)", [lhs, expr()])
        return ("Expr", [lhs])

    def expr():
        return _expr(P, ["and", "or"])

    out = []
    P._skip()
    while P.pk()[0] != "EOF":
        out.append(stmt()); P._skip()
    return ("GROUP", out)


# ---- shared precedence-climbing expression parser (works for py & c token streams) ----
def _expr(P, bool_ops):
    def boolean():
        node = comparison()
        while P.pk()[0] in ("KW", "OP") and P.pk()[1] in bool_ops:
            op = P.eat()[1]; node = (P.OPC.get(op, "B(bool)"), [node, comparison()])
        return node

    def comparison():
        node = additive()
        while P.pk()[0] == "OP" and P.pk()[1] in ("==", "!=", "<", ">", "<=", ">="):
            op = P.eat()[1]; node = (P.OPC[op], [node, additive()])
        return node

    def additive():
        node = mul()
        while P.pk()[0] == "OP" and P.pk()[1] in ("+", "-"):
            op = P.eat()[1]; node = (P.OPC[op], [node, mul()])
        return node

    def mul():
        node = power()
        while P.pk()[0] == "OP" and P.pk()[1] in ("*", "/", "//", "%"):
            op = P.eat()[1]; node = (P.OPC[op], [node, power()])
        return node

    def power():
        node = unary()
        if P.pk() == ("OP", "**"):
            P.eat(); node = (P.OPC["**"], [node, power()])
        return node

    def unary():
        if P.pk() == ("OP", "-"):
            P.eat(); return ("ALU(sub)", [("CONST", []), unary()])
        if P.pk() == ("OP", "*") or P.pk() == ("OP", "&"):     # C deref / address-of
            P.eat(); return unary()
        return atom()

    def atom():
        k, v = P.pk()
        if (k, v) == ("OP", "("):
            P.eat(); e = boolean(); P.acc("OP", ")"); return e
        if k == "NUM":
            P.eat(); return ("CONST", [])
        if k == "NAME":
            P.eat()
            if P.pk() == ("OP", "("):
                P.eat(); args = []
                while P.pk() != ("OP", ")") and P.pk()[0] != "EOF":
                    args.append(boolean()); P.acc("OP", ",")
                P.acc("OP", ")"); return ("M(apply)", args or [("OPERAND", [])])
            return ("OPERAND", [])
        P.eat(); return ("OPERAND", [])

    return boolean()


# ============================ C (brace/semicolon grammar) ============================
_C_KW = {"if", "else", "for", "while", "return", "int", "char", "float", "double", "void", "long", "short",
         "unsigned", "struct", "const", "static"}
_C_TYPES = {"int", "char", "float", "double", "void", "long", "short", "unsigned", "struct", "const", "static"}
_C_OPCLASS = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "/": "N(ratio)", "%": "I(mod)",
              "==": "K(compare)", "!=": "K(compare)", "<": "K(compare)", ">": "K(compare)", "<=": "K(compare)",
              ">=": "K(compare)", "&&": "B(and)", "||": "B(or)", "&": "ALU(and)", "|": "ALU(or)", "^": "ALU(xor)"}
_C_OPS = sorted(["==", "!=", "<=", ">=", "&&", "||", "+=", "-=", "*=", "/=", "+", "-", "*", "/", "%",
                 "<", ">", "=", "&", "|", "^", "(", ")", "{", "}", ";", ",", "."], key=len, reverse=True)


def _c_tokens(src):
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\n":
            i += 1; continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":         # // comment
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            w = src[i:j]; toks.append(("KW" if w in _C_KW else "NAME", w)); i = j; continue
        if c.isdigit():
            j = i
            while j < n and (src[j].isdigit() or src[j] in ".xXabcdefABCDEF"):
                j += 1
            toks.append(("NUM", src[i:j])); i = j; continue
        for op in _C_OPS:
            if src.startswith(op, i):
                toks.append(("OP", op)); i += len(op); break
        else:
            i += 1
    return toks


def _c_parse(toks):
    P = _Parser(toks, _C_OPCLASS, block_kind="brace")

    def expr():
        return _expr(P, ["&&", "||"])

    def block():
        if not P.acc("OP", "{"):
            return stmt()                                        # single-statement body
        st = []
        while P.pk() != ("OP", "}") and P.pk()[0] != "EOF":
            st.append(stmt())
        P.acc("OP", "}"); return ("GROUP", st)

    def _is_type():
        return P.pk() == ("KW",) or (P.pk()[0] == "KW" and P.pk()[1] in _C_TYPES)

    def stmt():
        k, v = P.pk()
        if (k, v) == ("OP", "{"):
            return block()
        if (k, v) == ("KW", "if"):
            P.eat(); P.acc("OP", "("); t = expr(); P.acc("OP", ")"); body = block(); orelse = []
            if P.pk() == ("KW", "else"):
                P.eat(); orelse = [block()]
            return ("C(branch)", [t, body] + orelse)
        if (k, v) == ("KW", "for"):
            P.eat(); P.acc("OP", "(")
            parts = []
            while P.pk() != ("OP", ")") and P.pk()[0] != "EOF":   # init ; cond ; step
                if P.pk() == ("OP", ";"):
                    P.eat(); continue
                parts.append(simple());
                P.acc("OP", ";")
            P.acc("OP", ")"); return ("I(loop)", parts + [block()])
        if (k, v) == ("KW", "while"):
            P.eat(); P.acc("OP", "("); t = expr(); P.acc("OP", ")"); return ("I(loop)", [t, block()])
        if (k, v) == ("KW", "return"):
            P.eat(); val = expr() if P.pk() != ("OP", ";") else ("OPERAND", []); P.acc("OP", ";"); return ("RET", [val])
        # type-led: a declaration / function def
        if k == "KW" and v in _C_TYPES:
            while P.pk()[0] == "KW" and P.pk()[1] in _C_TYPES:
                P.eat()
            P.acc("OP", "*")                                     # pointer return type
            name = P.acc("NAME")
            if P.pk() == ("OP", "("):                            # function def: type NAME ( params ) { body }
                P.eat(); params = []
                while P.pk() != ("OP", ")") and P.pk()[0] != "EOF":
                    if P.acc("NAME"):
                        params.append(("OPERAND", []))
                    if P.pk()[0] == "KW":
                        P.eat()
                    P.acc("OP", ",")
                P.acc("OP", ")")
                if P.pk() == ("OP", "{"):
                    return ("DEF", params + [block()])
                P.acc("OP", ";"); return ("DEF", params)
            if P.pk() == ("OP", "="):                            # typed assignment
                P.eat(); val = expr(); P.acc("OP", ";"); return ("A(assign)", [val])
            P.acc("OP", ";"); return ("A(assign)", [])
        s = simple(); P.acc("OP", ";"); return s

    def simple():
        lhs = expr()
        if P.pk() == ("OP", "="):
            P.eat(); return ("A(assign)", [lhs, expr()])
        if P.pk()[0] == "OP" and P.pk()[1] in ("+=", "-=", "*=", "/="):
            P.eat(); return ("A(assign)", [lhs, expr()])
        return ("Expr", [lhs])

    out = []
    while P.pk()[0] != "EOF":
        out.append(stmt())
    return ("GROUP", out)


# ============================ LaTeX-math (command/brace/^_ grammar) ============================
_TEX_CMDCLASS = {"\\frac": "N(ratio)", "\\sqrt": "N(root)", "\\cdot": "M(product)", "\\times": "M(product)",
                 "\\sum": "I(sum)", "\\int": "I(integral)", "\\prod": "M(product)"}
_TEX_OPCLASS = {"+": "ALU(add)", "-": "ALU(sub)", "*": "M(product)", "=": "K(equation)", "/": "N(ratio)"}


def _tex_tokens(src):
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\n":
            i += 1; continue
        if c == "\\":
            j = i + 1
            while j < n and src[j].isalpha():
                j += 1
            toks.append(("CMD", src[i:j])); i = j; continue
        if c.isdigit():
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                j += 1
            toks.append(("NUM", src[i:j])); i = j; continue
        if c.isalpha():
            toks.append(("NAME", c)); i += 1; continue           # each math letter is a symbol
        if c in "{}^_+-*=/()":
            toks.append(("OP", c)); i += 1; continue
        i += 1
    return toks


def _tex_parse(toks):
    P = _Parser(toks, _TEX_OPCLASS)

    def group():
        if P.acc("OP", "{"):
            e = additive()
            while P.pk() != ("OP", "}") and P.pk()[0] != "EOF":
                e = ("GROUP", [e, additive()])
            P.acc("OP", "}"); return e
        return atom()

    def atom():
        k, v = P.pk()
        if k == "CMD":
            P.eat()
            cls = _TEX_CMDCLASS.get(v, "CMD")
            args = []
            while P.pk() == ("OP", "{"):
                args.append(group())
            return (cls, args or [("OPERAND", [])])
        if (k, v) == ("OP", "("):
            P.eat(); e = additive(); P.acc("OP", ")"); return e
        if k == "NUM":
            P.eat(); return ("CONST", [])
        if k == "NAME":
            P.eat(); return ("OPERAND", [])
        P.eat(); return ("OPERAND", [])

    def power():
        node = group()
        while P.pk()[0] == "OP" and P.pk()[1] in ("^", "_"):
            op = P.eat()[1]; cls = "Jpow(power)" if op == "^" else "subscript"
            node = (cls, [node, group()])
        return node

    def mul():
        node = power()
        while (P.pk()[0] == "OP" and P.pk()[1] in ("*", "/")) or P.pk()[0] in ("NAME", "NUM", "CMD") or P.pk() == ("OP", "("):
            if P.pk()[0] == "OP" and P.pk()[1] in ("*", "/"):
                op = P.eat()[1]; node = (_TEX_OPCLASS[op], [node, power()])
            else:                                                # implicit multiplication (mc, 2x)
                node = ("M(product)", [node, power()])
        return node

    def additive():
        node = mul()
        while P.pk()[0] == "OP" and P.pk()[1] in ("+", "-", "="):
            op = P.eat()[1]; node = (_TEX_OPCLASS[op], [node, mul()])
        return node

    out = []
    while P.pk()[0] != "EOF":
        before = P.i
        out.append(additive())
        if P.i == before:
            P.eat()
    return ("GROUP", out) if len(out) != 1 else out[0]


# ============================ public API (genome-facing) ============================
_PARSERS = {"python": (_py_tokens, _py_parse), "c": (_c_tokens, _c_parse), "latex": (_tex_tokens, _tex_parse)}


def detect_language(src):
    s = src.strip()
    if ("{" in s and ";" in s) or "#include" in s or any((t + " ") in s for t in _C_TYPES):
        return "c"
    if "def " in s or "\n    " in s or s.startswith(("for ", "while ", "if ", "return ", "import ")):
        return "python"
    if "\\" in s or "$" in s or "^" in s:                        # math markers (after c/python ruled out)
        return "latex"
    return "python"


def parse(src, lang=None):
    lang = lang or detect_language(src)
    tok, prs = _PARSERS[lang]
    return lang, prs(tok(src.replace("$", "")))


def code_sig(src, lang=None):
    return sig(parse(src, lang)[1])


def structural_read(src, lang=None):
    """Siona's structural understanding of code/math: the A-N construct classes present + a one-line description."""
    lang, tree = parse(src, lang)
    cls = [c for c in classes_in(tree) if c not in ("GROUP", "OPERAND", "CONST", "Expr", "CMD")]
    return lang, cls, f"a {lang} fragment built from: {', '.join(cls) or '(operands only)'}"


def main():
    print(f"=== R-RBS-LM-RULEKERNELS — dep-free Python/C/LaTeX rule kernels (srmech {srmech.__version__}) ===\n")
    cases = {
        "python": ("def f(a,b):\n    return a+b", "def g(x,y):\n    return x+y"),
        "c":      ("int f(int a, int b){ return a + b; }", "int g(int x, int y){ return x + y; }"),
        "latex":  (r"\frac{a}{b} + \frac{c}{d}", r"\frac{p}{q} + \frac{r}{s}"),
    }
    for lang, (s1, s2) in cases.items():
        rinv = similarity(code_sig(s1, lang), code_sig(s2, lang))
        _, cls, desc = structural_read(s1, lang)
        print(f"[{lang:6}] rename/symbol-invariance = {rinv:+.4f}  | read: {desc}")
    print("\n[detect] auto-language:")
    for s in ("def h(xs):\n    return sum(xs)", "int main(){ return 0; }", r"E = m c^2"):
        print(f"    {detect_language(s):6} <- {s.splitlines()[0][:34]!r}")
    print("\n[structural read of E=mc^2]:", structural_read(r"E = m c^2", "latex")[1])
    print("\nVERDICT: three dep-FREE rule kernels (our own grammars; no ast/sympy/pycparser) — genuine RBS-HDC")
    print("  instruments on the srmech substrate. Symbol-invariant + structural. Genome-importable for Siona.")


if __name__ == "__main__":
    main()
