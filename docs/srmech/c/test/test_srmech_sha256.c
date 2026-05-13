/*
 * test_srmech_sha256.c — C-side smoke tests for srmech_sha256_hex.
 *
 * NIST FIPS 180-4 sample vectors + a few longer payloads. Mirrors
 * the discipline of ephemerides-spectral's test_es_encode.c — assert
 * + count, no test framework. Exits 0 on all-pass, non-zero on first
 * fail.
 *
 * Phase B3 — first C unit test for srmech.
 */

#include "srmech.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

static void check_eq_str(const char *got, const char *want, const char *desc)
{
    if (strcmp(got, want) == 0) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %s\n    want: %s\n", desc, got, want);
    }
}

static void check_eq_int(int got, int want, const char *desc)
{
    if (got == want) {
        g_passed++;
        printf("  PASS  %s (=%d)\n", desc, got);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %d\n    want: %d\n", desc, got, want);
    }
}

static void hash_and_check(const uint8_t *data,
                           size_t         data_len,
                           const char    *want,
                           const char    *desc)
{
    char out[65];
    out[64] = 'X';  /* poison; should be overwritten with NUL */
    const srmech_status_t st = srmech_sha256_hex(data, data_len, out);
    if (st != SRMECH_OK) {
        g_failed++;
        printf("  FAIL  %s — status %d\n", desc, (int)st);
        return;
    }
    if (out[64] != '\0') {
        g_failed++;
        printf("  FAIL  %s — NUL terminator missing\n", desc);
        return;
    }
    check_eq_str(out, want, desc);
}

int main(void)
{
    printf("== srmech_sha256_hex smoke tests ==\n");

    /* Metadata accessors — make sure they're linked + sane. */
    check_eq_int(srmech_abi_version(), SRMECH_ABI_VERSION,
                 "srmech_abi_version() matches SRMECH_ABI_VERSION");
    printf("  srmech_version() = %s\n", srmech_version());

    /* FIPS 180-4 §B.1 — "" → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 */
    hash_and_check(
        (const uint8_t *)"", 0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "empty string");

    /* FIPS 180-4 §B.2 — "abc" → ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad */
    hash_and_check(
        (const uint8_t *)"abc", 3,
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "FIPS B.2: 'abc'");

    /* FIPS 180-4 §B.3 — 448-bit msg → 248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1 */
    hash_and_check(
        (const uint8_t *)"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", 56,
        "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
        "FIPS B.3: 448-bit two-block message");

    /* Common sanity: "hello world" → b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9 */
    hash_and_check(
        (const uint8_t *)"hello world", 11,
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        "'hello world'");

    /* 1024-byte stream of 'a' — exercises full-block + partial-tail path. */
    {
        uint8_t buf[1024];
        memset(buf, 'a', sizeof(buf));
        hash_and_check(
            buf, sizeof(buf),
            "2edc986847e209b4016e141a6dc8716d3207350f416969382d431539bf292e4a",
            "1024 'a' chars");
    }

    /* Exactly 55 bytes — last block before two-block-tail kicks in. */
    {
        const uint8_t buf[55] = {
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a',
        };
        hash_and_check(
            buf, sizeof(buf),
            "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318",
            "55 'a' chars (last single-tail-block boundary)");
    }

    /* Exactly 56 bytes — first byte that forces two padding blocks. */
    {
        const uint8_t buf[56] = {
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a',
        };
        hash_and_check(
            buf, sizeof(buf),
            "b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a",
            "56 'a' chars (two-padding-block boundary)");
    }

    /* Exactly 64 bytes — one full block + a second pad block. */
    {
        const uint8_t buf[64] = {
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a','a','a','a','a','a','a','a','a','a','a','a',
            'a','a','a','a',
        };
        hash_and_check(
            buf, sizeof(buf),
            "ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb",
            "64 'a' chars (full-block boundary)");
    }

    /* Error: NULL out-buffer */
    {
        const srmech_status_t st = srmech_sha256_hex(
            (const uint8_t *)"x", 1, NULL);
        check_eq_int((int)st, (int)SRMECH_ERR_NULL_ARG,
                     "NULL out_hex returns SRMECH_ERR_NULL_ARG");
    }

    /* Error: NULL data with non-zero length */
    {
        char out[65];
        const srmech_status_t st = srmech_sha256_hex(NULL, 1, out);
        check_eq_int((int)st, (int)SRMECH_ERR_NULL_ARG,
                     "NULL data + len>0 returns SRMECH_ERR_NULL_ARG");
    }

    /* OK: NULL data with zero length — mirrors hashlib.sha256(b"") */
    {
        char out[65];
        const srmech_status_t st = srmech_sha256_hex(NULL, 0, out);
        if (st != SRMECH_OK) {
            g_failed++;
            printf("  FAIL  NULL data + len=0 should be OK (got status %d)\n",
                   (int)st);
        } else {
            check_eq_str(out,
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "NULL data + len=0 yields empty-string hash");
        }
    }

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
