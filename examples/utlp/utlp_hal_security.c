/**
 * @file utlp_hal_security.c
 * @brief UTLP HAL Security Layer - mbedtls Implementation
 *
 * @section overview Overview
 *
 * Hardware-accelerated cryptographic operations using mbedtls. On ESP32-C6,
 * the AES operations use the hardware crypto accelerator for performance.
 *
 * @section performance Performance
 *
 * Target: < 50μs for 8-byte Intron encryption/decryption
 * - ESP32-C6 AES accelerator: ~1μs per block
 * - SHA-256 for key derivation: ~10μs for 24 bytes
 *
 * @see utlp_hal_security.h for API documentation
 *
 * @version 1.0.0
 * @date 2026-01-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_hal_security.h"
#include "utlp_hal.h"

/* mbedtls includes */
#include "mbedtls/aes.h"
#include "mbedtls/sha256.h"

/* ESP-IDF random number generator */
#ifdef ESP_PLATFORM
#include "esp_random.h"
#else
/* Fallback for non-ESP platforms (e.g., native tests) */
#include <stdlib.h>
#include <time.h>
#endif

#include <string.h>

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

static const char *TAG = "utlp_security";

/** @brief Initialization flag */
static bool s_initialized = false;

/*============================================================================
 * WELL-KNOWN KEYS
 *==========================================================================*/

/**
 * @brief Zero Key for Public Mode
 *
 * All 16 bytes are 0x00. Used when no Swarm DNA is configured.
 * Maintains fixed packet geometry and traffic analysis resistance.
 */
const uint8_t UTLP_ZERO_KEY[UTLP_AES_KEY_SIZE] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

bool utlp_hal_security_init(void)
{
    if (s_initialized) {
        return true;  /* Already initialized */
    }

    /* mbedtls doesn't require explicit init for AES/SHA256 */
    /* ESP-IDF initializes the crypto hardware automatically */

#ifndef ESP_PLATFORM
    /* For non-ESP platforms, seed the random number generator */
    srand((unsigned int)time(NULL));
#endif

    s_initialized = true;
    utlp_hal_log_info(TAG, "Security HAL initialized (AES-128-CTR + SHA-256)");

    return true;
}

/*============================================================================
 * AES-128-CTR OPERATIONS
 *
 * Purple Team Directive 1: Enforce "Stateless" AES-CTR
 *
 * THE TRAP: mbedtls_aes_crypt_ctr() maintains internal state across calls:
 *   - nc_off: position within the current keystream block
 *   - nonce_counter: incremented counter for each 16-byte block
 *   - stream_block: cached partial keystream
 *
 * If you reuse these between packets, you get WRONG keystream positions!
 *
 * THE FIX: Reset ALL state variables before EVERY call. Treat each packet
 * as an independent, stateless encryption operation.
 *
 * WHY THIS MATTERS: UTLP packets are 8-byte Introns (half a block). Without
 * reset, the second packet would start at nc_off=8, producing garbage.
 *==========================================================================*/

void utlp_hal_aes_ctr(const uint8_t key[UTLP_AES_KEY_SIZE],
                      const uint8_t nonce[UTLP_AES_BLOCK_SIZE],
                      const uint8_t *input,
                      uint8_t *output,
                      size_t len)
{
    if (key == NULL || nonce == NULL || input == NULL || output == NULL) {
        utlp_hal_log_error(TAG, "AES-CTR: NULL parameter");
        return;
    }

    if (len == 0) {
        return;  /* Nothing to do */
    }

    mbedtls_aes_context ctx;
    mbedtls_aes_init(&ctx);

    /* Set encryption key (CTR mode uses encrypt for both directions) */
    int ret = mbedtls_aes_setkey_enc(&ctx, key, 128);
    if (ret != 0) {
        utlp_hal_log_error(TAG, "AES key setup failed: %d", ret);
        mbedtls_aes_free(&ctx);
        return;
    }

    /*
     * Purple Team Directive 1: STATELESS CTR MODE
     *
     * CRITICAL: These three variables MUST be fresh for every packet.
     * DO NOT persist or reuse between calls!
     *
     * - nonce_counter: Fresh copy from caller's nonce (16 bytes)
     * - stream_block:  Zeroed (no cached keystream from previous packet)
     * - nc_off:        ZERO (start at beginning of keystream block)
     */
    uint8_t nonce_counter[UTLP_AES_BLOCK_SIZE];
    uint8_t stream_block[UTLP_AES_BLOCK_SIZE];
    size_t nc_off = 0;  /* Purple Team: MUST be 0 for every packet! */

    /* Copy nonce to counter (will be modified by mbedtls) */
    memcpy(nonce_counter, nonce, UTLP_AES_BLOCK_SIZE);
    memset(stream_block, 0, UTLP_AES_BLOCK_SIZE);  /* Purple Team: No cached keystream! */

    /* Perform CTR encryption/decryption */
    ret = mbedtls_aes_crypt_ctr(&ctx, len, &nc_off, nonce_counter,
                                 stream_block, input, output);
    if (ret != 0) {
        utlp_hal_log_error(TAG, "AES-CTR operation failed: %d", ret);
    }

    /* Cleanup */
    mbedtls_aes_free(&ctx);

    /* Clear sensitive data from stack */
    memset(nonce_counter, 0, sizeof(nonce_counter));
    memset(stream_block, 0, sizeof(stream_block));
}

/*============================================================================
 * SHA-256 OPERATIONS
 *==========================================================================*/

void utlp_hal_sha256(const uint8_t *input,
                     size_t len,
                     uint8_t output[UTLP_SHA256_SIZE])
{
    if (input == NULL || output == NULL) {
        utlp_hal_log_error(TAG, "SHA-256: NULL parameter");
        return;
    }

    /*
     * mbedtls_sha256 parameters:
     * - input: data to hash
     * - len: length of data
     * - output: 32-byte buffer for hash
     * - is224: 0 for SHA-256, 1 for SHA-224
     */
    int ret = mbedtls_sha256(input, len, output, 0);
    if (ret != 0) {
        utlp_hal_log_error(TAG, "SHA-256 failed: %d", ret);
        memset(output, 0, UTLP_SHA256_SIZE);
    }
}

/*============================================================================
 * RANDOM NUMBER GENERATION
 *==========================================================================*/

void utlp_hal_random_bytes(uint8_t *buffer, size_t len)
{
    if (buffer == NULL || len == 0) {
        return;
    }

#ifdef ESP_PLATFORM
    /* Use ESP32 hardware RNG */
    esp_fill_random(buffer, len);
#else
    /* Fallback for non-ESP platforms (NOT cryptographically secure!) */
    for (size_t i = 0; i < len; i++) {
        buffer[i] = (uint8_t)(rand() & 0xFF);
    }
#endif
}

uint16_t utlp_hal_random_u16(void)
{
    uint16_t value;
    utlp_hal_random_bytes((uint8_t *)&value, sizeof(value));
    return value;
}
