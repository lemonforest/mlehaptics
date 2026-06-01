"""unflatten_prototype.py — F281 sec-B: generalized un-flatten cascade prototype.

Implements:
  unflatten(chart) ->
    step 1: autocorrelation = IFFT(|FFT(chart)|^2)   [Wiener-Khinchin; recovers recurring-Δ fiber]
    step 2: difference-graph on autocorr peaks ->
              dense_laplacian -> jacobi_eigvals        [fiber's spectral signature; srmech Class L]
    step 3: detect vs validate (F266) — autocorr DETECTS all candidate Δ;
              a conservation rule VALIDATES which are real (codeword edges)

Demonstrated on:
  Demo A — F280 ethanol mass-spec flat chart: peaks 46, 45, 31, 29, 27
  Demo B — Fibonacci-spacing chart (benign 1-D synthetic); peaks at Fibonacci positions

SCOPE: framework-reading; benign known inputs; no unknown-ID / synthesis / clinical.
CLASS-K CLEAN: |F|^2 = F * conj(F) (no abs()); inner products via dot (no abs()).
No-lineage. srmech Class L (dense_laplacian / jacobi_eigvals) for spectral steps.
FFT = numpy signal-processing (not a bypassed srmech primitive; identical to F280).

BUG-TEST: consistency checks vs math/oracle are embedded inline.
"""
import sys
import numpy as np

sys.path.insert(0, "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/rbs_lm_research")

import srmech.amsc.laplacian as SL
import loop_bind_moufang as oracle  # the oracle (parity check surface)
import srmech.amsc.hdc as SH        # native hdc — loop_bind parity check


# ---------------------------------------------------------------------------
# Consistency check 1: native loop_bind == oracle on 8x8 basis (required)
# ---------------------------------------------------------------------------
def _check_loop_bind_parity():
    ok = True
    for i in range(8):
        for j in range(8):
            ei, ej = oracle.e(i), oracle.e(j)
            native = SH.loop_bind(ei, ej)
            ref    = oracle.loop_bind(ei, ej)
            if not np.allclose(native, ref, atol=1e-12):
                ok = False
                print(f"  [ANOMALY] loop_bind e{i}*e{j}: native={native}  oracle={ref}")
    return ok


# ---------------------------------------------------------------------------
# Core: unflatten cascade
# ---------------------------------------------------------------------------

def _autocorr(chart: np.ndarray) -> np.ndarray:
    """Step 1 — Wiener-Khinchin autocorrelation.

    autocorr = IFFT(|FFT(chart)|^2) = IFFT(F * conj(F))
    Class-K clean: |F|^2 via F * conj(F), no abs().
    """
    F = np.fft.fft(chart)
    power = F * np.conj(F)          # Class-K: conj, not abs()
    return np.real(np.fft.ifft(power))


def _peak_lags(autocorr: np.ndarray, threshold: float = 0.5, max_lag: int | None = None) -> list[int]:
    """Extract positive lags where autocorr exceeds threshold."""
    n = len(autocorr)
    if max_lag is None:
        max_lag = n // 2
    return [d for d in range(1, max_lag + 1) if autocorr[d] > threshold]


def _difference_graph_laplacian(peak_positions: list[int], peak_lags: list[int]):
    """Step 2 — build difference graph on detected Δ-lags.

    Nodes = peak positions; edges = (i, j) if |pos_i - pos_j| is a detected lag.
    Uses dense_laplacian (srmech Class L).

    Returns (laplacian_matrix, node_list, edges).
    """
    n = len(peak_positions)
    lag_set = set(peak_lags)
    edges = []
    for a_idx in range(n):
        for b_idx in range(a_idx + 1, n):
            delta = abs(peak_positions[b_idx] - peak_positions[a_idx])
            if delta in lag_set:
                edges.append((a_idx, b_idx))

    if n == 0:
        return np.zeros((0, 0)), peak_positions, edges

    lap = SL.dense_laplacian(n, edges)
    return lap, peak_positions, edges


def _fiedler(eigvals: np.ndarray) -> float:
    """Fiedler value = second-smallest eigenvalue (first nonzero for connected graph)."""
    sorted_ev = np.sort(eigvals)
    nonzero = sorted_ev[sorted_ev > 1e-10]
    return float(nonzero[0]) if len(nonzero) > 0 else 0.0


