# Welesza — indeks dokumentacji projektu

**Źródło prawdy:** `main` • **Zakres:** świat, fabuła, mechaniki, level design, bestiariusz, dokumentacja wizualna i grafiki koncepcyjne.
**Nie obejmuje:** kodu gry, generatorów grafiki, testowych sprite'ów, atlasów ani animacji. Wspólne zasady renderu opisuje [kontrakt renderu](art/KONTRAKT-RENDERU.md).

Dokumenty wyraźnie odróżniają **decyzje autora**, **uzgodniony kierunek artystyczny**, **propozycje** i **rzeczy do przetestowania**. Nie zmieniaj statusu decyzji bez potwierdzenia autora.

## Fundament i fabuła

- [Koncepcja demo i historia](demo-fabula.md) — **koncepcja zaakceptowana**.
- [Podstawy mechanik](mechaniki-podstawy.md) — decyzje i oddzielne propozycje.
- [Przed prototypem](przed-prototypem.md) — otwarte decyzje oraz kolejność testów.

## Walka i rozwój

- [Walka, trafienia i wiązanki](walka-i-trafienia.md).
- [Pakiet walki 01](propozycja-walki-01.md) — do walidacji.
- [Pakiet wyprawy 02](propozycja-wyprawy-02.md) — do walidacji.
- [Bestiariusz demo](bestiariusz-demo.md) — lista typów, ataki i zachowania.
- [Spotkania i bossowie](spotkania-i-bossowie.md).
- [Przegląd pakietów 02–03](przeglad-pakietow-02-03.md).

## Świat, mapa i pierwsza wyprawa

- [Mapa Niemiru i lasu](pakiet-04-mapa.md) — wcześniejszy plan topologiczny.
- **[Cała dolina — mapa v0.2, sektory, warianty anomalii, QA i greybox](world/README.md)** — zaakceptowana podstawa do greyboxu; nie finalna geometria.
- [Walidator mapy i testy regresyjne](../tools/world/README.md) — skrypt Python, 16 testów i weryfikacja bramek fabularnych.
- [Początek gry i pierwsza wyprawa](pakiet-04-poczatek.md).
- [Plac przy wozie — plan i pakiet dla prototypu](plac-przy-wozie.md) — propozycja do oceny i testów.
- [Brief ilustracji ART-01–ART-07](pakiet-04-obrazy.md).
- [Przegląd pakietu 04](pakiet-04-przeglad.md).
- [Grafy poziomów, bossów i pierwszej wyprawy](graphs/) — dane projektowe, nie implementacja.

## Kierunek artystyczny i obrazy

- **[Przewodnik artystyczny Niemiru v1.1](art/niemir/NIEMIR_ART_DIRECTION.md)** — zaakceptowany klimat osady, paleta, kompozycja i standard oceny.
- [PDF przewodnika](art/niemir/NIEMIR_ART_DIRECTION.pdf) — wersja do czytania.
- **[Kontrakt renderu sprite'ów](art/KONTRAKT-RENDERU.md)** — decyzja autora: prerender w Blenderze; kamera, skala, kierunki, kotwica, światło, eksport i kontrola jakości.
- **[18 ilustracji koncepcyjnych](koncepty/README.md)** — potwory, cywile, architektura i kadry z perspektywy gry.
- [Przyroda boru](koncepty/przyroda/README.md) — arkusze roślinności, skał i drzew, plansze materiałów i [plan assetów](koncepty/przyroda/PLAN-ASSETOW.md).

## Granice między dokumentacją a produkcją

`main` utrzymuje wspólną wiedzę o grze, zatwierdzone referencje artystyczne i [kontrakt renderu](art/KONTRAKT-RENDERU.md). Metoda jest zatwierdzona (prerender w Blenderze), ale same generatory, pliki `.blend`, rendery i atlasy pozostają na niezależnych gałęziach, a ich wynik może trafić do wspólnej bazy dopiero po ocenie. Dokumenty archiwalnych prób technicznych (`skills-graficzne.md`, `zgodnosc-pixel-art.md`) nie stanowią standardu produkcji.

[Wróć do README](../README.md).
