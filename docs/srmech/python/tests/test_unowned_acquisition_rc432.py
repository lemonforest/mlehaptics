"""rc432 (`#T1132`) — UNOWNED FILESYSTEM ACQUISITIONS: allowlist + down-only CEIL.

WHAT THIS FINDS
===============
An acquisition — ``mkdir`` / ``makedirs`` / ``mkdtemp`` / a write-mode ``open`` —
that sits at a function's top level with a ``raise`` after it, and with nothing
owning it in between. When that raise fires, the resource was already taken and
nobody removes it: the raise is loud and the orphan is silent.

⚠️ STRICT ZERO IS IMPOSSIBLE HERE, AND THE REASON IS NOT LAZINESS
=================================================================
The **benign-by-contract** class is real and measured. Three of these sites are
``bus/_transport.py::bind``, all creating ``~/.srmech/`` — a shared, idempotent
directory every bus op wants to exist and which nothing should ever remove.
They are STRUCTURALLY INDISTINGUISHABLE from an orphan; only the contract
separates them. Forcing them to zero would mean wrapping correct code in a scope
it does not need, purely to satisfy a gate — which is the banned move.

So this ships as :data:`ALLOWED_UNOWNED_ACQUISITIONS` plus a down-only
:data:`CEIL_UNOWNED_ACQUIRE` on the residual, the rc415/rc423 shape.

CONDITION (2) IS THE WHOLE DESIGN
=================================
A site qualifies when all of:

1. it calls an acquisition primitive, AND
2. it is a **simple statement at function-body depth 0** — not inside any ``if``
   / ``for`` / ``while`` / ``try`` / ``with``, AND
3. a ``raise`` / ``assert`` appears lexically later in the same function (inline;
   nested ``def`` / ``lambda`` / ``class`` excluded), **or** a later bare-``Name``
   call resolves to a same-module ``def`` that raises inline (**tier 1, one hop,
   no transitive closure**).

Condition (2) is what converts a *reachability guess* into a **sound
implication**. Top-level statements execute in source order, so anything
lexically after one is reached only once that one completed. Therefore: **if the
later raise fires, the resource was already acquired.** That is a proof about
ordering GIVEN firing, not a guess about reachability — and it is why this gate
does not reproduce rc431's documented false-positive class, where an acquisition
in one branch of an ``if`` was paired with a raise in the mutually exclusive
sibling branch. Tier 1 is narrowed to same-module exact-name ``def``s for the
same reason: a package-wide bare-name lookup cross-contaminates.

⚠️ BLIND SPOTS — WRITTEN DOWN SO THE NEXT RC INHERITS THEM RATHER THAN REDISCOVERS
=================================================================================
1. **Loop bodies are invisible.** The ordering proof needs top-level statement
   ordering; inside a ``for``, a lexically-EARLIER raise fires earlier in the SAME
   iteration, so the implication fails. ``genome_register_attested``'s three
   inner-loop sites are permanent misses — and that partial-loop shape (earlier
   iterations' artifacts left behind while a later iteration raises) was 3 of the
   12 confirmed lines this rc repaired.
2. **Branch-local acquisitions are invisible** — condition (2) excludes anything
   inside ``if`` / ``try`` / ``with``. ``genome_import``'s native branch is a
   permanent miss, **so that repair is UNGATED here**: a regression in it reds
   nothing in this file.
3. **Attribute-call raisers are unresolved.** Tier 1 resolves bare ``Name`` calls
   only, so ``write_ndjson``'s raiser (``record.to_json_line()``) is invisible.
4. **The prior-data-destruction class is entirely outside this gate.** Truncating
   a pre-existing good file is a DESTRUCTION, not an acquisition. Nothing in rc432
   gates it; only ``test_acquire_before_validate_rc432.py`` covers it.
5. **It counts; it does not detect.** A ceiling seeded at the live population
   INCLUDES every present instance and can only fire on GROWTH.
6. **Dead-code ``raise`` statements** produce sound-but-unreachable flags. That is
   a different defect.
7. **The gate has NO notion of ownership** — it measures NESTING. Condition (2)
   skips every acquisition below function-body depth 0, owned or not, so a
   genuinely unowned ``mkdir`` inside an ``if`` or a ``try`` is invisible. This
   is the same fact as blind spot 2, stated from the other side, and it is
   written twice on purpose: rc432's control docstring named a ``with``-owned
   and a ``try/finally`` negative as though their silence demonstrated the gate
   recognising an owner. It does not, and
   :func:`test_the_nested_arms_are_silent_for_nesting_not_for_ownership`
   measures it by stripping the ownership out and observing the same silence.

**Coverage arithmetic: this gate saw 7 of the 12 confirmed lines. An rc that
repairs only what it can see repairs 7 of 12 and the ratchet reports green over
the other 5 forever.** That is why the driven per-site file exists and is the
stronger of the two.
"""

