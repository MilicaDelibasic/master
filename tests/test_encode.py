"""encode_r bit-packing helpers (usable before full encode_instruction)."""

from asm.encode import encode_r


def test_encode_r_add_x3_x1_x2():
    # add x3, x1, x2 → opcode=0x33, funct3=0, funct7=0, rd=3, rs1=1, rs2=2
    word = encode_r(opcode=0x33, rd=3, funct3=0, rs1=1, rs2=2, funct7=0)
    assert word == 0x002081B3
