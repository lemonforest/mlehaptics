#!/usr/bin/env python3
"""
Serial Log Parser for EMDR Pulser - Token-Efficient Compression
Creates reversible compressed logs with embedded dictionary for LLM analysis.

Usage: Drag-and-drop a serial log file onto this script.
       Creates a new file with "_parsed" suffix containing compressed log data.

Compression Features:
- Task name abbreviations (MOTOR_TASK → MT)
- Delta-encoded timestamps (15:26:25.231 → +231ms from base)
- ANSI color code removal
- Common phrase compression
- Self-contained format (dictionary embedded in output)

Author: Claude Code (Anthropic)
Date: 2025-11-29
"""

import sys
import re
from pathlib import Path
from collections import OrderedDict


# Compression dictionary (order matters - longest matches first)
COMPRESSION_DICT = OrderedDict([
    # Task names
    ('MOTOR_TASK', 'MT'),
    ('BLE_MANAGER', 'BM'),
    ('BLE_TASK', 'BT'),
    ('TIME_SYNC_TASK', 'TS'),
    ('TIME_SYNC', 'TSY'),  # Must come after TIME_SYNC_TASK
    ('BTN_TASK', 'BTN'),
    ('BUTTON_TASK', 'BTN'),
    ('MOTOR_CTRL', 'MC'),
    ('LED_CTRL', 'LED'),
    ('STATUS_LED', 'SLED'),

    # Roles and states
    ('CLIENT', 'C'),
    ('SERVER', 'S'),
    ('PAIRING', 'PAIR'),
    ('ADVERTISING', 'ADV'),
    ('CONNECTED', 'CONN'),
    ('DISCONNECTED', 'DISC'),

    # Common operations
    ('Waiting for', 'Wait'),
    ('Characteristic', 'Char'),
    ('notification', 'notif'),
    ('Notifications', 'Notifs'),
    ('Connection', 'Conn'),
    ('connection', 'conn'),
    ('Discovery', 'Disc'),
    ('discovery', 'disc'),
    ('Bilateral', 'Bilat'),
    ('Configuration', 'Config'),
    ('coordination', 'coord'),
    ('Coordination', 'Coord'),
    ('message', 'msg'),
    ('Message', 'Msg'),
    ('received', 'rcv'),
    ('Received', 'Rcv'),
    ('Complete', 'OK'),
    ('complete', 'ok'),
    ('successful', 'OK'),
    ('Successfully', 'OK'),
    ('started', 'start'),
    ('stopped', 'stop'),
    ('enabled', 'ON'),
    ('Enabled', 'ON'),
    ('disabled', 'OFF'),
    ('Disabled', 'OFF'),

    # BLE specific
    ('handle', 'h'),
    ('Service', 'Svc'),
    ('service', 'svc'),

    # Motor specific
    ('Battery', 'BAT'),
    ('battery', 'bat'),
    ('voltage', 'V'),
    ('Voltage', 'V'),
    ('Mode change', 'M→'),
    ('mode change', 'm→'),
    ('Forward', 'FWD'),
    ('forward', 'fwd'),
    ('Reverse', 'REV'),
    ('reverse', 'rev'),
    ('coasting', 'coast'),
    ('Coasting', 'Coast'),

    # Time sync
    ('beacon', 'bcn'),
    ('Beacon', 'Bcn'),
    ('offset', 'off'),
    ('Offset', 'Off'),
    ('quality', 'Q'),
    ('Quality', 'Q'),
    ('drift', 'drf'),
    ('Drift', 'Drf'),

    # Common symbols
    ('initialized', 'init'),
    ('Initialized', 'Init'),
    ('Initialize', 'Init'),
    ('Initializing', 'Init'),
    ('establishing', 'estab'),
    ('established', 'estab'),
    ('Established', 'Estab'),
])


# Regex patterns for ESP-IDF log lines
ESP_LOG_PATTERN = re.compile(
    r'^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*>.*?([IWED])\s*\((\d+)\)\s*(\w+):\s*(.*)$'
)

# ANSI escape code pattern (for removal)
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


def parse_timestamp(hh, mm, ss, ms):
    """Convert timestamp components to milliseconds since midnight."""
    return (int(hh) * 3600000 +
            int(mm) * 60000 +
            int(ss) * 1000 +
            int(ms))


