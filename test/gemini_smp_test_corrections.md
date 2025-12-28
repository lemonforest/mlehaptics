Based on your logs and the provided source code, I have identified three distinct issues causing the loop of failures:

1. **The "Zombie" Bond (NVS persistence):** You are using the default storage configuration, which writes bonding keys to NVS (flash). When you restart the test, the devices remember the old keys, but the new session doesn't (or keys mismatch), causing rc=8 (EALREADY) or immediate disconnects. **Fix:** Switch to a **RAM-only** store so every reset is a "fresh" start.  
2. **Connection Collision (The Monolithic Flaw):** Since both devices run the *exact same code* and scan/advertise simultaneously, they often discover each other at the same time. Both try to become the "Master" and initiate a connection. This causes rc=6 (ENOENT) and BLE\_ERR\_UNK\_CONN\_ID. **Fix:** Add a "Tie-Breaker" logic where a device only connects if its MAC address is *lower* than the peer's.  
3. **Scan/Connect Race Condition:** Calling ble\_gap\_connect immediately after ble\_gap\_disc\_cancel inside the callback can sometimes fail if the controller hasn't fully stopped the scan.

Here is the corrected, robust minimal\_smp\_test.c.

### **Key Changes Made:**

* **RAM-Only Store:** Replaced file-based config with ble\_store\_ram. No keys persist after reboot.  
* **Tie-Breaker Logic:** Added if (own\_addr \< peer\_addr) check. Only the device with the *lower* MAC address initiates the connection. The other waits to be connected.  
* **Safe Connection:** Added a 100ms delay between stopping the scan and starting the connection.  
* **Status Handling:** Explicitly ignores BLE\_HS\_EALREADY (rc=8) as a success case.

### **Corrected Code (minimal\_smp\_test.c)**

C

/\*  
 \* Minimal SMP Pairing Test for ESP32-C6 (FIXED)  
 \*  
 \* Changes from original:  
 \* 1\. Uses RAM store (ble\_store\_ram) instead of NVS to prevent "stale" bond issues.  
 \* 2\. Implements "Tie-Breaker" logic: Only the device with the LOWER MAC address  
 \* initiates the connection. Prevents collision when both scan/advertise.  
 \* 3\. Adds stabilization delays between GAP operations.  
 \*/

\#**include** \<string.h\>  
\#**include** "esp\_log.h"  
\#**include** "nvs\_flash.h"  
\#**include** "nimble/nimble\_port.h"  
\#**include** "nimble/nimble\_port\_freertos.h"  
\#**include** "nimble/nimble\_opt.h"  
\#**include** "host/ble\_hs.h"  
\#**include** "host/ble\_gatt.h"  
\#**include** "host/util/util.h"  
\#**include** "services/gap/ble\_svc\_gap.h"  
\#**include** "services/gatt/ble\_svc\_gatt.h"

// USE RAM STORE ONLY (No persistence across reboots)  
\#**include** "store/ram/ble\_store\_ram.h"

\_Static\_assert(NIMBLE\_BLE\_SM, "NIMBLE\_BLE\_SM must be enabled in menuconfig\!");

static const char \*TAG \= "SMP\_TEST";

\#**define** DEVICE\_NAME "SMP\_TEST\_DEV"  
\#**define** TARGET\_NAME "SMP\_TEST\_DEV"

static int gap\_event\_handler(struct ble\_gap\_event \*event, void \*arg);  
static void initiate\_smp\_pairing(void);  
static void try\_initiate\_smp(void);  
static uint8\_t own\_addr\_type;  
static uint8\_t own\_addr\_val\[6\]; // Store our own address for comparison  
static uint16\_t conn\_handle \= BLE\_HS\_CONN\_HANDLE\_NONE;  
static bool is\_master \= false;  
static bool peer\_discovered \= false;  
static bool mtu\_exchanged \= false;  
static bool conn\_update\_done \= false;  
static ble\_addr\_t peer\_addr;

