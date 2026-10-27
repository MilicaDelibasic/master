# Nacrt prijave teme master rada

> Radni nacrt za popunjavanje „Formulara za prijavu teme master rada" (Prilog 1).
> Tekst je raspoređen po sekcijama formulara; ograničenja broja karaktera su navedena uz svaku sekciju
> (broj u zagradi = približna trenutna dužina, sa razmacima).
>
> **Prije predaje obavezno:**
> - dopuniti sve `[…]` podatke (lični podaci, mentor, fakultet);
> - na mjestima `str. __` upisati **stvarne brojeve stranica** (Smjernice traže konkretne citate sa stranicom);
> - provjeriti izdanje/godinu svake reference u stvarnom primjerku (posebno one označene †);
> - potvrditi sa mentorom izbor RISC-V RV32I podskupa i stil citiranja (ovdje: harvardski, autor–godina).

---

## Podaci o kandidatu/kandidatkinji

| Polje | Vrijednost |
|---|---|
| Ime i prezime | Milica Delibašić |
| Broj indeksa | […] |
| Fakultet | […] |
| Studijski program | […] |
| Godina upisa master studija | […] |

## Podaci o predloženom mentoru/mentorki

| Polje | Vrijednost |
|---|---|
| Mentor/ka, institucija | […] |
| Komentor/ka (ako postoji) | — |
| Obrazloženje | […] (npr. oblast računarskih arhitektura / sistemskog softvera kojom se mentor bavi) |

## Podaci o master radu

**Naslov master rada:**
Dizajn i implementacija jednostavnog asemblerskog prevodioca za prostu arhitekturu

> Predlog preciznijeg, „problemski" formulisanog naslova (Smjernice to preporučuju) — po dogovoru sa mentorom:
> *Dizajn i implementacija dvoprolaznog asemblerskog prevodioca za podskup RISC-V arhitekture (RV32I)*

**Naslov na engleskom jeziku:**
Design and Implementation of a Simple Assembler for a Simple Architecture
(alternativa: *Design and Implementation of a Two-Pass Assembler for a RISC-V (RV32I) Subset*)

**Oblast istraživanja:** Računarske nauke — računarske arhitekture i sistemski softver (prevodioci)

---

## Predmet istraživanja (≤ 4000 karaktera)

Asembler je najniži sloj programskih prevodilaca: on prevodi simbolički zapis instrukcija procesora u mašinski kod i time povezuje arhitekturu skupa instrukcija (ISA) sa programima koji se na njoj izvršavaju (Beck, 1997, str. __; Patterson i Hennessy, 2020, str. __). Iako se danas programi rijetko pišu direktno u asembleru, razumijevanje procesa asembliranja ostaje ključno za razvoj kompajlera, operativnih sistema, ugrađenih sistema i alata za analizu binarnog koda (Levine, 2000, str. __).

Predmet istraživanja je projektovanje i implementacija jednostavnog dvoprolaznog asemblerskog prevodioca za podskup arhitekture RISC-V (RV32I). Klasičan dvoprolazni postupak — u prvom prolazu određivanje adresa i formiranje tabele simbola, a u drugom generisanje mašinskog koda uz razrješavanje referenci unaprijed — opisan je u literaturi o sistemskom softveru (Beck, 1997, str. __; Salomon, 1993, str. __), dok se tehnike leksičke i sintaksne analize preuzimaju iz teorije prevodilaca (Aho i dr., 2006, str. __; Cooper i Torczon, 2023, str. __; Nystrom, 2021, str. __).

Za ciljnu arhitekturu izabran je RISC-V, otvorena i modularna ISA nastala na Univerzitetu Kalifornija u Berkliju (Asanović i Patterson, 2014; Waterman, 2016). Osnovni celobrojni skup RV32I ima mali broj pravilnih formata instrukcija (R, I, S, B, U, J), što ga čini pogodnim za nastavu i za samostalnu implementaciju alata (Waterman i Asanović, 2019, str. __; Patterson i Waterman, 2017, str. __; Harris i Harris, 2022, str. __). Za razliku od vlastite izmišljene arhitekture, izbor postojeće ISA omogućava da se rezultat provjeri poređenjem sa referentnim alatima — GNU asemblerom (Free Software Foundation, 2024) i obrazovnim okruženjima poput RARS i Ripes (Petersen, 2021) — koji počivaju na istoj specifikaciji.

