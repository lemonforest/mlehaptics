/**
 * @file utlp_hal_c64.c
 * @brief Hardware Abstraction Layer - Commodore 64 Implementation
 *
 * UTLP HAL for the Commodore 64, proving that utlp_skeleton.c
 * compiles unchanged on a 1MHz 6502 from 1982.
 *
 * Hardware Mapping:
 *   - Time:     CIA Timer A+B chained (1MHz, ~1us resolution)
 *   - Actuator: VIC-II border color ($D020)
 *   - Radio:    User Port serial (Phase 2, stub for Phase 1)
 *   - Logging:  Screen output via cprintf
 *
 * @version 1.0.0
 * @date 2025-12-28
 */

/*
 * Include the LOCAL transformed header (C89-compatible).
 * The build script transforms utlp_hal.h from C99 to C89.
 */
#include "utlp_hal.h"

#include <stdio.h>
#include <string.h>
#include <stdarg.h>

/* cc65 headers */
#include <conio.h>
#include <peekpoke.h>
#include <c64.h>

/*============================================================================
 * C64 HARDWARE REGISTERS
 *==========================================================================*/

/* CIA #1 (Keyboard, Joystick, Timer) - $DC00-$DC0F */
#define CIA1_TA_LO      0xDC04  /* Timer A low byte */
#define CIA1_TA_HI      0xDC05  /* Timer A high byte */
#define CIA1_TB_LO      0xDC06  /* Timer B low byte */
#define CIA1_TB_HI      0xDC07  /* Timer B high byte */
#define CIA1_TOD_10TH   0xDC08  /* Time-of-Day 1/10 seconds */
#define CIA1_TOD_SEC    0xDC09  /* Time-of-Day seconds */
#define CIA1_TOD_MIN    0xDC0A  /* Time-of-Day minutes */
#define CIA1_TOD_HR     0xDC0B  /* Time-of-Day hours */
#define CIA1_ICR        0xDC0D  /* Interrupt Control Register */
#define CIA1_CRA        0xDC0E  /* Control Register A */
#define CIA1_CRB        0xDC0F  /* Control Register B */

/* CIA #2 (User Port, Serial) - $DD00-$DD0F */
#define CIA2_PRA        0xDD00  /* Port A (VIC bank select) */
#define CIA2_PRB        0xDD01  /* Port B (User Port data) */
#define CIA2_DDRA       0xDD02  /* Port A direction */
#define CIA2_DDRB       0xDD03  /* Port B direction */
#define CIA2_TA_LO      0xDD04  /* Timer A low byte */
#define CIA2_TA_HI      0xDD05  /* Timer A high byte */

/* VIC-II registers */
#define VIC_BORDER      0xD020  /* Border color */
#define VIC_BGCOLOR     0xD021  /* Background color */

/* C64 colors - use cc65's definitions from c64.h if available */
#ifndef COLOR_BLACK
#define COLOR_BLACK     0
#define COLOR_WHITE     1
#define COLOR_RED       2
#define COLOR_CYAN      3
#define COLOR_PURPLE    4
#define COLOR_GREEN     5
#define COLOR_BLUE      6
#define COLOR_YELLOW    7
#endif

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

/* The Global Time Union - 584,000 year clock on 64KB RAM! */
static utlp_time_t g_system_time = UTLP_TIME_ZERO;

/* Time synchronization offset (local + offset = atomic) */
static int32_t g_time_offset_us = 0;

/* Last timer reading for delta calculation */
static uint16_t g_last_timer_a = 0;

/* Fake MAC address for C64 (derived from machine type) */
static uint8_t g_local_mac[UTLP_MAC_SIZE] = {0xC6, 0x40, 0x19, 0x82, 0x00, 0x01};

/* Logging buffer (no variadic sprintf on C64, use simple approach) */
static char g_log_buffer[80];

/*============================================================================
 * TIMER INITIALIZATION
 *
 * Configure CIA1 Timer A to free-run at 1MHz (CPU clock).
 * This gives us ~1 microsecond resolution.
 *
 * Timer A counts DOWN from $FFFF to $0000, then reloads.
 * We track overflows to build a 32-bit microsecond counter.
 *==========================================================================*/

