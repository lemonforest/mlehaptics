/*
 * srmech_loophd_family.c — native whole-array C peers for the HD loop
 * division family (MS#21 v0.7.0rc20; the Rosetta C/Python parity completion).
 *
 * THE ROSETTA DISCIPLINE. Per the srmech notebook §3.29.4–§3.29.5 ("one SSoT,
 * three coherences": meaning [MFO + notebook] : language [Python AND C source,
 * both human-readable] : machine code [Compiled C]), EVERY Python op needs a
 * C-SOURCE rendering so the compile step has a machine-code tier to produce.
 * `srmech_loop_bind_hd_f64` (rc11/rc17) gave the HD BIND its native peer; this
 * file completes the family — the HD conjugate, the Moufang inverse, the
 * LEFT-unbind, and the RIGHT-unbind — so NO HD loop op is Python-only (the
 * earlier "the HD variants need no C peer" stance is retired: a Python op with
 * no C-source rendering is a Rosetta with a glyph missing from one script).
 *
 * SHAPE. Each is the SHIPPED per-block symbol (srmech_loop_conj_f64 /
 * srmech_loop_inv_f64 / srmech_loop_bind_f64 in srmech_loopbind.c) applied over
 * NB independent dim-8 blocks (the block-diagonal direct sum ⊕, #811/F289).
 * This is the FAITHFUL transpile of the Python per-block wrappers (hdc.py
 * loop_{conj,inv,unbind,runbind}_hd) — bit-exact with them by construction (same
 * per-block ops, same order), collapsing the Python per-block loop into ONE
 * native call. No N-way SIMD here: the bind's F292 graft owns that
 * (srmech_loopbind_hd.c); these are memory-light scalar compositions whose heavy
 * step, where present, is the per-block product (already native).
 *
 * HONEST CASCADE SHAPE. conj is Class C (orientation flip, the imaginary
 * index-negation); inv is Class-K clean (the norm² gate lives inside
 * loop_inv, never abs()); unbind = conj(a)·b and runbind = b·conj(a) are the
 * two division peels of the non-commutative loop bind (Class C ∘ Class M).
 * NO new privileged primitive; NO new class.
 *
 * THREAD/STATE. Pure over caller buffers; `out` MUST NOT alias the inputs.
 * Fixed-size dim-8 stack locals only (no malloc); reentrant.
 *
 * JPL Power-of-Ten: Rule 1 (no goto / recursion — flat block loop, fixed call
 * DAG into the per-block symbols); Rule 2 (loops bounded by nb); Rule 3 (no
 * malloc); Rule 4 (≤60-line functions); Rule 5 (≥2 asserts per function);
 * Rule 7 (srmech_status_t throughout); Rule 10 (-Wall -Wextra -Wpedantic
 * -Werror / /WX). ABI: new symbols only → SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

/* The octonion / k=7 carrier dimension (division holds at dim <= 8). */
#define SRMECH_LOOP_DIM ((size_t)8)

/* Per-block HD conjugate: out[k] = conj(x[k]) over nb dim-8 blocks. The
 * direct-sum ⊕ of NB single-element loop_conj's (#811/F289). x, out are each
 * nb*8 doubles; `out` MUST NOT alias x. nb == 0 is a no-op. */
srmech_status_t srmech_loop_conj_hd_f64(const double *x, size_t nb, double *out)
{
    if (nb > 0u && (x == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(nb == 0u || x != NULL);
    assert(nb == 0u || out != NULL);
    for (size_t k = 0; k < nb; ++k) {
        const srmech_status_t rc = srmech_loop_conj_f64(
            &x[k * SRMECH_LOOP_DIM], SRMECH_LOOP_DIM, &out[k * SRMECH_LOOP_DIM]);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}

/* Per-block HD Moufang inverse: out[k] = conj(x[k]) / <x[k],x[k]>. A zero
 * block has no inverse — the per-block loop_inv returns SRMECH_ERR_BAD_INPUT,
 * which propagates here (the Python wrapper's fallback raises on it). x, out
 * are each nb*8 doubles; `out` MUST NOT alias x. nb == 0 is a no-op. */
srmech_status_t srmech_loop_inv_hd_f64(const double *x, size_t nb, double *out)
{
    if (nb > 0u && (x == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(nb == 0u || x != NULL);
    assert(nb == 0u || out != NULL);
    for (size_t k = 0; k < nb; ++k) {
        const srmech_status_t rc = srmech_loop_inv_f64(
            &x[k * SRMECH_LOOP_DIM], SRMECH_LOOP_DIM, &out[k * SRMECH_LOOP_DIM]);
        if (rc != SRMECH_OK) {
            return rc;  /* zero block -> SRMECH_ERR_BAD_INPUT, propagated */
        }
    }
    return SRMECH_OK;
}

/* Per-block HD LEFT-unbind (Moufang left-division): out[k] = conj(a[k])·b[k].
 * Recovers v from loop_bind_hd(a, v) = a[k]·v[k] for unit-per-block a. a, b,
 * out are each nb*8 doubles; `out` MUST NOT alias a or b. nb == 0 is a no-op. */
srmech_status_t srmech_loop_unbind_hd_f64(const double *a, const double *b,
                                          size_t nb, double *out)
{
    if (nb > 0u && (a == NULL || b == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(nb == 0u || (a != NULL && b != NULL));
    assert(nb == 0u || out != NULL);
    for (size_t k = 0; k < nb; ++k) {
        double aconj[SRMECH_LOOP_DIM];
        srmech_status_t rc = srmech_loop_conj_f64(
            &a[k * SRMECH_LOOP_DIM], SRMECH_LOOP_DIM, aconj);
        if (rc != SRMECH_OK) {
            return rc;
        }
        rc = srmech_loop_bind_f64(aconj, &b[k * SRMECH_LOOP_DIM],
                                  SRMECH_LOOP_DIM, &out[k * SRMECH_LOOP_DIM]);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}

/* Per-block HD RIGHT-unbind (Moufang right-division): out[k] = b[k]·conj(a[k]).
 * Recovers v from loop_bind_hd(v, a) = v[k]·a[k] for unit-per-block a — the
 * peel a left-fold sequence store needs (most-recent element off the right;
 * F-§12.2). a, b, out are each nb*8 doubles; `out` MUST NOT alias a or b.
 * nb == 0 is a no-op. */
srmech_status_t srmech_loop_runbind_hd_f64(const double *a, const double *b,
                                           size_t nb, double *out)
{
    if (nb > 0u && (a == NULL || b == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(nb == 0u || (a != NULL && b != NULL));
    assert(nb == 0u || out != NULL);
    for (size_t k = 0; k < nb; ++k) {
        double aconj[SRMECH_LOOP_DIM];
        srmech_status_t rc = srmech_loop_conj_f64(
            &a[k * SRMECH_LOOP_DIM], SRMECH_LOOP_DIM, aconj);
        if (rc != SRMECH_OK) {
            return rc;
        }
        rc = srmech_loop_bind_f64(&b[k * SRMECH_LOOP_DIM], aconj,
                                  SRMECH_LOOP_DIM, &out[k * SRMECH_LOOP_DIM]);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}
