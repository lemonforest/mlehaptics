"""Per-program CSV export for the LOGO HDC pipeline.

Columns
-------
    name, family, symmetry,
    n_stmts, n_rules_static, n_cmds_static,
    exec_steps, n_segments, n_pendown,
    bbox_w, bbox_h, aspect,
    f2_self_sim_raw, f2_self_sim_deflated,
    f2_top_mode_loading,
    E_A1, E_A2, E_B1, E_B2, E_E,
    geom_norm

Number formatting mirrors chess_spectral.csv_export.fmt_num so any
downstream chat/LLM paste looks the same.
"""
from __future__ import annotations

import csv
import io
import math
from typing import Iterable, List, TextIO

import numpy as np

from logo_ast import walk
from logo_parser import parse
from logo_interp import run, static_rule_counts, static_cmd_counts
from logo_corpus import CORPUS, CorpusEntry
from logo_encode_geometry import encode_geometry, IRREP_DIM
from logo_fiber2 import (
    F2Payload, build_f2_matrix, program_features, EXTENDED_ORDER,
)


# Column ordering — SSOT for both header row and the per-row writer.
COLUMNS: List[str] = [
    "name", "family", "symmetry",
    "n_stmts", "n_rules_static", "n_cmds_static",
    "exec_steps", "n_segments", "n_pendown",
    "bbox_w", "bbox_h", "aspect",
    "f2_self_sim_raw", "f2_self_sim_deflated",
    "f2_transport_cos_nn", "chain_transport_cos",
    "E_A1", "E_A2", "E_B1", "E_B2", "E_E",
    "geom_norm",
]


# Pairs that get a populated `chain_transport_cos`. Defined here as
# SSOT so logo_transport's CLI verb and this exporter agree.
CHAIN_PAIRS = [("square", "spiral_square")]


# ─── Number formatting (mirrors chess-spectral) ────────────────────

