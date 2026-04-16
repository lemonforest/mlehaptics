"""logo_py — CLI for the LOGO HDC research spike.

Modeled loosely on chess-spectral's `spectral_py.py`. Verb structure:

    python logo_py.py parse     <src.logo>            — parse + dump AST
    python logo_py.py trace     <src.logo>            — run + dump turtle trace
    python logo_py.py encode    <src.logo>            — emit 320-dim geometry HV
    python logo_py.py fiber1                          — build F₁, print SVD report
    python logo_py.py fiber2                          — build F₂, print SVD report + deflated self-sim
    python logo_py.py csv       [-o OUT]              — emit per-program corpus CSV
    python logo_py.py version

Programs can be read from a file or piped in on stdin ('-').
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from logo_parser import parse
from logo_interp import run
from logo_corpus import CORPUS, get as get_corpus
from logo_encode_geometry import encode_geometry, geometry_grid, IRREP_DIM
from logo_csv_export import export_csv


VERSION = "0.1.0"


# ─── Source loading ────────────────────────────────────────────────

def _load_src(src_arg: str) -> str:
    """Load program source from a path, corpus entry name, or stdin ('-')."""
    if src_arg == "-":
        return sys.stdin.read()
    p = Path(src_arg)
    if p.exists():
        return p.read_text()
    # Fall back to corpus lookup — convenience for verbs like
    # `logo_py encode square`.
    try:
        return get_corpus(src_arg).source
    except KeyError:
        raise SystemExit(
            f"Not a file, not a corpus name: {src_arg!r}. "
            f"Try one of: {', '.join(e.name for e in CORPUS[:6])}, ..."
        )


# ─── Verbs ─────────────────────────────────────────────────────────

def cmd_parse(args: argparse.Namespace) -> int:
    prog = parse(_load_src(args.src))
    print(prog)
    return 0


def cmd_trace(args: argparse.Namespace) -> int:
    prog = parse(_load_src(args.src))
    ctx = run(prog)
    t = ctx.trace
    out = {
        "n_segments": len(t.segments),
        "n_pendown":  sum(1 for s in t.segments if s.pen_down),
        "bbox":       list(t.bbox()),
        "segments": [
            [s.x0, s.y0, s.x1, s.y1, int(s.pen_down)]
            for s in t.segments
        ],
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


def cmd_encode(args: argparse.Namespace) -> int:
    prog = parse(_load_src(args.src))
    ctx = run(prog)
    g = encode_geometry(ctx.trace)
    # Print summary + per-channel energies for a readable overview.
    channels = ("A1", "A2", "B1", "B2", "E")
    energies = {ch: float(np.dot(g[i*64:(i+1)*64], g[i*64:(i+1)*64]))
                for i, ch in enumerate(channels)}
    print(f"geom_hv dim={IRREP_DIM}  |g|={np.linalg.norm(g):.3e}")
    for ch, e in energies.items():
        print(f"  E_{ch} = {e:.3e}")
    if args.dump:
        # full vector, space-separated
        print(" ".join(f"{v:+.3e}" for v in g))
    return 0


def cmd_fiber1(_args: argparse.Namespace) -> int:
    from logo_build_splits import ALL_COMMANDS, f1_coincidences_corpus
    from logo_ast import ALL_RULES
    from logo_hdc import build_vocab_codebook, build_rule_codebook
    from logo_hdc.fiber import (
        build_fiber_matrix, svd_report, fiber_to_hdc, unbind_retrieve,
    )

    progs = [parse(e.source) for e in CORPUS]
    coinc = f1_coincidences_corpus(progs)
    M = build_fiber_matrix(coinc,
                           left_order=ALL_COMMANDS,
                           right_order=ALL_RULES)
    rep = svd_report(M)
    print(f"F1 matrix  shape={M.shape}  rank={rep.rank}")
    print("singular values:")
    for i, sv in enumerate(rep.singular_values):
        if sv > rep.rank_rtol * rep.singular_values[0]:
            print(f"  sigma[{i}] = {sv:.3f}")
    if rep.null_rows:
        print(f"null rows (cmds with no coincidence): "
              f"{[ALL_COMMANDS[i] for i in rep.null_rows]}")
    if rep.null_cols:
        print(f"null cols (rules with no coincidence): "
              f"{[ALL_RULES[i] for i in rep.null_cols]}")
    # Top features per mode
    print()
    print("Top-loading (command, rule) per dominant mode:")
    for k in range(min(4, rep.rank)):
        li = int(np.argmax(np.abs(rep.U[:, k])))
        ri = int(np.argmax(np.abs(rep.Vt[k, :])))
        print(f"  mode{k}  sigma={rep.singular_values[k]:.2f}  "
              f"{ALL_COMMANDS[li]:>8} <-> {ALL_RULES[ri]}")

    # HDC retrieval check (Phase 1c fix: per-row normalization).
    vocab_cb = build_vocab_codebook()
    rule_cb  = build_rule_codebook()
    rule_only_cb = {r: rule_cb[r] for r in ALL_RULES}
    F = fiber_to_hdc(M, vocab_cb, rule_cb,
                     left_order=ALL_COMMANDS, right_order=ALL_RULES)
    correct = 0
    total = 0
    for ci, c in enumerate(ALL_COMMANDS):
        if M[ci, :].sum() == 0:
            continue
        true_top = ALL_RULES[int(np.argmax(M[ci, :]))]
        pred_name, _pred_sim = unbind_retrieve(
            F, vocab_cb[c], rule_only_cb, top_k=1)[0]
        if pred_name == true_top:
            correct += 1
        total += 1
    print()
    print(f"HDC retrieval top-1 accuracy "
          f"(per-row-normalized fiber): {correct}/{total} "
          f"= {100*correct/total:.0f}%")
    return 0


def cmd_fiber2(_args: argparse.Namespace) -> int:
    from logo_fiber2 import (
        F2Payload, build_f2_matrix, program_features, EXTENDED_ORDER,
    )
    payload = F2Payload()
    for e in CORPUS:
        prog = parse(e.source)
        ctx = run(prog)
        payload.add(e.name, program_features(prog), encode_geometry(ctx.trace))
    M = build_f2_matrix(payload, right_order=EXTENDED_ORDER)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    rank = int(np.sum(s > 1e-6 * s[0]))
    print(f"F2 matrix  shape={M.shape}  rank={rank}")
    print("top singular values:")
    for i in range(min(8, rank)):
        idx = int(np.argmax(np.abs(U[:, i])))
        print(f"  sigma[{i}] = {s[i]:.3f}   dominant feat: "
              f"{EXTENDED_ORDER[idx]}  ({U[idx,i]:+.2f})")
    # Deflated self-similarity summary
    M_hi = M - s[0] * np.outer(U[:, 0], Vt[0])
    G = np.array(payload.geom_hvs)
    G_hi = G - G.mean(axis=0, keepdims=True)
    G_hi_n = G_hi / (np.linalg.norm(G_hi, axis=1, keepdims=True) + 1e-12)
    idx_of = {r: i for i, r in enumerate(EXTENDED_ORDER)}
    def featvec(rc):
        v = np.zeros(len(EXTENDED_ORDER))
        for r, c in rc.items():
            if r in idx_of: v[idx_of[r]] = c
        t = v.sum()
        return v / t if t > 0 else v
    print()
    print("Deflated self-similarity (pred_geom vs actual, mode-0 removed):")
    for p_idx, name in enumerate(payload.names):
        v = featvec(payload.rule_counts[p_idx])
        pred = M_hi.T @ v
        pn = pred / (np.linalg.norm(pred) + 1e-12)
        sim_self = float(G_hi_n[p_idx] @ pn)
        print(f"  {name:18s}  sim_self={sim_self:+.3f}")
    return 0


def cmd_transport(args: argparse.Namespace) -> int:
    from logo_transport import (
        build_context,
        polygon_pair_table, print_polygon_pair_table, DEFAULT_POLYGON_PAIRS,
        chain_transport, print_chain_result,
        feature_transport_table, print_feature_transport_table,
        mode_attribution, print_mode_attribution,
        chain_collapse_test, print_chain_collapse,
        cycle_holonomy, print_holonomy,
        chirality_test, print_chirality,
        holdout_transport_table, print_holdout_report,
        partial_trace_transport_table, print_partial_trace_report,
        fiber_drift, print_fiber_drift,
        spiral_extrapolation_probe, print_spiral_extrapolation,
    )
    cx = build_context()

    ran_anything = False

    # L7 verbs take priority if provided — they reset the default
    # polygon-pair fallback so we don't clutter the output.
    if args.holdout:
        names = [s.strip() for s in args.holdout.split(",") if s.strip()]
        print_holdout_report(holdout_transport_table(names))
        ran_anything = True

    if args.partial:
        parts = [int(s.strip()) for s in args.partial.split(",") if s.strip()]
        if len(parts) == 1:
            n = parts[0]
            print_partial_trace_report(partial_trace_transport_table(n, n))
        elif len(parts) >= 2:
            if ran_anything: print()
            print_partial_trace_report(
                partial_trace_transport_table(parts[0], parts[1])
            )
        ran_anything = True

    if args.drift:
        parts = [int(s.strip()) for s in args.drift.split(",") if s.strip()]
        if len(parts) >= 2:
            if ran_anything: print()
            print_fiber_drift(fiber_drift(parts[0], parts[1]))
            ran_anything = True

    if args.spiral_extrapolate:
        spec = args.spiral_extrapolate
        # Accept "n_early,n_late" or "name,n_early,n_late"
        parts = [s.strip() for s in spec.split(",") if s.strip()]
        if len(parts) == 2:
            name = "spiral_square"
            ne, nl = int(parts[0]), int(parts[1])
        elif len(parts) >= 3:
            name, ne, nl = parts[0], int(parts[1]), int(parts[2])
        else:
            name, ne, nl = "spiral_square", 10, 60
        if ran_anything: print()
        print_spiral_extrapolation(
            spiral_extrapolation_probe(name, ne, nl)
        )
        ran_anything = True

    if args.pairs or (not any([args.chain, args.characterize,
                                args.modes, args.topology,
                                args.holdout, args.partial, args.drift,
                                args.spiral_extrapolate])):
        # Default: polygon pairs.
        pairs = DEFAULT_POLYGON_PAIRS
        if isinstance(args.pairs, str) and args.pairs != "polygons":
            # Comma-separated "a,b;c,d" pair list.
            spec = []
            for chunk in args.pairs.split(";"):
                if "," in chunk:
                    a, b = chunk.split(",", 1)
                    spec.append((a.strip(), b.strip()))
            if spec:
                pairs = spec
        print_polygon_pair_table(polygon_pair_table(cx, pairs))
        ran_anything = True

    if args.chain:
        if ran_anything: print()
        a, b = (args.chain.split(",", 1) if "," in args.chain
                else ("square", "spiral_square"))
        print_chain_result(chain_transport(cx, (a.strip(), b.strip())))
        ran_anything = True

    if args.characterize:
        if ran_anything: print()
        print_feature_transport_table(feature_transport_table(cx))
        ran_anything = True

    if args.modes:
        if ran_anything: print()
        a, b = (args.modes.split(",", 1) if "," in args.modes
                else ("square", "triangle"))
        print_mode_attribution(mode_attribution(cx, (a.strip(), b.strip())))
        ran_anything = True

    if args.topology:
        if ran_anything: print()
        print_chain_collapse(chain_collapse_test(cx))
        print()
        print_holonomy(cycle_holonomy(cx))
        print()
        print_chirality(chirality_test(cx))
        ran_anything = True

    return 0


def cmd_csv(args: argparse.Namespace) -> int:
    if args.out:
        with open(args.out, "w", newline="") as f:
            n = export_csv(CORPUS, f)
        print(f"wrote {n} rows -> {args.out}", file=sys.stderr)
    else:
        export_csv(CORPUS, sys.stdout)
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"logo_py {VERSION}")
    return 0


# ─── Argparse skeleton ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logo_py",
        description="CLI for the LOGO HDC research spike.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", help="parse a program and dump its AST")
    sp.add_argument("src", help="file path, corpus entry name, or '-' for stdin")
    sp.set_defaults(func=cmd_parse)

    sp = sub.add_parser("trace", help="run a program and dump turtle trace (JSON)")
    sp.add_argument("src")
    sp.set_defaults(func=cmd_trace)

    sp = sub.add_parser("encode", help="encode a program's geometry HV")
    sp.add_argument("src")
    sp.add_argument("--dump", action="store_true",
                    help="print the full 320-dim vector, not just the summary")
    sp.set_defaults(func=cmd_encode)

    sp = sub.add_parser("fiber1", help="build F1 (vocab ↔ syntax), print SVD")
    sp.set_defaults(func=cmd_fiber1)

    sp = sub.add_parser("fiber2", help="build F2 (syntax ↔ geometry), print SVD + self-sim")
    sp.set_defaults(func=cmd_fiber2)

    sp = sub.add_parser("transport",
                        help="fiber transport experiments (Phase 2 / 2e)")
    sp.add_argument("--pairs", nargs="?", const="polygons", default=None,
                    help="polygon-pair transport table (default if no flags). "
                         "Pass 'a,b;c,d' for custom pairs, or 'polygons'.")
    sp.add_argument("--chain", nargs="?", const="square,spiral_square",
                    default=None,
                    help="chain transport vocab->syntax->geometry "
                         "(default: square,spiral_square)")
    sp.add_argument("--characterize", action="store_true",
                    help="per-feature transport(N) D4 decomposition")
    sp.add_argument("--modes", nargs="?", const="square,triangle", default=None,
                    help="per-SVD-mode attribution for a pair "
                         "(default: square,triangle)")
    sp.add_argument("--topology", action="store_true",
                    help="chain-collapse, cycle-holonomy, chirality tests")
    sp.add_argument("--holdout", default=None,
                    help="L7a: rebuild fiber excluding the named programs "
                         "(comma-separated, e.g. 'pentagon,octagon')")
    sp.add_argument("--partial", default=None,
                    help="L7b: partial-trace transport. 'N' for "
                         "build=target=N, 'N,M' for build-at-N target-at-M.")
    sp.add_argument("--drift", default=None,
                    help="L7b: fiber-drift matrix between anchors 'N,M'.")
    sp.add_argument("--spiral-extrapolate", dest="spiral_extrapolate",
                    default=None,
                    help="L7b.5: spiral extrapolation probe. 'N,M' for "
                         "spiral_square, or 'name,N,M' for a custom program.")
    sp.set_defaults(func=cmd_transport)

    sp = sub.add_parser("csv", help="emit per-program corpus CSV")
    sp.add_argument("-o", "--out", help="output path (default: stdout)")
    sp.set_defaults(func=cmd_csv)

    sp = sub.add_parser("version", help="print version")
    sp.set_defaults(func=cmd_version)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
