"""rc300 (`#938`) — a C-backed claim must be CHECKABLE against the loaded library.

The Rosetta ledger classifies 263 ops ``c_dispatched``: "routes to a ``srmech_*``
C symbol". Every such dispatch site is gated on ``hasattr(LIB, "srmech_x")`` and
falls to the pure-Python path when the symbol is absent. The answers stay
correct — those fallbacks are complete alternatives — but the classification
becomes FALSE and, before rc300, nothing said so anywhere. rc299 reclassified
``laplacian.mat_eigvals`` to ``c_dispatched``; ``_mat_eigvals_native`` is exactly
such a gate (``laplacian.py``, ``hasattr(_native.LIB, "srmech_mat_eigvals_ws")``
-> ``return None`` -> pure sweep).

Why ABI matching does not already cover it: ``_native`` sets ``HAS_NATIVE=False``
on an ABI mismatch, so a loaded library always matches ABI. But the header adds
symbols ABI-additively — "new symbols only, so SRMECH_ABI_VERSION stays N"
appears ~100 times in ``srmech.h`` — so the ABI pins the WIRE FORMAT of existing
exports, not the symbol SET. A stale-but-ABI-8 build is a reachable state whose
pure fallbacks are correct and whose ``c_dispatched`` claims are silently wrong.

What this module pins:

  1. the committed manifest matches a fresh extraction from the live tree
     (it cannot go stale silently);
  2. every claimed symbol resolves in the library actually loaded;
  3. the check DETECTS a missing symbol — asserted against a library proxy with
     a symbol hidden, so this file cannot pass by not looking;
  4. the pure path (``HAS_NATIVE`` False) stays healthy and unbroken;
  5. the unverifiable region is DOWN-ONLY.

(5) is the honest part. The extraction is static and shallow, so 23 of the 263
``c_dispatched`` ops reach their symbol through a class method or registry
indirection the walk does not follow. Those are not checked. Rather than let
that gap be invisible — the failure mode of `#918`/`#922`/`#937`, where a guard
passed because it was not looking — they are enumerated in
``UNVERIFIABLE_CLAIMS`` under a ceiling that only ever decreases.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from srmech import _native
from srmech.introspect._c_claims import (
    C_CLAIMS,
    UNVERIFIABLE_CEILING,
    UNVERIFIABLE_CLAIMS,
)

_PY_ROOT = Path(__file__).resolve().parent.parent
_TOOLS = _PY_ROOT / "tools"


# ── 1. the manifest is not stale ──────────────────────────────────────────────

def test_manifest_matches_a_fresh_extraction():
    """The committed manifest equals what the generator derives from live code.

    Without this the manifest is a hand-frozen list that silently stops
    describing the package the moment an op's dispatch changes — the manifest
    would then "pass" while checking symbols nothing dispatches to any more."""
    sys.path.insert(0, str(_TOOLS))
    try:
        gen = importlib.import_module("gen_c_claims")
        importlib.reload(gen)
    finally:
        sys.path.remove(str(_TOOLS))

    claims, unverifiable, off_header = gen.extract()

    assert claims == dict(C_CLAIMS), (
        "srmech/introspect/_c_claims.py is STALE — the live dispatch surface no longer "
        "matches the committed manifest. Rerun: python3 tools/gen_c_claims.py"
    )
    assert unverifiable == UNVERIFIABLE_CLAIMS, (
        "the unverifiable-claim set drifted — rerun tools/gen_c_claims.py"
    )
    # Every extracted token that is NOT declared in srmech.h is filtered out of
    # the manifest. Exactly one such token exists (a tempfile prefix); a NEW one
    # is worth a look, because a typo'd dispatch symbol can never resolve and
    # would pure-path forever in total silence.
    assert off_header == {
        "srmech.biology.coupling.resonant_spectrum_sparse": ["srmech_kext_"],
    }, f"unexpected non-header srmech_* token(s): {off_header}"


# ── 2. every claim resolves in the library we actually loaded ─────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="no native library loaded (pure install)")
def test_every_c_dispatched_claim_resolves():
    """No op may claim a C path this library does not contain.

    A failure here is a BUILD defect, not a correctness defect: the named ops
    still compute correct answers on their pure fallbacks. What is broken is the
    ``c_dispatched`` claim — and the fix is to rebuild the library, not to
    reclassify the op."""
    report = _native.c_claim_report()
    assert report["native"] is True
    assert report["unresolved"] == {}, (
        "ops classified c_dispatched whose C symbols are ABSENT from the loaded "
        f"library (stale/partial build — rebuild libsrmech): {report['unresolved']}"
    )
    assert report["consistent"] is True
    assert report["checked_ops"] == len(C_CLAIMS)


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="no native library loaded (pure install)")
def test_the_rc299_eigvals_claim_specifically_resolves():
    """The op that motivated rc300 is really in scope of the check.

    rc299 reclassified ``mat_eigvals`` to ``c_dispatched`` while its dispatch
    site could silently pure-path. `#918` had the parallel defect of
    ``CEIL_WIRE_GLUE_GAPS`` never having ``mat_eigvals`` in scope AT ALL, so
    naming it explicitly here is the guard against a repeat."""
    key = "srmech.math.laplacian.mat_eigvals"
    assert key in C_CLAIMS, f"{key} is not covered by the claim manifest"
    assert "srmech_mat_eigvals_ws" in C_CLAIMS[key]
    for sym in C_CLAIMS[key]:
        assert hasattr(_native.LIB, sym), f"{key} claims absent symbol {sym}"


# ── 3. the check DETECTS a missing symbol ─────────────────────────────────────

class _LibMissingSymbols:
    """A library proxy with named symbols hidden — a stale build, simulated."""

    def __init__(self, lib, hidden):
        self._lib = lib
        self._hidden = frozenset(hidden)

    def __getattr__(self, name):
        if name in self._hidden:
            raise AttributeError(name)
        return getattr(self._lib, name)


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="no native library loaded (pure install)")
def test_report_detects_a_hidden_symbol(monkeypatch):
    """Hide a claimed symbol; the report must NAME the affected op.

    This is the test that stops this file from being another check that passes
    because it is not looking. A green suite is only evidence if the red case is
    reachable — so the red case is asserted here directly."""
    hidden = "srmech_mat_eigvals_ws"
    monkeypatch.setattr(
        _native, "LIB", _LibMissingSymbols(_native.LIB, {hidden}))

    report = _native.c_claim_report()

    assert report["consistent"] is False, (
        "hiding a claimed symbol did NOT make the report inconsistent — the "
        "check is not actually looking at the library"
    )
    key = "srmech.math.laplacian.mat_eigvals"
    assert key in report["unresolved"]
    assert hidden in report["unresolved"][key]


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="no native library loaded (pure install)")
def test_describe_surfaces_the_inconsistency(monkeypatch):
    """describe() must carry the failure too — that is where an LLM reads it.

    A caller on the MCP surface sees ``native.has_native: true`` and can
    reasonably conclude the promised C path exists. Before rc300 there was no
    key that could say otherwise."""
    import srmech

    monkeypatch.setattr(
        _native, "LIB",
        _LibMissingSymbols(_native.LIB, {"srmech_mat_eigvals_ws"}))

    claims = srmech.describe()["c_claims"]
    assert claims["consistent"] is False
    assert "srmech.math.laplacian.mat_eigvals" in claims["unresolved"]


# ── 4. the pure path must not be broken by any of this ────────────────────────

def test_pure_install_is_healthy_and_makes_no_claim(monkeypatch):
    """``HAS_NATIVE`` False is the pure wheel's NORMAL state, not a defect.

    The pure wheel ships no library at all, so there is no claim to contradict.
    The report must say so without raising — a hard failure here would break a
    legitimate install over a condition that does not apply to it."""
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    monkeypatch.setattr(_native, "LIB", None)

    report = _native.c_claim_report()
    assert report["native"] is False
    assert report["consistent"] is True
    assert report["unresolved"] == {}
    assert report["checked_ops"] == 0
    # the unverifiable count is a property of the MANIFEST, not of the library,
    # so it is still reported on a pure install.
    assert report["unverifiable"] == len(UNVERIFIABLE_CLAIMS)


def test_describe_works_on_a_pure_install(monkeypatch):
    """describe() must stay callable, and keep its other keys, with no library."""
    import srmech

    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    monkeypatch.setattr(_native, "LIB", None)

    d = srmech.describe()
    assert d["native"]["has_native"] is False
    assert d["c_claims"]["native"] is False
    assert d["c_claims"]["consistent"] is True
    assert d["tools"]["total"] > 0          # the rest of describe() is intact
    assert d["carriers"]["total"] > 0


def test_c_claims_module_imports_without_a_library():
    """The manifest is plain data — it must not need ctypes or a loaded lib.

    It ships in the pure wheel too, so an import-time dependency on the native
    shim's loaded state would break that wheel."""
    import srmech.introspect._c_claims as mod

    assert isinstance(mod.C_CLAIMS, dict) and mod.C_CLAIMS
    assert all(isinstance(v, tuple) and v for v in mod.C_CLAIMS.values())
    assert all(s.startswith("srmech_")
               for syms in mod.C_CLAIMS.values() for s in syms)


