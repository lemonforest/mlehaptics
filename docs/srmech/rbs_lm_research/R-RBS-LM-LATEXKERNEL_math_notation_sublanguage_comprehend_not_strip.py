r"""R-RBS-LM-LATEXKERNEL (#226) — the LaTeX/math NOTATION as its OWN genome-encoded sublanguage kernel: COMPREHEND a
<math>/{{math}} block into a SYMBOL+RELATION graph, never strip it (user 2026-07-10: "we don't want to strip, we want
our knowledge kernel to understand the sublanguages … create it as its own sublanguage, that lives with programming
languages … our latex etc sublanguages [may not be genome-encoded yet]").

WHY this is the framework's home turf: a math equation IS a relationship graph — the variables are NODES, the operators
(=, \frac, +, ×, ^) are typed EDGES. `E = mc^2` → symbols {E, m, c}, relation E =(equals) m·c². That is EXACTLY the
relational form Siona stores (relational, not distributional). So `understand_latex(src) -> (symbols, relations)` is a
NOTATION→relationship-graph translator, the same shape as understand_markup(text) -> (prose, edges) [F764]. It is a
Class-B/F FORM grammar (TLV-framing + render/dispatch) — a NOTATION parser, no numeric primitive — and the graph it
emits then feeds the Class-L co-occurrence/community encoding (the 3-representation triality).

Sub/superscript LABELS are KEPT so `\sigma_\text{OC}` and `\sigma_\text{SC}` are DISTINCT nodes (they are different
physical quantities) — dropping them (the strip path) would merge two different meanings.

srmech 0.9.0rc207. Pure form-grammar (Class-B/F, like MARKUPGRAMMAR/F764) — no numeric primitive, no Python abs
builtin, no Counter, no CAD. The `latex` chromosome's gene labels are MATH_FORM_CLASSES (sibling to MARKUP_FORM_CLASSES).
Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-LATEXKERNEL_...py
"""
import re

# The language-layer FORM vocabulary — the Class-B/F framing classes the genome's `latex` chromosome carries as gene
# labels (sibling to MARKUPGRAMMAR.MARKUP_FORM_CLASSES; names chosen not to collide with common bare English words).
MATH_FORM_CLASSES = (
    "math_variable", "math_greek", "math_number", "math_binary_op", "math_relation_op",
    "math_fraction", "math_script", "math_accent", "math_function", "math_delimiter", "math_big_op",
)

# Greek letters (command name -> canonical symbol node label).
GREEK = set(("alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi varpi "
             "rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma "
             "Upsilon Phi Psi Omega ell partial nabla infty").split())
# relation operators (the strongest edge: they couple the two sides of the statement) -> canonical reltype.
RELATIONS = {"=": "equals", "\\equiv": "equiv", "\\approx": "approx", "\\sim": "sim", "\\propto": "propto",
             "\\neq": "neq", "\\ne": "neq", "<": "lt", ">": "gt", "\\leq": "leq", "\\le": "leq", "\\geq": "geq",
             "\\ge": "geq", "\\to": "maps", "\\rightarrow": "maps", "\\mapsto": "maps", "\\Rightarrow": "implies",
             "\\iff": "iff", "\\in": "in", "\\subset": "subset", "\\subseteq": "subseteq"}
BINARY = {"+": "add", "-": "sub", "\\pm": "pm", "\\mp": "mp", "\\times": "mul", "\\cdot": "mul", "\\ast": "mul",
          "\\div": "div", "*": "mul", "/": "div", "\\otimes": "tensor", "\\oplus": "dsum", "\\wedge": "wedge"}
ACCENTS = set("hat bar tilde vec dot ddot overline underline widehat widetilde check breve".split())
BIG_OPS = set("sum prod int oint iint iiint lim bigcup bigcap coprod".split())
# pure formatting/spacing commands: UNWRAP (keep any content, drop the command).
FMT = set(("left right displaystyle textstyle scriptstyle mathrm mathbf mathbb mathcal mathit mathsf mathfrak boldsymbol "
           "quad qquad , ; ! : space limits nolimits big Big bigg Bigg bigl bigr biggl biggr operatorname "
           "rm bf it sf tt mbox color textcolor textbf textit texttt textrm textsf mathtt mathnormal scriptscriptstyle "
           "colon bull phantom hphantom vphantom mathstrut strut negthinspace thinspace medspace thickspace "
           "begin end nonumber notag label ").split())     # begin/end: env delimiter (name consumed as a {label})
