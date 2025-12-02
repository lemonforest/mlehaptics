BEGIN {
    print "Wall Time    Dev A (SERVER)    Dev B (CLIENT)    Phase Check"
    print "=================================================================="
}

{
    if (match($0, /([0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}).*MOTOR_TASK: (SERVER|CLIENT): Cycle starts (ACTIVE|INACTIVE)/, arr)) {
        time = arr[1]
        role = arr[2]
        state = arr[3]
        
        if (FILENAME ~ /dev_a/) {
            a_state[time] = state
            a_role = role
        } else {
            b_state[time] = state  
            b_role = role
        }
        times[time] = 1
    }
}

END {
    n = asorti(times, sorted)
    
    for (i = 1; i <= n && i <= 100; i++) {
        t = sorted[i]
        a = (t in a_state) ? a_state[t] : "---"
        b = (t in b_state) ? b_state[t] : "---"
        
        if (a != "---" || b != "---") {
            # Calculate phase relationship
            status = ""
            if (a == "ACTIVE" && b == "ACTIVE") {
                status = "IN-PHASE (ERROR!)"
            } else if (a == "INACTIVE" && b == "INACTIVE") {
                status = "IN-PHASE (ERROR!)"
            } else if (a == "ACTIVE" && b == "INACTIVE") {
                status = "ANTIPHASE (OK)"
            } else if (a == "INACTIVE" && b == "ACTIVE") {
                status = "ANTIPHASE (OK)"
            }
            
            printf "%-13s %-17s %-17s %s\n", t, a, b, status
        }
    }
}
