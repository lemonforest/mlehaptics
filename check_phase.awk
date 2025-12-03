BEGIN {
    print "Time(wall)    Dev A State    Dev B State    Phase Check"
    print "============================================================"
}

# Read both files, store activations by wall clock time
{
    # Extract wall clock time (HH:MM:SS.mmm) and state
    if (match($0, /([0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}).*MOTOR_TASK: (SERVER|CLIENT): Cycle starts (ACTIVE|INACTIVE)/, arr)) {
        time = arr[1]
        state = arr[3]
        
        if (FILENAME ~ /dev_a/) {
            a_state[time] = state
        } else {
            b_state[time] = state
        }
        times[time] = 1
    }
}

END {
    # Sort times and compare states
    n = asorti(times, sorted)
    
    in_phase = 0
    antiphase = 0
    
    for (i = 1; i <= n && i <= 50; i++) {
        t = sorted[i]
        a = (t in a_state) ? a_state[t] : "---"
        b = (t in b_state) ? b_state[t] : "---"
        
        # Determine phase relationship
        status = ""
        if (a == "ACTIVE" && b == "ACTIVE") {
            status = "IN-PHASE (ERROR!)"
            in_phase++
        } else if (a == "INACTIVE" && b == "INACTIVE") {
            status = "IN-PHASE (ERROR!)"
            in_phase++
        } else if (a != "---" && b != "---") {
            status = "ANTIPHASE (OK)"
            antiphase++
        }
        
        if (a != "---" || b != "---") {
            printf "%-13s %-14s %-14s %s\n", t, a, b, status
        }
    }
    
    print "\n============================================================"
    print "Summary:"
    print "  Antiphase (correct): " antiphase
    print "  In-phase (ERROR): " in_phase
    if (in_phase > 0) {
        print "\nCRITICAL: Devices are activating IN-PHASE!"
    }
}
