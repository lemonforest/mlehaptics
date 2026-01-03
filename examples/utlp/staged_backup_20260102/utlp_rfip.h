/**
 * @file utlp_rfip.h
 * @brief RFIP - Reference Frame Independent Positioning
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
 * RFIP implements relational positioning for UTLP:
 * - Nodes know distances to neighbors (via RTT measurements)
 * - Nodes infer topology from the trust graph
 * - No absolute coordinates needed—only relative positions matter
 *
 * This enables "spatial trust": nodes can weight observations by distance,
 * detect when a peer has physically moved, and form "apertures" for
 * environmental sensing (acoustic, seismic, RF).
 *
 * @section loom The Spatial Loom
 *
 * RFIP is the **Spatial Loom** — the spatial threat domain in the generalized
 * Loom framework. Just as the Temporal Loom weaves Time Lords from clock
 * entropy, the Spatial Loom weaves position from observation entropy.
 *
 * | Loom Domain | Entropy Signal | Emergent State |
 * |-------------|----------------|----------------|
 * | Temporal | Clock drift | Time Lord (anchor) |
 * | Spectral | RF congestion | Channel divergence |
 * | **Spatial** | Position uncertainty | RFIP coordinates |
 *
 * @section hierarchy Data Hierarchy
 *
 * Build from always-available sources, let fancy stuff enhance:
 *
 * | Layer | Source | Precision | Always Available |
 * |-------|--------|-----------|------------------|
 * | 0 | RSSI | ~3-5m | Yes |
 * | 1 | RSSI differential | ~1-3m | Yes |
 * | 2 | TDoA from UTLP beacons | ~30cm | Yes (requires sync) |
 * | 3 | CSI | ~50cm-1m | Yes (ESP32 family) |
 * | 4 | Multipath signatures | Fingerprint | Yes (learned) |
 * | 5 | 802.11mc FTM | ~10-50cm | Platform-dependent |
 * | 6 | UWB (DW3000) | ~10cm | Add-on only |
 *
 * @section overview Overview
 * RFIP (Reference Frame Independent Positioning) enables distributed
 * nodes to estimate their relative positions using time-of-flight
 * measurements. This module integrates with the Metabolic Ledger
 * to provide position-aware trust scoring.
 *
 * @section status Implementation Status
 * - Phase 1 (current): HAL layer with capability detection (rfip_hal.h/c)
 * - Phase 2 (pending): CSI integration
 * - Phase 3 (pending): TDoA from UTLP beacons
 * - Phase 4 (pending): 802.11mc FTM enhancement
 * - Phase 5 (pending): UWB integration
 * - Phase 6 (pending): Fusion & ML
 *
 * @section chaos The "Chaos Monkey" Principle
 * ESP32 DevKit V1 has NO FTM support. It validates that core RFIP works
 * using only RSSI/CSI/TDoA. If it works on DevKit V1, it works anywhere.
 *
 * @see docs/RFIP_Technical_Specification.md - Master specification
 * @see docs/UTLP_Addendum_Reference_Frame_Independent_Positioning.md
 * @see docs/Connectionless_Distributed_Timing_Prior_Art.md - Section 1 (ToA Trilateration)
 * @see rfip_hal.h - Hardware abstraction layer
 *
 * @version 0.2.0 - HAL layer + anchor registry
 * @date 2025-12-31
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
 * STRUCT PACKING CONVENTION (Memory Alignment Optimization)
 *
 * Always order struct fields from largest to smallest alignment:
 *   1. 8-byte fields first (int64_t, uint64_t, double, pointers on 64-bit)
 *   2. 4-byte fields (int32_t, uint32_t, float)
 *   3. 2-byte fields (int16_t, uint16_t)
 *   4. 1-byte fields and arrays (uint8_t, bool, char[])
 *
 * This minimizes padding bytes inserted by the compiler for alignment.
 * See utlp_trust.h for detailed example with BAD/GOOD comparison.
 *==========================================================================*/

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Range estimate to a peer
 *
 * Contains the estimated distance to a specific peer along with
 * a confidence metric based on measurement quality.
 *
 * Packed heavy-first: 4-byte → 1-byte arrays → single bytes
 */
typedef struct {
    /* 4-byte fields first */
    int32_t  range_cm;          /**< Estimated range in centimeters */
    uint32_t last_update_ms;    /**< Timestamp of last measurement */
    /* 1-byte fields and arrays */
    uint8_t  peer_mac[6];       /**< Peer's MAC address */
    uint8_t  confidence;        /**< Confidence level 0-100% */
    uint8_t  _pad;              /**< Explicit padding for alignment */
} utlp_rfip_range_t;