def fmt_num(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    ax = abs(x)
    if ax < 1e-6:
        return "0"
    if ax >= 100.0:
        return f"{x:.0f}"
    if ax >= 1.0:
        return f"{x:.2f}"
    if ax >= 0.01:
        return f"{x:.3f}"
    return f"{x:.2e}"


# ─── Corpus → payload ──────────────────────────────────────────────

def build_payload(corpus: Iterable[CorpusEntry]) -> F2Payload:
    payload = F2Payload()
    for e in corpus:
        prog = parse(e.source)
        ctx = run(prog)
        payload.add(e.name, program_features(prog), encode_geometry(ctx.trace))
    return payload


# ─── Per-program row computation ───────────────────────────────────

def _channel_energy(geom_hv: np.ndarray, channel_idx: int) -> float:
    """Energy ||channel||² for a 320-dim D4-irrep HV, 64 dims per channel."""
    start = channel_idx * 64
    seg = geom_hv[start:start + 64]
    return float(np.dot(seg, seg))


def export_csv(corpus: Iterable[CorpusEntry], out: TextIO) -> int:
    """Write per-program CSV rows for `corpus` to `out`. Returns row count."""
    corpus = list(corpus)
    payload = build_payload(corpus)

    # Build F₂ and its SVD; deflate dominant mode for the "deflated"
    # self-similarity metric (polygon-symmetry recovery signal lives
    # in subdominant modes — see logo_research_notebook.md).
    M = build_f2_matrix(payload, right_order=EXTENDED_ORDER)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    M_hi = M - s[0] * np.outer(U[:, 0], Vt[0])

    G = np.array(payload.geom_hvs)
    Gn = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-12)
    G_hi = G - G.mean(axis=0, keepdims=True)
    G_hi_n = G_hi / (np.linalg.norm(G_hi, axis=1, keepdims=True) + 1e-12)

    idx_of_feat = {r: i for i, r in enumerate(EXTENDED_ORDER)}

    def featvec(rc) -> np.ndarray:
        v = np.zeros(len(EXTENDED_ORDER))
        for r, c in rc.items():
            if r in idx_of_feat:
                v[idx_of_feat[r]] = c
        tot = float(v.sum())
        return v / tot if tot > 0.0 else v

    # Mean feature vector across the corpus — the "from-mean" reference
    # for the per-program transport cosine column.
    feat_mean = np.mean(
        [featvec(rc) for rc in payload.rule_counts], axis=0)
    g_mean = G.mean(axis=0)

    # Pre-compute chain-transport cosines (one per declared CHAIN_PAIR).
    chain_cos: dict = {}
    try:
        from logo_transport import build_context, chain_transport
        cx = build_context(corpus)
        for a, b in CHAIN_PAIRS:
            if (a in cx.name_to_idx) and (b in cx.name_to_idx):
                r = chain_transport(cx, (a, b))
                chain_cos[a] = r.cos_geom_chain_actual
                chain_cos[b] = r.cos_geom_chain_actual
    except Exception:
        # Don't let chain transport break CSV export.
        chain_cos = {}

    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)

    n_rows = 0
    for p_idx, entry in enumerate(corpus):
        prog = parse(entry.source)
        ctx = run(prog)

        # Static vs dynamic counts
        rc_static = static_rule_counts(prog)
        cc_static = static_cmd_counts(prog)
        n_stmts = sum(1 for n in walk(prog)
                      if type(n).__name__.endswith("Stmt"))

        trace = ctx.trace
        segs = trace.segments
        n_pendown = sum(1 for s in segs if s.pen_down)
        x0, y0, x1, y1 = trace.bbox()
        bw, bh = x1 - x0, y1 - y0
        aspect = (bw / bh) if bh > 0 else float("nan")

        # Self-similarity: pred_geom = M.T @ featvec cos vs actual geom
        v = featvec(payload.rule_counts[p_idx])
        pred     = M.T    @ v
        pred_hi  = M_hi.T @ v
        pn  = pred    / (np.linalg.norm(pred)    + 1e-12)
        phn = pred_hi / (np.linalg.norm(pred_hi) + 1e-12)
        self_sim_raw      = float(Gn[p_idx]    @ pn)
        self_sim_deflated = float(G_hi_n[p_idx] @ phn)

        # f2_transport_cos_nn: cos(M_hi.T @ Δfeat_from_mean,
        #                          G_hi[idx]) — transport-from-mean signal.
        dv  = v - feat_mean
        dgp = M_hi.T @ dv
        dga = G[p_idx] - g_mean
        if np.linalg.norm(dgp) > 0 and np.linalg.norm(dga) > 0:
            f2_transport_cos = float(
                (dgp @ dga) / (np.linalg.norm(dgp) * np.linalg.norm(dga))
            )
        else:
            f2_transport_cos = 0.0
        chain_cos_val = chain_cos.get(entry.name, None)

        # D4 irrep channel energies (indices 0..4)
        g = payload.geom_hvs[p_idx]
        e_A1 = _channel_energy(g, 0)
        e_A2 = _channel_energy(g, 1)
        e_B1 = _channel_energy(g, 2)
        e_B2 = _channel_energy(g, 3)
        e_E  = _channel_energy(g, 4)

        row = [
            entry.name,
            entry.family,
            entry.symmetry,
            n_stmts,
            sum(rc_static.values()),
            sum(cc_static.values()),
            ctx.steps,
            len(segs),
            n_pendown,
            fmt_num(bw),
            fmt_num(bh),
            fmt_num(aspect),
            fmt_num(self_sim_raw),
            fmt_num(self_sim_deflated),
            fmt_num(f2_transport_cos),
            fmt_num(chain_cos_val) if chain_cos_val is not None else "",
            fmt_num(e_A1),
            fmt_num(e_A2),
            fmt_num(e_B1),
            fmt_num(e_B2),
            fmt_num(e_E),
            fmt_num(float(np.linalg.norm(g))),
        ]
        writer.writerow(row)
        n_rows += 1

    return n_rows


def export_csv_to_string(corpus: Iterable[CorpusEntry]) -> str:
    buf = io.StringIO()
    export_csv(corpus, buf)
    return buf.getvalue()
