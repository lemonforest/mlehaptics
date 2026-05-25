"""R-RBS-LM-25 — Variant A: GPU-less byte-level encode from notebook text.

Pure substrate-native: next-byte signal comes from the actual UTF-8 bytes
of the source notebook. No teacher model, no BPE tokenizer, no GPT-2
dependency at any point. Just `text.encode('utf-8')` + Class A content-mints.

This tests whether the byte-level cascade WORKS AT ALL at our scale. Same
ceiling expectation as R-RBS-LM-18 / -19 / -20 (3.3%-style; structural per
discrete-vs-continuous cascade limitation) — what we're checking is that
byte-level transitions can be encoded + recovered, not that we lift the
ceiling.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_bytes_variant_a.py \\
        --notebook docs/srmech/srmech_research_notebook.md \\
        --max-bytes 10000
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import CONTEXT_WINDOW, D, hierarchical_bundle  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    BYTE_VOCAB_SIZE,
    compute_byte_vocab_table,
    encode_observation_bytes,
    text_to_bytes,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", default="docs/srmech/srmech_research_notebook.md")
    parser.add_argument("--max-bytes", type=int, default=10000)
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    print(f"=== R-RBS-LM-25 Variant A — GPU-less byte-level from {args.notebook} ===")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW} bytes")
    print(f"  V = {BYTE_VOCAB_SIZE} (vs BPE 50,257)")

    text = Path(args.notebook).read_text()
    print(f"  notebook chars: {len(text):,}")

    all_bytes = text_to_bytes(text)
    print(f"  notebook bytes: {len(all_bytes):,}")
    all_bytes = all_bytes[:args.max_bytes]
    print(f"  using first {len(all_bytes):,} bytes (cap)")

    notebook_slug = Path(args.notebook).stem.replace("_research_notebook", "").replace("_", "-")
    out = args.out or f"docs/srmech/rbs_lm_research/rbs_lm_instrument_v25a_{notebook_slug}.bin"

    # Build vocab table (256 KB)
    print(f"\n=== Build byte vocab table (256 × D/8) ===")
    t0 = time.time()
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.1f} KB; "
          f"{time.time() - t0:.2f}s")

    # Harvest (context, next_byte) pairs from actual text
    print(f"\n=== Harvest (next_byte = actual next byte in text; stride {args.stride}) ===")
    observations = []
    for i in range(0, len(all_bytes) - CONTEXT_WINDOW, args.stride):
        ctx = all_bytes[i:i + CONTEXT_WINDOW]
        nxt = all_bytes[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))
    print(f"  observations: {len(observations)}")

    # Encode + bundle
    print(f"\n=== Encode + bundle ===")
    t0 = time.time()
    bindings = [
        encode_observation_bytes(ctx, nxt, vocab_table, D)
        for ctx, nxt in observations
    ]
    enc_t = time.time() - t0
    print(f"  {len(bindings)} bindings in {enc_t:.1f}s ({len(bindings)/enc_t:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bnd_t = time.time() - t0
    print(f"  bundle: {bnd_t:.2f}s; instrument = {len(instrument)} bytes")

    out_path = Path(out)
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    meta = {
        "partition": "R-RBS-LM-25",
        "variant": "A_gpu_less_byte_level_from_text",
        "notebook_path": args.notebook,
        "notebook_chars": len(text),
        "notebook_bytes_total": len(text_to_bytes(text)),
        "bytes_used": len(all_bytes),
        "max_bytes_cap": args.max_bytes,
        "stride": args.stride,
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "vocab_method": "class_a_content_mint_byte_<n>",
        "tokenizer": "utf-8 (no BPE, no GPT-2 dependency)",
        "harvest_method": "text_self_supervised_no_teacher_forward_pass",
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {out_path.with_suffix('.meta.json')}")


if __name__ == "__main__":
    main()
