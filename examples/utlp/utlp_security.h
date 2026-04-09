/**
 * @file utlp_security.h
 * @brief UTLP Security Layer - Rolling Splice-Site Security (Bio-TOTP)
 *
 * @section overview Overview
 *
 * Implements time-based encryption using the packet's own UTLP timestamp
 * as the key source. Creates "Rolling Splice-Site" security where the
 * decryption key changes every second.
 *
 * @section design Design Philosophy
 *
 * - **Hide the Physics**: TX_Power in Intron denies ranging intelligence
 * - **Publicize the Version**: Protocol_Version in Exon enables evolutionary safety
 * - **Fixed Geometry**: 32-byte packets regardless of encryption mode
 * - **Zero Key Public Mode**: Traffic analysis resistance even when "unencrypted"
 *
 * @section packet Packet Structure (32 bytes)
 *
 * ```
 * ┌─────────────────────────────────────────────────────────────┐
 * │  CLEARTEXT EXON (24 bytes)                                  │
 * ├─────────────────────────────────────────────────────────────┤
 * │  [0-3]   SequenceID          - Anti-replay counter          │
 * │  [4-11]  UTLP_Timestamp_US   - Monotonic time, nonce source │
 * │  [12-19] NTP_Timestamp_UTC   - Wall-clock or RANDOM         │
 * │  [20-21] Session_Salt        - Per-boot random              │
 * │  [22]    Stratum             - Time source depth            │
 * │  [23]    Protocol_Version    - Fixed 0x01                   │
 * ├─────────────────────────────────────────────────────────────┤
 * │  ENCRYPTED INTRON (8 bytes) - AES-128-CTR                   │
 * ├─────────────────────────────────────────────────────────────┤
 * │  [24]    TX_Power_dBm        - Hidden from adversaries      │
 * │  [25]    Battery_Level       - Scaled 0-255                 │
 * │  [26-27] Drift_PPM           - Signed int16                 │
 * │  [28]    Opcode              - Defines payload meaning      │
 * │  [29-31] Payload[3]          - Multiplexed data (per opcode)│
 * └─────────────────────────────────────────────────────────────┘
 * ```
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
 * PROTOCOL CONSTANTS
 *
 * CRITICAL: These define the FIXED GEOMETRY. Do not modify without
 * understanding the cryptographic implications.
 *==========================================================================*/

/**
 * @brief Current protocol version (embedded in Exon byte [23])
 *
 * VERSION REGISTRY:
 *   0x01 - Scalar time (uint64_t utlp_timestamp_us at bytes [4-11])
 *          THIS IS THE ONLY VERSION IMPLEMENTED IN THIS BRANCH.
 *          32-byte fixed geometry, AES-128-CTR encrypted Intron.
 *
 *   0x02 - Vector time (phase_chord[8] replacing bytes [4-11])
 *          Described in Technical Supplement S3. EXPERIMENTAL ONLY.
 *          Uses hyperdimensional coprime cyclic representation.
 *          NOT implemented here. Beacons with 0x02 are silently dropped.
 *
 *   0x03 - Segmented vector (40-byte packet with fine segment)
 *          Described in Technical Supplement S3 Section 14.7.
 *          SPECULATIVE. NOT implemented. Silently dropped.
 *
 * RX behavior: process_beacon() in utlp.c rejects any packet where
 * protocol_version != UTLP_PROTOCOL_VERSION before interpreting the
 * timestamp field. This prevents scalar code from misreading vector
 * phase chords as uint64_t values.
 */
/**
 * @brief Normal established beacon protocol version.
 * Scalar time (uint64_t utlp_timestamp_us in bytes [4-11]).
 */
#define UTLP_PROTOCOL_VERSION           0x01

/**
 * @brief Genesis-pulsing beacon protocol version.
 *
 * Sent during first 60 seconds after boot (genesis pulse phases 1-4).
 * Same wire format as 0x01 (scalar time), but explicitly signals
 * "I am a newborn seeking swarm adoption — do NOT adopt my timeline."
 *
 * Receivers accept both 0x01 and 0xFE but use the version to guard
 * against premature adoption of unstable genesis timelines.
 *
 * @see UTLP_GENESIS_PHASE_4_END_US (60 seconds)
 */
