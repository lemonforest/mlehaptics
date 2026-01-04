/**
 * @file utlp_hal_mg24_imu.c
 * @brief UTLP IMU HAL for Silicon Labs MG24 with LSM6DS3 (S2.46 Claims 114-120)
 *
 * @section overview Overview
 *
 * Production implementation for Seeed XIAO MG24's onboard LSM6DS3 6-axis IMU.
 * Provides the yield-pattern interface (Claim 114) for RFIP positioning.
 *
 * @section hardware Target Hardware
 *
 * - **MCU:** EFR32MG24B220F1536IM48
 * - **IMU:** STMicroelectronics LSM6DS3
 * - **Interface:** I2C @ 400 kHz
 * - **Address:** 0x6A (SA0 = GND) or 0x6B (SA0 = VDD)
 *
 * @section features Features
 *
 * | Feature | Implementation |
 * |---------|----------------|
 * | Sample Rate | 104 Hz (configurable) |
 * | Accel Range | ±4g (configurable) |
 * | Gyro Range | ±500 dps (configurable) |
 * | Fusion | Madgwick AHRS filter |
 * | Motion Detect | Variance-based confidence |
 *
 * @section claims Prior Art Claims (S2.46)
 *
 * - **Claim 114**: Yield-Pattern IMU Integration
 * - **Claim 115**: Beacon-Propagated Motion Confidence
 * - **Claim 116**: Cross-Sensor Disturbance Blanking
 * - **Claim 117**: Online Antenna Pattern Learning
 * - **Claim 118**: UTLP-Coordinated Dead Reckoning
 * - **Claim 119**: Emergent Anchor Topology
 * - **Claim 120**: RF-Derived Coordinate Frame Learning
 *
 * @version 1.0.0
 * @date 2026-01-03
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "rfip_hal.h"
#include <string.h>
#include <math.h>

/* Platform detection */
#if defined(EFR32MG24) || defined(CONFIG_SOC_SERIES_EFR32MG24)
#define UTLP_HAL_MG24_IMU_AVAILABLE 1

/* Zephyr I2C and logging */
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(utlp_mg24_imu, LOG_LEVEL_INF);

#else
#define UTLP_HAL_MG24_IMU_AVAILABLE 0
#endif

#if UTLP_HAL_MG24_IMU_AVAILABLE

/*============================================================================
 * LSM6DS3 REGISTER DEFINITIONS
 *==========================================================================*/

/** @brief LSM6DS3 I2C addresses */
#define LSM6DS3_ADDR_SA0_LOW    0x6A
#define LSM6DS3_ADDR_SA0_HIGH   0x6B
#define LSM6DS3_ADDR            LSM6DS3_ADDR_SA0_LOW

/** @brief LSM6DS3 register addresses */
#define LSM6DS3_WHO_AM_I        0x0F
#define LSM6DS3_CTRL1_XL        0x10  /* Accel control */
#define LSM6DS3_CTRL2_G         0x11  /* Gyro control */
#define LSM6DS3_CTRL3_C         0x12  /* Control 3 */
#define LSM6DS3_CTRL4_C         0x13  /* Control 4 */
#define LSM6DS3_CTRL5_C         0x14  /* Control 5 */
#define LSM6DS3_CTRL6_C         0x15  /* Control 6 */
#define LSM6DS3_CTRL7_G         0x16  /* Gyro control 2 */
#define LSM6DS3_CTRL8_XL        0x17  /* Accel control 2 */
#define LSM6DS3_CTRL9_XL        0x18  /* Accel control 3 */
#define LSM6DS3_CTRL10_C        0x19  /* Control 10 */
#define LSM6DS3_STATUS_REG      0x1E
#define LSM6DS3_OUT_TEMP_L      0x20
#define LSM6DS3_OUT_TEMP_H      0x21
#define LSM6DS3_OUTX_L_G        0x22  /* Gyro X low */
#define LSM6DS3_OUTX_H_G        0x23  /* Gyro X high */
#define LSM6DS3_OUTY_L_G        0x24
#define LSM6DS3_OUTY_H_G        0x25
#define LSM6DS3_OUTZ_L_G        0x26
#define LSM6DS3_OUTZ_H_G        0x27
#define LSM6DS3_OUTX_L_XL       0x28  /* Accel X low */
#define LSM6DS3_OUTX_H_XL       0x29  /* Accel X high */
#define LSM6DS3_OUTY_L_XL       0x2A
#define LSM6DS3_OUTY_H_XL       0x2B
#define LSM6DS3_OUTZ_L_XL       0x2C
#define LSM6DS3_OUTZ_H_XL       0x2D

