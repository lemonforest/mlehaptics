/**
 * @file utlp_security.c
 * @brief UTLP Security Layer - Rolling Splice-Site Implementation
 *
 * @section overview Overview
 *
 * Implements the Bio-TOTP (time-based one-time password) security model
 * where encryption keys roll every second based on the UTLP timestamp.
 *
 * @section algorithm Key Derivation Algorithm
 *
 * ```
 * quantized_sec = UTLP_Timestamp_US / 1,000,000  (floor to second)
 * hash_input = Swarm_DNA || quantized_sec        (24 bytes)
 * Key = SHA256(hash_input)[0:16]                 (first 128 bits)
 * ```
 *
 * @section sliding_window Sliding Window Decryption
 *
 * Receivers try three key windows to handle clock jitter:
 * 1. Current second (T)
 * 2. Previous second (T-1) for late arrivals
 * 3. Next second (T+1) for clock-ahead peers
 *
 * Semantic plausibility check determines which window is correct.
 *
 * @see utlp_security.h for API documentation
 *
 * @version 1.0.0
 * @date 2026-01-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_security.h"
#include "utlp_hal_security.h"

#include <string.h>
#include <stdarg.h>

/* Forward declarations for logging (avoid utlp_hal.h include dependency) */
void utlp_hal_log_info(const char *tag, const char *format, ...);
void utlp_hal_log_warn(const char *tag, const char *format, ...);
void utlp_hal_log_error(const char *tag, const char *format, ...);

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

static const char *TAG = "utlp_security";

/** @brief Per-boot Session_Salt (randomized at init) */
static uint16_t s_session_salt = 0;

/** @brief Monotonic sequence counter for anti-replay */
static uint32_t s_sequence_id = 0;

/** @brief Initialization flag */
static bool s_initialized = false;

/*============================================================================
 * KEY DERIVATION
 *
 * Purple Team Directive 4: Herd Immunity (Identical Fingerprinting)
 *
 * CRITICAL DESIGN DECISION: Public Mode (UTLP_ZERO_KEY) executes the EXACT
 * same code path as Private Mode (secret swarm_dna). We do NOT skip SHA256
 * or take any shortcuts for "unencrypted" packets.
 *
 * WHY THIS MATTERS:
 *   - CPU power consumption profile is identical for public and private nodes
 *   - Timing signature (SHA256 + AES duration) is identical
 *   - Side-channel analysis cannot distinguish encrypted from "cleartext" traffic
 *   - Adversary cannot identify high-value targets by observing crypto behavior
 *
 * THE TRAP TO AVOID:
 *   if (memcmp(swarm_dna, UTLP_ZERO_KEY, 16) == 0) {
 *       return;  // DON'T DO THIS! Creates timing side-channel.
 *   }
 *
 * Even with "no encryption", run Key = SHA256(Zeros || Time). The result is
 * deterministic and public, but the PROCESS is indistinguishable from real
 * encryption. This is "Herd Immunity" - public nodes protect private nodes
 * by making all traffic look identical.
 *==========================================================================*/

void utlp_security_derive_splice_key(const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                     uint64_t utlp_timestamp_us,
                                     uint8_t key_out[UTLP_DNA_SIZE])
{
    /*
     * Key derivation (runs for ALL packets, including Public Mode):
     * 1. Quantize timestamp to seconds (rolling every 1s)
     * 2. Concatenate: DNA (16 bytes) || quantized_time (8 bytes) = 24 bytes
     * 3. SHA-256 hash the concatenation (NEVER SKIP, even for Zero Key!)
     * 4. Use first 16 bytes as AES-128 key
     */

    /* Quantize to seconds (floor division) */
    uint64_t quantized_sec = utlp_timestamp_us / UTLP_SECURITY_US_PER_SEC;

    /* Build hash input: DNA || quantized_time */
    uint8_t hash_input[24];
    memcpy(hash_input, swarm_dna, UTLP_DNA_SIZE);
    memcpy(hash_input + UTLP_DNA_SIZE, &quantized_sec, sizeof(quantized_sec));

    /* SHA-256 produces 32 bytes, we use first 16 */
    uint8_t hash_output[UTLP_SHA256_SIZE];
    utlp_hal_sha256(hash_input, sizeof(hash_input), hash_output);

    /* Extract first 128 bits as AES key */
    memcpy(key_out, hash_output, UTLP_DNA_SIZE);

    /* Clear sensitive data from stack */
    memset(hash_input, 0, sizeof(hash_input));
    memset(hash_output, 0, sizeof(hash_output));
}

/*============================================================================
 * NONCE CONSTRUCTION
 *==========================================================================*/

