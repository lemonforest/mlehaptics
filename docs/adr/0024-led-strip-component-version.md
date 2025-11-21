# 0024: LED Strip Component Version Selection

**Date:** 2025-10-28
**Phase:** 0.4
**Status:** Accepted
**Type:** Build System

---

## Summary (Y-Statement)

In the context of WS2812B LED control for therapy light feedback,
facing decision between mature 2.5.x vs. newer 3.x API versions,
we decided for led_strip version 2.5.x family (specifically ^2.5.0),
and neglected upgrading to version 3.x with breaking changes,
to achieve stability and production-readiness for safety-critical device,
accepting we forego custom color component ordering feature (not needed).

---

## Problem Statement

Need to select appropriate version of Espressif's led_strip component for WS2812B control. Version 3.x introduces breaking API changes with minimal functional benefit, while version 2.5.x is mature and production-tested. Safety-critical medical device prioritizes stability over cutting-edge features.

---

## Context

**Technical Requirements:**
- Control 2× WS2812B RGB LEDs for therapy light feedback
- Standard GRB color format (green-red-blue order)
- ESP-IDF v5.5.0 compatibility required
- Production-quality code for medical device

**Version Comparison:**

**Version 2.5.x (Current):**
- Over 1 year of field deployment
- >1M downloads (proven stability)
- Clean API: `LED_PIXEL_FORMAT_GRB` enum style
- No known critical issues with ESP32-C6 or WS2812B
- Latest 2.5.5 includes build time optimizations for ESP-IDF v5.5.0

**Version 3.x (Latest):**
- Breaking changes: `led_pixel_format` → `color_component_format`
- Enum renamed: `LED_PIXEL_FORMAT_GRB` → `LED_STRIP_COLOR_COMPONENT_FMT_GRB`
- New feature: Custom color component ordering (irrelevant for standard WS2812B GRB)
- Migration effort: 1-2 hours across all test files
- Testing overhead: Full regression testing required

**JPL Coding Standards Context:**
- "If it ain't broke, don't fix it" principle
- Proven code more valuable than latest version for therapeutic applications
- Reduces risk of introducing bugs during development

---

## Decision

We will use led_strip version 2.5.x family (specifically ^2.5.0) for WS2812B control.

**Dependency Specification:**
```yaml
# File: src/idf_component.yml
dependencies:
  espressif/led_strip: "^2.5.0"  # Allows 2.5.x patches, blocks 3.x
```

**Working Code Pattern:**
```c
// Current working pattern (2.5.x)
led_strip_config_t strip_config = {
    .strip_gpio_num = GPIO_WS2812B_DIN,
    .max_leds = WS2812B_NUM_LEDS,
    .led_pixel_format = LED_PIXEL_FORMAT_GRB,  // ✅ 2.5.x API
    .led_model = LED_MODEL_WS2812,
    .flags.invert_out = false,
};

led_strip_rmt_config_t rmt_config = {
    .clk_src = RMT_CLK_SRC_DEFAULT,
    .resolution_hz = 10 * 1000 * 1000,  // 10MHz
    .flags.with_dma = false,
};

ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip));
```

**Automatic Security Updates:**
- Specification `^2.5.0` receives automatic patch updates
- Already received 2.5.0 → 2.5.5 updates automatically
- Stays within 2.5.x family (no breaking changes)
- Future 2.5.6, 2.5.7, etc. will auto-update if released

---

## Consequences

### Benefits

- **Stable and proven:** Over 1 year of production use (>1M downloads)
- **JPL compliant:** Prioritizes stability over bleeding-edge features
- **Zero migration overhead:** Code works today, continues working
- **Automatic security updates:** Patch versions auto-update within 2.5.x
- **Simple API:** Clean, readable configuration
- **Medical device appropriate:** Risk reduction for safety-critical system
- **Development velocity:** No time spent on unnecessary refactoring
- **Focus on therapeutics:** Engineering effort on bilateral stimulation, not library upgrades

### Drawbacks

- **No custom color ordering:** Can't use custom component sequences (not needed for standard WS2812B GRB)
- **Version 3.x features unavailable:** New API features won't be accessible (acceptable tradeoff)
- **Eventually end-of-life:** Version 2.5.x will eventually reach EOL (years away, migration path exists)