/** @brief WHO_AM_I expected value */
#define LSM6DS3_WHO_AM_I_VALUE  0x69

/** @brief ODR (Output Data Rate) settings */
#define LSM6DS3_ODR_104HZ       0x40  /* 104 Hz */
#define LSM6DS3_ODR_208HZ       0x50  /* 208 Hz */
#define LSM6DS3_ODR_416HZ       0x60  /* 416 Hz */

/** @brief Accelerometer full-scale settings */
#define LSM6DS3_XL_FS_2G        0x00
#define LSM6DS3_XL_FS_4G        0x08
#define LSM6DS3_XL_FS_8G        0x0C
#define LSM6DS3_XL_FS_16G       0x04

/** @brief Gyroscope full-scale settings */
#define LSM6DS3_G_FS_245DPS     0x00
#define LSM6DS3_G_FS_500DPS     0x04
#define LSM6DS3_G_FS_1000DPS    0x08
#define LSM6DS3_G_FS_2000DPS    0x0C

/*============================================================================
 * CONFIGURATION
 *==========================================================================*/

/** @brief Selected ODR: 104 Hz */
#define IMU_ODR                 LSM6DS3_ODR_104HZ

/** @brief Selected accel range: ±4g */
#define IMU_XL_FS               LSM6DS3_XL_FS_4G
#define IMU_XL_SENSITIVITY      0.122f  /* mg/LSB for ±4g */

/** @brief Selected gyro range: ±500 dps */
#define IMU_G_FS                LSM6DS3_G_FS_500DPS
#define IMU_G_SENSITIVITY       17.50f  /* mdps/LSB for ±500 dps */

/** @brief Madgwick filter beta parameter */
#define MADGWICK_BETA           0.1f

/** @brief Motion detection threshold (milli-g variance) */
#define MOTION_THRESHOLD_MG     100.0f

/** @brief Motion history length for variance calculation */
#define MOTION_HISTORY_LEN      16

/*============================================================================
 * STATE
 *==========================================================================*/

/** @brief I2C device binding */
static const struct device *s_i2c_dev = NULL;

/** @brief IMU initialized flag */
static bool s_initialized = false;

/** @brief Current quaternion (w, x, y, z) - unit quaternion */
static float s_quat[4] = {1.0f, 0.0f, 0.0f, 0.0f};

/** @brief Last sample timestamp */
static int64_t s_last_sample_us = 0;

/** @brief Motion history for variance calculation */
static float s_accel_history[MOTION_HISTORY_LEN];
static uint8_t s_history_idx = 0;
static bool s_history_full = false;

/** @brief Current motion confidence (0-255) */
static uint8_t s_motion_confidence = 0;

/** @brief Spinlock for thread safety */
static struct k_spinlock s_imu_spinlock;

/*============================================================================
 * I2C HELPERS
 *==========================================================================*/

/**
 * @brief Write single register
 */
static int lsm6ds3_write_reg(uint8_t reg, uint8_t value)
{
    uint8_t buf[2] = {reg, value};
    return i2c_write(s_i2c_dev, buf, 2, LSM6DS3_ADDR);
}

/**
 * @brief Read single register
 */
static int lsm6ds3_read_reg(uint8_t reg, uint8_t *value)
{
    return i2c_write_read(s_i2c_dev, LSM6DS3_ADDR, &reg, 1, value, 1);
}

/**
 * @brief Read multiple registers
 */
static int lsm6ds3_read_regs(uint8_t reg, uint8_t *buf, size_t len)
{
    return i2c_write_read(s_i2c_dev, LSM6DS3_ADDR, &reg, 1, buf, len);
}

/*============================================================================
 * MADGWICK AHRS FILTER
 *
 * Minimal implementation of Madgwick's gradient descent orientation filter.
 * Input: accelerometer (g) and gyroscope (rad/s)
 * Output: unit quaternion representing device orientation
 *
 * Reference: Sebastian Madgwick, "An efficient orientation filter for
 * inertial and inertial/magnetic sensor arrays" (2010)
 *==========================================================================*/

/**
 * @brief Fast inverse square root (Quake III style)
 */
static float inv_sqrt(float x)
{
    float halfx = 0.5f * x;
    float y = x;
    long i = *(long*)&y;
    i = 0x5f3759df - (i >> 1);
    y = *(float*)&i;
    y = y * (1.5f - (halfx * y * y));
    return y;
}

