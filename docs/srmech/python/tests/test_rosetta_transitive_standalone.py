"""Rosetta TRANSITIVE-standalone ratchet (v0.9.0rc12).

The existing ``test_rosetta_completeness.py`` checks that every op is *classified*
and that the two debt-bucket *counts* don't rise — but it NEVER walks the call
graph. So a ``composition_of_c`` op (which claims "standalone-C-ready: I only
compose ops that each reach C") could silently reach a ``bignum_reference`` /
``python_only_debt`` leaf and the ratchet wouldn't notice. That blind spot
is exactly how ``sed_is_navigable`` shipped mislabeled (it reached the
pure-Python ``left_mult_is_invertible``); see the rc12 SedenionRegister fix.

This ratchet closes the blind spot: for every ``composition_of_c`` op it walks
the TRANSITIVE callee graph (through methods + private helpers) and asserts the
op reaches NO non-standalone-ready leaf, except a small DOWN-ONLY allowlist of
explicitly-acknowledged debt (each with the leaf it needs + the rc that closes
it). A NEW composition→non-ready edge that is not allowlisted FAILS — so this
class of mislabel can never recur silently.

Numpy-free (walks srmech.amsc / qm / signal_processing with stdlib importlib /
inspect only).

── rc281 EXTENSION: the WIRE-FORMAT GLUE ratchet ───────────────────────────────

The walk above proves a composite *reaches* C-backed leaves. It does NOT prove a
bare-C host can run the composite's own GLUE — because it treats every
``composition_of_c`` op as a LEAF and stops there. That is strictly weaker than
ADR-0003 §2/§3 ("every composite, including orchestrators, gets its own C entry
point so a C-only caller can invoke the whole operation"), and it is exactly how
``integrate`` / ``mint_strand`` / ``amplify`` / ``copy_number_of`` each shipped as a
1:1-parity gap wearing an honest-looking label (see
``docs/srmech/notes/c_host_parity_audit_rc273.md`` §0, "the systemic root cause").

The second ratchet below closes that. Its SCOPE is the **wire-format surface**: the
ops that produce or consume srmech's own on-disk / on-wire byte structures — caps,
strands, manifests, section stores, tomes. That scope is not arbitrary. It is where
"a bare-C host cannot run this op" is a load-bearing claim rather than a theoretical
one, because the FORMAT is srmech's own: if the glue that lays out the bytes lives
only in Python, a C-only host cannot produce or consume the genome at all. It is
also the standing user directive (genome-must-exist-fully-in-C). Pure-math
``composition_of_c`` ops (the ``qm`` / ``signal_processing`` / dense-carrier
families) are deliberately OUT of scope: they compose C primitives over carriers with
no format to get wrong, and the transitive walk above already covers them.

In scope, an op must demonstrate its OWN GLUE is C-reachable, which means ONE of:

  (a) it declares a WHOLE-OP C peer in ``_WHOLE_OP_C_PEER`` — a single C entry point
      that performs the entire operation. The declaration is VERIFIED, not trusted:
      the symbol must be declared in ``c/include/srmech.h`` AND must actually be
      reachable through the op's dispatch glue.
  (b) it is on the DOWN-ONLY ``_KNOWN_GLUE_GAPS`` allowlist — a real, named,
      still-open parity gap with its audit reference.

Anything else — in particular any NEW ``composition_of_c`` op added to the genome /
plasmid surface without a C peer — FAILS. That is the whole point: this gap class
cannot recur silently.

Note what deliberately does NOT count as (a): a private helper that dispatches a C
PRIMITIVE. ``condense`` reaching ``srmech_genome_chromatin`` for its cap bytes is
"reaches a C leaf" — the weaker property this ratchet exists to reject — because the
range-find, region resolution and splice around that cap are still Python-only. Only
a whole-op entry point, or a pure delegation to one, satisfies ADR-0003.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
import re
import textwrap
from pathlib import Path

import pytest

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
# rc177 annex: mirror the ledger-walk extension to bus/dsl (this ratchet only
# iterates composition_of_c rows — all 39 bus/dsl rows are non_compute, so the
# extension is a no-op for its assertion; kept for cross-walk consistency).
# rc183 HOST-GLUE annex: mirror the extension to mcp/cli/llm too (all +24 rows are
# non_compute, so likewise a no-op for the composition_of_c assertion; kept for
# cross-walk consistency).
# rc218 PARITY-COMPLETENESS annex: mirror the extension to spectral/rbs_lm/
# introspect/profile_loader (the spectral + rbs_lm compute rows ARE
# composition_of_c, so this ratchet now walks them for hidden non-ready leaves).
#
# rc361 (`#T1034`): "kept identical across all four walk sites" is no longer a
# request to the next author — the tuple is SINGLE-SOURCED in
# tests/rosetta_roots.py and the other three sites import it. The four copies
# were measured identical before the collapse.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)
from rosetta_roots import ROSETTA_ROOTS as _ROOTS  # noqa: E402

# Buckets that are NOT standalone-C-ready (a composition_of_c op must not reach
# one transitively).
_NOT_READY = frozenset(
    ("bignum_reference", "python_only_debt", "c_exists_unbound")
)

# ── DOWN-ONLY allowlist of acknowledged composition→non-ready debt ──────────
# Each entry: (composition_of_c op defined_at, the non-ready leaf it reaches).
# This set may only SHRINK. To close an entry: give the leaf a C path (or
# reclassify) and DELETE the line. NEVER add without an explicit user-approved
# reason + the rc that will close it.
_ACKNOWLEDGED = {
    # (rc16 closed the sed_couple_working / sed_uncouple_working →
    # `hypercomplex_couple` edges: the coupler was rewritten to the exact-Q61
    # octonion couple `_couple_q61` that dispatches to `srmech_hypercomplex_couple_q61`
    # and composes only c_dispatched primitives — so it is now `c_dispatched`,
    # not `python_only_debt`, and the edges are no longer non-ready.)
    # (rc13 closed the exact_dft.lift → pi_cascade_digits edge by rerouting the
    # FPU-lift 2π to the c_dispatched `rational.atan`: 2π = 8·atan(1).)
}


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
        # .adapters = the net/file-IO collector surface (requests + optional
        # netCDF4/rasterio) — the documented IO-exclusion, see ROSETTA_LEDGER.md.
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield importlib.import_module(name)
        except Exception:  # noqa: BLE001
            continue


def _live_objects():
    """Map canonical ``defined_at`` (``<module>.<qualname>``) -> the object."""
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
                seen.setdefault(f"{objmod}.{qual}", obj)
    return seen


def _load_classification():
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def _key(obj):
    m = getattr(obj, "__module__", "") or ""
    return f"{m}.{getattr(obj, '__qualname__', '')}" if m.startswith("srmech") else None


def _names_in(code):
    """All global/attribute names referenced by a code object (recursing into
    nested code objects: comprehensions, lambdas, inner defs)."""
    out = set(code.co_names)
    for const in code.co_consts:
        if inspect.iscode(const):
            out |= _names_in(const)
    return out


def _local_imports(fn):
    """Resolve FUNCTION-LOCAL imports (e.g. ``from . import hypercomplex_couple``
    inside a method body) to {local_name: object} via an AST scan — these are
    invisible to ``fn.__globals__`` but are exactly where deferred-import leaves
    (the coupler, pi_cascade_digits) hide."""
    out = {}
    try:
        src = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(src)
    except (OSError, TypeError, SyntaxError):
        return out
    pkg = (getattr(fn, "__module__", "") or "").rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module
            if node.level:                      # relative: from . / .. import X
                parts = pkg.split(".")
                base = ".".join(parts[: len(parts) - (node.level - 1)] or parts)
                base = base + ("." + node.module if node.module else "")
            for alias in node.names:
                try:
                    mod = importlib.import_module(base)
                    out[alias.asname or alias.name] = getattr(mod, alias.name)
                except Exception:               # noqa: BLE001
                    continue
    return out


def _direct_callees(fn):
    """The srmech callables ``fn`` references — resolved through ``fn``'s own
    globals AND function-local imports (so deferred imports bind to the real
    object), following BOTH module-level functions AND ``Class().method`` /
    ``Class.method`` attribute calls."""
    g = dict(getattr(fn, "__globals__", {}) or {})
    g.update(_local_imports(fn))                 # local imports shadow/extend globals
    code = getattr(fn, "__code__", None)
    if code is None:
        return []
    names = _names_in(code)
    out = []
    classes = []
    for name in names:
        obj = g.get(name)
        if obj is None:
            continue
        if inspect.isclass(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            classes.append(obj)
        elif callable(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            out.append(obj)
    # method calls: an attribute name in co_names that is a method of a class
    # referenced in the same scope (covers the `_rehydrate(...).method()` /
    # `SedenionRegister().method()` adapter pattern).
    for cls in classes:
        for name in names:
            meth = getattr(cls, name, None)
            if callable(meth) and (getattr(meth, "__module__", "") or "").startswith("srmech"):
                out.append(meth)
    return out


def _reached_ledger_ops(start, cls):
    """Set of ledger ``defined_at`` keys transitively reachable from ``start``
    (a function object), recursing through non-ledger glue (methods/helpers)
    but treating a ``c_dispatched`` / ``composition_of_c`` ledger op as a LEAF
    (it is C-backed or itself validated — don't recurse into its fallback)."""
    reached = set()
    seen_code = set()
    queue = [start]
    while queue:
        fn = queue.pop()
        code = getattr(fn, "__code__", None)
        if code is None or id(code) in seen_code:
            continue
        seen_code.add(id(code))
        for callee in _direct_callees(fn):
            k = _key(callee)
            if k is not None and k in cls:
                reached.add(k)
                if cls[k] in ("c_dispatched", "composition_of_c", "non_compute"):
                    continue          # C-backed / validated-elsewhere leaf: stop
                # a not-ready ledger op: record but don't recurse further
                continue
            queue.append(callee)      # glue (method / private helper): recurse
    return reached


def test_no_composition_reaches_nonstandalone_leaf():
    cls = _load_classification()
    objs = _live_objects()
    violations = []
    for da, bucket in cls.items():
        if bucket != "composition_of_c":
            continue
        fn = objs.get(da)
        if fn is None:
            continue
        for leaf in _reached_ledger_ops(fn, cls):
            if cls.get(leaf) in _NOT_READY and (da, leaf) not in _ACKNOWLEDGED:
                violations.append(f"{da}  ->  {leaf}  ({cls[leaf]})")
    assert not violations, (
        "composition_of_c op(s) transitively reach a non-standalone-ready leaf "
        "and are NOT on the down-only acknowledged-debt allowlist — give the "
        "leaf a C path or fix the classification:\n  " + "\n  ".join(sorted(violations))
    )


def test_acknowledged_allowlist_is_still_live():
    """Every acknowledged (op, leaf) pair must still BE a real reachable edge —
    keeps the allowlist honest (a closed edge must be DELETED, not left)."""
    cls = _load_classification()
    objs = _live_objects()
    stale = []
    for da, leaf in _ACKNOWLEDGED:
        fn = objs.get(da)
        if fn is None or leaf not in _reached_ledger_ops(fn, cls):
            stale.append(f"{da} -> {leaf}")
    assert not stale, (
        "acknowledged-debt allowlist has stale entries (edge no longer reachable "
        "— DELETE the line, the debt is closed):\n  " + "\n  ".join(sorted(stale))
    )


# ═══════════════════════════════════════════════════════════════════════════════
# rc281 — the WIRE-FORMAT GLUE ratchet (see the module docstring for the why)
# ═══════════════════════════════════════════════════════════════════════════════

_HEADER = Path(__file__).resolve().parents[2] / "c" / "include" / "srmech.h"

#: Modules whose ``composition_of_c`` ops lay out srmech's own on-disk / on-wire
#: byte structures. Every op these modules expose is in scope.
_WIRE_FORMAT_MODULES = ("srmech.biology.genome", "srmech.biology.plasmid")

#: Individually-named in-scope ops that live OUTSIDE those modules. ``recursive_cut``
#: is the out-of-core recursive spectral bisection driver: it manages on-disk TOMES,
#: so it is a wire-format orchestrator even though it sits in ``laplacian``. Its
#: in-memory siblings there (``mat_norm``, ``normalized_cut_bisect``, …) are pure
#: carrier math and stay out of scope.
_WIRE_FORMAT_EXTRA = frozenset({"srmech.math.laplacian.recursive_cut"})

# ── (a) the VERIFIED whole-op C peers ────────────────────────────────────────
#: ``defined_at`` -> the single C entry point that performs the WHOLE operation.
#: Both halves of this claim are machine-checked below: the symbol must be declared
#: in c/include/srmech.h, and it must actually be reachable through the op's dispatch
#: glue. A declaration alone proves nothing — that was the rc273 failure mode.
_WHOLE_OP_C_PEER = {
    "srmech.biology.genome.accessible":       "srmech_genome_chromatin_access",
    # rc329 (§102 G7): the ACTIVE-TELOMERE packer earned its whole-op C peer
    # srmech_genome_active_telomere — the op⊗operand Hayflick cap pack (marker + label
    # + NUL + count, NUL-padded), factored out of srmech_genome_telomere_tick so a
    # bare-C host builds ONE active cap with no daughter-minting.
    "srmech.biology.genome.active_telomere":  "srmech_genome_active_telomere",
    "srmech.biology.genome.amplify":          "srmech_genome_amplify",       # rc281 (G6)
    "srmech.biology.genome.centromere_of":    "srmech_genome_centromere_of",
    "srmech.biology.genome.chromatin_of":     "srmech_genome_chromatin_of",
    "srmech.biology.genome.chromosome":       "srmech_genome_chromosome",
    # rc332 (§102 G7): the chromatin CONDENSE/DECONDENSE pair earned their whole-op C peers —
    # srmech_genome_condense (the shared label -> chromatin-range find + region resolution -> the
    # cap-splice insert index) and srmech_genome_decondense (the inverse per-block keep-mask). The
    # cap BYTES were already native (srmech_genome_chromatin); this rc lifts the Python-only
    # _chrom_range + region resolution into C, so a bare-C host runs each end-to-end.
    "srmech.biology.genome.condense":         "srmech_genome_condense",
    "srmech.biology.genome.copy_number_of":   "srmech_genome_copy_number",   # rc281 (G6)
    "srmech.biology.genome.decondense":       "srmech_genome_decondense",
    "srmech.biology.genome.genome":           "srmech_genome_mint",
    # rc333 (§102 G7): the GENES FAMILY earned its whole-op C peers — the per-gene
    # (label, leaves) BOUNDARY-PRESERVING read that srmech_genome_recall FLATTENS and
    # srmech_genome_gene_express_plan returns as SPANS. srmech_genome_genes is the in-memory
    # split; srmech_genome_genome_genes pages one chromosome's region off disk and splits it;
    # srmech_genome_genes_expressed is the demand-load orchestration (plan-walk + region-page +
    # gene_express collect). All three emit ONE shared (label, leaves) structure.
    "srmech.biology.genome.genes":            "srmech_genome_genes",
    # rc327 (§100 G2): the GAP-2 flagship builder earned its whole-op C peer
    # srmech_genome_from_graph — the G3 partition + per-group induced-subgraph relabel +
    # graph_to_kernel -> mint_strand loop + strand assembly, ALL in C. The LAST §100
    # G-series parity gap (the sibling of G3 below).
    "srmech.biology.genome.genome_from_graph": "srmech_genome_from_graph",
    "srmech.biology.genome.genome_genes":     "srmech_genome_genome_genes",   # rc333 (§102 G7)
    "srmech.biology.genome.genome_genes_expressed":
        "srmech_genome_genes_expressed",                                   # rc333 (§102 G7)
    # rc321 (§100 G3): the GRAPH partition earned its whole-op C peer
    # srmech_genome_graph_partition (recursive_cut + the exact-integer participation +
    # the antimode DECISION + per-node classify + group assembly, all in C). NOT the
    # strand-recovery `partition` below, which shares the DIFFERENT C name
    # srmech_genome_partition.
    "srmech.biology.genome.genome_partition": "srmech_genome_graph_partition",
    # `mint` is a pure delegation to `genome` (its whole body is `return genome(...)`),
    # so it inherits that op's entry point rather than owning a second one.
    "srmech.biology.genome.mint":             "srmech_genome_mint",
    # rc329 (§102 G7): the MINT-PLAN read loop earned its whole-op C peer
    # srmech_genome_mint_plan — encode_shape (plasmid-vs-nuclear) + the content-address
    # orientation per kernel, the WHOLE assembling loop in C (the per-step primitive was
    # already native; the loop that assembles the plan was not).
    "srmech.biology.genome.mint_plan":        "srmech_genome_mint_plan",
    "srmech.biology.genome.partition":        "srmech_genome_partition",
    "srmech.biology.genome.plasmid":          "srmech_genome_genome",
    # `quad_turn` is a pure delegation to the reversible Klein-4 bind primitive — the
    # whole op IS that one C call, so it is trivially C-runnable.
    "srmech.biology.genome.quad_turn":        "srmech_klein4_bind",
    "srmech.biology.genome.recall":           "srmech_genome_recall",
    "srmech.math.laplacian.recursive_cut":
        "srmech_laplacian_recursive_cut",                                 # rc284
    "srmech.biology.plasmid.genome_integrate_plasmids":
        "srmech_genome_integrate_plasmids",                               # rc279
    "srmech.biology.plasmid.plasmid_extract": "srmech_genome_plasmid_extract",
    # rc334 (§102 G7): add_plasmid — the LAST wire-glue gap — earned its whole-op C peer
    # srmech_genome_add_plasmid: the incremental CONSERVE (merge the section-count
    # accumulator + srmech_genome_conserved_core) + ORGANIZE (page every section off
    # disk, decode + harvest the induced core subgraph, pack it, then MINT the core +
    # FOLD the retained plasmids — the srmech_genome_integrate_plasmids discipline),
    # so a bare-C host runs one incremental add end-to-end. This DROPS
    # CEIL_WIRE_GLUE_GAPS 1 -> 0 and empties _KNOWN_GLUE_GAPS: the enumerated genome
    # wire-glue gap list is now EMPTY (the ADR-0003 genome-in-C commitment is met).
    "srmech.biology.plasmid.add_plasmid":     "srmech_genome_add_plasmid",
}

# ── (b) the DOWN-ONLY known-gap allowlist ────────────────────────────────────
#: ``defined_at`` -> (why it is still a gap, the audit / tracking reference).
#:
#: These are REAL, still-open ADR-0003 parity gaps — a bare-C host cannot run these
#: ops. They are acknowledged here so the ratchet can FAIL on anything NEW without
#: turning CI red on known-but-unfixed work.
#:
#: ⚠️ DOWN-ONLY. ``CEIL_WIRE_GLUE_GAPS`` below pins the length and a test asserts it
#: never grows. An entry leaves this list ONLY by landing its C peer (then move it to
#: ``_WHOLE_OP_C_PEER``). NEVER add an entry to make a failing build pass — a new op
#: without a C peer is the exact regression this ratchet exists to catch.
#:
#: Derived from the current tree (rosetta ledger × live C surface), not from a
#: hand-written list: rc276 closed `integrate` and rc277 closed `mint_strand`, so the
#: audit's G4/G5 are already gone; rc281 closes G6 (amplify + copy_number_of).
#: rc334 (§102 G7, #887): EMPTY — add_plasmid, the last remaining gap, earned its
#: whole-op C peer srmech_genome_add_plasmid, so the enumerated genome wire-glue gap
#: list is now empty. This is the concrete ADR-0003 "genome must exist fully in C"
#: closure: every wire-format composition_of_c op on the genome/plasmid surface has a
#: verified whole-op C entry point. (The make_class One.flat/One.scalar bignum-leaf
#: defers are a SEPARATE surface, not wire-glue; host_glue / dev_tooling remain
#: legitimately projection-specific.)
_KNOWN_GLUE_GAPS: dict = {}

#: DOWN-ONLY ceiling on the known-gap allowlist. 13 -> 11 at rc281 (amplify +
#: copy_number_of earned their C peers); 11 -> 10 at rc284 (§100 G1
#: laplacian.recursive_cut earned srmech_laplacian_recursive_cut — the
#: out-of-core recursive spectral bisection driver); 10 -> 9 at rc321 (§100 G3
#: genome_partition GRAPH op earned srmech_genome_graph_partition — recursive_cut +
#: the exact-integer participation + the antimode DECISION + per-node classify +
#: group assembly, all in C); 9 -> 8 at rc327 (§100 G2 genome_from_graph earned
#: srmech_genome_from_graph — the G3 partition + per-group induced-subgraph relabel +
#: graph_to_kernel -> mint_strand loop + strand assembly, all in C); 8 -> 6 at rc329
#: (§102 G7: the ACTIVE-TELOMERE packer earned srmech_genome_active_telomere — the
#: op⊗operand Hayflick cap pack factored out of the tick, no daughter-minting; and the
#: MINT-PLAN read loop earned srmech_genome_mint_plan — the encode_shape shape decision
#: + the content-address orientation per kernel, the WHOLE assembling loop in C); 6 -> 4 at
#: rc332 (§102 G7: the chromatin CONDENSE/DECONDENSE pair earned srmech_genome_condense /
#: srmech_genome_decondense — the shared label -> chromatin-range find + region resolution ->
#: the cap-splice insert index, and the inverse per-block keep-mask; the cap BYTES were already
#: native, so this lifts the Python-only _chrom_range + region resolution into C); 4 -> 1 at rc333
#: (§102 G7: the GENES FAMILY earned srmech_genome_genes / srmech_genome_genome_genes /
#: srmech_genome_genes_expressed — the per-gene (label, leaves) BOUNDARY-PRESERVING read that
#: srmech_genome_recall FLATTENS and srmech_genome_gene_express_plan returns as SPANS: the in-memory
#: split, the on-disk page-region + split, and the demand-load plan-walk + region-page +
#: gene_express collect, all in C); 1 -> 0 at rc334 (§102 G7: the LAST gap, add_plasmid,
#: earned srmech_genome_add_plasmid — the incremental CONSERVE (merge the section-count
#: accumulator + srmech_genome_conserved_core) + ORGANIZE (page every section off disk,
#: decode + harvest the induced core subgraph, pack it, then MINT the core + FOLD the
#: retained plasmids), so a bare-C host runs one incremental add end-to-end). The
#: enumerated genome wire-glue gap list is now EMPTY. This number may only DECREASE.
#:
#: G1 was the shared dead-end of G2 (genome_from_graph) and G3 (the GRAPH
#: genome_partition): rc284 UNBLOCKED both, rc321 CLOSED G3 with its own C surface
#: (participation + antimode histogram + per-node classify + group assembly on top of
#: recursive_cut), and rc327 CLOSED G2 — it composes G3 PLUS its in-RAM
#: _induced_subgraph relabel, the per-group graph_to_kernel -> mint_strand loop and
#: strand assembly. The §100 G-series parity ladder is fully closed; rc329 + rc332 + rc333 +
#: rc334 worked the §2 G7 leaf-family to close (active_telomere / mint_plan / condense /
#: decondense / genes / genome_genes / genome_genes_expressed / add_plasmid ALL closed —
#: the genome wire-glue surface is fully C-reachable).
CEIL_WIRE_GLUE_GAPS = 0


def _wire_scope(cls):
    """The in-scope ``composition_of_c`` ops: the wire-format surface."""
    return {
        da for da, bucket in cls.items()
        if bucket == "composition_of_c"
        and (any(da.startswith(m + ".") for m in _WIRE_FORMAT_MODULES)
             or da in _WIRE_FORMAT_EXTRA)
    }


def _unaccounted(cls, peers, gaps):
    """In-scope ops that declare NEITHER a whole-op C peer NOR a known gap.

    Factored out so the positive test can drive it with a synthetic op.
    """
    return sorted(_wire_scope(cls) - set(peers) - set(gaps))


def _dispatcher_names(fn):
    """The ``_native`` dispatcher names referenced in a callable's source."""
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    except (OSError, TypeError, SyntaxError):
        return set()
    out = set()
    for node in ast.walk(tree):
        name = node.id if isinstance(node, ast.Name) else (
            node.attr if isinstance(node, ast.Attribute) else None)
        if name and (name.endswith("_c") or name.startswith("has_native_")):
            out.add(name)
    return out


def _srmech_callables(fn):
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    except (OSError, TypeError, SyntaxError):
        return []
    g = getattr(fn, "__globals__", {}) or {}
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name):
            continue
        obj = g.get(node.id)
        if (callable(obj) and not inspect.isclass(obj)
                and (getattr(obj, "__module__", "") or "").startswith("srmech")):
            out.append(obj)
    return out


