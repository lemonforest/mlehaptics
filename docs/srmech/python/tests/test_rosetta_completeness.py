"""Rosetta-completeness ratchet (rc7; issue #928).

The C-mirror goal: every public **compute** op in ``srmech`` should dispatch to
a bit-exact C twin OR be a pure composition of such twins, so ``libsrmech`` runs
standalone — on a full OS *or* a thread-less microcontroller — with no host
Python. This test is the down-only debt ledger for that goal (cf. the C-transpile
libm ratchet that went 23 -> 0): the ``python_only_irreducible`` and
``c_exists_unbound`` counts only ever DECREASE.

How it works:
  1. Enumerate the live public-op surface (every public callable defined in
     ``srmech.amsc`` / ``srmech.qm`` / ``srmech.signal_processing``), keyed by
     its canonical ``defined_at`` = ``<module>.<qualname>`` (re-export-stable).
  2. Load the committed classification (``rosetta_classification.ndjson``) — one
     of six buckets per op (see ROSETTA_LEDGER.md §"The classification").
  3. Assert the live set and the classified set agree EXACTLY (a new op with no
     bucket fails here -> forces every addition to be classified; a removed op
     left in the file fails too -> keeps the ledger current).
  4. Assert the two DEBT buckets are at or below their pinned ceilings. To close
     debt: give an op its C twin (or wire the unbound one up), move its line to
     ``c_dispatched`` / ``composition_of_c``, and LOWER the matching ceiling.

The ceilings move DOWN only. Raising one is the one edit this test exists to
forbid — a rising ceiling means a Python-only kernel was added without a C twin,
which is exactly the standalone-C regression the ledger guards against.

Buckets (see ROSETTA_LEDGER.md):
  c_dispatched           — routes to a srmech_* C symbol (standalone-ready)
  composition_of_c       — pure composition of c_dispatched ops (standalone-ready)
  c_exists_unbound       — DEBT (cheap): a C twin exists, Python doesn't dispatch
  python_only_irreducible— DEBT: irreducible kernel, no C twin yet
  bignum_reference       — intentional exact-rational arbitrary-precision oracle
  non_compute            — IO / registry / schema / introspection (no kernel)
"""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
from pathlib import Path

import pytest

# #564 (numpy out the door): the qm / signal_processing surfaces are numpy-free
# now, and this audit walks them with stdlib importlib / inspect / pkgutil only
# (a submodule that still fails to import is simply skipped by ``_iter_submodules``
# — it contributes no live ops). So the completeness ratchet runs numpy-ABSENT
# (no ``importorskip``; the test must PASS, not skip, with numpy uninstalled).

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# Roots of the public COMPUTE surface (mirrors notes/_rosetta_inventory.py).
_ROOTS = ("srmech.amsc", "srmech.qm", "srmech.signal_processing")

# ----- the down-only debt ceilings (rc7 baseline; issue #928) -----------
# LOWER these as ops gain C twins. NEVER raise them.
# rc67: symmetric_eigendecompose stopped being Python-only-irreducible — it now
# delegates to the c_dispatched hermitian_eigendecompose + phase-canon, so it
# moved to composition_of_c. python_only_irreducible 108 -> 107.
# rc6 (0.9.0, §60 / F864): klein4_random earns its standalone-C MT19937 twin
# srmech_klein4_random (byte-identical to random.Random(seed).randrange(4)) and
# dispatches to it -> c_dispatched. python_only_irreducible 107 -> 106.
CEIL_PYTHON_ONLY_IRREDUCIBLE = 106
# rc8: SHA-256 mint cluster (6 ops) routed off raw hashlib onto sha256_raw -> 17.
# rc9: octonion left_mult/right_mult/conjugate (3) delegate to the C-backed
# hdc.loop_* family -> moved c_exists_unbound -> composition_of_c -> 14.
# rc10: cascade.cd_basis_product dispatches to srmech_cd_basis_product
# (-> c_dispatched) and octonion_mult_table composes it (-> composition_of_c) -> 12.
# rc11: cascade.hamming_encode/syndrome dispatch to srmech_hamming_* (-> c_dispatched)
# and hamming_decode_correct composes hamming_syndrome (-> composition_of_c) -> 9.
# rc12: hdc.polar_{bind,bundle,density} dispatch to srmech_polar_* (-> c_dispatched);
# all int8, bit-exact -> 6.
# rc13: lmmse.op routes its solve through the dense_solve cascade + its matvec
# through dense_matvec_complex (numpy is carriers-only there now) -> composes two
# c_dispatched ops -> composition_of_c -> 5. The remaining 5 were the Klein-4
# family (see also test_numpy_math_ratchet.py — the source-level guard that keeps
# numpy a carrier, not a math engine).
# rc170 (§53 / F818): klein4_bind/_bundle/_similarity dispatch to srmech_klein4_*
# (the C twins always shipped + were ctypes-bound; hdc.py just never called them)
# -> c_dispatched; klein4_unbind == klein4_bind(c, a) so it composes the now-
# dispatched bind -> composition_of_c. 5 -> 1 (only klein4_triality_cycle).
# rc171 (§53 / F818): klein4_triality_cycle dispatches to srmech_klein4_triality_cycle
# (same forward/inverse 3-cycle tables -> bit-identical) -> c_dispatched. 1 -> 0:
# the c_exists_unbound DEBT IS NOW EMPTY — every public op with a C twin dispatches
# to it. Keep this at 0; a regression means a Python-only op shipped with an
# unbound C twin — wire it, don't raise the ceiling.
CEIL_C_EXISTS_UNBOUND = 0

