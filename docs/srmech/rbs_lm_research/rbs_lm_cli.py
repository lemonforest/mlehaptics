"""R-RBS-LM-23 — RBS-LM CLI dispatcher.

Single-entry-point CLI exposing the operations registered in
`rbs_lm_tools.py`. Subcommands compose from the tool registry; new
tool entries automatically become discoverable via `rbs_lm_cli list`.

Usage:
    # List all registered RBS-LM tools (grouped by category)
    python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py list

    # Show registered tool details for one entry
    python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py info rbs_lm.inference.generate

    # Disk + research artefact summary
    python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py summary

    # Validate the RBS-LM catalog
    python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py validate-catalog

    # Run inference cascade on a prompt (uses Path C instrument from R-RBS-LM-18)
    python3 docs/srmech/rbs_lm_research/rbs_lm_cli.py infer \\
        "The morning sun" --max-new 10

When the work absorbs into srmech (R-RBS-LM-12 §6), the same dispatcher
becomes `srmech rbs-lm <subcommand>` via the srmech package entrypoint.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_tools import register_rbs_lm_profile  # noqa: E402
from srmech.amsc.tool_schema import get_tool_schema  # noqa: E402


def cmd_list(args):
    """List registered RBS-LM tools, grouped by category."""
    register_rbs_lm_profile()
    schema = get_tool_schema()
    rbs_lm_tools = schema.by_owner("rbs_lm")

    if args.format == "json":
        print(json.dumps([t.to_jsonable() for t in rbs_lm_tools], indent=2))
        return

    by_category = {}
    for tool in rbs_lm_tools:
        by_category.setdefault(tool.category, []).append(tool)

    print(f"=== RBS-LM tool registry ({len(rbs_lm_tools)} entries) ===")
    for category, tools in sorted(by_category.items()):
        print(f"\n  [{category}]")
        for tool in tools:
            name_short = tool.name.removeprefix("rbs_lm.")
            print(f"    {name_short:40s} — {tool.summary.split('.')[0]}.")

    print(f"\n=== Total srmech tool registry: {len(schema.tools)} entries "
          f"({len(schema.by_owner('srmech'))} srmech + "
          f"{len(rbs_lm_tools)} rbs_lm) ===")


def cmd_info(args):
    """Show details of one registered tool entry."""
    register_rbs_lm_profile()
    schema = get_tool_schema()
    tool = schema.lookup(args.tool_name)
    if tool is None:
        print(f"ERROR: tool {args.tool_name!r} not found in registry")
        print("Use 'list' to see registered tools.")
        sys.exit(1)
    print(json.dumps(tool.to_jsonable(), indent=2))


def cmd_summary(args):
    """Disk + research artefact summary."""
    from storage_management import disk_summary
    disk_summary(verbose=True)


def cmd_validate_catalog(args):
    """Validate the rbs_lm AMSC catalog."""
    register_rbs_lm_profile()
    import subprocess
    result = subprocess.run(
        ["python3", "docs/srmech/catalogs/rbs_lm/validate_catalog.py"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(f"STDERR:\n{result.stderr}", file=sys.stderr)
    sys.exit(result.returncode)


def cmd_infer(args):
    """Run inference cascade on a prompt using a saved instrument."""
    register_rbs_lm_profile()
    print(f"=== RBS-LM inference: '{args.prompt}' ===")
    print(f"  instrument: {args.instrument}")
    print(f"  vocab mode: {'Path C (WTE-projected)' if args.path_c else 'Path B (srmech-native)'}")
    print(f"  max new tokens: {args.max_new}")

    # Quick precheck for instrument file
    if not Path(args.instrument).exists():
        print(f"ERROR: instrument file not found at {args.instrument}")
        sys.exit(1)

    instrument = Path(args.instrument).read_bytes()
    print(f"  loaded instrument: {len(instrument)} bytes")

    # Lazy imports — only load torch + transformers if we're actually inferring
    print(f"  loading source model (gpt2) for vocab table + tokenizer...")
    import torch
    torch.set_num_threads(16)
    from transformers import GPT2LMHeadModel, GPT2Tokenizer

    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    if args.path_c:
        from rbs_lm_path_c import compute_path_c_vocab_table
        vocab_table = compute_path_c_vocab_table(model, D=8192, seed=42)
    else:
        from rbs_lm_inference import precompute_vocab_table
        vocab_table = precompute_vocab_table(vocab_size=50257, D=8192)

    print(f"  vocab table ready; running inference...")
    if args.path_c:
        from rbs_lm_path_c import encode_context_path_c
        from rbs_lm_inference import vectorised_cleanup
        from rbs_lm_encoder import CONTEXT_WINDOW, D, bind

        prompt_ids = tokenizer.encode(args.prompt)
        tokens = list(prompt_ids)
        import time
        t0 = time.time()
        for _ in range(args.max_new):
            ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
            ctx_vec = encode_context_path_c(ctx, vocab_table)
            cand = bind(instrument, ctx_vec)
            res = vectorised_cleanup(cand, vocab_table, D, top_k=1)
            tokens.append(res[0][0])
        elapsed = time.time() - t0
    else:
        from rbs_lm_inference import generate
        prompt_ids = tokenizer.encode(args.prompt)
        import time
        t0 = time.time()
        tokens, latencies = generate(instrument, prompt_ids, args.max_new, vocab_table)
        elapsed = time.time() - t0

    new_tokens = tokens[len(prompt_ids):]
    completion = tokenizer.decode(new_tokens)
    print(f"\n  prompt:     '{args.prompt}'")
    print(f"  completion: '{completion}'")
    print(f"  per-token latency: {(elapsed/args.max_new)*1000:.1f} ms")


def main():
    parser = argparse.ArgumentParser(
        description="RBS-LM CLI dispatcher (R-RBS-LM-23)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List registered RBS-LM tools")
    p_list.add_argument("--format", choices=["text", "json"], default="text")
    p_list.set_defaults(func=cmd_list)

    p_info = sub.add_parser("info", help="Show details of one tool entry")
    p_info.add_argument("tool_name", help="Full tool name, e.g. rbs_lm.inference.generate")
    p_info.set_defaults(func=cmd_info)

    p_sum = sub.add_parser("summary", help="Disk + research artefact summary")
    p_sum.set_defaults(func=cmd_summary)

    p_val = sub.add_parser("validate-catalog", help="Validate the rbs_lm AMSC catalog")
    p_val.set_defaults(func=cmd_validate_catalog)

    p_inf = sub.add_parser("infer", help="Run inference cascade on a prompt")
    p_inf.add_argument("prompt", help="Prompt text")
    p_inf.add_argument(
        "--instrument", default="docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin",
        help="Instrument .bin path (default: R-RBS-LM-18 Path C 491-obs)",
    )
    p_inf.add_argument(
        "--max-new", type=int, default=20,
        help="Number of tokens to generate (default 20)",
    )
    p_inf.add_argument(
        "--path-c", action="store_true", default=True,
        help="Use Path C inference (WTE-projected vocab; default True)",
    )
    p_inf.add_argument(
        "--no-path-c", dest="path_c", action="store_false",
        help="Use Path B inference (srmech-native vocab)",
    )
    p_inf.set_defaults(func=cmd_infer)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
