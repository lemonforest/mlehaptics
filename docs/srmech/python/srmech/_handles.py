"""Package-scope handle dual-grammar registry (v0.5.0rc16).

THE PROBLEM rc15 left open: 7 ``srmech.spectral.*`` tools were marked
``mcp_callable=False`` because their param/return surface is a bare
:class:`srmech.spectral.SpectralHandle` (or ``SpectralHandle | bytes``) —
an opaque, frozen, bytes-bearing dataclass JSON-RPC cannot carry **by
value**. The fix is a **by-reference** indirection: a producer tool returns
a small JSON *id* the LLM copies verbatim into the next tool's input, and a
shared in-process registry resolves that id back to the live object.

THE DUAL GRAMMAR (the locked concept — we never force both halves into one
"sentence"; each consumer speaks the grammar native to it):

* ``uuid`` — the CANONICAL, position-encoded, silicon-native / cyclic-
  algebra address. Minted at registration via ``uuid.uuid4().hex`` (the
  established idiom from :func:`srmech.bus._event.new_correlation_id`).
  Volatile / per-process — correct for an in-process by-reference store.
* ``name`` — the meaning-encoded, biology-native / continuous-Hopf grammar.
  For a ``SpectralHandle`` it auto-derives from the object's OWN content-
  addressing as ``"spectral:" + content_sha[:12]`` (``content_sha`` is the
  Class A SHA-256 already on the frozen dataclass — so NO new
  ``hashlib.sha256`` call is introduced; the route-through-``sha256_bytes``
  discipline is honoured). The recon CORRECTION that ``srmech.amsc.naming``
  is Class E binary-search (NOT a name registry) is decisive: the name is
  derived from the handle's content_sha, not built on ``naming.py``.

Resolution resolves by ``uuid`` first, then by ``name``; either half alone
returns the same in-process object. This IS the B/H/N translation locus the
substrate-self-recognition memory note names ("B/H/N translation lives in
registry resolution").

TWO ARMS, ONE MODULE (the two customers share ONE public surface):

* :meth:`HandleRegistry.register` / :meth:`HandleRegistry.resolve` — the
  STATEFUL uuid+name registration arm (the 7 spectral handles).
* :func:`resolve_operator_name` — the STATELESS name-grammar arm for
  ``chiral_dual``'s ``op``: an importable unary sequence->sequence operator
  is content-addressed by its dotted import path, so it needs no storage
  round. **Restricted to the ``srmech.`` namespace** (see that function).

SCOPE: in-process only for rc16. The JSON envelope is bus-transportable,
but a uuid minted in another interpreter will NOT resolve on the far side;
cross-process re-resolution (re-decompose via the content-addressed name)
is the rc17+ bus-registry extension. A later bus voxel registers each
``ServerEndpoint`` via ``register(endpoint, kind="bus-endpoint", ...)`` to
gain the UUID identity its permanently-``None`` ``Endpoint.pid`` reserved.

Pure Python; no C; no ABI change (ABI stays 3).
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple

#: Sentinel key that tags a handle id object on the JSON wire. Namespaced
#: (a leading ``$``) so it is unambiguous against every other wire shape in
#: play — a base64 bare-``str`` (the other arm of ``SpectralHandle |
#: bytes``), an ordinary ``dict`` / ``ChainSpec`` / ``Mapping`` object
#: param, and a serialised dataclass ``asdict`` (which has no sentinel).
HANDLE_ENVELOPE_KEY: str = "$srmech_handle"

#: Maximum number of live handles in the bounded-LRU store. Larger than
#: ``spectral.N_MAX_EIGENBASES`` (8) because handles are tiny (a frozen
#: dataclass holding already-packed bytes) and an LLM may juggle many
#: across one conversation; 256 caps unbounded growth (the leak risk) while
#: giving generous headroom.
HANDLE_REGISTRY_MAX: int = 256

#: Operator-name resolution allow-list prefix (v0.5.0rc16 safety fix). An
#: ``operator_name`` MUST begin with this so :func:`resolve_operator_name`
#: never advertises resolving an arbitrary importable callable (``os.system``
#: / builtins / stdlib are rejected with a clean error BEFORE any import).
_OPERATOR_NAME_ALLOWED_PREFIX: str = "srmech."


class HandleNotFoundError(KeyError):
    """Raised when a handle id (uuid or name) does not resolve — either it
    was never registered or it has been evicted from the bounded LRU. The
    message tells the caller to re-produce the handle via the originating
    tool."""


class HandleKindError(ValueError):
    """Raised when a handle resolves but was registered under a different
    ``kind`` than the caller asked for (e.g. resolving a ``bus-endpoint``
    handle as ``kind="spectral"``)."""


class HandleRegistry:
    """In-process bounded-LRU registry mapping ``uuid`` (canonical) and
    ``name`` (secondary) to a live Python object.

    Thread-safe via a single :class:`threading.RLock` (RLock, not Lock,
    because :meth:`register` calls :meth:`_resolve_uuid` internally for the
    idempotency check). The MCP server is single-threaded per call, but the
    bus (``srmech.bus`` ``serve()`` / ``Channel``) is genuinely cross-thread
    / cross-connection and the locked concept says the bus SHARES this
    table, so the lock is mandatory from day one.

    Eviction mirrors :func:`srmech.spectral._cache_eigenbasis`: ``move_to_end``
    on register + on resolve-touch (LRU), ``popitem(last=False)`` past
    :data:`HANDLE_REGISTRY_MAX`. No TTL (an LLM conversation is short-lived).
    """

    def __init__(self, max_entries: int = HANDLE_REGISTRY_MAX) -> None:
        assert max_entries >= 1, "registry capacity must be >= 1"
        self._max = max_entries
        self._lock = threading.RLock()
        # uuid_hex -> (obj, name, kind). The canonical, position-encoded
        # table; insertion order is the LRU order.
        self._store: "OrderedDict[str, Tuple[Any, str, str]]" = OrderedDict()
        # name -> uuid_hex (the meaning-encoded secondary index).
        self._name_index: Dict[str, str] = {}
        # value-hash -> uuid_hex (idempotency: an identical-by-value handle
        # registered twice returns its existing id rather than minting a
        # duplicate). Only populated for hashable objects.
        self._value_index: Dict[int, str] = {}

    # ── internal (lock held by caller) ──────────────────────────────────

    def _auto_name(self, obj: Any, kind: str) -> str:
        """Derive a meaning-encoded auto-name for ``obj``.

        For a ``SpectralHandle`` this reuses the object's existing
        ``content_sha`` (Class A SHA-256 already on the frozen dataclass —
        NO new hash call), giving a human/LLM-legible, content-meaningful
        name. Any other object falls back to ``"<kind>:<uuid-prefix>"`` at
        the call site (handled in :meth:`register`)."""
        content_sha = getattr(obj, "content_sha", None)
        if isinstance(content_sha, str) and content_sha:
            return f"{kind}:{content_sha[:12]}"
        return ""

    def _evict_if_over_cap(self) -> None:
        """Drop oldest entries past the bound, cleaning both secondary
        indices. Lock is held by the caller."""
        while len(self._store) > self._max:
            old_uuid, (old_obj, old_name, _old_kind) = self._store.popitem(
                last=False
            )
            # Only clear the name-index row if it still points at THIS uuid
            # (a newer same-name handle must be preserved).
            if self._name_index.get(old_name) == old_uuid:
                del self._name_index[old_name]
            try:
                vh = hash(old_obj)
            except TypeError:
                vh = None
            if vh is not None and self._value_index.get(vh) == old_uuid:
                del self._value_index[vh]

    def _resolve_uuid(self, uuid_hex: str) -> Optional[Tuple[Any, str, str]]:
        """Return the live ``(obj, name, kind)`` for ``uuid_hex`` (LRU-
        touching it) or ``None``. Lock held by caller."""
        entry = self._store.get(uuid_hex)
        if entry is not None:
            self._store.move_to_end(uuid_hex)
        return entry

    # ── public surface ──────────────────────────────────────────────────

    def register(
        self, obj: Any, *, kind: str, name: Optional[str] = None
    ) -> Tuple[str, str]:
        """Register ``obj`` under ``kind``; return ``(uuid_hex, name)``.

        Mints ``uuid.uuid4().hex``. If ``name`` is ``None`` an auto-name is
        derived (``SpectralHandle`` -> ``"spectral:" + content_sha[:12]``;
        otherwise ``"<kind>:<uuid-prefix>"``). Registration is IDEMPOTENT
        for hashable objects: an identical-by-value object already live
        returns its existing ``(uuid, name)`` instead of minting a duplicate
        (keeps repeated decompose->serialise stable and bounds churn)."""
        assert kind, "register: kind must be non-empty"
        with self._lock:
            # Idempotency short-circuit (hashable objects only).
            try:
                value_hash: Optional[int] = hash(obj)
            except TypeError:
                value_hash = None
            if value_hash is not None:
                existing_uuid = self._value_index.get(value_hash)
                if existing_uuid is not None:
                    existing = self._resolve_uuid(existing_uuid)
                    if existing is not None:
                        return existing_uuid, existing[1]
                    # Stale reverse-map row (its uuid was evicted) — drop it.
                    del self._value_index[value_hash]

            uuid_hex = uuid.uuid4().hex
            resolved_name = name if name is not None else self._auto_name(obj, kind)
            if not resolved_name:
                resolved_name = f"{kind}:{uuid_hex[:12]}"

            self._store[uuid_hex] = (obj, resolved_name, kind)
            self._store.move_to_end(uuid_hex)
            self._name_index[resolved_name] = uuid_hex
            if value_hash is not None:
                self._value_index[value_hash] = uuid_hex
            self._evict_if_over_cap()
            return uuid_hex, resolved_name

    def resolve(self, ref: Dict[str, Any], *, kind: Optional[str] = None) -> Any:
        """Resolve an inner handle dict ``{"uuid", "name", "kind"}`` to the
        live object. ``uuid`` first, then ``name``. If BOTH are present and
        resolve to DIFFERENT live uuids, the uuid wins (position-encoded
        identity) and a clean :class:`ValueError` is raised on the
        disagreement. Raises :class:`HandleNotFoundError` on a miss /
        eviction and :class:`HandleKindError` on a ``kind`` mismatch."""
        assert isinstance(ref, dict), "resolve: ref must be a handle dict"
        ref_uuid = ref.get("uuid")
        ref_name = ref.get("name")
        with self._lock:
            entry: Optional[Tuple[Any, str, str]] = None
            resolved_uuid: Optional[str] = None
            if isinstance(ref_uuid, str) and ref_uuid:
                entry = self._resolve_uuid(ref_uuid)
                resolved_uuid = ref_uuid if entry is not None else None
            if entry is None and isinstance(ref_name, str) and ref_name:
                name_uuid = self._name_index.get(ref_name)
                if name_uuid is not None:
                    entry = self._resolve_uuid(name_uuid)
                    resolved_uuid = name_uuid if entry is not None else None
            elif (
                entry is not None
                and isinstance(ref_name, str)
                and ref_name
            ):
                # uuid already resolved; if a name is ALSO supplied and it
                # points at a different live uuid, that is a contradiction.
                name_uuid = self._name_index.get(ref_name)
                if name_uuid is not None and name_uuid != resolved_uuid:
                    raise ValueError(
                        f"handle id disagreement: uuid {ref_uuid!r} and name "
                        f"{ref_name!r} resolve to different handles (uuid wins)"
                    )
            if entry is None:
                ident = ref_uuid or ref_name or "<empty>"
                raise HandleNotFoundError(
                    f"handle {ident!r} not found or evicted; re-produce it "
                    f"via the originating tool"
                )
            obj, _name, obj_kind = entry
            if kind is not None and obj_kind != kind:
                raise HandleKindError(
                    f"handle resolved as kind {obj_kind!r} but caller asked "
                    f"for kind {kind!r}"
                )
            return obj

    def clear(self) -> None:
        """Drop all handles. Test-isolation utility (parallels
        :func:`srmech.spectral.clear_eigenbasis_cache`)."""
        with self._lock:
            self._store.clear()
            self._name_index.clear()
            self._value_index.clear()

    def __len__(self) -> int:  # pragma: no cover - trivial
        with self._lock:
            return len(self._store)


#: Module-level singleton (mirrors ``tool_schema._REGISTRY`` +
#: ``spectral._EIGENBASIS_CACHE`` single-instance discipline).
_REGISTRY = HandleRegistry()


def get_handle_registry() -> HandleRegistry:
    """Return the process-wide :class:`HandleRegistry` singleton."""
    return _REGISTRY


def encode_envelope(uuid_hex: str, name: str, kind: str) -> Dict[str, Any]:
    """Build the on-wire handle id object
    ``{"$srmech_handle": {"uuid", "name", "kind"}}``."""
    assert uuid_hex and name and kind, "encode_envelope: all fields required"
    return {HANDLE_ENVELOPE_KEY: {"uuid": uuid_hex, "name": name, "kind": kind}}


def is_handle_envelope(value: Any) -> bool:
    """True iff ``value`` is a handle id object carrying the
    :data:`HANDLE_ENVELOPE_KEY` sentinel."""
    return isinstance(value, dict) and HANDLE_ENVELOPE_KEY in value


def resolve_operator_name(name: str) -> Callable[..., Any]:
    """Resolve an operator NAME (the name-grammar arm) to its live callable.

    This is ``chiral_dual``'s ``op`` resolver: a unary sequence->sequence
    operator is content-addressed by its dotted import path, so it needs no
    registry storage (the stateless half of the dual grammar).

    SAFETY (v0.5.0rc16 fix 4+5): the advertised contract is NOT "any
    importable callable". We restrict to the **srmech namespace** — ``name``
    MUST begin with ``"srmech."`` — and reject everything else (``os.system``,
    ``builtins.*``, stdlib, ``numpy.*``, ...) with a clean :class:`ValueError`
    BEFORE delegating to the dotted-callable resolver. We then best-effort
    verify the resolved object is callable. (The honest contract is "a
    dotted ``srmech.*`` unary sequence->sequence operator name." Note:
    ``_resolve_dotted_callable`` already checks ``callable()``; the
    *arity / seq->seq* contract is enforced at RUNTIME by ``chiral_dual``'s
    own native length-guard / Python composition — a resolvable-but-wrong
    op such as a binary or scalar op raises a ``TypeError`` there, NOT a
    ``ValueError`` — so we keep the namespace allow-list as the up-front
    guard and let the smoke synth a genuine unary op,
    ``srmech.amsc.cascade.chiral_flip``.)

    SAFETY (v0.5.0rc17 hardening): the ``srmech.*`` name PREFIX is necessary
    but NOT sufficient. ``_resolve_dotted_callable`` walks attributes, so a
    name can traverse THROUGH a srmech module to a re-exported stdlib
    callable (e.g. ``srmech.amsc.format.hashlib.sha256`` -> the real
    ``_hashlib`` ``sha256``). After resolution we additionally verify the
    resolved object's ``__module__`` is itself ``srmech.*``, rejecting any
    name that reaches a re-exported stdlib / foreign callable. Fail-closed:
    a ``None`` / non-``str`` ``__module__`` is treated as a reject.
    """
    if not isinstance(name, str) or not name:
        raise ValueError(
            f"operator_name must be a non-empty dotted string; got "
            f"{type(name).__name__}"
        )
    if not name.startswith(_OPERATOR_NAME_ALLOWED_PREFIX):
        raise ValueError(
            f"operator_name {name!r} is not permitted: only "
            f"{_OPERATOR_NAME_ALLOWED_PREFIX!r}-namespaced operator names are "
            f"resolvable (arbitrary importable callables are rejected for "
            f"safety)"
        )
    # Lazy import to avoid a _handles -> mcp import edge at module load.
    from srmech.mcp._tools import _resolve_dotted_callable

    resolved = _resolve_dotted_callable(name)
    # rc17 hardening: the srmech.* name PREFIX is necessary but not
    # sufficient -- _resolve_dotted_callable walks attributes, so a name can
    # traverse THROUGH a srmech module to a re-exported stdlib callable
    # (e.g. srmech.amsc.format.hashlib.sha256 -> the real _hashlib sha256).
    # Verify the RESOLVED object truly originates in the srmech namespace.
    origin = getattr(resolved, "__module__", None)
    if not (isinstance(origin, str) and origin.startswith(_OPERATOR_NAME_ALLOWED_PREFIX)):
        raise ValueError(
            f"operator_name {name!r} resolved to an object defined in "
            f"{origin!r}, outside the {_OPERATOR_NAME_ALLOWED_PREFIX!r} "
            f"namespace (re-exported stdlib / foreign callables are rejected "
            f"for safety)"
        )
    # Best-effort callability check (the resolver already enforces this,
    # but assert the advertised contract explicitly).
    if not callable(resolved):
        raise ValueError(f"operator_name {name!r} did not resolve to a callable")
    return resolved


__all__ = [
    "HANDLE_ENVELOPE_KEY",
    "HANDLE_REGISTRY_MAX",
    "HandleRegistry",
    "HandleNotFoundError",
    "HandleKindError",
    "get_handle_registry",
    "encode_envelope",
    "is_handle_envelope",
    "resolve_operator_name",
]
