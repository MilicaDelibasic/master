# Master rad — asemblerski prevodilac

Dizajn i implementacija jednostavnog asemblerskog prevodioca za prostu arhitekturu (RISC-V RV32I subset).

| | |
|--|--|
| Teza | srpski (Crna Gora), latinica |
| Implementacija | Python 3.12 |
| Remote | `git@github.com:MilicaDelibasic/master.git` |

## Struktura (cilj)

- `src/asm/` — asembler
- `examples/` — ulazni `.asm` programi
- `tests/` — pytest
- `docs/thesis/` — LaTeX izvor teze
- `plans/` — lokalni planovi (nije u gitu)
- `upustvo/` — literatura i smjernice (nije u gitu)

## Brzi start (kasnije)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
python -m asm examples\add.asm -o out\
```

Detaljni plan i LaTeX setup su u lokalnom folderu `plans/` (gitignored).
