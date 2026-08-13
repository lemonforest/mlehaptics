"""rc430 (`#T1127` / `#T1094`) — the (op, param)-keyed VALID-ARGUMENT provider.

THE MISSING INFORMATION, AND WHY IT IS KEYED BY (op, param)
----------------------------------------------------------
``ToolParameter`` publishes ``name`` / ``type`` / ``required`` / ``summary``.
A consumer can therefore synthesize a well-TYPED argument but not a VALID one:
``type`` cannot distinguish two ``int`` params with different domains, and it
cannot distinguish a ``str`` that is a label from a ``str`` that is a
filesystem path. ``tests/test_mcp.py``'s ``_synth_value_for_type`` is a
61-entry **type-keyed** table accreted in a test file for precisely that
reason, and its ``str`` row hands the literal ``"a"`` to every string
parameter — including ``genome_save(path=...)``, which then writes a stray
16-byte file named ``a`` into the package directory. That is `#T1094`.

This module supplies the same information from the side that already has it.
Every ToolEntry ships an ``example["worked"]`` snippet that is **executable
Python** (570 of 655 entries at rc430), and an argument that appeared in a call
that RETURNED is valid **by construction** — no derivation, no declaration, no
guess. The provider executes each snippet with the op wrapped in a recorder and
keeps the bound arguments of the calls that returned.

WHY NOT ``example["input"]``
---------------------------
``example["input"]`` is present on 449 entries and looks like a kwargs map. It
is NOT one — **the values are PROSE**. ``srmech.math.cyclic.gcd`` ships::

    {'a, b': 'Antikythera wheel + dial periods — b1 224 vs lunar 127, ...'}

``tests/test_tool_example_input_schema_rc355.py`` pins the *keys* toward
parameter names under a down-only ceiling; it says nothing about the values.
Reading ``input`` as kwargs would substitute a sentence for an integer. This
module never reads it.

WHY IT LIVES IN ``tools/`` AND NOT IN THE PACKAGE
-------------------------------------------------
Two hard reasons, neither of them taste:

* ``tests/test_selfhosting_import_ban.py`` holds a **down-only CEIL on ``json``
  import statements under ``srmech/``**. An in-package ledger reader would
  either break that ceiling or force a ``srmech._json`` front-door dependency
  for no benefit.
* A ``tools/`` module is importable by ``tools/gen_tool_docs.py`` directly and
  by tests via the ``sys.path.insert(TOOLS)`` pattern already used at
  ``tests/test_worked_examples_execute_rc354.py:100``. Zero package ripple,
  zero registry ripple, zero rosetta ripple.

THE LEDGER STORES ONLY JSON-ROUND-TRIPPABLE VALUES
--------------------------------------------------
Many recovered arguments are ``Mat`` / ``HV`` / ``bytes`` handles that JSON
cannot carry. Those are recorded as **present but unserializable**, by name,
rather than dropped silently — the count is a measurement, not a gap. The
consumers that need this provider (`the MCP JSON boundary, the doc-example
synthesiser`) are themselves JSON-bounded, so the serializable subset is
exactly the useful one, and the residual is named and counted rather than
papered over.

ABSENCE IS A VALUE
------------------
:data:`UNSYNTHESIZABLE` is a sentinel, not ``None`` and not a plausible-looking
default. A consumer that receives it must SKIP and RECORD, never substitute. A
value the harness cannot justify has to be visible and counted; the literal
``"a"`` fallback it replaces is the exact shape of the defect this closes.

Regenerate the ledger with::

    python3 tools/run_example_args.py              # full
    python3 tools/run_example_args.py --only-stale # re-run what changed

Freshness is enforced by
``tests/test_synth_args_provenance_rc430.py::test_ledger_is_fresh_against_the_live_schema``
— without it the ledger is a dead seam reporting on a tree that no longer
exists.
"""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PY_ROOT = Path(__file__).resolve().parents[1]
LEDGER = PY_ROOT / "tests" / "example_args_ledger.ndjson"

#: Cap on recorded calls per op. A worked snippet can call its own op dozens of
#: times; the first few bindings carry the information and the rest is bulk.
MAX_CALLS = 24

#: Cap on the serialised size of any single harvested value. A harvested
#: 4096-element matrix is a valid argument and a useless ledger row.
MAX_JSON_CHARS = 4096