def _glue_c_symbols(fn, hops=2):
    """The ``srmech_*`` C symbols reachable through an op's DISPATCH glue.

    Walks the op body plus the private helpers it calls (bounded hops — a dispatch
    is never buried deeper than a thin wrapper), collects the ``_native`` dispatcher
    names, and reads each dispatcher's own source for the C symbol it calls.
    """
    from srmech import _native
    names, frontier, seen = set(_dispatcher_names(fn)), [fn], set()
    for _ in range(hops):
        nxt = []
        for f in frontier:
            for h in _srmech_callables(f):
                code = getattr(h, "__code__", None)
                if code is None or id(code) in seen:
                    continue
                seen.add(id(code))
                names |= _dispatcher_names(h)
                nxt.append(h)
        frontier = nxt
    syms = set()
    for dispatcher in names:
        target = getattr(_native, dispatcher, None)
        if target is None:
            continue
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(target)))
        except (OSError, TypeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("srmech_"):
                syms.add(node.attr)
            elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and node.value.startswith("srmech_")):
                syms.add(node.value)
    return syms


def test_every_wire_format_op_is_c_reachable_or_an_acknowledged_gap():
    """THE ratchet: a NEW composition_of_c op on the wire-format surface that has no
    whole-op C peer FAILS here. It must either earn a C entry point (preferred) or be
    added to _KNOWN_GLUE_GAPS — and that list is down-only, so adding to it is a
    deliberate, reviewed act, not a quiet escape hatch."""
    cls = _load_classification()
    missing = _unaccounted(cls, _WHOLE_OP_C_PEER, _KNOWN_GLUE_GAPS)
    assert not missing, (
        "wire-format composition_of_c op(s) declare NEITHER a whole-op C peer NOR an "
        "acknowledged gap — a bare-C host cannot run their glue (ADR-0003 §2/§3):\n  "
        + "\n  ".join(missing)
        + "\n\nGive the op a C entry point and add it to _WHOLE_OP_C_PEER, or (only "
          "with an explicit reason + audit reference) add it to _KNOWN_GLUE_GAPS and "
          "RAISE CEIL_WIRE_GLUE_GAPS — which is a regression, not a fix."
    )


