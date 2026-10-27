# Softversko rješenje: algoritam i plan implementacije

Dvoprolazni asembler za podskup RISC-V arhitekture (RV32I), napisan u Python-u 3.12.

> **Stanje (27. 10. 2026.):** urađeni su kostur paketa, komandna linija, tabela simbola,
> zapis izlaznih fajlova, **leksički analizator**, **tabela instrukcija i registara** i
> **kodiranje svih šest formata** sa provjerom opsega (217 testova prolazi). Parser i oba
> prolaza još nisu napisani — to je plan iz odjeljka 7.

---

## 1. Ukratko — šta asembler radi

Asembler čita tekstualni program na asemblerskom jeziku i pretvara ga u **mašinski kod**:
niz 32-bitnih brojeva koje procesor direktno izvršava.

```
ulaz: loop.asm                          izlaz: loop.hex
--------------------------------        ------------------------
    addi t0, x0, 0                      00000000: 00000293
    addi t1, x0, 10                     00000004: 00a00313
loop:                                   00000008: 00128293
    addi t0, t0, 1                      0000000c: fe62cee3
    blt  t0, t1, loop
```

Svaka instrukcija postaje tačno jedna 32-bitna riječ (osim pseudo-instrukcija, koje mogu
postati dvije). Labela `loop` ne zauzima prostor — ona je samo ime za adresu `0x08`.

**Glavni problem koji asembler rješava su reference unaprijed:** instrukcija može koristiti
labelu koja je definisana *kasnije* u programu (npr. `beq t0, t1, kraj`, a `kraj:` je na
kraju). U trenutku čitanja te instrukcije adresa labele još nije poznata. Zato asembler
prolazi kroz program **dva puta**:

1. **prvi prolaz** — samo računa adrese i pamti gdje je koja labela (tabela simbola);
2. **drugi prolaz** — prevodi instrukcije u mašinski kod, sada kad su sve adrese poznate.

---

## 2. Arhitektura rješenja

```
 izvorni .asm
      │
      ▼
┌────────────┐  tokeni      ┌────────────┐  stavke programa   ┌──────────────┐
│   Lexer    │────────────▶ │   Parser   │──────────────────▶ │ Prvi prolaz  │
│ lexer.py ✅│              │ parser.py  │  (labele,          │ adrese +     │
└────────────┘              └────────────┘   direktive,       │ tabela simb. │
                                             instrukcije)     └──────┬───────┘
                                                                     │ tabela simbola
                                                                     ▼
 .bin / .hex   ┌────────────┐   riječi i bajtovi   ┌──────────────────────────┐
 ◀─────────────│   Izlaz    │◀──────────────────── │ Drugi prolaz             │
               │ output.py ✅│                      │ kodiranje (encode.py)    │
               └────────────┘                      └──────────────────────────┘
```

| Modul | Odgovornost | Stanje |
|---|---|---|
| `tokens.py` | vrste tokena (`IDENT`, `DIRECTIVE`, `INTEGER`, `STRING`, `,` `:` `(` `)`, `NEWLINE`, `EOF`) | ✅ |
| `lexer.py` | tekst → tokeni, sa linijom i kolonom svakog tokena | ✅ |
| `ast_nodes.py` | stavke programa: `LabelDef`, `Directive`, `Instruction` | ✅ (tipovi) |
| `parser.py` | tokeni → lista stavki programa | ⏳ |
| `symbols.py` | tabela simbola (definiši, pronađi, prijavi duplikat/nedefinisanu labelu) | ✅ |
| `isa.py` | tabela instrukcija: format, opcode, funct3, funct7, oblik operanada; mapa registara | ✅ |
| `encode.py` | pakovanje polja u 32-bitnu riječ za formate R, I, S, B, U, J; provjera opsega; `hi`/`lo` podjela | ✅ |
| `directives.py` | značenje direktiva (`.text`, `.data`, `.word`, …) | ⏳ |
| `assembler.py` | povezuje sve: parser → prvi prolaz → drugi prolaz | ⏳ |
| `output.py` | zapis `.bin` (little-endian) i `.hex` | ✅ |
| `errors.py` | greške sa lokacijom `fajl:linija:kolona: vrsta: poruka` | ✅ |
| `cli.py` | komandna linija `python -m asm ulaz.asm -o out/` | ✅ |

