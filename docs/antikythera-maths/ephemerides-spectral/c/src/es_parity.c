/* es_parity.c — C/Python parity Tier 1 (v0.6.0, ABI v3)
 *
 * Two new entry points so every encoder-touching Python bridge method
 * has a matching C path:
 *
 *   es_breathing_modulation — exposes the resonant-pair phase residue +
 *     integer-cosine-LUT modulation factor at a single JD. The math
 *     is the same as the breathing inner loop in es_encode.c, but
 *     evaluated at one (jd, body_a, body_b, n_a, n_b) without running
 *     the full encode.
 *
 *   es_find_syzygies — fixed-period synodic/draconic month enumeration.
 *     No encoder calls; pure modular arithmetic mirroring
 *     `_research/syzygy_window.py` 1:1.
 *
 * The parity smoke test (python/tests/test_parity_smoke.py) pins
 * agreement between the Python and C paths.
 */

#include "ephemerides_spectral.h"

#include <math.h>
#include <stddef.h>
#include <stdint.h>

/* ──────────────────────────────────────────────────────────────────
 * Anchor constants — SSOT lives in
 * python/ephemerides_spectral/_research/syzygy_window.py
 *
 * Mirrored here as static const so the C path produces byte-identical
 * output. If the Python anchors ever change, the parity smoke test
 * will catch the drift.
 * ────────────────────────────────────────────────────────────────── */

static const double SYNODIC_MONTH_DAYS              = 29.530588853;
static const double DRACONIC_MONTH_DAYS             = 27.212220817;
static const double LUNAR_REFERENCE_NEW_MOON_JD_TDB = 2451550.1;
static const double SOLAR_ECLIPSE_REFERENCE_JD_TDB  = 2451401.6916;

/* Modulus for ES_MODULO ops — only needed in the encode path; we
 * read phases via es_encode_state which already returns reduced
 * uint32 values. Keep this file dependency-light.
 */

/* ──────────────────────────────────────────────────────────────────
 * es_breathing_modulation
 * ────────────────────────────────────────────────────────────────── */

