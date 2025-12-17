# **Advanced Architectural Analysis and Optimization of Bilateral Pattern Playback Systems for ESP32-Based EMDR Therapeutics**

## **1\. Introduction: The Convergence of Real-Time Control and Therapeutic Efficacy**

The evolution of Eye Movement Desensitization and Reprocessing (EMDR) hardware is currently undergoing a paradigm shift, moving away from simple, discrete logic circuits toward sophisticated, connected embedded systems. The efficacy of EMDR therapy is fundamentally predicated on the precision, consistency, and "organic" quality of the bilateral stimulation (BLS)—the alternating left-right sensory inputs that facilitate the processing of traumatic memory. As these devices integrate into the broader Internet of Medical Things (IoMT) ecosystem, they face a unique set of engineering challenges: they must maintain the deterministic timing of a hard real-time system while managing the non-deterministic latencies associated with wireless communication and file system operations.

The proposed "Bilateral Pattern Playback" architecture, targeting the Espressif ESP32 microcontroller series, represents a significant technological leap. The ESP32’s dual-core architecture (in Xtensa-based variants like the S3) or efficient RISC-V structure (in C3/C6 variants) provides a robust platform for decoupling network stack operations from real-time actuator control. However, the transition from a theoretical architectural proposal to a deployment-ready firmware ecosystem demands a rigorous technical audit. This report provides an exhaustive analysis of the proposed system, referencing established industrial standards such as DMX-512 for stage lighting and SAE J1939 for automotive control to benchmark performance, reliability, and scalability.

This analysis prioritizes three core pillars: **Synchronization Integrity**, ensuring that visual, auditory, and haptic modalities remain perfectly aligned; **Data Persistence Reliability**, guaranteeing that user-defined therapeutic patterns are stored without corruption or excessive flash wear; and **Communication Efficiency**, optimizing Bluetooth Low Energy (BLE) throughput to allow for seamless pattern updates. By dissecting the "Zone vs. Role" models utilized in modern automotive architectures and applying them to the bilateral paradigm, we establish a framework that decouples logical identity from physical actuation. Furthermore, the report deeply investigates the "loop boundary" problem—a classic issue in sequencer design where cyclic patterns suffer from timing drift or truncated events at the wrap-around point—and proposes algorithmic solutions rooted in MIDI sequencer logic and game engine render loops.

## **2\. Architectural Paradigms: Zone Control versus Role-Based Logic**

In designing distributed embedded systems, particularly those involving distinct physical actuators like the left and right stimulators in an EMDR device, the fundamental organization of the control logic dictates the system's scalability, wiring complexity, and synchronization latency. The industry is currently witnessing a transition from function-based "Domain" architectures to location-based "Zone" architectures, a shift that holds profound implications for bilateral device design.

### **2.1 The Limitations of Domain-Based Architectures**

Historically, embedded systems in automotive and industrial contexts utilized domain-based architectures. In this model, Electronic Control Units (ECUs) are organized by function. For a bilateral EMDR device, a domain architecture would imply a single "Haptic Controller" managing both left and right motors, and a separate "Visual Controller" managing left and right LEDs. While this simplifies the functional logic within each firmware module—the motor code only thinks about motors—it creates significant integration challenges at the system level.

The primary deficit of the domain model in a bilateral context is the introduction of cross-domain latency. To trigger a simultaneous "Left Side Stimulus" consisting of a vibration and a light pulse, the central sequencer must dispatch synchronized messages to two different functional blocks. If the Haptic Controller is servicing a high-priority interrupt while the Visual Controller is idle, the tactile stimulus may lag behind the visual stimulus. In therapeutic contexts, this "sensory jitter" can be disorienting for the patient, potentially breaking the cognitive state required for effective processing. Furthermore, as noted in automotive architectural studies, domain-based systems suffer from complex wiring harnesses, as cables must run from central functional controllers to every endpoint, resulting in heavy and expensive cable bundles.1

### **2.2 The Zone Control Model: Physical Aggregation**

The Zone Control model, which is becoming the standard in modern vehicle design (e.g., Tesla, new EV platforms), organizes components by their physical location rather than their function. In the context of a bilateral EMDR device, this translates to a "Left Zone" and a "Right Zone." A single microcontroller (or a distinct thread/task within the ESP32) manages *all* functions—light, sound, and vibration—for that specific physical side.

The advantages of the Zone Architecture for EMDR are manifold:

* **Synchronization Integrity:** By grouping the haptic and visual actuators of the "Left Zone" under a single local control loop, the latency between seeing the light and feeling the vibration is effectively zeroed. They share the same local clock source and driver interrupts. The "Left Zone" receives a single command—"Activate Stimulus"—and executes the multi-modal feedback simultaneously.  
* **Scalability and Modularity:** Adding a new modality, such as thermal feedback or bio-sensing, to the Left Zone does not require a system-wide re-architecture. It merely requires updating the Zone Controller's capability list. The central sequencer remains agnostic to the specific hardware implementation of the zone.  
* **Simplified Message Passing:** The central sequencer needs only to broadcast a "Left Zone Active" command, rather than coordinating separate messages to a Motor Controller, an LED Controller, and an Audio Controller. This reduces bus traffic and CPU overhead.1

### **2.3 The Role-Based Logical Abstraction**

