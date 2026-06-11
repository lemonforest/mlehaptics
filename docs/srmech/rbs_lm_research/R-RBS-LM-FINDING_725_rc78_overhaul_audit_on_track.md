# Finding 725 — srmech 0.7.5rc78 overhaul audit: ON TRACK (typed `One` + `to_scalar`, cascade de-dup, §39 generator; numpy-removal in progress)

**Script:** `R-RBS-LM-OVERHAULAUDIT_rc78_the_one_typed_to_scalar_dedup_numpy_removal.py`
**Status:** VERIFIED (srmech 0.7.5rc78, TestPyPI, numpy-free venv) — review requested by the user
**User direction:** *"doing srmech overhaul … numpy removal … duplicate items from before we added the_one … TOML
config for classes giving names of familiarity … a `to_scalar` for when someone doesn't want matrix output. Pull
latest and make sure we're on the right track / makes sense."*

## Verdict: on track, and the choices make sense

| overhaul claim | rc78 reality (verified) | read |
|---|---|---|
| **typed the_one + `to_scalar`** | `the_one(σ, θ_num, θ_den, terms) -> One = S(σ,θ)`; **σ=±1 is chirality** (Class-C; rejects σ=2), θ is the angle. `One` carries the Hurwitz structure (Fano planes / block dims / grammar slots) and projects: **`to_scalar` → exact rational `(num,den)`, numpy-FREE** (optional `as_float`); `to_flat_rational` numpy-free; **`to_matrix`/`to_numpy` = the numpy LIFT** | ✅ **right.** "`to_scalar` for when someone doesn't want matrix output" = the numpy-free **exact** projection vs the numpy matrix lift. On-thesis: exact rational = the substrate truth (Class N); the matrix is the lift. σ=chirality, θ=angle is de-magicked (attested, not magic) |
| **de-dup ("duplicate items from before the_one")** | `cascade` is now a **package** of 12 focused modules organised around `one.py`: one / coupled / exact_dft / hypercomplex_dft / matrix_cascades / spectral_cascades / atoms / compose / cayley_dickson / hamming / parallel / sedenion_register | ✅ the multiple DFT/coupler ops consolidated around the typed the_one. Sensible |
| **class-TOML naming ("names of familiarity")** | ships `['Genome', 'Hurwitz']`; bring-your-own still registers live | ✅ working + expanding |
| **(our §39 wishlist) class generator** | `srmech.dsl.generate_class_descriptor(name, *, fields, methods, doc, kind) -> str` — *"the inverse of make_class"*; **round-trips** (generate → register → load as a class) | ✅ **delivered** — closes the §39 introspection loop |

**Genome regression clean** (the cascade restructure didn't break the storage surface — partition round-trip reversible).

## The one in-progress item (the numpy removal isn't finished)

`laplacian.fiedler_vector` **still hard-requires numpy** (`np.asarray` on `None` in the numpy-free venv — the same
gap as rc50/F724). The *pattern* is right (numpy-free **exact** path + numpy **lift**, exactly what `One` and
`jacobi_eigvals` now do), but the sweep hasn't reached the residual **Class-L spectral functions**. Concrete next
step in the numpy-removal: give `fiedler_vector` (and any sibling spectral fns) the **numpy-free exact / native
dispatch that `jacobi_eigvals` already has** — then the full Class-L spectral layer runs numpy-free, not just the
imports. (`qm.*` staying scientific-tier is by design; `One.to_matrix` needing numpy is by design — the lift.)

## Wishlist status (the user: "we don't have our wishlist items yet")

- **§38** native A-N binding — ✅ (rc42 / F716)
- **§40** U1 text→graph ops at the bar — ✅ (rc50 / F723)
- **§39** class generator from introspection — ✅ (rc78, this audit)
- **§41** genome persistence (disk-paged, bounding-tracked) — ⏳ not yet (just scoped this session)

**3 of 4 landed.** The remaining one (§41) is the persistence/introspection store; plus the numpy-removal sweep
(fiedler_vector et al.) to finish the Class-L spectral tier.

**Honest note:** this is a read-only audit on a small numpy-free venv; it confirms the *shape* is right and the
named pieces exist + work, not a full regression of all 287 ops. The exact-rational `to_scalar` (no float loss, σ
attested) and the de-dup around the typed `One` are the strongest signals that the overhaul is converging, not
sprawling.

**Composes:** §38/§39/§40/§41 (the wishlist) · F716 (genome surface) · F723/F724 (U1 + the fiedler-numpy gap first
seen) · F683/F684 (the_one coupler this types) · F708/F640 (no-magic — σ/θ attested). srmech 0.7.5rc78. Held open (F394).