/**
 * @brief Update quaternion with new sensor data
 *
 * @param gx Gyro X (rad/s)
 * @param gy Gyro Y (rad/s)
 * @param gz Gyro Z (rad/s)
 * @param ax Accel X (g, normalized)
 * @param ay Accel Y (g, normalized)
 * @param az Accel Z (g, normalized)
 * @param dt Time step (seconds)
 */
static void madgwick_update(float gx, float gy, float gz,
                             float ax, float ay, float az,
                             float dt)
{
    float q0 = s_quat[0], q1 = s_quat[1], q2 = s_quat[2], q3 = s_quat[3];
    float recipNorm;
    float s0, s1, s2, s3;
    float qDot1, qDot2, qDot3, qDot4;
    float _2q0, _2q1, _2q2, _2q3, _4q0, _4q1, _4q2, _8q1, _8q2;
    float q0q0, q1q1, q2q2, q3q3;

    /* Rate of change of quaternion from gyroscope */
    qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
    qDot2 = 0.5f * (q0 * gx + q2 * gz - q3 * gy);
    qDot3 = 0.5f * (q0 * gy - q1 * gz + q3 * gx);
    qDot4 = 0.5f * (q0 * gz + q1 * gy - q2 * gx);

    /* Compute feedback only if accelerometer measurement valid */
    if (!((ax == 0.0f) && (ay == 0.0f) && (az == 0.0f))) {
        /* Normalise accelerometer measurement */
        recipNorm = inv_sqrt(ax * ax + ay * ay + az * az);
        ax *= recipNorm;
        ay *= recipNorm;
        az *= recipNorm;

        /* Auxiliary variables */
        _2q0 = 2.0f * q0;
        _2q1 = 2.0f * q1;
        _2q2 = 2.0f * q2;
        _2q3 = 2.0f * q3;
        _4q0 = 4.0f * q0;
        _4q1 = 4.0f * q1;
        _4q2 = 4.0f * q2;
        _8q1 = 8.0f * q1;
        _8q2 = 8.0f * q2;
        q0q0 = q0 * q0;
        q1q1 = q1 * q1;
        q2q2 = q2 * q2;
        q3q3 = q3 * q3;

        /* Gradient decent algorithm corrective step */
        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay;
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0f * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az;
        s2 = 4.0f * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az;
        s3 = 4.0f * q1q1 * q3 - _2q1 * ax + 4.0f * q2q2 * q3 - _2q2 * ay;

        recipNorm = inv_sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3);
        s0 *= recipNorm;
        s1 *= recipNorm;
        s2 *= recipNorm;
        s3 *= recipNorm;

        /* Apply feedback step */
        qDot1 -= MADGWICK_BETA * s0;
        qDot2 -= MADGWICK_BETA * s1;
        qDot3 -= MADGWICK_BETA * s2;
        qDot4 -= MADGWICK_BETA * s3;
    }

    /* Integrate rate of change of quaternion */
    q0 += qDot1 * dt;
    q1 += qDot2 * dt;
    q2 += qDot3 * dt;
    q3 += qDot4 * dt;

    /* Normalise quaternion */
    recipNorm = inv_sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
    s_quat[0] = q0 * recipNorm;
    s_quat[1] = q1 * recipNorm;
    s_quat[2] = q2 * recipNorm;
    s_quat[3] = q3 * recipNorm;
}

/**
 * @brief Extract gravity vector from quaternion
 *
 * Gravity in body frame = R^T * [0, 0, 1]^T where R is rotation matrix
 */
static void quaternion_to_gravity(float *gx, float *gy, float *gz)
{
    float q0 = s_quat[0], q1 = s_quat[1], q2 = s_quat[2], q3 = s_quat[3];

    *gx = 2.0f * (q1 * q3 - q0 * q2);
    *gy = 2.0f * (q0 * q1 + q2 * q3);
    *gz = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3;
}

/*============================================================================
 * MOTION CONFIDENCE CALCULATION
 *
 * Uses variance of recent acceleration magnitude to detect motion.
 * Low variance = stationary, high variance = moving
 *==========================================================================*/

/**
 * @brief Update motion confidence from acceleration magnitude
 */
