"""R-RBS-LM-27 — Encode the English↔ASL-gloss parallel mini-corpus.

Builds a paired byte stream from `asl_corpus.json`:

    <english> \\x02 <asl_gloss> \\x03 \\n  <english> \\x02 ...

Where:
  - \\x02 (STX) is the "English ends; gloss begins" separator
  - \\x03 (ETX) is the "pair complete" end-marker
  - \\n separates consecutive pairs

The cascade learns byte-transitions across this entire concatenated stream
— including the critical English→\\x02→gloss boundary. At inference time
we'll prompt with `<english> \\x02` and let the cascade generate until it
emits \\x03 (or hits max_new_tokens).

Per R-RBS-LM-25 Variant B (Path D distillation) discipline: we drop any
teacher model at the end of encoding. The resulting instrument has
zero teacher-model dependency at inference time. The corpus IS the
ground-truth training signal (curated authoring, not model generations).

Honest expectation per `[[user_stance_ai_is_not_a_substrate]]` and the
R-RBS-LM-25 finding that V=256 byte mints lack clustering structure:
  - Surface will WORK (cascade learns byte-transitions; can be prompted)
  - Output quality at ~5000 obs scale on 74 pairs is unknown
  - Polysemy context-sensitivity (beat-egg vs beat-defeat) is the most
    discriminating test — does the cascade pick different gloss continuations
    for "I beat the eggs" vs "I beat him in chess"?

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_asl_corpus.py
"""

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


SEPARATOR_BYTE = 0x02   # STX — "English ends, gloss begins"
END_PAIR_BYTE = 0x03    # ETX — "pair complete"
PAIR_SEP_BYTE = 0x0A    # \n  — between consecutive pairs


def build_paired_stream(pairs, shuffle_seed=42):
    """Build a single byte stream from (English, gloss) pairs.

    Stream layout per pair:
        <english_utf8> \\x02 <gloss_utf8> \\x03 \\n

    Pairs are shuffled with a fixed seed so the cascade doesn't bias by
    category order.
    """
    import random
    rng = random.Random(shuffle_seed)
    shuffled = list(pairs)
    rng.shuffle(shuffled)

    chunks = []
    for p in shuffled:
        eng = text_to_bytes(p["english"])
        glo = text_to_bytes(p["asl_gloss"])
        chunks.append(eng + [SEPARATOR_BYTE] + glo + [END_PAIR_BYTE, PAIR_SEP_BYTE])

    stream = []
    for ch in chunks:
        stream.extend(ch)
    return stream


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="docs/srmech/rbs_lm_research/asl_corpus.json")
    parser.add_argument("--stride", type=int, default=4)
    parser.add_argument("--out", default="docs/srmech/rbs_lm_research/rbs_lm_instrument_v27_asl_gloss.bin")
    parser.add_argument("--shuffle-seed", type=int, default=42)
    args = parser.parse_args()

    print(f"=== R-RBS-LM-27 — Encode English↔ASL-gloss parallel corpus ===")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW} bytes; V = {BYTE_VOCAB_SIZE}")
    print(f"  separator: \\x02 (STX); end-pair: \\x03 (ETX); pair-sep: \\n")

    # ---- 1. Load corpus ----------------------------------------------
    corpus = json.load(open(args.corpus))
    pairs = corpus["pairs"]
    print(f"  corpus: {len(pairs)} (English, gloss) pairs from {args.corpus}")
    eng_bytes_total = sum(len(p["english"].encode("utf-8")) for p in pairs)
    glo_bytes_total = sum(len(p["asl_gloss"].encode("utf-8")) for p in pairs)
    print(f"    English bytes total: {eng_bytes_total}")
    print(f"    Gloss bytes total:   {glo_bytes_total}")

    # ---- 2. Build paired byte stream ---------------------------------
    print(f"\n=== Build paired byte stream ===")
    stream = build_paired_stream(pairs, shuffle_seed=args.shuffle_seed)
    print(f"  stream length: {len(stream)} bytes "
          f"({eng_bytes_total + glo_bytes_total} content + "
          f"{3 * len(pairs)} separator/end/sep)")

    # Spot-check the first pair
    first_pair_end = next(i for i, b in enumerate(stream) if b == END_PAIR_BYTE)
    print(f"  first pair (first {first_pair_end + 2} bytes):")
    sep_idx = next(i for i, b in enumerate(stream[:first_pair_end]) if b == SEPARATOR_BYTE)
    print(f"    English: {bytes(stream[:sep_idx]).decode('utf-8', errors='replace')!r}")
    print(f"    gloss:   {bytes(stream[sep_idx+1:first_pair_end]).decode('utf-8', errors='replace')!r}")

    # ---- 3. Build byte vocab table ------------------------------------
    print(f"\n=== Build byte vocab table ===")
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.1f} KB")

    # ---- 4. Harvest (byte_context, next_byte) pairs -------------------
    print(f"\n=== Harvest (stride {args.stride}) ===")
    observations = []
    for i in range(0, len(stream) - CONTEXT_WINDOW, args.stride):
        ctx = stream[i:i + CONTEXT_WINDOW]
        nxt = stream[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))
    print(f"  observations: {len(observations)}")

    # ---- 5. Encode + bundle -------------------------------------------
    print(f"\n=== Encode + bundle ===")
    t0 = time.time()
    bindings = [
        encode_observation_bytes(ctx, nxt, vocab_table, D)
        for ctx, nxt in observations
    ]
    enc_t = time.time() - t0
    print(f"  {len(bindings)} bindings in {enc_t:.1f}s "
          f"({len(bindings)/enc_t:.1f}/s, single-thread)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bnd_t = time.time() - t0
    print(f"  bundle: {bnd_t:.2f}s; instrument = {len(instrument)} bytes")

    out_path = Path(args.out)
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- 6. Metadata --------------------------------------------------
    meta = {
        "partition": "R-RBS-LM-27",
        "experiment": "english_to_asl_gloss_parallel_corpus_encoding",
        "corpus_path": args.corpus,
        "notation_spec": "docs/srmech/rbs_lm_research/asl_gloss_notation.md",
        "n_pairs": len(pairs),
        "english_bytes_total": eng_bytes_total,
        "gloss_bytes_total": glo_bytes_total,
        "paired_stream_bytes": len(stream),
        "separator_byte_hex": "0x02 (STX)",
        "end_pair_byte_hex": "0x03 (ETX)",
        "pair_separator_byte_hex": "0x0A (newline)",
        "shuffle_seed": args.shuffle_seed,
        "stride": args.stride,
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "vocab_method": "class_a_content_mint_byte_<n>",
        "tokenizer": "utf-8 (no BPE, no teacher model)",
        "harvest_method": "paired_english_gloss_byte_stream_self_supervised",
        "encode_seconds": enc_t,
        "bundle_seconds": bnd_t,
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {out_path.with_suffix('.meta.json')}")

    # ---- 7. Inference signature -----------------------------------------
    print(f"\n=== Load this instrument and prompt for translation: ===")
    print(f"  RBS_LM_INSTRUMENT={out_path} \\")
    print(f"    RBS_LM_MODEL_ID=rbs-lm-v27-asl-gloss \\")
    print(f"    RBS_LM_BYTE_MODE=1 \\")
    print(f"    ~/.venvs/rbs-lm-research/bin/python "
          f"docs/srmech/rbs_lm_research/rbs_lm_server.py")
    print(f"  Then send: <english>\\x02 — cascade should produce gloss bytes until \\x03")


if __name__ == "__main__":
    main()
