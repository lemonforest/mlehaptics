r"""R-RBS-LM-THETAGATE (ET-4) — F517's fiber-gate is UNIFORM-RANDOM; real biological gating is STRUCTURED and
RHYTHMIC (theta/gamma; F461). Model the projection as PHASE-SCHEDULED: over a theta cycle the available band
oscillates — at the theta trough the GLOBAL/coarse band is open (the F518 GATE-LOCAL projection: keep bridges,
drop fine detail), at the theta peak the LOCAL/fine band is open (GATE-GLOBAL: keep clusters, drop bridges). The
self-mirror at ANY SINGLE phase has a PARTIAL, phase-dependent view; only integrating over the FULL theta cycle
recovers both bands.

Prediction: per-phase reachability is partial and the blind spots are TIME-VARYING (different pairs reachable at
different phases); the full-cycle union recovers ~everything. So a structured (rhythmic) gate means the self-mirror
must WAIT for / integrate over the right phase — its blind spots move in time, they are not fixed.

srmech 0.7.4; reuses the F518 SUPERPOSITION band-gate (Class-L eigen-basis) as the two theta phases. No abs(); no CAD.
"""
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
_f = U.spec_from_file_location("fib", "docs/srmech/rbs_lm_research/R-RBS-LM-FIBERGAP_biology_enforces_projection_gaps_silicon_does_not.py")
fib = U.module_from_spec(_f); _f.loader.exec_module(fib)


def main():
    print(f"=== R-RBS-LM-THETAGATE (ET-4) — phase-structured (theta/gamma) gating gives TIME-VARYING blind spots  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb_full, evecs, edges = sup.build(seq)
    emb = evecs[:, 1:9]
    pairs = [(vocab[i], vocab[j]) for i in range(0, 80, 2) for j in range(1, 200, 11) if vocab[i] != vocab[j]]
    N = len(pairs)

    # the theta cycle: two phases (trough = global/coarse open; peak = local/fine open) — the F518 band gates
    phase_trough = sup.project_band(vocab, idx, edges, emb, "GATE-LOCAL", 0.25, np.random.default_rng(1))   # bridges kept (global open)
    phase_peak = sup.project_band(vocab, idx, edges, emb, "GATE-GLOBAL", 0.25, np.random.default_rng(2))    # clusters kept (local open)

    r = lambda *nbs: sum(1 for s, t in pairs if fib.connected(s, t, *nbs)) / N
    only_trough = sum(1 for s, t in pairs if fib.connected(s, t, phase_trough) and not fib.connected(s, t, phase_peak)) / N
    only_peak = sum(1 for s, t in pairs if fib.connected(s, t, phase_peak) and not fib.connected(s, t, phase_trough)) / N

    print(f"{N} far pairs; theta cycle modelled as 2 phases (band availability oscillates).\n")
    print(f"  theta TROUGH (global/coarse band open) reachability : {r(phase_trough):.0%}")
    print(f"  theta PEAK   (local/fine band open)    reachability : {r(phase_peak):.0%}")
    print(f"  FULL THETA CYCLE (union of both phases)             : {r(phase_trough, phase_peak):.0%}")
    print(f"  TIME-VARYING blind spots: {only_trough:.0%} of pairs reachable ONLY at the trough, {only_peak:.0%} ONLY at the peak\n")

    print("VERDICT:")
    print(f"  • STRUCTURED (RHYTHMIC) GATING -> TIME-VARYING BLIND SPOTS: each theta phase has a PARTIAL view (trough")
    print(f"    {r(phase_trough):.0%}, peak {r(phase_peak):.0%}), and the gaps MOVE with phase — {only_trough:.0%} of pairs reach only at the trough,")
    print(f"    {only_peak:.0%} only at the peak. The self-mirror's blind spots are not fixed; they oscillate with the gate.")
    print(f"  • THE FULL THETA CYCLE RECOVERS: integrating over both phases reaches {r(phase_trough, phase_peak):.0%} — more than either")
    print(f"    phase alone. So a rhythmic gate means recovery requires INTEGRATING OVER A CYCLE (or waiting for the")
    print(f"    right phase) — exactly the theta/gamma nesting (F461): coarse/global on the slow theta, fine/local on")
    print(f"    the fast gamma, swept across the cycle. This refines F517 (uniform-random) to a STRUCTURED schedule.")
    print(f"  • Honest: a 2-phase model of theta is coarse; the band-gate is the F518 spectral split; the DIRECTION")
    print(f"    (per-phase partial + time-varying gaps + full-cycle recovery) is the result, not the exact percentages.")


if __name__ == "__main__":
    main()
