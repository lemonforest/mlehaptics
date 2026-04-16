"""Phase 2 — fiber-as-transport-map experiments.

The plan's Iteration-2 question: are F₁/F₂ static co-occurrence summaries,
or do they function as **predictive transport maps**? `Δg_pred = M₂ᵀ · Δv`
should let a syntax-feature delta predict a geometry-irrep delta. If yes,
the split-object pattern picks up a generative interpretation.

Four experiments:

    2a  polygon-pair single-fiber transport         polygon_pair_table()
    2b  chain transport vocab → syntax → geometry   chain_transport()
    2c  per-feature transport(N) D4 decomposition   feature_transport_table()
    2d  per-SVD-mode attribution                    mode_attribution()

Conventions (must match `cmd_fiber2` in `logo_py.py` exactly so numbers
are interpretable):

* Geometry HVs are L2-normalized before accumulation into M₂
  (`build_f2_matrix(normalize_geom=True)`, default).
* Per-program syntax-feature vectors are L1-normalized
  (`featvec(rc) = v / sum(v)`).
* The "actual" delta lives in the same normalized-geom space as the
  prediction: G_n[idx_b] - G_n[idx_a] where G_n is each row L2-norm 1.
* Deflation removes the dominant SVD mode: M_hi = M - σ₀ u₀ v₀ᵀ. The
  deflated geometry space subtracts the mean-direction of G_n.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from logo_corpus import CORPUS, get as get_corpus
from logo_parser import parse
from logo_interp import run
from logo_encode_geometry import encode_geometry, IRREP_DIM
from logo_irrep import IRREP_NAMES, BOARD_DIM
from logo_fiber2 import (
    F2Payload, build_f2_matrix, program_features, EXTENDED_ORDER,
)


# ─── Shared payload / SVD bundle ──────────────────────────────────

@dataclass
class TransportContext:
    """Pre-computed bundle reused across all transport experiments."""
    payload: F2Payload
    feat_order: List[str]                    # EXTENDED_ORDER
    M: np.ndarray                            # (|feat|, 320)  raw F2
    U: np.ndarray                            # (|feat|, k)    SVD left
    s: np.ndarray                            # (k,)
    Vt: np.ndarray                           # (k, 320)
    M_hi: np.ndarray                         # M with mode-0 removed
    G_n: np.ndarray                          # (|progs|, 320) row-L2-normed
    G_hi: np.ndarray                         # G_n - mean(G_n)
    name_to_idx: Dict[str, int]
    feat_to_idx: Dict[str, int]


def build_context(corpus=CORPUS) -> TransportContext:
    """Build the F₂ context (matches cmd_fiber2 numerics)."""
    payload = F2Payload()
    for e in corpus:
        prog = parse(e.source)
        ctx  = run(prog)
        payload.add(e.name, program_features(prog), encode_geometry(ctx.trace))
    M = build_f2_matrix(payload, right_order=EXTENDED_ORDER)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    M_hi = M - s[0] * np.outer(U[:, 0], Vt[0])
    G = np.array(payload.geom_hvs)
    norms = np.linalg.norm(G, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    G_n = G / norms
    G_hi = G_n - G_n.mean(axis=0, keepdims=True)
    return TransportContext(
        payload=payload,
        feat_order=list(EXTENDED_ORDER),
        M=M, U=U, s=s, Vt=Vt, M_hi=M_hi,
        G_n=G_n, G_hi=G_hi,
        name_to_idx={n: i for i, n in enumerate(payload.names)},
        feat_to_idx={f: i for i, f in enumerate(EXTENDED_ORDER)},
    )


# ─── Feature-vector helpers ───────────────────────────────────────

def featvec(rc: Counter, feat_to_idx: Dict[str, int]) -> np.ndarray:
    """L1-normalized feature vector over EXTENDED_ORDER."""
    v = np.zeros(len(feat_to_idx))
    for r, c in rc.items():
        if r in feat_to_idx:
            v[feat_to_idx[r]] = c
    t = v.sum()
    return v / t if t > 0 else v


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(a @ b) / (na * nb)


def _norm_unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


# ─── 2a: Polygon-pair transport ───────────────────────────────────

DEFAULT_POLYGON_PAIRS: List[Tuple[str, str]] = [
    ("square",   "triangle"),
    ("square",   "hexagon"),
    ("triangle", "pentagon"),
    ("hexagon",  "octagon"),
    ("pentagon", "octagon"),
    ("square",   "dodecagon"),
]


@dataclass
class PairResult:
    a: str
    b: str
    cos_raw: float        # cos(M.T @ Δv,    Δg_actual_in_G_n)
    cos_deflated: float   # cos(M_hi.T @ Δv, Δg_actual_in_G_hi)
    irrep_energy: Dict[str, float]   # |Δg_actual|² split by D4 channel


def _irrep_energy(delta_g: np.ndarray) -> Dict[str, float]:
    """Split a 320-dim delta into per-irrep energy fractions."""
    total = float(delta_g @ delta_g)
    out: Dict[str, float] = {}
    if total <= 0.0:
        return {n: 0.0 for n in IRREP_NAMES}
    for i, name in enumerate(IRREP_NAMES):
        seg = delta_g[i * BOARD_DIM:(i + 1) * BOARD_DIM]
        out[name] = float(seg @ seg) / total
    return out


def polygon_pair_table(
    cx: TransportContext,
    pairs: Sequence[Tuple[str, str]] = DEFAULT_POLYGON_PAIRS,
) -> List[PairResult]:
    """For each (a, b), compute Δv, predict Δg, compare to actual."""
    rows: List[PairResult] = []
    for a, b in pairs:
        ia, ib = cx.name_to_idx[a], cx.name_to_idx[b]
        va = featvec(cx.payload.rule_counts[ia], cx.feat_to_idx)
        vb = featvec(cx.payload.rule_counts[ib], cx.feat_to_idx)
        dv = vb - va
        # raw: predict and compare in normalized-G space directly
        dg_actual_raw = cx.G_n[ib] - cx.G_n[ia]
        dg_pred_raw   = cx.M.T @ dv
        # deflated: same vectors with mean (≈ mode-0 direction) removed
        dg_actual_def = cx.G_hi[ib] - cx.G_hi[ia]
        dg_pred_def   = cx.M_hi.T @ dv
        rows.append(PairResult(
            a=a, b=b,
            cos_raw=_cos(dg_pred_raw, dg_actual_raw),
            cos_deflated=_cos(dg_pred_def, dg_actual_def),
            irrep_energy=_irrep_energy(dg_actual_raw),
        ))
    return rows


def print_polygon_pair_table(rows: Sequence[PairResult]) -> None:
    print("Polygon-pair transport (Δg_pred = M.T @ Δv vs Δg_actual):")
    print(f"  {'pair':28s} {'cos_raw':>9s} {'cos_def':>9s}   "
          f"D4 energy split (A1/A2/B1/B2/E)")
    for r in rows:
        eg = r.irrep_energy
        bar = " ".join(f"{eg[n]*100:4.0f}%" for n in IRREP_NAMES)
        pair = f"{r.a} -> {r.b}"
        print(f"  {pair:28s} {r.cos_raw:+9.3f} {r.cos_deflated:+9.3f}   {bar}")
    n = len(rows)
    n_def_better = sum(1 for r in rows if r.cos_deflated >= r.cos_raw)
    n_above_30   = sum(1 for r in rows if r.cos_deflated > 0.30)
    print()
    print(f"  L6a: cos_deflated > 0.30 in {n_above_30}/{n} pairs"
          f"   ({'PASS' if n_above_30 >= n - 1 else 'CHECK'})")
    print(f"  L6b: deflated >= raw  in {n_def_better}/{n} pairs"
          f"   ({'PASS' if n_def_better >= 4 else 'CHECK'})")


# ─── 2b: Chain transport (vocab → syntax → geometry) ──────────────

def _vocab_weight_vector(prog, vocab_cb, command_order: Sequence[str]) -> np.ndarray:
    """Per-command count vector (uniform — we use raw command counts)."""
    from logo_encode_vocab import command_sequence
    seq = Counter(command_sequence(prog))
    w = np.zeros(len(command_order))
    cmd_to_idx = {c: i for i, c in enumerate(command_order)}
    for c, n in seq.items():
        if c in cmd_to_idx:
            w[cmd_to_idx[c]] = n
    t = w.sum()
    return w / t if t > 0 else w


@dataclass
class ChainResult:
    a: str
    b: str
    cos_syntax_pred_actual: float        # via F1
    cos_geom_chain_actual: float         # via F1 then F2
    cos_geom_direct_actual: float        # via F2 with featvec delta (baseline)


def chain_transport(
    cx: TransportContext,
    pair: Tuple[str, str] = ("square", "spiral_square"),
) -> ChainResult:
    """vocab Δ → syntax Δ (via F₁ᵀ) → geometry Δ (via M₂ᵀ).

    Quality is double-approximated; baseline is direct featvec-delta
    transport so we can quantify the chain's penalty.
    """
    # Local imports keep the module light when only Phase 2a is wanted.
    from logo_build_splits import f1_coincidences_corpus, ALL_COMMANDS
    from logo_ast import ALL_RULES
    from logo_hdc import (
        build_vocab_codebook, build_rule_codebook,
        build_fiber_matrix,
    )

    a, b = pair
    ia, ib = cx.name_to_idx[a], cx.name_to_idx[b]

    # Build F₁ matrix (small + cheap).
    progs = [parse(e.source) for e in CORPUS]
    coinc = f1_coincidences_corpus(progs)
    M1 = build_fiber_matrix(coinc,
                            left_order=ALL_COMMANDS,
                            right_order=ALL_RULES)

    # vocab side: per-command count delta (b - a) in ALL_COMMANDS axis.
    vocab_cb = build_vocab_codebook()
    prog_a = parse(get_corpus(a).source)
    prog_b = parse(get_corpus(b).source)
    w_a = _vocab_weight_vector(prog_a, vocab_cb, ALL_COMMANDS)
    w_b = _vocab_weight_vector(prog_b, vocab_cb, ALL_COMMANDS)
    dw  = w_b - w_a

    # syntax-feature delta, predicted via M1.T (rules axis).
    # Lift into EXTENDED_ORDER by zero-fill: chain transport cannot
    # predict repeat_n=N value-fingerprint dims (those don't live in
    # F₁'s rule axis at all).
    dv_rules_pred = M1.T @ dw
    dv_extended_pred = np.zeros(len(cx.feat_order))
    rule_idx_in_ext = {r: cx.feat_to_idx[r] for r in ALL_RULES if r in cx.feat_to_idx}
    for r, idx_ext in rule_idx_in_ext.items():
        dv_extended_pred[idx_ext] = dv_rules_pred[ALL_RULES.index(r)]

    # syntax-feature delta, actual.
    va = featvec(cx.payload.rule_counts[ia], cx.feat_to_idx)
    vb = featvec(cx.payload.rule_counts[ib], cx.feat_to_idx)
    dv_actual = vb - va
    # Restrict actual to the rules subspace for fair vs-pred comparison.
    rules_mask = np.zeros(len(cx.feat_order), dtype=bool)
    for r in ALL_RULES:
        if r in cx.feat_to_idx:
            rules_mask[cx.feat_to_idx[r]] = True
    cos_syntax = _cos(dv_extended_pred[rules_mask], dv_actual[rules_mask])

    # geometry delta predictions (deflated F₂).
    dg_chain  = cx.M_hi.T @ dv_extended_pred
    dg_direct = cx.M_hi.T @ dv_actual
    dg_actual = cx.G_hi[ib] - cx.G_hi[ia]

    return ChainResult(
        a=a, b=b,
        cos_syntax_pred_actual = cos_syntax,
        cos_geom_chain_actual  = _cos(dg_chain,  dg_actual),
        cos_geom_direct_actual = _cos(dg_direct, dg_actual),
    )


def print_chain_result(r: ChainResult) -> None:
    print(f"Chain transport: {r.a} -> {r.b}")
    print(f"  cos(syntax_pred, syntax_actual) [via F1]   = {r.cos_syntax_pred_actual:+.3f}")
    print(f"  cos(geom_chain,  geom_actual)   [F1 -> F2] = {r.cos_geom_chain_actual:+.3f}")
    print(f"  cos(geom_direct, geom_actual)   [F2 only ] = {r.cos_geom_direct_actual:+.3f}")
    print()
    if r.cos_geom_chain_actual > 0.10:
        print(f"  L6c: chain cos > 0.10  ->  PASS")
    else:
        print(f"  L6c: chain cos > 0.10  ->  MISS  "
              f"(actual {r.cos_geom_chain_actual:+.3f})")


# ─── 2c: Per-feature transport(N) D4 characterization ─────────────

@dataclass
class FeatureTransport:
    feat: str
    energy_per_irrep: Dict[str, float]   # fraction of |transport|² per channel
    norm: float                          # |transport(N)|


def feature_transport_table(
    cx: TransportContext,
    feat_names: Sequence[str] = (
        "repeat_n=3", "repeat_n=4", "repeat_n=5",
        "repeat_n=6", "repeat_n=8", "repeat_n=12",
    ),
    *,
    use_deflated: bool = True,
) -> List[FeatureTransport]:
    """transport(feat) = M.T @ e_feat  (deflated by default)."""
    M = cx.M_hi if use_deflated else cx.M
    rows: List[FeatureTransport] = []
    for f in feat_names:
        if f not in cx.feat_to_idx:
            continue
        e = np.zeros(len(cx.feat_order))
        e[cx.feat_to_idx[f]] = 1.0
        t = M.T @ e
        rows.append(FeatureTransport(
            feat=f,
            energy_per_irrep=_irrep_energy(t),
            norm=float(np.linalg.norm(t)),
        ))
    return rows


def print_feature_transport_table(rows: Sequence[FeatureTransport]) -> None:
    print("Per-feature transport(N) — D4 channel decomposition (deflated):")
    print(f"  {'feature':16s} {'|t|':>8s}   "
          f"{'A1':>5s} {'A2':>5s} {'B1':>5s} {'B2':>5s} {'E':>5s}")
    for r in rows:
        eg = r.energy_per_irrep
        print(f"  {r.feat:16s} {r.norm:8.3f}   "
              f"{eg['A1']*100:4.0f}% {eg['A2']*100:4.0f}% "
              f"{eg['B1']*100:4.0f}% {eg['B2']*100:4.0f}% "
              f"{eg['E']*100:4.0f}%")
    print()
    print("  L6d: expect transport(4/8/12) concentrated in A1;")
    print("        transport(3) spread to B1+B2+E; transport(5) mixes A1+E.")


# ─── 2d: Per-SVD-mode attribution ─────────────────────────────────

@dataclass
class ModeAttribution:
    pair: Tuple[str, str]
    cos_per_mode: List[float]            # cos(term_k, Δg_actual)
    pred_frac_per_mode: List[float]      # ‖term_k‖² / ‖Δg_pred‖²
    cum_cos_per_mode: List[float]        # cum cos to Δg_actual after k terms
    sigmas: List[float]                  # σ_k for context


def mode_attribution(
    cx: TransportContext,
    pair: Tuple[str, str] = ("square", "triangle"),
    *,
    n_modes: int = 8,
) -> ModeAttribution:
    """Decompose Δg_pred = Σ_{k≥1} σ_k (u_k·Δv) v_k.

    Reports each mode's:
      cos        — alignment of its contribution with Δg_actual
      pred_frac  — share of the *prediction*'s energy carried by mode k
      cum_cos    — cumulative cos to Δg_actual after summing terms 1..k

    Mode 0 is skipped (deflated by construction in M_hi).
    """
    a, b = pair
    ia, ib = cx.name_to_idx[a], cx.name_to_idx[b]
    va = featvec(cx.payload.rule_counts[ia], cx.feat_to_idx)
    vb = featvec(cx.payload.rule_counts[ib], cx.feat_to_idx)
    dv = vb - va
    dg_actual = cx.G_hi[ib] - cx.G_hi[ia]

    K = min(n_modes + 1, cx.s.size)
    coeffs = [cx.s[k] * float(cx.U[:, k] @ dv) for k in range(1, K)]
    term_sq = [c * c for c in coeffs]            # since v_k unit-norm
    total_pred_sq = sum(term_sq) or 1.0

    cos_per: List[float] = []
    cum_per: List[float] = []
    accum   = np.zeros_like(dg_actual)
    for c, k in zip(coeffs, range(1, K)):
        term = c * cx.Vt[k]
        cos_per.append(_cos(term, dg_actual))
        accum = accum + term
        cum_per.append(_cos(accum, dg_actual))

    return ModeAttribution(
        pair=(a, b),
        cos_per_mode=cos_per,
        pred_frac_per_mode=[ts / total_pred_sq for ts in term_sq],
        cum_cos_per_mode=cum_per,
        sigmas=[float(cx.s[k]) for k in range(1, K)],
    )


def print_mode_attribution(r: ModeAttribution) -> None:
    a, b = r.pair
    print(f"Per-mode attribution: {a} -> {b}")
    print(f"  {'k':>3s} {'sigma':>8s} {'cos(term, Dg)':>14s} "
          f"{'pred share':>11s} {'cum cos':>9s}")
    for k, (sig, c, pf, cu) in enumerate(zip(r.sigmas,
                                             r.cos_per_mode,
                                             r.pred_frac_per_mode,
                                             r.cum_cos_per_mode), start=1):
        print(f"  {k:>3d} {sig:>8.3f} {c:>14.3f} "
              f"{pf*100:>10.1f}% {cu:>9.3f}")
    sig_4_7 = sum(r.pred_frac_per_mode[3:7]) if len(r.pred_frac_per_mode) >= 7 else 0.0
    verdict = "PASS" if sig_4_7 > 0.80 else "MISS"
    print()
    print(f"  L6e: modes 4-7 carry {sig_4_7*100:.1f}% of prediction "
          f"energy   ({verdict})")


# ─── Topology experiments (chain collapse, holonomy, chirality) ───
#
# Three-body structure:
#       Part A (vocab, 12)  ←F1→  Part B (syntax, 30)  ←F2→  Part C (geometry, 320)
#
# Each side gets a per-program count/embedding vector. Correlation
# matrices are sums of outer products over the corpus, with normalizers
# matching `build_f2_matrix` so all three matrices live in compatible
# scales:
#       v_A (12,)   = vocab counts (L1-normalized per program)
#       v_B (30,)   = extended-feature counts (L1-normalized per program)
#       v_C (320,)  = geometry HV (L2-normalized per program)
#
#       M_AB[a,b] = sum_p v_A_p[a] * v_B_p[b]
#       M_BC[b,c] = sum_p v_B_p[b] * v_C_p[c]
#       M_CA[c,a] = sum_p v_C_p[c] * v_A_p[a]
#       M_AA[a,a']= sum_p v_A_p[a] * v_A_p[a']
#       M_AC[a,c] = sum_p v_A_p[a] * v_C_p[c]
#
# All corpora and weights are shared with the F₂ payload so transport
# numbers are directly comparable to topology numbers.

@dataclass
class TopologyMatrices:
    A_order: List[str]                  # ALL_COMMANDS
    B_order: List[str]                  # EXTENDED_ORDER
    M_AB: np.ndarray                    # (|A|, |B|)
    M_BC: np.ndarray                    # (|B|, 320)  ≡ cx.M
    M_CA: np.ndarray                    # (320, |A|)
    M_AA: np.ndarray                    # (|A|, |A|)
    M_AC: np.ndarray                    # (|A|, 320)


def _vocab_counts(prog, command_order: Sequence[str]) -> np.ndarray:
    from logo_encode_vocab import command_sequence
    seq = Counter(command_sequence(prog))
    v = np.zeros(len(command_order))
    cmd_to_idx = {c: i for i, c in enumerate(command_order)}
    for c, n in seq.items():
        if c in cmd_to_idx:
            v[cmd_to_idx[c]] = n
    return v


def build_topology(cx: TransportContext) -> TopologyMatrices:
    """Build M_AB, M_BC, M_CA, M_AA, M_AC matching cx.M's normalizations."""
    from logo_build_splits import ALL_COMMANDS

    A_order = list(ALL_COMMANDS)
    B_order = list(cx.feat_order)
    nA, nB, nC = len(A_order), len(B_order), IRREP_DIM

    M_AB = np.zeros((nA, nB))
    M_BC = cx.M.copy()                            # by construction
    M_CA = np.zeros((nC, nA))
    M_AA = np.zeros((nA, nA))
    M_AC = np.zeros((nA, nC))

    for name in cx.payload.names:
        idx = cx.name_to_idx[name]
        rc  = cx.payload.rule_counts[idx]
        g   = cx.payload.geom_hvs[idx]
        # vocab counts (L1-normalized to match B normalization)
        from logo_corpus import get as get_corpus_entry
        prog = parse(get_corpus_entry(name).source)
        vA_raw = _vocab_counts(prog, A_order)
        ssA = vA_raw.sum()
        vA = vA_raw / ssA if ssA > 0 else vA_raw
        vB = featvec(rc, cx.feat_to_idx)
        gn = float(np.linalg.norm(g))
        vC = g / gn if gn > 0 else g

        M_AB += np.outer(vA, vB)
        M_CA += np.outer(vC, vA)
        M_AA += np.outer(vA, vA)
        M_AC += np.outer(vA, vC)

    return TopologyMatrices(A_order=A_order, B_order=B_order,
                            M_AB=M_AB, M_BC=M_BC, M_CA=M_CA,
                            M_AA=M_AA, M_AC=M_AC)


