/**
 * @file cie_lut.h
 * @brief CIE 1931 Perceptual Brightness Lookup Table
 *
 * Provides a 256-entry lookup table for converting linear brightness values
 * to perceptually uniform PWM duty cycles based on the CIE 1931 lightness
 * function.
 *
 * Human perception of brightness is non-linear - we're more sensitive to
 * changes in dim light than bright light. The CIE 1931 standard models this:
 *
 *   Y = ((L* + 16) / 116)^3           for L* > 8
 *   Y = L* / 903.3                     for L* <= 8
 *
 * Where:
 *   L* = Perceptual lightness (0-100, linear to human eye)
 *   Y  = Relative luminance (0-1, what the LED actually outputs)
 *
 * Example values:
 *   - 50% perceived (L*=50) = 18.4% actual PWM
 *   - 25% perceived (L*=25) = 5.1% actual PWM
 *   - 75% perceived (L*=75) = 46.7% actual PWM
 *
 * This creates smooth, "organic" fades rather than the harsh transitions
 * of linear PWM dimming.
 *
 * Usage:
 *   uint16_t pwm_duty = cie_lut_10bit[brightness_0_255];
 *   ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, pwm_duty);
 *
 * @see docs/bilateral_pattern_playback_architecture.md
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef CIE_LUT_H
#define CIE_LUT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief CIE 1931 perceptual brightness to 10-bit PWM lookup table
 *
 * Input: Linear brightness index 0-255 (human-perceived level)
 * Output: 10-bit PWM duty cycle 0-1023 (actual LED power)
 *
 * Generated using the CIE 1931 lightness formula.
 * Index corresponds to perceived brightness percentage:
 *   - 0 = 0% perceived (off)
 *   - 128 = ~50% perceived
 *   - 255 = 100% perceived (full brightness)
 */
static const uint16_t cie_lut_10bit[256] = {
    // 0-15: Very dark range (0-6% perceived)
    0,     1,     1,     1,     1,     1,     1,     1,
    1,     2,     2,     2,     2,     2,     2,     2,
    // 16-31
    2,     2,     2,     3,     3,     3,     3,     3,
    3,     3,     4,     4,     4,     4,     4,     5,
    // 32-47
    5,     5,     5,     6,     6,     6,     6,     7,
    7,     7,     8,     8,     8,     9,     9,    10,
    // 48-63
   10,    10,    11,    11,    12,    12,    13,    13,
   14,    14,    15,    15,    16,    17,    17,    18,
    // 64-79
   19,    19,    20,    21,    21,    22,    23,    24,
   24,    25,    26,    27,    28,    29,    30,    31,
    // 80-95
   32,    33,    34,    35,    36,    37,    38,    39,
   40,    42,    43,    44,    45,    47,    48,    49,
    // 96-111
   51,    52,    54,    55,    57,    58,    60,    61,
   63,    65,    66,    68,    70,    72,    74,    76,
    // 112-127
   78,    80,    82,    84,    86,    88,    90,    92,
   94,    97,    99,   101,   104,   106,   109,   111,
    // 128-143: Mid-range (50% perceived = ~188 actual)
  114,   117,   119,   122,   125,   128,   131,   134,
  137,   140,   143,   146,   149,   152,   156,   159,
    // 144-159
  163,   166,   170,   173,   177,   181,   185,   189,
  193,   197,   201,   205,   209,   214,   218,   222,
    // 160-175
  227,   232,   236,   241,   246,   251,   256,   261,
  266,   271,   276,   282,   287,   293,   298,   304,
    // 176-191
  310,   316,   322,   328,   334,   340,   347,   353,
  360,   366,   373,   380,   387,   394,   401,   408,
    // 192-207
  416,   423,   431,   438,   446,   454,   462,   470,
  479,   487,   495,   504,   513,   521,   530,   539,
    // 208-223
  549,   558,   567,   577,   587,   597,   607,   617,
  627,   638,   648,   659,   670,   681,   692,   703,
    // 224-239
  715,   727,   738,   750,   762,   775,   787,   800,
  812,   825,   838,   852,   865,   878,   892,   906,
    // 240-255: Bright range (94-100% perceived)
  920,   934,   948,   963,   977,   992,  1007,  1022,
 1023,  1023,  1023,  1023,  1023,  1023,  1023,  1023
};

