"""``srmech bus`` — operate the v0.5.0 bus from the shell.

v0.5.0rc4 (2026-05-28) adds five subcommands under ``srmech bus``:

* :func:`list_endpoints_cmd` (``srmech bus list``) — enumerate active
  endpoints owned by the current user; tabular or JSON.
* :func:`tap_cmd` (``srmech bus tap NAME``) — subscribe to an
  endpoint and stream every broadcast event to stdout.
* :func:`pipe_cmd` (``srmech bus pipe SRC DST``) — daemon: subscribe
  to ``SRC``; forward each event to ``DST`` (optionally via a
  Python-expression transform).
* :func:`send_cmd` (``srmech bus send NAME EVENT_JSON``) — one-shot
  request/response; print the response.
* :func:`serve_cmd` (``srmech bus serve NAME --echo``) — minimal
  test server that echoes inbound events back (or routes through a
  user-supplied handler).

Mirrors the :mod:`srmech.cli.status` pattern: argparse subparser
registration via :func:`add_arguments`, plus one ``run_*`` function
per subcommand dispatched by :func:`run`.

Framework reading: the bus CLI is Class M (cross-class bind) ∘
Class F (render to the OS-process shell surface) ∘ Class E (catalog
enumeration) — the shell IS another substrate-class-instance the
bus composes with, alongside Python / C / MCP.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from typing import Any, Dict, List, Optional

from .. import bus as _bus


# ─────────────────────────────────────────────────────────────────────
# argparse wiring
# ─────────────────────────────────────────────────────────────────────


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach ``srmech bus`` subparsers to ``parser``.

    Mirrors :func:`srmech.cli.status.add_arguments`. The parser is
    the ``bus`` parent — we add a nested ``required=True`` subparser
    set so e.g. ``srmech bus`` (no sub-sub) prints help instead of
    silently routing.
    """
    sub = parser.add_subparsers(
        dest="bus_subcommand", metavar="SUBCOMMAND", required=False,
    )

    # ----- list ------------------------------------------------------
    p_list = sub.add_parser(
        "list",
        help="List active bus endpoints (ownership-filtered).",
        description=(
            "Enumerate active srmech.bus endpoints owned by the "
            "current user (or all readable endpoints with --all). "
            "Tabular by default; --json for machine-readable output."
        ),
    )
    p_list.add_argument(
        "--json", action="store_true",
        help="Emit JSON array (one record per endpoint).",
    )
    p_list.add_argument(
        "--all", dest="show_all", action="store_true",
        help=(
            "Show every endpoint registration readable to the current "
            "user, not just those owned by the current user. "
            "(POSIX: same as default; the per-user bus dir is already "
            "user-scoped. Provided for cross-platform consistency.)"
        ),
    )

    # ----- tap -------------------------------------------------------
    p_tap = sub.add_parser(
        "tap",
        help="Subscribe to an endpoint and stream events to stdout.",
        description=(
            "Open a subscriber channel to NAME and print every "
            "broadcast event to stdout. Defaults: JSON one-per-line; "
            "no event-type filter; runs until Ctrl-C."
        ),
    )
    p_tap.add_argument("name", help="Endpoint name to subscribe to.")
    p_tap.add_argument(
        "--seed", default=None, metavar="HEX",
        help=(
            "Pre-shared seed (hex-encoded) for encrypted endpoints. "
            "If omitted, the bus seed-resolution cascade is used "
            "(SRMECH_BUS_SEED env var, then ~/.srmech/bus-NAME.seed)."
        ),
    )
    p_tap.add_argument(
        "--format", dest="output_format",
        choices=("json", "pretty"), default="json",
        help=(
            "Output format. 'json' (default): one compact JSON line "
            "per event. 'pretty': multi-line indented JSON."
        ),
    )
    p_tap.add_argument(
        "--filter", dest="type_filter", default=None, metavar="TYPE",
        help="Only show events whose 'type' field equals TYPE.",
    )
    p_tap.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Exit after receiving N events.",
    )

    # ----- pipe ------------------------------------------------------
    p_pipe = sub.add_parser(
        "pipe",
        help="Forward events from SRC to DST (daemon mode).",
        description=(
            "Subscribe to SRC; for each broadcast event, send it to "
            "DST (fire-and-forget). Optional Python-expression "
            "--transform reshapes each event before forwarding."
        ),
    )
    p_pipe.add_argument("src", help="Source endpoint name (subscribe).")
    p_pipe.add_argument("dst", help="Destination endpoint name (send).")
    p_pipe.add_argument(
        "--seed-src", default=None, metavar="HEX",
        help="Seed (hex) for the source channel; cascade default.",
    )
    p_pipe.add_argument(
        "--seed-dst", default=None, metavar="HEX",
        help="Seed (hex) for the destination channel; cascade default.",
    )
    p_pipe.add_argument(
        "--transform", default=None, metavar="PY_EXPR",
        help=(
            "Python expression evaluated with the inbound event "
            "bound as 'e'. Result is the dict sent to DST. "
            "Example: '{**e, \"marker\": \"piped\"}'. "
            "SECURITY: eval()'d; only use with trusted local input."
        ),
    )

    # ----- send ------------------------------------------------------
    p_send = sub.add_parser(
        "send",
        help="One-shot send + print response.",
        description=(
            "Send one event to NAME (req/rep) and print the "
            "response. EVENT_JSON is a JSON object; --stdin reads "
            "the JSON from stdin instead of the argument."
        ),
    )
    p_send.add_argument("name", help="Endpoint name to send to.")
    p_send.add_argument(
        "event_json", nargs="?", default=None,
        help="Event as a JSON object string (omitted with --stdin).",
    )
    p_send.add_argument(
        "--seed", default=None, metavar="HEX",
        help="Seed (hex) for encrypted endpoints; cascade default.",
    )
    p_send.add_argument(
        "--timeout", type=float, default=5.0, metavar="SECONDS",
        help="Reply timeout in seconds (default 5.0).",
    )
    p_send.add_argument(
        "--stdin", action="store_true",
        help="Read EVENT_JSON from stdin (positional arg ignored).",
    )

    # ----- serve -----------------------------------------------------
    p_serve = sub.add_parser(
        "serve",
        help="Run a minimal test server (echo or user handler).",
        description=(
            "Bind NAME and serve until Ctrl-C. --echo (default if no "
            "handler) wraps each inbound event as {'type': 'echo', "
            "'payload': <inbound-event>}. --handler-module imports a "
            "Python callable as the handler instead."
        ),
    )
    p_serve.add_argument("name", help="Endpoint name to bind.")
    p_serve.add_argument(
        "--echo", action="store_true",
        help="Echo inbound events back wrapped as 'type=echo'.",
    )
    p_serve.add_argument(
        "--seed", default=None, metavar="HEX",
        help="Pre-shared seed (hex) for the channel.",
    )
    p_serve.add_argument(
        "--seed-mint", action="store_true",
        help=(
            "Mint a fresh random seed at startup + write it to "
            "~/.srmech/bus-NAME.seed (0o600). Conflicts with --seed."
        ),
    )
    p_serve.add_argument(
        "--handler-module", default=None, metavar="PYMOD:func",
        help=(
            "Import a Python module + use its 'func' as the handler "
            "(advanced; module must be importable from PYTHONPATH)."
        ),
    )


