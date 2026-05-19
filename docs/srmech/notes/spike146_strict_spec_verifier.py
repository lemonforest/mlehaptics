"""Spike #146 strict-spec verifier — cancer cascade-shape sign-flipped bipartite + tripartite ecology.

Trauma-informed defensive scope: research/educational only. NOT diagnostic mechanism,
NOT therapeutic guidance, NOT clinical claim. Maps Hanahan-Weinberg canonical hallmarks
to the 14 A-N primitive vocabulary using strict-spec tests per Meta-lesson 2 of
[[feedback_multi_domain_multi_round_survival_falsification_method]].

Three closed-form tests:

  (1) Class L strict-spec — bipartite Laplacian eigenvalue 2 max test.
      Normal-tissue-graph (signed bipartite) -> max eigenvalue exactly 2.
      Sign-flipped graph (one edge sign reversed) -> max eigenvalue > 2,
      signalling bipartite-spectrum violation (cancer cellular-signaling sign flip).

  (2) Class K strict-spec — asymptote violation via telomerase override.
      Hayflick limit: closed-form Michaelis-Menten-like asymptote a_n -> L as n -> inf.
      Telomerase override: replace asymptote-bound recursion with affine continuation;
      check that the strict-spec asymptote property a_{n+1}/a_n -> 1 fails (becomes
      bounded-below-by constant); strict-spec K violated.

  (3) Class L scale-2 violation — tripartite-emergence detection.
      Self/non-self bipartite immune dispatch (Class D) vs cancer's self-AND-non-self
      tripartite. Three-block Laplacian: eigenvalue 2 ceases to be the max if the
      tripartite block adds eigenmodes above 2 (strict Class L bipartite spec broken;
      Class D dispatch scale violated).

All integer/rational arithmetic where possible; only spectral step uses float64 numpy
for eigenvalue extraction (read-only; not framework-content).
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np

# ----- Test 1: Class L bipartite Laplacian eigenvalue 2 max (strict spec) -----

def normalized_laplacian(A: np.ndarray) -> np.ndarray:
    """Normalized graph Laplacian L = I - D^{-1/2} A D^{-1/2} (Chung 1997).

    For bipartite graphs, max(eigvals(L)) == 2 exactly (algebraic bipartite property).
    """
    deg = A.sum(axis=1)
    # avoid divide-by-zero for isolated vertices
    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    D_inv_sqrt = np.diag(d_inv_sqrt)
    return np.eye(A.shape[0]) - D_inv_sqrt @ A @ D_inv_sqrt


def bipartite_K33() -> np.ndarray:
    """Bipartite K_{3,3} adjacency: 3 epithelial nodes <-> 3 stromal nodes.

    Normal-tissue toy model. Bipartite by construction: edges only between sets.
    """
    n = 6
    A = np.zeros((n, n), dtype=int)
    # set A = {0,1,2}, set B = {3,4,5}; full bipartite edges
    for i in range(3):
        for j in range(3, 6):
            A[i, j] = 1
            A[j, i] = 1
    return A.astype(float)


def cancer_sign_flip_within_set(A_base: np.ndarray) -> np.ndarray:
    """Add a within-set edge — violates bipartite property (contact-inhibition loss model).

    Adding edges within set A models cells in the epithelial layer signaling each other
    in a way that breaks the bipartite epithelial<->stromal boundary. Strict spec:
    bipartite max eigenvalue == 2 should fail to remain == 2 (typically the cascade
    moves off the exact-2 attractor; we just check the bipartite signature breaks).
    """
    A = A_base.copy()
    # add edge between nodes 0 and 1 (both in set A) — within-set
    A[0, 1] = 1
    A[1, 0] = 1
    return A


def test_class_L_bipartite_signature() -> dict:
    A_normal = bipartite_K33()
    L_normal = normalized_laplacian(A_normal)
    eig_normal = np.sort(np.linalg.eigvalsh(L_normal))

    A_cancer = cancer_sign_flip_within_set(A_normal)
    L_cancer = normalized_laplacian(A_cancer)
    eig_cancer = np.sort(np.linalg.eigvalsh(L_cancer))

    max_normal = float(eig_normal[-1])
    max_cancer = float(eig_cancer[-1])

    # Chung 1997: bipartite normalized Laplacian has max eigenvalue exactly 2
    bipartite_signature_normal = abs(max_normal - 2.0) < 1e-10
    bipartite_signature_cancer = abs(max_cancer - 2.0) < 1e-10

    return {
        "test": "class_L_bipartite_signature",
        "normal_tissue_max_eig": max_normal,
        "cancer_tissue_max_eig": max_cancer,
        "bipartite_signature_intact_normal": bool(bipartite_signature_normal),
        "bipartite_signature_intact_cancer": bool(bipartite_signature_cancer),
        "verdict": "sign_flip_breaks_bipartite_signature"
            if (bipartite_signature_normal and not bipartite_signature_cancer)
            else "indeterminate",
    }


# ----- Test 2: Class K Hayflick asymptote vs telomerase override (strict spec) -----

def hayflick_recursion(a0: float, k: float, L: float, n_steps: int) -> list[float]:
    """Closed-form Michaelis-Menten-shape asymptote.

    a_{n+1} = a_n + k * (L - a_n)
    -> a_n = L - (L - a0) * (1 - k)^n
    Approaches L as n -> inf; ratio a_{n+1}/a_n -> 1 asymptotically.
    """
    seq = [a0]
    for _ in range(n_steps):
        seq.append(seq[-1] + k * (L - seq[-1]))
    return seq


def telomerase_override(a0: float, slope: float, n_steps: int) -> list[float]:
    """Affine continuation — Hayflick override; no asymptote.

    a_{n+1} = a_n + slope
    Linear growth; strict Class K asymptote property (a_{n+1}/a_n -> 1 with bounded L)
    violated by construction.
    """
    return [a0 + i * slope for i in range(n_steps + 1)]


def test_class_K_asymptote_violation() -> dict:
    n_steps = 200
    L = 50.0
    a0 = 0.0

    normal = hayflick_recursion(a0=a0, k=0.1, L=L, n_steps=n_steps)
    cancer = telomerase_override(a0=a0, slope=0.5, n_steps=n_steps)

    # Strict spec for Class K: late-stage ratio a_{n}/a_{n-1} approaches 1, AND
    # the sequence is bounded above by L.
    normal_final_ratio = normal[-1] / normal[-2] if normal[-2] != 0 else float("inf")
    cancer_final_ratio = cancer[-1] / cancer[-2] if cancer[-2] != 0 else float("inf")

    normal_bounded = max(normal) <= L + 1e-9
    cancer_bounded = max(cancer) <= L + 1e-9

    return {
        "test": "class_K_asymptote_strict_spec",
        "normal_final_ratio": float(normal_final_ratio),
        "cancer_final_ratio": float(cancer_final_ratio),
        "normal_bounded_by_L": bool(normal_bounded),
        "cancer_bounded_by_L": bool(cancer_bounded),
        "asymptote_holds_normal": bool(abs(normal_final_ratio - 1.0) < 1e-3 and normal_bounded),
        "asymptote_holds_cancer": bool(abs(cancer_final_ratio - 1.0) < 1e-3 and cancer_bounded),
        "verdict": "telomerase_override_violates_class_K_strict_spec"
            if (normal_bounded and not cancer_bounded)
            else "indeterminate",
    }


# ----- Test 3: Tripartite immune-dispatch scale violation -----

def immune_bipartite() -> np.ndarray:
    """Self / non-self bipartite — Class D dispatch over two categories."""
    n = 6
    A = np.zeros((n, n), dtype=float)
    # set self = {0,1,2}; set nonself = {3,4,5}; edges between
    for i in range(3):
        for j in range(3, 6):
            A[i, j] = 1
            A[j, i] = 1
    return A


def immune_with_emergent_third_category() -> np.ndarray:
    """Emergent third category: cells that are BOTH self AND non-self.

    Tripartite block: connected to both self set AND non-self set, but also to
    each other (within-set edges in the emergent third category) — bipartite
    over original two sets is broken; immune dispatch (Class D) misses by
    construction.
    """
    n = 9
    A = np.zeros((n, n), dtype=float)
    # original bipartite
    for i in range(3):
        for j in range(3, 6):
            A[i, j] = 1
            A[j, i] = 1
    # emergent third category {6,7,8}, connects to both sides
    for k in range(6, 9):
        for i in range(3):
            A[k, i] = 1
            A[i, k] = 1
        for j in range(3, 6):
            A[k, j] = 1
            A[j, k] = 1
    # within third category — the "self AND non-self" cluster signals to itself
    A[6, 7] = 1
    A[7, 6] = 1
    A[7, 8] = 1
    A[8, 7] = 1
    return A


def test_tripartite_immune_dispatch_violation() -> dict:
    A_normal = immune_bipartite()
    A_cancer = immune_with_emergent_third_category()

    L_normal = normalized_laplacian(A_normal)
    L_cancer = normalized_laplacian(A_cancer)

    eig_normal = np.sort(np.linalg.eigvalsh(L_normal))
    eig_cancer = np.sort(np.linalg.eigvalsh(L_cancer))

    max_normal = float(eig_normal[-1])
    max_cancer = float(eig_cancer[-1])

    bipartite_normal = abs(max_normal - 2.0) < 1e-10
    bipartite_cancer = abs(max_cancer - 2.0) < 1e-10

    return {
        "test": "tripartite_immune_dispatch_violation",
        "normal_immune_max_eig": max_normal,
        "cancer_immune_max_eig": max_cancer,
        "bipartite_self_nonself_intact_normal": bool(bipartite_normal),
        "bipartite_self_nonself_intact_cancer": bool(bipartite_cancer),
        "verdict": "emergent_third_category_breaks_class_D_dispatch_bipartition"
            if (bipartite_normal and not bipartite_cancer)
            else "indeterminate",
    }


def main() -> None:
    today = date.today().isoformat()
    results = []
    for fn in (
        test_class_L_bipartite_signature,
        test_class_K_asymptote_violation,
        test_tripartite_immune_dispatch_violation,
    ):
        r = fn()
        r["date"] = today
        r["spike"] = 146
        results.append(r)
        print(json.dumps(r))


if __name__ == "__main__":
    main()
