#!/usr/bin/env python3
"""Generate ``srmech/introspect/_c_claims.py`` — the op -> C-symbol claim manifest.

rc300 (`#T938`). The Rosetta ledger classifies 263 ops ``c_dispatched``: "routes
to a ``srmech_*`` C symbol". That is a CLAIM about the loaded library, and until
rc300 nothing checked it. A dispatch site gated on
``hasattr(_native.LIB, "srmech_x")`` falls silently to the pure path when the
symbol is absent — correct answers, but the ``c_dispatched`` claim is then FALSE
and nothing says so. rc299 reclassified ``mat_eigvals`` to ``c_dispatched``,
which is exactly such a site (``laplacian.py`` ``_mat_eigvals_native``).

Why a committed manifest rather than a runtime walk: the ledger
(``tests/rosetta_classification.ndjson``) is a TEST fixture and does not ship in
the wheel, and a bytecode walk of the whole public surface is far too slow to
run inside ``describe()``. So extraction happens HERE, at dev time, and the
result is committed as a plain-Python module that ships in both the platform and
the pure wheel. ``tests/test_c_claim_resolution_rc300.py`` re-runs this
extraction against the live tree and fails if the committed manifest has
drifted, so the manifest cannot go stale silently.

Extraction (deliberately SHALLOW, so a symbol is attributed to the op that
actually names it rather than to every op transitively above it):

  * start at the ledger op;
  * follow only private helpers in the SAME module, ``*_c`` shims, and the
    ``has_native_*`` predicates in ``srmech._native`` (the canonical
    convention, and the bridge used by the lazy
    ``getattr(nat, "has_native_x", None)`` probe idiom);
  * collect every ``srmech_*`` token appearing as a bytecode name or string
    constant;
  * keep only tokens DECLARED IN ``c/include/srmech.h``. That filter removes
    incidental look-alike strings (e.g. the ``"srmech_kext_"`` tempfile prefix
    in ``coupling.py``) and would surface a typo'd dispatch symbol, which can
    never resolve and would silently pure-path forever.

Ops the walk cannot attribute a symbol to (dispatch reached through a class
method, a registry indirection, ...) are NOT silently dropped — they are emitted
as ``UNVERIFIABLE_CLAIMS`` with a down-only ceiling, so the size of the
unchecked region is a named, ratcheted number instead of an invisible gap.

Usage (rc346, `#T975` — run the ordered pass, not this script)::

    python3 tools/regen_all.py               # from docs/srmech/python
    python3 tools/regen_all.py --check       # exit 1 if anything is stale

This generator is INDEPENDENT of the tool docs — it reads the Rosetta ledger
and ``c/include/srmech.h``, and rc346 measured its output unchanged under
adding an op, editing a summary and editing ``_tool_docs.py``. It runs in the
pass anyway because ``--check`` must answer "is this stale?" for every
generated file rather than for a remembered subset, and because its true
inputs (the ledger, the header) move for reasons the tool surface does not
predict. A direct run refuses unless ``--standalone`` is passed; the
per-file ``--check`` below still works standalone.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY_ROOT = _HERE.parent                      # <repo>/docs/srmech/python
_SRMECH_ROOT = _PY_ROOT.parent               # <repo>/docs/srmech
_LEDGER = _PY_ROOT / "tests" / "rosetta_classification.ndjson"
_HEADER = _SRMECH_ROOT / "c" / "include" / "srmech.h"
# rc404 (`#T1069`): was `srmech/amsc/_c_claims.py` — a path ADR-0010 retired.
# The shipped artifact is `srmech/introspect/_c_claims.py`; `srmech/amsc/` has
# no `_c_claims.py` at all.
#
# SCOPE OF THE DEFECT, stated precisely, because it is narrower than it looks:
# the AUTHORITATIVE output path is the one in tools/codegen_manifest.py
# (`output="python/srmech/introspect/_c_claims.py"`), and that has been correct
# all along — so `regen_all.py` and the ripple gate were never affected. Only
# the `--standalone` escape hatch reads this constant, and it would have
# written a spurious dead file under amsc/ while leaving the real artifact
# untouched, reporting success either way. Aligning the two removes the
# divergence. Verified after the fix: a standalone render reproduces the
# committed `srmech/introspect/_c_claims.py` byte-for-byte.
_OUT = _PY_ROOT / "srmech" / "introspect" / "_c_claims.py"

_SYM = re.compile(r"^srmech_[A-Za-z0-9_]{2,}$")
_HASNAT = re.compile(r"^has_native_[A-Za-z0-9_]+$")
_NATIVE_MOD = "srmech._native"


def _header_symbols() -> set:
    """Every ``srmech_*`` token declared in the public C header."""
    text = _HEADER.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"\bsrmech_[A-Za-z0-9_]+\b", text))


def _codes(code, seen=None):
    if seen is None:
        seen = set()
    if id(code) in seen:
        return []
    seen.add(id(code))
    out = [code]
    for const in code.co_consts:
        if inspect.iscode(const):
            out += _codes(const, seen)
    return out


def _tokens(fn) -> set:
    """Every name + string constant anywhere in ``fn`` (including nested code)."""
    code = getattr(fn, "__code__", None)
    if code is None:
        return set()
    out = set()
    for c in _codes(code):
        out |= set(c.co_names)
        out |= {k for k in c.co_consts if isinstance(k, str)}
    return out


def _resolve(dotted: str):
    """Resolve a ledger ``defined_at`` key to a live object."""
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        mod_name = ".".join(parts[:split])
        rest = parts[split:]
        try:
            obj = importlib.import_module(mod_name)
        except Exception:  # noqa: BLE001 — optional / heavy submodule
            continue
        try:
            for part in rest:
                obj = getattr(obj, part)
            return obj
        except Exception:  # noqa: BLE001
            continue
    return None


def _lookup(fn, name, native_mod):
    """Resolve ``name`` as used inside ``fn``.

    Bare global, attribute of an imported ``srmech`` module in ``fn``'s globals,
    or an attribute of the ``_native`` shim (the lazy ``from . import _native as
    nat`` idiom keeps the module out of module-level globals)."""
    g = getattr(fn, "__globals__", {}) or {}
    if name in g:
        yield g[name]
    for value in g.values():
        if isinstance(value, types.ModuleType) and (
                getattr(value, "__name__", "") or "").startswith("srmech"):
            attr = getattr(value, name, None)
            if attr is not None:
                yield attr
    attr = getattr(native_mod, name, None)
    if attr is not None:
        yield attr


def _symbols_for(op_fn, native_mod) -> set:
    """The ``srmech_*`` tokens this op's own dispatch path names."""
    own_mod = getattr(op_fn, "__module__", "") or ""
    found = set()
    seen = set()
    queue = [op_fn]
    while queue:
        fn = queue.pop()
        code = getattr(fn, "__code__", None)
        if code is None or id(code) in seen:
            continue
        seen.add(id(code))
        toks = _tokens(fn)
        found |= {t for t in toks if _SYM.match(t)}
        fn_mod = getattr(fn, "__module__", "") or ""
        for tok in toks:
            if not (_HASNAT.match(tok) or tok.startswith("_") or tok.endswith("_c")):
                continue
            for obj in _lookup(fn, tok, native_mod):
                if not callable(obj) or inspect.isclass(obj):
                    continue
                obj_mod = getattr(obj, "__module__", "") or ""
                if obj_mod in (own_mod, _NATIVE_MOD, fn_mod):
                    queue.append(obj)
    return found


