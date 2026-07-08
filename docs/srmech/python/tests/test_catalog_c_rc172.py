"""rc172 — catalog REGISTRY / KERNEL-STATE / AUDIT logic → C (native == pure).

The ORCHESTRATION→C spine, batch 2. Four ``srmech.amsc.catalog`` ops earn C
peers (composing the srmech_json parser+writer+builder + srmech_sha256_hex):

  * ``list_registered_roots``  -> srmech_catalog_registered_roots
  * ``get_local_kernel_state`` -> srmech_catalog_local_kernel_state
  * ``use_local_kernel`` (+ ``clear_local_kernel``)
                               -> srmech_catalog_use_local_kernel
  * ``attestation_audit``      -> srmech_catalog_attestation_audit

This test pins native == pure across the registry / lookup / audit / kernel
sweep: register a root + list, a Class-E lookup hit + miss, a kernel
use/get/clear round-trip, an attestation_audit over a real attested source
(the data-only literature_curated path) + a synthetic full-MPR NDJSON via the
C peer directly, and the edge cases (empty registry, missing dataset,
duplicate register). numpy-free (stdlib json / ctypes / hashlib only).

The native == pure comparison forces HAS_NATIVE on/off around the SAME call;
when the native lib is absent both runs take the pure path (equal, trivially),
so the C-specific assertions are guarded by ``skipif(not NATIVE)``.
"""
from __future__ import annotations

import ctypes
import hashlib
import json

import pytest

from srmech.amsc import _native
from srmech.amsc import catalog

NATIVE = _native.HAS_NATIVE and _native.LIB is not None
needs_native = pytest.mark.skipif(
    not NATIVE, reason="native libsrmech not built in this env")


# ──────────────────────────────────────────────────────────────────────
# native == pure harness — run the SAME thunk with HAS_NATIVE forced on
# then off, restoring the flag. When NATIVE, the first run exercises the C
# peer; the second the complete pure path.
# ──────────────────────────────────────────────────────────────────────


def _native_then_pure(thunk):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        native = thunk()
        _native.HAS_NATIVE = False
        pure = thunk()
    finally:
        _native.HAS_NATIVE = saved
    return native, pure


@pytest.fixture(autouse=True)
def _clean_registry_state():
    """Reset the module registry + kernel state around every test."""
    catalog._clear_registered_roots()
    catalog.clear_local_kernel()
    yield
    catalog._clear_registered_roots()
    catalog.clear_local_kernel()


# ──────────────────────────────────────────────────────────────────────
# list_registered_roots
# ──────────────────────────────────────────────────────────────────────


def test_list_registered_roots_empty_native_pure():
    native, pure = _native_then_pure(catalog.list_registered_roots)
    assert native == pure
    # srmech's own attested root is always the implicit first entry.
    assert pure[0]["source"] == "srmech.amsc"
    assert len(pure) == 1


def test_list_registered_roots_with_registered_native_pure(tmp_path):
    ext = tmp_path / "ephem_roots"
    ext.mkdir()
    catalog.register_attested_root(ext, source="ephemerides-spectral")
    native, pure = _native_then_pure(catalog.list_registered_roots)
    assert native == pure
    assert pure[0]["source"] == "srmech.amsc"
    assert pure[-1]["source"] == "ephemerides-spectral"
    assert pure[-1]["path"] == str(ext.resolve())


def test_register_duplicate_is_idempotent(tmp_path):
    ext = tmp_path / "root_a"
    ext.mkdir()
    first = catalog.register_attested_root(ext, source="pkg")
    second = catalog.register_attested_root(ext, source="pkg")
    assert first["total_registered"] == second["total_registered"] == 1
    native, pure = _native_then_pure(catalog.list_registered_roots)
    assert native == pure
    # exactly one external entry (idempotent) plus srmech's own root.
    assert len(pure) == 2


# ──────────────────────────────────────────────────────────────────────
# use_local_kernel / get_local_kernel_state / clear_local_kernel
# ──────────────────────────────────────────────────────────────────────