static void init_timer(void)
{
    /*
     * Stop Timer A, set to continuous mode, load $FFFF
     * Control Register A bits:
     *   bit 0: Start timer (0=stop, 1=start)
     *   bit 3: One-shot (0=continuous, 1=one-shot)
     *   bit 4: Force load (1=load latch into timer)
     */
    POKE(CIA1_CRA, 0x00);           /* Stop timer */
    POKE(CIA1_TA_LO, 0xFF);         /* Latch low = $FF */
    POKE(CIA1_TA_HI, 0xFF);         /* Latch high = $FF */
    POKE(CIA1_CRA, 0x11);           /* Force load, start continuous */

    /* Clear state - memset for C89 compatibility (no compound literal assign) */
    memset(&g_system_time, 0, sizeof(g_system_time));
    g_last_timer_a = 0;
}

/*============================================================================
 * TIME API IMPLEMENTATION
 *==========================================================================*/

void utlp_hal_init(void)
{
    /* Clear screen and show initialization message */
    clrscr();
    textcolor(COLOR_CYAN);
    cprintf("UTLP HAL C64 v1.0\r\n");
    textcolor(COLOR_WHITE);
    cprintf("CIA Timer: 1MHz\r\n");
    cprintf("Actuator: Border color\r\n");
    cprintf("\r\n");

    /* Initialize timer for microsecond counting */
    init_timer();

    /* Set border to black initially */
    POKE(VIC_BORDER, COLOR_BLACK);
}

/**
 * @brief Update the cascaded clock from CIA Timer A
 *
 * This is the heart of the ripple-carry approach:
 *   1. Read CIA Timer A (16-bit, counts DOWN at 1MHz)
 *   2. Calculate 16-bit delta since last read
 *   3. Add delta to words.w0 with ripple carry to w1/w2/w3
 *
 * The beauty: We never load 64 bits into registers.
 * Only w0 changes on every call. w1/w2/w3 rarely touched.
 */
static void update_clock(void)
{
    uint8_t lo, hi;
    uint16_t timer_a;
    uint16_t diff;
    uint16_t old_w0;

    /* 1. Read CIA1 Timer A (16-bit, counts down) */
    lo = PEEK(CIA1_TA_LO);
    hi = PEEK(CIA1_TA_HI);
    timer_a = 65535 - ((uint16_t)hi << 8 | lo);  /* Invert: counts UP */

    /* 2. Calculate 16-bit delta (unsigned math handles wrap) */
    diff = timer_a - g_last_timer_a;

    /* 3. Ripple Carry Add */
    old_w0 = g_system_time.words.w0;
    g_system_time.words.w0 += diff;

    if (g_system_time.words.w0 < old_w0) {
        /* Ripple to w1 */
        if (++g_system_time.words.w1 == 0) {
            /* Ripple to w2 */
            if (++g_system_time.words.w2 == 0) {
                /* Ripple to w3 (The 584,000 year counter) */
                g_system_time.words.w3++;
            }
        }
    }

    g_last_timer_a = timer_a;
}

/**
 * @brief Get current time via output pointer
 *
 * cc65 LIMITATION: Cannot return structs > 4 bytes by value.
 * Uses output pointer instead.
 *
 * @param out Pointer to utlp_time_t to fill with current time
 */
void utlp_hal_get_time_ptr(utlp_time_t *out)
{
    update_clock();
    *out = g_system_time;
}

/**
 * @brief Get atomic time (local time + offset) via output pointer
 *
 * cc65 LIMITATION: Cannot return structs > 4 bytes by value.
 * Offset is applied to low 32-bits only (sufficient for ~71 min range).
 *
 * @param out Pointer to utlp_time_t to fill with atomic time
 */