#define UTLP_PROTOCOL_VERSION_GENESIS   0xFE

/** @brief Cleartext Exon size in bytes */
#define UTLP_EXON_SIZE              24

/** @brief Encrypted Intron size in bytes */
#define UTLP_INTRON_SIZE            8

/** @brief Total packet size (fixed geometry) */
#define UTLP_PACKET_SIZE            32

/** @brief Swarm DNA size in bytes (128-bit shared secret) */
#define UTLP_DNA_SIZE               16

/*
 * NOTE: UTLP_ZERO_KEY is declared in utlp_hal_security.h as:
 *   extern const uint8_t UTLP_ZERO_KEY[UTLP_AES_KEY_SIZE];
 *
 * Public mode zero key enables "Herd Immunity" (Purple Team PT-4):
 * When swarm_dna equals zero, the swarm operates in "public mode"
 * with deterministic but known encryption.
 */

/** @brief SHA256 output size in bytes */
#define UTLP_SHA256_SIZE            32

/*============================================================================
 * COMMAND OPCODES (Intron.command_opcode)
 *
 * Control plane messages embedded in the encrypted Intron.
 *==========================================================================*/

/**
 * @brief Command opcodes for control plane messages
 */
typedef enum {
    UTLP_CMD_NONE           = 0x00,  /**< Normal beacon (no command) */
    UTLP_CMD_GENESIS_PULSE  = 0x01,  /**< Announcing new genesis epoch */
    UTLP_CMD_DORMANCY_ENTER = 0x02,  /**< Node entering sleep */
    UTLP_CMD_DORMANCY_EXIT  = 0x03,  /**< Node waking from sleep */
    UTLP_CMD_ROLE_ANNOUNCE  = 0x04,  /**< Role change announcement */
    UTLP_CMD_RESERVED_BEGIN = 0x80   /**< 0x80-0xFF reserved for future use */
} utlp_command_opcode_t;

/*============================================================================
 * EXON - CLEARTEXT HEADER (24 bytes)
 *
 * All fields visible to adversaries. Contains timing, versioning, and
 * nonce components. NTP field randomized in Stealth Mode.
 *
 * CRITICAL: Field order is FIXED for cryptographic alignment.
 * DO NOT REORDER to optimize padding ("no box-trucking").
 *==========================================================================*/

/**
 * @brief Cleartext packet header (24 bytes)
 *
 * @warning Field order is cryptographically significant. Do not reorder.
 */
typedef struct __attribute__((packed)) {
    uint32_t sequence_id;           /**< [0-3]   Monotonic counter, anti-replay */
    uint64_t utlp_timestamp_us;     /**< [4-11]  Monotonic time, nonce component */
    uint64_t ntp_timestamp_utc;     /**< [12-19] Wall-clock, or RANDOM if stealth */
    uint16_t session_salt;          /**< [20-21] Per-boot random, nonce component */
    uint8_t  stratum;               /**< [22]    Time source depth */
    uint8_t  protocol_version;      /**< [23]    Protocol version (0x01) */
} utlp_exon_t;

/* Compile-time validation of Exon structure */
_Static_assert(sizeof(utlp_exon_t) == UTLP_EXON_SIZE,
               "Exon size mismatch - check struct packing");
_Static_assert(offsetof(utlp_exon_t, sequence_id) == 0,
               "sequence_id must be at offset 0");
_Static_assert(offsetof(utlp_exon_t, utlp_timestamp_us) == 4,
               "utlp_timestamp_us must be at offset 4");
_Static_assert(offsetof(utlp_exon_t, ntp_timestamp_utc) == 12,
               "ntp_timestamp_utc must be at offset 12");
_Static_assert(offsetof(utlp_exon_t, session_salt) == 20,
               "session_salt must be at offset 20");
_Static_assert(offsetof(utlp_exon_t, stratum) == 22,
               "stratum must be at offset 22");
_Static_assert(offsetof(utlp_exon_t, protocol_version) == 23,
               "protocol_version must be at offset 23");