def unflatten(chart: np.ndarray,
              conservation_rule: set[int] | None = None,
              threshold: float = 0.5,
              max_lag: int | None = None,
              label: str = "") -> dict:
    """The generalized un-flatten cascade (F281 sec-B).

    Parameters
    ----------
    chart              : 1-D intensity array (sparse peaks into a zero array)
    conservation_rule  : optional set of valid Δ lags (validation step; None = no filter)
    threshold          : autocorr peak threshold (default 0.5)
    max_lag            : max lag to scan (default len(chart)//2)
    label              : display label

    Returns
    -------
    dict with keys:
      autocorr          : full autocorrelation array
      detected_lags     : all candidate Δ's (step 1 / detect)
      validated_lags    : subset passing conservation rule (step 2/3 / validate)
      peak_positions    : positions of nonzero peaks in the input chart
      laplacian         : (n x n) difference-graph Laplacian
      eigvals           : jacobi_eigvals of the Laplacian
      fiedler           : Fiedler value of the difference-graph
      edges             : list of (node_idx, node_idx) edges in the difference graph
    """
    peak_positions = [int(i) for i in np.where(chart > 0)[0]]
    autocorr = _autocorr(chart)
    detected_lags = _peak_lags(autocorr, threshold=threshold, max_lag=max_lag)

    if conservation_rule is not None:
        validated_lags = [d for d in detected_lags if d in conservation_rule]
    else:
        validated_lags = detected_lags[:]

    lap, _, edges = _difference_graph_laplacian(peak_positions, validated_lags)

    if lap.shape[0] > 0:
        eigvals = SL.jacobi_eigvals(lap)
    else:
        eigvals = np.array([])

    fiedler = _fiedler(eigvals)

    return {
        "label":           label,
        "autocorr":        autocorr,
        "detected_lags":   detected_lags,
        "validated_lags":  validated_lags,
        "peak_positions":  peak_positions,
        "laplacian":       lap,
        "eigvals":         eigvals,
        "fiedler":         fiedler,
        "edges":           edges,
    }


# ---------------------------------------------------------------------------
# Consistency check 2: dense_laplacian sum == 2|E| == trace(L)
# ---------------------------------------------------------------------------
def _check_laplacian_sum(lap: np.ndarray, n_edges: int) -> bool:
    """Row sums == 0; trace(L) == 2|E| (combinatorial Laplacian identity)."""
    row_sum_ok = np.allclose(lap.sum(axis=1), 0.0, atol=1e-10)
    trace_ok   = np.isclose(np.trace(lap), 2 * n_edges, atol=1e-10)
    return bool(row_sum_ok and trace_ok)


# ---------------------------------------------------------------------------
# Demo A — ethanol mass-spec (F280)
# ---------------------------------------------------------------------------
ETHANOL_NEUTRALS = {1: "H", 2: "H2", 4: "(2H2)", 14: "CH2", 15: "CH3",
                    16: "O/CH4", 17: "OH", 18: "H2O", 28: "CO", 29: "CHO"}

# Conservation rule from F278/F279: ethanol neutral-loss codeword edges
# (the validated differences: 1=H, 2=H2, 17=OH, 45=M-1, 15=CH3, 29=CHO, 16=O, 18=H2O)
ETHANOL_CONSERVATION = {1, 2, 14, 15, 16, 17, 18, 29}   # attested-B (neutral-loss table)


def run_demo_a():
    print("=" * 70)
    print("DEMO A — ethanol mass-spec flat chart (F280 peaks: 46,45,31,29,27)")
    print("=" * 70)
    mz_max = 64
    chart = np.zeros(mz_max)
    for p in [46, 45, 31, 29, 27]:
        chart[p] = 1.0

    result = unflatten(chart,
                       conservation_rule=ETHANOL_CONSERVATION,
                       threshold=0.5,
                       max_lag=30,
                       label="ethanol_ms")

    print(f"\nStep 1 — Wiener-Khinchin autocorr: autocorr[0] = {result['autocorr'][0]:.0f} (= {len(result['peak_positions'])} peaks)")
    print(f"  detected Δ-lags (all recurring differences): {result['detected_lags']}")
    lag_decoded = [(d, ETHANOL_NEUTRALS.get(d, "?")) for d in result['detected_lags']]
    print(f"  decoded:  {lag_decoded}")

    print(f"\nStep 2/3 — validate vs conservation rule:")
    print(f"  validated_lags (codeword edges): {result['validated_lags']}")
    val_decoded = [(d, ETHANOL_NEUTRALS.get(d, "?")) for d in result['validated_lags']]
    print(f"  decoded: {val_decoded}")

    print(f"\nStep 2 — difference-graph on validated peaks:")
    print(f"  nodes (peak m/z): {result['peak_positions']}")
    print(f"  edges: {result['edges']}")
    print(f"  Laplacian shape: {result['laplacian'].shape}")
    print(f"  eigenvalues: {np.round(result['eigvals'], 4)}")
    print(f"  Fiedler value: {result['fiedler']:.4f}")
    if result['fiedler'] > 0:
        print(f"  -> graph is connected (Fiedler > 0); fiber is a single spanning component")
    else:
        print(f"  -> graph is disconnected or trivial (Fiedler = 0)")

    # Consistency check: Laplacian sum == 2|E|
    lap_ok = _check_laplacian_sum(result['laplacian'], len(result['edges']))
    print(f"\n  [CONSISTENCY] Laplacian: row-sum==0 AND trace==2|E|: {'PASS' if lap_ok else 'ANOMALY'}")
    if not lap_ok:
        print(f"    trace={np.trace(result['laplacian']):.4f}  expected 2*{len(result['edges'])}={2*len(result['edges'])}")

    return result


