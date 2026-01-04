/**
 * @file utlp_hal_security.h
 * @brief UTLP HAL Security Layer - Crypto Abstraction
 *
 * @section overview Overview
 *
 * Hardware Abstraction Layer for cryptographic operations. Wraps mbedtls
 * for ESP32-C6 (hardware-accelerated AES) and provides clean interface
 * for future Silicon Labs PSA Crypto migration.
 *
 * @section design Design Philosophy
 *
 * - **Single Code Path**: Always encrypt, even in Public Mode (Zero Key)
 * - **Fixed Geometry**: AES-128-CTR preserves packet size exactly
 * - **Hardware Acceleration**: Uses ESP32-C6 AES accelerator via mbedtls
 *
 * @section herd_immunity Purple Team Directive 4: Herd Immunity
 *
 * **CRITICAL DESIGN DECISION**: Public and Private nodes execute identical
 * crypto code paths. Do NOT optimize Public Mode by skipping SHA256 or AES.
 *
 * **Why This Matters:**
 * - CPU power profile is identical (no side-channel leakage)
 * - Timing signature is identical (no timing attacks)
 * - Traffic analysis cannot distinguish encrypted from "cleartext"
 * - Public nodes provide "cover" for private nodes in mixed swarms
 *
 * **The Trap to Avoid:**
 * @code
 * // BAD - Creates timing side-channel!
 * if (is_zero_key(dna)) {
 *     memcpy(output, input, 8);  // Skip crypto for "public" mode
 *     return;
 * }
 * @endcode
 *
 * **Correct Approach:**
 * @code
 * // GOOD - Run SHA256 + AES even for Zero Key
 * key = sha256(dna || time);  // Even if dna is all zeros
 * aes_ctr(key, nonce, input, output);
 * @endcode
 *
 * The result for Zero Key is deterministic and public, but the PROCESS is
 * indistinguishable from real encryption. This is "Herd Immunity" - public
 * nodes protect private nodes by making all traffic look identical.
 *
 * @section prior_art Prior Art Claims
 *
 * This module supports the following prior art claims:
 * - **Claim 255**: Rolling Splice-Site Security (Bio-TOTP)
 *
 * @version 1.0.0
 * @date 2026-01-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CRYPTO CONSTANTS
 *==========================================================================*/

/** @brief AES-128 key size in bytes */
#define UTLP_AES_KEY_SIZE       16

/** @brief AES block size / nonce size in bytes */
#define UTLP_AES_BLOCK_SIZE     16

/** @brief SHA-256 output size in bytes */
#define UTLP_SHA256_SIZE        32

/*============================================================================
 * WELL-KNOWN KEYS
 *==========================================================================*/

/**
 * @brief Zero Key for Public Mode
 *
 * Public swarms use this well-known key. Anyone can decrypt, but packets
 * are still scrambled to maintain fixed geometry and traffic analysis
 * resistance. Public and Private packets are indistinguishable by size.
 *
 * This is NOT "unencrypted" - it's encryption with a known key.
 */
extern const uint8_t UTLP_ZERO_KEY[UTLP_AES_KEY_SIZE];

/*============================================================================
 * AES-128-CTR OPERATIONS
 *
 * Stream cipher mode - ciphertext length equals plaintext length exactly.
 * Same function encrypts and decrypts (CTR is symmetric).
 *==========================================================================*/

/**
 * @brief Initialize the security HAL
 *
 * Call once during UTLP initialization. Sets up any required crypto
 * contexts for hardware acceleration.
 *
 * @return true on success, false on crypto subsystem failure
 */
bool utlp_hal_security_init(void);

/**
 * @brief AES-128-CTR encrypt/decrypt
 *
 * Stream cipher mode: Same function for encrypt and decrypt.
 * Output length EXACTLY equals input length (fixed geometry).
 *
 * @param key       16-byte AES key (from splice key derivation)
 * @param nonce     16-byte nonce (from Exon fields)
 * @param input     Plaintext or ciphertext input
 * @param output    Ciphertext or plaintext output
 * @param len       Length in bytes
 *
 * @note Uses mbedtls_aes_crypt_ctr internally (hardware-accelerated on ESP32-C6)
 */
void utlp_hal_aes_ctr(const uint8_t key[UTLP_AES_KEY_SIZE],
                      const uint8_t nonce[UTLP_AES_BLOCK_SIZE],
                      const uint8_t *input,
                      uint8_t *output,
                      size_t len);

/*============================================================================
 * SHA-256 OPERATIONS
 *
 * Used for key derivation: Key = SHA256(DNA || QuantizedTime)[0:16]
 *==========================================================================*/

/**
 * @brief Compute SHA-256 hash
 *
 * @param input     Data to hash
 * @param len       Length of input in bytes
 * @param output    32-byte output buffer for hash
 *
 * @note Uses mbedtls_sha256 internally (hardware-accelerated on ESP32-C6)
 */
void utlp_hal_sha256(const uint8_t *input,
                     size_t len,
                     uint8_t output[UTLP_SHA256_SIZE]);

/*============================================================================
 * RANDOM NUMBER GENERATION
 *
 * Used for Session_Salt (per-boot) and NTP Stealth Mode (per-packet).
 *==========================================================================*/

/**
 * @brief Fill buffer with cryptographically secure random bytes
 *
 * @param buffer    Output buffer
 * @param len       Number of random bytes to generate
 *
 * @note Uses esp_fill_random internally (hardware RNG)
 */
void utlp_hal_random_bytes(uint8_t *buffer, size_t len);

/**
 * @brief Generate a random 16-bit value
 *
 * Convenience function for Session_Salt generation.
 *
 * @return Random 16-bit value
 */
uint16_t utlp_hal_random_u16(void);

#ifdef __cplusplus
}
#endif