/*============================================================================
 * INTRON - ENCRYPTED PAYLOAD (8 bytes)
 *
 * Hidden from adversaries via AES-128-CTR. TX_Power concealed to deny
 * range estimation. Drift_PPM concealed to prevent clock fingerprinting.
 *
 * CRITICAL: Field order is FIXED for cryptographic alignment.
 * DO NOT REORDER to optimize padding ("no box-trucking").
 *
 * UNION DESIGN: Three access patterns for different use cases:
 * - .field.*  : Application View - clean C struct access for logic
 * - .u64      : Crypto View - fast 64-bit XOR with keystream
 * - .raw[8]   : Byte View - direct byte manipulation
 *
 * MULTIPLEXING: The 'opcode' field (byte 4) defines the meaning of
 * 'payload[3]' (bytes 5-7):
 *
 * | Opcode | Name              | payload[0] | payload[1] | payload[2] |
 * |--------|-------------------|------------|------------|------------|
 * | 0x00   | Heartbeat         | CPU_Load   | Role       | Error_Code |
 * | 0x01   | Extended Physics  | Reserved   | Reserved   | Reserved   |
 * | 0x02   | Dormancy Enter    | Sleep_Mode | Wake_Cond  | Reserved   |
 * | 0x03   | Dormancy Exit     | Wake_Src   | Reserved   | Reserved   |
 * | 0x04   | Role Announce     | New_Role   | Old_Role   | Reserved   |
 * | 0x80+  | Reserved          | TBD        | TBD        | TBD        |
 *==========================================================================*/

/**
 * @brief Encrypted packet payload (8 bytes) - Union for multi-view access
 *
 * @warning Field order is cryptographically significant. Do not reorder.
 *
 * Usage examples:
 * @code
 * // Application logic - clean struct access
 * intron.field.tx_power_dbm = -10;
 * intron.field.opcode = UTLP_CMD_NONE;
 * intron.field.payload[0] = cpu_load_percent;
 *
 * // Crypto operation - single 64-bit XOR
 * intron.u64 ^= keystream_block;
 *
 * // Byte-level access for serialization
 * memcpy(buffer, intron.raw, 8);
 * @endcode
 */
typedef union {
    /**
     * @brief Application View - Structured field access
     *
     * Use for all application logic: reading/writing individual fields,
     * semantic validation, logging, etc.
     */
    struct __attribute__((packed)) {
        int8_t   tx_power_dbm;      /**< [0]   TX power (hidden from adversaries) */
        uint8_t  battery_level;     /**< [1]   Scaled voltage 0-255 */
        int16_t  drift_ppm;         /**< [2-3] Signed drift in PPM (±32767) */
        uint8_t  opcode;            /**< [4]   Command opcode (defines payload meaning) */
        uint8_t  payload[3];        /**< [5-7] Multiplexed data (meaning per opcode) */
    } field;

    /**
     * @brief Crypto View - Fast 64-bit XOR
     *
     * Use for AES-CTR encryption/decryption: XOR entire Intron with
     * keystream in a single 64-bit operation instead of byte-by-byte.
     */
    uint64_t u64;

    /**
     * @brief Byte View - Raw byte access
     *
     * Use for serialization, memcpy operations, and low-level manipulation.
     */
    uint8_t raw[UTLP_INTRON_SIZE];
} utlp_intron_t;

/* Compile-time validation of Intron union */
_Static_assert(sizeof(utlp_intron_t) == UTLP_INTRON_SIZE,
               "Intron size mismatch - must be exactly 8 bytes");
_Static_assert(sizeof(((utlp_intron_t *)0)->field) == UTLP_INTRON_SIZE,
               "Intron.field struct size mismatch");
_Static_assert(offsetof(utlp_intron_t, field.tx_power_dbm) == 0,
               "tx_power_dbm must be at offset 0");
_Static_assert(offsetof(utlp_intron_t, field.battery_level) == 1,
               "battery_level must be at offset 1");
_Static_assert(offsetof(utlp_intron_t, field.drift_ppm) == 2,
               "drift_ppm must be at offset 2");
_Static_assert(offsetof(utlp_intron_t, field.opcode) == 4,
               "opcode must be at offset 4");
_Static_assert(offsetof(utlp_intron_t, field.payload) == 5,
               "payload must be at offset 5");

/*============================================================================
 * COMPLETE PACKET (32 bytes)
 *
 * Union allows access to Intron as either typed struct or raw bytes.
 *==========================================================================*/

