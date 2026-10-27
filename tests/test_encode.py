"""Instruction encoding tests: bit layouts, known words and range checks."""

import pytest

from asm.encode import (
    encode,
    encode_b,
    encode_i,
    encode_j,
    encode_r,
    encode_s,
    encode_u,
    split_hi_lo,
)
from asm.errors import SemanticError, SourceLocation
from asm.isa import INSTRUCTIONS, register_number

LOC = SourceLocation("t.asm", 7, 5)


def enc(mnemonic, **fields):
    """Encode by mnemonic with register names, e.g. enc("add", rd="x3", ...)."""
    regs = {k: register_number(v) for k, v in fields.items() if k in ("rd", "rs1", "rs2")}
    other = {k: v for k, v in fields.items() if k not in ("rd", "rs1", "rs2")}
    return encode(INSTRUCTIONS[mnemonic], **regs, **other)


# -- independent decoders (used to check the scrambled B/J layouts) -----------


def sign_extend(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def decode_b_offset(word):
    imm = (
        ((word >> 31) & 0x1) << 12
        | ((word >> 7) & 0x1) << 11
        | ((word >> 25) & 0x3F) << 5
        | ((word >> 8) & 0xF) << 1
    )
    return sign_extend(imm, 13)


def decode_j_offset(word):
    imm = (
        ((word >> 31) & 0x1) << 20
        | ((word >> 12) & 0xFF) << 12
        | ((word >> 20) & 0x1) << 11
        | ((word >> 21) & 0x3FF) << 1
    )
    return sign_extend(imm, 21)


# -- known machine words -----------------------------------------------------
# Computed by hand from the spec field layouts (and independently by a
# separate script for the docs/softversko-rjesenje.md examples).


@pytest.mark.parametrize(
    ("source", "fields", "word"),
    [
        # R
        ("add x3, x1, x2", dict(rd="x3", rs1="x1", rs2="x2"), 0x002081B3),
        # I: arithmetic (incl. negative immediate and the canonical nop)
        ("addi x1, x0, 5", dict(rd="x1", rs1="x0", imm=5), 0x00500093),
        ("addi t1, x0, 10", dict(rd="t1", rs1="x0", imm=10), 0x00A00313),
        ("addi a0, a0, -1", dict(rd="a0", rs1="a0", imm=-1), 0xFFF50513),
        ("addi x0, x0, 0  (nop)", dict(rd="x0", rs1="x0", imm=0), 0x00000013),
        # I: shifts
        ("slli t0, t0, 3", dict(rd="t0", rs1="t0", imm=3), 0x00329293),
        ("srai x1, x1, 3", dict(rd="x1", rs1="x1", imm=3), 0x4030D093),
        # I: load and jalr
        ("lw t1, 0(t0)", dict(rd="t1", rs1="t0", imm=0), 0x0002A303),
        ("jalr x0, 0(ra)  (ret)", dict(rd="x0", rs1="ra", imm=0), 0x00008067),
        # S
        ("sw t1, 0(t0)", dict(rs1="t0", rs2="t1", imm=0), 0x0062A023),
        ("sw t1, -4(sp)", dict(rs1="sp", rs2="t1", imm=-4), 0xFE612E23),
        # B
        ("blt t0, t1, -4", dict(rs1="t0", rs2="t1", imm=-4), 0xFE62CEE3),
        ("beq x0, x0, 0", dict(rs1="x0", rs2="x0", imm=0), 0x00000063),
        # U
        ("lui a0, 0x12345", dict(rd="a0", imm=0x12345), 0x12345537),
        ("auipc t0, 0x10000", dict(rd="t0", imm=0x10000), 0x10000297),
        # J
        ("jal x0, -8  (j)", dict(rd="x0", imm=-8), 0xFF9FF06F),
    ],
)
def test_known_words(source, fields, word):
    mnemonic = source.split()[0]
    assert enc(mnemonic, **fields) == word


def test_encode_r_matches_spec_layout():
    # add x3, x1, x2 → opcode=0x33, funct3=0, funct7=0, rd=3, rs1=1, rs2=2
    assert encode_r(opcode=0x33, rd=3, funct3=0, rs1=1, rs2=2, funct7=0) == 0x002081B3


def test_examples_from_docs():
    # docs/softversko-rjesenje.md, section 5 (loop.asm) and memory.asm
    loop = [
        enc("addi", rd="t0", rs1="x0", imm=0),
        enc("addi", rd="t1", rs1="x0", imm=10),
        enc("addi", rd="t0", rs1="t0", imm=1),
        enc("blt", rs1="t0", rs2="t1", imm=0x08 - 0x0C),
    ]
    assert loop == [0x00000293, 0x00A00313, 0x00128293, 0xFE62CEE3]

    hi, lo = split_hi_lo(0x10000000 - 0x0)  # la t0, value (value at 0x1000_0000, pc 0)
    memory = [
        enc("auipc", rd="t0", imm=hi),
        enc("addi", rd="t0", rs1="t0", imm=lo),
        enc("lw", rd="t1", rs1="t0", imm=0),
        enc("addi", rd="t1", rs1="t1", imm=1),
        enc("sw", rs1="t0", rs2="t1", imm=0),
    ]
    assert memory == [0x10000297, 0x00028293, 0x0002A303, 0x00130313, 0x0062A023]


# -- field placement ------------------------------------------------------------


@pytest.mark.parametrize("imm", [-2048, -1, 0, 1, 0x7FF])
def test_i_immediate_lands_in_top_12_bits(imm):
    word = encode_i(0x13, 1, 0, 2, imm)
    assert sign_extend(word >> 20, 12) == imm
    assert (word >> 15) & 0x1F == 2 and (word >> 7) & 0x1F == 1


@pytest.mark.parametrize("imm", [-2048, -4, 0, 31, 32, 2047])
def test_s_immediate_is_split(imm):
    word = encode_s(0x23, 2, 3, 4, imm)
    low = (word >> 7) & 0x1F
    high = (word >> 25) & 0x7F
    assert sign_extend(high << 5 | low, 12) == imm


def test_every_branch_offset_roundtrips():
    for offset in range(-4096, 4096, 2):
        assert decode_b_offset(encode_b(0x63, 0, 5, 6, offset)) == offset


@pytest.mark.parametrize("offset", [-1048576, -2048, -8, -2, 0, 2, 2046, 2048, 4096, 1048574])
def test_jump_offsets_roundtrip(offset):
    assert decode_j_offset(encode_j(0x6F, 1, offset)) == offset


def test_jump_offsets_roundtrip_sweep():
    for offset in range(-1048576, 1048576, 4094):  # step hits every bit group
        offset -= offset % 2
        assert decode_j_offset(encode_j(0x6F, 0, offset)) == offset


def test_shift_funct7_goes_to_top_bits():
    srli = enc("srli", rd="x1", rs1="x1", imm=31)
    srai = enc("srai", rd="x1", rs1="x1", imm=31)
    assert srli >> 25 == 0b0000000
    assert srai >> 25 == 0b0100000
    assert (srai >> 20) & 0x1F == 31


# -- range checks ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("mnemonic", "fields", "message"),
    [
        ("addi", dict(rd="x1", rs1="x0", imm=2048), "immediate 2048 out of range (-2048..2047)"),
        ("addi", dict(rd="x1", rs1="x0", imm=-2049), "immediate -2049 out of range"),
        ("lw", dict(rd="x1", rs1="sp", imm=5000), "immediate 5000 out of range"),
        ("sw", dict(rs1="sp", rs2="x1", imm=-3000), "offset -3000 out of range"),
        ("slli", dict(rd="x1", rs1="x1", imm=32), "shift amount 32 out of range (0..31)"),
        ("srai", dict(rd="x1", rs1="x1", imm=-1), "shift amount -1 out of range"),
        ("beq", dict(rs1="x0", rs2="x0", imm=4096), "branch offset 4096 out of range (-4096..4095)"),
        ("bne", dict(rs1="x0", rs2="x0", imm=-4098), "branch offset -4098 out of range"),
        ("beq", dict(rs1="x0", rs2="x0", imm=3), "branch offset 3 is not a multiple of 2"),
        ("jal", dict(rd="ra", imm=1048576), "jump offset 1048576 out of range"),
        ("jal", dict(rd="ra", imm=-7), "jump offset -7 is not a multiple of 2"),
        ("lui", dict(rd="x1", imm=0x100000), "upper immediate 1048576 out of range (0..1048575)"),
        ("auipc", dict(rd="x1", imm=-1), "upper immediate -1 out of range"),
    ],
)
def test_out_of_range_immediates(mnemonic, fields, message):
    with pytest.raises(SemanticError) as info:
        enc(mnemonic, location=LOC, **fields)
    assert message in str(info.value)
    assert info.value.location == LOC
    assert str(info.value).startswith("t.asm:7:5: semantic error:")


