"""MAP-B Hyperdimensional Computing primitives.

Representation
--------------
Hypervectors are float64 arrays with entries in {−1, +1}. This is MAP-B
(bipolar) — the simplest VSA variant with the cleanest unbind behaviour:

    bind(a, b) = a ⊙ b        (elementwise)
    unbind(c, a) = a ⊙ c       (self-inverse: unbind(bind(a,b), a) = b)
    bundle([v_i]) = sign(Σ v_i)   (majority vote, ties → +1)
    perm(v, k) = np.roll(v, k)    (permutation; optional ordering op)

Why MAP-B over FHRR/BSC:
    - bipolar is self-inverse under binding (no explicit inverse op)
    - cosine similarity is linear in bit-agreement (interpretable)
    - all ops are cheap numpy elementwise

Determinism
-----------
`atom(name)` returns the same HV across runs for the same name. The
seed is deterministic per-(name, dim), derived from a hash. This gives
us the "seeded codebook" property Steven's chess-spectral tables
pattern established.
"""
from __future__ import annotations

import hashlib
from typing import Iterable, List, Sequence, Union

import numpy as np

DEFAULT_DIM = 10_000

# Type alias — stays thin on purpose.
HD = np.ndarray


# ─── Atom creation (deterministic from name) ──────────────────────

def rng_for(name: str, *, dim: int = DEFAULT_DIM) -> np.random.Generator:
    """Deterministic RNG seeded from `name` + `dim`. Used for atoms and
    for any other stream that needs stable-across-runs randomness."""
    h = hashlib.blake2b(
        f"{name}|dim={dim}".encode("utf-8"),
        digest_size=8,
    ).digest()
    seed = int.from_bytes(h, "little", signed=False)
    return np.random.default_rng(seed)


def atom(name: str, *, dim: int = DEFAULT_DIM) -> HD:
    """Deterministic bipolar atom — same name → same vector, every run."""
    rng = rng_for(name, dim=dim)
    return rng.choice(np.array([-1.0, 1.0], dtype=np.float64), size=dim)


def random_hv(*, dim: int = DEFAULT_DIM, rng: np.random.Generator | None = None) -> HD:
    """Fresh random bipolar HV — non-deterministic unless `rng` given."""
    rng = rng if rng is not None else np.random.default_rng()
    return rng.choice(np.array([-1.0, 1.0], dtype=np.float64), size=dim)


# ─── Core VSA ops ─────────────────────────────────────────────────

def bind(a: HD, b: HD) -> HD:
    """Elementwise bipolar bind. Self-inverse: bind(bind(a,b), a) = b."""
    return a * b


def unbind(c: HD, a: HD) -> HD:
    """Inverse of bind, for bipolar MAP-B. Same as bind (self-inverse)."""
    return a * c


def bundle(vs: Sequence[HD]) -> HD:
    """Majority-vote bundle. Ties (sum == 0) resolve to +1 to stay bipolar.

    For weighted bundles we pre-scale the vectors and use bundle_sum
    below to avoid re-binarizing prematurely.
    """
    if len(vs) == 0:
        raise ValueError("bundle() needs at least one vector")
    s = np.sum(vs, axis=0)
    out = np.sign(s)
    out[out == 0.0] = 1.0
    return out


def bundle_sum(vs: Sequence[HD]) -> HD:
    """Weighted-friendly bundle: returns the raw sum (not binarized).

    Use this when you'll do further arithmetic before cleanup. The
    result is a real-valued vector; `np.sign(...)` gets you back to
    bipolar when needed.
    """
    return np.sum(vs, axis=0)


def perm(v: HD, k: int = 1) -> HD:
    """Cyclic permutation (rotation by k). Used for sequence ordering."""
    return np.roll(v, k)


# ─── Similarity & cleanup ─────────────────────────────────────────

def sim(a: HD, b: HD) -> float:
    """Cosine similarity — on bipolar HVs this is (agreement − disagreement)/D."""
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def normalize(v: HD) -> HD:
    """Map real-valued HV back to bipolar via sign."""
    out = np.sign(v)
    out[out == 0.0] = 1.0
    return out


def cleanup(
    probe: HD,
    codebook: dict[str, HD],
    *,
    top_k: int = 1,
) -> List[tuple[str, float]]:
    """Find the top_k codebook entries most similar to `probe`.

    Returns list of (name, sim) sorted descending.
    """
    scored = [(name, sim(probe, hv)) for name, hv in codebook.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