While the physical architecture should be Zone-based to optimize wiring and sync, the logical architecture must use Role-based addressing to maintain software flexibility. A "Role" defines the behavior (e.g., "Stimulator A," "Stimulator B," "Active," "Passive") independent of its physical connection. This decoupling of identity from function is a critical design pattern in distributed systems, often referred to as the Decoupling Principle.2

In practice, this means the firmware should never hardcode references to GPIO\_LEFT or GPIO\_RIGHT in the sequencing logic. Instead, the system should implement a Logical Addressing layer. The sequencer outputs commands to LOGICAL\_ROLE\_PRIMARY. A translation layer, functioning similarly to a Memory Management Unit (MMU) in an operating system, resolves LOGICAL\_ROLE\_PRIMARY to a physical zone at runtime.4

This abstraction enables dynamic remapping essential for user-centric features. For instance, if a user prefers to hold the "Left" tapper in their right hand due to cable routing or comfort, a simple software toggle can swap the logical roles without altering the underlying zone management or pattern data. The pattern data remains pure and portable, describing *behavior* rather than *hardware*.6

### **2.4 Logical vs. Physical Addressing in Distributed Systems**

The concept of separating logical and physical addresses is well-established in operating system theory but is equally applicable to this distributed control topology. In an OS, a logical address is generated by the CPU during execution, while the physical address corresponds to the actual location in the memory unit.7 In the bilateral device architecture, the "Physical Address" corresponds to the hardware interface (e.g., I2C\_ADDR\_0x40, BLE\_MAC\_C4:5B:22, or PWM\_CHANNEL\_0). The "Logical Address" corresponds to the therapeutic target (e.g., SIDE\_A or STIMULUS\_SOURCE).

Implementing a "Hardware Abstraction Layer" (HAL) that performs this translation allows the same pattern playback engine to drive internal GPIOs on a standalone device, external I2C expanders on a complex wired setup, or remote BLE peripherals on a fully wireless system. This aligns with the "Location Transparent Process Addressing" found in distributed computing, where a process sends a message to a logical name, and a name server maps it to the current physical location.8

**Table 1: Comparative Analysis of Architecture Models for Bilateral Stimulation**

| Feature | Domain Architecture | Zone Architecture (Recommended) | Role-Based Logical Overlay |
| :---- | :---- | :---- | :---- |
| **Primary Organization** | Function (Motor vs. LED) | Location (Left vs. Right) | Behavior (Stimulus vs. Rest) |
| **Synchronization** | Difficult (Cross-domain latency) | Excellent (Shared local clock) | Abstracted (Managed by sequencer) |
| **Wiring Complexity** | High (Function-specific routing) | Low (Local hubs/Zones) | N/A (Software layer) |
| **Scalability** | Low (Requires new controllers) | High (Modular zones) | High (Dynamic assignment) |
| **Fault Tolerance** | Single point of failure per function | Isolated zone failures | Dynamic role reassignment |
| **Data Coupling** | Tight coupling to hardware type | Tight coupling to location | Decoupled identity 2 |

## **3\. Data Structure Optimization for ESP32 Architectures**

The efficiency of the playback engine relies heavily on how pattern data is structured in memory. The ESP32 ecosystem involves both Xtensa (ESP32-S3) and RISC-V (ESP32-C3/C6) architectures. Differences in memory alignment handling between these architectures dictate strict best practices to avoid performance penalties, code bloat, and runtime exceptions.

### **3.1 Struct Alignment and The Padding Penalty**

Compilers for 32-bit architectures, including the Xtensa and RISC-V cores found in ESP32 modules, naturally align data to 4-byte boundaries (words) to optimize memory fetch cycles. If a C struct contains a mix of types with different sizes—such as uint8\_t (1 byte), uint16\_t (2 bytes), and uint32\_t (4 bytes)—the compiler injects invisible "padding bytes" to ensure that the larger types align with addresses divisible by their size.9

Consider a naive pattern step definition often found in initial prototypes:

C

struct NaiveStep {  
    uint8\_t type;       // 1 byte  
    uint32\_t duration;  // 4 bytes  
    uint8\_t intensity;  // 1 byte  
};

In a standard 32-bit environment, the compiler will likely pad this structure to 12 bytes.

1. type occupies byte 0\.  
2. Bytes 1, 2, and 3 become padding to ensure duration starts at byte 4\.  
3. duration occupies bytes 4-7.  
4. intensity occupies byte 8\.  
5. Bytes 9, 10, and 11 become padding to ensure the *next* struct in an array starts at a 4-byte aligned address.

This results in a 50% memory waste (6 bytes of actual data, 6 bytes of padding). For an EMDR device potentially storing sequences with thousands of steps, this bloat directly reduces the effective storage capacity of the NVS or filesystem. Furthermore, transmitting padded structures over BLE consumes valuable airtime and energy, transmitting noise rather than signal.

### **3.2 The \_\_attribute\_\_((packed)) Dilemma**

A common "quick fix" is to use the \_\_attribute\_\_((packed)) directive, which forces the compiler to eliminate all padding.

C

struct \_\_attribute\_\_((packed)) PackedStep {  
    uint8\_t type;  
    uint32\_t duration;  
    uint8\_t intensity;  
};

While this reduces the size to 6 bytes, it introduces significant performance risks. On RISC-V and Xtensa architectures, accessing unaligned 32-bit integers (like duration starting at byte offset 1\) is not a single bus operation. The processor must perform two memory fetches (loading two adjacent words) and then use bitwise shifts and masks to reconstruct the value.10

