"""rc432 (`#T1132`) — C-SIDE RESOURCE OWNERSHIP: two srmech-LOCAL ratchets.

⚠️ THESE ARE NOT "JPL RULE 11". THERE IS NO JPL RULE 11.
========================================================
Holzmann's Power of Ten has exactly ten rules, and
``test_jpl_audit.py::test_audit_doc_present_and_mentions_all_rules`` iterates
``range(1, 11)`` to prove the audit document covers all of them. Naming a local
invariant "Rule 11" would invent an external authority for a decision this
project made on its own. What follows is **srmech-local** — ratchet-family kin to
the JPL rules, sharing their shape (stdlib-only source scan, collect-then-assert,
allowlists that carry rationale), but not one of them.

WHAT THEY CHECK, AND WHY THE C SIDE GETS A GATE AT ALL
======================================================
Measured across all 137 ``c/src/*.c``: the C library holds **zero** handle leaks
across every held-handle PAL site, with zero ``goto``/``setjmp``/``longjmp``. The
error paths are correct by hand-placed release. That is affordable precisely
because Rule 3 (no malloc) removed almost everything ``goto cleanup;`` exists to
free — remove the resource and the cleanup problem mostly disappears.

But ``test_jpl_audit.py`` checks Rules 1/3/4/5/8 only. **Acquire/release symmetry
was UNGATED**: clean by discipline, not by enforcement. An ungated surface is one
edit away from decaying silently, and the decay would look exactly like working
code. C1 closes that.

⚠️ THE NON-CLAIM — NEITHER GATE WOULD HAVE CAUGHT THE SEED DEFECT
=================================================================
This is worth more than the gates and must not be softened anywhere it is
repeated.

* **C1 is blind to it BY CONSTRUCTION.** Its subject is held handles. The seed
  defect is a CREATED NODE, and ``srmech_genome.c`` makes **zero**
  ``srmech_plat_mkdir`` calls — re-measured by this file's own scan, not
  inherited. There is nothing in C for C1 to look at. C1's live population is 0
  and its known-defect population is 0: it is a strict-zero gate that has never
  had anything to find, and its entire value is PROSPECTIVE.
* **C2 is blind to it too.** It sees created nodes but requires two or more in
  one function. The C peer of the seed makes none; the Python seed makes one.
  C2's single live hit is a DIFFERENT instance that the seed defect did not
  motivate.

C1 is validated by a PLANTED LEAK IN A REAL FILE, so it is not the shape rc430's
D7 shipped — a falsifier that was empty by construction and could never have
returned otherwise. But the distinction has to be said out loud rather than
assumed from a green run.

**These gates detect the REGRESSION, never the original. The repairs produce the
result; the gates only pin it, and the repairs are strictly stronger.**

FURTHER BLIND SPOTS, WRITTEN DOWN SO THE NEXT RC INHERITS THEM
==============================================================
3. C2 requires >= 2 mkdirs in one function. A single unrolled-back ``mkdir`` is
   invisible.
4. Constructor-shaped acquires are out of scope BY CONTRACT (see
   :data:`CONSTRUCTOR_SHAPED`), so a leak in the
   ``stream_listen`` ↔ ``srmech_bus_server_stop`` pairing is invisible to C1.
5. C2's ceiling of 1 is a DEFERRAL PIN, not a clean bill of health. It names
   ``rcut_setup`` and names what `#T1133` must add.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_C_SRC_DIR = _HERE.parent.parent / "c" / "src"

pytestmark = pytest.mark.skipif(
    not _C_SRC_DIR.exists(),
    reason=(
        f"C source tree not present in this checkout ({_C_SRC_DIR} does not "
        f"exist); these are source-scanning ratchets over c/src/*.c"
    ),
)


# ────────────────────────────────────────────────────────────────────────
# Scanning primitives
# ────────────────────────────────────────────────────────────────────────

def _strip_comments_preserving_lines(text: str) -> str:
    """Blank out comments AND literal contents WITHOUT moving a single line.

    ⚠️ THIS IS THE FUNCTION THAT WAS WRONG, AND IT WAS WRONG INVISIBLY.

    The spike's first C scanner reused the Rules-1/3 idiom,
    ``re.sub(r"/\\*.*?\\*/", "", text, flags=re.S)``. That collapses a multi-line
    comment block into nothing and shifts every line after it upward. The scanner
    then reported ``rcut_setup``'s mkdirs at 2398/2400/2402 against a hand-read
    ground truth of 2760/2762/2764 — **a 362-line error in a scanner whose six
    planted controls were all green.** No control could see it, because a control
    is a short synthetic string with no comment blocks in it.

    The Rules-1/3 checks get away with the naive strip because they only ever
    ``findall`` — they report THAT a match exists, never WHERE. **A rule that
    reports a SITE cannot reuse it.** Every newline inside a comment is kept here,
    so a byte offset may move but a line number never does.

    ⚠️ IT WAS WRONG A SECOND TIME, AND FOR A SECOND INVISIBLE REASON
    ----------------------------------------------------------------
    rc432 blanked comments and stopped. But C source is full of braces that are
    not braces — ``if (c == '{') { depth++; }`` — and the downstream brace
    counter believed every one of them. Measured on the rc432 tree:
    ``srmech_genome.c::genome_json_object_span``, a ~25-line function whose whole
    job is to scan for ``'{'`` / ``'}'``, produced a span of **7,610 lines**
    (2426→10036) because its own char literals never let the depth return to
    zero. Since :func:`_function_spans` resumes at ``end + 1``, everything that
    runaway swallowed was skipped outright: **76 spans found where
    ``test_jpl_audit.py::_scan_functions`` finds 295 in the same file** — 219
    function starts lost, silently, with C1 reporting a clean zero over all of
    them.

    So literal CONTENTS are blanked too, delimiters kept. This also fixes the
    quieter twin, a brace inside a string constant (``char *s = "}";``).
    :func:`test_function_spans_agree_with_the_jpl_scanner` is the cross-check
    that would have caught both on the day they were written — an independent
    scanner over the same files, which is the thing no synthetic control could
    supply.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif text[i] in "'\"":
            # A char or string literal. Keep both delimiters so the token still
            # looks like a literal, blank the interior so no brace, quote,
            # ``return`` or symbol name inside it can be mistaken for code.
            quote = text[i]
            j = i + 1
            while j < n and text[j] != quote and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(quote)
            out.append("".join(ch if ch == "\n" else " " for ch in text[i + 1:j]))
            if j < n and text[j] == quote:
                out.append(quote)
                i = j + 1
            else:                        # unterminated at EOL/EOF — leave as-is
                i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _function_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    """``(name, first_body_line_idx, last_body_line_idx)`` per function.

    Same conventions ``test_jpl_audit.py::_scan_functions`` assumes: definitions
    at column 0, body brace on the definition line or shortly after. Not a C
    parser; a brace counter over srmech's own formatting.
    """
    def_pat = re.compile(
        r"^[a-zA-Z_][a-zA-Z_0-9 \t\*]+[ \t\*]([a-zA-Z_][a-zA-Z_0-9]+)\s*\("
    )
    spans: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.rstrip().endswith(";") or not line.strip():
            i += 1
            continue
        m = def_pat.match(line)
        # ⚠️ SAME TWO BLIND SPOTS AS THE JPL SCANNER, fixed the same way at
        # rc447 — and the agreement gate below is what surfaced them: fixing
        # only the JPL side made the two scanners disagree about 40+ functions.
        # (a) an unconditional `static const` skip hides every function
        #     returning a CONST POINTER; an INITIALIZER is what marks const
        #     DATA, so that is the test.
        _const_data = (line.lstrip().startswith("static const")
                       and "=" in line.split("(")[0])
        if m is None or _const_data or line.lstrip().startswith(
                ("typedef", "extern", "#", "}")):
            i += 1
            continue
        body = i
        while body < len(lines) and "{" not in lines[body]:
            if lines[body].rstrip().endswith(";") and body > i:
                body = -1
                break
            body += 1
        # (b) a 9-line brace look-ahead loses any function whose PARAMETER
        #     LIST is long — measured worst case +27 lines
        #     (srmech_cn_vwp_multisum_lhs). 40 covers it with headroom.
        if body < 0 or body >= len(lines) or body - i > 39:
            i += 1
            continue
        depth = lines[body].count("{") - lines[body].count("}")
        end = body
        for j in range(body + 1, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0:
                end = j
                break
        else:
            end = len(lines) - 1
        spans.append((m.group(1), body, end))
        i = end + 1
    return spans


def _depths(lines: list[str], body: int, end: int) -> list[int]:
    """Brace depth at the START of each line in ``[body, end]``, body-relative."""
    out = []
    depth = 0
    for j in range(body, end + 1):
        out.append(depth)
        depth += lines[j].count("{") - lines[j].count("}")
    return out


# ────────────────────────────────────────────────────────────────────────
# C1 — held-handle acquire/release symmetry
# ────────────────────────────────────────────────────────────────────────

#: acquire -> the release that MUST accompany every exit while it is held.
HELD_HANDLE_PAIRS = {
    "srmech_plat_file_open_ro": "srmech_plat_file_close_ro",
    "srmech_plat_rstream_open": "srmech_plat_rstream_close",
    "srmech_plat_dir_open": "srmech_plat_dir_close",
}

#: Acquires whose CONTRACT is to hand a live handle back to the caller — the
#: listen/connect/accept family, closed by ``srmech_bus_server_stop``. Demanding
#: a same-function close would demand they BREAK their own contract. That is a
#: different rule, not a noisier version of this one, and excluding them is a
#: scope statement rather than an exemption.
CONSTRUCTOR_SHAPED = (
    "stream_listen", "tcp_listen", "_connect", "_accept",
)

#: How far past an acquire a bare guard-return may sit and still be read as
#: "the acquisition itself failed, so nothing is held". BOUNDED DELIBERATELY:
#: "the first return, wherever it is" would swallow a genuine leak ten lines
#: downstream, which is the whole class this gate exists for.
OWN_GUARD_WINDOW = 4


def _unsafe_returns_in_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = _strip_comments_preserving_lines(raw).split("\n")
    findings: list[str] = []

    for name, body, end in _function_spans(lines):
        if any(tok in name for tok in CONSTRUCTOR_SHAPED):
            continue
        depths = _depths(lines, body, end)
        for acquire, release in HELD_HANDLE_PAIRS.items():
            for j in range(body, end + 1):
                if acquire + "(" not in lines[j]:
                    continue
                released_unconditionally = False
                for k in range(j + 1, end + 1):
                    has_release = release + "(" in lines[k]
                    # shape (c): a release at FUNCTION-BODY depth runs on every
                    # path, so every later return is covered. This is
                    # srmech_plat_file_read's
                    #   int err = ferror(fp); fclose(fp); if (err) return ...
                    if has_release and depths[k - body] <= depths[j - body]:
                        released_unconditionally = True
                    if not re.search(r"\breturn\b", lines[k]):
                        continue
                    if released_unconditionally:
                        continue
                    # shape (a): the acquisition itself failed — nothing held.
                    if k - j <= OWN_GUARD_WINDOW:
                        continue
                    # shape (b): released on this line, or anywhere inside this
                    # return's innermost enclosing block.
                    if has_release:
                        continue
                    # shape (b), STRICTLY: the release must sit at the return's
                    # OWN block depth. A release deeper than the return is
                    # inside a nested block the return does not pass through —
                    # a mutually exclusive path — and accepting it is how rc432
                    # went blind to the success-path close (see the docstring of
                    # test_c1_fires_on_a_deleted_success_path_close).
                    my_depth = depths[k - body]
                    covered = False
                    for b in range(k - 1, j, -1):
                        if depths[b - body] < my_depth:
                            break
                        if release + "(" in lines[b] \
                                and depths[b - body] == my_depth:
                            covered = True
                            break
                    if not covered:
                        findings.append(
                            f"{path.name}::{name} acquire@{j + 1} "
                            f"({acquire}) unsafe return@{k + 1}"
                        )
    return findings


def test_c1_held_handles_are_released_on_every_exit() -> None:
    """C1 — STRICT ZERO. Every ``return`` between an acquire and the end of its
    function must carry the matching release.

    Strict zero is affordable because the C side is clean BY MEASUREMENT, not by
    hope: zero leaks across all held-handle PAL sites today. The three deliberate
    idioms are accepted rather than exempted — (a) a guard return before the
    acquisition succeeded, (b) an inline release on the return's own block, and
    (c) capture-status-then-release-once-then-branch.
    """
    findings: list[str] = []
    for f in sorted(_C_SRC_DIR.glob("*.c")):
        findings.extend(_unsafe_returns_in_file(f))
    assert not findings, (
        "held handle(s) not released on an error-path return:\n  "
        + "\n  ".join(findings)
        + "\n\nThe C error paths hold zero leaks today and this gate exists so "
          "that cannot decay silently. If one of these is a legitimate fourth "
          "idiom, TEACH THE GATE THE SHAPE — do not exempt the file (`#T1132`)."
    )


def test_c1_fires_on_a_planted_leak_in_a_real_file() -> None:
    """C1's positive control, and it is deliberately NOT synthetic.

    A control string proves a regex works. It does not prove a rule fires inside
    a 2,000-line file with real comments, real macros and neighbouring functions —
    which is exactly where rc428's D1 and rc430's D7 both shipped green. So this
    mutates the REAL ``srmech_ndjson.c``: one ``srmech_plat_rstream_close(&rs);``
    is deleted from an error-path return, in a copy on disk, and the scanner must
    go from 0 to at least 1 on the same file."""
    src = _C_SRC_DIR / "srmech_ndjson.c"
    assert src.exists(), "srmech_ndjson.c is missing — the control has no subject"

    assert _unsafe_returns_in_file(src) == [], (
        "the UNMUTATED srmech_ndjson.c already reports a leak; the mutation "
        "control cannot distinguish its planted defect from a real one")

    original = src.read_text(encoding="utf-8")
    marker = "            srmech_plat_rstream_close(&rs);\n"
    assert original.count(marker) >= 1, (
        "the error-path close this control deletes is no longer written that "
        "way; re-point the mutation rather than deleting the control")
    mutated = original.replace(marker, "", 1)
    assert mutated != original

    tmp = src.with_name("_rc432_planted_leak_probe.c.tmp")
    try:
        tmp.write_text(mutated, encoding="utf-8")
        found = _unsafe_returns_in_file(tmp)
        assert found, (
            "C1 did NOT fire on a real file with a real close deleted. Every "
            "strict-zero verdict it returns is worthless until it does.")
    finally:
        if tmp.exists():
            tmp.unlink()


def test_c1_fires_on_a_deleted_success_path_close(tmp_path: Path) -> None:
    """C1's SECOND positive control, and the one that matters more.

    The control above deletes an ERROR-path close — a leak on an unusual path.
    This deletes the **success-path** close, which is a leak on EVERY successful
    call: strictly the more consequential defect, and the one rc432 could not
    see. Measured on the shipped gate: deleting
    ``srmech_ndjson.c``'s ``srmech_plat_rstream_close(&rs);`` at the end of
    ``srmech_ndjson_iter`` produced **zero findings**, as did the identical
    deletion in ``srmech_laplacian.c::fiedler_file_scan``.

    THE MECHANISM, because it is subtle and a future edit will re-introduce it:
    when the unclosed ``return`` sits at the function body's MINIMUM depth, the
    walk-back's ``depths[b] < my_depth`` stop condition can never trigger, so it
    scanned back to the acquisition and accepted an error-path release from
    inside a mutually exclusive ``if`` block. Requiring the covering release to
    sit at the return's OWN depth is the fix.

    One control fired and one did not, on the same gate, in the same file — which
    is why "the positive control passes" is not the same claim as "the gate
    sees the defect class".

    The mutant is written under ``tmp_path``, not beside the original.
    :func:`_unsafe_returns_in_file` reads whatever path it is handed, so nothing
    requires the probe to live in ``c/src`` — and this rc removed another test
    that wrote into a directory it shared with the rest of the suite. A control
    that leaves debris in the source tree when it is interrupted is a small
    version of the same mistake."""
    for fname, close_call in (("srmech_ndjson.c", "srmech_plat_rstream_close"),
                              ("srmech_laplacian.c", "srmech_plat_rstream_close")):
        src = _C_SRC_DIR / fname
        assert _unsafe_returns_in_file(src) == [], (
            f"the UNMUTATED {fname} already reports a leak; this control cannot "
            f"distinguish its planted defect from a real one")

        lines = src.read_text(encoding="utf-8").split("\n")
        # the success-path close: at function-body depth (4-space indent), as
        # opposed to the deeper error-path ones inside guard blocks.
        marker = "    " + close_call + "(&rs);"
        idx = [i for i, ln in enumerate(lines) if ln == marker]
        assert idx, (
            f"{fname}: no success-path {close_call} written at body depth any "
            f"more. Re-point this control at the current spelling rather than "
            f"deleting it — the defect class it guards did not go away.")

        mutated = lines[:idx[0]] + lines[idx[0] + 1:]
        tmp = tmp_path / fname
        tmp.write_text("\n".join(mutated), encoding="utf-8")
        found = _unsafe_returns_in_file(tmp)
        assert found, (
            f"C1 did NOT fire after deleting {fname}'s success-path "
            f"{close_call}. That is an unconditional handle leak on every "
            f"successful call, and a strict-zero gate that cannot see it is "
            f"reporting a zero it did not measure (`#T1132`).")


def test_function_spans_agree_with_the_jpl_scanner() -> None:
    """CROSS-CHECK against an INDEPENDENT scanner over the same files.

    Every control in this file was, until now, a short synthetic string. That
    class of control is structurally unable to catch a scanner that mis-parses
    real source — which is the failure this file's own top docstring records
    happening once already (the 362-line comment-strip offset), and which
    happened a second time in rc432: char literals such as ``c == '{'`` were fed
    to the brace counter, so ``srmech_genome.c::genome_json_object_span`` claimed
    a 7,610-line body and :func:`_function_spans` skipped everything inside it.
    **76 spans where the JPL scanner finds 295, in one file, with C1 reporting a
    clean zero over the 219 functions it had lost.**

    ``test_jpl_audit.py::_scan_functions`` was written independently, for a
    different rule family, and reads the same files. Agreement on the NAME SET
    per file is the assertion: counts differ harmlessly (the two disagree on
    duplicate spellings), but a function that one finds and the other does not is
    a parser defect in whichever is wrong. A second scanner is the only control
    that could ever have caught this, so it is the one that ships."""
    import test_jpl_audit as _jpl

    divergent = []
    for path in sorted(_C_SRC_DIR.glob("*.c")):
        text = _strip_comments_preserving_lines(
            path.read_text(encoding="utf-8", errors="replace"))
        ours = {name for name, _b, _e in _function_spans(text.split("\n"))}
        theirs = {row[0] for row in _jpl._scan_functions(path)}
        if ours != theirs:
            divergent.append(
                f"{path.name}: jpl-only={sorted(theirs - ours)[:5]} "
                f"c1-only={sorted(ours - theirs)[:5]}")

    assert not divergent, (
        "the two function scanners disagree about what functions exist:\n  "
        + "\n  ".join(divergent)
        + "\n\nOne of them is mis-parsing. Find out which BEFORE trusting any "
          "zero this file reports — a span that swallows its neighbours makes "
          "them invisible rather than clean (`#T1132`)."
    )


def test_literals_cannot_move_a_function_span() -> None:
    """The specific defect above, isolated and driven.

    A function whose body contains ``'{'`` as a char literal must have a span
    that ends where its closing brace is — not one that runs to end-of-file. The
    naive comment-only strip is reproduced inline so the contrast is measured
    here rather than asserted in prose.

    (Names are >= 2 characters because ``def_pat`` spells the identifier
    ``[a-zA-Z_][a-zA-Z_0-9]+``, which cannot match a one-letter function. The
    first draft of this control used ``f``/``g`` and found NOTHING in either
    mode — a control that returns empty for a reason unrelated to its subject,
    which is precisely the false-REFUTED shape. Recorded because the same trap
    is waiting for the next person who writes a synthetic C fixture here.)"""
    # The literal must be UNBALANCED — a '{' with no matching '}' literal. A
    # fixture carrying both cancels out and the naive scan gets the right answer
    # by luck, which is how the first draft of this control passed while
    # demonstrating nothing. srmech_genome.c's real shape is unbalanced.
    src = (
        "static int probe_brace(const char *s)\n"
        "{\n"
        "    if (s[0] == '{') { return 1; }\n"
        "    return 0;\n"
        "}\n"
        "static int probe_after(int x)\n"
        "{\n"
        "    return x;\n"
        "}\n"
    )
    want = ["probe_brace", "probe_after"]
    spans = _function_spans(_strip_comments_preserving_lines(src).split("\n"))
    assert [n for n, _b, _e in spans] == want, (
        f"literal braces moved a span boundary: {spans}. `probe_after` is "
        f"invisible when `probe_brace` runs away, and an invisible function "
        f"reports no leaks.")

    naive = _function_spans(src.split("\n"))          # the rc432 behaviour
    assert [n for n, _b, _e in naive] != want, (
        "the naive literal-blind scan now agrees, so this control no longer "
        "demonstrates anything — re-point it at a shape that still separates "
        "them rather than deleting it.")


# ────────────────────────────────────────────────────────────────────────
# C2 — created-node rollback
# ────────────────────────────────────────────────────────────────────────

MKDIR_CALL = "srmech_plat_mkdir"

#: DOWN-ONLY. Population is exactly one: ``srmech_laplacian.c::rcut_setup``,
#: three sequential creates each status-checked, with no rollback of the earlier
#: ones when a later one fails.
#:
#: This is NOT strict zero only because rc432 DEFERS the C half, and the ceiling
#: is the pin that makes the deferral an obligation rather than a comment. The C
#: repair needs TWO new PAL symbols, not one:
#:
#:   * ``srmech_plat_rmdir``      — there is no way to remove a directory today;
#:     the PAL has zero rmdir symbols and ``srmech_plat_file_remove`` is C89
#:     ``remove()``, which unlinks an empty directory on POSIX but NOT on Win32.
#:   * ``srmech_plat_mkdir_ex(path, int *created_out)`` — today's
#:     ``srmech_plat_mkdir`` maps ``EEXIST`` to ``SRMECH_OK`` deliberately, so C
#:     CANNOT tell "I created it" from "it was already there". A rollback built
#:     on that would delete a directory the caller already had, which is strictly
#:     worse than the orphan it set out to fix.
#:
#: Both are ADDITIVE symbols, so ABI stays 14. Changing the existing
#: ``srmech_plat_mkdir`` return vocabulary instead WOULD be a wire-format change
#: and would bump 14 -> 15. Do not.
#:
#: Priority note, measured: driven from Python, ``recursive_cut`` creates all
#: three directories before calling into C, so every C mkdir is an ``EEXIST``
#: no-op. The C hazard bites only a BARE-C HOST. That is why it is deferred and
#: not why it is ignored.
CEIL_CREATED_NODE_ROLLBACK = 1


def _mkdir_sites() -> list[tuple[str, str, list[int]]]:
    """``(file, function, [1-indexed mkdir lines])`` for functions with >= 2."""
    out = []
    for path in sorted(_C_SRC_DIR.glob("*.c")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        lines = _strip_comments_preserving_lines(raw).split("\n")
        for name, body, end in _function_spans(lines):
            hits = [j + 1 for j in range(body, end + 1)
                    if MKDIR_CALL + "(" in lines[j]]
            if len(hits) >= 2:
                out.append((path.name, name, hits))
    return out


ROLLBACK_TOKENS = ("srmech_plat_rmdir", "rcut_rollback", "srmech_plat_file_remove")


def _has_rollback(path: Path, name: str) -> bool:
    """Does ``name`` undo an earlier create when a later one fails?

    Any removal primitive appearing **after the first create** counts. Kept broad
    on purpose: the point is to notice the ABSENCE of any undo, and a gate that
    demanded one exact spelling would go stale the moment the repair picked
    another.

    ⚠️ **"After the first create" is enforced, not merely described.** rc432 said
    exactly that in this docstring and then scanned the WHOLE function, so a
    removal call sitting ABOVE the first ``mkdir`` — necessarily for some other
    resource, since nothing has been created yet — exempted the function. Driven,
    not argued: planting ``srmech_plat_file_remove("unrelated")`` one line above
    ``rcut_setup``'s first create flipped it to ``True``, which would have
    drained C2's ceiling to 0 and then, via the headroom assert, demanded the
    CEIL be lowered — silently discharging the `#T1133` obligation the ceiling
    exists to hold open. A gate that can be switched off by an unrelated line is
    worse than no gate, because it reports the absence it was built to detect."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = _strip_comments_preserving_lines(raw).split("\n")
    for fn, body, end in _function_spans(lines):
        if fn != name:
            continue
        creates = [j for j in range(body, end + 1) if MKDIR_CALL + "(" in lines[j]]
        if not creates:
            return False
        region = "\n".join(lines[creates[0] + 1:end + 1])
        return any(tok in region for tok in ROLLBACK_TOKENS)
    return False


def test_c2_multi_mkdir_functions_roll_back_earlier_creates() -> None:
    """C2 — DOWN-ONLY CEIL of :data:`CEIL_CREATED_NODE_ROLLBACK`."""
    unsafe = []
    for fname, fn, hits in _mkdir_sites():
        if not _has_rollback(_C_SRC_DIR / fname, fn):
            unsafe.append(f"{fname}::{fn} creates at {hits}, no rollback")

    assert len(unsafe) <= CEIL_CREATED_NODE_ROLLBACK, (
        f"created-node rollback ceiling BREACHED: {len(unsafe)} > "
        f"{CEIL_CREATED_NODE_ROLLBACK}\n  " + "\n  ".join(unsafe)
    )
    headroom = CEIL_CREATED_NODE_ROLLBACK - len(unsafe)
    print(f"\nCEIL_CREATED_NODE_ROLLBACK={CEIL_CREATED_NODE_ROLLBACK} "
          f"live={len(unsafe)} headroom={headroom}")
    assert headroom == 0, (
        f"the ceiling has drained to {len(unsafe)} but is still "
        f"{CEIL_CREATED_NODE_ROLLBACK}. A drained ceiling that nobody lowers "
        f"stops being a ratchet and becomes decoration — lower it to "
        f"{len(unsafe)}. If `#T1133` landed the rmdir/mkdir_ex pair and fixed "
        f"rcut_setup, this becomes STRICT ZERO."
    )


def test_c2_rollback_must_follow_the_first_create_not_merely_exist(
        tmp_path: Path) -> None:
    """A removal token ABOVE the first create must NOT exempt a function.

    Both directions, driven on the real ``rcut_setup``:

    * plant ``srmech_plat_file_remove`` one line ABOVE the first ``mkdir`` —
      necessarily about some other resource, since nothing has been created yet
      — and the function must stay unsafe;
    * plant the same token BELOW the last ``mkdir`` and it must count, because
      that is what a real rollback looks like.

    The first arm is the one that was broken: rc432 scanned the whole function
    body, so an unrelated line switched C2 off. The second arm is here so the
    fix cannot be over-tightened into a gate that no genuine repair can satisfy —
    a ratchet nobody can discharge gets deleted rather than obeyed."""
    sites = [s for s in _mkdir_sites() if s[0] == "srmech_laplacian.c"]
    assert sites, "rcut_setup is no longer C2's live site; re-point this control"
    fname, fn, hits = sites[0]
    src = _C_SRC_DIR / fname
    lines = src.read_text(encoding="utf-8").split("\n")

    assert not _has_rollback(src, fn), (
        f"{fn} already reports a rollback; this control cannot distinguish its "
        f"planted token from a real repair")

    token = '    (void)srmech_plat_file_remove("unrelated");'

    above = tmp_path / fname
    above.write_text("\n".join(lines[:hits[0] - 1] + [token]
                              + lines[hits[0] - 1:]), encoding="utf-8")
    assert not _has_rollback(above, fn), (
        "a removal call placed ABOVE the first create exempted the function. "
        "Nothing had been created yet, so it cannot be undoing one of these "
        "creates — and C2's ceiling would drain to 0 on it, whereupon the "
        "headroom assert demands the CEIL be lowered and `#T1133`'s obligation "
        "quietly disappears (`#T1132`).")

    below = tmp_path / ("below_" + fname)
    below.write_text("\n".join(lines[:hits[-1]] + [token]
                               + lines[hits[-1]:]), encoding="utf-8")
    assert _has_rollback(below, fn), (
        "a removal call placed BELOW the last create did NOT count as a "
        "rollback. The window is now too narrow for a real repair to satisfy, "
        "which is a different way for the same ratchet to stop working.")


def test_c2_population_is_the_one_deferral_we_named() -> None:
    """The ceiling must be spent on the site the deferral names, not on some
    other function that happens to occupy the slot. A ceiling of 1 pointing at
    an unknown site would be a number, not a pin."""
    sites = _mkdir_sites()
    assert sites, (
        "no multi-mkdir function found at all. Either the C tree moved or the "
        "scanner stopped seeing srmech_plat_mkdir — an EMPTY population is a "
        "finding, not a pass.")
    names = {(f, fn) for f, fn, _ in sites}
    assert ("srmech_laplacian.c", "rcut_setup") in names, (
        f"rcut_setup is no longer the multi-mkdir site this ceiling was seeded "
        f"for; found {sorted(names)}. If it was repaired, drop the ceiling to "
        f"zero — do not leave it pointing at nothing.")


def test_c2_fires_on_a_planted_rollback_free_pair_and_not_on_a_repaired_one(
        tmp_path: Path) -> None:
    """C2 from BOTH sides. A gate that only ever says 'fine' is not measuring."""
    no_rollback = (
        "srmech_status_t planted_setup(const char *a, const char *b)\n"
        "{\n"
        "    srmech_status_t st = srmech_plat_mkdir(a);\n"
        "    if (st != SRMECH_OK) { return st; }\n"
        "    st = srmech_plat_mkdir(b);\n"
        "    if (st != SRMECH_OK) { return st; }\n"
        "    return SRMECH_OK;\n"
        "}\n"
    )
    with_rollback = no_rollback.replace(
        "    st = srmech_plat_mkdir(b);\n"
        "    if (st != SRMECH_OK) { return st; }\n",
        "    st = srmech_plat_mkdir(b);\n"
        "    if (st != SRMECH_OK) { srmech_plat_rmdir(a); return st; }\n",
    )

    bad = tmp_path / "bad.c"
    bad.write_text(no_rollback, encoding="utf-8")
    good = tmp_path / "good.c"
    good.write_text(with_rollback, encoding="utf-8")

    def scan(p: Path) -> bool:
        lines = _strip_comments_preserving_lines(
            p.read_text(encoding="utf-8")).split("\n")
        for fn, body, end in _function_spans(lines):
            hits = [j for j in range(body, end + 1)
                    if MKDIR_CALL + "(" in lines[j]]
            if len(hits) >= 2:
                return not _has_rollback(p, fn)
        raise AssertionError(f"{p.name}: the scanner found no multi-mkdir "
                             f"function at all — it is not looking")

    assert scan(bad), "C2 did not fire on a rollback-free multi-mkdir pair"
    assert not scan(good), "C2 fired on a pair that DOES roll back"


# ────────────────────────────────────────────────────────────────────────
# The line-number self-check
# ────────────────────────────────────────────────────────────────────────

def test_every_reported_line_number_really_holds_the_token() -> None:
    """THE INVARIANT THAT WOULD HAVE CAUGHT THE 362-LINE OFFSET BUG.

    > Every line number the scanner reports must, when read back FROM THE REAL
    > FILE, contain the token the scanner claims is there.

    Stated as an invariant rather than a pinned literal, so it cannot rot: there
    is no hardcoded 2760 here, and it keeps working when the C source moves. It
    is the falsifier the spike's six green planted controls could not be — the
    offset bug was invisible to every one of them, and only an external oracle
    caught it.
    """
    checked = 0
    for fname, fn, hits in _mkdir_sites():
        raw_lines = (_C_SRC_DIR / fname).read_text(
            encoding="utf-8", errors="replace").split("\n")
        for ln in hits:
            assert MKDIR_CALL in raw_lines[ln - 1], (
                f"{fname}:{ln} was reported as a {MKDIR_CALL} call site, but "
                f"the REAL file line {ln} reads {raw_lines[ln - 1]!r}. The "
                f"scanner's line numbers are offset — almost certainly a "
                f"comment strip that removed newlines (`#T1132`)."
            )
            checked += 1
    assert checked >= 2, (
        f"only {checked} reported line numbers were verifiable; this check "
        f"cannot pass vacuously")
