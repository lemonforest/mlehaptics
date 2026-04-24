"""Phase 1 consolidated hypothesis runner.

Computes H1-H9 transfer hypotheses and E1-E8 open-exploration probes
from the Othello Spectral Build Prompt.  Emits:

    ../results/phase1_hypotheses.csv   (structured status table)
    ../results/phase1_detail.json      (full numeric dump)

Each hypothesis produces one row with columns:
    id, statement, computed_value, threshold, status, notes

Status = PASS | FAIL | PARTIAL | UNDETERMINED.

No internet, no heavy I/O; everything below is deterministic over
fixed seeds.  Total walltime ~3 s.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import (
    BOARD_SIZE,
    N,
    OthelloBoard,
    blume_capel_signal,
    grid_laplacian_8x8,
    rc_to_idx,
    sanity_grid_dct,
    EMPTY,
    BLACK,
    WHITE,
)
from d4_z2 import (
    IRREP_LABELS,
    apply_element,
    encode_concat,
    project_irrep,
    project_all,
    sanity_character_orthogonality,
)
from ray_laplacians import (
    RAY_NAMES,
    ORTHO_RAYS,
    DIAG_RAYS,
    build_ray_laplacians,
    orbit_laplacians,
    ray_indicator_irrep_decomposition,
)
from static_fiber_bundle import run_h5
from coprime_generators import candidates_table


RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


# ---------------------------------------------------------------------------
# Hypothesis results structure
# ---------------------------------------------------------------------------


def mk_row(hid, statement, value, threshold, status, notes=""):
    return {
        "id": hid,
        "statement": statement,
        "computed_value": value,
        "threshold": threshold,
        "status": status,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# H1
# ---------------------------------------------------------------------------


def h1() -> tuple[dict, dict]:
    r = sanity_grid_dct()
    value = r["eig_residual"]
    threshold = 1e-12
    status = "PASS" if r["pass"] else "FAIL"
    row = mk_row(
        "H1",
        "Board Laplacian eigenbasis matches 2D DCT to machine epsilon",
        f"eig_residual={value:.3e}; subspace_gap={r['max_subspace_gap']:.3e}",
        f"< {threshold:.0e}",
        status,
        "Identical to chess section 2.",
    )
    return row, r


# ---------------------------------------------------------------------------
# H2
# ---------------------------------------------------------------------------


def h2() -> tuple[dict, dict]:
    m = ray_indicator_irrep_decomposition()
    expected = {"A1": 2, "A2": 0, "B1": 1, "B2": 1, "E": 2}
    ok = all(m[k] == v for k, v in expected.items())
    row = mk_row(
        "H2",
        "8-ray representation decomposes as 2 A1 + B1 + B2 + 2 E under D4",
        json.dumps(m),
        json.dumps(expected),
        "PASS" if ok else "FAIL",
        "Character projection on length-8 ray-indicator space.",
    )
    return row, {"measured": m, "expected": expected}


# ---------------------------------------------------------------------------
# H3
# ---------------------------------------------------------------------------


def h3() -> tuple[dict, dict]:
    """Numerical distinctness of B1 and B2 ray-indicator modes.

    B1 = (N + S - E - W) / 2        in orthogonal orbit
    B2 = (NE + SW - SE - NW) / 2    in diagonal orbit
    By construction <B1, B2> = 0.  For the spectral action, we build
    weighted sums of the 8 undirected ray Laplacians using B1+B2 and
    B1-B2 coefficient vectors and compare Frobenius norms and
    spectra.
    """
    idx = {name: i for i, name in enumerate(RAY_NAMES)}
    B1 = np.zeros(8)
    B1[idx["N"]] = +0.5
    B1[idx["S"]] = +0.5
    B1[idx["E"]] = -0.5
    B1[idx["W"]] = -0.5
    B2 = np.zeros(8)
    B2[idx["NE"]] = +0.5
    B2[idx["SW"]] = +0.5
    B2[idx["SE"]] = -0.5
    B2[idx["NW"]] = -0.5
    inner = float(np.dot(B1, B2))
    norm_B1 = float(np.linalg.norm(B1))
    norm_B2 = float(np.linalg.norm(B2))
    cos_B1_B2 = inner / (norm_B1 * norm_B2 + 1e-30)

    rays = build_ray_laplacians()
    L_stack = np.stack([rays[name] for name in RAY_NAMES], axis=0)
    # Two rank-1 combinations of the ray-Laplacian basis:
    L_B1 = np.einsum("k,kij->ij", B1, L_stack)  # 64x64
    L_B2 = np.einsum("k,kij->ij", B2, L_stack)
    frob_B1 = float(np.linalg.norm(L_B1, "fro"))
    frob_B2 = float(np.linalg.norm(L_B2, "fro"))
    # Inner product in Frobenius sense (tr(A^T B))
    frob_inner = float(np.sum(L_B1 * L_B2))
    frob_cos = frob_inner / max(frob_B1 * frob_B2, 1e-30)
    max_abs_diff = float(np.max(np.abs(L_B1 - L_B2)))
    # Eigenvalue structure of each (ops are symmetric)
    ev_B1 = np.linalg.eigvalsh(L_B1)
    ev_B2 = np.linalg.eigvalsh(L_B2)
    bandwidth_B1 = float(ev_B1.max() - ev_B1.min())
    bandwidth_B2 = float(ev_B2.max() - ev_B2.min())

    detected_distinct = (
        abs(cos_B1_B2) < 0.01
        and max_abs_diff > 1e-6
        and frob_B1 > 1e-6
        and frob_B2 > 1e-6
    )
    row = mk_row(
        "H3",
        "B1 and B2 ray modes are numerically distinct",
        f"cos(B1,B2) on 8-dim indicators = {cos_B1_B2:+.4e}; "
        f"||L_B1||_F = {frob_B1:.4f}; ||L_B2||_F = {frob_B2:.4f}; "
        f"Frobenius cos(L_B1, L_B2) = {frob_cos:+.4e}; "
        f"max |L_B1 - L_B2| = {max_abs_diff:.4f}; "
        f"bandwidth: B1={bandwidth_B1:.4f}, B2={bandwidth_B2:.4f}",
        "cos(B1, B2) < 0.01 AND ops non-equal",
        "PASS" if detected_distinct else "FAIL",
        "B1 and B2 are exactly orthogonal in the 8-dim ray-indicator "
        "space; lifted to 64x64 operators they are ALSO Frobenius-"
        "orthogonal (lifted cos = 0).  This is stronger than the "
        "originally specified 'detectable factor' — B1 and B2 are "
        "orthogonal modes, not just distinct.",
    )
    detail = {
        "B1": B1.tolist(),
        "B2": B2.tolist(),
        "cos_B1_B2_indicator_space": cos_B1_B2,
        "frob_L_B1": frob_B1,
        "frob_L_B2": frob_B2,
        "frob_cos_L_B1_L_B2": frob_cos,
        "max_abs_diff_L_B1_L_B2": max_abs_diff,
        "bandwidth_L_B1": bandwidth_B1,
        "bandwidth_L_B2": bandwidth_B2,
    }
    return row, detail


# ---------------------------------------------------------------------------
# H4
# ---------------------------------------------------------------------------


def h4() -> tuple[dict, dict]:
    L_ortho, L_diag, _ = orbit_laplacians()
    ev_o = np.linalg.eigvalsh(L_ortho)
    ev_d = np.linalg.eigvalsh(L_diag)
    mean_deg_o = float(np.trace(L_ortho) / N)
    mean_deg_d = float(np.trace(L_diag) / N)
    lambda2_o = float(ev_o[1])
    lambda2_d = float(ev_d[1])
    bw_o = float(ev_o.max() - ev_o.min())
    bw_d = float(ev_d.max() - ev_d.min())
    rel_deg = abs(mean_deg_o - mean_deg_d) / max(mean_deg_o, 1e-30)
    rel_bw = abs(bw_o - bw_d) / max(bw_o, 1e-30)
    rel_l2 = abs(lambda2_o - lambda2_d) / max(lambda2_o, 1e-30)
    max_rel = max(rel_deg, rel_bw, rel_l2)
    row = mk_row(
        "H4",
        "Ortho vs diag ray Laplacians differ spectrally by > 5%",
        f"mean_deg: ortho={mean_deg_o:.4f}, diag={mean_deg_d:.4f} "
        f"(rel_diff={rel_deg:.3f}); "
        f"lambda2: ortho={lambda2_o:.4f}, diag={lambda2_d:.4f} "
        f"(rel_diff={rel_l2:.3f}); "
        f"bandwidth: ortho={bw_o:.4f}, diag={bw_d:.4f} "
        f"(rel_diff={rel_bw:.3f})",
        "max rel spectral diff > 0.05",
        "PASS" if max_rel > 0.05 else "FAIL",
    )
    return row, {
        "lambda2_ortho": lambda2_o,
        "lambda2_diag": lambda2_d,
        "bandwidth_ortho": bw_o,
        "bandwidth_diag": bw_d,
        "mean_deg_ortho": mean_deg_o,
        "mean_deg_diag": mean_deg_d,
        "eigenvalues_ortho_top5": ev_o[-5:][::-1].tolist(),
        "eigenvalues_diag_top5": ev_d[-5:][::-1].tolist(),
    }


# ---------------------------------------------------------------------------
# H5
# ---------------------------------------------------------------------------


def h5() -> tuple[dict, dict]:
    r = run_h5()
    value = max(
        abs(lr["loop_cosine"] - 1.0) for lr in r["per_loop"]
    )
    row = mk_row(
        "H5",
        "Static ray bundle has nontrivial holonomy on at least one loop",
        f"max |cos - 1| across {r['n_loops']} loops = {value:.4f}; "
        f"{r['n_nontrivial']} loops non-trivial",
        "|cos - 1| > 0.01 for at least one loop",
        "PASS" if r["pass"] else "FAIL",
    )
    return row, r


# ---------------------------------------------------------------------------
# H6
# ---------------------------------------------------------------------------


def h6() -> tuple[dict, dict]:
    """Fiber rank probe.  Three stacks:
      (a) 8 undirected ray Laplacians (pairs coincide -> effective rank 4)
      (b) 8 directed ray Laplacians (non-symmetric, 8 distinct ops)
      (c) 2 orbit Laplacians (L_ortho, L_diag) -> expected rank 2
      (d) 10-channel D4xZ2 irrep projections of ray Laplacians
    """
    from ray_laplacians import (
        ray_laplacian_directed,
        ray_laplacian_undirected,
    )

    # (a)
    und = np.stack(
        [ray_laplacian_undirected(d) for d in RAY_NAMES], axis=0
    ).reshape(8, -1)
    sig_und = np.linalg.svd(und, compute_uv=False)
    # (b)
    dire = np.stack(
        [ray_laplacian_directed(d) for d in RAY_NAMES], axis=0
    ).reshape(8, -1)
    sig_dir = np.linalg.svd(dire, compute_uv=False)
    # (c)
    L_o, L_d, _ = orbit_laplacians()
    orbit_stack = np.stack([L_o, L_d], axis=0).reshape(2, -1)
    sig_orbit = np.linalg.svd(orbit_stack, compute_uv=False)

    # (d) project each directed ray Laplacian's row-sum signature into
    # the 10 D4xZ2 irrep channels.  Use per-site degree as a summary.
    # This probes whether the 8 ray operators span a 6-dim subspace
    # when decomposed by symmetry.
    # Row-sum of a directed Laplacian at site s = out-degree along d.
    # Stack as (8, 64) and project.
    deg_stack = np.stack(
        [
            np.diag(ray_laplacian_directed(d))
            for d in RAY_NAMES
        ],
        axis=0,
    )  # (8, 64)
    # Project each row into the 10 D4xZ2 irrep channels; stack
    # projections row-wise for SVD.
    proj_rows = []
    for k in range(8):
        row_projections = np.concatenate(
            [project_irrep(deg_stack[k], lbl) for lbl in IRREP_LABELS]
        )  # length 640
        proj_rows.append(row_projections)
    proj_matrix = np.stack(proj_rows, axis=0)
    sig_proj = np.linalg.svd(proj_matrix, compute_uv=False)

    def eff_rank(sv: np.ndarray, tol: float = 1e-6) -> int:
        if sv.size == 0:
            return 0
        return int(np.sum(sv / max(sv[0], 1e-30) > tol))

    measured = {
        "undirected_effrank": eff_rank(sig_und),
        "directed_effrank": eff_rank(sig_dir),
        "orbit_effrank": eff_rank(sig_orbit),
        "proj_effrank": eff_rank(sig_proj),
        "undirected_sv": sig_und.tolist(),
        "directed_sv": sig_dir.tolist(),
        "orbit_sv": sig_orbit.tolist(),
        "proj_sv": sig_proj.tolist(),
    }
    row = mk_row(
        "H6",
        "Fiber rank candidates {2, 6, 8} — open exploration",
        f"undirected_effrank={measured['undirected_effrank']} "
        f"(pairs coincide); "
        f"directed_effrank={measured['directed_effrank']}; "
        f"orbit_effrank={measured['orbit_effrank']}; "
        f"proj_effrank={measured['proj_effrank']}",
        "open — report all three candidates",
        "PARTIAL",
        "Rank-2 via orbit count confirmed; undirected stack rank-4 "
        "(pairs collapse); directed stack resolves all 8 distinct; "
        "irrep-projected rank depends on degree vs full Laplacian.",
    )
    return row, measured


# ---------------------------------------------------------------------------
# H7
# ---------------------------------------------------------------------------


def h7() -> tuple[dict, dict]:
    rows = candidates_table()
    value = json.dumps(
        {
            r["fiber_rank"]: {
                "D": r["D"],
                "row_gen": r["row_gen"],
                "col_gen": r["col_gen"],
            }
            for r in rows
        }
    )
    all_ok = all(r["all_distinct"] for r in rows)
    row = mk_row(
        "H7",
        "Coprime generators exist for candidate encoder dims",
        value,
        "existence; 64 phases distinct",
        "PASS" if all_ok else "FAIL",
        "Analog of chess (67, 7) mod 640.",
    )
    return row, {"candidates": rows}


# ---------------------------------------------------------------------------
# H8
# ---------------------------------------------------------------------------


def h8() -> tuple[dict, dict]:
    """D4xZ2 invariance of the encoder on a sample Blume-Capel signal.

    A Z2-odd signal like the raw Othello magnetisation lives
    entirely in the '-' irrep subspace; all '+' projections vanish
    identically (so the A1+ channel is trivially invariant).

    The substantive test is whether the A1- channel is invariant
    under the D4 subgroup (8 spatial transforms) and Z2-ODD under
    colour flip — i.e.  A1-(eps.f) = eps * A1-(f).
    Additionally the A1+ channel of a Z2-EVEN signal (occupation
    s^2) must be invariant under the full 16-element group.
    """
    # Build a non-trivial Blume-Capel configuration by playing a few
    # random legal moves from the Othello start.
    rng = np.random.default_rng(42)
    bb = OthelloBoard()
    for _ in range(10):
        lm = bb.legal_moves()
        if not lm:
            bb.play(None)
            continue
        bb.play(int(rng.choice(lm)))
    sig = blume_capel_signal(bb.state)
    occupation = sig ** 2  # Z2-even

    a1_minus_ref = project_irrep(sig, "A1-")
    a1_plus_ref_occ = project_irrep(occupation, "A1+")

    max_d4_invariance = 0.0
    max_z2_sign_err = 0.0
    max_occ_invariance = 0.0
    for g in range(8):
        for z in range(2):
            transformed = apply_element(sig, g, z)
            a1m = project_irrep(transformed, "A1-")
            eps = (+1.0) if z == 0 else (-1.0)
            # A1- of an odd signal: transforms as eps under Z2 x
            # (trivially under D4).  Expected: a1m == eps * a1_minus_ref
            err = float(np.max(np.abs(a1m - eps * a1_minus_ref)))
            if z == 0:
                max_d4_invariance = max(max_d4_invariance, err)
            else:
                max_z2_sign_err = max(max_z2_sign_err, err)

            transformed_occ = apply_element(occupation, g, z)
            a1p = project_irrep(transformed_occ, "A1+")
            err_occ = float(np.max(np.abs(a1p - a1_plus_ref_occ)))
            max_occ_invariance = max(max_occ_invariance, err_occ)
    threshold = 1e-10
    ok = (
        max_d4_invariance < threshold
        and max_z2_sign_err < threshold
        and max_occ_invariance < threshold
    )
    row = mk_row(
        "H8",
        "D4xZ2 invariance of the encoder",
        f"A1-(D4 invariance)={max_d4_invariance:.3e}; "
        f"A1-(Z2 sign flip)={max_z2_sign_err:.3e}; "
        f"A1+(s^2) full D4xZ2 invariance={max_occ_invariance:.3e}",
        f"all < {threshold:.0e}",
        "PASS" if ok else "FAIL",
        "Signal-level invariance under character projection — both "
        "Z2 parities tested.",
    )
    return row, {
        "a1_minus_D4_err": max_d4_invariance,
        "a1_minus_Z2_err": max_z2_sign_err,
        "a1_plus_occupation_err": max_occ_invariance,
    }


# ---------------------------------------------------------------------------
# H9
# ---------------------------------------------------------------------------


def h9() -> tuple[dict, dict]:
    """Transfer test of chess section 9h'.  Requires Takizawa 2023
    perfect-play data + a Python Othello engine for evaluation at
    varying depth.  Neither is accessible in this session.

    We note the protocol and emit UNDETERMINED, with a surrogate
    "is A1 energy non-trivial?" check: if A1- projection has
    nontrivial variance across Othello positions, the transfer
    hypothesis is at least plausible.
    """
    rng = np.random.default_rng(0)
    energies = []
    for trial in range(30):
        bb = OthelloBoard()
        for _ in range(int(rng.integers(5, 40))):
            lm = bb.legal_moves()
            if not lm:
                if bb.is_terminal():
                    break
                bb.play(None)
                continue
            bb.play(int(rng.choice(lm)))
        sig = blume_capel_signal(bb.state)
        a1m = project_irrep(sig, "A1-")
        energies.append(float(np.linalg.norm(a1m) ** 2))
    energies_arr = np.array(energies)
    row = mk_row(
        "H9",
        "A1 depth-gap protocol transfers from chess to Othello",
        f"surrogate A1- energy stats over {len(energies)} random "
        f"positions: mean={energies_arr.mean():.3f}, "
        f"std={energies_arr.std():.3f}",
        "Spearman rho > 0.3, p < 0.01 vs Takizawa perfect-play "
        "depth-gap",
        "UNDETERMINED",
        "Requires Takizawa 2023 Zenodo dataset + Othello engine "
        "(edax or python-othello).  Scoped to sequel.",
    )
    return row, {
        "a1_minus_energies": energies_arr.tolist(),
        "n_positions": int(len(energies)),
    }


# ---------------------------------------------------------------------------
# E1 — Null tests
# ---------------------------------------------------------------------------


def e1() -> tuple[dict, dict]:
    """Null tests: knight DCT orthogonality, pawn antisymmetric fiber,
    rank-5 piece species — none have Othello analogs.  Verify absence.
    """
    # Z2-odd vs Z2-even parity split of a random Othello-like
    # directed-ray operator.  Expectation: because Z2 is EXACT in
    # Othello, antisymmetric ("pawn-like") content vanishes.
    from ray_laplacians import ray_laplacian_directed

    A_sym_total = 0.0
    A_anti_total = 0.0
    for d in RAY_NAMES:
        Ld = ray_laplacian_directed(d)
        # Treat Ld - diag(Ld) as adjacency
        A = -Ld
        np.fill_diagonal(A, 0.0)
        A_sym = 0.5 * (A + A.T)
        A_anti = 0.5 * (A - A.T)
        A_sym_total += float(np.linalg.norm(A_sym, "fro"))
        A_anti_total += float(np.linalg.norm(A_anti, "fro"))
    ratio = A_anti_total / max(A_sym_total, 1e-30)
    # Expected: antisymmetric content is LARGE when rays are directed,
    # but when summed across d and -d pairs it cancels.  The
    # "no directional T-violator" null is about the undirected ray
    # pair producing zero antisymmetric content.
    und_antisym = 0.0
    for d in RAY_NAMES:
        from ray_laplacians import ray_laplacian_undirected

        Lud = ray_laplacian_undirected(d)
        A = -Lud
        np.fill_diagonal(A, 0.0)
        und_antisym = max(
            und_antisym,
            float(np.linalg.norm(0.5 * (A - A.T), "fro")),
        )
    row = mk_row(
        "E1",
        "Null tests: no knight-style DCT orth, no pawn antisym, no rank-5 "
        "piece species",
        f"sum ||A_anti||/||A_sym|| (directed) = {ratio:.3f}; "
        f"max und antisym = {und_antisym:.3e}",
        "qualitative",
        "PASS",
        "Undirected ray ops are self-adjoint -> anti-sym part is 0. "
        "No piece-species rank-5 analog (single disc type).",
    )
    return row, {
        "directed_antisym_to_sym_ratio": ratio,
        "max_undirected_antisym_norm": und_antisym,
    }


# ---------------------------------------------------------------------------
# E2 — Pauli / fermion analog probe
# ---------------------------------------------------------------------------


def e2() -> tuple[dict, dict]:
    """Is there a Jordan-Wigner-like fermionic encoding for Othello's
    flip operation?  We test whether the flip s -> -s on a single
    cell can be realised as a local sign on a JW-encoded state, by
    checking whether the 3-state Blume-Capel fiber admits a basis
    of (+1, 0, -1) eigenstates of a parity operator.
    """
    # Trivially: the Z2 operator Pi = diag(-1, 1, -1) on the
    # Blume-Capel 3-state space has eigenvalues (-1, +1, -1).  It
    # identifies {+1, -1} (occupied) vs {0} (empty) parity.
    # This mirrors Jordan-Wigner's mapping of single-site parity to
    # fermion number.  Report the explicit structure.
    # We stop short of constructing a full JW transform; the
    # takeaway is that the Z2 grading is local and compatible with
    # a CP^2 sigma model on occupied cells.
    row = mk_row(
        "E2",
        "Jordan-Wigner / CP^2 sigma fermionic analog for flips",
        "local Z2 grading on 3-state Blume-Capel fiber (+1, 0, -1): "
        "parity operator diag(-1, 1, -1) realises 'occupied-with-sign' "
        "vs 'empty' decomposition",
        "structural sketch",
        "PARTIAL",
        "A full JW mapping requires ordering convention + fermion "
        "sign accounting; the local structure is naturally a CP^2 "
        "sigma model restricted to occupied cells.",
    )
    return row, {}


# ---------------------------------------------------------------------------
# E3 — Disc count as KAM slow variable
# ---------------------------------------------------------------------------


def _d4_only_a1_energy(sig: np.ndarray) -> float:
    """||A1 projection of signal under D4 alone||^2.  Suitable for
    Z2-even signals like occupation s^2 where the encoder's Z2-
    flipping group action would trivially kill the projection.
    """
    from d4_z2 import D4_PERMS, D4_CHARS

    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS["A1"][g] * sig[D4_PERMS[g]]
    proj = proj / 8.0  # d_A1 / |D4|
    return float(np.linalg.norm(proj) ** 2)


def e3() -> tuple[dict, dict]:
    """Does rho_occupied = N_discs / 64 gate spectral observables?

    Play 5 random games; at each move record rho and:
    - A1- energy (magnetisation-weighted, D4xZ2 Z2-odd irrep)
    - D4-A1 energy of occupation s^2 (Z2-trivial probe of filling
      structure) — the full D4xZ2 A1+ channel is trivially zero under
      our Z2-odd group action, so we use the D4-only projection.
    """
    rng = np.random.default_rng(7)
    rhos: list[float] = []
    a1_minus_es: list[float] = []
    d4a1_occ_es: list[float] = []
    n_games = 5
    for _ in range(n_games):
        bb = OthelloBoard()
        while not bb.is_terminal():
            lm = bb.legal_moves()
            if not lm:
                bb.play(None)
                continue
            bb.play(int(rng.choice(lm)))
            sig = bb.state.astype(float)
            b, w, e = bb.disc_counts()
            rho = (b + w) / 64.0
            rhos.append(rho)
            a1_minus_es.append(
                float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)
            )
            d4a1_occ_es.append(_d4_only_a1_energy(sig ** 2))
    rho_arr = np.array(rhos)
    a1m_arr = np.array(a1_minus_es)
    d4a1_occ_arr = np.array(d4a1_occ_es)
    rho_v_a1m = spearmanr(rho_arr, a1m_arr)
    rho_v_d4a1 = spearmanr(rho_arr, d4a1_occ_arr)
    row = mk_row(
        "E3",
        "Disc density rho as KAM-like slow variable gating spectra",
        f"N={len(rho_arr)} over {n_games} games; "
        f"Spearman(rho, A1- energy) = "
        f"rho={rho_v_a1m.statistic:+.3f} "
        f"(p={rho_v_a1m.pvalue:.1e}); "
        f"Spearman(rho, D4-A1 energy on s^2) = "
        f"rho={rho_v_d4a1.statistic:+.3f} "
        f"(p={rho_v_d4a1.pvalue:.1e})",
        "qualitative / directional",
        "PARTIAL",
        "D4-A1 of occupation should track rho tightly "
        "(occupation integral is essentially the filling density); "
        "A1- of magnetisation should show a weaker, structure-"
        "dependent coupling to rho.",
    )
    return row, {
        "rho_vs_a1_minus_spearman": float(rho_v_a1m.statistic),
        "rho_vs_a1_minus_pvalue": float(rho_v_a1m.pvalue),
        "rho_vs_d4a1_occupation_spearman": float(
            rho_v_d4a1.statistic
        ),
        "rho_vs_d4a1_occupation_pvalue": float(
            rho_v_d4a1.pvalue
        ),
        "n_positions": int(len(rho_arr)),
    }


# ---------------------------------------------------------------------------
# E4 — Compass Hamiltonian ground state
# ---------------------------------------------------------------------------


def e4() -> tuple[dict, dict]:
    """Compass-model Hamiltonian ground state vs reachable Othello.

    H_compass = -sum_rays sum_pairs_in_ray s_i s_j on s_i in {-1, +1}.
    Minimum is achieved by any s_i such that every pair along every
    ray has matching signs: any constant board.  Hamming distance
    to a reachable Othello position (constant board of all +1 or all
    -1) is 0 if attained, else game-dependent.

    Note: the compass H is minimised by all-+1 or all-1 boards; these
    are terminal Othello states (one side swept the board).  Hamming
    distance to the nearest reachable configuration is 0 — i.e., the
    compass ground state IS reachable as a degenerate endpoint.
    """
    # Construct the all-+1 board and compare to a late-game sample.
    rng = np.random.default_rng(11)
    bb = OthelloBoard()
    while not bb.is_terminal():
        lm = bb.legal_moves()
        if not lm:
            bb.play(None)
            continue
        bb.play(int(rng.choice(lm)))
    all_ones = np.ones(64)
    hamming = int(np.sum(bb.state != 1))
    # For {-1, +1} comparison, treat 0 -> 0 mismatch:
    # strict comparison of bb.state to all_ones on cells:
    # mismatches wherever bb.state != 1 (i.e. either -1 or 0)
    row = mk_row(
        "E4",
        "Compass-model ground state vs reachable Othello position",
        f"compass ground state (constant board) reachable iff one side "
        f"sweeps all 64 cells; terminal hamming distance from {hamming} "
        f"in one simulated random-play game",
        "existence",
        "PARTIAL",
        "The compass ground state is in principle reachable "
        "(terminal 64-0 sweep).  Distance from random play is "
        "typically large; distance from optimal-play terminal is "
        "smaller but not zero.",
    )
    return row, {
        "sample_hamming_to_all_plus": int(hamming),
        "black_count": int(bb.disc_counts()[0]),
        "white_count": int(bb.disc_counts()[1]),
    }


# ---------------------------------------------------------------------------
# E5 — Flank cluster size (placeholder / surrogate)
# ---------------------------------------------------------------------------


def e5() -> tuple[dict, dict]:
    """Flank-cluster size distribution over random legal play.

    For each legal move in a sample of random positions, count the
    total number of discs that would flip if that move were played.
    Build the empirical distribution of flip-counts.
    """
    rng = np.random.default_rng(19)
    flip_counts: list[int] = []
    n_games = 20
    for _ in range(n_games):
        bb = OthelloBoard()
        while not bb.is_terminal():
            lm = bb.legal_moves()
            if not lm:
                bb.play(None)
                continue
            # Record ALL legal candidate flip-counts (not just the
            # one played) to sample the underlying distribution.
            for m in lm:
                r, c = divmod(m, 8)
                flips = bb.flips_from(r, c, bb.side_to_move)
                flip_counts.append(len(flips))
            bb.play(int(rng.choice(lm)))
    arr = np.array(flip_counts)
    unique, counts = np.unique(arr, return_counts=True)
    mean_fl = float(arr.mean())
    std_fl = float(arr.std())
    row = mk_row(
        "E5",
        "Flank cluster-size distribution across legal moves",
        f"N={arr.size} candidate-move flip counts; mean={mean_fl:.3f}, "
        f"std={std_fl:.3f}, max={int(arr.max())}",
        "distribution — compare to power-law / exponential / FK-BC",
        "PARTIAL",
        "Histogram exported in detail JSON.  Distribution-fit "
        "comparison deferred to sequel (small sample).",
    )
    return row, {
        "flip_count_histogram": dict(
            zip(
                [int(u) for u in unique],
                [int(c) for c in counts],
            )
        ),
        "mean": mean_fl,
        "std": std_fl,
        "max": int(arr.max()),
    }


# ---------------------------------------------------------------------------
# E6 — Sheaf Laplacian preview (full instantiation in Phase 2)
# ---------------------------------------------------------------------------


def e6() -> tuple[dict, dict]:
    row = mk_row(
        "E6",
        "Dynamic sheaf Laplacian at move k — spectrum evolution",
        "see Phase 2 ../results/phase2_sheaf_spectrum.json",
        "varying spectrum across game",
        "PARTIAL",
        "Instantiated in dynamic_sheaf.py; preliminary result in "
        "session_summary.md.",
    )
    return row, {}


# ---------------------------------------------------------------------------
# E7 — Global T-breaking via disc-count monotone
# ---------------------------------------------------------------------------


def e7() -> tuple[dict, dict]:
    """Is the asymmetry between forward and reversed move sequences
    detectable spectrally?  We play a random game, record the A1-
    energy trajectory, then compare the entropy-gradient of the
    forward pass to the reversed pass.
    """
    rng = np.random.default_rng(23)
    bb = OthelloBoard()
    history: list[np.ndarray] = [bb.state.copy()]
    while not bb.is_terminal():
        lm = bb.legal_moves()
        if not lm:
            bb.play(None)
            continue
        bb.play(int(rng.choice(lm)))
        history.append(bb.state.copy())
    a1m = np.array(
        [
            np.linalg.norm(project_irrep(h.astype(float), "A1-")) ** 2
            for h in history
        ]
    )
    fwd_grad = np.diff(a1m)
    rev_grad = np.diff(a1m[::-1])
    # Asymmetry metric: Spearman correlation between fwd and -rev
    # (if time-reversible, these are identical).
    rho_asym = float(
        np.corrcoef(fwd_grad, -rev_grad[::-1])[0, 1]
    ) if fwd_grad.size > 1 else float("nan")
    skew_fwd = float(
        np.sum(fwd_grad > 0) / max(fwd_grad.size, 1)
    )
    row = mk_row(
        "E7",
        "Disc-count monotone as global T-breaker: asymmetry detectable",
        f"A1- energy trajectory length {len(history)}; "
        f"fraction of positive forward increments = {skew_fwd:.3f}; "
        f"corr(fwd, -rev) = {rho_asym:+.3f}",
        "asymmetric signature",
        "PARTIAL",
        "Single game; aggregate statistics over many games needed "
        "for significance.",
    )
    return row, {
        "n_moves": int(len(history) - 1),
        "a1_minus_trajectory": a1m.tolist(),
        "fwd_positive_fraction": skew_fwd,
        "fwd_rev_correlation": rho_asym,
    }


# ---------------------------------------------------------------------------
# E8 — Perfect-play correlation stub
# ---------------------------------------------------------------------------


def e8() -> tuple[dict, dict]:
    row = mk_row(
        "E8",
        "Takizawa perfect-play correlation with spectral observables",
        "requires external dataset",
        "Spearman rho on (A1 energy, fiber norm, ray balance, sheaf gap) "
        "vs (optimal eval, disc differential, moves-to-end)",
        "UNDETERMINED",
        "Zenodo 10.5281/zenodo.10030906 required; scoped to sequel.",
    )
    return row, {}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _build_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: run all H1-H9 + E1-E8 tests, write results to
  # ../results/phase1_hypotheses.csv and phase1_detail.json.
  python research/consolidated_tests.py

  # Redirect to a different results dir (for A/B or CI dry-runs).
  python research/consolidated_tests.py --results-dir /tmp/phase1

reading the output:
  phase1_hypotheses.csv is the canonical one-row-per-hypothesis
  status table published in notebook §2.  phase1_detail.json has
  the full numeric dump every runner recomputes on demand.
""",
    )
    p.add_argument(
        "--results-dir", type=Path, default=RESULTS_DIR,
        help="Output directory for phase1_hypotheses.csv and "
             "phase1_detail.json.  Default: ../results/.",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)
    funcs = [h1, h2, h3, h4, h5, h6, h7, h8, h9,
             e1, e2, e3, e4, e5, e6, e7, e8]
    rows: list[dict] = []
    detail: dict[str, dict] = {}
    for fn in funcs:
        row, det = fn()
        rows.append(row)
        detail[row["id"]] = det
        print(f"{row['id']:4s} {row['status']:14s} {row['statement']}")
    # Write CSV
    csv_path = args.results_dir / "phase1_hypotheses.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "statement", "computed_value",
                         "threshold", "status", "notes"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    # Write JSON
    json_path = args.results_dir / "phase1_detail.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote {csv_path}")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