The compiler generates significantly more assembly code to handle these unaligned accesses, leading to "code bloat" that negates the data size savings. In some strict configurations or specific RISC-V implementations, unaligned access can even trigger a processor trap or bus error, causing the device to crash.11 As noted in discussions regarding ESP32 struct packing, this approach forces the compiler to generate byte-wise access instructions, which are significantly slower than word-aligned loads.10

### **3.3 Optimized Member Ordering: The Best Practice**

The optimal strategy for the Bilateral Pattern Playback architecture is **manual alignment through member reordering**. By placing struct members in descending order of size (largest types first), we can satisfy alignment requirements without padding and without the performance penalties of packing.11

**Recommended Struct Architecture:**

C

typedef struct {  
    uint32\_t duration\_ms; // 4 bytes, aligned at offset 0  
    uint16\_t intensity;   // 2 bytes, aligned at offset 4  
    uint16\_t fade\_ms;     // 2 bytes, aligned at offset 6  
    uint8\_t  led\_red;     // 1 byte, aligned at offset 8  
    uint8\_t  led\_green;   // 1 byte, aligned at offset 9  
    uint8\_t  led\_blue;    // 1 byte, aligned at offset 10  
    uint8\_t  motor\_id;    // 1 byte, aligned at offset 11  
} BilateralStep;          // Total: 12 bytes. Naturally aligned.

This structure is naturally aligned. It requires no packed attribute, performs optimally on the CPU (single-cycle fetches for all multi-byte members), and transfers reliably over BLE or to NVS without hidden padding bytes corruption. The size is exactly 12 bytes, which is also convenient for block-based reads.

### **3.4 Variable-Length Data and the Index-Lookup Model**

Advanced EMDR patterns may require variable-length data, such as complex custom waveforms for LED breathing effects or haptic envelopes. Storing variable-length blobs directly in the pattern sequence is inefficient for ESP-IDF's NVS system, which prefers fixed-size entries.12 Writing large variable-length blobs can lead to heap exhaustion during serialization and rapid flash wear due to the need to move large pages of data.13

To address this, the architecture should employ an **Index-Lookup Model**:

1. **Step Struct:** The BilateralStep struct contains a uint8\_t waveform\_id rather than the waveform data itself.  
2. **Waveform Table:** A separate, static lookup table (stored in flash/RODATA) or a distinct file in the file system contains the heavy interpolation data (e.g., 256-byte gamma curves).

This approach keeps the sequence data lightweight and iterable. The sequencer simply references waveform\_id: 5 to retrieve the "Sine Wave" lookup table, rather than carrying 256 bytes of sine wave data in every step of the sequence. This decoupling aligns with the Separation of Concerns principle, ensuring that the "Sequence" data structure manages timing and flow, while the "Waveform" data structure manages signal fidelity.6

## **4\. State Persistence and Pattern Ingestion Strategy**

The system architecture adopts a strict "Separation of Persistence" model. To maximize flash longevity and simplify state management, the device differentiates between *System Settings*, which are persistent but rarely written, and *Unique Patterns*, which are volatile and managed externally by the Progressive Web App (PWA).

### **4.1 NVS Strategy: The "Save-on-Shutdown" Protocol**

The Non-Volatile Storage (NVS) partition is reserved strictly for system-critical configuration state that must survive a power cycle. To eliminate flash wear from repetitive writes during therapy sessions, NVS write operations are restricted to a single event: **Device Shutdown**.

* **Atomic State Commit:** During active operation, changes to intensity, mode selection, or brightness are held in RAM. When the user initiates a shutdown (via button hold) or a low-battery supervisory circuit triggers, the system executes a save\_context() routine.  
* **Wear Leveling:** Although ESP32 NVS implements internal wear leveling, restricting writes to shutdown events drastically reduces the erase cycles. Even with daily use, this strategy extends the theoretical flash lifespan to decades.13  
* **Saved Parameters:** The NVS blob should be minimal, containing only:  
  * last\_mode\_index (uint8\_t)  
  * global\_intensity (uint8\_t)  
  * led\_brightness (uint8\_t)  
  * paired\_device\_mac (uint8\_t6)  
    This ensures that when the user turns the device back on, it resumes exactly where they left off, preserving the continuity of the therapeutic experience.

### **4.2 Ephemeral Pattern Management (RAM & BLE)**

In this architecture, "Unique Patterns" (complex, custom sequences created in the PWA) are **not** stored in the device's persistent flash memory. The PWA acts as the library and "Source of Truth," while the device acts as a playback engine.

* **Ingestion over Persistence:** When a user selects a custom pattern in the PWA, it is serialized and transmitted to the device via BLE immediately. The device does not "install" this pattern; it loads it directly into a volatile **Active Pattern Buffer** in RAM.  
* **RAM Utilization:** The ESP32-C6/S3 has ample RAM to store even complex bilateral patterns. A 500-step pattern (approx. 5 minutes of unique non-looping variation) consumes only \~6KB of RAM using the optimized struct defined in Section 3.3. This eliminates the complexity and latency of writing to a filesystem (LittleFS) before playback can begin.  
* **State Volatility:** If the device is powered down, the custom pattern is lost from RAM. On reboot, the device reverts to a default onboard pattern (e.g., Mode 0: Standard Alternation) until the PWA reconnects and reloads a custom sequence. This "Stateless Pattern" approach prevents memory fragmentation and simplifies firmware updates, as there is no legacy pattern database to migrate.

