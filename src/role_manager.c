/**
 * @file role_manager.c
 * @brief Role Management and Fallback State Implementation
 *
 * Manages device role and synchronized fallback states for dual-device
 * bilateral stimulation per AD028 specification.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "role_manager.h"
#include "esp_log.h"
#include "freertos/semphr.h"
#include <string.h>

static const char *TAG = "ROLE_MGR";

/**
 * @brief Mutex timeout for operations
 *
 * JPL Rule #6: No unbounded waits - all mutex operations must have timeouts
 * 100ms timeout provides safety margin
 * If mutex timeout occurs, indicates potential deadlock or system failure
 */
#define MUTEX_TIMEOUT_MS 100

// ============================================================================
// PRIVATE STATE
// ============================================================================

static fallback_state_t g_fallback_state = {0};
static connection_state_t g_connection_state = CONN_STATE_IDLE;
static SemaphoreHandle_t g_state_mutex = NULL;

// ============================================================================
// INITIALIZATION
// ============================================================================

esp_err_t role_manager_init(void) {
    ESP_LOGI(TAG, "Initializing role manager");

    // Create mutex for thread-safe access
    g_state_mutex = xSemaphoreCreateMutex();
    if (g_state_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create state mutex");
        return ESP_ERR_NO_MEM;
    }

    // Initialize state
    memset(&g_fallback_state, 0, sizeof(g_fallback_state));
    g_fallback_state.current_role = ROLE_UNDETERMINED;
    g_fallback_state.current_phase = FALLBACK_NONE;
    g_connection_state = CONN_STATE_IDLE;

    ESP_LOGI(TAG, "Role manager initialized");
    return ESP_OK;
}

esp_err_t role_manager_deinit(void) {
    if (g_state_mutex != NULL) {
        vSemaphoreDelete(g_state_mutex);
        g_state_mutex = NULL;
    }
    return ESP_OK;
}

// ============================================================================
// ROLE DETERMINATION
// ============================================================================

device_role_t role_determine_by_battery(uint8_t local_battery, uint8_t peer_battery,
                                         const uint8_t local_mac[6], const uint8_t peer_mac[6]) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in role_determine_by_battery - possible deadlock");
        return ROLE_UNDETERMINED;  // Return safe default
    }

    // Battery-based role assignment per AD034
    // Higher battery = Controller (Server role)
    // Lower battery = Follower (Client role)
    // If equal batteries, use MAC address tiebreaker

    if (local_battery > peer_battery) {
        g_fallback_state.current_role = ROLE_SERVER;
        ESP_LOGI(TAG, "Role determined: SERVER (local battery %u%% > peer %u%%)",
                 local_battery, peer_battery);
    } else if (peer_battery > local_battery) {
        g_fallback_state.current_role = ROLE_CLIENT;
        ESP_LOGI(TAG, "Role determined: CLIENT (peer battery %u%% > local %u%%)",
                 peer_battery, local_battery);
    } else {
        // Batteries equal - use MAC address tiebreaker
        // Higher MAC address becomes Server (Controller)
        int mac_cmp = memcmp(local_mac, peer_mac, 6);
        if (mac_cmp > 0) {
            g_fallback_state.current_role = ROLE_SERVER;
            ESP_LOGI(TAG, "Role determined: SERVER (equal battery %u%%, local MAC higher)", local_battery);
        } else {
            g_fallback_state.current_role = ROLE_CLIENT;
            ESP_LOGI(TAG, "Role determined: CLIENT (equal battery %u%%, peer MAC higher)", peer_battery);
        }
        ESP_LOGD(TAG, "Local MAC: %02X:%02X:%02X:%02X:%02X:%02X",
                 local_mac[0], local_mac[1], local_mac[2], local_mac[3], local_mac[4], local_mac[5]);
        ESP_LOGD(TAG, "Peer MAC:  %02X:%02X:%02X:%02X:%02X:%02X",
                 peer_mac[0], peer_mac[1], peer_mac[2], peer_mac[3], peer_mac[4], peer_mac[5]);
    }

    device_role_t role = g_fallback_state.current_role;
    xSemaphoreGive(g_state_mutex);

    return role;
}

device_role_t role_get_current(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in role_get_current - possible deadlock");
        return ROLE_UNDETERMINED;  // Return safe default
    }
    device_role_t role = g_fallback_state.current_role;
    xSemaphoreGive(g_state_mutex);
    return role;
}

