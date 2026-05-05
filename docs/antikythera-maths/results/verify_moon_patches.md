# Moon catalog patches — patch-shrinks-residual verification

Re-run of the moon FFT sweep with each LS-fit recovered moon patch active. Each patch targets one dominant peak in the v0.5.3 spectrum.

- **Overall verdict:** **PARTIAL** (5 VINDICATED / 1 PARTIAL / 0 REJECTED out of 6)
- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.
- Window: ±200 yr around J2000 at 30-d cadence (4096 samples).

| patch | verdict | base amp | patched | shrinkage | RMS Δ |
| --- | :--- | ---: | ---: | ---: | ---: |
| `dione-1.06yr-diagonal` | **VINDICATED** | 1.168° | 0.021° | 98.2% | +2.336° |
| `tethys-0.38yr-diagonal` | **VINDICATED** | 1.751° | 0.109° | 93.8% | +1.433° |
| `enceladus-0.39yr-diagonal` | **VINDICATED** | 1.520° | 0.016° | 98.9% | +2.111° |
| `titan-0.69yr-diagonal` | **VINDICATED** | 1.564° | 0.071° | 95.5% | +0.940° |
| `iapetus-0.22yr-diagonal` | **VINDICATED** | 1.576° | 0.021° | 98.6% | +1.543° |
| `hyperion-0.20yr-diagonal` | **PARTIAL** | 5.439° | 1.351° | 75.2% | +3.715° |

## `dione-1.06yr-diagonal` — verdict: **VINDICATED**

- Body: **dione**
- Recovered amplitude: **3.5738°**
- Recovered period: **387.04 d**
- Recovered phase: **1.5027 rad** (86.10°)
- Baseline peak amplitude: **1.1678°**
- Patched peak amplitude: **0.0206°**
- Shrinkage: **98.2%**
- RMS residual: **2.535° → 0.199°** (+2.336°)

## `tethys-0.38yr-diagonal` — verdict: **VINDICATED**

- Body: **tethys**
- Recovered amplitude: **3.5733°**
- Recovered period: **138.24 d**
- Recovered phase: **1.1054 rad** (63.34°)
- Baseline peak amplitude: **1.7511°**
- Patched peak amplitude: **0.1093°**
- Shrinkage: **93.8%**
- RMS residual: **2.944° → 1.511°** (+1.433°)

## `enceladus-0.39yr-diagonal` — verdict: **VINDICATED**

- Body: **enceladus**
- Recovered amplitude: **3.5751°**
- Recovered period: **141.94 d**
- Recovered phase: **1.3156 rad** (75.38°)
- Baseline peak amplitude: **1.5196°**
- Patched peak amplitude: **0.0162°** (upper bound: target peak demoted below the K-th-strongest patched peak; actual amplitude is <= this value)
- Shrinkage: **98.9%**
- RMS residual: **2.569° → 0.458°** (+2.111°)

## `titan-0.69yr-diagonal` — verdict: **VINDICATED**

- Body: **titan**
- Recovered amplitude: **3.3130°**
- Recovered period: **252.74 d**
- Recovered phase: **0.2929 rad** (16.78°)
- Baseline peak amplitude: **1.5645°**
- Patched peak amplitude: **0.0709°**
- Shrinkage: **95.5%**
- RMS residual: **3.388° → 2.447°** (+0.940°)

## `iapetus-0.22yr-diagonal` — verdict: **VINDICATED**

- Body: **iapetus**
- Recovered amplitude: **3.2636°**
- Recovered period: **79.34 d**
- Recovered phase: **3.6725 rad** (210.42°)
- Baseline peak amplitude: **1.5758°**
- Patched peak amplitude: **0.0213°**
- Shrinkage: **98.6%**
- RMS residual: **2.497° → 0.954°** (+1.543°)

## `hyperion-0.20yr-diagonal` — verdict: **PARTIAL**

- Body: **hyperion**
- Recovered amplitude: **11.6459°**
- Recovered period: **72.42 d**
- Recovered phase: **0.9629 rad** (55.17°)
- Baseline peak amplitude: **5.4392°**
- Patched peak amplitude: **1.3511°**
- Shrinkage: **75.2%**
- RMS residual: **10.987° → 7.272°** (+3.715°)