# ─────────────────────────────────────────────────────────────────────
# Subcommand dispatcher
# ─────────────────────────────────────────────────────────────────────


def run(args: argparse.Namespace) -> int:
    """Dispatch the ``bus`` subcommand parsed into ``args``."""
    sub = getattr(args, "bus_subcommand", None)
    if sub is None:
        # No subcommand — same behaviour as a bare 'srmech bus':
        # print this parser's help and exit 0.
        print(
            "usage: srmech bus {list,tap,pipe,send,serve} ...",
            file=sys.stderr,
        )
        print(
            "(Run 'srmech bus <subcommand> --help' for subcommand help.)",
            file=sys.stderr,
        )
        return 0
    if sub == "list":
        return run_list(args)
    if sub == "tap":
        return run_tap(args)
    if sub == "pipe":
        return run_pipe(args)
    if sub == "send":
        return run_send(args)
    if sub == "serve":
        return run_serve(args)
    print(f"unknown bus subcommand: {sub!r}", file=sys.stderr)
    return 2


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _decode_seed(hex_str: Optional[str]) -> Optional[bytes]:
    """Decode a hex-encoded seed string. Returns None for None input.

    Raises :class:`ValueError` on a non-hex value or under-length seed
    (deferred to :mod:`srmech.bus._seed`'s own length validation).
    """
    if hex_str is None:
        return None
    try:
        return bytes.fromhex(hex_str.strip())
    except ValueError as exc:
        raise ValueError(f"--seed not a valid hex string: {exc}") from exc


def _format_event(event: Dict[str, Any], output_format: str) -> str:
    """Render one event dict for ``--format json`` or ``--format pretty``."""
    if output_format == "pretty":
        return json.dumps(event, indent=2, sort_keys=True, default=str)
    return json.dumps(event, sort_keys=True, default=str)


# ─────────────────────────────────────────────────────────────────────
# list
# ─────────────────────────────────────────────────────────────────────


