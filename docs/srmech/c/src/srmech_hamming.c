/*
 * srmech_hamming.c — Hamming / GF(2) linear block-code family.
 *
 * The CARRY/EC half of the sedenion front-loader (#910 / §30; findings
 * F442 + F449). A 2^n-1 single-error-correcting Hamming code, lean-ALU
 * XOR-native: GF(2) addition IS XOR IS parity. No float, no libm, no
 * malloc — a block code is `^` and index arithmetic only.
 *
 * Canonical construction (1-indexed): codeword length N = 2^n - 1; parity
 * bits at the power-of-two positions 1, 2, 4, ..., 2^(n-1); the k = N - n
 * remaining positions carry data. The parity bit at 2^i is the even-parity
 * XOR of every position whose index has bit i set. The syndrome (recompute
 * each parity, read the failed set as a binary number) IS the 1-indexed
 * position of the single flipped bit; 0 = clean. Distance 3 => corrects any
 * single-bit error. Hamming(7,4) is the octonion's own Fano plane (F441).
 *
 * Rosetta peer of srmech.amsc.cascade.hamming_* — attested bit-exact by
 * tests/test_cascade_hamming_parity.py.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — all loops bounded by N <= 2^16-1
 *   - Rule 3 (no malloc)      : OK — caller-owned buffers only
 *   - Rule 4 (<=60 lines/func): OK
 *   - Rule 5 (>=2 asserts/fn) : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Largest codeword length, 2^SRMECH_HAMMING_MAX_N - 1 — a loop over-bound. */
#define SRMECH_HAMMING_MAX_LEN (((size_t)1u << SRMECH_HAMMING_MAX_N) - 1u)

/* Recover n from a codeword length 2^n - 1, or 0 if `len` is not a valid
 * Hamming length in [2, SRMECH_HAMMING_MAX_N]. */
static int srmech_hamming_infer_n(size_t len)
{
    assert(SRMECH_HAMMING_MAX_N >= 2);
    for (int n = 2; n <= SRMECH_HAMMING_MAX_N; n++) {
        if (len == (((size_t)1u << n) - 1u)) {
            assert(n >= 2 && n <= SRMECH_HAMMING_MAX_N);
            return n;
        }
    }
    return 0;
}

/* 1 if every element of buf is a 0/1 bit, else 0. */
static int srmech_hamming_bits_ok(const uint8_t *buf, size_t len)
{
    assert(buf != NULL);
    assert(len <= SRMECH_HAMMING_MAX_LEN);
    for (size_t i = 0; i < len && i <= SRMECH_HAMMING_MAX_LEN; i++) {
        if (buf[i] > 1u) {
            return 0;
        }
    }
    return 1;
}

srmech_status_t srmech_hamming_encode(const uint8_t *data, size_t k, int n,
                                      uint8_t *out_codeword)
{
    assert(data != NULL);
    assert(out_codeword != NULL);
    if (data == NULL || out_codeword == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 2 || n > SRMECH_HAMMING_MAX_N) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t big = (((size_t)1u << n) - 1u);
    if (k != big - (size_t)n || !srmech_hamming_bits_ok(data, k)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (size_t i = 0; i < big; i++) {
        out_codeword[i] = 0u;
    }
    /* Data bits go at the non-power-of-two positions (1-indexed). */
    size_t slot = 0;
    for (size_t j = 1; j <= big; j++) {
        if ((j & (j - 1u)) != 0u) {
            out_codeword[j - 1u] = data[slot];
            slot++;
        }
    }
    assert(slot == k);
    /* Parity bit at 2^i = even-parity XOR of the positions it covers. */
    for (int i = 0; i < n; i++) {
        size_t p = ((size_t)1u << i);
        uint8_t par = 0u;
        for (size_t j = 1; j <= big; j++) {
            if (j != p && (j & p) != 0u) {
                par ^= out_codeword[j - 1u];
            }
        }
        out_codeword[p - 1u] = par;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_hamming_syndrome(const uint8_t *codeword, size_t len,
                                        int *out_pos)
{
    assert(codeword != NULL);
    assert(out_pos != NULL);
    if (codeword == NULL || out_pos == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int n = srmech_hamming_infer_n(len);
    if (n == 0 || !srmech_hamming_bits_ok(codeword, len)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int syn = 0;
    for (int i = 0; i < n; i++) {
        size_t p = ((size_t)1u << i);
        uint8_t s = 0u;
        for (size_t j = 1; j <= len; j++) {
            if ((j & p) != 0u) {
                s ^= codeword[j - 1u];
            }
        }
        if (s != 0u) {
            syn |= (int)p;
        }
    }
    assert(syn >= 0 && (size_t)syn <= len);
    *out_pos = syn;
    return SRMECH_OK;
}

srmech_status_t srmech_hamming_decode_correct(const uint8_t *codeword, size_t len,
                                              uint8_t *out_data, int *out_pos)
{
    assert(codeword != NULL);
    assert(out_data != NULL);
    assert(out_pos != NULL);
    if (codeword == NULL || out_data == NULL || out_pos == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int n = srmech_hamming_infer_n(len);
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int syn = 0;
    srmech_status_t st = srmech_hamming_syndrome(codeword, len, &syn);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Extract data positions, applying the single-bit correction inline:
     * the only bit that may flip is the one located at position `syn`. */
    size_t slot = 0;
    for (size_t j = 1; j <= len; j++) {
        if ((j & (j - 1u)) != 0u) {
            uint8_t bit = codeword[j - 1u];
            if ((int)j == syn) {
                bit ^= 1u;
            }
            out_data[slot] = bit;
            slot++;
        }
    }
    assert(slot == len - (size_t)n);
    *out_pos = syn;
    return SRMECH_OK;
}
