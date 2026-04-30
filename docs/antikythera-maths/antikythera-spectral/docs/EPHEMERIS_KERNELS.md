# JPL DE-series ephemeris kernels — what they are, when to use which

`antikythera-spectral` validates the encoder against JPL's DE-series ephemeris files. Different eras of validation need different kernels.

## Kernel summary

| Kernel | Coverage | Size on disk | Use when |
|---|---|---:|---|
| `de421` | 1899-07-29 to 2053-10-09 | ~16 MB | Modern control only (E-H1a). Cannot reach Hellenistic dates. |
| `de422` | 3001 BCE to 3000 CE | ~660 MB | Antikythera-era queries OK. Older long-coverage option. |
| `de440` | 1849 to 2150 | ~32 MB | Modern queries with current best dynamics. |
| `de441` | 13201 BCE to 17191 CE | ~3.1 GB | JPL current best (Park et al. 2021). Default for Hellenistic. |
| `de441_part1` | 13201 BCE to 1550 CE | ~1.5 GB | Hellenistic-only subset of DE441. **Recommended** for Antikythera work. |
| `de441_part2` | 1550 CE to 17191 CE | ~1.5 GB | Modern + future subset of DE441. |

## How to download

Per ADR 0001 / 0003 we never auto-download. Explicit user opt-in:

```bash
antikythera-spectral kernel download de441_part1   # prompts y/N, ~1.5 GB
```

Or programmatically:

```python
from antikythera_spectral.ephemeris import download_kernel
download_kernel("de441_part1")    # interactive y/N prompt + size warning
```

The download lands in `~/.antikythera_spectral_data/` (or wherever skyfield's `Loader` resolves to). Subsequent `load_ephemeris('de441_part1')` calls find it on disk.

## Allowlist

The package only accepts kernel names from a frozen tuple, validated **before** any URL or filesystem path is constructed:

```python
ALLOWED_KERNELS = (
    "de421", "de422", "de440", "de441", "de441_part1", "de441_part2",
)
```

Adding a kernel requires a PR review (and an ADR if the new kernel comes from a non-JPL source). See ADR 0003 for the discipline.

## Why so many

JPL releases successive ephemerides as their dynamic models improve. DE441 is the current best long-coverage kernel; DE422 is its predecessor; DE421 is the pre-2008 modern-only standard. We retain DE421 for two reasons:

1. **Modern-control test (E-H1a)** — pin the encoder against the modern era using a kernel small enough to ship in CI cache.
2. **Cross-validation comparator** — `compare_ephemerides('de421', 'de441')` shows users how much the modern best-estimate differs from older models within their overlap range.

## ΔT — see [DELTA_T_MODEL.md](DELTA_T_MODEL.md)

Hellenistic-era queries inherit ~3 hours of Earth-rotation drift uncertainty from the ΔT model the kernel uses. The cross-kernel differences a user sees at -200 BCE are mostly ΔT, not real kernel disagreements.

## References

- Park, R. S. et al. (2021). The JPL Planetary and Lunar Ephemerides DE440 and DE441. *Astron. J.* 161:105.
- Folkner, W. M. et al. (2014). The Planetary and Lunar Ephemerides DE430 and DE431. *IPN Progress Report* 42-196.
- Skyfield documentation: https://rhodesmill.org/skyfield/
