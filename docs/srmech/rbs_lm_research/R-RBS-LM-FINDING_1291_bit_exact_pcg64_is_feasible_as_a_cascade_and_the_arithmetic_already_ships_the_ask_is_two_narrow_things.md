# F1291 — **yes, a bit-exact PCG64 is a cascade of the 14 — and srmech ALREADY ships the arithmetic.** The LCG step composes from shipped Class-I ops (`mod_add(mod_mul(state, mult, m), inc, m)` equals raw modular arithmetic, verified). So Tier 3 does **not** need arithmetic-in-TOML; it needs **two narrow srmech extensions**: a 128-bit-capable `mod_mul` (the primitive is uint64-capped but `bigint_mul_c` already exists natively) and registering the Class-I modular family as chain-reachable cascade ops. With those, Tier 3 becomes a **rename with zero value change**, not a re-run of 184 files.

**User (2026-07-21):** *"we can't use the srmech make_class to create a mersenne twister and pcg64 rng operations?"* → then *"what about creating the arithmetic in the TOML, or we need to make an srmech ask for this to happen as part of the make_class() tooling?"*

## The layering, made precise
| layer | can it hold a new algorithm? | |
|---|---|---|
| **`make_class` TOML** | **no** | binds existing ops by dotted path (`One.dim → cascade.one.one_dim`); no arithmetic, no control flow |
| **`dsl.chain`** | composes ops | the composition layer — but only **15** ops are chain-registered, and the modular family is not among them |
| **Class-I ops** (`cyclic.mod_mul`, `mod_add`, `mod_pow`) | **the arithmetic already exists** | verified below |
| **native** (`bigint_mul_c`) | arbitrary-precision multiply, shipped | the 128-bit capacity is already there |

**So "put the arithmetic in the TOML" is the wrong layer** — it would duplicate ops that already exist one level down. The arithmetic isn't missing; the *reach* to it from the declarative layer is.

## The op is a cascade — demonstrated
PCG64-XSL-RR-128/64 is: `state ← state·mult + inc (mod 2¹²⁸)`, then `rotate_right((state≫64) ⊕ (state & 2⁶⁴−1), state≫122)`. Every operation is **MULTIPLY / ADD / XOR / SHIFT / ROTATE** — integer, Class I (cyclic/modular) + Class K (sign-free shifts). No float, no array, no numpy. The prototype runs deterministically and produces full-width u64 output.

And the step composes from **shipped** srmech ops within uint64:
```python
cyclic.mod_add(cyclic.mod_mul(state, mult, m), inc, m) == (state*mult + inc) % m   # True (rc299)
```

## The two gaps — both narrow, neither an "arithmetic language"
1. **`cyclic.mod_mul` is capped at uint64** — `_ensure_uint64`: *"parity surface is bounded by 2⁶⁴ − 1"* — and PCG64 needs a **128-bit** modulus. But srmech ships `_native.bigint_mul_c` (arbitrary-precision, native), so **the capacity exists; this is a surface bound, not an algorithm gap.** Ask: a 128-bit-capable modular multiply routed through `bigint_mul` above 64.
2. **The Class-I modular family isn't chain-registered** — only 15 cascade ops are exposed to `chain()`/TOML. Ask: register `mod_mul`/`mod_add`/`mod_pow` so an RNG cascade can be *declared* via `make_class` rather than hand-coded.

## Two gates that this environment cannot clear — stated so "feasible" is not misread as "done"
- **The constants must be ATTESTED.** PCG64's multiplier and XSL-RR rotation schedule are specific published values. Recalling them is the citation-hallucination failure MPM exists against, and a wrong constant yields a plausible stream that is silently not PCG64. The prototype makes them **required parameters with no default** and refuses to guess.
- **Parity is UNVERIFIABLE here.** numpy will not install on Python 3.14 and no other interpreter is present, so there is no reference stream to diff against. Matching `np.random.default_rng(seed)` also needs numpy's **SeedSequence** entropy-mixing reproduced — a second published algorithm with the same attestation requirement.

## What this changes about F1290
F1290 framed Tier 3 as *"accept that 184 files change their numbers, or keep numpy."* **This finding adds a third option that is strictly better than both:** a bit-exact PCG64 makes the migration a rename with **zero** value change — nothing re-runs, nothing is invalidated, numpy leaves the RNG path. That is worth the upstream work, which is why the user's question was the right one.

## The path (the F1286 route, already proven for CDRegister / eulerian_path / recover_check)
prototype the op here → **extract** the attested constants from the reference → verify against published PCG64 test vectors → land `mod_mul_wide` + chain-register the modular family → upstream `srmech.amsc.cyclic.pcg64_*` → declare `PCG64` via `make_class` → Tier 3 renames, numpy-free.

**Mersenne Twister is easier:** Python's own `random` already implements it, bit-exact with numpy's *legacy* `RandomState` (not `default_rng`). So any site that only needs MT can migrate to `random.Random(seed)` today — worth a per-site check of which generator a file actually depends on.

Filed as UPSTREAM_NOTES §110. Composes **F1290** (Tier 3, now with a third path), **F1286** (prototype→upstream route), **F1259** (RNG regimes), `[[feedback_pdf_extraction_citation_discipline]]` (Gate 1), `[[feedback_introspect_srmech_before_python_dispatch]]`.
