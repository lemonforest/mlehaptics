"""Tests for ``srmech._handles`` — the rc16 handle dual-grammar registry.

The package-scope name+uuid registry that makes the 7 ``srmech.spectral.*``
tools JSON-callable by reference (and the stateless operator-name arm that
makes ``chiral_dual``'s ``op`` honestly drivable). Covers: dual-grammar
resolution (uuid-first then name), uuid/name disagreement, bounded-LRU
eviction + ``HandleNotFoundError``, ``HandleKindError`` on kind mismatch,
idempotent same-value registration, thread-safety under concurrent
register/resolve, and the srmech-namespace operator-name allow-list.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import pytest

from srmech._handles import (
    HANDLE_ENVELOPE_KEY,
    HANDLE_REGISTRY_MAX,
    HandleKindError,
    HandleNotFoundError,
    HandleRegistry,
    encode_envelope,
    get_handle_registry,
    is_handle_envelope,
    resolve_operator_name,
)
from srmech.spectral import SpectralHandle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handle(seed: int = 0) -> SpectralHandle:
    """A frozen SpectralHandle with a distinct content_sha per ``seed``.

    The seed is placed at the FRONT of the 64-hex content_sha so the
    auto-name (``"spectral:" + content_sha[:12]``) differs per seed — two
    handles must not accidentally share a name in the eviction / dual-grammar
    fixtures.
    """
    prefix = f"{seed:012x}"  # 12 hex chars, unique per seed in test range
    return SpectralHandle(
        substrate_descriptor_hash=f"desc{seed:04d}",
        coefficients_bytes=bytes([seed % 256]) * 4 + seed.to_bytes(4, "big"),
        content_sha=prefix + "0" * (64 - len(prefix)),
        n_modes=4,
    )


@dataclass(frozen=True)
class _OtherKindHandle:
    """A non-spectral hashable object (no content_sha)."""

    tag: str


# ---------------------------------------------------------------------------
# Dual-grammar resolution
# ---------------------------------------------------------------------------


def test_register_resolve_by_uuid_and_name() -> None:
    """register() mints a uuid + content-addressed name; the SAME object
    resolves by uuid AND by name (dual-grammar both arms)."""
    reg = HandleRegistry()
    h = _make_handle(1)
    uuid_hex, name = reg.register(h, kind="spectral")

    assert len(uuid_hex) == 32  # uuid4().hex
    assert name == "spectral:" + h.content_sha[:12]

    by_uuid = reg.resolve({"uuid": uuid_hex})
    by_name = reg.resolve({"name": name})
    assert by_uuid is h
    assert by_name is h


def test_uuid_and_name_agree_else_error() -> None:
    """An envelope with BOTH uuid+name resolves identically; a name that
    points at a DIFFERENT live uuid raises a clean ValueError (uuid wins)."""
    reg = HandleRegistry()
    h1 = _make_handle(1)
    h2 = _make_handle(2)
    u1, n1 = reg.register(h1, kind="spectral")
    u2, n2 = reg.register(h2, kind="spectral")

    # Both halves agree -> resolves.
    assert reg.resolve({"uuid": u1, "name": n1}) is h1
    # uuid of h1 but name of h2 -> contradiction.
    with pytest.raises(ValueError):
        reg.resolve({"uuid": u1, "name": n2})


def test_resolve_by_kind_guard_and_mismatch() -> None:
    """resolve(kind=...) returns the object when kind matches and raises
    HandleKindError when it does not."""
    reg = HandleRegistry()
    other = _OtherKindHandle("x")
    u, _n = reg.register(other, kind="bus-endpoint", name="ep-A")

    assert reg.resolve({"uuid": u}, kind="bus-endpoint") is other
    with pytest.raises(HandleKindError):
        reg.resolve({"uuid": u}, kind="spectral")


# ---------------------------------------------------------------------------
# Eviction + not-found
# ---------------------------------------------------------------------------


def test_lru_eviction_and_not_found() -> None:
    """Registering > HANDLE_REGISTRY_MAX handles evicts the oldest; an
    evicted uuid resolve() raises HandleNotFoundError with a clear message;
    the evicted uuid's name-index row is also dropped."""
    reg = HandleRegistry(max_entries=4)
    ids = []
    for i in range(6):  # 2 over the cap of 4
        uuid_hex, name = reg.register(_make_handle(i), kind="spectral")
        ids.append((uuid_hex, name))

    assert len(reg) == 4
    # The two oldest (i=0, i=1) are evicted.
    for uuid_hex, name in ids[:2]:
        with pytest.raises(HandleNotFoundError) as ei:
            reg.resolve({"uuid": uuid_hex})
        assert "re-produce" in str(ei.value)
        # Name-index row for the evicted uuid is also gone.
        with pytest.raises(HandleNotFoundError):
            reg.resolve({"name": name})
    # The four newest survive.
    for uuid_hex, _name in ids[2:]:
        assert reg.resolve({"uuid": uuid_hex}) is not None


def test_resolve_unknown_raises_not_found() -> None:
    """A never-registered uuid / name raises HandleNotFoundError."""
    reg = HandleRegistry()
    with pytest.raises(HandleNotFoundError):
        reg.resolve({"uuid": "deadbeef" * 4})
    with pytest.raises(HandleNotFoundError):
        reg.resolve({"name": "spectral:nope"})


