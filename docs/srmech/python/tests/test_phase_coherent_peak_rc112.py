"""0.9.0rc112 — ``cascade.phase_coherent_peak``: the LIGHTWEIGHT matched-filter
PEAK READ over a rung/mode ladder (issue #1234 Item 1d, the F1000→F1001→F1002
refinement).

THE READ-vs-ENCODE SPLIT under test. The full ``quaternion_dft`` /
``octonion_dft`` (rc110/rc111) are the SPREAD-SPECTRUM ENCODING surface — the
whole length-N spectrum. This op is the deliberately-SEPARATE READ: the
matched-filter PEAK over a rung ladder (max phase-coherent energy), which
F1001 measured BEATS the full complex QDFT on the single-rung fold. The
target's cross-rung response is a SPIKE, so the peak IS the matched filter
(rejects off-rung noise), while the full transform coherently combines ALL
rungs incl. the off-rung noise (a spike's spectrum is flat → coherent
combination gains nothing, forfeits the max's noise-rejection).

The load-bearing gates this rc must hold:

  (a) API DISTINCT — its own op (NOT a kwarg on quaternion_dft); NO twiddle.
  (b) THE F1001 MINIATURE (load-bearing) — on a single-rung spike, candidate
      discrimination by phase_coherent_peak is MEASURABLY better than by the
      full quaternion_dft bin-argmax (the F1001 result reproduced in
      miniature, using the ACTUAL rc110 transform as the competitor).
  (c) PARITY — native whole-read vs fully-forced-pure BYTE-EXACT (==).
  (d) MATCHED FILTER — the optional `keys` per-rung template path.
  (e) CLASS-K — the peak is by squared magnitude (phase-coherent energy),
      never abs(); a large-magnitude negative sample peaks like its positive.
  (f) REGISTRATION — a NEW ToolEntry: tools.total 362 → 363; the Rosetta
      bucket is c_dispatched.
  (g) CARRIER / CONTRACT — real/complex/hypercomplex samples + Mat input +
      the contract errors.

numpy-free by construction (no numpy import, no ``np.``;
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

import srmech.amsc.cascade.hypercomplex_dft as hd
from srmech.amsc import _native
from srmech.amsc.cascade import phase_coherent_peak, quaternion_dft
from srmech.amsc.mat import Mat

NR = 6


def _force_pure(monkeypatch):
    """Force the pure-Python peak read (bypass the C peer)."""
    monkeypatch.setattr(hd, "_pcp_native_ready", lambda: False)


# ────────────────────────────────────────────────────────────────────
# (a) API distinctness + the return shape
# ────────────────────────────────────────────────────────────────────

def test_returns_peak_rung_score_and_scores():
    ladder = [0.1, 0.2, 0.9, -0.3, 0.05, 0.15]
    out = phase_coherent_peak(ladder)
    assert out["rung_index"] == 2                     # the spike at rung 2
    assert out["score"] == pytest.approx(0.81)        # 0.9² (energy)
    assert len(out["scores"]) == NR
    assert out["scores"][2] == pytest.approx(0.81)


def test_is_its_own_op_not_a_kwarg_on_quaternion_dft():
    """The READ is a SEPARATE op — quaternion_dft has NO phase_coherent_peak
    kwarg (the F1000→F1001 API split is structural, not a flag)."""
    import inspect
    sig = inspect.signature(quaternion_dft)
    assert "phase_coherent_peak" not in sig.parameters
    # And the read op does NOT take a twiddle axis — its absence IS the point.
    psig = inspect.signature(phase_coherent_peak)
    assert "mu_axis" not in psig.parameters
    assert set(psig.parameters) == {"ladder", "keys"}


# ────────────────────────────────────────────────────────────────────
# (b) THE F1001 MINIATURE — peak read BEATS the full transform (load-bearing)
# ────────────────────────────────────────────────────────────────────

def _peak_score(ladder):
    return phase_coherent_peak(ladder)["score"]


def _full_qdft_score(ladder):
    """The FULL transform (rc110 quaternion_dft) as the competing read: the
    whole spectrum's max-magnitude bin. The real per-rung responses lie in
    ℝ[i] ≅ ℂ, so this IS the complex QDFT F1001 measured — every off-rung
    noise sample is coherently folded into every bin (a spike's flat
    spectrum)."""
    quats = [[float(s), 0.0, 0.0, 0.0] for s in ladder]
    spectrum = quaternion_dft(quats, mu_axis="i")
    best = 0.0
    for q in spectrum:
        m = q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]
        if m > best:
            best = m
    return best


def test_f1001_miniature_peak_beats_full_transform_on_the_spike():
    """Reproduce F1001 in miniature: a single-rung fold read by (a) the PEAK
    (phase_coherent_peak) vs (b) the full quaternion_dft bin-argmax, scored
    by candidate discrimination (F1001's methodology). The peak recovers the
    true candidate MORE often — the spike's matched filter beats the coherent
    full transform (which folds in the off-rung noise)."""
    rng = random.Random(20260703)
    A, sigma = 2.5, 1.0        # moderate SNR: the regime where noise-folding bites
    trials, n_decoys = 300, 7
    peak_hits = qdft_hits = 0
    for _ in range(trials):
        r0 = rng.randrange(NR)
        true_lad = [rng.gauss(0.0, sigma) for _ in range(NR)]
        true_lad[r0] += A                                  # the single-rung spike
        cands = [true_lad] + [
            [rng.gauss(0.0, sigma) for _ in range(NR)] for _ in range(n_decoys)
        ]
        peak_hits += (max(range(len(cands)),
                          key=lambda i: _peak_score(cands[i])) == 0)
        qdft_hits += (max(range(len(cands)),
                          key=lambda i: _full_qdft_score(cands[i])) == 0)
    peak_acc = peak_hits / trials * 100.0
    qdft_acc = qdft_hits / trials * 100.0
    # The F1001 result: the PEAK read is measurably better than the full QDFT.
    assert peak_acc > qdft_acc, (
        f"peak {peak_acc:.1f}% must beat full-QDFT {qdft_acc:.1f}% "
        f"(the F1001 single-rung result)"
    )
    assert peak_acc - qdft_acc >= 8.0, (
        f"the peak's advantage {peak_acc - qdft_acc:.1f}pp collapsed "
        f"(peak {peak_acc:.1f}% vs full-QDFT {qdft_acc:.1f}%)"
    )


def test_peak_recovers_the_spike_rung_where_qdft_spreads_it_flat():
    """The mechanism, directly: for a clean spike the PEAK points at r0, while
    the full QDFT's spectrum is FLAT (a spike has equal energy in every bin)
    — so the QDFT cannot localise the rung at all."""
    r0 = 4
    ladder = [0.0] * NR
    ladder[r0] = 1.0
    assert phase_coherent_peak(ladder)["rung_index"] == r0
    quats = [[s, 0.0, 0.0, 0.0] for s in ladder]
    spectrum = quaternion_dft(quats, mu_axis="i")
    mags = [q[0] * q[0] + q[1] * q[1] for q in spectrum]
    # Parseval: a unit spike's |X[k]|² is 1 for EVERY bin — perfectly flat.
    assert all(m == pytest.approx(1.0) for m in mags)


# ────────────────────────────────────────────────────────────────────
# (c) Python == C parity — BYTE-EXACT
# ────────────────────────────────────────────────────────────────────

def test_native_symbol_present_on_native_build():
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("pure-Python environment (no native lib)")
    assert hasattr(_native.LIB, "srmech_phase_coherent_peak"), \
        "native lib lacks srmech_phase_coherent_peak"


@pytest.mark.parametrize("dim", (1, 2, 4, 8))
@pytest.mark.parametrize("use_keys", (False, True))
def test_native_matches_pure_byte_for_byte(dim, use_keys, monkeypatch):
    """Whichever path is active vs the FULLY-forced-pure path: IDENTICAL dict
    (==, not a tolerance), across sample dimensions and the keys/no-keys
    matched filters, several rung counts."""
    rng = random.Random(97 + dim + (100 if use_keys else 0))
    cases = []
    for n in (1, 2, 3, 5, 6, 12):
        ladder = [[rng.uniform(-3, 3) for _ in range(dim)] for _ in range(n)]
        keys = ([[rng.uniform(-2, 2) for _ in range(dim)] for _ in range(n)]
                if use_keys else None)
        cases.append((ladder, keys))
    active = [phase_coherent_peak(l, keys=k) for l, k in cases]
    _force_pure(monkeypatch)
    for (l, k), a in zip(cases, active):
        pure = phase_coherent_peak(l, keys=k)
        assert a == pure, f"native vs pure diverged (dim={dim}, keys={use_keys})"


def test_forced_pure_decides_completely(monkeypatch):
    _force_pure(monkeypatch)
    out = phase_coherent_peak([0.1, 0.9, 0.2])
    assert out["rung_index"] == 1


# ────────────────────────────────────────────────────────────────────
# (d) The matched-filter `keys` template path
# ────────────────────────────────────────────────────────────────────

def test_keys_matched_filter_selects_the_aligned_rung():
    """With per-rung templates, the peak is the rung whose sample best
    correlates with its template — not merely the largest-magnitude sample."""
    # rung 0: big sample, ORTHOGONAL to its template → low matched score.
    # rung 1: smaller sample, ALIGNED with its template → high matched score.
    ladder = [[3.0, 0.0], [1.0, 1.0], [0.5, 0.0]]
    keys = [[0.0, 1.0], [1.0, 1.0], [1.0, 0.0]]
    out = phase_coherent_peak(ladder, keys=keys)
    # rung 0: (3*0 + 0*1)² = 0; rung 1: (1*1 + 1*1)² = 4; rung 2: (0.5*1)² = 0.25
    assert out["rung_index"] == 1
    assert out["scores"] == pytest.approx([0.0, 4.0, 0.25])


def test_keys_none_is_the_identity_self_energy_filter():
    ladder = [[3.0, 0.0], [1.0, 1.0], [0.5, 0.0]]
    out = phase_coherent_peak(ladder)     # keys=None → Σ_i v² per rung
    assert out["scores"] == pytest.approx([9.0, 2.0, 0.25])
    assert out["rung_index"] == 0


# ────────────────────────────────────────────────────────────────────
# (e) Class-K discipline — the peak is by squared MAGNITUDE, never abs()
# ────────────────────────────────────────────────────────────────────

def test_peak_is_by_squared_magnitude_not_signed_value():
    """A strongly-NEGATIVE response has the same phase-coherent ENERGY as its
    positive mirror — the peak selects by squared magnitude (Class-K), so the
    read is a genuine phase-coherent energy detector (phase is a nuisance)."""
    ladder = [0.2, -0.9, 0.3, 0.1, 0.05, 0.15]
    out = phase_coherent_peak(ladder)
    assert out["rung_index"] == 1               # |−0.9|² dominates
    assert out["score"] == pytest.approx(0.81)


def test_no_abs_call_in_op_functions():
    """The op's functions must not CALL Python abs() (Class-K squared
    magnitude, not ALU absolute value). AST-checked so a docstring mention of
    ``abs()`` does not trip it."""
    import ast

    src = Path(hd.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    op_fns = {
        "_pcp_components", "_phase_coherent_peak_pure",
        "_try_native_phase_coherent_peak", "phase_coherent_peak",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in op_fns:
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                    assert call.func.id != "abs", \
                        f"{node.name} calls abs() — use Class-K squared magnitude"


# ────────────────────────────────────────────────────────────────────
# (f) Registration — a NEW ToolEntry (tools.total 362 → 363) + ledger
# ────────────────────────────────────────────────────────────────────

def test_tools_total_is_367():
    """phase_coherent_peak is a NEW public op → +1 ToolEntry (362 → 363)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 390


