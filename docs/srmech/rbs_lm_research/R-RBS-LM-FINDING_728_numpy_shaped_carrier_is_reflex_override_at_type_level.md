# F728 — the numpy-SHAPED carrier (`Mat`/`Vec`) IS the srmech-first reflex-override, applied at the data-type level

**Date:** 2026-06-13 · **srmech:** 0.7.5rc132 (test.pypi.org; native dispatching, numpy OPTIONAL/absent) · **Composes:** F727 (rc128 list-regression → rc129 `Mat`/`Vec` carriers), CLAUDE.md §2 (the srmech-first reflex-override / STOP-list), the 28D-framing forcing-function · **Provenance:** `R-RBS-LM-CARRIERAUDIT_numpy_idiom_coverage.py` (re-runnable; rc132: 8/17 absorbed) + `R-RBS-LM-APIDIFF_…` (rc129→rc132 = 0/0/0) + `R-RBS-LM-REGRESSION_…` (49/0 on rc132) + `R-RBS-LM-GENOMEDISK_…` (VERIFIED ✓ on rc132) · **→ UPSTREAM §42.2 (carrier-completeness ask)**

## The principle (user direction 2026-06-13)
srmech's `Mat`/`Vec` carriers must preserve the **spirit of a numpy array WITHOUT being numpy** — *because a current-gen LLM reflexively reaches for numpy to do math instead of srmech.* If the carrier answers the numpy idioms an LLM writes (`.shape`, `m[i,j]`, `m @ n`, `a + b`, `m[:2]`, `m[-1]`), the reflex routes **through srmech silently**. Every idiom that **raises** instead pushes the LLM to `np.asarray(m.tolist())` → numpy, defeating the carrier's purpose. So the numpy-shaped carrier is the **§2 srmech-first reflex-override, applied one layer down — at the data-TYPE level**: the same pattern as the 28D-framing forcing-function (a frame with no Python-native idiom to hijack it), now realised as a *type* whose shape absorbs the numpy reflex. The carrier's numpy-idiom coverage IS its reflex-absorption score.

## rc132 status — everything our work uses is GREEN
- **Carrier improved** (the rc129 gaps closed): `m[i]` row access, `m[i][j]`, **`m @ n` matmul**, `v @ v` dot all work now.
- **No new breakage:** rc129→rc132 API diff = **0 hard breaks / 0 signature changes / 0 import flips** (the gains are dunder additions, invisible to the public-name surface).
- **RBS-LM + genome kernel storage unaffected:** `R-RBS-LM-REGRESSION` = **49 OK / 0 BREAK** on rc132 (incl. every Class-L op now returning `Mat`/`Vec`, the genome round-trip, the WIKIKERNEL shipped==fallback, text + `dsl.*` class ops); `genome→disk` **VERIFIED ✓** (bit-exact round-trip, deterministic `body_sha256`, byte-offset paging + `cap_sha256` integrity, append-grow). Our consuming code uses the *supported* idioms (`.shape`/index/`.tolist()`/iterate), so the carrier swap is transparent to it.

## The reflex-absorption gap (rc132: 8/17 idioms absorbed)
**Absorbed ✅:** `.shape`, `m[i,j]`, `m[i]` row, `m[i][j]`, `len`/iterate, `.T`, `@` matmul, `v @ v`, `.tolist()`.
**Still raises ❌ (the bail-to-numpy gap):** elementwise/scalar `a + b` / `a - b` / `a * 2` / `2 * a`; slicing `m[:2]` / `m[:,0]` (column) / `v[:2]`; negative index `m[-1,-1]` / `v[-1]`.

These nine are *bread-and-butter numpy* — exactly the operations an LLM writes without thinking. While they raise, the carrier is a *partial* reflex sink: shape/index/matmul route through srmech, but arithmetic and slicing leak to numpy. **Goal-completing additions to `Mat`/`Vec`:** `__add__`/`__sub__`/`__mul__`/`__rmul__`/`__neg__`/`__truediv__` (elementwise + scalar, Class-K/Class-L honest under the hood — no `abs()`), slice-aware `__getitem__` (rows, columns `m[:,j]`, sub-blocks), and negative-index support. With those, `Mat`/`Vec` becomes a **near-total numpy-reflex sink** and the §2 STOP-list gets enforced *by the type system itself* rather than by discipline.

## Verdict
rc132 is **on track, nothing broken** — the carrier is now numpy-*shaped* for shape/index/matmul, and all our RBS-LM + genome surfaces pass. The remaining work is purely *goal-completing*: close the 9-idiom arithmetic/slice/negative-index gap so the carrier absorbs the numpy reflex completely instead of partially. Lodged as UPSTREAM §42.2.