def test_lru_touch_on_resolve_protects_recent() -> None:
    """resolve() LRU-touches an entry so a recently-resolved handle is not
    the next eviction victim."""
    reg = HandleRegistry(max_entries=3)
    u0, _ = reg.register(_make_handle(0), kind="spectral")
    u1, _ = reg.register(_make_handle(1), kind="spectral")
    u2, _ = reg.register(_make_handle(2), kind="spectral")
    # Touch u0 so it becomes most-recent; then push one more.
    reg.resolve({"uuid": u0})
    u3, _ = reg.register(_make_handle(3), kind="spectral")
    # u1 (now oldest) is evicted; u0 survived because it was touched.
    assert reg.resolve({"uuid": u0}) is not None
    with pytest.raises(HandleNotFoundError):
        reg.resolve({"uuid": u1})
    assert reg.resolve({"uuid": u2}) is not None
    assert reg.resolve({"uuid": u3}) is not None


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_same_value_registration() -> None:
    """Registering an identical (by-value frozen) SpectralHandle twice
    returns the SAME (uuid, name) and does not grow the table."""
    reg = HandleRegistry()
    h = _make_handle(7)
    u1, n1 = reg.register(h, kind="spectral")
    u2, n2 = reg.register(h, kind="spectral")
    assert (u1, n1) == (u2, n2)
    assert len(reg) == 1
    # A distinct-by-value handle gets its own id.
    u3, _n3 = reg.register(_make_handle(8), kind="spectral")
    assert u3 != u1
    assert len(reg) == 2


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------


def test_envelope_encode_and_detect() -> None:
    """encode_envelope() produces the sentinel-tagged id object;
    is_handle_envelope() recognises it and rejects other shapes."""
    env = encode_envelope("a" * 32, "spectral:abc", "spectral")
    assert HANDLE_ENVELOPE_KEY in env
    assert env[HANDLE_ENVELOPE_KEY] == {
        "uuid": "a" * 32,
        "name": "spectral:abc",
        "kind": "spectral",
    }
    assert is_handle_envelope(env)
    # Other JSON shapes are NOT handle envelopes.
    assert not is_handle_envelope({})
    assert not is_handle_envelope({"foo": "bar"})
    assert not is_handle_envelope("a base64 string")
    assert not is_handle_envelope([1, 2, 3])


def test_clear_empties_registry() -> None:
    reg = HandleRegistry()
    reg.register(_make_handle(1), kind="spectral")
    reg.register(_make_handle(2), kind="spectral")
    assert len(reg) == 2
    reg.clear()
    assert len(reg) == 0


def test_module_singleton_is_stable() -> None:
    """get_handle_registry() returns the SAME process-wide instance."""
    assert get_handle_registry() is get_handle_registry()


# ---------------------------------------------------------------------------
# Thread-safety
# ---------------------------------------------------------------------------


def test_thread_safety_smoke() -> None:
    """N threads concurrently register + resolve; final state consistent,
    no exception, no lost/duplicated uuids (RLock)."""
    reg = HandleRegistry(max_entries=10_000)
    n_threads = 8
    per_thread = 50
    errors: list = []
    minted: list = []
    lock = threading.Lock()

    def worker(base: int) -> None:
        try:
            for i in range(per_thread):
                h = _make_handle(base * per_thread + i)
                u, _name = reg.register(h, kind="spectral")
                # Immediately resolve what we just registered.
                assert reg.resolve({"uuid": u}) is h
                with lock:
                    minted.append(u)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(b,)) for b in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"thread errors: {errors}"
    # Every minted uuid is unique (no collision / lost update).
    assert len(minted) == n_threads * per_thread
    assert len(set(minted)) == len(minted)
    assert len(reg) == n_threads * per_thread


# ---------------------------------------------------------------------------
# Operator-name arm (the srmech-namespace allow-list — rc16 fix 4+5)
# ---------------------------------------------------------------------------


def test_resolve_operator_name_accepts_srmech_op() -> None:
    """A dotted ``srmech.*`` unary seq->seq op name resolves to the real
    callable."""
    fn = resolve_operator_name("srmech.amsc.cascade.chiral_flip")
    assert callable(fn)
    assert fn([1.0, 2.0, 3.0]) == [3.0, 2.0, 1.0]


def test_resolve_operator_name_rejects_non_srmech_namespace() -> None:
    """Anything outside the ``srmech.`` namespace is rejected with a clean
    ValueError BEFORE any import is attempted (os.system, builtins, stdlib,
    numpy, ...)."""
    for bad in (
        "os.system",
        "builtins.eval",
        "subprocess.run",
        "numpy.negative",
        "math.sqrt",
    ):
        with pytest.raises(ValueError) as ei:
            resolve_operator_name(bad)
        assert "not permitted" in str(ei.value)


def test_resolve_operator_name_rejects_bad_input() -> None:
    """Empty / non-string names raise a clean ValueError; a bare srmech
    name with no module path (or a non-importable srmech path) raises (the
    delegate's MCPToolError, a subclass-agnostic failure)."""
    with pytest.raises(ValueError):
        resolve_operator_name("")
    with pytest.raises(ValueError):
        resolve_operator_name(None)  # type: ignore[arg-type]
    # In-namespace but non-importable -> the delegate raises (MCPToolError).
    with pytest.raises(Exception):
        resolve_operator_name("srmech.does.not.exist.at_all")