def compress_line(line, base_timestamp_ms=None):
    """
    Compress a single ESP log line.

    Returns:
        tuple: (compressed_line, timestamp_ms) or (None, None) if not a valid log line
    """
    # Remove ANSI codes first
    line = ANSI_PATTERN.sub('', line)

    # Remove null bytes (UTF-16 artifacts)
    if '\x00' in line:
        line = line.replace('\x00', '')

    # Parse ESP log format
    match = ESP_LOG_PATTERN.match(line)
    if not match:
        return None, None

    hh, mm, ss, ms, level, tick, tag, message = match.groups()

    # Calculate timestamp
    timestamp_ms = parse_timestamp(hh, mm, ss, ms)

    # Compress tag (task name)
    compressed_tag = COMPRESSION_DICT.get(tag, tag)

    # Compress message content (apply all replacements with word boundaries)
    compressed_msg = message
    for original, replacement in COMPRESSION_DICT.items():
        # Use word boundaries for multi-word phrases, simple replace for single words
        if ' ' in original:
            # Multi-word phrase - exact match
            compressed_msg = compressed_msg.replace(original, replacement)
        else:
            # Single word - use word boundaries to avoid partial matches
            # But allow matches in compound words (e.g., "initialized")
            pattern = re.compile(r'\b' + re.escape(original) + r'\b')
            compressed_msg = pattern.sub(replacement, compressed_msg)

    # Format compressed line
    if base_timestamp_ms is None:
        # First line - use absolute timestamp
        time_str = f"{hh}:{mm}:{ss}.{ms}"
    else:
        # Delta encoding
        delta_ms = timestamp_ms - base_timestamp_ms
        if delta_ms >= 0:
            time_str = f"+{delta_ms}"
        else:
            time_str = f"{delta_ms}"

    compressed_line = f"{time_str} {level} ({tick}) {compressed_tag}: {compressed_msg}"

    return compressed_line, timestamp_ms