# ---------------------------------------------------------------------------
# Demo B — Fibonacci-spacing synthetic chart
# ---------------------------------------------------------------------------
# Fibonacci positions: 1, 2, 3, 5, 8, 13, 21, 34 (first 8; attested-B = integer sequence)
# The Fibonacci recurrence: F(n) = F(n-1) + F(n-2) => valid conservation rule = consecutive differences
FIBONACCI_PEAKS = [1, 2, 3, 5, 8, 13, 21, 34]
# Fibonacci differences between consecutive pairs: 1, 1, 2, 3, 5, 8, 13
FIBONACCI_CONSERVATION = {1, 2, 3, 5, 8, 13}   # Fibonacci numbers themselves (attested-to-structure: the recurrence)


def run_demo_b():
    print()
    print("=" * 70)
    print("DEMO B — Fibonacci-spacing synthetic chart (peaks at F-numbers)")
    print("=" * 70)
    chart_size = 40
    chart = np.zeros(chart_size)
    for p in FIBONACCI_PEAKS:
        chart[p] = 1.0

    result = unflatten(chart,
                       conservation_rule=FIBONACCI_CONSERVATION,
                       threshold=0.5,
                       max_lag=20,
                       label="fibonacci_synth")

    print(f"\nStep 1 — Wiener-Khinchin autocorr: autocorr[0] = {result['autocorr'][0]:.0f} (= {len(result['peak_positions'])} peaks)")
    print(f"  detected Δ-lags (all recurring differences): {result['detected_lags']}")

    print(f"\nStep 2/3 — validate vs Fibonacci recurrence conservation:")
    print(f"  validated_lags (Fibonacci codeword edges): {result['validated_lags']}")
    print(f"  (non-Fibonacci lags = projection artifact; excluded by conservation rule)")

    print(f"\nStep 2 — difference-graph on validated peaks:")
    print(f"  nodes (peak positions): {result['peak_positions']}")
    print(f"  edges: {result['edges']}")
    print(f"  Laplacian shape: {result['laplacian'].shape}")
    print(f"  eigenvalues: {np.round(result['eigvals'], 4)}")
    print(f"  Fiedler value: {result['fiedler']:.4f}")
    if result['fiedler'] > 0:
        print(f"  -> graph is connected (Fiedler > 0); all peaks in one fiber component")
    else:
        print(f"  -> graph is disconnected or trivial (Fiedler = 0)")
        print(f"  NOTE: if Fiedler=0 the Fibonacci peaks form disjoint groups under consecutive-Δ only")

    # Consistency check: Laplacian sum == 2|E|
    lap_ok = _check_laplacian_sum(result['laplacian'], len(result['edges']))
    print(f"\n  [CONSISTENCY] Laplacian: row-sum==0 AND trace==2|E|: {'PASS' if lap_ok else 'ANOMALY'}")
    if not lap_ok:
        print(f"    trace={np.trace(result['laplacian']):.4f}  expected 2*{len(result['edges'])}={2*len(result['edges'])}")

    return result


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def print_summary(res_a, res_b):
    print()
    print("=" * 70)
    print("SUMMARY — unflatten cascade prototype (F281 sec-B)")
    print("=" * 70)
    print()
    print("Demo A (ethanol mass-spec):")
    print(f"  detected fiber lags:    {res_a['detected_lags']}")
    print(f"  validated codeword lags:{res_a['validated_lags']}")
    print(f"  difference-graph edges: {res_a['edges']}")
    print(f"  Fiedler:                {res_a['fiedler']:.4f}")
    ev_str = " ".join(f"{v:.3f}" for v in res_a['eigvals'])
    print(f"  eigenspectrum:          [{ev_str}]")
    print()
    print("Demo B (Fibonacci synthetic):")
    print(f"  detected fiber lags:    {res_b['detected_lags']}")
    print(f"  validated codeword lags:{res_b['validated_lags']}")
    print(f"  difference-graph edges: {res_b['edges']}")
    print(f"  Fiedler:                {res_b['fiedler']:.4f}")
    ev_str = " ".join(f"{v:.3f}" for v in res_b['eigvals'])
    print(f"  eigenspectrum:          [{ev_str}]")
    print()
    print("Cascade structure confirmed:")
    print("  step 1 (Wiener-Khinchin autocorr) -> detects all recurring Δ")
    print("  step 2 (dense_laplacian + jacobi_eigvals) -> spectral signature of fiber")
    print("  step 3 (conservation filter) -> validates codeword edges vs projection artifact")
    print("  Fiedler > 0 => connected fiber (all detected real peaks span one component)")


if __name__ == "__main__":
    print("srmech unflatten cascade prototype — F281 sec-B")
    print(f"srmech version: {__import__('srmech').__version__}")
    print()

    # --- Parity oracle check ---
    print("[CONSISTENCY CHECK 1] native loop_bind == oracle (8x8 basis) ...")
    lb_ok = _check_loop_bind_parity()
    print(f"  loop_bind parity: {'PASS' if lb_ok else 'ANOMALY'}")
    print()

    res_a = run_demo_a()
    res_b = run_demo_b()
    print_summary(res_a, res_b)