def run_list(args: argparse.Namespace) -> int:
    """Implementation of ``srmech bus list``.

    The ``--all`` flag is a placeholder for future cross-user
    enumeration; on POSIX the per-user bus directory is already
    user-scoped, so it's currently a no-op. We accept the flag so
    scripts written against the future API don't need to change.
    """
    endpoints = _bus.list_endpoints()
    if args.json:
        payload = [
            {
                "name": ep.name,
                "transport": ep.transport,
                "path": str(ep.path),
                "alive": ep.alive,
                "pid": ep.pid,
            }
            for ep in endpoints
        ]
        json.dump(payload, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0
    if not endpoints:
        print("No active bus endpoints.")
        print("")
        print(
            "Hint: start one with `srmech bus serve NAME --echo` "
            "or call `srmech.bus.serve(...)` in Python."
        )
        return 0
    header = (
        f"{'NAME':<24} {'TRANSPORT':<10} {'PID':<8} "
        f"{'ENCRYPTED':<10} {'ALIVE':<6}"
    )
    print(header)
    print("-" * len(header))
    for ep in endpoints:
        pid_str = str(ep.pid) if ep.pid is not None else "?"
        # 'encrypted' is not yet exposed in the Endpoint discovery
        # record (rc3 introduced the discovery file alongside
        # registration; rc4 leaves Endpoint dataclass alone).
        # Probe by seed-file existence as a best-effort hint.
        encrypted = _seed_file_exists(ep.name)
        enc_str = "yes" if encrypted else "no"
        alive_str = "yes" if ep.alive else "no"
        name = ep.name[:24]
        transport = ep.transport[:10]
        print(
            f"{name:<24} {transport:<10} {pid_str:<8} "
            f"{enc_str:<10} {alive_str:<6}"
        )
    return 0


def _seed_file_exists(name: str) -> bool:
    """Best-effort probe for a discovery-seed file for ``name``."""
    try:
        from ..bus._seed import seed_path
        return seed_path(name).exists()
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────
# tap
# ─────────────────────────────────────────────────────────────────────


def run_tap(args: argparse.Namespace) -> int:
    """Implementation of ``srmech bus tap NAME``."""
    try:
        seed = _decode_seed(args.seed)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        ch = _bus.connect(args.name, **_bus.secret_kwargs(seed))
    except FileNotFoundError as exc:
        print(f"endpoint not found: {args.name} ({exc})", file=sys.stderr)
        return 1
    except _bus.BusError as exc:
        print(f"bus connect failed: {exc}", file=sys.stderr)
        return 1
    count = 0
    try:
        with ch:
            for event in ch.subscribe():
                if args.type_filter is not None and \
                        event.get("type") != args.type_filter:
                    continue
                print(_format_event(event, args.output_format), flush=True)
                count += 1
                if args.limit is not None and count >= args.limit:
                    break
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 130
    except _bus.BusError as exc:
        print(f"bus error during tap: {exc}", file=sys.stderr)
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────
# pipe
# ─────────────────────────────────────────────────────────────────────


def run_pipe(args: argparse.Namespace) -> int:
    """Implementation of ``srmech bus pipe SRC DST``.

    Streams events from SRC to DST. Optional ``--transform`` is a
    Python expression evaluated per event with ``e`` bound to the
    inbound event dict; the result is the dict sent to DST.

    The seed kwargs for SRC and DST flow into
    :func:`srmech.bus.connect` directly (rc4 wires both into the
    underlying :func:`srmech.bus._pipe.pipe` helper via the local
    loop here, since the helper itself doesn't yet accept seed
    kwargs as of rc3 — added inline for rc4 CLI ergonomics).
    """
    try:
        seed_src = _decode_seed(args.seed_src)
        seed_dst = _decode_seed(args.seed_dst)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    transform_callable = None
    if args.transform is not None:
        # eval'd at use; document the safety implications in --help.
        expr = args.transform

        def _transform(e: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return eval(expr, {"__builtins__": {}}, {"e": e})  # noqa: S307

        transform_callable = _transform

    print(
        f"piping {args.src} -> {args.dst} (Ctrl-C to stop)", flush=True,
    )
    count = 0
    try:
        with _bus.connect(args.src, **_bus.secret_kwargs(seed_src)) as src_ch, \
                _bus.connect(args.dst, **_bus.secret_kwargs(seed_dst)) as dst_ch:
            for event in src_ch.subscribe():
                out = event
                if transform_callable is not None:
                    try:
                        out = transform_callable(event)
                    except Exception as exc:
                        print(
                            f"transform raised; dropping event: {exc}",
                            file=sys.stderr,
                        )
                        continue
                    if out is None:
                        continue
                sink_event = {
                    "type": out.get("type", event.get("type", "_piped")),
                    "payload": out.get("payload", {}),
                }
                try:
                    dst_ch.send(sink_event, expect_reply=False)
                except _bus.BusError as exc:
                    print(f"sink send failed: {exc}", file=sys.stderr)
                    return 1
                count += 1
                print(
                    f"[#{count}] forwarded type={sink_event['type']}",
                    flush=True,
                )
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 130
    except FileNotFoundError as exc:
        print(f"endpoint not found: {exc}", file=sys.stderr)
        return 1
    except _bus.BusError as exc:
        print(f"bus error during pipe: {exc}", file=sys.stderr)
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────
# send
# ─────────────────────────────────────────────────────────────────────


def run_send(args: argparse.Namespace) -> int:
    """Implementation of ``srmech bus send NAME EVENT_JSON``."""
    try:
        seed = _decode_seed(args.seed)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.stdin:
        raw_json = sys.stdin.read()
    else:
        raw_json = args.event_json
    if raw_json is None or not raw_json.strip():
        print(
            "no event JSON provided (pass as positional arg or --stdin)",
            file=sys.stderr,
        )
        return 2
    try:
        event = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(event, dict):
        print(
            f"event must be a JSON object; got {type(event).__name__}",
            file=sys.stderr,
        )
        return 2
    if "type" not in event:
        print(
            "event missing required 'type' key",
            file=sys.stderr,
        )
        return 2

    try:
        ch = _bus.connect(args.name, **_bus.secret_kwargs(seed))
    except FileNotFoundError as exc:
        print(f"endpoint not found: {args.name} ({exc})", file=sys.stderr)
        return 1
    except _bus.BusError as exc:
        print(f"bus connect failed: {exc}", file=sys.stderr)
        return 1
    try:
        with ch:
            try:
                response = ch.send(event, timeout=float(args.timeout))
            except _bus.BusTimeout as exc:
                print(f"timeout: {exc}", file=sys.stderr)
                return 1
            except _bus.BusError as exc:
                print(f"bus error: {exc}", file=sys.stderr)
                return 1
        json.dump(response, sys.stdout, sort_keys=True, default=str)
        sys.stdout.write("\n")
        return 0
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 130


# ─────────────────────────────────────────────────────────────────────
# serve
# ─────────────────────────────────────────────────────────────────────


def _load_handler_module(spec: str):
    """Import ``spec`` of form ``module:attr`` and return the callable."""
    if ":" not in spec:
        raise ValueError(
            f"--handler-module must be 'module:func'; got {spec!r}"
        )
    mod_name, func_name = spec.split(":", 1)
    import importlib
    mod = importlib.import_module(mod_name)
    func = getattr(mod, func_name, None)
    if func is None:
        raise ValueError(
            f"module {mod_name!r} has no attribute {func_name!r}"
        )
    if not callable(func):
        raise ValueError(f"{spec!r} is not callable")
    return func


def _echo_handler(event: dict) -> dict:
    """Default ``--echo`` handler: wrap inbound event as type=echo."""
    return {
        "type": "echo",
        "payload": event,
    }


def run_serve(args: argparse.Namespace) -> int:
    """Implementation of ``srmech bus serve NAME``.

    Blocks until SIGINT (Ctrl-C). Exits 0 on clean shutdown.
    """
    if args.seed_mint and args.seed:
        print(
            "--seed and --seed-mint are mutually exclusive",
            file=sys.stderr,
        )
        return 2
    try:
        seed = _decode_seed(args.seed)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.seed_mint:
        try:
            from ..bus._seed import mint_and_write_seed
            seed = mint_and_write_seed(args.name)
            print(
                f"minted seed; wrote ~/.srmech/bus-{args.name}.seed",
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"seed-mint failed: {exc}", file=sys.stderr)
            return 1

    handler = None
    if args.handler_module is not None:
        try:
            handler = _load_handler_module(args.handler_module)
        except Exception as exc:
            print(f"handler-module load failed: {exc}", file=sys.stderr)
            return 2
    if handler is None:
        if not args.echo:
            print(
                "must pass --echo or --handler-module",
                file=sys.stderr,
            )
            return 2
        handler = _echo_handler

    try:
        ep = _bus.serve(args.name, handler=handler, **_bus.secret_kwargs(seed))
    except OSError as exc:
        print(f"serve failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"serving '{args.name}' (transport={ep.transport_kind}; "
        f"encrypted={ep.encrypted}; Ctrl-C to stop)",
        flush=True,
    )
    stop_signal = {"received": False}

    def _on_sigint(signum, frame):  # noqa: ARG001
        stop_signal["received"] = True

    try:
        signal.signal(signal.SIGINT, _on_sigint)
    except (ValueError, OSError):
        # Some embedded contexts (e.g. non-main thread) can't set;
        # fall back to KeyboardInterrupt-only.
        pass
    try:
        while not stop_signal["received"]:
            try:
                time.sleep(0.25)
            except KeyboardInterrupt:
                break
    finally:
        try:
            ep.stop()
        except Exception:
            pass
    print("server stopped.", file=sys.stderr)
    return 0


__all__ = [
    "add_arguments",
    "run",
    "run_list",
    "run_tap",
    "run_pipe",
    "run_send",
    "run_serve",
]