# --- blind-spot closure (R-RBS-LM-MATHBLINDSPOT, measured over 60,701 real <math> exprs) ---
FUNCTIONS = set(("sqrt log ln lg exp sin cos tan cot sec csc sinh cosh tanh coth arcsin arccos arctan arg deg det dim "
                 "gcd lcm hom ker lim liminf limsup max min sup inf pr binom tbinom dbinom mod pmod bmod").split())
NUMSETS = {"R": "reals", "N": "naturals", "Q": "rationals", "Z": "integers", "C": "complexes", "Complex": "complexes",
           "Reals": "reals", "Naturals": "naturals", "Rationals": "rationals", "Integers": "integers", "H": "quaternions",
           "F": "field", "P": "primes", "mathbbR": "reals"}
CONSTANTS = {"hbar": "hbar", "aleph": "aleph", "beth": "beth", "emptyset": "emptyset", "varnothing": "emptyset",
             "infty": "infty", "partial": "partial", "nabla": "nabla", "Re": "Re", "Im": "Im", "wp": "wp", "top": "top",
             "bot": "bot", "angle": "angle", "ell": "ell", "hslash": "hbar"}
DELIMS = set(("langle rangle lfloor rfloor lceil rceil vert Vert lvert rvert lVert rVert mid nmid backslash "
              "lbrace rbrace lbrack rbrack lgroup rgroup lang rang").split())     # grouping — no graph node
ELLIPSES = set("cdots ldots dots vdots ddots hdots dotsc dotsb dotsm dotsi cdot".split())   # continuation markers
RELATIONS.update({"\\forall": "forall", "\\exists": "exists", "\\nexists": "nexists", "\\implies": "implies",
                  "\\impliedby": "impliedby", "\\models": "models", "\\vdash": "vdash", "\\notin": "notin",
                  "\\ni": "ni", "\\supset": "supset", "\\supseteq": "supseteq", "\\subsetneq": "subsetneq",
                  "\\cong": "cong", "\\simeq": "simeq", "\\perp": "perp", "\\parallel": "parallel", "\\prec": "prec",
                  "\\succ": "succ", "\\ll": "ll", "\\gg": "gg", "\\doteq": "doteq", "\\triangleq": "defeq",
                  "\\Leftrightarrow": "iff", "\\Longrightarrow": "implies", "\\mapsto": "maps"})
BINARY.update({"\\cup": "union", "\\cap": "inter", "\\setminus": "setminus", "\\circ": "compose", "\\bullet": "bullet",
               "\\star": "star", "\\land": "and", "\\lor": "or", "\\wedge": "and", "\\vee": "or", "\\neg": "not",
               "\\lnot": "not", "\\over": "div", "\\odot": "odot", "\\ominus": "ominus", "\\sqcup": "sqcup",
               "\\uplus": "uplus", "\\amalg": "amalg", "\\bigcup": "union", "\\bigcap": "inter"})
_TOK = re.compile(r"\\\\|\\[a-zA-Z]+|\\[^a-zA-Z]|[A-Za-z]|[0-9]+|\^|_|\{|\}|[=<>+\-*/]|\S")


def _text_label(src, i):
    r"""at index i pointing just after '\text' / '\mathrm' etc: read the {label} and return (label, next_index)."""
    j = src.find("{", i)
    if j == -1 or j > i + 2:
        return None, i
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return re.sub(r"[^\w]", "", src[j + 1:k]), k + 1
        k += 1
    return None, i


def _brace_group(s, i):
    r"""skip whitespace at i, then read one balanced {...} group; return (inner, index-after) or (None, i)."""
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s) or s[i] != "{":
        return None, i
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return None, i


def _expand_fracs(src):
    r"""rewrite \frac{a}{b} -> (a)/(b) (innermost resolves on later passes) so a ratio becomes an explicit div op."""
    for _ in range(24):                                    # bounded nesting depth
        m = re.search(r"\\[cdt]?frac\b", src)              # \frac and \dfrac/\tfrac/\cfrac (was \\d?frac — a digit bug)
        if not m:
            break
        g1, k = _brace_group(src, m.end())
        g2, k = _brace_group(src, k)
        if g1 is None or g2 is None:
            src = src[:m.start()] + " " + src[m.end():]     # non-brace \frac: drop the command, keep operands
            continue
        src = src[:m.start()] + "(" + g1 + ")/(" + g2 + ")" + src[k:]
    return src


