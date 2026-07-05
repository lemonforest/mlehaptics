"""siona.photosynth — the EXCITE → PROPAGATE → HARVEST inference mode (F1059: inference IS photosynthesis).

A query EXCITES the power-source organelle (``dense_laplacian`` = the graph Hamiltonian ``L``, whose
eigenvalues ARE the energy levels); the excitation PROPAGATES through the knowledge structure via the heat
kernel ``e^{-tL}`` (diffusion — the cell force, ``heat_trace``'s kernel); and the answer is HARVESTED at the
"reaction center" — where the propagated energy CONCENTRATES. The chloroplast cascade, whole: photon in
(excite) → exciton walk (propagate, F1058) → reaction center (harvest = read-by-influence, F1057).

Two dials fall out of the physics:
  * the propagation time ``t`` is the working-set RADIUS (F1049): small ``t`` = tight (seed + nearest),
    large ``t`` = broad (the whole community + the bridging organelle services).
  * the harvested energy per kernel IS the E3-GRADED relevance (F1051 richness) — HOW MUCH each contributes,
    not just WHICH (the binary gene_express). Graph-aware: energy flows through RELATIONSHIPS, so the harvest
    pulls in the relationally-coherent working set (the community powered by the organelle), not only the
    directly-similar kernels a plain top-k grounding would return.

srmech-native, numpy-free: Class-M ``klein4_similarity`` (the coupling graph) ∘ Class-L ``dense_laplacian`` +
``symmetric_eigendecompose`` (``L`` = the dynamics generator) ∘ Class-N ``exp_series_truncate`` (the thermal
evolution ``e^{-tλ}`` as an exact rational, collapsed to a scalar only at the ranking/decision boundary).

Scale note: ``symmetric_eigendecompose`` is native up to n≤256; a corpus-scale instrument uses
``fiedler_sparse`` / a Lanczos low-mode basis (the follow-on). The eigenbasis is precomputed ONCE per
instrument; each query is then just a seed + a projection (cheap).
"""
from srmech.amsc import laplacian as _L, hdc as _hdc
from srmech import calculus as _C

__all__ = ["Instrument", "from_session"]


def _two_pi(terms=24):
    """2π via Machin's formula — π/4 = 4·atan(1/5) − atan(1/239) — so the small-argument atan series
    converge fast (an attested constant, not a magic number). This is the BEAT-SEAM period (F1064)."""
    a5, b5 = _C.atan_series_truncate(1, 5, terms)
    a239, b239 = _C.atan_series_truncate(1, 239, terms)
    return 32 * (a5 / b5) - 8 * (a239 / b239)          # 2π = 8·(4·atan(1/5) − atan(1/239))


_TWO_PI = _two_pi()


def _seam(x):
    """Fold an oscillation argument to [−π, π) at the resonance period 2π — the BEAT SEAM (F1064): without
    it the truncated cos/sin Taylor series diverges for |x| past its radius; the fold makes it valid at any x."""
    return x - round(x / _TWO_PI) * _TWO_PI


