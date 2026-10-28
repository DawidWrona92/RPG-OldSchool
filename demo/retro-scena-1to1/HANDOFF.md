# Retro scena 1:1 — Niemir (brama + osada)

Odtworzenie 1:1 obu dostarczonych kadrów jako grywalnej przeglądarkowej mini-sceny.
Tłem są **oryginalne kadry** (statyczne, cover-fit na canvasie), a ruchome są wyłącznie
postacie: bohater i NPC — wszyscy z animacją oddechu i parą z ust.

## Jak odpalić

- **Najprościej**: pobierz `niemir-1to1.html` (samodzielny plik ~1,1 MB, tła wbudowane
  base64) i otwórz dwuklikiem w przeglądarce.
- Alternatywnie `index.html` + `game.js` + `assets/` (wymaga plików obok siebie).

## Sterowanie

- `W A S D` / strzałki — chodzenie; `Shift` — bieg.
- Scena 1 (brama): podejdź w górę środkową ścieżką pod bramę → przejście do osady.
- Scena 2 (osada): zejdź w dół do dolnej krawędzi → powrót do bramy.

## Postacie

- **Bohater** (postać z pierwszego planu kadru 1): brązowe ubranie, tarcza w lewej
  ręce, miecz w prawej — sterowany graczem, animacja chodu, oddech, para z ust.
- Scena 1: strażnik w zbroi z pióropuszem i włócznią przy bramie, koń przy ogrodzeniu
  (rusza ogonem).
- Scena 2: kobieta w białej sukni z czerwonym fartuchem, wieśniak w kapeluszu z kijem,
  kowal przy kowadle (uderza młotem, iskry), dwie kury (dziobią ziemię).

## Stan / handoff

- Strefy chodu dobrane do kadrów: w scenie 1 korytarz środkowej ścieżki (0.42–0.58 X)
  pozwala podejść pod bramę; w scenie 2 dozwolony pas 0.44–0.92 Y.
- Przejścia scen z fade-to-black (~0.7 s), pozycje spawnu po obu stronach.
- Walidacja: `node --check` + smoke-test w `vm` (ruch, oba przejścia tam i z powrotem).
- Otwarte: kolizje z NPC, interakcje (E), dźwięki.
- Nie jest kontraktem produkcyjnym (produkcja: Blender/Cycles wg KONTRAKT-RENDERU.md).