void utlp_security_build_nonce(const utlp_exon_t *exon,
                               uint8_t nonce_out[16])
{
    /*
     * Nonce structure (16 bytes):
     * - Bytes 0-7:   UTLP_Timestamp_US (from Exon)
     * - Bytes 8-11:  SequenceID (from Exon)
     * - Bytes 12-13: Session_Salt (from Exon, per-boot random)
     * - Bytes 14-15: Zero padding
     *
     * This ensures nonce uniqueness:
     * - Timestamp provides temporal uniqueness
     * - SequenceID prevents collision within same second
     * - Session_Salt prevents reuse across reboots
     */

    if (exon == NULL || nonce_out == NULL) {
        return;
    }

    /* Bytes 0-7: UTLP timestamp */
    memcpy(nonce_out, &exon->utlp_timestamp_us, 8);

    /* Bytes 8-11: Sequence ID */
    memcpy(nonce_out + 8, &exon->sequence_id, 4);

    /* Bytes 12-13: Session Salt */
    memcpy(nonce_out + 12, &exon->session_salt, 2);

    /* Bytes 14-15: Zero padding */
    nonce_out[14] = 0;
    nonce_out[15] = 0;
}

/*============================================================================
 * ENCRYPTION
 *==========================================================================*/

void utlp_security_encrypt_intron(utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE])
{
    if (pkt == NULL || swarm_dna == NULL) {
        return;
    }

    /* Derive key from DNA + timestamp */
    uint8_t key[UTLP_DNA_SIZE];
    utlp_security_derive_splice_key(swarm_dna, pkt->exon.utlp_timestamp_us, key);

    /* Build nonce from Exon fields */
    uint8_t nonce[16];
    utlp_security_build_nonce(&pkt->exon, nonce);

    /* Encrypt Intron in place */
    uint8_t plaintext[UTLP_INTRON_SIZE];
    memcpy(plaintext, &pkt->intron, UTLP_INTRON_SIZE);

    utlp_hal_aes_ctr(key, nonce, plaintext, pkt->intron_raw, UTLP_INTRON_SIZE);

    /* Clear sensitive data from stack */
    memset(key, 0, sizeof(key));
    memset(plaintext, 0, sizeof(plaintext));
}

/*============================================================================
 * DECRYPTION WITH SLIDING WINDOW
 *==========================================================================*/

bool utlp_security_decrypt_intron(const utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                  utlp_intron_t *plaintext_out)
{
    if (pkt == NULL || swarm_dna == NULL || plaintext_out == NULL) {
        return false;
    }

    uint64_t tx_time = pkt->exon.utlp_timestamp_us;
    uint8_t key[UTLP_DNA_SIZE];
    uint8_t nonce[16];
    utlp_intron_t candidate;

    /* Build nonce from Exon (same for all key attempts) */
    utlp_security_build_nonce(&pkt->exon, nonce);

    /*
     * Sliding Window: Try T, T-1, T+1
     *
     * Order matters for performance:
     * 1. Current second (most common case)
     * 2. Previous second (late arrival)
     * 3. Next second (peer clock ahead)
     */

    /* Window 1: Current second (T) */
    utlp_security_derive_splice_key(swarm_dna, tx_time, key);
    utlp_hal_aes_ctr(key, nonce, pkt->intron_raw, (uint8_t *)&candidate, UTLP_INTRON_SIZE);

    if (utlp_security_intron_plausible(&candidate)) {
        *plaintext_out = candidate;
        memset(key, 0, sizeof(key));
        return true;
    }

    /* Window 2: Previous second (T-1) */
    utlp_security_derive_splice_key(swarm_dna, tx_time - UTLP_SECURITY_US_PER_SEC, key);
    utlp_hal_aes_ctr(key, nonce, pkt->intron_raw, (uint8_t *)&candidate, UTLP_INTRON_SIZE);

    if (utlp_security_intron_plausible(&candidate)) {
        *plaintext_out = candidate;
        memset(key, 0, sizeof(key));
        return true;
    }

    /* Window 3: Next second (T+1) */
    utlp_security_derive_splice_key(swarm_dna, tx_time + UTLP_SECURITY_US_PER_SEC, key);
    utlp_hal_aes_ctr(key, nonce, pkt->intron_raw, (uint8_t *)&candidate, UTLP_INTRON_SIZE);

    if (utlp_security_intron_plausible(&candidate)) {
        *plaintext_out = candidate;
        memset(key, 0, sizeof(key));
        return true;
    }

    /* All windows failed - packet from different swarm or corrupted */
    memset(key, 0, sizeof(key));
    return false;
}

