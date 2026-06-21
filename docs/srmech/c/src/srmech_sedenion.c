/*
 * srmech_sedenion.c — the sedenion-addressable hyper-loop address layer in C.
 *
 * Standalone-complete C peer of the SedenionRegister "address algebra"
 * (UPSTREAM §31 / F465 + F468; Python srmech.amsc.cascade.sedenion_register):
 * the navigation + reversibility-gate operations a C-only host (no Python)
 * needs to run "Siona's address layer."
 *
 *   - srmech_sedenion_navmap    : the signed pointer-advance permutation for
 *                                 right-multiply-by-e_j over the 16 slots
 *                                 (mirror of SedenionRegister.navmap).
 *   - srmech_sedenion_navigate  : route a set of occupied (slot, sign) records
 *                                 through that permutation, composing the
 *                                 Class-C signs (mirror of .navigate).
 *   - srmech_sedenion_is_navigable : the reversibility gate — is left-multiply
 *                                 by `direction` a bijection? (mirror of
 *                                 .is_navigable / left_mult_is_invertible).
 *
 * The carry/correct EC half is ALREADY in C: SedenionRegister.carry/correct
 * delegate to srmech_hamming_encode / srmech_hamming_decode_correct (§30).
 *
 * NO BIGNUM (user directive). is_navigable decides invertibility of the
 * n x n integer matrix L(x)[r][c] = sign(r^c, c) * x_{r^c} (a signed
 * XOR-circulant). The matrix is singular over Q iff singular over GF(p) for
 * EVERY prime p; equivalently the Q-rank is the MAX modular rank over a prime
 * set. Each prime is < 2^31, so every modular product a*b stays < 2^62 and
 * fits int64 — no value ever exceeds a machine word, no multi-precision limb
 * cascade, no library. A "singular" verdict is made CERTAIN by accumulating
 * enough primes that their product exceeds the Hadamard determinant bound
 * |det| <= (sum|x_i|)^n (a nonzero det below that product cannot vanish mod
 * every prime — the CRT certainty argument). The prime COUNT sizes from the
 * input magnitude (introspected per call); the table is the architectural
 * ceiling, and inputs beyond it return SRMECH_ERR_BAD_INPUT (no silent wrong
 * answer). Bit-exact (on the bool) with the Python Fraction-nullspace oracle,
 * attested by tests/test_cascade_sedenion_parity.py.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — bounded loops only
 *   - Rule 2 (bounded loops)    : OK — <= SRMECH_CD_MAX_DIM / table length
 *   - Rule 3 (no malloc)        : OK — caller arrays + bounded stack scratch
 *   - Rule 4 (<=60 lines/func)  : OK
 *   - Rule 5 (>=2 asserts/fn)   : OK
 *   - Rule 7 (return-value)     : OK — srmech_status_t
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Word-size primes just below 2^31 (verified prime; p*p < 2^62 fits int64).
 * 16 of them -> ~496-bit product, the certainty ceiling for the singular
 * verdict (covers the 16-slot address layer with vast margin). */
static const int64_t SED_PRIMES[] = {
    2147483647, 2147483629, 2147483587, 2147483579,
    2147483563, 2147483549, 2147483543, 2147483497,
    2147483489, 2147483477, 2147483423, 2147483399,
    2147483353, 2147483323, 2147483269, 2147483249
};
#define SED_NPRIMES ((int)(sizeof(SED_PRIMES) / sizeof(SED_PRIMES[0])))
/* floor(log2(p)) for every table prime — used for the certainty bit-budget. */
#define SED_PRIME_BITS 30

/* Bit length of an unsigned magnitude (0 for 0). */
static int sed_bitlen_u64(uint64_t v)
{
    int bits = 0;
    while (v != 0u) { bits++; v >>= 1; }
    assert(v == 0u);                        /* loop drained every set bit */
    assert(bits >= 0 && bits <= 64);
    return bits;
}

/* Modular exponentiation base^exp mod m (for the Fermat inverse). */
static int64_t sed_modpow(int64_t base, int64_t exp, int64_t m)
{
    assert(m > 1);
    assert(exp >= 0);
    int64_t result = 1 % m;
    int64_t b = base % m;
    if (b < 0) { b += m; }
    while (exp > 0) {
        if ((exp & 1) != 0) { result = (result * b) % m; }
        b = (b * b) % m;
        exp >>= 1;
    }
    return result;
}

/* Build the mod-p image of L(x): out[r*n+c] = sign(r^c,c) * x_{r^c} (mod p),
 * each entry normalised to [0, p). Returns SRMECH_OK or a CD error. */
static srmech_status_t sed_build_mod_matrix(const int64_t *dir, int n,
                                            int64_t p, int64_t *out)
{
    assert(dir != NULL && out != NULL);
    assert(n > 0 && n <= SRMECH_CD_MAX_DIM);
    for (int r = 0; r < n; r++) {
        for (int c = 0; c < n; c++) {
            int a = r ^ c;
            int idx = 0;
            int sign = 1;
            srmech_status_t st = srmech_cd_basis_product(n, a, c, &idx, &sign);
            if (st != SRMECH_OK) { return st; }
            assert(idx == r);
            int64_t v = dir[a] % p;
            if (v < 0) { v += p; }
            if (sign < 0 && v != 0) { v = p - v; }   /* Class-K sign-flip */
            out[r * n + c] = v;
        }
    }
    return SRMECH_OK;
}