---

## 3. Šta asembler prihvata (ulazni jezik)

### 3.1. Gramatika (EBNF)

```ebnf
program     = { line } EOF ;
line        = [ label ] [ statement ] NEWLINE ;
label       = IDENT ":" ;
statement   = directive | instruction ;
directive   = DIRECTIVE [ operands ] ;
instruction = IDENT [ operands ] ;
operands    = operand { "," operand } ;
operand     = register | INTEGER | IDENT | STRING | memory ;
memory      = [ INTEGER ] "(" register ")" ;      (* npr. 8(sp) ili (sp) *)
register    = IDENT ;                              (* x0..x31 ili ABI ime *)
```

### 3.2. Podržane instrukcije (podskup RV32I)

| Format | Instrukcije | Oblik u asembleru |
|---|---|---|
| R | `add sub and or xor sll srl sra slt sltu` | `add rd, rs1, rs2` |
| I (aritmetika) | `addi andi ori xori slti sltiu` | `addi rd, rs1, imm` |
| I (pomjeranje) | `slli srli srai` | `slli rd, rs1, shamt` |
| I (učitavanje) | `lw` (opciono `lb lh lbu lhu`) | `lw rd, imm(rs1)` |
| I (skok) | `jalr` | `jalr rd, imm(rs1)` |
| S | `sw` (opciono `sb sh`) | `sw rs2, imm(rs1)` |
| B | `beq bne blt bge bltu bgeu` | `beq rs1, rs2, labela` |
| U | `lui auipc` | `lui rd, imm20` |
| J | `jal` | `jal rd, labela` |

Ukupno 37 instrukcija; tabela je u `src/asm/isa.py`, a tabela opkodova u prilogu teze
(Prilog 3) generisana je iz nje. Registri: `x0`–`x31` i ABI imena
(`zero ra sp gp tp t0–t6 s0–s11 a0–a7`, kao i `fp` = `s0`).

### 3.3. Pseudo-instrukcije

Pseudo-instrukcija nije prava instrukcija procesora — asembler je zamjenjuje sa jednom ili
dvije prave:

| Pseudo | Zamjena | Riječi |
|---|---|---|
| `nop` | `addi x0, x0, 0` | 1 |
| `mv rd, rs` | `addi rd, rs, 0` | 1 |
| `not rd, rs` | `xori rd, rs, -1` | 1 |
| `j labela` | `jal x0, labela` | 1 |
| `ret` | `jalr x0, 0(ra)` | 1 |
| `li rd, imm` (−2048 ≤ imm ≤ 2047) | `addi rd, x0, imm` | 1 |
| `li rd, imm` (ostale vrijednosti) | `lui rd, hi` + `addi rd, rd, lo` | 2 |
| `la rd, labela` | `auipc rd, hi` + `addi rd, rd, lo` | 2 (uvijek) |

**Važno za prvi prolaz:** veličina svake pseudo-instrukcije mora biti poznata *bez* znanja
adresa labela. Kod `li` vrijednost je broj u samom tekstu, pa je veličina poznata odmah;
`la` je uvijek 2 riječi. Zato prvi prolaz može tačno izračunati sve adrese.

### 3.4. Direktive

| Direktiva | Značenje | Zauzima |
|---|---|---|
| `.text` | dalje slijedi kod | — |
| `.data` | dalje slijede podaci | — |
| `.word v1, v2, …` | 32-bitne vrijednosti (broj ili labela) | 4 bajta po vrijednosti, poravnato na 4 |
| `.byte v1, v2, …` | 8-bitne vrijednosti | 1 bajt po vrijednosti |
| `.ascii "tekst"` | bajtovi teksta | dužina teksta |
| `.asciiz "tekst"` | tekst + nula na kraju | dužina + 1 |
| `.space n` | n bajtova nula | n bajtova |

**Raspored memorije:** `.text` počinje na adresi `0x0000_0000`, a `.data` na `0x1000_0000`
(obje vrijednosti su konstante u kodu i mogu se promijeniti).

---

## 4. Algoritam

### 4.1. Leksička analiza (urađeno)

