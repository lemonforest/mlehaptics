/*
 * srmech_phase_coherent.c — C parity for srmech.amsc.cascade.phase_coherent_peak
 * (0.9.0rc112; issue #1234 Item 1d, the F1000->F1001->F1002 refinement):
 * the LIGHTWEIGHT matched-filter PEAK READ over a rung/mode ladder — the
 * READ counterpart to the full srmech_quaternion_dft / srmech_octonion_dft
 * (rc110/rc111) ENCODING transforms, kept API-DISTINCT from them.
 *
 * WHY THIS IS A SEPARATE OP, NOT THE FULL TRANSFORM (F1000 -> F1001 -> F1002).
 * For the RBS-LM single-rung fold the target's cross-rung response is a
 * SPIKE (each `next` is stored at ONE rung). F1001 measured that the full
 * complex QDFT (which coherently combines ALL rungs, twiddle included) is
 * WORSE than the peak read on that spike: a spike's spectrum is FLAT
 * (Parseval), so coherent combination gains nothing and forfeits the
 * max's off-rung noise-rejection. The optimal READ is the MATCHED FILTER
 * for a spike = the PEAK over the rung ladder (max phase-coherent energy),
 * which DISCARDS the off-rung noise. F1002 then settled it read-
 * independently (the elliptic code is circulant/generative but recall-
 * equivalent to independent keys — the transform's value is GENERATIVE
 * encoding, not read-amplification). So the READ path wants ONLY this
 * lightweight peak reduction — NOT the full transform.
 *
 * THE COMPUTATION (matched filter over a rung ladder). Given `n_rungs`
 * per-rung samples, each a `dim`-component real vector (a real scalar is
 * dim 1; a complex phase sample is the dim-2 pair (re, im); a quaternion /
 * octonion / Klein-4 sample is its dim-4 / dim-8 / general component
 * vector), the per-rung PHASE-COHERENT ENERGY is:
 *
 *   keys == NULL (identity matched filter): E_r = sum_i ladder[r][i]^2
 *       — the sample's own squared magnitude (the F1001 read: the ladder
 *       already holds the per-rung responses; the peak is the strongest-
 *       responding rung).
 *   keys != NULL (explicit per-rung template): c_r = sum_i keys[r][i]*
 *       ladder[r][i] (the real matched-filter correlation of the sample
 *       against its expected per-rung pattern), E_r = c_r * c_r.
 *
 * The PEAK is argmax_r E_r (ties -> lowest index). This is a LINEAR
 * matched-filter accumulation — NO twiddle, NO Fourier basis: the absence
 * of the twiddle IS what distinguishes the READ from the full transform
 * (F1001).
 *
 * HONEST CASCADE SHAPE. The per-rung energy is a Class-K real pin-slot
 * squared magnitude (sum of squares — never abs()); the argmax is a
 * Class-K magnitude comparison (strict `>`, lowest index wins). No sign
 * absolute value anywhere.
 *
 * BYTE-EXACT parity contract: the pure-Python mirror
 * (_phase_coherent_peak_pure) replicates this TU's float-op ORDER — the
 * inner accumulation runs i = 0..dim-1 left-to-right in a scalar, and the
 * argmax scan runs r = 0..n_rungs-1 — so FMA contraction must be OFF (a
 * fused multiply-add rounds once where mul+add round twice, diverging in
 * the last ulp). GCC in strict -std=c11 mode defaults -ffp-contract=off;
 * CLANG defaults ON (the rc110 macOS lesson), so the standard C11 pragma is
 * applied for clang; MSVC /fp:precise does not contract.
 *
 * THREAD/STATE. Pure functions over caller buffers; `out_scores` (if
 * given) MUST NOT alias `ladder` / `keys`. No shared static state;
 * reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; fixed call DAG.
 *   - Rule 2 (bounded loops)       : loops bounded by n_rungs * dim.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals.
 *   - Rule 4 (<=60 lines/func)     : the per-rung energy helper is split out.
 *   - Rule 5 (>=2 asserts/fn)      : pointer / dimension pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t throughout.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbol only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* BYTE-EXACT parity contract — FMA contraction OFF for clang (the rc110
 * lesson; see the file header). */
#if defined(__clang__)
#pragma STDC FP_CONTRACT OFF
#endif

/* The per-rung phase-coherent ENERGY (Class-K squared magnitude). `v` is a
 * `dim`-component sample; `g` is its matched-filter template, or NULL for
 * the identity (self-energy) filter. The accumulation order (i = 0..dim-1,
 * left-to-right in a scalar) IS the byte-exact parity contract with the
 * pure-Python mirror. No abs() — the energy is a sum of squares. */
static double srmech_pcp__energy(const double *v, const double *g, size_t dim)
{
    assert(v != NULL);
    assert(dim >= (size_t)1);
    if (g == NULL) {
        double e = 0.0;
        for (size_t i = 0; i < dim; ++i) {
            e += v[i] * v[i];
        }
        return e;
    }
    double c = 0.0;
    for (size_t i = 0; i < dim; ++i) {
        c += g[i] * v[i];
    }
    return c * c;
}

srmech_status_t srmech_phase_coherent_peak(
    const double *ladder, const double *keys, uint32_t n_rungs, size_t dim,
    uint32_t *out_index, double *out_score, double *out_scores)
{
    if (ladder == NULL || out_index == NULL || out_score == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_rungs == 0u || dim == (size_t)0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ladder != NULL && out_index != NULL && out_score != NULL);
    assert(n_rungs >= 1u && dim >= (size_t)1);
    uint32_t best_idx = 0u;
    double best_e = 0.0;
    for (uint32_t r = 0u; r < n_rungs; ++r) {
        const double *v = &ladder[(size_t)r * dim];
        const double *g = (keys != NULL) ? &keys[(size_t)r * dim] : NULL;
        const double e = srmech_pcp__energy(v, g, dim);
        if (out_scores != NULL) {
            out_scores[r] = e;
        }
        /* Class-K magnitude comparison; strict `>` keeps the LOWEST index on
         * a tie (byte-exact with the pure mirror's argmax). */
        if (r == 0u || e > best_e) {
            best_e = e;
            best_idx = r;
        }
    }
    *out_index = best_idx;
    *out_score = best_e;
    return SRMECH_OK;
}
