"""srmech.rbs_lm.inference — the native, bit-exact, catalog-instantiable RBS-LM
inference substrate (F166 Step 5: the fully-realized artifact).

Ported from the research subtree's ``_rbs_lm_inference`` (UPSTREAM_NOTES §9).
This is the F166 goal made an object: an inference substrate built UP from the
28D Klein-4 coordinate, NOT distilled DOWN from float weights. It composes the
four stones of the walk into one clean API, parameterized by the descriptor
catalog (``from_catalog``) OR an in-memory params dict (``from_params``):

  Step 1  ContextSubstrate.encode_context  — last-k tokens → ONE Klein-4 state
  Step 2  next_token_distribution          — Class M retrieve over the bounded atom set
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

import random
from dataclasses import dataclass, field
from typing import List, Mapping, Sequence

from srmech.amsc import hdc, rational
from srmech.amsc.hv import HV

from . import substrate as cs


def _softmax(x, t: float) -> List[float]:
    """Temperature softmax over a small candidate list — numpy-free. The
    per-element ``exp`` is the Class-N ``rational.exp`` cascade (the same
    substrate-native transcendental the DSP carrier-flips use; NOT the
    numpy-carrier ``elementwise_transcendental``), so the op runs numpy-absent.
    The ``z - max(z)`` shift is the standard overflow-safe form."""
    z = [xi / t for xi in x]
    m = max(z)
    e = [rational.exp(zi - m) for zi in z]
    s = sum(e)
    return [ei / s for ei in e]


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
    vocab_vecs: "list[HV] | None" = None
    vocab_idx: dict[str, int] = field(default_factory=dict)
    M: "HV | None" = None
    n_learned: int = 0

    # ----------------------------------------------------------------- build
    @classmethod
    def _build(cls, params: Mapping, *, descriptor_hash: str) -> "RBSLMInferenceSubstrate":
        """Shared construction from a ``literature_curated``-shaped params dict.

        ``params`` carries the same nested structure the descriptor catalog
        yields under ``desc.fetch["literature_curated"]``: a ``substrate`` table
        (D / token_seed_hex_chars / optional ``enc_mode``) and an
        ``inference.instrument`` table (operating_k / operating_temperature /
        memory_capacity / default_max_tokens / learn_seed).

        ``substrate.enc_mode`` selects the word encoder: ``"byteglyph"``
        (default — the C1 byte/glyph LM object, F916) or ``"wordhash"`` (the
        prior whole-word sha256 atom; pin it to reproduce pre-rc17 numerics)."""
        from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
        from srmech import __version__ as SRMECH_VERSION

        sub = params["substrate"]
        inst = params["inference"]["instrument"]
        ctx = cs.ContextSubstrate(D=int(sub["D"]),
                                  hex_chars=int(sub["token_seed_hex_chars"]),
                                  enc_mode=str(sub.get("enc_mode", "byteglyph")))
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
        """Load corpus knowledge: the bounded per-tome atom set (``vocab``) + a
        context→next associative memory of up to memory_capacity (k-window→next)
        pairs (the F154-bounded single memory). Deterministic in learn_seed.

        §57: NO bigram-count co-occurrence table is built — the candidate set is
        the bounded atom set itself, scored at inference time by the Class-M
        resonator over ``M``. The hand-rolled ``Counter()`` bigram tally the
        CLAUDE.md STOP-list flags as a statistical-LM contaminant is retired."""
        stream = list(token_stream)
        self.vocab = sorted(set(stream))
        self.vocab_idx = {w: i for i, w in enumerate(self.vocab)}
        self.vocab_vecs = [self.ctx.enc(w) for w in self.vocab]

        k = self.operating_k
        pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
        # numpy-free deterministic memory subsample (stdlib RNG; the framework-
        # native incidental source — re-derivable in learn_seed, no numpy).
        rng = random.Random(self.learn_seed)
        n = min(self.memory_capacity, len(pairs_all))
        idx = rng.sample(range(len(pairs_all)), n)
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
        distribution (Steps 2-3).

        §57: the candidate set is the FULL bounded per-tome atom set
        (``self.vocab``), scored by the Class-M resonator — probe the bundle
        ``M`` with the encoded context, then fractional-agreement similarity over
        every atom vector. There is NO bigram-count gate (the hand-rolled
        ``Counter()`` co-occurrence the CLAUDE.md STOP-list forbids): grounding
        comes from ``M``, not a statistical-LM next-token table. §56: ``T <= 0``
        is greedy (argmax → one-hot), no temperature softmax."""
        if self.M is None:
            raise RuntimeError("call .learn(stream) before inference")
        if not self.vocab:
            return [], []
        T = self.operating_temperature if temperature is None else temperature
        k = self.operating_k
        candidates = self.vocab
        probe = hdc.klein4_bind(self.M, self.ctx.encode_context(list(context[-k:])))
        sims = cs.sim_k4_batch(probe, self.vocab_vecs)
        if T <= 0.0:                                   # §56 greedy: argmax → one-hot
            best = 0
            for i in range(1, len(sims)):
                if sims[i] > sims[best]:                # Class K pin-slot compare
                    best = i
            p = [0.0] * len(candidates)
            p[best] = 1.0
            return candidates, p
        return candidates, _softmax(sims, T)

    # ------------------------------------------------------------- infer
    def infer(self, prompt: Sequence[str], max_tokens: int | None = None,
              temperature: float | None = None, seed: int = 0) -> list[str]:
        """Autoregressive generation (Step 4): the substrate conditioned on its own
        running output. Returns the prompt + generated tokens. Deterministic in seed."""
        max_tokens = self.default_max_tokens if max_tokens is None else max_tokens
        gr = random.Random(seed)  # numpy-free deterministic sampler (in seed)
        out = list(prompt)
        for _ in range(max_tokens):
            cands, p = self.next_token_distribution(out, temperature=temperature)
            if len(cands) == 0:
                break
            if len(cands) > 1:
                nxt = cands[gr.choices(range(len(cands)), weights=p, k=1)[0]]
            else:
                nxt = cands[0]
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
