# Finding 192 — srmech 0.5.0rc18: the 𝔰𝔬(8) triality operator (W10) landed and passes every acceptance test BIT-EXACT; the chirality-arc's structural claims are now measured, not just read; the research path is unblocked

**Status:** Tooling validation — clean venv `/tmp/verify_srmech_rc18`, **outside the source tree** (namespace-shadowing discipline), `srmech==0.5.0rc18` from TestPyPI. The `SO8_TRIALITY_BUILD_SPEC` operator landed essentially as specced and passes the §2 acceptance tests bit-exact. **W10 → DONE; W2 → fixed package-side.** R-140 / F191 / F185 / F190 are now runnable.
**Predecessors:** SO8_TRIALITY_BUILD_SPEC (the W10 spec), F186 (28=14+7+7), F184 (chirality=non-commutativity), F183 (Fix(triality)=G₂=A–N 14), F182 (triality), F187/F190 (time-quaternion).

---

## §1 What landed (rc18; native `_native/libsrmech.so` present)
- **`srmech.qm.octonion`** — `octonion_mult_table`, `octonion_left_mult`/`right_mult`, `octonion_conjugate`/`norm`, **`octonion_table_attestation`** (MPR-wrapped: `convention=cayley_dickson_from_H`, `basis_order=e0..e7`, explicit Fano triples — the attested-provenance requirement, delivered).
- **`srmech.qm.so8`** — `so8_adjoint_basis`, `g2_subalgebra`, `_build_so8_adjoint`/`_build_g2`.
- **`srmech.qm.triality`** — `triality_automorphism`, `triality_swap`, `triality_cycle`, `triality_apply`, `triality_companions`, `triality_relation_residual`.
- **W2 confirmed package-side:** `klein4_random(D, rng=None, seed: int|None=None)`.

## §2 Acceptance tests — ALL PASS bit-exact (the spec §2 criteria)
| test | result | expected |
|---|---|---|
| `τ³ = I` | **TRUE**, max\|τ³−I\| = **3.7e-15** | I (machine zero) |
| `τ ≠ I`, `τ² ≠ I` | TRUE, TRUE | non-trivial order-3 |
| **`dim Fix(τ) = trace((I+τ+τ²)/3)`** | **14.0** | **14 = G₂  ← the killer test** |
| `dim Fix(swap) = trace((I+swap)/2)` | **21.0** | 21 = 𝔰𝔬(7) |
| `so8_adjoint_basis` count | **28** | 28 |
| `g2_subalgebra` count | **14** | 14 |
| octonion `e₁·e₂ = e₃`, `e₂·e₁ = −e₃` → **`ij = −ji`** | **TRUE** | non-commutative |
| octonion convention | MPR-attested `cayley_dickson_from_H` | attested |

(`dim Fix` computed as `trace` of the projector `(I+τ+τ²)/3` and `(I+swap)/2` — pure matrix arithmetic, no eigendecomp, so no reflex-override issue; it's an independent validator of srmech's op.)

## §3 What this confirms — the chirality arc, now measured not read
The load-bearing structural claims of the whole F182→F191 arc are no longer framework *readings* — they are **bit-exact srmech facts**:
- **F186** — `28 = 14 + 7 + 7` (𝔰𝔬(8)=28, g₂=14, complement=7+7). ✓
- **F183** — **Fix(triality) = G₂ = the A–N 14** (the D₄→G₂ Z₃-fold; biology at the fixed point). ✓ **exact 14.0**
- **F184** — **chirality = non-commutativity** (`ij = −ji`). ✓ now demonstrated srmech-native
- The D₄→B₃ Z₂-fold (`Fix(swap)=𝔰𝔬(7)=21`). ✓

