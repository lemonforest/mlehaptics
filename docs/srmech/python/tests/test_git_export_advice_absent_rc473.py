"""Advice to set the repository-selecting pair for a whole command may not come back.
(rc473 instrument round, `#T1188`)

WHY
---
From 2026-09-11 to 2026-09-14 a test fixture wrote ``decoy identity`` into the
live repository's shared ``.git/config``, under a ``GIT_DIR`` / ``GIT_WORK_TREE``
pair that operators had put in their environment because SHIPPED remedy text told
them to (``tools/hooks/_hooklib.py``, ``tools/run_worked_examples.py``, the hooks
README, ``settings.sample.json``). The final round corrected every one of those
sentences, and no gate claimed to keep them corrected: merge-gate lenses re-planted
the advice into a remedy string and the hooks README and every candidate gate
stayed green. This is that gate.

WHAT IT SCANS
-------------
Four roots under ``docs/srmech`` — ``python/srmech``, ``python/tests``,
``python/tools`` (which holds the hooks README and ``settings.sample.json``) and
``notes`` — every file with a text suffix. ``python/CHANGELOG.md`` is under none
of them, deliberately: its rc473 section QUOTES the old advice inside dated,
marked corrections, and a dated record is not rewritten. ``tools/`` and ``notes/``
are not in ``sdist.include``, so those two roots skip where they are absent.

THE PREDICATE — thirteen forms (:data:`PATTERNS`)
-------------------------------------------------
A prose imperative (the verb, optional article words, then one of the two names,
across the phrase gate's gap characters: whitespace, comment leaders, quotes and
an escaped newline of any backslash count); a shell line setting a name with the
verb; a PowerShell ``$env:`` assignment; a ``cmd`` ``set`` / ``setx``; prose that
sets both names; the older "the name OVERRIDES discovery" wording; "give / hand /
pass the name"; and a per-command ``NAME=value`` prefix in front of a Python,
pytest, uv, bash, ``make`` or any ``*.py`` / ``*.sh`` invocation — a per-command
prefix still reaches every child git of that command, which is exactly the
incident.

Five more since instrument repair 1 (`#T1188`), each an input gate round i1
measured NO MATCH on: a JSON key naming either variable (a settings file's
``"env"`` object is how a variable reaches every hook command); "set / setting /
point / pointing" ONE name "to" or "at" something; ``declare -x``; ``setx [/M]
NAME value``; and ``[Environment]::SetEnvironmentVariable('NAME', …)``.

EXEMPT only when a negation sits IMMEDIATELY before the match, with nothing but
gap characters between: do not, don't, never, must not, should not, nobody / no
one / no operator (ever) has to. A negation elsewhere in the sentence exempts
nothing ("if git cannot follow the pointer, <verb> it" is advice).

THE ALLOW LIST is an EQUALITY over (path, sentence fragment): the residual that is
history or a warning. An unlisted hit reds, and a listed fragment that no longer
occurs reds too, so the list cannot go stale.

LIMITS, stated. (1) The list matches a fragment inside a sentence, so new advice
written INSIDE an allow-listed sentence would be admitted. (2) Forms outside the
thirteen are NOT seen, and a phrase gate cannot be complete: code that assigns
the variable (``os.environ[...] = ...``), passive or indirect wording ("with both
exported", "put them in your environment"), and a per-command prefix in front of
a command the ``cmd_prefix`` list does not name all pass. This limit was
unstated until instrument repair 1, when gate round i1 measured the settings
``"env"`` spelling and one-name "set ... to" prose passing it.

This file spells no advice in its own source: the verb and the names are joined
at run time, so the scan of ``python/tests`` reads this file too and finds nothing.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SR_ROOT = Path(__file__).resolve().parents[2]            # docs/srmech
ROOTS = ("python/srmech", "python/tests", "python/tools", "notes")
#: Roots that ``sdist.include`` does not ship; they skip where absent.
OPTIONAL_ROOTS = ("python/tools", "notes")
TEXT_SUFFIXES = {".py", ".md", ".json", ".sh", ".toml", ".txt", ".cfg", ".ini",
                 ".ps1", ".bash", ".yml", ".yaml"}

_VERB = "ex" + "port"
_D, _W = "GIT_" + "DIR", "GIT_" + "WORK_TREE"
_GAP = r"(?:\s|[*#>\"'`]|\\+n)+"
_NAME = r"\$?GIT_(?:DIR|WORK_TREE)\b"
PATTERNS = {
    "prose_verb": re.compile(r"\b" + _VERB + r"(?:ing)?" + _GAP
                             + r"(?:(?:the|both|a|pair|variables?)" + _GAP + r")*" + _NAME, re.I),
    "shell_line": re.compile(r"(?m)^[ \t]*" + _VERB + r"[ \t]+GIT_(?:DIR|WORK_TREE)[ \t]*="),
    "ps_env": re.compile(r"\$env:GIT_(?:DIR|WORK_TREE)\s*=", re.I),
    "cmd_set": re.compile(r"\bsetx?[ \t]+GIT_(?:DIR|WORK_TREE)[ \t]*=", re.I),
    "prose_set": re.compile(r"\bset(?:ting)?" + _GAP + _NAME + _GAP + r"(?:and|/|or)" + _GAP + _NAME, re.I),
    "override": re.compile(r"\bGIT_(?:DIR|WORK_TREE)\b[`'\"]*\s+" + "over" + r"rides?\b", re.I),
    "give": re.compile(r"\b(?:give|hand|pass)" + _GAP
                       + r"(?:(?:it|them|a|an|the|read-only)" + _GAP + r")*" + _NAME, re.I),
    "cmd_prefix": re.compile(r"\bGIT_(?:DIR|WORK_TREE)=\S+(?:[ \t]+GIT_\w+=\S+)*[ \t]+(?:env[ \t]+)?"
                             r"\S*(?:python3?|pytest|uv|bash|sh|make|\w+\.py|\w+\.sh)\b"),
    # Instrument repair 1 (`#T1188`): five forms gate round i1 measured NO MATCH on.
    # A settings file's "env" object is how a variable reaches every hook command.
    "json_key": re.compile(r"\"GIT_(?:DIR|WORK_TREE)\"\s*:"),
    "prose_set_one": re.compile(r"\b(?:set(?:ting)?|point(?:ing)?)" + _GAP
                                + r"(?:(?:the|a|an)" + _GAP + r")*" + _NAME + _GAP + r"(?:to|at)\b", re.I),
    "declare_x": re.compile(r"\bdeclare[ \t]+-\w*x\w*[ \t]+GIT_(?:DIR|WORK_TREE)\b"),
    "setx_space": re.compile(r"\bsetx(?:[ \t]+/[mM])?[ \t]+GIT_(?:DIR|WORK_TREE)\b", re.I),
    "dotnet_env": re.compile(r"SetEnvironmentVariable\(\s*['\"]GIT_(?:DIR|WORK_TREE)['\"]", re.I),
}
_NEGATION_ADJACENT = re.compile(
    r"(?:\bdo\s+not|\bdon't|\bnever|\bmust\s+not|\bshould\s+not|"
    r"\b(?:nobody|no\s+one|no\s+operator)(?:\s+ever)?\s+has\s+to)(?:\s|[*#>\"'`]|\\+n)*$", re.I)

#: (docs/srmech-relative path, fragment of the normalised sentence): history and
#: warnings, each read by hand at the rc473 instrument round.
ALLOW = {
    ("python/tests/_git_env.py", "was the advice"),
    ("python/tests/test_shell_line_loop_rc468.py", "the only way to un-skip it was to"),
    ("python/tools/census_regen_diff.py", "the obvious workaround"),
    ("notes/_rc473_final_layer3_geometry.sh", "was the old advice for it"),
    ("python/tools/hooks/README.md", "until the rc473 final round"),
    ("python/tools/hooks/_hooklib.py", "until the rc473 final round"),
    ("python/tools/rc471_figures.py", "which is the only way git"),
}


def _norm(text: str) -> str:
    text = re.sub(r"\\+n", " ", text)
    text = re.sub(r"[#*>\"'`]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _sentence(text: str, start: int, end: int) -> str:
    begin = max(text.rfind(sep, 0, start) for sep in (". ", "\n\n", ";", ":\n"))
    begin = 0 if begin < 0 else begin + 1
    ends = [x for x in (text.find(". ", end), text.find("\n\n", end)) if x >= 0]
    return _norm(text[begin:(min(ends) if ends else len(text)) + 1])


def scan_text(text: str):
    """``[(form, offset, normalised sentence, exempt)]`` for every match in ``text``."""
    found = []
    for form, rx in PATTERNS.items():
        for m in rx.finditer(text):
            exempt = bool(_NEGATION_ADJACENT.search(text[max(0, m.start() - 80):m.start()]))
            found.append((form, m.start(), _sentence(text, m.start(), m.end()), exempt))
    return found


def scan_root(root: str):
    """``(files scanned, [(path, line, form, sentence)] hits, exempt count)`` under ``root``."""
    files, hits, exempt = 0, [], 0
    for path in sorted((SR_ROOT / root).rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        files += 1
        rel = path.relative_to(SR_ROOT).as_posix()
        for form, offset, sentence, is_exempt in scan_text(text):
            if is_exempt:
                exempt += 1
            else:
                hits.append((rel, text.count("\n", 0, offset) + 1, form, sentence))
    return files, hits, exempt


#: Scanned-file floors, far below the populations measured at the instrument
#: round, so a root that silently stops being read reds.
_FLOORS = {"python/srmech": 200, "python/tests": 200, "python/tools": 20, "notes": 50}


@pytest.mark.parametrize("root", ROOTS)
def test_no_shipped_text_advises_setting_the_repository_selecting_pair(root: str) -> None:
    if not (SR_ROOT / root).is_dir():
        assert root in OPTIONAL_ROOTS, f"{root} is shipped and absent"
        pytest.skip(f"{root} is not in sdist.include and is absent in this cell")
    files, hits, exempt = scan_root(root)
    print(f"\n[rc473] {root}: {files} files, {len(hits)} hits, {exempt} exempt")
    assert files >= _FLOORS[root], f"{root}: only {files} text files were read"
    unexpected = [h for h in hits if not any(h[0] == p and frag in h[3] for p, frag in ALLOW)]
    stale = sorted((p, frag) for p, frag in ALLOW if p.startswith(root + "/")
                   and not any(h[0] == p and frag in h[3] for h in hits))
    assert not unexpected, (
        f"{len(unexpected)} line(s) under {root} advise setting the repository-"
        "selecting pair for a command. That advice is how a fixture wrote the live "
        "repository's shared config; the tools locate a worktree per invocation "
        "now, so no operator has to. Reword it, or negate it immediately before "
        "the phrase:\n  " + "\n  ".join(f"{p}:{n} [{f}] {s[:220]}" for p, n, f, s in unexpected))
    assert not stale, (
        f"allow-list entries under {root} no longer match any hit — remove or "
        f"re-read them: {stale}")


def _one(form: str, text: str):
    return [(f, s, e) for f, _o, s, e in scan_text(text) if f == form]


def test_each_form_matches_its_own_advice_and_only_an_adjacent_negation_exempts_it() -> None:
    examples = {
        "prose_verb": f"If that fails, {_VERB} {_D} and {_W}.",
        "shell_line": f"cd repo\n{_VERB} {_D}=/mnt/d/GitHub/mlehaptics/.git\n",
        "ps_env": f"$env:{_D} = 'D:/GitHub/mlehaptics/.git'",
        "cmd_set": f"set {_D}=D:\\GitHub\\mlehaptics\\.git",
        "prose_set": f"First set {_D} and {_W}, then run the hook.",
        "override": f"without `{_D}` over" + "rides the worktree cannot be opened",
        "give": f"it is safe to give a read-only ``{_D}`` to the tool",
        "cmd_prefix": f"# Run as {_D}=D:/x/.git {_W}=D:/x python -m pytest tests/",
        # instrument repair 1: gate round i1's NO MATCH inputs, one per new form
        "json_key": '{"env": {"' + _D + '": "/mnt/d/x/.git/worktrees/w", "' + _W + '": "/mnt/d/x"}}',
        "prose_set_one": f"If WSL git cannot follow the pointer, set {_D} to the worktree gitdir first.",
        "declare_x": f"declare -x {_D}=/mnt/d/x/.git",
        "setx_space": f"setx /M {_D} D:\\x\\.git",
        "dotnet_env": f"[Environment]::SetEnvironmentVariable('{_D}', 'D:/x/.git', 'User')",
    }
    more = [
        ("prose_set_one", f"Setting {_D} to the gitdir is enough."),
        ("prose_set_one", f"Point {_D} at the worktree's gitdir before running the hook."),
        ("cmd_prefix", f"{_D}=/mnt/d/x/.git {_W}=/mnt/d/x ./tools/ripple_check.py"),
        ("cmd_prefix", f"{_D}=/mnt/d/x/.git make test"),
    ]
    assert set(examples) == set(PATTERNS), sorted(set(PATTERNS) ^ set(examples))
    for form, text in [*examples.items(), *more]:
        got = _one(form, text)
        assert got and not got[0][2], (form, text, got)
    wrapped = f"# If WSL git does not follow the pointer, {_VERB}\\n# {_D} first"
    assert _one("prose_verb", wrapped) and not _one("prose_verb", wrapped)[0][2]
    adjacent = f"# never {_VERB} {_D} for this"
    assert _one("prose_verb", adjacent) and _one("prose_verb", adjacent)[0][2]
    distant = f"Do not panic: if WSL git does not follow the pointer, {_VERB} {_D} first."
    assert _one("prose_verb", distant) and not _one("prose_verb", distant)[0][2]
    sandbox = f"env = _child_env({_D}=str(gitdir), {_W}=str(worktree))"
    assert scan_text(sandbox) == [], scan_text(sandbox)


def test_the_changelog_is_out_of_scope_and_the_exclusion_is_load_bearing() -> None:
    changelog = SR_ROOT / "python" / "CHANGELOG.md"
    assert not any(changelog.is_relative_to(SR_ROOT / r) for r in ROOTS)
    if not changelog.is_file():
        pytest.skip("python/CHANGELOG.md is absent in this cell")
    quoted = [h for h in scan_text(changelog.read_text(encoding="utf-8")) if not h[3]]
    assert quoted, ("the CHANGELOG no longer quotes the old advice anywhere, so its "
                    "exclusion from this scan hides nothing and can be dropped")