def extract():
    """-> (claims: dict[op, tuple[sym]], unverifiable: tuple[op], off_header: dict)."""
    sys.path.insert(0, str(_PY_ROOT))
    native_mod = importlib.import_module(_NATIVE_MOD)
    header = _header_symbols()

    rows = [json.loads(line) for line in
            _LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    c_dispatched = sorted(r["defined_at"] for r in rows if r["bucket"] == "c_dispatched")
    composition = sorted(r["defined_at"] for r in rows
                         if r["bucket"] == "composition_of_c")

    claims = {}
    unverifiable = []
    off_header = {}
    for key in c_dispatched:
        fn = _resolve(key)
        if fn is None:
            unverifiable.append(key)
            continue
        syms = _symbols_for(fn, native_mod)
        declared = sorted(s for s in syms if s in header)
        stray = sorted(s for s in syms if s not in header)
        if stray:
            off_header[key] = stray
        if declared:
            claims[key] = tuple(declared)
        else:
            unverifiable.append(key)

    # rc463 (`#T1188`) — the UNDERSTATED-PARITY half, which is the reverse of the
    # direction this ledger was built to watch.
    #
    # Through rc462 the harvest read ONLY the ``c_dispatched`` bucket, so a
    # symbol reached from a ``composition_of_c`` op was claimed by nobody at
    # all. The canonical case is ``srmech_svd_f64``: DECLARED in srmech.h,
    # DEFINED in c/src/srmech_svd_qr.c, ctypes-BOUND in _native/__init__.py, and
    # actually CALLED by ``laplacian.mat_svd`` — which the ledger classifies
    # ``composition_of_c`` because it also composes other C ops. So ``svd`` read
    # as Python-only while it was C-dispatched. **Measured at rc463: 39 header
    # symbols were in exactly that state** (``srmech_svd_f64``, its ws_bound
    # peer, and 37 genome symbols), not the one the defect was found through.
    #
    # These ops are added to ``claims`` ONLY. They are never added to
    # ``unverifiable``: a composition that names no direct symbol is not a blind
    # spot, it is the DEFINITION of its bucket — so the unverifiable ceiling
    # keeps meaning exactly what it meant, a ``c_dispatched`` op whose symbol
    # the static walk could not attribute.
    for key in composition:
        fn = _resolve(key)
        if fn is None:
            continue
        syms = _symbols_for(fn, native_mod)
        declared = sorted(s for s in syms if s in header)
        stray = sorted(s for s in syms if s not in header)
        if stray:
            off_header.setdefault(key, stray)
        if declared:
            claims[key] = tuple(declared)
    return claims, tuple(sorted(unverifiable)), off_header


_TEMPLATE = '''"""GENERATED by ``tools/gen_c_claims.py`` — do not edit by hand.

The op -> C-symbol CLAIM manifest (rc300, `#T938`). Every op the Rosetta ledger
classifies ``c_dispatched`` asserts it "routes to a ``srmech_*`` C symbol". This
module records WHICH symbols, so that claim can be checked against the library
actually loaded instead of merely asserted in a fixture.

Why the check matters: every native dispatch site is gated on
``hasattr(_native.LIB, "srmech_x")``. When the symbol is absent the gate falls to
the pure-Python path — correct answers, but the ``c_dispatched`` claim is FALSE
and, before rc300, nothing said so. ABI matching does not cover this: the header
adds symbols ABI-additively ("new symbols only, so SRMECH_ABI_VERSION stays N"),
so a stale-but-ABI-{abi} library is a REACHABLE state with a correct pure
fallback and a silently false classification.

Consumed by :func:`srmech._native.c_claim_report` and surfaced as
``srmech.describe()["c_claims"]``. Regenerate with::

    python3 tools/regen_all.py            # from docs/srmech/python

``tests/test_c_claim_resolution_rc300.py`` re-derives this from the live tree and
fails on drift, so the manifest cannot silently go stale.
"""
from __future__ import annotations

from typing import Dict, Tuple

#: ``defined_at`` -> the C symbols that op's own dispatch path names.
C_CLAIMS: Dict[str, Tuple[str, ...]] = {{
{claims_body}}}

#: ``c_dispatched`` ops whose C symbol the static walk cannot attribute (the
#: dispatch is reached through a class method or a registry indirection). These
#: are NOT checked — listed explicitly so the unchecked region is a named,
#: ratcheted number rather than an invisible gap. DOWN-ONLY: see
#: ``UNVERIFIABLE_CEILING``.
UNVERIFIABLE_CLAIMS: Tuple[str, ...] = (
{unverifiable_body})

#: Down-only ratchet on ``len(UNVERIFIABLE_CLAIMS)``. Lower it when an op gains a
#: statically attributable dispatch path; RAISING it is the edit this ratchet
#: exists to forbid — a rise means a new C-backed claim shipped that nothing can
#: verify.
UNVERIFIABLE_CEILING: int = {ceiling}
'''


def render(claims, unverifiable, abi: int) -> str:
    claims_body = "".join(
        "    {!r}: ({},),\n".format(key, ", ".join(repr(s) for s in syms))
        if len(syms) == 1 else
        "    {!r}: (\n{}    ),\n".format(
            key, "".join("        {!r},\n".format(s) for s in syms))
        for key, syms in sorted(claims.items()))
    unverifiable_body = "".join("    {!r},\n".format(k) for k in unverifiable)
    return _TEMPLATE.format(
        claims_body=claims_body,
        unverifiable_body=unverifiable_body,
        ceiling=len(unverifiable),
        abi=abi,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the generated file would change")
    args = ap.parse_args()

    claims, unverifiable, off_header = extract()

    sys.path.insert(0, str(_PY_ROOT))
    native_mod = importlib.import_module(_NATIVE_MOD)
    abi = getattr(native_mod, "EXPECTED_ABI_VERSION", 0)

    text = render(claims, unverifiable, abi)

    n_syms = len({s for syms in claims.values() for s in syms})
    print(f"c_dispatched ops with attributable symbols : {len(claims)}")
    print(f"distinct C symbols claimed                 : {n_syms}")
    print(f"unverifiable (ratcheted)                   : {len(unverifiable)}")
    if off_header:
        print("\ntokens matched but NOT declared in srmech.h (filtered out):")
        for key, stray in sorted(off_header.items()):
            print(f"  {key}: {stray}")

    if args.check:
        current = _OUT.read_text(encoding="utf-8") if _OUT.exists() else ""
        if current != text:
            print("\nDRIFT: _c_claims.py is stale — rerun tools/gen_c_claims.py")
            return 1
        print("\n_c_claims.py is up to date.")
        return 0

    _OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"\nwrote {_OUT}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from codegen_manifest import require_regen_all

    # --check is read-only, so it stays reachable standalone: refusing it
    # would break the per-file staleness probe with no defect to prevent.
    if "--check" not in sys.argv[1:]:
        require_regen_all("gen_c_claims")
    raise SystemExit(main())