es_status_t es_breathing_modulation(double delta_t_days,
                                    size_t body_idx_a,
                                    size_t body_idx_b,
                                    int n_a,
                                    int n_b,
                                    uint32_t *out_phase,
                                    int32_t *out_cos_q14,
                                    double *out_modulation)
{
    if (out_phase == NULL || out_cos_q14 == NULL || out_modulation == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (!isfinite(delta_t_days)) {
        return ES_ERR_NON_FINITE_INPUT;
    }
    if (body_idx_a >= ES_N_BODIES || body_idx_b >= ES_N_BODIES) {
        return ES_ERR_INVALID_INDEX;
    }

    /* Encode the full system at delta_t and pluck the two body phases.
     * We call the public es_encode_state so that any patches active in
     * the registry contribute to phi_a / phi_b — matches the Python
     * bridge which calls inst.encode_state and then indexes into the
     * returned array. (The Python path calls _get_bip(...).encode_state
     * which honours the patch overlay too.)
     */
    uint32_t phases[ES_N_BODIES];
    es_status_t rc = es_encode_state(delta_t_days, phases);
    if (rc != ES_OK) {
        return rc;
    }

    const uint32_t phi_a = phases[body_idx_a];
    const uint32_t phi_b = phases[body_idx_b];

    /* Resonant phase: (n_a * phi_a - n_b * phi_b) mod 2^32.
     * Free uint32 overflow gives the cyclic-group reduction.
     * Mirrors es_encode.c's `res_phase = n_a * phi_a - m_b * phi_b`.
     */
    const uint32_t res_phase = (uint32_t)n_a * phi_a - (uint32_t)n_b * phi_b;

    *out_phase    = res_phase;
    *out_cos_q14  = es_cos_lut(res_phase, 1u);
    /* Default 10% breathing depth — matches Python bridge.
     * modulation = 1.0 + 0.1 * (cos_q14 / ES_COSINE_LUT_AMP)
     */
    *out_modulation = 1.0 + 0.1 * ((double)(*out_cos_q14) / (double)ES_COSINE_LUT_AMP);
    return ES_OK;
}

/* ──────────────────────────────────────────────────────────────────
 * es_find_syzygies
 *
 * Direct port of `_research/syzygy_window.py::find_syzygies`. Walks
 * new-moon multiples of the synodic month from the J2000-anchored
 * reference; for each, optionally also the half-cycle (full moon);
 * computes the draconic-month phase relative to the August 1999
 * solar-eclipse anchor; emits a candidate when the geometric score
 * is below threshold.
 * ────────────────────────────────────────────────────────────────── */

/* (a mod m) wrapped into [0, m) for positive m, matching Python's % */
static double pos_mod(double a, double m)
{
    double r = fmod(a, m);
    if (r < 0.0) r += m;
    return r;
}

/* min(|x|, |1-x|) wrapped into [0, 0.5], matching the Python
 * _modular_distance(x, 0.0) = min(|x|, 1-|x|).
 */
static double modular_distance_to_zero(double x)
{
    double a = fabs(x);
    double b = fabs(1.0 - a);
    return (a < b) ? a : b;
}

es_status_t es_find_syzygies(double jd_lo,
                             double jd_hi,
                             int kind,
                             double threshold,
                             size_t max_candidates,
                             es_syzygy_t *out_buf,
                             size_t out_capacity,
                             size_t *out_count)
{
    if (out_buf == NULL || out_count == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (!isfinite(jd_lo) || !isfinite(jd_hi)) {
        return ES_ERR_NON_FINITE_INPUT;
    }
    if (kind != ES_SYZYGY_KIND_FILTER_SOLAR
        && kind != ES_SYZYGY_KIND_FILTER_LUNAR
        && kind != ES_SYZYGY_KIND_FILTER_ALL) {
        return ES_ERR_INVALID_KIND;
    }
    if (!(threshold > 0.0 && threshold <= 0.5)) {
        return ES_ERR_INVALID_THRESHOLD;
    }
    if (jd_hi < jd_lo) {
        *out_count = 0;
        return ES_OK; /* empty window — match Python which raises but
                       * the bridge maps that to {ok: False}; here we
                       * defensively return zero candidates. The Python
                       * bridge already validated jd_hi >= jd_lo before
                       * calling. */
    }

    /* Targets: (kind_id, syn_target) pairs. We unroll the two-target
     * loop so the inner body stays branchless.
     */
    int n_targets = 0;
    int  target_kinds[2];
    double target_syn[2];
    if (kind == ES_SYZYGY_KIND_FILTER_SOLAR || kind == ES_SYZYGY_KIND_FILTER_ALL) {
        target_kinds[n_targets] = ES_SYZYGY_KIND_SOLAR;
        target_syn[n_targets]   = 0.0;
        ++n_targets;
    }
    if (kind == ES_SYZYGY_KIND_FILTER_LUNAR || kind == ES_SYZYGY_KIND_FILTER_ALL) {
        target_kinds[n_targets] = ES_SYZYGY_KIND_LUNAR;
        target_syn[n_targets]   = 0.5;
        ++n_targets;
    }

    /* Start at the first new moon >= jd_lo. */
    const double n_start_d = ceil((jd_lo - LUNAR_REFERENCE_NEW_MOON_JD_TDB) / SYNODIC_MONTH_DAYS);
    const double n_end_d   = floor((jd_hi - LUNAR_REFERENCE_NEW_MOON_JD_TDB) / SYNODIC_MONTH_DAYS);

    size_t count = 0;
    if (n_end_d < n_start_d) {
        *out_count = 0;
        return ES_OK;
    }

    for (double n = n_start_d; n <= n_end_d; n += 1.0) {
        const double jd_new_moon = LUNAR_REFERENCE_NEW_MOON_JD_TDB + n * SYNODIC_MONTH_DAYS;

        for (int t = 0; t < n_targets; ++t) {
            const double jd = jd_new_moon + target_syn[t] * SYNODIC_MONTH_DAYS;
            if (jd < jd_lo || jd > jd_hi) continue;

            /* Synodic phase residual is exactly 0 by enumeration. */
            const double syn_resid = 0.0;

            /* Draconic phase relative to August 1999 anchor. Eclipse
             * geometry is symmetric across ascending/descending nodes,
             * so we look at distance to phase = 0 modulo 0.5.
             */
            const double drc_offset = pos_mod(jd - SOLAR_ECLIPSE_REFERENCE_JD_TDB,
                                              DRACONIC_MONTH_DAYS);
            const double drc_phase  = drc_offset / DRACONIC_MONTH_DAYS;
            const double drc_resid  = modular_distance_to_zero(pos_mod(drc_phase * 2.0, 1.0)) / 2.0;

            const double score = sqrt(syn_resid * syn_resid + drc_resid * drc_resid);
            if (score < threshold) {
                if (count < out_capacity) {
                    out_buf[count].jd_tdb               = jd;
                    out_buf[count].kind                 = target_kinds[t];
                    out_buf[count].synodic_phase_resid  = syn_resid;
                    out_buf[count].draconic_phase_resid = drc_resid;
                    out_buf[count].score                = score;
                }
                ++count;
                if (count >= max_candidates) {
                    *out_count = (count > out_capacity) ? out_capacity : count;
                    return ES_OK;
                }
            }
        }
    }

    *out_count = (count > out_capacity) ? out_capacity : count;
    return ES_OK;
}
