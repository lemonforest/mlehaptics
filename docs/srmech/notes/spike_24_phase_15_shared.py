"""Spike #24 Phase 15 — shared analysis helpers.

Imported by each of the 6 cell scripts. Provides:
  - rigour_a_harmonic_analysis (Phase 9.2 method: Hann + parabolic interp)
  - rigour_b_harmonic_analysis (Welch + per-segment-variance CI + noise floor)
  - kepler_shape_verdict_rigour_a / _b
  - estimate_cycle_period (autocorrelation)
  - run_cell (top-level driver for one (formulation, rigour) cell)

All numpy/scipy stdlib; no new deps.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import welch


# ---------------------------------------------------------------------------
# Rigour A — Phase 9.2 method (Hann window + parabolic interp)
# ---------------------------------------------------------------------------
def rigour_a_harmonic_analysis(t, x, max_harmonics=10):
    t_uniform = np.linspace(t[0], t[-1], len(t))
    x_uniform = np.interp(t_uniform, t, x)
    x_detrended = x_uniform - np.mean(x_uniform)
    n = len(t_uniform)
    window = np.hanning(n)
    win_corr = np.sum(window) / n
    dt = t_uniform[1] - t_uniform[0]
    freqs = np.fft.rfftfreq(n, d=dt)
    amps = np.abs(np.fft.rfft(x_detrended * window)) / n * 2 / win_corr
    threshold = np.max(amps) * 0.01
    peak_indices = []
    for i in range(1, len(amps) - 1):
        if amps[i] > threshold and amps[i] > amps[i - 1] and amps[i] > amps[i + 1]:
            peak_indices.append(i)
    peak_indices.sort(key=lambda i: -amps[i])
    leading = []
    fundamental = None
    for i in peak_indices[:max_harmonics]:
        a_l, a_c, a_r = amps[i - 1], amps[i], amps[i + 1]
        denom = a_l - 2 * a_c + a_r
        delta = 0.5 * (a_l - a_r) / denom if denom != 0 else 0.0
        f_refined = freqs[i] + delta * (freqs[1] - freqs[0])
        if fundamental is None:
            fundamental = f_refined
        ratio = f_refined / fundamental if fundamental and fundamental > 0 else None
        leading.append({
            "freq_hz": float(f_refined),
            "amplitude": float(a_c),
            "ratio_to_fundamental": float(ratio) if ratio is not None else None,
        })
    return leading, fundamental


# ---------------------------------------------------------------------------
# Rigour B — Welch with per-segment variance CI + noise-floor significance
# ---------------------------------------------------------------------------
def rigour_b_harmonic_analysis(t, x, n_segments_target=100, max_harmonics=10):
    t_uniform = np.linspace(t[0], t[-1], len(t))
    x_uniform = np.interp(t_uniform, t, x)
    x_detrended = x_uniform - np.mean(x_uniform)
    n = len(t_uniform)
    dt = t_uniform[1] - t_uniform[0]
    fs = 1.0 / dt
    nperseg = max(256, int(2 * n / (n_segments_target + 1)))
    nperseg = min(nperseg, n)
    freqs, psd_mean = welch(x_detrended, fs=fs, window='hann',
                              nperseg=nperseg, noverlap=nperseg // 2,
                              scaling='spectrum')
    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    amps = np.sqrt(2.0 * psd_mean * df)

    # Per-segment CI: compute each Welch segment's amplitude individually using
    # the SAME scipy.signal.welch call (with nperseg = whole segment) so the
    # normalisation matches `amps` exactly. Avoids scaling drift between
    # the mean-Welch and the per-segment-Welch computations.
    step = nperseg // 2
    n_segs = (n - nperseg) // step + 1
    if n_segs >= 4:
        seg_amps_list = []
        for k in range(n_segs):
            seg = x_detrended[k * step:k * step + nperseg]
            if len(seg) < nperseg:
                break
            _, psd_seg = welch(seg, fs=fs, window='hann',
                                nperseg=len(seg), noverlap=0,
                                scaling='spectrum')
            seg_amps_list.append(np.sqrt(2.0 * psd_seg * df))
        if len(seg_amps_list) >= 4:
            seg_amps = np.array(seg_amps_list)
            amp_se_per_freq = np.std(seg_amps, axis=0, ddof=1) / np.sqrt(len(seg_amps_list))
            ci_low_per_freq = amps - 1.96 * amp_se_per_freq
            ci_high_per_freq = amps + 1.96 * amp_se_per_freq
            ci_low_per_freq = np.maximum(ci_low_per_freq, 0.0)
        else:
            ci_low_per_freq = amps.copy()
            ci_high_per_freq = amps.copy()
            amp_se_per_freq = np.zeros_like(amps)
    else:
        ci_low_per_freq = amps.copy()
        ci_high_per_freq = amps.copy()
        amp_se_per_freq = np.zeros_like(amps)

    threshold = np.max(amps) * 0.01
    peak_indices = []
    for i in range(1, len(amps) - 1):
        if amps[i] > threshold and amps[i] > amps[i - 1] and amps[i] > amps[i + 1]:
            peak_indices.append(i)
    peak_indices.sort(key=lambda i: -amps[i])

    if not peak_indices:
        return [], None, float(np.median(amps)), n_segs

    fundamental = freqs[peak_indices[0]]
    noise_floor = float(np.median(amps))

    leading = []
    for i in peak_indices[:max_harmonics]:
        a_l, a_c, a_r = amps[i - 1], amps[i], amps[i + 1]
        denom = a_l - 2 * a_c + a_r
        delta = 0.5 * (a_l - a_r) / denom if denom != 0 else 0.0
        f_refined = freqs[i] + delta * df
        ci_low = float(ci_low_per_freq[i])
        ci_high = float(ci_high_per_freq[i])
        ratio = f_refined / fundamental if fundamental > 0 else None
        significant = bool(a_c > 5.0 * noise_floor)
        leading.append({
            "freq_hz": float(f_refined),
            "amplitude": float(a_c),
            "amplitude_ci_low": ci_low,
            "amplitude_ci_high": ci_high,
            "amplitude_se": float(amp_se_per_freq[i]),
            "ratio_to_fundamental": float(ratio) if ratio is not None else None,
            "significant_vs_noise_floor_5x": significant,
        })
    return leading, float(fundamental), noise_floor, int(n_segs)


# ---------------------------------------------------------------------------
# Kepler-shape verdict
# ---------------------------------------------------------------------------
def _verdict_from_match(n_match, extras, n_floor=4):
    if n_match >= n_floor:
        return "kepler_shape_with_extras" if extras else "kepler_shape_clean"
    return "kepler_shape_absent"


def kepler_shape_verdict_rigour_a(leading, tol=0.05):
    if len(leading) < 2 or not leading or leading[0]["ratio_to_fundamental"] is None:
        return "absent", 0
    integer_match = []
    for k in range(1, 7):
        match = any(
            p["ratio_to_fundamental"] is not None
            and abs(p["ratio_to_fundamental"] - k) < tol
            for p in leading
        )
        integer_match.append(match)
    n_match = sum(integer_match)
    fund_amp = leading[0]["amplitude"]
    extras = any(
        p["ratio_to_fundamental"] is not None
        and p["amplitude"] > 0.05 * fund_amp
        and min(abs(p["ratio_to_fundamental"] - k) for k in range(1, 11)) > tol
        for p in leading
    )
    return _verdict_from_match(n_match, extras), n_match


def kepler_shape_verdict_rigour_b(leading, tol=0.06):
    if len(leading) < 2 or not leading or leading[0]["ratio_to_fundamental"] is None:
        return "absent", 0
    integer_match = []
    for k in range(1, 7):
        match = any(
            p["ratio_to_fundamental"] is not None
            and p["significant_vs_noise_floor_5x"]
            and abs(p["ratio_to_fundamental"] - k) < tol
            for p in leading
        )
        integer_match.append(match)
    n_match = sum(integer_match)
    fund_amp = leading[0]["amplitude"]
    extras = any(
        p["ratio_to_fundamental"] is not None
        and p["amplitude"] > 0.05 * fund_amp
        and p["significant_vs_noise_floor_5x"]
        and min(abs(p["ratio_to_fundamental"] - k) for k in range(1, 11)) > tol
        for p in leading
    )
    return _verdict_from_match(n_match, extras), n_match


# ---------------------------------------------------------------------------
# Cycle-period estimator
# ---------------------------------------------------------------------------
def estimate_cycle_period(fn, y0, t_max_probe=200.0, n_probe=10000, solver_kw=None,
                           var_index=0):
    kw = {"method": "RK45", "rtol": 1e-8, "atol": 1e-10}
    if solver_kw:
        kw.update(solver_kw)
    sol = solve_ivp(fn, (0.0, t_max_probe), y0,
                    t_eval=np.linspace(0.0, t_max_probe, n_probe), **kw)
    if not sol.success:
        return None
    half = n_probe // 2
    x = sol.y[var_index, half:] - np.mean(sol.y[var_index, half:])
    n = len(x)
    if np.std(x) < 1e-8:
        return None  # decayed to fixed point
    f = np.fft.rfft(x, n=2 * n)
    acf = np.fft.irfft(f * np.conj(f))[:n]
    if acf[0] == 0:
        return None
    acf /= acf[0]
    dt = (sol.t[-1] - sol.t[0]) / (n_probe - 1)
    zero_cross = None
    for k in range(1, n - 1):
        if acf[k] < 0 and acf[k - 1] >= 0:
            zero_cross = k
            break
    if zero_cross is None:
        return None
    for k in range(zero_cross + 1, n - 1):
        if acf[k] > acf[k - 1] and acf[k] > acf[k + 1]:
            return float(k * dt)
    return None


# ---------------------------------------------------------------------------
# Top-level cell driver
# ---------------------------------------------------------------------------
def run_rigour_level(rigour_label, fn, y0, t_cycle, n_cycles, transient_frac,
                     extras, solver_kw=None, target_var_index=0,
                     target_var_name="x", samples_per_cycle=20,
                     max_n_points=600_000):
    t_final = t_cycle * n_cycles
    n_points = min(max_n_points, max(samples_per_cycle * n_cycles, 10000))
    kw = {"method": "RK45", "rtol": 1e-8, "atol": 1e-10}
    if solver_kw:
        kw.update(solver_kw)
    sol = solve_ivp(fn, (0.0, t_final), y0,
                    t_eval=np.linspace(0.0, t_final, n_points), **kw)
    if not sol.success:
        return {
            "rigour_level": rigour_label,
            "integration_success": False,
            "error": str(sol.message),
            "t_final": float(t_final),
            "n_points_attempted": int(n_points),
        }
    keep = int(len(sol.t) * transient_frac)
    t = sol.t[keep:]
    x = sol.y[target_var_index, keep:]
    rec = {
        "rigour_level": rigour_label,
        "integration_success": True,
        "t_final": float(t_final),
        "n_cycles_integrated": int(n_cycles),
        "n_points": int(n_points),
        "transient_drop_fraction": float(transient_frac),
        "target_variable": target_var_name,
        "parameters": extras,
        "solver_method": kw.get("method", "RK45"),
        "solver_rtol": kw.get("rtol"),
        "solver_atol": kw.get("atol"),
    }
    if rigour_label == "A":
        leading, fund = rigour_a_harmonic_analysis(t, x)
        verdict, n_integer_match = kepler_shape_verdict_rigour_a(leading)
        rec["fundamental_freq_hz"] = float(fund) if fund else None
        rec["leading_harmonics"] = leading
        rec["n_integer_harmonics_matched_out_of_6"] = int(n_integer_match)
        rec["kepler_shape_verdict"] = verdict
    else:
        leading, fund, noise_floor, n_segs = rigour_b_harmonic_analysis(t, x)
        verdict, n_integer_match = kepler_shape_verdict_rigour_b(leading)
        rec["fundamental_freq_hz"] = float(fund) if fund else None
        rec["noise_floor"] = noise_floor
        rec["welch_n_segments"] = n_segs
        rec["leading_harmonics"] = leading
        rec["n_integer_harmonics_matched_out_of_6"] = int(n_integer_match)
        rec["kepler_shape_verdict"] = verdict
    return rec


def write_ndjson(records, out_path):
    with Path(out_path).open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def make_header(spike_phase, cell_id, domain, formulation, model, reference):
    return {
        "record_kind": "header",
        "spike": 24,
        "phase": spike_phase,
        "cell_id": cell_id,
        "domain": domain,
        "formulation": formulation,
        "model": model,
        "reference": reference,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_one_cell(cell_id, domain, formulation, model_name, reference,
                 fn, y0, params, out_path,
                 solver_kw=None, target_var_index=0, target_var_name="x",
                 t_cycle_fallback=None, max_n_points=600_000,
                 n_cycles_a=5000, n_cycles_b=50000,
                 transient_a=0.05, transient_b=0.02):
    """End-to-end runner for one (domain, formulation) cell.

    Returns the (rigour_a_rec, rigour_b_rec, cell_verdict_rec) tuple AND writes
    the per-cell NDJSON.
    """
    records = []
    records.append(make_header("15", cell_id, domain, formulation, model_name, reference))

    t_cycle = estimate_cycle_period(fn, y0, t_max_probe=200.0, n_probe=20000,
                                     solver_kw=solver_kw, var_index=target_var_index)
    if t_cycle is None or t_cycle <= 0:
        t_cycle = t_cycle_fallback or 6.283
        cycle_method = "fallback (autocorrelation failed)"
    else:
        cycle_method = "autocorrelation first-peak after first zero crossing"

    records.append({
        "record_kind": "cycle_period_estimate",
        "cell_id": cell_id,
        "t_cycle_estimated": float(t_cycle),
        "method": cycle_method,
    })

    rec_a = run_rigour_level("A", fn, y0, t_cycle, n_cycles=n_cycles_a,
                              transient_frac=transient_a, extras=params,
                              solver_kw=solver_kw,
                              target_var_index=target_var_index,
                              target_var_name=target_var_name,
                              max_n_points=max_n_points)
    rec_a["record_kind"] = "harmonic_signature"
    rec_a["cell_id"] = cell_id
    records.append(rec_a)

    rec_b = run_rigour_level("B", fn, y0, t_cycle, n_cycles=n_cycles_b,
                              transient_frac=transient_b, extras=params,
                              solver_kw=solver_kw,
                              target_var_index=target_var_index,
                              target_var_name=target_var_name,
                              max_n_points=max_n_points)
    rec_b["record_kind"] = "harmonic_signature"
    rec_b["cell_id"] = cell_id
    records.append(rec_b)

    a_verdict = rec_a.get("kepler_shape_verdict", "n/a")
    b_verdict = rec_b.get("kepler_shape_verdict", "n/a")
    cell_verdict = {
        "record_kind": "cell_verdict",
        "cell_id": cell_id,
        "rigour_a_verdict": a_verdict,
        "rigour_b_verdict": b_verdict,
        "rigour_a_n_integer_match": rec_a.get("n_integer_harmonics_matched_out_of_6"),
        "rigour_b_n_integer_match": rec_b.get("n_integer_harmonics_matched_out_of_6"),
        "rigour_levels_agree": (a_verdict == b_verdict),
    }
    records.append(cell_verdict)

    write_ndjson(records, out_path)
    return rec_a, rec_b, cell_verdict
