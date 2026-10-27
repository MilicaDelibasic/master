"""Instruction table and register map tests."""

import pytest

from asm.encode import encode_r
from asm.isa import (
    ABI_NAMES,
    INSTRUCTIONS,
    REGISTERS,
    Format,
    Syntax,
    lookup_instruction,
    register_number,
)

# -- instruction table ----------------------------------------------------

# Planned subset (docs/softversko-rjesenje.md, section 3.2) — must all exist.
PLANNED = {
    Format.R: "add sub and or xor sll srl sra slt sltu",
    Format.I: "addi andi ori xori slti sltiu slli srli srai lw lb lh lbu lhu jalr",
    Format.S: "sw sb sh",
    Format.B: "beq bne blt bge bltu bgeu",
    Format.U: "lui auipc",
    Format.J: "jal",
}


@pytest.mark.parametrize("fmt", list(PLANNED))
def test_planned_instructions_exist_with_right_format(fmt):
    for mnemonic in PLANNED[fmt].split():
        spec = lookup_instruction(mnemonic)
        assert spec is not None, mnemonic
        assert spec.format is fmt, mnemonic


def test_table_has_exactly_the_planned_instructions():
    planned = {m for names in PLANNED.values() for m in names.split()}
    assert set(INSTRUCTIONS) == planned


def test_mnemonic_lookup_is_case_insensitive():
    assert lookup_instruction("ADDI") is lookup_instruction("addi")


@pytest.mark.parametrize("name", ["li", "la", "nop", "mv", "j", "ret", "mul", "foo", ""])
def test_pseudo_and_unknown_are_not_real_instructions(name):
    assert lookup_instruction(name) is None


def test_fields_fit_their_bit_widths():
    for spec in INSTRUCTIONS.values():
        assert 0 <= spec.opcode < 2**7
        assert spec.opcode & 0b11 == 0b11, spec.mnemonic  # 32-bit encodings end in 11
        if spec.funct3 is not None:
            assert 0 <= spec.funct3 < 2**3
        if spec.funct7 is not None:
            assert 0 <= spec.funct7 < 2**7


@pytest.mark.parametrize(
    ("fmt", "has_funct3"),
    [(Format.R, True), (Format.I, True), (Format.S, True), (Format.B, True),
     (Format.U, False), (Format.J, False)],
)
def test_funct3_present_exactly_where_format_has_it(fmt, has_funct3):
    for spec in INSTRUCTIONS.values():
        if spec.format is fmt:
            assert (spec.funct3 is not None) == has_funct3, spec.mnemonic


def test_funct7_only_on_r_type_and_shift_immediates():
    for spec in INSTRUCTIONS.values():
        expected = spec.format is Format.R or spec.syntax is Syntax.RD_RS1_SHAMT
        assert (spec.funct7 is not None) == expected, spec.mnemonic


def test_encodings_are_unique():
    # (opcode, funct3, funct7) must identify exactly one instruction,
    # otherwise a disassembler could not tell them apart.
    keys = [(s.opcode, s.funct3, s.funct7) for s in INSTRUCTIONS.values()]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize(
    ("mnemonic", "opcode", "funct3", "funct7"),
    [
        # spot checks against RISC-V spec, chapter 24 (RV32I base opcode map)
        ("sub", 0b0110011, 0b000, 0b0100000),
        ("sra", 0b0110011, 0b101, 0b0100000),
        ("srai", 0b0010011, 0b101, 0b0100000),
        ("lw", 0b0000011, 0b010, None),
        ("lbu", 0b0000011, 0b100, None),
        ("jalr", 0b1100111, 0b000, None),
        ("sw", 0b0100011, 0b010, None),
        ("bgeu", 0b1100011, 0b111, None),
        ("auipc", 0b0010111, None, None),
        ("jal", 0b1101111, None, None),
    ],
)
def test_known_field_values(mnemonic, opcode, funct3, funct7):
    spec = INSTRUCTIONS[mnemonic]
    assert (spec.opcode, spec.funct3, spec.funct7) == (opcode, funct3, funct7)


@pytest.mark.parametrize(
    ("mnemonic", "word"),
    [
        # rd=x3, rs1=x1, rs2=x2; words computed by hand from the spec field layout
        ("add", 0x002081B3),
        ("sub", 0x402081B3),
        ("and", 0x0020F1B3),
        ("or", 0x0020E1B3),
        ("sra", 0x4020D1B3),
    ],
)
def test_r_type_table_entries_encode_to_known_words(mnemonic, word):
    spec = INSTRUCTIONS[mnemonic]
    assert encode_r(spec.opcode, 3, spec.funct3, 1, 2, spec.funct7) == word


@pytest.mark.parametrize(
    ("syntax", "count"),
    [(Syntax.RD_RS1_RS2, 3), (Syntax.RD_MEM, 2), (Syntax.RS1_RS2_LABEL, 3),
     (Syntax.RD_IMM20, 2), (Syntax.RD_LABEL, 2)],
)
def test_operand_count(syntax, count):
    assert syntax.operand_count == count


# -- registers --------------------------------------------------------------


def test_numeric_register_names():
    for n in range(32):
        assert register_number(f"x{n}") == n


@pytest.mark.parametrize(
    ("name", "number"),
    [("zero", 0), ("ra", 1), ("sp", 2), ("gp", 3), ("tp", 4),
     ("t0", 5), ("t2", 7), ("s0", 8), ("fp", 8), ("s1", 9),
     ("a0", 10), ("a7", 17), ("s2", 18), ("s11", 27), ("t3", 28), ("t6", 31)],
)
def test_abi_register_names(name, number):
    assert register_number(name) == number


def test_every_register_has_one_abi_name():
    assert len(ABI_NAMES) == 32
    assert len(set(ABI_NAMES)) == 32


def test_register_lookup_is_case_insensitive():
    assert register_number("T0") == 5
    assert register_number("X31") == 31


@pytest.mark.parametrize("name", ["x32", "x-1", "t7", "s12", "a8", "r1", "", "loop"])
def test_unknown_registers(name):
    assert register_number(name) is None


def test_register_map_size():
    # 32 numeric + 32 ABI + fp
    assert len(REGISTERS) == 65
