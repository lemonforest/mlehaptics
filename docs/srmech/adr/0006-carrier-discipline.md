# ADR-0006: Carrier discipline — exactness, sign, format, and bounded memory

**Status:** ✅ Accepted (standing architecture policy; consolidates discipline previously held only in project memory).
**Date:** 2026-07-17.
**Authors:** Steven Kirkland + Claude.
**Supersedes:** none.
**Superseded-by:** none.

---

## 1. Context

srmech's carriers (`Q`, `srmech_bigint`, `Mat`/`Vec`/`HV`, the exact-poly family)
are the operand vocabulary dual to the A–N operators. Their whole value is
*exactness held until the last possible moment* and *bounded, edge-deployable
memory*. This ADR fixes the rules that keep a carrier from silently degrading into
a lossy float, an ALU `abs()`, a reshaped list, or an unbounded allocation.

## 2. Decision

1. **Stay rational; collapse to a decimal ONLY at the display boundary.** An op
   returns its exact carrier (`Q` / pair / `srmech_bigint`), never a bare `float()`.
   `float(x)` is an opt-in cast named at the call site for display/interop, never a
   no-op wrapper inside the cascade.

2. **ALU all the way, FPU last mile.** Default scalars to `Q`; keep cyclic/exact
   reduction in the integer ALU; a `float` enters only at the terminal projection.
   Never `float()`-wrap an already-exact value "to normalize".

3. **Sign is a Class-K pin-slot, never an ALU `abs()`.** Magnitude is an explicit
   sign-branch (`x if x >= 0 else -x`) / `cascade.magnitude`; sign re-application is
   Class C. For a float→ℚ snap of a possibly-negative value use the SIGNED cascade
   `cascade.best_rational_signed` — the bare Class-N `rational.best_rational`
   requires a non-negative numerator and will raise on `{-1,0,+1}` structure
   constants, negative charges, or a slightly-negative near-zero eigenvalue.

4. **Preserve carrier FORMAT.** A refactor (e.g. a library removal) must keep a
   `Mat` a 2-D `Mat` and a `Vec` a 1-D `Vec` — never silently flatten a carrier to a
   nested/py list. The format is part of the contract downstream ops rely on.

5. **Prefer carrier-native arithmetic over downcast-and-decline.** The carrier owns
   its whole domain (e.g. bignum owns overflow); do not add an int64 "fast path" that
   declines at its ceiling unless a benchmark proves it is actually faster — and test
   parity AT the ceiling, not only on unit-bounded inputs.

6. **Bounded arena; no unbounded allocation.** No srmech op allocates unbounded
   (gigabyte) memory by default; the edge commitment is a bounded arena + an honest
   decline. A working-RAM explosion / ballooning malloc-free arena bound is ALWAYS a
   red flag for a MISSED FIBER (a structural decomposition not taken), never a
   legitimately "dense" computation — hunt the fiber, do not raise the bound.

7. **Route optimizations through dataflow, never arithmetic substitution.** Optimize
   the *route* (evaluation order, caching, native dispatch), never the arithmetic;
   every optimization is carrier-preserving and bit-identical. (The cascade SVD's
   nullspace accuracy, for instance, is too low to route `np.linalg.matrix_rank`
   through it — value-faithful for large singular values only.)

## 3. Consequences

- Results are exact and reproducible across platforms (no accumulated float error,
  no cross-platform `abs()`/rounding divergence).
- Memory stays edge-deployable; a blow-up is treated as a design bug (missed fiber),
  not accommodated.
- Float parity tests are within-tolerance by nature (ADR-0006); everything else is
  byte-exact.

## 4. Sources (consolidated from project memory)

`[[feedback_stay_rational_collapse_only_at_display]]` ·
`[[user_stance_alu_all_the_way_fpu_last_mile]]` ·
`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` ·
`[[feedback_best_rational_needs_nonnegative_use_signed_for_floats]]` ·
`[[feedback_numpy_removal_must_preserve_carrier_format_mat_vec_not_lists]]` ·
`[[feedback_prefer_carrier_native_arithmetic_over_downcast_decline]]` ·
`[[feedback_native_fixedpoint_kernel_has_magnitude_ceiling_test_at_it]]` ·
`[[feedback_cyclic_reduction_is_integer_float_only_at_projection]]` ·
`[[feedback_no_op_allocates_unbounded_memory_bounded_arena_budget_plus_honest_decline]]` ·
`[[feedback_ram_explosion_means_missed_fiber_never_dense]]` ·
`[[feedback_optimizations_are_carrier_preserving_dataflow_not_arithmetic_substitution]]` ·
`[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]`
