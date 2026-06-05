/*
 * srmech_kuramoto.c — C-parity for the Kuramoto coupled-oscillator
 * forward-Euler step (#778 follow-on; MS#20 rc9).
 *
 * Closes a C/Python parity gap: the dispatch-clock / coupled-oscillator
 * Euler integration the spectral-research arc hand-rolled in Python
 * (F141 / F231 / R-95 / F234) had NO native srmech_* primitive — so
 * srmech could not run the Kuramoto step under its full-parity
 * commitment (the library must run on a microcontroller with NO host
 * Python). This adds the native step.
 *
 * THE STEP. One forward-Euler step of the canonical Kuramoto model
 * (Kuramoto 1975; Acebrón et al. 2005, Rev. Mod. Phys. 77:137):
 *
 *     dθ_i/dt = ω_i + (K/N) Σ_j sin(θ_j − θ_i)
 *     θ_i(t+dt) = θ_i(t) + dt·[ ω_i + (K/N) Σ_j sin(θ_j − θ_i) ]
 *
 * HONEST CASCADE SHAPE. This composes existing class operations, it is
 * NOT a new privileged primitive: Class I (cyclic phase θ on the
 * circle) + the sin coupling (the Class-N rational trig cascade via
 * srmech_sin — rc44; the native executable runs the cascade, not libm,
 * the same C-transpile-triality routing srmech_kepler.c took at rc43)
 * + a sum-reduce over j + a Class-C Euler add (θ + dt·f). No abs().
 *
 * THREAD/STATE. Pure function over caller buffers — reads θ/ω, writes
 * the caller-supplied `out` (which MUST NOT alias θ or ω). No shared
 * static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : early returns only.
 *   - Rule 2 (bounded loops)  : the i/j loops are bounded by n.
 *   - Rule 3 (no malloc)      : caller buffers only.
 *   - Rule 4 (≤60 lines/func) : the per-oscillator coupling sum is
 *                               factored into its own helper.
 *   - Rule 5 (≥2 asserts/fn)  : pointer / aliasing pre-conditions.
 *   - Rule 7 (return-value)   : srmech_status_t throughout.
 *   - Rule 10 (warnings clean): -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbol only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

/* The mean-field coupling sum Σ_j sin(θ_j − θ_i) for oscillator i.
 * Reads ONLY the shared read-only θ array; no writes (reentrant). */
static double srmech_kuramoto__coupling_sum(
    const double *theta, size_t n, size_t i)
{
    assert(theta != NULL);
    assert(i < n);
    double acc = 0.0;
    for (size_t j = 0; j < n; ++j) {
        double sv;
        (void)srmech_sin(theta[j] - theta[i], &sv);   /* Class-N cascade, not libm */
        acc += sv;
    }
    return acc;
}

srmech_status_t srmech_cascade_kuramoto_step_f64(
    const double *theta, const double *omega, size_t n,
    double coupling_k, double dt, double *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && (theta == NULL || omega == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(n == 0 || (theta != NULL && omega != NULL));
    /* Mean-field normalisation K/N (n == 0 ⇒ no oscillators ⇒ no-op). */
    const double inv_n = (n > 0) ? (coupling_k / (double)n) : 0.0;
    for (size_t i = 0; i < n; ++i) {
        const double coupling = srmech_kuramoto__coupling_sum(theta, n, i);
        out[i] = theta[i] + dt * (omega[i] + inv_n * coupling);
    }
    return SRMECH_OK;
}

/* The GENERALISED Kuramoto-Sakaguchi coupling sum for oscillator i:
 *   Σ_j A_ij · sin(θ_j − θ_i − α)
 * `adjacency` is row-major n×n (A_ij weights j's influence on i; a
 * non-symmetric matrix expresses DIRECTED coupling, a Laplacian expresses
 * graph-structured coupling). When `adjacency == NULL` every weight is the
 * uniform mean-field `inv_n = K/N`. `alpha` is the Sakaguchi phase
 * frustration. Reads ONLY read-only arrays; no writes (reentrant). */
static double srmech_kuramoto__general_sum(
    const double *theta, const double *adjacency, size_t n, size_t i,
    double inv_n, double alpha)
{
    assert(theta != NULL);
    assert(i < n);
    double acc = 0.0;
    for (size_t j = 0; j < n; ++j) {
        const double w = (adjacency != NULL) ? adjacency[i * n + j] : inv_n;
        double sv;
        (void)srmech_sin(theta[j] - theta[i] - alpha, &sv);   /* Class-N cascade */
        acc += w * sv;
    }
    return acc;
}

srmech_status_t srmech_cascade_kuramoto_step_general_f64(
    const double *theta, const double *omega, size_t n,
    const double *adjacency, double coupling_k, double alpha,
    const double *pin_anchor, const double *pin_strength,
    double dt, double *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && (theta == NULL || omega == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(n == 0 || (theta != NULL && omega != NULL));
    /* Mean-field fallback weight when `adjacency == NULL`. */
    const double inv_n = (n > 0) ? (coupling_k / (double)n) : 0.0;
    for (size_t i = 0; i < n; ++i) {
        double f = omega[i] + srmech_kuramoto__general_sum(
            theta, adjacency, n, i, inv_n, alpha);
        if (pin_anchor != NULL) {
            /* Per-oscillator pinning toward anchor ψ_i: + p_i·sin(ψ_i − θ_i).
             * NULL pin_strength ⇒ unit strength. No abs(). */
            const double p = (pin_strength != NULL) ? pin_strength[i] : 1.0;
            double sv;
            (void)srmech_sin(pin_anchor[i] - theta[i], &sv);   /* Class-N cascade */
            f += p * sv;
        }
        out[i] = theta[i] + dt * f;
    }
    return SRMECH_OK;
}