def _matrix_cos(A: np.ndarray, B: np.ndarray) -> float:
    """Frobenius cosine between two same-shape matrices."""
    return _cos(A.ravel(), B.ravel())


def _frob(A: np.ndarray) -> float:
    return float(np.linalg.norm(A, ord='fro'))


def _normalize_frob(A: np.ndarray) -> np.ndarray:
    f = _frob(A)
    return A / f if f > 0 else A


# 2e.1: Chain collapse — does syntax mediate vocab → geometry?

@dataclass
class ChainCollapseResult:
    cos_narrow: float        # rules-only syntax (12 rule cols)
    cos_wide:   float        # full extended syntax (30 cols)
    rules_only_dim: int
    extended_dim: int


def chain_collapse_test(cx: TransportContext) -> ChainCollapseResult:
    """Compare F3_direct (vocab × geometry) against F3_chain = M_AB · M_BC.

    We test two B-widths:
      - narrow: only ALL_RULES columns of M_AB and rows of M_BC
      - wide:   full EXTENDED_ORDER (rules + repeat_n value buckets)

    Iteration-2 prediction: cos ~0.95 narrow, ~0.99 wide.
    """
    from logo_ast import ALL_RULES
    top = build_topology(cx)

    # narrow: project both M_AB and M_BC onto the rule columns/rows.
    rule_cols = [cx.feat_to_idx[r] for r in ALL_RULES if r in cx.feat_to_idx]
    M_AB_n = top.M_AB[:, rule_cols]
    M_BC_n = top.M_BC[rule_cols, :]
    F3_chain_n = M_AB_n @ M_BC_n
    cos_n = _matrix_cos(top.M_AC, F3_chain_n)

    # wide: the full extended axis.
    F3_chain_w = top.M_AB @ top.M_BC
    cos_w = _matrix_cos(top.M_AC, F3_chain_w)

    return ChainCollapseResult(
        cos_narrow=cos_n, cos_wide=cos_w,
        rules_only_dim=len(rule_cols),
        extended_dim=top.M_BC.shape[0],
    )


