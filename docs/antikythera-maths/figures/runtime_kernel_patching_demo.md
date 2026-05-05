# Runtime kernel patching demo — v0.4.0

Each row encodes the Sol Star System at a JD; columns show per-body phase delta (in degrees) under each catalog patch vs the no-patch baseline. With no patches active, the encoder is byte-identical to v0.3.1.

## `mars-7.96yr-diagonal` (sinusoid)

- amplitude: **3.45 deg**
- period:    **2907.3 d** (7.96 yr)

| JD | delta_t (yr) | delta_mars (deg) |
| --- | --- | --- |
| 2444240.00 | -20.0 | +0.2737 |
| 2449718.75 | -5.0 | +2.4875 |
| 2451545.00 | +0.0 | +0.0000 |
| 2453371.25 | +5.0 | -2.4875 |
| 2458850.00 | +20.0 | -0.2737 |

_(sanity: all other 24 bodies untouched at JD=2458850)_

## `mercury-10.69yr-diagonal` (sinusoid)

- amplitude: **9.19 deg**
- period:    **3905.1 d** (10.69 yr)

| JD | delta_t (yr) | delta_mercury (deg) |
| --- | --- | --- |
| 2444240.00 | -20.0 | +6.6742 |
| 2449718.75 | -5.0 | -1.8547 |
| 2451545.00 | +0.0 | +0.0000 |
| 2453371.25 | +5.0 | +1.8547 |
| 2458850.00 | +20.0 | -6.6742 |

_(sanity: all other 24 bodies untouched at JD=2458850)_

## `jupiter-saturn-9.56yr-coupled` (coupled-sinusoid)

- amplitude: **45.00 deg**
- period:    **3490.9 d** (9.56 yr)
- correlation: **-1** (anti-correlated libration)

| JD | delta_t (yr) | delta_jupiter (deg) | delta_saturn (deg) |
| --- | --- | --- | --- |
| 2444240.00 | -20.0 | -24.7258 | +24.7258 |
| 2449718.75 | -5.0 | +6.5213 | -6.5213 |
| 2451545.00 | +0.0 | +0.0000 | +0.0000 |
| 2453371.25 | +5.0 | -6.5213 | +6.5213 |
| 2458850.00 | +20.0 | +24.7258 | -24.7258 |

_(sanity: all other 24 bodies untouched at JD=2458850)_


---

These tables are reproducible — each row is the difference between a baseline encode (no patches) and a patched encode (the named patch active). For coupled patches, the two columns are equal in magnitude with opposite sign — the anti-correlated J-S libration signature.