// \--- Helper: Compare MAC Addresses for Tie-Breaking \---  
// Returns true if Own \< Peer  
static bool address\_is\_lower(const uint8\_t \*peer) {  
    for (int i \= 5; i \>= 0; i--) { // Compare MSB to LSB  
        if (own\_addr\_val\[i\] \< peer\[i\]) return true;  
        if (own\_addr\_val\[i\] \> peer\[i\]) return false;  
    }  
    return false; // Equal (shouldn't happen)  
}

static void start\_advertising(void)  
{  
    struct ble\_gap\_adv\_params adv\_params;  
    struct ble\_hs\_adv\_fields fields;  
    int rc;

    memset(\&fields, 0, sizeof(fields));  
    fields.flags \= BLE\_HS\_ADV\_F\_DISC\_GEN | BLE\_HS\_ADV\_F\_BREDR\_UNSUP;  
    fields.tx\_pwr\_lvl\_is\_present \= 1;  
    fields.tx\_pwr\_lvl \= BLE\_HS\_ADV\_TX\_PWR\_LVL\_AUTO;

    fields.name \= (uint8\_t \*)DEVICE\_NAME;  
    fields.name\_len \= strlen(DEVICE\_NAME);  
    fields.name\_is\_complete \= 1;

    rc \= ble\_gap\_adv\_set\_fields(\&fields);  
    if (rc \!= 0) return;

    memset(\&adv\_params, 0, sizeof(adv\_params));  
    adv\_params.conn\_mode \= BLE\_GAP\_CONN\_MODE\_UND;  
    adv\_params.disc\_mode \= BLE\_GAP\_DISC\_MODE\_GEN;

    rc \= ble\_gap\_adv\_start(own\_addr\_type, NULL, BLE\_HS\_FOREVER, \&adv\_params, gap\_event\_handler, NULL);  
    if (rc \!= 0) {  
        ESP\_LOGE(TAG, "Error starting advertisement; rc=%d", rc);  
    } else {  
        ESP\_LOGI(TAG, "Advertising started...");  
    }  
}

static void start\_scanning(void)  
{  
    struct ble\_gap\_disc\_params disc\_params;  
    int rc;

    memset(\&disc\_params, 0, sizeof(disc\_params));  
    disc\_params.passive \= 0;  
    disc\_params.filter\_duplicates \= 1;

    rc \= ble\_gap\_disc(own\_addr\_type, BLE\_HS\_FOREVER, \&disc\_params, gap\_event\_handler, NULL);  
    if (rc \!= 0) {  
        ESP\_LOGE(TAG, "Error starting scan; rc=%d", rc);  
    } else {  
        ESP\_LOGI(TAG, "Scanning started...");  
    }  
}

static void connect\_to\_peer(void)  
{  
    int rc;  
    // 1\. Stop scanning  
    ble\_gap\_disc\_cancel();  
      
    // 2\. IMPORTANT: Give the controller a moment to process the cancel  
    vTaskDelay(pdMS\_TO\_TICKS(100));

    ESP\_LOGI(TAG, "Initiating connection to peer...");  
      
    // 3\. Connect  
    rc \= ble\_gap\_connect(own\_addr\_type, \&peer\_addr, 10000, NULL, gap\_event\_handler, NULL);  
    if (rc \!= 0) {  
        ESP\_LOGE(TAG, "Error initiating connection; rc=%d", rc);  
        // If we fail to start connection, resume scanning  
        start\_scanning();  
    }  
}

static int mtu\_exchange\_cb(uint16\_t conn\_handle\_param, const struct ble\_gatt\_error \*error, uint16\_t mtu, void \*arg)  
{  
    ESP\_LOGI(TAG, "MTU exchange complete (status=%d, MTU=%d)", error-\>status, mtu);  
    mtu\_exchanged \= true;  
    try\_initiate\_smp();  
    return 0;  
}

