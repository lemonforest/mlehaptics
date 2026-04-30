# ADR-001: Unified v5 Wire Format with Per-Mode Frame Layouts

**Status:** Proposed
**Date:** 2026-04-29
**Context:** v1.6 differential spectral encoding feature
**Decision driver:** Steven's spec from the v1.6 design conversation:
"can't we make it all the same v5 and let the header tell us if
it's 2d or 4d?" + "let's have both B and C to augment full encoding"
+ "default for smaller files for diff" + "unless we're building out
scaffolding ... no MVP as a final product"

## Context

`.spectralz` (2D) and `.spectralz4` (4D) currently ship as two
parallel binary formats with versions v2 and v4 respectively. The
formats already share:

- 8-byte magic `"LARTPSEC"`
- 256-byte total header size
- Identical first five u32 fields (version, encoding_dim,
  frame_bytes, n_plies, ...)

The v4 (4D) format added two extra u32 fields (`board_dim_side`,
`n_dimensions`) where v2 (2D) had pad. They differ in the **frame
body** because of move-coord widths (2D: u8 from/to; 4D: 4×u8
from/to per coordinate).

Two new requirements drive a v5:

1. **Differential encoding modes.** v1.6 ships three encoding
   modes per the empirical spike from the design conversation:
   - **Mode 0**: dense (current v2/v4 behavior).
   - **Mode 1**: per-channel replacement (skip channels that
     didn't change). Wins when channel-level identity is
     preserved across plies. Empirical: 4D 2.84× compression on
     50-ply knight tour vs dense.
   - **Mode 2**: bit-XOR streaming (frame_N = frame_N XOR
     frame_{N−1}). Wins on chess hypervectors specifically (most
     modes stable per ply → XOR produces zero-byte runs that gzip
     eats). Empirical: 4D **7.23× compression** on the same
     fixture; 2D 1.08×.

2. **Unified header for 2D + 4D.** A single header struct that
   self-describes the dimension via `n_dimensions` (2 or 4)
   removes the parallel-version maintenance burden and is what
   the steven asked for ("let the header tell us if it's 2d or 4d").

## Decision

Define `.spectralz[4]` v5 = unified format that supersedes v2/v4
for new writes. v2/v4 readers stay forever for backward compat
with files already on disk.

### Header (256 bytes total)

```c
typedef struct {
    char     magic[8];       // "LARTPSEC" (unchanged from v2/v4)
    uint32_t version;        // 5
    uint32_t encoding_dim;   // 640 (2D) or 45056 (4D)
    uint32_t frame_bytes;    // dense-equivalent frame size
    uint32_t n_plies;
    uint32_t board_dim_side; // 8 (always)
    uint32_t n_dimensions;   // 2 or 4 — explicit dim flag
    uint8_t  encoding_mode;  // 0=dense, 1=per-channel, 2=XOR-stream
    uint8_t  reserved[223];  // zero-filled
} spectralz_v5_header_t;
```

Total: 8 + 6×4 + 1 + 223 = 256 bytes — slots into the existing
header geometry exactly.

### Encoding modes — frame body layouts

Each mode has its own frame body shape. The reader dispatches on
`encoding_mode` to pick the right frame parser. **No mode pays a
size tax for any other mode's existence** (per Steven's "if it
means writing more data, XOR should be the leanest file format").

#### Mode 0: dense (current v2/v4 behavior)

Frame body = `float32 encoding[encoding_dim]` + move-metadata tail
(dim-dependent: 2D uses 1-byte from/to; 4D uses 4-byte coordinate
tuples). Fixed size. `frame_bytes` in the header is the exact body
size.

#### Mode 1: per-channel replacement

Frame body has variable size. Layout:

```
frame_N:
    u32 body_size_bytes        // length of this frame's body
    u8  flags                  // bit 0: 0x01 = full-frame (independent),
                               //         else delta from frame N-1
    u8  n_channels_present     // 1..N_channels (0 = "no-change frame";
                               //                  in delta mode this means
                               //                  frame_N == frame_{N-1})
    [u8 channel_idx, u8 reserved, float32 buffer[channel_dim]] ×
        n_channels_present
    move-metadata tail (same as Mode 0)
```

Reader rebuilds the working frame by replacing only the channels
present. For `n_channels_present == 0` the working frame is
unchanged from the previous one.

#### Mode 2: XOR-streamed

Frame body fixed-size = `float32 encoding[encoding_dim]` (same as
Mode 0) but the values are the **bit-XOR of frame_N with frame_{N−1}**
treated as `uint32` arrays. Frame 0 is XOR with the zero baseline =
the original frame 0 verbatim.

Reader reconstructs via cumulative XOR: `frame_N = stored[N] XOR
frame_{N−1}`. Bit-exact, lossless.

### CLI surface

```
chess-spectral encode -i game.ndjson -o game.spectralz [--encoding=xor|channel|full]
chess-spectral-4d encode-moves4 ...                   [--encoding=xor|channel|full]

  --encoding=xor       (default for new writes) bit-XOR delta from previous frame
  --encoding=channel   per-channel replacement (skip unchanged channels)
  --encoding=full      legacy v2/v4 dense format (research-platform escape hatch)
```

Per Steven's "strict user opt-in": `--encoding=full` is the explicit
opt-out flag. There's no auto-fallback; the engine never silently
chooses a different mode based on heuristics.

### File extensions

Keep `.spectralz` (2D) and `.spectralz4` (4D) as cosmetic
convention so existing tooling (chess4d-OC, pgn_bridge.py
consumers) that filters by extension keeps working. Internally
both are v5 unified format; the extension is a hint, not a
contract.

## Consequences

**Positive:**
- Single header type unifies 2D + 4D maintenance.
- 7-8× compression on 4D files via XOR-streamed mode (empirical
  spike confirmed 7.23× on a 50-ply 4D fixture).
- Backward-compat: v2/v4 readers + writers stay; old files keep
  working.
- Default-on diff encoding for new writes makes the typical user's
  files smaller without action on their part.
- `--encoding=full` opt-out preserves the research platform's need
  for the literal dense format (e.g., for byte-for-byte parity
  testing with prior tools).

**Negative:**
- Three encoding modes mean three frame-body parsers per dim. The
  parser for mode 0 is the cheapest path (streaming float32 read);
  modes 1 and 2 add per-frame state.
- C-side port doubles in scope (must implement all three modes for
  byte-for-byte parity with Python).
- Round-trip parity test surface grows: must test all 3 modes ×
  2 dims = 6 cells.

**Open questions / deferred:**
- Should v5 also carry the move-history metadata that fen_4d v1's
  placement-only literal omits (turn, ep_target, halfmove_clock,
  fullmove_number)? Probably yes, in a sibling section of the
  header. Captured separately as a follow-up; not in v1.6 scope.
- Per-channel mode's flag field could grow to 8 bits with future
  mode-specific signals (e.g., a "no-op" frame, an "encoding
  reset" marker). For v5 we use only bit 0; reserved for forward
  compat.

## Phasing (PR breakdown for v1.6)

1. **PR-A (this ADR)**: design record, no code.
2. **PR-B**: v5 header + encoding-mode dispatch on the **read** path
   (Python reader auto-detects v2/v4/v5; for v5 routes by
   encoding_mode). 2D + 4D sides both updated. v5 writer in
   --encoding=full mode lands here too (full backward compat with
   v2/v4 frame layouts under the v5 header).
3. **PR-C**: Mode 1 (per-channel) reader + writer. Both 2D and 4D.
   Round-trip parity test in `test_smoke_e2e.py::test_v5_channel_roundtrip`.
4. **PR-D**: Mode 2 (XOR) reader + writer. Both 2D and 4D. Round-trip
   parity at the byte level (XOR reconstruction must produce
   bit-identical frames). Includes the spike-validated compression
   ratios as a regression sanity check.
5. **PR-E**: C-side mirror in `cs_frame.c` / `cs_frame_4d.c` of all
   three modes, gated by the existing C↔Python byte-for-byte
   parity test. CMake glue + miniz still serves as the gzip
   backend (independent of encoding mode).
6. **PR-F**: CLI wiring of `--encoding=xor|channel|full` flag in
   2D and 4D CLIs. Default = xor for new writes.

This is a clean, complete arc. Each PR independently mergeable.
The mode-by-mode order (full → channel → XOR) lets the parity
gate validate correctness incrementally.

## References

- Empirical spike on the Carlsen-Caruana / 4D-knight-tour
  fixtures: 4D XOR mode = 7.23× compression vs dense gzipped;
  per-channel = 2.84×; 2D XOR = 1.08×; per-channel = 0.99× (loss
  on 2D — gzip already eats most of the redundancy).
- v2 header struct: `python/chess_spectral/frame.py` `_HEADER_STRUCT`.
- v4 header struct: `python/chess_spectral/frame_4d.py`
  `_pack_header_with_version`.
- Steven's design-conversation notes (in v1.6 chat): `let's have
  both B and C to augment full encoding` (= modes 1 + 2 alongside
  mode 0); `our header format can identify the encoding scheme`
  (= encoding_mode header byte); "default for smaller files for
  diff" (= mode 2 default for new writes); strict user opt-in for
  --full (= mode 0 explicit fallback only).