### **4.3 Handling Large Data Transfer via BLE**

Since unique patterns are loaded dynamically, the BLE transport layer becomes the critical path for user experience. A "loading" delay of more than 1-2 seconds is unacceptable.

* **Throughput Optimization:** To transfer pattern buffers quickly, the firmware must negotiate a high-throughput BLE connection. This involves requesting a connection interval of \~15ms and an MTU (Maximum Transmission Unit) of 512 bytes (up from the default 23 bytes). This allows the PWA to burst transfer the pattern data in large chunks.  
* **Concurrency Protection (Mutex):** Writing to the Active Pattern Buffer while the playback engine is reading from it invites race conditions. A FreeRTOS Mutex (xSemaphoreCreateMutex) must protect the buffer.  
  * **Playback Task:** Takes the Mutex, reads the next step, releases Mutex.  
  * **BLE Write Task:** Takes the Mutex, overwrites the buffer with new pattern data, releases Mutex.  
  * *Note:* If the buffer update is atomic (replacing the whole pattern), the Playback Task should pause or reset to the start of the new pattern immediately upon Mutex release.

## **5\. BLE Pattern Distribution and Connectivity Optimization**

Transferring complex, user-defined patterns from a mobile application to the ESP32 over Bluetooth Low Energy (BLE) presents specific throughput challenges due to the protocol's inherent packet size limitations and connection intervals.

### **5.1 MTU Fragmentation and Reassembly**

The default BLE Maximum Transmission Unit (MTU) is 23 bytes. After the 3-byte ATT header, only 20 bytes of payload remain. Sending a 4KB pattern file in 20-byte chunks is incredibly inefficient due to the overhead of headers and the inter-packet delays.14

* **MTU Negotiation:** The ESP32 BLE stack supports an MTU up to 517 bytes.14 The firmware must explicitly handle the ESP\_GATTS\_MTU\_EVT and request/accept a larger MTU (e.g., 512 bytes) upon connection. While Android devices typically accept high MTUs, iOS devices often cap the MTU at around 185 bytes and do not allow the app to force a higher value.16 The firmware must be adaptive, dynamically sizing its reception buffers based on the negotiated MTU.  
* **Fragmentation Logic:** Even with a 512-byte MTU, larger patterns will require fragmentation. The application layer must handle this reassembly. Rather than using the complex "Long Write" characteristic (which has overhead), a custom application-layer framing protocol is often more efficient. This involves a header in the first packet describing the total size, followed by sequential chunks.

### **5.2 Throughput Optimization Strategies**

To maximize transfer speed and minimize the user's wait time during pattern sync:

1. **Connection Interval Tuning:** The connection interval—the frequency at which the radio wakes up to exchange data—drastically affects throughput. The default interval can be as high as 100ms. The ESP32 firmware should request a lower connection interval (e.g., min=15ms, max=30ms) during the data transfer phase. This allows many more packets to be exchanged per second.14  
2. **Write Without Response:** Using standard "Write Request" (BLE\_GATT\_OP\_WRITE\_REQ) requires the client (phone) to wait for an acknowledgment (ACK) from the server (ESP32) for every single packet. This round-trip latency kills throughput. The optimized approach is to use "Write Without Response" (BLE\_GATT\_OP\_WRITE\_CMD), which allows the phone to stream packets continuously, filling the link layer buffer.15  
3. **Flow Control:** Since "Write Without Response" provides no application-level confirmation, a packet could be dropped. To mitigate this without reverting to slow ACKs, implement a "Block Acknowledgement." The phone sends a block of packets (e.g., 4KB), then pauses and sends a "Check Block" command. The ESP32 verifies the checksum of the received block and sends a single ACK. If the checksum fails, the phone resends the specific block.17

### **5.3 Over-The-Air (OTA) Considerations**

While WiFi is preferred for firmware updates due to speed, BLE OTA is a viable fallback for the ESP32. However, it is slow (10-70 kB/s).14 If BLE OTA is implemented, it is crucial to use a dedicated service with large internal buffers to prevent RX buffer overflows on the ESP32 side, as the flash writing process (which blocks the CPU) can cause the BLE stack to drop incoming packets if flow control is not managed correctly.18 The architecture should prioritize pattern data transfer over BLE and reserve full firmware OTA for WiFi or USB where possible.19

## **6\. Sequencer Logic: Loop Boundaries and Timing Drift**

The heart of the EMDR device is the sequencer. A common flaw in embedded sequencers is "loop jitter" or "note truncation" at the wrap-around point of a repeating pattern. This section details the algorithmic solutions to these temporal challenges.

### **6.1 The "Note-Off" Paradox at Loop Boundaries**

In MIDI sequencing and music production, a critical edge case occurs when a "Note-On" event happens near the end of a loop, and the corresponding "Note-Off" event technically falls in the *next* loop iteration.

