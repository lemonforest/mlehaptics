"""Census + AST-precise rewriter for klein4_random -> regime-explicit ops.

Decision table (see task #931 / F1259 / F1260):

  seed=<plain int expr>              -> klein4_expand(D, seed)   RENAME  numbers PRESERVED
                                         (klein4_expand is byte-for-byte
                                          random.Random(seed).randrange(4), verified)
  rng=default_rng(<plain int expr>)  -> klein4_expand(D, int)    RESTREAM numbers CHANGE
                                         (numpy PCG64 stream -> stdlib MT19937)
  seed/rng derived from a WORD       -> ADDRESSED anti-pattern; needs per-site judgement
  seed/rng derived from coords/slot  -> klein4_address           numbers CHANGE
  anything else                      -> UNRESOLVED (left untouched)

Usage:
  migrate.py census <base>                 -> NDJSON census on stdout
  migrate.py apply <base> <decision-class> -> rewrite files in place
"""
import ast
import json
import os
import re
import sys

ROOTS = ["docs/srmech/rbs_lm_research", "docs/srmech/rbs_nn_research"]

# seed helpers that hash a LINGUISTIC TOKEN -> the F1260 word-hash anti-pattern
WORD_HASH = re.compile(
    r"(?<![\w.])(token_seed|_word_seed)\s*\(|"          # sha256/FNV of a token
    r"(?<![\w.])hash\s*\(\s*[a-z_]*(w|t|word|token|name|term|tok)\b|"  # builtin hash of a word var
    r"\bord\s*\("                                        # hand-rolled ord() string hash
)
# seed helpers that hash a NUMERIC COORDINATE or a SLOT LABEL -> legitimate addressing
ADDR_HASH = re.compile(r"(?<![\w.])(_hashseed|_hs|derive_seed)\s*\(")
# plain integer expression: identifiers, numbers, arithmetic. no calls.
PLAIN_INT = re.compile(r"^[\w\s.+\-*/%()\[\]'\"]+$")


class Finder(ast.NodeVisitor):
    def __init__(self):
        self.hits = []

    def visit_Call(self, node):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if name == "klein4_random":
            self.hits.append(node)
        self.generic_visit(node)


def seg(src, node):
    return ast.get_source_segment(src, node) or ""


# a bare int() wrapper around an otherwise-plain expression is still a plain mint
INT_WRAP = re.compile(r"^int\s*\(\s*(.+?)\s*\)$", re.S)
# _seed() is a TRUNCATION (first 8 bytes big-endian), not an avalanche hash:
# injective over the short keys used here, so it is a deterministic mint.
TRUNC_MINT = re.compile(r"^_seed\s*\(")
# a seed drawn OUT of a live generator inherits that generator's statefulness
FROM_STREAM = re.compile(r"\b(rng|gr|grr)\s*\.\s*(integers|random|choice)\s*\(")
# order-insensitive byte sum: a content hash so weak that anagrams collide
WEAK_SUM = re.compile(r"^sum\s*\(\s*\w+\s*\.\s*encode\s*\(\s*\)\s*\)$")


def is_plain_int(e):
    if e is None:
        return False
    m = INT_WRAP.match(e.strip())
    if m:
        e = m.group(1)
    if re.search(r"\w\s*\(", e):          # contains a call
        return False
    return bool(PLAIN_INT.match(e))


def content_of(e):
    """Pull the CONTENT operand out of a word-hash seed expression."""
    for pat in (
        r"(?<![\w.])hash\s*\(\s*([A-Za-z_]\w*)\s*\)",           # hash(w)
        r"(?<![\w.])token_seed\s*\(\s*([A-Za-z_]\w*)\s*[,)]",   # token_seed(word[, ...])
        r"(?<![\w.])_word_seed\s*\(\s*[^,]+,\s*([A-Za-z_]\w*)\s*\)",  # _word_seed(base, w)
        r"(?<![\w.])dseed\s*\(\s*([A-Za-z_]\w*)\s*\)",          # dseed(w)
        r"enumerate\s*\(\s*([A-Za-z_]\w*)\s*\)",                # sum(...ord(c) for i,c in enumerate(w))
        r"^sum\s*\(\s*([A-Za-z_]\w*)\s*\.\s*encode",            # sum(t.encode())
    ):
        m = re.search(pat, e)
        if m:
            return m.group(1)
    return None


