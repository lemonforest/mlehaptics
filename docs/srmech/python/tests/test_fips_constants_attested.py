"""v0.7.0rc19 — derive-and-assert gate for the attested SHA-256 magic constants.

The HAL constant-attestation discipline (rc19) says: a target-specific magic
constant that we cannot derive from the framework — and historically copied by
hand — must be (a) attested to its source in the .h, and (b) where the value IS
derivable, REGENERATED from first principles and asserted against the committed
table. This test is (b).

It re-derives the FIPS 180-4 round constants K[0..63] and initial hash value
H0[0..7] from first principles — by EXACT INTEGER arithmetic (integer cube /
square root of p<<96 / p<<64 over the first 64 / 8 primes; no float, no ULP
risk) — and asserts them byte-for-byte against:

  * c/src/srmech_sha256_constants.h  (the shared scalar K[64] + H0[8])
  * c/src/srmech_sha256_shani.h      (the packed SHA-NI KP[16][2], decoded)

A single wrong hex digit fails this test on ANY host, at unit-test time. This
is precisely the gate that was missing when rc18 shipped KP[14] as 0x8CC70808
instead of FIPS K[59]=0x8CC70208 — that typo survived the dev box (no SHA-NI)
and only failed on SHA-NI CI. With this test it fails locally, immediately.

FIPS 180-4 §4.2.2 (K) / §5.3.3 (H0): the first 32 bits of the fractional parts
of the cube roots (K) / square roots (H0) of the first N primes.
"""

import re
from pathlib import Path

C_SRC = Path(__file__).resolve().parents[2] / "c" / "src"
_MASK = 0xFFFFFFFF


# ── first-principles derivation (exact integer arithmetic) ────────────


def _first_primes(n: int) -> list[int]:
    ps: list[int] = []
    c = 2
    while len(ps) < n:
        if all(c % p for p in ps if p * p <= c):
            ps.append(c)
        c += 1
    return ps


def _icbrt(n: int) -> int:
    """Exact integer cube root (floor) via integer Newton + correction."""
    if n < 0:
        raise ValueError("icbrt of negative")
    if n == 0:
        return 0
    x = 1 << ((n.bit_length() + 2) // 3)
    while True:
        y = (2 * x + n // (x * x)) // 3
        if y >= x:
            break
        x = y
    while x * x * x > n:
        x -= 1
    while (x + 1) ** 3 <= n:
        x += 1
    return x


def _isqrt(n: int) -> int:
    import math
    return math.isqrt(n)


def _derive_K() -> list[int]:
    # K[i] = top 32 fractional bits of cbrt(p_i) = icbrt(p_i << 96) & mask.
    return [_icbrt(p << 96) & _MASK for p in _first_primes(64)]


def _derive_H0() -> list[int]:
    # H0[i] = top 32 fractional bits of sqrt(p_i) = isqrt(p_i << 64) & mask.
    return [_isqrt(p << 64) & _MASK for p in _first_primes(8)]


# ── parse the committed C headers ─────────────────────────────────────


def _parse_array(header: str, name: str, count: int) -> list[int]:
    text = (C_SRC / header).read_text(encoding="utf-8")
    # slice from `name[...] = {` to the next `};`
    start = text.index(name)
    brace = text.index("{", start)
    end = text.index("};", brace)
    body = text[brace + 1:end]
    vals = [int(h, 16) for h in re.findall(r"0x[0-9a-fA-F]{8}", body)]
    assert len(vals) == count, (
        f"{header}:{name} parsed {len(vals)} values, expected {count}"
    )
    return vals


def _parse_KP() -> list[tuple[int, int]]:
    text = (C_SRC / "srmech_sha256_shani.h").read_text(encoding="utf-8")
    start = text.index("SRMECH_SHA256NI_KP")
    brace = text.index("{", start)
    end = text.index("};", brace)
    body = text[brace + 1:end]
    rows = re.findall(
        r"\{\s*(0x[0-9a-fA-F]{16})ULL\s*,\s*(0x[0-9a-fA-F]{16})ULL\s*\}", body)
    assert len(rows) == 16, f"parsed {len(rows)} KP rows, expected 16"
    return [(int(hi, 16), int(lo, 16)) for hi, lo in rows]


# ── the gate ──────────────────────────────────────────────────────────


def test_fips_K_table_matches_first_principles_derivation():
    """c/src/srmech_sha256_constants.h K[64] == cube-roots-of-primes."""
    assert _parse_array("srmech_sha256_constants.h",
                        "SRMECH_SHA256_K", 64) == _derive_K()


def test_fips_H0_table_matches_first_principles_derivation():
    """c/src/srmech_sha256_constants.h H0[8] == square-roots-of-primes."""
    assert _parse_array("srmech_sha256_constants.h",
                        "SRMECH_SHA256_H0", 8) == _derive_H0()


def test_shani_packed_KP_decodes_to_FIPS_K():
    """The SHA-NI packed KP[16][2] decodes (per _mm_set_epi64x lane order
    [lo_lo, lo_hi, hi_lo, hi_hi] = K[4g..4g+3]) to the derived FIPS K.

    This is the EXACT check that catches the rc18 0x8CC70808→0x8CC70208 typo.
    """
    K = _derive_K()
    kp = _parse_KP()
    decoded: list[int] = []
    for hi, lo in kp:
        decoded += [lo & _MASK, (lo >> 32) & _MASK,
                    hi & _MASK, (hi >> 32) & _MASK]
    assert decoded == K


def test_derivation_self_check_round59():
    """Guard the guard: the derivation itself must yield the post-rc18-fix
    value for K[59] (the constant the typo corrupted)."""
    assert _derive_K()[59] == 0x8CC70208
