"""rc452 (`#T1166`) scratch — retype the nine ToolEntry registrations.

``ToolEntry`` prose is EMITTED into generated files and travels inside the
wheel — ``describe()``, the MCP tool list, the compiled C registry. A
``returns=R("tuple[int, int]", ...)`` on an op that returns ``Q`` is therefore a
falsehood that SHIPS, not documentation drift.

Exact-match with a printed occurrence count per substitution: a silent miss is
impossible. Run from ``docs/srmech/python``.
"""
import ast
import sys

P = "srmech/introspect/tool_schema.py"
raw = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
s = raw.replace("\r\n", "\n")

#: The exact-ℚ return, spelled once so the nine cannot drift apart.
QRET = ('returns=R("Q", "the exact rational, srmech.math.q.Q — rc452 (`#T1166`); '
        'num/den stay recoverable via .numerator / .denominator or `num, den = q`"),')

#: The widened operand spelling. Mirrors C\'s cr_as_rational, which takes a
#: CR_RATIONAL or a 2-int CR_LIST — the pair is an accepted INPUT, not the
#: return contract.
QOP = "Q | tuple[int, int]"

SUBS = [
    # ── the five series ops: returns only (their operands are two bare ints
    #    on BOTH projections — cr_op_series reads two separate CR_INTs — so
    #    there is no pair operand to widen. That is the measured boundary.)
    ('            returns=R("tuple[int, int]", "(out_num, out_den) of S_N reduced to lowest terms"),',
     "            " + QRET, 1),
    # ── the four binary ops: returns AND operands ─────────────────────────
    ('            parameters=(P("a", "tuple[int, int]", True, "(num, den) of first operand"),\n'
     '                        P("b", "tuple[int, int]", True, "(num, den) of second operand")),',
     '            parameters=(P("a", "%s", True, "first operand: a Q, or the (num, den) pair"),\n'
     '                        P("b", "%s", True, "second operand: a Q, or the (num, den) pair")),'
     % (QOP, QOP), 2),
    ('            parameters=(P("a", "tuple[int, int]", True, "(num, den) of dividend"),\n'
     '                        P("b", "tuple[int, int]", True, "(num, den) of divisor")),',
     '            parameters=(P("a", "%s", True, "dividend: a Q, or the (num, den) pair"),\n'
     '                        P("b", "%s", True, "divisor: a Q, or the (num, den) pair")),'
     % (QOP, QOP), 1),
    ('            parameters=(P("base", "tuple[int, int]", True, "(num, den) of base"),',
     '            parameters=(P("base", "%s", True, "base: a Q, or the (num, den) pair"),' % QOP, 1),
    # ── the remaining eight `returns` rows (all identical text) ───────────
    ('            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),',
     "            " + QRET, 8),
]

fail = False
for old, new, want in SUBS:
    got = s.count(old)
    print("  %2d/%2d  %s" % (got, want, old.strip().splitlines()[0][:78]))
    if got != want:
        fail = True
        continue
    s = s.replace(old, new)

if fail:
    print("MISMATCH — nothing written")
    sys.exit(1)

ast.parse(s)
open(P, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("written; parses OK; newline style", repr(nl))