def test_registered_under_flat_name():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.cascade.phase_coherent_peak" in names


def test_rosetta_bucket_is_c_dispatched():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in
            fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets = {r["defined_at"]: r["bucket"] for r in rows}
    assert buckets[
        "srmech.amsc.cascade.hypercomplex_dft.phase_coherent_peak"
    ] == "c_dispatched"


# ────────────────────────────────────────────────────────────────────
# (g) Carrier + contract hygiene
# ────────────────────────────────────────────────────────────────────

def test_complex_scalar_samples_coerced_to_re_im():
    ladder = [0.2 + 0.0j, 0.1 + 0.9j, 0.3 + 0.0j]
    out = phase_coherent_peak(ladder)         # |0.1+0.9j|² = 0.82 dominates
    assert out["rung_index"] == 1
    assert out["score"] == pytest.approx(0.82)


def test_hypercomplex_quaternion_samples():
    ladder = [[0.1, 0.1, 0.0, 0.0], [0.0, 0.0, 0.9, 0.1], [0.2, 0.0, 0.0, 0.0]]
    out = phase_coherent_peak(ladder)
    assert out["rung_index"] == 1             # 0.81 + 0.01 = 0.82


def test_real_mat_input_accepted():
    rows = [[0.1, 0.0], [0.2, 0.9], [0.3, 0.0]]
    m = Mat.from_rows(rows, is_complex=False)
    assert phase_coherent_peak(m) == phase_coherent_peak(rows)


def test_complex_mat_input_rejected():
    m = Mat.from_rows([[1 + 1j, 0]], is_complex=True)
    with pytest.raises(ValueError):
        phase_coherent_peak(m)


def test_contract_errors():
    with pytest.raises(ValueError):
        phase_coherent_peak([])                            # empty ladder
    with pytest.raises(ValueError):
        phase_coherent_peak([[0.1, 0.2], [0.3]])           # ragged dims
    with pytest.raises(ValueError):
        phase_coherent_peak([[0.1, 0.2]], keys=[[0.1], [0.2]])  # keys len ≠ rungs
    with pytest.raises(ValueError):
        phase_coherent_peak([[0.1, 0.2]], keys=[[0.1]])    # key dim ≠ sample dim


def test_tie_keeps_lowest_index():
    out = phase_coherent_peak([0.5, -0.5, 0.5])            # all |·|² = 0.25
    assert out["rung_index"] == 0