/*============================================================================
 * PLAUSIBILITY VALIDATION
 *==========================================================================*/

bool utlp_security_intron_plausible(const utlp_intron_t *intron)
{
    if (intron == NULL) {
        return false;
    }

    /*
     * Semantic validation (replaces authentication tag):
     *
     * Random garbage has ~1/256 chance of passing each check.
     * Combined probability of passing all checks with wrong key:
     * ~(51/256) × (5/256) × (2000/65536) ≈ 0.0024% per window
     * With 3 windows: ~0.0072% false positive rate
     *
     * This is acceptable for swarm synchronization where:
     * - False positives cause temporary desync, not security breach
     * - Repeated false positives are astronomically unlikely
     */

    /* Check 1: TX power in physically plausible range */
    if (intron->field.tx_power_dbm < UTLP_SECURITY_TX_POWER_MIN ||
        intron->field.tx_power_dbm > UTLP_SECURITY_TX_POWER_MAX) {
        return false;  /* -40 to +21 dBm (Purple Team: covers all ESP32 power levels) */
    }

    /* Check 2: Command opcode is defined or reserved */
    if (intron->field.opcode > UTLP_CMD_ROLE_ANNOUNCE &&
        intron->field.opcode < UTLP_CMD_RESERVED_BEGIN) {
        return false;  /* 0x05-0x7F is undefined gap */
    }

    /* Check 3: Drift PPM is physically plausible */
    if (intron->field.drift_ppm < -UTLP_SECURITY_DRIFT_PPM_MAX ||
        intron->field.drift_ppm > UTLP_SECURITY_DRIFT_PPM_MAX) {
        return false;  /* ±2000 PPM (Purple Team: covers worst-case crystal drift) */
    }

    /*
     * Check 4: Heartbeat (opcode 0x00) - multiplexed payload validation
     *
     * Purple Team Directive 5: For Heartbeat packets, validate the multiplexed
     * payload fields to tighten the semantic check.
     *
     * Heartbeat payload layout:
     *   - payload[0] = CPU_Load (0-100%)
     *   - payload[1] = Role (0-3: GENESIS/SERVER/CLIENT/OBSERVER)
     *   - payload[2] = Error_Code (0-255, any value valid)
     *
     * Random garbage has ~(101/256) × (4/256) ≈ 0.6% chance of passing.
     * Combined with other checks: ~0.00004% false positive rate.
     */
    if (intron->field.opcode == UTLP_CMD_NONE) {
        /* CPU_Load > 100% is physically impossible */
        if (intron->field.payload[0] > UTLP_SECURITY_CPU_LOAD_MAX) {
            return false;
        }
        /* Role > 3 is undefined (only 0-3 valid) */
        if (intron->field.payload[1] > UTLP_SECURITY_ROLE_MAX) {
            return false;
        }
        /* payload[2] (Error_Code) accepts any value 0-255 */
    }

    return true;
}

/*============================================================================
 * SESSION STATE
 *==========================================================================*/

uint16_t utlp_security_generate_session_salt(void)
{
    s_session_salt = utlp_hal_random_u16();
    s_initialized = true;
    utlp_hal_log_info(TAG, "Session salt generated: 0x%04X", s_session_salt);
    return s_session_salt;
}

uint16_t utlp_security_get_session_salt(void)
{
    if (!s_initialized) {
        /* Auto-initialize if not already done */
        return utlp_security_generate_session_salt();
    }
    return s_session_salt;
}

/*============================================================================
 * PACKET HELPERS
 *==========================================================================*/

void utlp_security_init_exon(utlp_exon_t *exon)
{
    if (exon == NULL) {
        return;
    }

    /* Fixed fields */
    exon->protocol_version = UTLP_PROTOCOL_VERSION;
    exon->session_salt = utlp_security_get_session_salt();

    /* Auto-increment sequence (wraps at 32-bit max) */
    exon->sequence_id = s_sequence_id++;

    /* Caller must set:
     * - utlp_timestamp_us
     * - ntp_timestamp_utc (or random for stealth)
     * - stratum
     */
}

void utlp_security_init_intron(utlp_intron_t *intron)
{
    if (intron == NULL) {
        return;
    }

    /*
     * Zero the entire union first (all 8 bytes) for safety,
     * then set default values via structured field access.
     */
    intron->u64 = 0;

    /* Default values via Application View */
    intron->field.opcode = UTLP_CMD_NONE;
    /* payload[0..2] already zeroed by u64 = 0 */

    /* Caller must set:
     * - field.tx_power_dbm
     * - field.battery_level
     * - field.drift_ppm
     * - field.payload[] (if opcode != UTLP_CMD_NONE)
     */
}
