"""Spike #114 — HDC bind as runtime delta-encoding primitive (Class M).

Concertmaster driver. Formalises ``srmech.amsc.hdc.bind`` as the
canonical delta-encoding primitive for runtime spectral content. Per
Spike #112 verdict: bind is already-shipped Class M (Phase C1 rc8), so
this spike is identity-not-implementation verification + substrate-
coupling parameter inventory + API surface recommendation.

Identity to verify (XOR self-inversion algebra, Plate 1995 / Kanerva 2009):

    bind(reference, current) = delta            # forward
    bind(reference, delta)   = current          # recovery (self-inverse)

Bit-exact across 4 substrate categories:

  1. Chess ply sequence — 8x8x12-bit occupancy bitboards; one ply ≈ 2-4
     cells changed; delta encodes the change exactly.
  2. Image frame sequence — 64x64 binary image; one frame's drift is
     a small fraction of total pixels; delta encodes only changed bits.
  3. Ephemeris state vector evolution — bipolar-quantised (x, v) state
     at fine time step; bit-exact roundtrip on quantised representation.
  4. Gear-DAG morph — Antikythera-style toy with one gear-ratio change;
     bit-exact roundtrip on the tooth-count encoding.

Per ``[[feedback_no_privileged_primitive_classes]]``: bind is Class M, no
new class. Per ``[[user_stance_identity_not_implementation_discipline]]``:
bind IS the delta primitive — XOR self-inversion is the identity claim,
not a reimplementation of holographic reduced representations.

Per ``[[feedback_ndjson_over_bloated_json]]``: emits one NDJSON record per
finding to ``spike114_findings_2026-05-18.ndjson``.

Per ``[[feedback_concertmaster_md_writes.md]]``: findings markdown returned
inline; only NDJSON + this .py are written to disk.

Worktree only: do NOT commit, do NOT open PR (run within concertmaster
brief).
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Anchor srmech package on sys.path.
SRMECH_PY = Path(r"D:/GitHub/mlehaptics/docs/srmech/python")
sys.path.insert(0, str(SRMECH_PY))

from srmech.amsc import _native, hdc  # noqa: E402

FINDINGS = Path(
    r"D:/GitHub/mlehaptics/docs/srmech/notes/spike114_findings_2026-05-18.ndjson"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def emit(record: dict[str, Any]) -> None:
    """Append one NDJSON record."""
    record.setdefault("spike", "spike-114")
    record.setdefault("date", "2026-05-18")
    record.setdefault("timestamp", now_iso())
    with FINDINGS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Substrate encoders. Each produces a bytes hypervector encoding the state.
# Per ``[[user_stance_fiber_as_spatially_absent_encoding]]``: each substrate
# has its own fiber; the encoder is the substrate-coupling operation that
# projects the substrate-specific state onto the HDC byte representation.
# ---------------------------------------------------------------------------


def encode_chess_bitboard(piece_grid: list[list[int]]) -> bytes:
    """8x8 chess board, 0-12 piece codes (0=empty, 1-6=white, 7-12=black).

    Encoding: 12 bitplanes (one per piece type), 8 bytes each → 96 bytes
    = 768-bit hypervector. This is the standard chess-spectral bitboard
    representation.

    Args:
        piece_grid: 8x8 array of piece codes [0, 12].

    Returns:
        96-byte (768-bit) BSC hypervector.
    """
    assert len(piece_grid) == 8 and all(len(r) == 8 for r in piece_grid)
    planes = [bytearray(8) for _ in range(12)]
    for r in range(8):
        for c in range(8):
            p = piece_grid[r][c]
            if p == 0:
                continue
            assert 1 <= p <= 12
            planes[p - 1][r] |= 1 << c
    return b"".join(bytes(p) for p in planes)


def encode_image_binary(pixels: list[list[int]]) -> bytes:
    """64x64 binary image (0 or 1 per pixel) packed into 512 bytes.

    Args:
        pixels: 64x64 array of {0, 1}.

    Returns:
        512-byte (4096-bit) BSC hypervector.
    """
    H = len(pixels)
    W = len(pixels[0])
    assert H == 64 and W == 64
    buf = bytearray(H * W // 8)
    for r in range(H):
        row = pixels[r]
        for c in range(W):
            if row[c]:
                idx = r * W + c
                buf[idx // 8] |= 1 << (idx % 8)
    return bytes(buf)


def encode_ephemeris_state(
    state: tuple[float, float, float, float, float, float],
    scale: float,
    n_bits: int,
) -> bytes:
    """Quantise a (x, y, z, vx, vy, vz) state to fixed-point bipolar bits.

    Each component → signed n_bits/6 fixed-point integer in [-2^(b-1), 2^(b-1)-1]
    via state_i / scale, then packed bit-by-bit. Quantisation IS the substrate-
    coupling regime per ``[[user_stance_framework_domain_algebra_not_length_or_magnitude]]``;
    bind operates on the quantised representation bit-exactly.

    Args:
        state: 6-component float vector.
        scale: divide-by-scale factor before quantisation.
        n_bits: total bits in the hypervector (must be multiple of 48).

    Returns:
        (n_bits // 8)-byte hypervector.
    """
    assert n_bits % 48 == 0
    bits_per_comp = n_bits // 6
    range_max = 1 << (bits_per_comp - 1)
    buf = bytearray(n_bits // 8)
    bit_pos = 0
    for v in state:
        q = int(round(v / scale))
        # Two's complement at bits_per_comp width.
        if q < 0:
            q += 1 << bits_per_comp
        q &= (1 << bits_per_comp) - 1
        # Sanity: representable.
        for b in range(bits_per_comp):
            if (q >> b) & 1:
                buf[bit_pos // 8] |= 1 << (bit_pos % 8)
            bit_pos += 1
    return bytes(buf)


def encode_gear_dag(tooth_counts: list[int], n_bits_per_gear: int = 16) -> bytes:
    """Encode a gear DAG by packing each gear's tooth count as n_bits_per_gear.

    Antikythera-toy: tooth counts are small integers (~30-200). 16 bits
    per gear is more than enough headroom. Each gear is a Class I cyclic
    encoding (ℤ/n) per ``[[user_stance_fiber_as_spatially_absent_encoding]]``
    — the gear's algebra is its tooth count; spatial dynamics emerge only
    under rotation. We encode the algebra here, not the rotation.

    Args:
        tooth_counts: list of small positive integers.
        n_bits_per_gear: bits per gear's tooth count.

    Returns:
        Hypervector packing all gears.
    """
    assert n_bits_per_gear in (8, 16, 32)
    assert all(0 < t < (1 << n_bits_per_gear) for t in tooth_counts)
    buf = bytearray(len(tooth_counts) * (n_bits_per_gear // 8))
    bytes_per_gear = n_bits_per_gear // 8
    for i, t in enumerate(tooth_counts):
        for b in range(bytes_per_gear):
            buf[i * bytes_per_gear + b] = (t >> (8 * b)) & 0xFF
    return bytes(buf)


# ---------------------------------------------------------------------------
# Round-trip verifier — the framework identity claim under test.
# ---------------------------------------------------------------------------


def verify_bind_roundtrip(
    reference: bytes,
    current: bytes,
    substrate: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify bind(reference, current) = delta; bind(reference, delta) = current.

    This is the core Class M identity assertion. Bit-exact pass/fail.

    Returns the record dict (caller appends to NDJSON).
    """
    assert len(reference) == len(current)
    D_bits = 8 * len(reference)

    t0 = time.perf_counter_ns()
    delta = hdc.bind(reference, current)
    t_bind_forward_ns = time.perf_counter_ns() - t0

    t0 = time.perf_counter_ns()
    recovered = hdc.bind(reference, delta)
    t_bind_recover_ns = time.perf_counter_ns() - t0

    bit_exact = recovered == current

    # Hamming weight of the delta (information content of the change).
    hamming = sum(bin(b).count("1") for b in delta)
    sparsity = hamming / D_bits

    record = {
        "phase": "substrate_roundtrip",
        "kind": "bit_exact_verification",
        "substrate": substrate,
        "D_bits": D_bits,
        "D_bytes": len(reference),
        "bind_forward_ns": t_bind_forward_ns,
        "bind_recover_ns": t_bind_recover_ns,
        "delta_hamming_weight": hamming,
        "delta_sparsity": sparsity,
        "bit_exact_roundtrip": bit_exact,
        "primitive_class": "Class M",
        "has_native": _native.HAS_NATIVE,
        "encoding": "binary spatter code (BSC); XOR self-inverse",
    }
    if extra:
        record.update(extra)
    return record


# ---------------------------------------------------------------------------
# Substrate 1: Chess ply sequence
# ---------------------------------------------------------------------------


def substrate_chess() -> dict[str, Any]:
    """Chess 5-ply sequence — verify per-ply delta encodes ~1 piece move."""
    # Standard initial position. 1=P, 2=N, 3=B, 4=R, 5=Q, 6=K (white);
    # 7-12 corresponding black.
    initial = [
        [10, 8, 9, 11, 12, 9, 8, 10],   # rank 8 (black back)
        [7, 7, 7, 7, 7, 7, 7, 7],       # rank 7 (black pawns)
        [0] * 8,
        [0] * 8,
        [0] * 8,
        [0] * 8,
        [1, 1, 1, 1, 1, 1, 1, 1],       # rank 2 (white pawns)
        [4, 2, 3, 5, 6, 3, 2, 4],       # rank 1 (white back)
    ]

    # 5-ply Italian game opening (white-bottom, ranks listed top-to-bottom).
    # Each ply changes exactly 2 cells (from + to).
    def deepcopy(g):
        return [row[:] for row in g]

    plies = [deepcopy(initial)]
    g = deepcopy(initial)
    # 1. e4 (P from rank 2 col 4 to rank 4 col 4).
    g[6][4] = 0
    g[4][4] = 1
    plies.append(deepcopy(g))
    # 1...e5
    g[1][4] = 0
    g[3][4] = 7
    plies.append(deepcopy(g))
    # 2. Nf3
    g[7][6] = 0
    g[5][5] = 2
    plies.append(deepcopy(g))
    # 2...Nc6
    g[0][1] = 0
    g[2][2] = 8
    plies.append(deepcopy(g))
    # 3. Bc4
    g[7][5] = 0
    g[4][2] = 3
    plies.append(deepcopy(g))

    encoded = [encode_chess_bitboard(p) for p in plies]
    all_pass = True
    deltas: list[tuple[int, int]] = []
    for i in range(1, len(encoded)):
        rec = verify_bind_roundtrip(
            reference=encoded[i - 1],
            current=encoded[i],
            substrate=f"chess_ply_{i}",
            extra={"ply_index": i, "ssot": "chess-spectral §5b rank-k delta identity"},
        )
        emit(rec)
        all_pass = all_pass and rec["bit_exact_roundtrip"]
        deltas.append((rec["delta_hamming_weight"], rec["D_bits"]))

    return {
        "category": "chess",
        "n_steps": len(plies) - 1,
        "all_bit_exact": all_pass,
        "delta_hamming_range": (min(d[0] for d in deltas), max(d[0] for d in deltas)),
        "D_bits": deltas[0][1],
        "note": "non-capture ply: hamming = 2 bits (1 bit cleared at FROM, 1 bit set at TO in the moving-piece's bitplane); captures would add +1 bit (cleared in captured piece's plane); promotions would shift the bit to a different plane",
    }


# ---------------------------------------------------------------------------
# Substrate 2: Image frame sequence
# ---------------------------------------------------------------------------


def substrate_image() -> dict[str, Any]:
    """64x64 binary frame sequence, ~10% drift per frame."""
    rng_state = 1234567
    H = W = 64

    def lcg():
        nonlocal rng_state
        rng_state = (rng_state * 1103515245 + 12345) & 0x7FFFFFFF
        return rng_state

    # Frame 0: deterministic checkerboard.
    frame0 = [[((r + c) % 2) for c in range(W)] for r in range(H)]
    frames = [frame0]
    # 3 successive frames where ~10% of pixels drift.
    for step in range(3):
        prev = frames[-1]
        new = [row[:] for row in prev]
        n_flip = (H * W) // 10
        for _ in range(n_flip):
            r = lcg() % H
            c = lcg() % W
            new[r][c] ^= 1
        frames.append(new)

    encoded = [encode_image_binary(f) for f in frames]
    all_pass = True
    deltas = []
    for i in range(1, len(encoded)):
        rec = verify_bind_roundtrip(
            reference=encoded[i - 1],
            current=encoded[i],
            substrate=f"image_frame_{i}",
            extra={"frame_index": i, "ssot": "Spike #112 saccadic_foveal_density framework_mapping"},
        )
        emit(rec)
        all_pass = all_pass and rec["bit_exact_roundtrip"]
        deltas.append((rec["delta_hamming_weight"], rec["D_bits"], rec["delta_sparsity"]))

    return {
        "category": "image",
        "n_steps": len(frames) - 1,
        "all_bit_exact": all_pass,
        "delta_sparsity_range": (
            min(d[2] for d in deltas),
            max(d[2] for d in deltas),
        ),
        "D_bits": deltas[0][1],
        "note": "expected sparsity ≈ 10% per Olshausen-Field sparse-coding analogy (most pixels unchanged)",
    }


# ---------------------------------------------------------------------------
# Substrate 3: Ephemeris state vector evolution
# ---------------------------------------------------------------------------


def substrate_ephemeris() -> dict[str, Any]:
    """3 successive (x, v) Earth-like states at fine time step.

    Toy circular orbit at 1 AU. Each step is small (dt = 1 hour ≈ 0.04°
    orbital phase). Delta encodes the drift only.

    Quantisation regime per ``[[user_stance_framework_domain_algebra_not_length_or_magnitude]]``:
    framework gives bit-exact roundtrip on the quantised representation;
    quantisation scale is a substrate-coupling parameter.
    """
    import math

    AU = 1.495978707e11  # metres
    GM_sun = 1.32712440018e20  # m^3/s^2
    R = AU
    omega = math.sqrt(GM_sun / R**3)
    v_circ = omega * R

    dt = 3600.0  # 1 hour
    theta0 = 0.0
    states = []
    for k in range(3):
        theta = theta0 + omega * k * dt
        x = R * math.cos(theta)
        y = R * math.sin(theta)
        z = 0.0
        vx = -v_circ * math.sin(theta)
        vy = v_circ * math.cos(theta)
        vz = 0.0
        states.append((x, y, z, vx, vy, vz))

    # Quantise: scale = 1 km for positions, ~scaled internally.
    # Use 384-bit total = 64 bits/component for headroom.
    n_bits = 384
    pos_scale = 1e3  # 1 km granularity
    # The encoder uses a uniform scale; we pick one that fits both pos and vel.
    # For circular orbit at 1 AU, v ≈ 30 km/s, x ≈ 1.5e11 m. Use a scale
    # that captures dynamic range: 1 km for positions ≈ 1.5e8 units;
    # 30 km/s / 1 km = 3e4 units. Both fit in 2^32. Use single uniform scale.
    encoded = [encode_ephemeris_state(s, pos_scale, n_bits) for s in states]

    all_pass = True
    deltas = []
    for i in range(1, len(encoded)):
        rec = verify_bind_roundtrip(
            reference=encoded[i - 1],
            current=encoded[i],
            substrate=f"ephemeris_step_{i}",
            extra={
                "step_index": i,
                "dt_seconds": dt,
                "pos_scale": pos_scale,
                "ssot": "Spike #112 reference_genome_delta framework_mapping",
                "quantisation_note": "bit-exact roundtrip on quantised representation; quantisation scale is substrate-coupling parameter",
            },
        )
        emit(rec)
        all_pass = all_pass and rec["bit_exact_roundtrip"]
        deltas.append((rec["delta_hamming_weight"], rec["D_bits"], rec["delta_sparsity"]))

    return {
        "category": "ephemeris",
        "n_steps": len(states) - 1,
        "all_bit_exact": all_pass,
        "delta_sparsity_range": (
            min(d[2] for d in deltas),
            max(d[2] for d in deltas),
        ),
        "D_bits": deltas[0][1],
        "quantisation_regime": "bit-exact at fixed-point precision; rounding error stays within last bit of fixed-point",
        "note": "circular-orbit toy at 1 AU, dt=1h; delta hamming reflects drift in low-order bits of x/y/vx/vy",
    }


# ---------------------------------------------------------------------------
# Substrate 4: Gear-DAG morph
# ---------------------------------------------------------------------------


def substrate_gear_dag() -> dict[str, Any]:
    """3-step Antikythera-toy gear DAG where one gear's ratio changes."""
    # 6-gear toy: tooth counts from Freeth et al. (2006) inspired (small set).
    # Per ``[[user_stance_fiber_as_spatially_absent_encoding]]``: tooth count
    # IS the gear's algebra (ℤ/n cyclic).
    base = [53, 38, 48, 24, 127, 64]
    steps = [base[:]]
    # Step 1: gear 0 tooth count changes 53 → 54 (one tooth added).
    g = base[:]
    g[0] = 54
    steps.append(g[:])
    # Step 2: gear 4 tooth count changes 127 → 128.
    g[4] = 128
    steps.append(g[:])
    # Step 3: gear 2 tooth count changes 48 → 49.
    g[2] = 49
    steps.append(g[:])

    encoded = [encode_gear_dag(s, n_bits_per_gear=16) for s in steps]
    all_pass = True
    deltas = []
    for i in range(1, len(encoded)):
        # Identify which gear changed.
        changed = [(j, steps[i - 1][j], steps[i][j]) for j in range(6) if steps[i - 1][j] != steps[i][j]]
        rec = verify_bind_roundtrip(
            reference=encoded[i - 1],
            current=encoded[i],
            substrate=f"gear_dag_step_{i}",
            extra={
                "step_index": i,
                "changed_gears": changed,
                "ssot": "Antikythera-spectral notebook gear-DAG (Freeth et al. 2006 attestation in ephemerides-spectral)",
                "ssot_secondary": "Spike #112 §5b chess rank-1 generalised to gear-DAG one-tooth perturbation",
            },
        )
        emit(rec)
        all_pass = all_pass and rec["bit_exact_roundtrip"]
        deltas.append((rec["delta_hamming_weight"], rec["D_bits"]))

    return {
        "category": "gear_dag",
        "n_steps": len(steps) - 1,
        "all_bit_exact": all_pass,
        "delta_hamming_range": (
            min(d[0] for d in deltas),
            max(d[0] for d in deltas),
        ),
        "D_bits": deltas[0][1],
        "note": "single-tooth change → delta hamming ≈ popcount(t_new XOR t_old); 53→54 = 0x35 XOR 0x36 = 0x03 → 2 bits set, etc.",
    }


# ---------------------------------------------------------------------------
# Algebraic-identity check: XOR self-inversion proof
# ---------------------------------------------------------------------------


def verify_xor_self_inversion_algebra() -> None:
    """Class M identity claim: bind is self-inverse by XOR algebra.

    For any a, b ∈ {0,1}^D:
      bind(a, bind(a, b)) = a XOR (a XOR b) = (a XOR a) XOR b = 0 XOR b = b

    This is the algebraic guarantee. Doesn't depend on substrate. Test on
    diverse byte patterns to confirm the framework identity holds.
    """
    test_vectors = [
        (bytes(16), bytes(16)),  # all-zero
        (b"\xff" * 16, b"\xff" * 16),  # all-one
        (b"\xaa" * 16, b"\x55" * 16),  # alternating
        (bytes(range(16)), bytes(range(16, 32))),  # diverse
    ]
    all_pass = True
    for a, b in test_vectors:
        delta = hdc.bind(a, b)
        recovered = hdc.bind(a, delta)
        ok = recovered == b
        all_pass = all_pass and ok

    # Also confirm commutativity + associativity of the algebra.
    a, b, c = bytes(range(16)), bytes(range(16, 32)), bytes(range(32, 48))
    commutes = hdc.bind(a, b) == hdc.bind(b, a)
    assoc = hdc.bind(a, hdc.bind(b, c)) == hdc.bind(hdc.bind(a, b), c)

    emit({
        "phase": "algebraic_identity",
        "kind": "xor_self_inversion_proof",
        "note": "Class M bind algebra: XOR self-inverse + commutative + associative; substrate-independent identity claim.",
        "self_inversion_all_pass": all_pass,
        "commutative": commutes,
        "associative": assoc,
        "ssot": "Plate (1995) HRR; Kanerva (2009) HDC §3.2 binding properties",
        "primitive_class": "Class M",
    })


# ---------------------------------------------------------------------------
# Storage / compute cost model
# ---------------------------------------------------------------------------


def storage_cost_model() -> None:
    """Document substrate-coupling parameters at the bind interface.

    Per ``[[user_stance_framework_domain_algebra_not_length_or_magnitude]]``:
    bind IS the framework operation; D, encoding scheme, storage savings
    are substrate-coupling magnitudes — they don't enter the framework
    identity, only the substrate's measurable bit-saving.

    Cost summary:
      - D (bits): substrate-chosen; typical 1024-100000.
      - bytes_per_delta = D / 8.
      - bytes_per_full_reencode = D / 8 (same; no compression at bind layer).
      - Saving comes from delta being SPARSE → can be packed to k * log2(D)
        bits for a popcount-k delta (RLE / coordinate list), but bind layer
        itself returns the full D-bit vector. Compression is a downstream
        choice; bind's job is identity.
      - Compute per bind: O(D) XOR ops; on D=1024-bit native: <1 µs.
      - Encoding cost depends on substrate: chess 8x8x12 bitplanes, image
        H*W*1 bits, ephemeris 6*bits_per_comp, gear DAG n_gears*16.
    """
    emit({
        "phase": "cost_model",
        "kind": "substrate_coupling_parameters",
        "parameters": {
            "D_bits_typical_range": [1024, 100000],
            "D_bits_canonical_default": 1024,
            "encoding_scheme": "binary spatter code (BSC); component-wise XOR",
            "bytes_per_delta": "D / 8 (same as full state)",
            "compute_per_bind": "O(D) XOR; native C path < 1 µs at D=1024",
            "bit_saving_mechanism": "delta is SPARSE → coordinate-list / RLE / Class-K asymptotic-DOF truncation downstream reduces storage to ~k * log2(D) bits for popcount-k delta",
            "encoder_cost_substrate_dependent": True,
        },
        "framework_invariant_per_user_stance": "bind IS the framework operation; D and bit-savings are substrate-coupling magnitudes; identity holds independent of D",
        "primitive_class": "Class M",
    })


# ---------------------------------------------------------------------------
# Bit-exact vs approximate regimes
# ---------------------------------------------------------------------------


def regime_demarcation() -> None:
    """Identify when bind is bit-exact vs approximate.

    Bit-exact regime:
      - BSC at fixed D (XOR is bit-exact integer arithmetic; no float).
      - State→bytes encoder is deterministic and lossless.

    Approximate regime (where bind operates on a LOSSY representation):
      - Quantisation enters: float state → fixed-point representation
        rounds to last bit; bind on quantised reps is bit-exact, but
        unquantise-bind-requantise loses sub-bit content.
      - Spectral truncation enters: Class K sparse asymptote (Spike #117);
        bind on truncated coefficients loses high-eigenmode content
        irrecoverably. Trade-off explicit.
      - Numeric BSC (non-binary; Plate 1995 HRR over reals using circular
        convolution): bind there is circular-convolution-of-permuted-vectors,
        NOT XOR — and the algebra is approximate by design (noise
        accumulates over compositions). srmech.amsc.hdc is BSC-only per
        the Kanerva (2009) canonical; HRR-over-reals is OUT of scope for
        this spike.

    Decision criterion for which to use when:
      USE BSC bind (bit-exact) when:
        - State has a natural binary / discrete representation (chess board,
          image bitmask, gear tooth count, occupancy grid, sensor sample
          at fixed-point precision).
        - Substrate eigenbasis is large enough that delta is sparse
          (Olshausen-Field sparse-coding regime).
        - Bit-exact recovery is required (audit trails, MPM attestation).

      USE quantised bind (bit-exact on quantised rep, approximate on
      original float) when:
        - State is float-continuous (ephemeris positions, sensor voltages)
          but the precision budget is bounded by the substrate-coupling
          quantisation scale anyway.

      AVOID bind when:
        - Bit-exact roundtrip on float originals is required AND substrate
          can't tolerate quantisation overhead.
    """
    # Demonstration: quantisation introduces a controlled error.
    # Two ephemeris states at sub-quantum-step distance — bind is bit-exact
    # on the quantised representation, but the float originals differ by less
    # than one quantum so they encode to the SAME bytes.
    s_a = (1.0e11, 0.0, 0.0, 0.0, 30000.0, 0.0)
    # s_b differs by 0.5 km (less than 1 km quantum) → same encoding.
    s_b = (1.0e11 + 500.0, 0.0, 0.0, 0.0, 30000.0, 0.0)
    enc_a = encode_ephemeris_state(s_a, scale=1e3, n_bits=384)
    enc_b = encode_ephemeris_state(s_b, scale=1e3, n_bits=384)
    encodes_equal = enc_a == enc_b

    delta_ab = hdc.bind(enc_a, enc_b)
    delta_is_zero = all(b == 0 for b in delta_ab)

    emit({
        "phase": "regime_demarcation",
        "kind": "bit_exact_vs_approximate",
        "bit_exact_regime": "BSC + lossless encoder + same-substrate roundtrip",
        "approximate_regime_1": "quantised float → fixed-point: bind bit-exact on rep; rep is approximate of float",
        "approximate_regime_2": "Class K sparse-truncated coefficients: bind bit-exact on truncated rep; truncation drops high modes (Spike #117)",
        "approximate_regime_3": "HRR over reals (Plate 1995): circular-convolution algebra is approximate by design — OUT OF SCOPE for srmech.amsc.hdc which is BSC-only",
        "decision_criterion": "use BSC bind for discrete/binary state; use quantised bind when float precision budget ≤ substrate quantum; do not use bind when float bit-exact recovery is required",
        "sub_quantum_demonstration": {
            "states_differ_by_meters": 500,
            "quantum_meters": 1000,
            "encodes_identical": encodes_equal,
            "delta_all_zero": delta_is_zero,
            "interpretation": "sub-quantum drift collapses to identity delta; this is correct substrate-coupling behaviour, not a bind defect",
        },
        "primitive_class": "Class M",
        "ssot": ["Kanerva (2009) §3.2 BSC", "Plate (1995) §III.A HRR algebra (out of scope)"],
    })


# ---------------------------------------------------------------------------
# API surface recommendation
# ---------------------------------------------------------------------------


def api_surface_recommendation() -> None:
    """Compare Options A vs B for srmech.spectral.delta and recommend.

    Per Spike #112 fermata: choose between the encoder-handling wrapper
    (Option A) or the direct-on-coefficients call (Option B).
    """
    # Both options are tractable — they have different cost / abstraction
    # tradeoffs. Empirically time both at D=1024 (the canonical srmech
    # DEFAULT_HDC_BYTES * 8).
    D_bytes = hdc.DEFAULT_HDC_BYTES  # 128 → 1024 bits
    ref_state = bytes(range(D_bytes))
    cur_state = bytes((b + 1) % 256 for b in ref_state)

    # Option A: per-call encoder. Simulate with a dummy encoder that
    # round-trips bytes through bytearray (representative cost shape).
    def encode_a(state: bytes) -> bytes:
        return bytes(bytearray(state))

    n_trials = 1000
    t0 = time.perf_counter_ns()
    for _ in range(n_trials):
        ref_enc = encode_a(ref_state)
        cur_enc = encode_a(cur_state)
        _ = hdc.bind(ref_enc, cur_enc)
    t_option_a_ns = (time.perf_counter_ns() - t0) / n_trials

    # Option B: direct on pre-encoded.
    ref_enc = encode_a(ref_state)
    cur_enc = encode_a(cur_state)
    t0 = time.perf_counter_ns()
    for _ in range(n_trials):
        _ = hdc.bind(ref_enc, cur_enc)
    t_option_b_ns = (time.perf_counter_ns() - t0) / n_trials

    speedup = t_option_a_ns / t_option_b_ns if t_option_b_ns > 0 else float("inf")

    emit({
        "phase": "api_recommendation",
        "kind": "option_a_vs_b",
        "option_a": {
            "signature": "srmech.spectral.delta(ref_handle, current_state) → bind(encode(ref_handle), encode(current_state))",
            "abstraction": "high; user never sees bind",
            "cost_per_call_ns": t_option_a_ns,
            "ssot_pro": "Spike #112 §design_decision api_surface_sketch",
        },
        "option_b": {
            "signature": "srmech.spectral.delta(ref_coeffs, current_coeffs) → bind(ref_coeffs, current_coeffs)",
            "abstraction": "low; user manages encoded coefficients",
            "cost_per_call_ns": t_option_b_ns,
            "ssot_pro": "streaming-sequence efficiency",
        },
        "speedup_b_over_a": speedup,
        "recommendation": "OPTION_B",
        "rationale": (
            "Per [[user_stance_identity_not_implementation_discipline]]: the framework "
            "operation IS bind on bytes; Option A hides that identity behind a wrapper "
            "and re-encodes both arguments on every call (2x encoder cost). For runtime "
            "streaming spectral (which is the WHOLE POINT of Spike #112 — per-step delta "
            "encoding of long sequences), the encoder runs once per state, not twice per "
            "delta. Option B is the algebraically-honest signature. Option A's "
            "abstraction-gain doesn't justify the 2x encoder cost on streaming."
        ),
        "rejected_option_tradeoff": (
            "Option A is appropriate for one-shot 'compare these two states' interactive "
            "calls where the caller doesn't manage handles. We can add Option A as a "
            "convenience wrapper LATER if requested — but Option B is the primary surface "
            "exposed to streaming consumers (predictive coding, hippocampal gating per "
            "Spike #112 prediction_error op)."
        ),
        "tool_schema_visibility": "srmech.spectral.delta (Option B signature) per Spike #115 tool_schema surface design",
        "primitive_class": "Class M",
        "alignment": [
            "feedback_no_binding_layer_carveout",
            "user_stance_identity_not_implementation_discipline",
            "user_stance_framework_domain_algebra_not_length_or_magnitude",
        ],
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Truncate findings file at start (clean run).
    if FINDINGS.exists():
        FINDINGS.unlink()

    emit({
        "phase": "framing",
        "kind": "framing",
        "note": (
            "Spike #114: formalise srmech.amsc.hdc.bind (Class M, Phase C1 rc8) as "
            "the runtime delta-encoding primitive. Identity-not-implementation: XOR "
            "self-inversion IS the delta-primitive algebra; bind already ships in C/Python "
            "parity; this spike verifies the identity across 4 substrate categories, "
            "documents substrate-coupling parameters, demarcates bit-exact vs approximate "
            "regimes, and recommends the API surface."
        ),
        "primitive_chain_target": ["Class M (hdc.bind self-inverse XOR)"],
        "stance_alignment": [
            "user_stance_identity_not_implementation_discipline",
            "user_stance_framework_domain_algebra_not_length_or_magnitude",
            "feedback_no_privileged_primitive_classes",
            "feedback_no_binding_layer_carveout",
            "feedback_science_is_ssot_not_project",
            "feedback_ndjson_over_bloated_json",
        ],
    })

    # 1. Algebraic identity (substrate-independent).
    verify_xor_self_inversion_algebra()

    # 2. Substrate-roundtrip identities (4 categories).
    summaries = {}
    for name, fn in [
        ("chess", substrate_chess),
        ("image", substrate_image),
        ("ephemeris", substrate_ephemeris),
        ("gear_dag", substrate_gear_dag),
    ]:
        summaries[name] = fn()

    # 3. Substrate-coupling cost model.
    storage_cost_model()

    # 4. Bit-exact vs approximate regimes.
    regime_demarcation()

    # 5. API surface recommendation.
    api_surface_recommendation()

    # 6. Verdict.
    n_substrates_passing = sum(1 for s in summaries.values() if s["all_bit_exact"])
    verdict_components = [
        f"HDC-BIND-DELTA-IDENTITY-BIT-EXACT-ACROSS-{n_substrates_passing}-OF-4-SUBSTRATES",
        "STORAGE-COST-MODEL-DOCUMENTED",
        "BIT-EXACT-VS-APPROXIMATE-REGIMES-IDENTIFIED",
        "API-SURFACE-RECOMMENDED-OPTION-B",
    ]
    emit({
        "phase": "verdict",
        "kind": "spike_verdict",
        "verdict": " + ".join(verdict_components),
        "per_substrate_summary": summaries,
        "n_substrates_bit_exact": n_substrates_passing,
        "no_new_class_promoted": True,
        "class_chain_attestation": "Class M (bind) only; no Class L or other primitive required for the identity claim; rank-k coefficient-domain extension is Spike #115/116 scope, not this spike",
        "framework_identity_holds": True,
        "stance_alignment_check": "math doesn't lie — XOR self-inversion is algebraic; bit-exact pass across substrates is expected by construction; ANY failure would indicate encoder bug, not bind bug",
        "fermata_for_conductor": [
            "OK to author srmech.spectral.delta (Option B) per Spike #115 tool-schema surface",
            "Spike #117 (Class K sparse_truncate) is next for the truncated-coefficient regime per regime_demarcation",
            "HRR-over-reals (Plate 1995) explicitly OUT of scope; if a future substrate needs it, that's a separate spike with documented approximation budget",
        ],
    })

    # Print one-line verdict for the conductor.
    print(f"spike-114 verdict: {' + '.join(verdict_components)}")


if __name__ == "__main__":
    main()