void utlp_hal_get_atomic_time_ptr(utlp_time_t *out)
{
    uint32_t old_lo;

    update_clock();
    *out = g_system_time;

    /* Add 32-bit offset to low dword */
    old_lo = out->dwords.lo;
    out->dwords.lo += g_time_offset_us;

    /* Handle carry to high dword */
    if ((g_time_offset_us > 0) && (out->dwords.lo < old_lo)) {
        out->dwords.hi++;
    } else if ((g_time_offset_us < 0) && (out->dwords.lo > old_lo)) {
        out->dwords.hi--;
    }
}

void utlp_hal_set_time_offset(int32_t offset_us)
{
    g_time_offset_us = offset_us;
}

void utlp_hal_yield(void)
{
    /*
     * No preemptive multitasking on C64.
     * Just a short delay to prevent tight loops from monopolizing.
     *
     * On a real system, this might poll keyboard or do housekeeping.
     */
    uint8_t i;
    for (i = 0; i < 100; i++) {
        /* Short delay loop */
    }
}

/*============================================================================
 * RADIO API IMPLEMENTATION (STUB FOR PHASE 1)
 *
 * Phase 1: No networking - return stubs
 * Phase 2: Implement User Port serial (software UART)
 *==========================================================================*/

void utlp_hal_get_mac(uint8_t *mac)
{
    memcpy(mac, g_local_mac, UTLP_MAC_SIZE);
}

bool utlp_hal_tx_packet(const uint8_t *peer_mac, const uint8_t *data, size_t len)
{
    /*
     * Phase 1 stub: No transmission capability.
     * Phase 2 will implement User Port software UART.
     */
    (void)peer_mac;
    (void)data;
    (void)len;
    return false;
}

bool utlp_hal_rx_poll(utlp_packet_t *out_packet)
{
    /*
     * Phase 1 stub: No reception capability.
     * Phase 2 will poll User Port for incoming data.
     */
    (void)out_packet;
    return false;
}

bool utlp_hal_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms)
{
    /*
     * Phase 1 stub: Wait for timeout then return false.
     *
     * We need to actually delay here so the main loop doesn't spin too fast.
     * Each CIA timer tick is ~1us, so timeout_ms * 1000 = microseconds.
     *
     * For simplicity, use a loop-based delay.
     */
    uint32_t target;
    utlp_time_t now_time;

    (void)out_packet;

    /*
     * Simplified delay: check timer for elapsed time.
     * This keeps the main loop running at reasonable speed.
     * Uses only low 32 bits (71 min range - plenty for timeout).
     */
    utlp_hal_get_time_ptr(&now_time);
    target = now_time.dwords.lo + (timeout_ms * 1000);

    do {
        /* Check for keyboard interrupt (STOP key) */
        if (kbhit()) {
            cgetc();  /* Consume key */
            break;
        }
        utlp_hal_get_time_ptr(&now_time);
    } while (now_time.dwords.lo < target);

    return false;
}

/*============================================================================
 * ACTUATOR API IMPLEMENTATION
 *
 * Maps duty_pct to VIC-II border color:
 *   0%   = BLACK (off)
 *   100% = WHITE (full on)
 *
 * For LED blink effect, caller sets duty to 0 or 100.
 *==========================================================================*/

void utlp_hal_set_actuator_phase(int channel, uint32_t frequency_hz,
                                  utlp_float_t phase_deg, utlp_float_t duty_pct)
{
    /*
     * C64 has no hardware PWM. We use border color as binary on/off.
     *
     * On C64 (cc65): duty_pct is fixed-point (0-10000 = 0-100%)
     *   duty_pct > 5000 = WHITE (on)   [5000 = 50.00%]
     *   duty_pct <= 5000 = BLACK (off)
     *
     * On ESP32: duty_pct is float, but this code path isn't used there.
     */
    (void)channel;
    (void)frequency_hz;
    (void)phase_deg;

#if UTLP_NO_FLOAT
    /* C64: Fixed-point comparison (0-10000 scale) */
    if (duty_pct > 5000) {
        POKE(VIC_BORDER, COLOR_WHITE);
    } else {
        POKE(VIC_BORDER, COLOR_BLACK);
    }
#else
    /* Other platforms: Float comparison */
    if (duty_pct > 50.0f) {
        POKE(VIC_BORDER, COLOR_WHITE);
    } else {
        POKE(VIC_BORDER, COLOR_BLACK);
    }
#endif
}

