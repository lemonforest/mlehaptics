# MLE Haptics Hardware Files

Open-source hardware for EMDR bilateral stimulation device.

## Current Version

**PCB:** v0.663399ADS (Phase 1 - Discrete MOSFET H-bridge)  
**Enclosure:** v0.663399u (Phase 1 - Seeed XIAO ESP32-C6 form factor)

> **Note on Versioning:** These are development versions. The project uses fractional version numbers during active development to indicate pre-release status. First production-ready release will be v1.0.

## ⚠️ Important: Hardware/Firmware Compatibility

**Current hardware (v0.663399ADS) has GPIO fixes implemented:**

The hardware files in this repository include fixes for ESP32-C6 GPIO19/GPIO20 crosstalk issues. **H-bridge control has been moved from GPIO19/GPIO20 to GPIO19/GPIO18**, and the button is now directly connected to GPIO1 (no jumper wire required).

**Firmware test files have NOT been updated yet:**

Existing firmware test files in `/test` directory still use the OLD GPIO definitions. Before building this hardware, you MUST update test file GPIO definitions:

```c
// OLD GPIO definitions (pre-v0.663399ADS hardware)
#define GPIO_BUTTON     20  // ❌ Old hardware via jumper to GPIO1
#define GPIO_M_IN1      19  // ✅ Still correct
#define GPIO_M_IN2      20  // ❌ Changed to GPIO18

// NEW GPIO definitions (v0.663399ADS and later)
#define GPIO_BUTTON      1  // ✅ Direct connection, no jumper
#define GPIO_M_IN1      19  // ✅ Unchanged
#define GPIO_M_IN2      18  // ✅ Moved from GPIO20
```

**Until firmware is updated:** This hardware should be considered developer-only. The schematic and gerbers are correct, but firmware compatibility requires manual GPIO definition updates.

## Repository Structure

```
hardware/
├── pcb/                                    # KiCad PCB project
│   ├── MLE_HAPTICS_PULSER.kicad_pro       # KiCad project file
│   ├── MLE_HAPTICS_PULSER.kicad_sch       # Schematic (GPIO fixes included)
│   ├── MLE_HAPTICS_PULSER.kicad_pcb       # PCB layout
│   ├── libraries/                          # Custom KiCad libraries
│   ├── production/
│   │   ├── gerbers/                        # Manufacturing files
│   │   │   └── gerbers-v.663399ADS.zip    # Gerber files (GPIO fixes included)
│   │   └── schematic/
│   │       └── MLE_HAPTICS_PULSER.pdf     # Schematic PDF (GPIO fixes included)
│   └── images/                             # PCB visualizations
│       ├── pcb_top_view.png
│       └── pcb_bottom_view.png
│
├── enclosure/                              # Mechanical design
│   └── phase1/                             # Phase 1 case design
│       ├── MLE_HAPTICS_PULSER-v0.663399u.FCStd  # FreeCAD source file
│       ├── stl/                            # STL files for 3D printing
│       │   ├── MLE_HAPTICS_PULSER-v0.663399u-bodyTop.stl
│       │   └── MLE_HAPTICS_PULSER-v0.663399u-bodyBottom.stl
│       ├── step/                           # STEP files for CAD interop
│       │   ├── MLE_HAPTICS_PULSER-v0.663399u-bodyTop.step
│       │   ├── MLE_HAPTICS_PULSER-v0.663399u-bodyBottom.step
│       │   └── MLE_HAPTICS_PULSER-v0.663399u-bodyTop_CLRMOD.step
│       └── images/                         # Enclosure renders
│           ├── MLE_HAPTICS_PULSER-v0.663399u.png
│           └── MLE_HAPTICS_PULSER-v0.663399u_WITH_PCB.png
│
├── datasheets/                             # Component datasheets
│   ├── esp32-c6_datasheet_en.pdf
│   ├── WS2812B.pdf
│   └── XIAO-ESP32-C6_v1.0_SCH_PDF_24028.pdf
│
└── docs/                                   # Hardware documentation (TBD)
```

## Quick Start for Builders

### ⚠️ Pre-Build Requirements

1. **Check firmware compatibility:** Ensure your firmware uses GPIO18 for H-bridge IN2 (not GPIO20)
2. **Update test files:** Modify `#define` statements in `/test` files to match new GPIO assignments
3. **Verify schematic:** Review `pcb/production/schematic/MLE_HAPTICS_PULSER.pdf` for current pin assignments

### PCB Manufacturing

1. **Download gerbers:** `pcb/production/gerbers/gerbers-v.663399ADS.zip`
2. **Upload to fab house:** JLCPCB, PCBWay, OSH Park, etc.
3. **Recommended specs:**
   - 2-layer PCB
   - 1.6mm thickness
   - HASL or ENIG finish
   - Any color (black recommended for aesthetics)

### Component Sourcing

