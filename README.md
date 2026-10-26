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
| [Pakiet 04: obrazy](docs/pakiet-04-obrazy.md) | Brief siedmiu kadrów do następnego etapu | Propozycja; ilustracji jeszcze nie wykonano |
| [Przegląd 04](docs/pakiet-04-przeglad.md) | Spójność, scenariusze graczy i walidacja połączeń mapy | Analiza projektu, nie testy gry |
| [Przed prototypem](docs/przed-prototypem.md) | Dalsza kolejność pracy i decyzje techniczne | Plan roboczy |

Autor przegląda większe pakiety i wskazuje poprawki; nowe propozycje nie stają się automatycznie zatwierdzonym projektem. Wartości liczbowe podane wcześniej są robocze. Nie ustalamy procentowego celu zużycia zapasów.

## Narzędzia projektowe

W [.agents/skills](.agents/skills) znajduje się 19 skilli projektowych z `gamesdesigners-source/agent-game-design-skills` oraz własny skill graficzny [welesza-sprites](.agents/skills/welesza-sprites/SKILL.md). Pochodzenie i licencja: [.agents/SKILLS-SOURCE.md](.agents/SKILLS-SOURCE.md). Instrukcje dla agentów LLM: [AGENTS.md](AGENTS.md).

## Grafika

Sprite'y postaci i potworów powstają jako prerender brył SDF (Python, NumPy, Pillow) w kamerze Diablo 2, w 8 kierunkach: [assets/sprites/prerender](assets/sprites/prerender). Metoda, kontrakt kadru i zasady równoległej pracy: [welesza-sprites](.agents/skills/welesza-sprites/SKILL.md). Pierwsza gotowa postać: Drwal jako ożywieniec, poza zapowiedzi Rozłupania.

```bash
python3 assets/sprites/prerender/drwal.py rozlupanie all
```

Przykładowa weryfikacja grafu projektu:

```bash
python3 .agents/skills/level-designer/scripts/validate_graph.py docs/graphs/boss-stroz.json
```

Nie zastępuje to testu walki, balansu, animacji ani zapisu w docelowym silniku.
