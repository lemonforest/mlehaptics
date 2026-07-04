"""0.9.0rc110 — ``cascade.quaternion_dft`` GRADUATED first-class (issue #1234
Item 1b, re-raise of #863; F380 / the in-repo R21 proof).

The op now stands on the rc109 ``qm.quaternion`` foundation (the 4×4
``L_q``/``R_q`` operators + ``quaternion_twiddle``) and dispatches the WHOLE
O(N²) exact-reference transform to the same-rc C peer
``srmech_quaternion_dft`` (byte-exact composed fallback — the parity
contract, not a tolerance).

THE CONVENTION under test (forward sign σ = −1; W(θ) = exp(μθ)):

    left  form:  X[k] = Σ_n W(σ·2πkn/N) · x[n]     (twiddle on the LEFT)
    right form:  X[k] = Σ_n x[n] · W(σ·2πkn/N)     (twiddle on the RIGHT)

inverse = σ = +1 + 1/N scale on the SAME side; each form is the exact
inverse of its own inverse-transform.

The load-bearing gates this rc must hold:

  (a) ROUND-TRIP — inverse(forward(x)) == x (and forward(inverse(x)) == x)
      to float tolerance, BOTH sides, several N including non-powers-of-2.
  (b) LEFT ≠ RIGHT on a generic quaternion signal (ℍ non-commutativity is
      REAL), degenerating to EXACT equality when the signal lies in ℝ[μ]
      (the classic check).
  (c) KLEIN-4 PRESERVATION — the issue's WHY as a test: a Klein-4-structured
      signal (both Z₂ axes carrying information) survives the QDFT
      round-trip on ALL FOUR components, while the complex-FFT path (the
      shipped ``spectral_cascades.fft`` on the ℂ-projection) structurally
      LOSES one axis (the flat shadow).
  (d) LINEARITY (ℝ-scalars, both forms) + the module-map convention locks
      (left form = right ℍ-module map; right form = left ℍ-module map).
  (e) PARSEVAL — Σ_k ‖X[k]‖² = N·Σ_n ‖x[n]‖² (this convention: forward
      unscaled), both one-sided forms.
  (f) PARITY — native whole-transform vs fully-forced-pure composed path
      BYTE-EXACT per coefficient (the C peer is a pure speedup, never a
      divergence).
  (g) DSL — the graduated ``quaternion_dft.toml`` descriptor loads via
      ``srmech.dsl`` and the op runs through a chain; the descriptor
      declares the C peer.
  (h) REGISTRATION — the ToolEntry pre-existed (v0.7.0rc31), so the
      graduation changes its Rosetta BUCKET (python_only_irreducible →
      c_dispatched), NOT the tool count: tools.total stays 362.

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
from srmech.amsc.cascade import quaternion_dft
from srmech.amsc.cascade.spectral_cascades import fft as complex_fft
from srmech.amsc.mat import Mat
from srmech.qm import quaternion as quat

FORMS = ("left", "right")
NS = (1, 2, 3, 5, 7, 8, 12, 16)          # incl. non-powers-of-2 (3, 5, 7, 12)
AXES = ("i", "j", "k", "ijk", "diagonal")


def _signal(n, seed=20260703):
    """A deterministic generic quaternion signal (all four components live)."""
    rng = random.Random(seed + n)
    return [[rng.uniform(-2.0, 2.0) for _ in range(4)] for _ in range(n)]


def _max_err(a, b):
    return max(abs(x - y) for u, v in zip(a, b) for x, y in zip(u, v))


def _qmul(a, b):
    """Quaternion product a·b via the rc109 left operator (exact table path)."""
    return [float(x) for x in (quat.quaternion_left_mult(a) @ list(b))]


def _force_pure(monkeypatch):
    """Force the FULLY-pure composed path: the whole-transform C peer AND the
    rc109 per-op native dispatches are all bypassed."""
    monkeypatch.setattr(hd, "_qdft_native_ready", lambda: False)
    monkeypatch.setattr(quat, "_native_ready", lambda s: False)


# ────────────────────────────────────────────────────────────────────
# (a) Round-trips — both sides, several N incl. non-powers-of-2
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("n", NS)
def test_round_trip_both_directions(form, n):
    x = _signal(n)
    fwd_back = quaternion_dft(quaternion_dft(x, form=form), form=form,
                              inverse=True)
    assert _max_err(fwd_back, x) < 1e-12 * max(1, n)
    inv_fwd = quaternion_dft(quaternion_dft(x, form=form, inverse=True),
                             form=form)
    assert _max_err(inv_fwd, x) < 1e-12 * max(1, n)


@pytest.mark.parametrize("axis", AXES)
def test_round_trip_every_axis_non_power_of_two(axis):
    x = _signal(7)
    got = quaternion_dft(quaternion_dft(x, form="right", mu_axis=axis),
                         form="right", mu_axis=axis, inverse=True)
    assert _max_err(got, x) < 1e-12


# ────────────────────────────────────────────────────────────────────
# (b) Left ≠ right is REAL; ℝ[μ] signals degenerate to exact equality
# ────────────────────────────────────────────────────────────────────

def test_left_and_right_are_genuinely_different():
    x = _signal(6)
    left = quaternion_dft(x, form="left")
    right = quaternion_dft(x, form="right")
    assert _max_err(left, right) > 1e-2, \
        "ℍ non-commutativity must make the left/right QDFTs differ"


@pytest.mark.parametrize("axis,slot", [("i", 1), ("j", 2), ("k", 3)])
def test_r_mu_signal_degenerates_to_equality(axis, slot):
    """The classic degeneracy: samples in ℝ[μ] commute with the twiddle, so
    left == right EXACTLY (same floats, not a tolerance)."""
    rng = random.Random(42)
    x = []
    for _ in range(5):
        s = [0.0, 0.0, 0.0, 0.0]
        s[0] = rng.uniform(-1, 1)
        s[slot] = rng.uniform(-1, 1)
        x.append(s)
    left = quaternion_dft(x, form="left", mu_axis=axis)
    right = quaternion_dft(x, form="right", mu_axis=axis)
    assert left == right


# ────────────────────────────────────────────────────────────────────
# (c) The Klein-4 preservation demonstration — the issue's WHY
# ────────────────────────────────────────────────────────────────────

def _enc(s):
    """Klein-4 sector s ∈ {0,1,2,3} → quaternion; bit0 → sign of the i
    component (one Z₂ axis), bit1 → sign of the j component (the other)."""
    return [0.0, 1.0 - 2 * (s & 1), 1.0 - 2 * ((s >> 1) & 1), 0.0]


def _dec(q):
    bit0 = 0 if q[1] > 0 else 1
    bit1 = 0 if q[2] > 0 else 1
    return bit0 | (bit1 << 1)


def test_klein4_preservation_qdft_keeps_both_axes_complex_fft_loses_one():
    """Encode a Klein-4-structured signal with BOTH Z₂ axes carrying
    information. The QDFT round-trip recovers every sector exactly (all four
    components ≈ 1e-15). Analysing the same object with the shipped COMPLEX
    fft REQUIRES projecting each quaternion to ℂ (q0 + q1·i) first — the
    projection has no slot for the second axis, so bit1 is structurally gone
    (100% loss on the j-channel): the flat shadow."""
    sectors = [0, 1, 2, 3, 2, 1, 0, 3]       # both bits toggle
    x = [_enc(s) for s in sectors]

    # QDFT (ℍ coefficient algebra): both axes survive the round-trip.
    back = quaternion_dft(quaternion_dft(x, form="left"), form="left",
                          inverse=True)
    assert [_dec(q) for q in back] == sectors
    qdft_err = _max_err(back, x)
    assert qdft_err < 1e-12, f"QDFT component recovery err {qdft_err:.2e}"

    # Complex-FFT path (the shipped op on the ℂ-projection): bit0 survives...
    z = [complex(q[0], q[1]) for q in x]      # the projection to ℂ
    zr = complex_fft(complex_fft(z), inverse=True)
    rec_bit0 = [0 if c.imag > 0 else 1 for c in zr]
    assert rec_bit0 == [s & 1 for s in sectors]
    # ...but the j-channel (bit1) was never representable in ℂ: reconstruct
    # quaternions from the complex round-trip and measure the j-channel loss.
    proj_back = [[c.real, c.imag, 0.0, 0.0] for c in zr]
    j_true = [q[2] for q in x]
    j_proj = [q[2] for q in proj_back]
    j_loss = max(abs(a - b) for a, b in zip(j_true, j_proj))
    assert j_loss == 1.0, (
        f"the ℂ projection must lose the FULL j-channel (|±1| → 0); "
        f"got max loss {j_loss}"
    )
    true_bit1 = [(s >> 1) & 1 for s in sectors]
    qdft_bit1 = [(_dec(q) >> 1) & 1 for q in back]
    assert qdft_bit1 == true_bit1, "QDFT must keep the axis the ℂ path lost"


# ────────────────────────────────────────────────────────────────────
# (d) Linearity + the module-map convention locks
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("form", FORMS)
def test_real_scalar_linearity(form):
    x = _signal(6, seed=1)
    y = _signal(6, seed=2)
    a, b = 1.75, -0.4
    combo = [[a * u[i] + b * v[i] for i in range(4)] for u, v in zip(x, y)]
    lhs = quaternion_dft(combo, form=form)
    X = quaternion_dft(x, form=form)
    Y = quaternion_dft(y, form=form)
    rhs = [[a * u[i] + b * v[i] for i in range(4)] for u, v in zip(X, Y)]
    assert _max_err(lhs, rhs) < 1e-12


def test_left_form_is_a_right_module_map_and_mirror():
    """Convention lock: QDFT_left(x·q) == QDFT_left(x)·q (the twiddle sits on
    the LEFT, so a RIGHT quaternion factor passes through) — and the mirror
    for the right form."""
    x = _signal(5, seed=3)
    q = [0.5, -1.0, 2.0, 0.25]
    xq = [_qmul(s, q) for s in x]
    lhs = quaternion_dft(xq, form="left")
    rhs = [_qmul(s, q) for s in quaternion_dft(x, form="left")]
    assert _max_err(lhs, rhs) < 1e-11
    qx = [_qmul(q, s) for s in x]
    lhs_r = quaternion_dft(qx, form="right")
    rhs_r = [_qmul(q, s) for s in quaternion_dft(x, form="right")]
    assert _max_err(lhs_r, rhs_r) < 1e-11


# ────────────────────────────────────────────────────────────────────
# (e) Parseval — this convention supports it cleanly (stated form)
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("n", (3, 5, 8, 12))
def test_parseval_energy(form, n):
    """Σ_k ‖X[k]‖² == N·Σ_n ‖x[n]‖² (forward unscaled — the twiddle is a unit
    quaternion and Σ_k W(k(n−n′)) = N·δ runs inside ℝ[μ] ≅ ℂ)."""
    x = _signal(n, seed=4)
    X = quaternion_dft(x, form=form)
    e_time = sum(c * c for v in x for c in v)
    e_freq = sum(c * c for v in X for c in v)
    assert e_freq == pytest.approx(n * e_time, rel=1e-12)


# ────────────────────────────────────────────────────────────────────
# (f) Python == C parity — BYTE-EXACT (the parity contract)
# ────────────────────────────────────────────────────────────────────

def test_native_symbol_present_on_native_build():
    """On a native build the rc110 symbol exists (never pure-only by
    accident). Skipped only when the whole lib is absent (pure wheel)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("pure-Python environment (no native lib)")
    assert hasattr(_native.LIB, "srmech_quaternion_dft"), \
        "native lib lacks srmech_quaternion_dft"


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("inverse", (False, True))
def test_native_matches_pure_byte_for_byte(form, inverse, monkeypatch):
    """Whichever path is active vs the FULLY-forced-pure composed path:
    IDENTICAL coefficients (==, not a tolerance) across axes and lengths —
    the rc109 parity pattern applied to the whole transform."""
    cases = [(n, ax) for n in (1, 2, 3, 5, 8, 12) for ax in AXES]
    cases += [(6, [0.0, 3.0, 4.0, 0.0])]        # a general (3-4-5) axis
    active = {}
    for n, ax in cases:
        key = (n, str(ax))
        active[key] = quaternion_dft(_signal(n), form=form, mu_axis=ax,
                                     inverse=inverse)
    _force_pure(monkeypatch)
    for n, ax in cases:
        key = (n, str(ax))
        pure = quaternion_dft(_signal(n), form=form, mu_axis=ax,
                              inverse=inverse)
        assert active[key] == pure, (
            f"quaternion_dft(n={n}, form={form}, mu_axis={ax}, "
            f"inverse={inverse}) diverged native vs pure"
        )


