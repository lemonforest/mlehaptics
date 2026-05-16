/*
 * srmech_kepler.c — Class K primitive: equation-of-centre / pin-slot.
 *
 * Task #217 Phase C1 rc7 — Class K earns its C surface per the per-class
 * parity discipline. Continuous projection-shadow of the integer-cyclic
 * upstream (Class I cyclic groups + Class J prime-period). Uses libm
 * (sin / cos / atan2 / fabs); double precision throughout.
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
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <math.h>
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
    double x = pin_distance + pin_offset * cos(theta);
    double y = pin_offset * sin(theta);
    *out_phi = atan2(y, x);
    return SRMECH_OK;
}

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
    if (e < 0.0 || e >= 1.0) {
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
    double E = M_rad + e * sin(M_rad);
    for (uint32_t i = 0; i < max_iter; i++) {
        double f      = E - e * sin(E) - M_rad;
        double f_prime = 1.0 - e * cos(E);
        /* f_prime > 0 for e < 1 (no division-by-zero risk). */
        double delta = f / f_prime;
        E -= delta;
        if (fabs(delta) < tolerance) {
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
    if (e < 0.0 || e >= 1.0) {
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
        delta += SRMECH_KEPLER_EOC_COEFFS[k_idx] * e_power * sin(harmonic);
    }
    *out_delta_rad = delta;
    return SRMECH_OK;
}
