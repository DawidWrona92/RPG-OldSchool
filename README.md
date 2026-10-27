# Welesza — demo ARPG

Projekt dark fantasy: przypadkowy podróżnik trafia do Niemiru, osady ukrytej w groźnym lesie. PC, single player, kamera i sterowanie inspirowane Diablo 2; wymagająca walka z niewieloma groźnymi przeciwnikami.

Repozytorium jest obecnie w fazie projektowej. Nie wybrano silnika i nie ma jeszcze grywalnej implementacji. Dokumenty rozróżniają zaakceptowane decyzje od propozycji do walidacji. Dane grafów opisują projekty stanów, nie kod AI.

## Kolejność czytania

| Materiał | Zawartość | Status |
|---|---|---|
| [Fabuła demo](docs/demo-fabula.md) | Niemir, cztery zadania główne, cztery poboczne, czternaście postaci | Zaakceptowana koncepcja; szczegóły otwarte oznaczone w tekście |
| [Podstawy mechanik](docs/mechaniki-podstawy.md) | Zebrane decyzje o sterowaniu, rozwoju i łupach | Decyzje i osobno oznaczone propozycje |
| [Ustalenia walki](docs/walka-i-trafienia.md) | Trafienia, krytyki i wiązanki | Decyzje i otwarte szczegóły |
| [Pakiet 01: walka](docs/propozycja-walki-01.md) | Przerwania, garda, wytrzymałość, kombinacje, strzelanie | Do walidacji |
| [Pakiet 02: wyprawa](docs/propozycja-wyprawy-02.md) | Leczenie, zapasy, odwrót, śmierć i zapis | Do walidacji; zależny od 01 |
| [Pakiet 03: bestiariusz](docs/bestiariusz-demo.md) | Sześć zwykłych typów wrogów, dwóch minibossów, Stróż | Do walidacji |
| [Pakiet 03: spotkania i bossowie](docs/spotkania-i-bossowie.md) | Areny, fazy, telegraphy, rozwiązania, reset i nagrody | Do walidacji; zależny od 01–02 |
| [Przegląd 02–03](docs/przeglad-pakietow-02-03.md) | Próby znalezienia luk w projekcie i wynik walidacji grafów | Analiza dokumentów, nie testy gry |
| [Pakiet 04: mapa](docs/pakiet-04-mapa.md) | Układ Niemiru i lasu, drogi, skróty, odnogi i metryki przestrzeni | Do walidacji |
| [Pakiet 04: początek](docs/pakiet-04-poczatek.md) | Prolog, nauka mechanik i pierwsza wyprawa | Do walidacji |
| [Pakiet 04: obrazy](docs/pakiet-04-obrazy.md) | Brief siedmiu kadrów do następnego etapu | Brief ART-01–07: do realizacji; istnieją osobne szkice koncepcyjne |
| [Przegląd 04](docs/pakiet-04-przeglad.md) | Spójność, scenariusze graczy i walidacja połączeń mapy | Analiza projektu, nie testy gry |
| [Przewodnik artystyczny Niemiru](docs/art/niemir/NIEMIR_ART_DIRECTION.md) ([PDF](docs/art/niemir/NIEMIR_ART_DIRECTION.pdf)) | Uzgodniony wygląd osady, przestrzeń, oświetlenie i kryteria oceny | Kierunek zatwierdzony; technologia otwarta |
| [Biblioteka 18 szkiców koncepcyjnych](docs/koncepty/README.md) | Potwory, mieszkańcy, budynki i makiety izometryczne | Referencje wyglądu, nie gotowe sprite’y |
| [Indeks dokumentacji](docs/INDEX.md) | Wszystkie dokumenty fabularne, projektowe i grafiki koncepcyjne | Centralny punkt wejścia |
| [Przed prototypem](docs/przed-prototypem.md) | Dalsza kolejność pracy i decyzje techniczne | Plan roboczy |

Autor przegląda większe pakiety i wskazuje poprawki; nowe propozycje nie stają się automatycznie zatwierdzonym projektem. Wartości liczbowe podane wcześniej są robocze. Nie ustalamy procentowego celu zużycia zapasów.

## Organizacja wiedzy i produkcji

**`main` jest wspólnym źródłem prawdy dla dokumentacji świata, mechanik, zadań, map i zatwierdzonego kierunku artystycznego.** Opisy zawierające propozycje nie stają się automatycznie kanonem. Zobacz [indeks dokumentacji](docs/INDEX.md), [bibliotekę szkiców](docs/koncepty/README.md), [przewodnik Niemiru](docs/art/niemir/NIEMIR_ART_DIRECTION.md) oraz [instrukcje dla współtwórców](AGENTS.md).

Eksperymenty dotyczące modelowania, teksturowania, animacji, renderowania i silnika gry pozostają na oddzielnych gałęziach. **Metoda tworzenia grafiki nie jest na `main` zatwierdzona.** Żaden istniejący eksperyment z innego brancha nie narzuca technologii całemu projektowi.

`.agents/skills/` zawiera historyczne i projektowe narzędzia zespołu. Starsze materiały graficzne oraz ich porównania nie są aktualnym kontraktem produkcyjnym; trwają nowe testy. Dokumenty `docs/skills-graficzne.md` i `docs/zgodnosc-pixel-art.md` mają znaczenie archiwalne.

Grafy `docs/graphs/` są **dokumentacją planowanego układu i zdarzeń**, nie wykonywalną implementacją gry.

## Mapa ciągłego świata

[**Projekt całej doliny Niemiru — mapa v0.1**](docs/world/README.md): 28 miejsc, 30 tras, 12 sektorów i kontrakt eksploracji bez ekranów ładowania. Układ przestrzenny jest **propozycją do greyboxu**, a nie zatwierdzonymi współrzędnymi świata. [Mapa SVG](docs/world/WORLD_MAP.svg) · [Karty sektorów](docs/world/SECTORS.md) · [Bezszwowy streaming](docs/world/STREAMING.md).