* **The Problem:** If a pattern is 1000ms long, and a haptic pulse starts at 900ms with a duration of 200ms, the "Stop Motor" command should occur at timestamp 1100ms. However, if the sequencer simply resets its tick counter to 0 at 1000ms, the timestamp 1100ms is never reached. The "Stop Motor" command is lost, and the motor vibrates indefinitely—a failure mode known as a "hanging note".20  
* The Solution: Phantom Buffering and Look-Ahead:  
  The sequencer logic must not treat the loop end as a hard wall. We propose a Look-Ahead Ring Buffer.  
  1. **Scheduled Event Queue:** The playback engine should parse the static pattern data and push "Events" (e.g., ACTION\_MOTOR\_ON, ACTION\_LED\_OFF) into a dynamic priority queue. This queue decouples "Pattern Time" from "Real Time".22  
  2. **Wrapping Logic:** When the parser reads an event that exceeds the Pattern\_Length, it does not discard it. It wraps the timestamp using modulo arithmetic: Event\_Time \= Event\_Time % Pattern\_Length. Crucially, it flags this event as belonging to the *next* iteration.  
  3. **Active Voice Tracking:** The system must maintain a list of "Active Actuators." If the loop wraps while an actuator is active (e.g., motor is ON), the system must explicitly carry over the "Off" event into the new timeline. Some sequencers handle this by sending an immediate "Note Off" at the loop boundary and a new "Note On" at the start (retriggering), but for smooth haptic feedback, carrying the state over is superior to retriggering.21

### **6.2 Timing Drift and Modulus Wrapping**

Relying on simple delay() calls is fatal for rhythmic accuracy because it ignores the time taken to execute the code itself. Over hundreds of cycles, this "execution jitter" accumulates, causing the EMDR frequency to drift.

* **Drift Correction:** The sequencer must use a "Next Execution Time" model based on the system's microsecond counter (esp\_timer\_get\_time()).  
  C  
  uint64\_t next\_event\_time \= esp\_timer\_get\_time() \+ step\_duration;  
  //... execution...  
  int64\_t delay \= next\_event\_time \- esp\_timer\_get\_time();  
  if (delay \> 0) precise\_delay(delay);

  This self-corrects; if one step takes too long to process, the delay for the next step naturally shortens to catch up.  
* **Modulus Wrapping:** Hardware timers eventually roll over. A 32-bit microsecond counter wraps every \~71 minutes. To handle this, the architecture must use **Unsigned Subtraction Logic**. In C, (CurrentTime \- StartTime) \>= Duration yields the correct result even if CurrentTime has wrapped around zero, provided the variables are unsigned and the interval is less than half the maximum counter value.24 This ensures the therapy session can run indefinitely without a "hiccup" at the 71-minute mark.

## **7\. Comparative Analysis: Benchmarking against Industry Standards**

To validate the robustness of the proposed architecture, we compare it against two established standards: DMX-512 (Theatrical Lighting) and SAE J1939 (Emergency Vehicle Control).

### **7.1 Comparison with DMX-512**

DMX-512 is the standard for stage lighting. It utilizes a continuous stream of data packets sent at 250 kbps over RS-485.26

* **Stateless vs. Stateful:** DMX is stateless; the controller sends the brightness value (0-255) for every channel, 44 times per second. If the cable is cut, the lights go black (or hold the last state).  
* **Architecture Contrast:** The EMDR device cannot afford the bandwidth or power consumption of a constant stream for a simple bilateral toggle. DMX follows a "Dumb Fixture, Smart Controller" model. The EMDR device requires a **"Smart Fixture"** model (autonomous playback). The sequence must reside *on* the device so that if the Bluetooth connection drops, the therapy session continues uninterrupted.  
* **Lesson Adopted:** The DMX concept of **Fade Time** is valuable. DMX controllers don't just switch values; they calculate intermediate steps. The Bilateral architecture should implement fade\_in\_ms and fade\_out\_ms in its step struct (as defined in Section 3.3) to allow for smooth transitions, mirroring the professional fade engines of DMX consoles.28

### **7.2 Comparison with Emergency Vehicle Protocols (SAE J1939)**

Modern emergency lighting (e.g., Whelen Core, SAE J1939) uses CAN bus to synchronize flash patterns across multiple vehicles (V2V Sync).30

* **Dynamic Variable Intensity (DVI):** Emergency systems have moved away from harsh square-wave flashing. They now use "Dynamic Variable Intensity" patterns that modulate brightness organically to reduce glare and panic at night.31  
* **Relevance to EMDR:** This is directly applicable. A sharp, instant ON/OFF visual stimulus can be jarring and induce anxiety, counteracting the therapy. The EMDR device should implement **Gamma-Corrected Fading** (CIE 1931 standard) to create "organic" pulses.  
  * *Implementation:* Rather than linear PWM changes, the firmware should use a lookup table (LUT) to map linear progress (0-255) to a logarithmic PWM duty cycle. This makes the light appear to fade linearly to the human eye, providing a soothing "breathing" effect rather than a robotic blink.33  
* **Priority Arbitration:** J1939 supports message priority.34 In EMDR, a "Safety Stop" command (panic button) must have the highest priority. The software scheduler must implement a pre-emptive priority queue, where a Safety Stop event bypasses the pattern buffer and immediately drives all actuators to the OFF state.35

**Table 3: Protocol Feature Matrix Comparison**

