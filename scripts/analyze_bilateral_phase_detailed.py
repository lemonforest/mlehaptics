#!/usr/bin/env python3
"""
Analyze bilateral phase timing with BLE link quality metrics (RSSI, RTT, Quality).

Enhanced version that extracts:
- Motor activation timestamps
- Sync beacon RSSI (CLIENT measures SERVER signal strength)
- Sync beacon RTT (round-trip time)
- Time sync quality (0-100%)

Correlates phase errors with BLE link quality to identify root causes.
"""

import re
import sys
import statistics
from collections import defaultdict

def parse_log_with_metrics(filename):
    """Extract ACTIVE activation timestamps and BLE metrics from log file.

    Returns:
        activations: List of (timestamp_ms, cycle_ms) tuples for ACTIVE states
        rssi_by_time: Dict mapping timestamp -> RSSI value
        rtt_by_time: Dict mapping timestamp -> RTT value
        quality_by_time: Dict mapping timestamp -> quality percentage
    """
    activations = []
    rssi_by_time = {}
    rtt_by_time = {}
    quality_by_time = {}
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

        # Extract timestamp from log line (I(timestamp))
        ts_match = re.search(r'I\((\d+)\)', cleaned_line)
        if not ts_match:
            continue
        timestamp_ms = int(ts_match.group(1))

        # Extract cycle period from motor epoch
        # Format: "Motor epoch set: 6072947 us, cycle: 2000 ms"
        epoch_match = re.search(r'Motorepochset:(\d+)us,cycle:(\d+)ms', cleaned_line)
        if epoch_match:
            current_cycle_ms = int(epoch_match.group(2))

        # Extract ACTIVE activation timestamp ONLY
        # Matches "Cycle starts ACTIVE" but NOT "Cycle starts INACTIVE"
        active_match = re.search(r'MOTOR_TASK:.*CyclestartsACTIVE', cleaned_line)
        if active_match and current_cycle_ms:
            activations.append((timestamp_ms, current_cycle_ms))

        # Extract RSSI from beacon processing
        # Format: "Beacon processed (seq: X, rssi: -YY dBm, ...)"
        # Or: "rssi=-XX" or "RSSI:-XX"
        rssi_match = re.search(r'rssi[=:]\s*(-?\d+)', cleaned_line)
        if rssi_match:
            rssi_dbm = int(rssi_match.group(1))
            rssi_by_time[timestamp_ms] = rssi_dbm

        # Extract RTT from beacon processing
        # Format: "RTT measured: XXXXX μs" (in microseconds, need to convert to ms)
        # After space removal: "RTTmeasured:81452μs" or "rtt=XXms"
        rtt_match = re.search(r'(RTTmeasured:|rtt[=:])\s*(\d+)', cleaned_line, re.IGNORECASE)
        if rtt_match:
            rtt_value = int(rtt_match.group(2))
            # Check if it's in microseconds (typically >1000)
            if rtt_value > 1000:
                rtt_ms = rtt_value / 1000.0  # Convert μs to ms
            else:
                rtt_ms = float(rtt_value)  # Already in ms
            rtt_by_time[timestamp_ms] = rtt_ms

        # Extract quality from beacon processing or quality updates
        # Format: "quality=XX%" or "Quality: XX%"
        quality_match = re.search(r'quality[=:]\s*(\d+)%?', cleaned_line)
        if quality_match:
            quality_pct = int(quality_match.group(1))
            quality_by_time[timestamp_ms] = quality_pct

    return activations, rssi_by_time, rtt_by_time, quality_by_time

def find_last_known_metric(timestamp_ms, metric_by_time):
    """Find last known metric value at or before timestamp.

    Uses "carry forward" approach - returns the most recent metric
    measurement that occurred before or at the given timestamp.
    This ensures all motor activations have link quality data.

    Returns metric value or None if no metric exists before timestamp.
    """
    if not metric_by_time:
        return None

    # Find the most recent metric timestamp that is <= current timestamp
    last_metric_ts = None
    for ts in sorted(metric_by_time.keys()):
        if ts <= timestamp_ms:
            last_metric_ts = ts
        else:
            break  # Stop once we pass the target timestamp

    return metric_by_time.get(last_metric_ts) if last_metric_ts is not None else None

