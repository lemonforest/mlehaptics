/* srmech_qm_constants.c — the qm CONSTANT-matrix builders (0.9.0rc212, #755).
 *
 * The base qm constant matrices — the Pauli σ_x/σ_y/σ_z + I₂ (spin.py), the
 * Dirac γ⁰..γ³ + the Minkowski metric η (relativistic.py), and the eight
 * Gell-Mann λ¹..λ⁸ + the SU(2)/SU(3) structure constants (gauge.py) — were
 * Python LITERALS with no C source: classified `composition_of_c`, yet a
 * bare-C host could not produce the constant DATA. This file closes that
 * python-free gap: each builder EMITS the canonical constant data
 * BYTE-IDENTICAL to the (rc212-canonicalized) Python literals.
 *
 * Zero canonicalization contract (rc212): every mathematically-zero slot is
 * +0.0 — the Python literals' -0.0 slots (from `-1j` / `_scale(-1.0, ·)`)
 * were canonicalized in the same rc, so the C tables here are plain constant
 * data with no signed-zero replication hazard. The only non-integer values
 * are the λ⁸ 1/√3 normaliser and the f^{458}=f^{678}=√3/2 SU(3) structure
 * constants — both derived through srmech's own libm-free
 * `srmech_rational_sqrt` (srmech_sqrt.c), whose double projection is
 * byte-identical to the Python `float(rational.sqrt(3.0))` (one rounding +
 * exact power-of-two scaling on both paths).
 *
 * Layout: complex matrices are row-major interleaved (re,im) pairs — the
 * `Mat` carrier layout (C99 `double _Complex` compatible); the Minkowski
 * metric is row-major REAL doubles (`is_complex=False`); the structure
 * constants are flat rank-3 row-major real doubles f[a][b][c].
 *
 * Canonical SSoT: Pauli (1927) Z. Phys. 43, 601; Peskin-Schroeder §3.2
 * eq 3.25 + A.6 (Dirac basis) + §3.1 eq 3.4 (mostly-minus metric);
 * Gell-Mann (1962) Phys. Rev. 125, 1067 eq 16; Peskin-Schroeder eq 17.34
 * (SU(3) structure constants).
 *
 * JPL Power-of-Ten: Rule 1 (no goto) OK; Rule 2 (bounded loops) OK — every
 * loop is a fixed-size table copy/fill; Rule 3 (no malloc) OK — caller
 * buffers only; Rule 4 (<=60 lines/fn) OK; Rule 5 (>=2 asserts/fn) OK;
 * Rule 7 (status returns) OK; Rule 10 (warnings clean) OK.
 *
 * ABI-additive: new symbols only, no callback typedef, so
 * SRMECH_ABI_VERSION stays 4.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

/* ── Pauli 2×2 tables (8 doubles each: row-major interleaved re,im) ─────── */
static const double srmech_qm_pauli_tab[4][8] = {
    /* σ_x = [[0, 1], [1, 0]] */
    {0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0},
    /* σ_y = [[0, -i], [i, 0]] — canonical true-zero real parts (+0.0) */
    {0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0},
    /* σ_z = [[1, 0], [0, -1]] */
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0},
    /* I₂ = [[1, 0], [0, 1]] (the Cl(0,3) scalar) */
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0},
};

/* ── Dirac γ 4×4 tables (32 doubles each; Dirac/standard basis) ──────────
 * γ⁰ = [[I₂, 0], [0, -I₂]];  γ^i = [[0, σ_i], [-σ_i, 0]]  (i = 1, 2, 3). */