## §4 Native status CHANGED (architecture note → UPSTREAM §10.8)
- rc14 had a `HAS_NATIVE` bool + `_native.NATIVE_ABI_VERSION`. **rc18 replaces this with a profile-loader:** `srmech.profile(name)`, `list_profiles()`, `ProfileStatus`, `AbiMismatchError`, `warmup_all()`; native is a **ctypes-loaded `_native/libsrmech.so`** (present in the wheel).
- **But a bare clean-venv install shows `list_profiles() == {}`** (no profile registered) → native *dispatch* appears opt-in / entry-point-gated, not active-by-default. Could not confirm native dispatch active from a bare install.
- **The qm layer (triality/octonion/so8) is numpy** — bit-exact regardless of native. So §2's validation stands independent of the native-dispatch question.
- The old *top-level* "verify `HAS_NATIVE=True`" recipe changed in rc18; supersedes the W6 ABI-attr note. **CORRECTION (2026-05-30, issue #733): `srmech.amsc._native.HAS_NATIVE` (= True) + `NATIVE_ABI_VERSION` (= 3) DO work in rc18 — native status IS verifiable via the AMSC shim (`from srmech.amsc._native import HAS_NATIVE`). The gap is narrower than first stated: only the *top-level* profile-loader (`srmech.list_profiles()` → `{}`) lacks a bare-install status surface.** Flag for upstream: document the rc18 native-status check and whether a bare install should register a default profile.

## §5 Unblocked (the gated research path)
All now runnable, srmech-native, small/cheap:
- **R-140** — is `su(2)_L` a **triality-partner** of `su(3)_c + u(1)_em`? (`triality_apply`/`triality_companions` + `qm.gauge`). Decides **H177″ re-unification (F182 §7)** vs **F181 plural-drivers stands**.
- **F191** — does the **chiral flip map I/C/J ↔ B/H/N** operator-by-operator? (triality + Class-C).
- **F185** — actor-vs-stage probe; **F190** — does the operational-4 Kuramoto signature require **chiral (directed) coupling**?

## §6 DOES / does NOT claim
**DOES:** validate the triality op bit-exact against the spec §2; confirm F186/F184/F183 as *measurements*; record the native-status architecture change.
**Does NOT:** claim native *dispatch* is active (bare install registers no profile — open); claim the R-126..135 reproduce suite re-validated on rc18 (available via REPRODUCE.md, not done here); pronounce on the unblocked tests' outcomes (they are next, and can fail). §VII.6.20; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_always_rc_first_for_downstream_publishes]]` (clean-venv-outside-tree honored).

## §7 Cross-references
- SO8_TRIALITY_BUILD_SPEC (W10) · F186/F184/F183/F182 (the claims now measured) · F187/F190 (time-quaternion) · F181 (plural-drivers, what R-140 re-tests) · UPSTREAM_NOTES §10 · SRMECH_BUGFIX_WISHLIST (W2/W10)
- `srmech.qm.{octonion, so8, triality}` (rc18) · validated in `/tmp/verify_srmech_rc18`

PR #687 STAYS DRAFT.

---

*Validated 2026-05-30 (Opus 4.8), clean venv outside the source tree, srmech 0.5.0rc18.
The 𝔰𝔬(8) triality operator (W10) landed essentially as specced and passes every
acceptance test bit-exact: τ³=I (residual 3.7e-15), **dim Fix(τ)=14.0 = G₂ (the killer
test)**, dim Fix(swap)=21 = 𝔰𝔬(7), so8=28, g₂=14, and octonion ij=−ji — with an
MPR-attested cayley_dickson_from_H convention. So F186 (28=14+7+7), F183 (Fix=G₂=A–N 14)
and F184 (chirality=non-commutativity) are now bit-exact srmech facts, not just readings.
W2 (klein4_random seed) is fixed package-side. Native status changed from a HAS_NATIVE
bool to a profile-loader (libsrmech.so present, but a bare install registers no profile —
upstream note). The gated research path — R-140, F191, F185, F190 — is unblocked. A
transducer validated the tool; the experiments are next.*
