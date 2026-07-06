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

    def excite_propagate_harvest_2axis(self, query, *, grounder=None, t=0.4, top=8, crank=None, z=None, mode="coherent"):
        """The TWO-AXIS harvest (F1066/F1069): carry the winding ``w`` WHOLE instead of folding it away, and
        return BOTH addressable objects of the beat seam. The oscillation argument ``bλ`` DIVMODs at the seam
        into ``(w = round(bλ/2π), θ = bλ − w·2π)`` — ``w`` (the metacycle winding) is KEPT, not collapsed:

          * ``"phase"`` — the FAST / epicycle axis: the coherent total ``|Σ_w u^w|²``, the graded working set
            (WHERE the energy lands; identical to :meth:`excite_propagate_harvest`).
          * ``"winding"`` — the SLOW / metacycle axis: the answer STRATIFIED BY SCALE — each winding level
            ``w`` = how many 2π turns a mode made = its tower / octave rung (F1069's chirality tower). Low ``w``
            = coarse / global modes; higher ``w`` = finer / local. The scale decomposition the fold discarded.

        Returns ``{"phase": [(label, energy)], "winding": [(w, [(label, energy)]), …]}``."""
        s = query if isinstance(query, int) else self._seed(query, grounder)
        if s is None:
            return {"phase": [], "winding": []}
        if crank is not None:
            cf, sf, sigma = self._crank_cossin(crank)
        else:
            cf, sf = z if z is not None else self._WICK.get(mode, (0.0, 1.0)); sigma = 1
        a, b = sigma * t * cf, sigma * t * sf
        wre = {}; wim = {}                                     # winding level w -> per-node re/im (KEPT, not folded)
        for k in range(self.N):
            lam = self._lam[k]
            full = b * lam
            w = int(round(full / _TWO_PI))                     # the WINDING = divmod's quotient (kept whole, F1069)
            arg = int(round((full - w * _TWO_PI) * 1000))      # the folded phase = divmod's remainder (the seam)
            dn, dd = _C.exp_series_truncate(-int(round(a * lam * 1000)), 1000, 18); dec = dn / dd
            cn, cd = _C.cos_series_truncate(arg, 1000, 18); c = cn / cd
            sn, sd = _C.sin_series_truncate(arg, 1000, 18); sv = sn / sd
            csk = self._evecs[s, k]
            if w not in wre:
                wre[w] = [0.0] * self.N; wim[w] = [0.0] * self.N
            rw = wre[w]; iw = wim[w]
            for i in range(self.N):
                g = csk * self._evecs[i, k]
                rw[i] += dec * c * g; iw[i] += -dec * sv * g
        tot = [0.0] * self.N                                   # FAST axis: coherent total |Σ_w u^w|² (the epicycle)
        for i in range(self.N):
            re = sum(wre[w][i] for w in wre); im = sum(wim[w][i] for w in wim)
            tot[i] = re * re + im * im
        order = sorted(range(self.N), key=lambda i: -tot[i])
        phase = [(self.labels[i], tot[i]) for i in order[:top] if tot[i] > 0]
        winding = []                                           # SLOW axis: per scale-level w, the partial harvest
        for w in sorted(wre):
            uw = [wre[w][i] * wre[w][i] + wim[w][i] * wim[w][i] for i in range(self.N)]
            ow = sorted(range(self.N), key=lambda i: -uw[i])
            rows = [(self.labels[i], uw[i]) for i in ow[:top] if uw[i] > 1e-9]
            if rows:
                winding.append((w, rows))
        return {"phase": phase, "winding": winding}

    @staticmethod
    def _archetype(n):
        """The verbosity ARCHETYPE that falls out of the emitted-path length (F1075) — none wrong by default,
        context selects which to prefer: terse (an answer) → concise → balanced → descriptive → expansive."""
        return ("terse" if n <= 1 else "concise" if n <= 3 else "balanced" if n <= 6
                else "descriptive" if n <= 10 else "expansive")

    def path_emit(self, query, *, grounder=None, t=20.0, coherence=1.0, max_steps=14, level_floor=0.03, breadth=None):
        """Emit a coarse→fine PATH by walking the winding tower (F1074). ``coherence`` ∈ [0, 1] is the ONE KNOB:
        it opens the tower (depth) AND sets ``breadth`` (per-level detail, ``1 + round(2·coherence)`` = 1 terse
        → 3 expansive) unless ``breadth`` is given. At each scale level w (ascending = coarse→fine) take the
        top-``breadth`` nodes, dedup, threshold by ``level_floor``. The verbosity ARCHETYPE (terse / concise /
        balanced / descriptive / expansive) FALLS OUT of the configuration — none is wrong by default; context
        selects which to prefer (F1075). knob 0 = thermal (one floor → a terse ANSWER); knob 1 = coherent (full
        tower, wide → an expansive PATH). Returns
        ``{"path": [labels coarse→fine], "archetype": name, "coherence": c, "levels_open": k, "breadth": b}``."""
        if breadth is None:
            breadth = 1 + int(round(2.0 * coherence))          # coherence drives per-level detail: 1 → 3
        phi = coherence * (_TWO_PI / 4.0)                      # coherence ∈ [0,1] → the Wick angle φ ∈ [0, π/2]
        cn, cd = _C.cos_series_truncate(int(round(phi * 1000)), 1000, 18); cf = cn / cd
        sn, sd = _C.sin_series_truncate(int(round(phi * 1000)), 1000, 18); sf = sn / sd
        two = self.excite_propagate_harvest_2axis(query, grounder=grounder, t=t, top=max(1, breadth), z=(cf, sf))
        levels = two["winding"]                                # [(w, [(label, energy)])], w ascending = coarse→fine
        if not levels:
            return {"path": [], "archetype": "terse", "coherence": coherence, "levels_open": 0, "breadth": breadth}
        maxe = max(rows[0][1] for _, rows in levels)
        seq = []; seen = set()
        for w, rows in levels:                                 # coarse → fine
            for lab, e in rows[:breadth]:
                if e < level_floor * maxe or lab in seen:
                    continue
                seen.add(lab); seq.append(lab)
                if len(seq) >= max_steps:
                    break
            if len(seq) >= max_steps:
                break
        return {"path": seq, "archetype": self._archetype(len(seq)),
                "coherence": coherence, "levels_open": len(levels), "breadth": breadth}


def from_session(session, *, limit=200, knn=4):
    """Build an :class:`Instrument` from a live siona Session's grounding index (its named D-dim kernels)."""
    idx = session.g._idx[:limit]
    return Instrument([(n.split(".")[-1], v) for n, v in idx], knn=knn)
