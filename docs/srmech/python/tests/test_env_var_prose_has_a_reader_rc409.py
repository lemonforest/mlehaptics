"""rc409 (`#T1080`) — an env-var the package DOCUMENTS must be one it READS.

`srmech/cascade/catalogs/__init__.py` advertised three configuration env-vars::

    the ``SRMECH_CLASS_PATH`` / ``SRMECH_CATALOG_PATH`` / ``SRMECH_ALIAS_PATH``
    env-vars — are the ``srmech.external.*`` extension point

Two of the three are real. **``SRMECH_CATALOG_PATH`` was never read by
anything.** The catalog reader is `srmech/dsl/_catalog.py:76`, and it reads
``SRMECH_CASCADE_PATH``. Census: exactly ONE occurrence of the phantom name in
the whole repo — the prose above. Introduced by `686a4329a` (rc364, the
ADR-0010 STRUCTURE slice that created `srmech.cascade`) and it never had a
reader at any commit.

This is the *silently-wrong-answer* class, aimed at the user rather than the
program: a reader follows shipped documentation, exports the variable, and
their catalog directory is never picked up. Nothing errors. Nothing warns. The
setting simply does not exist, and the failure looks like their own mistake.

WHY THE PREDICATE IS "THE PROSE CALLS IT AN ENV-VAR", NOT "IT LOOKS LIKE ONE"
============================================================================
A gate over every ``SRMECH_[A-Z_]+`` token in the package is unusable: measured
at rc409 there are **69** such tokens not literally read from ``os.environ``,
and almost all are correct — C API status codes (``SRMECH_OK``,
``SRMECH_ERR_LIMIT``), ctypes enum mirrors (``SRMECH_JSON_ARRAY``,
``SRMECH_TRANS_COS``), compile-time caps and genome marker prefixes. Requiring a
reader for those is simply wrong, and a hand-maintained exemption list for 60+
names would rot faster than the thing it guards.

So the trigger is the package's **own claim**. A token is checked only when the
surrounding prose calls it an *env-var* / *environment variable* — i.e. when
srmech has told the reader it is a runtime knob. That is self-limiting (8
tokens today, not 69), needs no allowlist, and it is exactly the population
where a missing reader is a user-visible lie rather than a naming coincidence.

THE READ-SET MUST FOLLOW THE INDIRECTION, OR IT MANUFACTURES PHANTOMS
====================================================================
A literal ``os.environ.get("SRMECH_X")`` scan finds 11 names and would report
**two false phantoms**: ``SRMECH_BUS_SEED`` and ``SRMECH_BUS_TOTP_WINDOW_NS``
are both real, both read, but through a module constant —
``ENV_VAR: str = "SRMECH_BUS_SEED"`` at `bus/_seed.py:40`, consumed at `:71`.
Note the **annotation**: a naive ``NAME = "..."`` pattern misses ``NAME: str =
"..."`` and reintroduces both phantoms. A gate that invents two false failures
while catching one true one gets suppressed, so the indirection is resolved
here and both are asserted GREEN below as live negative controls.
"""

from __future__ import annotations

import re
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1] / "srmech"

#: Any ``SRMECH_``-prefixed screaming-snake token.
_TOKEN = re.compile(r"\bSRMECH_[A-Z0-9_]+\b")

#: A module-level constant bound to an env-var NAME, annotation optional.
#: The ``: str`` form is the one that actually ships — see the docstring.
_CONST_BIND = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*[^=]+)?=\s*[\"'](SRMECH_[A-Z0-9_]+)[\"']")

#: The package's own claim that a name is a runtime knob.
_CLAIM = re.compile(r"env[-\s]?var|environment variable", re.IGNORECASE)

#: How far from the claim phrase a token still counts as claimed. ONE line, and
#: that is not arbitrary: the motivating defect wraps across exactly one line
#: boundary (the three names sit on :32, the word "env-vars" on :33). Zero would
#: miss the very defect this file was written for.
_WINDOW = 1


def _sources() -> "list[Path]":
    return sorted(p for p in _PKG.rglob("*.py") if "__pycache__" not in p.parts)


