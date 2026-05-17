"""Spike #41 anomaly investigation: why does PSD cosine similarity ~1.0
appear between fibonacci_log and multinacci_log AND between both and
the sawtooth anchor?

Hypothesis: log(F_n) ~ n * log(phi), i.e. a LINEAR ramp. The FFT of a
linear ramp (after DC removal) is dominated by 1/k harmonics (sawtooth-
like), so ALL log-growth signals have the same PSD shape.

This means time-domain PSD cosine-similarity is NOT a useful
fingerprint for growing-substrate sequences (Spike #38 lesson:
methodology is degenerate at this regime).

Per [[user_stance_string_theory_instrument_first]]: math doesn't lie,
investigate the anomaly. Don't paper over.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np

WORKSPACE = Path(__file__).resolve().parent
ANOMALY_RECORDS = WORKSPACE / "spike_41_anomaly_psd_records_2026-05-17.ndjson"
DATE_TAG = "2026-05-17"
SPIKE = "spike_41"


def emit(record: Dict) -> None:
    record = dict(record)
    record.setdefault("date", DATE_TAG)
    record.setdefault("spike", SPIKE)
    record.setdefault("timestamp", datetime.now(tz=timezone.utc).isoformat())
    with ANOMALY_RECORDS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=float))
        fh.write("\n")


def normalised_power_spectrum(seq, n_fft=256):
    seq = np.asarray(seq, dtype=np.float64)
    seq = seq - np.mean(seq)
    if np.all(seq == 0):
        return np.zeros(n_fft // 2)
    if len(seq) >= n_fft:
        seq = seq[:n_fft]
    else:
        seq = np.concatenate([seq, np.zeros(n_fft - len(seq))])
    psd = np.abs(np.fft.rfft(seq)) ** 2
    psd = psd[1:]
    norm = np.linalg.norm(psd)
    return psd / norm if norm > 0 else psd


def cosine_sim(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def main():
    if ANOMALY_RECORDS.exists():
        ANOMALY_RECORDS.unlink()

    print("=== Anomaly: PSD cosine sim ~ 1.0 between log-growth signals ===\n")

    n_terms = 256

    # Pure linear ramp
    linear_ramp = np.arange(n_terms, dtype=np.float64)

    # log(phi)^n (Fibonacci growth)
    phi = (1 + math.sqrt(5)) / 2
    log_phi = math.log(phi)
    fib_log_signal = np.array([n * log_phi for n in range(n_terms)])

    # log(spectral radius)^n for multinacci 3+7+1
    multi_spec = 1.516784  # from primary script
    log_multi = math.log(multi_spec)
    multi_log_signal = np.array([n * log_multi for n in range(n_terms)])

    # Pure sawtooth time-series
    M = np.linspace(0, 2 * np.pi, n_terms, endpoint=False)
    sawtooth = np.zeros(n_terms)
    for k in range(1, 21):
        sawtooth += (1.0 / k) * np.sin(k * M)

    # Pure cos (1 mode)
    cos_signal = np.cos(M)

    # Kepler-EOC at eps=0.1
    eoc = np.zeros(n_terms)
    for k in range(1, 41):
        eoc += (2.0 / k) * (0.1 ** k) * np.sin(k * M)

    # Compute PSDs
    psds = {
        "linear_ramp": normalised_power_spectrum(linear_ramp),
        "fib_log_signal": normalised_power_spectrum(fib_log_signal),
        "multi_log_signal": normalised_power_spectrum(multi_log_signal),
        "sawtooth": normalised_power_spectrum(sawtooth),
        "cos_signal": normalised_power_spectrum(cos_signal),
        "kepler_eoc": normalised_power_spectrum(eoc),
    }

    print("PSD cosine similarity matrix:")
    keys = list(psds.keys())
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            s = cosine_sim(psds[k1], psds[k2])
            print(f"  {k1:<20s} vs {k2:<20s}: {s:.4f}")
            emit({"pair": f"{k1} vs {k2}", "cosine_sim": s})

    print("\nDirect comparison of top-5 PSD bins:")
    for name in ["linear_ramp", "fib_log_signal", "multi_log_signal", "sawtooth"]:
        top5 = np.sort(psds[name])[::-1][:5]
        print(f"  {name:<20s}: {top5}")
        emit({"signal": name, "top5_psd_bins": [float(x) for x in top5]})

    print("\nVerdict:")
    print("  ALL log-growth signals (Fibonacci, Multinacci, linear-ramp) have")
    print("  IDENTICAL PSD shape (essentially the sawtooth 1/k harmonic series)")
    print("  because they are all linear ramps after DC removal.")
    print("  The PSD cosine-similarity finding in Step 5 of primary script is")
    print("  a METHODOLOGY ARTIFACT, NOT a structural-identity finding.")
    print()
    print("  Per Spike #38 lesson: methodology becomes degenerate at this regime.")
    print("  The COEFFICIENT-SERIES comparison (Step 6) is the load-bearing one.")
    print()

    emit({
        "kind": "anomaly_verdict",
        "anomaly": "PSD cosine sim ~ 1.0 between log-growth signals",
        "diagnosis": (
            "log(geometric_sequence) is a LINEAR RAMP. FFT of linear ramp (after "
            "DC removal) is dominated by 1/k harmonics (sawtooth-shape). "
            "All log-growth signals have identical PSD up to amplitude scaling. "
            "This means time-domain PSD cosine-similarity is NOT a useful "
            "fingerprint for growing-substrate sequences."
        ),
        "remediation": (
            "Use coefficient-series comparison (c_k Cauchy form) NOT time-domain "
            "PSD for growing-substrate comparison. Step 6 of primary script is "
            "load-bearing; Step 5 is methodology-artifact."
        ),
        "spike_38_pattern": "methodology degenerate at this regime",
    })


if __name__ == "__main__":
    main()