Lexer prolazi kroz tekst znak po znak i grupiše znakove u tokene: identifikatore (`addi`,
`t0`, `loop`), direktive (`.word`), brojeve (`42`, `-5`, `0x1F`, `0b101`), stringove i
interpunkciju. Komentari (`#` do kraja reda) i razmaci se preskaču. Svaki token pamti
liniju i kolonu, pa svaka kasnija greška može tačno pokazati gdje je nastala.
Detalji: docstring u `src/asm/lexer.py`.

### 4.2. Sintaksna analiza (parser)

Parser čita tokene red po red, po gramatici iz 3.1 (**rekurzivno spuštanje**: jedna funkcija
po pravilu gramatike), i za svaki red pravi stavke programa:

```text
za svaki red:
    ako red počinje sa IDENT iza kog je ":"   → LabelDef(ime)
    ako slijedi DIRECTIVE                     → Directive(ime, operandi)
    ako slijedi IDENT                         → Instruction(mnemonik, operandi)
    red mora završiti sa NEWLINE, inače greška "očekivan kraj reda"
```

Operandi se odmah klasifikuju: **registar** (`x5`, `t0` → broj 5), **broj**, **simbol**
(labela), **string** ili **memorijski operand** `imm(reg)`. Parser *ne* provjerava da li
instrukcija postoji ni koliko operanada traži — to radi prvi prolaz, gdje je tabela
instrukcija dostupna.

### 4.3. Prvi prolaz — adrese i tabela simbola

Cilj: za svaku labelu saznati adresu, i za svaku stavku znati gdje će biti u memoriji.

```text
sekcija ← .text
LC[.text] ← 0x0000_0000          # brojač lokacija (location counter) po sekciji
LC[.data] ← 0x1000_0000

za svaku stavku programa:
    ako je LabelDef:
        tabela_simbola.definiši(ime, LC[sekcija])          # duplikat → greška
    ako je Directive:
        ako je .text ili .data:  sekcija ← ta sekcija
        inače:
            ako .word:  poravnaj LC[sekcija] na 4
            stavka.adresa ← LC[sekcija]
            LC[sekcija] += veličina(direktiva)              # vidi tabelu 3.4
    ako je Instruction:
        provjeri da mnemonik postoji i da je broj operanada tačan
        ako sekcija nije .text → greška "instrukcija van .text sekcije"
        stavka.adresa ← LC[.text]
        LC[.text] += 4 · broj_riječi(instrukcija)           # 1, ili 2 za li/la
```

Na kraju prvog prolaza tabela simbola sadrži adresu **svake** labele, i one definisane
prije i one definisane poslije mjesta gdje se koriste.

### 4.4. Drugi prolaz — kodiranje

```text
tekst ← prazna lista 32-bitnih riječi
podaci ← prazan niz bajtova

za svaku stavku programa:
    ako je Instruction:
        za svaki operand koji je simbol:
            adresa ← tabela_simbola.zahtijevaj(ime)          # nema je → greška
        ako je pseudo-instrukcija: proširi u 1–2 prave instrukcije
        za svaku pravu instrukciju (na adresi pc):
            ako je grana (B) ili jal (J):
                pomjeraj ← adresa_labele − pc                # PC-relativno!
                provjeri opseg (B: ±4 KiB, J: ±1 MiB) i parnost
            provjeri opseg neposredne vrijednosti (I/S: −2048..2047)
            riječ ← kodiraj(format, polja)                   # 4.5
            dodaj riječ u tekst
    ako je Directive sa podacima:
        dodaj bajtove u podatke (.word: 4 bajta little-endian, labela → njena adresa)
```

### 4.5. Kodiranje formata (bitska polja)

Svaka instrukcija je 32-bitni broj. Polja se postavljaju pomjeranjem bitova
(`vrijednost << pozicija`) i spajaju operacijom ILI:

```text
R:  funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7]       | opcode[6:0]
I:  imm[11:0] → [31:20]        | rs1        | funct3        | rd             | opcode
S:  imm[11:5] → [31:25] | rs2  | rs1        | funct3        | imm[4:0]→[11:7]| opcode
B:  imm[12]→31, imm[10:5]→30:25 | rs2 | rs1 | funct3 | imm[4:1]→11:8, imm[11]→7 | opcode
U:  imm[31:12] → [31:12]                                    | rd             | opcode
J:  imm[20]→31, imm[10:1]→30:21, imm[11]→20, imm[19:12]→19:12 | rd           | opcode
```