def main():
    if len(sys.argv) != 3:
        print("Usage: analyze_bilateral_phase_detailed.py <server_log> <client_log>")
        sys.exit(1)

    server_log = sys.argv[1]
    client_log = sys.argv[2]

    print("Parsing SERVER log (ACTIVE only)...")
    server_acts, _, _, _ = parse_log_with_metrics(server_log)
    print(f"  Found {len(server_acts)} SERVER activations")

    print("Parsing CLIENT log (ACTIVE + BLE metrics)...")
    client_acts, rssi_by_time, rtt_by_time, quality_by_time = parse_log_with_metrics(client_log)
    print(f"  Found {len(client_acts)} CLIENT activations")
    print(f"  Found {len(rssi_by_time)} RSSI samples")
    print(f"  Found {len(rtt_by_time)} RTT samples")
    print(f"  Found {len(quality_by_time)} Quality samples")

    # Debug: Show first few RTT samples
    if rtt_by_time:
        print(f"\n  First 5 RTT samples:")
        for i, (ts, rtt) in enumerate(sorted(rtt_by_time.items())[:5]):
            print(f"    T={ts}ms: RTT={rtt:.1f}ms")
    else:
        print(f"\n  WARNING: No RTT samples found in CLIENT log!")

    if not server_acts or not client_acts:
        print("ERROR: No activations found in one or both logs")
        sys.exit(1)

    # Statistics tracking
    all_phase_errors = []
    phase_with_metrics = []  # Tuples of (phase_error, rssi, rtt, quality)
    overlap_count = 0
    good_count = 0
    warning_count = 0
    drift_count = 0

    print("\n" + "="*120)
    print("BILATERAL PHASE TIMING WITH BLE LINK QUALITY ANALYSIS")
    print("="*120)

    # Pair up activations - match each CLIENT ACTIVE with nearest SERVER ACTIVE
    print(f"\n{'Time (s)':<10} {'Period':<8} {'CLIENT @':<10} {'Target @':<10} {'Phase Err':<11} {'RSSI':<8} {'RTT':<8} {'Quality':<9} {'Status'}")
    print("-" * 120)

    server_idx = 0
    client_idx = 0

    while server_idx < len(server_acts) and client_idx < len(client_acts):
        server_ts, server_period = server_acts[server_idx]
        client_ts, client_period = client_acts[client_idx]

        # Target antiphase: CLIENT should start ACTIVE at SERVER_time + period/2
        target_client_ts = server_ts + (server_period // 2)

        # Phase error: How far is CLIENT from ideal target?
        phase_error_ms = client_ts - target_client_ts

        # Find last known BLE metrics (carry forward until next beacon update)
        rssi = find_last_known_metric(client_ts, rssi_by_time)
        rtt = find_last_known_metric(client_ts, rtt_by_time)
        quality = find_last_known_metric(client_ts, quality_by_time)

        # Track metrics correlation
        if rssi is not None or rtt is not None or quality is not None:
            phase_with_metrics.append((phase_error_ms, rssi, rtt, quality))

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

        rssi_str = f"{rssi} dBm" if rssi is not None else "N/A"
        rtt_str = f"{rtt:.1f} ms" if rtt is not None else "N/A"
        quality_str = f"{quality}%" if quality is not None else "N/A"

        print(f"{time_s:<10.2f} {server_period:<8} {client_rel_ms:<+10} {target_rel_ms:<10} {phase_error_ms:<+11} {rssi_str:<8} {rtt_str:<8} {quality_str:<9} {status}")

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

    print("="*120)

    # Statistics summary
    print("\n" + "="*120)
    print("PHASE ERROR STATISTICS")
    print("="*120)

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

    # BLE Metrics Correlation Analysis
    if phase_with_metrics:
        print("\n" + "="*120)
        print("BLE LINK QUALITY CORRELATION ANALYSIS")
        print("="*120)

        # Separate measurements by status
        good_metrics = [(err, rssi, rtt, qual) for err, rssi, rtt, qual in phase_with_metrics if abs(err) <= 10]
        warning_metrics = [(err, rssi, rtt, qual) for err, rssi, rtt, qual in phase_with_metrics if 10 < abs(err) <= 50]
        poor_metrics = [(err, rssi, rtt, qual) for err, rssi, rtt, qual in phase_with_metrics if abs(err) > 50]

        def safe_mean(values):
            """Calculate mean, filtering out None values."""
            filtered = [v for v in values if v is not None]
            return statistics.mean(filtered) if filtered else None

        def print_metric_stats(label, metrics):
            """Print BLE metric statistics for a given status category."""
            if not metrics:
                print(f"\n{label}: No measurements")
                return

            rssi_vals = [rssi for _, rssi, _, _ in metrics if rssi is not None]
            rtt_vals = [rtt for _, _, rtt, _ in metrics if rtt is not None]
            qual_vals = [qual for _, _, _, qual in metrics if qual is not None]

            print(f"\n{label} ({len(metrics)} measurements):")
            if rssi_vals:
                print(f"  RSSI: mean={statistics.mean(rssi_vals):.1f} dBm, min={min(rssi_vals)}, max={max(rssi_vals)}")
            else:
                print(f"  RSSI: No data")

            if rtt_vals:
                print(f"  RTT:  mean={statistics.mean(rtt_vals):.1f} ms, min={min(rtt_vals)}, max={max(rtt_vals)}")
            else:
                print(f"  RTT:  No data")

            if qual_vals:
                print(f"  Quality: mean={statistics.mean(qual_vals):.1f}%, min={min(qual_vals)}%, max={max(qual_vals)}%")
            else:
                print(f"  Quality: No data")

        print_metric_stats("GOOD timing (±10ms)", good_metrics)
        print_metric_stats("WARNING timing (±50ms)", warning_metrics)
        print_metric_stats("POOR timing (>50ms)", poor_metrics)

        # Identify outlier patterns
        print("\n" + "="*120)
        print("OUTLIER ANALYSIS - POOR timing cycles (>50ms error)")
        print("="*120)

        if poor_metrics:
            print(f"\nTotal POOR cycles: {len(poor_metrics)}")

            # Check if RSSI/RTT/Quality correlate with poor timing
            rssi_outliers = [rssi for _, rssi, _, _ in poor_metrics if rssi is not None and rssi < -90]
            rtt_outliers = [rtt for _, _, rtt, _ in poor_metrics if rtt is not None and rtt > 100]
            qual_outliers = [qual for _, _, _, qual in poor_metrics if qual is not None and qual < 50]

            print(f"  Weak RSSI (<-90 dBm): {len(rssi_outliers)} cycles")
            print(f"  High RTT (>100ms): {len(rtt_outliers)} cycles")
            print(f"  Low Quality (<50%): {len(qual_outliers)} cycles")

            # Recommendation
            print("\nRecommendations:")
            if len(rssi_outliers) > len(poor_metrics) * 0.3:
                print("  [!] Weak RSSI correlates with timing errors - consider TX power boost or antenna improvement")
            if len(rtt_outliers) > len(poor_metrics) * 0.3:
                print("  [!] High RTT correlates with timing errors - consider BLE connection parameter optimization")
            if len(qual_outliers) > len(poor_metrics) * 0.3:
                print("  [!] Low sync quality correlates with timing errors - implement quality-based outlier rejection")

            # Check if most poor timing has NO BLE issues
            no_ble_issues = [
                (err, rssi, rtt, qual) for err, rssi, rtt, qual in poor_metrics
                if (rssi is None or rssi >= -90) and
                   (rtt is None or rtt <= 100) and
                   (qual is None or qual >= 50)
            ]
            if len(no_ble_issues) > len(poor_metrics) * 0.7:
                print(f"  [OK] {len(no_ble_issues)}/{len(poor_metrics)} POOR cycles have GOOD BLE metrics")
                print("       -> Timing errors NOT caused by BLE link quality")
                print("       -> Likely algorithmic issue (convergence, correction limits, prediction)")

    print("\n" + "="*120)
    print("KEY:")
    print("  'CLIENT @'   = CLIENT activation time relative to SERVER (ms)")
    print("  'Target @'   = Ideal antiphase target (period/2 after SERVER)")
    print("  'Phase Err'  = CLIENT timing error from target (negative=early, positive=late)")
    print("  'RSSI'       = BLE signal strength (dBm, -50=excellent, -90=poor)")
    print("  'RTT'        = Round-trip time for sync beacons (ms)")
    print("  'Quality'    = Time sync quality (0-100%)")
    print("  'OVERLAP'    = CLIENT too early (>50ms before target, risk of both motors active)")
    print("  'DRIFT'      = CLIENT too late (>50ms after target, poor bilateral alternation)")
    print("  'WARNING'    = Within ±50ms of target (acceptable but not ideal)")
    print("  'GOOD'       = Within ±10ms of target (excellent bilateral coordination)")
    print("="*120)

if __name__ == "__main__":
    main()
