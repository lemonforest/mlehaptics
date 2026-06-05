# R-RBS-LM Finding 402 — srmech 0.7.0rc47 landed the numpy-removal: surface preview + multi-layer practice (look before we leap)

**Date:** 2026-06-04
**Arc:** srmech upstream verify (the §22 numpy-drop landing) · **srmech RUN (rc47 preview, hold lifted by user direction)**
**Provenance:** `R-RBS-LM-R36_rc47_multilayer_surface_practice.py` · clean venvs `/tmp/verify_srmech_v070rc47` (plain) + `/tmp/verify_srmech_v070rc47_sci` (`srmech[scientific]`) · UPSTREAM_NOTES §24
**Composes:** UPSTREAM §22 (numpy-drop Option 1) · §22b (HV carrier) · F383/F393 (the odd forces FPU; numpy-free A-N) · ALU-D / AX-2 (the held items this unblocks)

---

## "Look before we leap" — the rc47 surface, verified
The numpy-removal (§22 Option 1) shipped in **0.7.0rc47** (TestPyPI, cp314 native wheel, ABI 3). Inspected in two clean venvs outside the source tree, ops **computed** (not just imported):

| tier | install | modules | notes |
|---|---|---|---|
| **numpy-free core** | plain `pip install srmech` | `format`(A), `cyclic`(I), `primes`(J), `rational`(N), `cascade`(K/C/atoms), **`laplacian`(L)** | all COMPUTE; `dense_laplacian`→plain `list`; **`jacobi_eigvals` numpy-free** (C₄→`[0,2,2,4]`) |
| **scientific** | `pip install 'srmech[scientific]'` | `qm.*`, `signal_processing` | **clean, instructive `ImportError`** when not installed ("…`pip install 'srmech[scientific]'`") |

**Outward API changes a subagent/script must know:**
1. **`srmech.HAS_NATIVE` REMOVED** → **`srmech.native_status()`** (dict). Old `srmech.HAS_NATIVE` AttributeErrors. (CLAUDE.md/docs still say HAS_NATIVE — fix on the clean-tag pass.)
2. **numpy is OPTIONAL** (v0.7.0). Plain = numpy-free; `[scientific]` adds it.
3. **HV carrier (§22b confirmed):** `hdc.klein4_*` → `srmech.amsc.hv.HV` (not `ndarray`); `v==w` scalar `bool` (accepts `ndarray`); `v[i]` plain `int`; `.tolist()`/`.tobytes()`/`.to_numpy()`(uint8)/`.sectors`. **numpy never escapes implicitly.**

## Multi-layer practice (R36) — the new surface used correctly, end-to-end
One cascade touching **A→I→J→N→M→L→K** on rc47, using the rc47 contract (native_status, HV carrier, numpy-free lists):
- A `sha256`→seed; I `gcd`; J `factor(360)=2³·3²·5`; N `best_rational→(5,8)`;
- M Klein-4 HV: `klein4_bind` self-sim 1.000; **unbind round-trip `sim=1.000`** (HV exact);
- L sector-graph → **`jacobi_eigvals` numpy-free `[0,2,2,4]`**; K `cascade.magnitude` spectral gap = 2.0.
All correct. The new surface composes cleanly across layers.

## The one GAP (UPSTREAM §24 — upstream ask)
**`srmech.amsc.hdc` still hard-imports numpy at module top** (`import numpy as np`, hdc.py:36). On a **plain (numpy-free) install**, `import srmech.amsc.hdc` raises a **raw `ModuleNotFoundError`** — inconsistent: hdc *returns* the numpy-free HV carrier, yet its module won't import without numpy, and it skips the clean `[scientific]` gate `qm` uses. **Fix:** lazy/optional numpy import (Klein-4 is HV-numpy-free) **or** gate hdc behind `[scientific]` like `qm`. Klein-4-on-plain-install is the one broken seam.

## Queue impact
- **BX-8** (rc-verify numpy-drop + HV) → ✅ **done** by this verification.
- **ALU-D** (numpy-free Class-L) → ✅ **demonstrated** (`jacobi_eigvals` numpy-free, plain install).
- **AX-2 / BX-5..7** → now **rc47-walkable** (M on `[scientific]`; qm on `[scientific]`), pending user direction + the hdc-gap caveat for plain installs.

## Verdict
rc47 is the numpy-removal landing, verified: numpy-free core that **computes** (incl. Class-L), a clean `[scientific]` gate for qm/signal_processing, and the **HV carrier** so numpy never escapes implicitly (the reflex-guard). One inconsistency — **hdc hard-imports numpy → raw crash on a plain install** (UPSTREAM §24, upstream ask). The new surface is now known well enough to prime a subagent; next is the experiment — *does a subagent use this surface correctly **without** the explicit srmech-first / "treat it like a math library" priming, because the HV carrier + clean gate + numpy-free core self-enforce?*