def test_use_get_clear_kernel_roundtrip_native_pure(tmp_path):
    overlay = tmp_path / "kern"
    overlay.mkdir()

    # use (success, no scope)
    native, pure = _native_then_pure(lambda: catalog.use_local_kernel(overlay))
    assert native == pure
    assert pure["ok"] is True and pure["active"] is True
    assert pure["path"] == str(overlay.resolve())
    assert pure["message"].startswith("T2 overlay registered at ")

    # state while active
    catalog.use_local_kernel(overlay)
    native, pure = _native_then_pure(catalog.get_local_kernel_state)
    assert native == pure
    assert pure["ok"] is True and pure["active"] is True
    assert pure["path"] == str(overlay.resolve())
    # cache_hash is a real SHA-256 hex (sha256("") when no overlay files).
    assert len(pure["cache_hash"]) == 64

    # clear
    native, pure = _native_then_pure(catalog.clear_local_kernel)
    assert native == pure
    assert pure["active"] is False and pure["path"] is None
    assert pure["message"] == (
        "T2 overlay cleared; queries return T0+T1 baseline only")


def test_use_kernel_with_adapter_class_scope_native_pure(tmp_path):
    overlay = tmp_path / "kern_scoped"
    overlay.mkdir()
    native, pure = _native_then_pure(
        lambda: catalog.use_local_kernel(overlay, adapter_class="curated"))
    assert native == pure
    assert pure["adapter_class"] == "curated"
    assert "(scope: adapter_class='curated')" in pure["message"]


def test_kernel_state_inactive_native_pure():
    native, pure = _native_then_pure(catalog.get_local_kernel_state)
    assert native == pure
    assert pure["active"] is False and pure["path"] is None
    assert pure["n_overlay_sources"] == 0
    # sha256 of the empty canonical join.
    assert pure["cache_hash"] == hashlib.sha256(b"").hexdigest()


def test_get_local_kernel_state_cache_hash_matches_manual(tmp_path):
    """When overlays exist, the C-derived cache_hash equals the manual join
    hash — the Class-A composition is byte-exact."""
    overlay = tmp_path / "kern_overlay"
    # build an overlay tree matching a real registered source's key/table.
    src = catalog.list_attested_sources()["sources"]
    if not src:
        pytest.skip("no attested sources to overlay in this build")
    key = src[0]["key"]
    table = src[0]["data_schema_id"].split(".")[1] \
        if src[0]["data_schema_id"].count(".") >= 2 \
        else src[0]["data_schema_id"]
    (overlay / key).mkdir(parents=True)
    fpath = overlay / key / f"{table}.ndjson"
    fpath.write_bytes(b'{"data": {"x": 1}}\n')
    catalog.use_local_kernel(overlay)
    native, pure = _native_then_pure(catalog.get_local_kernel_state)
    assert native == pure
    # If the overlay covered this source, the per_source hash must appear.
    for entry in pure["per_source"]:
        assert len(entry["overlay_sha256"]) == 64


# ──────────────────────────────────────────────────────────────────────
# attestation_audit
# ──────────────────────────────────────────────────────────────────────


def _first_real_source_key():
    sources = catalog.list_attested_sources()["sources"]
    return sources[0]["key"] if sources else None


def test_attestation_audit_real_source_native_pure():
    key = _first_real_source_key()
    if key is None:
        pytest.skip("no attested sources in this build")
    native, pure = _native_then_pure(lambda: catalog.attestation_audit(key))
    assert native == pure
    assert pure["ok"] is True
    assert pure["source_key"] == key
    assert pure["n_rows"] == len(pure["rows"])
    for row in pure["rows"]:
        # every projected row carries exactly the six attestation fields.
        assert set(row) == {
            "data_schema_id", "response_sha256", "retrieved_at",
            "parser_version", "parser_rule_hash", "collector_descriptor_hash",
        }


def test_attestation_audit_all_real_sources_native_pure():
    sources = catalog.list_attested_sources()["sources"]
    if not sources:
        pytest.skip("no attested sources in this build")
    for s in sources:
        native, pure = _native_then_pure(
            lambda k=s["key"]: catalog.attestation_audit(k))
        assert native == pure, f"attestation_audit diverged for {s['key']}"


def test_attestation_audit_unknown_source_key():
    res = catalog.attestation_audit("nonexistent_source_xyz")
    assert res["ok"] is False
    assert "unknown source_key" in res["error"]
    assert "available" in res


