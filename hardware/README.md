# MLE Haptics Hardware Files

Open-source hardware for EMDR bilateral stimulation device.

## Hardware Versions

| Version | Status | Description | Gerbers |
|---------|--------|-------------|---------|
| **v0.663399-T** | 🔧 In Development | Tri-Modal (DRV2603 + audio amp + RGB) | `gerbers-v.663399-T.zip` |
| v0.663399ADS | ✅ Production | Discrete MOSFET H-bridge | `gerbers-v.663399ADS.zip` |

**Enclosure:** v0.663399u (compatible with both PCB versions)

> **Note on Versioning:** These are development versions. The project uses fractional version numbers during active development to indicate pre-release status. First production-ready release will be v1.0.

### v0.663399-T (Tri-Modal) - In Development

The "T" designates **Tri-Modal** output: haptic (motor), visual (RGB LED), and audio (amplified speaker). This is the first revision with a dedicated audio amplifier rather than a simple piezo sounder.

The PCB uses dedicated ICs instead of discrete MOSFETs:

- **DRV2603** - Texas Instruments haptic driver (replaces discrete H-bridge)
- **MAX9938** - Current sense amplifier for motor diagnostics
- **MAX98357A** - I2S audio amplifier (future audio feedback feature)
- **Dialight 587-2056-147F** - Addressable RGB LED (replaces WS2812B)

**Firmware status:** Not yet adapted for dedicated IC hardware. GPIO mappings and driver code TBD.

**Build Notes for v0.663399-T:**

**JP1 - LRA/ERM Motor Selection:**
The DRV2603 supports both LRA (Linear Resonant Actuator) and ERM (Eccentric Rotating Mass) motors via a 3-pad jumper:
- **Default (LRA):** JP1 etched between pads 1-2 (no modification needed)
- **For ERM motors:** Scratch/break the 1-2 trace, then solder blob pads 2-3

This approach avoids locking the design to one motor type or consuming a GPIO for runtime selection.

**Motor Selection Note:**
The development path uses a low-power LRA (0.8G, 54mA max) compared to the higher-powered ERM in v0.663399ADS production (15K RPM, 120mA). This is an intentional comparison of a high-power ERM against the lowest-power LRA available - not representative of all LRA options. Higher-force LRAs exist but draw more current.

**⚠️ DRV2603 LRA Resonance Compatibility:**

The DRV2603 auto-resonance tracking range is **140-235 Hz**. This is a critical constraint for LRA selection:

| LRA Size | Typical Resonance | DRV2603 Compatible |
|----------|-------------------|-------------------|
| 8mm | 200-280 Hz | ⚠️ Most are OUT OF RANGE |
| 10mm | 150-200 Hz | ✅ Generally compatible |
| 12mm+ | 120-170 Hz | ✅ Compatible |

**Design Decision:** After evaluating multiple 8mm LRAs, nearly all had resonance frequencies above 235 Hz (outside DRV2603 tracking range). Switching to 10mm LRA was chosen over the DRV2604L (wider range but significantly higher IC cost). 8mm and 10mm LRAs are similarly priced, making motor substitution the economical choice.

**Alternative:** The DRV2604L supports 45-300 Hz resonance tracking but costs significantly more. Only consider if 8mm form factor is absolutely required.

**PCB Revision Notes (December 2025):**

Recent hardware improvements to v0.663399-T:

1. **Current Sense Shunt - Kelvin Connection:** The MAX9938 current sense topology now uses proper 4-wire (Kelvin) sensing with matched-length traces from shunt to sense amplifier. This eliminates voltage drop errors from current-carrying PCB traces.

2. **DRV2603 PWM Series Resistor:** Added 22Ω series resistor on GPIO PWM output to DRV2603. Suppresses ringing from GPIO driving capacitive load. At 25kHz PWM, values up to 100Ω would work; 22Ω is conservative standard practice.

**Component Sizes:**
This revision diverges from strictly 0805 passives:
- **0603:** Several capacitors in current sense topology + battery sense filter cap
- **0402:** Shunt resistor for MAX9938 current sense