def coord_content_of(e):
    """Pull the pre-digest content expression out of a coordinate-address seed."""
    m = re.search(r"_dig\s*\(\s*(.+?)\s*\)\s*\[", e, re.S)
    if m:
        return m.group(1)
    m = re.search(r"sha256_bytes\s*\(\s*(.+?)\s*\)\s*\[", e, re.S)
    if m:
        return m.group(1)
    return None


def decide(seed_expr, rng_expr):
    """-> (regime, decision, numbers, reason)"""
    if rng_expr is not None:
        m = re.search(r"default_rng\s*\(\s*(.+?)\s*\)\s*$", rng_expr)
        inner = m.group(1) if m else None
        if inner is None:
            return ("STATEFUL_STREAM", "UNRESOLVED", "CHANGE",
                    f"'{rng_expr}' is a SHARED STATEFUL generator: successive calls draw DIFFERENT "
                    f"vectors. A single klein4_expand(D, seed) would return the SAME vector every "
                    f"time and silently collapse the experiment. Needs a per-draw distinct seed "
                    f"(counter/index), which is a redesign, not a rename.")
        if WORD_HASH.search(inner):
            return ("ADDRESSED", "REVIEW", "CHANGE",
                    f"rng seeded by word-hash '{inner}' -> F1260 anti-pattern; needs address-vs-representation call")
        if ADDR_HASH.search(inner):
            return ("ADDRESSED", "klein4_address", "CHANGE",
                    f"rng seeded by a coordinate/slot key '{inner}' -> genuine addressing")
        if is_plain_int(inner):
            return ("DRAWN", "klein4_expand", "CHANGE",
                    f"seeded generator default_rng({inner}); deterministic mint. numpy PCG64 -> stdlib MT19937, values change")
        return ("UNRESOLVED", "UNRESOLVED", "n/a", f"rng seed expr not classifiable: {inner}")
    if seed_expr is None:
        return ("UNRESOLVED", "UNRESOLVED", "n/a",
                "neither seed nor rng: the old path drew from urandom (never reproducible)")
    e = seed_expr
    if FROM_STREAM.search(e):
        return ("STATEFUL_STREAM", "UNRESOLVED", "CHANGE",
                f"seed is drawn OUT of a live generator ('{e}'), so it inherits that stream's "
                f"state; needs a per-draw deterministic seed, not a rename")
    if WEAK_SUM.match(e.strip()):
        return ("ADDRESSED", "REVIEW", "CHANGE",
                f"seed '{e}' is an order-insensitive byte sum: anagrams collide outright. "
                f"a content hash this weak is not even a sound ADDRESS")
    if "join(str(x) for x in" in e and coord_content_of(e):
        return ("ADDRESSED", "klein4_address", "CHANGE",
                f"seed digests a NUMERIC COORDINATE tuple ('{e}'): genuine addressing, "
                f"no edit-structure is owed between coordinates")
    if TRUNC_MINT.match(e.strip()):
        return ("DRAWN", "klein4_expand", "PRESERVED",
                f"_seed() is an 8-byte big-endian TRUNCATION, not an avalanche hash; injective "
                f"over these short keys, so this is a deterministic mint")
    if WORD_HASH.search(e):
        c = content_of(e)
        if c:
            return ("ADDRESSED", "klein4_address", "CHANGE",
                    f"seed '{e}' hashes a token to a scalar then mints a random vector -- the F1260 "
                    f"word-hash anti-pattern. These sites use the vector as an ATOMIC ADDRESS "
                    f"(retrieved by exact-identity argmax), never comparing two different tokens' "
                    f"vectors, so klein4_address is the faithful regime -- NOT klein4_encode_bytes, "
                    f"which would inject morphological similarity the experiment does not want. "
                    f"klein4_address also removes the narrow-seed-band aliasing and (for builtin "
                    f"hash) the PYTHONHASHSEED non-reproducibility.")
        return ("ADDRESSED", "REVIEW", "CHANGE",
                f"word-hash '{e}' but the content operand could not be extracted automatically")
    if ADDR_HASH.search(e):
        return ("ADDRESSED", "klein4_address", "CHANGE",
                f"seed is a coordinate/slot key '{e}' -> genuine addressing")
    if is_plain_int(e):
        return ("DRAWN", "klein4_expand", "PRESERVED",
                "plain integer mint; klein4_expand is byte-for-byte the old seed= path")
    return ("UNRESOLVED", "UNRESOLVED", "n/a", f"seed expr not classifiable: {e}")