**Bill of Materials (BOM):** See main repository `/docs/` for complete parts list

**Key Components:**
- Seeed XIAO ESP32-C6 development board
- ERM vibration motors (φ10mm × 3mm)
- WS2812B RGB LEDs (optional - for therapy light feature)
- H-bridge MOSFETs (AO3400A/AO3401A family)
- dual 350mAh LiPo batteries (700mAh)
- Passive components (resistors, capacitors)

### 3D Printing the Enclosure

**Print Settings:**
- **Layer height:** 0.2mm
- **Infill:** 20% (or higher for durability)
- **Material:** See material guide below

**Files to Print:**
- `enclosure/phase1/stl/MLE_HAPTICS_PULSER-v0.663399u-bodyTop.stl` (Standard)
- `enclosure/phase1/stl/MLE_HAPTICS_PULSER-v0.663399u-bodyBottom.stl`

**STEP Files:** Available in `enclosure/phase1/step/` for CAD modification

### Enclosure Material Selection

The therapy light feature (GPIO17 WS2812B LED) requires case materials with light transmission capability. See main repository documentation for details.

**Material Options:**
- **Light-blocking materials** (motor-only builds): Black nylon SLS, dark PLA/ABS, carbon fiber
- **Light-transmitting materials** (therapy light builds): Clear resin, translucent PETG, light-colored SLS nylon
- **Test before committing:** Print a test piece of your chosen material/color to verify light transmission

### Enclosure Variants: Standard vs CLRMOD

**Standard bodyTop (Default):**

File: `MLE_HAPTICS_PULSER-v0.663399u-bodyTop.step`

Includes access features for development and visual feedback:
- **Reset/Boot pin pinholes:** Access to Seeed XIAO ESP32-C6 Reset and Boot pins for programming
- **LED light transmission holes:** Allows visibility of:
  - **Red battery charge LED:** Hardware-controlled charge status indicator (not firmware accessible)
  - **Amber GPIO15 user LED:** On-board status LED (firmware-controlled via GPIO15)

**Use Standard bodyTop when:**
- Need Reset/Boot pin access for development, debugging, or frequent firmware updates
- Want visual battery charging status indication (red LED)
- Want GPIO15 status LED visible through case for debugging
- Building prototypes or development units

---

**CLRMOD bodyTop (Clean Model):**

File: `MLE_HAPTICS_PULSER-v0.663399u-bodyTop_CLRMOD.step`

Simplified variant that removes all access and light transmission features:
- **No Reset/Boot pin access:** Pinholes removed (cleaner appearance, no programming access)
- **No LED light transmission holes:** Blocks all LED light:
  - Red battery charge status LED (hardware-controlled) - not visible
  - Amber GPIO15 user LED (firmware status indicator) - not visible

**Use CLRMOD bodyTop when:**
- Building production/end-user devices where Reset/Boot access not needed
- Using translucent case materials but want clean appearance without random LED bleed-through
- Prioritizing minimalist aesthetics over visual debug feedback
- Device will be programmed and tested before final case assembly
- Creating a professional, finished product without visible indicator LEDs

**Note:** CLRMOD is only available as STEP file - import into your CAD software and export to STL if needed.

## Hardware Features

### PCB Specifications
- **MCU:** Seeed XIAO ESP32-C6 (RISC-V @ 160MHz)
- **Motor control:** Discrete MOSFET H-bridge (TB6612FNG-style topology)
- **Status LED:** On-board LED (GPIO15, amber)
- **Charge LED:** Hardware battery charge indicator (red, not firmware-controlled)
- **Therapy light:** WS2812B RGB LED (GPIO17, optional)
- **Battery monitoring:** ADC-based voltage measurement
- **Power management:** Deep sleep with button wake capability
- **Connectivity:** BLE 5.0 GATT server

### Current GPIO Pin Mapping (v0.663399ADS)

```
GPIO0:  Back-EMF sensing (ADC1_CH0, OUTA from H-bridge)
GPIO1:  Button input (direct connection, hardware debounced with 10k pull-up)
GPIO2:  Battery voltage monitor (ADC1_CH2, resistor divider)
GPIO15: Status LED (on-board amber LED, ACTIVE LOW, firmware-controlled)
GPIO16: Therapy light enable (P-MOSFET, ACTIVE LOW)
GPIO17: Therapy light output (WS2812B DIN or simple LED)
GPIO18: H-bridge IN2 (motor reverse control) ← MOVED FROM GPIO20
GPIO19: H-bridge IN1 (motor forward control)
GPIO21: Battery monitor enable (P-MOSFET gate control)

Hardware LEDs (not GPIO-controlled):
- Red LED: Battery charging status (hardware-controlled by charge IC)
- Amber LED: Connected to GPIO15 (firmware-controlled user status indicator)
```

