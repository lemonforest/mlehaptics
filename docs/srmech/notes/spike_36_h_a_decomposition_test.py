"""Spike #36 — H_a test: does Class M decompose into A-N compositions?

For each of Class M's 4 canonical operations, attempt to construct it
ONLY from other A-N primitive operations (not Class M itself). Verify
functional equivalence against the canonical srmech.amsc.hdc reference
at D in {64, 512, 4096, 32768} bits.

If ALL 4 ops decompose cleanly, Class M's individual operations are
derivable. The H_a verdict then asks whether the composite STRUCTURE
of the 4 ops together has identity beyond the sum of the parts.

Per [[user_stance_identity_not_implementation_discipline]]: implementation
parity at the per-op level does NOT prove identity-collapse. We test
implementation; we record what identity-question remains open.

Reference: srmech.amsc.hdc.{bind, bundle, permute, similarity}.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add srmech to path
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = Path("D:/GitHub/mlehaptics")
SRMECH_PY = PROJECT_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PY))

from srmech.amsc import hdc as M  # Class M canonical reference

# ----------------------------------------------------------------------
# Class I operations (cyclic-group / modular arithmetic).
# Per Spike #30A: Class I IS the cyclic-shift / XOR-as-Z/2 family.
# ----------------------------------------------------------------------

def class_I_z2_add(a_bit: int, b_bit: int) -> int:
    """Class I — Z/2 cyclic addition. a + b mod 2. This IS XOR for bits."""
    return (a_bit + b_bit) % 2


def class_I_cyclic_shift_bit_index(i: int, shift: int, D: int) -> int:
    """Class I — cyclic shift of bit index i by `shift` positions on Z/D."""
    return (i - shift) % D


# ----------------------------------------------------------------------
# Class C operations (streaming iteration).
# Per [[user_stance_1d_t_as_storage_extraction]]: Class C IS the "crank"
# that drives iteration over a stream of elements.
# ----------------------------------------------------------------------

def class_C_stream_sum(stream, init=0):
    """Class C — fold a stream by addition. Returns sum."""
    acc = init
    for x in stream:
        acc = acc + x
    return acc


def class_C_iterate(seq):
    """Class C — yield elements one at a time (the canonical 'next() until
    StopIteration' operation that Spike #30A characterised)."""
    for x in seq:
        yield x


# ----------------------------------------------------------------------
# Class B operations (TLV / byte-canonical layout).
# Per Spike #30A: Class B is fixed-offset record packing; we use it
# for the "for each byte, for each bit" addressing scheme that maps
# the 1D-bit array to a 2D (byte, bit-in-byte) layout.
# ----------------------------------------------------------------------

def class_B_get_bit(buf: bytes, i: int) -> int:
    """Class B — addressable byte storage with bit-within-byte extraction.
    Returns bit i (counting from LSB within byte i//8)."""
    return (buf[i // 8] >> (i % 8)) & 1


def class_B_set_bit(buf: bytearray, i: int, val: int) -> None:
    """Class B — addressable byte storage with bit-within-byte set."""
    if val:
        buf[i // 8] |= (1 << (i % 8))


# ----------------------------------------------------------------------
# Class J operations (prime-factorisation / period; integer arithmetic).
# Per Spike #30A: Class J reduces to integer arithmetic / divisibility /
# threshold-via-integer-division. We use it for the bundle threshold.
# ----------------------------------------------------------------------

def class_J_threshold(count: int, n: int) -> int:
    """Class J — integer-division-based threshold computation.
    For odd n, the bundle majority threshold is (n+1)//2."""
    return (n + 1) // 2  # integer ceiling-division by 2


def class_J_compare_geq(count: int, threshold: int) -> int:
    """Class J — integer comparison (does count >= threshold?). Returns 0/1."""
    return 1 if count >= threshold else 0


# ----------------------------------------------------------------------
# Class N operations (rational-approximation; rational normalisation).
# Per Spike #30A: Class N reduces to I + J (modular + gcd). We use it for
# the similarity-score [-1, 1] normalisation.
# ----------------------------------------------------------------------

def class_N_normalise_to_neg1_plus1(hamming: int, D: int) -> float:
    """Class N — rational normalisation: 1 - 2*hamming/D in [-1, +1].
    This is a rational map from (hamming, D) to a scalar in [-1, 1]."""
    return 1.0 - 2.0 * hamming / D


# ----------------------------------------------------------------------
# Class L operations (graph-Laplacian).
# Not needed for HDC reconstruction, but listed for completeness.
# ----------------------------------------------------------------------

# (no L op required by H_a test)


# ----------------------------------------------------------------------
# Reconstructed HDC operations using ONLY classes other than M.
# ----------------------------------------------------------------------

def bind_via_IxB(a: bytes, b: bytes) -> bytes:
    """bind(a, b) reconstructed as Class I (Z/2 addition) over Class B (byte
    addressable storage), iterated by Class C.

    Decomposition: bind = Class I (Z/2 add) ∘ Class B (bit address) ∘ Class C (iterate over D)
    """
    assert len(a) == len(b) and len(a) > 0
    n = len(a)
    D = n * 8
    out = bytearray(n)
    for i in class_C_iterate(range(D)):  # Class C iteration
        ai = class_B_get_bit(a, i)        # Class B addressing
        bi = class_B_get_bit(b, i)        # Class B addressing
        out_bit = class_I_z2_add(ai, bi)  # Class I Z/2 addition
        class_B_set_bit(out, i, out_bit)  # Class B set
    return bytes(out)


def bundle_via_CxJxB(vectors) -> bytes:
    """bundle(vectors) reconstructed as Class C (iterate vectors, sum) +
    Class J (integer threshold + compare) + Class B (bit addressing).

    Decomposition: bundle = Class C (sum stream) ∘ Class J (threshold-compare)
                              ∘ Class B (per-bit addressing)
    """
    n_vectors = len(vectors)
    assert n_vectors > 0 and (n_vectors & 1) == 1  # odd, per BSC convention
    n_bytes = len(vectors[0])
    assert n_bytes > 0
    D = n_bytes * 8
    threshold = class_J_threshold(0, n_vectors)  # (n+1)//2 via Class J
    out = bytearray(n_bytes)
    for i in class_C_iterate(range(D)):
        # Class C: stream-sum of bit at position i across all vectors
        bit_stream = (class_B_get_bit(v, i) for v in vectors)
        count = class_C_stream_sum(bit_stream)
        # Class J: integer compare against threshold
        result_bit = class_J_compare_geq(count, threshold)
        # Class B: write back
        class_B_set_bit(out, i, result_bit)
    return bytes(out)


def permute_via_IxB(a: bytes, rotate_bits: int) -> bytes:
    """permute(a, k) reconstructed as Class I (cyclic-shift on Z/D) ∘ Class B
    (bit addressing) ∘ Class C (iterate over D).

    Decomposition: permute = Class I (cyclic-shift index map) ∘ Class B (bit
                                addressing) ∘ Class C (iterate)
    """
    n = len(a)
    assert n > 0
    D = n * 8
    out = bytearray(n)
    for i in class_C_iterate(range(D)):
        # Class I: cyclic-shift on Z/D, computing source bit index
        src = class_I_cyclic_shift_bit_index(i, rotate_bits, D)
        # Class B: get bit at source index
        src_bit = class_B_get_bit(a, src)
        # Class B: set bit at destination index i
        class_B_set_bit(out, i, src_bit)
    return bytes(out)


def similarity_via_IxCxJxN(a: bytes, b: bytes) -> float:
    """similarity(a, b) reconstructed as Class I (Z/2 add for Hamming) +
    Class C (stream-sum count) + Class J (popcount per byte) + Class N
    (rational normalise).

    Decomposition: similarity = Class C (sum stream) ∘ Class J (popcount-byte)
                                  ∘ Class I (Z/2 add for XOR) ∘ Class N (rational)
    """
    assert len(a) == len(b) and len(a) > 0
    n = len(a)
    D = n * 8

    def hamming_per_bit_stream():
        for i in range(D):
            ai = class_B_get_bit(a, i)
            bi = class_B_get_bit(b, i)
            # Class I: Z/2 add — this IS the XOR comparison for one bit
            yield class_I_z2_add(ai, bi)

    # Class C: stream-sum to get Hamming distance
    hamming = class_C_stream_sum(hamming_per_bit_stream())
    # Class N: rational normalisation to [-1, +1]
    return class_N_normalise_to_neg1_plus1(hamming, D)


# ----------------------------------------------------------------------
# Equivalence test.
# ----------------------------------------------------------------------

def deterministic_bytes(seed: int, n_bytes: int) -> bytes:
    """Deterministic byte string via a tiny LCG (no random module — kept
    deterministic across runs for MPM reproducibility)."""
    out = bytearray(n_bytes)
    state = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    for i in range(n_bytes):
        state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        out[i] = (state >> 56) & 0xFF
    return bytes(out)


def run_test():
    """Run the H_a decomposition equivalence test."""
    records = []
    test_sizes = [8, 64, 512, 4096]  # n_bytes (D = 64, 512, 4096, 32768 bits)

    for n_bytes in test_sizes:
        D = n_bytes * 8
        # Generate test vectors deterministically
        a = deterministic_bytes(seed=0xA1, n_bytes=n_bytes)
        b = deterministic_bytes(seed=0xB2, n_bytes=n_bytes)
        c = deterministic_bytes(seed=0xC3, n_bytes=n_bytes)
        d = deterministic_bytes(seed=0xD4, n_bytes=n_bytes)
        e = deterministic_bytes(seed=0xE5, n_bytes=n_bytes)

        # ----- bind test -----
        ref_bind = M.bind(a, b)
        rec_bind = bind_via_IxB(a, b)
        bind_match = (ref_bind == rec_bind)
        records.append({
            "op": "bind",
            "n_bytes": n_bytes,
            "D_bits": D,
            "match": bind_match,
            "decomposition": "Class I (Z/2 add) ∘ Class B (bit addr) ∘ Class C (iterate)",
            "ref_first_8_bytes_hex": ref_bind[:8].hex(),
            "rec_first_8_bytes_hex": rec_bind[:8].hex(),
        })

        # ----- bundle test (n_vectors = 5, odd) -----
        vectors = [a, b, c, d, e]
        ref_bundle = M.bundle(vectors)
        rec_bundle = bundle_via_CxJxB(vectors)
        bundle_match = (ref_bundle == rec_bundle)
        records.append({
            "op": "bundle",
            "n_bytes": n_bytes,
            "D_bits": D,
            "n_vectors": 5,
            "match": bundle_match,
            "decomposition": "Class C (stream-sum) ∘ Class J (threshold-compare) ∘ Class B (bit addr)",
            "ref_first_8_bytes_hex": ref_bundle[:8].hex(),
            "rec_first_8_bytes_hex": rec_bundle[:8].hex(),
        })

        # ----- permute test (rotate_bits = 13, prime to test corners) -----
        for rotate_bits in [0, 1, 13, D // 3, D - 1, D, D + 7, -7, -D, -D - 13]:
            ref_permute = M.permute(a, rotate_bits)
            rec_permute = permute_via_IxB(a, rotate_bits)
            permute_match = (ref_permute == rec_permute)
            records.append({
                "op": "permute",
                "n_bytes": n_bytes,
                "D_bits": D,
                "rotate_bits": rotate_bits,
                "match": permute_match,
                "decomposition": "Class I (cyclic-shift Z/D) ∘ Class B (bit addr) ∘ Class C (iterate)",
                "ref_first_8_bytes_hex": ref_permute[:8].hex(),
                "rec_first_8_bytes_hex": rec_permute[:8].hex(),
            })

        # ----- similarity test -----
        ref_sim = M.similarity(a, b)
        rec_sim = similarity_via_IxCxJxN(a, b)
        sim_diff = abs(ref_sim - rec_sim)
        sim_match = (sim_diff < 1e-12)
        records.append({
            "op": "similarity",
            "n_bytes": n_bytes,
            "D_bits": D,
            "match": sim_match,
            "decomposition": "Class C (sum) ∘ Class J (popcount) ∘ Class I (Z/2 add) ∘ Class N (rational)",
            "ref_value": ref_sim,
            "rec_value": rec_sim,
            "abs_diff": sim_diff,
        })

        # ----- bind self-inverse algebraic identity (independent of decomposition) -----
        # bind(a, bind(a, b)) == b — this is Z/2 self-inverse, an I-level identity
        rec_self_inv = bind_via_IxB(a, bind_via_IxB(a, b))
        records.append({
            "op": "bind_self_inverse_identity",
            "n_bytes": n_bytes,
            "D_bits": D,
            "match": (rec_self_inv == b),
            "note": "Algebraic identity bind(a, bind(a, b)) = b verified with I+B+C decomposition",
        })

    return records


def main():
    records = run_test()
    ndjson_path = HERE / "h_a_decomposition_per_op.ndjson"
    with open(ndjson_path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    n_total = len(records)
    n_match = sum(1 for r in records if r["match"])
    print(f"H_a decomposition test: {n_match}/{n_total} ops match reference")
    print(f"NDJSON written: {ndjson_path}")

    # Per-op verdict summary
    by_op = {}
    for r in records:
        by_op.setdefault(r["op"], []).append(r["match"])

    print("\nPer-op verdicts:")
    for op, matches in by_op.items():
        all_match = all(matches)
        n = len(matches)
        verdict = "DECOMPOSES" if all_match else "MISMATCH"
        print(f"  {op:35s}: {sum(matches)}/{n}  {verdict}")

    if n_match == n_total:
        print("\nH_a verdict (implementation level): ALL 4 ops decompose cleanly into A-N compositions.")
        print("Class M's individual operations are derivable from other classes.")
        print("Identity question (does the COMPOSITE structure carry identity beyond parts?)")
        print("remains open — H_a does not collapse on implementation parity alone.")
    else:
        print(f"\nH_a verdict: PARTIAL — {n_match}/{n_total} ops match; investigate failures.")


if __name__ == "__main__":
    main()