def test_declared_whole_op_c_peers_exist_in_the_header():
    """A declaration is not a proof: every peer named above must really be declared
    in c/include/srmech.h. This is what stops a future rc from silencing the ratchet
    by inventing a symbol name."""
    assert _HEADER.exists(), f"missing C header {_HEADER}"
    header = _HEADER.read_text(encoding="utf-8", errors="replace")
    declared = set(re.findall(r"\bsrmech_[a-z0-9_]+\b", header))
    absent = sorted(f"{op} -> {sym}" for op, sym in _WHOLE_OP_C_PEER.items()
                    if sym not in declared)
    assert not absent, (
        "declared whole-op C peer(s) are NOT in c/include/srmech.h:\n  "
        + "\n  ".join(absent))


def test_declared_whole_op_c_peers_are_actually_dispatched():
    """The other half of the proof: the op must really REACH its declared peer through
    its dispatch glue. A C entry point nobody calls is `c_exists_unbound`, not parity."""
    objs = _live_objects()
    broken = []
    for op, sym in sorted(_WHOLE_OP_C_PEER.items()):
        fn = objs.get(op)
        if fn is None:
            continue                      # not importable in this env — skip, not fail
        if sym not in _glue_c_symbols(fn):
            broken.append(f"{op} declares {sym} but does not dispatch it")
    assert not broken, (
        "declared whole-op C peer(s) are not reachable through the op's glue:\n  "
        + "\n  ".join(broken))