/**
 * @brief Complete UTLP v1 wire packet (32 bytes)
 *
 * Named `utlp_wire_packet_t` to distinguish from the HAL-level receive buffer
 * `utlp_packet_t` in utlp_hal.h. This struct represents the actual 32-byte
 * over-the-air format; the HAL packet wraps this in a receive buffer with
 * metadata (RSSI, timestamp, MAC, etc.).
 *
 * @warning Intron must start at exactly offset 24 (UTLP_EXON_SIZE).
 */
typedef struct __attribute__((packed)) {
    utlp_exon_t exon;               /**< [0-23]  Cleartext header */
    union {
        utlp_intron_t intron;       /**< [24-31] Decrypted payload (typed) */
        uint8_t intron_raw[UTLP_INTRON_SIZE]; /**< [24-31] Raw encrypted bytes */
    };
} utlp_wire_packet_t;

/* Compile-time validation of complete packet */
_Static_assert(sizeof(utlp_wire_packet_t) == UTLP_PACKET_SIZE,
               "Packet size mismatch - must be exactly 32 bytes");
_Static_assert(offsetof(utlp_wire_packet_t, exon) == 0,
               "Exon must start at offset 0");
_Static_assert(offsetof(utlp_wire_packet_t, intron) == UTLP_EXON_SIZE,
               "Intron must start at offset 24 (cryptographic boundary)");

/*============================================================================
 * SECURITY CONFIGURATION CONSTANTS
 *
 * Purple Team Directive 5: Strict Plausibility Checking
 *
 * Without an authentication tag (AES-CTR mode), we rely on semantic validation
 * to detect wrong-key decryptions. These constants define "physically plausible"
 * ranges that random garbage is unlikely to satisfy.
 *
 * False positive probability: ~0.007% per packet (acceptable for swarm sync)
 *==========================================================================*/

/**
 * @brief TX power plausible range minimum (dBm)
 *
 * -40 dBm covers lowest ESP32 power settings. Values below this are
 * implausible for any real hardware transmission.
 */
#define UTLP_SECURITY_TX_POWER_MIN      (-40)

/**
 * @brief TX power plausible range maximum (dBm)
 *
 * +21 dBm is maximum legal EIRP in most jurisdictions.
 */
#define UTLP_SECURITY_TX_POWER_MAX      (21)

/**
 * @brief Drift PPM plausible range (±2000 PPM)
 *
 * ±2000 PPM covers worst-case crystal oscillator drift including
 * temperature extremes. Values outside this indicate wrong key or corruption.
 */
#define UTLP_SECURITY_DRIFT_PPM_MAX     (2000)

/**
 * @brief Maximum CPU load percentage for Heartbeat plausibility
 *
 * CPU load > 100% is physically impossible.
 */
#define UTLP_SECURITY_CPU_LOAD_MAX      (100)

/**
 * @brief Maximum role value for Heartbeat plausibility
 *
 * Valid roles: 0=GENESIS, 1=SERVER, 2=CLIENT, 3=OBSERVER
 * Values > 3 indicate wrong key decryption.
 */
#define UTLP_SECURITY_ROLE_MAX          (3)

/** @brief Microseconds per second (for key quantization) */
#define UTLP_SECURITY_US_PER_SEC        (1000000ULL)

/*============================================================================
 * SECURITY API - KEY DERIVATION
 *==========================================================================*/

/**
 * @brief Derive splice key from Swarm DNA + quantized timestamp
 *
 * Key = SHA256( Swarm_DNA || Quantize_1s(UTLP_Timestamp_US) )[0:16]
 *
 * The key changes every second. Receivers must try T-1, T, T+1 windows.
 *
 * @param swarm_dna         16-byte shared secret (use UTLP_ZERO_KEY for public)
 * @param utlp_timestamp_us Packet timestamp (will be quantized to seconds)
 * @param key_out           16-byte output buffer for derived AES key
 */
void utlp_security_derive_splice_key(const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                     uint64_t utlp_timestamp_us,
                                     uint8_t key_out[UTLP_DNA_SIZE]);

/*============================================================================
 * SECURITY API - NONCE CONSTRUCTION
 *==========================================================================*/