def print_chain_collapse(r: ChainCollapseResult) -> None:
    print("Chain collapse: F3_chain (= M_AB @ M_BC) vs F3_direct (= M_AC)")
    print(f"  narrow B (rules only, dim {r.rules_only_dim})    "
          f"cos = {r.cos_narrow:+.3f}")
    print(f"  wide   B (extended,   dim {r.extended_dim})     "
          f"cos = {r.cos_wide:+.3f}")
    delta = r.cos_wide - r.cos_narrow
    print(f"  widening gain (wide - narrow)                   "
          f"d   = {delta:+.3f}")
    print(f"  Interpretation: syntax of width {r.extended_dim} mediates")
    print(f"  ~{r.cos_wide*100:.0f}% of vocab->geometry correlation;")
    print(f"  the wide-narrow gap shows what value-fingerprint features add.")


# 2e.2: Cycle holonomy

@dataclass
class HolonomyResult:
    M_AA_norm: float
    C_fwd_norm: float
    cos_round_trip_vs_direct: float
    holonomy_frob: float                 # ||normalize(C_fwd) - normalize(M_AA)||_F
    cycle_singular_values: np.ndarray


def cycle_holonomy(cx: TransportContext) -> HolonomyResult:
    """Build C_fwd = M_CA^T @ M_BC^T @ M_AB^T (vocab-to-vocab via A->B->C->A).

    Compare against the direct M_AA. Plan prediction: cos ~0.93,
    holonomy norm ~0.37. Cycle SVD is expected to crush mass into the
    leading mode (geometry-visible commands survive the round trip;
    geometry-invisible commands like MAKE/PENUP get distorted).
    """
    top = build_topology(cx)
    C_fwd = top.M_CA.T @ top.M_BC.T @ top.M_AB.T   # (|A|, |A|)
    cos_v = _matrix_cos(C_fwd, top.M_AA)
    H = _normalize_frob(C_fwd) - _normalize_frob(top.M_AA)
    s = np.linalg.svd(C_fwd, compute_uv=False)
    return HolonomyResult(
        M_AA_norm=_frob(top.M_AA),
        C_fwd_norm=_frob(C_fwd),
        cos_round_trip_vs_direct=cos_v,
        holonomy_frob=_frob(H),
        cycle_singular_values=s,
    )


