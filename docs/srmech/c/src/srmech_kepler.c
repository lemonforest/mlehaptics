/*
 * srmech_kepler.c — Class K primitive: equation-of-centre / pin-slot.
 *
 * Task #217 Phase C1 rc7 — Class K earns its C surface per the per-class
 * parity discipline. Continuous projection-shadow of the integer-cyclic
 * upstream (Class I cyclic groups + Class J prime-period). Trig routes through
 * the Class-N cascade (srmech_sin / srmech_cos / srmech_atan2, rc43); the
 * convergence magnitude is a Class-K sign-branch (never fabs, rc46) — so this
 * file holds NO libm call. Double precision throughout.
 *
 * Three load-bearing operations:
 *
 *   - srmech_pin_slot           : era-appropriate Antikythera pin-and-slot
 *                                 transform (Freeth 2021 Supp S9 reconstruction)
 *   - srmech_kepler_solve       : Newton-Raphson on Kepler's equation
 *                                 M = E - e * sin(E)  (Kepler 1609 + Smith 1979)
 *   - srmech_equation_of_centre : Fourier-series principal-term-per-harmonic
 *                                 nu - M in eccentricity e (Brouwer & Clemence
 *                                 1961 §3.2 + Murray & Dermott 1999 §2.5)
 *
 * Per [[user_stance_kepler_shape_universal]] + PR #416 F2/F15/F17:
 * Kepler-equation algebra IS pin-slot composition. The bronze instantiates
 * Class K natively (pin-on-eccentric-disc + radial slot follower); the
 * universe instantiates the same algebra via gravitational dynamics. Same
 * Kepler-shape primitive cascade at different dimensional reaches per
 * [[user_stance_1d_t_as_storage_extraction]].
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Pin-slot transform        : Freeth (2021) Nature Sci Rep, Supp S9.
 *   - Kepler equation           : Kepler (1609) Astronomia Nova.
 *   - Newton-Raphson starter    : Smith (1979) Celestial Mech 19, 163.
 *   - Equation-of-centre series : Brouwer & Clemence (1961) Methods of
 *                                 Celestial Mechanics, §3.2; Murray &
 *                                 Dermott (1999) Solar System Dynamics,
 *                                 §2.5 eq 2.84-2.88.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — Newton-Raphson capped at max_iter
 *                              (caller; default 30); equation-of-centre
 *                              bounded at SRMECH_KEPLER_EOC_MAX_TERMS = 6
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK — entry-pointer assert +
 *                              precondition / post-condition invariant
 *                              (per [[feedback_jpl_rule_5_two_assert_habit]])
 *   - Rule 7 (return-value)   : OK as of 0.9.0rc473 — every srmech_status_t
 *                              returned inside this file is captured and
 *                              checked. It was VIOLATED through rc472 at
 *                              SEVEN sites, and this line read "OK —
 *                              srmech_status_t throughout" from the file's
 *                              first commit to rc472; every one of those
 *                              discards was already present. Rule 7 is about
 *                              CHECKING a returned value, not about declaring
 *                              a return type, and "srmech_status_t
 *                              throughout" answers the second question while
 *                              appearing to answer the first.
 *
 *                              It survived because Rule 7 has NO DETECTOR in
 *                              the pytest ratchet: tests/test_jpl_audit.py
 *                              mechanically ratchets Rules 1, 3, 4, 5, 8 and
 *                              9, and carries no RULE_7 symbol at all, so
 *                              this claim was never measured against
 *                              anything. Measured at rc473 by planting
 *                              warn_unused_result on the seven Class-N
 *                              callees and compiling c/src unmodified: 24
 *                              -Wunused-result diagnostics across 7 files,
 *                              the same file:line set the
 *                              `(void)srmech_<callee>(` grep finds, 0 other
 *                              diagnostics. Seven of the 24 were here.
 *
 *                              What replaces the missing detector for this
 *                              family is SRMECH_NODISCARD in srmech.h: the
 *                              seven Class-N callees and their seven clean
 *                              _q61 peers carry warn_unused_result, and on
 *                              gcc neither a bare call nor an explicit
 *                              (void) cast silences it, so re-introducing
 *                              any of the 24 is a -Werror build failure
 *                              rather than a quiet regression. That is a
 *                              compile-time guard on this ONE family, not a
 *                              Rule-7 detector over the whole library; the
 *                              general ratchet is still owed.
 *
 *                              Corrected rather than deleted, per the
 *                              in-place-correction precedent JPL_AUDIT.md
 *                              sets for its own headline.
 *   - Rule 10 (warnings clean): OK
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

/* Principal sin(kM) coefficient at lowest-order e^k contribution.
 * Index i = k-1 (i.e., coefficients[0] is the sin(M) coefficient at e^1).
 * Values per Brouwer & Clemence 1961 §3.2; cross-checked against Murray &
 * Dermott 1999 §2.5 Table 2.5 + eq 2.84-2.88. Capped at k = 6 to keep
 * coefficient verification straightforward; higher orders can extend the
 * table without ABI changes. */