---

## Options Considered

### Option A: Version 3.0.1 (Latest Stable)

**Pros:**
- Latest stable release
- Future-proof (newer API)

**Cons:**
- Breaking API changes require code modifications
- Only new feature is custom color ordering (not needed for standard WS2812B)
- Migration effort with zero functional benefit
- Increases risk during critical development phase
- Testing overhead for regression validation

**Selected:** NO
**Rationale:** Zero functional benefit doesn't justify migration risk and effort

### Option B: Lock to Specific Version 2.5.5

**Pros:**
- Maximum version stability
- Predictable builds

**Cons:**
- Loses automatic security patch updates
- More rigid than necessary

**Selected:** NO
**Rationale:** `^2.5.0` range is safer (gets patches automatically) while avoiding breaking changes

### Option C: Version 2.5.x Range (^2.5.0) - CHOSEN

**Pros:**
- Stable API (no breaking changes)
- Automatic security patches
- Production-tested code
- Simple, clear configuration
- JPL coding standards alignment

**Cons:**
- Won't receive 3.x features (acceptable)
- Eventually end-of-life (migration path exists)

**Selected:** YES
**Rationale:** Best balance of stability, security updates, and risk mitigation

### Option D: Version 3.x Range Specification

**Pros:**
- Would receive future 3.x updates

**Cons:**
- Would receive future breaking changes automatically
- Not appropriate for safety-critical medical device

**Selected:** NO
**Rationale:** Unacceptable risk of automatic breaking changes

---

## Related Decisions

### Related
- **AD027: Modular Source File Architecture** - led_control.c/h module uses this component
- WS2812B hardware integration across all test files

---

## Implementation Notes

### Code References

- **Component Manifest:** `src/idf_component.yml` (dependency specification)
- **Test Implementation:** `test/ws2812b_test.c` (reference code pattern)
- **Production Use:** All test files using WS2812B LEDs

**Files Using LED Strip:**
- `test/ws2812b_test.c` - Hardware validation test
- `test/single_device_demo_test.c` - Research study test with integrated LED
- Future bilateral application files

### Build Environment

- **ESP-IDF Version:** v5.5.0
- **Component Version:** 2.5.5 (auto-updated from 2.5.0)
- **Component Source:** Espressif Component Registry
- **Version Range:** ^2.5.0 (allows 2.5.x, blocks 3.x)

### Testing & Verification

**Verification Status:**
- Current build: ✅ Successful with 2.5.5
- Hardware testing: ✅ WS2812B control working correctly
- Test files: ✅ ws2812b_test.c and single_device_demo_test.c validated
- Deep sleep integration: ✅ LED power management verified

**ESP-IDF Compatibility:**
- Version 2.5.x supports ESP-IDF v4.4 through v5.5.0
- Version 3.x drops ESP-IDF v4.x support (not relevant for this project)
- Both versions fully compatible with ESP-IDF v5.5.0 (our target)

---

## Migration Notes

Migrated from `docs/architecture_decisions.md` on 2025-11-21
Original location: AD024
Git commit: (phase 0.4 implementation)

**Decision Timeline:**
- October 2025: Selected version 2.5.0 for initial implementation
- November 2025: Documented as AD024 after version 3.x investigation
- Auto-updated to 2.5.5 via semver range specification

**Migration Path (Future):**

If version 3.x becomes necessary (unlikely scenarios):
- ESP-IDF v6.x forces 3.x requirement
- Critical bug only fixed in 3.x
- Version 2.5.x reaches end-of-life

**Migration Checklist:**
1. Update `src/idf_component.yml`: `espressif/led_strip: "^3.0.1"`
2. Update all `led_strip_config_t` initializations:
   - Replace: `led_pixel_format` → `color_component_format`
   - Replace: `LED_PIXEL_FORMAT_GRB` → `LED_STRIP_COLOR_COMPONENT_FMT_GRB`
3. Clean build: `rm -rf managed_components/espressif__led_strip && pio run -t clean`
4. Test on hardware: Full regression testing of WS2812B functionality

---

**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser Project)
**Last Updated:** 2025-11-21
