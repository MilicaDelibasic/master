# Example: simple counted loop (scaffold sample)

.text
    addi t0, x0, 0
    addi t1, x0, 10
loop:
    addi t0, t0, 1
    blt  t0, t1, loop
    # done
