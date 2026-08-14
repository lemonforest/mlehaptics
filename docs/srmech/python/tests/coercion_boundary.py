"""tests/coercion_boundary.py — the SINGLE derivation of what a registered op's
COERCION BOUNDARY actually accepts and produces (rc363; ADR-0012 §3.1 C2/C3).

Why this module exists
----------------------
Two introspect properties ADR-0012 §3.1 states as clauses — **C2 (typed
honestly)** and **C3 (constructible)** — are both questions about *the carriers
an op really touches*. Until rc363 the only machine-readable answer in the tree
was the **declared type string** (``ToolEntry.parameters[].type`` /
``returns.type``), and both ``carrier_schema()``'s ops back-index and the rc205
drift ratchet derive from exactly that field. ADR-0012 §2 states the resulting
guarantee precisely: *"``describe()`` and ``carrier_schema()`` report the
carriers the op surface DECLARES, not the carriers it USES."*

rc362 is the measured exhibit. Three ``srmech.music`` ops accepted ``Qalg``,
said so in their coercion ``raise`` text and in their human prose, and declared
``partials`` as a bare ``Sequence``. The rc205 ratchet — whose stated job is to
force a newly-surfaced carrier into the registry — **passed**, because the token
``"Qalg"`` occurred in 0 of 525 declared type strings. A gate that cannot fire on
the one case it exists for is a false green
(``[[feedback_false_green_comments_and_dead_instrumentation_seams]]``).

So this module derives the same question from a **second, independent channel**:
the op's own source. It reads what the callable BRANCHES ON, not what a
hand-written string says. The two channels can then be compared, which is the
whole point — a single channel cannot disagree with itself.

What a "coercion boundary" is, exactly
--------------------------------------
Start at the registered op's own function, with its declared parameters as the
TRACKED value set. Propagate tracking through, and only through, four dataflow
forms that keep the identity of a caller-supplied value intact:

1. ``y = x``               — a plain rebind of a tracked name;
2. ``for y in x``          — an ELEMENT of a tracked sequence (this is the form
                             the ``partials`` spectrum rides: the carrier is the
                             element, never the container);
3. ``for i, y in enumerate(x)`` — the same, with an index;
4. ``helper(x)``           — a call to a **module-level function**, in this
                             module or imported from another srmech module,
                             binding the tracked argument to that helper's
                             parameter name, and recursing.

Inside every reached function, an ``isinstance(<tracked>, C)`` guard is read as
a statement about the boundary:

* the guard is **ACCEPTING** when passing it does not raise —
  ``if isinstance(v, Qalg): return v`` (accepts), or the negated invariant form
  ``if not isinstance(v, Mat): raise`` (also accepts: the only way past is to BE
  one);
* the guard is **REFUSING** when passing it raises —
  ``if isinstance(v, float): raise TypeError(...)`` (``srmech.music._spectra``
  refuses floats on purpose, and that refusal is a capability statement in its
  own right).

**The tracking restriction is load-bearing, not an optimisation.** Without it,
attributing every ``isinstance`` in the defining module to every op in it
mis-reads internal invariant checks on RECONSTRUCTED values as boundary
statements. Measured at rc363: module-scoped attribution flagged
``coupling.fold_spectrum`` as accepting a ``Poly``, when the guarded ``R`` is
rebuilt from recovered HDC tokens and has no dataflow path from any parameter.
Dataflow tracking removes that row and keeps every genuine one.

What it deliberately does NOT do
--------------------------------
* **The call graph follows IMPORTED helpers, but only functions.** A coercion
  helper imported from a sibling module IS followed (measured at rc363:
  ``elliptic_zeilberger`` and ``elliptic_wz_certificate`` both do
  ``from .elliptic_recurrence import _coerce_ratio``, and a module-local walk
  loses both). Methods, ``functools`` wrappers and C callables are not followed.
* **No type inference.** Only literal ``isinstance`` targets and literal
  constructor calls are read. An op that dispatches on ``type(x) is C`` or on
  duck-typing is not seen.
* **No claim of exhaustiveness.** :attr:`Boundary.accepted` is a LOWER BOUND on
  what an op accepts. Every gate built on it must therefore assert a
  "everything found must be declared / registered" direction and never the
  converse.

Pure stdlib (``ast`` / ``inspect`` / ``importlib``); numpy-free; no ``abs()``.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Boundary",
    "NON_CARRIER_CLASSES",
    "boundaries",
    "boundary_for",
    "defining_module",
    "is_operand_carrier_candidate",
    "is_srmech_class",
    "resolve_class",
    "resolve_class_name",
]

#: srmech classes that appear on an op boundary and are NOT operand carriers —
#: the SINGLE source shared by the rc205 declared-type ratchet
#: (``tests/test_carrier_schema_rc205.py``) and the rc363 use-derivation gate
#: (``tests/test_carrier_use_derivation_rc363.py``). Two gates asking the same
#: question from opposite channels must not be able to disagree about which
#: names are exempt — forking this set is the defect the rc361 single-decoder
#: instrument exists to stop, in the operand direction.
#:
#: Every entry is an infrastructure / handle type: a thing an op takes or hands
#: back to carry a REFERENCE or a CONTEXT, never a mathematical operand. A
#: carrier belongs in ``carrier_schema._CARRIERS`` instead — the question to ask
#: is "does a caller do MATHS with it?".
NON_CARRIER_CLASSES = frozenset({
    "ChainSpec",         # compose chain-spec IR (orchestration, not operand)
    "Endpoint",          # bus endpoint handle
    "MPRRecord",         # provenance record envelope
    "RecoverableFold",   # coupling pair-carrier handle (in-process only)
    "Run",               # introspect run record
    "SearchResult",      # introspect search result envelope (rc411)
    "SpectralHandle",    # by-reference spectral handle (rc16 envelope)
    # rc411 (`#T1086`): two introspect types, both records rather than operands.
    # `ToolSchema` is the registry VIEW returned by the newly-registered
    # `get_tool_schema`; `SearchResult` is the ranked-record envelope returned
    # by `search` (a `tuple` subclass carrying the ADR-0011 corpus witness).
    # Nobody does maths with either — they carry rows and a provenance digest,
    # which is the `Run` shape (an introspect record), not the `Mat` shape.
    #
    # Note it took BOTH gates to surface them, which is the argument for this
    # set being single-sourced: the rc205 ratchet reads the DECLARED ToolEntry
    # return type and saw only `ToolSchema`; the rc363 use-derivation gate reads
    # the SOURCE annotation and saw only `SearchResult`. Either alone would have
    # left the other unexempted and the tree red.
    "ToolSchema",        # tool-registry view (introspection, not operand)
    # rc419 (`#T1110`): the two signal_processing dispatcher types, both
    # in-process CONTEXT/REFERENCE objects that fail the "does a caller do
    # MATHS with it?" question outright.
    #
    # `CascadeContext` is a position on a per-thread stack — substrate label,
    # depth, D, closed. Its whole meaning is WHERE it sits while a with-block
    # is open; it carries no value a caller computes on.
    #
    # `OperationEntry` is the path-registry record: an op name, a literature
    # citation, an A-N class tuple, and the two IMPLEMENTATION CALLABLES. A
    # function is the clearest possible non-operand — which is also why
    # `path_registry.lookup` is `mcp_callable=False`; the same fact drives
    # both, from the two different channels.
    "CascadeContext",    # per-thread dispatch-routing scope (rc419)
    "OperationEntry",    # path-registry record holding live callables (rc419)
})

# Dunder methods are a class's own protocol, not an op's coercion boundary:
# ``__eq__(self, other)`` guarding ``isinstance(other, Self)`` says nothing about
# what any op accepts. They are never module-level functions, so the walk below
# cannot reach them — this constant records the reasoning for the reader.
_DUNDER_NOTE = "dunder guards are unreachable: only module-level defs are walked"


def defining_module(tool_name: str) -> Optional[str]:
    """The module a registered op is **defined in**, which is not always the
    module its dotted registry name points at.

    ``srmech.music.spectrum_tier`` is registered under ``srmech.music`` and
    defined in ``srmech.music._spectra``; reading the source of the former gives
    ``__init__.py``, which contains no coercion at all. Resolving through
    ``__module__`` is what makes a re-exported op analysable — measured at rc363:
    scoping by registry name instead loses the entire ``srmech.music`` boundary.
    """
    mod, _, attr = tool_name.rpartition(".")
    if not mod or not attr:
        return None
    try:
        obj = getattr(importlib.import_module(mod), attr, None)
    except Exception:  # noqa: BLE001 — an unimportable module is simply not analysable
        return None
    dm = getattr(obj, "__module__", None)
    return dm if isinstance(dm, str) and dm.startswith("srmech") else None


def is_srmech_class(obj: Any) -> bool:
    """True for a class DEFINED in this package (``__module__`` under
    ``srmech.``). ``Fraction`` / ``Path`` / ``Sequence`` are therefore excluded
    without needing to be named."""
    return (isinstance(obj, type)
            and str(getattr(obj, "__module__", "")).startswith("srmech"))


def resolve_class(node: ast.AST,
                  module_globals: Dict[str, Any]) -> Optional[Tuple[str, type]]:
    """``(name, class)`` for the srmech class an AST expression names, resolved
    against the defining module's live globals — ``Qalg`` (a ``Name``) or
    ``ellbase.Theta`` (an ``Attribute``). ``None`` when it does not resolve to a
    srmech class.

    Resolving against the real namespace rather than against a token list is
    what keeps a local variable that happens to be spelled like a class from
    being read as one — and it hands the caller the CLASS OBJECT, so
    :func:`is_operand_carrier_candidate` can ask structural questions
    (is it an exception? is it private?) instead of pattern-matching names."""
    if isinstance(node, ast.Name):
        obj = module_globals.get(node.id)
        return (node.id, obj) if is_srmech_class(obj) else None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        base = module_globals.get(node.value.id)
        obj = getattr(base, node.attr, None) if base is not None else None
        return (node.attr, obj) if is_srmech_class(obj) else None
    return None


def resolve_class_name(node: ast.AST, module_globals: Dict[str, Any]) -> Optional[str]:
    """:func:`resolve_class`, name only."""
    hit = resolve_class(node, module_globals)
    return hit[0] if hit is not None else None


def is_operand_carrier_candidate(name: str, cls: type) -> bool:
    """Is this srmech class a candidate OPERAND CARRIER — the population
    ``carrier_schema`` is scoped to?

    Two structural exclusions, each a rule rather than an allowlist entry, so a
    future class of the same kind is excluded without anyone editing a list:

    * **Exceptions.** A ``BaseException`` subclass is a control-flow signal, not
      an operand. ``GenomeBoundingError`` / ``ChainSpecError`` /
      ``MPRValidationError`` / ``SectionCountsCancelled`` /
      ``BioTotpFormatError`` / ``BioTotpDecryptError`` are all surfaced by the
      walk and all excluded here — 6 of the 22 unregistered classes measured at
      rc363.
    * **Private names.** A leading underscore is the package's own statement
      that the name is not public surface. Measured at rc363 these are all lazy
      import aliases of a REGISTERED carrier (``_HV`` / ``_Mat`` / ``_Vec`` /
      ``_Q``) or an internal handle (``_CoocTopkNative`` / ``_PublishHandle``) —
      6 more.

    Everything else is a candidate and must either hold a ``carrier_schema`` row
    or be justified on the gate's non-carrier allowlist."""
    if name.startswith("_"):
        return False
    try:
        if issubclass(cls, BaseException):
            return False
    except TypeError:  # pragma: no cover — cls is always a class here
        return False
    return True


