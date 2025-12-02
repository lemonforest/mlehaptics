#!/usr/bin/env python3
"""Check for CORRECTION COMPARE logs in CLIENT serial output."""

import sys

with open('correction_search_results.txt', 'w', encoding='utf-8') as out:
    with open('serial_log_dev_b_1747-20251201.txt', 'r', encoding='utf-16-le', errors='ignore') as f:
        count = 0
        for line in f:
            if 'CORRECTION COMPARE' in line or 'correction' in line.lower():
                out.write(line.strip() + '\n')
                count += 1
                if count >= 30:
                    break

        if count == 0:
            out.write("No CORRECTION COMPARE logs found in CLIENT log.\n")
            out.write("\nSearching for RTT-related logs instead...\n\n")

    with open('serial_log_dev_b_1747-20251201.txt', 'r', encoding='utf-16-le', errors='ignore') as f:
        count = 0
        for line in f:
            if 'RTT measured' in line:
                out.write(line.strip() + '\n')
                count += 1
                if count >= 10:
                    break

print("Search complete. Results saved to correction_search_results.txt")