Postojeći asembleri su ili industrijski alati velike složenosti (GNU as, LLVM), čija interna struktura nije pogodna za upoznavanje sa principima prevođenja, ili su dio simulatora čiji je fokus na izvršavanju, a ne na samom procesu prevođenja (Vollmar i Sanderson, 2006). Ovaj rad zato teži rješenju koje je dovoljno malo da se može u potpunosti opisati, a dovoljno potpuno da prevodi smislene programe: sa labelama, direktivama za podatke, granama, skokovima i pristupom memoriji, uz jasne poruke o greškama sa tačnom lokacijom u izvornom kodu.

Aktuelnost teme ogleda se u ubrzanom širenju RISC-V arhitekture u industriji i nastavi (Hennessy i Patterson, 2019, str. __), kao i u potrebi za transparentnim alatima koji pokazuju vezu između teorije prevodilaca i hardvera. Primjenjivost rješenja je prvenstveno obrazovna (demonstracija faza prevođenja, osnova za laboratorijske vježbe), a pravci budućeg razvoja obuhvataju proširenje skupa instrukcija (ekstenzije M, C), generisanje relokatibilnih objektnih fajlova (ELF), povezivanje sa simulatorom i grafički prikaz prevođenja.

> (~2 900 karaktera — ima prostora za još 1–2 rečenice pregleda istraživanja; Smjernice traže **narativni** pregled.)

## Ciljevi istraživanja (≤ 1800 karaktera)

Opšti cilj rada je projektovanje, implementacija i evaluacija jednostavnog dvoprolaznog asemblerskog prevodioca za podskup RISC-V arhitekture RV32I.

Posebni ciljevi su:

1. specificirati ciljnu arhitekturu: registre, organizaciju memorije, formate instrukcija, skup podržanih instrukcija i načine adresiranja;
2. definisati asemblerski jezik: sintaksu, direktive (.text, .data, .word, .byte, .ascii/.asciiz, .space), labele i pravila pisanja programa, uz formalni opis gramatike (EBNF);
3. implementirati asembler u programskom jeziku Python kroz jasno razdvojene faze: leksički analizator, parser, tabelu simbola, prvi i drugi prolaz i generator izlaznih fajlova (binarni i heksadecimalni zapis);
4. obezbijediti razumljivu obradu leksičkih, sintaksnih i semantičkih grešaka sa navođenjem fajla, linije i kolone;
5. provjeriti ispravnost generisanog mašinskog koda automatizovanim testovima i poređenjem sa referentnim asemblerom;
6. analizirati prednosti, ograničenja i mogućnosti proširenja razvijenog rješenja.

## Istraživačka pitanja (≤ 1800 karaktera)

> Smjernice: Odbor insistira na formi istraživačkog pitanja (1 glavno + najmanje 2 pomoćna).

**Glavno istraživačko pitanje:**
Na koji način se može projektovati i implementirati jednostavan dvoprolazni asemblerski prevodilac za podskup RISC-V arhitekture (RV32I) tako da generiše ispravan mašinski kod i daje razumljive dijagnostičke poruke o greškama?

**Pomoćna istraživačka pitanja:**

1. Koji minimalni skup instrukcija, direktiva i pseudo-instrukcija RV32I arhitekture je dovoljan za pisanje smislenih programa (aritmetika, grananje, petlje, pristup memoriji)?
2. Kako se klasične faze prevodioca — leksička, sintaksna i semantička analiza i generisanje koda — preslikavaju na arhitekturu dvoprolaznog asemblera i koje su posebnosti obrade referenci unaprijed (forward references) kod grana i skokova?
3. U kojoj mjeri se mašinski kod koji generiše razvijeni asembler poklapa sa kodom referentnog asemblera (GNU as) za isti ulazni program, i po čemu se razvijeno rješenje razlikuje od postojećih asemblera u pogledu dijagnostike grešaka i složenosti implementacije?

## Plan za realizaciju istraživanja i kratak osvrt na očekivane rezultate (≤ 3000 karaktera)

Istraživanje je razvojnog (konstruktivnog) tipa i realizuje se kroz sljedeće korake:

1. **Pregled literature** (mjesec 1): teorija prevodilaca, sistemski softver i dvoprolazni asembleri, specifikacija RISC-V arhitekture i postojeći alati (GNU as, RARS, Ripes).
2. **Specifikacija** (mjesec 1–2): izbor podskupa RV32I instrukcija, tabela opkodova i formata, definicija sintakse asemblerskog jezika i gramatike u EBNF obliku.
3. **Implementacija** (mjesec 2–4): iterativni razvoj po fazama prevodioca — leksički analizator, parser, tabela simbola, prvi prolaz (adrese i simboli), drugi prolaz (kodiranje instrukcija, razrješavanje labela), generisanje izlaza i obrada grešaka. Implementacija se razvija u programskom jeziku Python 3.12, bez generatora parsera, uz sistem za kontrolu verzija Git.
4. **Testiranje** (paralelno sa implementacijom): jedinični testovi za svaku fazu (pytest), integracioni testovi nad primjerima programa i testovi grešaka (namjerno neispravni ulazni programi).
5. **Evaluacija** (mjesec 4–5): poređenje generisanog mašinskog koda sa izlazom GNU asemblera (riscv64-unknown-elf-as) za isti skup programa; analiza poruka o greškama, ograničenja i performansi.
6. **Pisanje rada** (paralelno, završetak u mjesecu 5–6).