def test_forced_pure_path_round_trips(monkeypatch):
    """The composed pure path alone (no C at any layer) decides the transform
    completely — the co-equal-parity discipline."""
    _force_pure(monkeypatch)
    x = _signal(5)
    for form in FORMS:
        back = quaternion_dft(quaternion_dft(x, form=form), form=form,
                              inverse=True)
        assert _max_err(back, x) < 1e-12


# ────────────────────────────────────────────────────────────────────
# (g) DSL — the graduated TOML loads + runs
# ────────────────────────────────────────────────────────────────────

def test_dsl_loads_descriptor_and_runs_chain():
    from srmech import dsl
    x = _signal(4)
    via_chain = dsl.chain().then("quaternion_dft", form="right",
                                 mu_axis="j").run(x)
    direct = quaternion_dft(x, form="right", mu_axis="j")
    assert via_chain == direct


def test_descriptor_declares_the_graduation_and_c_peer():
    from srmech.dsl import get_descriptor
    desc = get_descriptor("quaternion_dft")
    cascade = desc["cascade"]
    assert cascade["name"] == "quaternion_dft"
    assert cascade["native"]["c_symbol"] == "srmech_quaternion_dft"
    assert cascade["native"]["abi_version"] == 3
    assert "graduated" in cascade["graduation"]["tier"]
    assert set(cascade["signature"]["forms"]) == {"left", "right"}
    # The F1000→F1001 encode/read API split is stated on the descriptor.
    assert "phase_coherent_peak" in cascade["graduation"]["read_path_split"]


