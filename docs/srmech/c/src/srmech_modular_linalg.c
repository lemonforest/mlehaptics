/*
 * srmech_modular_linalg.c -- Class I modular linear algebra: GF(p) RREF.
 *
 * srmech 0.9.0rc44, rung 1 of the CRT-QMat re-fibration arc. The exact-Q
 * QMat Gauss-Jordan (rc40) reserves a malloc-free arena sized by the Hadamard
 * worst-case fraction envelope -- measured ~1.5 GB for a 17-bit answer on the
 * order-2 Franel Zeilberger system, a ~369:1 over-reservation. The fix is to
 * re-fibrate the dense solve onto CRT: solve mod several machine-int primes
 * (each a bounded GF(p) elimination with ZERO coefficient swell), CRT-combine,
 * rational-reconstruct once. This file is the bottom of that stack -- the
 * swell-free GF(p) RREF kernel.
 *
 * srmech_gf_rref reduces a caller-supplied int64 matrix to reduced row-echelon
 * form over the field GF(p) IN PLACE, writing the rank + the pivot columns. All
 * arithmetic is bounded machine-int: 2 < p < 2**31 guarantees a*b fits uint64,
 * so the modular multiply needs no russian-peasant doubling -- a single 64-bit
 * intermediate. There is NO fraction growth and NO bignum -- that bound is the
 * whole point of the row.
 *
 * Sign/zero handling is Class-K: every decision is a compare-to-0 over residues
 * already reduced into [0, p); there is no abs() anywhere (the residues are
 * non-negative by construction).
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc (the matrix + pivots buffers
 * are caller-owned). Bounded loops via the fixed n_rows / n_cols extents.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK -- n_rows / n_cols extents
 *   - Rule 3 (no malloc)      : OK -- caller-owned buffers
 *   - Rule 4 (<=60 lines/func) : OK
 *   - Rule 5 (>=2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK -- srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Row-major element access: matrix[r * n_cols + c]. Centralises the index
 * arithmetic so the kernel below reads as plain matrix math. */
static int64_t m_at(const int64_t *m, uint32_t n_cols, uint32_t r, uint32_t c)
{
    assert(m != NULL);
    assert(c < n_cols);
    return m[(uint64_t)r * (uint64_t)n_cols + (uint64_t)c];
}

/* (a + b) mod p, with a, b already in [0, p) and p < 2**31 so a + b < 2**32. */
static uint64_t gf_add(uint64_t a, uint64_t b, uint64_t p)
{
    assert(p > 2u);
    assert(a < p && b < p);
    return (a + b) % p;
}

/* (a * b) mod p, with a, b in [0, p) and p < 2**31 so a * b < 2**62 < 2**64. */
static uint64_t gf_mul(uint64_t a, uint64_t b, uint64_t p)
{
    assert(p > 2u);
    assert(a < p && b < p);
    return (a * b) % p;
}

/* Modular inverse of a in GF(p) via Fermat: a**(p-2) mod p (p prime).
 * Square-and-multiply, bounded by the 31 significant bits of (p - 2). a must be
 * nonzero mod p (the caller only inverts a discovered nonzero pivot). */
static uint64_t gf_inv(uint64_t a, uint64_t p)
{
    uint64_t result = 1u;
    uint64_t base   = a % p;
    uint64_t e      = p - 2u;
    assert(p > 2u);
    assert(base != 0u);
    while (e != 0u) {
        if ((e & 1u) != 0u) {
            result = gf_mul(result, base, p);
        }
        base = gf_mul(base, base, p);
        e >>= 1;
    }
    return result;
}

/* Scale row r (in place) by the field scalar s: m[r][c] *= s for all c. */
static void gf_scale_row(int64_t *m, uint32_t n_cols, uint32_t r,
                         uint64_t s, uint64_t p)
{
    uint64_t base = (uint64_t)r * (uint64_t)n_cols;
    assert(m != NULL);
    assert(s < p);
    for (uint32_t c = 0; c < n_cols; c++) {
        uint64_t v = (uint64_t)m[base + c];
        m[base + c] = (int64_t)gf_mul(v, s, p);
    }
}