/* Rank of an n x n integer matrix over GF(p) (Gaussian elimination, in place;
 * destroys `a`). All products stay < 2^62 since p < 2^31. */
static int sed_modular_rank(int64_t *a, int n, int64_t p)
{
    assert(a != NULL && p > 1);
    assert(n > 0 && n <= SRMECH_CD_MAX_DIM);
    int rank = 0;
    for (int col = 0; col < n && rank < n; col++) {
        int piv = -1;
        for (int r = rank; r < n; r++) {
            if (a[r * n + col] % p != 0) { piv = r; break; }
        }
        if (piv < 0) { continue; }
        for (int c = 0; c < n; c++) {                 /* swap rows rank, piv */
            int64_t t = a[rank * n + c];
            a[rank * n + c] = a[piv * n + c];
            a[piv * n + c] = t;
        }
        int64_t inv = sed_modpow(a[rank * n + col], p - 2, p);
        for (int c = 0; c < n; c++) {
            a[rank * n + c] = (a[rank * n + c] * inv) % p;
        }
        for (int r = 0; r < n; r++) {
            int64_t f = a[r * n + col] % p;
            if (r != rank && f != 0) {
                for (int c = 0; c < n; c++) {
                    int64_t s = (a[r * n + c] - f * a[rank * n + c]) % p;
                    if (s < 0) { s += p; }
                    a[r * n + c] = s;
                }
            }
        }
        rank++;
    }
    return rank;
}

srmech_status_t srmech_sedenion_navmap(int j, int *out_dest, int *out_sign)
{
    assert(out_dest != NULL);
    assert(out_sign != NULL);
    if (out_dest == NULL || out_sign == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (j < 0 || j >= SRMECH_SEDENION_NUM_SLOTS) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (int i = 0; i < SRMECH_SEDENION_NUM_SLOTS; i++) {
        int idx = 0;
        int sign = 1;
        srmech_status_t st = srmech_cd_basis_product(
            SRMECH_SEDENION_NUM_SLOTS, i, j, &idx, &sign);
        if (st != SRMECH_OK) { return st; }
        out_dest[i] = idx;
        out_sign[i] = sign;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_sedenion_navigate(int j,
                                         const int *in_slots,
                                         const int *in_signs,
                                         size_t count,
                                         int *out_slots,
                                         int *out_signs)
{
    assert(out_slots != NULL && out_signs != NULL);
    assert(in_slots != NULL || count == 0);
    if (out_slots == NULL || out_signs == NULL ||
        (in_slots == NULL && count > 0) || (in_signs == NULL && count > 0)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (j < 0 || j >= SRMECH_SEDENION_NUM_SLOTS) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (size_t m = 0; m < count; m++) {
        int s_in = in_slots[m];
        int sgn = in_signs[m];
        if (s_in < 0 || s_in >= SRMECH_SEDENION_NUM_SLOTS ||
            (sgn != 1 && sgn != -1)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        int idx = 0;
        int sign = 1;
        srmech_status_t st = srmech_cd_basis_product(
            SRMECH_SEDENION_NUM_SLOTS, s_in, j, &idx, &sign);
        if (st != SRMECH_OK) { return st; }
        out_slots[m] = idx;
        out_signs[m] = sgn * sign;          /* compose the Class-C signs */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_sedenion_is_navigable(const int64_t *direction,
                                             size_t n, int *out_invertible)
{
    assert(direction != NULL);
    assert(out_invertible != NULL);
    if (direction == NULL || out_invertible == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 1 || n > (size_t)SRMECH_CD_MAX_DIM ||
        (n & (n - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int nn = (int)n;
    uint64_t s = 0u;                        /* sum|x_i| for the Hadamard bound */
    for (int i = 0; i < nn; i++) {
        int64_t v = direction[i];
        uint64_t a = (v < 0) ? (uint64_t)(-(v + 1)) + 1u : (uint64_t)v;
        if (a > UINT64_MAX - s) { return SRMECH_ERR_BAD_INPUT; }   /* overflow */
        s += a;
    }
    /* |det| <= (sum|x_i|)^n  ->  bit-budget for the singular certainty test. */
    int bound_bits = nn * sed_bitlen_u64(s);
    int64_t mat[SRMECH_CD_MAX_DIM * SRMECH_CD_MAX_DIM];
    int acc_bits = 0;
    for (int pi = 0; pi < SED_NPRIMES; pi++) {
        srmech_status_t st = sed_build_mod_matrix(direction, nn,
                                                  SED_PRIMES[pi], mat);
        if (st != SRMECH_OK) { return st; }
        if (sed_modular_rank(mat, nn, SED_PRIMES[pi]) == nn) {
            *out_invertible = 1;            /* full rank mod p => Q-invertible */
            return SRMECH_OK;
        }
        acc_bits += SED_PRIME_BITS;
        if (acc_bits > bound_bits) {
            *out_invertible = 0;            /* certain singular (CRT) */
            return SRMECH_OK;
        }
    }
    return SRMECH_ERR_BAD_INPUT;             /* magnitude beyond the prime table */
}
