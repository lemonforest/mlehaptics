# Moon residual diagnostic — Phase A

**Hypothesis**: 13 of 17 moons show ~100° RMS residuals against ephemeris truth because the encoder advances at a uniform rate `omega = 2π / P_sidereal` while skyfield's `ecliptic_latlon()` measures longitude in Earth's J2000 ecliptic plane — for moons in inclined orbits the ecliptic projection is non-uniform in orbital phase.

- Native encoder used: **True**
- Auxiliary kernels: **['mar099s', 'jup365', 'sat441']**
- Samples per orbital period: **256**

Each body sampled at uniform JD over ONE full sidereal period starting from REFERENCE_JD = J2000.0. Residual = (encoded longitude − truth ecliptic longitude) mod 2π, signed.

| body | class | period (d) | RMS (°) | peak (°) | top-1 harmonic amp (°) |
| --- | --- | ---: | ---: | ---: | ---: |
| callisto | control | 16.689 | 1.040 | 1.689 | 0.8436 |
| titan | control | 15.945 | 5.212 | 10.402 | 3.1400 |
| io | broken | 1.769 | 0.418 | 0.738 | 0.2863 |
| europa | broken | 3.551 | 0.811 | 1.362 | 0.4840 |
| mimas | broken | 0.942 | 5.273 | 9.658 | 3.4386 |
| metis | broken | 0.295 | 0.066 | 0.117 | 0.0228 |

## Reading the table

If the diagnosis is right: **broken** rows have RMS within factor-of-3 of their v0.5.2 sweep RMS (so the broken signal IS the orbital-period warp, the v0.5.2 FFT was just aliasing it to near-DC content), AND the top-1 modulation harmonic should be comparable in amplitude to the v0.5.2 RMS (the warp is concentrated in 1-2 harmonics of the orbital period). **Control** rows should have RMS << 1°.