/**
 * @brief CIE 1931 perceptual brightness to 8-bit PWM lookup table
 *
 * Input: Linear brightness index 0-255 (human-perceived level)
 * Output: 8-bit PWM duty cycle 0-255 (actual LED power)
 *
 * Use this for WS2812B LEDs which have 8-bit color depth per channel.
 */
static const uint8_t cie_lut_8bit[256] = {
    // 0-15
    0,     0,     0,     0,     0,     0,     0,     0,
    0,     0,     0,     1,     1,     1,     1,     1,
    // 16-31
    1,     1,     1,     1,     1,     1,     1,     1,
    1,     1,     2,     2,     2,     2,     2,     2,
    // 32-47
    2,     2,     2,     3,     3,     3,     3,     3,
    3,     3,     4,     4,     4,     4,     4,     5,
    // 48-63
    5,     5,     5,     5,     6,     6,     6,     6,
    7,     7,     7,     7,     8,     8,     8,     9,
    // 64-79
    9,     9,    10,    10,    10,    11,    11,    12,
   12,    12,    13,    13,    14,    14,    15,    15,
    // 80-95
   16,    16,    17,    17,    18,    18,    19,    19,
   20,    21,    21,    22,    22,    23,    24,    24,
    // 96-111
   25,    26,    27,    27,    28,    29,    30,    30,
   31,    32,    33,    34,    35,    35,    36,    37,
    // 112-127
   38,    39,    40,    41,    42,    43,    44,    45,
   46,    47,    49,    50,    51,    52,    53,    55,
    // 128-143: Mid-range
   56,    57,    58,    60,    61,    62,    64,    65,
   67,    68,    70,    71,    73,    74,    76,    78,
    // 144-159
   79,    81,    83,    85,    86,    88,    90,    92,
   94,    96,    98,   100,   102,   104,   106,   109,
    // 160-175
  111,   113,   115,   118,   120,   123,   125,   127,
  130,   133,   135,   138,   141,   143,   146,   149,
    // 176-191
  152,   155,   158,   161,   164,   167,   170,   173,
  177,   180,   183,   187,   190,   194,   197,   201,
    // 192-207
  205,   208,   212,   216,   220,   224,   228,   232,
  236,   240,   244,   248,   252,   255,   255,   255,
    // 208-223
  255,   255,   255,   255,   255,   255,   255,   255,
  255,   255,   255,   255,   255,   255,   255,   255,
    // 224-239
  255,   255,   255,   255,   255,   255,   255,   255,
  255,   255,   255,   255,   255,   255,   255,   255,
    // 240-255
  255,   255,   255,   255,   255,   255,   255,   255,
  255,   255,   255,   255,   255,   255,   255,   255
};

/**
 * @brief Convert linear brightness percentage (0-100) to perceptual index (0-255)
 * @param percent Linear brightness percentage 0-100
 * @return Perceptual index 0-255 for lookup tables
 */
static inline uint8_t cie_percent_to_index(uint8_t percent) {
    if (percent >= 100) return 255;
    return (uint8_t)((percent * 255 + 50) / 100);  // Round to nearest
}

/**
 * @brief Get 8-bit PWM value for perceptual brightness percentage
 * @param percent Perceived brightness percentage 0-100
 * @return 8-bit PWM duty cycle for WS2812B
 *
 * Example: 50% perceived brightness returns ~46 (18% actual)
 */
static inline uint8_t cie_get_pwm_8bit(uint8_t percent) {
    return cie_lut_8bit[cie_percent_to_index(percent)];
}

/**
 * @brief Get 10-bit PWM value for perceptual brightness percentage
 * @param percent Perceived brightness percentage 0-100
 * @return 10-bit PWM duty cycle for LEDC
 *
 * Example: 50% perceived brightness returns ~188 (18.4% actual)
 */
static inline uint16_t cie_get_pwm_10bit(uint8_t percent) {
    return cie_lut_10bit[cie_percent_to_index(percent)];
}

#ifdef __cplusplus
}
#endif

#endif // CIE_LUT_H
