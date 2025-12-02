#!/bin/bash

# Analyze single-device timing drift
LOG_A="serial_log_dev_a_0644-20251202.txt"
LOG_B="serial_log_dev_b_converted.txt"

echo "==================================================================="
echo "Tech Spike: Isolated Device Timing Analysis"
echo "==================================================================="
echo ""

for LOG in "$LOG_A" "$LOG_B"; do
    DEVICE=$(echo $LOG | grep -o "dev_[ab]" | sed 's/dev_/Device /')
    echo "--- $DEVICE ($LOG) ---"
    
    grep -E "MOTOR_TASK: SERVER: Cycle starts" "$LOG" | awk -v dev="$DEVICE" '
    BEGIN {
        first_ms = 0;
        last_ms = 0;
        cycle_count = 0;
        error_sum = 0;
        error_sq_sum = 0;
        max_error = -999999;
        min_error = 999999;
    }
    {
        match($0, /\(([0-9]+)\)/, arr);
        if (arr[1]) {
            ms = arr[1];
            if (first_ms == 0) {
                first_ms = ms;
            }
            if (last_ms > 0) {
                delta = ms - last_ms;
                error = delta - 1000;
                error_sum += error;
                error_sq_sum += error * error;
                cycle_count++;
                
                if (error > max_error) max_error = error;
                if (error < min_error) min_error = error;
            }
            last_ms = ms;
        }
    }
    END {
        if (cycle_count > 0) {
            duration_s = (last_ms - first_ms) / 1000;
            duration_m = duration_s / 60;
            avg_error = error_sum / cycle_count;
            variance = (error_sq_sum / cycle_count) - (avg_error * avg_error);
            std_dev = sqrt(variance);
            
            # Calculate cumulative drift
            cumulative_drift_ms = avg_error * cycle_count;
            
            print "Cycles: " cycle_count;
            print "Duration: " duration_s " seconds (" sprintf("%.1f", duration_m) " minutes)";
            print "";
            print "Timing Precision:";
            print "  Mean error: " sprintf("%.3f", avg_error) " ms";
            print "  Std deviation: " sprintf("%.3f", std_dev) " ms";
            print "  Min error: " min_error " ms";
            print "  Max error: " max_error " ms";
            print "";
            print "Cumulative Drift:";
            print "  Total drift: " sprintf("%.1f", cumulative_drift_ms) " ms over " sprintf("%.1f", duration_m) " minutes";
            print "  Drift rate: " sprintf("%.3f", cumulative_drift_ms / duration_s) " ms/second";
            print "  Relative error: " sprintf("%.6f", (cumulative_drift_ms / (duration_s * 1000)) * 100) "%";
        }
    }
    '
    echo ""
done

echo "==================================================================="