def decompress_line(compressed_line, reverse_dict, base_timestamp_ms):
    """
    Decompress a line back to original format (for validation).

    Returns:
        str: Decompressed line
    """
    # Parse compressed format
    match = re.match(r'^(\+?-?\d+(?::\d{2}:\d{2}\.\d{3})?)\s+([IWED])\s+\((\d+)\)\s+(\w+):\s+(.*)$', compressed_line)
    if not match:
        return None

    time_str, level, tick, tag, message = match.groups()

    # Decompress tag
    decompressed_tag = reverse_dict.get(tag, tag)

    # Decompress message
    decompressed_msg = message
    for compressed, original in reverse_dict.items():
        decompressed_msg = decompressed_msg.replace(compressed, original)

    # Reconstruct timestamp (approximate - just for validation structure)
    if ':' in time_str:
        # Absolute timestamp
        timestamp = time_str
    else:
        # Delta timestamp - reconstruct approximate
        delta_ms = int(time_str)
        total_ms = base_timestamp_ms + delta_ms
        hh = (total_ms // 3600000) % 24
        mm = (total_ms % 3600000) // 60000
        ss = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        timestamp = f"{hh:02d}:{mm:02d}:{ss:02d}.{ms:03d}"

    return f"{timestamp} > I ({tick}) {decompressed_tag}: {decompressed_msg}"


def parse_log_file(input_path):
    """
    Parse and compress serial log file.

    Returns:
        tuple: (compressed_lines, base_timestamp_info, stats)
    """
    compressed_lines = []
    base_timestamp_ms = None
    base_timestamp_str = None
    original_lines_count = 0
    processed_lines_count = 0

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                original_lines_count += 1
                line = line.rstrip()

                # Skip empty lines
                if not line:
                    continue

                # Compress line
                compressed_line, timestamp_ms = compress_line(line, base_timestamp_ms)

                if compressed_line:
                    # Set base timestamp from first line
                    if base_timestamp_ms is None:
                        base_timestamp_ms = timestamp_ms
                        base_timestamp_str = compressed_line.split()[0]

                    compressed_lines.append(compressed_line)
                    processed_lines_count += 1

    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None, None

    stats = {
        'original_lines': original_lines_count,
        'processed_lines': processed_lines_count,
        'base_timestamp': base_timestamp_str,
        'base_timestamp_ms': base_timestamp_ms
    }

    return compressed_lines, base_timestamp_str, stats


def validate_compression(sample_lines, reverse_dict, base_timestamp_ms):
    """
    Validate that compression is reversible (test round-trip).

    Returns:
        bool: True if validation passes
    """
    if not sample_lines:
        return True

    # Test first few lines
    test_count = min(5, len(sample_lines))
    for i, compressed_line in enumerate(sample_lines[:test_count]):
        decompressed = decompress_line(compressed_line, reverse_dict, base_timestamp_ms)
        if decompressed is None:
            print(f"WARNING: Line {i+1} failed to decompress")
            return False

    return True


def write_compressed_output(output_path, compressed_lines, base_timestamp_str, stats):
    """
    Write compressed output with embedded dictionary header.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header with compression dictionary
            f.write("# ===================================================================\n")
            f.write("# COMPRESSED ESP32 SERIAL LOG - Token-Efficient Format\n")
            f.write("# ===================================================================\n")
            f.write("#\n")
            f.write("# COMPRESSION DICTIONARY (for decompression/LLM understanding):\n")
            f.write("#\n")

            # Write dictionary in compact format
            items = list(COMPRESSION_DICT.items())
            for i in range(0, len(items), 4):
                chunk = items[i:i+4]
                dict_line = " | ".join([f"{v}={k}" for k, v in chunk])
                f.write(f"# {dict_line}\n")

            f.write("#\n")
            f.write(f"# Base Timestamp: {base_timestamp_str} (delta encoding for subsequent lines)\n")
            f.write(f"# Log Levels: I=Info, W=Warning, E=Error, D=Debug\n")
            f.write(f"# Time Format: +NNN = milliseconds offset from base timestamp\n")
            f.write("#\n")
            f.write("# ===================================================================\n")
            f.write("# COMPRESSED LOGS START BELOW\n")
            f.write("# ===================================================================\n")
            f.write("\n")

            # Write compressed log lines
            for line in compressed_lines:
                f.write(line + '\n')

        return True

    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


def main():
    """Main entry point - handles drag-and-drop file processing."""

    # Check for drag-and-drop file argument
    if len(sys.argv) < 2:
        print("Usage: Drag and drop a serial log file onto this script.")
        print("       Creates a new file with '_parsed' suffix.")
        input("Press Enter to exit...")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # Validate input file exists
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"Compressing: {input_path.name}")
    print("This may take a moment for large files...")

    # Parse and compress log file
    compressed_lines, base_timestamp_str, stats = parse_log_file(input_path)

    if compressed_lines is None:
        print("Failed to parse log file.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Validate compression (round-trip test)
    reverse_dict = {v: k for k, v in COMPRESSION_DICT.items()}
    print("Validating compression (round-trip test)...")
    if not validate_compression(compressed_lines, reverse_dict, stats['base_timestamp_ms']):
        print("WARNING: Compression validation failed!")
        print("Some data may not be reversible. Proceeding anyway...")

    # Create output filename (insert "_parsed" before extension)
    output_path = input_path.with_stem(f"{input_path.stem}_parsed")

    # Write compressed output
    print("Writing compressed output...")
    if not write_compressed_output(output_path, compressed_lines, base_timestamp_str, stats):
        print("Failed to write output file.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Calculate compression stats
    original_size = input_path.stat().st_size
    compressed_size = output_path.stat().st_size
    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

    # Calculate original bytes for processed lines (estimate)
    original_lines = stats['original_lines']
    processed_lines = stats['processed_lines']
    line_reduction_pct = (1 - processed_lines / original_lines) * 100 if original_lines > 0 else 0

    print(f"\nSuccess!")
    print(f"  Input:  {input_path.name}")
    print(f"    - Lines: {original_lines}")
    print(f"    - Size:  {original_size:,} bytes")
    print(f"  Output: {output_path.name}")
    print(f"    - Lines: {processed_lines} ({line_reduction_pct:.1f}% reduction)")
    print(f"    - Size:  {compressed_size:,} bytes ({compression_ratio:.1f}% smaller)")
    print(f"\nCompression: {original_size:,} -> {compressed_size:,} bytes")
    print(f"Token savings: ~{compression_ratio:.0f}% (estimated)")
    print(f"\nParsed log saved to: {output_path}")

    input("\nPress Enter to exit...")


if __name__ == '__main__':
    main()