from __future__ import annotations

import ast
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent / "srmech"

ACQUIRE_NAMES = frozenset({
    "mkdir", "makedirs", "mkdtemp", "NamedTemporaryFile", "TemporaryDirectory",
})

#: Tags an allowlist entry may carry. CLOSED, and short on purpose.
#:
#: An enum member with no measured instance is an unfalsifiable category, so a
#: fourth is added only when a real site needs it. Extending this set is a
#: deliberate commit, not housekeeping.
ALLOWED_TAGS = frozenset({
    # the node is shared, idempotent, and DESIGNED to persist
    "SHARED_IDEMPOTENT",
    # the caller owns the node's lifetime by documented contract
    "CALLER_OWNS_SCRATCH",
    # the site IS the ownership mechanism — removing the resource here is
    # precisely what the enclosing construct exists to do
    "IS_THE_OWNER",
})

#: Keyed ``(relpath, qualname, kind)`` — **never line numbers, they rot.**
#: Every entry carries a tag from :data:`ALLOWED_TAGS`, a non-empty prose
#: rationale, **and the exact number of sites it covers**;
#: :func:`test_allowlist_entries_are_all_justified` enforces all three.
#: That is the mechanism that makes "a bare allowlist with no reasons"
#: structurally impossible, following ``RULE_5_EXEMPT_FUNCTIONS``.
#:
#: ⚠️ **THE COUNT IS NOT DECORATION — it is the whole difference between an
#: exemption and a hole.** rc432 shipped this dict keyed on
#: ``(file, qualname, kind)`` with no multiplicity, and :func:`_residual`
#: filtered EVERY row matching a key. Measured: 3 keys were absorbing **7**
#: rows — ``bind`` 3, ``_recursive_cut_impl`` 3, ``owned_scratch_dir`` 1. So a
#: NEW, genuinely unowned ``mkdir`` added anywhere inside ``bind`` would have
#: been exempted silently, under a rationale whose text describes one specific
#: idempotent directory and asserts "It is idempotent". An allowlist that
#: exempts a site nobody has read is indistinguishable from no allowlist at
#: all, and it fails in the direction that stays green.
ALLOWED_UNOWNED_ACQUISITIONS: dict[tuple[str, str, str], tuple[str, str, int]] = {
    ("srmech/bus/_transport.py", "bind", "mkdir"): (
        "SHARED_IDEMPOTENT",
        "Creates ~/.srmech/, the shared socket-and-state root that EVERY bus op "
        "wants to exist. It is idempotent, it is not this call's to own, and "
        "removing it on a bind failure would break every other live bus client. "
        "Structurally identical to an orphan; only the contract separates them, "
        "which is exactly why strict zero is impossible on this axis. The three "
        "covered sites are the socket-root creates on bind's own paths; a "
        "FOURTH acquisition in this function is not covered by that reasoning "
        "and must be read before it is exempted.",
        3,
    ),
    ("srmech/math/laplacian.py", "_recursive_cut_impl", "makedirs"): (
        "CALLER_OWNS_SCRATCH",
        "The impl half of the `#T1132` S7 split: it performs the acquisitions "
        "and deliberately never decides their lifetime. Ownership lives one "
        "level up in recursive_cut, which keeps a CALLER-NAMED work_dir (the "
        "caller owns it, the tomes in it are the bounded record) and wraps a "
        "work_dir=None scratch in _ownedfs.owned_scratch_dir. Giving this half "
        "an owner too would delete the caller's directory. Three sites, one per "
        "level of the work_dir tree this impl lays out.",
        3,
    ),
    ("srmech/_ownedfs.py", "owned_scratch_dir", "mkdtemp"): (
        "IS_THE_OWNER",
        "The helper that IMPLEMENTS the invariant this gate measures. Its "
        "mkdtemp is at top level and its re-raise is below — the exact shape "
        "the predicate looks for — because that IS the ownership construct: it "
        "acquires, yields, and rmtree's on any BaseException. A gate cannot "
        "distinguish the mechanism from the defect by shape alone, so this is "
        "an allowlist entry rather than a predicate special case, and it is "
        "recorded rather than hidden. Exactly one site: the single mkdtemp.",
        1,
    ),
}