_DEBT_BUCKETS = ("python_only_irreducible", "c_exists_unbound")
_ALL_BUCKETS = (
    "c_dispatched", "c_exists_unbound", "composition_of_c",
    "python_only_irreducible", "bignum_reference", "non_compute",
)


def _iter_submodules(root_name):
    root = importlib.import_module(root_name)
    yield root
    if not hasattr(root, "__path__"):
        return
    for info in pkgutil.walk_packages(root.__path__, root_name + "."):
        name = info.name
        tail = name.rsplit(".", 1)[-1]
        if tail.startswith("_") and tail != "__init__":
            continue
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield importlib.import_module(name)
        except Exception:  # noqa: BLE001 — a module that won't import has no live ops
            continue


def _live_ops():
    """Map canonical ``defined_at`` -> ``exposed_as`` for every public op.

    Same walk as notes/_rosetta_inventory.py: public, callable, NON-class,
    DEFINED in the srmech package (skips numpy/stdlib re-exports), deduped by
    ``<module>.<qualname>`` so re-exports collapse to one canonical identity.
    """
    seen = {}
    for root_name in _ROOTS:
        try:
            importlib.import_module(root_name)
        except Exception:  # noqa: BLE001
            continue
        for mod in _iter_submodules(root_name):
            names = getattr(mod, "__all__", None)
            if names is None:
                names = [n for n in dir(mod) if not n.startswith("_")]
            for n in names:
                obj = getattr(mod, n, None)
                if not callable(obj) or inspect.isclass(obj):
                    continue
                objmod = getattr(obj, "__module__", "") or ""
                if not objmod.startswith("srmech"):
                    continue
                qual = getattr(obj, "__qualname__", n)
                key = f"{objmod}.{qual}"
                seen.setdefault(key, f"{mod.__name__}.{n}")
    return seen


def _load_classification():
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def test_every_bucket_value_is_known():
    cls = _load_classification()
    bad = {da: b for da, b in cls.items() if b not in _ALL_BUCKETS}
    assert not bad, f"classification has unknown bucket values: {bad}"


def test_live_surface_is_fully_classified():
    """Every live public op has a committed bucket (new ops must be classified)."""
    live = _live_ops()
    cls = _load_classification()
    unclassified = sorted(set(live) - set(cls))
    assert not unclassified, (
        f"{len(unclassified)} live op(s) have no Rosetta classification — add a "
        f"bucket line to rosetta_classification.ndjson for each:\n"
        + "\n".join(f"  - {d}  (exposed: {live[d]})" for d in unclassified)
    )


def test_no_stale_classification():
    """Every classified op still exists (removed ops must leave the ledger)."""
    live = _live_ops()
    cls = _load_classification()
    stale = sorted(set(cls) - set(live))
    assert not stale, (
        f"{len(stale)} classified op(s) no longer exist — remove their lines "
        f"from rosetta_classification.ndjson:\n" + "\n".join(f"  - {d}" for d in stale)
    )


@pytest.mark.parametrize("bucket,ceiling", [
    ("python_only_irreducible", CEIL_PYTHON_ONLY_IRREDUCIBLE),
    ("c_exists_unbound", CEIL_C_EXISTS_UNBOUND),
])
def test_debt_bucket_is_monotone_decreasing(bucket, ceiling):
    """The two DEBT buckets stay at or below their down-only ceilings.

    If this fails because the count went UP, a Python-only op was added without a
    C twin (or an unbound one slipped in) — give it a twin / wire it up instead
    of raising the ceiling. If the count went DOWN, lower the ceiling to match.
    """
    cls = _load_classification()
    live = set(_live_ops())
    count = sum(1 for da, b in cls.items() if b == bucket and da in live)
    assert count <= ceiling, (
        f"{bucket} = {count} exceeds the down-only ceiling {ceiling}. "
        f"A standalone-C regression: close the debt, don't raise the ceiling."
    )
    # Tightness guard: if the real count dropped below the ceiling, the ceiling
    # must be lowered to lock the win in (keeps the ratchet honest).
    assert count == ceiling, (
        f"{bucket} = {count} is BELOW its ceiling {ceiling} — debt was closed; "
        f"lower CEIL_{bucket.upper()} to {count} to lock the ratchet."
    )