/* dst_row -= factor * src_row (mod p), over all columns. */
static void gf_eliminate(int64_t *m, uint32_t n_cols, uint32_t dst, uint32_t src,
                         uint64_t factor, uint64_t p)
{
    uint64_t dbase = (uint64_t)dst * (uint64_t)n_cols;
    uint64_t sbase = (uint64_t)src * (uint64_t)n_cols;
    assert(m != NULL);
    assert(factor < p);
    for (uint32_t c = 0; c < n_cols; c++) {
        uint64_t sv = gf_mul((uint64_t)m[sbase + c], factor, p);
        uint64_t dv = (uint64_t)m[dbase + c];
        /* dv - sv (mod p) == dv + neg (mod p), where neg = (p - sv) mod p so
         * that sv == 0 maps to 0 (not p) and stays inside the [0, p) domain. */
        uint64_t neg = (p - sv) % p;
        m[dbase + c] = (int64_t)gf_add(dv, neg, p);
    }
}

/* Swap rows r0 and r1 in place. */
static void gf_swap_rows(int64_t *m, uint32_t n_cols, uint32_t r0, uint32_t r1)
{
    uint64_t b0 = (uint64_t)r0 * (uint64_t)n_cols;
    uint64_t b1 = (uint64_t)r1 * (uint64_t)n_cols;
    assert(m != NULL);
    assert(r0 <= r1);
    for (uint32_t c = 0; c < n_cols; c++) {
        int64_t t = m[b0 + c];
        m[b0 + c] = m[b1 + c];
        m[b1 + c] = t;
    }
}

/* Reduce every matrix entry into the canonical residue [0, p). Handles
 * negative inputs (a true modulo, not C's truncated remainder). */
static void gf_canonicalize(int64_t *m, uint32_t n_rows, uint32_t n_cols,
                            uint64_t p)
{
    uint64_t total = (uint64_t)n_rows * (uint64_t)n_cols;
    assert(m != NULL);
    assert(p > 2u);
    for (uint64_t i = 0; i < total; i++) {
        int64_t v = m[i];
        int64_t r = v % (int64_t)p;
        if (r < 0) {
            r += (int64_t)p;
        }
        m[i] = r;
    }
}

srmech_status_t srmech_gf_rref(int64_t  *matrix,
                               uint32_t  n_rows,
                               uint32_t  n_cols,
                               uint64_t  p,
                               uint32_t *out_pivots,
                               uint32_t *out_rank)
{
    uint32_t pivot_row = 0;
    assert(out_pivots != NULL);
    assert(out_rank != NULL);
    if (matrix == NULL || out_pivots == NULL || out_rank == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* p must be an odd prime in (2, 2**31) so a*b fits uint64 and Fermat
     * inversion is valid. The caller (Python next_prime / a prime table)
     * guarantees primality; here we only guard the arithmetic domain. */
    if (p <= 2u || p >= (1ull << 31)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out_rank = 0;
    gf_canonicalize(matrix, n_rows, n_cols, p);
    for (uint32_t col = 0; col < n_cols && pivot_row < n_rows; col++) {
        /* Find a nonzero entry in this column at or below pivot_row. */
        uint32_t sel = n_rows;
        for (uint32_t r = pivot_row; r < n_rows; r++) {
            if (m_at(matrix, n_cols, r, col) != 0) {
                sel = r;
                break;
            }
        }
        if (sel == n_rows) {
            continue;                       /* free column, no pivot here */
        }
        if (sel != pivot_row) {
            gf_swap_rows(matrix, n_cols, pivot_row, sel);
        }
        /* Normalise the pivot row so its leading entry is 1. */
        uint64_t lead = (uint64_t)m_at(matrix, n_cols, pivot_row, col);
        gf_scale_row(matrix, n_cols, pivot_row, gf_inv(lead, p), p);
        /* Eliminate this column from every other row (reduced echelon). */
        for (uint32_t r = 0; r < n_rows; r++) {
            if (r == pivot_row) {
                continue;
            }
            uint64_t f = (uint64_t)m_at(matrix, n_cols, r, col);
            if (f != 0) {
                gf_eliminate(matrix, n_cols, r, pivot_row, f, p);
            }
        }
        out_pivots[pivot_row] = col;
        pivot_row++;
    }
    *out_rank = pivot_row;
    return SRMECH_OK;
}