class Boundary:
    """What one registered op's coercion boundary says, derived from source.

    ``accepted`` / ``refused`` — srmech class names an ``isinstance`` guard on a
    tracked (parameter-derived) value admits / rejects.
    ``raise_named``          — srmech class names appearing in the literal text
                               of a ``raise`` inside the reached functions.
    ``constructed``          — srmech class names the op's OWN body instantiates
                               (the produce-side channel; helpers are not walked
                               for this, so it stays tight).
    ``annotated``            — srmech class names in the runtime signature
                               annotations (params + return).
    ``reached``              — the functions the walk entered, for reporting.
    """

    __slots__ = ("name", "module", "accepted", "refused", "raise_named",
                 "constructed", "annotated", "reached", "classes")

    def __init__(self, name: str, module: Optional[str]) -> None:
        self.name = name
        self.module = module
        self.accepted: Set[str] = set()
        self.refused: Set[str] = set()
        self.raise_named: Set[str] = set()
        self.constructed: Set[str] = set()
        self.annotated: Set[str] = set()
        self.reached: Set[str] = set()
        #: every resolved class name -> the CLASS OBJECT, so a caller can ask
        #: structural questions (see :func:`is_operand_carrier_candidate`)
        #: rather than pattern-match the spelling.
        self.classes: Dict[str, type] = {}

    @property
    def surfaced(self) -> Set[str]:
        """Every srmech class this op is measured to CONSUME or PRODUCE — the
        C3 question. Refusals are excluded on purpose: refusing a ``float`` is
        not surfacing one."""
        return self.accepted | self.constructed | self.annotated

    def __repr__(self) -> str:  # pragma: no cover — diagnostics only
        return (f"Boundary({self.name!r}, accepted={sorted(self.accepted)}, "
                f"constructed={sorted(self.constructed)}, "
                f"annotated={sorted(self.annotated)})")