# ── 5. the unchecked region is DOWN-ONLY ──────────────────────────────────────

def test_unverifiable_claims_ratchet_down_only():
    """The blind spot is named and may only shrink.

    The static walk cannot attribute a symbol to these ops. That is a real limit
    of this check and it is recorded rather than hidden: a RISING count means a
    new C-backed claim shipped that nothing can verify, which is the exact
    regression this ratchet exists to forbid."""
    assert len(UNVERIFIABLE_CLAIMS) <= UNVERIFIABLE_CEILING, (
        f"unverifiable c_dispatched claims rose to {len(UNVERIFIABLE_CLAIMS)} "
        f"(ceiling {UNVERIFIABLE_CEILING}). A new C-backed claim shipped that "
        f"the claim check cannot see. Give the op a statically attributable "
        f"dispatch path rather than raising this number."
    )


def test_unverifiable_and_checked_partition_the_ledger():
    """checked + unverifiable == every c_dispatched op. No op is simply dropped.

    Without this, an op could vanish from BOTH sets and the ceiling would still
    pass — coverage loss disguised as coverage."""
    import json

    ledger = _PY_ROOT / "tests" / "rosetta_classification.ndjson"
    rows = [json.loads(x) for x in
            ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
    c_dispatched = {r["defined_at"] for r in rows if r["bucket"] == "c_dispatched"}

    covered = set(C_CLAIMS) | set(UNVERIFIABLE_CLAIMS)
    assert covered == c_dispatched, (
        "the claim manifest and the ledger disagree on the c_dispatched set; "
        f"ledger-only={sorted(c_dispatched - covered)}, "
        f"manifest-only={sorted(covered - c_dispatched)}"
    )
