"""CLI smoke tests."""

from asm.cli import build_parser, main
from asm.output import write_bin, write_hex


def test_build_parser_help():
    parser = build_parser()
    help_text = parser.format_help()
    assert "RV32I" in help_text
    assert "-o" in help_text


def test_main_missing_file(tmp_path):
    code = main([str(tmp_path / "missing.asm")])
    assert code == 2


def test_main_not_implemented_yet(tmp_path):
    asm_file = tmp_path / "nop.asm"
    asm_file.write_text(".text\n", encoding="utf-8")
    code = main([str(asm_file), "-o", str(tmp_path / "out")])
    assert code == 1


def test_write_hex_and_bin(tmp_path):
    words = [0x00A00093, 0x00B00113]  # placeholder words
    bin_path = tmp_path / "t.bin"
    hex_path = tmp_path / "t.hex"
    write_bin(bin_path, words)
    write_hex(hex_path, words, base_address=0)
    assert bin_path.read_bytes() == bytes.fromhex("9300a0001301b000")
    assert "00000000: 00a00093" in hex_path.read_text(encoding="utf-8")
