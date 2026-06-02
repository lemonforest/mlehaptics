"""``srmech dsl`` — operate the v0.5.0rc8 cascade DSL from the shell.

Three subcommands:

* :func:`run_run` (``srmech dsl run CHAIN.toml --input X --output Y``) —
  load a TOML chain spec, execute it against an input value, emit the
  result.
* :func:`run_ops` (``srmech dsl ops``) — list the cascade-catalog ops
  available to ``chain().then(...)``.
* :func:`run_visualize` (``srmech dsl visualize CHAIN.toml``) — pretty-
  print a parsed chain's stage list (with class composition for each
  cascade-catalog op pulled from the matching TOML descriptor).

Framework reading: the CLI is Class F (render-to-shell) ∘ Class E
(catalog enumeration) atop the DSL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional


def _safe_print(line: str) -> None:
    """Print ``line`` to stdout; replace characters the stdout encoding
    can't represent (Windows cp1252 lacks the cascade-composition ∘
    character, etc.)."""
    enc = (sys.stdout.encoding or "utf-8").lower()
    if enc in ("utf-8", "utf8"):
        print(line)
        return
    try:
        sys.stdout.write(line + "\n")
    except UnicodeEncodeError:
        sys.stdout.write(
            line.encode(enc, errors="replace").decode(enc)
            + "\n"
        )


# ─────────────────────────────────────────────────────────────────────
# argparse wiring
# ─────────────────────────────────────────────────────────────────────


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach ``srmech dsl`` subparsers to ``parser``."""
    sub = parser.add_subparsers(
        dest="dsl_command", required=False,
    )

    # run
    run_p = sub.add_parser(
        "run",
        help="Execute a TOML cascade-DSL chain spec.",
        description=(
            "Load a TOML chain spec, parse it via "
            "srmech.dsl.build_chain_from_toml, run it against an "
            "input value, and print the result. Inputs and outputs "
            "are JSON-shaped on the wire (use --input-file / "
            "--output-file for non-trivial data)."
        ),
    )
    run_p.add_argument("chain_toml", help="Path to TOML chain spec.")
    run_p.add_argument(
        "--input",
        help=(
            "Inline JSON input value passed to chain.run(). Mutually "
            "exclusive with --input-file."
        ),
    )
    run_p.add_argument(
        "--input-file",
        help=(
            "Path to a file containing JSON / NDJSON input. NDJSON "
            "files are read into a list of one parsed record per line."
        ),
    )
    run_p.add_argument(
        "--output-file",
        help=(
            "Path to write the result; format inferred from extension "
            "(.json -> single JSON; .ndjson -> one record per line for "
            "list/tuple outputs). Default: stdout."
        ),
    )
    run_p.add_argument(
        "--ndjson-input",
        action="store_true",
        help=(
            "Treat --input-file as NDJSON (one record per line); "
            "default is single JSON document."
        ),
    )
    run_p.add_argument(
        "--json",
        action="store_true",
        help="Force JSON output to stdout even when result is scalar.",
    )

    # ops
    sub.add_parser(
        "ops",
        help="List cascade-catalog ops available to chain().then(...).",
        description=(
            "Read all TOML descriptors under "
            "srmech/amsc/_research/cascade_catalog/ and print the "
            "available op names + their class composition."
        ),
    ).add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output (one record per op).",
    )

    # visualize
    viz_p = sub.add_parser(
        "visualize",
        help="Pretty-print a parsed chain's stage list.",
        description=(
            "Load a TOML chain spec and print its stages in order, "
            "annotated with the class composition pulled from each "
            "stage's cascade-catalog descriptor."
        ),
    )
    viz_p.add_argument("chain_toml", help="Path to TOML chain spec.")
    viz_p.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output.",
    )


def run(args: argparse.Namespace) -> int:
    """Dispatch one ``srmech dsl ...`` invocation."""
    cmd = getattr(args, "dsl_command", None)
    if cmd == "run":
        return run_run(args)
    if cmd == "ops":
        return run_ops(args)
    if cmd == "visualize":
        return run_visualize(args)
    # No sub-sub-command: print help.
    print("srmech dsl: missing subcommand. Try `srmech dsl --help`.")
    return 2


# ─────────────────────────────────────────────────────────────────────
# subcommand implementations
# ─────────────────────────────────────────────────────────────────────


