#Universal Time Layer Protocol (UTLP)**Status:** Draft / Experimental
**Maintainer:** MLE Haptics Project

> **"Time is a Public Utility."**

##1. Abstract
The Universal Time Layer Protocol (UTLP) is an open, unencrypted, and application-agnostic protocol for distributed time synchronization over BLE (Bluetooth Low Energy) Mesh.

Unlike traditional synchronization methods that couple timing with application data (requiring pairing, encryption, and specific app logic), UTLP treats time as a **broadcast environmental variable**. It allows disparate devices—from medical wearables to municipal infrastructure—to share a single, high-precision "Source of Truth" without exchanging private data.

##2. Philosophy: The "Glass Wall" Architecture
UTLP mandates a strict separation of concerns within the firmware:

* **The Time Stack (Public/Low-Level):**
* Listens for *any* UTLP beacon.
* Prioritizes sources based on Stratum (distance to GPS) and Stability.
* Maintains a monotonic system clock (microsecond precision).
* **Security:** None. Relies on "Common Mode Rejection" (if time is spoofed, it is spoofed identically for all local nodes, preserving relative synchronization).


* **The Application Stack (Private/High-Level):**
* Contains user data, encryption, and business logic.
* **Read-Only Access:** Simply queries `UTLP_GetEpoch()` to schedule events.
* Does not need to know *how* synchronization was achieved.



##3. Stratum Hierarchy
UTLP uses a "Baton Passing" model (similar to NTP) to determine authority. Lower Stratum values indicate higher trust.

| Stratum | Class | Description |
| --- | --- | --- |
| **0** | **Primary Reference** | Active external lock (GPS, Atomic, Cellular PTP). The "Gold Standard." |
| **1** | **Direct Link** | Device directly receiving RF packets from Stratum 0. |
| **2-15** | **Mesh Hop** | Device synced to Stratum (N-1). Each hop adds ~50µs jitter uncertainty. |
| **255** | **Free Running** | No external reference. Running on internal crystal with local drift compensation. |

##4. Protocol Specification
UTLP utilizes standard BLE Advertising packets.

**Service UUID:** `0xFEFE` (Proposed)

###Packet Payload Structure (Manufacturing Data)```c
struct UTLP_Payload {
    uint8_t  magic[2];       // 0xFE, 0xFE (Protocol Identifier)
    uint8_t  stratum;        // 0 = GPS, 255 = Free Run
    uint8_t  quality;        // 0-100 (Battery level or Oscillator confidence)
    uint8_t  hops;           // Distance from Master (Loop prevention)
    uint64_t epoch_us;       // Microseconds since Epoch (Jan 1 1970 or Custom)
    int32_t  drift_rate;     // Estimated drift in ppb (parts per billion)
};

```

##5. operational Logic
###5.1 Opportunistic Synchronization
Devices default to **Listener Mode**.

1. Device scans for `0xFEFE` packets.
2. **Comparison:**
* Is `Packet.Stratum < Current_Stratum`? **Switch immediately.**
* Is `Packet.Stratum == Current_Stratum` AND `Packet.Quality > Current_Quality`? **Switch.**


3. **Result:** A cheap consumer device will automatically "latch" onto a high-precision source (e.g., an emergency vehicle or base station) passing nearby, temporarily achieving Stratum 1 precision.

###5.2 The Flywheel Effect
If a device loses connection to its Master (e.g., source moves out of range):

1. It does **not** reset the clock.
2. It enters **Holdover Mode**.
3. It degrades its advertised Stratum (e.g., from 2 to 3, or to 255).
4. It continues to increment the clock using its internal crystal, applying the last known `Drift_Rate` correction.

###5.3 Battery-Aware Leader Election (The "Swarm" Rule)
In the absence of Stratum 0/1 sources (e.g., deep indoors):

1. Nodes broadcast their **Battery Level** in the `quality` field.
2. If `My_Battery < Threshold` (e.g., 20%), the current Master sets `quality = 0`.
3. The swarm automatically re-elects the neighbor with the highest `quality` score as the new local time anchor.

##6. Security Considerations
UTLP effectively creates a **Shared Hallucination**.

* **Spoofing:** A bad actor *can* broadcast a fake time (e.g., "The year is 2050").
* **Impact:** All listening devices will agree it is 2050.
* **Safety:** Since haptic/therapeutic patterns rely on **relative timing** (Intervals), the absolute time error is irrelevant to physical safety. The "Left" and "Right" units remain perfectly synchronized to the spoofed clock.