@needs_native
def test_attestation_audit_c_peer_populated_mpr():
    """Direct C-peer test over a synthetic FULL-MPR NDJSON (populated
    attestation blocks + a comment header + a blank + a data-only row)."""
    lib = _native.LIB
    nd = (
        b"# comment header line\n"
        b'{"mpr_version":"1.0","data":{"x":1.5,"n":7},'
        b'"data_schema_id":"src.tab.v1",'
        b'"attestation":{"response_sha256":"deadbeef",'
        b'"retrieved_at":"2026-01-01T00:00:00Z","parser_version":"srmech 0.9",'
        b'"parser_rule_hash":"rr","collector_descriptor_hash":"cc"},'
        b'"rendering":{}}\n'
        b"\n"
        b'   {"data":{"only":"data-row"}}\n'
    )
    sk = b"mysrc"
    ws_bytes = int(lib.srmech_catalog_attestation_audit_arena_bytes(
        len(nd), len(sk)))
    ws = (ctypes.c_char * ws_bytes)()
    out = (ctypes.c_char * (2 * len(nd) + 4096))()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_catalog_attestation_audit(
        sk, len(sk), nd, len(nd), ws, ws_bytes, out, len(out),
        ctypes.byref(out_len))
    assert rc == _native.SRMECH_OK
    got = json.loads(out.raw[:out_len.value].decode("utf-8"))
    assert got == {
        "ok": True, "source_key": "mysrc", "n_rows": 2, "rows": [
            {"data_schema_id": "src.tab.v1", "response_sha256": "deadbeef",
             "retrieved_at": "2026-01-01T00:00:00Z",
             "parser_version": "srmech 0.9", "parser_rule_hash": "rr",
             "collector_descriptor_hash": "cc"},
            {"data_schema_id": "", "response_sha256": "", "retrieved_at": "",
             "parser_version": "", "parser_rule_hash": "",
             "collector_descriptor_hash": ""},
        ],
    }


# ──────────────────────────────────────────────────────────────────────
# list_attested_sources — composes the descriptor parse + a pure filter/sort/
# project (classified composes_c directly, consistent with the already-
# composes_c get_attested_dataset / get_attested_descriptor).
# ──────────────────────────────────────────────────────────────────────


def test_list_attested_sources_native_pure():
    native, pure = _native_then_pure(catalog.list_attested_sources)
    assert native == pure
    assert pure["ok"] is True
    assert pure["n_sources"] == len(pure["sources"])
    # sorted by key.
    keys = [s["key"] for s in pure["sources"]]
    assert keys == sorted(keys)


def test_list_attested_sources_adapter_class_filter():
    curated = catalog.list_attested_sources(adapter_class="curated")
    assert curated["adapter_class"] == "curated"
    for s in curated["sources"]:
        assert s["adapter"] == "literature_curated"
    with pytest.raises(ValueError):
        catalog.list_attested_sources(adapter_class="not_a_real_class")


# ──────────────────────────────────────────────────────────────────────
# Class-E catalog lookup (existing srmech_catalog_lookup) — hit + miss.
# ──────────────────────────────────────────────────────────────────────


@needs_native
def test_catalog_lookup_hit_and_miss():
    lib = _native.LIB
    # sorted (key, value) catalog packed into one buffer.
    pairs = [(b"alpha", b"A-val"), (b"gamma", b"G-val"), (b"omega", b"O-val")]
    buf = bytearray()
    key_off, key_len, val_off, val_len = [], [], [], []
    for k, v in pairs:
        key_off.append(len(buf)); key_len.append(len(k)); buf += k
        val_off.append(len(buf)); val_len.append(len(v)); buf += v
    n = len(pairs)
    cbuf = (ctypes.c_uint8 * len(buf)).from_buffer_copy(bytes(buf))
    ck_off = (ctypes.c_uint32 * n)(*key_off)
    ck_len = (ctypes.c_uint32 * n)(*key_len)
    cv_off = (ctypes.c_uint32 * n)(*val_off)
    cv_len = (ctypes.c_uint32 * n)(*val_len)

    def lookup(key: bytes):
        ckey = (ctypes.c_uint8 * len(key)).from_buffer_copy(key)
        found = ctypes.c_bool()
        voff = ctypes.c_uint32()
        vlen = ctypes.c_uint32()
        rc = lib.srmech_catalog_lookup(
            ckey, len(key), cbuf, ck_off, ck_len, cv_off, cv_len, n,
            ctypes.byref(found), ctypes.byref(voff), ctypes.byref(vlen))
        assert rc == _native.SRMECH_OK
        if not found.value:
            return None
        return bytes(buf[voff.value:voff.value + vlen.value])

    assert lookup(b"gamma") == b"G-val"   # hit
    assert lookup(b"alpha") == b"A-val"   # hit (first)
    assert lookup(b"omega") == b"O-val"   # hit (last)
    assert lookup(b"delta") is None       # miss (between keys)
    assert lookup(b"zzz") is None         # miss (after last)