def run_run(args: argparse.Namespace) -> int:
    """``srmech dsl run CHAIN.toml`` — execute one chain spec."""
    from .. import dsl as _dsl

    chain_path = Path(args.chain_toml)
    if not chain_path.exists():
        print(
            f"srmech dsl run: chain spec not found: {chain_path}",
            file=sys.stderr,
        )
        return 2

    try:
        ch = _dsl.build_chain_from_toml(chain_path)
    except Exception as exc:
        print(
            f"srmech dsl run: failed to build chain: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    # Resolve input.
    if args.input is not None and args.input_file is not None:
        print(
            "srmech dsl run: --input and --input-file are mutually exclusive",
            file=sys.stderr,
        )
        return 2

    if args.input is not None:
        try:
            input_value = json.loads(args.input)
        except json.JSONDecodeError as exc:
            print(
                f"srmech dsl run: --input is not valid JSON: {exc}",
                file=sys.stderr,
            )
            return 2
    elif args.input_file is not None:
        in_path = Path(args.input_file)
        if not in_path.exists():
            print(
                f"srmech dsl run: input file not found: {in_path}",
                file=sys.stderr,
            )
            return 2
        if args.ndjson_input or in_path.suffix.lower() == ".ndjson":
            input_value = []
            with open(in_path, "rb") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    input_value.append(json.loads(raw))
        else:
            with open(in_path, "rb") as fh:
                input_value = json.loads(fh.read())
    else:
        print(
            "srmech dsl run: provide --input or --input-file",
            file=sys.stderr,
        )
        return 2

    # Execute.
    try:
        result = ch.run(input_value)
    except Exception as exc:
        print(
            f"srmech dsl run: chain execution failed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    # Emit result.
    serialised = _json_safe(result)
    if args.output_file:
        out_path = Path(args.output_file)
        if out_path.suffix.lower() == ".ndjson":
            if not isinstance(serialised, list):
                print(
                    "srmech dsl run: NDJSON output requires list/tuple "
                    "result; got "
                    f"{type(serialised).__name__}",
                    file=sys.stderr,
                )
                return 1
            with open(out_path, "wb") as fh:
                for row in serialised:
                    fh.write(json.dumps(row).encode("utf-8"))
                    fh.write(b"\n")
        else:
            with open(out_path, "wb") as fh:
                fh.write(json.dumps(serialised).encode("utf-8"))
                fh.write(b"\n")
    else:
        if args.json or not isinstance(
            serialised, (str, int, float, bool),
        ):
            print(json.dumps(serialised))
        else:
            print(serialised)
    return 0


def run_ops(args: argparse.Namespace) -> int:
    """``srmech dsl ops`` — list cascade-catalog ops."""
    from .. import dsl as _dsl

    names = _dsl.list_cascade_ops()
    if args.json:
        records: List[dict] = []
        for name in names:
            desc = _dsl.get_descriptor(name)
            cascade = desc.get("cascade", {})
            records.append({
                "name": name,
                "class_composition": cascade.get("class_composition", ""),
                "purpose": cascade.get("purpose", ""),
                # DSL role: "stage" (plain `op=` value→value) or
                # "combinator" (a special form — drive via its own
                # discriminator, e.g. `parallel_body=`, NOT `op=`).
                "kind": cascade.get("kind", "stage"),
            })
        print(json.dumps(records, indent=2))
        return 0

    _safe_print(f"Cascade-catalog ops ({len(names)} total):")
    for name in names:
        desc = _dsl.get_descriptor(name)
        cascade = desc.get("cascade", {})
        cls = cascade.get("class_composition", "")
        purpose = cascade.get("purpose", "")
        # Mark a combinator so a CLI user knows it is NOT a plain `op=`
        # stage (drive it via the `parallel` discriminator instead).
        tag = " [combinator]" if cascade.get("kind") == "combinator" else ""
        _safe_print(f"  {name:<24}  [{cls}]{tag}  {purpose}")
    _safe_print(
        "\nkind: plain ops are `op=` chain stages; a [combinator] is a "
        "special form — drive it via its own discriminator "
        "(e.g. `parallel_body=`), not `op=`."
    )
    return 0


def run_visualize(args: argparse.Namespace) -> int:
    """``srmech dsl visualize CHAIN.toml`` — pretty-print a parsed chain."""
    from .. import dsl as _dsl

    chain_path = Path(args.chain_toml)
    if not chain_path.exists():
        print(
            f"srmech dsl visualize: chain spec not found: {chain_path}",
            file=sys.stderr,
        )
        return 2

    try:
        ch = _dsl.build_chain_from_toml(chain_path)
    except Exception as exc:
        print(
            f"srmech dsl visualize: failed to build chain: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    if args.json:
        record = {
            "name": ch.name,
            "n_stages": len(ch),
            "stages": [
                {"op": op, "kwargs": kwargs}
                for op, kwargs in ch.stages()
            ],
        }
        print(json.dumps(record, indent=2))
        return 0

    _safe_print(f"Chain: {ch.name}  ({len(ch)} stages)")
    catalog_names = set(_dsl.list_cascade_ops())
    for idx, (op_name, kwargs) in enumerate(ch.stages()):
        annot = ""
        if op_name in catalog_names:
            desc = _dsl.get_descriptor(op_name)
            cascade = desc.get("cascade", {})
            cls = cascade.get("class_composition", "")
            if cls:
                annot = f"  [{cls}]"
        kw_render = ""
        if kwargs:
            kw_render = "  kwargs=" + json.dumps(kwargs)
        _safe_print(f"  [{idx}] {op_name}{annot}{kw_render}")
    return 0


# ─────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────


def _json_safe(value: Any) -> Any:
    """Coerce a chain result into a JSON-serialisable shape.

    Handles the common cascade-output shapes: scalars pass through,
    tuples become lists, numpy arrays become nested lists. Mixed
    payloads are best-effort; anything truly opaque is stringified.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    return str(value)


__all__ = ["add_arguments", "run"]
