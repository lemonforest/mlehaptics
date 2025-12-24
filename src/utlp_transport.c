/**
 * @file utlp_transport.c
 * @brief UTLP Transport HAL - Common Implementation
 *
 * Platform-agnostic functionality shared across all transport implementations.
 * Currently provides:
 * - HKDF-SHA256 key derivation for session encryption
 *
 * Vendor-specific implementations (espnow, shockburst) provide the actual
 * transport operations and register their vtable.
 *
 * @see utlp_transport.h
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#include "utlp_transport.h"
#include <string.h>

// mbedTLS for hardware-accelerated HKDF-SHA256
// On ESP32-C6, this uses the hardware SHA accelerator automatically
#include "mbedtls/hkdf.h"
#include "mbedtls/md.h"

// Hardware RNG for nonce generation
// This is the only platform-specific include in the common code
// (could be abstracted further if needed)
#if defined(ESP_PLATFORM)
#include "esp_random.h"
#define UTLP_FILL_RANDOM(buf, len) esp_fill_random(buf, len)
#else
// Fallback for non-ESP platforms (would need proper implementation)
#include <stdlib.h>
#define UTLP_FILL_RANDOM(buf, len) do { \
    for (size_t i = 0; i < (len); i++) ((uint8_t*)(buf))[i] = rand(); \
} while(0)
#endif

// ============================================================================
// CONSTANTS
// ============================================================================

/** @brief HKDF info string for domain separation */
static const char *UTLP_HKDF_INFO = "UTLP-SESSION-KEY-v1";

// ============================================================================
// GLOBAL TRANSPORT INSTANCE
// ============================================================================

/**
 * @brief Default transport pointer (NULL until initialized)
 *
 * Set by vendor-specific init function, e.g.:
 *   utlp_transport = &espnow_transport_ops;
 */
const utlp_transport_ops_t *utlp_transport = NULL;

// ============================================================================
// KEY DERIVATION IMPLEMENTATION
// ============================================================================

utlp_err_t utlp_generate_key_exchange(utlp_key_exchange_t *key_exchange,
                                       const uint8_t local_mac[UTLP_MAC_SIZE])
{
    if (key_exchange == NULL || local_mac == NULL) {
        return UTLP_ERR_INVALID_ARG;
    }

    // Generate cryptographically random nonce
    UTLP_FILL_RANDOM(key_exchange->nonce, UTLP_NONCE_SIZE);

    // Include local MAC for verification by responder
    memcpy(key_exchange->initiator_mac, local_mac, UTLP_MAC_SIZE);

    return UTLP_OK;
}

utlp_err_t utlp_derive_session_key(const uint8_t initiator_mac[UTLP_MAC_SIZE],
                                    const uint8_t responder_mac[UTLP_MAC_SIZE],
                                    const uint8_t nonce[UTLP_NONCE_SIZE],
                                    uint8_t key_out[UTLP_KEY_SIZE])
{
    if (initiator_mac == NULL || responder_mac == NULL ||
        nonce == NULL || key_out == NULL) {
        return UTLP_ERR_INVALID_ARG;
    }

    // Build input keying material: INITIATOR_MAC || RESPONDER_MAC || nonce
    // Total: 6 + 6 + 8 = 20 bytes
    // Ordering is canonical: initiator first, then responder
    uint8_t ikm[UTLP_MAC_SIZE + UTLP_MAC_SIZE + UTLP_NONCE_SIZE];
    memcpy(ikm, initiator_mac, UTLP_MAC_SIZE);
    memcpy(ikm + UTLP_MAC_SIZE, responder_mac, UTLP_MAC_SIZE);
    memcpy(ikm + UTLP_MAC_SIZE + UTLP_MAC_SIZE, nonce, UTLP_NONCE_SIZE);

    // Get SHA-256 message digest info for HKDF
    const mbedtls_md_info_t *md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (md_info == NULL) {
        memset(ikm, 0, sizeof(ikm));  // Clear sensitive data
        return UTLP_ERR_CRYPTO_FAILED;
    }

    // Derive key using HKDF-SHA256
    // - No salt (NULL, 0) - the nonce provides uniqueness
    // - Info string provides domain separation
    int ret = mbedtls_hkdf(
        md_info,
        NULL, 0,                                    // salt (optional)
        ikm, sizeof(ikm),                           // input keying material
        (const uint8_t *)UTLP_HKDF_INFO,            // info string
        strlen(UTLP_HKDF_INFO),                     // info length
        key_out, UTLP_KEY_SIZE                      // output key
    );

    // Zero out sensitive input keying material
    memset(ikm, 0, sizeof(ikm));

    if (ret != 0) {
        return UTLP_ERR_CRYPTO_FAILED;
    }

    return UTLP_OK;
}
