"""rc452 (`#T1166`) scratch — retype the nine ops' SHIPPED prose in one pass.

Return annotations and the docstring ``Returns``/doctest lines are emitted into
the wheel (``describe()``, the MCP tool list, the compiled C registry), so a
stale ``tuple[int, int]`` there is a shipped falsehood, not a comment. Each
substitution is exact-match and its occurrence count is printed, so a silent
miss is impossible.

Run from ``docs/srmech/python``.
"""
import ast
import sys

P = "srmech/math/rational.py"
raw = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
s = raw.replace("\r\n", "\n")

SUBS = [
    # ── return annotations (9) ────────────────────────────────────────────
    # LONGEST INDENT FIRST — the 24-space form is a SUBSTRING of the 25- and
    # 26-space ones, so counting it first reports 5 where 3 are meant. Caught
    # by the exact-count guard rather than by reading, which is the point of
    # having the guard.
    ("                          num_terms: int) -> Tuple[int, int]:",
     '                          num_terms: int) -> "_QType":', 1),
    ("                         num_terms: int) -> Tuple[int, int]:",
     '                         num_terms: int) -> "_QType":', 1),
    ("                        num_terms: int) -> Tuple[int, int]:",
     '                        num_terms: int) -> "_QType":', 3),
    ("def rational_add(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:",
     'def rational_add(a: "_QOrPair", b: "_QOrPair") -> "_QType":', 1),
    ("def rational_mul(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:",
     'def rational_mul(a: "_QOrPair", b: "_QOrPair") -> "_QType":', 1),
    ("def rational_div(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:",
     'def rational_div(a: "_QOrPair", b: "_QOrPair") -> "_QType":', 1),
    ("def rational_pow_uint(base: Tuple[int, int], exp: int) -> Tuple[int, int]:",
     'def rational_pow_uint(base: "_QOrPair", exp: int) -> "_QType":', 1),
    # ── docstring return declarations ─────────────────────────────────────
    ("    (out_num, out_den) : tuple[int, int]\n"
     "        Reduced rational ``S_N(p/q) = out_num / out_den``. Always\n"
     "        ``out_den > 0`` and ``gcd(|out_num|, out_den) == 1``.",
     "    q : srmech.math.q.Q\n"
     "        Reduced exact rational ``S_N(p/q)``. Always\n"
     "        ``q.denominator > 0`` and ``gcd(|q.numerator|, q.denominator) == 1``.\n"
     "        rc452 (`#T1166`): a ``Q``, not a ``(num, den)`` tuple — the same\n"
     "        exact-ℚ scalar the C peer builds as ``CR_RATIONAL`` and the chain\n"
     "        wire spells ``q``. ``num, den = q`` still unpacks.", 1),
    # ── doctests (they ship; a false example is a false claim) ────────────
    (">>> exp_series_truncate(1, 1, 10)  # S_10(1)\n    (9864101, 3628800)",
     ">>> exp_series_truncate(1, 1, 10)  # S_10(1)\n    Q(9864101, 3628800)", 1),
    (">>> exp_series_truncate(1, 2, 5)   # S_5(0.5)\n    (6331, 3840)",
     ">>> exp_series_truncate(1, 2, 5)   # S_5(0.5)\n    Q(6331, 3840)", 1),
    (">>> exp_series_truncate(0, 1, 5)\n    (1, 1)",
     ">>> exp_series_truncate(0, 1, 5)\n    Q(1, 1)", 1),
    (">>> sin_series_truncate(0, 1, 5)\n    (0, 1)",
     ">>> sin_series_truncate(0, 1, 5)\n    Q(0, 1)", 1),
    (">>> sin_series_truncate(1, 1, 5)[0] / sin_series_truncate(1, 1, 5)[1]",
     ">>> float(sin_series_truncate(1, 1, 5))", 1),
    # ── rational_div's Raises block: the TypeError row is now wrong ───────
    ("    TypeError\n"
     "        If ``a`` or ``b`` is not a 2-element tuple/list ``(num, den)``.",
     "    TypeError\n"
     "        If ``a`` or ``b`` is neither a :class:`~srmech.math.q.Q` nor a\n"
     "        2-element tuple/list ``(num, den)``. rc452 (`#T1166`) widened the\n"
     "        accepted set to mirror C's ``cr_as_rational``, which takes a\n"
     "        ``CR_RATIONAL`` or a 2-int ``CR_LIST``; the CLASS raised on a\n"
     "        malformed operand is unchanged.", 1),
]

fail = False
for old, new, want in SUBS:
    got = s.count(old)
    print("  %2d/%2d  %s" % (got, want, old.splitlines()[0][:78]))
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
