#!/usr/bin/env python3
"""
Analyze bilateral phase timing from dual-device logs (CORRECTED VERSION).

Measures CLIENT motor activation (ACTIVE state) phase offset from ideal antiphase
target (SERVER timestamp + period/2).

KEY FIX: Only counts "Cycle starts ACTIVE" for both devices, ignoring CLIENT's
"Cycle starts INACTIVE" which is not a motor activation.
"""

import re
import sys
import statistics

def parse_log_active_only(filename):
    """Extract ACTIVE activation timestamps and cycle period from log file.

    IMPORTANT: Only counts "Cycle starts ACTIVE" - ignores INACTIVE transitions.
    """
    activations = []
    current_cycle_ms = None

    # Detect encoding by checking for UTF-16 LE BOM (FF FE)
    with open(filename, 'rb') as f:
        first_bytes = f.read(2)

    if first_bytes == b'\xff\xfe':
        encoding = 'utf-16-le'
    else:
        encoding = 'utf-8'

    # Read file with detected encoding
    with open(filename, 'r', encoding=encoding, errors='ignore') as f:
        lines = f.readlines()

    for line in lines:
        # Remove ALL spaces (handles both normal and wide-character encoding)
        cleaned_line = line.replace(' ', '')

        # Extract cycle period from motor epoch
        # Format: "Motor epoch set: 6072947 us, cycle: 2000 ms"
        epoch_match = re.search(r'Motorepochset:(\d+)us,cycle:(\d+)ms', cleaned_line)
        if epoch_match:
            current_cycle_ms = int(epoch_match.group(2))

        # Extract ACTIVE activation timestamp ONLY
        # Matches "Cycle starts ACTIVE" but NOT "Cycle starts INACTIVE"
        active_match = re.search(r'I\((\d+)\)MOTOR_TASK:.*CyclestartsACTIVE', cleaned_line)

        if active_match:
            timestamp_ms = int(active_match.group(1))
            if current_cycle_ms:  # Only add if we have a valid cycle period
                activations.append((timestamp_ms, current_cycle_ms))

    return activations

def main():
    if len(sys.argv) != 3:
        print("Usage: analyze_bilateral_phase.py <server_log> <client_log>")
        sys.exit(1)

    server_log = sys.argv[1]
    client_log = sys.argv[2]

    print("Parsing SERVER log (ACTIVE only)...")
    server_acts = parse_log_active_only(server_log)
    print(f"  Found {len(server_acts)} SERVER activations")

    print("Parsing CLIENT log (ACTIVE only)...")
    client_acts = parse_log_active_only(client_log)
    print(f"  Found {len(client_acts)} CLIENT activations")

    if not server_acts or not client_acts:
        print("ERROR: No activations found in one or both logs")
        sys.exit(1)

    # Statistics tracking
    all_phase_errors = []
    overlap_count = 0
    good_count = 0
    warning_count = 0
    drift_count = 0

    print("\n" + "="*100)
    print("BILATERAL PHASE TIMING ANALYSIS (ACTIVE CYCLES ONLY)")
    print("="*100)

    # Pair up activations - match each CLIENT ACTIVE with nearest SERVER ACTIVE
    print(f"\n{'Time (s)':<12} {'Period (ms)':<12} {'CLIENT @':<12} {'Target @':<12} {'Phase Err':<12} {'Status'}")
    print("-" * 100)

    server_idx = 0
    client_idx = 0

    while server_idx < len(server_acts) and client_idx < len(client_acts):
        server_ts, server_period = server_acts[server_idx]
        client_ts, client_period = client_acts[client_idx]

        # Target antiphase: CLIENT should start ACTIVE at SERVER_time + period/2
        target_client_ts = server_ts + (server_period // 2)

        # Phase error: How far is CLIENT from ideal target?
        phase_error_ms = client_ts - target_client_ts

        # Status
        if abs(phase_error_ms) <= 10:
            status = "GOOD"
            good_count += 1
        elif abs(phase_error_ms) <= 50:
            status = "WARNING"
            warning_count += 1
        elif phase_error_ms < 0:
            status = "OVERLAP"
            overlap_count += 1
        else:
            status = "DRIFT"
            drift_count += 1

        all_phase_errors.append(phase_error_ms)

        # Print analysis
        time_s = server_ts / 1000.0
        client_rel_ms = client_ts - server_ts  # Relative to SERVER start
        target_rel_ms = server_period // 2
        print(f"{time_s:<12.2f} {server_period:<12} {client_rel_ms:<+12} {target_rel_ms:<12} {phase_error_ms:<+12} {status}")

        # Move to next pair
        if phase_error_ms < -(server_period // 2):
            # CLIENT is more than half-period before SERVER - likely from previous cycle
            client_idx += 1
        elif phase_error_ms > (server_period // 2):
            # CLIENT is more than half-period after SERVER - likely from next cycle
            server_idx += 1
        else:
            # Normal case - within reasonable range, advance both
            server_idx += 1
            client_idx += 1

    print("="*100)

    # Statistics summary
    print("\n" + "="*100)
    print("PHASE ERROR STATISTICS")
    print("="*100)

    print(f"\nTotal paired measurements: {len(all_phase_errors)}")
    print(f"Mean phase error:          {statistics.mean(all_phase_errors):+.1f} ms")
    print(f"Std deviation:             {statistics.stdev(all_phase_errors):.1f} ms" if len(all_phase_errors) > 1 else "N/A")
    print(f"Min error (most early):    {min(all_phase_errors):+.1f} ms")
    print(f"Max error (most late):     {max(all_phase_errors):+.1f} ms")

    print(f"\nStatus Breakdown:")
    print(f"  GOOD (±10ms):     {good_count:5d} ({100.0*good_count/len(all_phase_errors):.1f}%)")
    print(f"  WARNING (±50ms):  {warning_count:5d} ({100.0*warning_count/len(all_phase_errors):.1f}%)")
    print(f"  OVERLAP (<-50ms): {overlap_count:5d} ({100.0*overlap_count/len(all_phase_errors):.1f}%)")
    print(f"  DRIFT (>50ms):    {drift_count:5d} ({100.0*drift_count/len(all_phase_errors):.1f}%)")

    print("\n" + "="*100)
    print("KEY:")
    print("  'CLIENT @'   = CLIENT activation time relative to SERVER (ms)")
    print("  'Target @'   = Ideal antiphase target (period/2 after SERVER)")
    print("  'Phase Err'  = CLIENT timing error from target (negative=early, positive=late)")
    print("  'OVERLAP'    = CLIENT too early (>50ms before target, risk of both motors active)")
    print("  'DRIFT'      = CLIENT too late (>50ms after target, poor bilateral alternation)")
    print("  'WARNING'    = Within ±50ms of target (acceptable but not ideal)")
    print("  'GOOD'       = Within ±10ms of target (excellent bilateral coordination)")
    print("="*100)

if __name__ == "__main__":
    main()