def print_holonomy(r: HolonomyResult) -> None:
    print("Cycle holonomy: round-trip A->B->C->A vs direct A<->A")
    print(f"  ||M_AA||_F                          = {r.M_AA_norm:.3f}")
    print(f"  ||C_fwd||_F                         = {r.C_fwd_norm:.3f}")
    print(f"  cos(C_fwd, M_AA)  [normalized]       = {r.cos_round_trip_vs_direct:+.3f}")
    print(f"  holonomy ||delta||_F                 = {r.holonomy_frob:+.3f}")
    s = r.cycle_singular_values
    top = float(s[0])
    print(f"  cycle SVD (top {min(6, s.size)} singular values, normalized to s_0):")
    for k in range(min(6, s.size)):
        print(f"    s[{k}] = {float(s[k]):.4f}   "
              f"({float(s[k])/top*100:.1f}% of s_0)")
    crush = (s[1] / top) if s.size > 1 and top > 0 else 0.0
    print(f"  Mode-0 dominance: s_1 / s_0 = {crush:.3f}   "
          f"(low = cycle crushes to one mode)")


# 2e.3: Chirality (commutator)

@dataclass
class ChiralityResult:
    cos_fwd_rev: float                   # cos(C_fwd, C_rev)
    commutator_frob: float               # ||normalize(C_fwd) - normalize(C_rev)||
    is_symmetric: bool                   # commutator < 0.01