class Instrument:
    """The knowledge genome's SPECTRAL power structure — the Laplacian eigenbasis of the kernel-similarity
    graph, precomputed once. ``excite_propagate_harvest`` then runs one query as a seed + heat-kernel read."""

    def __init__(self, named_vectors, *, knn=4):
        items = list(named_vectors)
        self.labels = [lab for lab, _ in items]
        self._vecs = [v for _, v in items]
        self.N = len(items)
        self._pos = {lab: i for i, lab in enumerate(self.labels)}
        sim = lambda a, b: _hdc.klein4_similarity(a, b).as_float()   # Class-M coupling
        # kNN edges (sparse; each node's top-knn neighbors, symmetrised)
        und = {i: set() for i in range(self.N)}
        for i in range(self.N):
            for _, j in sorted(((sim(self._vecs[i], self._vecs[j]), j)
                                for j in range(self.N) if j != i), reverse=True)[:knn]:
                und[i].add(j); und[j].add(i)
        edges = sorted({(min(i, j), max(i, j)) for i in und for j in und[i]})
        weights = [sim(self._vecs[a], self._vecs[b]) for a, b in edges]
        # Class-L: L = the graph Hamiltonian; its eigenbasis is the spectral power structure (the organelle)
        self._evals, self._evecs = _L.symmetric_eigendecompose(_L.dense_laplacian(self.N, edges, weights))
        self._lam = [self._evals[k] for k in range(self.N)]

    def _seed(self, query, grounder):
        """EXCITE — ground the utterance to its landing kernel (the antenna where the query is absorbed)."""
        if query in self._pos:
            return self._pos[query]
        g = grounder.ground(query, 1, owner="srmech")
        top = g[0][1].split(".")[-1]
        return self._pos.get(top)

    # thermal/coherent are NOT two families: ONE propagator e^{-zL} with z COMPLEX (the Wick rotation).
    # z = t·(cf + i·sf) on the unit quarter-circle: (cf, sf) = (1, 0) real → THERMAL (decoherent diffusion),
    # (0, 1) imaginary → COHERENT (unitary quantum walk), in between → PARTIAL coherence (a damped walk —
    # the physically real regime; the chloroplast is NOT perfectly coherent). The i is the coherence DIAL
    # (the field↔excitation duality axis, `[[user_stance_imaginary_does_not_mean_unreal]]` — a 90° rotation,
    # a real direction), invisible in the substrate formula where z is simply complex.
    _WICK = {"thermal": (1.0, 0.0), "coherent": (0.0, 1.0)}

    @staticmethod
    def _crank_cossin(one, terms=18):
        """Extract the θ-crank (cos θ, sin θ) from a ``the_one`` instance — its epicycle phase (Class-K) —
        so the propagator's complex-time direction e^{iφ} IS the_one's crank (F1063): φ = θ, and σ = the
        time-direction. This closes the loop: the propagator is not isomorphic to the_one, it is MADE of it."""
        thn, thd = one.theta
        cn, cd = _C.cos_series_truncate(int(thn), int(thd), terms)
        sn, sd = _C.sin_series_truncate(int(thn), int(thd), terms)
        return cn / cd, sn / sd, getattr(one, "sigma", 1)

    def excite_propagate_harvest(self, query, *, grounder=None, t=0.4, top=8, mode="thermal", z=None, crank=None):
        """One EPH read: EXCITE (seed) → PROPAGATE (``e^{-zL}``, ONE complex-time propagator) → HARVEST
        (rank by the Born-rule energy ``|u|²``). The complex time ``z = σ·t·(cos θ + i sin θ)`` is set by
        ``crank`` — a ``the_one(σ, θ)`` instance whose θ-crank IS the coherence direction and σ the time-
        direction (F1063). Or by ``z=(cf, sf)`` directly, or ``mode`` (``"thermal"``=θ=0, ``"coherent"``=θ=π/2).
        The oscillation argument is folded at the beat seam 2π (F1064) so the Taylor pieces stay valid.
        ``harvest = Propagate · excite`` — the op⊗operand cascade, EPH."""
        s = query if isinstance(query, int) else self._seed(query, grounder)
        if s is None:
            return []
        if crank is not None:                                  # the_one IS the crank (F1063)
            cf, sf, sigma = self._crank_cossin(crank)
        else:
            cf, sf = z if z is not None else self._WICK.get(mode, (1.0, 0.0)); sigma = 1
        a, b = sigma * t * cf, sigma * t * sf                  # z = σ·t·(cf + i·sf) = the_one crank × scale
        re = [0.0] * self.N; im = [0.0] * self.N
        for k in range(self.N):
            lam = self._lam[k]                                 # e^{-zλ} = e^{-aλ}·(cos bλ - i sin bλ)
            dn, dd = _C.exp_series_truncate(-int(round(a * lam * 1000)), 1000, 18); dec = dn / dd
            arg = int(round(_seam(b * lam) * 1000))            # BEAT SEAM: fold bλ at 2π before the Taylor pieces
            cn, cd = _C.cos_series_truncate(arg, 1000, 18); c = cn / cd
            sn, sd = _C.sin_series_truncate(arg, 1000, 18); sv = sn / sd
            csk = self._evecs[s, k]
            for i in range(self.N):
                w = csk * self._evecs[i, k]
                re[i] += dec * c * w; im[i] += -dec * sv * w
        u = [re[i] * re[i] + im[i] * im[i] for i in range(self.N)]   # Born-rule harvest |u|² (energy)
        order = sorted(range(self.N), key=lambda i: -u[i])
        return [(self.labels[i], u[i]) for i in order[:top] if u[i] > 0]


def from_session(session, *, limit=200, knn=4):
    """Build an :class:`Instrument` from a live siona Session's grounding index (its named D-dim kernels)."""
    idx = session.g._idx[:limit]
    return Instrument([(n.split(".")[-1], v) for n, v in idx], knn=knn)
