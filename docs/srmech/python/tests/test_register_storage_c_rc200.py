"""Register HDC-STORAGE leaves + the mint_vector foundation — pure-vs-native
agreement (v0.9.0rc200; re-pointed at the general register in rc464 `#T1188`).

make_class → C, leaf-batch 6/8 (#887), the heaviest batch: the ONE new
foundational C symbol ``srmech_mint_vector`` (the deterministic RBS-HDC minter,
byte-for-byte mirror of Python ``mint_vector`` — SHA-256(name ‖ u64_be(counter))
chained, truncated to D/8 bytes) lets the 4 HDC-STORAGE leaves compose in C:

    cdr_write         → mint (srmech_mint_vector) the key's vec + record the slot
    cdr_materialize   → bundle (srmech_hdc_bundle) the slot vectors; "__pad__" for
                        even-N; raises on empty
    cdr_read_unbind   → bind-unbind (srmech_hdc_bind) the slot from materialize
    cdr_clean         → nearest-codebook argmax over srmech_hdc_similarity, skip
                        "__pad__", Class-K magnitude tie-break (never abs())

rc464 removed the 16-slot ``SedenionRegister`` these leaves were written for and
re-pointed them at ``CDRegister``, which subsumes it — the register here is
``cd_register(16, namespace="SEDENION", coupling=True, error_correction=True)``,
that class's exact spelling. The mint FOUNDATION below is register-independent
and is unchanged; it is the half of this module that was never about 16 slots.

The EXACT foundation (``mint_vector``) is native == pure BYTE-IDENTICAL. The 4
leaves compose it + the C hdc bind/bundle/similarity, so their read/clean parity
is a DETERMINISTIC-SAME-DECISION contract (the HDC store is fuzzy), NOT byte-
exact. Every check toggles ``_native.HAS_NATIVE`` off to force the pure path and
compares against the (default) native path — so it PASSES (not skips) with the
native lib loaded, and is a no-op-equal (pure == pure) with no lib. numpy-free.
"""
import contextlib
import json
from pathlib import Path

from srmech import _native
from srmech.signal_processing import mint_vector
from srmech.signal_processing._paths import D_MIN
from srmech.cascade.cd_register import (
    CDRegister,
    cdr_write, cdr_materialize, cdr_read_unbind, cdr_clean,
)


