# `.spectral[z]` / `.spectralz4` wire format reference

Canonical user-facing spec for the binary container that holds chess-spectral
encoder output. Covers all four shipped versions (v2 / v3 / v4 / v5) and
how readers dispatch between them.

> **Looking for the design rationale?** That lives in
> [`docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md`](adr/wire_format/ADR-001-v5-unified-encoding-modes.md).
> This file is the user-facing format spec; the ADR is the why.

## Versions at a glance

| Version | Magic       | Shipped in | Encoder | Frame body | File ext | Status |
|---------|-------------|------------|---------|------------|----------|--------|
| **v2**  | `LARTPSEC`  | v0.x       | 2D 640-dim | dense  | `.spectral` / `.spectralz` | reader-only |
| **v3**  | `LARTPSEC`  | v1.0       | 4D 40 960-dim | dense | `.spectralz4` | reader-only (legacy) |
| **v4**  | `LARTPSEC`  | v1.1.1     | 4D 45 056-dim | dense | `.spectralz4` | reader-only (legacy) |
| **v5**  | `LARTPSEC`  | v1.6       | 2D *or* 4D, three encoding modes | dense / per-channel / xor-stream | `.spectral[z]` or `.spectralz4` | **default for new writes** |

The magic bytes (`LARTPSEC`, ASCII, little-endian = `0x434553505452414C`) are
identical across all versions. Readers detect the version by reading the
first 12 bytes (magic + u32 version), then dispatch to the right parser.

## Compression

Any version may be transparently gzipped (RFC 1952) — the `z` suffix in
`.spectralz` / `.spectralz4` indicates gzip compression. Readers detect
gzip by peeking the first two bytes (`0x1F 0x8B`) and decompress before
parsing the LARTPSEC header. The internal layout is identical between
gzipped and uncompressed forms; gzip is a transport wrapper.

The C writer always emits gzip with `mtime=0` for deterministic output
(byte-for-byte reproducibility across runs). The Python writer matches.

## v5 — current format (v1.6+)

**Single header serves both 2D and 4D**, parameterised by `n_dimensions`.
Three encoding modes for the frame body, selected by `encoding_mode`.

### Header (256 bytes, little-endian)

```c
typedef struct {
    char     magic[8];       // "LARTPSEC"
    uint32_t version;        // 5
    uint32_t encoding_dim;   // 640 (2D) or 45056 (4D)
    uint32_t frame_bytes;    // dense-equivalent frame size
    uint32_t n_plies;        // number of frames that follow
    uint32_t board_dim_side; // 8 (always)
    uint32_t n_dimensions;   // 2 or 4 — the explicit dim flag
    uint8_t  encoding_mode;  // 0=dense, 1=per-channel, 2=xor-stream
    uint8_t  reserved[223];  // zero-filled
} spectralz_v5_header_t;
```

Total: `8 + 6×4 + 1 + 223 = 256 bytes` — matches the v2/v4 header geometry
exactly, so v5 files have the same on-disk header size as their
predecessors.

### Encoding modes

The `encoding_mode` byte selects one of three frame-body layouts. Each
layout is independently optimal for a different workload; ADR-001 has the
empirical compression numbers (4D XOR-stream measured 7.23× compression
vs dense gzipped on a 50-ply knight-tour fixture).

#### Mode 0 — dense

Frame body = `float32 encoding[encoding_dim]` followed by move metadata.
Identical body to v2 (2D) / v3 / v4 (4D) — only the header differs. This
is the `--encoding=full` CLI flag's effect.

| Component | 2D bytes | 4D bytes |
|---|---|---|
| `encoding[encoding_dim]` | 640 × 4 = 2560 | 45 056 × 4 = 180 224 |
| `ply` (u32) | 4 | 4 |
| move-from coordinates | 1 (u8) | 4 (u8 × 4) |
| move-to coordinates | 1 (u8) | 4 (u8 × 4) |
| `promo` (u8) | 1 | 1 |
| `flags` (u8) | 1 | 1 |
| **total** | **2568** | **180 238** |

#### Mode 1 — per-channel replacement

Frame body has variable size. Layout per ply:

```
u32 body_size_bytes        // length of body (excluding own size field)
u8  flags                  // bit 0 = PC_FLAG_FULL (independent frame)
u8  n_channels_present     // 0..N_channels
[u8 channel_idx, u8 reserved, float32 buffer[channel_dim]] × n_present
<move-metadata tail>       // 8 B (2D) or 14 B (4D), same as mode 0
```

The encoder compares each frame against the previous reconstructed one and
emits only the channels whose float32 bit pattern changed. Channel layout:
2D = 10 channels × 64 modes; 4D = 11 channels × 4096 modes. The first
frame is always emitted with the FULL flag set (independent baseline).

#### Mode 2 — XOR-stream

Frame body fixed-size = identical layout to mode 0. The DIFFERENCE: each
frame's `encoding[]` payload is the bit-XOR of the real encoding with the
previous reconstructed frame's encoding (treated as `uint32` arrays).
Frame 0 is XOR'd with zero = verbatim.

```
real_frame[N] = stored[N] XOR real_frame[N-1]    // cumulative reconstruction
```

Bit-exact, lossless. The wins come from gzip: chess hypervectors are
mostly stable per ply, so XOR yields long zero-byte runs that gzip
compresses essentially for free. This is the **leanest** encoding format
— same fixed frame body size as mode 0, no per-frame overhead.

## Reader dispatch

A correct reader handles all four versions. The Python reference reader
(`chess_spectral.frame_v5.peek_version()`) reads only the first 12 bytes:

```python
from chess_spectral.frame_v5 import peek_version

v = peek_version("game.spectralz")  # transparent over gzip
if v == 2:
    # 2D legacy → chess_spectral.frame.read_all()
    ...
elif v in (3, 4):
    # 4D legacy → chess_spectral.frame_4d.read_all()
    ...
elif v == 5:
    # unified → chess_spectral.frame_v5.read_v5_header()
    #          + dispatch on encoding_mode + n_dimensions
    ...
```

Implementation: [`python/chess_spectral/frame_v5.py`](../python/chess_spectral/frame_v5.py).

## Backward compatibility guarantees

- **v2/v3/v4 readers stay forever.** Files already on disk keep working.
- **Magic is unchanged across versions.** Any reader that checks the magic
  before the version field will still recognise the file.
- **v5 dense-mode frame body bytes are byte-identical to v2/v4.** A v5
  file in mode 0 is a v2/v4 file with a different header. Tools that only
  process the encoding payload (e.g., the chess-maths-viewer's frame
  iterator) will work unchanged on v5 dense files.
- **Default for new writes (v1.6+).** `--encoding=xor` is the default
  CLI mode; users opt out with `--encoding=full` (mode 0) for byte-for-
  byte compatibility with prior tools that haven't learned the v5 modes.

## See also

- [ADR-001 v5 unified encoding modes](adr/wire_format/ADR-001-v5-unified-encoding-modes.md) — design rationale + phasing plan.
- [`python/chess_spectral/frame_v5.py`](../python/chess_spectral/frame_v5.py) — Python reference reader/writer (all 3 modes).
- [`python/chess_spectral/frame.py`](../python/chess_spectral/frame.py) — v2 reader/writer (2D legacy).
- [`python/chess_spectral/frame_4d.py`](../python/chess_spectral/frame_4d.py) — v3/v4 reader/writer (4D legacy).
- [FEN4_FORMAT.md](FEN4_FORMAT.md) — the 4D position literal grammar (input to encoder).
- [NDJSON4_FORMAT.md](NDJSON4_FORMAT.md) — the 4D ply-log streaming format (input to bulk encode).