static void update_motion_confidence(float accel_mag_mg)
{
    /* Add to history */
    s_accel_history[s_history_idx] = accel_mag_mg;
    s_history_idx = (s_history_idx + 1) % MOTION_HISTORY_LEN;
    if (s_history_idx == 0) {
        s_history_full = true;
    }

    /* Calculate variance once we have enough samples */
    if (!s_history_full) {
        s_motion_confidence = 0;  /* Not enough data yet */
        return;
    }

    /* Calculate mean */
    float sum = 0.0f;
    for (int i = 0; i < MOTION_HISTORY_LEN; i++) {
        sum += s_accel_history[i];
    }
    float mean = sum / MOTION_HISTORY_LEN;

    /* Calculate variance */
    float var_sum = 0.0f;
    for (int i = 0; i < MOTION_HISTORY_LEN; i++) {
        float diff = s_accel_history[i] - mean;
        var_sum += diff * diff;
    }
    float variance = var_sum / MOTION_HISTORY_LEN;

    /* Map variance to 0-255 confidence
     * Low variance (< threshold) = low confidence (stationary)
     * High variance = high confidence (moving)
     */
    float confidence = variance / MOTION_THRESHOLD_MG;
    if (confidence > 1.0f) confidence = 1.0f;

    s_motion_confidence = (uint8_t)(confidence * 255.0f);
}

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize LSM6DS3 IMU
 *
 * @return true if successful
 */
bool utlp_imu_init(void)
{
    if (s_initialized) {
        return true;
    }

    /* Get I2C device */
    s_i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));
    if (!device_is_ready(s_i2c_dev)) {
        LOG_ERR("I2C device not ready");
        return false;
    }

    /* Verify WHO_AM_I */
    uint8_t who_am_i;
    if (lsm6ds3_read_reg(LSM6DS3_WHO_AM_I, &who_am_i) != 0) {
        LOG_ERR("Failed to read WHO_AM_I");
        return false;
    }

    if (who_am_i != LSM6DS3_WHO_AM_I_VALUE) {
        LOG_ERR("Unexpected WHO_AM_I: 0x%02X (expected 0x%02X)",
                who_am_i, LSM6DS3_WHO_AM_I_VALUE);
        return false;
    }

    LOG_INF("LSM6DS3 detected (WHO_AM_I: 0x%02X)", who_am_i);

    /* Configure accelerometer: ODR 104 Hz, ±4g */
    if (lsm6ds3_write_reg(LSM6DS3_CTRL1_XL, IMU_ODR | IMU_XL_FS) != 0) {
        LOG_ERR("Failed to configure accelerometer");
        return false;
    }

    /* Configure gyroscope: ODR 104 Hz, ±500 dps */
    if (lsm6ds3_write_reg(LSM6DS3_CTRL2_G, IMU_ODR | IMU_G_FS) != 0) {
        LOG_ERR("Failed to configure gyroscope");
        return false;
    }

    /* Enable block data update (BDU) */
    if (lsm6ds3_write_reg(LSM6DS3_CTRL3_C, 0x44) != 0) {  /* BDU + IF_INC */
        LOG_ERR("Failed to configure CTRL3");
        return false;
    }

    s_initialized = true;
    s_last_sample_us = k_uptime_get() * 1000;

    LOG_INF("LSM6DS3 initialized: ODR=104Hz, Accel=±4g, Gyro=±500dps");
    return true;
}

/**
 * @brief Sample IMU and update fusion filter
 *
 * Call this at the configured ODR (104 Hz).
 */
void utlp_imu_update(void)
{
    if (!s_initialized) {
        return;
    }

    /* Read all sensor data (12 bytes: gyro XYZ + accel XYZ) */
    uint8_t data[12];
    if (lsm6ds3_read_regs(LSM6DS3_OUTX_L_G, data, 12) != 0) {
        LOG_WRN("Failed to read sensor data");
        return;
    }

    /* Parse gyroscope (raw → dps → rad/s) */
    int16_t gx_raw = (int16_t)(data[0] | (data[1] << 8));
    int16_t gy_raw = (int16_t)(data[2] | (data[3] << 8));
    int16_t gz_raw = (int16_t)(data[4] | (data[5] << 8));

    float gx_dps = gx_raw * IMU_G_SENSITIVITY / 1000.0f;
    float gy_dps = gy_raw * IMU_G_SENSITIVITY / 1000.0f;
    float gz_dps = gz_raw * IMU_G_SENSITIVITY / 1000.0f;

    float gx_rad = gx_dps * (3.14159265f / 180.0f);
    float gy_rad = gy_dps * (3.14159265f / 180.0f);
    float gz_rad = gz_dps * (3.14159265f / 180.0f);

    /* Parse accelerometer (raw → mg → g) */
    int16_t ax_raw = (int16_t)(data[6] | (data[7] << 8));
    int16_t ay_raw = (int16_t)(data[8] | (data[9] << 8));
    int16_t az_raw = (int16_t)(data[10] | (data[11] << 8));

    float ax_mg = ax_raw * IMU_XL_SENSITIVITY;
    float ay_mg = ay_raw * IMU_XL_SENSITIVITY;
    float az_mg = az_raw * IMU_XL_SENSITIVITY;

    float ax_g = ax_mg / 1000.0f;
    float ay_g = ay_mg / 1000.0f;
    float az_g = az_mg / 1000.0f;

    /* Calculate dt */
    int64_t now_us = k_uptime_get() * 1000;
    float dt = (now_us - s_last_sample_us) / 1000000.0f;
    s_last_sample_us = now_us;

    /* Clamp dt to reasonable range */
    if (dt <= 0.0f || dt > 0.1f) {
        dt = 1.0f / 104.0f;  /* Default to 104 Hz */
    }

    /* Update Madgwick filter */
    k_spinlock_key_t key = k_spin_lock(&s_imu_spinlock);
    madgwick_update(gx_rad, gy_rad, gz_rad, ax_g, ay_g, az_g, dt);
    k_spin_unlock(&s_imu_spinlock, key);

    /* Update motion confidence */
    float accel_mag = sqrtf(ax_mg * ax_mg + ay_mg * ay_mg + az_mg * az_mg);
    update_motion_confidence(accel_mag);
}