def test_known_glue_gaps_ceiling_is_down_only():
    """DOWN-ONLY, the same shape as the JPL Rule-5 exempt list and CEIL_NUMPY_CARRIER:
    the acknowledged-gap list may only SHRINK. Closing a gap means deleting its entry
    and LOWERING this ceiling."""
    assert len(_KNOWN_GLUE_GAPS) == CEIL_WIRE_GLUE_GAPS, (
        f"known-glue-gap count {len(_KNOWN_GLUE_GAPS)} != ceiling "
        f"{CEIL_WIRE_GLUE_GAPS}.\nThis ratchet is DOWN-ONLY: a new acknowledged gap is "
        f"a REGRESSION (the op should have earned a C peer instead). Landing a C peer "
        f"should LOWER the ceiling.\nGaps:\n  "
        + "\n  ".join(sorted(_KNOWN_GLUE_GAPS)))


def test_known_glue_gaps_are_still_gaps():
    """Keeps the allowlist honest in the other direction: an op that has QUIETLY
    earned a whole-op C peer must be MOVED to _WHOLE_OP_C_PEER (and the ceiling
    lowered), not left sitting here claiming to be broken."""
    overlap = sorted(set(_KNOWN_GLUE_GAPS) & set(_WHOLE_OP_C_PEER))
    assert not overlap, (
        "op(s) are BOTH an acknowledged gap and a declared C peer — delete the gap "
        "entry and lower CEIL_WIRE_GLUE_GAPS:\n  " + "\n  ".join(overlap))