esp_err_t role_set(device_role_t role) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in role_set - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    device_role_t old_role = g_fallback_state.current_role;
    g_fallback_state.current_role = role;

    ESP_LOGI(TAG, "Role changed: %s -> %s",
             role_to_string(old_role), role_to_string(role));

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

bool role_should_become_server(uint32_t disconnect_duration_ms) {
    if (disconnect_duration_ms >= ROLE_SURVIVOR_TIMEOUT_MS) {
        // JPL compliance: Bounded mutex wait with timeout error handling
        if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
            ESP_LOGE(TAG, "Mutex timeout in role_should_become_server - possible deadlock");
            return false;  // Return safe default
        }
        bool should_become = (g_fallback_state.current_role == ROLE_CLIENT);
        xSemaphoreGive(g_state_mutex);

        if (should_become) {
            ESP_LOGI(TAG, "Survivor timeout reached (%u ms) - becoming server",
                     disconnect_duration_ms);
        }
        return should_become;
    }
    return false;
}

// ============================================================================
// FALLBACK MANAGEMENT
// ============================================================================

esp_err_t fallback_start(const fallback_state_t *established_params) {
    if (established_params == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_start - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    // Capture current operational parameters
    g_fallback_state.disconnect_time = xTaskGetTickCount();
    g_fallback_state.established_cycle_ms = established_params->established_cycle_ms;
    g_fallback_state.established_duty_ms = established_params->established_duty_ms;
    g_fallback_state.established_intensity = established_params->established_intensity;
    g_fallback_state.established_mode = established_params->established_mode;

    // Set fallback role based on current role
    g_fallback_state.fallback_role = g_fallback_state.current_role;

    // Start in synchronized phase 1
    g_fallback_state.current_phase = FALLBACK_PHASE1_SYNC;
    g_fallback_state.phase1_sync_active = true;
    g_fallback_state.sync_reference_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;

    ESP_LOGI(TAG, "Fallback started: Phase 1 (synchronized), cycle=%ums, duty=%ums",
             g_fallback_state.established_cycle_ms,
             g_fallback_state.established_duty_ms);

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

fallback_phase_t fallback_update_phase(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_update_phase - possible deadlock");
        return FALLBACK_NONE;  // Return safe default
    }

    if (g_fallback_state.current_phase == FALLBACK_NONE) {
        xSemaphoreGive(g_state_mutex);
        return FALLBACK_NONE;
    }

    uint32_t now = xTaskGetTickCount();
    uint32_t disconnect_duration = (now - g_fallback_state.disconnect_time) * portTICK_PERIOD_MS;

    // Check for phase transition
    if (g_fallback_state.current_phase == FALLBACK_PHASE1_SYNC &&
        disconnect_duration >= FALLBACK_PHASE1_DURATION_MS) {

        // Transition to phase 2
        g_fallback_state.current_phase = FALLBACK_PHASE2_ROLE;
        g_fallback_state.phase1_sync_active = false;

        ESP_LOGI(TAG, "Fallback phase transition: Phase 1 -> Phase 2 (role-only)");
        ESP_LOGI(TAG, "Device will continue as %s only",
                 g_fallback_state.fallback_role == ROLE_SERVER ? "FORWARD" : "REVERSE");
    }

    fallback_phase_t phase = g_fallback_state.current_phase;
    xSemaphoreGive(g_state_mutex);

    return phase;
}

fallback_phase_t fallback_get_phase(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_get_phase - possible deadlock");
        return FALLBACK_NONE;  // Return safe default
    }
    fallback_phase_t phase = g_fallback_state.current_phase;
    xSemaphoreGive(g_state_mutex);
    return phase;
}

const fallback_state_t* fallback_get_state(void) {
    // Note: Caller must ensure thread safety
    return &g_fallback_state;
}

esp_err_t fallback_stop(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_stop - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    ESP_LOGI(TAG, "Fallback stopped - connection restored");

    g_fallback_state.current_phase = FALLBACK_NONE;
    g_fallback_state.phase1_sync_active = false;
    g_fallback_state.disconnect_time = 0;

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

bool fallback_should_reconnect(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_should_reconnect - possible deadlock");
        return false;  // Return safe default
    }

    if (g_fallback_state.current_phase == FALLBACK_NONE) {
        xSemaphoreGive(g_state_mutex);
        return false;
    }

    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    uint32_t time_since_attempt = now - g_fallback_state.last_reconnect_attempt;

    bool should_reconnect = (time_since_attempt >= RECONNECT_INTERVAL_MS);

    xSemaphoreGive(g_state_mutex);
    return should_reconnect;
}