def chirality_test(cx: TransportContext) -> ChiralityResult:
    """Compare C_fwd to C_rev = M_AB @ M_BC @ M_CA.

    Mathematically, C_rev = C_fwd^T, so commutator = antisymmetric part
    of C_fwd. Symmetric C_fwd (commutator ~0) means the cycle is
    'torus-like' — order doesn't matter. Asymmetric C_fwd is chiral.

    With a 21-program corpus, small commutator signals may be corpus
    bias rather than intrinsic structure — caveat noted in the report.
    """
    top = build_topology(cx)
    C_fwd = top.M_CA.T @ top.M_BC.T @ top.M_AB.T
    C_rev = top.M_AB @ top.M_BC @ top.M_CA           # = C_fwd.T
    cos_fr = _matrix_cos(C_fwd, C_rev)
    comm   = _normalize_frob(C_fwd) - _normalize_frob(C_rev)
    return ChiralityResult(
        cos_fwd_rev=cos_fr,
        commutator_frob=_frob(comm),
        is_symmetric=_frob(comm) < 0.01,
    )


def print_chirality(r: ChiralityResult) -> None:
    print("Chirality: C_fwd vs C_rev = C_fwd^T")
    print(f"  cos(C_fwd, C_rev)                   = {r.cos_fwd_rev:+.3f}")
    print(f"  commutator ||normalized delta||_F    = {r.commutator_frob:+.3f}")
    verdict = ("symmetric (torus-like)" if r.is_symmetric
               else "chiral (non-commutative)")
    print(f"  Verdict: {verdict}")
    print(f"  Caveat: 21-program corpus -> small commutators may be")
    print(f"  corpus bias rather than intrinsic three-body structure.")


# ─── L7a: Held-out generalization ─────────────────────────────────
#
# Every L6 number was measured on the same 21 programs that built F₂.
# L7a rebuilds F₂ from a reduced corpus (dropping pentagon+octagon by
# default) and checks whether transport(5)/transport(8) retain their
# D4 character class, and whether polygon-pair transport still points
# at the right geometry when pentagon/octagon are no longer in the
# fiber. If these generalize, iteration 2's structural claims survive.
# If they don't, L6d was a memorization artefact.

def holdout_context(holdouts: Sequence[str]) -> TransportContext:
    """Build F₂ context from CORPUS minus the named programs."""
    drop = set(holdouts)
    reduced = [e for e in CORPUS if e.name not in drop]
    return build_context(reduced)


@dataclass
class HoldoutChannelRow:
    feat: str
    full_energy: Dict[str, float]
    ho_energy:   Dict[str, float]
    full_norm:   float
    ho_norm:     float


@dataclass
class HoldoutPairRow:
    a: str
    b: str
    cos_full: float    # cos(cx_full.M_hi.T @ dv, dg_actual_full)
    cos_ho:   float    # cos(cx_ho.M_hi.T   @ dv, dg_actual_full)


@dataclass
class HoldoutReport:
    holdouts: List[str]
    channels: List[HoldoutChannelRow]
    pairs:    List[HoldoutPairRow]


# Map held-out polygon names to the repeat_n features whose character
# class we care about preserving under hold-out.
_HOLDOUT_FEATURE_HINTS: Dict[str, str] = {
    "triangle":  "repeat_n=3",
    "square":    "repeat_n=4",
    "pentagon":  "repeat_n=5",
    "hexagon":   "repeat_n=6",
    "octagon":   "repeat_n=8",
    "dodecagon": "repeat_n=12",
}


