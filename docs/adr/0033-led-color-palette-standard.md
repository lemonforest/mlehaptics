# 0033: LED Color Palette Standard

**Date:** 2025-11-13
**Phase:** Phase 1b
**Status:** Approved
**Type:** Architecture

---

## Summary (Y-Statement)

In the context of mobile app control for WS2812B RGB LED colors via BLE Configuration Service,
facing a palette mismatch between `ble_manager.c` and `led_control.c` that would cause incorrect colors,
we decided to standardize on a single 16-color palette with `ble_manager.c` as authoritative source,
and neglected maintaining separate palettes in different modules,
to achieve consistent "what you select is what you get" user experience,
accepting the need to synchronize palette definitions during modular refactoring.

---

## Problem Statement

Mobile app control via BLE Configuration Service (AD032) includes a 16-color palette mode for WS2812B RGB LED control. During modular architecture implementation, a palette mismatch was discovered between `ble_manager.c` (master palette) and `led_control.c` (hardware implementation) - colors 8-15 were completely different, which would cause incorrect LED colors when users selected palette indices via mobile app.

---

## Context

**Background:**
- Mobile app sends palette index (0-15) via BLE Configuration Service
- `ble_manager.c` stores palette definition for app synchronization
- `led_control.c` implements WS2812B hardware control
- Palette mismatch discovered during Phase 1b modular refactoring
- Colors 8-15 differed completely between modules

**Requirements:**
- Single source of truth for palette definition
- Consistent color output (mobile app → BLE → hardware)
- Support for both palette mode and custom RGB mode
- Brightness scaling (10-30%) for user comfort

---

## Decision

Standardize on a single 16-color palette across all modules, with `ble_manager.c` as the authoritative source and `led_control.c` synchronized to match.

### 16-Color Palette Standard

| Index | Color Name | RGB Values | Hex | Notes |
|-------|------------|------------|-----|-------|
| 0 | Red | (255, 0, 0) | #FF0000 | Primary colors |
| 1 | Green | (0, 255, 0) | #00FF00 | Primary colors |
| 2 | Blue | (0, 0, 255) | #0000FF | Primary colors |
| 3 | Yellow | (255, 255, 0) | #FFFF00 | Secondary colors |
| 4 | Cyan | (0, 255, 255) | #00FFFF | Secondary colors |
| 5 | Magenta | (255, 0, 255) | #FF00FF | Secondary colors |
| 6 | Orange | (255, 128, 0) | #FF8000 | Warm tones |
| 7 | Purple | (128, 0, 255) | #8000FF | Cool tones |
| 8 | Spring Green | (0, 255, 128) | #00FF80 | Nature colors |
| 9 | Pink | (255, 192, 203) | #FFC0CB | Soft colors |
| 10 | White | (255, 255, 255) | #FFFFFF | Neutral |
| 11 | Olive | (128, 128, 0) | #808000 | Earth tones |
| 12 | Teal | (0, 128, 128) | #008080 | Cool tones |
| 13 | Violet | (128, 0, 128) | #800080 | Cool tones |
| 14 | Turquoise | (64, 224, 208) | #40E0D0 | Cool tones |
| 15 | Dark Orange | (255, 140, 0) | #FF8C00 | Warm tones |

### Palette Design Rationale

- **0-2**: Primary colors (Red/Green/Blue) - Essential basics
- **3-5**: Secondary colors (Yellow/Cyan/Magenta) - RGB mixing completes color wheel
- **6-7**: Popular warm/cool tones (Orange/Purple) - User favorites
- **8-15**: Diverse extended palette - Nature colors, soft colors, earth tones, neutrals
- **Balanced distribution**: Warm tones (6,15), cool tones (7,12,13,14), nature (8,11), soft (9,10)

### Usage Flow

1. **Mobile App**: User selects color from palette (sends index 0-15 via BLE)
2. **BLE Manager**: Stores `led_palette_index` in characteristic data
3. **LED Control**: Reads `ble_get_led_palette_index()` and looks up RGB from `led_color_palette[]`
4. **WS2812B**: Applies RGB with brightness scaling (10-30%) and sends to LED hardware

### Brightness Scaling

All RGB values are scaled by brightness percentage (10-30% range for user comfort):

```c
// Example: Red (255,0,0) at 20% brightness → (51,0,0)
uint8_t r_final = (color.r * brightness) / 100;
uint8_t g_final = (color.g * brightness) / 100;
uint8_t b_final = (color.b * brightness) / 100;
```

---

## Consequences

### Benefits