void fallback_mark_reconnect_attempt(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in fallback_mark_reconnect_attempt - possible deadlock");
        return;  // Early return on timeout
    }
    g_fallback_state.last_reconnect_attempt = xTaskGetTickCount() * portTICK_PERIOD_MS;
    ESP_LOGI(TAG, "Reconnection attempt marked");
    xSemaphoreGive(g_state_mutex);
}

// ============================================================================
// CONNECTION STATE MANAGEMENT
// ============================================================================

esp_err_t connection_state_set(connection_state_t state) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in connection_state_set - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    connection_state_t old_state = g_connection_state;
    g_connection_state = state;

    ESP_LOGI(TAG, "Connection state: %s -> %s",
             old_state == CONN_STATE_CONNECTED ? "CONNECTED" : "DISCONNECTED",
             state == CONN_STATE_CONNECTED ? "CONNECTED" : "DISCONNECTED");

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

connection_state_t connection_state_get(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in connection_state_get - possible deadlock");
        return CONN_STATE_IDLE;  // Return safe default
    }
    connection_state_t state = g_connection_state;
    xSemaphoreGive(g_state_mutex);
    return state;
}

bool connection_is_active(void) {
    return connection_state_get() == CONN_STATE_CONNECTED;
}

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

esp_err_t session_start(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in session_start - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    g_fallback_state.session_start_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
    g_fallback_state.session_active = true;

    ESP_LOGI(TAG, "Session started");

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

bool session_should_end(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in session_should_end - possible deadlock");
        return false;  // Return safe default
    }

    if (!g_fallback_state.session_active) {
        xSemaphoreGive(g_state_mutex);
        return false;
    }

    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
    uint32_t elapsed = now - g_fallback_state.session_start_time;

    bool should_end = (elapsed >= SESSION_DURATION_MAX_MS);

    xSemaphoreGive(g_state_mutex);

    if (should_end) {
        ESP_LOGI(TAG, "Session duration exceeded (%u minutes)",
                 elapsed / 60000);
    }

    return should_end;
}

uint32_t session_get_elapsed_ms(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in session_get_elapsed_ms - possible deadlock");
        return 0;  // Return safe default
    }

    uint32_t elapsed = 0;
    if (g_fallback_state.session_active) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        elapsed = now - g_fallback_state.session_start_time;
    }

    xSemaphoreGive(g_state_mutex);
    return elapsed;
}

esp_err_t session_end(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in session_end - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    g_fallback_state.session_active = false;
    uint32_t duration = session_get_elapsed_ms();

    ESP_LOGI(TAG, "Session ended (duration: %u minutes)", duration / 60000);

    xSemaphoreGive(g_state_mutex);
    return ESP_OK;
}

// ============================================================================
// STATUS AND LOGGING
// ============================================================================

const char* role_to_string(device_role_t role) {
    switch (role) {
        case ROLE_UNDETERMINED: return "UNDETERMINED";
        case ROLE_SERVER:       return "SERVER";
        case ROLE_CLIENT:       return "CLIENT";
        case ROLE_STANDALONE:   return "STANDALONE";
        default:                return "UNKNOWN";
    }
}

const char* fallback_phase_to_string(fallback_phase_t phase) {
    switch (phase) {
        case FALLBACK_NONE:        return "NONE (Connected)";
        case FALLBACK_PHASE1_SYNC: return "PHASE 1 (Synchronized)";
        case FALLBACK_PHASE2_ROLE: return "PHASE 2 (Role-only)";
        default:                   return "UNKNOWN";
    }
}

void role_log_status(const char *tag) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(g_state_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in role_log_status - possible deadlock");
        return;  // Early return on timeout
    }

    ESP_LOGI(tag, "Role Manager Status:");
    ESP_LOGI(tag, "  Current Role: %s", role_to_string(g_fallback_state.current_role));
    ESP_LOGI(tag, "  Fallback Phase: %s", fallback_phase_to_string(g_fallback_state.current_phase));
    ESP_LOGI(tag, "  Connection: %s",
             g_connection_state == CONN_STATE_CONNECTED ? "CONNECTED" : "DISCONNECTED");

    if (g_fallback_state.session_active) {
        uint32_t elapsed = session_get_elapsed_ms();
        ESP_LOGI(tag, "  Session Time: %u minutes", elapsed / 60000);
    }

    xSemaphoreGive(g_state_mutex);
}