def _read_set() -> "set[str]":
    """Every env-var name the package actually reads, indirection resolved."""
    found: set[str] = set()
    for path in _sources():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        consts: dict[str, str] = {}
        env_lines: list[str] = []
        for line in lines:
            m = _CONST_BIND.match(line)
            if m:
                consts[m.group(1)] = m.group(2)
            if "environ" in line:
                env_lines.append(line)
                found.update(_TOKEN.findall(line))
        # Resolve `os.environ.get(ENV_VAR)` through the constant table.
        for line in env_lines:
            for const_name, env_name in consts.items():
                if re.search(rf"\b{re.escape(const_name)}\b", line):
                    found.add(env_name)
    return found


def _claimed() -> "dict[str, list[str]]":
    """``{token: ["path:line", ...]}`` for tokens the prose CALLS an env-var."""
    out: dict[str, list[str]] = {}
    for path in _sources():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        claim_rows = {i for i, ln in enumerate(lines) if _CLAIM.search(ln)}
        if not claim_rows:
            continue
        rel = path.relative_to(_PKG.parent).as_posix()
        for i, line in enumerate(lines):
            if not any(abs(i - c) <= _WINDOW for c in claim_rows):
                continue
            for tok in _TOKEN.findall(line):
                out.setdefault(tok, []).append(f"{rel}:{i + 1}")
    return out


# ── non-vacuity: both instruments must be able to return otherwise ────


def test_the_extractors_can_still_see_something() -> None:
    """A gate whose scanners silently return nothing passes every assertion.

    Pin the SHAPE of both sides, not a total: an import-time refactor, a
    docstring reflow or a renamed helper must fail HERE, loudly, rather than
    quietly making the strict-zero test below vacuous.
    """
    read = _read_set()
    claimed = _claimed()
    assert len(read) >= 10, (
        f"read-set collapsed to {len(read)} names ({sorted(read)}) - the "
        "os.environ scan has stopped observing.")
    assert len(claimed) >= 5, (
        f"only {len(claimed)} env-var claims found in package prose - the "
        "claim scan has stopped observing.")
    assert "SRMECH_CASCADE_PATH" in read, (
        "the real catalog env-var is missing from the read-set")


def test_the_module_constant_indirection_is_resolved() -> None:
    """LIVE NEGATIVE CONTROL for the read-set extractor.

    These two are read ONLY through an annotated module constant. If the
    indirection ever stops being followed they become phantoms, and the gate
    below starts failing on two names that are perfectly correct. Asserting
    them GREEN here means a future 'simplification' of the extractor fails on
    this test — which explains the cause — instead of on the strict-zero test,
    which would blame the innocent prose.
    """
    read = _read_set()
    for name in ("SRMECH_BUS_SEED", "SRMECH_BUS_TOTP_WINDOW_NS"):
        assert name in read, (
            f"{name} is read via a module constant "
            f"(e.g. `ENV_VAR: str = \"{name}\"` then `os.environ.get(ENV_VAR)`) "
            "but the read-set extractor did not follow the indirection. Fix "
            "_read_set / _CONST_BIND - do NOT exempt the name.")


# ── the invariant ─────────────────────────────────────────────────────


def test_every_documented_env_var_has_a_reader() -> None:
    """STRICT ZERO. Documenting a knob that does not exist is a silent lie.

    FAILED BEFORE rc409 on ``SRMECH_CATALOG_PATH``: advertised in the shipped
    docstring of `srmech/cascade/catalogs/__init__.py`, read by nothing, one
    single occurrence tree-wide. The correct name is ``SRMECH_CASCADE_PATH``.
    """
    read = _read_set()
    phantoms = {t: w for t, w in _claimed().items() if t not in read}

    assert not phantoms, (
        f"{len(phantoms)} env-var(s) DOCUMENTED but never read:\n"
        + "\n".join(f"  {t} — claimed at {', '.join(w)}"
                    for t, w in sorted(phantoms.items()))
        + "\n\nA user who follows this prose exports the variable and nothing "
          "happens: no error, no warning, the setting simply does not exist. "
          "Either fix the name to the one the code reads, delete the claim, or "
          "implement the reader.\n"
          f"Names actually read: {', '.join(sorted(read))}")