# ── AST plumbing ─────────────────────────────────────────────────────────────

_module_cache: Dict[str, Tuple[Optional[Dict[str, ast.FunctionDef]], Dict[str, Any]]] = {}


def _module_functions(mod_name: str):
    """``{function name: FunctionDef}`` for the module-level defs of ``mod_name``,
    plus the module's live globals. Cached — 525 ops share ~92 modules."""
    if mod_name in _module_cache:
        return _module_cache[mod_name]
    fns: Optional[Dict[str, ast.FunctionDef]] = None
    glb: Dict[str, Any] = {}
    try:
        mod = importlib.import_module(mod_name)
        glb = dict(vars(mod))
        tree = ast.parse(inspect.getsource(mod))
        fns = {n.name: n for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    except Exception:  # noqa: BLE001 — a C-only / source-less module is not analysable
        fns = None
    _module_cache[mod_name] = (fns, glb)
    return fns, glb


def _param_names(fn: ast.FunctionDef) -> List[str]:
    a = fn.args
    return ([p.arg for p in a.posonlyargs] + [p.arg for p in a.args]
            + ([a.vararg.arg] if a.vararg else [])
            + [p.arg for p in a.kwonlyargs])


def _propagate(fn: ast.AST, tracked: Set[str]) -> Set[str]:
    """Grow ``tracked`` over the four identity-preserving dataflow forms until
    it stops growing. Fixed-point rather than single-pass, because a rebind can
    precede or follow the loop that feeds it."""
    grown = set(tracked)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Name) and node.value.id in grown:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name) and tgt.id not in grown:
                            grown.add(tgt.id)
                            changed = True
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                src = node.iter
                # `for y in enumerate(x)` / `for i, y in enumerate(x)`
                if (isinstance(src, ast.Call) and isinstance(src.func, ast.Name)
                        and src.func.id in ("enumerate", "reversed", "sorted", "list", "tuple")
                        and src.args):
                    src = src.args[0]
                if isinstance(src, ast.Name) and src.id in grown:
                    tgt = node.target
                    names = (tgt.elts if isinstance(tgt, (ast.Tuple, ast.List))
                             else [tgt])
                    for nm in names:
                        if isinstance(nm, ast.Name) and nm.id not in grown:
                            grown.add(nm.id)
                            changed = True
    return grown