| Feature | DMX-512 | SAE J1939 (Emergency) | Proposed Bilateral Architecture |
| :---- | :---- | :---- | :---- |
| **Topology** | Daisy-Chain (Bus) | Bus / Star | Wireless (BLE/WiFi) \+ Internal |
| **State Management** | Stateless (Stream) | Stateful (Messages) | **Stateful (Sequenced)** |
| **Timing Source** | Central Controller | Distributed / Sync | **Local (ESP32)** |
| **Transitions** | Controller-calculated | Pattern-based | **Interpolated (Gamma Corrected)** |
| **Safety Logic** | Low (Keep-alive) | High (Priority msgs) | **High (Watchdog \+ Interrupt)** |
| **Data Flow** | Continuous | Event-Driven | **Buffered Streaming** |

## **8\. Proposed Architecture: The "Bilateral Pattern Playback" Engine**

Synthesizing the research and analysis, the following refined architecture is proposed for the ESP32-based EMDR device.

### **8.1 System Layers**

1. **Hardware Abstraction Layer (HAL):** Implements the **Zone Model**. It maps Zone\_Left and Zone\_Right to physical GPIOs, PWM channels, or external drivers. This layer handles the low-level "bit-banging" and hardware timers.  
2. **Logical Layer:** Implements **Role-based addressing**. It manages the state machine for Stimulator\_Active and Stimulator\_Passive, mapping these abstract roles to the physical Zones defined in the HAL.  
3. **Playback Engine:** A high-priority FreeRTOS task running on **ESP32 Core 1** (isolating it from the WiFi/BLE stack on Core 0).  
   * **Storage:** Uses **LittleFS** to stream binary pattern files (.bin).  
   * **Buffering:** Uses a **Double-Buffer** mechanism. It loads the next 64 steps into RAM Buffer A while playing from Buffer B, ensuring zero latency during file reads.  
   * **Timing:** Uses **Unsigned Delta Timing** to prevent drift over long sessions.  
4. **Interpolation Engine:** Handles LED fading and Haptic ramping.  
   * Uses **Integer Math** (fixed point) for fading calculations to avoid Floating Point Unit (FPU) overhead inside Interrupt Service Routines (ISRs).37  
   * Implements **CIE 1931 Gamma Correction** via a pre-calculated lookup table for natural visual fading.33

### **8.2 Integration with Existing High-Precision Synchronization (PTP)**

The project has already established a robust Precision Time Protocol (PTP)-inspired synchronization mechanism that achieves ±30 microseconds accuracy. The proposed Pattern Playback Engine must integrate with this existing foundation rather than introducing a redundant protocol.

* **Epoch-Based Execution:** The Playback Engine functions as a consumer of the existing synchronized time base. It does not manage the synchronization negotiation itself. Instead, it queries the time\_sync service for the current server\_time and the agreed-upon motor\_epoch\_us (start time).  
* **Absolute Time Scheduling:** The "Conductor" task calculates the current position in the pattern by subtracting motor\_epoch\_us from now\_us.  
  C  
  // Robust sync integration  
  uint64\_t now\_us;  
  time\_sync\_get\_time(\&now\_us);  
  uint32\_t pattern\_cursor\_ms \= (now\_us \- motor\_epoch\_us) / 1000;

  This ensures that if a device momentarily disconnects or reboots, it immediately jumps to the correct frame in the pattern upon recovery, maintaining perfect phase alignment with its peer without needing to negotiate a new "start" command.  
* **Superiority over UDP/DMX:** This PTP-based approach is vastly superior to the "fire-and-forget" UDP synchronization used in WLED (which suffers from network jitter). By relying on a synchronized local clock, the playback is immune to momentary packet loss and network latency spikes, delivering the medical-grade consistency required for EMDR therapy.

### **8.3 Safety and Edge Case Handling**

* **Hardware Watchdog:** A dedicated hardware watchdog timer (WDT) must be reset only by the successful completion of a pattern playback loop iteration. If the loop hangs (e.g., due to an infinite loop in corrupted pattern data), the WDT resets the device to a safe "OFF" state.  
* **Boundary Protection:** The pattern loader must validate that fade\_time \<= duration. If a user programs a 500ms fade in a 100ms step, the firmware must clamp the fade time to maintain integrity and prevent buffer underruns.28

## **9\. Conclusion**

The transition of the EMDR device from concept to a robust embedded product requires a shift from naive implementations to structured, standardized architectures. By adopting a **Zone-based physical architecture** decoupled by a **Role-based logical layer**, the system gains the flexibility to adapt to various hardware form factors without extensive code rewrites. Data structures must be rigorously optimized for **32-bit alignment** to ensure performance and stability on the ESP32's RISC architectures. Storage strategies should rely on **LittleFS** for pattern management, strictly avoiding the pitfalls of NVS for large data blobs. Finally, by adopting the safety prioritization of **J1939** and the organic fading algorithms of **DVI/DMX**, the device can deliver a therapeutic experience that is not only functional but fluid, reliable, and safe.

### **Recommendations Summary:**

1. **Storage:** **Adopt LittleFS** for pattern storage; restrict NVS to system configuration.  
2. **Data:** **Use Aligned Binary Structs** for internal data handling; avoid JSON in critical paths.  
3. **Architecture:** **Implement Zone Architecture** for hardware abstraction and synchronization.  
4. **Connectivity:** **Optimize BLE** with 512B MTU, Write-Without-Response, and binary payloads.  
5. **Visuals:** **Use Integer-based Gamma Correction** for "organic" LED control.  
6. **Sequencing:** **Leverage Existing PTP Sync** to drive absolute-time pattern execution.