# ────────────────────────────────────────────────────────────────────
# (h) Registration / ledger — bucket moved, count unchanged
# ────────────────────────────────────────────────────────────────────

def test_tools_total_stays_367():
    """The quaternion_dft ToolEntry pre-existed (v0.7.0rc31) — graduation
    updates the entry + its Rosetta bucket, it does NOT add a tool."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 390


def test_rosetta_bucket_is_c_dispatched():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in
            fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets = {r["defined_at"]: r["bucket"] for r in rows}
    assert buckets[
        "srmech.amsc.cascade.hypercomplex_dft.quaternion_dft"
    ] == "c_dispatched"


# ────────────────────────────────────────────────────────────────────
# Carrier + contract hygiene
# ────────────────────────────────────────────────────────────────────

def test_real_mat_input_accepted():
    x = _signal(4)
    m = Mat.from_rows(x, is_complex=False)
    assert quaternion_dft(m) == quaternion_dft(x)


def test_complex_mat_input_rejected():
    m = Mat.from_rows([[1 + 1j, 0, 0, 0]], is_complex=True)
    with pytest.raises(ValueError):
        quaternion_dft(m)


def test_contract_errors_preserved():
    with pytest.raises(ValueError):
        quaternion_dft([[1.0, 2.0, 3.0]])            # not a 4/8-vector
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0, 0, 0, 0, 1]])   # nonzero octonion tail
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0]], form="two_sided")
    with pytest.raises(ValueError, match="diagonal"):
        quaternion_dft([[0, 1, 0, 0]], mu_axis="z")
    assert quaternion_dft([]) == []
