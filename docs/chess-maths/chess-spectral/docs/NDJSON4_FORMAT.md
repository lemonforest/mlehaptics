# NDJSON4 — 4D ply-log format

**Version:** v1
**Status:** Stable
**Used by:** `spectral_4d encode`, `chess-spectral-4d encode-moves4`

---

## Overview

NDJSON4 is the bulk input format for the 4D encoder. Each line is one
fully-self-contained position represented by a FEN4 v1 literal (see
[FEN4_FORMAT.md](FEN4_FORMAT.md)). The encoder reads each line, parses
the FEN4, encodes to 45 056 float32, and writes a single frame to a
v4 `.spectralz4` (or plain `.spectral4`) file.

This mirrors the 2D NDJSON pipeline ([src/main.c:435-505](../src/main.c)):
no move replay, no state machine — every ply stands on its own. Move
metadata (`move_from`, `move_to`, `promo`, `flags`) is recorded in the
output frame for downstream consumers but never interpreted by the
encoder.

---

## Line schema

Each non-blank line is a JSON object with these fields:

| Field        | Type             | Required | Default        | Notes |
|--------------|------------------|----------|----------------|-------|
| `fen4`       | string           | ✅       | —              | FEN4 v1 literal — the ply's full position |
| `ply`        | integer          |          | line index     | Recorded in the output frame's `ply` field |
| `move_from`  | array of 4 ints  |          | `[0,0,0,0]`    | Source square (x,y,z,w) of the move that PRODUCED this ply |
| `move_to`    | array of 4 ints  |          | `[0,0,0,0]`    | Destination square (x,y,z,w) |
| `promo`      | integer (0–255)  |          | `0`            | Promotion piece byte (caller-defined enum) |
| `flags`      | integer (0–255)  |          | `0`            | Move flags byte (castling / en-passant / check, caller-defined) |

Any field not listed above is **ignored** (e.g. annotation strings,
clock info, comment fields). This makes NDJSON4 forward-compatible with
producers that emit extra metadata.

Blank lines and lines containing the substring `bridge_version` are
skipped (matching the 2D producer convention).

---

## Examples

### Minimal — two plies

```jsonl
{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0; k@7,7,7,7"}
{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0; k@7,7,7,7", "move_from": [0,0,0,0], "move_to": [1,0,0,0]}
```

### With move flags

```jsonl
{"ply": 0, "fen4": "4d-fen v1: K@4,0,0,0; k@4,7,7,7; Pw@0,1,0,0"}
{"ply": 1, "fen4": "4d-fen v1: K@4,0,0,0; k@4,7,7,7; Pw@0,3,0,0", "move_from": [0,1,0,0], "move_to": [0,3,0,0], "flags": 1}
```

### Producer header (ignored by encoder)

```jsonl
{"bridge_version": "4d-1.0", "produced_at": "2026-04-25T12:00:00Z"}
{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0"}
```

The encoder skips any line containing `bridge_version`, so producers
can include a header line for downstream tools without breaking the
encoder.

---

## Output

The encoder produces a v4 `.spectralz4` (or plain `.spectral4`) file
with one frame per non-skipped line. The frame layout is documented in
[python/chess_spectral/frame_4d.py](../python/chess_spectral/frame_4d.py)
and mirrored exactly by [include/cs_frame_4d.h](../include/cs_frame_4d.h).

---

## Errors

- **FEN4 parse error**: the encoder logs a warning and SKIPS the line
  (does not abort). Following lines are processed normally. This
  matches the 2D producer convention — partial corpora are still
  usable.
- **Missing `fen4` field**: same as above (skipped with warning).
- **Malformed JSON**: same as above. The encoder does not require a
  full JSON parser; it scans for the documented fields.

The exit code is 0 if at least one frame was written, non-zero only on
hard I/O failures (header write, file open, etc.).
