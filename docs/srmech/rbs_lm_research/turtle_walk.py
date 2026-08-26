"""R-RBS-LM-44 — Turtle walk: natural-language → LOGO action via cascade.

Tests R-RBS-LM-40 candidate E (projection to constrained structured action
vocabulary) using LOGO's 12-atom action space as the target. Per R-RBS-LM-43
§3.3 + Finding 9: a constrained-vocabulary projection is the substrate-honest
first test of the M1 → M2 surface projection layer.

Pipeline:
  English fragment → byte-level cascade (trained on parallel English↔LOGO corpus)
    → LOGO command bytes → LOGO L0 parser/interpreter → turtle trace + geometry

Per `[[user_stance_ai_is_not_a_substrate]]`: the cascade is still a transducer.
What changes is the projection target — instead of trying to produce coherent
English prose (impossible per R-RBS-LM-19 structural ceiling), we project to a
SMALL STRUCTURED VOCABULARY (12 atoms + numbers) where success is much more
verifiable: does the output PARSE as LOGO? Does executing it move the turtle?

Honors user-direction 2026-05-26: turtle-walk via cascade-as-language-projection.
Founded on user's childhood LOGO experience (age 7-8; 5.25" floppy with notebook)
per the cross-substrate-cascade-matching methodology — see R-RBS-LM-43 §0.

Usage:
    # Step 1: encode the parallel corpus into a v44 instrument
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/turtle_walk.py encode

    # Step 2: probe the instrument with English fragments; report whether
    # cascade outputs parse as valid LOGO
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/turtle_walk.py smoke
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
    bytes_to_text,
)


CORPUS_PATH = "docs/srmech/rbs_lm_research/turtle_walk_corpus.json"
INSTRUMENT_PATH = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v44_turtle_walk.bin"
SEPARATOR_BYTE = 0x02   # STX — "English ends, LOGO begins"
END_PAIR_BYTE = 0x03    # ETX — "pair complete"
PAIR_SEP_BYTE = 0x0A    # \n  — between pairs


def build_paired_stream(pairs, shuffle_seed=42):
    """Build a single byte stream from (English, LOGO) pairs.
    Pattern: <english_utf8> \\x02 <logo_utf8> \\x03 \\n <next pair>...
    """
    import random
    rng = random.Random(shuffle_seed)
    shuffled = list(pairs)
    rng.shuffle(shuffled)

    stream = []
    for p in shuffled:
        eng = text_to_bytes(p["english"])
        logo = text_to_bytes(p["logo"])
        stream.extend(eng)
        stream.append(SEPARATOR_BYTE)
        stream.extend(logo)
        stream.append(END_PAIR_BYTE)
        stream.append(PAIR_SEP_BYTE)
    return stream


def encode_corpus(corpus_path=CORPUS_PATH, out_path=INSTRUMENT_PATH,
                   stride=4, shuffle_seed=42):
    print(f"=== R-RBS-LM-44 — Encode English↔LOGO parallel corpus ===")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW} bytes; V = {BYTE_VOCAB_SIZE}")
    print(f"  separator: \\x02 (STX); end-pair: \\x03 (ETX); pair-sep: \\n")

    corpus = json.load(open(corpus_path))
    pairs = corpus["pairs"]
    print(f"  corpus: {len(pairs)} (English, LOGO) pairs from {corpus_path}")

    eng_bytes_total = sum(len(p["english"].encode("utf-8")) for p in pairs)
    logo_bytes_total = sum(len(p["logo"].encode("utf-8")) for p in pairs)
    print(f"    English bytes total: {eng_bytes_total}")
    print(f"    LOGO bytes total:    {logo_bytes_total}")

    # Build paired byte stream
    print(f"\n=== Build paired byte stream ===")
    stream = build_paired_stream(pairs, shuffle_seed=shuffle_seed)
    print(f"  stream length: {len(stream)} bytes "
          f"({eng_bytes_total + logo_bytes_total} content + {3 * len(pairs)} delim)")

    # Build byte vocab table
    print(f"\n=== Build byte vocab table ===")
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.1f} KB")

    # Harvest (byte_context, next_byte) pairs
    print(f"\n=== Harvest (stride {stride}) ===")
    observations = []
    for i in range(0, len(stream) - CONTEXT_WINDOW, stride):
        ctx = stream[i:i + CONTEXT_WINDOW]
        nxt = stream[i + CONTEXT_WINDOW]
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

    Path(out_path).write_bytes(instrument)
    print(f"  saved: {out_path}")

    # Metadata
    meta = {
        "partition": "R-RBS-LM-44",
        "experiment": "english_to_logo_constrained_vocabulary_projection",
        "corpus_path": corpus_path,
        "n_pairs": len(pairs),
        "english_bytes_total": eng_bytes_total,
        "logo_bytes_total": logo_bytes_total,
        "paired_stream_bytes": len(stream),
        "shuffle_seed": shuffle_seed,
        "stride": stride,
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "framework_reading_anchor": "R-RBS-LM-40 candidate E (constrained structured action vocabulary projection); R-RBS-LM-43 §3.3 + Finding 9",
    }
    Path(out_path).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    return out_path


# ---- Smoke: probe + parse + execute ------------------------------------

PROBE_QUERIES = [
    "walk forward 100",       # direct training example
    "turn left",              # direct
    "draw a square",          # direct
    "make a hexagon",         # near training (had pentagon/hexagon)
    "go forward 50",          # near training
    "draw a circle",          # direct
    "lift pen up",            # direct
    "walk in a circle",       # polysemy_walk
    "spin around",            # direct
    "take a big step",        # speed_distance
    "draw a star",            # NOT in training — out-of-distribution probe
    "make me a flower",       # OOD probe
]


def generate_logo_for(bot, english, max_new=64):
    """Prompt cascade with `<english>\\x02`, generate until ETX or max_new."""
    from rbs_lm_encoder import bind
    from rbs_lm_bytes import vectorised_cleanup_bytes, encode_context_bytes

    prompt_bytes = list(english.encode("utf-8")) + [SEPARATOR_BYTE]
    tokens = list(prompt_bytes)
    new_bytes = []
    for _ in range(max_new):
        ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
        ctx_vec = encode_context_bytes(ctx, bot.vocab_table, D)
        cand = bind(bot.instrument, ctx_vec)
        res = vectorised_cleanup_bytes(cand, bot.vocab_table, D, top_k=1)
        nxt = res[0][0]
        if nxt == END_PAIR_BYTE:
            break
        new_bytes.append(nxt)
        tokens.append(nxt)
    return new_bytes


def try_parse_and_execute(logo_text):
    """Try to parse + run the candidate LOGO text. Return (parse_ok, exec_ok, n_segments, err)."""
    try:
        sys.path.insert(0, "docs/logo-maths")
        from logo_parser import parse  # type: ignore
        from logo_interp import run  # type: ignore
    except Exception as e:
        return False, False, 0, f"logo-import-fail: {e}"

    try:
        prog = parse(logo_text)
    except Exception as e:
        return False, False, 0, f"parse: {type(e).__name__}: {str(e)[:100]}"

    try:
        ctx = run(prog)
    except Exception as e:
        return True, False, 0, f"exec: {type(e).__name__}: {str(e)[:100]}"

    n_segments = len(ctx.trace.segments) if hasattr(ctx, "trace") else 0
    return True, True, n_segments, None


def smoke():
    from rbs_lm_chatbot import RBSChatbotBytes
    if not Path(INSTRUMENT_PATH).exists():
        print(f"FATAL: {INSTRUMENT_PATH} not found. Run `turtle_walk.py encode` first.")
        sys.exit(1)

    print(f"=== R-RBS-LM-44 — Turtle walk smoke ===")
    print(f"  instrument: {INSTRUMENT_PATH}")
    bot = RBSChatbotBytes.load(instrument_path=INSTRUMENT_PATH, verbose=True)

    results = []
    n_parse_ok = 0
    n_exec_ok = 0
    for query in PROBE_QUERIES:
        t0 = time.time()
        new_bytes = generate_logo_for(bot, query, max_new=64)
        elapsed = (time.time() - t0) * 1000
        text = bytes_to_text(new_bytes)
        parse_ok, exec_ok, n_segs, err = try_parse_and_execute(text)
        if parse_ok:
            n_parse_ok += 1
        if exec_ok:
            n_exec_ok += 1
        status = "EXEC" if exec_ok else ("PARSE" if parse_ok else "FAIL")
        print(f"\n  {status:>5}  english:  {query!r}")
        print(f"         cascade:  {text!r}")
        print(f"         {'segments=' + str(n_segs) if exec_ok else 'err=' + (err or 'unknown')}")
        print(f"         {elapsed:.0f} ms; {len(new_bytes)} bytes")
        results.append({
            "english": query,
            "cascade_output": text,
            "cascade_bytes": new_bytes,
            "parse_ok": parse_ok,
            "exec_ok": exec_ok,
            "n_segments": n_segs,
            "error": err,
            "elapsed_ms": elapsed,
        })

    print(f"\n=== Summary ===")
    print(f"  PARSE success: {n_parse_ok}/{len(PROBE_QUERIES)}")
    print(f"  EXEC  success: {n_exec_ok}/{len(PROBE_QUERIES)}")

    out_path = Path("docs/srmech/rbs_lm_research/turtle_walk_smoke_results.json")
    out_path.write_text(json.dumps({
        "partition": "R-RBS-LM-44",
        "instrument": INSTRUMENT_PATH,
        "n_parse_ok": n_parse_ok,
        "n_exec_ok": n_exec_ok,
        "n_total": len(PROBE_QUERIES),
        "results": results,
    }, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")

    print(f"\n=== Honest framework reading ===")
    if n_exec_ok == len(PROBE_QUERIES):
        print(f"  → All probes produced executable LOGO. R-RBS-LM-40 candidate E is")
        print(f"    operationally viable for constrained-action-vocabulary projection.")
    elif n_exec_ok > 0:
        print(f"  → Partial execution success ({n_exec_ok}/{len(PROBE_QUERIES)}).")
        print(f"    Cascade IS projecting some queries to valid LOGO; mode-collapses on others.")
        print(f"    Candidate E is partially viable; refinement (more pairs / structured atoms) may help.")
    elif n_parse_ok > 0:
        print(f"  → Parse succeeds on {n_parse_ok} queries but execution fails on all.")
        print(f"    Suggests cascade picks LOGO-token bytes but produces malformed programs.")
        print(f"    Structured-atom encoding (LOGO L1 pattern) may be needed.")
    else:
        print(f"  → No probe produced parseable LOGO. Cascade output mode-collapses.")
        print(f"    Candidate E refuted at this corpus scale; need: more pairs, structured atoms,")
        print(f"    OR substrate-foreign-rejection per R-RBS-LM-19 pattern applies here too.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["encode", "smoke"],
                        help="encode: build v44 instrument; smoke: probe + parse + execute")
    parser.add_argument("--stride", type=int, default=4)
    args = parser.parse_args()

    if args.action == "encode":
        encode_corpus(stride=args.stride)
    elif args.action == "smoke":
        smoke()


if __name__ == "__main__":
    main()