Assembly complexity increases slightly, but smaller components are localized to the current sense area.

**Optional Components:**
- **MAX9938 + shunt R:** Can be omitted entirely; solder-blob the shunt pads if skipping
- **Battery sense filter cap (0603):** Optional - current v0.663399ADS production runs without a low-pass filter cap and ADC works fine

**Motor/Speaker Connector:**
The motor connector is now 4-pin, combining motor and speaker outputs. The existing enclosure (v0.663399u) has 3 overlapping 10mm circles in the bottom designed for the motor - this accommodates a small speaker, though audio quality will be modest (adequate for tones/feedback, not music playback). Finding speakers that fit the 10mm constraint is challenging but several candidates identified.

**Battery Sense Redesign:**
The battery monitoring circuit no longer requires a dedicated enable GPIO. Instead, a self-latching voltage divider design is used - the ADC pin is driven HIGH or LOW to control the measurement. This frees up GPIO21 compared to v0.663399ADS.

**3.3V Addressable RGB:**
The Dialight 587-2056-147F was specifically chosen because it is rated for 3.3V operation, unlike the WS2812B which is nominally 5V (and required level shifting or tolerance of out-of-spec operation).

**GPIO Utilization:**
This revision uses **all available GPIO** broken out on the Seeed XIAO ESP32-C6. No spare pins remain for future expansion on this form factor.

**Board Size:**
The PCB is slightly larger near the MCU module area to accommodate a continuous ground strip across all board edges, improving EMI performance and ground return paths.

### v0.663399ADS (MOSFET H-bridge) - Production Ready

The current production hardware uses discrete MOSFET H-bridge topology. This is the version to build if you want working hardware today.

**Archive:** The complete MOSFET H-bridge design is preserved in `pcb/MLE_HAPTICS_PULSER_MOSFET_H_BRIDGE.7z`

## Hardware/Firmware Compatibility

### v0.663399ADS (MOSFET H-bridge) - ✅ Fully Compatible

Firmware is fully updated for v0.663399ADS hardware. GPIO crosstalk fixes are implemented:
- H-bridge IN1 (forward) on GPIO18 (moved from GPIO20)
- H-bridge IN2 (reverse) on GPIO19
- Button directly connected to GPIO1 (no jumper wire required)

```c
// Current GPIO definitions (v0.663399ADS)
#define GPIO_BUTTON      1  // Direct connection
#define GPIO_M_IN2      19  // H-bridge reverse
#define GPIO_M_IN1      18  // H-bridge forward
```

### v0.663399-T (Dedicated IC) - ⏳ Firmware Pending

The dedicated IC hardware uses different components requiring new firmware:
- DRV2603 haptic driver (I2C or analog control - TBD)
- MAX98357A audio amp (I2S interface)
- Dialight addressable RGB (different protocol than WS2812B)
- MAX9938 current sense (analog input)

GPIO mapping for v0.663399-T will be documented once firmware development begins.

## Repository Structure

