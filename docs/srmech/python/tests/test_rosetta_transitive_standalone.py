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
# composition_of_c, so this ratchet now walks them for hidden non-ready leaves;
# kept identical across all four walk sites).
_ROOTS = (
    "srmech.amsc", "srmech.qm", "srmech.signal_processing",
    "srmech.bus", "srmech.dsl",
    "srmech.mcp", "srmech.cli", "srmech.llm",
    "srmech.spectral", "srmech.rbs_lm",
    "srmech.introspect", "srmech.profile_loader",
)

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
_WIRE_FORMAT_MODULES = ("srmech.amsc.genome", "srmech.amsc.plasmid")

#: Individually-named in-scope ops that live OUTSIDE those modules. ``recursive_cut``
#: is the out-of-core recursive spectral bisection driver: it manages on-disk TOMES,
#: so it is a wire-format orchestrator even though it sits in ``laplacian``. Its
#: in-memory siblings there (``mat_norm``, ``normalized_cut_bisect``, …) are pure
#: carrier math and stay out of scope.
_WIRE_FORMAT_EXTRA = frozenset({"srmech.amsc.laplacian.recursive_cut"})

# ── (a) the VERIFIED whole-op C peers ────────────────────────────────────────
#: ``defined_at`` -> the single C entry point that performs the WHOLE operation.
#: Both halves of this claim are machine-checked below: the symbol must be declared
#: in c/include/srmech.h, and it must actually be reachable through the op's dispatch
#: glue. A declaration alone proves nothing — that was the rc273 failure mode.
_WHOLE_OP_C_PEER = {
    "srmech.amsc.genome.accessible":       "srmech_genome_chromatin_access",
    "srmech.amsc.genome.amplify":          "srmech_genome_amplify",       # rc281 (G6)
    "srmech.amsc.genome.centromere_of":    "srmech_genome_centromere_of",
    "srmech.amsc.genome.chromatin_of":     "srmech_genome_chromatin_of",
    "srmech.amsc.genome.chromosome":       "srmech_genome_chromosome",
    "srmech.amsc.genome.copy_number_of":   "srmech_genome_copy_number",   # rc281 (G6)
    "srmech.amsc.genome.genome":           "srmech_genome_mint",
    # `mint` is a pure delegation to `genome` (its whole body is `return genome(...)`),
    # so it inherits that op's entry point rather than owning a second one.
    "srmech.amsc.genome.mint":             "srmech_genome_mint",
    "srmech.amsc.genome.partition":        "srmech_genome_partition",
    "srmech.amsc.genome.plasmid":          "srmech_genome_genome",
    # `quad_turn` is a pure delegation to the reversible Klein-4 bind primitive — the
    # whole op IS that one C call, so it is trivially C-runnable.
    "srmech.amsc.genome.quad_turn":        "srmech_klein4_bind",
    "srmech.amsc.genome.recall":           "srmech_genome_recall",
    "srmech.amsc.laplacian.recursive_cut":
        "srmech_laplacian_recursive_cut",                                 # rc284
    "srmech.amsc.plasmid.genome_integrate_plasmids":
        "srmech_genome_integrate_plasmids",                               # rc279
    "srmech.amsc.plasmid.plasmid_extract": "srmech_genome_plasmid_extract",
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
_KNOWN_GLUE_GAPS = {
    "srmech.amsc.genome.active_telomere": (
        "a single cap PACKER with no exposed entry point; the pack logic exists inside "
        "srmech_genome_telomere_tick (which mints daughter active caps) but is not "
        "callable on its own",
        "c_host_parity_audit_rc273 §2 G7",
    ),
    "srmech.amsc.genome.condense": (
        "GAP-lite: the cap BYTES are native (srmech_genome_chromatin) but the "
        "_chrom_range(label) lookup, region resolution and splice around them are "
        "Python-only — reaching a C primitive is not a whole-op entry",
        "c_host_parity_audit_rc273 §2 G7",
    ),
    "srmech.amsc.genome.decondense": (
        "the whole-strand form is a near-trivial 0x48 cap-filter, but the label-scoped "
        "form needs the same Python-only range-find as condense",
        "c_host_parity_audit_rc273 §2 G7",
    ),
    "srmech.amsc.genome.genes": (
        "an in-memory recall-variant that KEEPS per-gene boundaries; "
        "srmech_genome_recall flattens them and srmech_genome_gene_express_plan returns "
        "spans, so neither returns the (label, leaves) split this op does",
        "c_host_parity_audit_rc273 §2 G7",
    ),
    "srmech.amsc.genome.genome_genes": (
        "the on-disk sibling of `genes` — catalog read + region page, then the same "
        "missing per-gene split",
        "c_host_parity_audit_rc273 §2 G7 (genes family)",
    ),
    "srmech.amsc.genome.genome_genes_expressed": (
        "on-disk gene-express ORCHESTRATION: the per-gene decision has a C peer "
        "(srmech_genome_gene_express_plan) but the plan-walk / region-page / collect "
        "loop around it does not",
        "c_host_parity_audit_rc273 §2 G7 (genes family)",
    ),
    "srmech.amsc.genome.genome_from_graph": (
        "the §100 GAP-2 compound flagship: needs recursive_cut + genome_partition plus "
        "its own _induced_subgraph relabel, per-group graph_to_kernel -> mint_strand "
        "loop and strand assembly",
        "c_host_parity_audit_rc273 §2 G2",
    ),
    "srmech.amsc.genome.genome_partition": (
        "the GRAPH partition (NOT the strand-recovery op that shares the C name "
        "srmech_genome_partition): composes recursive_cut + an exact-integer "
        "participation + antimode + per-node classify, all Python",
        "c_host_parity_audit_rc273 §2 G3",
    ),
    "srmech.amsc.genome.mint_plan": (
        "a pure encode_shape-loop READ (it builds nothing); the per-step primitive is "
        "native but the loop that assembles the plan is not",
        "c_host_parity_audit_rc273 §2 G7",
    ),
    "srmech.amsc.genome.relative_writhe": (
        "rc317 (#1308): the Fuller Second-Theorem relative writhe — a geometry READ "
        "whose per-step primitives (Class-N sqrt / pi-cascade / best_rational) are "
        "C-backed, but whose Fuller-integrand assembly + dual-precision best_rational "
        "ANCHORING LOOP is Python-only, so it is not a whole-op C entry a bare-C host "
        "can call. Peer to discrete_writhe (which owns srmech_genome_discrete_writhe); "
        "a srmech_genome_relative_writhe whole-op peer is the eventual close",
        "c_host_parity_audit rc317 #1308 (Fuller Second-Theorem exact-rational "
        "relative writhe — composition-only ship; whole-op C peer pending)",
    ),
    "srmech.amsc.plasmid.add_plasmid": (
        "an ORCHESTRATOR over three C peers (plasmid_extract / conserved_core / "
        "integrate_plasmids) with no whole-op entry of its own — ADR-0003 §3 names "
        "orchestrators explicitly",
        "c_host_parity_audit_rc273 §2 G2 (plasmid pipeline)",
    ),
}

#: DOWN-ONLY ceiling on the known-gap allowlist. 13 -> 11 at rc281 (amplify +
#: copy_number_of earned their C peers); 11 -> 10 at rc284 (§100 G1
#: laplacian.recursive_cut earned srmech_laplacian_recursive_cut — the
#: out-of-core recursive spectral bisection driver). This number may only
#: DECREASE.
#:
#: G1 was the shared dead-end of G2 (genome_from_graph) and G3 (the GRAPH
#: genome_partition), so rc284 UNBLOCKS both — but unblocking is not closing:
#: each still needs C surfaces of its own that recursive_cut does not supply.
#: G3 additionally needs exact-integer participation + the antimode histogram +
#: per-node classify; G2 needs all of G3 plus its in-RAM _induced_subgraph
#: relabel, the per-group graph_to_kernel -> mint_strand loop and strand
#: assembly. They are separate rcs, not free riders on this one.
#:
#: ⚠️ rc317 (#1308) RAISED this 10 -> 11 for genome.relative_writhe (the Fuller
#: Second-Theorem relative writhe), shipped as composition_of_c per the op's
#: spec (its Class-N primitives sqrt / pi-cascade / best_rational are C-backed,
#: but the Fuller-integrand + dual-precision anchoring LOOP is Python glue). By
#: this ratchet's own policy that is a REGRESSION, not a fix — flagged for review:
#: the clean close is a whole-op srmech_genome_relative_writhe C peer (then move
#: it to _WHOLE_OP_C_PEER, reclassify c_dispatched, and lower this back to 10).
CEIL_WIRE_GLUE_GAPS = 11


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
    from srmech.amsc import _native
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
    cls["srmech.amsc.genome.sneaky_new_op"] = "composition_of_c"
    missing = _unaccounted(cls, _WHOLE_OP_C_PEER, _KNOWN_GLUE_GAPS)
    assert "srmech.amsc.genome.sneaky_new_op" in missing, (
        "the wire-format ratchet did NOT flag a new un-C-reachable genome op — the "
        "check has degraded to a no-op")
    # …and a NON-wire op (pure carrier math) is correctly left alone.
    cls["srmech.amsc.laplacian.mat_norm"] = "composition_of_c"
    assert "srmech.amsc.laplacian.mat_norm" not in _unaccounted(
        cls, _WHOLE_OP_C_PEER, _KNOWN_GLUE_GAPS), (
        "the ratchet over-reached into pure carrier math — scope creep")


def test_ratchet_catches_a_peer_declared_with_a_nonexistent_symbol():
    """The escape hatch a future rc would reach for first: declare a plausible-looking
    C symbol that does not exist. The header check must catch it."""
    header = _HEADER.read_text(encoding="utf-8", errors="replace")
    declared = set(re.findall(r"\bsrmech_[a-z0-9_]+\b", header))
    assert "srmech_genome_totally_invented_peer" not in declared
    fake = dict(_WHOLE_OP_C_PEER)
    fake["srmech.amsc.genome.sneaky_new_op"] = "srmech_genome_totally_invented_peer"
    absent = [op for op, sym in fake.items() if sym not in declared]
    assert absent == ["srmech.amsc.genome.sneaky_new_op"]


def test_ratchet_catches_a_peer_that_is_declared_but_not_dispatched():
    """The subtler escape hatch: point a Python-only op at a REAL C symbol it never
    calls. The dispatch check must catch that too — this is precisely the rc273 error
    (a real C surface nearby, no path from the op to it)."""
    objs = _live_objects()
    gap_op = "srmech.amsc.genome.mint_plan"        # a known Python-only-glue op
    fn = objs.get(gap_op)
    if fn is None:
        pytest.skip("srmech.amsc.genome.mint_plan not importable in this env")
    # srmech_genome_amplify is real (rc281) but mint_plan has no path to it.
    assert "srmech_genome_amplify" not in _glue_c_symbols(fn), (
        "expected mint_plan to have NO path to the amplify peer — if this changed, "
        "the fixture op for this test needs updating")
