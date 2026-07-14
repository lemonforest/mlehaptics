"""_tool_docs_curated.py — HAND-CURATED introspection docs for the
central ops (rc240 #838). Merged OVER the docstring-seeded floor by
tools/gen_tool_docs.py (curation wins). Every EXAMPLE here is a REAL
executed result (probed by tools/gen_curated_probe.py), never typed."""
from __future__ import annotations

from typing import Any, Dict

CURATED: Dict[str, Dict[str, Any]] = {
    "srmech.amsc.cascade.magnitude": {"example": {"input": {"x": "-3.5"}, "output": "3.5"}, "explanation": "The Class-K real pin-slot magnitude |x| — the cascade-honest replacement for Python abs(): a sign-branch phase-boundary op, NOT a complex modulus (it rejects complex input by contract)."},
    "srmech.amsc.cascade.net_chirality": {"example": {"input": {"orientations": "[1, -1, 1, 1]"}, "output": "-1"}, "explanation": "Class-C net chirality: the signed product/sum reduction of a sequence of per-step orientations into the one net which-way handedness."},
    "srmech.amsc.cascade.pin_slot_at_zero": {"example": {"input": {"x": "-3.5"}, "output": "(-1, 3.5)"}, "explanation": "The Class-K pin-slot at zero: splits x into its sign (the pinned phase boundary, −1/0/+1) and its magnitude — the primitive |·| composes from."},
    "srmech.amsc.cascade.the_one": {"example": {"input": {"sigma": "1", "theta_den": "4", "theta_num": "1", "w": "(1, 0, 1)"}, "output": "One(sigma=+1, theta=(1, 4), terms=24, dim=14, partition=(1, 3, 7, 3), winding=(1, 0, 1))"}, "explanation": "The One S(σ,θ,w) = ⨁(ℝ·1 ⊕ σ·e^{Î·θ}·Im 𝔸ₙ) over the 1+3+7 Hurwitz tower (dim 2+4+8=14). σ is chirality, (θ_num/θ_den) the epicycle angle, and the winding triad w = (Saros, Metonic, Callippic) carries the spinor sign (−1)^Σw + the metacycle tower — the object whose two chiralities are one."},
    "srmech.amsc.cyclic.gcd": {"example": {"input": {"a": "12", "b": "18"}, "output": "6"}},
    "srmech.amsc.cyclic.mod_pow": {"example": {"input": {"a": "7", "k": "13", "n": "11"}, "output": "2"}, "explanation": "Modular exponentiation a^k mod n by square-and-multiply (Class-I cyclic group). Exact; the Fermat/RSA-style fast power on ℤ/n."},
    "srmech.amsc.format.sha256_bytes": {"example": {"input": {"data": "b'abc'"}, "output": "'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'"}},
    "srmech.amsc.hdc.bind": {"example": {"input": {"a": "b'abc'", "b": "b'abc'"}, "output": "b'\\x00\\x00\\x00'"}, "explanation": "Component-wise XOR of two binary-spatter-code (BSC) hypervectors — the Class-M bind that ties a role to a filler; self-inverse (bind(x,x)=0)."},
    "srmech.amsc.hdc.bundle": {"example": {"input": {"vectors": "[b'abc', b'abd', b'abe']"}, "output": "b'abe'"}, "explanation": "Majority-rule superposition of several BSC hypervectors into one that is similar to each input — the Class-M bundle (the set/record former)."},
    "srmech.amsc.hdc.similarity": {"example": {"input": {"a": "b'abc'", "b": "b'abd'"}, "output": "Q(3, 4)"}, "explanation": "Normalised agreement (1 − 2·Hamming/D) between two BSC hypervectors, as an exact rational Q. +1 = identical, 0 = orthogonal, −1 = complementary."},
    "srmech.amsc.laplacian.dense_laplacian": {"example": {"input": {"edges": "[(0, 1), (1, 2), (2, 0), (2, 3)]", "n": "4", "weights": "[1.0, 1.0, 1.0, 1.0]"}, "output": "Mat(4x4, real)"}, "explanation": "Combinatorial graph Laplacian L = D − A of a weighted undirected graph (n nodes, edges + per-edge weights) as a dense Mat — the foundation the Class-L spectral readers (fiedler / spine / eigvals) run on."},
    "srmech.amsc.laplacian.fiedler_vector": {"example": {"input": {"arg0": "Mat(4x4, real)"}, "output": "Vec(4, real)"}, "explanation": "Eigenvector of the second-smallest Laplacian eigenvalue (λ1). Its sign per node gives the natural 2-way spectral cut of the graph."},
    "srmech.amsc.laplacian.jacobi_eigvals": {"example": {"input": {"arg0": "Mat(4x4, real)"}, "output": "Vec(4, real)"}, "explanation": "Ascending eigenvalues of a symmetric Mat via cyclic Jacobi rotations (no numpy). On a graph Laplacian: λ0 = 0 for a connected graph; λ1 (the Fiedler value) measures algebraic connectivity."},
    "srmech.amsc.laplacian.spectral_spine": {"example": {"input": {"edges": "[(0, 1), (1, 2), (2, 0), (2, 3)]", "k": "3", "weights": "[1.0, 1.0, 1.0, 1.0]"}, "output": "[2, 0, 1]"}, "explanation": "The structurally-central 'spine': top-|component| nodes of the dominant-eigenvalue eigenvector — the centrality axis, complementing the community readers (fiedler 2-way / three_fold 3-way)."},
    "srmech.amsc.laplacian.three_fold_eigvec_groups": {"example": {"input": {"arg0": "Mat(4x4, real)"}, "output": "{'low': Mat(4x1, real), 'mid': Mat(4x1, real), 'high': Mat(4x2, real)}"}, "explanation": "3-way spectral partition from the sign pattern across the low eigenvectors (the k=3 community read; complements fiedler's 2-way and spine's centrality)."},
    "srmech.amsc.primes.is_prime": {"example": {"input": {"n": "97"}, "output": "True"}, "explanation": "Deterministic primality test (Class-J). True iff n is prime."},
    "srmech.amsc.rational.best_rational": {"example": {"input": {"denominator": "100000", "max_denominator": "100", "numerator": "314159"}, "output": "(22, 7)"}, "explanation": "Best rational p/q with q ≤ max_denominator approximating numerator/denominator (Class-N small-denominator anchor via continued fractions). Takes an INTEGER numerator/denominator pair, never a float."},
}