```
hardware/
├── pcb/                                    # KiCad PCB project
│   ├── MLE_HAPTICS_PULSER.kicad_pro       # KiCad project file
│   ├── MLE_HAPTICS_PULSER.kicad_sch       # Schematic (v0.663399-T dedicated IC)
│   ├── MLE_HAPTICS_PULSER.kicad_pcb       # PCB layout (v0.663399-T dedicated IC)
│   ├── MLE_HAPTICS_PULSER_MOSFET_H_BRIDGE.7z  # Archive of v0.663399ADS design
│   ├── libraries/                          # Custom KiCad libraries
│   │   ├── mlehaptics_library/            # Project symbols and footprints
│   │   └── 3dmodels/                      # 3D models for components
│   ├── production/
│   │   ├── gerbers/
│   │   │   ├── gerbers-v.663399-T.zip     # v0.663399-T (dedicated IC) - IN DEVELOPMENT
│   │   │   └── gerbers-v.663399ADS.zip    # v0.663399ADS (MOSFET) - PRODUCTION
│   │   └── schematic/
│   │       ├── MLE_HAPTICS_PULSER_663399-T.pdf              # Dedicated IC schematic
│   │       └── MLE_HAPTICS_PULSER_MOSFET_H_BRIDGE_663399ADS.pdf  # MOSFET schematic
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
│   ├── esp32-c6_datasheet_en.pdf          # MCU
│   ├── XIAO-ESP32-C6_v1.0_SCH_PDF_24028.pdf  # Dev board schematic
│   ├── WS2812B.pdf                         # RGB LED (v0.663399ADS)
│   ├── drv2603.pdf                         # Haptic driver IC (v0.663399-T)
│   ├── max9938.pdf                         # Current sense amp (v0.663399-T)
│   ├── max98357a-max98357b.pdf             # Audio amp (v0.663399-T)
│   ├── Dialight_datasheet_587-2056-147F_Addressable_RGB.pdf  # RGB LED (v0.663399-T)
│   ├── JYLRA0825Z.pdf                      # ERM motor option
│   └── PYU-RL_GROUP_521_ROHS_L.pdf         # ERM motor option
│
└── docs/                                   # KiCad library source files
    ├── DRV2603RUNR.zip                     # DRV2603 KiCad library
    ├── MAX9938TEUK_T.zip                   # MAX9938 KiCad library
    ├── MAX98357AETE_T.zip                  # MAX98357A KiCad library
    ├── LIB_587-2056-147F.zip               # Dialight RGB KiCad library
    └── OPL_Kicad_Library.zip               # Open Parts Library
```

## Quick Start for Builders

### Choose Your Version

**Building today? Use v0.663399ADS** (MOSFET H-bridge)
- Firmware ready, fully tested
- Production gerbers: `gerbers-v.663399ADS.zip`
- Schematic: `MLE_HAPTICS_PULSER_MOSFET_H_BRIDGE_663399ADS.pdf`

**Experimenting with new ICs? Use v0.663399-T** (Dedicated IC)
- Hardware ready, firmware pending
- Development gerbers: `gerbers-v.663399-T.zip`
- Schematic: `MLE_HAPTICS_PULSER_663399-T.pdf`

### PCB Manufacturing

**For production builds (recommended):**
1. **Download gerbers:** `pcb/production/gerbers/gerbers-v.663399ADS.zip` (MOSFET H-bridge)
2. **Upload to fab house:** JLCPCB, PCBWay, OSH Park, etc.
3. **Recommended specs:**
   - 2-layer PCB
   - 1.6mm thickness
   - HASL or ENIG finish
   - Any color (black recommended for aesthetics)

**For development builds (dedicated IC - firmware not ready):**
1. **Download gerbers:** `pcb/production/gerbers/gerbers-v.663399-T.zip`
2. **Note:** Firmware support for DRV2603 not yet implemented

### Component Sourcing

**Bill of Materials (BOM):** See main repository `/docs/` for complete parts list

### Battery Specification

The enclosure is designed for two EEMB LP402535 LiPo batteries wired in parallel (1S2P configuration).