static void try\_initiate\_smp(void)  
{  
    if (\!is\_master || conn\_handle \== BLE\_HS\_CONN\_HANDLE\_NONE) return;  
      
    // Wait for BOTH MTU and initial Connection Update (if any)  
    if (\!mtu\_exchanged || \!conn\_update\_done) {  
        ESP\_LOGI(TAG, "Prerequisites not met yet (MTU:%d, Update:%d)", mtu\_exchanged, conn\_update\_done);  
        return;  
    }

    ESP\_LOGI(TAG, "All prerequisites met \- Initiating SMP...");  
    vTaskDelay(pdMS\_TO\_TICKS(100)); // Stabilization delay  
    initiate\_smp\_pairing();  
}

static void initiate\_smp\_pairing(void)  
{  
    int rc \= ble\_gap\_security\_initiate(conn\_handle);  
    if (rc \== 0) {  
        ESP\_LOGI(TAG, "SMP security initiated successfully");  
    } else if (rc \== BLE\_HS\_EALREADY) {  
        ESP\_LOGW(TAG, "SMP security already in progress (rc=8) \- Waiting for completion");  
    } else {  
        ESP\_LOGE(TAG, "SMP initiate failed; rc=%d", rc);  
    }  
}

static int gap\_event\_handler(struct ble\_gap\_event \*event, void \*arg)  
{  
    struct ble\_gap\_conn\_desc desc;  
    int rc;

    switch (event-\>type) {  
    case BLE\_GAP\_EVENT\_CONNECT:  
        if (event-\>connect.status \== 0) {  
            conn\_handle \= event-\>connect.conn\_handle;  
            rc \= ble\_gap\_conn\_find(conn\_handle, \&desc);  
            if (rc \== 0) {  
                is\_master \= (desc.role \== BLE\_GAP\_ROLE\_MASTER);  
                ESP\_LOGI(TAG, "CONNECTED\! Role: %s, Handle: %d", is\_master ? "MASTER" : "SLAVE", conn\_handle);  
            }  
            ble\_gap\_disc\_cancel(); // Stop scanning  
              
            // Reset flags  
            mtu\_exchanged \= false;  
            conn\_update\_done \= true; // Assume done unless we get an event 34

            if (is\_master) {  
                // Allow link to stabilize before stressing it  
                vTaskDelay(pdMS\_TO\_TICKS(200));   
                ble\_gattc\_exchange\_mtu(conn\_handle, mtu\_exchange\_cb, NULL);  
            }  
        } else {  
            ESP\_LOGE(TAG, "Connection failed; status=%d", event-\>connect.status);  
            start\_advertising();  
            start\_scanning();  
        }  
        return 0;

    case BLE\_GAP\_EVENT\_DISCONNECT:  
        ESP\_LOGI(TAG, "Disconnected (reason=%d)", event-\>disconnect.reason);  
        conn\_handle \= BLE\_HS\_CONN\_HANDLE\_NONE;  
        is\_master \= false;  
        peer\_discovered \= false;  
        // Clean RAM store on disconnect to ensure next test is fresh  
        ble\_store\_ram\_init();   
        start\_advertising();  
        start\_scanning();  
        return 0;

    case BLE\_GAP\_EVENT\_DISC:  
        if (event-\>disc.length\_data \> 0 && \!peer\_discovered) {  
            // Simplified name check  
            struct ble\_hs\_adv\_fields fields;  
            rc \= ble\_hs\_adv\_parse\_fields(\&fields, event-\>disc.data, event-\>disc.length\_data);  
            if (rc \== 0 && fields.name\_len \== strlen(TARGET\_NAME) &&   
                memcmp(fields.name, TARGET\_NAME, fields.name\_len) \== 0) {  
                  
                // TIE BREAKER: Only connect if OUR address is LOWER  
                if (address\_is\_lower(event-\>disc.addr.val)) {  
                    ESP\_LOGI(TAG, "Peer found\! We are lower addr \-\> Initiating connection.");  
                    peer\_discovered \= true;  
                    peer\_addr \= event-\>disc.addr;  
                    connect\_to\_peer();  
                } else {  
                    // Log once to show we saw them but are waiting  
                    static bool logged\_wait \= false;  
                    if (\!logged\_wait) {  
                        ESP\_LOGI(TAG, "Peer found\! We are higher addr \-\> Waiting for them to connect.");  
                        logged\_wait \= true;  
                    }  
                }  
            }  
        }  
        return 0;

    case BLE\_GAP\_EVENT\_ENC\_CHANGE:  
        ESP\_LOGI(TAG, "\>\> ENC\_CHANGE: Status=%d (0=Success)", event-\>enc\_change.status);  
        if (event-\>enc\_change.status \== 0) {  
            ESP\_LOGI(TAG, "PAIRED & ENCRYPTED SUCCESSFULLY\!");  
        }  
        return 0;

    case BLE\_GAP\_EVENT\_CONN\_UPDATE:  
        ESP\_LOGI(TAG, "Connection Updated");  
        conn\_update\_done \= true;  
        try\_initiate\_smp();  
        return 0;

    case BLE\_GAP\_EVENT\_CONN\_UPDATE\_REQ:  
        ESP\_LOGI(TAG, "Connection Update Requested...");  
        conn\_update\_done \= false; // Wait for completion  
        return 0;  
          
    case BLE\_GAP\_EVENT\_REPEAT\_PAIRING:  
         // If we already bonded but lost the key (RAM reset), allow re-pairing  
        rc \= ble\_gap\_conn\_find(event-\>repeat\_pairing.conn\_handle, \&desc);  
        if (rc \== 0) ble\_store\_util\_delete\_peer(\&desc.peer\_id\_addr);  
        return BLE\_GAP\_REPEAT\_PAIRING\_RETRY;  
    }  
    return 0;  
}