def _features_for_holdouts(holdouts: Sequence[str]) -> List[str]:
    feats = []
    for h in holdouts:
        f = _HOLDOUT_FEATURE_HINTS.get(h)
        if f and f not in feats:
            feats.append(f)
    return feats or ["repeat_n=5", "repeat_n=8"]


def holdout_transport_table(
    holdouts: Sequence[str],
    *,
    feat_names: Optional[Sequence[str]] = None,
    pair_names: Optional[Sequence[Tuple[str, str]]] = None,
) -> HoldoutReport:
    """L7a: compare transport(N) D4 decomposition + pair transport
    between the full fiber and a held-out fiber.

    Defaults derive the feature list from the hold-out names (pentagon
    → repeat_n=5, octagon → repeat_n=8) and use neighbour-pairs that
    straddle the held-out set.
    """
    cx_full = build_context()
    cx_ho   = holdout_context(list(holdouts))

    feats = list(feat_names) if feat_names else _features_for_holdouts(holdouts)
    if pair_names is None:
        pair_names = []
        if "pentagon" in holdouts:
            pair_names.append(("triangle", "pentagon"))
        if "octagon" in holdouts:
            pair_names.append(("hexagon",  "octagon"))
        if not pair_names:
            pair_names = [("square", "triangle")]

    # Per-feature D4 energy split, full vs held-out (both deflated).
    full_rows = feature_transport_table(cx_full, feats, use_deflated=True)
    ho_rows   = feature_transport_table(cx_ho,   feats, use_deflated=True)
    full_by = {r.feat: r for r in full_rows}
    ho_by   = {r.feat: r for r in ho_rows}
    channels: List[HoldoutChannelRow] = []
    for f in feats:
        if f in full_by and f in ho_by:
            channels.append(HoldoutChannelRow(
                feat=f,
                full_energy=full_by[f].energy_per_irrep,
                ho_energy  =ho_by[f].energy_per_irrep,
                full_norm  =full_by[f].norm,
                ho_norm    =ho_by[f].norm,
            ))

    # Pair-transport: predict using held-out fiber, compare against
    # full-corpus geometry delta. The ground truth doesn't move — we
    # only ask whether the reduced fiber still aligns with it.
    pairs: List[HoldoutPairRow] = []
    for a, b in pair_names:
        if a not in cx_full.name_to_idx or b not in cx_full.name_to_idx:
            continue
        ia, ib = cx_full.name_to_idx[a], cx_full.name_to_idx[b]
        va = featvec(cx_full.payload.rule_counts[ia], cx_full.feat_to_idx)
        vb = featvec(cx_full.payload.rule_counts[ib], cx_full.feat_to_idx)
        dv = vb - va
        dg_actual = cx_full.G_hi[ib] - cx_full.G_hi[ia]
        dg_pred_full = cx_full.M_hi.T @ dv
        dg_pred_ho   = cx_ho.M_hi.T   @ dv
        pairs.append(HoldoutPairRow(
            a=a, b=b,
            cos_full=_cos(dg_pred_full, dg_actual),
            cos_ho  =_cos(dg_pred_ho,   dg_actual),
        ))

    return HoldoutReport(
        holdouts=list(holdouts),
        channels=channels,
        pairs=pairs,
    )


def print_holdout_report(r: HoldoutReport) -> None:
    print(f"Hold-out generalization: excluding {', '.join(r.holdouts)}")
    print()
    print("Per-feature D4 decomposition (deflated, full vs held-out):")
    print(f"  {'feat':14s} {'scope':>6s} {'|t|':>8s}   "
          f"{'A1':>5s} {'A2':>5s} {'B1':>5s} {'B2':>5s} {'E':>5s}")
    for c in r.channels:
        for label, eg, n in (("full", c.full_energy, c.full_norm),
                             ("ho",   c.ho_energy,   c.ho_norm)):
            print(f"  {c.feat:14s} {label:>6s} {n:8.3f}   "
                  f"{eg['A1']*100:4.0f}% {eg['A2']*100:4.0f}% "
                  f"{eg['B1']*100:4.0f}% {eg['B2']*100:4.0f}% "
                  f"{eg['E']*100:4.0f}%")
    print()

    # Predictions.
    for c in r.channels:
        N = c.feat.split("=")[-1]
        norm_ratio = (c.ho_norm / c.full_norm) if c.full_norm > 0 else 0.0
        max_pp = max(
            abs(c.full_energy[k] - c.ho_energy[k]) * 100
            for k in IRREP_NAMES
        )
        verdict_channel = "PASS" if max_pp <= 20.0 else "MISS"
        print(f"  L7a channel-drift max(|full - ho|) for {c.feat:14s} "
              f"= {max_pp:5.1f}pp   ({verdict_channel})")
        if N == "5":
            a1e_full = c.full_energy["A1"] + c.full_energy["E"]
            a1e_ho   = c.ho_energy["A1"]   + c.ho_energy["E"]
            drift = abs(a1e_full - a1e_ho) * 100
            verdict = "PASS" if drift <= 20.0 else "MISS"
            print(f"  L7a.1 transport(5) A1+E share drift       "
                  f"= {drift:5.1f}pp   ({verdict})")
        if N == "8":
            verdict = "PASS" if c.ho_energy["A1"] >= 0.50 else "MISS"
            print(f"  L7a.2 transport(8) A1 fraction (ho)       "
                  f"= {c.ho_energy['A1']*100:5.1f}%   ({verdict})")
        verdict_norm = "PASS" if norm_ratio >= 0.30 else "MISS"
        print(f"  L7a.3 |t({N})| ratio (holdout/full)        "
              f"= {norm_ratio:5.3f}   ({verdict_norm})")
    print()
    print("Pair transport under held-out fiber (vs full-corpus Dg):")
    print(f"  {'pair':28s} {'cos_full':>10s} {'cos_ho':>10s}")
    for p in r.pairs:
        pair = f"{p.a} -> {p.b}"
        print(f"  {pair:28s} {p.cos_full:+10.3f} {p.cos_ho:+10.3f}")
    if r.pairs:
        best = max(p.cos_ho for p in r.pairs)
        verdict = "PASS" if best > 0.25 else "MISS"
        print(f"  L7a.4 best pair cos_ho                     "
              f"= {best:+.3f}   ({verdict})")