Formati B i J imaju „ispremještane” bitove pomjeraja. Bit 0 pomjeraja se ne čuva jer su
adrese instrukcija uvijek parne.

**`hi`/`lo` za `li` i `la`:** `addi` sabira 12-bitni broj **sa znakom**. Zato se gornjih 20
bita računa sa zaokruživanjem:

```text
hi = (vrijednost + 0x800) >> 12
lo = vrijednost − (hi << 12)          # uvijek u opsegu −2048..2047
```

Primjer: `li t0, 0x12345FFF` → `hi = 0x12346`, `lo = −1` →
`lui t0, 0x12346` + `addi t0, t0, -1`.

### 4.6. Obrada grešaka

| Faza | Primjer greške | Poruka |
|---|---|---|
| Lexer | nepoznat znak, loš broj | `t.asm:3:14: lexical error: invalid integer literal '12abc'` |
| Parser | nedostaje zarez, višak tokena | `t.asm:5:9: syntax error: expected ','` |
| Prvi prolaz | nepoznata instrukcija, pogrešan broj operanada, dupla labela, nepoznat registar | `t.asm:7:1: semantic error: duplicate label 'loop' (first defined at t.asm:4)` |
| Drugi prolaz | nedefinisana labela, broj van opsega, grana predaleko | `t.asm:9:5: semantic error: immediate 5000 out of range (-2048..2047)` |

Pravilo: prvi prolaz **skuplja** sve greške (da korisnik vidi sve odjednom), a ako ih ima,
drugi prolaz se ne pokreće.

### 4.7. Izlaz

- `ime.bin` — riječi `.text` sekcije, little-endian (najniži bajt prvi);
- `ime.hex` — čitljiv prikaz `adresa: riječ`, jedna riječ po redu;
- `ime.data.bin` / `ime.data.hex` — sadržaj `.data` sekcije (ako postoji);
- opciono `ime.lst` (`--listing`) — adresa, mašinski kod i originalna linija jedna pored druge.

---

## 5. Primjer korak po korak: `examples/loop.asm`

```asm
.text
    addi t0, x0, 0
    addi t1, x0, 10
loop:
    addi t0, t0, 1
    blt  t0, t1, loop
```

**Prvi prolaz** (t0 = x5, t1 = x6):

| Stavka | Adresa | LC poslije |
|---|---|---|
| `addi t0, x0, 0` | 0x00 | 0x04 |
| `addi t1, x0, 10` | 0x04 | 0x08 |
| `loop:` → tabela simbola: **loop = 0x08** | — | 0x08 |
| `addi t0, t0, 1` | 0x08 | 0x0C |
| `blt t0, t1, loop` | 0x0C | 0x10 |

**Drugi prolaz:**

| Adresa | Instrukcija | Polja | Mašinski kod |
|---|---|---|---|
| 0x00 | `addi t0, x0, 0` | I: imm=0, rs1=0, f3=000, rd=5, op=0010011 | `0x00000293` |
| 0x04 | `addi t1, x0, 10` | I: imm=10, rs1=0, f3=000, rd=6, op=0010011 | `0x00A00313` |
| 0x08 | `addi t0, t0, 1` | I: imm=1, rs1=5, f3=000, rd=5, op=0010011 | `0x00128293` |
| 0x0C | `blt t0, t1, loop` | B: pomjeraj = 0x08 − 0x0C = **−4**, rs1=5, rs2=6, f3=100, op=1100011 | `0xFE62CEE3` |

Kodiranje grane `blt` (pomjeraj −4 kao 13-bitni broj = `1 1111 1111 1100`):

```text
imm[12]=1  imm[10:5]=111111  rs2=00110  rs1=00101  f3=100  imm[4:1]=1110  imm[11]=1  op=1100011
→ 1 111111 00110 00101 100 1110 1 1100011 = 0xFE62CEE3
```

Ostali primjeri (provjereno ručnim računom):

| Program | Mašinski kod |
|---|---|
| `add.asm` | `00500093`, `00700113`, `002081B3` |
| `memory.asm` (`value` na `0x1000_0000`) | `10000297`, `00028293` (= `la t0, value`), `0002A303`, `00130313`, `0062A023` |

---

## 6. Ključne odluke (za razgovor sa mentorom)