Istraživanje ne uključuje rad sa ispitanicima niti prikupljanje ličnih podataka, pa nije potrebna posebna saglasnost.

Očekuje se da rezultat rada bude funkcionalan asembler koji za podržani podskup RV32I prevodi izvorne programe u binarni i heksadecimalni zapis mašinskog koda, skup primjera i automatizovanih testova, kao i analiza koja treba da pokaže u kojoj mjeri se izlaz poklapa sa referentnim alatom i koja su ograničenja ovakvog pristupa. Očekuje se i da rad pruži sistematičan prikaz preslikavanja teorijskih faza prevodioca na konkretnu implementaciju, pogodan za upotrebu u nastavi.

## Naučne/istraživačke metode (≤ 3000 karaktera)

- **Metoda analize i sinteze literature** — za izgradnju teorijskog okvira o arhitekturama skupa instrukcija i strukturi prevodilaca (Aho i dr., 2006; Beck, 1997; Patterson i Hennessy, 2020) i za izbor podskupa instrukcija na osnovu zvanične specifikacije (Waterman i Asanović, 2019).
- **Metoda modelovanja (specifikacije)** — formalni opis ciljne arhitekture (formati i polja instrukcija) i asemblerskog jezika (gramatika u EBNF obliku), čime se definiše šta asembler treba da prihvati i šta da generiše (Aho i dr., 2006, str. __; Wirth, 1996, str. __).
- **Metoda projektovanja i implementacije (konstruktivna metoda)** — razvoj softverskog rješenja kroz razdvojene module koji odgovaraju fazama prevodioca: ručno pisan leksički analizator i parser rekurzivnim spuštanjem (Nystrom, 2021, str. __; Cooper i Torczon, 2023, str. __), tabela simbola i dvoprolazni algoritam asembliranja (Beck, 1997, str. __; Salomon, 1993, str. __).
- **Eksperimentalna metoda (testiranje i verifikacija)** — automatizovani jedinični i integracioni testovi; za svaki testni program provjerava se da li generisani mašinski kod odgovara očekivanom, kao i da li se za neispravne programe prijavljuje odgovarajuća greška sa tačnom lokacijom.
- **Komparativna metoda** — poređenje izlaza razvijenog asemblera sa referentnim GNU asemblerom (Free Software Foundation, 2024) i obrazovnim alatima (RARS, Ripes; Petersen, 2021) u pogledu ispravnosti koda, kvaliteta dijagnostike i obima podržanih funkcionalnosti.
- **Metoda deskripcije i studije slučaja** — detaljan prikaz prevođenja odabranih primjera programa (tok kroz faze, sadržaj tabele simbola, generisani mašinski kod).

## Predlog strukture master rada

1. **Uvod** — predmet i cilj rada, motivacija, značaj asemblera u računarskim sistemima, istraživačka pitanja, metodologija i struktura rada.
2. **Osnove računarskih arhitektura i asemblera** — arhitektura računarskih sistema, mašinski i asemblerski jezik, instrukcijski skup, RISC i CISC, pregled RISC-V arhitekture, uloga asemblera u prevođenju programa.
3. **Teorijske osnove prevodilaca** — vrste i struktura prevodilaca, leksička, sintaksna i semantička analiza, generisanje mašinskog koda, obrada grešaka.
4. **Specifikacija jednostavne arhitekture** — arhitektura sistema, organizacija memorije, registri, formati instrukcija, podržani skup instrukcija, načini adresiranja, primjer izvršavanja instrukcija.
5. **Projektovanje asemblerskog jezika** — sintaksa, direktive, labele i simboli, tipovi instrukcija, pravila pisanja programa, primjeri.
6. **Dizajn i implementacija asemblerskog prevodioca** — arhitektura rješenja, izbor jezika i alata, leksički analizator, parser, tabela simbola, prevođenje u mašinski kod, generisanje izlaza, obrada grešaka, testiranje.
7. **Praktična realizacija i primjeri rada** — opis sistema, tok prevođenja, primjer programa, generisani mašinski kod, analiza rada, performanse i ograničenja.
8. **Evaluacija i diskusija** — prednosti, nedostaci, poređenje sa postojećim asemblerima, mogućnosti unapređenja.
9. **Zaključak** — ostvareni rezultati, odgovori na istraživačka pitanja, doprinos rada, pravci budućeg razvoja.
10. **Literatura**
11. **Prilozi** — izvorni kod asemblera, primjeri ulaznih programa, tabela instrukcija i opkodova, korisničko uputstvo.

