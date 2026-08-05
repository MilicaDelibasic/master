# Example: word in .data and load/store (scaffold sample)

.data
value:
    .word 42

.text
    la   t0, value      # may become auipc+addi pseudo later
    lw   t1, 0(t0)
    addi t1, t1, 1
    sw   t1, 0(t0)
