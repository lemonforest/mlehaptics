#!/usr/bin/env python3
"""Check motor task logs in CLIENT serial output."""

with open('motor_log_results.txt', 'w', encoding='utf-8') as out:
    with open('serial_log_dev_b_1747-20251201.txt', 'r', encoding='utf-16-le', errors='ignore') as f:
        count = 0
        for line in f:
            if 'MOTOR_TASK' in line and ('CATCH-UP' in line or 'INACTIVE' in line or 'calculated' in line or 'wait=' in line):
                out.write(line.strip() + '\n')
                count += 1
                if count >= 50:
                    break

        if count == 0:
            out.write("No MOTOR_TASK drift/wait logs found.\n")
            out.write("\nSearching for any MOTOR_TASK logs...\n\n")

    # If no drift logs, show any MOTOR_TASK logs
    if count == 0:
        with open('serial_log_dev_b_1747-20251201.txt', 'r', encoding='utf-16-le', errors='ignore') as f:
            for line in f:
                if 'MOTOR_TASK' in line:
                    out.write(line.strip() + '\n')
                    count += 1
                    if count >= 30:
                        break

print("Search complete. Results saved to motor_log_results.txt")