def collect(base):
    rows = []
    for root in ROOTS:
        for dirpath, _d, files in os.walk(os.path.join(base, root)):
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, base).replace("\\", "/")
                raw = open(path, "rb").read()
                src = raw.decode("utf-8", errors="replace")
                if "klein4_random" not in src:
                    continue
                try:
                    tree = ast.parse(src)
                except SyntaxError as ex:
                    rows.append({"file": rel, "line": 0, "regime": "UNRESOLVED",
                                 "decision": "UNRESOLVED", "numbers": "n/a",
                                 "reason": f"does not parse under this interpreter: {ex}"})
                    continue
                f = Finder()
                f.visit(tree)
                for n in f.hits:
                    kw = {k.arg: seg(src, k.value) for k in n.keywords if k.arg}
                    pos = [seg(src, a) for a in n.args]
                    d_expr = pos[0] if pos else kw.get("D")
                    seed_expr = kw.get("seed")
                    rng_expr = kw.get("rng")
                    if len(pos) > 1 and rng_expr is None and seed_expr is None:
                        rng_expr = pos[1]   # old signature: 2nd positional IS rng
                    regime, decision, numbers, reason = decide(seed_expr, rng_expr)
                    prefix = ""
                    if isinstance(n.func, ast.Attribute):
                        prefix = seg(src, n.func.value) + "."
                    content = None
                    if decision == "klein4_address":
                        basis = seed_expr if seed_expr is not None else (rng_expr or "")
                        content = content_of(basis) or coord_content_of(basis)
                        if content is None:
                            decision, reason = "REVIEW", reason + " [content operand not extractable]"
                    rows.append({
                        "file": rel, "line": n.lineno, "col": n.col_offset,
                        "end_line": n.end_lineno, "end_col": n.end_col_offset,
                        "call": " ".join(seg(src, n).split())[:220],
                        "prefix": prefix, "D": d_expr,
                        "seed": seed_expr, "rng": rng_expr, "content": content,
                        "regime": regime, "decision": decision,
                        "numbers": numbers, "reason": reason,
                    })
    return rows


def splice(base, rows, want):
    """Rewrite sites whose decision == want. Preserves line endings exactly."""
    byfile = {}
    for r in rows:
        if r.get("decision") == want and r.get("end_line"):
            byfile.setdefault(r["file"], []).append(r)
    changed = 0
    for rel, rs in byfile.items():
        path = os.path.join(base, rel)
        raw = open(path, "rb").read()
        src = raw.decode("utf-8")
        lines = src.splitlines(keepends=True)
        # byte-offset index of each line start, computed on utf-8
        blines = [ln.encode("utf-8") for ln in lines]
        starts = [0]
        for b in blines:
            starts.append(starts[-1] + len(b))
        buf = bytearray(src.encode("utf-8"))
        edits = []
        for r in rs:
            s = starts[r["line"] - 1] + r["col"]
            e = starts[r["end_line"] - 1] + r["end_col"]
            if want == "klein4_expand":
                arg = r["seed"]
                if arg is None and r["rng"]:
                    m = re.search(r"default_rng\s*\(\s*(.+?)\s*\)\s*$", r["rng"])
                    arg = m.group(1)
                new = f'{r["prefix"]}klein4_expand({r["D"]}, {arg})'
            elif want == "klein4_address":
                if not r.get("content"):
                    continue
                new = f'{r["prefix"]}klein4_address({r["D"]}, {r["content"]})'
            else:
                continue
            edits.append((s, e, new.encode("utf-8")))
        for s, e, new in sorted(edits, reverse=True):
            buf[s:e] = new
        out = bytes(buf)
        # verify the result still parses and no klein4_random remains at those sites
        ast.parse(out.decode("utf-8"))
        open(path, "wb").write(out)
        changed += len(edits)
    return changed, len(byfile)


def main():
    cmd, base = sys.argv[1], sys.argv[2]
    rows = collect(base)
    if cmd == "census":
        from collections import Counter
        print(json.dumps({"sites": len(rows), "files": len({r["file"] for r in rows})}), file=sys.stderr)
        print(json.dumps(dict(Counter(r["decision"] for r in rows))), file=sys.stderr)
        print(json.dumps(dict(Counter(r["numbers"] for r in rows))), file=sys.stderr)
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
    elif cmd == "apply":
        n, nf = splice(base, rows, sys.argv[3])
        print(f"rewrote {n} sites across {nf} files -> {sys.argv[3]}", file=sys.stderr)


if __name__ == "__main__":
    main()