@pytest.mark.parametrize(
    ("mnemonic", "fields"),
    [
        ("addi", dict(rd="x1", rs1="x0", imm=-2048)),
        ("addi", dict(rd="x1", rs1="x0", imm=2047)),
        ("beq", dict(rs1="x0", rs2="x0", imm=-4096)),
        ("beq", dict(rs1="x0", rs2="x0", imm=4094)),
        ("jal", dict(rd="x0", imm=-1048576)),
        ("jal", dict(rd="x0", imm=1048574)),
        ("lui", dict(rd="x1", imm=0xFFFFF)),
        ("slli", dict(rd="x1", rs1="x1", imm=0)),
    ],
)
def test_boundary_values_are_accepted(mnemonic, fields):
    enc(mnemonic, **fields)


@pytest.mark.parametrize("reg", [-1, 32])
def test_bad_register_number_is_a_programming_error(reg):
    with pytest.raises(ValueError):
        encode_i(0x13, reg, 0, 0, 0)


# -- hi/lo split for li / la -------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "hi", "lo"),
    [
        (0, 0, 0),
        (0x10000000, 0x10000, 0),
        (0x12345678, 0x12345, 0x678),
        (0x12345FFF, 0x12346, -1),  # bit 11 set → hi rounded up, lo negative
        (0x00000800, 0x1, -2048),
        (0x000007FF, 0x0, 2047),
        (-1, 0x0, -1),
        (0xFFFFFFFF, 0x0, -1),
        (-0x80000000, 0x80000, 0),
    ],
)
def test_split_hi_lo(value, hi, lo):
    assert split_hi_lo(value) == (hi, lo)


@pytest.mark.parametrize("value", [0, 1, 2047, 2048, 0x7FFFFFFF, 0x80000000, 0xDEADBEEF, -5, -2049])
def test_split_hi_lo_reconstructs_value(value):
    hi, lo = split_hi_lo(value)
    assert -2048 <= lo <= 2047
    assert ((hi << 12) + lo) & 0xFFFFFFFF == value & 0xFFFFFFFF


@pytest.mark.parametrize("value", [0x100000000, -0x80000001])
def test_split_hi_lo_rejects_values_wider_than_32_bits(value):
    with pytest.raises(SemanticError, match="does not fit in 32 bits"):
        split_hi_lo(value, location=LOC)
