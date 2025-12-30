/**
 * @file utlp_rfip.h
 * @brief RFIP Stubs - Reference Frame Independent Positioning
 *
 * @section vision Vision: Position Without Coordinates
 *
 * Traditional positioning requires a coordinate system: GPS gives latitude/
 * longitude, indoor positioning gives (x,y) relative to a floor plan. These
 * systems assume a pre-existing reference frame defined by infrastructure.
 *
 * RFIP asks: **what if position emerged from relationships, not coordinates?**
 *
 * In biological systems, cells don't know their GPS coordinates. They know
 * their neighbors: "I am 3 cell-widths from the blood vessel, adjacent to
 * the neuron, downstream from the signal source." Position is relational.
 *
 * RFIP will implement relational positioning for UTLP:
 * - Nodes know distances to neighbors (via RTT measurements)
 * - Nodes infer topology from the trust graph
 * - No absolute coordinates needed—only relative positions matter
 *
 * This enables "spatial trust": nodes can weight observations by distance,
 * detect when a peer has physically moved, and form "apertures" for
 * environmental sensing (acoustic, seismic, RF).
 *
 * @section overview Overview
 * RFIP (Reference Frame Independent Positioning) enables distributed
 * nodes to estimate their relative positions using time-of-flight
 * measurements. This module will integrate with the Metabolic Ledger
 * to provide position-aware trust scoring.
 *
 * @section status Implementation Status
 * This is a STUB file. Functions declared here are not implemented.
 * The stubs exist to:
 * - Reserve the API surface for future work
 * - Enable compilation of code that references RFIP types
 * - Document the intended interface
 *
 * @section future Future Implementation
 * When implemented, RFIP will:
 * - Process RTT (round-trip time) measurements from beacon exchanges
 * - Estimate peer distances using time-of-arrival trilateration
 * - Feed position data to the Metabolic Ledger for spatial trust scoring
 * - Enable "dynamic aperture beamforming" for environmental sensing
 *
 * @see docs/UTLP_Addendum_Reference_Frame_Independent_Positioning.md
 * @see docs/Connectionless_Distributed_Timing_Prior_Art.md - Section 1 (ToA Trilateration)
 *
 * @version 0.1.0 - Stub only
 * @date 2025-12-29
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Range estimate to a peer
 *
 * Contains the estimated distance to a specific peer along with
 * a confidence metric based on measurement quality.
 */
typedef struct {
    uint8_t  peer_mac[6];       /**< Peer's MAC address */
    int32_t  range_cm;          /**< Estimated range in centimeters */
    uint8_t  confidence;        /**< Confidence level 0-100% */
    uint32_t last_update_ms;    /**< Timestamp of last measurement */
} utlp_rfip_range_t;

/**
 * @brief Position estimate in local coordinate frame
 *
 * Relative position using the first 3 discovered peers as
 * reference points (arbitrary local coordinate system).
 */
typedef struct {
    int32_t  x_cm;              /**< X position in centimeters */
    int32_t  y_cm;              /**< Y position in centimeters */
    int32_t  z_cm;              /**< Z position in centimeters (if 3D) */
    uint8_t  dimensions;        /**< 2 or 3 (2D or 3D positioning) */
    uint8_t  confidence;        /**< Position confidence 0-100% */
    bool     valid;             /**< Position computed successfully? */
} utlp_rfip_position_t;

/*============================================================================
 * STUB API - Not Implemented
 *
 * These functions are declared but not defined. They exist to:
 * 1. Reserve the API surface for future implementation
 * 2. Enable compilation of code that references RFIP
 * 3. Document the intended interface
 *==========================================================================*/

/**
 * @brief Initialize the RFIP subsystem
 *
 * STUB - Not implemented.
 *
 * When implemented, will:
 * - Allocate range tracking structures
 * - Initialize trilateration solver
 * - Register with timing subsystem for RTT callbacks
 */
void utlp_rfip_init(void);

/**
 * @brief Get estimated range to a specific peer
 *
 * STUB - Not implemented. Always returns false.
 *
 * When implemented, will:
 * - Look up peer in range table
 * - Return most recent range estimate with confidence
 *
 * @param mac       Peer's 6-byte MAC address
 * @param out_range Output buffer for range estimate
 * @return true if range available, false if peer unknown
 */
bool utlp_rfip_get_range(const uint8_t *mac, utlp_rfip_range_t *out_range);

/**
 * @brief Process a timing measurement for range estimation
 *
 * STUB - Not implemented.
 *
 * When implemented, will:
 * - Convert RTT to distance using speed of light
 * - Apply multipath correction algorithms
 * - Update running average for this peer
 * - Trigger position recalculation if enough peers known
 *
 * @param mac    Peer's 6-byte MAC address
 * @param rtt_us Round-trip time in microseconds
 */
void utlp_rfip_process_timing(const uint8_t *mac, int64_t rtt_us);

/**
 * @brief Get this node's position estimate
 *
 * STUB - Not implemented. Always returns invalid position.
 *
 * When implemented, will:
 * - Run trilateration using ranges to 3+ peers
 * - Return position in local coordinate frame
 *
 * @param out_pos Output buffer for position estimate
 * @return true if position computed, false otherwise
 */
bool utlp_rfip_get_position(utlp_rfip_position_t *out_pos);

/**
 * @brief Get the count of peers with valid range estimates
 *
 * STUB - Not implemented. Always returns 0.
 *
 * @return Number of peers with recent range measurements
 */
uint8_t utlp_rfip_get_peer_count(void);

#ifdef __cplusplus
}
#endif
