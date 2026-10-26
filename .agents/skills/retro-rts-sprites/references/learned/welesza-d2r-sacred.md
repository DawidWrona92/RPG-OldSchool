# Karta stylu wyuczona z referencji: Diablo II Resurrected (baza 8 screenów)

Data: 26 października 2026 r. Źródło: 8 screenów Diablo II: Resurrected dostarczonych przez autora. Screeny Sacred odrzucone decyzją autora — obowiązuje wyłącznie to, co pokrywa się z D2R. Pliki pozostają poza repozytorium (prawa autorskie Blizzard); wykorzystujemy wyłącznie abstrakcyjne zasady stylu, zgodnie z `reference-learning.md`.

## Pomiary (analyze_reference)

| Kadr | Dominujące grupy barw (hue°) | Wniosek |
|---|---|---|
| D2R akt I (620–1950 px) | 30–90° (zielenie 60–90, ziemia 30), czerwień 0° tylko akcent | las = zgaszone zielenie + gleba; czerwień wyłącznie na wrogach/ogniu |
| D2R loch/jaskinia | 30° zdecydowanie dominuje, zieleń prawie nieobecna | podziemia = paleta ziemska, ciepła pochodnia na zimnym tle |

Wspólne: luminancja pełna 0–255 (głębokie cienie + jasne refleksy), kontrast realizowany jasnością, nie nasyceniem; sprite'y bez półprzezroczystości.

## Wnioski wizualne

1. **Kamera i skala**: izometryczny top-down 3/4, postać ≈ 1/5–1/6 wysokości ekranu; potwierdza canvas 96×116 przy jednostce ~64–84 px wys.
2. **Światło**: źródło górne/z-góry-prawego w terenie otwartym, punktowe ciepłe (pochodnie #ff8c42) na zimnym tle lochów. Cień pada pod postacią, nie rozmywa sylwetki.
3. **Czytelność wrogów**: ciemna sylwetka + subtelny rim light na krawędziach + akcent barwny tylko tam, gdzie gra sygnalizuje zagrożenie. Nigdy kolor tła.
4. **Nastrój**: groza przez ciemność i desaturację terenu; jednostki mają płaskie płaszczyzny materiałów z ostrymi, skupionymi refleksami metalu; brak ditheringu na tkaninach.

## Reguły do rysowania (seria 01 przerysowana + kolejne)

- Kontur ciemny `#17171f` pozostaje; każda jednostka dostaje 1 px rim light po stronie lewej-górnej (jak D2R), rozjaśniony względem materiału, nie czysto biały.
- Baza jednostek przyciemniona i zdesaturowana o jeden stopień względem terenu — jednostka nie może być jaśniejsza od średniej sceny.
- Zakaz ditheringu na tkaninach; metal: ostre refleksy 2–3 px, tkanina: duże płaskie płaszczyzny.
- Czerwień dozwolona tylko: sygnał ataku nieparowalnego, krew, ogień — nigdy dekoracja zwykłego wroga (zgodne z bestiariuszem).
- Cień podłoża: płaski, ciemny, pod postacią — bez rozmycia i bez półprzezroczystości.
