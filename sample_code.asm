        ADDI    X9, XZR, #0     // X9 = 0 (sum)
        ADDI    X10, XZR, #1    // X10 = 1 (i = 1)

loop:   
        ADD     X9, X9, X10     // sum += i
        ADDI    X10, X10, #1    // i += 1
        SUBI    X11, X10, #4    // X11 = i - 4
        CBNZ    X11, loop       // if X11 != 0 (i < 4), continue loop

        // After loop, sum (1+2+3=6) is stored in X9
