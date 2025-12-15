/**
 * @file firmware_version.h
 * @brief Firmware Version Information (AD040 - Simplified Phase 1)
 *
 * Provides firmware versioning for ensuring both devices run identical builds.
 * Version information is automatically embedded at compile time.
 *
 * @date November 22, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef FIRMWARE_VERSION_H
#define FIRMWARE_VERSION_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "esp_log.h"

// ============================================================================
// VERSION INFORMATION (from platformio.ini build flags)
// ============================================================================

#ifndef FIRMWARE_VERSION_MAJOR
#define FIRMWARE_VERSION_MAJOR 0
#endif

#ifndef FIRMWARE_VERSION_MINOR
#define FIRMWARE_VERSION_MINOR 6  // Tracks phase number (Phase 6)
#endif

#ifndef FIRMWARE_VERSION_PATCH
#define FIRMWARE_VERSION_PATCH 122  // Bug #103: First PWA frequency change now triggers sync
#endif

#ifndef FIRMWARE_VERSION_CHECK_ENABLED
#define FIRMWARE_VERSION_CHECK_ENABLED 1  // Enforce version matching by default
#endif

// Build timestamp (unique identifier per build)
// These are standard C preprocessor macros set at compile time
#define FIRMWARE_BUILD_DATE __DATE__  // "Nov 22 2025"
#define FIRMWARE_BUILD_TIME __TIME__  // "15:30:45"

// Combined version string for logging
#define FIRMWARE_VERSION_STRING "v" \
    STRINGIFY(FIRMWARE_VERSION_MAJOR) "." \
    STRINGIFY(FIRMWARE_VERSION_MINOR) "." \
    STRINGIFY(FIRMWARE_VERSION_PATCH) \
    " (" FIRMWARE_BUILD_DATE " " FIRMWARE_BUILD_TIME ")"

// Stringify macro helper
#define STRINGIFY(x) #x

// ============================================================================
// FIRMWARE VERSION STRUCTURE
// ============================================================================

/**
 * @brief Firmware version structure for BLE transmission
 *
 * Compact 16-byte structure for peer version exchange.
 * Build timestamp serves as unique build identifier.
 */
typedef struct __attribute__((packed)) {
    uint8_t major;                  // Major version (breaking changes)
    uint8_t minor;                  // Minor version (feature additions)
    uint8_t patch;                  // Patch version (bug fixes)
    uint8_t check_enabled;          // 1=enforce matching, 0=allow mismatch
    char build_date[12];            // "Nov 22 2025" (11 chars + null)
    char build_time[9];             // "15:30:45" (8 chars + null)
} firmware_version_t;

// ============================================================================
// PUBLIC FUNCTIONS
// ============================================================================

/**
 * @brief Get local firmware version information
 * @return Firmware version structure with build timestamp
 */
static inline firmware_version_t firmware_get_version(void) {
    firmware_version_t version = {
        .major = FIRMWARE_VERSION_MAJOR,
        .minor = FIRMWARE_VERSION_MINOR,
        .patch = FIRMWARE_VERSION_PATCH,
        .check_enabled = FIRMWARE_VERSION_CHECK_ENABLED,
    };

    // Copy build timestamp strings
    snprintf(version.build_date, sizeof(version.build_date), "%s", FIRMWARE_BUILD_DATE);
    snprintf(version.build_time, sizeof(version.build_time), "%s", FIRMWARE_BUILD_TIME);

    return version;
}

/**
 * @brief Compare two firmware versions for equality
 *
 * @param a First version
 * @param b Second version
 * @return true if versions match (same build timestamp), false otherwise
 *
 * Logic:
 * - If either device has check disabled, always return true (allow mismatch)
 * - Otherwise, compare major.minor.patch AND build timestamp
 */
static inline bool firmware_versions_match(firmware_version_t a, firmware_version_t b) {
    // If either device has version checking disabled, allow connection
    if (a.check_enabled == 0 || b.check_enabled == 0) {
        return true;  // Dev mode - allow any mismatch
    }

    // Check semantic version numbers
    if (a.major != b.major || a.minor != b.minor || a.patch != b.patch) {
        return false;
    }

    // Check build timestamp (ensures same binary)
    if (strcmp(a.build_date, b.build_date) != 0 || strcmp(a.build_time, b.build_time) != 0) {
        return false;
    }

    return true;  // Exact match
}

/**
 * @brief Log firmware version to console
 * @param tag ESP-IDF log tag
 * @param prefix Prefix string (e.g., "Local", "Peer")
 * @param version Version to log
 */
static inline void firmware_log_version(const char *tag, const char *prefix, firmware_version_t version) {
    ESP_LOGI(tag, "%s firmware: v%d.%d.%d built %s %s (check=%s)",
             prefix,
             version.major, version.minor, version.patch,
             version.build_date, version.build_time,
             version.check_enabled ? "ENABLED" : "DISABLED");
}

#endif // FIRMWARE_VERSION_H
