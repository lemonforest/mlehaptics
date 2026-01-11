/**
 * @file utlp_security.c
 * @brief UTLP Security Layer - Phase 0 Stub
 *
 * PHASE 0 STUB: Minimal session_salt and packet initialization.
 * Full Bio-TOTP encryption will be added in later phases.
 *
 * @version 0.0.1 (Phase 0 Stub)
 * @date 2026-01-08
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_security.h"
#include "utlp_hal_security.h"

#include <string.h>

/* Forward declarations for logging */
void utlp_hal_log_info(const char *tag, const char *format, ...);

static const char *TAG = "UTLP_SECURITY";

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

static struct {
    uint16_t session_salt;
    uint32_t sequence_id;
    bool     initialized;
} s_security_state = {0};

/*============================================================================
 * SESSION STATE API
 *==========================================================================*/

uint16_t utlp_security_generate_session_salt(void)
{
    uint8_t rand_bytes[2];
    utlp_hal_random_bytes(rand_bytes, sizeof(rand_bytes));

    s_security_state.session_salt = (uint16_t)(rand_bytes[0] | (rand_bytes[1] << 8));
    s_security_state.initialized = true;

    utlp_hal_log_info(TAG, "Phase 0 stub: session_salt=0x%04X",
                      s_security_state.session_salt);

    return s_security_state.session_salt;
}

uint16_t utlp_security_get_session_salt(void)
{
    return s_security_state.session_salt;
}

/*============================================================================
 * KEY DERIVATION API (STUB)
 *==========================================================================*/

void utlp_security_derive_splice_key(const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                     uint64_t utlp_timestamp_us,
                                     uint8_t key_out[UTLP_DNA_SIZE])
{
    (void)utlp_timestamp_us;

    /* Phase 0: Just copy the DNA as key (public mode uses zero key) */
    memcpy(key_out, swarm_dna, UTLP_DNA_SIZE);
}

/*============================================================================
 * NONCE API
 *==========================================================================*/

void utlp_security_build_nonce(const utlp_exon_t *exon,
                               uint8_t nonce_out[16])
{
    memset(nonce_out, 0, 16);

    if (exon == NULL) {
        return;
    }

    /* Bytes 0-7: UTLP timestamp */
    memcpy(&nonce_out[0], &exon->utlp_timestamp_us, sizeof(uint64_t));

    /* Bytes 8-11: Sequence ID */
    memcpy(&nonce_out[8], &exon->sequence_id, sizeof(uint32_t));

    /* Bytes 12-13: Session salt */
    memcpy(&nonce_out[12], &exon->session_salt, sizeof(uint16_t));

    /* Bytes 14-15: Zero padding */
}

/*============================================================================
 * ENCRYPTION API (STUB - Pass-through for Phase 0)
 *==========================================================================*/

void utlp_security_encrypt_intron(utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE])
{
    (void)swarm_dna;

    /* Phase 0: No encryption - intron sent in cleartext */
    /* In public mode (zero key), this is acceptable for testing */
    (void)pkt;
}

bool utlp_security_decrypt_intron(const utlp_wire_packet_t *pkt,
                                  const uint8_t swarm_dna[UTLP_DNA_SIZE],
                                  utlp_intron_t *plaintext_out)
{
    (void)swarm_dna;

    if (pkt == NULL || plaintext_out == NULL) {
        return false;
    }

    /* Phase 0: No decryption - copy intron directly */
    memcpy(plaintext_out, &pkt->intron, sizeof(utlp_intron_t));

    return true;
}

/*============================================================================
 * PLAUSIBILITY VALIDATION (STUB)
 *==========================================================================*/

bool utlp_security_intron_plausible(const utlp_intron_t *intron)
{
    if (intron == NULL) {
        return false;
    }

    /* Phase 0: Basic range checks */
    if (intron->field.tx_power_dbm < UTLP_SECURITY_TX_POWER_MIN ||
        intron->field.tx_power_dbm > UTLP_SECURITY_TX_POWER_MAX) {
        return false;
    }

    if (intron->field.drift_ppm < -UTLP_SECURITY_DRIFT_PPM_MAX ||
        intron->field.drift_ppm > UTLP_SECURITY_DRIFT_PPM_MAX) {
        return false;
    }

    return true;
}

/*============================================================================
 * PACKET HELPERS
 *==========================================================================*/

void utlp_security_init_exon(utlp_exon_t *exon)
{
    if (exon == NULL) {
        return;
    }

    memset(exon, 0, sizeof(utlp_exon_t));

    exon->protocol_version = UTLP_PROTOCOL_VERSION;
    exon->session_salt = s_security_state.session_salt;
    exon->sequence_id = s_security_state.sequence_id++;
}

void utlp_security_init_intron(utlp_intron_t *intron)
{
    if (intron == NULL) {
        return;
    }

    /* Zero via u64 view for efficiency */
    intron->u64 = 0;

    /* Set defaults */
    intron->field.opcode = UTLP_CMD_NONE;
}