**Reference Battery:** [EEMB LP402535 320mAh 3.7V](https://www.amazon.com/dp/B08HD1N273)

| Specification | Value |
|---------------|-------|
| Model | LP402535 (4.0mm × 25mm × 35mm naming convention) |
| Voltage | 3.7V nominal |
| Capacity | 320mAh typical (300mAh minimum) |
| **Dimensions** | **25.5 × 36 × 4.3mm** (W × L × H) |
| Weight | ~6g per cell |
| Connector | Molex-style 2-pin (⚠️ verify polarity!) |
| Protection | PCM with overcharge/overdischarge/overcurrent/short circuit |
| Certifications | UN 38.3, IEC, UL |

**Configuration:** Two cells in parallel (1S2P)
- Combined capacity: 640mAh
- Voltage: 3.7V (unchanged - parallel connection)
- Fits in enclosure battery compartment

**Substitution Guidelines:**

If sourcing alternative batteries, match these critical dimensions:
- **Thickness:** ≤4.5mm (enclosure clearance)
- **Width:** ~25mm (battery slot width)
- **Length:** ~35mm (battery slot length)

Batteries with similar "402535" or "402530" designations should fit. Always verify polarity before connecting - LiPo connector polarity is NOT standardized.

**Key Components (v0.663399ADS - MOSFET H-bridge):**
- Seeed XIAO ESP32-C6 development board
- ERM vibration motors (φ10mm × 3mm)
- WS2812B RGB LEDs (optional - for therapy light feature)
- H-bridge MOSFETs (AO3400A/AO3401A family)
- Dual EEMB LP402535 320mAh LiPo batteries (640mAh combined)
- Passive components (resistors, capacitors)

**Key Components (v0.663399-T - Dedicated IC):**
- Seeed XIAO ESP32-C6 development board
- **10mm LRA motor** (resonance 150-200 Hz for DRV2603 compatibility - see note above)
- **E-Switch TL1105 (65gf)** - Soft-touch tactile switch (see note below)
- DRV2603 haptic driver IC (Texas Instruments)
- MAX9938 current sense amplifier (Analog Devices)
- MAX98357A I2S audio amplifier (Analog Devices)
- Dialight 587-2056-147F addressable RGB LED
- Dual EEMB LP402535 320mAh LiPo batteries (640mAh combined)
- Passive components (resistors, capacitors, 22Ω series R for PWM)

**Button Selection Note:**
The E-Switch TL1105 with 65gf actuation force was chosen over standard SMT 6×6×5mm tact switches (typically 160-260gf) for user comfort during therapy sessions. The soft-touch feel reduces finger fatigue and provides a gentler, less jarring interaction appropriate for therapeutic use. The metal dome mechanism produces a subtle tactile "tick" rather than a loud click. Higher BOM cost accepted for improved user experience.

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

Simplified variant that removes access holes for clean, diffused light transmission:
- **No Reset/Boot pin access:** Pinholes removed (cleaner appearance, no programming access)
- **No indicator LED holes:** Prevents focused LED hotspots through case:
  - Red battery charge status LED (hardware-controlled) - visible as diffused glow through translucent material
  - Amber GPIO15 user LED (firmware status indicator) - visible as diffused glow through translucent material
  - **Result with clear/translucent materials:** Clean, uniform illumination without bright hotspots

**Use CLRMOD bodyTop when:**
- **Printing with clear SLA resin or translucent materials** - provides diffused LED visibility without focused hotspots
- Building production/end-user devices where Reset/Boot access not needed
- Want WS2812B therapy light to illuminate entire case uniformly
- Prioritizing clean aesthetics over direct indicator LED visibility
- Device will be programmed and tested before final case assembly
- Creating a professional, finished product with diffused lighting effect

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
GPIO18: H-bridge IN1 (motor forward control) ← MOVED FROM GPIO20
GPIO19: H-bridge IN2 (motor reverse control) - UNCHANGED
GPIO21: Battery monitor enable (P-MOSFET gate control)

Hardware LEDs (not GPIO-controlled):
- Red LED: Battery charging status (hardware-controlled by charge IC)
- Amber LED: Connected to GPIO15 (firmware-controlled user status indicator)
```

**Key Change from Previous Hardware:**
- ✅ **GPIO20 → GPIO18** for H-bridge IN1 forward (fixes ESP32-C6 GPIO19/GPIO20 crosstalk)
- ✅ **Button on GPIO1** directly (no jumper wire required)

### Enclosure Features
- **Form factor:** Designed for Seeed XIAO ESP32-C6
- **Battery compartment:** Fits dual 320mAh LiPo batteries (640mAh)
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
- H-bridge IN1 (forward) relocated from GPIO20 → GPIO18
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

✅ **All firmware updated (December 2025):** GPIO definitions in `/test` and `/src` directories now match v0.663399ADS hardware. No manual updates required for production builds.

## Other Considerations

- **Battery life:** Current design targets 20+ minute sessions; power optimization ongoing
- **Component sourcing (v0.663399ADS):** Some MOSFETs have long lead times; check availability
- **Component sourcing (v0.663399-T):** DRV2603, MAX9938, MAX98357A available from major distributors (Mouser, DigiKey)

## License

Hardware licensed under **CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S v2)**

This is a copyleft license for hardware designs. Any modifications or derivative works must be released under the same license terms.

Full license text: [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt)

## Datasheets

Key component datasheets are included in `datasheets/` directory:

**Common to both versions:**
- **ESP32-C6:** Complete MCU specifications
- **XIAO ESP32-C6:** Module schematic and pinout
- **JYLRA0825Z / PYU-RL:** ERM motor options

**v0.663399ADS (MOSFET H-bridge):**
- **WS2812B:** RGB LED timing and control

**v0.663399-T (Dedicated IC):**
- **DRV2603:** Texas Instruments haptic driver
- **MAX9938:** Analog Devices current sense amplifier
- **MAX98357A:** Analog Devices I2S audio amplifier
- **Dialight 587-2056-147F:** Addressable RGB LED
- **SPKM.10.8.A / AS01008MR-3:** Small speaker candidates for audio output

Additional datasheets (passives) available from component manufacturers.

## Development Status

### v0.663399ADS (MOSFET H-bridge) - Production Ready
✅ PCB designed with GPIO crosstalk fixes
✅ Enclosure v0.663399u validated with hardware
✅ Discrete MOSFET H-bridge functional
✅ Button directly connected to GPIO1 (no jumper)
✅ H-bridge on GPIO18/GPIO19 (crosstalk resolved)
✅ Standard and CLRMOD case variants available
✅ Firmware fully functional

### v0.663399-T (Dedicated IC) - In Development
✅ Schematic complete
✅ PCB layout complete
✅ Gerbers generated
✅ KiCad libraries created (DRV2603, MAX9938, MAX98357A, Dialight RGB)
⏳ Awaiting PCB fabrication
⏳ Firmware adaptation needed (DRV2603 driver, I2S audio, new GPIO mapping)

### Firmware Development Status
✅ Single-device operation with 5 modes
✅ BLE GATT server operational
✅ v0.663399ADS GPIO definitions updated
🔄 Dual-device bilateral pairing protocol in development
⏳ v0.663399-T dedicated IC firmware TBD

### Hardware Roadmap

**v1.0 Target: v0.663399-T (Tri-Modal)**
- Validates dedicated IC approach with existing enclosure (v0.663399u)
- Uses current 3D printed case design - no mechanical changes
- Focus: firmware development for DRV2603, I2S audio, new RGB protocol

**v2.0 (Future):**
- Improved battery supply options
- New enclosure design required
- Scope TBD based on v1.0 learnings

### Future Work
- [ ] DRV2603 driver implementation for v0.663399-T
- [ ] I2S audio feedback (MAX98357A) for v0.663399-T
- [ ] ERM vs LRA actuator comparative research
- [ ] Enhanced power management

## Assembly Instructions

**Coming Soon:** Detailed assembly guide will be added to `docs/` directory

**Prerequisites:**
- Soldering iron and basic SMD soldering skills
- Multimeter for continuity and voltage testing
- 3D printer or 3D printing service access

**Estimated build time:** 2-3 hours for experienced builders

**Version Notes:**
- **v0.663399ADS:** Firmware ready, build and flash immediately
- **v0.663399-T:** Firmware in development, hardware can be built but not yet functional

## Contributing

See main repository [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**In brief:** Bug reports and suggestions via GitHub issues are welcome. I prefer to implement changes myself to ensure hands-on hardware testing. Forks are encouraged!

**Areas where feedback is especially helpful:**
- PCB layout issues or improvements
- Alternative enclosure designs (different form factors, materials)
- Bill of materials cost reduction ideas
- ERM vs LRA motor evaluation experiences with DRV2603

## Questions or Issues?

Open a GitHub issue in the main repository with the `hardware` label.

---

**This hardware is part of the MLE Haptics open-source EMDR bilateral stimulation device project.**  
**For firmware, documentation, and project overview, see main repository.**