This architectural foundation provides the robustness required for a medical-grade device while maximizing the specific capabilities of the ESP32 platform.

#### **Works cited**

1. How a Zone Architecture Paves the Way to a Fully Software-Defined Vehicle \- Texas Instruments, accessed December 16, 2025, [https://www.ti.com/lit/pdf/spry345](https://www.ti.com/lit/pdf/spry345)  
2. Decentralized Identifiers (DIDs) v1.0 \- W3C, accessed December 16, 2025, [https://www.w3.org/TR/did-1.0/](https://www.w3.org/TR/did-1.0/)  
3. The Decoupling Principle:A Practical Privacy Framework, accessed December 16, 2025, [https://conferences.sigcomm.org/hotnets/2022/papers/hotnets22\_schmitt.pdf](https://conferences.sigcomm.org/hotnets/2022/papers/hotnets22_schmitt.pdf)  
4. 7.5: Logical vs Physical Address \- Engineering LibreTexts, accessed December 16, 2025, [https://eng.libretexts.org/Courses/Delta\_College/Operating\_System%3A\_The\_Basics/07%3A\_Memory/7.5%3A\_Logical\_vs\_Physical\_Address](https://eng.libretexts.org/Courses/Delta_College/Operating_System%3A_The_Basics/07%3A_Memory/7.5%3A_Logical_vs_Physical_Address)  
5. Day 16: Logical vs Physical Address Space \- Exploring Operating Systems \- Mohit Mishra, accessed December 16, 2025, [https://mohitmishra786.github.io/exploring-os/src/day-16-logical-vs-physical-address-space.html](https://mohitmishra786.github.io/exploring-os/src/day-16-logical-vs-physical-address-space.html)  
6. The Decoupling Principle For Future-Proof Data Architectures \- Awadelrahman M. A. Ahmed, accessed December 16, 2025, [https://awadrahman.medium.com/the-decoupling-principle-for-future-proof-data-architectures-9c8ace859905](https://awadrahman.medium.com/the-decoupling-principle-for-future-proof-data-architectures-9c8ace859905)  
7. Difference Between Logical and Physical Address in Operating System, accessed December 16, 2025, [https://embeddedworlddevelopers.blogspot.com/2017/04/difference-between-logical-and-physical.html](https://embeddedworlddevelopers.blogspot.com/2017/04/difference-between-logical-and-physical.html)  
8. Process Addressing in Distributed System \- GeeksforGeeks, accessed December 16, 2025, [https://www.geeksforgeeks.org/computer-networks/process-addressing-in-distributed-system/](https://www.geeksforgeeks.org/computer-networks/process-addressing-in-distributed-system/)  
9. Q1CHENL/c-alignment-cheatsheet: How alignment works in C \- GitHub, accessed December 16, 2025, [https://github.com/Q1CHENL/c-alignment-cheatsheet](https://github.com/Q1CHENL/c-alignment-cheatsheet)  
10. Why I hate \_\_attribute\_\_((packed)) \- Arduino Forum, accessed December 16, 2025, [https://forum.arduino.cc/t/why-i-hate-attribute-packed/1350854](https://forum.arduino.cc/t/why-i-hate-attribute-packed/1350854)  
11. Reorder struct members to prevent padding \- ESP32 Forum, accessed December 16, 2025, [https://esp32.com/viewtopic.php?t=36229](https://esp32.com/viewtopic.php?t=36229)  
12. esp-idf/docs/en/api-reference/storage/nvs\_flash.rst at master \- GitHub, accessed December 16, 2025, [https://github.com/espressif/esp-idf/blob/master/docs/en/api-reference/storage/nvs\_flash.rst](https://github.com/espressif/esp-idf/blob/master/docs/en/api-reference/storage/nvs_flash.rst)  
13. Non-Volatile Storage (NVS) \- \- — ESP-FAQ latest documentation, accessed December 16, 2025, [https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/storage/nvs.html](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/storage/nvs.html)  
14. Bluetooth LE & Bluetooth \- \- — ESP-FAQ latest documentation, accessed December 16, 2025, [https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/bt/ble.html](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/bt/ble.html)  
15. Maximizing BLE Throughput Part 4: Everything You Need To Know \- Punch Through, accessed December 16, 2025, [https://punchthrough.com/ble-throughput-part-4/](https://punchthrough.com/ble-throughput-part-4/)  
16. BLE notification transfer size \- ESP32 Forum, accessed December 16, 2025, [https://esp32.com/viewtopic.php?t=1989](https://esp32.com/viewtopic.php?t=1989)  
17. File Transfer using Bluetooth Classic, ESP32, SD SPI, and Android : r/arduino \- Reddit, accessed December 16, 2025, [https://www.reddit.com/r/arduino/comments/mx7x31/file\_transfer\_using\_bluetooth\_classic\_esp32\_sd/](https://www.reddit.com/r/arduino/comments/mx7x31/file_transfer_using_bluetooth_classic_esp32_sd/)  
18. ESP32 Bluetooth large data transfer issue, accessed December 16, 2025, [https://esp32.com/viewtopic.php?t=21450](https://esp32.com/viewtopic.php?t=21450)  
19. Advanced System for Remote Updates on ESP32-Based Devices Using Over-the-Air Update Technology \- MDPI, accessed December 16, 2025, [https://www.mdpi.com/2073-431X/14/12/531](https://www.mdpi.com/2073-431X/14/12/531)  
20. Midi note cut off in loop mode \- Cubasis \- Steinberg Forums, accessed December 16, 2025, [https://forums.steinberg.net/t/midi-note-cut-off-in-loop-mode/972172](https://forums.steinberg.net/t/midi-note-cut-off-in-loop-mode/972172)  
21. MIDI clips, have a note play over repeat : r/Bitwig \- Reddit, accessed December 16, 2025, [https://www.reddit.com/r/Bitwig/comments/1hvpfr7/midi\_clips\_have\_a\_note\_play\_over\_repeat/](https://www.reddit.com/r/Bitwig/comments/1hvpfr7/midi_clips_have_a_note_play_over_repeat/)  
22. Event Queue \- Game Programming Patterns, accessed December 16, 2025, [https://gameprogrammingpatterns.com/event-queue.html](https://gameprogrammingpatterns.com/event-queue.html)  
23. How can I create a seamless loop without clicks? \- Logic Pro Help, accessed December 16, 2025, [https://www.logicprohelp.com/forums/topic/155787-how-can-i-create-a-seamless-loop-without-clicks/](https://www.logicprohelp.com/forums/topic/155787-how-can-i-create-a-seamless-loop-without-clicks/)  
24. How to deal with a wrapping counter in embedded C \- Stack Overflow, accessed December 16, 2025, [https://stackoverflow.com/questions/3095623/how-to-deal-with-a-wrapping-counter-in-embedded-c](https://stackoverflow.com/questions/3095623/how-to-deal-with-a-wrapping-counter-in-embedded-c)  
25. What happened first? Handling timer wraparound \- Rapita Systems, accessed December 16, 2025, [https://www.rapitasystems.com/blog/what-happened-first-handling-timer-wraparound](https://www.rapitasystems.com/blog/what-happened-first-handling-timer-wraparound)  
26. Introduction To DMX512 | Pathway Connectivity, accessed December 16, 2025, [https://pathway.acuitybrands.com/-/media/abl/pathway/files/resources/reference-guides/introduction-to-dmx512.pdf?forceBehavior=open](https://pathway.acuitybrands.com/-/media/abl/pathway/files/resources/reference-guides/introduction-to-dmx512.pdf?forceBehavior=open)  
27. DMX-512 Fundamentals \- Lutron, accessed December 16, 2025, [https://assets.lutron.com/a/documents/DMX%20webinar\_7-29-2010.pdf](https://assets.lutron.com/a/documents/DMX%20webinar_7-29-2010.pdf)  
28. Fade \[The DMX Wiki\], accessed December 16, 2025, [https://www.thedmxwiki.com/dmx\_definitions/fade](https://www.thedmxwiki.com/dmx_definitions/fade)  
29. Lighting Cue Timing – Better Scene Transitions, accessed December 16, 2025, [https://www.onstagelighting.co.uk/console-programming/lighting-cue-timing/](https://www.onstagelighting.co.uk/console-programming/lighting-cue-timing/)  
30. Core® Control Systems \- Whelen Engineering, accessed December 16, 2025, [https://www.whelen.com/control-systems/core-control-systems](https://www.whelen.com/control-systems/core-control-systems)  
31. How DVI and V2V Lighting Tech Protect First Responders \- Whelen Engineering, accessed December 16, 2025, [https://www.whelen.com/newsroom/articles/benefits-of-dvi-v2v-technology-for-first-responders](https://www.whelen.com/newsroom/articles/benefits-of-dvi-v2v-technology-for-first-responders)  
32. Clearer Warnings, Safer Responses. \- Whelen Engineering, accessed December 16, 2025, [https://www.whelen.com/nighttimesafety](https://www.whelen.com/nighttimesafety)  
33. Linear LED PWM, accessed December 16, 2025, [https://jared.geek.nz/2013/02/linear-led-pwm/](https://jared.geek.nz/2013/02/linear-led-pwm/)  
34. J1939 Explained (2025): PGNs, SPNs & Heavy-Duty Diagnostics \- AutoPi.io, accessed December 16, 2025, [https://www.autopi.io/blog/j1939-explained/](https://www.autopi.io/blog/j1939-explained/)  
35. Hard real-time & scheduling : r/embedded \- Reddit, accessed December 16, 2025, [https://www.reddit.com/r/embedded/comments/us8kps/hard\_realtime\_scheduling/](https://www.reddit.com/r/embedded/comments/us8kps/hard_realtime_scheduling/)  
36. Task Scheduling in Embedded System, accessed December 16, 2025, [https://www.embedded.com/tasks-and-scheduling/](https://www.embedded.com/tasks-and-scheduling/)  
37. Introduction to Microcontrollers \- Driving WS2812 RGB LEDs \- EmbeddedRelated.com, accessed December 16, 2025, [https://www.embeddedrelated.com/showarticle/528.php](https://www.embeddedrelated.com/showarticle/528.php)  
38. How to fade an LED linearly using PWM. : r/electronics \- Reddit, accessed December 16, 2025, [https://www.reddit.com/r/electronics/comments/18148v/how\_to\_fade\_an\_led\_linearly\_using\_pwm/](https://www.reddit.com/r/electronics/comments/18148v/how_to_fade_an_led_linearly_using_pwm/)