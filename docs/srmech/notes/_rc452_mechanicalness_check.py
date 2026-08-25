"""rc452 (`#T1166`) — the MECHANICALNESS CHECK, as an instrument rather than a claim.

The ruling's falsification clause has two arms. One is countable (the red set)
and the s1 runner owns it. The other is "any fix that turns out NON-MECHANICAL
re-opens the A-CARRIER placement question" — and the plan left that as a review
assertion with no instrument behind it, which means a semantic rewrite hiding a
non-mechanical repair would be caught only by a human reading a diff.

This reads the ACTUAL diff of rc452's test-side sweep and classifies every
changed line against the allowed patterns:

  P1  subscript -> exact-Q accessor      x[0] -> x.numerator, x[1] -> x.denominator
  P2  return-type pin flip               isinstance(v, tuple) -> isinstance(v, Q)

Anything else is reported as NON-MECHANICAL by name. Declared exceptions must
be listed in :data:`DECLARED_NON_MECHANICAL` with a reason — an exception you
have to write down is a different thing from one you can wave through.

Usage (from the worktree root, with git on PATH)::

    git diff <base>..HEAD -- docs/srmech/python/tests/ | python3 _rc452_mechanicalness_check.py

or pass a diff file as argv[1].
"""
import re
import sys

#: Edits that are deliberately NOT the two patterns. Each needs a reason, and
#: the reason has to survive being read back.
DECLARED_NON_MECHANICAL = {
    "tests/test_asymptotic_calculus_alias.py": (
        "The return-type PIN itself, plus the function RENAME that goes with "
        "it (test_sin_series_truncate_returns_rational_tuple -> "
        "..._returns_exact_q) and the docstring stating the flip. A test whose "
        "NAME asserts 'rational_tuple' while its body asserts Q is a falsehood "
        "that ships in the sdist. Declared, not waved through."),
}

#: Every pattern is normalised to the SAME placeholder on both sides, and ALL
#: of them are applied before the comparison. Applying one at a time was the
#: first shape of this checker and it reported 4 false NON-MECHANICALs, because
#: a line carrying BOTH ``[0]`` and ``[1]`` still held the other subscript after
#: one substitution. An instrument that cannot pass a correct input is not
#: measuring mechanicalness, it is measuring its own arity.
ALLOWED = [
    # P3 FIRST — it is the only MULTI-TOKEN pattern, and P1 would otherwise
    # consume its `[0]` / `[1]` before it could match. (Measured: with P1 first
    # the checker reported the one true P3 line as NON-MECHANICAL.)
    # P3 — subscript-pair to UNPACK, for a HETEROGENEOUS container. Added at
    # rc452-s3 on a measured need, not in advance: the jacobi test builds
    # coefficient lists whose seeds are (num, den) tuples and whose appended
    # elements are Q, so no single accessor spelling reads both. ``f(*t)`` does,
    # since Q defines __iter__ and a 2-tuple does too, and it is exactly
    # equivalent to ``f(t[0], t[1])`` on the old shape. Declared as its own
    # pattern rather than folded into P1, because "we needed a third pattern"
    # is information about the change and hiding it would be the tell.
    (re.compile(r"\(\s*(\w+)\[0\]\s*,\s*\1\[1\]\s*\)"), re.compile(r"\(\s*\*\s*(\w+)\s*\)"),
     "<UNPACK>"),
    # P1 — subscript to exact-Q accessor.
    (re.compile(r"\[0\]"), re.compile(r"\.numerator"), "<NUM>"),
    (re.compile(r"\[1\]"), re.compile(r"\.denominator"), "<DEN>"),
    # P2 — the return-type pin.
    (re.compile(r"isinstance\((.*?),\s*tuple\)"),
     re.compile(r"isinstance\((.*?),\s*Q\)"), "<ISINST>"),
]

#: Only source files carry call sites. A regenerated ledger is an ARTIFACT of
#: the codegen graph, not a hand edit, and holding it to a call-site pattern
#: would make the checker fire on every regen.
SOURCE_SUFFIX = ".py"


def code_lines(lines):
    """Drop comment-only and blank lines.

    A comment carries no behaviour, and this tree requires the reason for a
    change to be written down next to it — so counting explanatory comments as
    non-mechanical edits would penalise exactly the discipline it is meant to
    protect. It does NOT weaken the check: a repair that deletes an assertion
    and adds a comment saying so still shows up, because the DELETED code line
    is still counted and has no partner.
    """
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append(ln)
    return out


def hunks(diff_text):
    """Yield (path, removed_lines, added_lines) per file."""
    path = None
    rem, add = [], []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if path:
                yield path, rem, add
            path, rem, add = None, [], []
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("-") and not line.startswith("---"):
            rem.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            add.append(line[1:])
    if path:
        yield path, rem, add


def classify(path, rem, add):
    """Return (verdict, detail)."""
    short = path.split("docs/srmech/python/", 1)[-1]
    if not path.endswith(SOURCE_SUFFIX):
        return "SKIPPED", "not a source file — generated artifact, no call sites"
    if short in DECLARED_NON_MECHANICAL:
        return "DECLARED", DECLARED_NON_MECHANICAL[short]
    rem, add = code_lines(rem), code_lines(add)
    if len(rem) != len(add):
        return "NON-MECHANICAL", (
            "line count moved (%d removed, %d added) — a pure accessor swap is "
            "1:1" % (len(rem), len(add)))
    for r, a in zip(rem, add):
        nr, na, fired = r, a, False
        for pat_old, pat_new, token in ALLOWED:
            if pat_old.search(nr) or pat_new.search(na):
                fired = True
            nr = pat_old.sub(token, nr)
            na = pat_new.sub(token, na)
        if not fired or nr.strip() != na.strip():
            return "NON-MECHANICAL", (
                "line is not P1 or P2 (normalised: %r vs %r):\n    - %s\n    + %s"
                % (nr.strip(), na.strip(), r.strip(), a.strip()))
    return "MECHANICAL", "%d line(s), all P1/P2" % len(rem)


def main():
    text = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 \
        else sys.stdin.read()
    bad = 0
    n = 0
    for path, rem, add in hunks(text):
        if not rem and not add:
            continue
        n += 1
        verdict, detail = classify(path, rem, add)
        print("%-16s %s\n                 %s" % (verdict, path, detail))
        if verdict == "NON-MECHANICAL":
            bad += 1
    # SELF-CHECK: an instrument that can only say MECHANICAL has measured
    # nothing. Prove it separates, on two lines it has never seen.
    v_good, _ = classify("x/tests/t.py", ["    assert nat[1] > 0"],
                         ["    assert nat.denominator > 0"])
    v_bad, _ = classify("x/tests/t.py", ["    assert nat[1] > 0"],
                        ["    assert True  # silenced"])
    print("\nself-check: accessor-swap -> %s ; silencing rewrite -> %s" % (v_good, v_bad))
    assert v_good == "MECHANICAL" and v_bad == "NON-MECHANICAL", (v_good, v_bad)

    print("%d file(s) inspected, %d NON-MECHANICAL" % (n, bad))
    if bad:
        print("*** A NON-MECHANICAL REPAIR RE-OPENS THE A-CARRIER PLACEMENT "
              "QUESTION. Report it; do not absorb it. ***")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