#: Name fragments that mark a parameter as POSSIBLY a filesystem path.
#: Used only ever to REFUSE, never to assert — see :func:`is_path_shaped`.
PATH_NAME_MARKERS = (
    "path", "file", "dir", "dest", "root", "out", "src", "target", "folder",
)

#: Declared types that are a path outright.
PATH_TYPES = frozenset({"pathlib.Path", "Path", "str | pathlib.Path",
                        "Optional[pathlib.Path]"})


def is_path_shaped(param_name: str, type_string: str) -> bool:
    """True when a parameter might name a filesystem location.

    THE HEURISTIC IS SAFE BECAUSE IT IS ONLY EVER USED TO REFUSE. The two
    error directions are not symmetric: a false positive costs one synthesised
    example, while a false negative writes a file into the user's tree. That
    asymmetry — not the accuracy of the name list — is what licenses a name
    heuristic here, and it is why this function must never be used to *claim*
    that something IS a path.

    Contrast with the frame axis in ``introspect/tool_schema.py``, where a
    name-derived roster is explicitly forbidden: there the heuristic would
    ASSERT a property, and a wrong assertion makes a consumer synthesize a
    confidently invalid argument. Same heuristic, opposite licence.
    """
    if type_string in PATH_TYPES:
        return True
    if type_string not in ("str", "Optional[str]"):
        return False
    low = param_name.lower()
    return any(marker in low for marker in PATH_NAME_MARKERS)


class _Unsynthesizable:
    """The 'no justified value' sentinel. Distinct from ``None``, which is a
    legitimate argument value for an optional parameter."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "UNSYNTHESIZABLE"

    def __bool__(self) -> bool:
        return False


#: The sentinel. A consumer receiving this MUST skip and record the reason.
UNSYNTHESIZABLE = _Unsynthesizable()


# ──────────────────────────────────────────────────────────────────────
# JSON round-trip admission
# ──────────────────────────────────────────────────────────────────────

def _as_wire(value: Any) -> Any:
    """The value as JSON would deliver it: tuples become lists, recursively."""
    if isinstance(value, tuple):
        return [_as_wire(v) for v in value]
    if isinstance(value, list):
        return [_as_wire(v) for v in value]
    if isinstance(value, dict):
        return {k: _as_wire(v) for k, v in value.items()}
    return value


def jsonable(value: Any) -> Tuple[bool, Any]:
    """``(ok, wire_value)``. ``ok`` is True when the value survives a
    ``dumps``/``loads`` round trip **up to the tuple/list collapse**.

    The first draft compared the reloaded value against the original with
    ``==`` and rejected anything that moved. That is too strict, and the
    measurement said so: ``just_limit((3, 2))``, ``tempers_out((81, 80), 12)``
    and ``comma_of_chain((3, 2), 12, (2, 1))`` all publish TUPLE arguments,
    all were rejected as unserializable, and all three then failed the frame
    probe with ``TypeError: missing 1 required positional argument`` — an
    artefact of the harvest, read as a property of the op.

    Collapsing tuples to lists is not a loosening of the contract, it IS the
    contract: **JSON has no tuple**, so a list is precisely what an MCP client
    puts on the wire, and ``srmech.mcp._tools._coerce_arguments`` exists to
    turn it back. Recording the wire form is recording the truth.

    Everything else stays strict — a dict with int keys still fails, because
    ``{1: "a"}`` really does come back as ``{"1": "a"}`` and that is a changed
    argument rather than a changed spelling.
    """
    try:
        text = json.dumps(value, sort_keys=True)
    except (TypeError, ValueError):
        return False, None
    if len(text) > MAX_JSON_CHARS:
        return False, None
    try:
        back = json.loads(text)
    except ValueError:  # pragma: no cover - dumps output is always loadable
        return False, None
    if back != _as_wire(value):
        return False, None
    return True, back


# ──────────────────────────────────────────────────────────────────────
# The harvest
# ──────────────────────────────────────────────────────────────────────

def snippet_source(example: Optional[Dict[str, Any]]) -> Optional[str]:
    """The executable source of a worked example, ``setup`` prepended."""
    if not isinstance(example, dict):
        return None
    worked = example.get("worked")
    if not isinstance(worked, str) or not worked.strip():
        return None
    setup = example.get("setup")
    if isinstance(setup, str) and setup.strip():
        return setup + "\n" + worked
    return worked


def resolve(op_name: str):
    """``(module, func_name, callable)`` for a registered op, or ``None``.

    Resolution is by dotted path, which is what the registry name IS. A failure
    here is recorded as ``unresolvable`` rather than raised: profile-contributed
    tools and class-bound surfaces legitimately do not resolve this way, and a
    provider that dies on them would report a smaller registry than exists.
    """
    mod_name, _, fname = op_name.rpartition(".")
    if not mod_name or not fname:
        return None
    try:
        mod = importlib.import_module(mod_name)
    except BaseException:
        return None
    fn = getattr(mod, fname, None)
    if fn is None or not callable(fn):
        return None
    return mod, fname, fn


def record_calls(op_name: str, example: Optional[Dict[str, Any]]
                 ) -> Tuple[List[Tuple[tuple, dict]], Optional[str]]:
    """Execute the published snippet with the op wrapped; return the args of
    the calls that RETURNED, plus any snippet error.

    A call that raised is NOT recorded — its arguments are exactly the invalid
    ones. A snippet that dies partway still yields the calls that completed
    before it died, which is why the error is returned alongside rather than
    instead of the harvest.
    """
    src = snippet_source(example)
    if src is None:
        return [], "no_worked_snippet"
    res = resolve(op_name)
    if res is None:
        return [], "unresolvable"
    mod, fname, real = res
    seen: List[Tuple[tuple, dict]] = []

    def wrapper(*a, **kw):
        r = real(*a, **kw)          # raises => not recorded, which is correct
        if len(seen) < MAX_CALLS:
            seen.append((a, dict(kw)))
        return r

    try:
        wrapper.__name__ = getattr(real, "__name__", fname)
        wrapper.__doc__ = getattr(real, "__doc__", None)
        wrapper.__wrapped__ = real
    except Exception:
        pass

    setattr(mod, fname, wrapper)
    err = None
    try:
        exec(compile(src, f"<worked:{op_name}>", "exec"), {"__name__": "__worked__"})
    except BaseException as exc:
        err = f"{type(exc).__name__}: {str(exc)[:200]}"
    finally:
        setattr(mod, fname, real)
    return seen, err


def bind(fn, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Positional+keyword call -> a full ``{param_name: value}`` map."""
    sig = inspect.signature(fn)
    b = sig.bind(*args, **kwargs)
    b.apply_defaults()
    return dict(b.arguments)


