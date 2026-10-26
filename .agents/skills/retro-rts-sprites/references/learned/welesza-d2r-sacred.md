# Karta stylu wyuczona z referencji: D2R + Sacred (baza 10 screenów)

Data: 26 października 2026 r. Źródła: 8 screenów Diablo II: Resurrected i 2 screeny Sacred dostarczone przez autora. Pliki pozostają poza repozytorium (prawa autorskie Blizzard/Ascaron); wykorzystujemy wyłącznie abstrakcyjne zasady stylu, zgodnie z `reference-learning.md`.

## Pomiary (analyze_reference)

| Kadr | Rozmiar | Dominujące grupy barw (hue°) | Wniosek |
|---|---|---|---|
| D2R akt I (620–1950 px) | różne | 30–90° (zielenie 60–90, ziemia 30), czerwienie 0° jako akcent | las = zgaszone zielenie + gleba, czerwień tylko na wrogach/ogniu |
| D2R loch/jaskinia | 780–1920 px | 30° zdecydowanie dominuje, zieleń prawie nieobecna | podziemia = paleta ziemista, ciepła pochodnia na zimnym tle |
| Sacred osada | 1024×768 | 30/60/90 zbalansowane, luminancja średnia ~95 | jaśniejszy, pastelowy kontrapunkt: czytelność przez światło dzienne |

Wspólne: luminancja pełna 0–255 (głębokie cienie + jasne refleksy), półprzezroczystość nieobecna w sprite'ach (dane pełne RGBA), kontrast realizowany jasnością, nie nasyceniem.

## Wnioski wizualne (analiza kadrów)

1. **Kamera i skala**: izometryczny top-down 3/4, postać to ~1/5–1/6 wysokości ekranu; potwierdza canvas 96×116 przy jednostce ~64–84 px wys.
2. **Światło**: D2R — źródło górne/z-góry-prawej w osadzie, punktowe ciepłe (pochodnie #ff8c42) na zimnym tle; Sacred — rozproszone dzienne z lewego górnego. Cień pada pod postacią, nie rozmywa sylwetki.
3. **Czytelność wrogów**: sylwetka + akcent barwny (czerwień #8b0000–#983d48 na zieleni) + subtelny rim light. Nigdy kolor tła.
4. **Paleta Weleszy po korekcie**: baza zgaszone zielenie (60–90°), ziemia/gleba (30°), czerwień wyłącznie jako sygnał wroga/krwi/ognia; loch = ziemia + zimny błękit pośredni, bez zieleni. Pasuje do obecnego `style-card.md` — palette serii 01 jest zgodna (tkanina wyblakła, futro, brak czerwieni na zwykłych przeciwnikach).
5. **Nastrój**: D2R utrzymuje grozę przez ciemność i desaturację; Sacred pokazuje, że osada może być jaśniejsza bez utraty stylu. Dla Niemira → osada jasniejsza niż bór, zgodnie z `pakiet-04-obrazy.md` („ciepło nie oznacza bezpieczeństwa").

## Reguły do rysowania (aktualizacja serii 02+)

- Kontur ciemny `#17171f` pozostaje; na tle boru dodać 1 px rim light z lewego górnego na krawędziach jednostek (jak D2R).
- Zakaz ditheringu na tkaninach potwierdzony — D2R używa płaskich płaszczyzn z ostrymi refleksami metalu.
- Czerwień dozwolona tylko: sygnał ataku nieparowalnego, krew, ogień — nigdy dekoracja zwykłego wroga (spójne z bestiariuszem).
- Osada (Niemir) może używać wyższej luminancji średniej (~90–110) niż bór (~30–50); to rozróżnienie obszarów z mapy pakietu 04.
