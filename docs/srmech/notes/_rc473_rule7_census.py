"""rc473 stage C (`#T1188`) — the Rule-7 census the audit document never had.

``c/JPL_AUDIT.md`` recorded Rule 7 as *"Violations: 0 / Pass"* with a
four-function evidence table, while 24 discarded ``srmech_status_t`` values sat
in ``c/src``. When this script was written there was no Rule-7 detector in
``tests/test_jpl_audit.py`` at all — its test functions named Rules 1, 3, 4, 5,
8 and 9, and the string ``RULE_7`` did not appear in the file — so nothing
contradicted the sentence. This script measures what the document should have
said.

⚠️ **That paragraph read in the present tense until the rc473 pre-publish pass
shipped the ratchet** (A4: ``RULE_7_NODISCARD_ROSTER`` + two down-only ceilings
+ a vacuity seed + four ``test_rule_7_*`` functions). The two ``jpl_audit_*``
fields this script emits are exactly the reading that had to move, and they
did: ``[] -> ["RULE_7", "RULE_7_NODISCARD_ROSTER", "RULE_7_VACUITY_SEEDS"]``
and ``[] -> the four test names``. Both were written as an instrument that
could return otherwise, and it returned otherwise the first time it was asked.

⚠️ **And that first reading was SHORT, which is this rc's own defect class a
third time.** The symbol pattern below was ``\\bRULE_7\\w*``, and ``\\b`` does
not match between ``L`` and ``R`` — so ``CEIL_RULE_7_SRC`` and
``CEIL_RULE_7_TEST``, the two down-only ceilings that ARE the ratchet, were
invisible to it while three other symbols were found. A reader that returns a
non-empty short list reads as a complete list. Widened to allow a leading
``[A-Z_]*``; the same anchoring defect is already recorded twice in this rc, at
``_SCALAR_DECL``'s ``^srmech_status_t`` and at ``_rc473_nodiscard_plant.py``'s
roster pattern.

⚠️ **And the WIDENED reading was LONG, which is the same defect from the other
side.** This reader took ``test_jpl_audit.py`` UNMASKED while masking its own C
scan two functions away, so the bare token ``RULE_7`` inside that file's
comment *"# string `RULE_7` zero times — so nothing was positioned to
contradict that"* was counted as a symbol: **eleven** reported where **ten**
identifiers exist, and **three** under the narrow pattern where **two** do. The
census of the ratchet was counting the sentence that says the string appeared
zero times. Masked at the A6 repair pass with ``_mask_python`` (``tokenize``,
not a regex — the thing being masked is a docstring containing the token) and
verified against ``ast``: ten identifiers contain ``RULE_7`` and bare
``RULE_7`` is not one of them. A census that counts prose and a grep that
cannot spell its own symbol fail the same way, and this rc has now committed
both.

Three populations, each with its predicate written out:

  1. **The rc473 family** — a discarded return from one of the seven Class-N
     double callees rc473 repaired. Predicate: ``(void)NAME(`` anywhere on a
     line, over ``c/src/*.c``, ``c/test/*.c``, ``c/tools/*.c``.
  2. **Every ``SRMECH_NODISCARD``-tagged declaration** in ``c/include/srmech.h``
     — the compiler-enforced half of the rule. A discard of one of these is a
     ``-Werror=unused-result`` build failure on gcc and clang for a BARE
     statement discard, and **on gcc alone** for the ``(void)``-cast form —
     which is the form all twenty-four sites rc473 repaired took. clang reads
     an explicit cast as an acknowledgement and emits nothing even under
     ``-Wunused-result -Werror``. Under ``_MSC_VER`` the macro expands empty
     and neither form is diagnosed. (This line said "on gcc and clang"
     unqualified until the A6 repair pass; the A2 pass MEASURED the form split
     and swept five surfaces without reaching this one — the script whose own
     output the CHANGELOG entry quotes.)
  3. **Every other ``(void)srmech_*(`` discard in the C tree** — the residual
     the document owes a reason for, enumerated by symbol so it can be read.

⚠️ THE SCAN IS MASKED, AND THE UNMASKED RUN IS WHY. Run without masking, this
census reported **1** family discard: ``c/test/test_srmech_value_status_rc473.c``
line 55, which is the bad spelling QUOTED inside that file's own block comment
explaining what it is. A prose hit in a census of code is the same defect class
the tree's own JPL scanner carries ``_mask_c_literals`` to avoid.

Run:  python3 notes/_rc473_rule7_census.py           (no srmech import needed)
Writes ``notes/_rc473_rule7_census.ndjson``.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "c"

#: The seven double callees rc473 repaired. Spelled in full: the rc473 history
#: records a scoping grep that spelled ``srmech_sqrt`` where the symbol is
#: ``srmech_rational_sqrt``, which hid two whole files from the count.
_FAMILY = ("srmech_sin", "srmech_cos", "srmech_atan", "srmech_atan2",
           "srmech_exp", "srmech_log", "srmech_rational_sqrt")

_FAMILY_DISCARD = re.compile(r"\(void\)\s*(" + "|".join(_FAMILY) + r")\s*\(")
_ANY_DISCARD = re.compile(r"\(void\)\s*(srmech_[A-Za-z0-9_]+)\s*\(")
_NODISCARD_DECL = re.compile(
    r"^SRMECH_NODISCARD\s+srmech_status_t\s+(srmech_[A-Za-z0-9_]+)\(", re.M)

_LINE_COMMENT = re.compile(r"//.*$")
_BLOCK_ONE_LINE = re.compile(r"/\*.*?\*/")
_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
_CHAR = re.compile(r"'(?:\\.|[^'\\])*'")


def mask_lines(text: str) -> list[str]:
    """Return the file's lines with comments and literals blanked out.

    Line-oriented so no newline character is ever compared: a block-comment
    depth flag carries across lines, and everything inside a comment becomes
    an empty line. Line count is preserved so ``file:line`` stays truthful.
    """
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        if in_block:
            end = line.find("*/")
            if end < 0:
                out.append("")
                continue
            line = line[end + 2:]
            in_block = False
        line = _BLOCK_ONE_LINE.sub(" ", line)
        start = line.find("/*")
        if start >= 0:
            in_block = True
            line = line[:start]
        line = _LINE_COMMENT.sub("", line)
        line = _STRING.sub('""', line)
        line = _CHAR.sub("''", line)
        out.append(line)
    return out


def _mask_python(text: str) -> str:
    """Blank out Python comments and string/bytes literals, newlines kept.

    ``tokenize`` rather than a regex, because the thing being masked is a
    docstring that CONTAINS the token being counted, and a regex over quotes
    cannot see a triple-quoted block reliably. Anything that fails to tokenize
    is returned unmasked rather than silently half-masked — a partial mask
    reads exactly like a complete one, which is this rc's own defect class.
    """
    import io
    import tokenize

    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    lines = text.splitlines(keepends=True)
    out = list(lines)
    for tok in toks:
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (r1, c1), (r2, c2) = tok.start, tok.end
        for r in range(r1, r2 + 1):
            line = out[r - 1]
            body = line.rstrip("\r\n")
            tail = line[len(body):]
            a = c1 if r == r1 else 0
            b = c2 if r == r2 else len(body)
            b = min(b, len(body))
            if a >= b:
                continue
            out[r - 1] = body[:a] + " " * (b - a) + body[b:] + tail
    return "".join(out)


def _sources() -> list[Path]:
    out: list[Path] = []
    for sub in ("src", "test", "tools"):
        d = C / sub
        if d.is_dir():
            out += sorted(d.glob("*.c"))
    return out


def main() -> int:
    rows: list[dict] = []
    family_hits: list[str] = []
    other_hits: Counter = Counter()
    other_sites: list[str] = []
    per_dir: Counter = Counter()

    files = _sources()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        per_dir[path.parent.name] += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(mask_lines(text), 1):
            for m in _FAMILY_DISCARD.finditer(line):
                family_hits.append(f"{rel}:{lineno} {m.group(1)}")
            for m in _ANY_DISCARD.finditer(line):
                if m.group(1) in _FAMILY:
                    continue
                other_hits[m.group(1)] += 1
                other_sites.append(f"{rel}:{lineno} {m.group(1)}")

    header_text = (C / "include" / "srmech.h").read_text(encoding="utf-8")
    header_masked = "\n".join(mask_lines(header_text))
    tagged = sorted(set(_NODISCARD_DECL.findall(header_masked)))

    jpl_raw = (ROOT / "python" / "tests" / "test_jpl_audit.py").read_text(
        encoding="utf-8")
    # MASKED before the symbol scan, for the same reason the C scan is masked
    # (see the module docstring's masking note). Unmasked, this reader counted
    # the bare token `RULE_7` inside the comment "# string `RULE_7` zero times
    # — so nothing was positioned to contradict that" as a SYMBOL: it reported
    # ELEVEN where ten identifiers exist, so the census of the ratchet was
    # literally counting the sentence that says the string appeared zero
    # times. Corrected at the A6 repair pass; verified against ast, which
    # finds ten identifiers containing RULE_7 and says bare `RULE_7` is not
    # one of them.
    jpl = _mask_python(jpl_raw)
    # `[A-Z_]*` prefix, not a bare `\b`: `\b` does not match between the `L` of
    # CEIL and the `R` of RULE_7, so the two down-only ceilings — the ratchet
    # itself — were invisible to the first spelling. See the module docstring.
    rule7_symbols = sorted(set(re.findall(r"\b[A-Z_]*RULE_7\w*", jpl)))
    rule7_tests = sorted(set(re.findall(r"def (test_\w*rule_7\w*)", jpl)))

    rows.append({
        "kind": "rule7_census",
        "c_files_scanned": len(files),
        "files_per_dir": dict(per_dir),
        "family_discards_masked": len(family_hits),
        "family_sites": family_hits,
        "nodiscard_tagged_decls": len(tagged),
        "nodiscard_names": tagged,
        "other_srmech_discards": sum(other_hits.values()),
        "other_by_symbol": dict(other_hits.most_common()),
        "jpl_audit_RULE_7_symbols": rule7_symbols,
        "jpl_audit_rule_7_tests": rule7_tests,
    })
    rows.append({"kind": "other_discard_sites", "sites": other_sites})

    print(json.dumps(rows[0], indent=2, sort_keys=True))
    print(f"\nother-discard sites listed: {len(other_sites)}")

    dest = Path(__file__).resolve().parent / "_rc473_rule7_census.ndjson"
    with dest.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"wrote {len(rows)} rows -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