@contextlib.contextmanager
def force_pure():
    """Force the whole native stack to the pure Python fallback by dropping
    ``_native.HAS_NATIVE`` for the duration (every dispatch guard + every
    ``has_native_*`` helper reads it at call time)."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved


# ── the FOUNDATION: srmech_mint_vector byte-identical to the pure chain ────────

# Names of varied byte-lengths — including ones whose (len % 64) puts the
# name-tail + 8-byte counter across the 64-byte block boundary (rem+8 in
# {63,64,65,71}) to exercise BOTH finalize branches of the C midstate path.
_MINT_NAMES = [
    "",                       # empty name (name == NULL, name_len == 0)
    "SEDENION:e0",
    "VAL:alpha",
    "__pad__",
    "x" * 55,                 # rem 55 -> tail 63  (< 64: direct finalize)
    "y" * 56,                 # rem 56 -> tail 64  (== 64: one block + finalize)
    "z" * 57,                 # rem 57 -> tail 65  (>= 64: one block + finalize)
    "w" * 63,                 # rem 63 -> tail 71  (>= 64: one block + finalize)
    "q" * 64,                 # exactly one full block, rem 0 -> tail 8
    "k" * 120,                # 120 % 64 == 56 -> tail 64 (full block first)
    "e" * 127,                # 127 % 64 == 63 -> tail 71
    "the quick brown fox jumps over the lazy dog" * 4,   # long multibyte-ish
    "ünïcödé:κλ",             # multi-byte UTF-8 (name encodes via utf-8)
]

# D values (bits, multiple of 8) — one digest (D_MIN), an exact multiple of 32
# bytes (8192 -> 1024), and a NON-multiple of 32 bytes (520 -> 65) so the final
# digest is truncated mid-chain.
_MINT_DS = [D_MIN, 520, 8192]


def test_mint_vector_native_equals_pure_byte_identical():
    for name in _MINT_NAMES:
        for D in _MINT_DS:
            native = mint_vector(name, D=D)
            with force_pure():
                pure = mint_vector(name, D=D)
            assert native == pure, f"mint parity failed: name={name!r} D={D}"
            assert len(native) == D // 8


def test_mint_vector_native_matches_reference_sha_chain():
    """Independent oracle: the mint chain recomputed with stdlib hashlib —
    SHA256(name.utf8 ‖ counter.to_bytes(8,'big')), 8-byte BIG-ENDIAN counter,
    concatenated then truncated to D/8 — must equal the (native) mint_vector."""
    import hashlib
    for name in ("SEDENION:e7", "VAL:gamma", "q" * 63, "ünïcödé:κλ"):
        for D in (D_MIN, 520, 8192):
            n_bytes = D // 8
            out = bytearray()
            counter = 0
            nb = name.encode("utf-8")
            while len(out) < n_bytes:
                out.extend(hashlib.sha256(nb + counter.to_bytes(8, "big")).digest())
                counter += 1
            assert mint_vector(name, D=D) == bytes(out[:n_bytes])


def test_mint_vector_c_wrapper_direct():
    """The low-level wrapper: mint_vector_c(name_bytes, n_bytes) == the public
    mint (native path) — or None when the C peer is absent (no lib)."""
    got = _native.mint_vector_c(b"VAL:delta", 1024)
    if _native.has_native_mint_vector():
        assert got == mint_vector("VAL:delta", D=8192)
        assert got is not None and len(got) == 1024
        # counter-8-BE boundary sanity: n_bytes < 32 takes just the first digest
        import hashlib
        assert _native.mint_vector_c(b"VAL:delta", 5) == \
            hashlib.sha256(b"VAL:delta" + (0).to_bytes(8, "big")).digest()[:5]
    else:
        assert got is None


# ── the 4 STORAGE leaves: native == pure DETERMINISTIC-SAME-DECISION ──────────

def _register():
    r = CDRegister(16, namespace="SEDENION", coupling=True,
                   error_correction=True)
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(10, "gamma")
    r.write(7, "delta", sign=-1)
    return r


def test_register_write_native_equals_pure():
    r = _register()
    slots, codebook = r.slots(), r.codebook
    native = cdr_write(5, "epsilon", r.dim, r.D, r.namespace, codebook, slots)
    with force_pure():
        pure = cdr_write(5, "epsilon", r.dim, r.D, r.namespace, codebook, slots)
    # (None, {slots, codebook}) — the mutate route; byte-identical minted vec
    assert native[0] is None and pure[0] is None
    assert native[1]["slots"] == pure[1]["slots"]
    assert native[1]["codebook"] == pure[1]["codebook"]
    # the new key was minted into the codebook, the slot recorded
    assert 5 in native[1]["slots"] and native[1]["slots"][5] == ("epsilon", 1)
    assert native[1]["codebook"]["epsilon"] == mint_vector("VAL:epsilon", D=r.D)


def test_register_materialize_native_equals_pure():
    r = _register()
    native = cdr_materialize(r.dim, r.D, r.namespace, r.codebook, r.slots())
    with force_pure():
        pure = cdr_materialize(r.dim, r.D, r.namespace, r.codebook, r.slots())
    assert native == pure               # bundle over minted vecs is deterministic
    assert len(native) == r.D // 8


def test_register_materialize_even_n_pads_and_empty_raises():
    # even N (4 slots) triggers the "__pad__" odd-N tie-break mint
    r = _register()
    assert len(r.slots()) % 2 == 0
    materialised = cdr_materialize(r.dim, r.D, r.namespace, r.codebook, r.slots())
    assert len(materialised) == r.D // 8
    # empty register raises (mirrored exactly)
    import pytest
    with pytest.raises(ValueError):
        cdr_materialize(r.dim, r.D, r.namespace, {}, {})


def test_register_read_unbind_then_clean_recovers_each_slot():
    """The read CHAIN (cdr_read_unbind -> cdr_clean) recovers the written
    (key, sign) at every occupied slot — native and pure make the SAME decision."""
    r = _register()
    slots, codebook = r.slots(), r.codebook
    for slot, (key, sign) in slots.items():
        noisy = cdr_read_unbind(slot, r.dim, r.D, r.namespace, codebook, slots)
        with force_pure():
            noisy_pure = cdr_read_unbind(slot, r.dim, r.D, r.namespace, codebook, slots)
        assert noisy == noisy_pure                      # bind-unbind is exact
        got_key, got_sign = cdr_clean(noisy, codebook)
        with force_pure():
            got_key_p, got_sign_p = cdr_clean(noisy, codebook)
        assert (got_key, got_sign) == (got_key_p, got_sign_p)   # same decision
        assert (got_key, got_sign) == (key, sign)               # recovers write


def test_register_read_unbind_empty_register_is_none():
    assert cdr_read_unbind(0, 16, 8192, 'SEDENION', {}, {}) is None
    assert cdr_clean(None, {}) == (None, 1)


def test_register_clean_skips_pad_and_ties_toward_lowest():
    """cdr_clean skips the "__pad__" sentinel and keeps the Class-K magnitude
    tie-break (>= for +sense, > for -sense); an empty/pad-only codebook yields
    the (None, +1) short-circuit."""
    assert cdr_clean(b"\x00" * 1024, {"__pad__": b"\x00" * 1024}) == (None, 1)


# ── round-trip through the class surface (write -> read recovers the key) ──────

def test_register_write_read_round_trip():
    r = CDRegister(16, namespace="SEDENION", coupling=True,
                   error_correction=True)
    writes = {2: ("apple", 1), 6: ("banana", -1), 9: ("cherry", 1),
              14: ("date", -1), 1: ("elder", 1)}
    for slot, (key, sign) in writes.items():
        r.write(slot, key, sign=sign)
    for slot, (key, sign) in writes.items():
        assert r.read(slot) == (key, sign)


# ── ledger / classification sanity ────────────────────────────────────────────

def test_storage_leaves_ledger_classification():
    rows = {
        json.loads(l)["defined_at"]: json.loads(l)
        for l in (Path(__file__).resolve().parent
                  / "rosetta_classification.ndjson").read_text(
                      encoding="utf-8").splitlines() if l.strip()
    }
    base = "srmech.cascade.cd_register."
    for leaf in ("cdr_write", "cdr_materialize", "cdr_read_unbind", "cdr_clean"):
        assert rows[base + leaf]["bucket"] == "composition_of_c"
    # the foundation earned its dedicated C peer -> c_dispatched
    assert rows["srmech.signal_processing.rbs_hdc_instrument.mint_vector"][
        "bucket"] == "c_dispatched"