def _guards(fn: ast.AST, tracked: Set[str], glb: Dict[str, Any],
            out: Boundary) -> None:
    """Record every ``isinstance(<tracked>, C)`` guard in ``fn`` as accepting or
    refusing. A guard whose ``if`` body raises is a refusal; the negated form
    ``if not isinstance(...): raise`` is an ACCEPTANCE (the invariant shape)."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test, negated = node.test, False
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            test, negated = test.operand, True
        body_raises = any(
            isinstance(s, ast.Raise)
            for s in ast.walk(ast.Module(body=list(node.body), type_ignores=[])))
        for call in ast.walk(test):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "isinstance" and len(call.args) == 2):
                continue
            subj = call.args[0]
            if isinstance(subj, ast.Subscript) and isinstance(subj.value, ast.Name):
                subj = subj.value
            if not (isinstance(subj, ast.Name) and subj.id in tracked):
                continue
            tgt = call.args[1]
            items = tgt.elts if isinstance(tgt, (ast.Tuple, ast.List)) else [tgt]
            for item in items:
                hit = resolve_class(item, glb)
                if hit is None:
                    continue
                cls, obj = hit
                out.classes[cls] = obj
                accepts = (negated and body_raises) or (not negated and not body_raises)
                (out.accepted if accepts else out.refused).add(cls)


def _raise_strings(fn: ast.AST) -> List[str]:
    texts: List[str] = []
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Raise) and node.exc is not None):
            continue
        for sub in ast.walk(node.exc):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                texts.append(sub.value)
            elif isinstance(sub, ast.JoinedStr):
                for val in sub.values:
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        texts.append(val.value)
    return texts


#: Hard ceiling on call-graph depth. Not a correctness device — the ``seen``
#: memo already terminates every cycle — but a bound on how far a boundary claim
#: may travel from the op that is being described. Measured at rc363: the
#: deepest genuine coercion chain in the tree is 3 (op -> _read -> _coerce_ratio).
_MAX_DEPTH = 6


def _walk(fn_name: str, tracked: Set[str], mod_name: str,
          out: Boundary, seen: Set[Tuple[str, ...]], depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        return
    fns, glb = _module_functions(mod_name)
    if not fns:
        return
    fn = fns.get(fn_name)
    if fn is None:
        return
    key = (mod_name, fn_name) + tuple(sorted(tracked))
    if key in seen:
        return
    seen.add(key)
    out.reached.add(f"{mod_name}.{fn_name}")

    grown = _propagate(fn, tracked)
    _guards(fn, grown, glb, out)
    for text in _raise_strings(fn):
        for tok in _identifiers(text):
            if is_srmech_class(glb.get(tok)):
                out.raise_named.add(tok)
                out.classes[tok] = glb[tok]

    # follow helper calls, binding tracked args to the callee's param names
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        callee_name, callee_mod = node.func.id, mod_name
        callee = fns.get(callee_name)
        if callee is None:
            # an IMPORTED module-level function: resolve it in the live globals
            # and continue the walk in the module that DEFINES it.
            obj = glb.get(node.func.id)
            defmod = getattr(obj, "__module__", None)
            objname = getattr(obj, "__name__", None)
            if not (inspect.isfunction(obj) and isinstance(defmod, str)
                    and defmod.startswith("srmech") and isinstance(objname, str)):
                continue
            other_fns, _ = _module_functions(defmod)
            if not other_fns or objname not in other_fns:
                continue
            callee, callee_name, callee_mod = other_fns[objname], objname, defmod
        names = _param_names(callee)
        passed: Set[str] = set()
        for i, arg in enumerate(node.args):
            if isinstance(arg, ast.Name) and arg.id in grown and i < len(names):
                passed.add(names[i])
        for kw in node.keywords:
            if (kw.arg and isinstance(kw.value, ast.Name)
                    and kw.value.id in grown and kw.arg in names):
                passed.add(kw.arg)
        if passed:
            _walk(callee_name, passed, callee_mod, out, seen, depth + 1)


_IDENT_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def _identifiers(text: str) -> Set[str]:
    """Identifier-shaped runs in free text. Hand-rolled rather than ``re`` so the
    boundary between "a word in prose" and "a Python name" is visible here."""
    out: Set[str] = set()
    cur: List[str] = []
    for ch in text:
        if ch in _IDENT_CHARS:
            cur.append(ch)
        else:
            if cur:
                out.add("".join(cur))
            cur = []
    if cur:
        out.add("".join(cur))
    return out


def _constructed(fn: ast.FunctionDef, glb: Dict[str, Any],
                 out: "Boundary") -> Set[str]:
    """srmech classes the op's own body instantiates **on a return path** — the
    produce-side channel.

    Two restrictions, both measured rather than assumed:

    * **Only inside a ``return`` expression.** Instantiating a class is not
      producing one; a scratch object built mid-body never reaches the caller.
    * **Never an attribute-call RECEIVER.** ``return ModularFormsRing().represent(...)``
      constructs a transient ENGINE and returns a ``dict`` of exact-ℚ
      coefficients. Measured at rc363: without this restriction the derivation
      reported ``ModularFormsRing`` and ``QuasiModularFormsRing`` as produced
      carriers, which would have forced two engine classes into the operand
      registry — a registry row nothing consumes is the vacuous-field defect
      ADR-0012 §6.3 declines by name.

    ``return _spectrum_to_result(CarrierSpectrum(element))`` passes both: the
    construction is an ARGUMENT on the return path, and the built object is what
    the returned dict carries under ``'spectrum'``. That is the shape ADR-0012
    §3.1 C3 names.

    A classmethod factory (``return EllRatio.monomial(r)``) is NOT seen — the
    call target resolves to a method, not a class. Under-reporting, which is the
    safe direction for a subset assertion.
    """
    found: Set[str] = set()
    for stmt in ast.walk(fn):
        if not (isinstance(stmt, ast.Return) and stmt.value is not None):
            continue
        receivers = {id(n.func.value) for n in ast.walk(stmt.value)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        for node in ast.walk(stmt.value):
            if not isinstance(node, ast.Call) or id(node) in receivers:
                continue
            hit = resolve_class(node.func, glb)
            if hit is not None:
                found.add(hit[0])
                out.classes[hit[0]] = hit[1]
    return found


def _annotation_classes(obj: Any, glb: Dict[str, Any],
                        out: "Boundary") -> Set[str]:
    """srmech classes named in the runtime signature annotations. String
    annotations (``from __future__ import annotations`` is tree-wide) are read
    textually and resolved against the defining module's globals."""
    found: Set[str] = set()
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):  # pragma: no cover — builtins / C callables
        return found
    blobs: List[str] = []
    for p in sig.parameters.values():
        if p.annotation is not inspect.Parameter.empty:
            blobs.append(str(p.annotation))
    if sig.return_annotation is not inspect.Signature.empty:
        blobs.append(str(sig.return_annotation))
    for blob in blobs:
        for tok in _identifiers(blob):
            if is_srmech_class(glb.get(tok)):
                found.add(tok)
                out.classes[tok] = glb[tok]
    return found


