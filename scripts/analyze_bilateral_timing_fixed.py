#!/usr/bin/env python3
"""
Analyze bilateral timing from dual-device logs (FIXED VERSION).
Calculates CLIENT activation delta from SERVER's period/2 target.
FIX: Deduplicates activations by timestamp (don't count "Cycle starts" AND "Motor cmd" separately)
"""

import re
import sys

def parse_log(filename):
    """Extract activation timestamps and cycle period from log file."""
    activations_set = set()  # Use set to deduplicate by (timestamp, cycle)
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

            # Extract activation timestamp - ONLY from "Cycle starts ACTIVE" (more reliable)
            active_match = re.search(r'I\((\d+)\)MOTOR_TASK:.*CyclestartsACTIVE', cleaned_line)

            if active_match:
                timestamp_ms = int(active_match.group(1))
                if current_cycle_ms:  # Only add if we have a valid cycle period
                    activations_set.add((timestamp_ms, current_cycle_ms))

    # Convert set to sorted list
    activations = sorted(list(activations_set))
    return activations

def main():
    if len(sys.argv) != 3:
        print("Usage: analyze_bilateral_timing_fixed.py <server_log> <client_log>")
        sys.exit(1)

    server_log = sys.argv[1]
    client_log = sys.argv[2]

    print("Parsing SERVER log...")
    server_acts = parse_log(server_log)
    print(f"  Found {len(server_acts)} SERVER activations")

    print("Parsing CLIENT log...")
    client_acts = parse_log(client_log)
    print(f"  Found {len(client_acts)} CLIENT activations")

    if not server_acts or not client_acts:
        print("ERROR: No activations found in one or both logs")
        sys.exit(1)

    print("\n" + "="*80)
    print("BILATERAL TIMING ANALYSIS (DEDUPLICATED)")
    print("="*80)

    # Pair up activations chronologically
    server_idx = 0
    client_idx = 0

    print(f"\n{'Time (s)':<12} {'Period (ms)':<12} {'Delta (ms)':<12} {'Target (ms)':<12} {'Error (ms)':<12} {'Status'}")
    print("-" * 80)

    while server_idx < len(server_acts) and client_idx < len(client_acts):
        server_ts, server_period = server_acts[server_idx]
        client_ts, client_period = client_acts[client_idx]

        # Calculate delta (CLIENT - SERVER)
        delta_ms = client_ts - server_ts

        # Target is period/2
        target_ms = server_period // 2 if server_period else 1000

        # Error from target
        error_ms = delta_ms - target_ms

        # Status
        if abs(error_ms) <= 10:
            status = "GOOD"
        elif abs(error_ms) <= 50:
            status = "WARNING"
        else:
            status = "OVERLAP" if error_ms < 0 else "DRIFT"

        # Print analysis
        time_s = server_ts / 1000.0
        print(f"{time_s:<12.2f} {server_period:<12} {delta_ms:<12} {target_ms:<12} {error_ms:<+12} {status}")

        # Move to next pair
        if delta_ms < 0:
            # CLIENT activated before this SERVER - skip this CLIENT
            client_idx += 1
        else:
            # Normal case - move to next SERVER
            server_idx += 1
            # Also move CLIENT if we've processed this one
            if client_idx < len(client_acts) - 1:
                next_client_ts = client_acts[client_idx + 1][0]
                if next_client_ts < server_ts + server_period:
                    client_idx += 1

    print("="*80)

if __name__ == "__main__":
    main()