def test_every_acknowledged_gap_is_still_in_scope():
    """A gap entry for an op that no longer exists (renamed / reclassified / removed)
    is dead weight that hides the real count — delete it."""
    cls = _load_classification()
    scope = _wire_scope(cls)
    stale = sorted(set(_KNOWN_GLUE_GAPS) - scope)
    assert not stale, (
        "acknowledged-gap entries are no longer live wire-format composition_of_c ops "
        "(DELETE them and lower CEIL_WIRE_GLUE_GAPS):\n  " + "\n  ".join(stale))


def test_every_acknowledged_gap_documents_a_reason_and_a_reference():
    for op, entry in sorted(_KNOWN_GLUE_GAPS.items()):
        assert isinstance(entry, tuple) and len(entry) == 2, op
        why, ref = entry
        assert why and len(why) > 40, f"{op}: give a real reason, not {why!r}"
        assert ref and "audit" in ref.lower(), f"{op}: cite the audit, got {ref!r}"


# ── the POSITIVE test: prove the ratchet actually catches a regression ───────

def test_ratchet_catches_a_new_un_c_reachable_wire_op():
    """A synthetic NEW composition_of_c genome op with Python-only glue, on neither
    list, must be FLAGGED. Without this test the ratchet could silently degrade to a
    no-op and nobody would know."""
    cls = dict(_load_classification())
    cls["srmech.biology.genome.sneaky_new_op"] = "composition_of_c"
    missing = _unaccounted(cls, _WHOLE_OP_C_PEER, _KNOWN_GLUE_GAPS)
    assert "srmech.biology.genome.sneaky_new_op" in missing, (
        "the wire-format ratchet did NOT flag a new un-C-reachable genome op — the "
        "check has degraded to a no-op")
    # …and a NON-wire op (pure carrier math) is correctly left alone.
    cls["srmech.math.laplacian.mat_norm"] = "composition_of_c"
    assert "srmech.math.laplacian.mat_norm" not in _unaccounted(
        cls, _WHOLE_OP_C_PEER, _KNOWN_GLUE_GAPS), (
        "the ratchet over-reached into pure carrier math — scope creep")


