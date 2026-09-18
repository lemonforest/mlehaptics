/*
 * srmech_sqrt_internal.h -- the sticky, magnitude-normalised sqrt core shared
 * by srmech_rational_sqrt and srmech_sqrt_q61 (0.9.0rc476, `#T1188`).
 *
 * The core lives in srmech_sqrt.c because it reads that file's two-limb
 * isqrt128 and its IEEE exponent builder, and one copy of those is the rule.
 * The two EXPORTED symbols are re-expressed as projections over it: the double
 * projection rounds the core's odd root to 53 bits IN INTEGERS, and the Q61
 * projection hands back the core's (root, p) pair unchanged.
 *
 * The core ITSELF is static. What this header publishes is the DOUBLE
 * projection, srmech_sqrt_scaled, plus the one-step reciprocal built over it.
 * That is deliberate: a consumer that wanted a double from the raw (root, p)
 * pair would have to re-derive the 53-bit rounding, and a rounding rule
 * written twice is a rounding rule that will disagree once.
 *
 * Like srmech_trig_internal.h, srmech_ellbase_internal.h and
 * srmech_thetasum_internal.h this is NOT public API: no srmech.h exposure, no
 * ctypes binding, no ABI surface. The srmech_sqrt_ prefix is for link-level
 * uniqueness only. License: MIT.
 *
 * (That sentence deliberately stops where the precedent stops. A draft of this
 * header also claimed "no new exported symbol", which is measurably FALSE at
 * the link level: nm -D --defined-only counts 806 `T srmech_*` before this
 * file and 808 after, the two additions being the names declared below. The
 * precedent's own srmech_trig_kepler_q61 is likewise `T` in the shipped .so.
 * What is true, and what the sentence above says, is that nothing here reaches
 * srmech.h, the ctypes bindings or the ABI -- which is why adding it does not
 * bump. rc476 bumps because SERVED VALUES MOVE, not because of these.)
 *
 * NOT SEEN BY THE JPL SCANNERS. tests/test_jpl_audit.py::_c_files globs the
 * .c files under c/src and the .h files under c/include, so no rule reads THIS
 * file at all; and Rule 7's population is `srmech.h exports | same-file
 * statics`, so a DISCARDED status from either name below is invisible to that
 * detector in every file except the one that defines it. Every call site
 * therefore captures the status and either propagates it or asserts on it with
 * a stated reason, and widening _rule7_header_population to the private
 * headers under c/src is the drain test_jpl_audit.py already names as next.
 * The SRMECH_NODISCARD tags below still reach the gcc and clang guards for a
 * BARE-statement discard; they are empty under _MSC_VER.
 */
#ifndef SRMECH_SQRT_INTERNAL_H
#define SRMECH_SQRT_INTERNAL_H

#include "srmech.h"

#include <stdint.h>

/* *out = the CORRECTLY ROUNDED double nearest sqrt((num/den) * 2^e0).
 *
 * Internally: NORMALISE the radicand into [2^106, 2^109) so the floor root
 * always carries 54 or 55 bits (the step the shipped route lacked -- a
 * subnormal radicand reached the floor with a root as narrow as 28 bits and
 * the served double was wrong by up to 16,609,076 ulps); pin the halved
 * exponent's parity; root it; set a STICKY low bit when the radicand is not a
 * perfect square, which makes a rounding midpoint impossible; then round that
 * root to 53 bits IN INTEGERS, so the answer does not depend on the host's
 * uint64 -> double conversion or on the FPU rounding mode.
 *
 * Preconditions (the caller's): out non-NULL, num > 0, den > 0, and num no
 * more than 108 bits WIDER than den -- there is no bignum here, so a radicand
 * needing a negative shift is REFUSED rather than asserted away. (The Python
 * exact route reaches that case and takes its own negative-shift branch; the C
 * side has no exact-route peer that can reach it.) The result of a valid call
 * is never subnormal: sqrt of any positive finite double lies in
 * [2^-537, 2^512].
 *
 * Returns SRMECH_ERR_NULL_ARG on a NULL out, SRMECH_ERR_BAD_INPUT on a zero
 * num or den or on a radicand out of the declared width, SRMECH_OK otherwise.
 * On any refusal *out is set to 0.0 rather than left indeterminate.
 */
SRMECH_NODISCARD srmech_status_t srmech_sqrt_scaled(uint64_t num,
                                                    uint64_t den,
                                                    int32_t  e0,
                                                    double  *out);

/* *out = the CORRECTLY ROUNDED double nearest 1/sqrt(x), in ONE rounding.
 *
 * `1.0 / sqrt(d)` rounds twice and the second rounding is not repairable by
 * fixing the first. A double IS a dyadic rational mant*2^e, so its reciprocal
 * is the exact rational (1/mant)*2^-e and goes straight into the scaled root
 * above. Refuses x <= 0, NaN and +Inf with SRMECH_ERR_BAD_INPUT and *out = 0.0.
 */
SRMECH_NODISCARD srmech_status_t srmech_inv_sqrt(double x, double *out);

#endif /* SRMECH_SQRT_INTERNAL_H */