# ─── L7b: Partial-trace fibers ────────────────────────────────────
#
# Up to now F₂ has been built from the FINAL geometry of each program.
# L7b builds F₂ from geometry-at-step-N, asking whether the fiber
# carries forward-in-time information: does M_build_hi.T @ featvec(p)
# predict geometry at step N+Δ when the fiber was built at step N?
#
# Polygon programs are "done" after a handful of segments so their
# geometry rows at N=10/30/60 are identical; spirals and fractals are
# the actual test. No interpreter changes needed — we just truncate
# Trace.segments and re-encode.

def _trace_for(name: str):
    """Run a program by corpus name and return its full Trace."""
    prog = parse(get_corpus(name).source)
    return run(prog).trace


def partial_geom_for(entry, n_segments: int) -> np.ndarray:
    """Encode the first n_segments of a program's trace as geometry HV."""
    from logo_interp import Trace
    prog = parse(entry.source)
    ctx  = run(prog)
    segs = ctx.trace.segments[:n_segments]
    return encode_geometry(Trace(segments=list(segs)))


def partial_geom(name: str, n_segments: int) -> np.ndarray:
    """Convenience: partial_geom_for by corpus name."""
    return partial_geom_for(get_corpus(name), n_segments)


def partial_trace_lengths(corpus=CORPUS) -> Dict[str, int]:
    """Report full trace length (segment count) per program."""
    out: Dict[str, int] = {}
    for e in corpus:
        prog = parse(e.source)
        ctx  = run(prog)
        out[e.name] = len(ctx.trace.segments)
    return out