void utlp_hal_actuator_stop(int channel)
{
    (void)channel;
    POKE(VIC_BORDER, COLOR_BLACK);
}

/*============================================================================
 * LOGGING API IMPLEMENTATION
 *
 * cc65 has limited printf support. We use cprintf for screen output.
 *
 * IMPORTANT: cc65's vprintf/vsprintf may not be available or may have
 * limited functionality. We implement a simplified version that handles
 * common format specifiers.
 *==========================================================================*/

/**
 * @brief Simple format string handler for C64
 *
 * Handles: %s, %d, %u, %lld, %llu, %02X
 * Limited but sufficient for UTLP logging.
 */
static void print_formatted(const char *format, va_list args)
{
    const char *p = format;
    char c;
    int is_long;  /* Track 'l' modifier */

    while ((c = *p++) != '\0') {
        if (c != '%') {
            cputc(c);
            continue;
        }

        /* Format specifier */
        c = *p++;
        if (c == '\0') break;

        /* Handle width/flags */
        while (c == '0' || c == '+' || c == '-' || c == ' ' ||
               (c >= '1' && c <= '9') || c == '.') {
            c = *p++;
            if (c == '\0') return;
        }

        /* Handle length modifiers */
        is_long = 0;
        if (c == 'l') {
            is_long = 1;
            c = *p++;
            if (c == 'l') c = *p++;  /* Skip second 'l' for %lld/%llu */
        }

        switch (c) {
            case 's': {
                const char *s = va_arg(args, const char *);
                cputs(s ? s : "(null)");
                break;
            }
            case 'd':
            case 'i':
                /*
                 * cc65 varargs: Small types promoted to int (16-bit).
                 * %d  = int (16-bit)
                 * %ld = long (32-bit)
                 */
                if (is_long) {
                    long val = va_arg(args, long);
                    cprintf("%ld", val);
                } else {
                    int val = va_arg(args, int);
                    cprintf("%d", val);
                }
                break;
            case 'u':
                if (is_long) {
                    unsigned long val = va_arg(args, unsigned long);
                    cprintf("%lu", val);
                } else {
                    unsigned val = va_arg(args, unsigned);
                    cprintf("%u", val);
                }
                break;
            case 'x':
            case 'X':
                if (is_long) {
                    unsigned long val = va_arg(args, unsigned long);
                    cprintf("%lx", val);
                } else {
                    unsigned val = va_arg(args, unsigned);
                    cprintf("%x", val);
                }
                break;
            case '%':
                cputc('%');
                break;
            default:
                cputc('%');
                cputc(c);
                break;
        }
    }
}

void utlp_hal_log_info(const char *tag, const char *format, ...)
{
    va_list args;

    (void)tag;  /* C64: Skip tag to save columns */

    textcolor(COLOR_GREEN);
    cputc('I');
    cputc(':');
    textcolor(COLOR_WHITE);

    va_start(args, format);
    print_formatted(format, args);
    va_end(args);

    cprintf("\r\n");
}

void utlp_hal_log_error(const char *tag, const char *format, ...)
{
    va_list args;

    (void)tag;  /* C64: Skip tag to save columns */

    textcolor(COLOR_RED);
    cputc('E');
    cputc(':');
    textcolor(COLOR_WHITE);

    va_start(args, format);
    print_formatted(format, args);
    va_end(args);

    cprintf("\r\n");
}

void utlp_hal_log_warn(const char *tag, const char *format, ...)
{
    va_list args;

    (void)tag;  /* C64: Skip tag to save columns */

    textcolor(COLOR_YELLOW);
    cputc('W');
    cputc(':');
    textcolor(COLOR_WHITE);

    va_start(args, format);
    print_formatted(format, args);
    va_end(args);

    cprintf("\r\n");
}