#: DOWN-ONLY. **Measured after the rc432 repairs landed, not chosen.** The
#: pre-repair tier-1 population was 11; it is 10 now, of which 7 are allowlisted.
#:
#: The three residual sites, each named so the number is never anonymous:
#:   * ``genome_save``   — mkdir now sits below all validation, but still above
#:     the native call, so a native FAILURE leaves the directory.
#:   * ``genome_explode``— same shape, same position.
#:   * ``genome_pack``   — the DISPUTED-WEAK one (see the test below).
#:
#: The first two are the I/O-FAULT class, not the acquire-before-VALIDATE class
#: this rc closed: the C call is the operation, not a validation of its inputs.
#: They stay in the residual rather than the allowlist because "we chose not to
#: extend scope here" is not the same claim as "this is benign".
CEIL_UNOWNED_ACQUIRE = 3


# ────────────────────────────────────────────────────────────────────────
# The scanner
# ────────────────────────────────────────────────────────────────────────

def _acquire_kind(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    f = node.func
    name = f.attr if isinstance(f, ast.Attribute) else (
        f.id if isinstance(f, ast.Name) else None)
    if name in ACQUIRE_NAMES:
        return name
    if name == "open":
        candidates = list(node.args[1:2]) + [
            k.value for k in node.keywords if k.arg == "mode"]
        for a in candidates:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                    and any(c in a.value for c in "wxa"):
                return "open-write"
    return None


def _inline_nodes(fn: ast.AST) -> list[ast.AST]:
    """Every node in ``fn``'s body EXCLUDING nested ``def`` / ``lambda`` /
    ``class`` — a raise inside a closure fires when the closure is CALLED, which
    says nothing about this function's own ordering.

    ⚠️ The filter is applied when a node is POPPED, not when its children are
    pushed. The first build filtered on push, which missed the case that matters:
    a nested ``def`` sitting directly in ``fn.body`` was already on the stack, so
    its own body was walked and its ``raise`` counted as this function's. The
    ``closure-raise`` control caught it — see
    :func:`test_control_negatives_are_all_silent`."""
    nested = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
    out: list[ast.AST] = []
    stack = list(fn.body)                                    # type: ignore[attr-defined]
    while stack:
        n = stack.pop()
        if isinstance(n, nested):
            continue
        out.append(n)
        stack.extend(ast.iter_child_nodes(n))
    return out


def _raises_inline(fn: ast.AST) -> list[ast.AST]:
    return [n for n in _inline_nodes(fn)
            if isinstance(n, (ast.Raise, ast.Assert))]


def scan_source(source: str, relpath: str) -> list[dict]:
    """The predicate, over one module's source. Pure — no filesystem — so the
    controls below can drive it on strings."""
    tree = ast.parse(source)
    module_fns: dict[str, ast.AST] = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            module_fns.setdefault(n.name, n)

    found: list[dict] = []
    for fn in [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        raises = _raises_inline(fn)
        for idx, stmt in enumerate(fn.body):
            # CONDITION 2 — a SIMPLE statement at function-body depth 0.
            if not isinstance(stmt, (ast.Expr, ast.Assign, ast.AnnAssign,
                                     ast.AugAssign)):
                continue
            kind = None
            for sub in ast.walk(stmt):
                kind = _acquire_kind(sub)
                if kind:
                    break
            if not kind:
                continue

            reason = None
            later = [r for r in raises if r.lineno > stmt.lineno]
            if later:
                reason = (f"inline-{type(later[0]).__name__.lower()}"
                          f"@{later[0].lineno}")
            else:
                for s2 in fn.body[idx + 1:]:                 # TIER 1, ONE HOP
                    for sub in ast.walk(s2):
                        if isinstance(sub, ast.Call) and \
                                isinstance(sub.func, ast.Name):
                            callee = module_fns.get(sub.func.id)
                            if callee is not None and _raises_inline(callee):
                                reason = f"tier1-callee:{sub.func.id}@{sub.lineno}"
                                break
                    if reason:
                        break
            if reason:
                found.append({"file": relpath, "qualname": fn.name,
                              "line": stmt.lineno, "kind": kind,
                              "reason": reason})
    return found


#: Memo for :func:`_scan_package`. FIVE tests in this file need the identical
#: full-package AST walk, at ~8s each in the fork-isolated cell, and the walk is
#: a pure read of a tree no test mutates. Caching it is not a shortcut around a
#: measurement — every test still evaluates its own predicate over the same
#: rows; it just stops paying four times for one traversal.
_SCAN_CACHE: list[dict] | None = None


def _scan_package() -> list[dict]:
    global _SCAN_CACHE
    if _SCAN_CACHE is None:
        rows: list[dict] = []
        for p in sorted(_PKG.rglob("*.py")):
            rel = str(p.relative_to(_PKG.parent)).replace("\\", "/")
            try:
                rows.extend(scan_source(p.read_text(encoding="utf-8"), rel))
            except SyntaxError:                              # pragma: no cover
                continue
        _SCAN_CACHE = rows
    # a fresh list per caller, so no test can perturb another's population
    return list(_SCAN_CACHE)


def _residual() -> list[dict]:
    """Rows no allowlist entry accounts for.

    ⚠️ **An entry exempts its DECLARED NUMBER of rows and no more.** Rows beyond
    that count fall through to the residual and press on the ceiling, which is
    the only reason a growing exemption is visible at all. rc432 filtered on key
    membership alone, so one entry covered an unbounded number of sites."""
    remaining = {k: v[2] for k, v in ALLOWED_UNOWNED_ACQUISITIONS.items()}
    out: list[dict] = []
    for r in _scan_package():
        key = (r["file"], r["qualname"], r["kind"])
        if remaining.get(key, 0) > 0:
            remaining[key] -= 1
            continue
        out.append(r)
    return out


# ────────────────────────────────────────────────────────────────────────
# The ratchet
# ────────────────────────────────────────────────────────────────────────

def test_unowned_acquisition_ceiling_holds() -> None:
    """DOWN-ONLY. rc415's printed-headroom shape, so a drained ceiling is visible
    rather than inert."""
    residual = _residual()
    listing = "\n  ".join(
        f"{r['file']}::{r['qualname']}@{r['line']} ({r['kind']}) -> {r['reason']}"
        for r in residual)
    assert len(residual) <= CEIL_UNOWNED_ACQUIRE, (
        f"unowned-acquisition ceiling BREACHED: {len(residual)} > "
        f"{CEIL_UNOWNED_ACQUIRE}\n  {listing}\n\n"
        f"A new acquisition sits above a raise with nothing owning it. Either "
        f"move it below the validation (the cheap repair, and the right one at "
        f"five of this rc's eight sites), or give it an owner "
        f"(srmech._ownedfs.created_dirs / owned_scratch_dir). Adding an "
        f"allowlist entry is the LAST option and requires a tag plus a written "
        f"rationale (`#T1132`)."
    )
    headroom = CEIL_UNOWNED_ACQUIRE - len(residual)
    print(f"\nCEIL_UNOWNED_ACQUIRE={CEIL_UNOWNED_ACQUIRE} "
          f"live={len(residual)} headroom={headroom}")
    assert headroom == 0, (
        f"the residual has drained to {len(residual)} but the ceiling still "
        f"reads {CEIL_UNOWNED_ACQUIRE}. A ceiling nobody lowers stops being a "
        f"ratchet and becomes decoration — lower it to {len(residual)}.\n"
        f"  {listing}"
    )


def test_allowlist_entries_are_all_justified() -> None:
    """Every allowlist entry carries an in-enum tag, real prose, AND a count.

    This is the mechanism that makes a bare allowlist structurally impossible,
    and it is the same one ``RULE_5_EXEMPT_FUNCTIONS`` uses. An exemption whose
    reason is not written down is indistinguishable from a defect somebody got
    tired of.

    (rc432 carried an ``assert <expr> or True`` here, which its own trailing
    comment conceded was "not a check". It could not fail on any input, so it
    was not an assertion — it was a comment wearing one's clothes. Deleted
    rather than repaired: the property it gestured at, that a relpath may carry
    ``rcNNN``, is not one anything needs to enforce.)"""
    for key, value in ALLOWED_UNOWNED_ACQUISITIONS.items():
        assert isinstance(key, tuple) and len(key) == 3, key
        relpath, qualname, kind = key
        assert isinstance(value, tuple) and len(value) == 3, (
            f"{key}: entries are (tag, rationale, expected_count); got "
            f"{len(value) if isinstance(value, tuple) else type(value)}.")
        tag, rationale, expected = value
        assert tag in ALLOWED_TAGS, (
            f"{key}: tag {tag!r} is outside the closed set {sorted(ALLOWED_TAGS)}. "
            f"Extending the enum is a deliberate commit — a member with no "
            f"measured instance is an unfalsifiable category.")
        assert len(rationale.split()) >= 20, (
            f"{key}: rationale is {len(rationale.split())} words. An exemption "
            f"needs a reason a reader can evaluate, not a label.")
        assert isinstance(expected, int) and expected >= 1, (
            f"{key}: expected_count must be a positive int; got {expected!r}.")
        assert relpath and qualname and kind


def test_allowlist_multiplicity_matches_the_live_site_count() -> None:
    """Each entry covers EXACTLY the number of sites it declares.

    Fires in BOTH directions on purpose. Upward: a new acquisition lands inside
    an already-exempt function and would otherwise inherit an exemption written
    for its neighbours — the hole measured in rc432, where 3 keys silently
    absorbed 7 rows. Downward: a repair removed a covered site and the entry now
    over-declares, which pre-approves the next acquisition to land on that key.
    """
    live: dict[tuple[str, str, str], int] = {}
    for r in _scan_package():
        key = (r["file"], r["qualname"], r["kind"])
        live[key] = live.get(key, 0) + 1

    wrong = []
    for key, (_tag, _why, expected) in ALLOWED_UNOWNED_ACQUISITIONS.items():
        got = live.get(key, 0)
        if got != expected:
            wrong.append(f"{key}: declares {expected}, {got} live")
    assert not wrong, (
        "allowlist multiplicity no longer matches the tree:\n  "
        + "\n  ".join(wrong)
        + "\n\nIf a site was ADDED, read it — the existing rationale was written "
          "about its neighbours, not about it. If a site was REMOVED, lower the "
          "count so the entry stops covering ground that no longer exists "
          "(`#T1132`)."
    )


def test_every_allowlist_entry_still_matches_a_real_site() -> None:
    """An allowlist that outlives its sites silently widens. If a repair removed
    one of these, the entry must go with it — otherwise the next acquisition to
    land on that ``(file, qualname, kind)`` key is exempted by inheritance."""
    live = {(r["file"], r["qualname"], r["kind"]) for r in _scan_package()}
    stale = sorted(set(ALLOWED_UNOWNED_ACQUISITIONS) - live)
    assert not stale, (
        f"allowlist entries no longer matching any site: {stale}. Remove them "
        f"— a stale exemption pre-approves a future defect at the same key.")


def test_genome_pack_stays_in_the_residual_not_the_allowlist() -> None:
    """``genome_pack`` is DISPUTED-WEAK and counts toward the ceiling.

    The rc431 triage marked it REFUTED because its *caller-input* validation is
    correctly placed, and it was right about that. But ``_read_chr()`` runs after
    the mkdir and can raise on IO, so the site is not established as benign
    either. The residual is the honest home for "we do not know": putting it in
    the allowlist would assert a benignity nobody has measured, and would improve
    the gate's apparent precision by relabelling rather than by learning
    anything."""
    assert ("srmech/biology/genome.py", "genome_pack", "mkdir") \
        not in ALLOWED_UNOWNED_ACQUISITIONS, (
        "genome_pack was moved into the allowlist. If it has actually been "
        "proven benign, say so with a measurement and a rationale; if it was "
        "repaired, the ceiling drops instead.")


# ────────────────────────────────────────────────────────────────────────
# CONTROLS — the predicate is driven from BOTH sides
# ────────────────────────────────────────────────────────────────────────

_POS_UNOWNED = """
import os
def f(p):
    os.mkdir(p)
    if not p:
        raise ValueError("bad")
"""

_NEG_WITH_OWNED = """
import contextlib, os
def f(p):
    with contextlib.suppress(OSError):
        os.mkdir(p)
    raise ValueError("bad")
"""

_NEG_TRY_FINALLY = """
import os, shutil
def f(p):
    try:
        os.mkdir(p)
        raise ValueError("bad")
    finally:
        shutil.rmtree(p, ignore_errors=True)
"""

_NEG_RAISE_BEFORE_ACQUIRE = """
import os
def f(p):
    if not p:
        raise ValueError("bad")
    os.mkdir(p)
"""

_NEG_SIBLING_BRANCH = """
import os
def f(p, flag):
    if flag:
        os.mkdir(p)
    else:
        raise ValueError("the other branch")
"""

_NEG_CLOSURE_RAISE = """
import os
def f(p):
    os.mkdir(p)
    def inner():
        raise ValueError("fires when CALLED, not here")
    return inner
"""

_TIER1_CALLEE_RAISES = """
import os
def _boom(x):
    raise ValueError("nope")
def f(p):
    os.mkdir(p)
    return _boom(p)
"""

_TIER1_CALLEE_CLEAN = """
import os
def _fine(x):
    return x
def f(p):
    os.mkdir(p)
    return _fine(p)
"""

_TIER1_ATTRIBUTE_CALL = """
import os
def f(p, rec):
    os.mkdir(p)
    return rec.to_json_line()
"""


def test_control_positive_unowned_then_raise_is_flagged() -> None:
    """POSITIVE CONTROL. Every zero this file reports is worthless until the
    predicate is shown to fire on the shape it names."""
    hits = scan_source(_POS_UNOWNED, "ctl.py")
    assert len(hits) == 1 and hits[0]["kind"] == "mkdir", hits


def test_control_negatives_are_all_silent() -> None:
    """Five shapes that must NOT flag.

    ``_NEG_SIBLING_BRANCH`` is the one that matters most: it reproduces rc431's
    documented false-positive class verbatim, where an acquisition in one branch
    was paired with a raise in the mutually exclusive sibling. The first build of
    this predicate walked INTO compound statements and flagged it. Condition (2)
    is what fixed it, and this control is what caught it.

    ⚠️ **Only three of these five DISCRIMINATE.** ``raise-before-acquire``,
    ``sibling-branch`` and ``closure-raise`` each go silent for the reason their
    name gives, and each has a neighbouring mutant that DOES flag. The other two
    do not — see
    :func:`test_the_nested_arms_are_silent_for_nesting_not_for_ownership`, which
    measures why and pins it as a blind spot. They stay here because they are
    still true statements about shapes that must not flag; they are simply not
    evidence that ownership is recognised, and rc432's docstring implied they
    were."""
    for label, src in (("with-owned", _NEG_WITH_OWNED),
                       ("try/finally", _NEG_TRY_FINALLY),
                       ("raise-before-acquire", _NEG_RAISE_BEFORE_ACQUIRE),
                       ("sibling-branch", _NEG_SIBLING_BRANCH),
                       ("closure-raise", _NEG_CLOSURE_RAISE)):
        assert scan_source(src, "ctl.py") == [], (
            f"{label}: flagged a shape that is not the defect — this is how a "
            f"gate starts getting edited around instead of trusted.")


#: The ``with``/``try`` negatives with the OWNERSHIP REMOVED. A ``with`` block
#: that owns something unrelated, and a ``finally`` that releases nothing.
_MUT_WITH_OWNS_NOTHING = """
import os
def f(p, log):
    with open(log, "r") as fh:
        os.mkdir(p)
    raise ValueError("bad")
"""

_MUT_FINALLY_RELEASES_NOTHING = """
import os
def f(p):
    try:
        os.mkdir(p)
        raise ValueError("bad")
    finally:
        pass
"""


def test_the_nested_arms_are_silent_for_nesting_not_for_ownership() -> None:
    """The ``with-owned`` / ``try-finally`` negatives do NOT test ownership.

    Measured, not argued: strip the ownership out of both — a ``with`` holding an
    unrelated read handle, a ``finally: pass`` that releases nothing — and the
    scanner is still silent. The acquisition is now genuinely unowned and
    genuinely followed by a raise, which is the defect exactly, and the predicate
    says nothing.

    **The reason is condition (2), and it is by design.** The gate skips ANY
    acquisition that is not a simple statement at function-body depth 0, whether
    something owns it or not. It has no notion of ownership at all. rc432's
    docstring named those two arms as if their silence were evidence the gate
    recognises an owner; this test replaces that implication with the true
    statement and pins it, so a later reader does not re-derive the gate's
    coverage from a label.

    This is BLIND SPOT 7 in the module docstring, and it is the largest one:
    every genuinely-unowned acquisition that happens to sit inside an ``if`` or a
    ``try`` is invisible here. ``test_acquire_before_validate_rc432.py`` is what
    covers those sites, by DRIVING them."""
    for label, src in (("with-owns-nothing", _MUT_WITH_OWNS_NOTHING),
                       ("finally-releases-nothing", _MUT_FINALLY_RELEASES_NOTHING)):
        assert scan_source(src, "ctl.py") == [], (
            f"{label}: the gate flagged a nested acquisition. That would be a "
            f"WIDENING of condition (2), not a fix — and condition (2) is the "
            f"whole soundness argument. State the new argument before accepting "
            f"it, and re-check the sibling-branch control, which is what "
            f"condition (2) exists to keep silent.")


def test_control_tier1_resolves_one_hop_and_no_further() -> None:
    """Tier 1 sees a bare-Name callee that raises, ignores one that does not, and
    cannot resolve an attribute call. The third is a KNOWN blind spot rather than
    a bug, and it is pinned so a later 'improvement' has to face it deliberately:
    it is exactly why ``write_ndjson``'s ``record.to_json_line()`` is invisible."""
    assert len(scan_source(_TIER1_CALLEE_RAISES, "ctl.py")) == 1
    assert scan_source(_TIER1_CALLEE_CLEAN, "ctl.py") == []
    assert scan_source(_TIER1_ATTRIBUTE_CALL, "ctl.py") == [], (
        "tier 1 resolved an ATTRIBUTE call. That is a widening, not a fix — "
        "state the new soundness argument before accepting it.")


def test_reported_line_numbers_really_hold_an_acquisition() -> None:
    """The same self-check the C gate carries: every reported line, read back
    from the real file, must contain the token claimed for it. Rot-proof (no
    pinned literals) and it fails loudly on any offset bug."""
    rows = _scan_package()
    assert rows, "the scanner visited the package and found NOTHING — an empty " \
                 "population is a finding, not a pass"
    for r in rows:
        text = (_PKG.parent / r["file"]).read_text(encoding="utf-8")
        line = text.split("\n")[r["line"] - 1]
        assert r["kind"].split("-")[0] in line, (
            f"{r['file']}:{r['line']} was reported as a {r['kind']} site, but "
            f"the real line reads {line!r}")