static const double SRMECH_KEPLER_EOC_COEFFS[SRMECH_KEPLER_EOC_MAX_TERMS] = {
    2.0,                     /* k=1: 2 e            sin(M)  */
    5.0 / 4.0,               /* k=2: (5/4) e^2      sin(2M) */
    13.0 / 12.0,             /* k=3: (13/12) e^3    sin(3M) */
    103.0 / 96.0,            /* k=4: (103/96) e^4   sin(4M) */
    1097.0 / 960.0,          /* k=5: (1097/960) e^5 sin(5M) */
    1223.0 / 960.0           /* k=6: (1223/960) e^6 sin(6M) */
};

srmech_status_t srmech_pin_slot(double  theta,
                                double  pin_offset,
                                double  pin_distance,
                                double *out_phi)
{
    assert(out_phi != NULL);
    assert(pin_distance != 0.0 || pin_offset != 0.0);
    if (out_phi == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_phi = 0.0;
    /* Degenerate case: zero baseline AND zero pin offset. atan2(0, 0) is
     * implementation-defined; refuse rather than silently return 0. */
    if (pin_distance == 0.0 && pin_offset == 0.0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Standard Antikythera pin-and-slot: pin position relative to follower
     * axis is (d + i*cos(theta), i*sin(theta)); follower angle is the
     * angle to that point. Per Freeth 2021 Supp S9. */
    /* Class-N cascade trig (srmech_cos/sin/atan2), not libm — so the native
     * executable runs the same cascade as the Python source (rc43, C-transpile
     * triality coherence). */
    /* Each cascade call's status is CAPTURED and CHECKED (rc473, `#T1188`).
     * *out_phi was set to 0.0 above, so a refusal leaves a defined value that
     * is not an answer, and the caller learns which it is from the status. */
    double cs;
    double sn;
    srmech_status_t st = srmech_cos(theta, &cs);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sin(theta, &sn);
    if (st != SRMECH_OK) { return st; }
    double x = pin_distance + pin_offset * cs;
    double y = pin_offset * sn;
    return srmech_atan2(y, x, out_phi);
}

/* rc473 (`#T1188`): every srmech_sin / srmech_cos status inside the Newton
 * iteration is captured and checked. A refusal mid-iteration writes the
 * best-effort E reached so far and returns the callee's status — the same
 * partial-result shape this function already used for non-convergence
 * (SRMECH_ERR_OVERFLOW with the best-effort E at the bottom).
 *
 * Through rc472 those statuses were discarded, and the consequence was not a
 * NaN but a plausible number: srmech_sin(2^55) already refused and wrote 0.0,
 * so E was never moved off its M initial guess and the caller was handed
 * E == M with SRMECH_OK. Measured at rc472,
 * srmech_kepler_solve(2^55, 0.3, 1e-12, 20) -> (SRMECH_OK,
 * 3.602879701896397e+16), and 3.602879701896397e+16 IS 2^55. */
srmech_status_t srmech_kepler_solve(double    M_rad,
                                    double    e,
                                    double    tolerance,
                                    uint32_t  max_iter,
                                    double   *out_E_rad)
{
    assert(out_E_rad != NULL);
    assert(max_iter > 0 || e == 0.0);
    if (out_E_rad == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_E_rad = M_rad;
    /* rc473 repair (`#T1188`): spelled as the NEGATION of the accepted band,
     * not as a disjunction of rejections. `e < 0.0 || e >= 1.0` is NaN-BLIND —
     * both comparisons are false for a NaN, so the rejecting branch is not
     * taken and the NaN flows on. The Python peer already spells it
     * `if not (0.0 <= e < 1.0)` (kepler.py:151), which IS NaN-catching, so the
     * two projections differed in which inputs they serve — ADR-0009 §2.4. */
    if (!(e >= 0.0 && e < 1.0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (max_iter == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Circular orbit (e = 0): E = M exactly. */
    if (e == 0.0) {
        return SRMECH_OK;
    }
    /* Smith (1979) initial guess: E_0 = M + e * sin(M). Converges in 4-6
     * iterations for e < 0.5; e >= 0.95 may need >30 (caller's max_iter). */
    double sin_m;
    srmech_status_t st = srmech_sin(M_rad, &sin_m);
    if (st != SRMECH_OK) { return st; }   /* *out_E_rad stays M_rad (set above) */
    double E = M_rad + e * sin_m;
    for (uint32_t i = 0; i < max_iter; i++) {
        double sin_e;
        double cos_e;
        st = srmech_sin(E, &sin_e);
        if (st != SRMECH_OK) { *out_E_rad = E; return st; }
        st = srmech_cos(E, &cos_e);
        if (st != SRMECH_OK) { *out_E_rad = E; return st; }
        double f      = E - e * sin_e - M_rad;
        double f_prime = 1.0 - e * cos_e;
        /* f_prime > 0 for e < 1 (no division-by-zero risk). */
        double delta = f / f_prime;
        E -= delta;
        double adelta = (delta < 0.0) ? -delta : delta;   /* Class-K magnitude, not fabs */
        if (adelta < tolerance) {
            *out_E_rad = E;
            return SRMECH_OK;
        }
    }
    /* Did not converge within max_iter; return best-effort E with overflow
     * status so caller can decide (tighten tolerance, raise max_iter, or
     * accept the partial result). */
    *out_E_rad = E;
    return SRMECH_ERR_OVERFLOW;
}

/* rc473 (`#T1188`) — THE row this rc is named for. 4 * (2^53 + 1) is exactly
 * 2^55, which srmech_sin already refused at rc472, and the sin call inside
 * the harmonic loop discarded that refusal: the C projection answered
 * (SRMECH_OK, -0.08984990210223018) for an input the Python projection
 * raised ValueError on. The status is now propagated; *out_delta_rad stays
 * at the 0.0 set on entry, which is a defined value and not an answer. */
srmech_status_t srmech_equation_of_centre(double    M_rad,
                                          double    e,
                                          uint32_t  n_terms,
                                          double   *out_delta_rad)
{
    assert(out_delta_rad != NULL);
    assert(n_terms <= SRMECH_KEPLER_EOC_MAX_TERMS);
    if (out_delta_rad == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_delta_rad = 0.0;
    /* rc473 repair (`#T1188`): the SAME NaN-blind spelling as kepler_solve's,
     * and here it was reachable. Measured on the rc473 branch head before this
     * repair, native cell, ABI 26: the C symbol answered
     * srmech_equation_of_centre(0.7, NaN, 4) -> status 0 (SRMECH_OK), out=nan
     * while kepler.equation_of_centre(0.7, nan, 4) raised
     * "e must satisfy 0 <= e < 1; got nan". kepler_solve was saved only
     * incidentally (a NaN e poisons E and srmech_sin now refuses NaN); this
     * one had no such backstop, because e never reaches a callee that
     * validates it — it is only ever MULTIPLIED. */
    if (!(e >= 0.0 && e < 1.0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_terms == 0 || n_terms > SRMECH_KEPLER_EOC_MAX_TERMS) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Sum principal-term-per-harmonic: c_k * e^k * sin(k * M) for k = 1..n.
     * e_power accumulates e^k iteratively to avoid pow() calls. */
    double delta = 0.0;
    double e_power = 1.0;
    for (uint32_t k_idx = 0; k_idx < n_terms; k_idx++) {
        e_power *= e;
        double harmonic = (double)(k_idx + 1) * M_rad;
        double sin_h;
        srmech_status_t st = srmech_sin(harmonic, &sin_h);
        if (st != SRMECH_OK) { return st; }
        delta += SRMECH_KEPLER_EOC_COEFFS[k_idx] * e_power * sin_h;
    }
    *out_delta_rad = delta;
    return SRMECH_OK;
}