/**
 * @brief IMU state callback for RFIP (Claim 114: Yield Pattern)
 *
 * This is the callback registered with rfip_imu_register_callback().
 * RFIP calls this to get current IMU state.
 */
bool utlp_imu_get_state_callback(rfip_imu_state_t *state)
{
    if (!s_initialized || !state) {
        return false;
    }

    /* Read current sensor data */
    uint8_t data[12];
    if (lsm6ds3_read_regs(LSM6DS3_OUTX_L_G, data, 12) != 0) {
        return false;
    }

    /* Parse gyroscope */
    int16_t gx_raw = (int16_t)(data[0] | (data[1] << 8));
    int16_t gy_raw = (int16_t)(data[2] | (data[3] << 8));
    int16_t gz_raw = (int16_t)(data[4] | (data[5] << 8));

    state->gyro_x_dps = gx_raw * IMU_G_SENSITIVITY / 1000.0f;
    state->gyro_y_dps = gy_raw * IMU_G_SENSITIVITY / 1000.0f;
    state->gyro_z_dps = gz_raw * IMU_G_SENSITIVITY / 1000.0f;

    /* Parse accelerometer */
    int16_t ax_raw = (int16_t)(data[6] | (data[7] << 8));
    int16_t ay_raw = (int16_t)(data[8] | (data[9] << 8));
    int16_t az_raw = (int16_t)(data[10] | (data[11] << 8));

    state->accel_x_mg = ax_raw * IMU_XL_SENSITIVITY;
    state->accel_y_mg = ay_raw * IMU_XL_SENSITIVITY;
    state->accel_z_mg = az_raw * IMU_XL_SENSITIVITY;

    /* Copy quaternion with spinlock protection */
    k_spinlock_key_t key = k_spin_lock(&s_imu_spinlock);
    state->quat_w = s_quat[0];
    state->quat_x = s_quat[1];
    state->quat_y = s_quat[2];
    state->quat_z = s_quat[3];

    /* Calculate gravity vector from quaternion */
    quaternion_to_gravity(&state->gravity_x, &state->gravity_y, &state->gravity_z);
    k_spin_unlock(&s_imu_spinlock, key);

    /* Timestamp and motion confidence */
    state->timestamp_us = k_uptime_get() * 1000;
    state->motion_confidence = s_motion_confidence;
    state->valid = true;

    return true;
}

/**
 * @brief Check if IMU is initialized
 */
bool utlp_imu_is_initialized(void)
{
    return s_initialized;
}

/**
 * @brief Get current motion confidence
 */
uint8_t utlp_imu_get_motion_confidence(void)
{
    return s_motion_confidence;
}

#else /* !UTLP_HAL_MG24_IMU_AVAILABLE */

/*============================================================================
 * STUB IMPLEMENTATION (Platform Not Available)
 *==========================================================================*/

bool utlp_imu_init(void) { return false; }
void utlp_imu_update(void) { }
bool utlp_imu_get_state_callback(rfip_imu_state_t *state) { (void)state; return false; }
bool utlp_imu_is_initialized(void) { return false; }
uint8_t utlp_imu_get_motion_confidence(void) { return 0; }

#endif /* UTLP_HAL_MG24_IMU_AVAILABLE */