- ✅ **Consistency:** Mobile app → BLE → Hardware produces expected LED colors
- ✅ **User Experience:** What you select is what you get (WYSIWYG)
- ✅ **Maintenance:** Single source of truth for palette definition
- ✅ **Documentation:** Clear reference for mobile app developers
- ✅ **Flexibility:** 16 colors covers most therapeutic/preference needs
- ✅ **Fallback:** Users can always use Custom RGB mode for exact colors

### Drawbacks

- Requires synchronization between `ble_manager.c` and `led_control.c` during updates
- Palette is fixed at compile time (not user-customizable)
- 16 colors may not cover all user preferences (mitigated by Custom RGB mode)

---

## Options Considered

### Option A: Separate Palettes (Original Implementation)

**Pros:**
- Module independence
- No synchronization needed

**Cons:**
- Color mismatch between selection and output
- Poor user experience (unexpected colors)
- Difficult to debug

**Selected:** NO
**Rationale:** Unacceptable user experience, debugging nightmare

### Option B: Single Palette with ble_manager.c Authority (Selected)

**Pros:**
- Single source of truth
- Consistent color output
- Easy to document
- Mobile app uses same palette

**Cons:**
- Requires synchronization during updates
- Fixed at compile time

**Selected:** YES
**Rationale:** Best balance of consistency and maintainability

### Option C: Runtime Palette Loading

**Pros:**
- User-customizable palettes
- Maximum flexibility

**Cons:**
- Dynamic memory allocation (JPL violation)
- Complex implementation
- No clear use case for custom palettes

**Selected:** NO
**Rationale:** Unnecessary complexity, JPL compliance issue

---

## Related Decisions

### Related
- AD032: BLE Configuration Service Architecture - Defines palette mode characteristic
- AD032: BLE Configuration Service Architecture - Also defines Custom RGB mode alternative

---

## Implementation Notes

### Code References

**Master Definition** (`src/ble_manager.c`):
```c
const rgb_color_t color_palette[16] = {
    {255, 0,   0,   "Red"},
    {0,   255, 0,   "Green"},
    {0,   0,   255, "Blue"},
    {255, 255, 0,   "Yellow"},
    {0,   255, 255, "Cyan"},
    {255, 0,   255, "Magenta"},
    {255, 128, 0,   "Orange"},
    {128, 0,   255, "Purple"},
    {0,   255, 128, "Spring Green"},
    {255, 192, 203, "Pink"},
    {255, 255, 255, "White"},
    {128, 128, 0,   "Olive"},
    {0,   128, 128, "Teal"},
    {128, 0,   128, "Violet"},
    {64,  224, 208, "Turquoise"},
    {255, 140, 0,   "Dark Orange"}
};
```

**Hardware Implementation** (`src/led_control.c`):
```c
const led_rgb_t led_color_palette[16] = {
    {255,   0,   0},  // 0: Red
    {0,   255,   0},  // 1: Green
    {0,     0, 255},  // 2: Blue
    {255, 255,   0},  // 3: Yellow
    {0,   255, 255},  // 4: Cyan
    {255,   0, 255},  // 5: Magenta
    {255, 128,   0},  // 6: Orange
    {128,   0, 255},  // 7: Purple
    {0,   255, 128},  // 8: Spring Green
    {255, 192, 203},  // 9: Pink
    {255, 255, 255},  // 10: White
    {128, 128,   0},  // 11: Olive
    {0,   128, 128},  // 12: Teal
    {128,   0, 128},  // 13: Violet
    {64,  224, 208},  // 14: Turquoise
    {255, 140,   0}   // 15: Dark Orange
};
```

### Build Environment

- **Environment Name:** `xiao_esp32c6`
- **Configuration File:** `sdkconfig.xiao_esp32c6`
- Palette is compile-time constant (no runtime modification)

### Testing & Verification

**Testing Required:**
- Mobile app palette selection for all 16 indices
- Visual verification of LED colors match selection
- Brightness scaling accuracy (10%, 20%, 30%)
- Custom RGB mode as alternative

**Testing Evidence:**
- Colors 0-7 verified correct during Phase 1b testing
- Colors 8-15 mismatch discovered and fixed during modular refactoring
- Post-fix verification pending hardware testing

---

## Integration Notes

- Palette is compile-time constant (no runtime modification needed)
- Mobile app should display palette preview using these exact RGB values
- BLE characteristic validates index 0-15, returns error for invalid indices
- Default palette index is 0 (Red) on first boot
- NVS saves last-used palette index across power cycles

**Alternative to Palette Mode:**

**Custom RGB Mode** (Color Mode = 1) allows full-spectrum color selection via mobile app color wheel/picker, bypassing palette entirely. This provides unlimited color options but requires more complex UI. Palette mode is for users who prefer quick selection.

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD033 (lines 3223-3350)
Git commit: TBD (migration commit)

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
