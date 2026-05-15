"""Spike #24 bonus 11c — boundary-condition mechanism reading of the
mode-selection gap (concertmaster-dispatched, parallel with 11a/11b/11d).

Reading 3 hypothesis: Different boundary conditions on the cyclic-group
cascade factors select different sparse subsets from the full ~200-mode
periodic spectrum. The mode-selection rule is *which BC is physically
appropriate per factor* — and this is a topological choice, not a free
parameter.

Bonus 10 baseline:
    Cascade C_2 × C_7 × C_4 × C_6 × C_16 with radii
    (3659.035, 1.0287, 1.4428, 104.193, 135758.328)
    achieved log-L2 = 0.614 via subset-selection (9-of-~200 modes)
    but log-L2 = 3.32 strict lightest-9.

This probe asks: does any BC combination from
    {periodic, anti-periodic, Dirichlet, Neumann, twisted(theta)}
applied per factor produce lightest-9 match < 1.0 dex on the SM target?

If YES: CLOSURE — the mode-selection rule IS a BC choice; gap closed.
If NO: NEGATIVE — gap remains for parallel-reading alternatives.

Discipline guards (concertmaster-level):
  - Per `feedback_antiquity_not_greek`: Class L spectral-graph falsifier
    on directed/anti-periodic/Dirichlet Laplacian variants.
  - Per `feedback_trauma_informed_defensive_scope`: methodological only.
  - Per `feedback_ndjson_over_bloated_json`: NDJSON output.
  - Per `feedback_pdf_extraction_citation_discipline`: SM masses from PDG.
  - Per `feedback_no_lineage_claims_in_notebook`: no academic-lineage
    framings about external work.
  - stdlib + numpy + scipy ONLY; isolated venv at .venv_bonus_11c.
  - Per-PID isolation: this script never broad-kills processes.
  - Deterministic seed = 20260515 for any randomness.
  - No new primitive class invented; Class L applied to multiple
    Laplacian-construction variants (BC choice is part of Class L's
    operational specification, not a new class).
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15"
PROBE_VERSION = "0.1.0"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_11c_mode_selection_boundary_conditions_probe_2026-05-15.ndjson"

START_TIME = time.time()
MY_PID = os.getpid()


# ----------------------------------------------------------------------------
# MFO §IV.6 SM mass² target spectrum (PDG 2024 charged-fermion masses)
# Normalised to (m/m_e)^2. Sorted ascending by mass.
# ----------------------------------------------------------------------------
SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASSES_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])
LOG10_TARGET = np.log10(SM_MASS_SQ_RATIOS)
N_TARGET = len(SM_MASS_SQ_RATIOS)  # 9


# ----------------------------------------------------------------------------
# Boundary-condition variants — Class L (spectral-graph Laplacian) applied
# under different topological choices per factor.
# ----------------------------------------------------------------------------
# Eigenvalues for cyclic-group / chain Laplacians with different BCs:
#
#  periodic       : closed-loop, lambda_k = 2(1 - cos(2pi k / n)),  k=0..n-1
#                   has a zero mode at k=0.
#  antiperiodic   : twisted by pi (fermionic on the circle),
#                   lambda_k = 2(1 - cos(pi(2k+1)/n)),  k=0..n-1
#                   no zero mode.
#  twisted(theta) : ψ(0) = e^{iθ} ψ(n_i), eigenvalues
#                   lambda_k = 2(1 - cos((2pi k + theta)/n)),  k=0..n-1.
#                   theta=0 → periodic; theta=pi → antiperiodic.
#  dirichlet      : open chain length n, ψ(0)=ψ(n)=0.
#                   lambda_k = 2(1 - cos(pi k / n)),  k=1..n-1.
#                   no zero mode; n-1 eigenvalues.
#  neumann        : open chain length n, derivative-zero at ends.
#                   lambda_k = 2(1 - cos(pi k / n)),  k=0..n-1.
#                   has a zero mode at k=0.
#
# All scale by 1/radius^2.
# ----------------------------------------------------------------------------
def cyclic_eigs_periodic(n: int, radius: float) -> np.ndarray:
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


def cyclic_eigs_antiperiodic(n: int, radius: float) -> np.ndarray:
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(math.pi * (2 * k + 1) / n))


def cyclic_eigs_twisted(n: int, radius: float, theta: float) -> np.ndarray:
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos((2.0 * math.pi * k + theta) / n))


def cyclic_eigs_dirichlet(n: int, radius: float) -> np.ndarray:
    # open chain of length n: n nodes, edges between adjacent, both ends fixed.
    # The eigenvalues of -d^2/dx^2 on [0, L] with Dirichlet are
    # (k pi / L)^2 → discretised: 2(1 - cos(k pi / n)) for k=1..n.
    # We take k=1..n-1 for n-1 eigenvalues (the n-th = n*pi mode is the
    # Nyquist edge; convention: use n-1 modes which match the n-1 interior
    # nodes of the open chain).
    k = np.arange(1, n)
    return (2.0 / radius**2) * (1.0 - np.cos(math.pi * k / n))


def cyclic_eigs_neumann(n: int, radius: float) -> np.ndarray:
    # open chain of length n, derivative-zero ends → cosine basis,
    # eigenvalues 2(1 - cos(k pi / n)) for k=0..n-1.
    # k=0 is the constant (zero) mode.
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(math.pi * k / n))


# BC type codes for compact descriptor records.
BC_TYPES = ("periodic", "antiperiodic", "dirichlet", "neumann", "twisted_pi2")
# We include a single "twisted at theta=pi/2" sample as the representative
# generic twisted condition; periodic (theta=0) and antiperiodic (theta=pi)
# are already covered. theta=pi/2 is the quarter-twist (a "spin-c-like"
# intermediate condition that sits between fermionic and bosonic BCs).


def eigs_for_bc(n: int, radius: float, bc: str) -> np.ndarray:
    if bc == "periodic":
        return cyclic_eigs_periodic(n, radius)
    if bc == "antiperiodic":
        return cyclic_eigs_antiperiodic(n, radius)
    if bc == "dirichlet":
        return cyclic_eigs_dirichlet(n, radius)
    if bc == "neumann":
        return cyclic_eigs_neumann(n, radius)
    if bc == "twisted_pi2":
        return cyclic_eigs_twisted(n, radius, math.pi / 2.0)
    raise ValueError(f"unknown bc: {bc}")


# ----------------------------------------------------------------------------
# Product-Laplacian eigenvalue composition (Class E primitive)
# ----------------------------------------------------------------------------
def product_eigenvalues_smallest(factor_spectra: List[np.ndarray], topN: int) -> np.ndarray:
    """Smallest topN eigenvalues of the direct-product Laplacian.

    Product-Laplacian rule: lambda = sum_j lambda_{i_j}^(j).
    """
    current = np.sort(factor_spectra[0])
    for spectrum in factor_spectra[1:]:
        spec_sorted = np.sort(spectrum)
        all_sums = current[:, None] + spec_sorted[None, :]
        flat = np.sort(all_sums.ravel())
        keep = min(len(flat), max(topN * 4, 64))
        current = flat[:keep]
    return np.sort(current)[:topN]


# ----------------------------------------------------------------------------
# Cascade with per-factor BC labels.
# ----------------------------------------------------------------------------
@dataclass
class CascadeBC:
    ns: Tuple[int, ...]
    rs: Tuple[float, ...]
    bcs: Tuple[str, ...]  # per-factor BC label

    @property
    def k(self) -> int:
        return len(self.ns)

    def factor_spectra(self) -> List[np.ndarray]:
        return [eigs_for_bc(n, r, bc) for n, r, bc in zip(self.ns, self.rs, self.bcs)]


# ----------------------------------------------------------------------------
# Matching metrics — lightest-9 strict + subset-match (bonus 10 metric)
# ----------------------------------------------------------------------------
def lightest9_score(eigs: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
    """Bonus 10's lightest-9 strict metric.

    Take 9 smallest non-zero eigenvalues, normalise to lightest, compute
    log10-L2 distance to SM target log-ratios.
    """
    nonzero = eigs[eigs > 1e-12]
    if len(nonzero) < N_TARGET:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf))
    top9 = nonzero[:N_TARGET]
    ratios = top9 / top9[0]
    log_pred = np.log10(ratios)
    diffs = log_pred - LOG10_TARGET
    score = float(np.sqrt(np.sum(diffs**2)))
    return score, ratios, diffs


def subset_match_score(eigs: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray, List[int]]:
    """Bonus 10's subset-match metric.

    Find best 9-mode subset from top eigenvalues that matches SM target.
    Greedy nearest-log10 selection per target ratio.
    """
    nonzero = eigs[eigs > 1e-12]
    if len(nonzero) < N_TARGET:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), list(range(N_TARGET)))
    log_eigs = np.log10(nonzero)
    best_score = np.inf
    best_ratios = None
    best_diffs = None
    best_indices: List[int] = []
    n_anchors = min(20, len(nonzero))
    for anchor_idx in range(n_anchors):
        anchor_log = log_eigs[anchor_idx]
        rel_log_eigs = log_eigs - anchor_log
        selected_indices = [anchor_idx]
        selected_log_ratios = [0.0]
        used = {anchor_idx}
        valid = True
        for target_log in LOG10_TARGET[1:]:
            best_local_idx = -1
            best_local_dist = np.inf
            for j in range(len(rel_log_eigs)):
                if j in used:
                    continue
                d = abs(rel_log_eigs[j] - target_log)
                if d < best_local_dist:
                    best_local_dist = d
                    best_local_idx = j
            if best_local_idx == -1:
                valid = False
                break
            used.add(best_local_idx)
            selected_indices.append(best_local_idx)
            selected_log_ratios.append(rel_log_eigs[best_local_idx])
        if not valid:
            continue
        log_diffs = np.array(selected_log_ratios) - LOG10_TARGET
        score = float(np.sqrt(np.sum(log_diffs**2)))
        if score < best_score:
            best_score = score
            best_ratios = 10.0 ** np.array(selected_log_ratios)
            best_diffs = log_diffs
            best_indices = list(selected_indices)
    if best_ratios is None:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), list(range(N_TARGET)))
    return best_score, best_ratios, best_diffs, best_indices


# ----------------------------------------------------------------------------
# Reference cascades from bonus 10's top-3 subset-match candidates
# (using the same radii as the bonus 10 winners, so BC is the ONLY
# independent variable here).
# ----------------------------------------------------------------------------
REFERENCE_CASCADES = [
    {
        "label": "rank1_subset",
        "ns": (2, 7, 4, 6, 16),
        "rs": (3659.03506590957, 1.0286749515294853, 1.442834378987582, 104.19253977340335, 135758.32777190334),
        "bonus10_subset_score": 0.614,
        "bonus10_lightest9_score": 15.622,  # this cascade does very poorly on lightest9
    },
    {
        "label": "rank2_subset",
        "ns": (4, 17, 2, 5),
        "rs": (4.228091168870134, 367386.7909205613, 10282.072777272158, 336.1679820892126),
        "bonus10_subset_score": 0.637,
        "bonus10_lightest9_score": None,
    },
    {
        "label": "rank3_subset",
        "ns": (7, 2, 14, 4),
        "rs": (63.29422595842321, 2299.719998588086, 102290.34949178646, 1.0),
        "bonus10_subset_score": 0.677,
        "bonus10_lightest9_score": None,
    },
    # Bonus 10's lightest-9 best cascade (different from rank-1 subset winner).
    # This is the strict-metric reference and the proper "can BC close the
    # lightest-9 gap" target.
    {
        "label": "rank1_lightest9",
        "ns": (2, 2, 13, 2),
        "rs": (1058376.3333733503, 1394.028369520248, 4.81563761558375, 170063.20569750882),
        "bonus10_subset_score": None,
        "bonus10_lightest9_score": 3.318,
    },
]


# ----------------------------------------------------------------------------
# BC sweep — full Cartesian over BC_TYPES per factor.
# ----------------------------------------------------------------------------
def sweep_bcs_on_cascade(
    cascade_label: str,
    ns: Tuple[int, ...],
    rs: Tuple[float, ...],
    n_keep: int = 200,
) -> Tuple[List[Dict], Dict]:
    """Sweep all BC combinations on a fixed (ns, rs) cascade.

    Returns (per_combination_records, summary_record).
    """
    k = len(ns)
    n_combos = len(BC_TYPES) ** k
    records: List[Dict] = []
    best_lightest9 = (np.inf, None, None, None)
    best_subset = (np.inf, None, None, None, None)
    n_evaluated = 0
    n_failed = 0

    for bc_tuple in itertools.product(BC_TYPES, repeat=k):
        cascade = CascadeBC(ns=ns, rs=rs, bcs=bc_tuple)
        specs = cascade.factor_spectra()
        # Skip if any factor has < N_TARGET nonzero modes (e.g. small Dirichlet).
        # We allow any combination; product spectrum is the relevant size.
        try:
            eigs = product_eigenvalues_smallest(specs, topN=n_keep)
        except Exception as exc:
            n_failed += 1
            continue
        lscore, lratios, ldiffs = lightest9_score(eigs)
        sscore, sratios, sdiffs, sidx = subset_match_score(eigs)

        n_evaluated += 1
        if lscore < best_lightest9[0]:
            best_lightest9 = (lscore, bc_tuple, lratios, ldiffs)
        if sscore < best_subset[0]:
            best_subset = (sscore, bc_tuple, sratios, sdiffs, sidx)

        # Record only the better-than-bonus-10-subset hits to limit NDJSON size;
        # OR record all that are CLOSURE-grade (lightest9 < 1.0).
        if lscore < 5.0 or sscore < 0.7:
            records.append({
                "record": "bc_combination",
                "probe": PROBE_NAME,
                "cascade_label": cascade_label,
                "ns": list(ns),
                "log10_rs": [math.log10(r) for r in rs],
                "bcs": list(bc_tuple),
                "lightest9_log_L2": lscore,
                "subset_match_log_L2": sscore,
                "n_modes_kept": n_keep,
            })

    summary = {
        "record": "bc_sweep_summary",
        "probe": PROBE_NAME,
        "cascade_label": cascade_label,
        "ns": list(ns),
        "rs": list(rs),
        "log10_rs": [math.log10(r) for r in rs],
        "n_combos_attempted": n_combos,
        "n_evaluated": n_evaluated,
        "n_failed": n_failed,
        "bc_types_per_factor": list(BC_TYPES),
        "best_lightest9": {
            "log_L2": best_lightest9[0],
            "bcs": list(best_lightest9[1]) if best_lightest9[1] else None,
            "predicted_9_ratios": (best_lightest9[2].tolist()
                                   if best_lightest9[2] is not None else None),
            "log10_diffs": (best_lightest9[3].tolist()
                            if best_lightest9[3] is not None else None),
        },
        "best_subset": {
            "log_L2": best_subset[0],
            "bcs": list(best_subset[1]) if best_subset[1] else None,
            "predicted_9_ratios": (best_subset[2].tolist()
                                   if best_subset[2] is not None else None),
            "log10_diffs": (best_subset[3].tolist()
                            if best_subset[3] is not None else None),
            "selected_mode_indices": best_subset[4],
        },
    }
    return records, summary


# ----------------------------------------------------------------------------
# Sanity check — replicate bonus 10's all-periodic result.
# ----------------------------------------------------------------------------
def replicate_bonus10(cascade_dict: Dict) -> Dict:
    ns = cascade_dict["ns"]
    rs = cascade_dict["rs"]
    k = len(ns)
    cascade = CascadeBC(ns=ns, rs=rs, bcs=tuple(["periodic"] * k))
    specs = cascade.factor_spectra()
    eigs = product_eigenvalues_smallest(specs, topN=200)
    lscore, lratios, ldiffs = lightest9_score(eigs)
    sscore, sratios, sdiffs, sidx = subset_match_score(eigs)
    rec = {
        "record": "bonus10_replication_check",
        "probe": PROBE_NAME,
        "cascade_label": cascade_dict["label"],
        "ns": list(ns),
        "all_periodic_lightest9_log_L2": lscore,
        "all_periodic_subset_log_L2": sscore,
        "bonus10_reported_subset": cascade_dict.get("bonus10_subset_score"),
        "bonus10_reported_lightest9": cascade_dict.get("bonus10_lightest9_score"),
    }
    # Check whichever metric bonus 10 reported for this cascade
    if cascade_dict.get("bonus10_subset_score") is not None:
        rec["subset_replication_delta"] = abs(sscore - cascade_dict["bonus10_subset_score"])
        rec["subset_replication_ok"] = rec["subset_replication_delta"] < 0.01
    if cascade_dict.get("bonus10_lightest9_score") is not None:
        rec["lightest9_replication_delta"] = abs(lscore - cascade_dict["bonus10_lightest9_score"])
        rec["lightest9_replication_ok"] = rec["lightest9_replication_delta"] < 0.01
    return rec


# ----------------------------------------------------------------------------
# Per-factor BC ablation — which factor's BC matters most for the gap?
# ----------------------------------------------------------------------------
def per_factor_ablation(
    cascade_label: str,
    ns: Tuple[int, ...],
    rs: Tuple[float, ...],
    best_bcs: Tuple[str, ...],
) -> List[Dict]:
    """Take the best BC combination and check what happens if each factor's
    BC is reverted to periodic (the bonus 10 baseline).

    This identifies which factor's BC choice carries the most weight.
    """
    out = []
    for i in range(len(ns)):
        bcs_ablated = list(best_bcs)
        bcs_ablated[i] = "periodic"
        cascade = CascadeBC(ns=ns, rs=rs, bcs=tuple(bcs_ablated))
        specs = cascade.factor_spectra()
        eigs = product_eigenvalues_smallest(specs, topN=200)
        lscore, _, _ = lightest9_score(eigs)
        sscore, _, _, _ = subset_match_score(eigs)
        out.append({
            "record": "per_factor_ablation",
            "probe": PROBE_NAME,
            "cascade_label": cascade_label,
            "factor_index": i,
            "factor_n": ns[i],
            "factor_radius": rs[i],
            "best_bcs": list(best_bcs),
            "ablated_bc_to_periodic": bcs_ablated[i],
            "ablated_bcs": bcs_ablated,
            "lightest9_log_L2": lscore,
            "subset_match_log_L2": sscore,
        })
    return out


# ----------------------------------------------------------------------------
# Provenance / probe self-hash
# ----------------------------------------------------------------------------
def probe_self_hash() -> str:
    src_path = Path(__file__)
    src_bytes = src_path.read_bytes()
    return hashlib.sha256(src_bytes).hexdigest()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    records: List[Dict] = []

    # Provenance.
    records.append({
        "record": "provenance",
        "probe": PROBE_NAME,
        "probe_version": PROBE_VERSION,
        "probe_self_sha256": probe_self_hash(),
        "seed": SEED,
        "platform_python": sys.version,
        "platform": sys.platform,
        "pid": MY_PID,
        "isolated_venv": ".venv_bonus_11c",
        "spec": (
            "Bonus 11c — boundary-condition mechanism reading of mode-selection gap. "
            "Sweep all BC combinations over {periodic, antiperiodic, dirichlet, "
            "neumann, twisted_pi2} per cascade factor; check whether any BC "
            "combination achieves lightest-9 < 1.0 dex on SM target (CLOSURE), "
            "improves over bonus 10's subset-match 0.614 (PARTIAL), or fails "
            "to outperform bonus 10 baseline (NEGATIVE)."
        ),
        "bonus10_baseline": {
            "subset_match_log_L2": 0.614,
            "lightest9_strict_log_L2": 3.32,
            "cascade": "C_2 x C_7 x C_4 x C_6 x C_16",
            "bcs": "all periodic",
        },
        "target": "SM charged-fermion mass^2 ratios (PDG 2024, 9 elements)",
        "bc_variants_tested": list(BC_TYPES),
        "sm_fermions": SM_FERMIONS,
        "sm_log10_target_ratios": LOG10_TARGET.tolist(),
    })

    # Step 1: Replicate bonus 10's all-periodic result on each reference cascade.
    print(f"[{time.time()-START_TIME:.1f}s] Step 1: bonus 10 replication checks")
    for cdict in REFERENCE_CASCADES:
        rec = replicate_bonus10(cdict)
        msg = f"  {cdict['label']}: L9={rec['all_periodic_lightest9_log_L2']:.3f}, subset={rec['all_periodic_subset_log_L2']:.3f}"
        if cdict.get('bonus10_subset_score') is not None:
            msg += f" [bonus10 subset={cdict['bonus10_subset_score']:.3f}]"
        if cdict.get('bonus10_lightest9_score') is not None:
            msg += f" [bonus10 L9={cdict['bonus10_lightest9_score']:.3f}]"
        print(msg)
        records.append(rec)

    # Step 2: Full BC sweep on each reference cascade.
    print(f"\n[{time.time()-START_TIME:.1f}s] Step 2: BC sweep on rank-1 cascade "
          f"(5^5 = {5**5} combinations)")
    rec_list_1, summary_1 = sweep_bcs_on_cascade(
        cascade_label=REFERENCE_CASCADES[0]["label"],
        ns=REFERENCE_CASCADES[0]["ns"],
        rs=REFERENCE_CASCADES[0]["rs"],
        n_keep=200,
    )
    print(f"  rank1 BC sweep: evaluated {summary_1['n_evaluated']}/{summary_1['n_combos_attempted']}")
    print(f"  best lightest9: log_L2={summary_1['best_lightest9']['log_L2']:.3f} "
          f"bcs={summary_1['best_lightest9']['bcs']}")
    print(f"  best subset:    log_L2={summary_1['best_subset']['log_L2']:.3f} "
          f"bcs={summary_1['best_subset']['bcs']}")
    records.append(summary_1)
    records.extend(rec_list_1)

    print(f"\n[{time.time()-START_TIME:.1f}s] Step 3: BC sweep on rank-2 cascade "
          f"(5^4 = {5**4} combinations)")
    rec_list_2, summary_2 = sweep_bcs_on_cascade(
        cascade_label=REFERENCE_CASCADES[1]["label"],
        ns=REFERENCE_CASCADES[1]["ns"],
        rs=REFERENCE_CASCADES[1]["rs"],
        n_keep=200,
    )
    print(f"  rank2 BC sweep: evaluated {summary_2['n_evaluated']}/{summary_2['n_combos_attempted']}")
    print(f"  best lightest9: log_L2={summary_2['best_lightest9']['log_L2']:.3f} "
          f"bcs={summary_2['best_lightest9']['bcs']}")
    print(f"  best subset:    log_L2={summary_2['best_subset']['log_L2']:.3f} "
          f"bcs={summary_2['best_subset']['bcs']}")
    records.append(summary_2)
    records.extend(rec_list_2)

    print(f"\n[{time.time()-START_TIME:.1f}s] Step 4: BC sweep on rank-3 cascade "
          f"(5^4 = {5**4} combinations)")
    rec_list_3, summary_3 = sweep_bcs_on_cascade(
        cascade_label=REFERENCE_CASCADES[2]["label"],
        ns=REFERENCE_CASCADES[2]["ns"],
        rs=REFERENCE_CASCADES[2]["rs"],
        n_keep=200,
    )
    print(f"  rank3 BC sweep: evaluated {summary_3['n_evaluated']}/{summary_3['n_combos_attempted']}")
    print(f"  best lightest9: log_L2={summary_3['best_lightest9']['log_L2']:.3f} "
          f"bcs={summary_3['best_lightest9']['bcs']}")
    print(f"  best subset:    log_L2={summary_3['best_subset']['log_L2']:.3f} "
          f"bcs={summary_3['best_subset']['bcs']}")
    records.append(summary_3)
    records.extend(rec_list_3)

    # Step 4b: BC sweep on the bonus 10 lightest-9 winner cascade.
    # This is the proper "can BC close the lightest-9 gap" test.
    print(f"\n[{time.time()-START_TIME:.1f}s] Step 4b: BC sweep on rank-1 lightest-9 cascade "
          f"(C_2 x C_2 x C_13 x C_2; bonus 10 reported L9=3.32 baseline) "
          f"(5^4 = {5**4} combinations)")
    rec_list_l9, summary_l9 = sweep_bcs_on_cascade(
        cascade_label=REFERENCE_CASCADES[3]["label"],
        ns=REFERENCE_CASCADES[3]["ns"],
        rs=REFERENCE_CASCADES[3]["rs"],
        n_keep=200,
    )
    print(f"  rank1_lightest9 BC sweep: evaluated {summary_l9['n_evaluated']}/{summary_l9['n_combos_attempted']}")
    print(f"  best lightest9: log_L2={summary_l9['best_lightest9']['log_L2']:.3f} "
          f"bcs={summary_l9['best_lightest9']['bcs']}")
    print(f"  best subset:    log_L2={summary_l9['best_subset']['log_L2']:.3f} "
          f"bcs={summary_l9['best_subset']['bcs']}")
    records.append(summary_l9)
    records.extend(rec_list_l9)

    # Step 5: Per-factor ablation on the rank-1 winner.
    print(f"\n[{time.time()-START_TIME:.1f}s] Step 5: per-factor ablation on rank-1 best")
    best_bcs_1 = tuple(summary_1["best_lightest9"]["bcs"])
    ablation_records = per_factor_ablation(
        cascade_label=REFERENCE_CASCADES[0]["label"],
        ns=REFERENCE_CASCADES[0]["ns"],
        rs=REFERENCE_CASCADES[0]["rs"],
        best_bcs=best_bcs_1,
    )
    for r in ablation_records:
        print(f"  ablate factor {r['factor_index']} (n={r['factor_n']}, "
              f"{r['ablated_bc_to_periodic']}): "
              f"lightest9={r['lightest9_log_L2']:.3f}, subset={r['subset_match_log_L2']:.3f}")
    records.extend(ablation_records)

    # Step 6: Verdict
    best_overall_lightest9 = min(
        summary_1["best_lightest9"]["log_L2"],
        summary_2["best_lightest9"]["log_L2"],
        summary_3["best_lightest9"]["log_L2"],
        summary_l9["best_lightest9"]["log_L2"],
    )
    best_overall_subset = min(
        summary_1["best_subset"]["log_L2"],
        summary_2["best_subset"]["log_L2"],
        summary_3["best_subset"]["log_L2"],
        summary_l9["best_subset"]["log_L2"],
    )

    if best_overall_lightest9 < 1.0:
        verdict = "CLOSURE"
        reason = (f"Lightest-9 strict log_L2 = {best_overall_lightest9:.3f} < 1.0 SUCCESS "
                  f"threshold. A specific BC choice on the cascade gives natural mass²"
                  f" match without subset selection. The mode-selection gap IS a BC choice.")
    elif best_overall_lightest9 < 2.5:
        verdict = "PARTIAL_STRONG"
        reason = (f"Lightest-9 strict log_L2 = {best_overall_lightest9:.3f} ∈ [1.0, 2.5). "
                  f"Substantial improvement over bonus 10 baseline 3.32 but does not "
                  f"clear SUCCESS threshold. BC mechanism is meaningfully active but "
                  f"insufficient alone for full closure.")
    elif best_overall_lightest9 < 3.32:
        verdict = "PARTIAL_WEAK"
        reason = (f"Lightest-9 strict log_L2 = {best_overall_lightest9:.3f} ∈ [2.5, 3.32). "
                  f"Marginal improvement over bonus 10 baseline 3.32. BC choice has "
                  f"second-order effect on the mode-selection gap.")
    else:
        verdict = "NEGATIVE"
        reason = (f"Lightest-9 strict log_L2 = {best_overall_lightest9:.3f} ≥ 3.32. "
                  f"No BC combination outperforms bonus 10's periodic baseline. "
                  f"The mode-selection gap is NOT closable by BC choice alone.")

    records.append({
        "record": "verdict",
        "probe": PROBE_NAME,
        "verdict": verdict,
        "best_overall_lightest9_log_L2": best_overall_lightest9,
        "best_overall_subset_log_L2": best_overall_subset,
        "bonus10_lightest9_baseline": 3.32,
        "bonus10_subset_baseline": 0.614,
        "success_threshold_lightest9": 1.0,
        "improvement_vs_lightest9_baseline": 3.32 - best_overall_lightest9,
        "improvement_vs_subset_baseline": 0.614 - best_overall_subset,
        "reason": reason,
    })

    # Totals + integrity.
    elapsed = time.time() - START_TIME
    records.append({
        "record": "totals",
        "probe": PROBE_NAME,
        "n_records": len(records) + 1,
        "elapsed_seconds": elapsed,
        "n_bc_combinations_total": 5**5 + 5**4 + 5**4 + 5**4,
        "n_factor_evaluations": (5**5) * 5 + (5**4) * 4 + (5**4) * 4 + (5**4) * 4,
        "completion_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    # Write NDJSON.
    with open(NDJSON_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str))
            f.write("\n")

    # Integrity record over NDJSON.
    ndjson_bytes = NDJSON_PATH.read_bytes()
    integrity = {
        "record": "integrity",
        "probe": PROBE_NAME,
        "ndjson_sha256": hashlib.sha256(ndjson_bytes).hexdigest(),
        "ndjson_bytes": len(ndjson_bytes),
        "n_records_written": len(records),
    }
    with open(NDJSON_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(integrity))
        f.write("\n")

    print(f"\n[{time.time()-START_TIME:.1f}s] DONE")
    print(f"  Verdict: {verdict}")
    print(f"  best lightest9: {best_overall_lightest9:.3f} (vs bonus10 3.32)")
    print(f"  best subset:    {best_overall_subset:.3f} (vs bonus10 0.614)")
    print(f"  NDJSON: {NDJSON_PATH}")


if __name__ == "__main__":
    main()