/**
 * @brief Position estimate in local coordinate frame
 *
 * Relative position using the first 3 discovered peers as
 * reference points (arbitrary local coordinate system).
 *
 * Packed heavy-first: 4-byte → single bytes
 */
typedef struct {
    /* 4-byte fields first */
    int32_t  x_cm;              /**< X position in centimeters */
    int32_t  y_cm;              /**< Y position in centimeters */
    int32_t  z_cm;              /**< Z position in centimeters (if 3D) */
    /* 1-byte fields */
    uint8_t  dimensions;        /**< 2 or 3 (2D or 3D positioning) */
    uint8_t  confidence;        /**< Position confidence 0-100% */
    bool     valid;             /**< Position computed successfully? */
    uint8_t  _pad;              /**< Explicit padding for alignment */
} utlp_rfip_position_t;

/*============================================================================
 * ANCHOR REGISTRY (From RFIP Tech Spec Section 5.2)
 *
 * Anchors are nodes with known positions that provide ranging reference.
 * In UTLP, any synchronized node can serve as an anchor for TDoA.
 *==========================================================================*/

/**
 * @brief Known anchor node for positioning
 *
 * Anchors provide the reference points for trilateration. Position can be:
 * - Explicitly configured (infrastructure anchors)
 * - Derived from FTM/UWB measurements to other anchors
 * - Estimated from consensus (multiple observers agree on relative position)
 *
 * Packed heavy-first: floats (4-byte) → 4-byte → arrays → single bytes
 *
 * @see docs/RFIP_Technical_Specification.md - Section 5.2
 */
typedef struct {
    /* 4-byte fields first (floats are 4 bytes) */
    float    x_m;               /**< X position in meters */
    float    y_m;               /**< Y position in meters */
    float    z_m;               /**< Z position in meters */
    uint32_t last_seen_ms;      /**< Timestamp of last observation */
    /* 1-byte arrays */
    uint8_t  mac[6];            /**< Anchor's MAC address */
    /* Single bytes */
    uint8_t  capabilities;      /**< RFIP capabilities (rfip_capability_t flags) */
    uint8_t  health_score;      /**< UTLP trust metric (from Metabolic Ledger) */
} utlp_rfip_anchor_t;

/**
 * @brief Maximum anchors tracked (Silicon Dunbar's Number for spatial)
 *
 * Matches the trust module's DUNBAR_PEERS limit for consistency.
 * More anchors = better accuracy, but diminishing returns past ~8-12.
 */
#define UTLP_RFIP_MAX_ANCHORS 16

/**
 * @brief Anchor registry for position calculation
 *
 * Tracks known anchors for trilateration. Populated from:
 * - Configuration (explicit anchor positions)
 * - Discovery (peers advertising anchor capability)
 * - Promotion (stable nodes with good connectivity)
 */
typedef struct {
    utlp_rfip_anchor_t anchors[UTLP_RFIP_MAX_ANCHORS];
    uint8_t            count;   /**< Number of valid anchors */
    uint8_t            _pad[3]; /**< Explicit padding for 4-byte alignment */
} utlp_rfip_anchor_registry_t;

/*============================================================================
 * ENHANCED POSITION ESTIMATE (From RFIP Tech Spec Section 5.3)
 *
 * Full position estimate with uncertainty and timestamp for fusion.
 *==========================================================================*/

/**
 * @brief Full position estimate with uncertainty
 *
 * Enhanced position structure with:
 * - UTLP atomic timestamp (for temporal correlation)
 * - Position in meters (floats for sub-meter precision)
 * - Error bounds per axis (1σ uncertainty)
 * - Quality metrics for fusion weighting
 *
 * Packed heavy-first: 64-bit → floats → single bytes
 *
 * @see docs/RFIP_Technical_Specification.md - Section 5.3
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  timestamp_us;      /**< UTLP atomic time of estimate */

    /* 4-byte fields (floats) */
    float    x_m;               /**< X position in meters */
    float    y_m;               /**< Y position in meters */
    float    z_m;               /**< Z position in meters */
    float    error_x_m;         /**< X uncertainty in meters (1σ) */
    float    error_y_m;         /**< Y uncertainty in meters (1σ) */
    float    error_z_m;         /**< Z uncertainty in meters (1σ) */

    /* 1-byte fields */
    uint8_t  num_observations;  /**< Number of data points used */
    uint8_t  quality;           /**< Overall quality metric 0-255 */
    uint8_t  _pad[2];           /**< Explicit padding for alignment */
} utlp_rfip_position_full_t;

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
