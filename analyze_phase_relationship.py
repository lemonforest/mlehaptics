#!/usr/bin/env python3
"""Analyze phase relationship between paired devices."""

import re
from datetime import datetime

def parse_log(filename):
    """Extract activation timestamps and role from log file."""
    activations = []
    device_role = None
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Extract role from connection logs
            if 'CLIENT role assigned' in line or 'SERVER role assigned' in line:
                if 'CLIENT' in line:
                    device_role = 'CLIENT'
                elif 'SERVER' in line:
                    device_role = 'SERVER'
            
            # Extract motor activations
            match = re.search(r'I \((\d+)\) MOTOR_TASK: (SERVER|CLIENT): Cycle starts (ACTIVE|INACTIVE)', line)
            if match:
                timestamp_ms = int(match.group(1))
                role = match.group(2)
                state = match.group(3)
                activations.append({
                    'timestamp_ms': timestamp_ms,
                    'role': role,
                    'state': state
                })
    
    return activations, device_role

def analyze_phase_relationship(log_a, log_b):
    """Compare activation timing between two devices."""
    act_a, role_a = parse_log(log_a)
    act_b, role_b = parse_log(log_b)
    
    print("=" * 70)
    print("Phase Relationship Analysis - Paired Devices")
    print("=" * 70)
    print(f"\nDevice A: {log_a}")
    print(f"  Role: {role_a}")
    print(f"  Activations: {len(act_a)}")
    print(f"\nDevice B: {log_b}")
    print(f"  Role: {role_b}")
    print(f"  Activations: {len(act_b)}")
    print()
    
    if len(act_a) == 0 or len(act_b) == 0:
        print("ERROR: No activations found in one or both logs")
        return
    
    # Find first 20 activations from each device
    print("-" * 70)
    print("First 20 Activations Comparison:")
    print("-" * 70)
    print(f"{'Time (s)':<10} {'Dev A State':<15} {'Dev B State':<15} {'Phase Diff (ms)':<18}")
    print("-" * 70)
    
    # Use Device A timestamps as reference
    for i in range(min(20, len(act_a))):
        time_a = act_a[i]['timestamp_ms']
        state_a = act_a[i]['state']
        
        # Find closest activation in Device B
        closest_b = min(act_b, key=lambda x: abs(x['timestamp_ms'] - time_a))
        time_b = closest_b['timestamp_ms']
        state_b = closest_b['state']
        
        phase_diff = time_b - time_a
        
        # Determine if in-phase or antiphase
        if state_a == state_b:
            phase_status = "IN-PHASE ⚠️"
        else:
            phase_status = "ANTIPHASE ✓"
        
        print(f"{time_a/1000:<10.1f} {state_a:<15} {state_b:<15} {phase_diff:>6} ms  {phase_status}")
    
    # Analyze ACTIVE state timing specifically
    print("\n" + "=" * 70)
    print("ACTIVE State Phase Analysis (First 50 cycles):")
    print("=" * 70)
    
    active_a = [a for a in act_a if a['state'] == 'ACTIVE'][:50]
    active_b = [a for a in act_b if a['state'] == 'ACTIVE'][:50]
    
    in_phase_count = 0
    antiphase_count = 0
    phase_errors = []
    
    for act in active_a:
        time_a = act['timestamp_ms']
        
        # Find any Device B ACTIVE within ±100ms
        nearby_b = [b for b in active_b if abs(b['timestamp_ms'] - time_a) < 100]
        
        if nearby_b:
            # Device B is ACTIVE at same time - IN-PHASE ERROR
            in_phase_count += 1
            closest = min(nearby_b, key=lambda x: abs(x['timestamp_ms'] - time_a))
            phase_errors.append({
                'time_s': time_a / 1000,
                'diff_ms': closest['timestamp_ms'] - time_a,
                'type': 'IN-PHASE'
            })
        else:
            antiphase_count += 1
    
    print(f"\nTotal ACTIVE cycles analyzed: {len(active_a)}")
    print(f"ANTIPHASE (correct): {antiphase_count} ({antiphase_count/len(active_a)*100:.1f}%)")
    print(f"IN-PHASE (ERROR): {in_phase_count} ({in_phase_count/len(active_a)*100:.1f}%)")
    
    if phase_errors:
        print(f"\n⚠️  CRITICAL: Devices are activating IN-PHASE!")
        print("\nFirst 10 IN-PHASE errors:")
        print(f"{'Time (s)':<10} {'Phase Diff (ms)':<18}")
        for err in phase_errors[:10]:
            print(f"{err['time_s']:<10.1f} {err['diff_ms']:>6} ms")
    else:
        print("\n✓ Devices are correctly in ANTIPHASE")
    
    # Check nominal 500ms offset (for 0.5Hz @ 50% phase offset)
    print("\n" + "=" * 70)
    print("Expected Phase Offset Analysis:")
    print("=" * 70)
    print("At 0.5 Hz (2000ms cycle), antiphase = 1000ms offset")
    print("Device A ACTIVE at T=0ms → Device B should be ACTIVE at T=1000ms")
    
    if len(active_a) > 0 and len(active_b) > 0:
        # Calculate actual phase offset
        first_a = active_a[0]['timestamp_ms']
        first_b = active_b[0]['timestamp_ms']
        actual_offset = abs(first_b - first_a)
        
        print(f"\nActual offset: {actual_offset} ms")
        print(f"Expected: ~1000 ms (for antiphase at 0.5 Hz)")
        
        if actual_offset < 100:
            print(f"⚠️  CRITICAL: Offset is {actual_offset}ms - devices are IN-PHASE!")
        elif 900 <= actual_offset <= 1100:
            print(f"✓ Offset is {actual_offset}ms - correct antiphase")
        else:
            print(f"⚠️  Offset is {actual_offset}ms - unexpected phase relationship")

if __name__ == '__main__':
    analyze_phase_relationship('serial_log_dev_a_0841-20251202.txt', 
                               'serial_log_dev_b_0841-20251202.txt')
