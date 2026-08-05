"""rc404 (`#T1069`) — the down-only ratchet on the OVERFLOW/LIMIT conflation.

WHAT IS BEING RATCHETED. Through rc403 the C tree used ``SRMECH_ERR_OVERFLOW``
for two conditions a caller must tell apart: "the buffer YOU supplied was too
small" (grow and retry) and "this bound is structural — an unrepresentable
value, a compiled-in cap, a non-convergent iteration" (retrying is futile).
rc404 adds ``SRMECH_ERR_LIMIT = 8`` for the second and migrates ONE MEASURED
SLICE — ``srmech_json.c`` and ``srmech_toml.c`` — where a live cost defect was
measured. The rest of the tree still conflates them. This file makes that
residue VISIBLE and MONOTONE so it drains instead of drifting.

WHY THE CEILING IS ON LINES AND NOT ON FILES
--------------------------------------------
A file-level ceiling was the obvious first design and it is **arithmetically
impossible**. Measured across the rc404 migration:

======================================================  ======  ======
metric                                                   rc403   rc404
======================================================  ======  ======
``.c`` files MENTIONING ``SRMECH_ERR_OVERFLOW``             98      98
``.c`` files with a ``return SRMECH_ERR_OVERFLOW``          95      95
``return SRMECH_ERR_OVERFLOW`` LINES                       720     706
``srmech_json.c`` returns                                   15      10
``srmech_toml.c`` returns                                   10       1
======================================================  ======  ======

The file count **cannot move**, because both migrated files deliberately RETAIN
their buffer-class returns — 10 and 1, which is exactly ``DRAINED_EXACT`` below.
A file with even one remaining return is still counted by any file-level grep,
so a file-level pin would either sit forever at 98/95 (measuring nothing) or be
set to a number the tree can never reach (reddening rc404 itself).

The alternative reading — "files still returning OVERFLOW for a NON-BUFFER
reason" — is not mechanically decidable. Classifying a given return line as
buffer-class or structural is precisely the human judgement this rc performs by
hand, one site at a time. No grep computes it. Note also that 98 and 95 are
different populations: 98 files MENTION the token, 95 RETURN it. Conflating
"mention" with "return" is its own measurement error.

So the ceiling counts LINES, which do move, monotonically, and are decidable.

WHAT EACH HALF CATCHES
----------------------
* ``DRAINED_EXACT`` is an EXACT pin, both directions. Adding an eleventh bare
  ``return SRMECH_ERR_OVERFLOW`` to ``srmech_json.c`` reds it — which is the
  point: these two files have been adjudicated line by line, so a NEW status-4
  return in them is a claim that needs its own justification, not a default.
* ``CEIL_CONFLATING_RETURN_LINES`` is DOWN-ONLY. It reds if the tree-wide count
  grows, and it reds with a "lower the ratchet" message if it shrinks — so a
  future slice cannot land without recording its own progress.

COUNTING RULE. Block comments are stripped before counting, because a
``return SRMECH_ERR_OVERFLOW`` inside a ``/* ... */`` narration is prose, not a
producer site. Measured at rc404: **2** such lines (``srmech_ndjson.c`` and
``srmech_rational.c``), neither in the migrated slice. A raw grep therefore
reads 2 high; this file's counter strips them and pins the stripped number.

KNOWN REMAINING CONFLATION, named so it is not mistaken for done: ``srmech.h``
documents ``SRMECH_ERR_OVERFLOW`` as a "bounded buffer overflow guard", and
that is still FALSE for the ~700 unmigrated sites — for instance
``srmech_ndjson.c`` returns it for a line exceeding
``SRMECH_NDJSON_MAX_LINE_BYTES``, a compiled-in structural cap that is
LIMIT-class by rc404's own rule. The comment becomes true when the ratchet
reaches the buffer-only floor, not at rc404.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: ``docs/srmech/c/src``. ``parents[2]`` is ``docs/srmech``, which reaches ABOVE
#: ``docs/srmech/python`` — hence the mandatory SCAN_ROOTS declaration in
#: tests/test_ref_notation_emitted_rc348.py (``("docs/srmech/c",)``).
_C_SRC_DIR = Path(__file__).resolve().parents[2] / "c" / "src"

#: EXACT pin: the buffer-class returns that SURVIVE in the migrated slice.
#: These two files were adjudicated site by site in rc404, so both a new
#: status-4 return and the loss of a legitimate one must be deliberate.
DRAINED_EXACT = {
    # json: the arena / output-buffer returns. The structural six (the
    # tmp[64] staging bound, strtoll ERANGE, the >int64 guard, uint32
    # child-count saturation, and both depth caps) moved to LIMIT.
    "srmech_json.c": 10,
    # toml: exactly ONE survivor — genuine arena exhaustion in
    # toml_arena_alloc. Its compound partner (a saturated toml_align_up,
    # which no arena satisfies) split off to LIMIT, as did the other nine.
    "srmech_toml.c": 1,
}

#: DOWN-ONLY CEIL on tree-wide ``return SRMECH_ERR_OVERFLOW`` LINES, comments
#: stripped. rc403 measured 718 (720 raw, less 2 inside block comments);
#: rc404 migrates 14 of them, landing at 704.
CEIL_CONFLATING_RETURN_LINES = 704

_RETURN_OVERFLOW = re.compile(r"return\s+SRMECH_ERR_OVERFLOW\s*;")


def _strip_comments(text: str) -> str:
    """Blank out C comments, PRESERVING newlines so line counts stay honest.

    STRING- AND CHAR-LITERAL AWARE, and that is not pedantry — a regex-only
    stripper measures this tree WRONG. ``srmech_platform.c`` builds the Windows
    FindFirstFile glob with::

        int w = snprintf(pattern, sizeof(pattern), "%s/*", path);
        if (w < 0 || (size_t)w >= sizeof(pattern)) { return SRMECH_ERR_OVERFLOW; }

    The ``/*`` there is inside a STRING LITERAL. A naive ``/\\*.*?\\*/`` with
    DOTALL treats it as a comment opener, runs to the next ``*/`` somewhere
    below, and blanks the live ``return`` on the following line — silently
    under-counting by one and leaving a real conflating site unprotected by the
    ceiling. The scan below tracks literal state, so that line is counted.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "*":                      # block comment
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        elif c == "/" and nxt == "/":                    # line comment
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif c in ('"', "'"):                            # literal: copy verbatim
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(text[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _count_returns(path: Path) -> int:
    text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    return len(_RETURN_OVERFLOW.findall(text))


pytestmark = pytest.mark.skipif(
    not _C_SRC_DIR.exists(),
    reason=f"C sources not present at {_C_SRC_DIR} (pure-wheel checkout)",
)


def test_migrated_slice_holds_exactly_its_buffer_returns() -> None:
    """The two rc404-migrated files keep EXACTLY their buffer-class returns."""
    for name, expected in sorted(DRAINED_EXACT.items()):
        path = _C_SRC_DIR / name
        assert path.exists(), f"{name} is missing from {_C_SRC_DIR}"
        actual = _count_returns(path)
        assert actual == expected, (
            f"{name}: expected exactly {expected} `return SRMECH_ERR_OVERFLOW` "
            f"(the buffer-class survivors adjudicated in rc404), found {actual}.\n"
            f"  MORE than {expected}: a new status-4 return landed in a file "
            f"whose sites were classified one by one. If the new return really "
            f"is a caller-supplied-buffer failure, raise the number here and say "
            f"why. If growing the caller's arena cannot fix it, it is "
            f"SRMECH_ERR_LIMIT.\n"
            f"  FEWER than {expected}: a legitimate retryable return was "
            f"removed or re-statused; every caller grow-loop keys on status 4, "
            f"so lower this number only with the loop audited."
        )


def test_conflating_return_lines_ratchet_down_only() -> None:
    """Tree-wide status-4 returns may only DECREASE."""
    per_file = {
        path.name: _count_returns(path)
        for path in sorted(_C_SRC_DIR.glob("*.c"))
    }
    total = sum(per_file.values())
    worst = sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    worst_text = ", ".join(f"{n}={c}" for n, c in worst if c)

    assert total <= CEIL_CONFLATING_RETURN_LINES, (
        f"`return SRMECH_ERR_OVERFLOW` lines rose to {total}, above the "
        f"down-only ceiling {CEIL_CONFLATING_RETURN_LINES}.\n"
        f"Heaviest files: {worst_text}.\n"
        f"Status 4 means ONE thing as of rc404: a caller-supplied buffer was "
        f"too small and GROWING IT IS THE FIX. If the new site is a value "
        f"outside a representable range, a compiled-in cap, or a "
        f"non-convergent iteration, it is SRMECH_ERR_LIMIT — returning 4 there "
        f"makes a caller's grow-loop allocate its way to a verdict that was "
        f"fixed before it started."
    )

    assert total == CEIL_CONFLATING_RETURN_LINES, (
        f"GOOD NEWS — status-4 returns fell to {total}, below the ceiling "
        f"{CEIL_CONFLATING_RETURN_LINES}. Lower CEIL_CONFLATING_RETURN_LINES "
        f"to {total} so the progress is locked in and cannot silently reverse."
    )


def test_the_counter_ignores_commented_out_returns() -> None:
    """The instrument must not count prose — proven, not asserted.

    Without this, a docs-only edit could move the ceiling, and the ratchet
    would be measuring narration rather than producer sites.
    """
    sample = (
        "int f(void) {\n"
        "    /* historical: this used to `return SRMECH_ERR_OVERFLOW;` here */\n"
        "    // return SRMECH_ERR_OVERFLOW;\n"
        "    return SRMECH_ERR_OVERFLOW;\n"
        "}\n"
    )
    stripped = _strip_comments(sample)
    assert len(_RETURN_OVERFLOW.findall(stripped)) == 1, (
        "the comment-stripping counter is broken: it must count the ONE live "
        "return and neither of the two commented ones"
    )
    # Line-count preservation matters for any future line-number reporting.
    assert stripped.count("\n") == sample.count("\n")

    # And it must still SEE a live return — an instrument that counts zero
    # everywhere would satisfy the ceiling vacuously.
    assert _count_returns(_C_SRC_DIR / "srmech_json.c") > 0


def test_counter_is_string_literal_aware() -> None:
    """A ``/*`` inside a STRING LITERAL must not open a comment.

    This is a REGRESSION GUARD on the instrument, not on the library. The
    obvious ``/\\*.*?\\*/`` stripper gets this wrong on real srmech source:
    ``srmech_platform.c`` writes ``snprintf(pattern, ..., "%s/*", path)`` for
    the Windows FindFirstFile glob, and a regex stripper swallows from that
    literal to the next ``*/``, blanking the live ``return
    SRMECH_ERR_OVERFLOW;`` on the very next line. The ceiling would then be set
    one too low and one genuine conflating site would sit outside it.
    """
    sample = (
        'int w = snprintf(pattern, sizeof(pattern), "%s/*", path);\n'
        "if (w < 0) { return SRMECH_ERR_OVERFLOW; }\n"
        "/* a genuine comment */\n"
        "int later = 1;\n"
    )
    stripped = _strip_comments(sample)
    assert len(_RETURN_OVERFLOW.findall(stripped)) == 1, (
        "a `/*` inside a string literal was treated as a comment opener, "
        "blanking the live return on the following line"
    )
    assert "int later = 1;" in stripped, (
        "code after the literal was swallowed by a phantom comment"
    )

    # The real file this guard is derived from must still contribute its site.
    platform = _C_SRC_DIR / "srmech_platform.c"
    if platform.exists():
        assert _count_returns(platform) >= 1, (
            "srmech_platform.c's live status-4 return vanished from the count "
            "— the literal-aware scan has regressed"
        )