1. **Dva prolaza umjesto jednog.** Jednoprolazni asembler mora pamtiti „rupe” za nepoznate
   labele i popunjavati ih kasnije (*backpatching*); dva prolaza su jednostavnija za
   objašnjavanje i testiranje, a za programe ove veličine brzina nije problem.
2. **Ručno pisan lexer i parser** umjesto generatora (lex/yacc) — svaka faza prevodioca je
   vidljiva u kodu, što je i cilj rada.
3. **Postojeća arhitektura (RV32I) umjesto izmišljene** — rezultat se može provjeriti
   poređenjem sa GNU asemblerom (`riscv64-unknown-elf-as`).
4. **Fiksna veličina pseudo-instrukcija** (`la` uvijek 2 riječi) — zato prvi prolaz uvijek
   zna tačne adrese.
5. **Bez spoljnih biblioteka** — samo standardna biblioteka Python-a.

---

## 7. Plan implementacije

Svaki korak se završava testovima (`pytest`) i commit-om.

| # | Korak | Fajlovi | Gotovo kada |
|---|---|---|---|
| 1 | ✅ Lexer | `lexer.py`, `tests/test_lexer.py` | 50 testova prolazi |
| 2 | ✅ Tabela instrukcija i registara | `isa.py`, `tests/test_isa.py` | 74 testa: svaki mnemonik iz 3.2 ima format/opcode/funct3/funct7, kodiranja jedinstvena; `x0..x31`, ABI imena i `fp` daju 0–31 |
| 3 | ✅ Kodiranje svih formata | `encode.py`, `tests/test_encode.py` | 84 testa: poznate riječi (odjeljak 5, negativni pomjeraji), svi pomjeraji grana i uzorak skokova dekodirani nazad, granice opsega, `split_hi_lo` |
| 4 | **Parser** | `parser.py`, `ast_nodes.py` (dodati tip `Operand`), `tests/test_parser.py` | sva tri primjera se parsiraju; greške za loš red imaju tačnu lokaciju |
| 5 | **Prvi prolaz** | `assembler.py`, `directives.py`, `tests/test_assembler.py` | tabela simbola za `loop.asm` daje `loop = 0x08`; duple labele i nepoznate instrukcije prijavljene |
| 6 | **Drugi prolaz + pseudo-instrukcije** | `assembler.py`, `encode.py` | `assemble_source` vraća tačne riječi za `add/loop/memory.asm` (odjeljak 5) |
| 7 | **Izlaz za podatke i CLI** | `output.py`, `cli.py` | `python -m asm examples/memory.asm -o out/` pravi `.bin/.hex` i za `.data`; iz `cli.py` uklonjen privremeni `except NotImplementedError` |
| 8 | **Golden testovi i više primjera** | `examples/*.asm`, `tests/golden/*.hex` | 5+ primjera (petlja, grananje, memorija, funkcija sa `jal`/`ret`, niz u `.data`); izlaz se poredi sa sačuvanim `.hex` |
| 9 | **Poređenje sa GNU as** | skripta `tools/compare_gnu.py` *(opciono)* | za sve primjere mašinski kod identičan izlazu `riscv64-unknown-elf-as` + `objdump` |
| 10 | Nice-to-have | `cli.py` | `--listing`, `--symbols` (ispis tabele simbola), `-v` |

**Redoslijed i zavisnosti:** 2 → 3 se mogu raditi nezavisno od 4; 5 traži 2 i 4; 6 traži 3 i 5.
Koraci 2–6 su jezgro rada, a poglavlje 5 teze („Dizajn i implementacija”) piše se paralelno —
svaka sekcija poglavlja odgovara jednom koraku.

---

## 8. Kako se dokazuje da radi (za sekciju 5.9 i poglavlje 6 teze)

- **Jedinični testovi** po modulu (lexer, kodiranje svakog formata, parser, prolazi).
- **Golden testovi**: za svaki primjer sačuvan je očekivani `.hex`; test ponovo asemblira
  primjer i poredi.
- **Testovi grešaka**: namjerno neispravni programi (dupla labela, nedefinisana labela,
  broj van opsega, grana predaleko) — provjerava se poruka i linija/kolona.
- **Poređenje sa referentnim alatom**: isti programi kroz GNU as; mašinski kod mora biti
  identičan. To je ujedno i odgovor na treće pomoćno istraživačko pitanje iz prijave.
