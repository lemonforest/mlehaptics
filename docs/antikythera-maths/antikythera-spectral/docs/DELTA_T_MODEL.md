# ΔT — Earth-rotation drift, and what it means for Hellenistic-era queries

ΔT (Greek "delta-T") is the difference between Terrestrial Time (a uniform tick from atomic clocks back-extrapolated through ephemeris models) and Universal Time (the rotation of the Earth). For modern queries this is small and well-known (~70 s in 2025); for Hellenistic-era queries it grows, and uncertainty grows with it.

## Magnitudes

At -200 BCE (~Antikythera mechanism era), ΔT is approximately **3 hours** (10 800 seconds). The uncertainty in ΔT at that epoch is roughly **±1 hour**, dominated by:

- gaps in ancient eclipse-timing records,
- modelling assumptions about lunar tidal acceleration ("d_dot"),
- small-scale fluctuations in Earth-rotation rate that we cannot resolve at multi-millennium timescales.

Authoritative model: Morrison & Stephenson 2004, *Historical values of the Earth's clock error ΔT*, J. Hist. Astron. 35:327. The NASA Five Millennium Catalog of Solar Eclipses (Espenak) bakes this model in for the JD timestamps it publishes.

## Why this dominates apparent kernel-vs-kernel differences at -200 BCE

When a user calls `compare_ephemerides(jd, body, 'de441', 'de422')` for a Hellenistic JD:

- DE441 and DE422 use slightly different ΔT models internally,
- the apparent body position depends on both the dynamic-model state at TDB *and* the rotation of the observer (Earth) at UT,
- the cross-kernel difference can be 10–15 arc-minutes for the **fast-moving Moon**, with negligible difference for slow planets like Saturn.

That 10–15 arc-minute Moon difference is **mostly ΔT**, not a real kernel disagreement. A user surprised by it should look at this document first.

## Why E-H1b's tolerance is ±1 day, not ±1 hour

The Hellenistic eclipse anchor list (`research/hellenistic_eclipses.HELLENISTIC_ANCHORS`) carries JDs from Espenak's NASA Five Millennium Catalog. Those JDs already incorporate the Morrison & Stephenson 2004 ΔT model. But:

- ancient observers timed eclipses to the day, occasionally to the hour, never to the minute,
- the catalogue's JD therefore inherits ~3 hours of ΔT uncertainty per anchor,
- absorbing this into a ±1-day tolerance gives the encoder ~8× safety margin.

If we tightened E-H1b to ±1 hour, the test would fail not because the encoder is wrong but because ancient observers couldn't time eclipses that precisely.

## Practical guidance

If you're using `compare_ephemerides` for Hellenistic-era queries:

- Differences ≤ 15 arc-minutes for slow planets, ≤ 1° for the Moon → expected, dominated by ΔT.
- Differences > 1° → likely a real kernel disagreement worth investigating (rare; almost never happens between long-coverage kernels like DE441 vs DE422).

For modern queries (1900+ CE):

- Both kernels agree to sub-arc-second precision; differences > 0.1″ are noise-level.

## References

- Morrison, L. V. & Stephenson, F. R. (2004). Historical values of the Earth's clock error ΔT. *Journal for the History of Astronomy* 35:327–336.
- Espenak, F. NASA Five Millennium Catalog of Solar Eclipses (-1999 to +3000). https://eclipse.gsfc.nasa.gov/SEcat5/SEcatalog.html
- Park, R. S. et al. (2021). The JPL Planetary and Lunar Ephemerides DE440 and DE441. *Astronomical Journal* 161:105.
