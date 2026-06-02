"""srmech.rbs_lm.inference — the native, bit-exact, catalog-instantiable RBS-LM
inference substrate (F166 Step 5: the fully-realized artifact).

Ported from the research subtree's ``_rbs_lm_inference`` (UPSTREAM_NOTES §9).
This is the F166 goal made an object: an inference substrate built UP from the
28D Klein-4 coordinate, NOT distilled DOWN from float weights. It composes the
four stones of the walk into one clean API, parameterized by the descriptor
catalog (``from_catalog``) OR an in-memory params dict (``from_params``):

  Step 1  ContextSubstrate.encode_context  — last-k tokens → ONE Klein-4 state
  Step 2  next_token_distribution          — Class M retrieve over bigram-legal candidates
  Step 3  temperature                       — the recall↔diversity dial (cold regime)
  Step 4  infer                             — the autoregressive loop (= inference)

Determinism / attestation: SHA-256 token seeds → fixed Klein-4 vectors; exact XOR
bind; seeded sampling. Same corpus + same params + same srmech_version + same
seed → bit-exact identical output. attestation() returns the MPR block so any
generated sequence is re-derivable and citable.

Per [[user_stance_kepler_shape_universal]]: inference IS a named A-N cascade
(Class A∘M encode + iω₇ position, Class M retrieve, temperature sample) iterated.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from srmech.amsc import hdc

from . import substrate as cs


def _softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


@dataclass
class RBSLMInferenceSubstrate:
    """Native RBS-LM inference substrate (F166).

    Build via :meth:`from_catalog` (the descriptor TOML SSOT) or
    :meth:`from_params` (an in-memory params dict — same key structure the
    catalog yields, for tests / programmatic callers without a TOML file).
    """

    ctx: cs.ContextSubstrate
    operating_k: int
    operating_temperature: float
    memory_capacity: int
    default_max_tokens: int
    learn_seed: int
    descriptor_hash: str
    srmech_version: str
    abi_version: int
    has_native: bool

    # learned state (populated by .learn())
    vocab: list[str] = field(default_factory=list)
    vocab_vecs: np.ndarray | None = None
    vocab_idx: dict[str, int] = field(default_factory=dict)
    next_after: dict[str, list[str]] = field(default_factory=dict)
    bigram_counts: dict[str, Counter] = field(default_factory=dict)
    M: np.ndarray | None = None
    n_learned: int = 0

    # ----------------------------------------------------------------- build
    @classmethod
    def _build(cls, params: Mapping, *, descriptor_hash: str) -> "RBSLMInferenceSubstrate":
        """Shared construction from a ``literature_curated``-shaped params dict.

        ``params`` carries the same nested structure the descriptor catalog
        yields under ``desc.fetch["literature_curated"]``: a ``substrate`` table
        (D / token_seed_hex_chars) and an ``inference.instrument`` table
        (operating_k / operating_temperature / memory_capacity /
        default_max_tokens / learn_seed)."""
        from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
        from srmech import __version__ as SRMECH_VERSION

        sub = params["substrate"]
        inst = params["inference"]["instrument"]
        ctx = cs.ContextSubstrate(D=int(sub["D"]),
                                  hex_chars=int(sub["token_seed_hex_chars"]))
        return cls(
            ctx=ctx,
            operating_k=int(inst["operating_k"]),
            operating_temperature=float(inst["operating_temperature"]),
            memory_capacity=int(inst["memory_capacity"]),
            default_max_tokens=int(inst["default_max_tokens"]),
            learn_seed=int(inst["learn_seed"]),
            descriptor_hash=descriptor_hash,
            srmech_version=SRMECH_VERSION,
            abi_version=NATIVE_ABI_VERSION,
            has_native=HAS_NATIVE,
        )

    @classmethod
    def from_catalog(cls, catalog_path) -> "RBSLMInferenceSubstrate":
        """Instantiate the substrate from a descriptor catalog (the SSOT).

        The substrate + inference parameters live under
        ``[fetch.literature_curated.*]`` — ``desc.fetch["literature_curated"]``
        carries a ``substrate`` table and an ``inference.instrument`` table.
        """
        from srmech.amsc import load_descriptor, descriptor_hash

        desc = load_descriptor(catalog_path)
        dh = descriptor_hash(catalog_path)
        lc = desc.fetch["literature_curated"]
        return cls._build(lc, descriptor_hash=dh)

    @classmethod
    def from_params(cls, params: Mapping) -> "RBSLMInferenceSubstrate":
        """Instantiate the substrate from an in-memory params dict (no TOML).

        ``params`` is the same nested dict the catalog would yield under
        ``desc.fetch["literature_curated"]``: a ``substrate`` table (``D``,
        ``token_seed_hex_chars``) and an ``inference.instrument`` table
        (``operating_k``, ``operating_temperature``, ``memory_capacity``,
        ``default_max_tokens``, ``learn_seed``). ``descriptor_hash`` is set to
        the empty string since there is no descriptor file backing it."""
        return cls._build(params, descriptor_hash="")

    # ----------------------------------------------------------------- learn
    def learn(self, token_stream: Sequence[str]) -> "RBSLMInferenceSubstrate":
        """Load corpus knowledge: the bigram candidate structure (full stream) +
        a context→next associative memory of up to memory_capacity (k-window→next)
        pairs (the F154-bounded single memory). Deterministic in learn_seed."""
        stream = list(token_stream)
        self.vocab = sorted(set(stream))
        self.vocab_idx = {w: i for i, w in enumerate(self.vocab)}
        self.vocab_vecs = np.stack([self.ctx.enc(w) for w in self.vocab])

        self.bigram_counts = defaultdict(Counter)
        for a, b in zip(stream, stream[1:]):
            self.bigram_counts[a][b] += 1
        self.next_after = {a: sorted(c.keys()) for a, c in self.bigram_counts.items()}

        k = self.operating_k
        pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
        rng = np.random.default_rng(self.learn_seed)
        n = min(self.memory_capacity, len(pairs_all))
        idx = rng.choice(len(pairs_all), size=n, replace=False)
        pairs = [pairs_all[i] for i in idx]
        assoc = []
        for win, nxt in pairs:
            cs_state = self.ctx.encode_context(list(win))
            assoc.append(hdc.klein4_bind(cs_state, self.ctx.enc(nxt)))
        self.M = self.ctx.bundle_odd(assoc)
        self.n_learned = n
        return self

    # ------------------------------------------------------- distribution
    def next_token_distribution(self, context: Sequence[str],
                                temperature: float | None = None):
        """Return (candidates, probabilities) — the context-conditioned next-token
        distribution over the bigram-legal candidate set (Steps 2-3)."""
        if self.M is None:
            raise RuntimeError("call .learn(stream) before inference")
        T = self.operating_temperature if temperature is None else temperature
        k = self.operating_k
        last = context[-1]
        candidates = self.next_after.get(last, [])
        if not candidates:
            return [], np.array([])
        if len(candidates) == 1:
            return candidates, np.array([1.0])
        cidx = [self.vocab_idx[c] for c in candidates]
        probe = hdc.klein4_bind(self.M, self.ctx.encode_context(list(context[-k:])))
        sims = cs.sim_k4_batch(probe, self.vocab_vecs[cidx])
        return candidates, _softmax(sims, T)

    # ------------------------------------------------------------- infer
    def infer(self, prompt: Sequence[str], max_tokens: int | None = None,
              temperature: float | None = None, seed: int = 0) -> list[str]:
        """Autoregressive generation (Step 4): the substrate conditioned on its own
        running output. Returns the prompt + generated tokens. Deterministic in seed."""
        max_tokens = self.default_max_tokens if max_tokens is None else max_tokens
        gr = np.random.default_rng(seed)
        out = list(prompt)
        for _ in range(max_tokens):
            cands, p = self.next_token_distribution(out, temperature=temperature)
            if len(cands) == 0:
                break
            nxt = cands[int(gr.choice(len(cands), p=p))] if len(cands) > 1 else cands[0]
            out.append(nxt)
        return out

    # --------------------------------------------------------- attestation
    def attestation(self) -> dict:
        """MPR-style attestation block — makes any generated sequence re-derivable."""
        return {
            "method": "config_descriptor",
            "descriptor_hash": self.descriptor_hash,
            "srmech_version": self.srmech_version,
            "abi_version": self.abi_version,
            "has_native": self.has_native,
            "operating_k": self.operating_k,
            "operating_temperature": self.operating_temperature,
            "memory_capacity": self.memory_capacity,
            "n_learned": self.n_learned,
            "vocab_size": len(self.vocab),
            "substrate": "28D Klein-4 chirality; native cascade; bit-exact",
            "provenance": ("Native RBS-LM inference substrate (F166 Steps 1-5). "
                           "Inference = Class A∘M encode + iω₇ position, Class M "
                           "retrieve, temperature sample, iterated. Same corpus + "
                           "catalog + srmech_version + seed → bit-exact output. "
                           "NOT a float-weight distillation."),
        }

    def describe(self) -> str:
        return (f"RBSLMInferenceSubstrate(D={self.ctx.D}, k={self.operating_k}, "
                f"T={self.operating_temperature}, learned={self.n_learned}/"
                f"{self.memory_capacity}, vocab={len(self.vocab)}, "
                f"native={self.has_native}, srmech={self.srmech_version})")