def build_partial_context(n_segments: int, corpus=CORPUS) -> TransportContext:
    """Build a TransportContext from geometry-at-step-N rather than final.

    Programs with fewer than n_segments contribute their full trace —
    their geometry row is identical at every anchor N > len(trace). This
    is the natural baseline for fiber-drift measurements: polygons
    contribute time-invariant rows, spirals/fractals carry the signal.
    """
    from logo_interp import Trace
    payload = F2Payload()
    for e in corpus:
        prog = parse(e.source)
        ctx  = run(prog)
        segs = ctx.trace.segments[:n_segments]
        g = encode_geometry(Trace(segments=list(segs)))
        payload.add(e.name, program_features(prog), g)
    M = build_f2_matrix(payload, right_order=EXTENDED_ORDER)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    M_hi = M - s[0] * np.outer(U[:, 0], Vt[0])
    G = np.array(payload.geom_hvs)
    norms = np.linalg.norm(G, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    G_n = G / norms
    G_hi = G_n - G_n.mean(axis=0, keepdims=True)
    return TransportContext(
        payload=payload,
        feat_order=list(EXTENDED_ORDER),
        M=M, U=U, s=s, Vt=Vt, M_hi=M_hi,
        G_n=G_n, G_hi=G_hi,
        name_to_idx={n: i for i, n in enumerate(payload.names)},
        feat_to_idx={f: i for i, f in enumerate(EXTENDED_ORDER)},
    )


@dataclass
class PartialTraceRow:
    name: str
    family: str
    cos_pred_target: float    # cos(M_build_hi.T @ featvec, g_target)
    len_full: int             # full trace length
    len_at_build: int
    len_at_target: int


@dataclass
class PartialTraceReport:
    n_build: int
    n_target: int
    rows: List[PartialTraceRow]


def partial_trace_transport_table(
    n_build: int,
    n_target: int,
) -> PartialTraceReport:
    """Build fiber at step n_build, predict each program's geometry at
    step n_target, report per-program cos(pred, target)."""
    cx_b  = build_partial_context(n_build)
    rows: List[PartialTraceRow] = []
    lengths = partial_trace_lengths()
    for entry in CORPUS:
        if entry.name not in cx_b.name_to_idx:
            continue
        idx = cx_b.name_to_idx[entry.name]
        v   = featvec(cx_b.payload.rule_counts[idx], cx_b.feat_to_idx)
        g_pred = cx_b.M_hi.T @ v
        g_target = partial_geom_for(entry, n_target)
        gt_n = float(np.linalg.norm(g_target))
        if gt_n > 0.0:
            g_target = g_target / gt_n
        # Center g_target in the same deflated space as g_pred by
        # subtracting the mean geometry (matches how cx_b.G_hi is built).
        g_target_hi = g_target - cx_b.G_n.mean(axis=0)
        rows.append(PartialTraceRow(
            name=entry.name,
            family=entry.family,
            cos_pred_target=_cos(g_pred, g_target_hi),
            len_full=lengths[entry.name],
            len_at_build=min(lengths[entry.name], n_build),
            len_at_target=min(lengths[entry.name], n_target),
        ))
    return PartialTraceReport(
        n_build=n_build,
        n_target=n_target,
        rows=rows,
    )


def print_partial_trace_report(r: PartialTraceReport) -> None:
    print(f"Partial-trace transport: fiber built at N={r.n_build}, "
          f"target at N={r.n_target}")
    print(f"  {'name':18s} {'family':12s} {'len':>4s} "
          f"{'at_b':>5s} {'at_t':>5s}   {'cos(pred, g_target)':>20s}")
    for row in r.rows:
        print(f"  {row.name:18s} {row.family:12s} {row.len_full:>4d} "
              f"{row.len_at_build:>5d} {row.len_at_target:>5d}   "
              f"{row.cos_pred_target:>+20.3f}")
    print()
    # Per-family aggregates.
    by_fam: Dict[str, List[float]] = {}
    for row in r.rows:
        by_fam.setdefault(row.family, []).append(row.cos_pred_target)
    for fam, vals in sorted(by_fam.items()):
        mean = float(np.mean(vals))
        print(f"  family {fam:12s}  n={len(vals):>2d}   mean cos = {mean:+.3f}")
    poly_mean = float(np.mean(by_fam.get("polygon", [0.0])))
    spir_mean = float(np.mean(by_fam.get("spiral",  [0.0])))
    v1 = "PASS" if poly_mean > 0.40 else "MISS"
    v2 = "PASS" if spir_mean > 0.20 else "MISS"
    print()
    print(f"  L7b.1 polygon mean > 0.40  = {poly_mean:+.3f}  ({v1})")
    print(f"  L7b.2 spiral  mean > 0.20  = {spir_mean:+.3f}  ({v2})")


@dataclass
class DriftRow:
    feat: str
    row_delta_norm: float      # ||M_late[f] - M_early[f]||
    row_early_norm: float


@dataclass
class DriftResult:
    n_early: int
    n_late: int
    frob_cos: float            # frob-cos(cx_e.M, cx_l.M)
    frob_rel_delta: float      # ||M_l - M_e||_F / ||M_e||_F
    per_irrep_cos: Dict[str, float]
    top_drift_rows: List[DriftRow]


def fiber_drift(n_early: int, n_late: int) -> DriftResult:
    """Compare fibers at two anchors — Frobenius cos, per-irrep cosine,
    and which syntax features carry the most drift."""
    cx_e = build_partial_context(n_early)
    cx_l = build_partial_context(n_late)
    M_e, M_l = cx_e.M, cx_l.M
    frob_cos = _matrix_cos(M_e, M_l)
    frob_rel = _frob(M_l - M_e) / (_frob(M_e) + 1e-12)

    per_irrep: Dict[str, float] = {}
    for i, name in enumerate(IRREP_NAMES):
        Me_c = M_e[:, i * BOARD_DIM:(i + 1) * BOARD_DIM]
        Ml_c = M_l[:, i * BOARD_DIM:(i + 1) * BOARD_DIM]
        per_irrep[name] = _matrix_cos(Me_c, Ml_c)

    rows: List[DriftRow] = []
    for idx, feat in enumerate(cx_e.feat_order):
        re = M_e[idx]
        rl = M_l[idx]
        rows.append(DriftRow(
            feat=feat,
            row_delta_norm=float(np.linalg.norm(rl - re)),
            row_early_norm=float(np.linalg.norm(re)),
        ))
    rows.sort(key=lambda r: r.row_delta_norm, reverse=True)

    return DriftResult(
        n_early=n_early, n_late=n_late,
        frob_cos=frob_cos,
        frob_rel_delta=frob_rel,
        per_irrep_cos=per_irrep,
        top_drift_rows=rows[:10],
    )


def print_fiber_drift(r: DriftResult) -> None:
    print(f"Fiber drift: M at N={r.n_early}  vs  M at N={r.n_late}")
    print(f"  Frobenius cos(M_e, M_l)      = {r.frob_cos:+.3f}")
    print(f"  ||M_l - M_e||_F / ||M_e||_F  = {r.frob_rel_delta:.3f}")
    print(f"  Per-irrep cos:")
    for name, c in r.per_irrep_cos.items():
        print(f"    {name}  cos = {c:+.3f}")
    v = "PASS" if r.frob_rel_delta > 0.10 else "MISS"
    print(f"  L7b.3 frob rel-delta > 0.10  ({v})")
    print()
    print("  Top-drift syntax features (||M_l[row] - M_e[row]||):")
    print(f"    {'feat':18s} {'drift':>8s}  {'early':>8s}")
    for dr in r.top_drift_rows:
        print(f"    {dr.feat:18s} {dr.row_delta_norm:>8.3f}  "
              f"{dr.row_early_norm:>8.3f}")
    names = [dr.feat for dr in r.top_drift_rows[:5]]
    hits = sum(1 for f in names if f in ("MAKE", "repeat_n=60",
                                         "repeat_n=40", "repeat_n=80",
                                         "r_STMT_is_MAKE"))
    v4 = "PASS" if hits >= 1 else "MISS"
    print(f"  L7b.4 spiral-marker feats in top-5  (hits={hits})  ({v4})")


@dataclass
class SpiralExtrapolationResult:
    name: str
    n_early: int
    n_late: int
    cos_fiber_pred: float     # cos(M_e_hi.T @ featvec, g_late)
    cos_snapshot: float       # cos(g_early, g_late) — baseline
    gain: float               # cos_fiber_pred - cos_snapshot


def spiral_extrapolation_probe(
    name: str = "spiral_square",
    n_early: int = 10,
    n_late:  int = 60,
) -> SpiralExtrapolationResult:
    """L7b.5: does the fiber built at n_early predict the target geometry
    at n_late better than simply reusing the snapshot at n_early?"""
    cx_e = build_partial_context(n_early)
    entry = get_corpus(name)
    idx = cx_e.name_to_idx[name]
    v = featvec(cx_e.payload.rule_counts[idx], cx_e.feat_to_idx)
    g_pred = cx_e.M_hi.T @ v

    g_early = partial_geom_for(entry, n_early)
    g_late  = partial_geom_for(entry, n_late)
    cos_snap = _cos(g_early, g_late)
    # Deflate prediction space consistently with cx_e.G_hi.
    mean_row = cx_e.G_n.mean(axis=0)
    n_late_n = float(np.linalg.norm(g_late))
    g_late_n = g_late / n_late_n if n_late_n > 0 else g_late
    g_late_hi = g_late_n - mean_row
    cos_pred = _cos(g_pred, g_late_hi)
    return SpiralExtrapolationResult(
        name=name,
        n_early=n_early, n_late=n_late,
        cos_fiber_pred=cos_pred,
        cos_snapshot=cos_snap,
        gain=cos_pred - cos_snap,
    )


def print_spiral_extrapolation(r: SpiralExtrapolationResult) -> None:
    print(f"Spiral extrapolation: {r.name} fiber at N={r.n_early} "
          f"predicting geometry at N={r.n_late}")
    print(f"  cos(fiber_pred, g_late)   = {r.cos_fiber_pred:+.3f}")
    print(f"  cos(g_early,    g_late)   = {r.cos_snapshot:+.3f}   [snapshot baseline]")
    print(f"  gain (fiber - snapshot)   = {r.gain:+.3f}")
    v = "PASS" if r.gain > 0.10 else "MISS"
    print(f"  L7b.5 fiber beats snapshot by > 0.10   ({v})")