/**
 * @brief Build 16-byte nonce from packet Exon fields
 *
 * Nonce construction:
 * - Bytes 0-7:   UTLP_Timestamp_US
 * - Bytes 8-11:  SequenceID
 * - Bytes 12-13: Session_Salt (per-boot random)
 * - Bytes 14-15: Zero padding
 *
 * Session_Salt prevents nonce reuse across device reboots.
 *
 * @param exon      Pointer to Exon (source of nonce components)
 * @param nonce_out 16-byte output buffer
 */
void utlp_security_build_nonce(const utlp_exon_t *exon,
                               uint8_t nonce_out[16]);

/*============================================================================
 * SECURITY API - ENCRYPTION/DECRYPTION
 *==========================================================================*/

/**
 * @brief Encrypt Intron payload (for beacon transmission)
 *
 * @param pkt       Packet with populated Exon and plaintext Intron
 * @param swarm_dna 16-byte shared secret (use UTLP_ZERO_KEY for public)
 *
 * @note Modifies pkt->intron_raw in place with ciphertext
 */
void utlp_security_encrypt_intron(utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE]);

/**
 * @brief Decrypt Intron with sliding window (T-1, T, T+1)
 *
 * AES-CTR has no authentication tag. We decrypt with each key window
 * and check if the result is semantically plausible.
 *
 * @param pkt           Packet with ciphertext in intron_raw
 * @param swarm_dna     16-byte shared secret (use UTLP_ZERO_KEY for public)
 * @param plaintext_out Output buffer for decrypted Intron (if successful)
 *
 * @return true if any window produced plausible values, false otherwise
 *
 * @note On failure, packet should be silently dropped (no health penalty)
 */
bool utlp_security_decrypt_intron(const utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                  utlp_intron_t *plaintext_out);

/*============================================================================
 * SECURITY API - PLAUSIBILITY VALIDATION
 *==========================================================================*/

/**
 * @brief Check if decrypted Intron values are semantically plausible
 *
 * Without authentication tag (CTR mode), we use semantic validation:
 * - TX_Power_dBm: -30 to +21 dBm (typical ESP32 range)
 * - Command_Opcode: 0x00-0x04 defined, 0x80+ reserved
 * - Drift_PPM: ±1000 is reasonable
 *
 * Random garbage has very low chance of passing all checks.
 *
 * @param intron Pointer to decrypted Intron candidate
 *
 * @return true if values are plausible, false if likely garbage
 */
bool utlp_security_intron_plausible(const utlp_intron_t *intron);

/*============================================================================
 * SECURITY API - SESSION STATE
 *==========================================================================*/

/**
 * @brief Generate per-boot Session_Salt
 *
 * Call once during UTLP initialization. Returns a random 16-bit value
 * that will be included in all beacons for this session.
 *
 * @return Random 16-bit Session_Salt
 */
uint16_t utlp_security_generate_session_salt(void);

/**
 * @brief Get the current Session_Salt
 *
 * @return Session_Salt generated at initialization
 */
uint16_t utlp_security_get_session_salt(void);

/*============================================================================
 * SECURITY API - PACKET HELPERS
 *==========================================================================*/

/**
 * @brief Initialize an Exon with standard fields
 *
 * Populates:
 * - protocol_version: UTLP_PROTOCOL_VERSION
 * - session_salt: from security module state
 * - sequence_id: auto-incremented
 *
 * Caller must still set:
 * - utlp_timestamp_us
 * - ntp_timestamp_utc (or fill with random if stealth)
 * - stratum
 *
 * @param exon Exon structure to initialize
 */
void utlp_security_init_exon(utlp_exon_t *exon);

/**
 * @brief Initialize an Intron with default values
 *
 * Zeros all 8 bytes via .u64, then populates:
 * - field.opcode: UTLP_CMD_NONE
 * - field.payload[0..2]: zeros
 *
 * Caller must still set:
 * - field.tx_power_dbm
 * - field.battery_level
 * - field.drift_ppm
 * - field.payload[] (if opcode != UTLP_CMD_NONE)
 *
 * @param intron Pointer to Intron union to initialize
 */
void utlp_security_init_intron(utlp_intron_t *intron);

#ifdef __cplusplus
}
#endif
