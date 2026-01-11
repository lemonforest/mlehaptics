/**
 * @file utlp_trust.c
 * @brief STUB - The Metabolic Ledger (N≥3 feature, not implemented for N=2)
 *
 * This file provides compilation stubs for the trust/reputation system.
 * The full implementation requires N≥3 for meaningful consensus.
 *
 * @see utlp_trust.h for the complete API documentation
 * @version 0.0.0 (Stub for N=2 testing)
 */

#include "utlp_trust.h"
#include "utlp_hal.h"

static const char *TAG = "UTLP_TRUST";

/*============================================================================
 * STUB IMPLEMENTATIONS - N≥3 FEATURE NOT YET IMPLEMENTED
 *
 * These stubs allow compilation while the N=2 protocol is being validated.
 * Full implementation will be added when scaling to N≥3.
 *==========================================================================*/

void utlp_trust_init(void)
{
    utlp_hal_log_info(TAG, "Trust subsystem STUB (N>=3 feature)");
}

void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum)
{
    (void)mac;
    (void)offset_us;
    (void)stratum;
}

void utlp_trust_record_observation_arbor(const uint8_t *mac, int32_t offset_us,
                                         uint8_t stratum, uint8_t arbor_id,
                                         int8_t rssi, uint16_t session_salt)
{
    (void)mac;
    (void)offset_us;
    (void)stratum;
    (void)arbor_id;
    (void)rssi;
    (void)session_salt;
}

uint8_t utlp_trust_get_health_arbor(const uint8_t *mac, uint8_t arbor_id)
{
    (void)mac;
    (void)arbor_id;
    return UTLP_TRUST_STARTUP;  /* Default health */
}

void utlp_trust_log_spectral_coherence(const utlp_peer_ledger_t *peer,
                                       uint8_t current_arbor, uint32_t now_ms)
{
    (void)peer;
    (void)current_arbor;
    (void)now_ms;
}

void utlp_trust_snapshot_arbor(uint8_t arbor_id)
{
    (void)arbor_id;
}

bool utlp_trust_get_consensus(int32_t *out_consensus_offset)
{
    (void)out_consensus_offset;
    return false;  /* No consensus at N=2 */
}

utlp_peer_ledger_t* utlp_trust_select_best_peer(void)
{
    return NULL;  /* No peer tracking at N=2 stub */
}

void utlp_trust_log_status(void)
{
    utlp_hal_log_info(TAG, "Trust: STUB (N>=3 feature)");
}

bool utlp_trust_has_quorum(int64_t my_offset, int32_t threshold_us)
{
    (void)my_offset;
    (void)threshold_us;
    return false;  /* No quorum possible at N=2 */
}

uint8_t utlp_trust_get_peer_health(const uint8_t *mac)
{
    (void)mac;
    return UTLP_TRUST_STARTUP;
}

bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer,
                                   int64_t peer_tx_time)
{
    (void)peer;
    (void)peer_tx_time;
    return false;
}

bool utlp_trust_check_regression(const utlp_peer_ledger_t *peer,
                                 int64_t reported_tx,
                                 uint32_t now_ms)
{
    (void)peer;
    (void)reported_tx;
    (void)now_ms;
    return false;
}

void utlp_trust_update_tx_tracking(const uint8_t *mac,
                                   int64_t tx_time_us,
                                   uint32_t now_ms)
{
    (void)mac;
    (void)tx_time_us;
    (void)now_ms;
}

utlp_peer_ledger_t* utlp_trust_get_peer(const uint8_t *mac)
{
    (void)mac;
    return NULL;
}

uint8_t utlp_trust_count_neighbors_by_stratum_arbor(
    utlp_arbor_id_t arbor_id, uint8_t stratum)
{
    (void)arbor_id;
    (void)stratum;
    return 0;
}

uint8_t utlp_trust_get_best_stratum_arbor(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
    return 255;  /* Worst stratum */
}

void utlp_trust_get_coherence(utlp_coherence_t *out)
{
    if (out) {
        out->consensus_us = 0;
        out->drift_spread_us = 0;
        out->last_coherent_ms = 0;
        out->healthy_peers = 0;
        out->agreeing_peers = 0;
        out->coherence_pct = 0;
        out->is_coherent = false;
    }
}

void utlp_trust_log_coherence(void)
{
    utlp_hal_log_info(TAG, "Coherence: STUB (N>=3 feature)");
}