def boundary_for(tool_name: str) -> Boundary:
    """Derive :class:`Boundary` for one registered op name. Always returns a
    Boundary — an unanalysable op (no source, C-only, a functools wrapper)
    yields an EMPTY one, and every gate reports how many it could analyse so an
    empty selection can never masquerade as a clean pass.

    ⚠️ **The registry LEAF is not always the DEF name** (rc424, `#T1113`). This
    function resolved the MODULE through the live object's ``__module__`` (see
    :func:`defining_module`, whose docstring calls that "what makes a
    re-exported op analysable") but then looked the FUNCTION up by the registry
    leaf. That asymmetry was invisible for as long as every re-export happened
    to preserve the name: ``srmech.music.spectrum_tier`` is defined in
    ``_spectra`` as ``def spectrum_tier``, so leaf and def agreed by luck.

    ``srmech.signal_processing.music_doa`` is the first op where the re-export
    RENAMES — it is ``closed_form_ops.music_doa.op``, promoted to the package
    surface under a name that disambiguates it from the ``srmech.music``
    package. Its module resolved fine and its function did not, so the walk
    returned an EMPTY Boundary and ``test_the_derivation_selects_a_real_
    population`` went red on 1 of 612 — correctly, because a blind op makes the
    strict-zero gate downstream uninformative.

    So the function is now resolved the same way the module already was, and
    the same way :func:`_walk` has ALWAYS resolved an imported callee a few
    lines below (``__module__`` + ``__name__`` off the live object). This is
    not a Path-A special case and names no protocol: it fixes the general class
    "registered under a different leaf than it is defined as", which covers
    every re-export, promotion and alias — including the 38 remaining
    ``closed_form_ops`` modules queued by `#T1112`, all of which define
    ``def op`` and would otherwise each land blind here.
    """
    mod = defining_module(tool_name)
    out = Boundary(tool_name, mod)
    if mod is None:
        return out
    fns, glb = _module_functions(mod)
    if not fns:
        return out
    pkg, _, root = tool_name.rpartition(".")
    try:
        obj = getattr(importlib.import_module(pkg), root, None)
    except Exception:  # noqa: BLE001 — an unimportable module is not analysable
        obj = None
    fn_name, fn = root, fns.get(root)
    if fn is None:
        # Fall back to the DEF name off the live object. Deliberately narrow:
        # the name must exist in the DEFINING module's own top-level defs, so a
        # functools wrapper pointing at some other module still yields an empty
        # Boundary exactly as before rather than silently analysing the wrong
        # body.
        objname = getattr(obj, "__name__", None)
        if isinstance(objname, str) and objname in fns:
            fn_name, fn = objname, fns[objname]
    if fn is None:
        return out
    _walk(fn_name, set(_param_names(fn)), mod, out, set())
    out.constructed |= _constructed(fn, glb, out)
    if obj is not None:
        out.annotated |= _annotation_classes(obj, glb, out)
    return out


def boundaries(tool_names: Sequence[str]) -> Dict[str, Boundary]:
    """:func:`boundary_for` over many names (the parse cache makes this cheap)."""
    return {n: boundary_for(n) for n in tool_names}