**Key Change from Previous Hardware:**
- ✅ **GPIO20 → GPIO18** for H-bridge IN2 (fixes ESP32-C6 GPIO19/GPIO20 crosstalk)
- ✅ **Button on GPIO1** directly (no jumper wire required)

### Enclosure Features
- **Form factor:** Designed for Seeed XIAO ESP32-C6
- **Battery compartment:** Fits dual 350mAh LiPo batteries (700mAh)
- **Button access:** Hardware button accessible through case
- **Material variants:** Supports both opaque and translucent case builds
- **Variant options:** Standard (with LED/pin access) or CLRMOD (clean, no access holes)
- **Phase 1 design:** Discrete MOSFET PCB compatibility

## Hardware Issue Resolution

### ESP32-C6 GPIO19/GPIO20 Crosstalk ✅ FIXED

**Background:** ESP32-C6 GPIO19 and GPIO20 exhibit electrical crosstalk during boot sequence  
**Reference:** [ESP32-C6 GitHub Issue #11975](https://github.com/espressif/esp-idf/issues/11975)  
**Status:** ✅ **RESOLVED in v0.663399ADS hardware**

**Solution Implemented:**
- H-bridge IN2 relocated from GPIO20 → GPIO18
- Button connected directly to GPIO1 (no jumper wire)
- GPIO20 avoided entirely in current design

**Previous Hardware Workaround (pre-v0.663399ADS):**
- Required GPIO18→GPIO1 jumper wire for button
- GPIO20 used for H-bridge control (caused crosstalk issues)

**Current Hardware (v0.663399ADS and later):**
- No jumper wire required
- Clean GPIO routing without crosstalk concerns
- Button and H-bridge both functional

### Firmware Compatibility Notes

**Important:** Firmware test files in `/test` directory still reference OLD GPIO assignments:

```c
// Test files currently use (INCORRECT for v0.663399ADS):
#define GPIO_BUTTON  20   // Should be GPIO1
#define GPIO_M_IN2   20   // Should be GPIO18
```

**Required firmware updates:**
1. Update all test files: `GPIO_BUTTON` from 20 → 1
2. Update all test files: `GPIO_M_IN2` from 20 → 18
3. Verify no remaining references to GPIO20 in motor control code

**This will be addressed in a future firmware update.** Early builders should manually update GPIO definitions before compiling.

## Other Considerations

- **Battery life:** Current design targets 20+ minute sessions; power optimization ongoing
- **Component sourcing:** Some MOSFETs have long lead times; check availability before ordering PCBs

## License

Hardware licensed under **CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S v2)**

This is a copyleft license for hardware designs. Any modifications or derivative works must be released under the same license terms.

Full license text: [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt)

## Datasheets

Key component datasheets are included in `datasheets/` directory:
- **ESP32-C6:** Complete MCU specifications
- **WS2812B:** RGB LED timing and control
- **XIAO ESP32-C6:** Module schematic and pinout

Additional datasheets (MOSFETs, passives) available from component manufacturers.

## Development Status

### Current Hardware (v0.663399ADS)
✅ PCB designed with GPIO crosstalk fixes  
✅ Enclosure v0.663399u validated with hardware  
✅ Discrete MOSFET H-bridge functional  
✅ Button directly connected to GPIO1 (no jumper)  
✅ H-bridge on GPIO18/GPIO19 (crosstalk resolved)  
✅ Standard and CLRMOD case variants available  
⚠️  Firmware test files not yet updated for new GPIO assignments  

### Firmware Development Status
✅ Single-device operation with 5 modes  
✅ BLE GATT server operational  
⚠️  Firmware uses old GPIO definitions (manual update required)  
🔄 Dual-device bilateral pairing protocol in development  

### Phase 2 (Future)
- [ ] Dedicated haptic driver ICs (DRV2605L family evaluation)
- [ ] ERM vs LRA actuator comparative research
- [ ] Enhanced power management

## Assembly Instructions

**Coming Soon:** Detailed assembly guide will be added to `docs/` directory

**Prerequisites:**
- Soldering iron and basic SMD soldering skills
- Multimeter for continuity and voltage testing
- 3D printer or 3D printing service access
- **Firmware modification skills** to update GPIO definitions

**Estimated build time:** 2-3 hours for experienced builders (plus firmware GPIO updates)

## Contributing

Hardware contributions welcome! See main repository `CONTRIBUTING.md` for guidelines.

**Areas of interest:**
- PCB layout optimization
- Alternative enclosure designs (different form factors, materials)
- Bill of materials cost reduction
- Phase 2 haptic driver IC evaluation
- Firmware GPIO definition updates for v0.663399ADS hardware
- STL export of CLRMOD variant for community convenience

## Questions or Issues?

Open a GitHub issue in the main repository with the `hardware` label.

---

**This hardware is part of the MLE Haptics open-source EMDR bilateral stimulation device project.**  
**For firmware, documentation, and project overview, see main repository.**