def harvest_op(op_name: str, example: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Harvest one op. Returns a ledger record (a plain dict, always).

    ``args`` holds only the JSON-round-trippable bindings; ``unserializable``
    names the parameters that were recovered but cannot be carried as JSON.
    Both are reported because the difference between "no valid value exists"
    and "a valid value exists that JSON cannot express" is a real distinction
    and collapsing it would understate the coverage.
    """
    rec: Dict[str, Any] = {
        "op": op_name,
        "status": "",
        "args": {},
        "unserializable": [],
        "n_calls": 0,
        "error": None,
    }
    calls, err = record_calls(op_name, example)
    rec["error"] = err
    if not calls:
        rec["status"] = {
            "no_worked_snippet": "no_worked_snippet",
            "unresolvable": "unresolvable",
        }.get(err or "", "no_returning_call")
        return rec
    rec["n_calls"] = len(calls)
    res = resolve(op_name)
    if res is None:  # pragma: no cover - record_calls already returned above
        rec["status"] = "unresolvable"
        return rec
    _, _, real = res
    bound: Optional[Dict[str, Any]] = None
    for args, kwargs in calls:
        try:
            bound = bind(real, args, kwargs)
            break
        except BaseException:
            continue
    if bound is None:
        rec["status"] = "bind_failed"
        return rec
    ok_args: Dict[str, Any] = {}
    unser: List[str] = []
    transient: List[str] = []
    for pname, value in bound.items():
        # A HARVESTED ARGUMENT MUST BE REPRODUCIBLE, and a filesystem path is
        # the one class that is not. Measured at rc430:
        # ``fiedler_sparse_file`` harvested ``path='/tmp/tmpbb5ta8r_/codon.graph'``
        # — a file the snippet created in its own temp directory, which is gone
        # by the time anything reads the ledger. The op then classified
        # BASE_RAISES on one run and NOT_ADMISSIBLE on the next, and a census
        # that answers differently on the same tree is not a measurement.
        #
        # Path params are therefore never harvested. The cost is exactly 3 of
        # 33 path-ish parameters (the rest were never recoverable anyway), and
        # in exchange every path parameter is served by ONE mechanism — the
        # sandbox tier — instead of two that disagree.
        if is_path_shaped(pname, "str") and isinstance(value, (str, bytes)):
            transient.append(pname)
            continue
        ok, canon = jsonable(value)
        if ok:
            ok_args[pname] = canon
        else:
            unser.append(pname)
    if transient:
        rec["transient_path_params"] = sorted(transient)
    rec["args"] = ok_args
    rec["unserializable"] = sorted(unser)
    rec["status"] = "ok" if ok_args else "no_jsonable_arg"
    return rec


# ──────────────────────────────────────────────────────────────────────
# The ledger
# ──────────────────────────────────────────────────────────────────────

def load_ledger(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """``{op_name: record}`` from the committed ledger. ``{}`` when absent."""
    p = path or LEDGER
    if not p.exists():
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("record") == "meta":
            continue
        out[row["op"]] = row
    return out


def load_meta(path: Optional[Path] = None) -> Dict[str, Any]:
    """The ledger's meta row (``{}`` when the ledger is absent)."""
    p = path or LEDGER
    if not p.exists():
        return {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("record") == "meta":
            return row
    return {}


def write_ledger(records: List[Dict[str, Any]], meta: Dict[str, Any],
                 path: Optional[Path] = None) -> None:
    """Write the NDJSON ledger, one record per line, sorted by op name."""
    p = path or LEDGER
    lines = [json.dumps(dict(meta, record="meta"), sort_keys=True)]
    for rec in sorted(records, key=lambda r: r["op"]):
        lines.append(json.dumps(rec, sort_keys=True))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# ──────────────────────────────────────────────────────────────────────
# The consumer-facing lookup
# ──────────────────────────────────────────────────────────────────────

class ArgProvider:
    """Ledger-backed ``(op, param) -> value`` lookup.

    The unit of the answer is the (op, param) PAIR. That is the whole point:
    a type-keyed table cannot distinguish ``cyclic_mod_add``'s ``n`` from
    ``is_prime``'s ``n``, and cannot distinguish ``genome_save``'s ``path``
    from ``normal_order``'s ``convention`` — both are ``str``.
    """

    def __init__(self, ledger: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self._rows = load_ledger() if ledger is None else ledger

    def has(self, op_name: str, param: str) -> bool:
        row = self._rows.get(op_name)
        return bool(row) and param in (row.get("args") or {})

    def get(self, op_name: str, param: str) -> Any:
        """The harvested value, or :data:`UNSYNTHESIZABLE`."""
        row = self._rows.get(op_name)
        if not row:
            return UNSYNTHESIZABLE
        args = row.get("args") or {}
        if param not in args:
            return UNSYNTHESIZABLE
        return args[param]

    def kwargs(self, op_name: str) -> Dict[str, Any]:
        """Every harvested argument for one op (possibly empty)."""
        row = self._rows.get(op_name)
        return dict((row or {}).get("args") or {})

    def ops(self):
        return set(self._rows)


#: Process-wide provider, built lazily so importing this module is cheap.
_PROVIDER: Optional[ArgProvider] = None


def provider() -> ArgProvider:
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = ArgProvider()
    return _PROVIDER


# ──────────────────────────────────────────────────────────────────────
# The safe last resort — for EPHEMERAL consumers only
# ──────────────────────────────────────────────────────────────────────

_SANDBOX: Optional[Path] = None


def sandbox_dir() -> Path:
    """A per-process temp directory a synthesised path may point into.

    For a consumer whose output is NOT committed (the MCP every-tool smoke),
    this keeps full invocation coverage while making the filesystem effect
    harmless: an op that really does write lands in a temp directory that no
    gate, no build and no user ever reads.

    A COMMITTED consumer must NOT use this — the directory name changes every
    run, so a generated artifact containing it could never be byte-identical
    twice. ``tools/gen_tool_docs.py`` therefore refuses instead, which is why
    :data:`UNSYNTHESIZABLE` exists as a separate answer from "here is a value".
    """
    global _SANDBOX
    if _SANDBOX is None:
        import tempfile
        _SANDBOX = Path(tempfile.mkdtemp(prefix="srmech_synth_"))
    return _SANDBOX


def sandbox_path(param_name: str) -> str:
    """A nonexistent, writable-if-touched path inside :func:`sandbox_dir`."""
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in param_name)
    return str(sandbox_dir() / f"srmech_synth_{safe}")