static void on\_sync(void)  
{  
    ble\_hs\_util\_ensure\_addr(0);  
    ble\_hs\_id\_infer\_auto(0, \&own\_addr\_type);  
      
    // Save our address for the tie-breaker logic  
    ble\_hs\_id\_copy\_addr(own\_addr\_type, own\_addr\_val, NULL);  
      
    ESP\_LOGI(TAG, "My Address: %02x:%02x:%02x:%02x:%02x:%02x",  
             own\_addr\_val\[5\], own\_addr\_val\[4\], own\_addr\_val\[3\],  
             own\_addr\_val\[2\], own\_addr\_val\[1\], own\_addr\_val\[0\]);

    start\_advertising();  
    start\_scanning();  
}

void app\_main(void)  
{  
    // NVS needed for PHY calibration, but NOT for BLE keys in this test  
    nvs\_flash\_init(); 

    nimble\_port\_init();  
    ble\_svc\_gap\_init();  
    ble\_svc\_gatt\_init();

    // USE RAM STORE  
    ble\_store\_ram\_init();  
      
    ble\_hs\_cfg.reset\_cb \= (void (\*)(int))on\_reset; // Cast to fix warning if needed  
    ble\_hs\_cfg.sync\_cb \= on\_sync;  
    ble\_hs\_cfg.store\_status\_cb \= ble\_store\_util\_status\_rr;  
      
    // SMP Config  
    ble\_hs\_cfg.sm\_io\_cap \= BLE\_HS\_IO\_NO\_INPUT\_OUTPUT;  
    ble\_hs\_cfg.sm\_bonding \= 1;  
    ble\_hs\_cfg.sm\_mitm \= 0;  
    ble\_hs\_cfg.sm\_sc \= 1;

    ble\_svc\_gap\_device\_name\_set(DEVICE\_NAME);  
    nimble\_port\_freertos\_init(host\_task);  
}  