static const double srmech_qm_gamma_tab[4][32] = {
    /* γ⁰ = diag(1, 1, -1, -1) */
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0},
    /* γ¹: (0,3)=1, (1,2)=1, (2,1)=-1, (3,0)=-1 */
    {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
     0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* γ²: (0,3)=-i, (1,2)=+i, (2,1)=+i, (3,0)=-i */
    {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
     0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* γ³: (0,2)=1, (1,3)=-1, (2,0)=-1, (3,1)=1 */
    {0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0,
     -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0},
};

/* ── Gell-Mann λ¹..λ⁷ 3×3 tables (18 doubles each; λ⁸ is computed) ──────── */
static const double srmech_qm_gm_tab[7][18] = {
    /* λ¹: (0,1)=1, (1,0)=1 */
    {0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
     1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* λ²: (0,1)=-i, (1,0)=+i — canonical true-zero real parts (+0.0) */
    {0.0, 0.0, 0.0, -1.0, 0.0, 0.0,
     0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* λ³: diag(1, -1, 0) */
    {1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, -1.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* λ⁴: (0,2)=1, (2,0)=1 */
    {0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     1.0, 0.0, 0.0, 0.0, 0.0, 0.0},
    /* λ⁵: (0,2)=-i, (2,0)=+i */
    {0.0, 0.0, 0.0, 0.0, 0.0, -1.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 1.0, 0.0, 0.0, 0.0, 0.0},
    /* λ⁶: (1,2)=1, (2,1)=1 */
    {0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
     0.0, 0.0, 1.0, 0.0, 0.0, 0.0},
    /* λ⁷: (1,2)=-i, (2,1)=+i */
    {0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, -1.0,
     0.0, 0.0, 0.0, 1.0, 0.0, 0.0},
};

srmech_status_t srmech_qm_pauli(int32_t which, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (which < 0 || which > 3) { return SRMECH_ERR_BAD_INPUT; }
    assert(which >= 0 && which <= 3);   /* validated above */
    for (size_t k = 0; k < 8u; ++k) { out[k] = srmech_qm_pauli_tab[which][k]; }
    return SRMECH_OK;
}

srmech_status_t srmech_qm_dirac_gamma(int32_t mu, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (mu < 0 || mu > 3) { return SRMECH_ERR_BAD_INPUT; }
    assert(mu >= 0 && mu <= 3);   /* validated above */
    for (size_t k = 0; k < 32u; ++k) { out[k] = srmech_qm_gamma_tab[mu][k]; }
    return SRMECH_OK;
}

srmech_status_t srmech_qm_minkowski_metric(double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    for (size_t k = 0; k < 16u; ++k) { out[k] = 0.0; }
    out[0] = 1.0;                       /* η⁰⁰ = +1 (mostly-minus) */
    out[5] = -1.0;
    out[10] = -1.0;
    out[15] = -1.0;
    assert(out[0] == 1.0 && out[15] == -1.0);   /* diag written */
    return SRMECH_OK;
}

srmech_status_t srmech_qm_gell_mann(int32_t a, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (a < 1 || a > 8) { return SRMECH_ERR_BAD_INPUT; }
    if (a <= 7) {
        for (size_t k = 0; k < 18u; ++k) { out[k] = srmech_qm_gm_tab[a - 1][k]; }
        return SRMECH_OK;
    }
    /* λ⁸ = (1/√3) · diag(1, 1, -2) — the normaliser through srmech's own
     * libm-free rational sqrt (byte-identical to the Python
     * 1.0 / float(rational.sqrt(3.0)): one rounding each path). */
    double s3 = 0.0;
    srmech_status_t st = srmech_rational_sqrt(3.0, &s3);
    if (st != SRMECH_OK) { return st; }
    assert(s3 > 1.0 && s3 < 2.0);   /* √3 ≈ 1.732 */
    for (size_t k = 0; k < 18u; ++k) { out[k] = 0.0; }
    out[0] = 1.0 / s3;
    out[8] = 1.0 / s3;
    out[16] = -2.0 * (1.0 / s3);
    return SRMECH_OK;
}

srmech_status_t srmech_qm_su2_structure(double *out)
{
    /* ε^{abc}: f[a][b][c]=+1 and f[b][a][c]=-1 for each cyclic (a,b,c) —
     * the same fill order as the Python su2_structure_constants. */
    static const int32_t cyc[3][3] = {{0, 1, 2}, {1, 2, 0}, {2, 0, 1}};
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    for (size_t k = 0; k < 27u; ++k) { out[k] = 0.0; }
    for (size_t r = 0; r < 3u; ++r) {
        int32_t a = cyc[r][0];
        int32_t b = cyc[r][1];
        int32_t c = cyc[r][2];
        assert(a >= 0 && a < 3 && b >= 0 && b < 3 && c >= 0 && c < 3);
        out[(a * 3 + b) * 3 + c] = 1.0;
        out[(b * 3 + a) * 3 + c] = -1.0;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_qm_su3_structure(double *out)
{
    /* Non-zero seeds (Peskin-Schroeder eq 17.34), filled by total
     * antisymmetry over the six permutations — the same seed order, the
     * same permutation order, and the same sign·value multiplies as the
     * Python su3_structure_constants (byte-identical fill). */
    static const int32_t seed_idx[9][3] = {
        {0, 1, 2}, {0, 3, 6}, {1, 3, 5}, {1, 4, 6}, {2, 3, 4},
        {0, 4, 5}, {2, 5, 6}, {3, 4, 7}, {5, 6, 7},
    };
    static const double seed_val[9] = {
        1.0, 0.5, 0.5, 0.5, 0.5, -0.5, -0.5, 0.0, 0.0,   /* [7],[8] = √3/2 */
    };
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    double s3 = 0.0;
    srmech_status_t st = srmech_rational_sqrt(3.0, &s3);
    if (st != SRMECH_OK) { return st; }
    assert(s3 > 1.0 && s3 < 2.0);   /* √3 ≈ 1.732 */
    for (size_t k = 0; k < 512u; ++k) { out[k] = 0.0; }
    for (size_t r = 0; r < 9u; ++r) {
        int32_t a = seed_idx[r][0];
        int32_t b = seed_idx[r][1];
        int32_t c = seed_idx[r][2];
        double val = (r >= 7u) ? (s3 / 2.0) : seed_val[r];
        const int32_t perm[6][3] = {
            {a, b, c}, {b, c, a}, {c, a, b}, {a, c, b}, {c, b, a}, {b, a, c},
        };
        static const double sign[6] = {1.0, 1.0, 1.0, -1.0, -1.0, -1.0};
        for (size_t p = 0; p < 6u; ++p) {
            int32_t i = perm[p][0];
            int32_t j = perm[p][1];
            int32_t k3 = perm[p][2];
            out[(i * 8 + j) * 8 + k3] = sign[p] * val;
        }
    }
    return SRMECH_OK;
}