---

## Literatura (harvardski stil, abecedno)

> ≥ 10 primarnih referenci, od toga ≥ 5 iz posljednjih 10 godina (2016+). Ovdje: 21 naslov, 10 iz 2016+ (označeno ★).
> † = provjeriti tačno izdanje/godinu u primjerku koji se koristi.

1. Aho, A. V., Lam, M. S., Sethi, R. i Ullman, J. D. (2006) *Compilers: Principles, Techniques, and Tools*, 2. izd. Boston: Pearson/Addison-Wesley.
2. Appel, A. W. (1998) *Modern Compiler Implementation in C*. Cambridge: Cambridge University Press.
3. Asanović, K. i Patterson, D. A. (2014) *Instruction Sets Should Be Free: The Case for RISC-V*. Technical Report UCB/EECS-2014-146. Berkeley: University of California.
4. Beck, L. L. (1997) *System Software: An Introduction to Systems Programming*, 3. izd. Reading, MA: Addison-Wesley.
5. ★ Cooper, K. D. i Torczon, L. (2023) *Engineering a Compiler*, 3. izd. Cambridge, MA: Morgan Kaufmann. †
6. ★ Free Software Foundation (2024) *Using as: The GNU Assembler* (dokumentacija GNU Binutils). Dostupno na: https://sourceware.org/binutils/docs/as/ [pristupljeno: …].
7. Grune, D., van Reeuwijk, K., Bal, H. E., Jacobs, C. J. H. i Langendoen, K. (2012) *Modern Compiler Design*, 2. izd. New York: Springer.
8. ★ Harris, S. L. i Harris, D. M. (2022) *Digital Design and Computer Architecture: RISC-V Edition*. Cambridge, MA: Morgan Kaufmann. †
9. ★ Hennessy, J. L. i Patterson, D. A. (2019) *Computer Architecture: A Quantitative Approach*, 6. izd. Cambridge, MA: Morgan Kaufmann. †
10. Hyde, R. (2010) *The Art of Assembly Language*, 2. izd. San Francisco: No Starch Press.
11. Levine, J. R. (2000) *Linkers and Loaders*. San Francisco: Morgan Kaufmann.
12. ★ Nystrom, R. (2021) *Crafting Interpreters*. Genever Benning.
13. ★ Patterson, D. A. i Hennessy, J. L. (2020) *Computer Organization and Design RISC-V Edition: The Hardware/Software Interface*, 2. izd. Cambridge, MA: Morgan Kaufmann. †
14. ★ Patterson, D. i Waterman, A. (2017) *The RISC-V Reader: An Open Architecture Atlas*. Strawberry Canyon.
15. ★ Petersen, M. B. (2021) „Ripes: A Visual Computer Architecture Simulator", u: *2021 IEEE/ACM Workshop on Computer Architecture Education (WCAE)*. IEEE. †
16. ★ RISC-V International (2024) *RISC-V Assembly Programmer's Manual*. Dostupno na: https://github.com/riscv-non-isa/riscv-asm-manual [pristupljeno: …].
17. Salomon, D. (1993) *Assemblers and Loaders*. Chichester: Ellis Horwood.
18. Vollmar, K. i Sanderson, P. (2006) „MARS: An Education-Oriented MIPS Assembly Language Simulator", *ACM SIGCSE Bulletin*, 38(1), str. 239–243.
19. ★ Waterman, A. (2016) *Design of the RISC-V Instruction Set Architecture*. Doktorska disertacija, UCB/EECS-2016-1. Berkeley: University of California.
20. ★ Waterman, A. i Asanović, K. (ur.) (2019) *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA*, verzija 20191213. RISC-V Foundation.
21. Wirth, N. (1996) *Compiler Construction*. Harlow: Addison-Wesley.

> Smjernice: najviše 2–3 osnovna udžbenika; skoro sve reference treba da budu citirane u tekstu prijave.
> Trenutno su u tekstu citirane sve osim Appel (1998), Grune i dr. (2012), Hyde (2010) i RISC-V International (2024) —
> ili ih ubaciti u Predmet istraživanja / Metode, ili izbaciti sa liste.