def understand_latex(src):
    r"""Comprehend a LaTeX math source into a relationship graph. Returns a dict:
        symbols   : ordered unique symbol nodes (variables/greek, with sub/sup labels kept -> sigma_OC != sigma_SC)
        relations : [(left_symbol, reltype, right_symbol)] — statement couplings (=, <, ->) + fraction ratios
        ops       : the operator classes present (the math 'flavor' signature)
        gloss     : the symbol nodes as a token list (so the math CO-OCCURS with the surrounding prose concepts)
    COMPREHEND, not strip: every symbol is kept as a node; the operators become typed edges.
    """
    # 1. strip {{math}}/wiki emphasis noise that rides inline math: ''x''->x, <sub>/<sup> markers -> _ / ^, drop '1='
    src = re.sub(r"^\s*1\s*=", "", src)
    src = src.replace("''", "")
    src = re.sub(r"<sub>(.*?)</sub>", r"_{\1}", src, flags=re.I)
    src = re.sub(r"<sup>(.*?)</sup>", r"^{\1}", src, flags=re.I)
    src = re.sub(r"<[^>]+>", " ", src)
    had_frac = bool(re.search(r"\\[cdt]?frac\b", src))
    src = _expand_fracs(src)                       # \frac{a}{b} -> (a)/(b): the ratio is now an explicit div op

    tokens = []                                   # (klass, value) — the classified notation stream
    i, n = 0, len(src)
    while i < n:
        m = _TOK.match(src, i)
        if not m:
            i += 1; continue
        t = m.group(0); i = m.end()
        if t.startswith("\\"):
            name = t[1:]
            if name == "\\":                                          # row separator inside an environment
                continue
            if name in ("begin", "end", "label", "tag", "ref", "eqref", "cite", "href", "url"):
                _lab, i = _text_label(src, i)                         # consume the {argument} (env name / label) — not math
                continue
            if name in FUNCTIONS:
                tokens.append(("sym", name)); continue                # named function (sin/cos/log/det) = a symbol node
            if name in NUMSETS:
                tokens.append(("sym", NUMSETS[name])); continue        # number set (R/N/Q/Z/C) = a symbol node
            if name in CONSTANTS:
                tokens.append(("sym", CONSTANTS[name])); continue      # constant (hbar/aleph/infty) = a symbol node
            if name in DELIMS or name in ELLIPSES:
                continue                                               # delimiter / continuation — no graph node
            if name in FMT:
                if name in ("text", "mathrm", "mathbf", "operatorname"):
                    lab, i = _text_label(src, i)
                    if lab:
                        tokens.append(("label", lab))
                continue
            if name == "text":
                lab, i = _text_label(src, i)
                if lab:
                    tokens.append(("label", lab))
                continue
            if name == "frac":
                tokens.append(("frac", "\\frac")); continue
            if name in GREEK:
                tokens.append(("sym", name)); continue
            if name in ACCENTS:
                tokens.append(("accent", name)); continue
            if name in BIG_OPS:
                tokens.append((MATH_FORM_CLASSES[10], name)); continue   # math_big_op
            if t in RELATIONS:
                tokens.append(("rel", RELATIONS[t])); continue
            if t in BINARY:
                tokens.append(("bin", BINARY[t])); continue
            tokens.append(("func", name)); continue                      # any other \cmd = a named function/relation
        if t in RELATIONS:
            tokens.append(("rel", RELATIONS[t])); continue
        if t in BINARY:
            tokens.append(("bin", BINARY[t])); continue
        if t in ("^", "_"):
            tokens.append(("script", t)); continue
        if t in ("{", "}"):
            tokens.append(("brace", t)); continue
        if t.isdigit():
            tokens.append(("num", t)); continue
        if t.isalpha():
            tokens.append(("sym", t)); continue
        # other single chars (delimiters ( ) [ ] . , etc.) -> delimiter (ignored for the graph)

    # 2. attach immediate sub/sup labels to the preceding symbol so sigma_OC != sigma_SC
    nodes = []                                    # sequence of symbol-node ids in reading order
    ops_present = set()
    rels_seq = []                                 # ('rel', reltype) markers interleaved at symbol positions
    frac_marks = []                               # index positions where a fraction starts
    k = 0
    while k < len(tokens):
        kl, v = tokens[k]
        if kl == "sym":
            node = v
            j = k + 1
            while j < len(tokens) and tokens[j][0] == "brace":     # skip braces closing an enclosing accent/group
                j += 1
            if j < len(tokens) and tokens[j][0] == "script":       # attach a trailing sub/sup: _X / _{...} / ^{...}
                sc = "_" if tokens[j][1] == "_" else "^"
                j += 1
                if j < len(tokens) and tokens[j] == ("brace", "{"):
                    j += 1; parts = []
                    while j < len(tokens) and tokens[j] != ("brace", "}"):
                        if tokens[j][0] in ("label", "sym", "num"):
                            parts.append(str(tokens[j][1]))
                        j += 1
                    if j < len(tokens):
                        j += 1                                     # consume closing brace
                    if parts:
                        node += sc + "".join(parts)
                elif j < len(tokens) and tokens[j][0] in ("label", "sym", "num"):
                    node += sc + str(tokens[j][1]); j += 1
            nodes.append(("node", node)); k = j; continue
        if kl == "rel":
            nodes.append(("rel", v)); ops_present.add("math_relation_op")
        elif kl == "bin":
            nodes.append(("bin", v)); ops_present.add("math_binary_op")
        elif kl == "frac":
            nodes.append(("frac", "frac")); ops_present.add("math_fraction")
        elif kl == "accent":
            ops_present.add("math_accent")
        elif kl == MATH_FORM_CLASSES[10]:
            ops_present.add("math_big_op")
        elif kl == "func":
            ops_present.add("math_function")
        elif kl == "num":
            ops_present.add("math_number")
        k += 1

    # 3. symbols (unique, order-preserving)
    symbols, seen = [], set()
    for kind, v in nodes:
        if kind == "node" and v not in seen:
            seen.add(v); symbols.append(v)
    # relations: split at relation ops into segments; WITHIN a segment adjacent symbols are joined by their binary op
    # (explicit + - x /, else 'mul' for juxtaposition), and the relation op couples the two segment HEADS (leftmost
    # symbol). So E = mc^2 -> (m,mul,c^2) [the product] + (E,equals,m) [E equals that product] — NOT a false E=c^2.
    relations = []

    def _flush(seg):                                        # emit intra-segment operator edges; return the head symbol
        syms, prev, pend = [], None, None
        for kind, v in seg:
            if kind == "bin":
                pend = v
            elif kind == "node":
                if prev is not None:
                    relations.append((prev, pend or "mul", v))
                prev, pend = v, None; syms.append(v)
        return syms[0] if syms else None

    heads, seg = [], []
    for kind, v in nodes:
        if kind == "rel":
            heads.append(("head", _flush(seg))); heads.append(("rel", v)); seg = []
        elif kind in ("node", "bin"):
            seg.append((kind, v))
    heads.append(("head", _flush(seg)))
    for a in range(0, len(heads) - 2, 2):                   # (head, rel, head) triples -> couple the two sides
        l, rt, r = heads[a][1], heads[a + 1][1], heads[a + 2][1]
        if l and r:
            relations.append((l, rt, r))
    if not relations and len(symbols) >= 2:                 # single expression, no relation/binary op
        for x in range(len(symbols) - 1):
            relations.append((symbols[x], "expr", symbols[x + 1]))
    seen_rel, dedup = set(), []                             # dedupe + drop self-loops (x==y = co-occurrence noise)
    for x, rt, y in relations:
        if x != y and (x, rt, y) not in seen_rel:
            seen_rel.add((x, rt, y)); dedup.append((x, rt, y))
    if had_frac:
        ops_present.add("math_fraction")
    return {"symbols": symbols, "relations": dedup, "ops": sorted(ops_present), "gloss": symbols}


if __name__ == "__main__":
    SAMPLES = [
        r"\alpha = (1 - D) \bar\alpha(\theta_i) + D \bar{\bar\alpha}.",
        r"A =\left ( \frac{1329\times10^{-H/5}}{D} \right ) ^2,",
        r"\hat{\sigma}_\text{OC} = \frac{{\sigma}_\text{OC}}{\pi r^2}",
        r"E = mc^2",
        r"1=''I'' = ''P''/''V''",
        r"0 = d(a, a) \le d(a, b) + d(b, a) = 2d(a, b)",
    ]
    print("=== LATEXKERNEL — comprehend LaTeX/math into a symbol+relation graph (not strip) ===\n")
    for s in SAMPLES:
        r = understand_latex(s)
        print(f"  SRC: {s}")
        print(f"    symbols : {r['symbols']}")
        print(f"    relations: {r['relations']}")
        print(f"    ops     : {r['ops']}\n")