def test_ratchet_catches_a_peer_declared_with_a_nonexistent_symbol():
    """The escape hatch a future rc would reach for first: declare a plausible-looking
    C symbol that does not exist. The header check must catch it."""
    header = _HEADER.read_text(encoding="utf-8", errors="replace")
    declared = set(re.findall(r"\bsrmech_[a-z0-9_]+\b", header))
    assert "srmech_genome_totally_invented_peer" not in declared
    fake = dict(_WHOLE_OP_C_PEER)
    fake["srmech.biology.genome.sneaky_new_op"] = "srmech_genome_totally_invented_peer"
    absent = [op for op, sym in fake.items() if sym not in declared]
    assert absent == ["srmech.biology.genome.sneaky_new_op"]


def test_ratchet_catches_a_peer_that_is_declared_but_not_dispatched():
    """The subtler escape hatch: point a Python-only op at a REAL C symbol it never
    calls. The dispatch check must catch that too — this is precisely the rc273 error
    (a real C surface nearby, no path from the op to it)."""
    objs = _live_objects()
    gap_op = "srmech.biology.genome.mint_plan"        # a known Python-only-glue op
    fn = objs.get(gap_op)
    if fn is None:
        pytest.skip("srmech.biology.genome.mint_plan not importable in this env")
    # srmech_genome_amplify is real (rc281) but mint_plan has no path to it.
    assert "srmech_genome_amplify" not in _glue_c_symbols(fn), (
        "expected mint_plan to have NO path to the amplify peer — if this changed, "
        "the fixture op for this test needs updating")
