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

/* Build the (kind, syn-target) pair list for the requested kind
 * filter. Returns the number of target rows populated (1 or 2 in
 * practice — see ES_SYZYGY_KIND_FILTER_*). target_kinds + target_syn
 * are caller-supplied buffers of capacity 2.
 */
static int select_syzygy_targets(int kind,
                                 int target_kinds[2],
                                 double target_syn[2])
{
    int n_targets = 0;
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
    return n_targets;
}

/* Score a single candidate event at jd. The synodic residual is
 * exactly 0 by enumeration; the draconic residual is computed
 * relative to the August 1999 solar-eclipse anchor, exploiting the
 * ascending/descending-node symmetry (distance to phase = 0 mod 0.5).
 * Returns the geometric score (sqrt of summed squared residuals);
 * out_syn_resid and out_drc_resid are filled for the caller's struct.
 */
static double score_syzygy_event(double jd,
                                 double *out_syn_resid,
                                 double *out_drc_resid)
{
    const double syn_resid = 0.0;
    const double drc_offset = pos_mod(jd - SOLAR_ECLIPSE_REFERENCE_JD_TDB,
                                      DRACONIC_MONTH_DAYS);
    const double drc_phase  = drc_offset / DRACONIC_MONTH_DAYS;
    const double drc_resid  = modular_distance_to_zero(pos_mod(drc_phase * 2.0, 1.0)) / 2.0;
    *out_syn_resid = syn_resid;
    *out_drc_resid = drc_resid;
    return sqrt(syn_resid * syn_resid + drc_resid * drc_resid);
}

/* Emit one matching event into the caller's out_buf if there's room
 * (silently increment past the cap so the caller can detect overflow
 * via count > capacity, matching the Python bridge's pre-allocation
 * sizing). Returns 1 if the caller-supplied max_candidates cap has
 * been reached and the walk should terminate, else 0.
 */
static int emit_syzygy_event(double jd, int kind_id,
                             double syn_resid, double drc_resid, double score,
                             es_syzygy_t *out_buf, size_t out_capacity,
                             size_t max_candidates, size_t *count)
{
    if (*count < out_capacity) {
        out_buf[*count].jd_tdb               = jd;
        out_buf[*count].kind                 = kind_id;
        out_buf[*count].synodic_phase_resid  = syn_resid;
        out_buf[*count].draconic_phase_resid = drc_resid;
        out_buf[*count].score                = score;
    }
    ++(*count);
    return (*count >= max_candidates) ? 1 : 0;
}

/* Validate es_find_syzygies inputs. Returns ES_OK if all checks pass
 * AND the window is non-empty; returns a non-OK status on validation
 * failure; returns ES_OK with *out_window_empty=1 when the window is
 * legitimately empty (jd_hi < jd_lo) — in that case the caller should
 * write *out_count = 0 and bail.
 */
static es_status_t validate_syzygy_args(double jd_lo, double jd_hi,
                                        int kind, double threshold,
                                        const es_syzygy_t *out_buf,
                                        const size_t *out_count,
                                        int *out_window_empty)
{
    *out_window_empty = 0;
    if (out_buf == NULL || out_count == NULL) return ES_ERR_NULL_OUTPUT;
    if (!isfinite(jd_lo) || !isfinite(jd_hi)) return ES_ERR_NON_FINITE_INPUT;
    if (kind != ES_SYZYGY_KIND_FILTER_SOLAR
        && kind != ES_SYZYGY_KIND_FILTER_LUNAR
        && kind != ES_SYZYGY_KIND_FILTER_ALL) {
        return ES_ERR_INVALID_KIND;
    }
    if (!(threshold > 0.0 && threshold <= 0.5)) return ES_ERR_INVALID_THRESHOLD;
    if (jd_hi < jd_lo) {
        /* Empty window — match Python which raises but the bridge maps
         * that to {ok: False}; here we defensively return zero.
         */
        *out_window_empty = 1;
    }
    return ES_OK;
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
    int window_empty = 0;
    const es_status_t vrc = validate_syzygy_args(jd_lo, jd_hi, kind, threshold,
                                                  out_buf, out_count,
                                                  &window_empty);
    if (vrc != ES_OK) return vrc;
    if (window_empty) {
        *out_count = 0;
        return ES_OK;
    }

    /* (kind_id, syn-target) pair list — at most two rows. */
    int    target_kinds[2];
    double target_syn[2];
    const int n_targets = select_syzygy_targets(kind, target_kinds, target_syn);

    /* Start at the first new moon >= jd_lo. */
    const double n_start_d = ceil((jd_lo - LUNAR_REFERENCE_NEW_MOON_JD_TDB) / SYNODIC_MONTH_DAYS);
    const double n_end_d   = floor((jd_hi - LUNAR_REFERENCE_NEW_MOON_JD_TDB) / SYNODIC_MONTH_DAYS);

    if (n_end_d < n_start_d) {
        *out_count = 0;
        return ES_OK;
    }

    size_t count = 0;
    for (double n = n_start_d; n <= n_end_d; n += 1.0) {
        const double jd_new_moon = LUNAR_REFERENCE_NEW_MOON_JD_TDB + n * SYNODIC_MONTH_DAYS;
        for (int t = 0; t < n_targets; ++t) {
            const double jd = jd_new_moon + target_syn[t] * SYNODIC_MONTH_DAYS;
            if (jd < jd_lo || jd > jd_hi) continue;
            double syn_resid, drc_resid;
            const double score = score_syzygy_event(jd, &syn_resid, &drc_resid);
            if (score >= threshold) continue;
            if (emit_syzygy_event(jd, target_kinds[t], syn_resid, drc_resid, score,
                                  out_buf, out_capacity, max_candidates, &count)) {
                *out_count = (count > out_capacity) ? out_capacity : count;
                return ES_OK;
            }
        }
    }
    *out_count = (count > out_capacity) ? out_capacity : count;
    return ES_OK;
}
